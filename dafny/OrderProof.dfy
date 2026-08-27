include "Types.dfy"
include "Validation.dfy"
include "AccountUtility.dfy"

module OrderProof {
    import opened Types
    import opened Validation
    import opened AccountUtility

    // Adding a fresh valid order preserves a valid unique order set.
    lemma PrependOrderPreservesValidity(head: Order, tail: seq<Order>)
        requires IsValidOrder(head)
        requires IsValidOrderSet(tail)
        requires !ExistsOrder(tail, head.orderId)
        ensures IsValidOrderSet([head] + tail)
    {
    }

    // Replacing one order cannot introduce an ID which was previously absent.
    lemma UpdateOrderPreservesMissingId(
        orders: seq<Order>, updated: Order, orderId: OrderId
    )
        requires IsValidOrderSet(orders)
        requires IsValidOrder(updated)
        requires ExistsOrder(orders, updated.orderId)
        requires !ExistsOrder(orders, orderId)
        ensures !ExistsOrder(UpdateOrder(orders, updated), orderId)
        decreases |orders|
    {
        if orders[0].orderId != updated.orderId {
            assert !ExistsOrder(orders[1..], orderId);
            UpdateOrderPreservesMissingId(orders[1..], updated, orderId);
        }
    }

    // Replacing an existing order by a valid version preserves set validity.
    lemma UpdateOrderPreservesValidity(orders: seq<Order>, updated: Order)
        requires IsValidOrderSet(orders)
        requires IsValidOrder(updated)
        requires ExistsOrder(orders, updated.orderId)
        ensures IsValidOrderSet(UpdateOrder(orders, updated))
        decreases |orders|
    {
        if orders[0].orderId == updated.orderId {
            assert !ExistsOrder(orders[1..], updated.orderId);
            PrependOrderPreservesValidity(updated, orders[1..]);
        } else {
            assert !ExistsOrder(orders[1..], orders[0].orderId);
            UpdateOrderPreservesMissingId(orders[1..], updated, orders[0].orderId);
            UpdateOrderPreservesValidity(orders[1..], updated);
            PrependOrderPreservesValidity(orders[0], UpdateOrder(orders[1..], updated));
        }
    }
}
