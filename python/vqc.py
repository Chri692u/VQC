"""Public wrappers around the generated Dafny VQC account module.

This layer exposes the minimal verified account, order, and money operations that
are intended for external library use. The implementation lives in the generated
Dafny Python modules that are loaded below.
"""

from __future__ import annotations

import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Generated runtime setup
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
ACCOUNT_PY = REPO_ROOT / "compiled" / "py" / "Account-py"
ACTUAL_ACCOUNT_PY = REPO_ROOT / "compiled" / "py" / "Account-py-py"

if not ACTUAL_ACCOUNT_PY.exists():
    subprocess.run(
        [
            "dafny",
            "build",
            "src/Account.dfy",
            "--target:py",
            "--output:" + str(ACCOUNT_PY),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

ACCOUNT_PY = ACTUAL_ACCOUNT_PY

if str(ACCOUNT_PY) not in sys.path:
    sys.path.insert(0, str(ACCOUNT_PY))

from _dafny import HaltException

import AccountOps as AccountOpsModule
import Currency as CurrencyModule
import Execution as ExecutionModule
import Orders as OrdersModule
import Types as TypesModule
import Validation as ValidationModule

AccountOps = AccountOpsModule.default__
DafnyCurrency = CurrencyModule.default__
Orders = OrdersModule.default__
Execution = ExecutionModule.default__
Types = TypesModule
Validation = ValidationModule.default__


# ---------------------------------------------------------------------------
# Money / currency
# ---------------------------------------------------------------------------


class Money(int):
    """Integer-backed money value with explicit decimal conversion methods.

    The underlying Dafny model stores money as an integer, so the Python wrapper
    preserves that exact integer representation internally. For user-facing
    decimal values, provide explicit conversion methods.
    """

    SCALE = 100

    @classmethod
    def AsDecimal(cls, value: Any) -> Decimal:
        if isinstance(value, bool):
            return Decimal(int(value))
        if isinstance(value, Decimal):
            return value
        if isinstance(value, float):
            return Decimal(str(value))
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, int):
            return Decimal(int(value))
        return Decimal(int(value))

    @classmethod
    def Normalize(cls, value: Any) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, Money):
            return int(value)
        if isinstance(value, (Decimal, float, str)):
            return int((cls.AsDecimal(value) * cls.SCALE).to_integral_value())
        if isinstance(value, int):
            return int(value)
        return int(value)

    @staticmethod
    def Coerce(value: Any) -> int:
        return Money.Normalize(value)

    @classmethod
    def FromMinorUnits(cls, value: int) -> "Money":
        return int.__new__(cls, int(value))

    @classmethod
    def FromDecimal(cls, value: Decimal | float | int | str) -> "Money":
        minor_units = (cls.AsDecimal(value) * cls.SCALE).to_integral_value()
        return cls.FromMinorUnits(minor_units)

    @classmethod
    def FromFloat(cls, value: float) -> "Money":
        return cls.FromDecimal(value)

    def ToDecimal(self) -> Decimal:
        return Decimal(int(self)) / Decimal(self.SCALE)

    def __new__(cls, value: int | float | Decimal | str = 0):
        if isinstance(value, (Decimal, float, str)):
            value = (cls.AsDecimal(value) * cls.SCALE).to_integral_value()
        return int.__new__(cls, int(value))

    def __add__(self, other):
        return Money(int(self) + self.Coerce(other))

    __radd__ = __add__

    def __sub__(self, other):
        return Money(int(self) - self.Coerce(other))

    def __rsub__(self, other):
        return Money(self.Coerce(other) - int(self))

    def __mul__(self, other):
        return Money(int(self) * self.Coerce(other))

    __rmul__ = __mul__

    def __pos__(self):
        return Money(+int(self))

    def __neg__(self):
        return Money(-int(self))

    def __abs__(self):
        return Money(abs(int(self)))

    def __lt__(self, other):
        return int(self) < self.Coerce(other)

    def __le__(self, other):
        return int(self) <= self.Coerce(other)

    def __gt__(self, other):
        return int(self) > self.Coerce(other)

    def __ge__(self, other):
        return int(self) >= self.Coerce(other)

    def __str__(self):
        return str(self.ToDecimal())

    def __repr__(self):
        return f"Money({self.ToDecimal()})"


def Sum(values: list[Money]) -> Money:
    return Money(DafnyCurrency.Sum([int(value) for value in values]))


def Cost(quantity: int, price: Money) -> Money:
    return Money(DafnyCurrency.Cost(quantity, int(price)))


# ---------------------------------------------------------------------------
# Account lifecycle
# ---------------------------------------------------------------------------


def NewAccount() -> Any:
    return AccountOps.NewAccount()


def Deposit(account: Any, amount: Money, ledger_id: int = 1, timestamp: int = 0) -> Any:
    return AccountOps.Deposit(account, ledger_id, amount, timestamp)


