"""Small shared utilities for the Python VQC boundary."""

from __future__ import annotations

from typing import Any


class VQCUtility:
    """Pure Python helpers mirroring the small Dafny utility layer."""

    @staticmethod
    def GetField(value: Any, name: str, default: Any = None) -> Any:
        if isinstance(value, dict):
            return value.get(name, default)
        return getattr(value, name, default)

    @staticmethod
    def GetOrderKey(broker_order: Any) -> str:
        order_id = VQCUtility.GetField(broker_order, "id")
        if order_id is None:
            raise ValueError("broker order is missing its ID")
        return str(order_id)

    @staticmethod
    def NextOrderId(orders: Any) -> int:
        if not orders:
            return 1
        return max(order.orderId for order in orders) + 1

    @staticmethod
    def GetOrAddId(ids: dict[str, int], external_id: Any, label: str) -> int:
        key = str(external_id)
        if not key:
            raise ValueError(f"{label} is missing its ID")
        if key not in ids:
            ids[key] = len(ids) + 1
        return ids[key]
