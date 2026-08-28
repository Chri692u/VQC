from pathlib import Path
import unittest
from unittest.mock import patch

from bindings import vqc_dafny_core


class DafnyCoreLoaderTests(unittest.TestCase):
    def test_compiled_core_is_resolved_relative_to_python_runtime(self):
        python_runtime = Path(vqc_dafny_core.__file__).resolve().parents[1]

        self.assertEqual(
            vqc_dafny_core.MODULE_PATH,
            python_runtime / "compiled" / "VQC-py",
        )

    def test_missing_compiled_core_fails_without_attempting_a_build(self):
        missing = Path(__file__).resolve().parent / "missing-AccountOps.py"

        with patch.object(vqc_dafny_core, "GENERATED_SENTINEL", missing):
            with self.assertRaisesRegex(FileNotFoundError, "compile_python.ps1"):
                vqc_dafny_core.EnsureDafnyCore()


if __name__ == "__main__":
    unittest.main(verbosity=2)
