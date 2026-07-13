# IFVR Phase 2.5 Truth Domain Runtime Isolation

## Paper
Production paper lifecycle routes use `CanonicalRuntimeProvider` and `CanonicalEnterpriseRuntime`.

## Proof
Legacy paper self-training is explicitly proof-routed under `/api/proof/paper/*`.

## Simulation/Replay
Decision Laboratory and replay surfaces remain compatibility/simulation routes. They are not accepted by the production provider as paper runtime.

## Live
Live remains disabled. Provider construction rejects canonical runtimes with `live_trading_enabled=True`.

## Test Evidence
`test_provider_rejects_live_runtime_injection` verifies live runtime injection is refused.
