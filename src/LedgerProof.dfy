include "Types.dfy"
include "Validation.dfy"
include "Ledger.dfy"
include "AccountUtility.dfy"

module LedgerProof {
    import opened Types
    import opened Validation
    import opened LedgerOps
    import opened AccountUtility

    // Bounds every existing ledger ID by the sequence maximum.
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

    // The generated next ID cannot already occur in a valid ledger.
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
}
