include "Currency.dfy"
include "Execution.dfy"

module Ledger {
    import opened Currency
    import opened Execution

    // ----------------------
    // Identifiers
    // ----------------------

    datatype LedgerId = LedgerId(value: nat)

    predicate IsValidLedgerId(id: LedgerId)
    {
        id.value > 0
    }

    // ----------------------
    // Historical entries
    // ----------------------

    datatype LedgerEntry =
        | Deposit(id: LedgerId, amount: Money, timestamp: nat)
        | Withdrawal(id: LedgerId, amount: Money, timestamp: nat)
        | Trade(id: LedgerId, fill: Fill)

    function EntryId(entry: LedgerEntry): LedgerId
    {
        match entry
        case Deposit(id, _, _) => id
        case Withdrawal(id, _, _) => id
        case Trade(id, _) => id
    }

    // ----------------------
    // Validation
    // ----------------------

    predicate IsValidEntry(entry: LedgerEntry)
    {
        match entry
        case Deposit(id, amount, _) =>
            IsValidLedgerId(id) &&
            Currency.IsPositive(amount)
        case Withdrawal(id, amount, _) =>
            IsValidLedgerId(id) &&
            Currency.IsPositive(amount)
        case Trade(id, fill) =>
            IsValidLedgerId(id) &&
            Execution.IsValidFill(fill)
    }

    // ----------------------
    // Ledger history
    // ----------------------

    datatype Ledger = Ledger(entries: seq<LedgerEntry>)

    predicate ContainsLedgerId(entries: seq<LedgerEntry>, id: LedgerId)
    {
        exists i :: 0 <= i < |entries| && EntryId(entries[i]) == id
    }

    predicate AllUniqueLedgerIds(entries: seq<LedgerEntry>)
    {
        forall i, j :: 0 <= i < j < |entries| ==> EntryId(entries[i]) != EntryId(entries[j])
    }

    predicate IsValidLedger(ledger: Ledger)
    {
        (forall i :: 0 <= i < |ledger.entries| ==> IsValidEntry(ledger.entries[i])) &&
        AllUniqueLedgerIds(ledger.entries)
    }

    // ----------------------
    // Append
    // ----------------------

    function Append(ledger: Ledger, entry: LedgerEntry): (newLedger: Ledger)
        requires IsValidLedger(ledger)
        requires IsValidEntry(entry)
        requires !ContainsLedgerId(ledger.entries, EntryId(entry))
        ensures newLedger.entries == ledger.entries + [entry]
        ensures IsValidLedger(newLedger)
    {
        var next := Ledger(ledger.entries + [entry]);
        next
    }

    // ----------------------
    // Queries
    // ----------------------

    function TotalDeposits(ledger: Ledger): Money
        requires IsValidLedger(ledger)
        decreases |ledger.entries|
    {
        if |ledger.entries| == 0 then
            Money(0)
        else
            match ledger.entries[0]
            case Deposit(_, amount, _) =>
                Currency.Add(amount, TotalDeposits(Ledger(ledger.entries[1..])))
            case Withdrawal(_, _, _) =>
                TotalDeposits(Ledger(ledger.entries[1..]))
            case Trade(_, _) =>
                TotalDeposits(Ledger(ledger.entries[1..]))
    }

    function TotalWithdrawals(ledger: Ledger): Money
        requires IsValidLedger(ledger)
        decreases |ledger.entries|
    {
        if |ledger.entries| == 0 then
            Money(0)
        else
            match ledger.entries[0]
            case Deposit(_, _, _) =>
                TotalWithdrawals(Ledger(ledger.entries[1..]))
            case Withdrawal(_, amount, _) =>
                Currency.Add(amount, TotalWithdrawals(Ledger(ledger.entries[1..])))
            case Trade(_, _) =>
                TotalWithdrawals(Ledger(ledger.entries[1..]))
    }

    function NetCashFlow(ledger: Ledger): Money
        requires IsValidLedger(ledger)
    {
        Currency.Sub(TotalDeposits(ledger), TotalWithdrawals(ledger))
    }
}
