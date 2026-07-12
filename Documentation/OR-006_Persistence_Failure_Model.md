# OR-006 Persistence Failure Model

Persistence failures fail closed.

Implemented diagnostics include:

- `PERSISTENCE_BACKEND_UNAVAILABLE`
- `PERSISTENCE_WRITE_FAILED`
- `DUPLICATE_IDENTITY_REJECTED`
- `PAYLOAD_HASH_MISMATCH`

Critical persistence diagnostics prevent paper operation during recovery.
