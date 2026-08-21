# VQC New API Overview

This document describes the public-facing Dafny API. It is intended as a concise reference for the primitives that are currently modelled in the project.

## Module: Types

Core shared domain types used throughout the system.

### Data types

- `Money` — immutable monetary value wrapper around `int`
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

## Module: Validation

Validation helpers for money, identifiers, orders, fills, positions, and ledger entries.

### Money predicates

- `IsZero(m: Money)`
- `IsPositive(m: Money)`
- `IsNegative(m: Money)`

### Shared predicates

- `HasNonEmptySymbol(symbol: string)`

### Order predicates

- `IsOpenStatus(status: OrderStatus)`
- `IsMarketOrder(order: Order)`
- `IsLimitOrder(order: Order)`
- `HasPositiveQuantity(order: Order)`
- `HasBoundedFilledQuantity(order: Order)`
- `HasValidOrderSymbol(order: Order)`
- `HasValidOrderType(order: Order)`
- `HasValidOrderStatus(order: Order)`
- `HasRemainingQuantity(order: Order)`
- `IsFullyFilled(order: Order)`
- `IsUnfilled(order: Order)`
- `CanAcceptFill(status: OrderStatus)`
- `CanTransition(fromStatus, toStatus)`
- `IsValidOrder(order: Order)`
- `IsValidOrderSet(orders: seq<Order>)`

### Execution predicates

- `HasValidExecutionId(fill: Fill)`
- `HasValidFillQuantity(fill: Fill)`
- `HasValidFillSymbol(fill: Fill)`
- `IsValidFill(fill: Fill)`

### Position predicates

- `HasValidPositionSymbol(position: Position)`
- `HasValidPositionAveragePrice(position: Position)`
- `IsOpen(position: Position)`
- `IsClosed(position: Position)`
- `IsValidPosition(position: Position)`
- `IsValidPositionSet(positions: seq<Position>)`

### Ledger predicates

- `IsValidLedgerId(id: LedgerId)`
- `HasLedgerEntryId(entry: LedgerEntry, id: LedgerId)`
- `ContainsLedgerId(entries: seq<LedgerEntry>, id: LedgerId)`
- `AllUniqueLedgerIds(entries: seq<LedgerEntry>)`
- `IsValidEntry(entry: LedgerEntry)`
- `IsValidLedger(ledger: Ledger)`
- `IsValidAccount(account: Account)`

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

## Module: Orders

Order-level logic and state transitions.

### Core functions

- `RemainingQuantity(order: Order): nat`
- `SetStatus(order: Order, newStatus: OrderStatus): Order`
- `ApplyFill(order: Order, fillQuantity: nat): Order`
- `Cancel(order: Order): Order`
- `Reject(order: Order): Order`

These functions are designed to preserve the order invariants while transitioning an order through its compliance and fill lifecycle.

---

## Module: Execution

Fill aggregation and execution semantics.

### Core functions

- `ExecutionValue(fill: Fill): Money`
- `TotalExecutedQuantity(fills: seq<Fill>): nat`
- `TotalExecutedValue(fills: seq<Fill>): Money`
- `TotalExecutedQuantityForOrder(fills: seq<Fill>, order: Order): nat`

### Predicates

- `BelongsToOrder(fill: Fill, order: Order)`

---

## Module: Positions

Position updates and value calculations.

### Core functions

- `PositionValue(position: Position): Money`
- `ApplyBuy(position: Position, fill: Fill): Position`
- `ApplySell(position: Position, fill: Fill): Position`

These functions update the average price and quantity in a way consistent with the model’s trading semantics.

---

## Module: LedgerOps

Ledger append and ledger-level accounting queries.

### Core functions

- `Append(ledger: Ledger, entry: LedgerEntry): Ledger`
- `TotalDeposits(ledger: Ledger): Money`
- `TotalWithdrawals(ledger: Ledger): Money`
- `NetCashFlow(ledger: Ledger): Money`

This module is intentionally narrow: its primary responsibilities are appending valid ledger entries and computing cash-flow summaries over an append-only history.

---

## Module: AccountOps

Account-level operations that update cash, ledger, positions, and orders together.

### Constructor

- `NewAccount(): Account`

### Ledger helpers

- `MaxLedgerId(entries: seq<LedgerEntry>): nat`
- `NextLedgerId(ledger: Ledger): LedgerId`

### Query and update helpers

- `ExistsOrder(orders: seq<Order>, target: OrderId)`
- `GetOrder(orders: seq<Order>, target: OrderId): Order`
- `ReplaceOrder(orders: seq<Order>, updated: Order): seq<Order>`
- `ExistsPosition(positions: seq<Position>, symbol: string)`
- `GetPosition(positions: seq<Position>, symbol: string): Position`
- `ReplacePosition(positions: seq<Position>, updated: Position): seq<Position>`
- `UpsertPosition(positions: seq<Position>, updated: Position): seq<Position>`

### Account transformations

- `Deposit(account: Account, id: LedgerId, amount: Money, timestamp: nat): Account`
- `Withdraw(account: Account, id: LedgerId, amount: Money, timestamp: nat): Account`
- `PlaceOrder(account: Account, order: Order): Account`
- `Update(account: Account, order: Order, fill: Fill): Account`

These operations are the main account-level API for applying financial events while preserving the verified invariants for ledger uniqueness, order validity, and position consistency.

---