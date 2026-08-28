include "Types.dfy"
include "Lifecycle.dfy"

module Validation {
    import opened Types
    import opened OrderLifecycle

    // Money checks.
    predicate IsZero(m: Money)
    {
        m.value == 0
    }

    predicate IsPositive(m: Money)
    {
        m.value > 0
    }

    predicate IsNegative(m: Money)
    {
        m.value < 0
    }

    // Identifier checks.
    predicate IsValidOrderId(orderId: OrderId)
    {
        orderId.value > 0
    }

    predicate IsValidExecutionId(executionId: ExecutionId)
    {
        executionId.value > 0
    }

    predicate IsValidLedgerId(ledgerId: LedgerId)
    {
        ledgerId.value > 0
    }

    // Shared checks.
    predicate HasNonEmptySymbol(symbol: string)
    {
        |symbol| > 0
    }

    // Order checks.
    predicate HasPositiveQuantity(order: Order)
    {
        order.quantity > 0
    }

    predicate HasBoundedFilledQuantity(order: Order)
    {
        order.filledQuantity <= order.quantity
    }

    predicate HasValidOrderSymbol(order: Order)
    {
        HasNonEmptySymbol(order.symbol)
    }

    predicate HasValidOrderType(order: Order)
    {
        match order.orderType
            case Market => true
            case Limit(limitPrice) => IsPositive(limitPrice)
            case Stop(stopPrice) => IsPositive(stopPrice)
            case StopLimit(stopPrice, limitPrice) =>
                IsPositive(stopPrice) && IsPositive(limitPrice)
    }

    // Status compatibility is a lifecycle rule. It is intentionally separate
    // from IsValidOrder, which describes a structurally well-formed snapshot.
    predicate HasValidOrderStatus(order: Order)
    {
        IsStatusCompatible(order.status, order.filledQuantity, order.quantity)
    }

    predicate HasRemainingQuantity(order: Order)
    {
        order.filledQuantity < order.quantity
    }

    predicate IsFullyFilled(order: Order)
    {
        order.filledQuantity == order.quantity
    }

    predicate IsUnfilled(order: Order)
    {
        order.filledQuantity == 0
    }

    // Lifecycle transition predicates. These group the semantic conditions
    // required by order operations without making them global validity rules.
    predicate CanSetOrderStatus(order: Order, newStatus: OrderStatus)
    {
        IsValidOrder(order) &&
        OrderLifecycle.CanSetStatus(
            order.status, order.filledQuantity, order.quantity, newStatus
        )
    }

    predicate CanApplyFill(order: Order, fillQuantity: nat)
    {
        IsValidOrder(order) &&
        OrderLifecycle.CanApplyFill(
            order.status, order.filledQuantity, order.quantity, fillQuantity
        )
    }

    predicate CanCancelOrder(order: Order)
    {
        IsValidOrder(order) &&
        OrderLifecycle.CanCancel(order.status, order.filledQuantity, order.quantity)
    }

    predicate CanRejectOrder(order: Order)
    {
        IsValidOrder(order) &&
        OrderLifecycle.CanReject(order.status, order.filledQuantity)
    }

    predicate IsValidOrder(order: Order)
    {
        IsValidOrderId(order.orderId) &&
        HasPositiveQuantity(order) &&
        HasBoundedFilledQuantity(order) &&
        HasValidOrderSymbol(order) &&
        HasValidOrderType(order)
    }

    predicate IsValidOrderSet(orders: seq<Order>)
    {
        (forall i :: 0 <= i < |orders| ==> IsValidOrder(orders[i])) &&
        (forall i, j :: 0 <= i < j < |orders| ==> orders[i].orderId != orders[j].orderId)
    }

    predicate HasLifecycleConsistentOrders(orders: seq<Order>)
    {
        forall i :: 0 <= i < |orders| ==> HasValidOrderStatus(orders[i])
    }

    // Sequence-editing predicates keep the collection helpers' contracts
    // aligned with the domain validity rules.
    predicate CanUpdateOrder(orders: seq<Order>, updated: Order)
    {
        IsValidOrderSet(orders) &&
        IsValidOrder(updated) &&
        exists i :: 0 <= i < |orders| && orders[i].orderId == updated.orderId
    }

    // Execution checks.
    predicate HasValidExecutionId(fill: Fill)
    {
        IsValidExecutionId(fill.executionId)
    }

    predicate HasValidFillQuantity(fill: Fill)
    {
        fill.quantity > 0
    }

    predicate HasValidFillSymbol(fill: Fill)
    {
        HasNonEmptySymbol(fill.symbol)
    }

