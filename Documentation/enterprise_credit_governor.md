# Enterprise Credit Governor

The Enterprise Credit Governor minimizes API credit consumption while preserving ARGOS operational capability. It keeps AI offices dormant by default, validates AI activations, enforces budgets, detects waste patterns, and reports spend by organization, office, workflow, task, and operational output.

## Responsibilities

- Keep AI offices dormant unless activated by the Commander, an authorized predecessor office, a scheduled workflow, a valid enterprise event, or a critical alert.
- Require every activation to include task identifier, activating source, receiving office, purpose, required output, maximum runtime, maximum credit budget, evidence package, return route, and audit identifier.
- Prevent continuous autonomous loops, free-form cross-office chatter, self-activation, unauthorized activation, and untraced API usage.
- Enforce deterministic workflow precedence:
  Commander -> Executive -> Seeker -> Analyst -> Risk -> Executive -> Trader -> Historian -> Librarian -> Academy.
- Maintain daily, weekly, monthly, office, workflow, and task budgets.
- Activate Warning Mode, Restricted Mode, Commander Approval Mode, or Hard Stop Mode as budget thresholds are reached.
- Prefer deterministic code for data ingestion, calculations, logs, alerts, scheduling, dashboards, and event routing.
- Reserve AI inference for synthesis, ambiguous reasoning, conflict analysis, Historian reflection, Librarian summary, Academy lesson generation, and Commander-requested explanations.

## Runtime Integration

Implementation lives in `src/argos/control_panel/credit_governor.py`.

API endpoints:

- `GET /api/credit-governor/state`
- `POST /api/credit-governor/configure`
- `POST /api/credit-governor/activate`
- `POST /api/credit-governor/complete`

## Dashboard Surface

The ARGOS Control Panel displays:

- current credit mode
- daily, weekly, monthly, office, workflow, and task budgets
- AI activation gate
- spend report
- credit-governor detections
- activation history

## Auditability

Every budget override and activation decision is published through the Enterprise Activity Bus. Rejected activations are preserved and never silently discarded.
