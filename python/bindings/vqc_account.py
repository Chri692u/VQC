"""
API Bindings for the VQC Account module.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Any

from bindings.vqc_dafny_core import EnsureDafnyCore

EnsureDafnyCore()

from _dafny import HaltException
from _dafny import Seq
import AccountOps as AccountOpsModule
from bindings.vqc_currency import Money
from bindings.vqc_types import Account, FillRecord, OrderRecord, PositionRecord, StatusEnum

AccountOps = AccountOpsModule.default__

def NewAccount() -> Account:
    return AccountOps.NewAccount()


def Bootstrap(
    cash: Money,
    positions: list[PositionRecord],
    orders: list[OrderRecord],
    ledger_id: int = 1,
    timestamp: int = 0,
) -> Account:
    return AccountOps.Bootstrap(cash, Seq(positions), Seq(orders), ledger_id, timestamp)


def Deposit(account: Account, amount: Money, ledger_id: int = 1, timestamp: int = 0) -> Account:
    return AccountOps.Deposit(account, ledger_id, amount, timestamp)


def Withdraw(account: Account, amount: Money, ledger_id: int = 1, timestamp: int = 0) -> Account:
    return AccountOps.Withdraw(account, ledger_id, amount, timestamp)


def PlaceOrder(account: Account, order: OrderRecord) -> Account:
    return AccountOps.PlaceOrder(account, order)


def SetOrderStatus(account: Account, order_id: int, new_status: str) -> Account:
    return AccountOps.SetOrderStatus(account, order_id, StatusEnum(new_status))


def Update(account: Account, fill: FillRecord) -> Account:
    return AccountOps.Update(account, fill)
