# EO-DD Transaction Intent Model

`TransactionIntent` is immutable once persisted. It captures:
- transaction id, type, schema version, and paper truth domain
- EO-DC decision id and approval status
- source authority, source event, mission, workflow, and token lineage
- asset, account, order, fill, and position identifiers
- intended participants, required actions, and dependency order
- idempotency key, expected preconditions, expected postconditions
- doctrine, policy, creation sequence, expiration, recovery strategy, reconciliation strategy
- deterministic transaction hash

The coordinator persists intent before any participant can be acknowledged. A duplicate idempotency key returns the existing intent and does not append a second intent record.

