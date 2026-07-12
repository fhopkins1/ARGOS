# OR-006 State Ownership Model

## Canonical Owners

- Scheduler owns scheduled missions and dispatch state.
- Mission Planner owns mission plans.
- Workflow Orchestrator owns workflows and Workflow Execution Tokens.
- Paper Broker owns broker order and fill evidence.
- Position Registry owns enterprise position state.
- Performance Truth owns immutable truth ledgers.
- Doctrine/Policy Manager owns policy and doctrine state.
- Runtime owns only mode, admissions, failures, and checkpointable continuity state.

## Rule

No recovered dashboard or checkpoint value may overwrite an authoritative owner. Commander surfaces rebuild from persisted truth.
