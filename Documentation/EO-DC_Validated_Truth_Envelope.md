# EO-DC Validated Truth Envelope

EO-DC normalizes Phase III.5 `OperationalTruthEnvelope` into `ValidatedTruthEnvelope`.

The EO-DC envelope adds object type, object ID, evidence quality, intended consumer, mission/workflow/token lineage, token owner placeholder, parent/source references, observation and effective timestamps, freshness, integrity hash, Doctrine and Policy versions, promotion scope, permitted and prohibited consumers, expiration, revocation state, degraded/fallback/synthetic/replay/test/proof/simulation indicators, evaluator version, and promotion state.

Approved envelopes are immutable. Corrections, revocations, and supersessions produce new assurance evidence rather than rewriting prior approvals.

