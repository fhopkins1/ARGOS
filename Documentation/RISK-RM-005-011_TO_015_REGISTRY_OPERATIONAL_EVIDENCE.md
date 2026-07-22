# RISK-RM-005-011 to RISK-RM-005-015 Registry Operational Evidence

## Scope

This evidence note covers the candidate-bound operational implementation for:

- RISK-RM-005-011 Constitutional Metrics Operationalization
- RISK-RM-005-012 Version Compatibility Matrix Population
- RISK-RM-005-013 Registry Cross-Reference Graph Materialization
- RISK-RM-005-014 Certification Evidence Registry Population
- RISK-RM-005-015 Candidate Certification Manifest Generation

## Implementation

The implementation is provided by `src/argos/risk/rm005_registry_operational.py`.

It consumes the candidate-bound RM005 execution package from `RiskRm005ExecutionOperationalSupport` and derives:

- calculated constitutional metrics from execution evidence;
- explicit version compatibility records for every discovered candidate artifact;
- a registry cross-reference graph linking candidates, artifacts, schemas, rules, tests, metrics, compatibility records, and evidence records;
- a populated certification evidence registry;
- a single candidate-bound certification manifest.

No metric, compatibility result, evidence record, graph edge, or manifest count is manually entered as a certification outcome. Records are deterministically derived from candidate artifacts and the RM005 execution package.

## Verification

Focused verification is provided by `Tests/test_risk_rm005_registry_operational.py`.

The test suite verifies:

- complete order coverage for RISK-RM-005-011 through RISK-RM-005-015;
- manifest binding to the exact candidate digest;
- metric, compatibility, graph, evidence, and manifest population from real artifacts;
- deterministic temporary-candidate behavior;
- fail-closed metric behavior when required evidence is missing;
- fail-closed compatibility behavior when explicit compatibility is unavailable;
- fail-closed manifest behavior on artifact inventory mismatch.

## Certification Boundary

This implementation does not declare independent constitutional certification. It produces candidate-bound operational evidence for review by the enterprise certification authority.
