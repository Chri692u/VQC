from pathlib import Path
import sys
import time

import schedule

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bindings.alpaca_adapter import AlpacaAdapter
from vqc_client import VQCClient
from vqc_utility import DisplayAccount, DisplayLedger, Logger


# Well-known US listings that Alpaca normally reports on different exchanges.
SYMBOLS = ("AAPL", "KO", "GLD")
BUY_INTERVAL = 1
BUY_INTERVAL_UNIT = "minutes"


def BuyOneShareAcrossMarkets(client: VQCClient, logger: Logger) -> None:
    """Validate the selected Alpaca listings and submit one share of each."""
    if not client.MarketIsOpen():
        logger.Log("Example", "Market is closed; skipping this interval.")
        return

    assets = [client.broker.get_asset(symbol) for symbol in SYMBOLS]
    exchanges = {
        str(getattr(asset.exchange, "value", asset.exchange))
        for asset in assets
    }
    if len(exchanges) != len(assets):
        raise RuntimeError(
            "Alpaca no longer reports the selected symbols on distinct exchanges"
        )

    for asset in assets:
        try:
            exchange = str(getattr(asset.exchange, "value", asset.exchange))
            if not asset.tradable:
                raise RuntimeError(
                    f"Alpaca reports {asset.symbol} on {exchange} as not tradable"
                )
            logger.Log("Example", f"Submitting {asset.symbol} on {exchange}.")
            client.MarketOrder(asset.symbol, 1)
        except Exception as error:
            logger.Log("Example", f"{type(error).__name__}: {error}")

if __name__ == "__main__":
    logger = Logger()
    client = VQCClient("KEYS.env", AlpacaAdapter(), logger)

    logger.Log("Example", DisplayAccount(client.account))
    logger.Log("Example", DisplayLedger(client.account.ledger))

    BuyOneShareAcrossMarkets(client, logger)
    getattr(schedule.every(BUY_INTERVAL), BUY_INTERVAL_UNIT).do(
        BuyOneShareAcrossMarkets,
        client=client,
        logger=logger,
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.Log("Example", "Stopped.")
