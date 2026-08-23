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

import AccountOps as AccountOpsModule
import Currency as CurrencyModule
import Execution as ExecutionModule
import Orders as OrdersModule
import Types as TypesModule

AccountOps = AccountOpsModule.default__
DafnyCurrency = CurrencyModule.default__
Orders = OrdersModule.default__
Execution = ExecutionModule.default__
Types = TypesModule

# ---------------------------------------------------------------------------
# Money / currency
# ---------------------------------------------------------------------------


class Money(int):
    """Integer-backed money value with explicit decimal conversion helpers.

    The underlying Dafny model stores money as an integer, so the Python wrapper
    preserves that exact integer representation internally. For user-facing
    decimal values, provide explicit conversion methods.
    """

    SCALE = 100

    @classmethod
    def _as_decimal(cls, value):
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
    def _normalize(cls, value):
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, Money):
            return int(value)
        if isinstance(value, (Decimal, float, str)):
            return int((cls._as_decimal(value) * cls.SCALE).to_integral_value())
        if isinstance(value, int):
            return int(value)
        return int(value)

    @staticmethod
    def _coerce(value):
        return Money._normalize(value)

    @classmethod
    def _from_minor_units(cls, value):
        return int.__new__(cls, int(value))

    @classmethod
    def from_decimal(cls, value):
        minor_units = (cls._as_decimal(value) * cls.SCALE).to_integral_value()
        return cls._from_minor_units(minor_units)

    @classmethod
    def from_float(cls, value):
        return cls.from_decimal(value)

    def to_decimal(self):
        return Decimal(int(self)) / Decimal(self.SCALE)

    def __new__(cls, value: int | float | Decimal | str = 0):
        if isinstance(value, (Decimal, float, str)):
            value = (cls._as_decimal(value) * cls.SCALE).to_integral_value()
        return int.__new__(cls, int(value))

    def __add__(self, other):
        return Money(int(self) + self._coerce(other))

    __radd__ = __add__

    def __sub__(self, other):
        return Money(int(self) - self._coerce(other))

    def __rsub__(self, other):
        return Money(self._coerce(other) - int(self))

    def __mul__(self, other):
        return Money(int(self) * self._coerce(other))

    __rmul__ = __mul__

    def __pos__(self):
        return Money(+int(self))

    def __neg__(self):
        return Money(-int(self))

    def __abs__(self):
        return Money(abs(int(self)))

    def __lt__(self, other):
        return int(self) < self._coerce(other)

    def __le__(self, other):
        return int(self) <= self._coerce(other)

    def __gt__(self, other):
        return int(self) > self._coerce(other)

    def __ge__(self, other):
        return int(self) >= self._coerce(other)

    def __str__(self):
        return str(self.to_decimal())

    def __repr__(self):
        return f"Money({self.to_decimal()})"


def Sum(values):
    return Money(DafnyCurrency.Sum([int(v) for v in values]))


def Cost(qty, price):
    return Money(DafnyCurrency.Cost(int(qty), int(price)))

# ---------------------------------------------------------------------------
# Account lifecycle
# ---------------------------------------------------------------------------

NewAccount = AccountOps.NewAccount


def Deposit(account, amount: int, ledger_id: int = 1, timestamp: int = 0):
    return AccountOps.Deposit(account, ledger_id, amount, timestamp)


def Withdraw(account, amount: int, ledger_id: int = 1, timestamp: int = 0):
    return AccountOps.Withdraw(account, ledger_id, amount, timestamp)


PlaceOrder = AccountOps.PlaceOrder
Update = AccountOps.Update

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
):
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


def Fill(execution_id: int, order_id: int, symbol: str, quantity: int, price: int, timestamp: int):
    return Types.Fill_Fill(execution_id, order_id, symbol, quantity, price, timestamp)


def Position(symbol: str, quantity: int, average_price: int):
    return Types.Position_Position(symbol, quantity, average_price)


def display_account(account) -> str:
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

# ---------------------------------------------------------------------------
# Order state helpers
# ---------------------------------------------------------------------------


def _status_enum(status: str):
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


def SetStatus(order, new_status: str):
    return Orders.SetStatus(order, _status_enum(new_status))


def SetOrderStatus(account, order_id: int, new_status: str):
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

# ---------------------------------------------------------------------------
# Public facade
# ---------------------------------------------------------------------------


class VQC:
    Money = Money
    NewAccount = NewAccount
    Deposit = Deposit
    Withdraw = Withdraw
    PlaceOrder = PlaceOrder
    Update = Update
    Order = Order
    Fill = Fill
    Position = Position
    display_account = display_account
    Sum = Sum
    Cost = Cost
    RemainingQuantity = RemainingQuantity
    SetStatus = SetStatus
    SetOrderStatus = SetOrderStatus
    ApplyFill = ApplyFill
    Cancel = Cancel
    Reject = Reject
    ExecutionValue = ExecutionValue
    Types = Types


__all__ = [
    "Money",
    "VQC",
    "NewAccount",
    "Deposit",
    "Withdraw",
    "PlaceOrder",
    "Update",
    "Order",
    "Fill",
    "Position",
    "display_account",
    "Sum",
    "Cost",
    "RemainingQuantity",
    "SetStatus",
    "SetOrderStatus",
    "ApplyFill",
    "Cancel",
    "Reject",
    "ExecutionValue",
    "Types",
]
