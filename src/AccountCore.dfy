include "Currency.dfy"
include "Orders.dfy"
include "Execution.dfy"
include "Positions.dfy"
include "Ledger.dfy"

module AccountCore {
    import opened Currency
    import opened Orders
    import opened Execution
    import opened Positions
    import opened Ledger

    datatype Account = Account(
        cash: Money,
        ledger: Ledger,
        positions: seq<Position>,
        orders: seq<Order>
    )

    predicate IsValidPositionSet(positions: seq<Position>)
    {
        (forall i :: 0 <= i < |positions| ==> IsValidPosition(positions[i])) &&
        (forall i, j :: 0 <= i < j < |positions| ==> positions[i].symbol != positions[j].symbol)
    }

    predicate IsValidOrderSet(orders: seq<Order>)
    {
        (forall i :: 0 <= i < |orders| ==> IsValidOrder(orders[i])) &&
        (forall i, j :: 0 <= i < j < |orders| ==> orders[i].orderId != orders[j].orderId)
    }

    predicate IsValidAccount(account: Account)
    {
        IsValidLedger(account.ledger) &&
        IsValidPositionSet(account.positions) &&
        IsValidOrderSet(account.orders)
    }

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

    function NextLedgerId(ledger: Ledger): LedgerId
        requires IsValidLedger(ledger)
    {
        LedgerId(MaxLedgerId(ledger.entries) + 1)
    }

    predicate ExistsOrder(orders: seq<Order>, target: OrderId)
    {
        exists i :: 0 <= i < |orders| && orders[i].orderId == target
    }

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

    function ReplaceOrder(orders: seq<Order>, updated: Order): seq<Order>
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
            [orders[0]] + ReplaceOrder(orders[1..], updated)
    }

    predicate ExistsPosition(positions: seq<Position>, symbol: string)
    {
        exists i :: 0 <= i < |positions| && positions[i].symbol == symbol
    }

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

    lemma GetPositionIsValid(positions: seq<Position>, symbol: string)
        requires IsValidPositionSet(positions)
        requires ExistsPosition(positions, symbol)
        ensures IsValidPosition(GetPosition(positions, symbol))
    {
        if |positions| == 0 {
            // impossible: ExistsPosition(positions, symbol) would be false
        } else if positions[0].symbol == symbol {
            assert IsValidPosition(positions[0]);
        } else {
            assert ExistsPosition(positions[1..], symbol);
            GetPositionIsValid(positions[1..], symbol);
        }
    }

    function ReplacePosition(positions: seq<Position>, updated: Position): seq<Position>
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
            [positions[0]] + ReplacePosition(positions[1..], updated)
    }

    function UpsertPosition(positions: seq<Position>, updated: Position): seq<Position>
        requires IsValidPositionSet(positions)
        requires IsValidPosition(updated)
        decreases |positions|
    {
        if |positions| == 0 then
            [updated]
        else if positions[0].symbol == updated.symbol then
            [updated] + positions[1..]
        else
            [positions[0]] + UpsertPosition(positions[1..], updated)
    }

    function NewAccount(): Account
    {
        Account(Money(0), Ledger([]), [], [])
    }

    function Deposit(account: Account, id: LedgerId, amount: Money, timestamp: nat): Account
        requires IsValidAccount(account)
        requires IsValidLedgerId(id)
        requires Currency.IsPositive(amount)
        requires !ContainsLedgerId(account.ledger.entries, id)
    {
        var entry: LedgerEntry := LedgerEntry.Deposit(id, amount, timestamp);
        var nextLedger := Append(account.ledger, entry);
        Account(
            Currency.Add(account.cash, amount),
            nextLedger,
            account.positions,
            account.orders
        )
    }

    function Withdraw(account: Account, id: LedgerId, amount: Money, timestamp: nat): Account
        requires IsValidAccount(account)
        requires IsValidLedgerId(id)
        requires Currency.IsPositive(amount)
        requires !ContainsLedgerId(account.ledger.entries, id)
        requires Currency.Gte(account.cash, amount)
    {
        var entry: LedgerEntry := LedgerEntry.Withdrawal(id, amount, timestamp);
        var nextLedger := Append(account.ledger, entry);
        Account(
            Currency.Sub(account.cash, amount),
            nextLedger,
            account.positions,
            account.orders
        )
    }

    function PlaceOrder(account: Account, order: Order): Account
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

    function Update(account: Account, order: Order, fill: Fill): Account
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
            ReplaceOrder(account.orders, updatedOrder)
        else
            account.orders + [updatedOrder];

        var basePosition :=
            if ExistsPosition(account.positions, order.symbol) then
                var pos := GetPosition(account.positions, order.symbol);
                GetPositionIsValid(account.positions, order.symbol);
                assert IsValidPosition(pos);
                pos
            else
                var pos := Position(order.symbol, 0, Money(0));
                assert |pos.symbol| > 0;
                assert (pos.quantity == 0 && Currency.IsZero(pos.averagePrice)) || (pos.quantity > 0 && Currency.IsPositive(pos.averagePrice));
                pos;
        assert |basePosition.symbol| > 0;
        assert (basePosition.quantity == 0 && Currency.IsZero(basePosition.averagePrice)) || (basePosition.quantity > 0 && Currency.IsPositive(basePosition.averagePrice));

        var nextPosition :=
            if order.side == Buy then
                var pos := Position(
                    order.symbol,
                    basePosition.quantity + fill.quantity,
                    if basePosition.quantity == 0 then
                        fill.price
                    else
                        Currency.Money(
                            (basePosition.averagePrice.value * basePosition.quantity + fill.price.value * fill.quantity) /
                            (basePosition.quantity + fill.quantity)
                        )
                );
                assert |pos.symbol| > 0;
                assert (pos.quantity == 0 && Currency.IsZero(pos.averagePrice)) || (pos.quantity > 0 && Currency.IsPositive(pos.averagePrice));
                pos
            else
                var soldQuantity := basePosition.quantity - fill.quantity;
                assert fill.quantity <= basePosition.quantity;
                var pos := Position(
                    order.symbol,
                    soldQuantity,
                    if basePosition.quantity == fill.quantity then
                        Money(0)
                    else
                        basePosition.averagePrice
                );
                assert |pos.symbol| > 0;
                assert (pos.quantity == 0 && Currency.IsZero(pos.averagePrice)) || (pos.quantity > 0 && Currency.IsPositive(pos.averagePrice));
                pos;
        assert |nextPosition.symbol| > 0;
        assert (nextPosition.quantity == 0 && Currency.IsZero(nextPosition.averagePrice)) || (nextPosition.quantity > 0 && Currency.IsPositive(nextPosition.averagePrice));

        var updatedPositions :=
            if ExistsPosition(account.positions, order.symbol) then
                ReplacePosition(account.positions, nextPosition)
            else
                UpsertPosition(account.positions, nextPosition);

        var nextId := NextLedgerId(account.ledger);
        var tradeEntry: LedgerEntry := LedgerEntry.Trade(nextId, fill);
        var nextLedger := Append(account.ledger, tradeEntry);

        var executionValue := ExecutionValue(fill);
        var nextCash :=
            if order.side == Buy then
                Currency.Sub(account.cash, executionValue)
            else
                Currency.Add(account.cash, executionValue);

        Account(
            nextCash,
            nextLedger,
            updatedPositions,
            updatedOrders
        )
    }
}
