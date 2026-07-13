# IFVR Phase 2.5 Legacy Runtime Disposition

## Summary
`runtime.py` remains as a compatibility dashboard facade. It is no longer the eager production server composition root, and its critical authorities now delegate to `CanonicalEnterpriseRuntime` components where safe.

## Responsibility Disposition
| Responsibility | Disposition | Notes |
|---|---|---|
| Server production startup | delegated | `server.py` uses `CanonicalRuntimeProvider`. |
| Paper start/halt | delegated | `/api/paper/start` and `/api/paper/halt` call provider start/halt. |
| Proof self-training | proof-only | Moved to `/api/proof/paper/*`. |
| Workflow Orchestrator | delegated | Legacy runtime references canonical component. |
| Communications Bus | delegated | Legacy runtime references canonical component. |
| Enterprise Cost Governor | delegated | Legacy runtime references canonical component. |
| Doctrine/Policy Manager | delegated | Legacy runtime references canonical component. |
| Event Detection | delegated | Legacy runtime references canonical component. |
| Freshness/Memory/Workflow Delta/Priority | delegated | Legacy runtime references canonical components. |
| Market Data Provider | delegated | Legacy runtime references canonical component. |
| Mission Planner | delegated | Legacy runtime references canonical component. |
| Performance Truth | delegated | Legacy runtime references canonical component. |
| Position Monitoring | delegated | Legacy runtime references canonical component. |
| Strategic Intelligence | delegated | Legacy runtime references canonical component. |
| Dashboard state assembly | retained compatibility | Still broad; read-only behavior tested only for canonical snapshot. |
| Decision Lab / replay | simulation compatibility | Not certified as production paper truth. |
| Legacy workflow route methods | compatibility | Still present for dashboard tests; not promoted as production entry. |

## Deprecation
Legacy `/api/paper/start` no longer means proof self-training. Proof start/halt callers must use `/api/proof/paper/start` and `/api/proof/paper/halt`.

## Remaining Risk
`runtime.py` still contains substantial read-model and command surface area. A future IFVR step should split it into pure projections and explicit compatibility command adapters.
