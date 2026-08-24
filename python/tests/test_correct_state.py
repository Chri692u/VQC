import unittest

from vqc import VQC


class DafnyStateTests(unittest.TestCase):
    def test_state(self):
        # AccountOps.Deposit: valid positive cash movement.
        account = VQC.Deposit(VQC.NewAccount(), 1000, 1, 0)
        self.assertEqual(account.cash, 1000)

        # AccountOps.Withdraw: valid withdrawal covered by account cash.
        account = VQC.Withdraw(account, 100, 2, 0)
        self.assertEqual(account.cash, 900)

        # AccountOps.PlaceOrder: valid new order with a unique ID.
        order = VQC.Order(1, "GLD", 2, "buy", "market", "new", 0)
        account = VQC.PlaceOrder(account, order)
        self.assertEqual(len(account.orders), 1)

        # AccountOps.Update: valid fill within the order's remaining quantity.
        fill = VQC.Fill(1, 1, "GLD", 2, 100, 0)
        account = VQC.Update(account, order, fill)

        self.assertEqual(account.cash, 700)
        self.assertEqual(account.orders[0].filledQuantity, 2)
        self.assertTrue(account.orders[0].status.is_Filled)
        self.assertEqual(account.positions[0].symbol, "GLD")
        self.assertEqual(account.positions[0].quantity, 2)
        self.assertEqual(len(account.ledger), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
