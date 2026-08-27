"""
API Bindings for the VQC Account module.
"""
from __future__ import annotations
from bindings.vqc_dafny_core import EnsureDafnyCore

EnsureDafnyCore()

from _dafny import Seq
import AccountOps as AccountOpsModule
from bindings.vqc_currency import Money
from bindings.vqc_types import (
    Account,
    FillRecord,
    OrderRecord,
    OrderStatus,
    PositionRecord,
    _to_dafny_order_status,
)

AccountOps = AccountOpsModule.default__

def NewAccount() -> Account:
    """Return a verified empty account."""
    return AccountOps.NewAccount()


def Bootstrap(
    cash: Money,
    positions: list[PositionRecord],
    orders: list[OrderRecord],
    ledger_id: int = 1,
    timestamp: int = 0,
) -> Account:
    """Create a trusted opening snapshot from broker-derived state."""
    return AccountOps.Bootstrap(cash, Seq(positions), Seq(orders), ledger_id, timestamp)


def Deposit(account: Account, amount: Money, ledger_id: int = 1, timestamp: int = 0) -> Account:
    """Return an account with a verified positive deposit applied."""
    return AccountOps.Deposit(account, ledger_id, amount, timestamp)


def Withdraw(account: Account, amount: Money, ledger_id: int = 1, timestamp: int = 0) -> Account:
    """Return an account with a verified positive withdrawal applied."""
    return AccountOps.Withdraw(account, ledger_id, amount, timestamp)


def PlaceOrder(account: Account, order: OrderRecord) -> Account:
    """Return an account containing a new structurally valid order."""
    return AccountOps.PlaceOrder(account, order)


def SetOrderStatus(account: Account, order_id: int, new_status: OrderStatus) -> Account:
    """Apply a verified non-fill lifecycle transition."""
    return AccountOps.SetOrderStatus(account, order_id, _to_dafny_order_status(new_status))


def Update(account: Account, fill: FillRecord) -> Account:
    """Apply one verified fill to cash, positions, orders, and ledger."""
    return AccountOps.Update(account, fill)
