# EO-CJ Enterprise Priority Engine

EO-CJ adds the Enterprise Priority Engine, the deterministic authority for ranking competing missions, events, office demands, recovery actions, and scarce-resource requests.

The engine is advisory. It does not authorize missions, wake offices, transfer Workflow Execution Tokens, reserve budget, submit broker orders, mutate positions, or alter ledgers. EO-CA remains the Scheduler authority.

## Priority Doctrine

Default protected doctrine:

1. Emergency recovery
2. Position safety
3. Broker and ledger integrity
4. Risk control
5. Required lifecycle action
6. Commander-directed missions
7. Tactical evaluation
8. Strategic intelligence
9. Historical review
10. Capability development

Safety precedence is enforced before numeric score arithmetic. Aging and starvation prevention can help lower-priority work advance only when doing so does not outrank protected safety work.

## Runtime API

- `GET /api/enterprise-priority/state`
- `POST /api/enterprise-priority/evaluate`
- `POST /api/enterprise-priority/replay`
- `POST /api/enterprise-priority/recover`
- `POST /api/enterprise-priority/modifier`

## Bridge Panels

The Enterprise Priority Bridge shows:

- summary posture
- ranked mission queue
- score breakdown
- safety precedence
- priority inheritance
- preemption assessments
- starvation and aging
- resource constraints
- suspended/deferred work
- EO-CA scheduler feed

## Integration

EO-CJ consumes existing records from:

- EO-CA Enterprise Operations Scheduler
- EO-CD Enterprise Mission Planner
- EO-CE Enterprise Cost Governor
- EO-CC Event Detection Engine
- EO-CF Information Freshness Engine
- EO-CG Enterprise Memory Cache
- EO-CH Workflow Delta Engine
- Workflow Runtime Monitor

## Safety Boundaries

The UI cannot directly set numeric priority or start work. Commander modifier records are bounded audit inputs; they do not bypass safety precedence or Scheduler authority.
