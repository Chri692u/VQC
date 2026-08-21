# API Overview

This document lists only the public functions intended for external use. Types and internal verification helpers are managed inside the Dafny modules.

## Currency.dfy

Public types:

- `Money` - immutable monetary value wrapper around `int`.

- `Add(a, b)` - add two money values.
- `Sub(a, b)` - subtract one money value from another.
- `Neg(a)` - negate a money value.
- `Abs(a)` - return the absolute value.
- `Eq(a, b)` - compare two money values for equality.
- `Lt(a, b)` - compare two money values with less-than.
- `Lte(a, b)` - compare two money values with less-than-or-equal.
- `Gt(a, b)` - compare two money values with greater-than.
- `Gte(a, b)` - compare two money values with greater-than-or-equal.
- `IsZero(m)` - true when the value is zero.
- `IsPositive(m)` - true when the value is strictly positive.
- `IsNegative(m)` - true when the value is strictly negative.
- `Sum(moneys)` - sum a sequence of money values.
- `Cost(qty, price)` - compute quantity times unit price.

## Orders.dfy

Public types:

- `OrderId` - unique order identifier.
- `OrderSide` - `Buy` or `Sell`.
- `OrderType` - `Market` or `Limit(limitPrice)`.
- `OrderStatus` - `New`, `PartiallyFilled`, `Filled`, `Cancelled`, or `Rejected`.
- `Order` - immutable order record containing identity, symbol, quantity, side, type, status, and filled quantity.

- `IsOpenStatus(status)` - true when the order is still active.
- `IsMarketOrder(order)` - true when the order is a market order.
- `IsLimitOrder(order)` - true when the order is a limit order.
- `HasRemainingQuantity(order)` - true when the order still has quantity left to fill.
- `IsFullyFilled(order)` - true when the filled quantity equals the total quantity.
- `IsUnfilled(order)` - true when no quantity has been filled.
- `IsValidOrder(order)` - checks structural validity of an order.
- `RemainingQuantity(order)` - returns the unfilled quantity.

## Execution.dfy

Public types:

- `ExecutionId` - unique identifier for a fill.
- `Fill` - immutable execution record containing execution id, order id, symbol, quantity, price, and timestamp.

- `IsValidFill(fill)` - checks that a fill is structurally valid.
- `ExecutionValue(fill)` - compute the monetary value of one fill.
- `TotalExecutedQuantity(fills)` - sum quantities across fills.
- `TotalExecutedValue(fills)` - sum execution values across fills.
- `AverageExecutionPrice(fills)` - compute an average execution price from a non-empty fill set.
- `TotalExecutedQuantityForOrder(fills, order)` - total quantity for fills related to one order.
- `TotalExecutedValueForOrder(fills, order)` - total execution value for fills related to one order.
- `BelongsToOrder(fill, order)` - check whether a fill matches one order.
- `SameOrder(fill1, fill2)` - check whether two fills refer to the same order.
- `AllBelongToOrder(fills, order)` - check whether every fill in a sequence belongs to one order.
- `FillsAccountForOrder(fills, order)` - check whether the fills sum to the order quantity.
- `FillsDoNotExceedOrder(fills, order)` - check whether the fills stay within the order quantity.


## Positions.dfy
Public types:

- `Position` - Symbol, quantity, average price

- `IsValidPosition(pos)` - Predicate for valid positions
- `IsOpen(pos)` - Check if quantity above 0
- `IsClosed(pos)` - Check if quantity is 0
- `PositionValue(pos)` - Computes quantity times average unit price
- `ApplyBuy(pos,fill)` - Computes the updated position from a buy
- `ApplySell(pos,fill)` - Computes the updated position from a sell

## Ledger.dfy

Public types:

- `LedgerId` - unique identifier for a ledger event.
- `LedgerEntry` - one historical account-affecting event, with variants `Deposit`, `Withdrawal`, and `Trade`.
- `Ledger` - immutable append-only ledger history storing a sequence of entries.

Public functions and predicates:
- `EntryId(entry)` - extracts the ledger id from any entry.
- `IsValidEntry(entry)` - validates one ledger event.
- `IsValidLedgerId(id)` - checks that a ledger event id is positive.
- `IsValidLedger(ledger)` - validates all entries and uniqueness of ids.
- `ContainsLedgerId(entries, id)` - checks whether an id is already present in a ledger history.
- `AllUniqueLedgerIds(entries)` - checks that all ids in a history are unique.
- `Append(ledger, entry)` - returns a new immutable ledger with the new entry appended; requires a valid current ledger, a valid new entry, and a fresh id.
- `TotalDeposits(ledger)` - requires `IsValidLedger(ledger)` and sums all deposit amounts.
- `TotalWithdrawals(ledger)` - requires `IsValidLedger(ledger)` and sums all withdrawal amounts.
- `NetCashFlow(ledger)` - requires `IsValidLedger(ledger)` and computes deposits minus withdrawals, excluding trades.
