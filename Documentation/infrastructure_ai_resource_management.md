# Infrastructure & AI Resource Management

The Infrastructure & AI Resource Management system is the technical operations center for the ARGOS Control Panel. It continuously measures AI usage, token consumption, resource utilization, operating cost, infrastructure health, optimization opportunities, alerts, and Commander overrides.

## Responsibilities

- Monitor AI model usage, token consumption, CPU, memory, storage, database health, network activity, queue length, workflow throughput, organization availability, and infrastructure health.
- Calculate daily and monthly token usage, daily and monthly operating cost, organization resource consumption, office resource consumption, workflow cost, and AI utilization.
- Generate deterministic optimization recommendations for scheduling, resource allocation, runtime reduction, prompt optimization, scaling, and budget management.
- Support Commander controls for daily budget, monthly budget, runtime limits, cost saving mode, high performance mode, and organization resource limits.
- Generate alerts for budget thresholds, infrastructure failures, resource exhaustion, excessive token usage, API failures, database failures, and unexpected cost growth.
- Preserve historical usage, cost, health, optimization actions, and Commander overrides.

## Runtime Integration

Implementation lives in `src/argos/control_panel/infrastructure.py` and is integrated into `ControlPanelRuntime`.

Dashboard API endpoints:

- `GET /api/infrastructure/state`
- `POST /api/infrastructure/configure`
- `POST /api/infrastructure/optimization`

The manager consumes existing deterministic runtime signals:

- visible operating costs
- scheduler office states
- Enterprise Activity Bus throughput
- resource utilization values
- audit event counts

## Dashboard Surface

The control panel displays:

- daily and monthly token usage
- daily and monthly operating cost
- daily and monthly budget utilization
- AI model usage
- infrastructure health
- alerts
- optimization recommendations
- Commander budget and mode controls

## Auditability

Commander configuration changes and optimization actions are published to the Enterprise Activity Bus. Historical resource records remain append-only within the runtime session and contain deterministic audit identifiers.
