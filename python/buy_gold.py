import logging
import os
import time

from dotenv import load_dotenv

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, OrderStatus, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

from vqc_bindings import VQC

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


# -------- broker wrappers -----------------------------------------------------

def get_client() -> TradingClient:
    load_dotenv("KEYS.env")
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError("Missing Alpaca credentials in KEYS.env")
    return TradingClient(api_key, secret_key, paper=True)


def get_position_qty(client: TradingClient, symbol: str) -> float:
    for position in client.get_all_positions():
        if position.symbol == symbol:
            return float(position.qty)
    return 0.0


def wait_for_fill(client: TradingClient, order_id: str, label: str):
    final_statuses = {
        OrderStatus.FILLED,
        OrderStatus.CANCELED,
        OrderStatus.REJECTED,
        OrderStatus.EXPIRED,
        OrderStatus.DONE_FOR_DAY,
        OrderStatus.STOPPED,
        OrderStatus.SUSPENDED,
        OrderStatus.REPLACED,
    }
    for _ in range(60):
        order = client.get_order_by_id(order_id)
        logging.info("%s status: %s", label, order.status)
        if order.status in final_statuses:
            return order
        time.sleep(0.5)
    raise TimeoutError(f"{label} did not complete in time")


def submit_market_order(client: TradingClient, symbol: str, qty: float, side: OrderSide):
    order = MarketOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.DAY)
    result = client.submit_order(order_data=order)
    logging.info("submitted %s %s: id=%s status=%s qty=%s", side.name, symbol, result.id, result.status, result.qty)
    return result


def buy_symbol(client: TradingClient, symbol: str, qty: float = 1.0):
    return submit_market_order(client, symbol, qty, OrderSide.BUY)


def sell_symbol(client: TradingClient, symbol: str, qty: float = 1.0):
    return submit_market_order(client, symbol, qty, OrderSide.SELL)


# -------- VQC account events --------------------------------------------------

def new_vqc_account(cash: float):
    account = VQC.NewAccount()
    return VQC.Deposit(account, VQC.Money.from_decimal(str(cash)), 1, 0)


def apply_fill_event(account, symbol: str, side: str, qty: float, price: float, ledger_id: int):
    order = VQC.Order(ledger_id, symbol, int(qty), side, "market", 0, "new")
    fill = VQC.Fill(ledger_id, ledger_id, symbol, int(qty), VQC.Money.from_decimal(str(price)), ledger_id)
    account = VQC.PlaceOrder(account, order)
    return VQC.Update(account, order, fill)


def log_vqc_state(label: str, account):
    logging.info("%s | cash=%s | position_count=%s | order_count=%s", label, account.cash, len(account.positions), len(account.orders))


def model_buy_only(cash: float, symbol: str, qty: float = 1.0, price: float = 200.0):
    """Model the actual no-position path: a single buy from current cash."""
    account = new_vqc_account(cash)
    log_vqc_state("VQC before buy", account)
    account = apply_fill_event(account, symbol, "buy", qty, price, 1)
    log_vqc_state("VQC after buy", account)
    return {"valid": account.cash >= 0, "cash": account.cash, "account": account}


def model_sell_then_buy_reset(cash: float, symbol: str, qty: float = 1.0, price: float = 200.0):
    """Use VQC public account events to model a sell-then-buy reset flow."""
    account = new_vqc_account(cash)
    log_vqc_state("VQC before sell", account)
    account = apply_fill_event(account, symbol, "sell", qty, price, 1)
    log_vqc_state("VQC after sell", account)
    account = apply_fill_event(account, symbol, "buy", qty, price, 2)
    log_vqc_state("VQC after buy", account)
    return {"valid": account.cash >= 0, "cash": account.cash, "account": account}


# -------- strategy -----------------------------------------------------------

def ensure_single_position(client: TradingClient, symbol: str, qty: float = 1.0):
    """Hold exactly one unit. If already present, sell then buy back to test the reset path."""
    current_qty = get_position_qty(client, symbol)
    cash = float(client.get_account().cash)

    if current_qty == 0:
        vqc_model = model_buy_only(cash, symbol, qty=qty)
        logging.info("VQC validation result: valid=%s cash=%s", vqc_model["valid"], vqc_model["cash"])
        logging.info("No %s position found; buying %s.", symbol, qty)
        result = buy_symbol(client, symbol, qty)
        return {"action": "buy", "result": result, "vqc": vqc_model}

    if current_qty == qty:
        vqc_model = model_sell_then_buy_reset(cash, symbol, qty=qty)
        logging.info("VQC validation result: valid=%s cash=%s", vqc_model["valid"], vqc_model["cash"])
        logging.info("%s already equals %s; testing sell-then-buy reset.", symbol, qty)
        sell_result = sell_symbol(client, symbol, current_qty)
        wait_for_fill(client, sell_result.id, f"{symbol} sell")
        buy_result = buy_symbol(client, symbol, qty)
        return {"action": "reset_same_qty", "sell": sell_result, "buy": buy_result, "vqc": vqc_model}

    vqc_model = model_sell_then_buy_reset(cash, symbol, qty=qty)
    logging.info("VQC validation result: valid=%s cash=%s", vqc_model["valid"], vqc_model["cash"])
    logging.info("%s currently %s; resetting to %s by sell then buy.", symbol, current_qty, qty)
    sell_result = sell_symbol(client, symbol, current_qty)
    wait_for_fill(client, sell_result.id, f"{symbol} sell")
    buy_result = buy_symbol(client, symbol, qty)
    return {"action": "reset", "sell": sell_result, "buy": buy_result, "vqc": vqc_model}


def main():
    client = get_client()
    try:
        result = ensure_single_position(client, "GLD", qty=1.0)
        #logging.info("Final action summary: %s", result)
    except Exception as exc:
        logging.exception("Gold trading flow failed: %s", exc)
        raise


if __name__ == "__main__":
    main()