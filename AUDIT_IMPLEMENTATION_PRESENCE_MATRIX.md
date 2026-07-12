# AUDIT Implementation Presence Matrix

| Expected name | Actual file path | Entry point | Present | Tracked | Included | Runtime construction site | Tests/docs | Notes |
|---|---|---|---:|---:|---:|---|---|---|
| OR-001 through OR-007 | `Documentation/OR-001_* through OR-007_*` | `OR reports` | present | yes | yes | Documentation/OR-* | See `Tests/` and `Documentation/OR-*` | docs |
| EO-CA through EO-CO | `src/argos/control_panel/*` | `Series C components` | partial | yes | yes | CanonicalEnterpriseRuntime | See `Tests/` and `Documentation/OR-*` | EO-CO not explicit |
| EO-BS Strategic Intelligence Command | `src/argos/control_panel/strategic_intelligence_command.py` | `StrategicIntelligenceCommand` | present | yes | yes | runtime/dashboard | See `Tests/` and `Documentation/OR-*` |  |
| Workflow Orchestrator | `src/argos/control_panel/workflow_orchestrator.py` | `EnterpriseWorkflowOrchestrator` | present | yes | yes | CanonicalEnterpriseRuntime | See `Tests/` and `Documentation/OR-*` |  |
| Workflow Execution Tokens | `src/argos/control_panel/workflow_orchestrator.py` | `WorkflowExecutionToken` | present | yes | yes | workflow creation/transfer | See `Tests/` and `Documentation/OR-*` |  |
| LAW VII | `src/argos/control_panel/workflow_orchestrator.py` | `exclusive token validation` | present | yes | yes | workflow/token paths | See `Tests/` and `Documentation/OR-*` |  |
| Scheduler | `src/argos/control_panel/scheduler.py` | `EnterpriseOperationsScheduler` | present | yes | yes | CanonicalEnterpriseRuntime.admit_scheduled_obligation | See `Tests/` and `Documentation/OR-*` |  |
| Mission Planner | `src/argos/control_panel/mission_planner.py` | `EnterpriseMissionPlanner` | present | yes | yes | canonical admission | See `Tests/` and `Documentation/OR-*` |  |
| Office Duty Officer | `src/argos/control_panel/office_duty_officer.py` | `OfficeDutyOfficerRegistry` | present | yes | yes | canonical admission | See `Tests/` and `Documentation/OR-*` |  |
| Event Detection | `src/argos/control_panel/event_detection_engine.py` | `EventDetectionEngine` | present | yes | yes | runtime/dashboard | See `Tests/` and `Documentation/OR-*` |  |
| Cost Governor | `src/argos/control_panel/enterprise_cost_governor.py` | `EnterpriseCostGovernor` | present | yes | yes | canonical admission/gateway | See `Tests/` and `Documentation/OR-*` |  |
| API Execution Gateway | `src/argos/control_panel/api_execution_gateway.py` | `ApiExecutionGateway` | present | yes | yes | runtime/server | See `Tests/` and `Documentation/OR-*` |  |
| Freshness | `src/argos/control_panel/information_freshness_engine.py` | `InformationFreshnessEngine` | present | yes | yes | canonical components | See `Tests/` and `Documentation/OR-*` |  |
| Cache | `src/argos/control_panel/enterprise_memory_cache.py` | `EnterpriseMemoryCache` | present | yes | yes | canonical components | See `Tests/` and `Documentation/OR-*` |  |
| Workflow Delta | `src/argos/control_panel/workflow_delta_engine.py` | `WorkflowDeltaEngine` | present | yes | yes | canonical components | See `Tests/` and `Documentation/OR-*` |  |
| Priority Engine | `src/argos/control_panel/enterprise_priority_engine.py` | `EnterprisePriorityEngine` | present | yes | yes | canonical admission | See `Tests/` and `Documentation/OR-*` |  |
| Communications Bus | `src/argos/control_panel/enterprise_communications_bus.py` | `EnterpriseCommunicationsBus` | present | yes | yes | runtime/dashboard | See `Tests/` and `Documentation/OR-*` |  |
| Paper Broker | `src/argos/trader/paper_brokerage.py` | `DeterministicPaperBrokerage` | present | yes | yes | broker tests/runtime | See `Tests/` and `Documentation/OR-*` |  |
| Trader order management | `src/argos/trader/order_management.py` | `Order Management Office` | present | yes | yes | trader group | See `Tests/` and `Documentation/OR-*` |  |
| Position Registry | `src/argos/control_panel/position_registry.py` | `PositionRegistry` | present | yes | yes | position lifecycle | See `Tests/` and `Documentation/OR-*` |  |
| EO-CK Position Monitoring Network | `src/argos/control_panel/position_monitoring_network.py` | `PositionMonitoringNetwork` | present | yes | yes | runtime/dashboard | See `Tests/` and `Documentation/OR-*` |  |
| Position Surveillance | `src/argos/control_panel/position_surveillance_engine.py` | `PositionSurveillanceEngine` | present | yes | yes | runtime/dashboard | See `Tests/` and `Documentation/OR-*` |  |
| Position Exit Decision Engine | `src/argos/control_panel/position_exit_decision_engine.py` | `PositionExitDecisionEngine` | present | yes | yes | position lifecycle | See `Tests/` and `Documentation/OR-*` |  |
| Closed Position Truth | `src/argos/control_panel/closed_position_truth.py` | `ClosedPositionTruth` | present | yes | yes | position lifecycle | See `Tests/` and `Documentation/OR-*` |  |
| Performance Truth | `src/argos/control_panel/performance_truth_engine.py` | `PerformanceTruthEngine` | present | yes | yes | broker/position lifecycle | See `Tests/` and `Documentation/OR-*` |  |
| Historian | `src/argos/historian/*` | `Historian offices` | present | yes | yes | legacy/runtime surfaces | See `Tests/` and `Documentation/OR-*` |  |
| Commander read models | `src/argos/control_panel/commander_*.py; ui/argos_control_panel/*` | `Commander dashboards` | present | yes | yes | server/dashboard | See `Tests/` and `Documentation/OR-*` | legacy proof surfaces remain |
| Policy Manager | `src/argos/control_panel/enterprise_doctrine_policy_manager.py` | `EnterpriseDoctrinePolicyManager` | present | yes | yes | runtime/dashboard | See `Tests/` and `Documentation/OR-*` |  |
| Doctrine Manager | `src/argos/librarian/doctrine_management.py` | `Doctrine management` | present | yes | yes | librarian/control panel | See `Tests/` and `Documentation/OR-*` |  |
| Persistence | `src/argos/control_panel/enterprise_persistence.py; src/argos/foundation/persistence/*` | `DurableEnterprisePersistenceStore` | present | yes | yes | runtime recovery | See `Tests/` and `Documentation/OR-*` |  |
| Recovery | `src/argos/control_panel/enterprise_failure_recovery.py` | `EnterpriseFailureRecovery` | present | yes | yes | runtime/dashboard | See `Tests/` and `Documentation/OR-*` |  |
| Replay | `src/argos/control_panel/market_replay_engine.py` | `MarketReplayEngine` | present | yes | yes | decision lab/dashboard | See `Tests/` and `Documentation/OR-*` | long-duration replay not certified |
| Enterprise Efficiency Analytics | `src/argos/control_panel/enterprise_efficiency_analytics.py` | `EnterpriseEfficiencyAnalytics` | present | yes | yes | runtime/dashboard | See `Tests/` and `Documentation/OR-*` |  |
| Truth-domain and provenance enforcement | `src/argos/control_panel/truth_domain.py` | `TruthDomain` | present | yes | yes | truth/persistence paths | See `Tests/` and `Documentation/OR-*` | full synthetic truth removal not certified |
