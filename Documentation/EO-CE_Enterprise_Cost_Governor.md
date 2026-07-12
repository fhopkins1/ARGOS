# EO-CE - Enterprise Cost Governor

EO-CE adds the Enterprise Cost Governor, the authoritative computational-capital control layer for ARGOS.

## Core Boundary

Cost authority is separate from mission authority.

EO-CD proposes resource envelopes. EO-CA authorizes missions. EO-CE authorizes bounded expenditure inside approved policy. EO-CE does not create missions, wake offices, start workflows, submit broker orders, make investment decisions, or alter risk policy.

## Implemented Components

- `src/argos/control_panel/enterprise_cost_governor.py`
  - `EnterpriseCostGovernor`
  - `EnterpriseBudgetPolicy`
  - `BudgetAccount`
  - `CostReservationRequest`
  - `CostReservation`
  - `CostAuthorizationRequest`
  - `CostAuthorizationRecord`
  - `CostUsageRecord`
  - `CostLedgerEntry`
  - `CircuitBreakerRecord`
  - `CostOverrideRecord`

## Capabilities

- Versioned budget policy.
- Daily, category, and protected reserve budget accounts.
- Mission-plan reservation requests from EO-CD envelopes.
- Reservation approval, reduction, deferment, rejection, local-only, and safety-reserve decisions.
- Gateway per-call authorization.
- Usage accounting and idempotent duplicate protection.
- Settlement and release of unused funds.
- Distinct estimated, reserved, incurred, settled, and released values.
- Provider/model restrictions.
- API-call and token ceiling enforcement.
- Circuit-breaker and alert records.
- Forecast panel for day/week/month capacity.
- Restart recovery from snapshots.

## API Gateway Integration

`ApiExecutionGateway` accepts optional EO-CE hooks:

- `authorize_cost`
- `record_cost_usage`

Gateway requests with a `cost_reservation_id` must pass EO-CE authorization before execution can continue. `real_api_pilot` Gateway calls without an attached reservation receive a bounded Gateway reservation before authorization, so pilot model usage remains attributed, capped, and recorded. Existing LAW VII workflow-token and legacy credit-governor checks still run after EO-CE permits the cost side.

## Runtime and API

Runtime state exposes `enterpriseCostGovernor`.

POST routes:

- `/api/cost-governor/reserve`
- `/api/cost-governor/release`
- `/api/cost-governor/settle`
- `/api/cost-governor/policy`

## Control Panel Bridge

The Enterprise Cost Governance Bridge displays:

- budget allocation
- protected reserves
- mission reservations
- office cost table
- provider/model usage
- authorization stream
- forecast

## Known Limitations

- Persistence is runtime snapshot/in-memory until a durable repository is added.
- Provider pricing is intentionally conservative and versioned but not live-provider sourced.
- Dry-run Gateway display calls remain local/non-metered. Paid or metered `real_api_pilot` calls are reservation-governed before execution and usage-recorded after completion.
