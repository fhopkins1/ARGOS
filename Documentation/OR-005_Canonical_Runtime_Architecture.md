# OR-005 Canonical Runtime Architecture

## Composition Root

`src/argos/control_panel/canonical_enterprise_runtime.py::CanonicalEnterpriseRuntime` is the Part 1 canonical composition root. It constructs one explicit component graph and exposes startup, halt, admission, API gate, strategic mandate, and read-only observation methods.

## Active Path

The implemented Part 1 admission path is:

Enterprise Operations Scheduler -> Mission Planner -> Cost Governor -> Priority Engine -> Workflow Orchestrator and Workflow Execution Token -> Scheduler dispatch -> Duty Officer decisions.

Downstream trading remains broker-authoritative through OR-003, and position state remains OR-004 position-authoritative. Part 1 does not execute the full Seeker-to-Trader chain.

## Runtime Modes

The runtime distinguishes stopped, initializing, recovering, ready, paper idle, paper active, paper degraded, halting, halted, faulted, proof, simulation, and live disabled. Live startup fails closed.

## Startup

Startup validates critical dependencies, duplicate stateful authority identities, and live-disabled configuration. Valid paper startup enters `paper_idle`; it does not create missions, workflows, orders, fills, positions, or profits.

## Halt

Halt sets Scheduler to `Halted`, stops the runtime loop flag, and enters `halted`.

## Degraded Rules

Missing critical authorities fail closed. Noncritical downstream activation remains Part 2 work and is not silently substituted.
