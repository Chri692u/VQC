"""Broker-neutral contract used by the client and synchronization daemon."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Protocol

from bindings.vqc_types import OrderSide, OrderStatus, OrderType
from .vqc_lifecycle import LifecycleUpdate


class TradeUpdateKind(Enum):
    """The two broker-event categories understood by synchronization."""

    FILL = "fill"
    LIFECYCLE = "lifecycle"


class OrderTimeInForce(Enum):
    """Broker-neutral order-duration choices supported by the client."""

    DAY = "day"
    GTC = "gtc"
    OPG = "opg"
    CLS = "cls"
    IOC = "ioc"
    FOK = "fok"


TradeUpdateCallback = Callable[[Any], Awaitable[None]]
PriceInput = Decimal | int | float | str


class BrokerAdapter(Protocol):
    """Operations every isolated broker integration must implement.

    Broker-native objects deliberately remain ``Any`` at this boundary. Each
    adapter converts them into the strongly constrained VQC records and enums.
    Implementations must not silently truncate quantities or invent missing
    broker fields. They must reject broker account economics that cannot be
    represented by VQC's scalar cash model; adapters never perform FX.
    """

    def MakeBroker(self, env_path: Path, paper: bool) -> Any:
        """Create the native broker client from explicit configuration."""
        ...

    def CanStream(self) -> bool:
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
        time_in_force: OrderTimeInForce,
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

    def GetUpdateEvent(self, update: Any) -> Any:
        """Return the broker-native event name from a trade update."""
        ...

    def ToLifecycleUpdate(self, update: Any) -> LifecycleUpdate:
        """Normalize one non-fill broker event and its failure reason."""
        ...

    def GetExecutionKey(self, update: Any) -> str:
        """Return a stable execution identifier for fill deduplication."""
        ...

    def ToVQCPosition(self, position: Any) -> Any:
        """Normalize one broker position into VQC state."""
        ...

    def ToVQCOrder(
        self,
        order: Any,
        order_id: int,
        filled_quantity: int | None = None,
        status: OrderStatus | None = None,
    ) -> Any:
        """Normalize one broker order into VQC state."""
        ...

    def ToVQCFill(
        self, update: Any, execution_id: int, order_id: int,
    ) -> Any:
        """Normalize one broker fill into VQC state."""
        ...

    def RunTradeStream(self, callback: TradeUpdateCallback) -> None:
        """Run the native event stream and invoke the async callback."""
        ...


__all__ = [
    "BrokerAdapter",
    "OrderTimeInForce",
    "PriceInput",
    "TradeUpdateCallback",
    "TradeUpdateKind",
]
