include "Types.dfy"

module Validation {
    import opened Types

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
    predicate IsValidOrderId(id: OrderId)
    {
        id.value > 0
    }

    predicate IsValidExecutionId(id: ExecutionId)
    {
        id.value > 0
    }

    predicate IsValidLedgerId(id: LedgerId)
    {
        id.value > 0
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
    }

    // Status compatibility is a lifecycle rule. It is intentionally separate
    // from IsValidOrder, which describes a structurally well-formed snapshot.
    predicate IsOrderStatusCompatible(status: OrderStatus, filledQuantity: nat, quantity: nat)
    {
        match status
            case New => filledQuantity == 0
            case Accepted => filledQuantity == 0
            case PartiallyFilled => 0 < filledQuantity < quantity
            case Filled => filledQuantity == quantity
            case Cancelled => filledQuantity < quantity
            case Rejected => filledQuantity == 0
    }

    predicate HasValidOrderStatus(order: Order)
    {
        IsOrderStatusCompatible(order.status, order.filledQuantity, order.quantity)
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

    predicate CanAcceptFill(status: OrderStatus)
    {
        status == New || status == Accepted || status == PartiallyFilled
    }

    predicate CanTransition(fromStatus: OrderStatus, toStatus: OrderStatus)
    {
        fromStatus == toStatus ||
        (match fromStatus
            case New =>
                toStatus == Accepted || toStatus == PartiallyFilled || toStatus == Filled || toStatus == Cancelled || toStatus == Rejected
            case Accepted =>
                toStatus == PartiallyFilled || toStatus == Filled || toStatus == Cancelled || toStatus == Rejected
            case PartiallyFilled =>
                toStatus == Filled || toStatus == Cancelled || toStatus == Rejected
            case Filled =>
                toStatus == Filled
            case Cancelled =>
                toStatus == Cancelled
            case Rejected =>
                toStatus == Rejected)
    }

    // Lifecycle transition predicates. These group the semantic conditions
    // required by order operations without making them global validity rules.
    predicate CanSetOrderStatus(order: Order, newStatus: OrderStatus)
    {
        IsValidOrder(order) &&
        CanTransition(order.status, newStatus) &&
        IsOrderStatusCompatible(newStatus, order.filledQuantity, order.quantity)
    }

    predicate CanApplyFill(order: Order, fillQuantity: nat)
    {
        IsValidOrder(order) &&
        CanAcceptFill(order.status) &&
        fillQuantity > 0 &&
        fillQuantity <= order.quantity - order.filledQuantity
    }

    predicate CanCancelOrder(order: Order)
    {
        IsValidOrder(order) &&
        (order.status == New || order.status == Accepted || order.status == PartiallyFilled) &&
        HasRemainingQuantity(order)
    }

    predicate CanRejectOrder(order: Order)
    {
        IsValidOrder(order) &&
        (order.status == New || order.status == Accepted) &&
        IsUnfilled(order)
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
        (forall i :: 0 <= i < |positions| ==> IsValidPosition(positions[i])) &&
        (forall i, j :: 0 <= i < j < |positions| ==> positions[i].symbol != positions[j].symbol)
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
    predicate ContainsLedgerId(entries: seq<LedgerEntry>, id: LedgerId)
    {
        exists i :: 0 <= i < |entries| && EntryId(entries[i]) == id
    }

    predicate AllUniqueLedgerIds(entries: seq<LedgerEntry>)
    {
        forall i, j :: 0 <= i < j < |entries| ==> EntryId(entries[i]) != EntryId(entries[j])
    }

    predicate IsValidEntry(entry: LedgerEntry)
    {
        match entry
            case Opening(id, _, positions, orders, _) =>
                IsValidLedgerId(id) &&
                IsValidPositionSet(positions) &&
                IsValidOrderSet(orders) &&
                HasLifecycleConsistentOrders(orders)
            case Deposit(id, amount, _) =>
                IsValidLedgerId(id) && IsPositive(amount)
            case Withdrawal(id, amount, _) =>
                IsValidLedgerId(id) && IsPositive(amount)
            case Trade(id, fill) =>
                IsValidLedgerId(id) && IsValidFill(fill)
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
