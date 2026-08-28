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