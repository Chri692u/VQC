module Types {
    // Core numeric value used across money-based operations.
    datatype Money = Money(value: int)

    // Identifiers.
    datatype OrderId = OrderId(value: nat)
    datatype ExecutionId = ExecutionId(value: nat)
    datatype LedgerId = LedgerId(value: nat)

    // Order lifecycle and pricing.
    datatype OrderSide = Buy | Sell
    datatype OrderType = Market | Limit(limitPrice: Money)
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

    // Execution and fill representation.
    datatype Fill = Fill(
        executionId: ExecutionId,
        orderId: OrderId,
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
        | Deposit(id: LedgerId, amount: Money, timestamp: nat)
        | Withdrawal(id: LedgerId, amount: Money, timestamp: nat)
        | Trade(id: LedgerId, fill: Fill)

    datatype Ledger = Ledger(entries: seq<LedgerEntry>)

    // Returns the ledger identifier associated with any ledger entry.
    function EntryId(entry: LedgerEntry): LedgerId
    {
        match entry
            case Deposit(id, _, _) => id
            case Withdrawal(id, _, _) => id
            case Trade(id, _) => id
    }

    // Account state.
    datatype Account = Account(
        cash: Money,
        ledger: Ledger,
        positions: seq<Position>,
        orders: seq<Order>
    )
}
