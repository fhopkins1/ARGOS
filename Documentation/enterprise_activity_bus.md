# Enterprise Activity Bus

The Enterprise Activity Bus (EAB) is the deterministic communication backbone for the ARGOS Control Panel and Enterprise Command Center.

## Responsibilities

- Receive operational events from ARGOS organizations, Infrastructure, and Commander Interface.
- Normalize every event into a canonical enterprise event format.
- Timestamp, sequence, archive, and audit each event.
- Distribute events according to deterministic organizational subscriptions.
- Publish events to the Enterprise Activity Feed, Commander notifications, Alert Center, and historical timeline.
- Support Commander filtering by organization, office, severity, workflow, asset, portfolio, case file, status, and time.

## Canonical Event Fields

- Event Identifier
- Timestamp
- Organization
- Office
- Workflow
- Task Identifier
- Event Category
- Severity
- Summary
- Detailed Description
- Supporting Evidence
- Correlation Identifier
- Audit Identifier
- Asset
- Portfolio
- Case File
- Status

## Subscriptions

- Commander receives every enterprise event.
- Historian receives complete enterprise activity.
- Executive receives critical and emergency enterprise events.
- Trader receives execution, command, and trading events relevant to execution.
- Academy receives validated knowledge and education events.
- Alert Center receives warning, critical, and emergency events.

## Runtime Interfaces

- `GET /api/state` returns the current EAB snapshot.
- `GET /api/eab/events` returns the filtered EAB snapshot.

## Integrity Monitoring

The EAB reports event throughput, latency, chronological ordering, communication health, subscription health, correlation integrity, delivery success, archive depth, duplicate events, broken correlations, unauthorized events, delayed events, lost events, and communication failures.
