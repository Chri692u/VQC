"""Tests for console diagnostics."""

import unittest
from unittest.mock import patch

from vqc_diagnostics import Logger


class LoggerTests(unittest.TestCase):
    def test_muted_logger_does_not_print(self):
        with patch("builtins.print") as print_mock:
            Logger(mute=True).Log("Client", "Hidden message")

        print_mock.assert_not_called()

    def test_logger_tags_each_multiline_message_line(self):
        with patch("builtins.print") as print_mock:
            Logger().Log("Diagnostics", "Ledger\n  #1 Opening")

        print_mock.assert_called_once_with(
            "[VQC][Diagnostics] Ledger\n[VQC][Diagnostics]   #1 Opening"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
