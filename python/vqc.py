"""Public wrappers around the generated Dafny VQC account module.

This layer exposes the minimal verified account, order, and money operations that
are intended for external library use. The implementation lives in the generated
Dafny Python modules that are loaded below.
"""

from __future__ import annotations

from bindings import (
    Account,
    Bootstrap,
    Cost,
    Deposit,
    Fill,
    FillRecord,
    IsValidAccount,
    IsValidFill,
    IsValidLedger,
    IsValidOrder,
    IsValidPosition,
    Ledger,
    Money,
    NewAccount,
    Order,
    OrderRecord,
    PlaceOrder,
    Position,
    PositionRecord,
    RemainingQuantity,
    SetOrderStatus,
    Sum,
    Update,
    Withdraw,
)
from bindings.vqc_dafny_core import EnsureDafnyCore

EnsureDafnyCore()

from _dafny import HaltException

class VQC:
    HaltException = HaltException
    Money = Money
    Account = Account
    Ledger = Ledger
    OrderRecord = OrderRecord
    FillRecord = FillRecord
    PositionRecord = PositionRecord
    NewAccount = NewAccount
    Bootstrap = Bootstrap
    Deposit = Deposit
    Withdraw = Withdraw
    PlaceOrder = PlaceOrder
    Update = Update
    Order = Order
    Fill = Fill
    Position = Position
    Sum = Sum
    Cost = Cost
    RemainingQuantity = RemainingQuantity
    SetOrderStatus = SetOrderStatus
    IsValidOrder = IsValidOrder
    IsValidFill = IsValidFill
    IsValidPosition = IsValidPosition
    IsValidLedger = IsValidLedger
    IsValidAccount = IsValidAccount


__all__ = [
    "Money",
    "Account",
    "Ledger",
    "OrderRecord",
    "FillRecord",
    "PositionRecord",
    "HaltException",
    "VQC",
    "NewAccount",
    "Bootstrap",
    "Deposit",
    "Withdraw",
    "PlaceOrder",
    "Update",
    "Order",
    "Fill",
    "Position",
    "Sum",
    "Cost",
    "RemainingQuantity",
    "SetOrderStatus",
    "IsValidOrder",
    "IsValidFill",
    "IsValidPosition",
    "IsValidLedger",
    "IsValidAccount",
]
