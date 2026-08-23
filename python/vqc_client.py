from __future__ import annotations

import os
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from dotenv import load_dotenv

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest

from vqc_bindings import VQC


def alpaca_money_to_vqc_money(value):
    return VQC.Money.from_decimal(str(value))


def alpaca_position_to_vqc_position(position):
    return VQC.Position(
        position.symbol,
        int(float(position.qty)),
        alpaca_money_to_vqc_money(position.avg_entry_price or 0),
    )


def alpaca_status_to_vqc_status(status) -> str:
    status = getattr(status, "value", status).lower()
    if status in {
        "new",
        "pending_new",
        "pending_cancel",
        "pending_replace",
        "done_for_day",
        "calculated",
        "held",
        "stopped",
    }:
        return "new"
    if status == "accepted":
        return "accepted"
    if status in {"partially_filled", "partial_fill"}:
        return "partially_filled"
    if status == "filled":
        return "filled"
    if status in {"canceled", "cancelled", "expired"}:
        return "cancelled"
    if status == "rejected":
        return "rejected"
    raise ValueError(f"unsupported Alpaca order status: {status}")


def alpaca_order_to_vqc_order(
    order,
    order_id: int = 1,
    filled_quantity: int | None = None,
    status: str | None = None,
):
    side = getattr(getattr(order, "side", "buy"), "value", getattr(order, "side", "buy"))
    filled_quantity = (
        int(float(getattr(order, "filled_qty", 0) or 0))
        if filled_quantity is None
        else filled_quantity
    )
    status = (
        alpaca_status_to_vqc_status(getattr(order, "status", "new"))
        if status is None
        else status
    )
    return VQC.Order(
        order_id,
        order.symbol,
        int(float(getattr(order, "qty", 0) or 0)),
        side,
        "market",
        status,
        filled_quantity,
    )


def alpaca_fill_to_vqc_fill(fill, execution_id: int = 1, order_id: int = 1):
    return VQC.Fill(
        execution_id,
        order_id,
        fill.symbol,
        int(float(getattr(fill, "qty", 0) or 0)),
        alpaca_money_to_vqc_money(getattr(fill, "price", 0) or 0),
        0,
    )


@dataclass
class VQCClient:
    """Minimal VQC-boundary client.

    This is intentionally small: it initializes the VQC account state from the
    broker view, validates internal trade rules before external execution, and
    exposes the tiny API needed for testing and experimentation.
    """

    api_key: str | None = None
    secret_key: str | None = None
    url_override: str | None = None
    paper: bool = True
    broker: Any | None = None
    account: Any = field(default=None, init=False)

    def __post_init__(self):
        if self.broker is None:
            self.broker = self._make_broker()
        self.account = VQC.NewAccount()
        self._sync_account_from_broker()

    def _make_broker(self) -> TradingClient:
        load_dotenv("KEYS.env")
        self.api_key = self.api_key or os.getenv("ALPACA_API_KEY")
        self.secret_key = self.secret_key or os.getenv("ALPACA_SECRET_KEY")
        self.url_override = self.url_override or os.getenv("ALPACA_BASE_URL") or os.getenv("ALPACA_URL")
        if not self.api_key or not self.secret_key:
            raise RuntimeError("Missing Alpaca credentials in KEYS.env")
        return TradingClient(
            self.api_key,
            self.secret_key,
            paper=self.paper,
            url_override=self.url_override,
        )

    def _sync_account_from_broker(self):
        acct = self.broker.get_account()
        cash = Decimal(str(acct.cash))
        self.account = VQC.Deposit(self.account, VQC.Money.from_decimal(cash), 1, 0)

        open_orders = self.broker.get_orders(
            filter=GetOrdersRequest(status=QueryOrderStatus.ALL, limit=500)
        )
        for order_id, broker_order in enumerate(open_orders, start=1):
            vqc_order = alpaca_order_to_vqc_order(broker_order, order_id=order_id)
            self.account = VQC.PlaceOrder(self.account, vqc_order)

    def _next_order_id(self) -> int:
        if not self.account.orders:
            return 1
        return max(order.orderId for order in self.account.orders) + 1

    def market_is_open(self) -> bool:
        return bool(self.broker.get_clock().is_open)

    def submit_order(self, symbol: str, qty: float, side: str):
        if not self.market_is_open():
            raise RuntimeError(f"Market is closed; cannot submit {side} order for {symbol} now.")

        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )

        # Validate the transition before sending anything to the broker.
        vqc_order = VQC.Order(self._next_order_id(), symbol, int(qty), side, "market", "new", 0)
        next_account = VQC.PlaceOrder(self.account, vqc_order)
        accepted_account = VQC.SetOrderStatus(next_account, vqc_order.orderId, "accepted")

        result = self.broker.submit_order(order_data=order)
        self.account = accepted_account
        return result

    def buy(self, symbol: str, qty: float = 1.0):
        return self.submit_order(symbol, qty, "buy")

    def sell(self, symbol: str, qty: float = 1.0):
        return self.submit_order(symbol, qty, "sell")

    def __repr__(self) -> str:
        return f"VQCClient(account_cash={self.account.cash})"


if __name__ == "__main__":
    client = VQCClient()
    market_open = client.market_is_open()

    if market_open:
        order = client.buy("GLD", 1)
        print(f"Submitted buy order: {order}")
    else:
        print("Market is closed.")
        print(VQC.display_account(client.account))
