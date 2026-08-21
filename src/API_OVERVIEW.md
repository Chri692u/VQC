# VQC API Overview

This document describes the public-facing Dafny API. It is intentionally limited to the operations a library consumer or integrator would use, and it excludes internal helper functions that are only used to implement account state transitions.

## Module: Types

Core shared domain types used throughout the system.

### Data types

- `Money` — immutable monetary value wrapper around `int` intended as fixed-scale linear integers
- `OrderId` — order identifier
- `ExecutionId` — execution/fill identifier
- `LedgerId` — ledger entry identifier
- `OrderSide` — `Buy | Sell`
- `OrderType` — `Market | Limit(limitPrice: Money)`
- `OrderStatus` — `New | PartiallyFilled | Filled | Cancelled | Rejected`
- `Order` — canonical order record
- `Fill` — execution record
- `Position` — symbol + quantity + average price
- `LedgerEntry` — `Deposit | Withdrawal | Trade`
- `Ledger` — append-only ledger history as `seq<LedgerEntry>`
- `Account` — cash + ledger + positions + orders

### Utility

- `EntryId(entry: LedgerEntry): LedgerId` — extracts the ledger id from any entry variant

---

## Module: Currency

Core arithmetic and comparison helpers for money.

### Constructors and arithmetic

- `Add(a: Money, b: Money): Money`
- `Sub(a: Money, b: Money): Money`
- `Neg(a: Money): Money`
- `Abs(a: Money): Money`
- `Sum(moneys: seq<Money>): Money`
- `Cost(qty: nat, price: Money): Money`

### Comparison predicates

- `Eq(a, b)`
- `Lt(a, b)`
- `Lte(a, b)`
- `Gt(a, b)`
- `Gte(a, b)`

---

## Module: AccountOps

Account-level operations that update cash, ledger, positions, and orders together.

### Constructor

- `NewAccount(): Account`

### Account transformations

- `Deposit(account: Account, id: LedgerId, amount: Money, timestamp: nat): Account`
- `Withdraw(account: Account, id: LedgerId, amount: Money, timestamp: nat): Account`
- `PlaceOrder(account: Account, order: Order): Account`
- `Update(account: Account, order: Order, fill: Fill): Account`

These operations are the main account-level API for applying financial events while preserving the verified invariants for ledger uniqueness, order validity, and position consistency.

---