# OR-004 Persistence and Recovery Requirements

## Required Persistent State

- Position registry objects and history.
- Broker order IDs and fill IDs.
- Workflow token lineage.
- Exit authorization records.
- Lifecycle reconciliation records.
- Closed-position truth records.
- Market valuation provenance.

## Recovery Requirements

On restart or replay, the system must:

- Rebuild positions from broker-authoritative fills without duplicate fill application.
- Preserve pending close reservations.
- Reconcile existing closed-position truth before creating new closure records.
- Retain rejected authorization and reconciliation codes.
- Refuse to infer closure from advisory exit recommendations.

## Current Implementation Note

The in-memory components now carry the required state fields and idempotent fill behavior. Durable persistence wiring is still a future integration requirement unless the hosting runtime snapshots these objects externally.
