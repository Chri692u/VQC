# VQC Python API Overview

Import the public facade with `from vqc import VQC`. It exposes Dafny-generated
records and verified account transitions without exposing Dafny modules or proof
helpers.

## Types and constructors

| Python API | Purpose |
| --- | --- |
| `VQC.Money` | Signed fixed-scale money. Use `VQC.Money.FromDecimal("12.34")` for user-facing values. |
| `VQC.Order(id, symbol, quantity, side, order_type, status, filled_quantity)` | Creates an order. Sides are `"buy"` / `"sell"`; statuses include `"new"`, `"accepted"`, `"partially_filled"`, `"filled"`, `"cancelled"`, and `"rejected"`. |
| `VQC.Fill(execution_id, order_id, symbol, quantity, price, timestamp)` | Creates one priced execution against an existing order. |
| `VQC.Position(symbol, quantity, average_price)` | Creates a long-only position. Quantity cannot be negative. |
| `VQC.Account`, `VQC.Ledger`, `VQC.OrderRecord`, `VQC.FillRecord`, `VQC.PositionRecord` | Type aliases for annotations and inspection. |

## Verified account transitions

Each of these returns a new account and preserves `VQC.IsValidAccount` when its
input is valid. They do not mutate the supplied account.

```python
account = VQC.NewAccount()
account = VQC.Bootstrap(cash, positions, orders, ledger_id=1, timestamp=0)
account = VQC.Deposit(account, amount, ledger_id=2, timestamp=0)
account = VQC.Withdraw(account, amount, ledger_id=3, timestamp=0)
account = VQC.PlaceOrder(account, order)
account = VQC.Update(account, fill)
```

- `NewAccount()` creates an empty account.
- `Bootstrap(...)` creates an account from a trusted current snapshot. `positions`
  and `orders` are ordinary Python lists.
- `Deposit` / `Withdraw` append ledger entries. Withdrawal currently requires
  enough cash; cash may nevertheless become negative through margin-funded buys.
- `PlaceOrder` requires a valid order with a fresh ID.
- `Update` applies a fill to the matching stored order. It updates cash,
  positions, order fill status, and the trade ledger entry. A fill never creates
  an order.

## Other public functions

| Python API | Purpose |
| --- | --- |
| `VQC.Sum(values)`, `VQC.Cost(quantity, price)` | Money helpers. |
| `VQC.RemainingQuantity(order)` | Returns an order's unfilled quantity. |
| `VQC.IsValidOrder`, `VQC.IsValidFill`, `VQC.IsValidPosition`, `VQC.IsValidLedger`, `VQC.IsValidAccount` | Validation predicates. |
| `VQC.SetOrderStatus(account, order_id, status)` | Python helper for a non-fill order lifecycle status update. |

`SetOrderStatus` is not a verified account transition. Use `Update` for every
broker fill; use `SetOrderStatus` only for lifecycle events such as acceptance,
cancellation, or rejection.
