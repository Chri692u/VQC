# VQC — Verified Quant Core

VQC is a Dafny-verified financial state-transition core for cash, orders, fills, positions, and ledger history.
It bootstraps a trusted account snapshot, then composes verified deposit, withdrawal, order, and fill transitions.
Python bindings expose the verified API; broker integration remains outside the trusted core.

Get started by visiting the [Python tutorial](python/examples/TUTORIAL.md).
