"""Locates and builds the compiled Dafny VQC core."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "python" / "compiled" / "VQC.py"
MODULE_PATH = REPO_ROOT / "python" / "compiled" / "VQC-py"
GENERATED_SENTINEL = MODULE_PATH / "AccountOps.py"


def _core_needs_build() -> bool:
    """Return whether generated Python is absent or older than Dafny sources."""
    if not GENERATED_SENTINEL.exists():
        return True
    generated_at = GENERATED_SENTINEL.stat().st_mtime
    return any(
        source.stat().st_mtime > generated_at
        for source in (REPO_ROOT / "dafny").glob("*.dfy")
    )


def EnsureDafnyCore() -> Path:
    """Build the Dafny core when needed and return its Python module path."""
    if _core_needs_build():
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
