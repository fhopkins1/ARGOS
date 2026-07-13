# EO-DD Transaction State Machine

EO-DD states are:
- `INTENT_CREATED`
- `INTENT_PERSISTED`
- `PRECONDITIONS_VALIDATED`
- `PARTICIPANTS_READY`
- `APPLYING`
- `PARTIALLY_APPLIED`
- `RECONCILIATION_PENDING`
- `RECONCILED`
- `COMMITTED`
- `HISTORICALLY_PRESERVED`
- `REJECTED`
- `BLOCKED`
- `FAILED_RETRYABLE`
- `FAILED_NONRETRYABLE`
- `RECOVERY_REQUIRED`
- `QUARANTINED`
- `SUPERSEDED`
- `CANCELLED_BEFORE_APPLICATION`
- `INCONCLUSIVE`

Commit is allowed only when every required participant is acknowledged and reconciliation has no blocking discrepancy. Partial acknowledgment cannot transition to `COMMITTED`.

