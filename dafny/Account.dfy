include "Types.dfy"
include "Validation.dfy"
include "Currency.dfy"
include "Orders.dfy"
include "Execution.dfy"
include "Positions.dfy"
include "Ledger.dfy"
include "AccountUtility.dfy"
include "AccountProof.dfy"
include "LedgerProof.dfy"
include "OrderProof.dfy"
include "PositionProof.dfy"

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
    import opened LedgerProof
    import opened OrderProof
    import opened PositionProof

    // Returns a new empty account.
    function NewAccount(): Account
        ensures IsValidAccount(NewAccount())
    {
        Account(Money(0), Ledger([]), [], [])
    }

    // Creates an account from one trusted broker-state snapshot.
    function BootstrapCore(
        cash: Money,
        positions: seq<Position>,
        orders: seq<Order>,
        ledgerId: LedgerId,
        timestamp: nat
    ): Account
        requires CanBootstrap(cash, positions, orders, ledgerId)
        ensures IsValidAccount(BootstrapCore(cash, positions, orders, ledgerId, timestamp))
        ensures BootstrapCore(cash, positions, orders, ledgerId, timestamp).cash == cash
        ensures BootstrapCore(cash, positions, orders, ledgerId, timestamp).positions == positions
        ensures BootstrapCore(cash, positions, orders, ledgerId, timestamp).orders == orders
        ensures BootstrapCore(cash, positions, orders, ledgerId, timestamp).ledger ==
            Ledger([Opening(ledgerId, cash, positions, orders, timestamp)])
    {
        Account(
            cash,
            Ledger([Opening(ledgerId, cash, positions, orders, timestamp)]),
            positions,
            orders
        )
    }

    // Adds a deposit to the account ledger and cash balance.
    function DepositCore(
        account: Account, ledgerId: LedgerId, amount: Money, timestamp: nat
    ): Account
        requires CanDeposit(account, ledgerId, amount)
        ensures IsValidAccount(DepositCore(account, ledgerId, amount, timestamp))
    {
        var entry := LedgerEntry.Deposit(ledgerId, amount, timestamp);
        var nextLedger := Append(account.ledger, entry);
        Account(
            Add(account.cash, amount),
            nextLedger,
            account.positions,
            account.orders
        )
    }

    // Removes a withdrawal from the account ledger and cash balance.
    function WithdrawCore(
        account: Account, ledgerId: LedgerId, amount: Money, timestamp: nat
    ): Account
        requires CanWithdraw(account, ledgerId, amount)
        ensures IsValidAccount(WithdrawCore(account, ledgerId, amount, timestamp))
    {
        var entry := LedgerEntry.Withdrawal(ledgerId, amount, timestamp);
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
        ensures IsValidAccount(PlaceOrderCore(account, order))
    {
        Account(
            account.cash,
            account.ledger,
            account.positions,
            account.orders + [order]
        )
    }

    // Updates the lifecycle status of an existing order without an execution.
    function SetOrderStatusCore(
        account: Account, orderId: OrderId, newStatus: OrderStatus
    ): Account
        requires CanSetAccountOrderStatus(account, orderId, newStatus)
        ensures IsValidAccount(SetOrderStatusCore(account, orderId, newStatus))
    {
        var order := GetOrder(account.orders, orderId);
        var updatedOrder := Orders.SetStatus(order, newStatus);
        // Lemma invocation.
        UpdateOrderPreservesValidity(account.orders, updatedOrder);
        Account(
            account.cash,
            account.ledger,
            account.positions,
            UpdateOrder(account.orders, updatedOrder)
        )
    }

    // Updates an account with a fill against an existing order.
    function UpdateCore(account: Account, fill: Fill): Account
        requires CanUpdate(account, fill)
        ensures IsValidAccount(UpdateCore(account, fill))
    {
        var order := GetOrder(account.orders, fill.orderId);
        var updatedOrder := Orders.ApplyFill(order, fill.quantity);
        
        // Lemma invocation.
        UpdateOrderPreservesValidity(account.orders, updatedOrder);
        var updatedOrders := UpdateOrder(account.orders, updatedOrder);
        var basePosition := PositionOrEmpty(account.positions, order.symbol);
        var nextPosition :=
            if order.side == Buy then 
                Positions.ApplyBuy(basePosition, fill) 
            else
                Positions.ApplySell(basePosition, fill);

        // Lemma invocation.
        ApplyPositionUpdatePreservesValidity(account.positions, nextPosition, order.side);
        var updatedPositions :=
            if order.side == Sell && IsClosed(nextPosition) then
                RemovePosition(account.positions, nextPosition.symbol)
            else
                UpsertPosition(account.positions, nextPosition);
        var nextId := NextLedgerId(account.ledger);
        var tradeEntry := LedgerEntry.Trade(nextId, fill);

        // Lemma invocation.
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

    method Deposit(
        account: Account, ledgerId: LedgerId, amount: Money, timestamp: nat
    ) returns (result: Account)
        ensures IsValidAccount(result)
    {
        expect CanDeposit(account, ledgerId, amount);
        result := DepositCore(account, ledgerId, amount, timestamp);
    }

    method Bootstrap(
        cash: Money,
        positions: seq<Position>,
        orders: seq<Order>,
        ledgerId: LedgerId,
        timestamp: nat
    ) returns (result: Account)
        ensures IsValidAccount(result)
        ensures result.cash == cash
        ensures result.positions == positions
        ensures result.orders == orders
        ensures result.ledger == Ledger([Opening(ledgerId, cash, positions, orders, timestamp)])
    {
        expect CanBootstrap(cash, positions, orders, ledgerId);
        result := BootstrapCore(cash, positions, orders, ledgerId, timestamp);
    }

    method Withdraw(
        account: Account, ledgerId: LedgerId, amount: Money, timestamp: nat
    ) returns (result: Account)
        ensures IsValidAccount(result)
    {
        expect CanWithdraw(account, ledgerId, amount);
        result := WithdrawCore(account, ledgerId, amount, timestamp);
    }

    method PlaceOrder(account: Account, order: Order) returns (result: Account)
        ensures IsValidAccount(result)
    {
        expect CanPlaceOrder(account, order);
        result := PlaceOrderCore(account, order);
    }

    method SetOrderStatus(
        account: Account, orderId: OrderId, newStatus: OrderStatus
    ) returns (result: Account)
        ensures IsValidAccount(result)
    {
        expect CanSetAccountOrderStatus(account, orderId, newStatus);
        result := SetOrderStatusCore(account, orderId, newStatus);
    }

    method Update(account: Account, fill: Fill) returns (result: Account)
        ensures IsValidAccount(result)
    {
        expect CanUpdate(account, fill);
        result := UpdateCore(account, fill);
    }
}
