"""Internal synchronization worker for broker-backed VQC clients."""

from __future__ import annotations

from threading import Thread
from typing import Any

from bindings.broker_adapter import TradeUpdateKind
from bindings.vqc_types import OrderStatus
from vqc import VQC
from vqc_utility import VQCUtility


class _VQCDaemon:
    """Synchronize broker snapshots and events into one client-owned account."""

    def __init__(self, client: Any) -> None:
        self._client = client
        self._order_ids: dict[str, int] = {}
        self._fill_ids: dict[str, int] = {}
        self._trade_stream_thread: Thread | None = None
        self._stream_error: Exception | None = None

    def _SyncAccountFromBroker(self) -> None:
        adapter = self._client._adapter
        broker = self._client.broker
        positions = [
            adapter.ToVQCPosition(position)
            for position in adapter.GetPositions(broker)
        ]
        broker_orders = adapter.GetOpenOrders(broker)
        orders = [
            adapter.ToVQCOrder(order, order_id)
            for order_id, order in enumerate(broker_orders, start=1)
        ]

        with self._client._state_lock:
            self._client._account = VQC.Bootstrap(
                VQC.Money.FromDecimal(str(adapter.GetCash(broker))),
                positions,
                orders,
            )
            self._order_ids = {
                adapter.GetOrderKey(order): order_id
                for order_id, order in enumerate(broker_orders, start=1)
            }
        self._client.logger.Log("Daemon", "Bootstrapped account from broker state.")

    def _TrackSubmittedOrder(self, broker_order: Any) -> None:
        with self._client._state_lock:
            order_id = VQCUtility.NextOrderId(self._client._account.orders)

            # Cumulative fills in the synchronous response have no execution
            # price. Register a clean order and let stream fills apply economics.
            order = self._client._adapter.ToVQCOrder(
                broker_order,
                order_id,
                filled_quantity=0,
                status=OrderStatus.NEW,
            )
            self._client._account = VQC.PlaceOrder(self._client._account, order)
            order_key = self._client._adapter.GetOrderKey(broker_order)
            self._order_ids[order_key] = order_id

        status = self._client._adapter.GetOrderStatus(broker_order)
        if status not in {
            OrderStatus.NEW,
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.FILLED,
        }:
            self._SetOrderStatus(broker_order)

    def _SetOrderStatus(self, broker_order: Any) -> None:
        with self._client._state_lock:
            order_key = self._client._adapter.GetOrderKey(broker_order)
            order_id = self._order_ids[order_key]
            status = self._client._adapter.GetOrderStatus(broker_order)
            if status in {OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED}:
                # Execution events alone carry the incremental fill price and
                # quantity needed for a verified economic transition.
                return
            self._client._account = VQC.SetOrderStatus(
                self._client._account, order_id, status
            )

    def _HandleTradeUpdate(self, update: Any) -> None:
        with self._client._state_lock:
            adapter = self._client._adapter
            broker_order = adapter.GetUpdateOrder(update)
            order_key = adapter.GetOrderKey(broker_order)

            if order_key not in self._order_ids:
                self._client.logger.Log(
                    "Reconciliation",
                    f"Untracked broker order {order_key}; refreshing account from broker.",
                )
                self._SyncAccountFromBroker()
                return

            if adapter.GetUpdateKind(update) is TradeUpdateKind.LIFECYCLE:
                self._SetOrderStatus(broker_order)
                return

            execution_key = adapter.GetExecutionKey(update)
            if execution_key in self._fill_ids:
                return

            fill = adapter.ToVQCFill(
                update,
                execution_id=max(self._fill_ids.values(), default=0) + 1,
                order_id=self._order_ids[order_key],
            )
            self._client._account = VQC.Update(self._client._account, fill)
            self._fill_ids[execution_key] = fill.executionId
            self._client.logger.Log(
                "Validation",
                f"Applied fill for {fill.symbol} x {fill.quantity} at {fill.price}.",
            )

    async def _OnTradeUpdate(self, update: Any) -> None:
        self._HandleTradeUpdate(update)

    def _RunTradeStream(self) -> None:
        try:
            self._client._adapter.RunTradeStream(self._client, self._OnTradeUpdate)
        except Exception as error:
            self._stream_error = error
            self._client.logger.Log(
                "Daemon", f"Trade stream stopped: {type(error).__name__}: {error}"
            )
            raise

    def _StartTradeStream(self) -> None:
        if self._trade_stream_thread and self._trade_stream_thread.is_alive():
            return
        self._trade_stream_thread = Thread(
            target=self._RunTradeStream,
            name="vqc-trade-stream",
            daemon=True,
        )
        self._trade_stream_thread.start()
