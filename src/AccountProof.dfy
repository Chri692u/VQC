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

    predicate CanDeposit(account: Account, id: LedgerId, amount: Money)
    {
        IsValidAccount(account) &&
        IsValidLedgerId(id) &&
        IsPositive(amount) &&
        !ContainsLedgerId(account.ledger.entries, id)
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

    predicate CanUpdate(account: Account, order: Order, fill: Fill)
    {
        IsValidAccount(account) &&
        IsApplicableFill(order, fill) &&
        (order.side == Buy || ExistsPosition(account.positions, order.symbol)) &&
        (order.side == Sell ==>
            ExistsPosition(account.positions, order.symbol) &&
            GetPosition(account.positions, order.symbol).quantity >= fill.quantity)
    }
}
