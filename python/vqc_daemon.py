"""Internal synchronization worker for broker-backed VQC clients."""

from __future__ import annotations

from threading import Event, Thread
from typing import Any

from bindings.broker_adapter import TradeUpdateKind
from bindings.vqc_lifecycle import LifecycleUpdate, OrderLifecycle
from bindings.vqc_types import OrderStatus
from vqc import VQC
from vqc_utility import VQCUtility


class _VQCDaemon:
    """Synchronize broker snapshots and events into one client-owned account."""

    _INITIAL_RETRY_SECONDS = 1
    _MAX_RETRY_SECONDS = 30

    def __init__(self, client: Any) -> None:
        self._client = client
        self._order_ids: dict[str, int] = {}
        self._fill_ids: dict[str, int] = {}
        self._lifecycle = OrderLifecycle(client.logger)
        self._trade_stream_thread: Thread | None = None
        self._stream_error: Exception | None = None
        self._stop_event = Event()

    def _SyncAccountFromBroker(self) -> None:
        adapter = self._client._adapter
        broker = self._client.broker
        with self._client._state_lock:
            positions = [
                adapter.ToVQCPosition(position)
                for position in adapter.GetPositions(broker)
            ]
            broker_orders = adapter.GetOpenOrders(broker)
            orders = [
                adapter.ToVQCOrder(order, order_id)
                for order_id, order in enumerate(broker_orders, start=1)
            ]
            self._client._account = VQC.Bootstrap(
                VQC.Money.FromDecimal(str(adapter.GetCash(broker))),
                positions,
                orders,
            )
            self._order_ids.clear()
            self._order_ids.update(
                {
                    adapter.GetOrderKey(order): order_id
                    for order_id, order in enumerate(broker_orders, start=1)
                }
            )
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
                status=OrderStatus.PENDING,
            )
            self._client._account = self._lifecycle.Place(
                self._client._account, order
            )
            order_key = self._client._adapter.GetOrderKey(broker_order)
            self._order_ids[order_key] = order_id

        status = self._client._adapter.GetOrderStatus(broker_order)
        if status not in {
            OrderStatus.PENDING,
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.FILLED,
        }:
            self._ApplyLifecycleUpdate(
                LifecycleUpdate(
                    order_key=order_key,
                    status=status,
                    event="submission",
                )
            )

    def _ApplyLifecycleUpdate(self, update: LifecycleUpdate) -> None:
        """Resolve, verify, apply, and report one lifecycle transition."""
        with self._client._state_lock:
            order_id = self._order_ids.get(update.order_key)
            if order_id is None:
                raise KeyError(
                    f"untracked broker order {update.order_key!r} in lifecycle update"
                )
            self._client._account = self._lifecycle.ApplyStatus(
                self._client._account, order_id, update
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
                self._ApplyLifecycleUpdate(adapter.ToLifecycleUpdate(update))
                return

            execution_key = adapter.GetExecutionKey(update)
            if execution_key in self._fill_ids:
                return

            fill = adapter.ToVQCFill(
                update,
                execution_id=max(self._fill_ids.values(), default=0) + 1,
                order_id=self._order_ids[order_key],
            )
            raw_event = adapter.GetUpdateEvent(update)
            event = str(getattr(raw_event, "value", raw_event)).lower()
            self._client._account = self._lifecycle.ApplyFill(
                self._client._account, fill, event
            )
            self._fill_ids[execution_key] = fill.executionId

    async def _OnTradeUpdate(self, update: Any) -> None:
        self._HandleTradeUpdate(update)

    def _RunTradeStream(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._client._adapter.RunTradeStream(
                    self._client, self._OnTradeUpdate
                )
                if self._stop_event.is_set():
                    return
                self._stream_error = RuntimeError("trade stream ended")
            except Exception as error:
                self._stream_error = error
            self._client.logger.Log(
                "Daemon",
                f"Trade stream stopped: {type(self._stream_error).__name__}: "
                f"{self._stream_error}",
            )
            if self._stop_event.is_set():
                return
            if not self._RecoverBrokerSnapshot():
                return
            self._client.logger.Log("Daemon", "Restarting trade stream.")

    def _RecoverBrokerSnapshot(self) -> bool:
        """Block stream restart until a fresh trusted snapshot is established."""
        retry_seconds = self._INITIAL_RETRY_SECONDS
        while not self._stop_event.is_set():
            try:
                self._SyncAccountFromBroker()
                self._client.logger.Log(
                    "Reconciliation",
                    "Refreshed broker state after trade-stream interruption.",
                )
                return True
            except Exception as error:
                self._client.logger.Log(
                    "Reconciliation",
                    f"Refresh failed: {type(error).__name__}: {error}. "
                    f"Retrying in {retry_seconds}s; stream remains stopped.",
                )
            if self._stop_event.wait(retry_seconds):
                return False
            retry_seconds = min(
                retry_seconds * 2,
                self._MAX_RETRY_SECONDS,
            )
        return False

    def _StartTradeStream(self) -> None:
        if self._trade_stream_thread and self._trade_stream_thread.is_alive():
            return
        self._trade_stream_thread = Thread(
            target=self._RunTradeStream,
            name="vqc-trade-stream",
            daemon=True,
        )
        self._trade_stream_thread.start()
