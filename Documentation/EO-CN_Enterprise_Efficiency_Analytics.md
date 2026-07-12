# EO-CN - Enterprise Efficiency Analytics

EO-CN adds deterministic enterprise efficiency analytics for ARGOS.

The subsystem measures time, cost, utilization, workflow throughput, mission throughput, cache reuse, workflow delta use, monitoring coverage, communications reliability, recovery burden, and Commander attention. It reports findings and lineage; it does not optimize or command the enterprise.

## Responsibilities

- Maintain typed, versioned efficiency metric definitions.
- Calculate immutable metric values with source lineage and data quality.
- Build enterprise efficiency snapshots and balanced scorecards.
- Generate advisory findings that distinguish observation from causal claims.
- Support deterministic recalculation, period comparison, finding acknowledgement, and metric-lineage inspection.
- Preserve paper/live mode in metric records.

## Runtime Integration

The runtime exposes EO-CN under `enterpriseEfficiencyAnalytics`.

API routes:

- `GET /api/efficiency-analytics/state`
- `POST /api/efficiency-analytics/refresh`
- `POST /api/efficiency-analytics/acknowledge`
- `POST /api/efficiency-analytics/recalculate`
- `POST /api/efficiency-analytics/lineage`
- `POST /api/efficiency-analytics/compare`

Dashboard refresh calculates a read-only preview. Explicit refresh persists a snapshot in the EO-CN analytics history.

## Source Systems

EO-CN consumes existing runtime snapshots from:

- EO-CA / EO-CB scheduler and duty officer state
- workflow orchestrator and workflow runtime monitor
- API runtime and execution gateway
- EO-CE cost governor
- EO-CF freshness
- EO-CG memory cache
- EO-CH workflow delta
- EO-CJ priority
- EO-CK position monitoring
- EO-CL communications bus
- failure recovery framework
- CNAC and Commander daily review
- performance truth

## Commander Bridge

The control panel displays:

- enterprise scorecard
- office efficiency
- mission efficiency
- workflow efficiency
- cost efficiency
- reuse and delta
- communications efficiency
- recovery efficiency
- findings console
- metric lineage
- LAW VII / authority boundaries

## Safety Boundaries

EO-CN does not:

- authorize missions
- alter enterprise priority
- approve cost
- change budgets
- wake offices
- transfer Workflow Execution Tokens
- mutate operational truth
- mutate ledgers
- change recovery policy
- invoke AI for routine analytics

Findings are advisory review signals only.
