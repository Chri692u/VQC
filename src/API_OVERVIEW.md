# Dafny API

These Dafny functions and methods are the implementation surface consumed by
the bindings in other languages. Internal functions, utilities and proof lemmas are not to be used by external interfaces.

`Types.Money(value: int)` is the money value used by `Currency` and all account
operations. It stores signed integer minor units; For example, the Python `VQC.Money` binding
uses a scale of 100, so `VQC.Money.FromDecimal("12.34")` becomes `Money(1234)`
in Dafny.

| Dafny module | Function or method | Python use |
| --- | --- | --- |
| `AccountOps` | `NewAccount()` | Creates an empty account. |
| `AccountOps` | `Bootstrap(cash, positions, orders, id, timestamp)` | Creates an account from a trusted broker snapshot. |
| `AccountOps` | `Deposit`, `Withdraw` | Applies a cash movement and ledger entry. |
| `AccountOps` | `PlaceOrder(account, order)` | Adds a new order to the account. |
| `AccountOps` | `Update(account, fill)` | Applies a fill to its stored order, position, cash, and ledger. |
| `Currency` | `Sum(values)`, `Cost(quantity, price)` | Money arithmetic helpers. |
| `Orders` | `RemainingQuantity(order)` | Reads an order's unfilled quantity. |
| `Orders` | `SetStatus(order, status)` | Used internally by Python's `SetOrderStatus` helper. |
| `Validation` | `IsValidOrder`, `IsValidFill`, `IsValidPosition`, `IsValidLedger`, `IsValidAccount` | Exposed as Python validation predicates. |

The `AccountOps` methods preserve `IsValidAccount` when their preconditions are
met. External interfaces should use `Update` for fills; a fill never creates an order. and similarly for all operations on account.
