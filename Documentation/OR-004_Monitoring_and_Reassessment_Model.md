# OR-004 Monitoring and Reassessment Model

## Monitoring Sources

- Active positions from `PositionRegistry`.
- Market snapshots from `MarketDataProviderAbstractionLayer`.
- Surveillance events from `PositionSurveillanceEngine`.
- Advisory monitoring events from `PositionMonitoringNetwork`.

## Behavior

`EnterprisePositionLifecycleManager.monitor_positions()` gathers active positions, applies market marks, runs surveillance, runs monitoring watchers, and publishes an EO-CL observation event. This path observes and annotates risk; it does not open, close, or resize positions.

## Reassessment

`EnterprisePositionLifecycleManager.evaluate_exits()` evaluates surveillance and risk context through `ExitDecisionEngine`. Recommendations remain advisory until `authorize_exit()` is called with valid provenance and risk/policy approval identifiers.

## Fail-Closed Controls

- Missing position identity prevents authorization.
- Missing decision provenance prevents authorization.
- Missing risk or policy approval prevents authorization.
- Requested exit quantity above available quantity is rejected.
- Monitoring events do not carry trading authority.
