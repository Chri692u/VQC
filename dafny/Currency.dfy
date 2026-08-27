include "Types.dfy"
include "Validation.dfy"

module Currency {
    import opened Types

    // Adds two money values.
    function Add(a: Money, b: Money): Money
    {
        Money(a.value + b.value)
    }

    // Subtracts one money value from another.
    function Sub(a: Money, b: Money): Money
    {
        Money(a.value - b.value)
    }

    // Negates a money value.
    function Neg(a: Money): Money
    {
        Money(-a.value)
    }

    // Returns the absolute value of a money amount.
    function Abs(a: Money): Money
    {
        if a.value < 0 then Money(-a.value) else a
    }

    // Returns true when two money values are equal.
    predicate Eq(a: Money, b: Money)
    {
        a.value == b.value
    }

    // Returns true when a is less than b.
    predicate Lt(a: Money, b: Money)
    {
        a.value < b.value
    }

    // Returns true when a is less than or equal to b.
    predicate Lte(a: Money, b: Money)
    {
        a.value <= b.value
    }

    // Returns true when a is greater than b.
    predicate Gt(a: Money, b: Money)
    {
        a.value > b.value
    }

    // Returns true when a is greater than or equal to b.
    predicate Gte(a: Money, b: Money)
    {
        a.value >= b.value
    }

    // Sums a sequence of money values.
    function Sum(values: seq<Money>): Money
        decreases |values|
    {
        if |values| == 0 then
            Money(0)
        else
            Add(values[0], Sum(values[1..]))
    }

    // Computes notional value as quantity times unit price.
    function Cost(quantity: nat, price: Money): Money
    {
        Money(quantity as int * price.value)
    }
}
