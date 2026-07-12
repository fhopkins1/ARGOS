# EO-CK - Position Monitoring Network

EO-CK adds a bounded Position Monitoring Network for active ARGOS Position Objects.

The network creates deterministic watchers around open positions and emits monitoring events for downstream event detection. It does not execute exits, wake offices, mutate positions, mutate ledgers, or invoke AI for routine display.

## Responsibilities

- Watch active positions for stop-loss, profit-target, trailing-stop, drawdown, volatility, holding-period, broker-state, risk-trigger, earnings-proximity placeholder, and data-quality conditions.
- Produce a watcher roster, latest monitoring events, monitoring passes, watcher coverage, audit history, and dead-letter visibility.
- Feed high-priority position signals to EO-CC through `eventDetectionFeed`.
- Expose restart recovery and replay views for deterministic verification.

## Runtime Integration

The runtime exposes EO-CK under `positionMonitoringNetwork` in the control-panel state payload.

API routes:

- `GET /api/position-monitoring/state`
- `POST /api/position-monitoring/scan`
- `POST /api/position-monitoring/recover`
- `POST /api/position-monitoring/replay`

## Safety Boundaries

EO-CK is an observation layer only.

- No order placement.
- No direct exit decisions.
- No mission authorization.
- No office activation.
- No position or ledger mutation.
- No routine AI calls.
- No uncontrolled loops.

## Commander Visibility

The ARGOS Control Panel displays:

- network status and watcher counts
- watcher roster
- monitoring events
- watcher coverage
- EO-CC event feed readiness

## EO-CC Bridge

EO-CC reads `positionMonitoringNetwork.eventDetectionFeed` and may validate high or critical monitoring events into the Event Detection Engine. EO-CK itself only emits event candidates.
