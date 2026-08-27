"""
API Bindings for the VQC types.
"""
from __future__ import annotations
from enum import Enum
from typing import Any

from bindings.vqc_dafny_core import EnsureDafnyCore
from bindings.vqc_currency import Money

EnsureDafnyCore()

import Orders as OrdersModule
import Types as TypesModule
import Validation as ValidationModule

Orders = OrdersModule.default__
Types = TypesModule
Validation = ValidationModule.default__

Account = Types.Account_Account
Ledger = Types.Ledger_Ledger
OrderRecord = Types.Order_Order
FillRecord = Types.Fill_Fill
PositionRecord = Types.Position_Position


class OrderStatus(Enum):
    """Broker-neutral lifecycle states supported by the verified core."""

    NEW = "new"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderSide(Enum):
    """Economic direction of an order."""

    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Primitive order instructions represented by VQC."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


def Order(
    order_id: int,
    symbol: str,
    quantity: int,
    side: OrderSide = OrderSide.BUY,
    order_type: OrderType = OrderType.MARKET,
    status: OrderStatus = OrderStatus.NEW,
    filled_quantity: int = 0,
    limit_price: Money | None = None,
    stop_price: Money | None = None,
) -> OrderRecord:
    """Create a typed Dafny order record from the public Python enums."""
    if side is OrderSide.BUY:
        side_enum = Types.OrderSide_Buy()
    elif side is OrderSide.SELL:
        side_enum = Types.OrderSide_Sell()
    else:
        raise ValueError(f"unsupported side: {side}")

    if order_type is OrderType.MARKET:
        order_type_enum = Types.OrderType_Market()
    elif order_type is OrderType.LIMIT:
        if limit_price is None:
            raise ValueError("limit order requires a limit_price")
        order_type_enum = Types.OrderType_Limit(limit_price)
    elif order_type is OrderType.STOP:
        if stop_price is None:
            raise ValueError("stop order requires a stop_price")
        order_type_enum = Types.OrderType_Stop(stop_price)
    elif order_type is OrderType.STOP_LIMIT:
        if stop_price is None or limit_price is None:
            raise ValueError("stop-limit order requires stop_price and limit_price")
        order_type_enum = Types.OrderType_StopLimit(stop_price, limit_price)
    else:
        raise ValueError(f"unsupported order type: {order_type}")

    status_enum = _to_dafny_order_status(status)

    return OrderRecord(
        order_id,
        symbol,
        quantity,
        side_enum,
        order_type_enum,
        status_enum,
        filled_quantity,
    )


def Fill(
    execution_id: int,
    order_id: int,
    symbol: str,
    quantity: int,
    price: Money,
    timestamp: int,
) -> FillRecord:
    """Create a priced execution record for an existing order."""
    return FillRecord(execution_id, order_id, symbol, quantity, price, timestamp)


def Position(symbol: str, quantity: int, average_price: Money) -> PositionRecord:
    """Create a long-position record using whole-share quantity."""
    return PositionRecord(symbol, quantity, average_price)


def _to_dafny_order_status(status: OrderStatus) -> Any:
    """Translate the public enum into its generated Dafny counterpart."""
    if status is OrderStatus.NEW:
        return Types.OrderStatus_New()
    if status is OrderStatus.ACCEPTED:
        return Types.OrderStatus_Accepted()
    if status is OrderStatus.PARTIALLY_FILLED:
        return Types.OrderStatus_PartiallyFilled()
    if status is OrderStatus.FILLED:
        return Types.OrderStatus_Filled()
    if status is OrderStatus.CANCELLED:
        return Types.OrderStatus_Cancelled()
    if status is OrderStatus.REJECTED:
        return Types.OrderStatus_Rejected()
    raise ValueError(f"unsupported status: {status}")


RemainingQuantity = Orders.RemainingQuantity


IsValidOrder = Validation.IsValidOrder
IsValidFill = Validation.IsValidFill
IsValidPosition = Validation.IsValidPosition
IsValidLedger = Validation.IsValidLedger
IsValidAccount = Validation.IsValidAccount
