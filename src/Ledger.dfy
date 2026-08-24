include "Types.dfy"
include "Validation.dfy"
include "Currency.dfy"
include "Execution.dfy"

module LedgerOps {
    import opened Types
    import opened Validation
    import opened Currency

    // Appends a new entry to the ledger, preserving uniqueness of ledger ids.
    function Append(ledger: Ledger, entry: LedgerEntry): Ledger
        requires CanAppendLedgerEntry(ledger, entry)
        ensures IsValidLedger(Append(ledger, entry))
    {
        Ledger(ledger.entries + [entry])
    }

    // Sums deposited values in the ledger.
    function TotalDeposits(ledger: Ledger): Money
        requires IsValidLedger(ledger)
        decreases |ledger.entries|
    {
        if |ledger.entries| == 0 then
            Money(0)
        else
            match ledger.entries[0]
                case Deposit(_, amount, _) =>
                    Add(amount, TotalDeposits(Ledger(ledger.entries[1..])))
                case Withdrawal(_, _, _) =>
                    TotalDeposits(Ledger(ledger.entries[1..]))
                case Trade(_, _) =>
                    TotalDeposits(Ledger(ledger.entries[1..]))
    }

    // Sums withdrawn values in the ledger.
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
                    Add(amount, TotalWithdrawals(Ledger(ledger.entries[1..])))
                case Trade(_, _) =>
                    TotalWithdrawals(Ledger(ledger.entries[1..]))
    }

    // Returns the net cash flow for the ledger.
    function NetCashFlow(ledger: Ledger): Money
        requires IsValidLedger(ledger)
    {
        Sub(TotalDeposits(ledger), TotalWithdrawals(ledger))
    }
}
