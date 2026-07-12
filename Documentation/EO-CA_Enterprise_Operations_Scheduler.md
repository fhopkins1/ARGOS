# EO-CA - Enterprise Operations Scheduler

## Purpose

The Enterprise Operations Scheduler (EOS) is the top-level operational authority for deciding when ARGOS performs bounded work. EOS schedules missions, authorizes office wake requests, enforces operating modes, prevents duplicate work, tracks cost, and returns offices to inactive states after mission completion.

EOS is not an investment-decision office. It does not select securities, approve trades, size positions, alter orders, or override Risk. It only authorizes when mission workers may operate.

## Mission Model

EOS persists append-only mission evidence through canonical `EnterpriseMission` records. Each mission includes type, name, trigger, priority, criticality, required offices, workflow type, execution token reference, runtime ceiling, API cost ceiling, API call ceiling, market-session requirement, concurrency policy, status, result, cost summary, and audit reference.

Supported states are:

`Planned`, `Queued`, `Awaiting Trigger`, `Awaiting Market Session`, `Awaiting Resources`, `Authorized`, `Running`, `Partially Completed`, `Completed`, `Completed With Warnings`, `Suspended`, `Cancelled`, `Failed`, `Aborted`, and `Expired`.

Invalid state transitions are rejected deterministically.

## Activation Model

EOS creates `OfficeActivationRequest` records for each required office in a dispatched mission. Activation requests include mission ID, office ID, reason, assigned task, inputs, expected outputs, priority, activation time, runtime ceiling, API cost ceiling, API call ceiling, requested wake state, completion criteria, cooldown requirement, status, and audit reference.

Commander direct office wake actions are wrapped in a Commander-directed EOS mission so office activation remains attributable.

## Initial Templates

Default paper-trading mission templates include:

- Pre-Market Readiness Mission
- Post-Open Discovery Mission
- Midday Position Review Mission
- Pre-Close Risk Mission
- End-of-Day Reconciliation Mission
- Overnight Strategic Research Mission

Overnight strategic research is disabled by default until budget controls are configured.

## Operating Modes

EOS supports:

- Full Paper Trading
- Observation Only
- Position Management Only
- Capital Preservation
- Strategic Research Only
- Maintenance
- Halted

Position safety and reconciliation missions retain priority over discretionary discovery.

## Market Calendar

EO-CA includes a market-calendar abstraction for U.S. equities with regular, pre-market, after-hours, closed, holiday, and early-close awareness. Cryptocurrency is represented as continuous, but continuous availability does not authorize continuous expensive office activation.

## Budget And Duplicate Safeguards

EOS is disabled by default. It has daily and per-mission API ceilings, prevents duplicate scheduled missions inside exclusion windows, records suppressed work, and marks missions `Awaiting Resources` when budget is unavailable.

## Workflow And API Gateway Integration

Every cognitive or decision-producing mission records a Workflow Execution Token reference. The API Execution Gateway accepts optional EOS context fields: mission ID, office ID, scheduling authorization ID, and remaining mission budget. Routine scheduling uses deterministic local logic and does not invoke AI.

## Control Panel

The Enterprise Operations Bridge appears in the scheduling panel. It displays current operating mode, scheduler status, market session, next mission, active mission count, mission cost monitor, timeline, suppressed work, and Commander controls to enable, disable, set mode, run a mission, and cancel queued work.

## Known Limitations

EOS currently provides deterministic mission scheduling, mission authorization, office activation records, and bridge visibility. Future EOs are expected to deepen event detection, mission planning, cost governance, information freshness, office wakefulness internals, and enterprise efficiency analytics.
