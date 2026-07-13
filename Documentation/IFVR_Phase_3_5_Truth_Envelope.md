# IFVR Phase III.5 Truth Envelope

## Purpose

Phase III.5 establishes `OperationalTruthEnvelope` as the required provenance contract for authoritative PAPER operational writes.

## Canonical Fields

- `truth_domain`: must be `PAPER`.
- `provenance_status`: must be `VALIDATED`.
- `truth_classification`: must be `PAPER_OPERATIONAL`.
- `certification_status`: must be `PAPER_OPERATIONAL_CERTIFIED`.
- `originating_authority`: must be an authorized operational authority.
- `originating_workflow_id`, `workflow_token_id`, `mission_id`, `source_event_id`: must be present.
- `schema_version`, `validation_result`, `idempotency_key`, `timestamp_utc`, `caller`: must be present.
- `degraded`: must be false.

## Enforcement

The canonical implementation is `src/argos/control_panel/truth_domain.py`.

Authoritative write boundaries call `require_operational_truth_envelope(...)`, which rejects missing, proof, simulation, live, degraded, uncertified, unvalidated, or wrong-authority envelopes with deterministic codes.

