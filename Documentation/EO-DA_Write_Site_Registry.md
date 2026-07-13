# EO-DA Write-Site Registry

The canonical registry is `authoritative_write_site_registry()`.

## Registered Authoritative Writes

- Scheduler mission creation and dispatch.
- Mission Planner mission plan creation.
- Workflow Orchestrator workflow and token lifecycle writes.
- Trader order intent construction.
- Paper Broker order, event, fill, and settlement writes.
- Position Registry position and history mutation.
- Performance Truth broker-authoritative order ingestion.
- Closed Position Truth closed lifecycle record creation.
- Durable persistence writes and transaction commits.
- Doctrine and Policy version/state writes.

Each write site declares writer, authority, entity, operation, truth domain, provenance requirement, token requirement, idempotency requirement, persistence requirement, pre-write invariants, post-write invariants, and source reference.

