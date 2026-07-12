# OR-004 Position Lifecycle Architecture

## Scope

OR-004 introduces a broker-confirmed position lifecycle layer for paper operations. The implementation binds OR-003 broker realism to position registry state, monitoring, exit authorization, broker order submission, closed-position truth, and reconciliation.

## Implemented Components

- `EnterprisePositionLifecycleManager` coordinates monitoring, exit evaluation, authorization, broker submission, and reconciliation.
- `PositionRegistry` now carries broker order IDs, fill IDs, workflow lineage, mission/trader/account identity, pending close quantity, available quantity, realized P&L from fills, and valuation provenance.
- `PerformanceTruthEngine.record_broker_authoritative_order` forwards broker fills into the registry and computes realized sell P&L from the current cost basis.
- `ClosedPositionTruthBuilder` treats `SETTLED` OR-003 broker orders as broker-confirmed orders for closure reconciliation.
- EO-CK monitoring, position surveillance, exit decisioning, EO-CL events, and closed truth are reused rather than bypassed.

## Lifecycle Flow

1. A paper broker fill is recorded by OR-003 and ingested into Performance Truth.
2. A buy fill creates or increases a supervised `PositionObject`.
3. Monitoring and surveillance observe current positions using market data provenance.
4. Exit decisions are advisory until explicitly authorized.
5. Authorization reserves close quantity and moves the position to `exit_pending`; it does not reduce quantity or close the position.
6. Only broker-confirmed sell fills reduce the position.
7. Closed-position truth reconciles matching broker-confirmed opening and closing orders before closure is certified.

## Operational Rule

Position state is not allowed to imply execution. Registry quantity changes require broker-confirmed fill identity.
