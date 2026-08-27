"""Self-contained Alpaca implementation of the broker adapter contract."""

from __future__ import annotations

import os
from datetime import datetime
from uuid import uuid4
from typing import Any

from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest
from alpaca.trading.stream import TradingStream

from vqc import VQC
from vqc_utility import VQCUtility


class AlpacaAdapter:
    """Stateless Alpaca-to-VQC conversion functions."""

    @staticmethod
    def ToVQCTimestamp(value: Any) -> int:
        if isinstance(value, datetime):
            return int(value.timestamp())
        if isinstance(value, str):
            return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
        if value is None:
            return 0
        return int(value)

    @staticmethod
    def ToVQCMoney(value: Any) -> Any:
        return VQC.Money.FromDecimal(str(value))

    @staticmethod
    def ToVQCStatus(status: Any) -> str:
        status = getattr(status, "value", status).lower()
        if status in {"new", "pending_new", "pending_cancel", "pending_replace", "done_for_day", "calculated", "held", "stopped"}:
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

    @staticmethod
    def ToVQCPosition(position: Any) -> Any:
        quantity = int(float(position.qty))
        if quantity < 0:
            raise ValueError("VQC currently supports long-only broker positions")
        return VQC.Position(
            position.symbol,
            quantity,
            AlpacaAdapter.ToVQCMoney(position.avg_entry_price or 0),
        )

    @staticmethod
    def ToVQCOrder(
        order: Any,
        order_id: int,
        filled_quantity: int | None = None,
        status: str | None = None,
    ) -> Any:
        side = getattr(getattr(order, "side", "buy"), "value", getattr(order, "side", "buy"))
        quantity = int(float(getattr(order, "qty", 0) or 0))
        filled = int(float(getattr(order, "filled_qty", 0) or 0)) if filled_quantity is None else filled_quantity
        order_status = AlpacaAdapter.ToVQCStatus(getattr(order, "status", "new")) if status is None else status
        return VQC.Order(order_id, order.symbol, quantity, side, "market", order_status, filled)

    @staticmethod
    def ToVQCFill(update: Any, execution_id: int, order_id: int) -> Any:
        broker_order = VQCUtility.GetField(update, "order")
        if broker_order is None:
            raise ValueError("trade update is missing its order")
        return VQC.Fill(
            execution_id,
            order_id,
            VQCUtility.GetField(broker_order, "symbol"),
            int(float(VQCUtility.GetField(update, "qty", 0) or 0)),
            AlpacaAdapter.ToVQCMoney(VQCUtility.GetField(update, "price", 0) or 0),
            AlpacaAdapter.ToVQCTimestamp(VQCUtility.GetField(update, "timestamp")),
        )

    def MakeBroker(self, client: Any) -> TradingClient:
        load_dotenv("KEYS.env")
        client.api_key = client.api_key or os.getenv("ALPACA_API_KEY")
        client.secret_key = client.secret_key or os.getenv("ALPACA_SECRET_KEY")
        client.url_override = (
            client.url_override or os.getenv("ALPACA_BASE_URL") or os.getenv("ALPACA_URL")
        )
        if not client.api_key or not client.secret_key:
            raise RuntimeError("Missing Alpaca credentials in KEYS.env")
        return TradingClient(
            client.api_key, client.secret_key, paper=client.paper, url_override=client.url_override
        )

    def CanStream(self, client: Any) -> bool:
        return bool(client.api_key and client.secret_key)

    def IsMarketOpen(self, broker: Any) -> bool:
        return bool(broker.get_clock().is_open)

    def SubmitOrder(self, broker: Any, symbol: str, quantity: float, side: str) -> Any:
        request = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            client_order_id=str(uuid4()),
        )
        return broker.submit_order(order_data=request)

    def GetCash(self, broker: Any) -> Any:
        return broker.get_account().cash

    def GetPositions(self, broker: Any) -> list[Any]:
        return broker.get_all_positions()

    def GetOpenOrders(self, broker: Any) -> list[Any]:
        return broker.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN, limit=500))

    def GetOrderKey(self, order: Any) -> str:
        return VQCUtility.GetOrderKey(order)

    def GetOrderStatus(self, order: Any) -> str:
        return self.ToVQCStatus(VQCUtility.GetField(order, "status", "new"))

    def GetUpdateEvent(self, update: Any) -> str:
        return str(VQCUtility.GetField(update, "event", "")).lower()

    def GetUpdateOrder(self, update: Any) -> Any:
        return VQCUtility.GetField(update, "order")

    def GetExecutionKey(self, update: Any) -> str:
        execution_id = VQCUtility.GetField(update, "execution_id")
        if execution_id is None:
            raise ValueError("fill update is missing its execution ID")
        return str(execution_id)

    def RunTradeStream(self, client: Any, callback: Any) -> None:
        stream = TradingStream(
            client.api_key, client.secret_key, paper=client.paper, url_override=client.url_override
        )
        stream.subscribe_trade_updates(callback)
        stream.run()


__all__ = ["AlpacaAdapter"]
