# EO-CB - Office Duty Officer

## Purpose

The Office Duty Officer (ODO) framework gives each major ARGOS office a lightweight deterministic sentry. The Duty Officer remains available while the parent office sleeps and decides whether incoming tasking should be rejected, queued, routed, answered from cache, escalated, or recommended for scheduler-authorized office wake.

The Duty Officer is not the parent office. It does not generate theses, approve trades, place orders, override Risk, or perform full analysis.

## Request Lifecycle

Incoming tasking becomes an `OfficeTaskingRequest`. The ODO validates mission authorization, Workflow Execution Token context, operating mode, office relevance, freshness, duplicate status, cost, budget, cooldown, and cache reuse before it can recommend full office activation.

Every evaluation emits a `DutyOfficerDecision` with disposition, reason code, explanation, rules evaluated, mission state, budget state, freshness state, routing or cache references, wake recommendation, activation cost estimate, value estimate, wake score, confidence, and audit record.

## Dispositions

Supported dispositions include reject, return for correction, queue, defer, route, answer from cache, resolve locally, escalate, recommend wake, emergency wake request, duplicate suppressed, expired, and prohibitions by mode, budget, cooldown, or market session.

## Capability Profiles

Initial profiles exist for:

- Executive
- Seeker
- Analyst
- Strategic Intelligence
- Risk
- Trader
- Historian
- Librarian
- Academy

Profiles define supported request types, operating-mode permissions, queue limits, cooldown, expected activation cost, cache reuse policy, duplicate window, routing destinations, and escalation destinations.

## Scheduler Integration

ODO does not self-authorize a full office wake. It submits wake recommendations and emergency wake requests to EOS visibility. Full activation remains under the Enterprise Operations Scheduler and Workflow Execution Token discipline.

## Cache And Freshness

EO-CB uses a timestamp-based fallback cache until the future Information Freshness Engine and Enterprise Memory Cache exist. Fresh approved products can answer requests without waking a parent office. Unknown freshness is explicit and conservative.

## Dashboard

The Enterprise Operations Bridge displays the Duty Officer roster, pending requests, wake recommendations, suppressed work, and audit detail. Commander tasking can be submitted through `/api/odo/task`.

## Safeguards

Routine ODO triage is deterministic and uses no external AI. ODO API Gateway requests now have fields for duty officer ID, parent office ID, mission ID, office ID, scheduling authorization, and remaining mission budget for future enforcement.

## Known Limitations

EO-CB implements the framework and deterministic fallback behavior. Future EOs will deepen event detection, freshness, memory cache, workflow delta logic, and full wakefulness-state management.
