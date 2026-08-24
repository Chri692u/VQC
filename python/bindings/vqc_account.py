"""
API Bindings for the VQC Account module.
"""
from __future__ import annotations
from decimal import Decimal
from pathlib import Path
from typing import Any
import subprocess
import sys

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
