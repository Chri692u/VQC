include "Currency.dfy"

module Orders {
	import opened Currency

	// ----------------------
	// Data types
	// ----------------------

	datatype OrderId = OrderId(value: nat)

	datatype OrderSide = Buy | Sell

	datatype OrderType = Market | Limit(limitPrice: Currency.Money)

	datatype OrderStatus = New | PartiallyFilled | Filled | Cancelled | Rejected

	datatype Order = Order(
		orderId: OrderId,
		symbol: string,
		quantity: nat,
		side: OrderSide,
		orderType: OrderType,
		status: OrderStatus,
		filledQuantity: nat
	)

	// ----------------------
	// General Predicates
	// ----------------------

	predicate IsOpenStatus(status: OrderStatus)
	{
		status == New || status == PartiallyFilled
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
		status == New || status == PartiallyFilled
	}

	predicate CanTransition(fromStatus: OrderStatus, toStatus: OrderStatus)
	{
		fromStatus == toStatus ||
		(match fromStatus
			case New => toStatus == PartiallyFilled || toStatus == Filled || toStatus == Cancelled || toStatus == Rejected
			case PartiallyFilled => toStatus == Filled || toStatus == Cancelled || toStatus == Rejected
			case Filled => toStatus == Filled
			case Cancelled => toStatus == Cancelled
			case Rejected => toStatus == Rejected)
	}

	// ----------------------
	// Validation
	// ----------------------

	predicate IsValidOrder(order: Order)
	{
		order.quantity > 0 &&
		0 <= order.filledQuantity <= order.quantity &&
		|order.symbol| > 0 &&
		(match order.orderType
			case Market => true
			case Limit(limitPrice) => Currency.Gt(limitPrice, Currency.Money(0))) &&
		(match order.status
			case New => IsUnfilled(order)
			case PartiallyFilled => 0 < order.filledQuantity < order.quantity
			case Filled => IsFullyFilled(order)
			case Cancelled => order.filledQuantity < order.quantity
			case Rejected => IsUnfilled(order))
	}

	// ----------------------
	// Derived Values
	// ----------------------

	function RemainingQuantity(order: Order): nat
		requires IsValidOrder(order)
	{
		order.quantity - order.filledQuantity
	}

	// ----------------------
	// State Transitions
	// ----------------------

	function SetStatus(order: Order, newStatus: OrderStatus): Order
		requires IsValidOrder(order)
		requires CanTransition(order.status, newStatus)
	{
		Order(order.orderId, order.symbol, order.quantity, order.side, order.orderType, newStatus, order.filledQuantity)
	}

	function ApplyFill(order: Order, fillQuantity: nat): Order
		requires IsValidOrder(order)
		requires CanAcceptFill(order.status)
		requires fillQuantity > 0
		requires fillQuantity <= RemainingQuantity(order)
	{
		Order(
			order.orderId,
			order.symbol,
			order.quantity,
			order.side,
			order.orderType,
			if order.filledQuantity + fillQuantity == order.quantity then Filled else PartiallyFilled,
			order.filledQuantity + fillQuantity
		)
	}

	// ----------------------
	// Terminal Actions
	// ----------------------

	function Cancel(order: Order): Order
		requires IsValidOrder(order)
		requires order.status == New || order.status == PartiallyFilled
	{
		Order(order.orderId, order.symbol, order.quantity, order.side, order.orderType, Cancelled, order.filledQuantity)
	}

	function Reject(order: Order): Order
		requires IsValidOrder(order)
		requires order.status == New
	{
		Order(order.orderId, order.symbol, order.quantity, order.side, order.orderType, Rejected, 0)
	}
}
