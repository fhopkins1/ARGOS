# EO-DA Broker and Position Reconciliation Invariants

`BrokerPositionInvariantMonitor` evaluates Performance Truth snapshots.

## Broker Checks

- Filled quantities require Broker order identity.
- Rejected, cancelled, and expired orders cannot contain fills.

## Position Checks

- Open positions require fill or Broker order lineage.
- Position Broker order references must point to filled orders.
- Closed Position Truth must be unique per position.

The monitor verifies existing evidence. It does not create fills, mutate positions, reconcile state, or create Closed Position Truth.

