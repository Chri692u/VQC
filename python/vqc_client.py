from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from bindings.broker_adapter import BrokerAdapter
from vqc_daemon import VQCDaemon
from vqc_utility import Logger


def _DefaultAdapter() -> BrokerAdapter:
    from bindings.alpaca_adapter import AlpacaAdapter

    return AlpacaAdapter()


@dataclass
class VQCClient:
    """Order-submission boundary backed by a synchronized VQC daemon."""

    api_key: str | None = None
    secret_key: str | None = None
    url_override: str | None = None
    paper: bool = True
    start_trade_stream: bool = True
    broker: Any | None = None
    adapter: BrokerAdapter = field(default_factory=_DefaultAdapter)
    logger: Logger = field(default_factory=Logger)
    account: Any = field(default=None, init=False)
    state_lock: Any = field(default_factory=RLock, init=False, repr=False)
    daemon: VQCDaemon = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.broker is None:
            self.broker = self.MakeBroker()
        self.daemon = VQCDaemon(self)
        self.daemon.SyncAccountFromBroker()
        if self.start_trade_stream and self.adapter.CanStream(self):
            self.daemon.StartTradeStream()

    def MakeBroker(self) -> Any:
        return self.adapter.MakeBroker(self)

    def SubmitOrder(self, symbol: str, quantity: float, side: str) -> Any:
        if not self.MarketIsOpen():
            raise RuntimeError(
                f"[VQC][Client] Market is closed; cannot submit {side} order for {symbol} now."
            )
        result = self.adapter.SubmitOrder(self.broker, symbol, quantity, side)
        self.daemon.TrackSubmittedOrder(result, symbol, quantity, side)
        self.logger.Log("Validation", f"Submitted {side} order for {symbol} x {quantity}.")
        status = self.adapter.GetOrderStatus(result)
        if status not in {"new", "partially_filled", "filled"}:
            self.logger.Log("Validation", f"Order status is {status}")
        return result

    def Buy(self, symbol: str, quantity: float = 1.0) -> Any:
        return self.SubmitOrder(symbol, quantity, "buy")

    def Sell(self, symbol: str, quantity: float = 1.0) -> Any:
        return self.SubmitOrder(symbol, quantity, "sell")

    def MarketIsOpen(self) -> bool:
        is_open = self.adapter.IsMarketOpen(self.broker)
        self.logger.Log("Client", f"Market is {'open' if is_open else 'closed'}.")
        return is_open

    def __repr__(self) -> str:
        return f"VQCClient(account_cash={self.account.cash})"


__all__ = ["VQCClient"]
