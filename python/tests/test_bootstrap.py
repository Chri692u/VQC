"""Regression tests for creating a VQC account from a broker snapshot."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from alpaca.trading.requests import (
    LimitOrderRequest,
    MarketOrderRequest,
    StopLimitOrderRequest,
    StopOrderRequest,
)

from bindings.alpaca_adapter import AlpacaAdapter
from bindings.vqc_lifecycle import LifecycleUpdate
from vqc import VQC
from vqc_client import OrderTimeInForce, VQCClient as _VQCClient
from vqc_utility import Logger

GLD = "GLD"
SLV = "SLV"
AAPL = "AAPL"


def VQCClient(*, broker, start_trade_stream=True):
    """Construct the explicit production client around a native test broker."""
    return _VQCClient(
        "unused-test.env",
        AlpacaAdapter(),
        Logger(),
        start_trade_stream=start_trade_stream,
        broker_client=broker,
    )


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
                type="market",
            )
        ]

    def get_clock(self):
        return SimpleNamespace(is_open=False)

    def submit_order(self, order_data):
        raise AssertionError("this broker double does not accept submissions")


class SubmissionBroker(SnapshotBroker):
    def __init__(self):
        self.requests = []

    def get_clock(self):
        return SimpleNamespace(is_open=True)

    def submit_order(self, order_data):
        self.requests.append(order_data)
        return SimpleNamespace(
            id=f"submitted-{len(self.requests)}",
            symbol=order_data.symbol,
            side=order_data.side,
            qty=order_data.qty,
            filled_qty="0",
            status="new",
            type=order_data.type,
            limit_price=getattr(order_data, "limit_price", None),
            stop_price=getattr(order_data, "stop_price", None),
        )


class ExtendedHoursBroker(SubmissionBroker):
    def get_clock(self):
        return SimpleNamespace(is_open=False)


class MutableSnapshotBroker(SnapshotBroker):
    def __init__(self):
        self.cash = "1000"

    def get_account(self):
        return SimpleNamespace(cash=self.cash)


class ImmediatelyPartiallyFilledBroker(SubmissionBroker):
    def submit_order(self, order_data):
        result = super().submit_order(order_data)
        result.status = "partially_filled"
        result.filled_qty = "1"
        return result


class FractionalPositionBroker(SnapshotBroker):
    def get_all_positions(self):
        return [SimpleNamespace(symbol="GLD", qty="1.5", avg_entry_price="10")]


class OpenSellOrderBroker(SubmissionBroker):
    def get_orders(self, filter):
        return [
            SimpleNamespace(
                id="open-sell",
                symbol="GLD",
                side="sell",
                qty="1",
                filled_qty="0",
                status="accepted",
                type="market",
            )
        ]


class BootstrapTests(unittest.TestCase):
    def test_cross_border_identifier_and_broker_rejection_are_not_hidden(self):
        broker = SubmissionBroker()
        broker.submit_order = lambda order_data: (_ for _ in ()).throw(
            RuntimeError(f"instrument {order_data.symbol} is not available")
        )
        client = VQCClient(broker=broker, start_trade_stream=False)

        with self.assertRaisesRegex(RuntimeError, "SAP:XETR.*not available"):
            client.MarketOrder("SAP:XETR", 1)

    def test_alpaca_statuses_normalize_without_leaking_broker_enums(self):
        self.assertIs(AlpacaAdapter._ToVQCStatus("pending_new"), VQC.OrderStatus.PENDING)
        self.assertIs(AlpacaAdapter._ToVQCStatus("new"), VQC.OrderStatus.OPEN)
        self.assertIs(
            AlpacaAdapter._ToVQCStatus("pending_cancel"), VQC.OrderStatus.OPEN
        )
        self.assertIs(
            AlpacaAdapter._ToVQCStatus("done_for_day"), VQC.OrderStatus.CANCELLED
        )

    def test_four_core_order_types_are_valid(self):
        price = VQC.Money.FromDecimal("10")
        orders = [
            VQC.Order(1, GLD, 1, order_type=VQC.OrderType.MARKET),
            VQC.Order(2, GLD, 1, order_type=VQC.OrderType.LIMIT, limit_price=price),
            VQC.Order(3, GLD, 1, order_type=VQC.OrderType.STOP, stop_price=price),
            VQC.Order(
                4,
                GLD,
                1,
                order_type=VQC.OrderType.STOP_LIMIT,
                stop_price=price,
                limit_price=price,
            ),
        ]

        self.assertTrue(all(VQC.IsValidOrder(order) for order in orders))
        self.assertTrue(orders[0].orderType.is_Market)
        self.assertTrue(orders[1].orderType.is_Limit)
        self.assertTrue(orders[2].orderType.is_Stop)
        self.assertTrue(orders[3].orderType.is_StopLimit)

    def test_client_submits_all_four_alpaca_order_requests(self):
        broker = SubmissionBroker()
        client = VQCClient(broker=broker, start_trade_stream=False)

        client.MarketOrder(GLD, 1)
        client.LimitOrder(GLD, 1, 10)
        client.StopOrder(GLD, 1, 9)
        client.StopLimitOrder(GLD, 1, 9, 8)

        self.assertEqual(
            [type(request) for request in broker.requests],
            [MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest],
        )
        self.assertEqual(
            [request.side.value for request in broker.requests],
            ["buy", "buy", "buy", "buy"],
        )
        submitted_orders = client.account.orders[-4:]
        self.assertTrue(submitted_orders[0].orderType.is_Market)
        self.assertTrue(submitted_orders[1].orderType.is_Limit)
        self.assertTrue(submitted_orders[2].orderType.is_Stop)
        self.assertTrue(submitted_orders[3].orderType.is_StopLimit)
        self.assertTrue(VQC.IsValidAccount(client.account))

    def test_extended_hours_requires_and_submits_a_limit_order(self):
        broker = ExtendedHoursBroker()
        client = VQCClient(broker=broker, start_trade_stream=False)

        client.LimitOrder(GLD, 1, 10, extended_hours=True)

        self.assertTrue(broker.requests[0].extended_hours)
        with self.assertRaisesRegex(ValueError, "must be limit orders"):
            client._submit_order("GLD", 1, VQC.OrderType.MARKET, extended_hours=True)

    def test_caller_controls_closed_market_submission_policy(self):
        broker = ExtendedHoursBroker()
        client = VQCClient(broker=broker, start_trade_stream=False)

        client.MarketOrder(GLD, 1)

        self.assertEqual(len(broker.requests), 1)
        self.assertFalse(broker.requests[0].extended_hours)

    def test_caller_can_choose_time_in_force(self):
        broker = SubmissionBroker()
        client = VQCClient(broker=broker, start_trade_stream=False)

        client.LimitOrder(
            GLD, 1, 10, time_in_force=OrderTimeInForce.GTC
        )

        self.assertEqual(broker.requests[0].time_in_force.value, "gtc")

    def test_extended_hours_rejects_non_day_duration(self):
        client = VQCClient(
            broker=ExtendedHoursBroker(), start_trade_stream=False
        )

        with self.assertRaisesRegex(ValueError, "require DAY"):
            client.LimitOrder(
                GLD,
                1,
                10,
                extended_hours=True,
                time_in_force=OrderTimeInForce.GTC,
            )

    def test_signed_market_orders_and_liquidation(self):
        broker = SubmissionBroker()
        client = VQCClient(broker=broker, start_trade_stream=False)

        client.MarketOrder(GLD, -1)

        self.assertEqual(broker.requests[0].side.value, "sell")
        self.assertEqual(broker.requests[0].qty, 1)

        liquidation_broker = SubmissionBroker()
        liquidation_client = VQCClient(
            broker=liquidation_broker, start_trade_stream=False
        )
        liquidation_client.Liquidate(GLD)
        self.assertEqual(liquidation_broker.requests[0].side.value, "sell")
        self.assertEqual(liquidation_broker.requests[0].qty, 1)
        with self.assertRaisesRegex(ValueError, "cannot be zero"):
            client.MarketOrder(GLD, 0)
        with self.assertRaisesRegex(ValueError, "no open position"):
            client.Liquidate(AAPL)

    def test_sell_orders_reserve_remaining_position_quantity(self):
        broker = SubmissionBroker()
        client = VQCClient(broker=broker, start_trade_stream=False)

        client.LimitOrder(GLD, -1, 10)

        with self.assertRaisesRegex(ValueError, "only 0 shares are available"):
            client.MarketOrder(GLD, -1)
        self.assertEqual(len(broker.requests), 1)

    def test_sell_without_a_verified_position_is_rejected(self):
        broker = SubmissionBroker()
        client = VQCClient(broker=broker, start_trade_stream=False)

        with self.assertRaisesRegex(ValueError, "only 0 shares are available"):
            client.MarketOrder(SLV, -1)
        self.assertEqual(broker.requests, [])

    def test_fractional_quantities_are_rejected_instead_of_truncated(self):
        client = VQCClient(broker=SubmissionBroker(), start_trade_stream=False)

        with self.assertRaisesRegex(TypeError, "whole number"):
            client.MarketOrder(GLD, 1.5)
        with self.assertRaisesRegex(ValueError, "whole number"):
            VQCClient(broker=FractionalPositionBroker(), start_trade_stream=False)

    def test_order_prices_are_validated_before_broker_submission(self):
        broker = SubmissionBroker()
        client = VQCClient(broker=broker, start_trade_stream=False)

        for invalid_price in (0, -1, float("nan"), float("inf")):
            with self.assertRaisesRegex(ValueError, "positive finite"):
                client.LimitOrder(GLD, 1, invalid_price)
        with self.assertRaisesRegex(TypeError, "positive finite"):
            client.StopOrder(GLD, 1, True)

        self.assertEqual(broker.requests, [])

    def test_liquidate_rejects_duplicate_open_sell_exposure(self):
        broker = OpenSellOrderBroker()
        client = VQCClient(broker=broker, start_trade_stream=False)

        with self.assertRaisesRegex(ValueError, "only 0 shares are available"):
            client.Liquidate(GLD)
        self.assertEqual(broker.requests, [])

    def test_submit_response_does_not_apply_unpriced_cumulative_fills(self):
        broker = ImmediatelyPartiallyFilledBroker()
        client = VQCClient(broker=broker, start_trade_stream=False)

        result = client.MarketOrder(SLV, 2)
        submitted = client.account.orders[-1]

        self.assertTrue(submitted.status.is_Pending)
        self.assertEqual(submitted.filledQuantity, 0)

        client._daemon._HandleTradeUpdate(
            SimpleNamespace(
                event="partial_fill",
                execution_id="execution-after-submit",
                qty="1",
                price="11",
                timestamp="2026-08-24T12:00:00Z",
                order=result,
            )
        )

        self.assertEqual(client.account.orders[-1].filledQuantity, 1)
        self.assertTrue(client.account.orders[-1].status.is_PartiallyFilled)

    def test_requested_unavailable_stream_is_not_silently_disabled(self):
        with self.assertRaisesRegex(RuntimeError, "cannot stream"):
            VQCClient(broker=SnapshotBroker())

    def test_client_owns_state_synchronized_by_daemon(self):
        client = VQCClient(broker=SnapshotBroker(), start_trade_stream=False)

        self.assertEqual(client.account.cash, VQC.Money.FromDecimal("1000"))
        self.assertEqual(client._daemon._order_ids, {"broker-order-1": 1})
        self.assertTrue(VQC.IsValidAccount(client.account))

    def test_bootstrap_preserves_the_broker_snapshot(self):
        cash = VQC.Money.FromDecimal("-25.50")
        position = VQC.Position(GLD, 2, VQC.Money.FromDecimal("10"))
        order = VQC.Order(1, GLD, 2, VQC.OrderSide.BUY, VQC.OrderType.MARKET, VQC.OrderStatus.OPEN, 0)

        account = VQC.Bootstrap(cash, [position], [order], ledger_id=7, timestamp=9)

        self.assertEqual(account.cash, cash)
        self.assertEqual(len(account.positions), 1)
        self.assertEqual(len(account.orders), 1)
        self.assertEqual(len(account.ledger), 1)
        self.assertTrue(account.ledger[0].is_Opening)
        self.assertEqual(account.ledger[0].cash, cash)
        self.assertEqual(account.ledger[0].positions[0], position)
        self.assertEqual(account.ledger[0].orders[0], order)
        self.assertEqual(account.ledger[0].timestamp, 9)
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

        client._daemon._HandleTradeUpdate(update)

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

        client._daemon._HandleTradeUpdate(update)

        self.assertEqual(len(client.account.orders), 1)
        self.assertTrue(VQC.IsValidAccount(client.account))

    def test_stream_interruption_refreshes_broker_state_before_stopping(self):
        broker = MutableSnapshotBroker()
        client = VQCClient(broker=broker, start_trade_stream=False)
        stream_calls = 0

        def interrupted(*_):
            nonlocal stream_calls
            stream_calls += 1
            if stream_calls == 1:
                broker.cash = "900"
                raise ConnectionError("stream disconnected")
            client._daemon._stop_event.set()

        with patch.object(
            client.broker_adapter, "RunTradeStream", side_effect=interrupted
        ):
            client._daemon._RunTradeStream()

        self.assertEqual(client.account.cash, VQC.Money.FromDecimal("900"))
        self.assertEqual(stream_calls, 2)
        self.assertIsInstance(client._daemon._stream_error, ConnectionError)
        self.assertTrue(VQC.IsValidAccount(client.account))

    def test_stream_stays_stopped_until_snapshot_recovery_succeeds(self):
        broker = MutableSnapshotBroker()
        client = VQCClient(broker=broker, start_trade_stream=False)
        original_get_account = broker.get_account
        refresh_attempts = 0
        stream_calls = 0

        def sometimes_failing_account():
            nonlocal refresh_attempts
            refresh_attempts += 1
            if refresh_attempts <= 2:
                raise ConnectionError("snapshot unavailable")
            broker.cash = "800"
            return original_get_account()

        def interrupted(*_):
            nonlocal stream_calls
            stream_calls += 1
            if stream_calls == 1:
                raise ConnectionError("stream disconnected")
            client._daemon._stop_event.set()

        broker.get_account = sometimes_failing_account
        with (
            patch.object(
                client.broker_adapter, "RunTradeStream", side_effect=interrupted
            ),
            patch.object(client._daemon._stop_event, "wait", return_value=False),
        ):
            client._daemon._RunTradeStream()

        self.assertEqual(refresh_attempts, 3)
        self.assertEqual(stream_calls, 2)
        self.assertEqual(client.account.cash, VQC.Money.FromDecimal("800"))

    def test_client_applies_a_non_fill_lifecycle_event(self):
        client = VQCClient(broker=SnapshotBroker(), start_trade_stream=False)
        update = SimpleNamespace(
            event="canceled",
            order=SimpleNamespace(
                id="broker-order-1",
                symbol="GLD",
                side="buy",
                qty="2",
                filled_qty="0",
                status="canceled",
            ),
        )

        client._daemon._HandleTradeUpdate(update)

        self.assertTrue(client.account.orders[0].status.is_Cancelled)
        self.assertTrue(VQC.IsValidAccount(client.account))

    def test_client_applies_and_reports_a_rejection_reason(self):
        client = VQCClient(broker=SnapshotBroker(), start_trade_stream=False)
        update = SimpleNamespace(
            event="rejected",
            reason="insufficient buying power",
            order=SimpleNamespace(
                id="broker-order-1",
                symbol="GLD",
                side="buy",
                qty="2",
                filled_qty="0",
                status="rejected",
            ),
        )

        client._daemon._HandleTradeUpdate(update)

        self.assertTrue(client.account.orders[0].status.is_Rejected)
        self.assertEqual(len(client.account.ledger), 1)
        self.assertTrue(VQC.IsValidAccount(client.account))

    def test_lifecycle_path_refuses_unpriced_fill_statuses(self):
        client = VQCClient(broker=SnapshotBroker(), start_trade_stream=False)
        update = LifecycleUpdate(
            order_key="broker-order-1",
            status=VQC.OrderStatus.PARTIALLY_FILLED,
            event="partial_fill",
        )

        with self.assertRaisesRegex(ValueError, "without execution economics"):
            client._daemon._ApplyLifecycleUpdate(update)


if __name__ == "__main__":
    unittest.main(verbosity=2)
