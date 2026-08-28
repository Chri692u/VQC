# VQC tutorial

This tutorial starts with the verified core, which does not contact a broker,
and then shows paper trading through `VQCClient`.

## What “verified” means here

The account transition rules are written and proved in Dafny. Dafny verifies
that each accepted `NewAccount`, `Bootstrap`, `Deposit`, `Withdraw`,
`PlaceOrder`, `SetOrderStatus`, and `Update` transition returns an account that
satisfies `IsValidAccount`.

That invariant currently means the account has structurally valid, uniquely
identified orders; valid active long positions with unique symbols; and a valid
ledger with unique IDs and an opening entry only at the start. It does **not**
prove that a broker, quote, credential, clock, network response, or trading
strategy is correct. Python validates and translates those external values
before handing records to the verified core.

> Keep `paper=True` while learning. The order examples can submit real broker
> requests if you deliberately construct a client with `paper=False`.

## 1. Set up Python

From the repository root:

```powershell
python -m venv python\.venv
python\.venv\Scripts\python.exe -m pip install -r python\requirements.txt
```

Run Python examples from the `python` directory so imports resolve naturally:

```powershell
cd python
.\.venv\Scripts\python.exe
```

## 2. Money is exact

VQC stores money as integer minor units. Use decimal strings when the value must
be exact:

```python
from vqc import VQC

price = VQC.Money.FromDecimal("425.37")

print(price)                 # 425.37
print(int(price))            # 42537 minor units
print(price.ToDecimal())     # Decimal("425.37")
print(VQC.Cost(2, price))    # 850.74
```

`FromDecimal` rounds to the nearest cent using round-half-even. Booleans and
non-finite values such as infinity are rejected.

In Dafny, `Money` is a signed integer of minor units. `Sum` and `Cost` therefore
use integer arithmetic without floating-point drift. Decimal parsing and
rounding happen in the Python boundary, not in Dafny.

## 3. Create a verified account

Account operations are immutable: each call returns a new account.

```python
from vqc import VQC

account = VQC.NewAccount()
account = VQC.Deposit(
    account,
    VQC.Money.FromDecimal("1000.00"),
    ledger_id=1,
    timestamp=0,
)

print(account.cash)  # 1000
```

Do not reuse a ledger ID. Deposits, withdrawals, and the opening snapshot each
need a unique positive `ledger_id`. Python `Deposit` and `Withdraw` allocate the
next ID when `ledger_id` is omitted; pass one explicitly only when an external
system owns the identifier.

Dafny proves that `NewAccount` is valid and that an accepted deposit preserves
account validity. Its precondition requires a positive amount and a fresh,
positive ledger ID. `Withdraw` additionally requires enough cash, so an
overdrawn withdrawal is rejected before an invalid account can be returned.

`Bootstrap` is useful when importing a trusted broker snapshot:

```python
account = VQC.Bootstrap(
    VQC.Money.FromDecimal("1000.00"),
    positions=[],
    orders=[],
    ledger_id=1,
    timestamp=0,
)
```

Dafny gives `Bootstrap` a stronger, exact contract: the result contains exactly
the supplied cash, positions, and orders, plus exactly one matching `Opening`
ledger entry. “Trusted snapshot” matters—the proof checks structural validity,
but cannot prove that values received from a broker are economically truthful.

## 4. Model an order and a fill

VQC supports market, limit, stop, and stop-limit orders. Direction is represented
by `OrderSide` in the verified records:

```python
order = VQC.Order(
    order_id=1,
    symbol="GLD",
    quantity=2,
    side=VQC.OrderSide.BUY,
    order_type=VQC.OrderType.MARKET,
)

account = VQC.PlaceOrder(account, order)
```

Dafny accepts placement only when the order ID is positive and unused, the
symbol is non-empty, quantity is positive, prices required by the order type are
positive, and the order is unfilled in a placeable lifecycle state. It proves
that adding such an order preserves the account invariant.

An order does not change cash or positions. Only a priced execution does that:

```python
fill = VQC.Fill(
    execution_id=1,
    order_id=1,
    symbol="GLD",
    quantity=1,
    price=VQC.Money.FromDecimal("425.00"),
    timestamp=0,
)

account = VQC.Update(account, fill)

print(VQC.RemainingQuantity(account.orders[0]))  # 1
print(account.positions[0].quantity)             # 1
```

Every fill should use a unique positive `execution_id`. The current Dafny model
proves that the ID is positive, but global execution-ID uniqueness is still an
adapter/application responsibility. Applying a fill additionally requires an
existing fillable `order_id`, the same symbol as that order, a positive
whole-share quantity and price, and a quantity no greater than the order's
remainder. A sell cannot exceed the verified long position. A broker's
cumulative `filled_qty` is not a fill because it does not identify the price of
the individual execution.

For an accepted update, Dafny proves that order progress, cash, positions, and
the appended trade-ledger entry remain structurally valid. A full sell removes
the closed position while preserving its order and ledger history.

Non-fill lifecycle changes use `SetOrderStatus`. `PENDING` means submitted but
not active; `OPEN` means accepted and active at the broker:

```python
account = VQC.SetOrderStatus(
    account,
    order_id=1,
    new_status=VQC.OrderStatus.OPEN,
)
```

Invalid transitions raise `VQC.HaltException` rather than producing an invalid
account.

The allowed lifecycle graph is checked in Dafny. Fill events move orders to
`PartiallyFilled` or `Filled`; `SetOrderStatus` is reserved for compatible
non-fill transitions such as acceptance, cancellation, and rejection.

