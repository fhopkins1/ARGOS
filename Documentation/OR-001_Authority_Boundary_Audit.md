# OR-001 Authority Boundary Audit

## Boundary Evidence

- Executive control panel blocks real-world trading unless gate requirements and configuration are satisfied in `src/argos/executive/control_panel.py`.
- Workflow ownership is enforced by `src/argos/control_panel/workflow_orchestrator.py`.
- API/model usage is rejected when the requesting office is not the current workflow token owner.
- Office Duty Officers declare that they do not bypass scheduler, workflow tokens, or full office wake authority in `office_duty_officer.py`.
- Communications Bus documentation and runtime state describe transport as non-authority.
- Performance Truth Engine separates paper and live environments.

## Authority Checks

| Boundary | Finding |
|---|---|
| Commander does not fabricate decisions | Mostly compliant. Commander surfaces display/report state; decision objects are generated in workflow/runtime paths. |
| Analyst does not trade | Mostly compliant. Analyst participates in workflow outputs; order/fill recording is in performance/trader systems. |
| Trader does not analyze | Mostly compliant at module boundary; trader modules focus on order, execution, monitoring, positions, and broker integration. |
| Historian does not authorize | Mostly compliant; historian modules measure/evaluate/record. |
| Runtime does not bypass offices | Partially compliant. Runtime coordinates all systems, but paper workflow placeholder completion is centralized in `runtime.py`. |
| Execution Gateway does not fabricate outcomes | Compliant for live outcomes; dry-run structured outputs are explicit. |
| Performance Truth Engine does not fabricate history | Mostly compliant for ledgers; paper order simulation is deterministic and isolated. |
| Decision Laboratory cannot mutate production truth | Mostly compliant based on naming and runtime routing; deeper certification should verify no write path to Performance Truth. |
| Commander dashboards remain read-only | Mostly compliant for GET routes; POST routes exist for Commander actions and operational controls. |

## Violations / Risks

- No confirmed hard authority violation was found.
- Risk: `ControlPanelRuntime` is a large coordinator that can create paper workflows, advance placeholder stages, generate decision objects, and record completed workflows. This should be certified as orchestration-only in OR-002.
- Risk: UI POST routes can trigger operational actions; read-only Commander dashboard surfaces should remain separated from action endpoints.

