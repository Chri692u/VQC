from pathlib import Path
import sys
import time
import schedule

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vqc_client import VQCClient
from vqc_diagnostics import DisplayLedger

BUY_INTERVAL = 1
BUY_INTERVAL_UNIT = "minutes"

def buy_gold_and_silver(vqc_client: VQCClient):
    print("Starting interval buy for GLD and SLV.")
    for symbol in ["GLD", "SLV"]:
        try:
            vqc_client.Buy(symbol, 1)
        except Exception as e:
            pass

if __name__ == "__main__":
    vqc_client = VQCClient()
    print(f"Initialized VQCClient with account cash: {vqc_client.account.cash}")
    print(f"At broker time: {vqc_client.broker.get_clock().timestamp}")
    print(DisplayLedger(vqc_client.account.ledger))
    symbols = ["GLD", "SLV"]
    getattr(schedule.every(BUY_INTERVAL), BUY_INTERVAL_UNIT).do(
        buy_gold_and_silver,
        vqc_client=vqc_client,
    )
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped.")
