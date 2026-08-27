"""Keep the verified VQC account synchronized with a broker."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Thread
from typing import Any

from vqc import VQC
from vqc_utility import VQCUtility


@dataclass
class VQCDaemon:
    """Own synchronized VQC state and consume broker lifecycle events."""

    client: Any
    order_ids: dict[str, int] = field(default_factory=dict, init=False)
    fill_ids: dict[str, int] = field(default_factory=dict, init=False)
    trade_stream_thread: Thread | None = field(default=None, init=False, repr=False)

    def SyncAccountFromBroker(self) -> None:
        adapter = self.client.adapter
        positions = [adapter.ToVQCPosition(value) for value in adapter.GetPositions(self.client.broker)]
        broker_orders = adapter.GetOpenOrders(self.client.broker)
        orders = [adapter.ToVQCOrder(value, order_id) for order_id, value in enumerate(broker_orders, 1)]
        with self.client.state_lock:
            self.client.account = VQC.Bootstrap(
                VQC.Money.FromDecimal(str(adapter.GetCash(self.client.broker))), positions, orders
            )
            self.order_ids = {
                adapter.GetOrderKey(value): order_id
                for order_id, value in enumerate(broker_orders, 1)
            }
        self.client.logger.Log("Daemon", "Bootstrapped account from broker state.")

    def NextOrderId(self) -> int:
        with self.client.state_lock:
            return VQCUtility.NextOrderId(self.client.account.orders)

    def TrackSubmittedOrder(self, broker_order: Any, symbol: str, quantity: float, side: str) -> None:
        with self.client.state_lock:
            order_id = VQCUtility.NextOrderId(self.client.account.orders)
            order = VQC.Order(order_id, symbol, int(quantity), side, "market", "new", 0)
            self.client.account = VQC.PlaceOrder(self.client.account, order)
            self.order_ids[self.client.adapter.GetOrderKey(broker_order)] = order_id
        status = self.client.adapter.GetOrderStatus(broker_order)
        if status not in {"new", "partially_filled", "filled"}:
            self.SetOrderStatus(broker_order)

    def SetOrderStatus(self, broker_order: Any) -> None:
        with self.client.state_lock:
            order_id = self.order_ids[self.client.adapter.GetOrderKey(broker_order)]
            status = self.client.adapter.GetOrderStatus(broker_order)
            if status in {"partially_filled", "filled"}:
                raise ValueError("filled broker orders must be applied through a fill event")
            self.client.account = VQC.SetOrderStatus(self.client.account, order_id, status)

    def HandleTradeUpdate(self, update: Any) -> None:
        with self.client.state_lock:
            event = self.client.adapter.GetUpdateEvent(update)
            broker_order = self.client.adapter.GetUpdateOrder(update)
            if broker_order is None:
                raise ValueError("trade update is missing its order")
            order_key = self.client.adapter.GetOrderKey(broker_order)
            if order_key not in self.order_ids:
                self.client.logger.Log("Reconciliation", f"Untracked broker order {order_key}; refreshing account from broker.")
                self.SyncAccountFromBroker()
                return
            if event not in {"partial_fill", "fill"}:
                self.SetOrderStatus(broker_order)
                return
            execution_key = self.client.adapter.GetExecutionKey(update)
            if execution_key in self.fill_ids:
                return
            fill = self.client.adapter.ToVQCFill(
                update,
                execution_id=max(self.fill_ids.values(), default=0) + 1,
                order_id=self.order_ids[order_key],
            )
            self.client.account = VQC.Update(self.client.account, fill)
            self.fill_ids[execution_key] = fill.executionId
            self.client.logger.Log("Validation", f"Applied fill for {fill.symbol} x {fill.quantity} at {fill.price}.")

    async def OnTradeUpdate(self, update: Any) -> None:
        self.HandleTradeUpdate(update)

    def RunTradeStream(self) -> None:
        self.client.adapter.RunTradeStream(self.client, self.OnTradeUpdate)

    def StartTradeStream(self) -> None:
        if self.trade_stream_thread and self.trade_stream_thread.is_alive():
            return
        self.trade_stream_thread = Thread(
            target=self.RunTradeStream, name="vqc-trade-stream", daemon=True
        )
        self.trade_stream_thread.start()


__all__ = ["VQCDaemon"]
