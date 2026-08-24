# VQC Python API

```python
from vqc import VQC
from vqc_broker_adapter import BrokerAdapter
from vqc_client import VQCClient
from vqc_diagnostics import DisplayAccount, DisplayLedger, Logger, ReportException
from vqc_utility import VQCUtility
```

The runtime implementation uses Python and Alpaca. All account calls return a new account; they do not mutate the input account.
Invalid Dafny preconditions raise `VQC.HaltException` at runtime.

## Money

| Call | Result |
| --- | --- |
| `VQC.Money.FromDecimal(value)` | Converts a decimal value to scaled minor units. `"12.34"` becomes `1234`. |
| `VQC.Money.FromMinorUnits(value)` | Creates money directly from an integer number of minor units. |
| `money.ToDecimal()` | Converts scaled money back to `Decimal`. |
| `VQC.Sum(values)` | Returns the sum of a `list[VQC.Money]`. |
| `VQC.Cost(quantity, price)` | Returns `quantity * price`. |

## Records

| Call | Result |
| --- | --- |
| `VQC.Order(order_id, symbol, quantity, side="buy", order_type="market", status="new", filled_quantity=0, limit_price=None)` | Creates an order record. `side` is `"buy"` or `"sell"`; `order_type` is `"market"` or `"limit"`. |
| `VQC.Fill(execution_id, order_id, symbol, quantity, price, timestamp)` | Creates a priced execution record for an existing order. |
| `VQC.Position(symbol, quantity, average_price)` | Creates a long-only position record. |

The record type aliases are `VQC.Account`, `VQC.Ledger`, `VQC.OrderRecord`,
`VQC.FillRecord`, and `VQC.PositionRecord`.

## Account calls

| Call | Result |
| --- | --- |
| `VQC.NewAccount()` | Returns an empty account. |
| `VQC.Bootstrap(cash, positions, orders, ledger_id=1, timestamp=0)` | Returns an account from a trusted snapshot. `positions` and `orders` are Python lists. |
| `VQC.Deposit(account, amount, ledger_id=1, timestamp=0)` | Adds positive cash and appends a deposit ledger entry. |
| `VQC.Withdraw(account, amount, ledger_id=1, timestamp=0)` | Removes positive cash and appends a withdrawal ledger entry. |
| `VQC.PlaceOrder(account, order)` | Adds a valid order with a fresh order ID. |
| `VQC.Update(account, fill)` | Applies a fill to its existing stored order, then updates cash, position, order state, and ledger. |
| `VQC.SetOrderStatus(account, order_id, new_status)` | Applies a non-fill lifecycle status update. |

Use `Update` only for broker `partial_fill` and `fill` events. A fill never
creates an order. Use `SetOrderStatus` only for events such as acceptance,
cancellation, or rejection.

## Validation and order utility

| Call | Result |
| --- | --- |
| `VQC.RemainingQuantity(order)` | Returns `order.quantity - order.filledQuantity`. |
| `VQC.IsValidOrder(value)` | Checks structural order validity. |
| `VQC.IsValidFill(value)` | Checks fill validity. |
| `VQC.IsValidPosition(value)` | Checks position validity. |
| `VQC.IsValidLedger(value)` | Checks ledger validity. |
| `VQC.IsValidAccount(value)` | Checks structural account validity. |

`VQCUtility` provides small Python-side helpers used by the client: `GetField`
reads either an object attribute or dictionary field, `GetOrderKey` extracts a
broker order ID, `NextOrderId` finds the next VQC numeric order ID, and
`GetOrAddId` assigns a local numeric ID to an external ID.

## Alpaca client and adapters

`VQCClient` is the Python broker boundary:

```python
from vqc_client import VQCClient

client = VQCClient()
client.Buy("GLD", 1)
```

On construction it bootstraps VQC from Alpaca cash, positions, and open orders.
`Buy`, `Sell`, and `SubmitOrder` submit broker orders; broker `partial_fill` and
`fill` events call `VQC.Update`. Other broker lifecycle events call
`VQC.SetOrderStatus`.

`BrokerAdapter` performs the conversion from Alpaca values to VQC records:

- prices, cash, and average prices become scaled `VQC.Money` values;
- timestamps become Unix seconds;
- Alpaca order statuses become VQC status strings;
- Alpaca positions become long-only VQC positions; a short position raises an
  error because VQC positions cannot have negative quantity;
- Alpaca orders and fills become `VQC.Order` and `VQC.Fill` records using the
  VQC numeric IDs assigned by the client.

## Diagnostics

`Logger(mute=False)` in `vqc_diagnostics` prints tagged messages such as
`[VQC][Client] ...`. Pass `Logger(mute=True)` to `VQCClient(logger=...)` to
suppress client output. `DisplayAccount(account)`, `DisplayLedger(ledger)`, and
`ReportException(error)` return readable strings for logging or printing.

## Minimal example

```python
cash = VQC.Money.FromDecimal("1000")
account = VQC.Bootstrap(cash, [], [])

order = VQC.Order(1, "GLD", 1)
account = VQC.PlaceOrder(account, order)

fill = VQC.Fill(1, 1, "GLD", 1, VQC.Money.FromDecimal("425"), 0)
account = VQC.Update(account, fill)
```

`examples/IntervalBuy.py` creates `VQCClient` and schedules recurring GLD/SLV
buys. Change `BUY_INTERVAL` and `BUY_INTERVAL_UNIT` to use test or live cadence.
