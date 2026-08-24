include "Types.dfy"
include "Validation.dfy"
include "Currency.dfy"
include "Orders.dfy"

module Execution {
    import opened Types
    import opened Validation
    import opened Currency
    import opened Orders

    // Returns the monetary value of a fill.
    function ExecutionValue(fill: Fill): Money
        requires IsValidFill(fill)
    {
        Cost(fill.quantity, fill.price)
    }

    // Returns the total quantity across a sequence of fills.
    function TotalExecutedQuantity(fills: seq<Fill>): nat
        decreases |fills|
    {
        if |fills| == 0 then
            0
        else
            fills[0].quantity + TotalExecutedQuantity(fills[1..])
    }

    // Returns the total value across a sequence of valid fills.
    function TotalExecutedValue(fills: seq<Fill>): Money
        requires forall i :: 0 <= i < |fills| ==> IsValidFill(fills[i])
        decreases |fills|
    {
        if |fills| == 0 then
            Money(0)
        else
            Add(ExecutionValue(fills[0]), TotalExecutedValue(fills[1..]))
    }

    // Returns the total executed quantity for a specific order.
    function TotalExecutedQuantityForOrder(fills: seq<Fill>, order: Order): nat
        decreases |fills|
    {
        if |fills| == 0 then
            0
        else if BelongsToOrder(fills[0], order) then
            fills[0].quantity + TotalExecutedQuantityForOrder(fills[1..], order)
        else
            TotalExecutedQuantityForOrder(fills[1..], order)
    }

    // Returns true when a fill belongs to an order.
    predicate BelongsToOrder(fill: Fill, order: Order)
    {
        fill.orderId == order.orderId &&
        fill.symbol == order.symbol
    }

    // Returns true when a fill can be applied to this current order snapshot.
    // The order, rather than the fill, is the authoritative source of side and
    // lifecycle state.
    predicate IsApplicableFill(order: Order, fill: Fill)
    {
        IsValidFill(fill) &&
        BelongsToOrder(fill, order) &&
        CanApplyFill(order, fill.quantity)
    }

}
