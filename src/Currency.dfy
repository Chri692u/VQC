module Currency {
	datatype Money = Money(value: int)

	// ----------------------
	// Arithmetics
	// ----------------------

	function Add(a: Money, b: Money): Money
	{
		Money(a.value + b.value)
	}

	function Sub(a: Money, b: Money): Money
	{
		Money(a.value - b.value)
	}

	function Neg(a: Money): Money
	{
		Money(-a.value)
	}

	function Abs(a: Money): Money
	{
		if a.value < 0 then Money(-a.value) else a
	}

	// ----------------------
	// Comparisons
	// ----------------------

	predicate Eq(a: Money, b: Money)
	{
		a.value == b.value
	}

	predicate Lt(a: Money, b: Money)
	{
		a.value < b.value
	}

	predicate Lte(a: Money, b: Money)
	{
		a.value <= b.value
	}

	predicate Gt(a: Money, b: Money)
	{
		a.value > b.value
	}

	predicate Gte(a: Money, b: Money)
	{
		a.value >= b.value
	}

	// ----------------------
	// Predicates
	// ----------------------

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

	// ----------------------
	// Primitives
	// ----------------------

	function Sum(moneys: seq<Money>): Money
		decreases |moneys|
	{
		if |moneys| == 0 then Money(0) else Add(moneys[0], Sum(moneys[1..]))
	}

	// Computes trade notional as quantity times unit price.
	function Cost(qty: nat, price: Money): Money
	{
		Money(qty as int * price.value)
	}
}
