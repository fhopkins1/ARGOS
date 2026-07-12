# OR-005 Scheduler, Mission, and Duty Model

## Scheduled Obligation Lifecycle

`CanonicalEnterpriseRuntime.admit_scheduled_obligation()` creates a scheduler mission from a template, submits the mission data to Mission Planner, requests a Cost Governor reservation, evaluates priority, creates a Workflow Execution Token, dispatches the mission, and submits duty officer tasking requests.

## Deduplication

Scheduler template idempotency remains the first deduplication boundary. Mission Planner suppresses duplicate triggers. Duty Officer suppresses duplicate tasking keys.

## Wake and Sleep

Offices begin asleep. Duty Officer can recommend wake only with mission ID and execution token context. Scheduler activation records are the authority for work admission.

## Cost, Freshness, and Priority

Cost Governor reservation is required before external API work. Freshness, cache, delta, and priority snapshots are connected into the admission evaluation. Part 2 must deepen policy/doctrine and downstream office enforcement.
