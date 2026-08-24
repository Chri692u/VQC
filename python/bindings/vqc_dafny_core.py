"""Locates and builds the compiled Dafny VQC core."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "python" / "compiled" / "VQC.py"
MODULE_PATH = REPO_ROOT / "python" / "compiled" / "VQC-py"


def EnsureDafnyCore() -> Path:
    """Build the Dafny core when needed and return its Python module path."""
    if not MODULE_PATH.exists():
        subprocess.run(
            [
                "dafny",
                "build",
                "dafny/Account.dfy",
                "--target:py",
                "--output:" + str(OUTPUT_PATH),
            ],
            cwd=REPO_ROOT,
            check=True,
        )

    if str(MODULE_PATH) not in sys.path:
        sys.path.insert(0, str(MODULE_PATH))

    return MODULE_PATH


EnsureDafnyCore()
