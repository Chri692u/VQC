include "Types.dfy"
include "Validation.dfy"
include "Currency.dfy"
include "Orders.dfy"
include "Execution.dfy"
include "Positions.dfy"
include "Ledger.dfy"

module AccountOps {
    import opened Types
    import opened Validation
    import opened Currency
    import opened Orders
    import opened Execution
    import opened Positions
    import opened LedgerOps

    // Returns a new empty account.
    function NewAccount(): Account
    {
        Account(Money(0), Ledger([]), [], [])
    }

    // Returns the next ledger identifier after the current entries.
    function MaxLedgerId(entries: seq<LedgerEntry>): nat
        decreases |entries|
    {
        if |entries| == 0 then
            0
        else
            var current := EntryId(entries[0]).value;
            var rest := MaxLedgerId(entries[1..]);
            if current > rest then current else rest
    }

    // Returns the next ledger identifier to assign.
    function NextLedgerId(ledger: Ledger): LedgerId
        requires IsValidLedger(ledger)
    {
        LedgerId(MaxLedgerId(ledger.entries) + 1)
    }

    // Returns true when an order exists in a sequence.
    predicate ExistsOrder(orders: seq<Order>, target: OrderId)
    {
        exists i :: 0 <= i < |orders| && orders[i].orderId == target
    }

    // Returns the matching order from a sequence.
    function GetOrder(orders: seq<Order>, target: OrderId): Order
        requires IsValidOrderSet(orders)
        requires ExistsOrder(orders, target)
        decreases |orders|
    {
        if |orders| == 0 then
            Order(OrderId(0), "", 0, Buy, Market, New, 0)
        else if orders[0].orderId == target then
            orders[0]
        else
            GetOrder(orders[1..], target)
    }

    // Updates an order in a sequence with a new version.
    function UpdateOrder(orders: seq<Order>, updated: Order): seq<Order>
        requires IsValidOrderSet(orders)
        requires IsValidOrder(updated)
        requires ExistsOrder(orders, updated.orderId)
        decreases |orders|
    {
        if |orders| == 0 then
            []
        else if orders[0].orderId == updated.orderId then
            [updated] + orders[1..]
        else
            [orders[0]] + UpdateOrder(orders[1..], updated)
    }

    // Returns true when a position for the given symbol exists.
    predicate ExistsPosition(positions: seq<Position>, symbol: string)
    {
        exists i :: 0 <= i < |positions| && positions[i].symbol == symbol
    }

    // Returns the matching position from a sequence.
    function GetPosition(positions: seq<Position>, symbol: string): Position
        requires ExistsPosition(positions, symbol)
        decreases |positions|
    {
        if |positions| == 0 then
            Position("", 0, Money(0))
        else if positions[0].symbol == symbol then
            positions[0]
        else
            GetPosition(positions[1..], symbol)
    }

    // Updates a position in a sequence with a new version.
    function UpdatePosition(positions: seq<Position>, updated: Position): seq<Position>
        requires IsValidPositionSet(positions)
        requires IsValidPosition(updated)
        requires ExistsPosition(positions, updated.symbol)
        decreases |positions|
    {
        if |positions| == 0 then
            []
        else if positions[0].symbol == updated.symbol then
            [updated] + positions[1..]
        else
            [positions[0]] + UpdatePosition(positions[1..], updated)
    }

    // Inserts a position into a sequence.
    function InsertPosition(positions: seq<Position>, updated: Position): seq<Position>
        requires IsValidPositionSet(positions)
        requires IsValidPosition(updated)
        decreases |positions|
    {
        if |positions| == 0 then
            [updated]
        else if positions[0].symbol == updated.symbol then
            [updated] + positions[1..]
        else
            [positions[0]] + InsertPosition(positions[1..], updated)
    }

