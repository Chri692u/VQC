"""Broker-neutral order lifecycle records and verified transitions."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Protocol

from .vqc_account import PlaceOrder, SetOrderStatus, Update
from .vqc_types import OrderStatus


@dataclass(frozen=True)
class LifecycleUpdate:
    """One normalized, non-economic broker order-state transition."""

    order_key: str
    status: OrderStatus
    event: str
    reason: str | None = None


class LifecycleLogger(Protocol):
    """Minimal logger contract required by lifecycle reporting."""

    def Log(self, component: str, message: str) -> None:
        ...


class OrderLifecycle:
    """Own verified order transitions and their diagnostic reporting."""

    _FILL_STATUSES = frozenset(
        {OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED}
    )

    def __init__(self, logger: LifecycleLogger) -> None:
        self._logger = logger

    @staticmethod
    def StatusName(status: Any) -> str:
        """Return a stable name for a generated Dafny lifecycle status."""
        generated_name = type(status).__name__.rsplit("_", 1)[-1]
        return re.sub(r"(?<!^)(?=[A-Z])", "_", generated_name).lower()

    @staticmethod
    def _FindOrder(account: Any, order_id: int) -> Any:
        order = next(
            (order for order in account.orders if order.orderId == order_id),
            None,
        )
        if order is None:
            raise ValueError(f"account has no order #{order_id}")
        return order

    def _LogTransition(
        self,
        order_id: int,
        previous: str,
        current: str,
        event: str,
        detail: str | None = None,
    ) -> None:
        message = f"Order #{order_id}: {previous} -> {current} ({event})."
        if detail:
            message += f" {detail}"
        self._logger.Log("Lifecycle", message)

    def Place(self, account: Any, order: Any) -> Any:
        """Register a submitted order and report its initial state."""
        result = PlaceOrder(account, order)
        self._LogTransition(
            order.orderId,
            "created",
            self.StatusName(order.status),
            "submission",
        )
        return result

    def ApplyStatus(
        self, account: Any, order_id: int, update: LifecycleUpdate
    ) -> Any:
        """Apply and report one verified non-economic transition."""
        if update.status in self._FILL_STATUSES:
            raise ValueError(
                f"lifecycle event {update.event!r} cannot apply fill status "
                f"{update.status.value!r} without execution economics"
            )
        order = self._FindOrder(account, order_id)
        previous = self.StatusName(order.status)
        if previous == update.status.value:
            return account
        if update.status is OrderStatus.PENDING and previous != "pending":
            return account

        result = SetOrderStatus(account, order_id, update.status)
        detail = f"Reason: {update.reason}" if update.reason else None
        self._LogTransition(
            order_id, previous, update.status.value, update.event, detail
        )
        return result

    def ApplyFill(self, account: Any, fill: Any, event: str) -> Any:
        """Apply one priced execution and report the resulting lifecycle state."""
        order = self._FindOrder(account, fill.orderId)
        previous = self.StatusName(order.status)
        result = Update(account, fill)
        current = self.StatusName(self._FindOrder(result, fill.orderId).status)
        self._LogTransition(
            fill.orderId,
            previous,
            current,
            event,
            f"Filled {fill.symbol} x {fill.quantity} at {fill.price}.",
        )
        return result


__all__ = ["LifecycleLogger", "LifecycleUpdate", "OrderLifecycle"]
