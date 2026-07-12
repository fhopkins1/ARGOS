# EO-CL - Enterprise Communications Bus

EO-CL adds the Enterprise Communications Bus, the typed internal transport fabric for ARGOS enterprise messages.

The bus transports authority-bearing records, observations, events, commands, workflow handoffs, health signals, audit notifications, and system notifications. It does not create authority.

## Responsibilities

- Create immutable enterprise message envelopes.
- Validate schema, source authority metadata, idempotency, payload hashes, and paper/live mode.
- Persist message stream, outbox records, acknowledgements, dead letters, quarantine, replay records, correlation trace, audit trail, and metrics in runtime state.
- Route deterministically to registered subscribers.
- Preserve correlation and causation context.
- Support replay-safe analytical replay and guarded production redelivery paths.
- Expose transport health and Commander visibility.

## Message Taxonomy

Supported message kinds:

- `COMMAND`
- `EVENT`
- `OBSERVATION`
- `QUERY`
- `QUERY_RESPONSE`
- `WORKFLOW_HANDOFF`
- `MISSION_MESSAGE`
- `HEALTH_SIGNAL`
- `POLICY_PUBLICATION`
- `AUDIT_NOTIFICATION`
- `RECOVERY_MESSAGE`
- `SYSTEM_NOTIFICATION`

## Runtime Integration

The runtime exposes EO-CL under `enterpriseCommunicationsBus`.

API routes:

- `GET /api/communications-bus/state`
- `POST /api/communications-bus/publish`
- `POST /api/communications-bus/retry`
- `POST /api/communications-bus/replay`
- `POST /api/communications-bus/recover`
- `POST /api/communications-bus/trace`

Runtime enterprise events published through EAB are mirrored into EO-CL as `ENTERPRISE_ACTIVITY_EVENT` messages.

EO-CK position monitoring observations are published into EO-CL as `POSITION_MONITORING_OBSERVATION` messages and routed to the EO-CC subscriber.

## Commander Bridge

The ARGOS Control Panel displays:

- bus health
- delivery success rate
- outbox depth
- retry backlog
- dead-letter count
- quarantine count
- live and paper lane latency
- active and unavailable subscribers
- message stream
- correlation trace index
- dead-letter queue
- quarantine records
- subscriber health
- schema registry
- LAW VII / authority boundaries
- transport audit

## Safety Boundaries

EO-CL does not:

- authorize missions
- wake offices
- transfer Workflow Execution Token ownership
- execute business logic
- place trades
- mutate ledgers
- assign enterprise priority
- spend budget
- invoke AI for routing or routine transport

Delivery is not execution. A delivered mission, workflow, or broker message still requires validation by the authoritative subsystem.

## Paper/Live Isolation

Messages carry `paper_live_mode`.

Authority-sensitive paper messages targeting live broker subscribers are rejected and quarantined.

## Replay

Analytical replay creates a linked replay message and marks `productionMutation` false.

Dangerous production redelivery requires explicit authorization and remains subject to subscriber and authority validation.
