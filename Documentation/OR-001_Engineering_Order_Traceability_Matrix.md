# OR-001 Engineering Order Traceability Matrix

## Traceability Limitation

The repository does not contain a single canonical Engineering Order index mapping every EO from `EO-A` through `EO-CO` to source modules. This is itself an OR-001 finding. Traceability below is built from available repository evidence: documentation filenames, test names, module names, `PROJECT_HANDOFF.md`, and runtime wiring.

## Foundation Orders

| Order / Area | Evidence | Status | Notes |
|---|---|---:|---|
| EO-001 repository skeleton | `README.md`, `Scripts/verify_repository_structure.py`, `Tests/test_repository_structure.py` | Implemented, superseded | Root README is obsolete because runtime now exists. |
| EO-002 identity framework | `src/argos/foundation/identity/*`, `Documentation/identity_framework.md` | Implemented | Deterministic identifier validation and registry exist. |
| EO-003 contracts | `src/argos/foundation/contracts/base.py`, `Documentation/canonical_data_contract_framework.md` | Implemented | Base/operational/infrastructure contracts exist. |
| EO-004 courier communication | `src/argos/foundation/communication/*`, `Documentation/deterministic_communication_courier_framework.md` | Implemented | Mailbox/courier rules reject direct delivery. |
| EO-005 audit traceability | `src/argos/foundation/audit/*`, `Documentation/audit_traceability_framework.md` | Implemented | Hash-chain in-memory audit log and replay exist. |
| EO-006 configuration | `src/argos/foundation/configuration/*`, `Documentation/configuration_environment_framework.md` | Implemented | Live trading cannot be enabled by default config validation. |
| EO-007 persistence | `src/argos/foundation/persistence/*`, `Documentation/database_persistence_foundation.md` | Partially implemented | Append-only and hash-chained, but in-memory only. |
| EO-008 prompt/specification repository | `src/argos/foundation/prompts/*`, `Documentation/prompt_specification_repository.md` | Implemented | Prompt repository/snapshots exist. |
| EO-009 testing framework | `src/argos/foundation/testing/*`, `Documentation/foundation_testing_framework.md` | Implemented | Registry, runner, and reports exist. |

## Enterprise Group Orders

| Area | Evidence | Status |
|---|---|---:|
| Executive Group | `src/argos/executive/*`, `Documentation/executive_group_framework.md`, `executive_workflow.md`, `commander_decision_engine.md` | Implemented |
| Seeker Group | `src/argos/seeker/*`, `Documentation/seeker_department_framework.md`, seeker office docs | Implemented |
| Analyst Group | `src/argos/analyst/*`, `Documentation/analyst_department_framework.md`, analyst office docs | Implemented |
| Risk Office | `src/argos/risk/*`, `Documentation/risk_office_framework.md`, risk office docs | Implemented |
| Trader Group | `src/argos/trader/*`, `Documentation/trader_group_framework.md`, trader office docs | Implemented |
| Historian Group | `src/argos/historian/*`, historian docs | Implemented |
| Librarian Group | `src/argos/librarian/*`, librarian docs | Implemented |
| Academy | `src/argos/academy/*`, academy docs | Implemented |

## Operations / Control Panel Orders

| Order | Primary Modules / Docs | Status | Runtime Wiring |
|---|---|---:|---|
| OE-100 / OE-100A Command Bridge | `command_console.py`, `runtime.py`, `ui/argos_control_panel/app.js` | Implemented | Wired through `/api/ecc/action` and dashboard state. |
| OE-101 Executive Subcommand Bridge | `ecc.py`, `runtime.py`, UI | Implemented | Wired. |
| OE-102 Seeker Intelligence Bridge | `runtime.py`, Seeker/market modules, UI | Implemented | Wired. |
| OE-010 Workflow Orchestrator | `workflow_orchestrator.py`, `workflow_runtime_monitor.py` | Implemented | Wired to runtime and API gateway. |
| OE-011A API Execution Gateway | `api_execution_gateway.py`, `api_runtime_monitor.py` | Implemented | Wired; dry-run default. |
| EO-CA Enterprise Operations Scheduler | `scheduler.py`, `Documentation/EO-CA_Enterprise_Operations_Scheduler.md` | Implemented | Wired in runtime and `/api/eos/control`. |
| EO-CB Office Duty Officer | `office_duty_officer.py`, `Documentation/EO-CB_Office_Duty_Officer.md` | Implemented | Wired through scheduler and `/api/odo/task`. |
| EO-CC Event Detection Engine | `event_detection_engine.py`, `Documentation/EO-CC_Event_Detection_Engine.md` | Implemented | Wired to `/api/event-detection/*`. |
| EO-CD Mission Planner | `mission_planner.py`, `Documentation/EO-CD_Enterprise_Mission_Planner.md` | Implemented | Wired to `/api/mission-planner/*`. |
| EO-CE Cost Governor | `enterprise_cost_governor.py`, `Documentation/EO-CE_Enterprise_Cost_Governor.md` | Implemented | Wired to gateway and `/api/cost-governor/*`. |
| EO-CF Freshness Engine | `information_freshness_engine.py`, `Documentation/EO-CF_Information_Freshness_Engine.md` | Implemented | Wired to memory/delta/runtime state. |
| EO-CG Memory Cache | `enterprise_memory_cache.py`, `Documentation/EO-CG_Enterprise_Memory_Cache.md` | Implemented | Wired to freshness and runtime state. |
| EO-CH Workflow Delta Engine | `workflow_delta_engine.py`, `Documentation/EO-CH_Workflow_Delta_Engine.md` | Implemented | Wired to freshness/cache/runtime state. |
| EO-CI Wakefulness Manager | No matching doc/module found | Missing | No repository evidence. |
| EO-CJ Priority Engine | `enterprise_priority_engine.py`, `Documentation/EO-CJ_Enterprise_Priority_Engine.md` | Implemented | Wired to scheduler feed/state. |
| EO-CK Position Monitoring Network | `position_monitoring_network.py`, `Documentation/EO-CK_Position_Monitoring_Network.md` | Implemented | Wired to performance truth and communications bus. |
| EO-CL Communications Bus | `enterprise_communications_bus.py`, `Documentation/EO-CL_Enterprise_Communications_Bus.md` | Implemented | Wired in runtime with policy schema registration. |
| EO-CM | No matching doc/module found | Missing | No repository evidence. |
| EO-CN Efficiency Analytics | `enterprise_efficiency_analytics.py`, `Documentation/EO-CN_Enterprise_Efficiency_Analytics.md` | Implemented | Wired to runtime state. |
| EO-CO Doctrine & Policy Manager | `enterprise_doctrine_policy_manager.py`, `PROJECT_HANDOFF.md` | Implemented, doc gap | Runtime module exists; `Documentation/EO-CO_*.md` was not found. |

## Confidence

Confidence is high for runtime-wired Series C modules because `ControlPanelRuntime.__init__` imports and instantiates them. Confidence is medium for older EO letters because the repository lacks a canonical EO-A-through-CO index.

