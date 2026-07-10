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
		if |fills| == 0 then true else IsValidFill(fills[0]) && AllValidFills(fills[1..])
	}

	// ----------------------
	// Derived Values
	// ----------------------

	function ExecutionValue(fill: Fill): Currency.Money
		requires IsValidFill(fill)
	{
		Currency.Cost(fill.quantity, fill.price)
	}

	function ExecutionValues(fills: seq<Fill>): seq<Currency.Money>
		requires AllValidFills(fills)
		decreases |fills|
	{
		if |fills| == 0 then
			[]
		else
			[ExecutionValue(fills[0])] + ExecutionValues(fills[1..])
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
	{
		Currency.Sum(ExecutionValues(fills))
	}

	function AverageExecutionPrice(fills: seq<Fill>): Currency.Money
		requires AllValidFills(fills)
		requires TotalExecutedQuantity(fills) > 0
	{
		Currency.Money(TotalExecutedValue(fills).value / TotalExecutedQuantity(fills))
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

	function ExecutionValuesForOrder(fills: seq<Fill>, order: Order): seq<Currency.Money>
		requires IsValidOrder(order)
		requires AllValidFills(fills)
		decreases |fills|
	{
		if |fills| == 0 then
			[]
		else if BelongsToOrder(fills[0], order) then
			[ExecutionValue(fills[0])] + ExecutionValuesForOrder(fills[1..], order)
		else
			ExecutionValuesForOrder(fills[1..], order)
	}

	function TotalExecutedValueForOrder(fills: seq<Fill>, order: Order): Currency.Money
		requires IsValidOrder(order)
		requires AllValidFills(fills)
	{
		Currency.Sum(ExecutionValuesForOrder(fills, order))
	}

	// ----------------------
	// Matching Helpers (this is sub-optimal and should probably be worked around later)
	// ----------------------

	predicate BelongsToOrder(fill: Fill, order: Order)
	{
		fill.orderId == order.orderId && fill.symbol == order.symbol
	}

	predicate SameOrder(fill1: Fill, fill2: Fill)
	{
		fill1.orderId == fill2.orderId && fill1.symbol == fill2.symbol
	}

	predicate AllBelongToOrder(fills: seq<Fill>, order: Order)
		decreases |fills|
	{
		if |fills| == 0 then
			true
		else
			BelongsToOrder(fills[0], order) && AllBelongToOrder(fills[1..], order)
	}

	predicate FillsAccountForOrder(fills: seq<Fill>, order: Order)
		requires IsValidOrder(order)
	{
		AllBelongToOrder(fills, order) && TotalExecutedQuantityForOrder(fills, order) == order.quantity
	}

	predicate FillsDoNotExceedOrder(fills: seq<Fill>, order: Order)
		requires IsValidOrder(order)
	{
		AllBelongToOrder(fills, order) && TotalExecutedQuantityForOrder(fills, order) <= order.quantity
	}
}
