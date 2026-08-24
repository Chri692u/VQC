include "Types.dfy"
include "Validation.dfy"
include "Currency.dfy"
include "Orders.dfy"
include "Execution.dfy"
include "Positions.dfy"
include "Ledger.dfy"
include "AccountUtility.dfy"
include "AccountProof.dfy"

module AccountOps {
    import opened Types
    import opened Validation
    import opened Currency
    import opened Orders
    import opened Execution
    import opened Positions
    import opened LedgerOps
    import opened AccountUtility
    import opened AccountProof

    // Returns a new empty account.
    function NewAccount(): Account
    {
        Account(Money(0), Ledger([]), [], [])
    }

    // Adds a deposit to the account ledger and cash balance.
    function DepositCore(account: Account, id: LedgerId, amount: Money, timestamp: nat): Account
        requires CanDeposit(account, id, amount)
    {
        var entry := LedgerEntry.Deposit(id, amount, timestamp);
        var nextLedger := Append(account.ledger, entry);
        Account(
            Add(account.cash, amount),
            nextLedger,
            account.positions,
            account.orders
        )
    }

    // Removes a withdrawal from the account ledger and cash balance.
    function WithdrawCore(account: Account, id: LedgerId, amount: Money, timestamp: nat): Account
        requires CanWithdraw(account, id, amount)
    {
        var entry := LedgerEntry.Withdrawal(id, amount, timestamp);
        var nextLedger := Append(account.ledger, entry);
        Account(
            Sub(account.cash, amount),
            nextLedger,
            account.positions,
            account.orders
        )
    }

    // Adds a new order to the account.
    function PlaceOrderCore(account: Account, order: Order): Account
        requires CanPlaceOrder(account, order)
    {
        Account(
            account.cash,
            account.ledger,
            account.positions,
            account.orders + [order]
        )
    }

    // Updates an account with a fill against an existing order.
    function UpdateCore(account: Account, order: Order, fill: Fill): Account
        requires CanUpdate(account, order, fill)
    {
        var updatedOrder := Orders.ApplyFill(order, fill.quantity);
        var updatedOrders := UpsertOrder(account.orders, updatedOrder);
        var basePosition := PositionOrEmpty(account.positions, order.symbol);
        var nextPosition :=
            if order.side == Buy then 
                Positions.ApplyBuy(basePosition, fill) 
            else
                Positions.ApplySell(basePosition, fill);
        var updatedPositions := UpsertPosition(account.positions, nextPosition);
        var nextId := NextLedgerId(account.ledger);
        var tradeEntry := LedgerEntry.Trade(nextId, fill);
        NextLedgerIdIsFresh(account.ledger);
        var nextLedger := Append(account.ledger, tradeEntry);

        var executionValue := ExecutionValue(fill);
        var nextCash :=
            if order.side == Buy then
                Sub(account.cash, executionValue)
            else
                Add(account.cash, executionValue);

        Account(
            nextCash,
            nextLedger,
            updatedPositions,
            updatedOrders
        )
    }

    method Deposit(account: Account, id: LedgerId, amount: Money, timestamp: nat) returns (result: Account)
    {
        expect CanDeposit(account, id, amount);
        result := DepositCore(account, id, amount, timestamp);
    }

    method Withdraw(account: Account, id: LedgerId, amount: Money, timestamp: nat) returns (result: Account)
    {
        expect CanWithdraw(account, id, amount);
        result := WithdrawCore(account, id, amount, timestamp);
    }

    method PlaceOrder(account: Account, order: Order) returns (result: Account)
    {
        expect CanPlaceOrder(account, order);
        result := PlaceOrderCore(account, order);
    }

    method Update(account: Account, order: Order, fill: Fill) returns (result: Account)
    {
        expect CanUpdate(account, order, fill);
        result := UpdateCore(account, order, fill);
    }
}
