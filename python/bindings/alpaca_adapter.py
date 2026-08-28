"""Self-contained Alpaca implementation of the broker adapter contract."""

from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import (
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
    StopLimitOrderRequest,
    StopOrderRequest,
)
from alpaca.trading.stream import TradingStream

from vqc import VQC
from bindings.broker_adapter import PriceInput, TradeUpdateKind
from bindings.vqc_types import OrderSide as VQCOrderSide
from bindings.vqc_types import OrderStatus, OrderType as VQCOrderType
from vqc_utility import VQCUtility
from bindings.vqc_lifecycle import LifecycleUpdate


class AlpacaAdapter:
    """Stateless Alpaca-to-VQC conversion functions."""

    @staticmethod
    def _ToVQCTimestamp(value: Any) -> int:
        if isinstance(value, datetime):
            return int(value.timestamp())
        if isinstance(value, str):
            return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
        if value is None:
            return 0
        return int(value)

    @staticmethod
    def _ToVQCMoney(value: Any) -> Any:
        return VQC.Money.FromDecimal(str(value))

    @staticmethod
    def _ToWholeQuantity(value: Any, label: str, allow_zero: bool = False) -> int:
        """Convert broker quantities without silently truncating fractions."""
        try:
            quantity = Decimal(str(value))
        except (InvalidOperation, ValueError) as error:
            raise ValueError(f"{label} has invalid quantity {value!r}") from error
        if not quantity.is_finite() or quantity != quantity.to_integral_value():
            raise ValueError(f"{label} quantity must be a whole number, got {value!r}")
        result = int(quantity)
        if result < 0 or (result == 0 and not allow_zero):
            raise ValueError(f"{label} quantity must be {'non-negative' if allow_zero else 'positive'}")
        return result

    @staticmethod
    def _ToVQCStatus(status: Any) -> OrderStatus:
        status = str(getattr(status, "value", status)).lower()
        if status in {"pending_new", "pending_review"}:
            return OrderStatus.PENDING
        if status in {
            "new",
            "accepted",
            "accepted_for_bidding",
            "pending_cancel",
            "pending_replace",
            "held",
            "stopped",
            "suspended",
        }:
            return OrderStatus.OPEN
        if status in {"partially_filled", "partial_fill"}:
            return OrderStatus.PARTIALLY_FILLED
        if status == "filled":
            return OrderStatus.FILLED
        if status in {"canceled", "cancelled", "expired", "done_for_day", "replaced", "calculated"}:
            return OrderStatus.CANCELLED
        if status == "rejected":
            return OrderStatus.REJECTED
        raise ValueError(f"unsupported Alpaca order status: {status}")

    @staticmethod
    def ToVQCPosition(position: Any) -> Any:
        """Convert a whole, long Alpaca position into a VQC position."""
        raw_quantity = VQCUtility.RequireField(position, "qty", "broker position")
        if Decimal(str(raw_quantity)) < 0:
            raise ValueError("VQC currently supports long-only broker positions")
        quantity = AlpacaAdapter._ToWholeQuantity(raw_quantity, "broker position")
        return VQC.Position(
            VQCUtility.RequireField(position, "symbol", "broker position"),
            quantity,
            AlpacaAdapter._ToVQCMoney(
                VQCUtility.RequireField(position, "avg_entry_price", "broker position")
            ),
        )

    @staticmethod
    def ToVQCOrder(
        order: Any,
        order_id: int,
        filled_quantity: int | None = None,
        status: OrderStatus | None = None,
    ) -> Any:
        """Convert an Alpaca order without losing type, prices, or status."""
        raw_side = VQCUtility.RequireField(order, "side", "broker order")
        side_value = getattr(raw_side, "value", raw_side)
        side = VQCOrderSide(side_value)
        quantity = AlpacaAdapter._ToWholeQuantity(
            VQCUtility.RequireField(order, "qty", "broker order"), "broker order"
        )
        filled = (
            AlpacaAdapter._ToWholeQuantity(
                VQCUtility.RequireField(order, "filled_qty", "broker order"),
                "broker filled",
                allow_zero=True,
            )
            if filled_quantity is None
            else filled_quantity
        )
        order_status = (
            AlpacaAdapter._ToVQCStatus(VQCUtility.RequireField(order, "status", "broker order"))
            if status is None
            else status
        )
        if filled == quantity:
            order_status = OrderStatus.FILLED
        elif filled > 0 and order_status in {OrderStatus.PENDING, OrderStatus.OPEN}:
            order_status = OrderStatus.PARTIALLY_FILLED
        raw_order_type = VQCUtility.RequireField(order, "type", "broker order")
        order_type_value = getattr(raw_order_type, "value", raw_order_type)
        order_type = VQCOrderType(order_type_value)
        limit_price = getattr(order, "limit_price", None)
        stop_price = getattr(order, "stop_price", None)
        return VQC.Order(
            order_id,
            VQCUtility.RequireField(order, "symbol", "broker order"),
            quantity,
            side,
            order_type,
            order_status,
            filled,
            AlpacaAdapter._ToVQCMoney(limit_price) if limit_price is not None else None,
            AlpacaAdapter._ToVQCMoney(stop_price) if stop_price is not None else None,
        )

    @staticmethod
    def ToVQCFill(update: Any, execution_id: int, order_id: int) -> Any:
        """Convert one priced Alpaca execution update into a VQC fill."""
        broker_order = VQCUtility.RequireField(update, "order", "trade update")
        return VQC.Fill(
            execution_id,
            order_id,
            VQCUtility.RequireField(broker_order, "symbol", "broker order"),
            AlpacaAdapter._ToWholeQuantity(
                VQCUtility.RequireField(update, "qty", "trade update"), "trade fill"
            ),
            AlpacaAdapter._ToVQCMoney(
                VQCUtility.RequireField(update, "price", "trade update")
            ),
            AlpacaAdapter._ToVQCTimestamp(
                VQCUtility.RequireField(update, "timestamp", "trade update")
            ),
        )

    def MakeBroker(self, client: Any) -> TradingClient:
        """Create an Alpaca trading client from VQC configuration or environment."""
        load_dotenv("KEYS.env")
        client._api_key = client._api_key or os.getenv("ALPACA_API_KEY")
        client._secret_key = client._secret_key or os.getenv("ALPACA_SECRET_KEY")
        client._url_override = (
            client._url_override or os.getenv("ALPACA_BASE_URL") or os.getenv("ALPACA_URL")
        )
        if not client._api_key or not client._secret_key:
            raise RuntimeError("Missing Alpaca credentials in KEYS.env")
        return TradingClient(
            client._api_key,
            client._secret_key,
            paper=client._paper,
            url_override=client._url_override,
        )

    def CanStream(self, client: Any) -> bool:
        """Return whether Alpaca streaming credentials are available."""
        return bool(client._api_key and client._secret_key)

    def IsMarketOpen(self, broker: Any) -> bool:
        """Return Alpaca's regular-session clock state."""
        return bool(broker.get_clock().is_open)

    def SubmitOrder(
        self,
        broker: Any,
        symbol: str,
        quantity: int,
        side: VQCOrderSide,
        order_type: VQCOrderType,
        limit_price: PriceInput | None,
        stop_price: PriceInput | None,
        extended_hours: bool,
    ) -> Any:
        """Build and submit one of VQC's four supported Alpaca order types."""
        if extended_hours and order_type is not VQCOrderType.LIMIT:
            raise ValueError("extended-hours orders must be limit orders")
        arguments = dict(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.BUY if side is VQCOrderSide.BUY else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            client_order_id=str(uuid4()),
            extended_hours=extended_hours,
        )
        if order_type is VQCOrderType.MARKET:
            request = MarketOrderRequest(**arguments)
        elif order_type is VQCOrderType.LIMIT:
            if limit_price is None:
                raise ValueError("limit order requires a limit_price")
            request = LimitOrderRequest(**arguments, limit_price=limit_price)
        elif order_type is VQCOrderType.STOP:
            if stop_price is None:
                raise ValueError("stop order requires a stop_price")
            request = StopOrderRequest(**arguments, stop_price=stop_price)
        elif order_type is VQCOrderType.STOP_LIMIT:
            if stop_price is None or limit_price is None:
                raise ValueError("stop-limit order requires stop_price and limit_price")
            request = StopLimitOrderRequest(
                **arguments, stop_price=stop_price, limit_price=limit_price
            )
        else:
            raise ValueError(f"unsupported order type: {order_type}")
        return broker.submit_order(order_data=request)

    def GetCash(self, broker: Any) -> Any:
        """Return Alpaca account cash in major currency units."""
        return broker.get_account().cash

    def GetPositions(self, broker: Any) -> list[Any]:
        """Return Alpaca's open positions."""
        return broker.get_all_positions()

    def GetOpenOrders(self, broker: Any) -> list[Any]:
        """Return up to Alpaca's 500 open-order response limit."""
        return broker.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN, limit=500))

    def GetOrderKey(self, order: Any) -> str:
        """Return Alpaca's UUID order identifier as text."""
        return VQCUtility.GetOrderKey(order)

    def GetOrderStatus(self, order: Any) -> OrderStatus:
        """Normalize Alpaca status and cumulative fill state into VQC."""
        status = self._ToVQCStatus(
            VQCUtility.RequireField(order, "status", "broker order")
        )
        quantity = self._ToWholeQuantity(
            VQCUtility.RequireField(order, "qty", "broker order"), "broker order"
        )
        filled = self._ToWholeQuantity(
            VQCUtility.RequireField(order, "filled_qty", "broker order"),
            "broker filled",
            allow_zero=True,
        )
        if filled == quantity:
            return OrderStatus.FILLED
        if filled > 0 and status in {OrderStatus.PENDING, OrderStatus.OPEN}:
            return OrderStatus.PARTIALLY_FILLED
        return status

    def GetUpdateKind(self, update: Any) -> TradeUpdateKind:
        """Classify Alpaca fill events separately from lifecycle events."""
        raw_event = VQCUtility.RequireField(update, "event", "trade update")
        event = getattr(raw_event, "value", raw_event)
        return (
            TradeUpdateKind.FILL
            if str(event).lower() in {"partial_fill", "fill"}
            else TradeUpdateKind.LIFECYCLE
        )

    def GetUpdateOrder(self, update: Any) -> Any:
        """Return the order embedded in an Alpaca trade update."""
        return VQCUtility.RequireField(update, "order", "trade update")

    def GetUpdateEvent(self, update: Any) -> Any:
        """Return the Alpaca trade-update event name."""
        return VQCUtility.RequireField(update, "event", "trade update")

    def ToLifecycleUpdate(self, update: Any) -> LifecycleUpdate:
        """Normalize an Alpaca non-fill event, retaining diagnostic context."""
        broker_order = self.GetUpdateOrder(update)
        raw_event = self.GetUpdateEvent(update)
        event = str(getattr(raw_event, "value", raw_event)).lower()
        status = (
            OrderStatus.PENDING
            if event in {"pending_new", "pending_review"}
            else OrderStatus.OPEN
            if event in {"new", "accepted", "accepted_for_bidding"}
            else self.GetOrderStatus(broker_order)
        )
        reason = next(
            (
                str(value)
                for value in (
                    VQCUtility.GetField(update, "reason"),
                    VQCUtility.GetField(update, "message"),
                    VQCUtility.GetField(broker_order, "reject_reason"),
                )
                if value
            ),
            None,
        )
        return LifecycleUpdate(
            order_key=self.GetOrderKey(broker_order),
            status=status,
            event=event,
            reason=reason,
        )

    def GetExecutionKey(self, update: Any) -> str:
        """Return Alpaca's execution UUID for fill deduplication."""
        execution_id = VQCUtility.GetField(update, "execution_id")
        if execution_id is None:
            raise ValueError("fill update is missing its execution ID")
        return str(execution_id)

    def RunTradeStream(self, client: Any, callback: Any) -> None:
        """Run Alpaca's account trade-update WebSocket until it stops."""
        stream = TradingStream(
            client._api_key,
            client._secret_key,
            paper=client._paper,
            url_override=client._url_override,
        )
        stream.subscribe_trade_updates(callback)
        stream.run()


__all__ = ["AlpacaAdapter"]
