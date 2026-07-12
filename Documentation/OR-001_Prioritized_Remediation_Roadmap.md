# OR-001 Prioritized Remediation Roadmap

## OR-002: Runtime Certification and Source-of-Truth Cleanup

- Update obsolete `README.md` to match `PROJECT_HANDOFF.md`.
- Create a canonical EO index from EO-A through EO-CO.
- Label proof/demo paper workflow paths separately from certified runtime paths.
- Certify `ControlPanelRuntime` as orchestration-only and document every authority handoff.

## OR-003: Durable Persistence Integration

- Add durable repository adapter while preserving append-only hash-chain semantics.
- Add canonical schemas for missions, workflows, Workflow Execution Tokens, orders, broker responses, fills, positions, performance truth, messages, policy state, recovery checkpoints, and replay history.
- Restore runtime state from persisted records on startup.

## OR-004: Recovery and Replay Certification

- Add restart/recovery tests for scheduler, workflow tokens, performance truth, communications bus, and policy manager.
- Validate replay equivalence before and after restart.
- Require immutable recovery evidence for every restored object.

## OR-005: Placeholder and Simulation Isolation

- Gate deterministic placeholders behind explicit proof-mode metadata.
- Audit UI labels so simulated/paper/demo outputs cannot be mistaken for live results.
- Maintain paper/live isolation checks in tests.

## OR-006: Dependency and Runtime Decomposition

- Produce a machine-readable runtime dependency manifest.
- Split `ControlPanelRuntime` state assembly into smaller composition units without changing authority boundaries.
- Add static checks preventing direct workflow/token mutation outside the orchestrator.

## OR-007: Production Brokerage and Live Trading Certification

- Keep live trading disabled until broker adapters, risk certification, treasury funding, human approval, persistence, recovery, and audit trails pass end-to-end tests.
- Certify paper broker behavior separately from any live broker adapter.
- Add explicit broker response/fill persistence and reconciliation reports.

