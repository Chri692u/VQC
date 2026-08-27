"""Broker-neutral contract used by the client and synchronization daemon."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any, Awaitable, Callable, Protocol

from bindings.vqc_types import OrderSide, OrderStatus, OrderType


class TradeUpdateKind(Enum):
    """Normalized categories understood by the synchronization daemon."""

    FILL = "fill"
    LIFECYCLE = "lifecycle"


TradeUpdateCallback = Callable[[Any], Awaitable[None]]
PriceInput = Decimal | int | float | str


class BrokerAdapter(Protocol):
    """Operations every isolated broker integration must implement.

    Broker-native objects deliberately remain ``Any`` at this boundary. Each
    adapter converts them into the strongly constrained VQC records and enums.
    Implementations must not silently truncate quantities or invent missing
    broker fields.
    """

    def MakeBroker(self, client: Any) -> Any:
        """Create the native broker client from VQC client configuration."""
        ...

    def CanStream(self, client: Any) -> bool:
        """Return whether the adapter has enough configuration to stream."""
        ...

    def IsMarketOpen(self, broker: Any) -> bool:
        """Return the broker's regular-session clock state."""
        ...

    def SubmitOrder(
        self,
        broker: Any,
        symbol: str,
        quantity: int,
        side: OrderSide,
        order_type: OrderType,
        limit_price: PriceInput | None,
        stop_price: PriceInput | None,
        extended_hours: bool,
    ) -> Any:
        """Submit one native broker order and return its broker record."""
        ...

    def GetCash(self, broker: Any) -> Any:
        """Return the broker account's cash value in major currency units."""
        ...

    def GetPositions(self, broker: Any) -> list[Any]:
        """Return all native open-position records."""
        ...

    def GetOpenOrders(self, broker: Any) -> list[Any]:
        """Return all native open-order records used for reconciliation."""
        ...

    def GetOrderKey(self, order: Any) -> str:
        """Return a stable broker identifier for one order."""
        ...

    def GetOrderStatus(self, order: Any) -> OrderStatus:
        """Normalize a native status into the VQC lifecycle enum."""
        ...

    def GetUpdateKind(self, update: Any) -> TradeUpdateKind:
        """Classify a native update as execution or lifecycle only."""
        ...

    def GetUpdateOrder(self, update: Any) -> Any:
        """Return the native order embedded in a trade update."""
        ...

    def GetExecutionKey(self, update: Any) -> str:
        """Return a stable execution identifier for fill deduplication."""
        ...

    def ToVQCPosition(self, position: Any) -> Any:
        """Convert one native position into a valid VQC position."""
        ...

    def ToVQCOrder(
        self,
        order: Any,
        order_id: int,
        filled_quantity: int | None = None,
        status: OrderStatus | None = None,
    ) -> Any:
        """Convert one native order, allowing safe submission overrides."""
        ...

    def ToVQCFill(self, update: Any, execution_id: int, order_id: int) -> Any:
        """Convert one native execution update into a valid VQC fill."""
        ...

    def RunTradeStream(self, client: Any, callback: TradeUpdateCallback) -> None:
        """Run the native event stream and invoke the async callback."""
        ...


__all__ = ["BrokerAdapter", "PriceInput", "TradeUpdateCallback", "TradeUpdateKind"]