def Withdraw(account: Any, amount: Money, ledger_id: int = 1, timestamp: int = 0) -> Any:
    return AccountOps.Withdraw(account, ledger_id, amount, timestamp)


def PlaceOrder(account: Any, order: Any) -> Any:
    return AccountOps.PlaceOrder(account, order)


def Update(account: Any, order: Any, fill: Any) -> Any:
    return AccountOps.Update(account, order, fill)


# ---------------------------------------------------------------------------
# Order and execution records
# ---------------------------------------------------------------------------


def Order(
    order_id: int,
    symbol: str,
    quantity: int,
    side: str = "buy",
    order_type: str = "market",
    status: str = "new",
    filled_quantity: int = 0,
    limit_price: int | None = None,
) -> Any:
    if side == "buy":
        side_enum = Types.OrderSide_Buy()
    elif side == "sell":
        side_enum = Types.OrderSide_Sell()
    else:
        raise ValueError(f"unsupported side: {side}")

    if order_type == "market":
        order_type_enum = Types.OrderType_Market()
    elif order_type == "limit":
        if limit_price is None:
            raise ValueError("limit order requires a limit_price")
        order_type_enum = Types.OrderType_Limit(limit_price)
    else:
        raise ValueError(f"unsupported order type: {order_type}")

    if status == "new":
        status_enum = Types.OrderStatus_New()
    elif status == "accepted":
        status_enum = Types.OrderStatus_Accepted()
    elif status == "partially_filled":
        status_enum = Types.OrderStatus_PartiallyFilled()
    elif status == "filled":
        status_enum = Types.OrderStatus_Filled()
    elif status == "cancelled":
        status_enum = Types.OrderStatus_Cancelled()
    elif status == "rejected":
        status_enum = Types.OrderStatus_Rejected()
    else:
        raise ValueError(f"unsupported status: {status}")

    return Types.Order_Order(
        order_id,
        symbol,
        quantity,
        side_enum,
        order_type_enum,
        status_enum,
        filled_quantity,
    )


def Fill(execution_id: int, order_id: int, symbol: str, quantity: int, price: Money, timestamp: int) -> Any:
    return Types.Fill_Fill(execution_id, order_id, symbol, quantity, price, timestamp)


def Position(symbol: str, quantity: int, average_price: Money) -> Any:
    return Types.Position_Position(symbol, quantity, average_price)


# ---------------------------------------------------------------------------
# Order state operations
# ---------------------------------------------------------------------------


def StatusEnum(status: str) -> Any:
    if status == "new":
        return Types.OrderStatus_New()
    if status == "accepted":
        return Types.OrderStatus_Accepted()
    if status == "partially_filled":
        return Types.OrderStatus_PartiallyFilled()
    if status == "filled":
        return Types.OrderStatus_Filled()
    if status == "cancelled":
        return Types.OrderStatus_Cancelled()
    if status == "rejected":
        return Types.OrderStatus_Rejected()
    raise ValueError(f"unsupported status: {status}")


RemainingQuantity = Orders.RemainingQuantity


def SetStatus(order: Any, new_status: str) -> Any:
    return Orders.SetStatus(order, StatusEnum(new_status))


def SetOrderStatus(account: Any, order_id: int, new_status: str) -> Any:
    updated_orders = []
    found = False
    for order in account.orders:
        if order.orderId == order_id:
            updated_orders.append(SetStatus(order, new_status))
            found = True
        else:
            updated_orders.append(order)
    if not found:
        raise ValueError(f"order not found: {order_id}")
    return Types.Account_Account(
        account.cash,
        account.ledger,
        account.positions,
        updated_orders,
    )


ApplyFill = Orders.ApplyFill
Cancel = Orders.Cancel
Reject = Orders.Reject
ExecutionValue = Execution.ExecutionValue

IsValidOrder = Validation.IsValidOrder
IsValidFill = Validation.IsValidFill
IsValidPosition = Validation.IsValidPosition
IsValidLedger = Validation.IsValidLedger
IsValidAccount = Validation.IsValidAccount


# ---------------------------------------------------------------------------
# Public facade
# ---------------------------------------------------------------------------


class VQC:
    HaltException = HaltException
    Money = Money
    NewAccount = NewAccount
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
    SetStatus = SetStatus
    SetOrderStatus = SetOrderStatus
    ApplyFill = ApplyFill
    Cancel = Cancel
    Reject = Reject
    ExecutionValue = ExecutionValue
    IsValidOrder = IsValidOrder
    IsValidFill = IsValidFill
    IsValidPosition = IsValidPosition
    IsValidLedger = IsValidLedger
    IsValidAccount = IsValidAccount
    Types = Types


__all__ = [
    "Money",
    "HaltException",
    "VQC",
    "NewAccount",
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
    "SetStatus",
    "SetOrderStatus",
    "ApplyFill",
    "Cancel",
    "Reject",
    "ExecutionValue",
    "IsValidOrder",
    "IsValidFill",
    "IsValidPosition",
    "IsValidLedger",
    "IsValidAccount",
    "Types",
]
