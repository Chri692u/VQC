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
    // public proof boundary. Domain preservation lemmas live beside the
    // corresponding model: LedgerProof, OrderProof, and PositionProof.

    predicate CanDeposit(account: Account, ledgerId: LedgerId, amount: Money)
    {
        IsValidAccount(account) &&
        IsValidLedgerId(ledgerId) &&
        IsPositive(amount) &&
        !ContainsLedgerId(account.ledger.entries, ledgerId)
    }

    predicate CanBootstrap(
        cash: Money, positions: seq<Position>, orders: seq<Order>, ledgerId: LedgerId
    )
    {
        IsValidLedgerId(ledgerId) &&
        IsValidPositionSet(positions) &&
        IsValidOrderSet(orders) &&
        HasLifecycleConsistentOrders(orders)
    }

    predicate CanWithdraw(account: Account, ledgerId: LedgerId, amount: Money)
    {
        CanDeposit(account, ledgerId, amount) &&
        Gte(account.cash, amount)
    }

    predicate CanPlaceOrder(account: Account, order: Order)
    {
        IsValidAccount(account) &&
        IsValidOrder(order) &&
        HasValidOrderStatus(order) &&
        order.status == Pending &&
        order.filledQuantity == 0 &&
        !ExistsOrder(account.orders, order.orderId)
    }

    predicate CanSetAccountOrderStatus(
        account: Account, orderId: OrderId, newStatus: OrderStatus
    )
    {
        IsValidAccount(account) &&
        ExistsOrder(account.orders, orderId) &&
        var order := GetOrder(account.orders, orderId);
        CanSetOrderStatus(order, newStatus)
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
