# IFVR Phase 2.5 Loop Ownership Model

| Loop | Owner | Start site | Stop site | Duplicate protection | Domain |
|---|---|---|---|---|---|
| Canonical runtime operating state | `CanonicalEnterpriseRuntime` | `start()` | `halt()` | `_loop_started` idempotency | paper |
| Scheduler dispatch eligibility | `EnterpriseOperationsScheduler` under canonical runtime | canonical start/admission | canonical halt mode | canonical singleton | paper/control |
| Proof paper runner | legacy compatibility runtime | `/api/proof/paper/start` | `/api/proof/paper/halt` | thread event/lock | proof |
| UI polling | browser/client | UI JavaScript | browser stop | observational | read model |
| Decision Lab replay | compatibility runtime command | replay command route | replay control | simulation/replay only | simulation |

## Remediation
Production `/api/paper/start` no longer arms the proof runner. Repeated canonical start and halt are tested as idempotent.
