# OR-006 Persistence Inventory

The executable inventory is exposed by `enterprise_persistence_inventory()`.

| Component | Owner | Category | Object type | Restore order |
| --- | --- | --- | --- | --- |
| Runtime | CanonicalEnterpriseRuntime | C | `enterprise_runtime_state` | 5 |
| Scheduler/Missions | EnterpriseOperationsScheduler | A | `enterprise_mission_state` | 7 |
| Mission Plans | EnterpriseMissionPlanner | A | `enterprise_mission_state` | 8 |
| Workflows/Tokens | EnterpriseWorkflowOrchestrator | A | `enterprise_workflow_state` | 9 |
| Broker Orders/Fills | DeterministicPaperBrokerage | A | `enterprise_broker_state` | 12 |
| Positions | PositionRegistry | A | `enterprise_position_state` | 15 |
| Performance Truth | PerformanceTruthEngine | A | `enterprise_performance_truth` | 17 |
| Policy/Doctrine | EnterpriseDoctrinePolicyManager | A | `enterprise_policy_state` | 3 |
| Checkpoints | CanonicalEnterpriseRuntime | C | `enterprise_runtime_checkpoint` | 22 |

Category A survives restart. Category C checkpoints accelerate recovery but never replace truth.
