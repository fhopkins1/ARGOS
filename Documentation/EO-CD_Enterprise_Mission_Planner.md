# EO-CD - Enterprise Mission Planner

EO-CD adds the Enterprise Mission Planner, the deterministic planning layer between validated operational triggers and EO-CA scheduler authorization.

## Core Boundary

Planning is not authorization.

The planner may intake triggers, select templates, define objectives, choose a minimum workforce, build dependencies, estimate resources, validate plans, and submit ready plans to EO-CA. It does not wake offices, start workflows, call AI for mission execution, submit broker orders, mutate positions, mutate ledgers, reserve credits, or approve its own work.

## Implemented Components

- `src/argos/control_panel/mission_planner.py`
  - `EnterpriseMissionPlanner`
  - `MissionTrigger`
  - `MissionObjective`
  - `MissionOfficeAssignment`
  - `MissionDependency`
  - `MissionInputRequirement`
  - `MissionOutputContract`
  - `MissionResourceEnvelope`
  - `MissionCompletionPolicy`
  - `MissionTemplateRecord`
  - `MissionPlanRecord`

## Initial Template Inventory

- `position_safety_review_v1`
- `broker_reconciliation_v1`
- `end_of_day_reconciliation_v1`
- `commander_briefing_v1`
- `earnings_reassessment_v1`
- `opportunity_scan_v1`
- `strategic_research_v1`
- `information_refresh_v1`
- `enterprise_recovery_v1`
- `cost_review_v1`

Templates are versioned and include supported trigger types, mandatory offices, conditional offices, prohibited offices, default sequence, cost class, runtime ceiling, API-call ceiling, and completion criteria.

## Runtime and API

The runtime exposes planner state under `enterpriseMissionPlanner`.

POST routes:

- `/api/mission-planner/plan-event`
- `/api/mission-planner/commander-request`
- `/api/mission-planner/submit`
- `/api/mission-planner/replay`

Submitting a plan creates an EOS mission record for review. EOS remains the authority for authorization and dispatch.

## Mission Planning Bridge

The UI bridge displays:

- planning queue
- draft mission plans
- minimum workforce decisions
- dependency graph summaries
- resource envelopes
- reuse and delta decisions
- completion and failure policy

## Safety Notes

- Routine planning is deterministic.
- Replay is isolated from production state.
- Suppressed or locally satisfied triggers can produce no-action plans.
- Duplicate related triggers merge into one unresolved plan.
- Critical escalation can supersede an unresolved draft.
- Planner snapshots support restart recovery without duplicate plan generation.

## Known Limitations

- Persistence is currently in-memory through runtime snapshots.
- Cache and information freshness are represented as deterministic integration points until EO-CF and EO-CG provide authoritative services.
- Dependency graphs are sequence-oriented and intentionally lightweight until the future workflow delta engine expands impact analysis.
