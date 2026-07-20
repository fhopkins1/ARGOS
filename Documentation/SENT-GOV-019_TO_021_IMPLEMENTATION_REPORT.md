# SENT-GOV-019 to SENT-GOV-021 Implementation Report

## Scope

This implementation adds Sentinel governance controls for bridge classification and certification, truth provenance/domain enforcement, and independent certification verdict evaluation.

## Implemented Controls

- Immutable canonical bridge registry with deterministic content hashing and discovered-call-path comparison.
- Bridge invocation evaluator enforcing registered bridge identity, source and destination authority, operating-mode eligibility, certification state, workflow-token continuity, duplicate prevention, idempotency evidence, and rejection evidence.
- Bridge certification evaluator requiring conjunctive mandatory dimensions, negative testing, restart testing, recovery testing, and self-attestation rejection.
- Truth governance evaluator enforcing approved source provenance, truth classification, truth-domain isolation, synthetic-promotion prohibition, lineage requirements, freshness, conflict handling, recovery limits, corruption quarantine, and eligibility boundaries.
- Independent certification verdict evaluator with PASS, FAIL, INDETERMINATE, and INVALID_AUDIT outcomes based on candidate identity, repository integrity, evidence completeness, deterministic rerun, scope, and audit independence.

## Verification

- `python -m unittest Tests.test_sent_mo001_to_005_sentinel_observation Tests.test_sent_mo_runtime_certification_revision Tests.test_sent_gov019_to_021_governance`
- `python -m compileall src\argos\sentinel Tests\test_sent_gov019_to_021_governance.py`

## Constitutional Result

Codex produces implementation controls and candidate evidence only. Final constitutional certification remains reserved for independent audit under SENT-GOV-021.
