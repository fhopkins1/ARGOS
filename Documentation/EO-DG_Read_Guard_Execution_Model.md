# EO-DG Read Guard Execution Model

A guarded read:
1. Identifies the registered surface.
2. Validates runtime mode and truth domain.
3. Captures pre-read semantic digests.
4. Captures counters for API calls, cost, office wakeups, token transfers, broker events, persistence sequence, transaction journal, truth records, and Historian records.
5. Executes the read.
6. Captures post-read digests and counters.
7. Compares state.
8. Produces a read-integrity result.
9. Preserves evidence.
10. Quarantines critical mutating surfaces.

Synchronous, asynchronous, streaming, and polling reads are supported.

