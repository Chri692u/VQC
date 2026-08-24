"""Regression tests for creating a VQC account from a broker snapshot."""

from types import SimpleNamespace
import unittest

from vqc import VQC
from vqc_client import VQCClient


class SnapshotBroker:
    """Small broker double containing a cash balance, one position, and one order."""

    def get_account(self):
        return SimpleNamespace(cash="1000")

    def get_all_positions(self):
        return [SimpleNamespace(symbol="GLD", qty="1", avg_entry_price="10")]

    def get_orders(self, filter):
        return [
            SimpleNamespace(
                id="broker-order-1",
                symbol="GLD",
                side="buy",
                qty="2",
                filled_qty="0",
                status="accepted",
            )
        ]


class BootstrapTests(unittest.TestCase):
    def test_bootstrap_preserves_the_broker_snapshot(self):
        cash = VQC.Money.FromDecimal("-25.50")
        position = VQC.Position("GLD", 2, VQC.Money.FromDecimal("10"))
        order = VQC.Order(1, "GLD", 2, "buy", "market", "accepted", 0)

        account = VQC.Bootstrap(cash, [position], [order], ledger_id=7, timestamp=9)

        self.assertEqual(account.cash, cash)
        self.assertEqual(len(account.positions), 1)
        self.assertEqual(len(account.orders), 1)
        self.assertEqual(len(account.ledger), 1)
        self.assertTrue(account.ledger[0].is_Opening)
        self.assertTrue(VQC.IsValidAccount(account))

    def test_client_bootstraps_then_applies_a_subsequent_fill(self):
        client = VQCClient(broker=SnapshotBroker(), start_trade_stream=False)
        update = SimpleNamespace(
            event="partial_fill",
            execution_id="broker-execution-1",
            qty="1",
            price="11",
            timestamp="2026-08-24T12:00:00Z",
            order=SimpleNamespace(
                id="broker-order-1",
                symbol="GLD",
                side="buy",
                qty="2",
                filled_qty="1",
                status="partially_filled",
            ),
        )

        client.HandleTradeUpdate(update)

        self.assertEqual(client.account.orders[0].filledQuantity, 1)
        self.assertTrue(client.account.orders[0].status.is_PartiallyFilled)
        self.assertEqual(client.account.positions[0].quantity, 2)
        self.assertEqual(len(client.account.ledger), 2)
        self.assertTrue(VQC.IsValidAccount(client.account))

    def test_client_refreshes_when_a_broker_event_is_untracked(self):
        client = VQCClient(broker=SnapshotBroker(), start_trade_stream=False)
        update = SimpleNamespace(
            event="new",
            order=SimpleNamespace(
                id="untracked-broker-order",
                symbol="SLV",
                side="buy",
                qty="1",
                filled_qty="0",
                status="new",
            ),
        )

        client.HandleTradeUpdate(update)

        self.assertEqual(len(client.account.orders), 1)
        self.assertTrue(VQC.IsValidAccount(client.account))


if __name__ == "__main__":
    unittest.main(verbosity=2)