## 5. Inspect the result

```python
from vqc_utility import DisplayAccount, DisplayLedger

print(DisplayAccount(account))
print(DisplayLedger(account.ledger))
print(VQC.IsValidAccount(account))
```

The display functions are for people; strategy code should read the account
records directly.

`IsValidAccount` calls the Dafny structural invariant directly. A `True` result
does not mean that a position has the current market value or that a strategy is
profitable; those facts are outside the verified state model.

## 6. Connect to an Alpaca paper account

Create `python/KEYS.env`:

```dotenv
ALPACA_API_KEY=your-paper-key
ALPACA_SECRET_KEY=your-paper-secret
```

Then create the client:

```python
from bindings.alpaca_adapter import AlpacaAdapter
from vqc_client import VQCClient
from vqc_utility import Logger

client = VQCClient("KEYS.env", AlpacaAdapter(), Logger(), paper=True)
print(client.MarketIsOpen())
print(client.account.cash)
```

Construction loads the broker's cash, whole-share long positions, and open
orders into a verified snapshot. Broker synchronization is private; use
`client.account` to read the latest snapshot.

The Alpaca SDK, HTTP calls, stream delivery, and adapter itself are not Dafny
verified. The useful boundary is that broker data must be converted into valid
VQC records before Dafny accepts the snapshot or a later transition.

## 7. Signed order quantities

All four client order methods use the same rule:

- positive quantity means buy;
- negative quantity means sell;
- zero and fractional quantities are rejected.

```python
client.MarketOrder(gld, 1)     # buy one share
client.MarketOrder(gld, -1)    # sell one share

client.LimitOrder(gld, 1, limit_price="420.00")
client.StopOrder(gld, -1, stop_price="400.00")
client.StopLimitOrder(
    gld,
    -1,
    stop_price="400.00",
    limit_price="399.00",
)
```

Required prices must be positive and finite.

Signed quantities are a convenient Python client API. The adapter converts the
sign into Dafny's explicit `Buy` or `Sell` side and passes the absolute natural
quantity to the verified order model.

### What the four order types mean

- `MarketOrder`: execute at the best available price. This is the simplest
  regular-session order, but its final price is not guaranteed.
- `LimitOrder`: execute only at the limit price or better. It may never fill.
- `StopOrder`: when the stop price is reached, activate a market order. The
  execution price can differ from the stop price.
- `StopLimitOrder`: when the stop is reached, activate a limit order. This
  controls price but may leave the order unfilled.

## 8. Market hours and extended hours

The overall pattern is normal for US-equity brokers: regular and extended
sessions have different liquidity and order rules. The exact sessions,
supported assets, order types, and time-in-force values are nevertheless broker
specific.

`MarketIsOpen` is an informational query. A strategy can decide whether to queue
an ordinary order for the next session:

```python
if client.MarketIsOpen() or queue_for_next_session:
    client.MarketOrder(gld, 1)
```

For an extended-hours request, VQC requires a limit order:

```python
client.LimitOrder(
    gld,
    1,
    limit_price="425.00",
    extended_hours=True,
)
```

This matches the included Alpaca adapter: Alpaca accepts extended-hours equity
orders only as limit orders with a supported time in force. `DAY` is the default;
callers can choose another `OrderTimeInForce` for compatible regular-session
orders. Requiring a limit is also common at other brokers because thin
extended-hours liquidity makes an unbounded market order risky, but another
broker may have different rules.

The flag means the order is eligible outside the regular session. It does not
guarantee a fill. Your strategy must obtain a current quote and choose its own
acceptable limit; VQC does not invent a price when market data is missing.

Some brokers allow an ordinary order submitted after closing to queue for the
next session. VQC leaves that decision to the caller and broker. Setting
`extended_hours=True` instead requests eligibility during the extended session;
it is not merely permission to queue.

Market-clock and extended-hours decisions are intentionally outside Dafny: they
depend on live broker rules and data. Dafny verifies the resulting order and
state transition, not whether the exchange will accept or execute it.

## 9. Liquidate a position

```python
client.Liquidate(gld)
```

This submits a market sell for the full verified long position. It fails if the
position does not exist or if outstanding sell orders have already reserved any
of its quantity. The broker decides when the market order is eligible to execute.

The Python guard prevents overlapping liquidation requests. If a sell fill is
later applied, Dafny independently requires that its quantity cannot exceed the
verified position and proves that a fully closed position is removed correctly.

## 10. Handle errors at the strategy boundary

```python
from vqc_utility import Logger, ReportException

logger = Logger()

try:
    client.MarketOrder(gld, 0)
except VQC.HaltException as error:
    logger.Log("Strategy", ReportException(error))
except (TypeError, ValueError, RuntimeError) as error:
    logger.Log("Strategy", f"Order was not submitted: {error}")
```

Handle insufficient market data, a closed market, and rejected broker requests
as normal strategy outcomes. Do not catch an error and silently pretend an order
was placed.

`VQC.HaltException` specifically signals a failed verified precondition. Ordinary
Python exceptions describe failures at the unverified boundary, such as malformed
input, unavailable data, a closed market, or a broker rejection.

## Next example

[`IntervalBuy.py`](./IntervalBuy.py) shows a small scheduled strategy. During the
regular session it uses market orders. Outside it, the example requests a latest
ask, derives a limit, and submits an extended-hours limit order. It logs a precise
error and skips the order when the quote is unavailable or unusable.

For the complete supported surface, see the
[`Python API overview`](../API_OVERVIEW.md).
