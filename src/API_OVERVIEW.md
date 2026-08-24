# Dafny API

These Dafny functions and methods are the implementation surface consumed by
the bindings in other languages. Internal functions, utilities, contract
predicates, and proof lemmas are not to be used by external interfaces.

`Types.Money(value: int)` is the money value used by `Currency` and all account
operations. It stores signed integer minor units; for example, the Python `VQC.Money` binding
uses a scale of 100, so `VQC.Money.FromDecimal("12.34")` becomes `Money(1234)`
in Dafny.

| Dafny module | Function or method | External use |
| --- | --- | --- |
| `AccountOps` | `NewAccount()` | Creates an empty account. |
| `AccountOps` | `Bootstrap(cash, positions, orders, id, timestamp)` | Creates an account from a trusted broker snapshot. |
| `AccountOps` | `Deposit`, `Withdraw` | Applies a cash movement and ledger entry. |
| `AccountOps` | `PlaceOrder(account, order)` | Adds a new order to the account. |
| `AccountOps` | `SetOrderStatus(account, orderId, newStatus)` | Applies a valid non-fill lifecycle status change to an existing order. |
| `AccountOps` | `Update(account, fill)` | Applies a fill to its stored order, position, cash, and ledger. |
| `Currency` | `Sum(values)`, `Cost(quantity, price)` | Money arithmetic. |
| `Orders` | `RemainingQuantity(order)` | Reads an order's unfilled quantity. |
| `Validation` | `IsValidOrder`, `IsValidFill`, `IsValidPosition`, `IsValidLedger`, `IsValidAccount` | Exposed to external interfaces for validation predicates. |

`Bootstrap` has an exact snapshot contract: its result has exactly the supplied
cash, positions, and orders, and its ledger is exactly one `Opening` entry with
those values and the supplied ID/timestamp.

Internal preservation proofs are split by domain: `LedgerProof` proves fresh
generated ledger IDs, `OrderProof` proves valid order replacement, and
`PositionProof` proves valid position upsert/removal. `AccountProof` contains
the composed account-operation contract predicates; none of these modules is
part of the Python API.

The `AccountOps` methods preserve `IsValidAccount` when their preconditions are
met. Account position sets contain only active, positive-quantity holdings;
closing sells remain recorded as ledger trades. External interfaces should use
`Update` for fills; a fill never creates an order. `IsValidAccount` is currently
structural validity, not a proof that cash and positions can be reconstructed
from the full ledger history.
