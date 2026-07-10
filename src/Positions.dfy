include "Currency.dfy"
include "Execution.dfy"

module Positions {
    import opened Currency
    import opened Execution
    
    datatype Position = Position(
        symbol: string,
        quantity: nat,
        averagePrice: Currency.Money
    )

    // ----------------------
	// Validation
	// ----------------------

    predicate IsValidPosition(pos: Position)
    {
        |pos.symbol| > 0 &&
        (
            (pos.quantity == 0 && Currency.IsZero(pos.averagePrice)) ||
            (pos.quantity > 0 && Currency.IsPositive(pos.averagePrice))
        )
    }

    predicate isOpen(pos: Position)
    {
        pos.quantity > 0
    }

    predicate isClosed(pos: Position)
    {
        pos.quantity == 0
    }

    // ----------------------
	// Primitives
	// ----------------------
    function PositionValue (pos: Position): Currency.Money
        requires IsValidPosition(pos)
    {
        Currency.Cost(pos.quantity, pos.averagePrice)
    }

    function ApplyBuy(pos: Position, fill: Fill): Position
        requires IsValidPosition(pos)
        requires IsValidFill(fill)
        requires pos.symbol == fill.symbol
    {
        Position(
            pos.symbol,
            pos.quantity + fill.quantity,
            if pos.quantity == 0 then
                fill.price
            else
                Currency.Money(
                    (pos.averagePrice.value * pos.quantity + fill.price.value * fill.quantity) / (pos.quantity + fill.quantity)
                )
        )
    }

    function ApplySell(pos: Position, fill: Fill): Position
        requires IsValidPosition(pos)
        requires IsValidFill(fill)
        requires pos.symbol == fill.symbol
        requires pos.quantity >= fill.quantity
    {
        Position(
            pos.symbol,
            pos.quantity - fill.quantity,
            if pos.quantity == fill.quantity then
                Currency.Money(0)
            else
                pos.averagePrice
        )
    }
}