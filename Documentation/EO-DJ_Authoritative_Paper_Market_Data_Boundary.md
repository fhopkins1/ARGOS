# EO-DJ Authoritative Paper Market Data Boundary

EO-DJ closes the production-reachable mock market-data path. Canonical paper and live decision workflows must use `MarketDataGateway` with an explicitly authorized provider. Missing provider configuration fails closed; no mock, fixture, replay, development simulation, previous price, hard-coded price, or generated value is selected as fallback.

Proof domains are `PAPER_AUTHORITATIVE`, `LIVE_AUTHORITATIVE`, `REPLAY`, `TEST`, and `DEVELOPMENT_SIMULATION`. `REPLAY`, `TEST`, and `DEVELOPMENT_SIMULATION` providers are non-production by policy and cannot be registered for paper or live authority.

Every accepted observation is a `MarketDataObservation` with provider identity, provider classification, proof domain, instrument identity, observation type, normalized payload, source timestamp, ingestion timestamp, freshness policy evidence, evidence status, request/correlation identifiers, persistence identity, schema version, and deterministic hash.

Freshness is evaluated by policy. `FRESH` observations can support current decisions. `STALE` and `EXPIRED` observations may remain historical evidence but are rejected where current evidence is required. `UNKNOWN` timestamps fail closed.

Raw observations and derived facts are distinct. Derived facts must retain source observation IDs or an immutable input manifest and must not be labeled as raw external observations.

Recovery never reconstructs missing observations. Restored workflows must reload observations by immutable ID, verify hashes, preserve original timestamps and proof domain, and block dependent financial workflows when evidence is absent.

EO-DJ evidence is generated under `Documentation/EO-DJ_Evidence/`:

- `eo_dj_market_source_inventory.json`
- `eo_dj_provider_authority_registry.json`
- `eo_dj_production_reachability.json`
- `eo_dj_market_observation_trace.json`
- `eo_dj_prohibited_source_rejections.json`
- `eo_dj_recovery_missing_evidence_trace.json`
- `eo_dj_test_results.json`
- `eo_dj_certification.json`

Operational limitation: no real external authoritative paper provider is configured by this EO. Boundary readiness is not provider-service readiness. ARGOS remains not certified for continuous authoritative paper trading until an external provider is configured, health-checked, persisted, and separately certified.
