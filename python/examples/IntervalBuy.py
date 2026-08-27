from pathlib import Path
import sys
import time
import schedule

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vqc_client import VQCClient
from vqc_utility import DisplayLedger, Logger

BUY_INTERVAL = 1
BUY_INTERVAL_UNIT = "minutes"

def buy_gold_and_silver(vqc_client: VQCClient, logger: Logger):
    logger.Log("Example", "Starting interval buy for GLD and SLV.")
    for symbol in ["GLD", "SLV"]:
        try:
            vqc_client.Buy(symbol, 1)
        except Exception as error:
            logger.Log("Example", f"Could not submit {symbol}: {error}")

if __name__ == "__main__":
    logger = Logger(mute=False)
    vqc_client = VQCClient(logger=logger)
    logger.Log("Example", f"Initialized client with cash: {vqc_client.account.cash}")
    logger.Log("Example", f"Broker time: {vqc_client.broker.get_clock().timestamp}")
    logger.Log("Diagnostics", DisplayLedger(vqc_client.account.ledger))
    getattr(schedule.every(BUY_INTERVAL), BUY_INTERVAL_UNIT).do(
        buy_gold_and_silver,
        vqc_client=vqc_client,
        logger=logger,
    )
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.Log("Example", "Stopped.")
