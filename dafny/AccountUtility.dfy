include "Types.dfy"
include "Validation.dfy"

module AccountUtility {
    import opened Types
    import opened Validation

    // Returns the greatest ledger identifier in a sequence, or zero when empty.
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

    predicate ExistsOrder(orders: seq<Order>, orderId: OrderId)
    {
        exists i :: 0 <= i < |orders| && orders[i].orderId == orderId
    }

    function GetOrder(orders: seq<Order>, orderId: OrderId): Order
        requires IsValidOrderSet(orders)
        requires ExistsOrder(orders, orderId)
        ensures GetOrder(orders, orderId).orderId == orderId
        decreases |orders|
    {
        if |orders| == 0 then
            Order(OrderId(0), "", 0, Buy, Market, Pending, 0)
        else if orders[0].orderId == orderId then
            orders[0]
        else
            GetOrder(orders[1..], orderId)
    }

    function UpdateOrder(orders: seq<Order>, updated: Order): seq<Order>
        requires CanUpdateOrder(orders, updated)
        decreases |orders|
    {
        if |orders| == 0 then
            []
        else if orders[0].orderId == updated.orderId then
            [updated] + orders[1..]
        else
            [orders[0]] + UpdateOrder(orders[1..], updated)
    }

    // Replaces an existing order with the same ID, or appends a new one.
    function UpsertOrder(orders: seq<Order>, updated: Order): seq<Order>
        requires IsValidOrderSet(orders)
        requires IsValidOrder(updated)
    {
        if ExistsOrder(orders, updated.orderId) then
            UpdateOrder(orders, updated)
        else
            orders + [updated]
    }

    predicate ExistsPosition(positions: seq<Position>, symbol: string)
    {
        exists i :: 0 <= i < |positions| && positions[i].symbol == symbol
    }

    function GetPosition(positions: seq<Position>, symbol: string): Position
        requires IsValidPositionSet(positions)
        requires ExistsPosition(positions, symbol)
        ensures IsValidPosition(GetPosition(positions, symbol))
        ensures GetPosition(positions, symbol).symbol == symbol
        decreases |positions|
    {
        if |positions| == 0 then
            Position("", 0, Money(0))
        else if positions[0].symbol == symbol then
            positions[0]
        else
            GetPosition(positions[1..], symbol)
    }

    // Returns the position for a symbol, or a valid empty position when absent.
    function PositionOrEmpty(positions: seq<Position>, symbol: string): Position
        requires IsValidPositionSet(positions)
        requires HasNonEmptySymbol(symbol)
        ensures IsValidPosition(PositionOrEmpty(positions, symbol))
        ensures PositionOrEmpty(positions, symbol).symbol == symbol
    {
        if ExistsPosition(positions, symbol) then
            GetPosition(positions, symbol)
        else
            Position(symbol, 0, Money(0))
    }

    function UpdatePosition(positions: seq<Position>, updated: Position): seq<Position>
        requires CanUpdatePosition(positions, updated)
        decreases |positions|
    {
        if |positions| == 0 then
            []
        else if positions[0].symbol == updated.symbol then
            [updated] + positions[1..]
        else
            [positions[0]] + UpdatePosition(positions[1..], updated)
    }

    // Replaces a position with the same symbol, or appends a new one.
    function UpsertPosition(positions: seq<Position>, updated: Position): seq<Position>
        requires CanUpsertPosition(positions, updated)
        decreases |positions|
    {
        if |positions| == 0 then
            [updated]
        else if positions[0].symbol == updated.symbol then
            [updated] + positions[1..]
        else
            [positions[0]] + UpsertPosition(positions[1..], updated)
    }

    // Removes the active position for a symbol after it has been fully sold.
    function RemovePosition(positions: seq<Position>, symbol: string): seq<Position>
        requires CanRemovePosition(positions, symbol)
        decreases |positions|
    {
        if positions[0].symbol == symbol then
            positions[1..]
        else
            [positions[0]] + RemovePosition(positions[1..], symbol)
    }

}
