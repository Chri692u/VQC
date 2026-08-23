from decimal import Decimal

from vqc_bindings import VQC


# ---------------------------------------------------------------------------
# Account lifecycle tests
# ---------------------------------------------------------------------------

def test_new_account():
    print("[test] NewAccount")
    account = VQC.NewAccount()
    assert account.cash == 0
    assert len(account.orders) == 0
    assert len(account.positions) == 0
    assert len(account.ledger) == 0


def test_deposit_and_withdraw():
    print("[test] Deposit/Withdraw")
    account = VQC.NewAccount()
    account = VQC.Deposit(account, 1000, 1, 0)
    assert account.cash == 1000

    account = VQC.Withdraw(account, 250, 2, 1)
    assert account.cash == 750


# ---------------------------------------------------------------------------
# Order and execution tests
# ---------------------------------------------------------------------------

def test_order_and_fill_construction():
    print("[test] Order/Fill/Position")
    order = VQC.Order(1, "AAPL", 10, "buy", "market", "new", 0)
    assert order.orderId == 1
    assert order.symbol == "AAPL"
    assert order.quantity == 10

    fill = VQC.Fill(1, 1, "AAPL", 10, 195, 0)
    assert fill.executionId == 1
    assert fill.price == 195

    position = VQC.Position("AAPL", 10, 195)
    assert position.symbol == "AAPL"
    assert position.quantity == 10


def test_place_order_and_update_fill():
    print("[test] PlaceOrder/Update")
    account = VQC.NewAccount()
    account = VQC.Deposit(account, 1000, 1, 0)

    order = VQC.Order(1, "AAPL", 10, "buy", "market", "new", 0)
    account = VQC.PlaceOrder(account, order)
    assert len(account.orders) == 1

    fill = VQC.Fill(1, 1, "AAPL", 10, 195, 0)
    account = VQC.Update(account, order, fill)
    assert account.cash == -950
    assert account.orders[0].filledQuantity == 10
    assert account.positions[0].symbol == "AAPL"
    assert account.positions[0].quantity == 10


# ---------------------------------------------------------------------------
# Money arithmetic tests
# ---------------------------------------------------------------------------

def test_money_arithmetic():
    print("[test] Money arithmetic")
    a = VQC.Money(10)
    b = VQC.Money(5)
    c = VQC.Money(3)
    price = VQC.Money(10.50)
    fee = VQC.Money(1.25)

    assert a + b == VQC.Money(15)
    assert a - b == VQC.Money(5)
    assert -a == VQC.Money(-10)
    assert +a == VQC.Money(10)
    assert a + 5 == VQC.Money(15)
    assert 5 + a == VQC.Money(15)
    assert a * c == VQC.Money(30)
    assert price == VQC.Money(1050)
    assert price + fee == VQC.Money(1175)
    assert VQC.Money.from_decimal("10.50") == VQC.Money(1050)
    assert VQC.Money.from_decimal("10.50").to_decimal() == Decimal("10.50")
    assert VQC.Money(1050).to_decimal() == Decimal("10.50")
    assert VQC.Sum([VQC.Money(1), VQC.Money(2), VQC.Money(3)]) == VQC.Money(6)
    assert VQC.Cost(3, VQC.Money(7)) == VQC.Money(21)


# ---------------------------------------------------------------------------
# Order state and execution helpers
# ---------------------------------------------------------------------------

def test_order_helpers():
    print("[test] Order helpers")
    order = VQC.Order(1, "AAPL", 8, "buy", "market", "partially_filled", 3)
    assert VQC.RemainingQuantity(order) == 5

    updated = VQC.ApplyFill(order, 2)
    assert updated.filledQuantity == 5
    assert updated.status.is_PartiallyFilled or updated.status.is_Filled

    cancelled = VQC.Cancel(order)
    assert cancelled.status.is_Cancelled

    rejected = VQC.Reject(order)
    assert rejected.status.is_Rejected
    assert rejected.filledQuantity == 0

    set_status = VQC.SetStatus(order, "filled")
    assert set_status.status.is_Filled


def test_execution_helper():
    print("[test] ExecutionValue")
    fill = VQC.Fill(1, 1, "AAPL", 5, 200, 0)
    assert VQC.ExecutionValue(fill) == VQC.Money(1000)


if __name__ == "__main__":
    print("[run] starting VQC binding tests")
    test_new_account()
    test_deposit_and_withdraw()
    test_order_and_fill_construction()
    test_place_order_and_update_fill()
    test_money_arithmetic()
    test_order_helpers()
    test_execution_helper()
    print("[run] bindings ok")
