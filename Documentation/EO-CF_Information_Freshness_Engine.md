# EO-CF - Information Freshness Engine

EO-CF adds the Information Freshness Engine, the authoritative deterministic service that decides whether registered information is current enough for a specific decision context.

## Boundary

EO-CF evaluates metadata, provenance, age, dependency state, supersession, contradiction, and requested use. It does not retrieve data, call AI, wake offices, create missions, authorize expenditure, mutate positions, or submit broker orders.

## Implemented Components

- `src/argos/control_panel/information_freshness_engine.py`
  - `InformationFreshnessEngine`
  - `InformationRecord`
  - `FreshnessPolicy`
  - `FreshnessEvaluationContext`
  - `DependencyLink`
  - `FreshnessDecision`
  - `InvalidationRecord`
  - `ContradictionRecord`

## Capabilities

- Versioned freshness policies.
- Contextual decisions by decision-use class.
- Market/open-position/active-order age overrides.
- Source authority, confidence, and provenance validation.
- Dependency graph registration with cycle detection.
- Partial and full invalidation.
- Supersession preservation.
- Contradiction preservation and resolution records.
- Field and section freshness scopes.
- Reuse, validation, partial-refresh, full-refresh, and block recommendations.
- Restart recovery from snapshots.
- EO-CB, EO-CD, EO-CE, EO-CG, and EO-CH integration feeds.

## Runtime and API

Runtime state exposes `informationFreshnessEngine`.

Routes:

- `GET /api/information-freshness/state`
- `POST /api/information-freshness/register`
- `POST /api/information-freshness/evaluate`
- `POST /api/information-freshness/invalidate`
- `POST /api/information-freshness/supersede`
- `POST /api/information-freshness/contradiction`
- `POST /api/information-freshness/policy`

## Control Panel Bridge

The Information Freshness Bridge displays:

- header freshness indicators
- registered inventory
- stale and at-risk records
- dependency map
- supersession and contradiction records
- policy explorer
- reuse and refresh recommendations
- reevaluation queue

## Known Limitations

- Persistence is runtime snapshot/in-memory until a durable repository is added.
- Market-calendar behavior is policy-driven with current market-state inputs; a full external holiday calendar is not queried.
- EO-CG and EO-CH are represented as stable interfaces until those EOs are implemented.
