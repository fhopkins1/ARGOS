# OR-004 Position Reconciliation Specification

## Closure Inputs

Closed-position truth requires broker-confirmed opening orders and broker-confirmed closing orders for the same symbol and environment. OR-004 recognizes `FILLED`, `PARTIALLY_FILLED`, and `SETTLED` order states.

## Quantity Rule

A position is reconciled as closed only when closing quantity matches opening quantity within the existing tolerance used by `ClosedPositionTruthBuilder`.

## Registry Rule

The registry may reserve close quantity during authorization, but it cannot reduce quantity until a sell fill is accepted from the broker-authoritative path.

## Reconciliation Output

`EnterprisePositionLifecycleManager.reconcile_position()` runs closed truth, ingests the resulting closed-position record into Performance Truth, and emits a lifecycle reconciliation record with:

- Position ID.
- Reconciled closed truth ID.
- Registry status.
- Closed truth status.
- Exit decision state.
- Surveillance state.
- Rejection codes, if any.

## Failure Handling

If closed truth cannot be established, the reconciliation record is marked rejected and the reason is retained for follow-up remediation.
