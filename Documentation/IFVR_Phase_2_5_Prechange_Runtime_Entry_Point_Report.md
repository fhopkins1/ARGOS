# IFVR Phase 2.5 Prechange Runtime Entry Point Report

## Recorded Baseline
- Branch: `main`
- Pre-change commit: `34efd82c01ce3af5d3315dbfb24165952eb001cd`
- Production server entry point: `src/argos/control_panel/server.py::run`
- Legacy dashboard factory: `src/argos/control_panel/runtime.py::create_runtime`
- Canonical runtime: `src/argos/control_panel/canonical_enterprise_runtime.py::CanonicalEnterpriseRuntime`

## Prechange Finding
Before remediation, `server.py::run` called `create_runtime()` at server startup. That constructed `ControlPanelRuntime`, which independently instantiated many stateful authorities, including workflow orchestration, mission planning, communications, cost governance, performance truth, position monitoring, market data, and strategic intelligence objects. The canonical runtime existed, but was not the server production composition root.

## Entry Point Classification
| Entry point | Runtime object | Truth domain | Paper reachable | Authoritative writes reachable | Bypasses canonical runtime | Disposition |
|---|---|---|---:|---:|---:|---|
| `python -m argos.control_panel.server` / `server.py::main` | `ControlPanelRuntime` via `create_runtime()` | mixed dashboard/proof/paper labels | yes | yes | yes | unsafe production bypass prechange |
| `server.py::run` | `ControlPanelRuntime` | mixed | yes | yes | yes | remediated to provider + lazy compatibility proxy |
| `runtime.py::create_runtime` | `ControlPanelRuntime` | compatibility/proof/read model | yes | yes | yes prechange | retained as compatibility facade |
| `CanonicalEnterpriseRuntime()` | canonical runtime | paper, live disabled | yes | yes through canonical paths | no | canonical |
| OR-005/OR-006/OR-007 tests | direct `CanonicalEnterpriseRuntime` | paper/test | yes | yes through tests | no | test-only canonical |
| Decision Lab / replay routes | legacy runtime methods | simulation/replay | no direct paper certification | read/replay mutation possible by command | partially | compatibility/simulation |
| Proof paper self-training | `runtime.start_paper_self_training` | proof | not certified paper | proof workflow only | yes prechange | moved under explicit proof routes |

## Loop Inventory
Prechange loops existed in the legacy paper proof runner and canonical runtime start state. The server constructed the legacy runtime eagerly, so a production process could have a proof runner-capable object graph even before explicit proof command routing.

## Prechange Verdict
Prechange architecture was **not converged**. It had one canonical runtime in code and one server-facing legacy runtime composition root.
