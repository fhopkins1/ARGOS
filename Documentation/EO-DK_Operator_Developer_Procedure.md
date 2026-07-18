# EO-DK Operator and Developer Procedure

1. Define a bridge with a stable EO-DB-compatible bridge ID.
2. Register it in `CanonicalBridgeRegistry`.
3. Select the transfer class: ownership transfer, information delivery, authority request, or external execution.
4. Declare proof domains, token requirements, persistence requirements, idempotency, failure, and recovery policy.
5. Implement destination acceptance; do not fabricate acceptance in the source.
6. Initiate handoff through `CanonicalBridgeExecutor.execute()`.
7. Verify source release and destination activation for ownership-transfer bridges.
8. Add dynamic tests for acceptance, rejection, idempotency, and artifact integrity.
9. Generate EO-DK evidence with `Scripts/generate_eodk_evidence.py`.
10. Treat `INCOMPLETE` as a blocker for full bridge certification when required dynamic endpoint traces are absent.
