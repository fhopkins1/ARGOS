# OR-001 Operational Readiness Checklist

| Area | Classification | Evidence / Reason |
|---|---:|---|
| Repository | Near Ready | Broad source/docs/tests exist; root README is obsolete. |
| Runtime | Requires Integration | Local runtime works, but state is in-memory and monolithic. |
| Paper brokerage | Near Ready | Paper order/fill realism exists with buying power/session/liquidity checks. |
| Position lifecycle | Near Ready | Position registry, surveillance, monitoring, sizing, exit, and closed truth modules exist. |
| Persistence | Requires Integration | Foundation exists; operational objects are not durably persisted. |
| Recovery | Requires Integration | Recovery modules exist, but restart restoration is not end-to-end. |
| Replay | Requires Certification | Replay modules exist; production replay consistency needs durable truth. |
| Commander dashboard | Near Ready | UI/backend routes are broad; action/read-only separation needs certification. |
| Enterprise messaging | Near Ready | EO-CL bus exists and is wired; durability needs integration. |
| Enterprise truth | Requires Integration | Performance Truth exists but is process-memory. |
| Auditability | Near Ready | Hash-chain audit exists; operational audit durability incomplete. |
| Determinism | Near Ready | Deterministic-first patterns are strong; placeholder paths need explicit certification labels. |
| Live trading | Requires Certification | Gates block default live trading; no live brokerage production certification found. |

## Verification Attempt

- `node --check ui/argos_control_panel/app.js` completed successfully.
- `py -m unittest Tests.test_argos_control_panel_dashboard` ran 430 tests in 230.860 seconds and failed 1 test: `test_eo_y_calibration_does_not_mutate_positions_ledgers_or_invoke_ai`. The failure shows EO-Y calibration changed `performanceTruthEngine.positionRegistry.metrics.historyRecordCount` from 2 to 3, indicating a mutation of position registry history during a path expected not to mutate ledgers or invoke AI.