    predicate IsValidFill(fill: Fill)
    {
        HasValidExecutionId(fill) &&
        HasValidFillQuantity(fill) &&
        HasValidFillSymbol(fill) &&
        IsPositive(fill.price)
    }

    // Position checks.
    // Returns true when the position has open quantity.
    predicate IsOpen(position: Position)
    {
        position.quantity > 0
    }

    // Returns true when the position is fully closed.
    predicate IsClosed(position: Position)
    {
        position.quantity == 0
    }
    
    predicate HasValidPositionSymbol(position: Position)
    {
        HasNonEmptySymbol(position.symbol)
    }

    predicate HasValidPositionAveragePrice(position: Position)
    {
        (IsClosed(position) && IsZero(position.averagePrice)) ||
        (IsOpen(position) && IsPositive(position.averagePrice))
    }

    predicate IsValidPosition(position: Position)
    {
        HasValidPositionSymbol(position) &&
        HasValidPositionAveragePrice(position)
    }

    predicate IsValidPositionSet(positions: seq<Position>)
    {
        // Account position sets contain active holdings only.
        (forall i :: 0 <= i < |positions| ==> IsValidPosition(positions[i]) && IsOpen(positions[i])) &&
        (forall i, j :: 0 <= i < j < |positions| ==> positions[i].symbol != positions[j].symbol)
    }

    predicate CanUpdatePosition(positions: seq<Position>, updated: Position)
    {
        IsValidPositionSet(positions) &&
        IsValidPosition(updated) &&
        exists i :: 0 <= i < |positions| && positions[i].symbol == updated.symbol
    }

    predicate CanUpsertPosition(positions: seq<Position>, updated: Position)
    {
        IsValidPositionSet(positions) &&
        IsValidPosition(updated) &&
        IsOpen(updated)
    }

    predicate CanRemovePosition(positions: seq<Position>, symbol: string)
    {
        IsValidPositionSet(positions) &&
        exists i :: 0 <= i < |positions| && positions[i].symbol == symbol
    }

    // Position transition predicates.
    predicate CanApplyBuy(position: Position, fill: Fill)
    {
        IsValidPosition(position) &&
        IsValidFill(fill) &&
        position.symbol == fill.symbol
    }

    predicate CanApplySell(position: Position, fill: Fill)
    {
        CanApplyBuy(position, fill) &&
        position.quantity >= fill.quantity
    }

    // Ledger checks.
    predicate ContainsLedgerId(entries: seq<LedgerEntry>, ledgerId: LedgerId)
    {
        exists i :: 0 <= i < |entries| && EntryId(entries[i]) == ledgerId
    }

    predicate AllUniqueLedgerIds(entries: seq<LedgerEntry>)
    {
        forall i, j :: 0 <= i < j < |entries| ==> EntryId(entries[i]) != EntryId(entries[j])
    }

    predicate IsValidEntry(entry: LedgerEntry)
    {
        match entry
            case Opening(ledgerId, _, positions, orders, _) =>
                IsValidLedgerId(ledgerId) &&
                IsValidPositionSet(positions) &&
                IsValidOrderSet(orders) &&
                HasLifecycleConsistentOrders(orders)
            case Deposit(ledgerId, amount, _) =>
                IsValidLedgerId(ledgerId) && IsPositive(amount)
            case Withdrawal(ledgerId, amount, _) =>
                IsValidLedgerId(ledgerId) && IsPositive(amount)
            case Trade(ledgerId, fill) =>
                IsValidLedgerId(ledgerId) && IsValidFill(fill)
    }

    predicate IsOpeningEntry(entry: LedgerEntry)
    {
        match entry
            case Opening(_, _, _, _, _) => true
            case _ => false
    }

    predicate HasOpeningOnlyAtStart(entries: seq<LedgerEntry>)
    {
        forall i :: 0 <= i < |entries| && IsOpeningEntry(entries[i]) ==> i == 0
    }

    predicate IsValidLedger(ledger: Ledger)
    {
        (forall i :: 0 <= i < |ledger.entries| ==> IsValidEntry(ledger.entries[i])) &&
        AllUniqueLedgerIds(ledger.entries) &&
        HasOpeningOnlyAtStart(ledger.entries)
    }

    // Ledger transition predicate.
    predicate CanAppendLedgerEntry(ledger: Ledger, entry: LedgerEntry)
    {
        IsValidLedger(ledger) &&
        IsValidEntry(entry) &&
        !IsOpeningEntry(entry) &&
        !ContainsLedgerId(ledger.entries, EntryId(entry))
    }

    // Account checks.
    predicate IsValidAccount(account: Account)
    {
        IsValidLedger(account.ledger) &&
        IsValidPositionSet(account.positions) &&
        IsValidOrderSet(account.orders)
    }
}
