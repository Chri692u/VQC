include "Types.dfy"
include "Validation.dfy"
include "Currency.dfy"

module Orders {
    import opened Types
    import opened Validation

    // Returns the remaining unfilled quantity for an order.
    function RemainingQuantity(order: Order): nat
        requires IsValidOrder(order)
    {
        order.quantity - order.filledQuantity
    }

    // Returns the order after applying a status transition.
    function SetStatus(order: Order, newStatus: OrderStatus): Order
        requires CanSetOrderStatus(order, newStatus)
        ensures IsValidOrder(SetStatus(order, newStatus))
        ensures HasValidOrderStatus(SetStatus(order, newStatus))
        ensures SetStatus(order, newStatus).orderId == order.orderId
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
        requires CanApplyFill(order, fillQuantity)
        ensures IsValidOrder(ApplyFill(order, fillQuantity))
        ensures HasValidOrderStatus(ApplyFill(order, fillQuantity))
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
        requires CanCancelOrder(order)
        ensures IsValidOrder(Cancel(order))
        ensures HasValidOrderStatus(Cancel(order))
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
        requires CanRejectOrder(order)
        ensures IsValidOrder(Reject(order))
        ensures HasValidOrderStatus(Reject(order))
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
