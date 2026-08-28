"""Shared helpers, formatting, and logging for the Python VQC boundary."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


class VQCUtility:
    """Internal helpers shared by adapters and synchronization code."""

    @staticmethod
    def GetField(value: Any, name: str, default: Any = None) -> Any:
        """Read a field uniformly from a broker object or mapping."""
        if isinstance(value, dict):
            return value.get(name, default)
        return getattr(value, name, default)

    @staticmethod
    def RequireField(value: Any, name: str, label: str) -> Any:
        """Read a required broker field and identify malformed responses."""
        result = VQCUtility.GetField(value, name)
        if result is None:
            raise ValueError(f"{label} is missing {name}")
        return result

    @staticmethod
    def GetOrderKey(broker_order: Any) -> str:
        """Return the stable string key for a broker-native order."""
        order_id = VQCUtility.GetField(broker_order, "id")
        if order_id is None:
            raise ValueError("broker order is missing its ID")
        return str(order_id)

    @staticmethod
    def NextOrderId(orders: Any) -> int:
        """Choose the next local numeric order ID."""
        if not orders:
            return 1
        return max(order.orderId for order in orders) + 1


@dataclass
class Logger:
    """Small console logger that can suppress all VQC output."""

    mute: bool = False

    def Log(self, component: str, message: str) -> None:
        """Print a consistently tagged message unless output is muted."""
        if self.mute:
            return
        prefix = f"[VQC][{component}]"
        print("\n".join(f"{prefix} {line}" for line in message.splitlines()))


def ReportException(error: Exception) -> str:
    """Return a concise report for a Dafny or Python runtime exception."""
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
    """Format a VQC account snapshot for diagnostics."""

    def order_type(order: Any) -> str:
        """Describe the generated order-type variant and its prices."""
        value = order.orderType
        if value.is_Limit:
            return f"limit @{value.limitPrice}"
        if value.is_Stop:
            return f"stop @{value.stopPrice}"
        if value.is_StopLimit:
            return f"stop-limit stop={value.stopPrice} limit={value.limitPrice}"
        return "market"

    position_lines = [
        f"    {position.symbol}: {position.quantity} shares @ {position.averagePrice}"
        for position in account.positions
    ]
    order_lines = [
        f"    #{order.orderId} {type(order.side).__name__.rsplit('_', 1)[-1].lower()} "
        f"{order.quantity} {order.symbol} {order_type(order)} "
        f"({type(order.status).__name__.rsplit('_', 1)[-1].lower()})"
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
    """Format VQC ledger entries for diagnostics."""
    lines = ["Ledger"]
    # The generated Account.ledger accessor projects the Dafny Ledger
    # datatype to its entries sequence at the Python boundary.
    for entry in ledger:
        entry_id = getattr(entry, "ledgerId", "unknown")
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


__all__ = ["Logger", "ReportException", "DisplayAccount", "DisplayLedger"]
