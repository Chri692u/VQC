# VQC API Overview

This document describes only the verified Dafny public API and the matching
Python bindings. It excludes internal helpers, proof lemmas, and broker/client
integration code.

## Dafny types

Defined by `Types.dfy` and exposed by the Python facade as `VQC` types.

| Dafny type | Meaning | Python exposure |
| --- | --- | --- |
| `Money` | Signed fixed-scale monetary value. | `VQC.Money` |
| `OrderId`, `ExecutionId`, `LedgerId` | Positive domain identifiers. | Integers are accepted by constructors/bindings. |
| `OrderSide` | `Buy` or `Sell`. | `"buy"` or `"sell"` in `VQC.Order`. |
| `OrderType` | `Market` or `Limit(price)`. | `"market"` or `"limit"` in `VQC.Order`. |
| `OrderStatus` | Order lifecycle status. | Status strings in `VQC.Order` / `VQC.SetOrderStatus`. |
| `Order` | Authoritative order: ID, symbol, quantity, side, type, status, and filled quantity. | `VQC.Order(...)`, `VQC.OrderRecord` |
| `Fill` | A priced execution against an order: execution ID, order ID, symbol, quantity, price, and timestamp. | `VQC.Fill(...)`, `VQC.FillRecord` |
| `Position` | Symbol, non-negative quantity, and average price. | `VQC.Position(...)`, `VQC.PositionRecord` |
| `LedgerEntry` | `Opening`, `Deposit`, `Withdrawal`, or `Trade`. | Exposed through `VQC.Account.ledger`. |
| `Ledger` | Append-only sequence of ledger entries. | `VQC.Ledger`; generated account values expose its entries as `account.ledger`. |
| `Account` | Cash, ledger, positions, and orders. | `VQC.Account` |

`Money` may be negative, including account cash. Positions remain long-only in
the current model.

## Dafny account API

The public methods in `AccountOps` are listed below. Each returns an `Account`
and has `ensures IsValidAccount(result)`.

| Dafny method | Preconditions, in domain terms | Effect |
| --- | --- | --- |
| `NewAccount()` | None. | Creates an empty account. |
| `Bootstrap(cash, positions, orders, id, timestamp)` | Valid unique positions and orders, lifecycle-consistent orders, and a valid ledger ID. | Creates one `Opening` ledger entry containing the supplied trusted state. |
| `Deposit(account, id, amount, timestamp)` | Valid account, fresh ledger ID, positive amount. | Adds cash and appends a `Deposit`. |
| `Withdraw(account, id, amount, timestamp)` | Deposit preconditions and cash at least the amount. | Subtracts cash and appends a `Withdrawal`. |
| `PlaceOrder(account, order)` | Valid account and a valid order with a fresh order ID. | Adds the order. |
| `Update(account, fill)` | Valid account; an existing authoritative order; a fill applicable to it; sufficient position quantity for a sell. | Updates that order, cash, position, and appends a `Trade` with a fresh ledger ID. |

`Update` deliberately accepts no `Order` argument. The fill's `orderId` selects
the authoritative order stored in the account; a fill cannot create an order.

## Python bindings

The following names mirror the verified Dafny surface:

```python
from vqc import VQC

account = VQC.NewAccount()
account = VQC.Bootstrap(cash, positions, orders, ledger_id=1, timestamp=0)
account = VQC.Deposit(account, amount, ledger_id=2, timestamp=0)
account = VQC.Withdraw(account, amount, ledger_id=3, timestamp=0)
account = VQC.PlaceOrder(account, order)
account = VQC.Update(account, fill)
```

`VQC.Bootstrap` accepts Python lists of `VQC.PositionRecord` and
`VQC.OrderRecord`; the binding converts them to Dafny sequences. The exposed
type aliases are `VQC.Account`, `VQC.Ledger`, `VQC.OrderRecord`,
`VQC.FillRecord`, and `VQC.PositionRecord`.

The bindings also expose these verified lower-level operations and predicates:

- Money and execution: `VQC.Sum`, `VQC.Cost`, `VQC.ExecutionValue`.
- Orders: `VQC.RemainingQuantity`, `VQC.ApplyFill`, `VQC.SetStatus`,
  `VQC.SetOrderStatus`, `VQC.Cancel`, `VQC.Reject`.
- Predicates: `VQC.IsValidOrder`, `VQC.IsValidFill`, `VQC.IsValidPosition`,
  `VQC.IsValidLedger`, `VQC.IsValidAccount`.

## Current validity boundary

`IsValidAccount` currently proves structural consistency: valid ledger entries
with unique ledger IDs, valid positions with unique symbols, and valid orders
with unique order IDs. Reconciliation invariants such as reconstructing cash or
positions from the ledger are not yet part of this public contract.
