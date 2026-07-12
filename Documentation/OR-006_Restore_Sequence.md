# OR-006 Restore Sequence

Implemented restore order:

1. Schema and repository validation.
2. Fresh canonical runtime construction.
3. Mission state.
4. Mission plan state.
5. Workflow and token state.
6. Runtime continuity state.
7. Broker evidence presence check.
8. Position evidence presence check.
9. Performance Truth evidence presence check.
10. Recovery audit.

Checkpoint data is restored only after authoritative state checks and cannot overwrite truth.
