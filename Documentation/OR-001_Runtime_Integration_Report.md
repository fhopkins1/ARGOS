# OR-001 Runtime Integration Report

## Startup Trace

1. `Launch_ARGOS_Control_Panel.cmd` invokes `Scripts/launch_argos_control_panel.ps1`.
2. `Scripts/start_argos_control_panel.py` adds `src` to Python import path and calls `argos.control_panel.server.main`.
3. `src/argos/control_panel/server.py` creates `ControlPanelRuntime` and serves UI plus `/api/*` routes.
4. `ControlPanelRuntime.__init__` constructs in-memory audit, in-memory persistence, Executive control panel, activity bus, communications bus, doctrine policy manager, scheduler, workflow orchestrator, API gateway, performance truth engine, dashboards, and analytics engines.

## Mission and Workflow Path

- Missions are planned and authorized through `OfficeScheduler` and `EnterpriseMissionPlanner`.
- Duty Officer requests are triaged by `OfficeDutyOfficerRegistry` before office wake recommendations.
- Workflow execution is controlled by `EnterpriseWorkflowOrchestrator` using one `WorkflowExecutionToken` per workflow.
- Paper self-training creates `paper_trading_session` workflows through `ControlPanelRuntime.start_paper_self_training`, then advances stages in `_paper_trading_workflow_loop`.
- Model/API execution must pass `ApiExecutionGateway`, which validates workflow token ownership, credit authorization, cost authorization, prompt contract, and output schema.

## Runtime Execution Path

- Opportunity / event discovery: `event_detection_engine.py`, Seeker modules, market context, and operations bridge state.
- Workflow generation: `mission_planner.py`, `scheduler.py`, `workflow_orchestrator.py`.
- Token ownership: `workflow_orchestrator.py` lifecycle states.
- Office activation: `scheduler.py` and `office_duty_officer.py`.
- Decision production: `_paper_decision_object` in `runtime.py`, `decision_object_schema.py`, `decision_object_quality_scoring.py`, `decision_explainability_engine.py`.
- Risk approval surfaces: Risk package modules plus `enterprise_operational_guardrails.py`, `enterprise_risk_factor_engine.py`, and position/stress engines.
- Trader authorization and broker submission: Trader group modules and `performance_truth_engine.py` paper order recording.
- Historian / performance recording: `performance_truth_engine.py`, `trade_attribution_engine.py`, Historian modules.
- Commander reporting: `commander_strategic_dashboard.py`, `commander_briefing_generator.py`, `cnac.py`, `ecc.py`, UI bridge routes.

## Shutdown, Restart, Recovery, Replay

- Shutdown is available at process/server level but there is no durable runtime checkpoint in the control panel runtime.
- Recovery modules exist: `enterprise_failure_recovery.py`, persistence backup/restore, communications bus recovery, market replay, and reproducibility framework.
- Restart does not reload workflows, orders, missions, or performance truth from disk because the active runtime uses in-memory stores.

## Integration Gaps

- Persistent runtime state is not durable across process restart.
- Root `README.md` is obsolete relative to `PROJECT_HANDOFF.md` and current source.
- EO-CO implementation exists without a matching `Documentation/EO-CO_*.md` file.
- EO-CI and EO-CM were not found.
- Many office modules implement deterministic products, but the control panel runtime is the primary integration path; not every older office module is directly reachable through server routes.

