"""
API Bindings for the VQC Account module.
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
import AccountOps as AccountOpsModule
from bindings.vqc_currency import Money

AccountOps = AccountOpsModule.default__

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
