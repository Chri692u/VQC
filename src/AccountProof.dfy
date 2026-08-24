include "Types.dfy"
include "Validation.dfy"
include "Currency.dfy"
include "Execution.dfy"
include "AccountUtility.dfy"

module AccountProof {
    import opened Types
    import opened Validation
    import opened Currency
    import opened Execution
    import opened AccountUtility

    // Account-operation contracts. AccountOps uses these predicates as its
    // public proof boundary;

    lemma EntryIdAtMostMaxLedgerId(entries: seq<LedgerEntry>, index: int)
        requires 0 <= index < |entries|
        ensures EntryId(entries[index]).value <= MaxLedgerId(entries)
        decreases |entries|
    {
        if index == 0 {
        } else {
            EntryIdAtMostMaxLedgerId(entries[1..], index - 1);
        }
    }

    // The next generated ID cannot already occur in the ledger.
    lemma NextLedgerIdIsFresh(ledger: Ledger)
        requires IsValidLedger(ledger)
        ensures !ContainsLedgerId(ledger.entries, NextLedgerId(ledger))
    {
        forall index {:trigger ledger.entries[index]}
            | 0 <= index < |ledger.entries|
            ensures EntryId(ledger.entries[index]) != NextLedgerId(ledger)
        {
            EntryIdAtMostMaxLedgerId(ledger.entries, index);
        }
    }

    lemma PrependOrderPreservesValidity(head: Order, tail: seq<Order>)
        requires IsValidOrder(head)
        requires IsValidOrderSet(tail)
        requires !ExistsOrder(tail, head.orderId)
        ensures IsValidOrderSet([head] + tail)
    {
    }

    lemma UpdateOrderPreservesMissingId(orders: seq<Order>, updated: Order, id: OrderId)
        requires IsValidOrderSet(orders)
        requires IsValidOrder(updated)
        requires ExistsOrder(orders, updated.orderId)
        requires !ExistsOrder(orders, id)
        ensures !ExistsOrder(UpdateOrder(orders, updated), id)
        decreases |orders|
    {
        if orders[0].orderId != updated.orderId {
            assert !ExistsOrder(orders[1..], id);
            UpdateOrderPreservesMissingId(orders[1..], updated, id);
        }
    }

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

    lemma PrependPositionPreservesValidity(head: Position, tail: seq<Position>)
        requires IsValidPosition(head)
        requires IsValidPositionSet(tail)
        requires !ExistsPosition(tail, head.symbol)
        ensures IsValidPositionSet([head] + tail)
    {
    }

    lemma UpsertPositionPreservesMissingSymbol(
        positions: seq<Position>, updated: Position, symbol: string
    )
        requires IsValidPositionSet(positions)
        requires IsValidPosition(updated)
        requires !ExistsPosition(positions, symbol)
        requires updated.symbol != symbol
        ensures !ExistsPosition(UpsertPosition(positions, updated), symbol)
        decreases |positions|
    {
        if |positions| > 0 && positions[0].symbol != updated.symbol {
            assert !ExistsPosition(positions[1..], symbol);
            UpsertPositionPreservesMissingSymbol(positions[1..], updated, symbol);
        }
    }

    lemma UpsertPositionPreservesValidity(positions: seq<Position>, updated: Position)
        requires IsValidPositionSet(positions)
        requires IsValidPosition(updated)
        ensures IsValidPositionSet(UpsertPosition(positions, updated))
        decreases |positions|
    {
        if |positions| == 0 {
            PrependPositionPreservesValidity(updated, []);
        } else if positions[0].symbol == updated.symbol {
            assert !ExistsPosition(positions[1..], updated.symbol);
            PrependPositionPreservesValidity(updated, positions[1..]);
        } else {
            assert !ExistsPosition(positions[1..], positions[0].symbol);
            UpsertPositionPreservesMissingSymbol(
                positions[1..], updated, positions[0].symbol
            );
            UpsertPositionPreservesValidity(positions[1..], updated);
            PrependPositionPreservesValidity(
                positions[0], UpsertPosition(positions[1..], updated)
            );
        }
    }

    predicate CanDeposit(account: Account, id: LedgerId, amount: Money)
    {
        IsValidAccount(account) &&
        IsValidLedgerId(id) &&
        IsPositive(amount) &&
        !ContainsLedgerId(account.ledger.entries, id)
    }

    predicate CanBootstrap(cash: Money, positions: seq<Position>, orders: seq<Order>, id: LedgerId)
    {
        IsValidLedgerId(id) &&
        IsValidPositionSet(positions) &&
        IsValidOrderSet(orders) &&
        HasLifecycleConsistentOrders(orders)
    }

    predicate CanWithdraw(account: Account, id: LedgerId, amount: Money)
    {
        CanDeposit(account, id, amount) &&
        Gte(account.cash, amount)
    }

    predicate CanPlaceOrder(account: Account, order: Order)
    {
        IsValidAccount(account) &&
        IsValidOrder(order) &&
        !ExistsOrder(account.orders, order.orderId)
    }

    predicate CanUpdate(account: Account, fill: Fill)
    {
        IsValidAccount(account) &&
        ExistsOrder(account.orders, fill.orderId) &&
        var order := GetOrder(account.orders, fill.orderId);
        IsApplicableFill(order, fill) &&
        (order.side == Buy || ExistsPosition(account.positions, order.symbol)) &&
        (order.side == Sell ==>
            ExistsPosition(account.positions, order.symbol) &&
            GetPosition(account.positions, order.symbol).quantity >= fill.quantity)
    }
}
