# Dafny API Overview

The Dafny core provides immutable account records and verified state transitions. Python and TypeScript bindings call this API.

## Types

`Types` defines `Money`, identifiers, orders, fills, positions, ledger entries, and accounts. Orders support `Buy` and `Sell`; `Market`, `Limit`, `Stop`, and `StopLimit`; and the lifecycle states `Pending`, `Open`, `PartiallyFilled`, `Filled`, `Cancelled`, and `Rejected`.

## Account operations

| Operation | Purpose |
| --- | --- |
| `NewAccount()` | Creates an empty account. |
| `Bootstrap(cash, positions, orders, ledgerId, timestamp)` | Creates an account from a trusted snapshot. |
| `Deposit(account, ledgerId, amount, timestamp)` | Adds cash and a deposit ledger entry. |
| `Withdraw(account, ledgerId, amount, timestamp)` | Removes cash and adds a withdrawal ledger entry. |
| `PlaceOrder(account, order)` | Adds a fresh pending, unfilled order. |
| `SetOrderStatus(account, orderId, newStatus)` | Applies a non-fill lifecycle transition. |
| `Update(account, fill)` | Applies a priced fill to the order, cash, positions, and ledger. |

Every operation returns a new `Account`.

## Utilities

| Module | Available functions |
| --- | --- |
| `Currency` | `Sum`, `Cost` |
| `Orders` | `RemainingQuantity` |
| `Validation` | `IsValidOrder`, `IsValidFill`, `IsValidPosition`, `IsValidLedger`, `IsValidAccount` |

Use `Bootstrap` for broker snapshots, `PlaceOrder` for new orders, `SetOrderStatus` for non-fill events, and `Update` for priced executions.
