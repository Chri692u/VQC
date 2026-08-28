# Dafny improvements before split
1. **Execution uniqueness** - the identity and deduplication foundation needed
   before safe replay or stronger historical proofs.
2. **Replay across re-bootstrap boundaries** - the largest remaining gap in
   maintaining one continuous history through stream failure and recovery.
3. **Ledger/account consistency invariant** - establishes the common statement
   that the current account agrees with its recorded history.
4. **Decision on negative money** - settles whether cash/history consistency
   should permit margin-like negative cash before proving stronger semantics.
5. **Short-position support in the Dafny core model** - extend position and
   execution semantics to distinguish opening, increasing, reducing, and closing
   long and short exposure, with explicit rules for overselling and covering.
6. **Order/history consistency proof** - connects lifecycle state and filled
   quantity to the recorded order executions.
7. **Cash/history consistency proof** - connects opening cash, cash movements,
   and trade executions to current cash, subject to the negative-money policy.
8. **Position/history consistency proof** - reconstructs active positions from
   the opening snapshot and subsequent executions.
9. **Timestamp/order monotonicity** - useful historical discipline, but less
   important to economic correctness than identity, replay, and state agreement.

# Python improvements before split
1. **Persistent execution identity and deduplication** - retain broker execution
   keys across reconnects and process restarts so the same economic event can
   never be applied twice. This is the Python counterpart to verified execution
   uniqueness in Dafny and is the foundation for replay.

2. **Explicit synchronization state** - expose a small state such as
   `Synchronized`, `Recovering`, `Stale`, or `Stopped`. This lets an algorithm
   know whether `client.account` is currently trusted and lets submission policy
   react deliberately while recovery is in progress.

3. **Gap-safe reconnect and resynchronization** - keep the existing reconnect,
   backoff, and fresh-bootstrap behavior, but close the timing gap between
   obtaining a snapshot and resubscribing to broker events. Buffering, a broker
   cursor, or an execution-history query can provide that handoff.

4. **Deterministic client shutdown** - add `Close()` and context-manager support
   so an algorithm can stop the broker stream, recovery loop, and background
   thread without relying on process termination.

5. **Broker adapter conformance tests** - define reusable tests that every
   adapter must pass for quantity rejection, status normalization, order keys,
   execution keys, snapshots, submissions, and stream events. This keeps future
   brokers consistent with the VQC boundary.

6. **Persistent canonical event log** - store normalized broker order and
   execution events before applying them. This provides an auditable input to
   recovery and replay without storing broker SDK objects.

7. **Replay verification integration** - read canonical missed events in order,
   deduplicate them, apply them through `OrderLifecycle` and `VQC.Update`, and
   confirm the result against a fresh broker snapshot.

8. **Crash/restart continuity** - restore the last trusted checkpoint, execution
   keys, order mapping, and unapplied events after a process restart. Startup
   bootstrap already restores current broker state; this item preserves one
   continuous local history instead.

9. **Periodic and on-demand broker-state reconciliation** - compare VQC cash,
   positions, and open orders with the broker outside stream-failure recovery,
   report divergence, and establish a fresh trusted snapshot when required.

The order is a mix of importance and dependency. In particular, replay depends
on stable execution identity and benefits from a canonical event log; crash
recovery becomes meaningful once those records can be persisted.
