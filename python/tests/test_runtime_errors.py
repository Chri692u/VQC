import unittest

from vqc_diagnostics import ReportException
from vqc import HaltException, VQC


class DafnyRuntimeNegativeTests(unittest.TestCase):
    def test_dafny_exception_can_be_reported(self):
        try:
            VQC.Withdraw(VQC.Deposit(VQC.NewAccount(), 100, 1, 0), 101, 2, 0)
        except HaltException as error:
            report = ReportException(error)

        self.assertIn("Dafny runtime error", report)
        self.assertIn("dafny/Account.dfy", report)
        self.assertIn("expectation violation", report)

    def test_duplicate_deposit_id_raises_dafny_runtime_error(self):
        account = VQC.Deposit(VQC.NewAccount(), 100, 1, 0)

        with self.assertRaises(HaltException):
            VQC.Deposit(account, 50, 1, 0)

    def test_withdrawal_larger_than_cash_raises_dafny_runtime_error(self):
        account = VQC.Deposit(VQC.NewAccount(), 100, 1, 0)

        with self.assertRaises(HaltException):
            VQC.Withdraw(account, 101, 2, 0)

    def test_invalid_order_raises_dafny_runtime_error(self):
        account = VQC.NewAccount()
        invalid_order = VQC.Order(1, "GLD", 0, "buy", "market", "new", 0)

        with self.assertRaises(HaltException):
            VQC.PlaceOrder(account, invalid_order)

    def test_fill_larger_than_remaining_quantity_raises_dafny_runtime_error(self):
        account = VQC.Deposit(VQC.NewAccount(), 1000, 1, 0)
        order = VQC.Order(1, "GLD", 1, "buy", "market", "new", 0)
        account = VQC.PlaceOrder(account, order)
        invalid_fill = VQC.Fill(1, 1, "GLD", 2, 100, 0)

        with self.assertRaises(HaltException):
            VQC.Update(account, invalid_fill)

    def test_invalid_order_status_transition_raises_dafny_runtime_error(self):
        account = VQC.PlaceOrder(
            VQC.NewAccount(),
            VQC.Order(1, "GLD", 1, "buy", "market", "new", 0),
        )
        account = VQC.SetOrderStatus(account, 1, "accepted")

        with self.assertRaises(HaltException):
            VQC.SetOrderStatus(account, 1, "new")


if __name__ == "__main__":
    unittest.main(verbosity=2)
