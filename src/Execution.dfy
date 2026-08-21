include "Orders.dfy"

module Execution {
    import opened Currency
    import opened Orders

    // ----------------------
    // Identifiers
    // ----------------------

    datatype ExecutionId = ExecutionId(value: nat)

    // ----------------------
    // Fill Representation
    // ----------------------

    datatype Fill = Fill(
        executionId: ExecutionId,
        orderId: OrderId,
        symbol: string,
        quantity: nat,
        price: Currency.Money,
        timestamp: nat
    )

    // ----------------------
    // Validation
    // ----------------------

    predicate IsValidFill(fill: Fill)
    {
        fill.executionId.value > 0 &&
        fill.quantity > 0 &&
        |fill.symbol| > 0 &&
        Currency.IsPositive(fill.price)
    }

    predicate AllValidFills(fills: seq<Fill>)
        decreases |fills|
    {
        if |fills| == 0 then
            true
        else
            IsValidFill(fills[0]) &&
            AllValidFills(fills[1..])
    }

    // ----------------------
    // Derived Values
    // ----------------------

    function ExecutionValue(fill: Fill): Currency.Money
        requires IsValidFill(fill)
    {
        Currency.Cost(fill.quantity, fill.price)
    }

    // ----------------------
    // Aggregation
    // ----------------------

    function TotalExecutedQuantity(fills: seq<Fill>): nat
        decreases |fills|
    {
        if |fills| == 0 then
            0
        else
            fills[0].quantity + TotalExecutedQuantity(fills[1..])
    }

    function TotalExecutedValue(fills: seq<Fill>): Currency.Money
        requires AllValidFills(fills)
        decreases |fills|
    {
        if |fills| == 0 then
            Currency.Money(0)
        else
            Currency.Add(
                ExecutionValue(fills[0]),
                TotalExecutedValue(fills[1..])
            )
    }

    function TotalExecutedQuantityForOrder(fills: seq<Fill>, order: Order): nat
        requires IsValidOrder(order)
        decreases |fills|
    {
        if |fills| == 0 then
            0
        else if BelongsToOrder(fills[0], order) then
            fills[0].quantity + TotalExecutedQuantityForOrder(fills[1..], order)
        else
            TotalExecutedQuantityForOrder(fills[1..], order)
    }

    // ----------------------
    // Matching
    // ----------------------

    predicate BelongsToOrder(fill: Fill, order: Order)
    {
        fill.orderId == order.orderId &&
        fill.symbol == order.symbol
    }
}