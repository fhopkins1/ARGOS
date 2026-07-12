# OR-006 Transaction Boundary Model

`DurableEnterprisePersistenceStore.commit_transaction()` preflights all writes, appends each authoritative record, and persists an `enterprise_transaction` record containing boundary ID, write list, and record hashes.

Implemented transaction groups:

- Canonical runtime persistence snapshot.
- Mission plus workflow persistence.
- Runtime checkpoint after authoritative writes.

If preflight fails, no write begins. If backend write fails, persistence fails closed and emits diagnostics.
