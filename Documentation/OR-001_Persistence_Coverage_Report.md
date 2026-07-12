# OR-001 Persistence Coverage Report

## Persistence Foundation

`src/argos/foundation/persistence` implements append-only immutable records, required schema fields, hash-chain integrity, history/latest/all-record APIs, migration descriptors, and backup/restore helpers. The active repository class is `InMemoryPersistenceRepository`.

## Coverage Matrix

| Object / Truth | Coverage |
|---|---:|
| Case files | Persisted schema exists |
| Operational documents | Persisted schema exists |
| Audit events | Persisted schema exists |
| Configuration snapshots | Persisted schema exists |
| Prompt snapshots | Persisted schema exists |
| Model snapshots | Persisted schema exists |
| Staff / department registry | Persisted schema exists |
| Missions | Memory only in scheduler |
| Decision Objects | Memory/runtime products; not canonical persisted object type |
| Workflow Objects | Memory only in workflow orchestrator |
| Workflow Execution Tokens | Memory only inside workflow records |
| Orders | Memory only in Performance Truth / Trader modules |
| Broker responses | Memory only or module-local records |
| Fills | Memory only |
| Open positions | Memory only |
| Closed trades | Memory only |
| Portfolio valuations | Memory only |
| Performance truth | Memory only |
| Commander state | Memory only except control panel action contracts |
| Enterprise messaging | Memory only |
| Policy state | Memory only |
| Recovery state | Partial module support, not durable runtime baseline |
| Replay history | Partial; audit/persistence replay and market replay exist |
| Audit history | In-memory hash-chain; control panel persists some operational documents |

## Finding

The persistence architecture is deterministic and audit-friendly, but the operational runtime is not production durable. OR-003 should introduce a durable repository adapter and canonical object schemas for missions, workflows, tokens, orders, fills, positions, performance truth, messages, and policies.

