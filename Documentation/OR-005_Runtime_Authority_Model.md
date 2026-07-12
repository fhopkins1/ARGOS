# OR-005 Runtime Authority Model

## Runtime

Runtime may construct systems, validate dependencies, start and halt the loop, coordinate admission, assemble read-only status, and fail closed. It may not create financial decisions, broker fills, profits, losses, or positions.

## Scheduler

Scheduler owns obligation eligibility, mission records, mission authorization, dispatch, and activation records. It does not select assets or approve trades.

## Mission Planner

Mission Planner converts qualified triggers into bounded mission plans. It does not perform office analysis or broker execution.

## Duty Officer

Duty Officer evaluates whether offices should wake, route, queue, defer, reject, or answer from cache. It does not perform office work.

## Workflow Orchestrator

Workflow Orchestrator owns workflow lifecycle and Workflow Execution Token ownership. Runtime cannot impersonate an office.

## Broker, Position, and Truth

Broker fills remain owned by OR-003 `DeterministicPaperBrokerage`. Position state remains owned by OR-004 registry/lifecycle interfaces. Performance Truth records authoritative outcomes but does not create outcomes.

## Commander

Commander surfaces direct and observe. Dashboard/read-only paths must not mutate authoritative runtime state.
