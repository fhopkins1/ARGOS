# EO-DA Read-Only Integrity Model

`ReadOnlyIntegrityGuard` captures semantic digests before and after a read operation.

Protected state may include runtime status, workflow counts, authority identities, broker order counts, active position counts, and other semantic digests supplied by the caller.

The guard returns assurance evidence. It does not repair state and does not write financial truth.

The targeted test suite verifies mutation detection with `INV-READONLY-001`.

