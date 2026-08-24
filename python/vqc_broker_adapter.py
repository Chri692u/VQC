"""Conversions from Alpaca broker values to the VQC model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from vqc import VQC
from vqc_utility import VQCUtility


class BrokerAdapter:
    """Stateless Alpaca-to-VQC conversion functions."""

    @staticmethod
    def ToVQCTimestamp(value: Any) -> int:
        if isinstance(value, datetime):
            return int(value.timestamp())
        if isinstance(value, str):
            return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
        if value is None:
            return 0
        return int(value)

    @staticmethod
    def ToVQCMoney(value: Any) -> Any:
        return VQC.Money.FromDecimal(str(value))

    @staticmethod
    def ToVQCStatus(status: Any) -> str:
        status = getattr(status, "value", status).lower()
        if status in {"new", "pending_new", "pending_cancel", "pending_replace", "done_for_day", "calculated", "held", "stopped"}:
            return "new"
        if status == "accepted":
            return "accepted"
        if status in {"partially_filled", "partial_fill"}:
            return "partially_filled"
        if status == "filled":
            return "filled"
        if status in {"canceled", "cancelled", "expired"}:
            return "cancelled"
        if status == "rejected":
            return "rejected"
        raise ValueError(f"unsupported Alpaca order status: {status}")

    @staticmethod
    def ToVQCPosition(position: Any) -> Any:
        return VQC.Position(
            position.symbol,
            int(float(position.qty)),
            BrokerAdapter.ToVQCMoney(position.avg_entry_price or 0),
        )

    @staticmethod
    def ToVQCOrder(
        order: Any,
        order_id: int,
        filled_quantity: int | None = None,
        status: str | None = None,
    ) -> Any:
        side = getattr(getattr(order, "side", "buy"), "value", getattr(order, "side", "buy"))
        quantity = int(float(getattr(order, "qty", 0) or 0))
        filled = int(float(getattr(order, "filled_qty", 0) or 0)) if filled_quantity is None else filled_quantity
        order_status = BrokerAdapter.ToVQCStatus(getattr(order, "status", "new")) if status is None else status
        return VQC.Order(order_id, order.symbol, quantity, side, "market", order_status, filled)

    @staticmethod
    def ToVQCFill(update: Any, execution_id: int, order_id: int) -> Any:
        broker_order = VQCUtility.GetField(update, "order")
        if broker_order is None:
            raise ValueError("trade update is missing its order")
        return VQC.Fill(
            execution_id,
            order_id,
            VQCUtility.GetField(broker_order, "symbol"),
            int(float(VQCUtility.GetField(update, "qty", 0) or 0)),
            BrokerAdapter.ToVQCMoney(VQCUtility.GetField(update, "price", 0) or 0),
            BrokerAdapter.ToVQCTimestamp(VQCUtility.GetField(update, "timestamp")),
        )


__all__ = ["BrokerAdapter"]
