from __future__ import annotations

import os
from dataclasses import dataclass, field
from decimal import Decimal
from threading import Thread
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest
from alpaca.trading.stream import TradingStream

from vqc_broker_adapter import BrokerAdapter
from vqc_utility import VQCUtility
from vqc import VQC

@dataclass
class VQCClient:
    """Small broker boundary around the verified VQC account model."""

    api_key: str | None = None
    secret_key: str | None = None
    url_override: str | None = None
    paper: bool = True
    start_trade_stream: bool = True
    broker: Any | None = None
    account: Any = field(default=None, init=False)
    order_ids: dict[str, int] = field(default_factory=dict, init=False)
    fill_ids: dict[str, int] = field(default_factory=dict, init=False)
    trade_stream_thread: Thread | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.broker is None:
            self.broker = self.MakeBroker()
        self.SyncAccountFromBroker()
        if self.start_trade_stream and self.api_key and self.secret_key:
            self.StartTradeStream()

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
        """Create one trusted VQC opening snapshot from current broker state."""
        account_info = self.broker.get_account()
        cash = Decimal(str(account_info.cash))
        broker_positions = self.broker.get_all_positions()
        positions = [BrokerAdapter.ToVQCPosition(position) for position in broker_positions]
        broker_orders = self.broker.get_orders(
            filter=GetOrdersRequest(status=QueryOrderStatus.OPEN, limit=500)
        )
        orders = [
            BrokerAdapter.ToVQCOrder(broker_order, order_id)
            for order_id, broker_order in enumerate(broker_orders, start=1)
        ]
        self.account = VQC.Bootstrap(VQC.Money.FromDecimal(cash), positions, orders)
        self.order_ids = {
            VQCUtility.GetOrderKey(broker_order): order_id
            for order_id, broker_order in enumerate(broker_orders, start=1)
        }
        print("[VQC][Client] Bootstrapped account from broker state.")

    def NextOrderId(self) -> int:
        return VQCUtility.NextOrderId(self.account.orders)

    def _SetOrderStatus(self, broker_order: Any) -> None:
        """Apply a non-execution lifecycle event reported by the broker."""
        vqc_order_id = self.order_ids[VQCUtility.GetOrderKey(broker_order)]
        status = BrokerAdapter.ToVQCStatus(VQCUtility.GetField(broker_order, "status", "new"))
        if status in {"partially_filled", "filled"}:
            raise ValueError("filled broker orders must be applied through a fill event")
        self.account = VQC.SetOrderStatus(self.account, vqc_order_id, status)

    def HandleTradeUpdate(self, update: Any) -> None:
        """Apply one Alpaca trade-update event to the verified account.

        Only ``partial_fill`` and ``fill`` events call VQC.Update. All other
        lifecycle events only change the order status.
        """
        event = str(VQCUtility.GetField(update, "event", "")).lower()
        broker_order = VQCUtility.GetField(update, "order")
        if broker_order is None:
            raise ValueError("trade update is missing its order")

        broker_order_key = VQCUtility.GetOrderKey(broker_order)
        if broker_order_key not in self.order_ids:
            raise ValueError(f"untracked broker order: {broker_order_key}")

        if event not in {"partial_fill", "fill"}:
            self._SetOrderStatus(broker_order)
            return

        external_execution_id = VQCUtility.GetField(update, "execution_id")
        if external_execution_id is None:
            raise ValueError("fill update is missing its execution ID")
        if str(external_execution_id) in self.fill_ids:
            return

        vqc_order_id = self.order_ids[broker_order_key]
        vqc_fill = BrokerAdapter.ToVQCFill(
            update,
            execution_id=VQCUtility.GetOrAddId(self.fill_ids, external_execution_id, "fill"),
            order_id=vqc_order_id,
        )
        self.account = VQC.Update(self.account, vqc_fill)

    async def OnTradeUpdate(self, update: Any) -> None:
        """Async callback suitable for TradingStream.subscribe_trade_updates."""
        self.HandleTradeUpdate(update)

    def RunTradeStream(self) -> None:
        """Run Alpaca's trade-update stream; call this before submitting orders."""
        if not self.api_key or not self.secret_key:
            raise RuntimeError("Alpaca credentials are required to run the trade stream")
        stream = TradingStream(
            self.api_key,
            self.secret_key,
            paper=self.paper,
            url_override=self.url_override,
        )
        stream.subscribe_trade_updates(self.OnTradeUpdate)
        stream.run()

    def StartTradeStream(self) -> None:
        """Start the broker event stream once, without blocking the caller."""
        if self.trade_stream_thread and self.trade_stream_thread.is_alive():
            return
        self.trade_stream_thread = Thread(
            target=self.RunTradeStream,
            name="vqc-alpaca-trade-stream",
            daemon=True,
        )
        self.trade_stream_thread.start()

    def MarketIsOpen(self) -> bool:
        clock = self.broker.get_clock()
        print(f"[VQC][Client] Market is {'open' if clock.is_open else 'closed'}.")
        return clock.is_open

    def SubmitOrder(self, symbol: str, quantity: float, side: str) -> Any:
        if not self.MarketIsOpen():
            raise RuntimeError(f"[VQC][Client] Market is closed; cannot submit {side} order for {symbol} now.")

        client_order_id = str(uuid4())
        order = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            client_order_id=client_order_id,
        )

        result = self.broker.submit_order(order_data=order)
        vqc_order_id = self.NextOrderId()
        self.order_ids[VQCUtility.GetOrderKey(result)] = vqc_order_id
        vqc_order = VQC.Order(vqc_order_id, symbol, int(quantity), side, "market", "new", 0)
        self.account = VQC.PlaceOrder(self.account, vqc_order)
        print(f"[VQC][Validation] Submitted {side} order for {symbol} x {quantity}.")
        result_status = BrokerAdapter.ToVQCStatus(VQCUtility.GetField(result, "status", "new"))
        if result_status not in {"new", "partially_filled", "filled"}:
            print(f"[VQC][Validation] Order status is {result_status}")
            self._SetOrderStatus(result)
        return result

    def Buy(self, symbol: str, quantity: float = 1.0) -> Any:
        return self.SubmitOrder(symbol, quantity, "buy")

    def Sell(self, symbol: str, quantity: float = 1.0) -> Any:
        return self.SubmitOrder(symbol, quantity, "sell")

    def __repr__(self) -> str:
        return f"VQCClient(account_cash={self.account.cash})"


if __name__ == "__main__":
    client = VQCClient()
    try:
        client.Buy("GLD", 1)
    except RuntimeError as error:
        print(f"[VQC][Client] No order submitted: {error}")
