# RISK-RM-006-001 to RISK-RM-006-005 Independent Certification Evidence

## Scope

This evidence note covers the independent certification and closure implementation for:

- RISK-RM-006-001 Immutable Candidate Acceptance
- RISK-RM-006-002 Independent Certification Execution
- RISK-RM-006-003 Independent Finding Adjudication
- RISK-RM-006-004 Constitutional Certification Determination
- RISK-RM-006-005 Constitutional Closure

## Implementation

The implementation is provided by `src/argos/risk/rm006_independent_certification.py`.

It consumes the RISK-RM-005A operational completion package and deterministically produces:

- an immutable candidate acceptance record issued by the Independent Risk Office Certification Authority;
- an independent certification execution record;
- independent finding adjudication records;
- exactly one final independent certification determination;
- a constitutional closure record that seals the candidate only when all closure preconditions pass.

This layer is intentionally separate from RM005A operational readiness. RM005A may recommend readiness, but RM006 is the first layer that may issue the independent certification determination and closure record.

## Verification

Focused verification is provided by `Tests/test_risk_rm006_independent_certification.py`.

The test suite verifies:

- complete order coverage for RISK-RM-006-001 through RISK-RM-006-005;
- successful immutable candidate acceptance for the committed repository candidate;
- rejection of unreproducible unversioned candidates;
- fail-closed forced candidate rejection;
- independent execution findings adjudicated as blocking;
- determination failure when blocking findings exist;
- closure failure when certification preconditions do not pass.

## Certification Boundary

The independent certification support issues deterministic certification records for the evaluated candidate. Future changes to candidate artifacts, doctrine, schemas, registries, rules, or evidence require a fresh candidate-bound certification run.
