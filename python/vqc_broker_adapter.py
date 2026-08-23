from __future__ import annotations

import os
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from dotenv import load_dotenv

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest

from vqc import VQC


def AlpacaMoneyToVQCMoney(value: Any) -> Any:
    return VQC.Money.FromDecimal(str(value))


def AlpacaPositionToVQCPosition(position: Any) -> Any:
    return VQC.Position(
        position.symbol,
        int(float(position.qty)),
        AlpacaMoneyToVQCMoney(position.avg_entry_price or 0),
    )


def AlpacaStatusToVQCStatus(status: Any) -> str:
    status = getattr(status, "value", status).lower()
    if status in {
        "new",
        "pending_new",
        "pending_cancel",
        "pending_replace",
        "done_for_day",
        "calculated",
        "held",
        "stopped",
    }:
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


def AlpacaOrderToVQCOrder(
    order: Any,
    order_id: int = 1,
    filled_quantity: int | None = None,
    status: str | None = None,
) -> Any:
    side = getattr(getattr(order, "side", "buy"), "value", getattr(order, "side", "buy"))
    filled_quantity = (
        int(float(getattr(order, "filled_qty", 0) or 0))
        if filled_quantity is None
        else filled_quantity
    )
    status = (
        AlpacaStatusToVQCStatus(getattr(order, "status", "new"))
        if status is None
        else status
    )
    return VQC.Order(
        order_id,
        order.symbol,
        int(float(getattr(order, "qty", 0) or 0)),
        side,
        "market",
        status,
        filled_quantity,
    )


def AlpacaFillToVQCFill(fill: Any, execution_id: int = 1, order_id: int = 1) -> Any:
    return VQC.Fill(
        execution_id,
        order_id,
        fill.symbol,
        int(float(getattr(fill, "qty", 0) or 0)),
        AlpacaMoneyToVQCMoney(getattr(fill, "price", 0) or 0),
        0,
    )