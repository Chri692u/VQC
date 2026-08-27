# VQC — Verified Quant Core

VQC is a Dafny-verified financial state-transition core for cash, orders, fills,
positions, and ledger history. It bootstraps a trusted account snapshot and then
applies verified deposit, withdrawal, order, status, and fill transitions.

## Dafny correctness guarantees

VQC provides two central correctness guarantees. First, `Bootstrap` proves that a trusted broker snapshot satisfying VQC's input requirements produces a valid account. Second, every verified account transition proves that, given a valid account, the resulting account remains valid. Together, these proofs establish account validity at bootstrap and preserve it through all subsequent accepted core operations.

In particular, account validity guarantees:

* valid and uniquely identified orders;
* valid market, limit, stop, and stop-limit instructions;
* compatible order-status transitions and bounded fill quantities;
* active, long-only positions with unique symbols;
* sells that cannot exceed the verified position quantity;
* a valid ledger with unique IDs and any opening entry restricted to its start;
* immutable transitions—a new account is returned instead of mutating the old one.

These guarantees apply only to the verified state and transitions modeled by VQC. VQC does not prove that broker data or market quotes are truthful, that a network or stream is reliable, that an order will execute, or that a strategy will make money. These properties are outside the verified model. `Bootstrap` therefore treats its broker snapshot as trusted input, while requiring that snapshot to satisfy VQC's structural rules before establishing the initial valid account.


## Python client and adapters

The Python bindings expose the verified API. `VQCClient` adds a small order API,
owns the latest verified snapshot, and performs private background
reconciliation.

A broker adapter contains everything specific to one broker:

- native client and credential setup;
- account, position, order, and market-clock requests;
- order submission and trade-stream handling;
- normalization of broker statuses and event kinds;
- conversion of native money, quantities, timestamps, orders, positions, and
  fills into VQC records.

The included `AlpacaAdapter` implements this boundary for Alpaca. Another broker
can implement `BrokerAdapter` without placing its SDK types or rules in the
verified core or generic client. Adapters must reject unsupported fractional or
short-position state rather than silently truncating or changing it.

Read more about the [verified Dafny core](dafny/API_OVERVIEW.md), the
[Python API](python/API_OVERVIEW.md), and the [Dafny language](https://dafny.org/).

Get started with the [Python tutorial](python/examples/TUTORIAL.md).
