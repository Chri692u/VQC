"""
API Bindings for the VQC types.
"""
from __future__ import annotations
from decimal import Decimal
from pathlib import Path
from typing import Any
import subprocess
import sys

# ---------------------------------------------------------------------------
# Generated runtime setup
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
CODE_PY = REPO_ROOT / "compiled" / "py" / "Account-py"
ACTUAL_CODE_PY = REPO_ROOT / "compiled" / "py" / "Account-py-py"

if not ACTUAL_CODE_PY.exists():
    subprocess.run(
        [
            "dafny",
            "build",
            "src/Account.dfy",
            "--target:py",
            "--output:" + str(CODE_PY),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

CODE_PY = ACTUAL_CODE_PY

if str(CODE_PY) not in sys.path:
    sys.path.insert(0, str(CODE_PY))

from _dafny import HaltException
import Orders as OrdersModule
import Types as TypesModule
import Execution as ExecutionModule
import Validation as ValidationModule

# Dafny emits each module's declarations under its ``default__`` class.
Orders = OrdersModule.default__
Types = TypesModule
Execution = ExecutionModule.default__
Validation = ValidationModule.default__

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
