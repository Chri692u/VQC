import unittest

from vqc import VQC


class DafnyStateTests(unittest.TestCase):
    def test_state(self):
        account = VQC.Deposit(VQC.NewAccount(), 1000, 1, 0)
        self.assertEqual(account.cash, 1000)

        account = VQC.Withdraw(account, 100, 2, 0)
        self.assertEqual(account.cash, 900)

        order = VQC.Order(1, "GLD", 2, VQC.OrderSide.BUY, VQC.OrderType.MARKET, VQC.OrderStatus.PENDING, 0)
        account = VQC.PlaceOrder(account, order)
        self.assertEqual(len(account.orders), 1)

        fill = VQC.Fill(1, 1, "GLD", 2, 100, 0)
        account = VQC.Update(account, fill)

        self.assertEqual(account.cash, 700)
        self.assertEqual(account.orders[0].filledQuantity, 2)
        self.assertTrue(account.orders[0].status.is_Filled)
        self.assertEqual(account.positions[0].symbol, "GLD")
        self.assertEqual(account.positions[0].quantity, 2)
        self.assertEqual(len(account.ledger), 3)

    def test_cash_movements_allocate_fresh_ledger_ids_by_default(self):
        account = VQC.Deposit(VQC.NewAccount(), 1000)
        account = VQC.Deposit(account, 100)
        account = VQC.Withdraw(account, 50)

        self.assertEqual(
            [entry.ledgerId for entry in account.ledger],
            [1, 2, 3],
        )
        self.assertTrue(VQC.IsValidAccount(account))

    def test_status_update_keeps_orders_as_a_dafny_sequence(self):
        account = VQC.PlaceOrder(
            VQC.NewAccount(),
            VQC.Order(1, "GLD", 1, VQC.OrderSide.BUY, VQC.OrderType.MARKET, VQC.OrderStatus.PENDING, 0),
        )
        account = VQC.SetOrderStatus(account, 1, VQC.OrderStatus.OPEN)
        account = VQC.PlaceOrder(
            account,
            VQC.Order(2, "SLV", 1, VQC.OrderSide.BUY, VQC.OrderType.MARKET, VQC.OrderStatus.PENDING, 0),
        )

        self.assertEqual(len(account.orders), 2)
        self.assertTrue(account.orders[0].status.is_Open)
        self.assertTrue(VQC.IsValidAccount(account))

    def test_full_sell_removes_the_active_position_but_keeps_the_trade(self):
        account = VQC.PlaceOrder(
            VQC.NewAccount(),
            VQC.Order(1, "GLD", 1, VQC.OrderSide.BUY, VQC.OrderType.MARKET, VQC.OrderStatus.PENDING, 0),
        )
        account = VQC.Update(account, VQC.Fill(1, 1, "GLD", 1, 100, 0))
        account = VQC.PlaceOrder(
            account,
            VQC.Order(2, "GLD", 1, VQC.OrderSide.SELL, VQC.OrderType.MARKET, VQC.OrderStatus.PENDING, 0),
        )
        account = VQC.Update(account, VQC.Fill(2, 2, "GLD", 1, 110, 0))

        self.assertEqual(len(account.positions), 0)
        self.assertEqual(len(account.ledger), 2)
        self.assertTrue(account.ledger[1].is_Trade)
        self.assertTrue(VQC.IsValidAccount(account))


if __name__ == "__main__":
    unittest.main(verbosity=2)
