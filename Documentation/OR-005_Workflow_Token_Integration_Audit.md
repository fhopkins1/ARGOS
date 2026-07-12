# OR-005 Workflow Token Integration Audit

## Active Transitions

Part 1 creates workflows through `EnterpriseWorkflowOrchestrator.create_validate_queue_assign()`. The resulting Workflow Execution Token is passed to Scheduler dispatch and Duty Officer requests.

## Rejections

- Live startup: `LIVE_TRADING_DISABLED`.
- Runtime admission before start: `RUNTIME_NOT_STARTED`.
- Seeker without mandate: `MISSING_STRATEGIC_MANDATE`.
- Unreserved API request: `COST_RESERVATION_REQUIRED`.

## Cancellation and Halt

Halt moves Scheduler into `Halted` mode and stops runtime loop ownership. Full cancellation propagation into downstream office work is Part 2.

## Remaining Risk

The legacy dashboard runtime still exposes older workflow controls. OR-005 Part 1 adds the canonical path but does not remove all compatibility paths.
