# OR-001 Repository Architecture Report

## Scope

This report inventories the ARGOS repository as observed on 2026-07-10. Evidence is repository-local only.

## Repository Shape

- Root project files: `README.md`, `PROJECT_HANDOFF.md`, `pyproject.toml`, `.env.example`, `Launch_ARGOS_Control_Panel.cmd`.
- Runtime source: `src/argos`.
- Local web UI: `ui/argos_control_panel/index.html`, `ui/argos_control_panel/app.js`, `ui/argos_control_panel/styles.css`.
- Launch scripts: `Scripts/start_argos_control_panel.py`, `Scripts/launch_argos_control_panel.ps1`, `Scripts/verify_repository_structure.py`.
- Tests: `Tests/` contains broad unit coverage, including `Tests/test_argos_control_panel_dashboard.py`.
- Documentation: `Documentation/` contains office, framework, and Series C EO documents.
- Outputs: `outputs/` contains prior readiness and completion reports.

## Runtime Inventory

### Enterprise Runtime

- `src/argos/control_panel/runtime.py` is the central local runtime. `ControlPanelRuntime.__init__` constructs audit, persistence, Executive control, EAB, Communications Bus, Doctrine Policy Manager, scheduler, workflow orchestrator, API gateway, performance truth, analytics, strategic, market, risk, and position systems.
- `src/argos/control_panel/server.py` exposes a local HTTP server and maps `/api/*` endpoints to `ControlPanelRuntime`.
- `Scripts/start_argos_control_panel.py` inserts `src` into `sys.path` and calls `argos.control_panel.server.main`.

### Scheduling, Missions, Wakefulness

- `src/argos/control_panel/scheduler.py` implements `OfficeScheduler`, `EnterpriseMission`, mission transitions, office activation requests, operating modes, budget checks, duplicate suppression, and market-session deferral.
- `src/argos/control_panel/office_duty_officer.py` implements `OfficeDutyOfficerRegistry` and pre-wake triage.
- `src/argos/control_panel/event_detection_engine.py`, `mission_planner.py`, `enterprise_cost_governor.py`, `information_freshness_engine.py`, `enterprise_memory_cache.py`, `workflow_delta_engine.py`, `enterprise_priority_engine.py`, `position_monitoring_network.py`, `enterprise_communications_bus.py`, `enterprise_efficiency_analytics.py`, and `enterprise_doctrine_policy_manager.py` implement most documented Enterprise Operations Series C systems.

### Workflow Execution Tokens

- `src/argos/control_panel/workflow_orchestrator.py` defines `WorkflowExecutionToken`, `WorkflowRecord`, `OwnershipTransferAudit`, and deterministic lifecycle transitions.
- `src/argos/control_panel/workflow_runtime_monitor.py` renders token timelines, LAW VII panels, token integrity, global alerts, and active owner checks.

### Broker, Orders, Positions, Performance Truth

- `src/argos/trader/broker_integration.py` defines broker request/response types and `DeterministicPaperBrokerAdapter`.
- `src/argos/trader/order_management.py`, `position_management.py`, `trade_execution.py`, `trade_monitoring.py`, and `execution_quality.py` implement office-level deterministic trading lifecycle models.
- `src/argos/control_panel/performance_truth_engine.py` records paper/live-separated orders, fills, positions, trades, valuations, benchmarks, decision outcomes, workflow attribution, and integrity metadata.
- `src/argos/control_panel/position_registry.py`, `position_sizing_engine.py`, `position_surveillance_engine.py`, `position_exit_decision_engine.py`, and `closed_position_truth.py` implement control-panel position lifecycle surfaces.

### Persistence, Replay, Audit

- `src/argos/foundation/audit/*` provides append-only in-memory audit events with hash-chain integrity and case-file replay.
- `src/argos/foundation/persistence/*` provides an append-only in-memory repository, immutable records, schema definitions, migration descriptors, backup/restore, and replay helpers.
- `src/argos/control_panel/market_replay_engine.py` and `enterprise_reproducibility_framework.py` provide replay/reproducibility surfaces.

### Dashboards and Bridges

- Commander and operational surfaces are in `src/argos/control_panel/command_console.py`, `ecc.py`, `cnac.py`, `commander_strategic_dashboard.py`, `commander_briefing_generator.py`, and `commander_daily_review_workspace.py`.
- UI bridge implementation is in `ui/argos_control_panel/app.js`; backend routes are in `src/argos/control_panel/server.py`.

## Architecture Finding

ARGOS is not an EO-001 skeleton. The root `README.md` still states EO-001 scope and “no runtime trading behavior,” but `PROJECT_HANDOFF.md` and the source tree show a broad deterministic enterprise runtime with a local control panel, paper trading, workflow orchestration, and operational engines.

