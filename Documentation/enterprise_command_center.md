# Enterprise Command Center

The Enterprise Command Center (ECC) is the primary operational interface for the ARGOS Deterministic Cognitive Enterprise.

## Responsibilities

- Aggregate operational state from Executive, Seeker, Analyst, Risk, Trader, Historian, Librarian, Academy, and Infrastructure.
- Maintain current status, task, workflow, mode, alerts, resource usage, and recent activity for every organization.
- Provide deterministic drill-down from enterprise to organization, office, workflow, task, supporting evidence, historical records, and audit references.
- Execute Commander actions through audited control paths.
- Monitor workflow deadlocks, unresponsive organizations, queue congestion, infrastructure failures, operational drift, communication failures, and active alerts.

## Commander Actions

The dashboard supports these audited actions:

- Pause Organization
- Resume Organization
- Change Operating Mode
- Configure Schedule
- Review Evidence
- Inspect Workflows
- View Historical Activity
- Export Reports

Every action creates an `ECC_COMMANDER_ACTION` operational document and a staff-decision audit event.

## Runtime Interfaces

- `GET /api/state` returns the dashboard state and embedded `ecc` model.
- `POST /api/ecc/action` executes an audited Commander action.
- `POST /api/ecc/export` generates an ECC report and audits the export.

## Safety Boundaries

The ECC does not perform market analysis, trading strategy, or live execution. It supervises operational state and routes Commander intent through deterministic, auditable control interfaces.
