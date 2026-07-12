# OR-005 Series C Component Inventory

## Canonical Mapping

| EO | Capability | Canonical implementation | Runtime attribute | Status | OR-005 action |
| --- | --- | --- | --- | --- | --- |
| EO-CA | Enterprise Operations Scheduler | `src/argos/control_panel/scheduler.py::EnterpriseOperationsScheduler` | `scheduler` | Active canonical Part 1 | Retain/connect |
| EO-CB | Office Duty Officer | `src/argos/control_panel/office_duty_officer.py::OfficeDutyOfficerRegistry` | `duty_officers` | Active canonical Part 1 | Retain/connect |
| EO-CC | Event Detection Engine | `src/argos/control_panel/event_detection_engine.py::EventDetectionEngine` | `event_detection` | Active canonical Part 1 | Retain/connect |
| EO-CD | Enterprise Mission Planner | `src/argos/control_panel/mission_planner.py::EnterpriseMissionPlanner` | `mission_planner` | Active canonical Part 1 | Retain/connect |
| EO-CE | Enterprise Cost Governor | `src/argos/control_panel/enterprise_cost_governor.py::EnterpriseCostGovernor` | `cost_governor` | Active canonical Part 1 | Retain/connect |
| EO-CF | Information Freshness Engine | `src/argos/control_panel/information_freshness_engine.py::InformationFreshnessEngine` | `freshness_engine` | Active canonical Part 1 | Retain/connect |
| EO-CG | Enterprise Memory Cache | `src/argos/control_panel/enterprise_memory_cache.py::EnterpriseMemoryCache` | `memory_cache` | Active canonical Part 1 | Retain/connect |
| EO-CH | Workflow Delta Engine | `src/argos/control_panel/workflow_delta_engine.py::WorkflowDeltaEngine` | `workflow_delta` | Active canonical Part 1 | Retain/connect |
| EO-CI | Office Wakefulness Manager | Found under `OfficeDutyOfficerRegistry` and `EnterpriseOperationsScheduler` office state | `duty_officers` / `scheduler` | Found under existing authorities | Alias/document; do not duplicate |
| EO-CJ | Enterprise Priority Engine | `src/argos/control_panel/enterprise_priority_engine.py::EnterprisePriorityEngine` | `priority_engine` | Active canonical Part 1 | Retain/connect |
| EO-CK | Position Monitoring Network | `src/argos/control_panel/position_monitoring_network.py::PositionMonitoringNetwork` | `position_monitoring` | Active canonical Part 1 | Retain/connect |
| EO-CL | Enterprise Communications Bus | `src/argos/control_panel/enterprise_communications_bus.py::EnterpriseCommunicationsBus` | `communications_bus` | Active canonical Part 1 | Retain/connect |
| EO-CM | Commander Mission Generator | No separate canonical implementation found | commander directive path via Mission Planner/Scheduler | Documented Part 2 gap | Resolve in Part 2 |
| EO-CN | Enterprise Efficiency Analytics | `src/argos/control_panel/enterprise_efficiency_analytics.py::EnterpriseEfficiencyAnalytics` | `efficiency_analytics` | Active canonical Part 1 | Retain/connect |
| EO-CO | Doctrine and Policy Manager | `src/argos/control_panel/enterprise_doctrine_policy_manager.py::EnterpriseDoctrinePolicyManager` | `doctrine_policy` | Active canonical Part 1 | Retain/connect |

## Executable Inventory

`CanonicalEnterpriseRuntime.series_c_inventory()` returns this mapping as executable metadata. The inventory is tested in `Tests/test_or005_canonical_runtime.py`.

## Key Findings

- EO-CI is not missing functionally; office wakefulness is split across the Duty Officer and Scheduler office-state model. Creating a new EO-CI module would duplicate authority.
- EO-CM remains uncertain. Commander-directed missions currently flow through Mission Planner and Scheduler, but a separately named Commander Mission Generator was not found.
- EO-CO exists as doctrine/policy implementation and is now included in the OR-005 inventory.
