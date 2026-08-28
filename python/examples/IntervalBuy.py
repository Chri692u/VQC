from decimal import Decimal, InvalidOperation, ROUND_UP
from pathlib import Path
import sys
import time

import schedule
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from dotenv import dotenv_values

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vqc_client import VQCClient
from vqc_utility import DisplayAccount, DisplayLedger, Logger
from bindings.alpaca_adapter import AlpacaAdapter

BUY_INTERVAL = 1
BUY_INTERVAL_UNIT = "minutes"
SYMBOLS = ["GLD", "SLV"]
LIMIT_BUFFER = Decimal("1.005")


class MarketDataUnavailableError(RuntimeError):
    """Raised when the strategy cannot derive a price from its selected feed."""


def GetExtendedHoursLimit(data: StockHistoricalDataClient, symbol: str) -> Decimal:
    """Return a conservatively rounded buy limit from the latest ask quote."""
    quotes = data.get_stock_latest_quote(
        StockLatestQuoteRequest(symbol_or_symbols=symbol)
    )
    quote = quotes.get(symbol)
    if quote is None:
        raise MarketDataUnavailableError(
            f"The selected market-data feed returned no quote for {symbol}; "
            "no order was submitted."
        )
    try:
        ask = Decimal(str(quote.ask_price))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise MarketDataUnavailableError(
            f"The selected market-data feed returned invalid "
            f"ask={quote.ask_price!r} for {symbol}; no order was submitted."
        ) from error
    if not ask.is_finite() or ask <= 0:
        raise MarketDataUnavailableError(
            f"The selected market-data feed returned ask={quote.ask_price!r} "
            f"for {symbol}; no order was submitted."
        )
    return (ask * LIMIT_BUFFER).quantize(Decimal("0.01"), rounding=ROUND_UP)


def BuyGoldAndSilver(
    client: VQCClient,
    data: StockHistoricalDataClient,
    logger: Logger,
) -> None:
    """Place one-share orders appropriate for the broker's market clock."""
    regular_market = client.MarketIsOpen()
    for symbol in SYMBOLS:
        try:
            if regular_market:
                client.MarketOrder(symbol, 1)
            else:
                limit_price = GetExtendedHoursLimit(data, symbol)
                client.LimitOrder(
                    symbol,
                    1,
                    limit_price,
                    extended_hours=True,
                )
                logger.Log("Example", f"Extended-hours {symbol} limit: ${limit_price}.")
        except Exception as error:
            logger.Log(
                "Example",
                f"{type(error).__name__}: {error}",
            )


if __name__ == "__main__":
    environment_path = "KEYS.env"
    configuration = dotenv_values(environment_path)
    logger = Logger()
    client = VQCClient(environment_path, AlpacaAdapter(), logger)
    data = StockHistoricalDataClient(
        configuration.get("ALPACA_API_KEY"),
        configuration.get("ALPACA_SECRET_KEY"),
    )

    logger.Log("Example", DisplayAccount(client.account))
    logger.Log("Example", DisplayLedger(client.account.ledger))

    BuyGoldAndSilver(client, data, logger)
    getattr(schedule.every(BUY_INTERVAL), BUY_INTERVAL_UNIT).do(
        BuyGoldAndSilver,
        client=client,
        data=data,
        logger=logger,
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.Log("Example", "Stopped.")
