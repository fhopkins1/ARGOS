# IFVR Phase 2.5 Production Entry Point Map

| Entry point | Production role | Runtime provider | Canonical runtime construction | Notes |
|---|---|---|---|---|
| `server.py::main` | CLI server launch | `get_server_runtime_provider` | `CanonicalRuntimeProvider()` creates `CanonicalEnterpriseRuntime` | Production process entry. |
| `server.py::run` | HTTP server construction | `get_server_runtime_provider` | provider singleton | No eager `create_runtime()` call. |
| `/api/runtime/provider` | status/read | provider snapshot | existing provider | Inspectable runtime identity and state. |
| `/api/paper/start` | production paper start | provider start | existing provider runtime | Idempotent canonical start. |
| `/api/paper/halt` | production halt | provider halt | existing provider runtime | Idempotent canonical halt. |
| `/api/proof/paper/start` | proof compatibility | lazy compatibility proxy | legacy facade with canonical authorities | Explicit proof route. |
| `/api/proof/paper/halt` | proof compatibility | lazy compatibility proxy | legacy facade with canonical authorities | Explicit proof route. |
| `create_runtime()` | dashboard/test compatibility | none | constructs compatibility facade with internal canonical runtime | Not server production root. |

## Invariant
`Tests/test_ifvr001_runtime_convergence.py` fails if `server.py::run` returns to eager `runtime = create_runtime()` construction or loses `get_server_runtime_provider()`.
