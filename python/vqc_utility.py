"""Shared helpers, formatting, and logging for the Python VQC boundary."""

from __future__ import annotations

from dataclasses import dataclass
import re
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


@dataclass
class Logger:
    """Small console logger that can suppress all VQC output."""

    mute: bool = False

    def Log(self, component: str, message: str) -> None:
        if self.mute:
            return
        prefix = f"[VQC][{component}]"
        print("\n".join(f"{prefix} {line}" for line in message.splitlines()))


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
    position_lines = [
        f"    {position.symbol}: {position.quantity} shares @ {position.averagePrice}"
        for position in account.positions
    ]
    order_lines = [
        f"    #{order.orderId} {type(order.side).__name__.rsplit('_', 1)[-1].lower()} "
        f"{order.quantity} {order.symbol} ({type(order.status).__name__.rsplit('_', 1)[-1].lower()})"
        for order in account.orders
    ]
    return "\n".join(
        [
            "Account",
            f"  Cash: {account.cash}",
            "  Positions:",
            *(position_lines or ["    none"]),
            "  Orders:",
            *(order_lines or ["    none"]),
            f"  Ledger entries: {len(account.ledger)}",
        ]
    )


def DisplayLedger(ledger: Any) -> str:
    lines = ["Ledger"]
    for entry in ledger:
        entry_id = getattr(entry, "id_", "unknown")
        if getattr(entry, "is_Opening", False):
            lines.append(
                f"  #{entry_id} Opening: cash={entry.cash}, "
                f"positions={len(entry.positions)}, orders={len(entry.orders)}"
            )
        elif getattr(entry, "is_Deposit", False):
            lines.append(f"  #{entry_id} Deposit: amount={entry.amount}")
        elif getattr(entry, "is_Withdrawal", False):
            lines.append(f"  #{entry_id} Withdrawal: amount={entry.amount}")
        elif getattr(entry, "is_Trade", False):
            fill = entry.fill
            lines.append(
                f"  #{entry_id} Trade: order={fill.orderId}, {fill.symbol} x{fill.quantity} "
                f"@ {fill.price}"
            )
        else:
            lines.append(f"  #{entry_id} Unknown entry")
    return "\n".join(lines)


__all__ = ["VQCUtility", "Logger", "ReportException", "DisplayAccount", "DisplayLedger"]
