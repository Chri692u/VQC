include "Types.dfy"
include "Validation.dfy"
include "AccountUtility.dfy"

module PositionProof {
    import opened Types
    import opened Validation
    import opened AccountUtility

    // Adding an open position with a fresh symbol preserves a valid position set.
    lemma PrependPositionPreservesValidity(head: Position, tail: seq<Position>)
        requires IsValidPosition(head)
        requires IsOpen(head)
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
        requires IsOpen(updated)
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

    // Inserting or replacing an open valid position preserves set validity.
    lemma UpsertPositionPreservesValidity(positions: seq<Position>, updated: Position)
        requires IsValidPositionSet(positions)
        requires IsValidPosition(updated)
        requires IsOpen(updated)
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

    lemma RemovePositionPreservesMissingSymbol(
        positions: seq<Position>, removedSymbol: string, missingSymbol: string
    )
        requires IsValidPositionSet(positions)
        requires ExistsPosition(positions, removedSymbol)
        requires !ExistsPosition(positions, missingSymbol)
        requires removedSymbol != missingSymbol
        ensures !ExistsPosition(RemovePosition(positions, removedSymbol), missingSymbol)
        decreases |positions|
    {
        if positions[0].symbol != removedSymbol {
            assert ExistsPosition(positions[1..], removedSymbol);
            assert !ExistsPosition(positions[1..], missingSymbol);
            RemovePositionPreservesMissingSymbol(
                positions[1..], removedSymbol, missingSymbol
            );
        }
    }

    // Removing an existing active position preserves the remaining set.
    lemma RemovePositionPreservesValidity(positions: seq<Position>, symbol: string)
        requires IsValidPositionSet(positions)
        requires ExistsPosition(positions, symbol)
        ensures IsValidPositionSet(RemovePosition(positions, symbol))
        decreases |positions|
    {
        if positions[0].symbol != symbol {
            assert ExistsPosition(positions[1..], symbol);
            assert !ExistsPosition(positions[1..], positions[0].symbol);
            RemovePositionPreservesMissingSymbol(
                positions[1..], symbol, positions[0].symbol
            );
            RemovePositionPreservesValidity(positions[1..], symbol);
            PrependPositionPreservesValidity(
                positions[0], RemovePosition(positions[1..], symbol)
            );
        }
    }

    // A buy upserts an open position; a fully closed sell removes it.
    lemma ApplyPositionUpdatePreservesValidity(
        positions: seq<Position>, updated: Position, side: OrderSide
    )
        requires IsValidPositionSet(positions)
        requires IsValidPosition(updated)
        requires side == Buy ==> IsOpen(updated)
        requires side == Sell ==> ExistsPosition(positions, updated.symbol)
        ensures IsValidPositionSet(
            if side == Sell && IsClosed(updated) then
                RemovePosition(positions, updated.symbol)
            else
                UpsertPosition(positions, updated)
        )
    {
        if side == Sell && IsClosed(updated) {
            RemovePositionPreservesValidity(positions, updated.symbol);
        } else {
            assert IsOpen(updated);
            UpsertPositionPreservesValidity(positions, updated);
        }
    }
}
