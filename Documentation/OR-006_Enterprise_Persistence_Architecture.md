# OR-006 Enterprise Persistence Architecture

## Architecture

OR-006 extends the existing foundation persistence package with enterprise object families and adds `DurableEnterprisePersistenceStore`.

The store uses:

- Foundation `PersistentRecord` hash chains.
- Foundation schema validation through `canonical_schemas()`.
- Foundation `BackupService` deterministic JSON backups.
- OR-006 envelopes carrying schema version, truth domain, serialization version, creation/modification sequence, payload hash, and idempotency key.

## Principle

Runtime memory is cache and projection. Authoritative continuity state is persisted through enterprise object families and recovered into the canonical OR-005 runtime.

## Implemented Families

- Runtime state.
- Runtime checkpoints.
- Mission state.
- Workflow and token state.
- Broker state.
- Position state.
- Performance Truth.
- Policy state.
- Recovery audit.
- Transaction boundary records.

## Scope Note

Part 2 recovery is implemented for canonical runtime, missions, workflows, Workflow Execution Tokens, persisted evidence, checkpoint separation, corruption detection, and recovery audit. Deep reconstruction of every legacy dashboard surface remains outside this certification.
