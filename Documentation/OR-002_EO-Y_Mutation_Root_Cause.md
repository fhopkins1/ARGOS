# OR-002 EO-Y Mutation Root Cause

## Trigger

The failing test was:

`test_eo_y_calibration_does_not_mutate_positions_ledgers_or_invoke_ai`

The test called `runtime.state()` twice after recording a manual paper order. The first call observed `historyRecordCount == 2`; the second call observed `historyRecordCount == 3`.

## Root Cause

The mutation did not originate inside `EnterpriseRealityCalibrationEngine`. The calibration engine is read-only over dictionary snapshots.

The mutation occurred during `ControlPanelRuntime.state()` assembly before calibration. Runtime called:

- `PositionSurveillanceEngine.surveil(position_registry=..., ...)`
- `ExitDecisionEngine.evaluate(position_registry=..., ...)`

Those engines are legitimate operational engines and can mutate the `PositionRegistry` when run in active operational mode. However, state assembly and calibration are Commander/advisory read paths. They must not append registry history.

## Violated Contract

Commander state polling and EO-Y calibration must not mutate:

- Position ledgers
- Position registry history
- Orders
- Fills
- Trades
- Portfolio valuations
- AI invocation records

## Fix

- Added `mutate_registry: bool = True` to `PositionSurveillanceEngine.surveil`.
- Added `mutate_registry: bool = True` to `ExitDecisionEngine.evaluate`.
- Updated `ControlPanelRuntime._position_surveillance_state` to call surveillance with `mutate_registry=False`.
- Updated `ControlPanelRuntime._position_exit_decision_state` to call exit evaluation with `mutate_registry=False`.
- Direct engine tests retain default mutating behavior for explicit operational surveillance.

## Regression Tests

- `test_eo_y_calibration_does_not_mutate_positions_ledgers_or_invoke_ai` now passes.
- `test_eo_xb_runtime_exposes_position_surveillance_without_background_worker_or_ai` now asserts runtime dashboard surveillance is read-only.

