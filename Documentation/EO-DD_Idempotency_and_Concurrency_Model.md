# EO-DD Idempotency and Concurrency Model

Transaction intent idempotency is keyed by explicit idempotency key or by deterministic source identity: type, source authority, source event, mission, workflow, token, asset, account, order, fill, and position.

Acknowledgment idempotency is keyed by explicit acknowledgment idempotency key or participant evidence tuple.

The journal is append-only and hash chained. Integrity validation verifies previous-record linkage and record hashes so replay can detect tampering or missing records.

