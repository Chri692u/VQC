module Types {
    // Core numeric value used across money-based operations.
    datatype Money = Money(value: int)

    // Identifiers.
    datatype OrderId = OrderId(value: nat)
    datatype ExecutionId = ExecutionId(value: nat)
    datatype LedgerId = LedgerId(value: nat)

    // Order lifecycle and pricing.
    datatype OrderSide = Buy | Sell
    datatype OrderType =
        | Market
        | Limit(limitPrice: Money)
        | Stop(stopPrice: Money)
        | StopLimit(stopPrice: Money, limitPrice: Money)
    datatype OrderStatus = New | Accepted | PartiallyFilled | Filled | Cancelled | Rejected

    // Order representation.
    datatype Order = Order(
        orderId: OrderId,
        symbol: string,
        quantity: nat,
        side: OrderSide,
        orderType: OrderType,
        status: OrderStatus,
        filledQuantity: nat
    )

    // Execution and fill representation. The order supplies the economic side
    // (buy or sell); a fill records the priced quantity executed against it.
    datatype Fill = Fill(
        executionId: ExecutionId,
        orderId: OrderId, // References the authoritative order.
        symbol: string,
        quantity: nat,
        price: Money,
        timestamp: nat
    )

    // Position representation.
    datatype Position = Position(
        symbol: string,
        quantity: nat,
        averagePrice: Money
    )

    // Ledger history.
    datatype LedgerEntry =
        | Opening(
            ledgerId: LedgerId,
            cash: Money,
            positions: seq<Position>,
            orders: seq<Order>,
            timestamp: nat
        )
        | Deposit(ledgerId: LedgerId, amount: Money, timestamp: nat)
        | Withdrawal(ledgerId: LedgerId, amount: Money, timestamp: nat)
        | Trade(ledgerId: LedgerId, fill: Fill)

    datatype Ledger = Ledger(entries: seq<LedgerEntry>)

    // Returns the ledger identifier associated with any ledger entry.
    function EntryId(entry: LedgerEntry): LedgerId
    {
        match entry
            case Opening(ledgerId, _, _, _, _) => ledgerId
            case Deposit(ledgerId, _, _) => ledgerId
            case Withdrawal(ledgerId, _, _) => ledgerId
            case Trade(ledgerId, _) => ledgerId
    }

    // Account state.
    datatype Account = Account(
        cash: Money,
        ledger: Ledger,
        positions: seq<Position>,
        orders: seq<Order>
    )
}
