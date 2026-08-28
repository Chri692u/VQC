"""Public broker client for verified VQC order and account operations."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from threading import RLock
from typing import Any

from bindings.broker_adapter import (
    BrokerAdapter,
    OrderTimeInForce,
    PriceInput,
)
from bindings.vqc_types import OrderSide, OrderStatus, OrderType
from vqc_daemon import _VQCDaemon
from vqc_utility import Logger

class VQCClient:
    """Submit broker orders while maintaining a verified local account.

    Public attributes:
        broker: Broker SDK client used for direct, broker-specific read access.
        logger: Logger receiving lifecycle, daemon, and reconciliation messages.
        account: Read-only property containing the latest verified VQC snapshot.

    Quantities are whole signed shares: positive quantities buy, negative
    quantities sell, and zero is rejected. Fractional shares are intentionally
    unsupported because the current Dafny model stores quantities as naturals.
    """

    def __init__(
        self,
        env_path: str | Path,
        broker: BrokerAdapter,
        logger: Logger,
        *,
        paper: bool = True,
        start_trade_stream: bool = True,
        broker_client: Any | None = None,
    ) -> None:
        """Create a client and bootstrap its account from the broker.

        ``env_path``, ``broker``, and ``logger`` are explicit dependencies.
        The broker adapter creates its native client from the environment file.
        ``broker_client`` is a keyword-only injection seam for deterministic
        tests. Set ``start_trade_stream=False`` for manual event processing.
        """
        self.env_path = Path(env_path)
        self.broker_adapter = broker
        self.logger = logger
        self._paper = paper
        self._state_lock = RLock()
        self._account: Any = None
        self.broker = (
            broker_client
            if broker_client is not None
            else self.broker_adapter.MakeBroker(self.env_path, self._paper)
        )

        self._daemon = _VQCDaemon(self)
        self._daemon._SyncAccountFromBroker()
        if start_trade_stream and self.broker_adapter.CanStream():
            self._daemon._StartTradeStream()
        elif start_trade_stream:
            raise RuntimeError(
                "trade streaming was requested but the adapter cannot stream; "
                "provide streaming configuration or set start_trade_stream=False"
            )

    @property
    def account(self) -> Any:
        """Return the latest immutable VQC account snapshot."""
        with self._state_lock:
            return self._account

    @staticmethod
    def _order_direction(quantity: int) -> tuple[OrderSide, int]:
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise TypeError("order quantity must be a whole number")
        if quantity == 0:
            raise ValueError("order quantity cannot be zero")
        side = OrderSide.BUY if quantity > 0 else OrderSide.SELL
        return side, abs(quantity)

    @staticmethod
    def _validate_price(name: str, value: PriceInput | None) -> None:
        if value is None:
            raise ValueError(f"{name} is required")
        if isinstance(value, bool):
            raise TypeError(f"{name} must be a positive finite number")
        try:
            price = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise TypeError(f"{name} must be a positive finite number") from error
        if not price.is_finite() or price <= 0:
            raise ValueError(f"{name} must be a positive finite number")

    def _submit_order(
        self,
        symbol: str,
        quantity: int,
        order_type: OrderType,
        limit_price: PriceInput | None = None,
        stop_price: PriceInput | None = None,
        extended_hours: bool = False,
        time_in_force: OrderTimeInForce = OrderTimeInForce.DAY,
    ) -> Any:
        side, absolute_quantity = self._order_direction(quantity)
        if not symbol or not symbol.strip():
            raise ValueError("order symbol cannot be empty")
        identifier = symbol.strip().upper()
        if extended_hours and order_type is not OrderType.LIMIT:
            raise ValueError("extended-hours orders must be limit orders")
        if order_type in {OrderType.LIMIT, OrderType.STOP_LIMIT}:
            self._validate_price("limit_price", limit_price)
        if order_type in {OrderType.STOP, OrderType.STOP_LIMIT}:
            self._validate_price("stop_price", stop_price)

        with self._state_lock:
            if side is OrderSide.SELL:
                self._RequireAvailableToSell(identifier, absolute_quantity)
            result = self.broker_adapter.SubmitOrder(
                self.broker,
                identifier,
                absolute_quantity,
                side,
                order_type,
                limit_price,
                stop_price,
                extended_hours,
                time_in_force,
            )
            self._daemon._TrackSubmittedOrder(result)
            return result

    def _RequireAvailableToSell(self, symbol: str, quantity: int) -> None:
        """Prevent open sell orders from exceeding a verified long position."""
        position = next(
            (
                position
                for position in self._account.positions
                if position.symbol == symbol
            ),
            None,
        )
        position_quantity = 0 if position is None else position.quantity
        reserved_quantity = sum(
            order.quantity - order.filledQuantity
            for order in self._account.orders
            if order.symbol == symbol
            and order.side.is_Sell
            and (
                order.status.is_Pending
                or order.status.is_Open
                or order.status.is_PartiallyFilled
            )
        )
        available_quantity = position_quantity - reserved_quantity
        if quantity > available_quantity:
            raise ValueError(
                f"cannot sell {quantity} {symbol}; only {available_quantity} "
                f"shares are available after reserving {reserved_quantity} "
                "for open sell orders"
            )

    def MarketOrder(
        self,
        symbol: str,
        quantity: int,
        time_in_force: OrderTimeInForce = OrderTimeInForce.DAY,
    ) -> Any:
        """Submit a market order and let the broker determine its eligibility."""
        return self._submit_order(
            symbol, quantity, OrderType.MARKET, time_in_force=time_in_force
        )

    def LimitOrder(
        self,
        symbol: str,
        quantity: int,
        limit_price: PriceInput,
        extended_hours: bool = False,
        time_in_force: OrderTimeInForce = OrderTimeInForce.DAY,
    ) -> Any:
        """Submit a limit order; optionally make it extended-hours eligible."""
        return self._submit_order(
            symbol,
            quantity,
            OrderType.LIMIT,
            limit_price=limit_price,
            extended_hours=extended_hours,
            time_in_force=time_in_force,
        )

    def StopOrder(
        self,
        symbol: str,
        quantity: int,
        stop_price: PriceInput,
        time_in_force: OrderTimeInForce = OrderTimeInForce.DAY,
    ) -> Any:
        """Submit a stop order using signed quantity and a trigger price."""
        return self._submit_order(
            symbol,
            quantity,
            OrderType.STOP,
            stop_price=stop_price,
            time_in_force=time_in_force,
        )

    def StopLimitOrder(
        self,
        symbol: str,
        quantity: int,
        stop_price: PriceInput,
        limit_price: PriceInput,
        time_in_force: OrderTimeInForce = OrderTimeInForce.DAY,
    ) -> Any:
        """Submit a stop-limit order with trigger and execution prices."""
        return self._submit_order(
            symbol,
            quantity,
            OrderType.STOP_LIMIT,
            limit_price=limit_price,
            stop_price=stop_price,
            time_in_force=time_in_force,
        )

    def Liquidate(self, symbol: str) -> Any:
        """Submit a market sell for the full verified long position."""
        normalized_symbol = symbol.strip().upper()
        with self._state_lock:
            position = next(
                (
                    position
                    for position in self._account.positions
                    if position.symbol == normalized_symbol
                ),
                None,
            )
            if position is None:
                raise ValueError(f"no open position for {normalized_symbol}")
            return self.MarketOrder(normalized_symbol, -position.quantity)

    def MarketIsOpen(self) -> bool:
        """Return the configured broker's regular-session market-clock state."""
        return self.broker_adapter.IsMarketOpen(self.broker)

    def __repr__(self) -> str:
        return f"VQCClient(account_cash={self.account.cash})"


__all__ = [
    "OrderTimeInForce",
    "VQCClient",
]
