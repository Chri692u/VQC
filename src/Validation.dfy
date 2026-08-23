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
    predicate IsOpenStatus(status: OrderStatus)
    {
        status == New || status == Accepted || status == PartiallyFilled
    }

    predicate IsMarketOrder(order: Order)
    {
        order.orderType == Market
    }

    predicate IsLimitOrder(order: Order)
    {
        match order.orderType
            case Market => false
            case Limit(_) => true
    }

    predicate HasPositiveQuantity(order: Order)
    {
        order.quantity > 0
    }

    predicate HasBoundedFilledQuantity(order: Order)
    {
        0 <= order.filledQuantity <= order.quantity
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

    predicate HasValidOrderStatus(order: Order)
    {
        match order.status
            case New => IsUnfilled(order)
            case Accepted => IsUnfilled(order)
            case PartiallyFilled => 0 < order.filledQuantity < order.quantity
            case Filled => IsFullyFilled(order)
            case Cancelled => order.filledQuantity < order.quantity
            case Rejected => IsUnfilled(order)
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

    predicate IsValidOrder(order: Order)
    {
        HasPositiveQuantity(order) &&
        HasBoundedFilledQuantity(order) &&
        HasValidOrderSymbol(order) &&
        HasValidOrderType(order) &&
        HasValidOrderStatus(order)
    }

    predicate IsValidOrderSet(orders: seq<Order>)
    {
        (forall i :: 0 <= i < |orders| ==> IsValidOrder(orders[i])) &&
        (forall i, j :: 0 <= i < j < |orders| ==> orders[i].orderId != orders[j].orderId)
    }

    // Execution checks.
    predicate HasValidExecutionId(fill: Fill)
    {
        fill.executionId.value > 0
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
        (position.quantity == 0 && IsZero(position.averagePrice)) ||
        (position.quantity > 0 && IsPositive(position.averagePrice))
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

    // Ledger checks.
    predicate HasLedgerEntryId(entry: LedgerEntry, id: LedgerId)
    {
        EntryId(entry) == id
    }

    predicate ContainsLedgerId(entries: seq<LedgerEntry>, id: LedgerId)
    {
        exists i :: 0 <= i < |entries| && HasLedgerEntryId(entries[i], id)
    }

    predicate AllUniqueLedgerIds(entries: seq<LedgerEntry>)
    {
        forall i, j :: 0 <= i < j < |entries| ==> !HasLedgerEntryId(entries[i], EntryId(entries[j]))
    }

    predicate IsValidEntry(entry: LedgerEntry)
    {
        match entry
            case Deposit(id, amount, _) =>
                IsValidLedgerId(id) && IsPositive(amount)
            case Withdrawal(id, amount, _) =>
                IsValidLedgerId(id) && IsPositive(amount)
            case Trade(id, fill) =>
                IsValidLedgerId(id) && IsValidFill(fill)
    }

    predicate IsValidLedger(ledger: Ledger)
    {
        (forall i :: 0 <= i < |ledger.entries| ==> IsValidEntry(ledger.entries[i])) &&
        AllUniqueLedgerIds(ledger.entries)
    }

    // Account checks.
    predicate IsValidAccount(account: Account)
    {
        IsValidLedger(account.ledger) &&
        IsValidPositionSet(account.positions) &&
        IsValidOrderSet(account.orders)
    }
}
