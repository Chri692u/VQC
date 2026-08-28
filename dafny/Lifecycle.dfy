include "Types.dfy"

// Order-lifecycle rules live here so that execution, account, and broker
// boundaries cannot each invent their own interpretation of a status.
module OrderLifecycle {
    import opened Types

    predicate IsStatusCompatible(
        status: OrderStatus, filledQuantity: nat, quantity: nat
    )
    {
        match status
            case Pending => filledQuantity == 0
            case Open => filledQuantity == 0
            case PartiallyFilled => 0 < filledQuantity < quantity
            case Filled => filledQuantity == quantity
            case Cancelled => filledQuantity < quantity
            case Rejected => filledQuantity == 0
    }

    predicate CanAcceptFill(status: OrderStatus)
    {
        status == Pending || status == Open || status == PartiallyFilled
    }

    predicate CanTransition(fromStatus: OrderStatus, toStatus: OrderStatus)
    {
        fromStatus == toStatus ||
        (match fromStatus
            case Pending =>
                toStatus == Open || toStatus == PartiallyFilled ||
                toStatus == Filled || toStatus == Cancelled || toStatus == Rejected
            case Open =>
                toStatus == PartiallyFilled || toStatus == Filled ||
                toStatus == Cancelled || toStatus == Rejected
            case PartiallyFilled =>
                toStatus == Filled || toStatus == Cancelled
            case Filled => toStatus == Filled
            case Cancelled => toStatus == Cancelled
            case Rejected => toStatus == Rejected)
    }

    predicate CanSetStatus(
        status: OrderStatus,
        filledQuantity: nat,
        quantity: nat,
        newStatus: OrderStatus
    )
    {
        CanTransition(status, newStatus) &&
        IsStatusCompatible(newStatus, filledQuantity, quantity)
    }

    predicate CanApplyFill(
        status: OrderStatus,
        filledQuantity: nat,
        quantity: nat,
        fillQuantity: nat
    )
    {
        CanAcceptFill(status) &&
        fillQuantity > 0 &&
        filledQuantity <= quantity &&
        fillQuantity <= quantity - filledQuantity
    }

    predicate CanCancel(status: OrderStatus, filledQuantity: nat, quantity: nat)
    {
        CanAcceptFill(status) && filledQuantity < quantity
    }

    predicate CanReject(status: OrderStatus, filledQuantity: nat)
    {
        (status == Pending || status == Open) && filledQuantity == 0
    }
}
