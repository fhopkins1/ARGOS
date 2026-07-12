# OR-004 Position and Trade Identity Model

## Position Identity

Positions retain the existing registry `position_id` and now also record:

- Broker order IDs.
- Broker fill IDs.
- Workflow token lineage.
- Mission ID.
- Trader identity.
- Account ID.
- Execution mode and truth domain.
- Certification state.

## Fill Identity

Broker fills are ingested from OR-003 into Performance Truth and then into `PositionRegistry`. Duplicate fill IDs are ignored so replay does not double-count quantity or P&L.

## Trade Identity

Sell orders carry realized P&L derived from the current position average cost, broker fill price, commissions, and slippage. This prevents synthetic zero-P&L sell records from certifying as operational truth.

## Provenance

Market valuation updates retain source, quote ID, timestamp, and mark price where available. Position lifecycle records preserve workflow token lineage so a closed position can be traced back to the authorization and broker execution path.
