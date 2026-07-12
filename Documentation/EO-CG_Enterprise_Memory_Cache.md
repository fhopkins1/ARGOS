# EO-CG - Enterprise Memory Cache

EO-CG adds the Enterprise Memory Cache, the governed repository for reusable, validated, attributable ARGOS work.

## Boundary

The cache stores and retrieves prior enterprise products. It does not create truth, declare freshness, wake offices, create missions, call AI, retrieve paid data, or authorize expenditure. EO-CF remains the freshness authority for reuse.

## Implemented Components

- `src/argos/control_panel/enterprise_memory_cache.py`
  - `EnterpriseMemoryCache`
  - `CacheProductRecord`
  - `CacheAdmissionRequest`
  - `CacheAdmissionDecision`
  - `CacheQuery`
  - `CacheMatch`
  - `CacheReuseEvaluation`
  - `CacheRetrievalResult`
  - `CacheInvalidationRecord`
  - `CacheAccessRecord`

## Capabilities

- Controlled admission to validated, candidate, historical, reference, archived, or quarantined tiers.
- Deterministic product keys and product-version indexing.
- Duplicate detection by content hash and product reference.
- Immutable validated records with superseding versions instead of silent mutation.
- Deterministic retrieval by subject, product type, product key, lineage, schema, fields, and sections.
- Structured non-AI similarity scoring.
- EO-CF-backed freshness and decision-use reuse evaluation.
- Environment isolation for live, paper, simulation, replay, test, and development records.
- Partial scope reuse and rejected reuse records.
- Invalidation and access audit records.
- Contradiction registration that blocks silent reuse.
- Quarantine for suspicious authority claims and unsafe operational reuse.
- Retention and archival controls that preserve history without automatic deletion.
- Repository method manifest for deterministic lookup and audit inspection.
- Restart recovery from snapshot.
- EO-CH feed for future workflow delta planning.

## Runtime and API

Runtime state exposes `enterpriseMemoryCache`.

Routes:

- `GET /api/enterprise-memory/state`
- `POST /api/enterprise-memory/admit`
- `POST /api/enterprise-memory/query`
- `POST /api/enterprise-memory/invalidate`
- `POST /api/enterprise-memory/supersede`

## Control Panel Bridge

The Enterprise Memory Bridge displays:

- cache inventory
- admission decisions
- retrieval results
- reuse evaluations
- invalidation and access audit
- contradiction, quarantine, and archival records
- indexes
- retention policy and repository-method evidence
- EO-CH delta feed

## Known Limitations

- Persistence is runtime snapshot/in-memory until a durable repository is added.
- Similarity retrieval is deterministic structured matching only; model-assisted semantic retrieval is intentionally absent.
- EO-CH integration is provided as a stable feed until the Workflow Delta Engine is implemented.
- External durable payload storage, PDF export, and model-assisted semantic retrieval are intentionally not added in EO-CG.