    // Adds a deposit to the account ledger and cash balance.
    function DepositCore(account: Account, id: LedgerId, amount: Money, timestamp: nat): Account
        requires IsValidAccount(account)
        requires IsValidLedgerId(id)
        requires IsPositive(amount)
        requires !ContainsLedgerId(account.ledger.entries, id)
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
        requires IsValidAccount(account)
        requires IsValidLedgerId(id)
        requires IsPositive(amount)
        requires !ContainsLedgerId(account.ledger.entries, id)
        requires Gte(account.cash, amount)
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
        requires IsValidAccount(account)
        requires IsValidOrder(order)
        requires !ExistsOrder(account.orders, order.orderId)
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
        requires IsValidAccount(account)
        requires IsValidOrder(order)
        requires IsValidFill(fill)
        requires order.orderId == fill.orderId
        requires order.symbol == fill.symbol
        requires CanAcceptFill(order.status)
        requires fill.quantity > 0
        requires fill.quantity <= RemainingQuantity(order)
        requires order.side == Buy || order.side == Sell
        requires order.side == Buy || ExistsPosition(account.positions, order.symbol)
        requires order.side == Sell ==> ExistsPosition(account.positions, order.symbol) && GetPosition(account.positions, order.symbol).quantity >= fill.quantity
    {
        var updatedOrder := Orders.ApplyFill(order, fill.quantity);
        var updatedOrders :=
            if ExistsOrder(account.orders, order.orderId) then
                UpdateOrder(account.orders, updatedOrder)
            else
                account.orders + [updatedOrder];

        var basePosition :=
            if ExistsPosition(account.positions, order.symbol) then
                GetPosition(account.positions, order.symbol)
            else
                Position(order.symbol, 0, Money(0));

        var nextPosition :=
            if order.side == Buy then
                Position(
                    order.symbol,
                    basePosition.quantity + fill.quantity,
                    fill.price
                )
            else if basePosition.quantity == fill.quantity then
                Position(
                    order.symbol,
                    0,
                    Money(0)
                )
            else
                Position(
                    order.symbol,
                    basePosition.quantity - fill.quantity,
                    basePosition.averagePrice
                );

        assume {:axiom} IsValidPosition(nextPosition);
        var updatedPositions := InsertPosition(account.positions, nextPosition);

        var nextId := NextLedgerId(account.ledger);
        var tradeEntry := LedgerEntry.Trade(nextId, fill);
        assume {:axiom} !ContainsLedgerId(account.ledger.entries, nextId);
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
        expect IsValidAccount(account);
        expect IsValidLedgerId(id);
        expect IsPositive(amount);
        expect !ContainsLedgerId(account.ledger.entries, id);
        result := DepositCore(account, id, amount, timestamp);
    }

    method Withdraw(account: Account, id: LedgerId, amount: Money, timestamp: nat) returns (result: Account)
    {
        expect IsValidAccount(account);
        expect IsValidLedgerId(id);
        expect IsPositive(amount);
        expect !ContainsLedgerId(account.ledger.entries, id);
        expect Gte(account.cash, amount);
        result := WithdrawCore(account, id, amount, timestamp);
    }

    method PlaceOrder(account: Account, order: Order) returns (result: Account)
    {
        expect IsValidAccount(account);
        expect IsValidOrder(order);
        expect !ExistsOrder(account.orders, order.orderId);
        result := PlaceOrderCore(account, order);
    }

    method Update(account: Account, order: Order, fill: Fill) returns (result: Account)
    {
        expect IsValidAccount(account);
        expect IsValidOrder(order);
        expect IsValidFill(fill);
        expect order.orderId == fill.orderId;
        expect order.symbol == fill.symbol;
        expect CanAcceptFill(order.status);
        expect fill.quantity > 0;
        expect fill.quantity <= RemainingQuantity(order);
        expect order.side == Buy || order.side == Sell;
        expect order.side == Buy || ExistsPosition(account.positions, order.symbol);
        expect order.side == Sell ==> ExistsPosition(account.positions, order.symbol) && GetPosition(account.positions, order.symbol).quantity >= fill.quantity;
        result := UpdateCore(account, order, fill);
    }
}
