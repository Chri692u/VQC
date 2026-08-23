"""Formatting and reporting functions for VQC runtime values and failures."""

from __future__ import annotations

import re
from typing import Any


def ReportException(error: Exception) -> str:
    message = str(error)
    location = "unknown Dafny source"
    match = re.match(r"([^()]+\(\d+,\d+\)):", message)
    if match:
        location = match.group(1)
    return "\n".join(
        [
            "Dafny runtime error",
            f"  Type: {type(error).__name__}",
            f"  Source: {location}",
            f"  Message: {message}",
        ]
    )


def DisplayAccount(account: Any) -> str:
    positions = account.positions
    orders = account.orders
    position_lines = [
        f"    {position.symbol}: {position.quantity} shares @ {position.averagePrice}"
        for position in positions
    ]
    order_lines = [
        f"    #{order.orderId} {type(order.side).__name__.rsplit('_', 1)[-1].lower()} "
        f"{order.quantity} {order.symbol} ({type(order.status).__name__.rsplit('_', 1)[-1].lower()})"
        for order in orders
    ]

    return "\n".join(
        [
            "VQC Account",
            f"  Cash: {account.cash}",
            "  Positions:",
            *(position_lines or ["    none"]),
            "  Orders:",
            *(order_lines or ["    none"]),
            f"  Ledger entries: {len(account.ledger)}",
        ]
    )


__all__ = ["ReportException", "DisplayAccount"]
