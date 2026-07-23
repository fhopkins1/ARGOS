# AUTH-RM-001-001 to AUTH-RM-001-008 Compliance Evidence

## Scope

This evidence note covers the revised Authorizations Office compliance work orders:

- AUTH-RM-001-001 Immutable Candidate Compliance
- AUTH-RM-001-002 Canonical Implementation Reconciliation
- AUTH-RM-001-003 Constitutional Requirement Materialization
- AUTH-RM-001-004 Operational Office Completion
- AUTH-RM-001-005 Certification Test Completion
- AUTH-RM-001-006 Operational Evidence Completion
- AUTH-RM-001-007 Persistence, Replay, and Recovery Verification
- AUTH-RM-001-008 Certification Infrastructure Completion

## Implementation

The executable implementation is in `src/argos/control_panel/authorization_authority.py`.

The revised compliance layer is provided by `AuthorizationsOfficeComplianceSupport`. It consumes the existing candidate-bound `AuthorizationRemediationPackage` and produces an `AuthorizationCompliancePackage` containing:

- immutable candidate compliance evidence;
- canonical Authorizations implementation inventory;
- eight operational constitutional requirement records;
- eight executable certification test specifications;
- eight deterministic certification test execution records;
- candidate-bound operational evidence;
- persistence, replay, recovery, interruption-boundary, and idempotency verification;
- executable certification infrastructure manifest and package digests;
- final fail-closed compliance status.

## Verification

The focused executable tests are in `Tests/test_authorization_authority_compliance.py`.

They verify:

- revised order coverage for AUTH-RM-001-001 through AUTH-RM-001-008;
- candidate identity binding and evidence alignment;
- executable certification test materialization and execution;
- certification infrastructure assembly;
- fail-closed behavior when the canonical implementation artifact is absent;
- deterministic replay, recovery, interruption-boundary, and idempotency verification.

The existing Authorizations tests in `Tests/test_authorization_authority.py` continue to verify the broader AUTH-RM-001-001 through AUTH-RM-001-013 remediation support.

## Audit Boundary

The compliance package records the mutable worktree state separately from immutable candidate identity. Candidate evidence is bound to the Git commit tree and Authorizations canonical artifacts, while local unrelated evidence-package changes remain visible through normal Git status and are not used as substitutes for candidate artifacts.
