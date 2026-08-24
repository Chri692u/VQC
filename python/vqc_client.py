from __future__ import annotations

import os
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from dotenv import load_dotenv

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest

from vqc_diagnostics import DisplayAccount
from vqc_broker_adapter import AlpacaMoneyToVQCMoney, AlpacaPositionToVQCPosition, AlpacaStatusToVQCStatus, AlpacaOrderToVQCOrder, AlpacaFillToVQCFill
from vqc import VQC

@dataclass
class VQCClient:
    """Small broker boundary around the verified VQC account model."""

    api_key: str | None = None
    secret_key: str | None = None
    url_override: str | None = None
    paper: bool = True
    broker: Any | None = None
    account: Any = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.broker is None:
            self.broker = self.MakeBroker()
        self.account = VQC.NewAccount()
        self.SyncAccountFromBroker()

    def MakeBroker(self) -> TradingClient:
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

    def SyncAccountFromBroker(self) -> None:
        account_info = self.broker.get_account()
        cash = Decimal(str(account_info.cash))
        self.account = VQC.Deposit(self.account, VQC.Money.FromDecimal(cash), 1, 0)

        open_orders = self.broker.get_orders(
            filter=GetOrdersRequest(status=QueryOrderStatus.ALL, limit=500)
        )
        for order_id, broker_order in enumerate(open_orders, start=1):
            vqc_order = AlpacaOrderToVQCOrder(broker_order, order_id=order_id)
            self.account = VQC.PlaceOrder(self.account, vqc_order)

    def NextOrderId(self) -> int:
        if not self.account.orders:
            return 1
        return max(order.orderId for order in self.account.orders) + 1

    def MarketIsOpen(self) -> bool:
        clock = self.broker.get_clock()
        print(
            f"Alpaca clock: timestamp={clock.timestamp}, "
            f"is_open={clock.is_open}, "
            f"next_open={clock.next_open}, "
            f"next_close={clock.next_close}"
        )
        return clock.is_open

    def SubmitOrder(self, symbol: str, quantity: float, side: str) -> Any:
        if not self.MarketIsOpen():
            raise RuntimeError(f"Market is closed; cannot submit {side} order for {symbol} now.")

        order = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )

        vqc_order = VQC.Order(self.NextOrderId(), symbol, int(quantity), side, "market", "new", 0)
        next_account = VQC.PlaceOrder(self.account, vqc_order)
        accepted_account = VQC.SetOrderStatus(next_account, vqc_order.orderId, "accepted") # ?? 

        result = self.broker.submit_order(order_data=order)
        self.account = accepted_account
        return result

    def Buy(self, symbol: str, quantity: float = 1.0) -> Any:
        return self.SubmitOrder(symbol, quantity, "buy")

    def Sell(self, symbol: str, quantity: float = 1.0) -> Any:
        return self.SubmitOrder(symbol, quantity, "sell")

    def __repr__(self) -> str:
        return f"VQCClient(account_cash={self.account.cash})"


if __name__ == "__main__":
    client = VQCClient()
    market_open = client.MarketIsOpen()

    if market_open:
        order = client.Buy("GLD", 1)
        print(f"Submitted buy order: {order}")
    else:
        print("Market is closed.")
        print(DisplayAccount(client.account))
