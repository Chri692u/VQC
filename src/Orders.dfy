include "Types.dfy"
include "Validation.dfy"
include "Currency.dfy"

module Orders {
    import opened Types
    import opened Validation
    import opened Currency

    // Returns the remaining unfilled quantity for an order.
    function RemainingQuantity(order: Order): nat
        requires IsValidOrder(order)
    {
        order.quantity - order.filledQuantity
    }

    // Returns the order after applying a status transition.
    function SetStatus(order: Order, newStatus: OrderStatus): Order
        requires IsValidOrder(order)
        requires CanTransition(order.status, newStatus)
    {
        Order(
            order.orderId,
            order.symbol,
            order.quantity,
            order.side,
            order.orderType,
            newStatus,
            order.filledQuantity
        )
    }

    // Returns the order after accepting a fill amount.
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

    // Returns the order in a cancelled state.
    function Cancel(order: Order): Order
        requires IsValidOrder(order)
        requires order.status == New || order.status == Accepted || order.status == PartiallyFilled
    {
        Order(
            order.orderId,
            order.symbol,
            order.quantity,
            order.side,
            order.orderType,
            Cancelled,
            order.filledQuantity
        )
    }

    // Returns the order in a rejected state.
    function Reject(order: Order): Order
        requires IsValidOrder(order)
        requires order.status == New || order.status == Accepted
    {
        Order(
            order.orderId,
            order.symbol,
            order.quantity,
            order.side,
            order.orderType,
            Rejected,
            0
        )
    }
}
