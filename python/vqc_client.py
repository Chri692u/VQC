"""Public broker client for verified VQC order and account operations."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from threading import RLock
from typing import Any

from bindings.broker_adapter import BrokerAdapter, PriceInput
from bindings.vqc_types import OrderSide, OrderStatus, OrderType
from vqc_daemon import _VQCDaemon
from vqc_utility import Logger


def _default_adapter() -> BrokerAdapter:
    """Load Alpaca lazily so alternate adapters need not import its SDK."""
    from bindings.alpaca_adapter import AlpacaAdapter

    return AlpacaAdapter()


class VQCClient:
    """Submit broker orders while maintaining a verified local account.

    Public attributes:
        broker: Broker SDK client used for direct, broker-specific read access.
        logger: Logger receiving client, validation, and reconciliation messages.
        account: Read-only property containing the latest verified VQC snapshot.

    Quantities are whole signed shares: positive quantities buy, negative
    quantities sell, and zero is rejected. Fractional shares are intentionally
    unsupported because the current Dafny model stores quantities as naturals.
    """

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        url_override: str | None = None,
        paper: bool = True,
        start_trade_stream: bool = True,
        broker: Any | None = None,
        adapter: BrokerAdapter | None = None,
        logger: Logger | None = None,
    ) -> None:
        """Create a client and bootstrap its account from the broker.

        Credentials and ``paper`` configure the default Alpaca adapter. Passing
        both ``broker`` and ``adapter`` allows another broker implementation.
        Set ``start_trade_stream=False`` for deterministic tests or manual event
        processing.
        """
        self.broker = broker
        self.logger = logger or Logger()
        self._api_key = api_key
        self._secret_key = secret_key
        self._url_override = url_override
        self._paper = paper
        self._adapter = adapter or _default_adapter()
        self._state_lock = RLock()
        self._account: Any = None

        if self.broker is None:
            self.broker = self._adapter.MakeBroker(self)

        self._daemon = _VQCDaemon(self)
        self._daemon._SyncAccountFromBroker()
        if start_trade_stream and self._adapter.CanStream(self):
            self._daemon._StartTradeStream()

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
    ) -> Any:
        side, absolute_quantity = self._order_direction(quantity)
        if not symbol or not symbol.strip():
            raise ValueError("order symbol cannot be empty")
        if extended_hours and order_type is not OrderType.LIMIT:
            raise ValueError("extended-hours orders must be limit orders")
        if order_type in {OrderType.LIMIT, OrderType.STOP_LIMIT}:
            self._validate_price("limit_price", limit_price)
        if order_type in {OrderType.STOP, OrderType.STOP_LIMIT}:
            self._validate_price("stop_price", stop_price)

        with self._state_lock:
            if not extended_hours and not self.MarketIsOpen():
                raise RuntimeError(
                    f"[VQC][Client] Market is closed; cannot submit {side.value} "
                    f"order for {symbol} now."
                )
            result = self._adapter.SubmitOrder(
                self.broker,
                symbol.strip().upper(),
                absolute_quantity,
                side,
                order_type,
                limit_price,
                stop_price,
                extended_hours,
            )
            self._daemon._TrackSubmittedOrder(result)
            self.logger.Log(
                "Validation",
                f"Submitted {order_type.value} {side.value} order for "
                f"{symbol.strip().upper()} x {absolute_quantity}.",
            )
            status = self._adapter.GetOrderStatus(result)
            if status not in {
                OrderStatus.NEW,
                OrderStatus.PARTIALLY_FILLED,
                OrderStatus.FILLED,
            }:
                self.logger.Log("Validation", f"Order status is {status.value}.")
            return result

    def MarketOrder(self, symbol: str, quantity: int) -> Any:
        """Submit a regular-session market order using signed quantity."""
        return self._submit_order(symbol, quantity, OrderType.MARKET)

    def LimitOrder(
        self,
        symbol: str,
        quantity: int,
        limit_price: PriceInput,
        extended_hours: bool = False,
    ) -> Any:
        """Submit a limit order; optionally make it extended-hours eligible."""
        return self._submit_order(
            symbol,
            quantity,
            OrderType.LIMIT,
            limit_price=limit_price,
            extended_hours=extended_hours,
        )

    def StopOrder(self, symbol: str, quantity: int, stop_price: PriceInput) -> Any:
        """Submit a stop order using signed quantity and a trigger price."""
        return self._submit_order(
            symbol, quantity, OrderType.STOP, stop_price=stop_price
        )

    def StopLimitOrder(
        self,
        symbol: str,
        quantity: int,
        stop_price: PriceInput,
        limit_price: PriceInput,
    ) -> Any:
        """Submit a stop-limit order with trigger and execution prices."""
        return self._submit_order(
            symbol,
            quantity,
            OrderType.STOP_LIMIT,
            limit_price=limit_price,
            stop_price=stop_price,
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
            open_sell_orders = [
                order
                for order in self._account.orders
                if order.symbol == normalized_symbol
                and order.side.is_Sell
                and (
                    order.status.is_New
                    or order.status.is_Accepted
                    or order.status.is_PartiallyFilled
                )
            ]
            if open_sell_orders:
                raise RuntimeError(
                    f"cannot liquidate {normalized_symbol} while it has open sell orders"
                )
            return self.MarketOrder(normalized_symbol, -position.quantity)

    def MarketIsOpen(self) -> bool:
        """Return the configured broker's regular-session market-clock state."""
        is_open = self._adapter.IsMarketOpen(self.broker)
        self.logger.Log("Client", f"Market is {'open' if is_open else 'closed'}.")
        return is_open

    def __repr__(self) -> str:
        return f"VQCClient(account_cash={self.account.cash})"


__all__ = ["VQCClient"]
