# OR-006 Runtime Recovery Audit

Every recovery writes an `enterprise_recovery_audit` record containing:

- recovery mode,
- start and completion time,
- restored entities,
- deferred entities,
- failed entities,
- diagnostics,
- whether paper operation is allowed.

The audit is append-only and hash-chained through the foundation repository.
