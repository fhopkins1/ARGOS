# EO-DE Recovery Verification

EO-DE verifies that injected faults recover or fail closed with evidence preserved.

For every execution record, recovery evidence tracks:
- duplicate workflows
- duplicate tokens
- duplicate fills
- duplicate positions
- duplicate Performance Truth
- duplicate Historian records
- deterministic Commander alert
- evidence preservation

Transaction, persistence, replay, and idempotency faults exercise EO-DD recovery behavior and are expected to produce `RECOVERY_REQUIRED` rather than fabricated repair.

