# EO-015 Executive Dashboard

The Executive Dashboard is a read-only deterministic projection over existing
Foundation and Executive records. It does not duplicate data, modify decisions,
perform analysis, or implement trading logic.

## Displays

- pending packets
- rejected packets
- recent decisions
- executive clock
- queue depth
- decision throughput
- utilization
- organizational health
- command table

## Traceability

Every displayed value includes a source reference such as a persistence record,
decision registry entry, routing log, or Executive Clock source.

## Refresh and Audit

`ExecutiveDashboard.refresh()` and related filter/sort/table interactions create
audit events where appropriate through the Foundation Audit Service.

