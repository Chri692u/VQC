# VQC Python API

Import VQC with `from vqc import VQC`. Account functions return new immutable
account values; they do not mutate the account passed to them.

## Construction

| API | Purpose |
| --- | --- |
| `VQC.Money.FromDecimal(value)` | Creates money from a decimal value such as `"12.34"`. |
| `VQC.Order(...)`, `VQC.Fill(...)`, `VQC.Position(...)` | Create records used by account operations. |
| `VQC.NewAccount()` | Creates an empty account. |
| `VQC.Bootstrap(cash, positions, orders, ledger_id=1, timestamp=0)` | Creates an account from current trusted broker state. Positions and orders are Python lists. |

## Account transitions

```python
from vqc import VQC

cash = VQC.Money.FromDecimal("1000")
account = VQC.Bootstrap(cash, [], [])

order = VQC.Order(1, "GLD", 1, "buy", "market", "new", 0)
account = VQC.PlaceOrder(account, order)

fill = VQC.Fill(1, 1, "GLD", 1, VQC.Money.FromDecimal("425"), 0)
account = VQC.Update(account, fill)
```

- `VQC.Deposit` and `VQC.Withdraw` change cash and append ledger entries.
- `VQC.PlaceOrder` adds a valid, uniquely identified order.
- `VQC.Update` applies a broker fill to its existing stored order. It updates
  cash, position, order status, and the trade ledger entry.
- `VQC.SetOrderStatus` is for non-fill lifecycle events such as acceptance,
  cancellation, and rejection. Use `Update` for every fill.

## Helpers

`VQC.Sum`, `VQC.Cost`, and `VQC.RemainingQuantity` provide small money/order
helpers. `VQC.IsValidOrder`, `VQC.IsValidFill`, `VQC.IsValidPosition`,
`VQC.IsValidLedger`, and `VQC.IsValidAccount` expose validation predicates.

## Example

`examples/IntervalBuy.py` creates a `VQCClient` and schedules recurring GLD and
SLV buys. Change `BUY_INTERVAL` and `BUY_INTERVAL_UNIT` to switch between test
cadences such as `1` / `"minutes"` and live cadences such as `2` / `"weeks"`.
