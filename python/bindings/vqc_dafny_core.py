"""Locates the precompiled Dafny VQC core shipped with the Python runtime."""

from __future__ import annotations

from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "compiled" / "VQC-py"
GENERATED_SENTINEL = MODULE_PATH / "AccountOps.py"


def EnsureDafnyCore() -> Path:
    """Expose the precompiled core or fail with a compilation instruction."""
    if not GENERATED_SENTINEL.is_file():
        raise FileNotFoundError(
            "Compiled VQC Python core is missing from "
            f"{MODULE_PATH}. Run compile_python.ps1 in the VQC repository, "
            "then copy the complete Python runtime."
        )

    module_path = str(MODULE_PATH)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)

    return MODULE_PATH


EnsureDafnyCore()
