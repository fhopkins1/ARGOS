# IFVR Phase 2.5 Canonical Runtime Architecture

## Final Composition Root
`CanonicalEnterpriseRuntime` is now the production runtime owned by `CanonicalRuntimeProvider`.

Production startup path:

`server.py::run` -> `get_server_runtime_provider()` -> `CanonicalRuntimeProvider` -> `CanonicalEnterpriseRuntime`

The provider exposes:
- runtime identity;
- creation timestamp;
- mode;
- truth domain;
- health;
- started/halt state;
- live-trading disabled state.

## Server Integration
`server.py` now creates the canonical provider at startup and exposes `/api/runtime/provider` as an inspection endpoint. Production `/api/paper/start` and `/api/paper/halt` delegate to the provider.

Legacy proof self-training was moved to explicit compatibility routes:
- `/api/proof/paper/start`
- `/api/proof/paper/halt`

## Compatibility Adapter
`ControlPanelRuntime` remains because the dashboard and many existing tests use its broad read model. It now owns a `canonical_runtime` and shares critical stateful authorities from that canonical graph for workflow orchestration, communications, cost governance, doctrine/policy, market data, mission planning, performance truth, position monitoring, strategic intelligence, workflow delta, freshness, memory cache, and priority.

## Live Trading
Live trading remains disabled. `CanonicalRuntimeProvider` rejects injected canonical runtimes with `live_trading_enabled=True`.

## Remaining Limitation
`runtime.py` is not yet a fully thin facade. It is partially converged for critical authorities but still contains many compatibility command/read-model responsibilities.
