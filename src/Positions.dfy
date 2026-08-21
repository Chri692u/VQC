include "Types.dfy"
include "Validation.dfy"
include "Currency.dfy"
include "Execution.dfy"

module Positions {
    import opened Types
    import opened Validation
    import opened Currency
    import opened Execution

    // Returns the current value of a position.
    function PositionValue(position: Position): Money
        requires IsValidPosition(position)
    {
        Cost(position.quantity, position.averagePrice)
    }

    // Returns a position after applying a buy fill.
    function ApplyBuy(position: Position, fill: Fill): Position
        requires IsValidPosition(position)
        requires IsValidFill(fill)
        requires position.symbol == fill.symbol
    {
        Position(
            position.symbol,
            position.quantity + fill.quantity,
            if position.quantity == 0 then
                fill.price
            else
                Money(
                    (position.averagePrice.value * position.quantity + fill.price.value * fill.quantity) /
                    (position.quantity + fill.quantity)
                )
        )
    }

    // Returns a position after applying a sell fill.
    function ApplySell(position: Position, fill: Fill): Position
        requires IsValidPosition(position)
        requires IsValidFill(fill)
        requires position.symbol == fill.symbol
        requires position.quantity >= fill.quantity
    {
        Position(
            position.symbol,
            position.quantity - fill.quantity,
            if position.quantity == fill.quantity then
                Money(0)
            else
                position.averagePrice
        )
    }
}
