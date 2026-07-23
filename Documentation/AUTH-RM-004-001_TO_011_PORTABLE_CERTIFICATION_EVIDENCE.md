# AUTH-RM-004-001 to AUTH-RM-004-011 Portable Certification Evidence

## Scope

This evidence note covers the AUTH-RM-004 Authorizations Office portable independent certification package:

- AUTH-RM-004-001 Portable Immutable Candidate Constitution
- AUTH-RM-004-002 Independent Candidate Integrity and Cleanliness Enforcement
- AUTH-RM-004-003 Repository-Wide Constitutional Closure Discovery
- AUTH-RM-004-004 Bidirectional Constitutional Traceability and Orphan Elimination
- AUTH-RM-004-005 Independent Constitutional Rule Execution Engine
- AUTH-RM-004-006 Authentic Persistence and Durable State Verification
- AUTH-RM-004-007 Authentic Replay, Interruption, and Recovery Verification
- AUTH-RM-004-008 Clean-Room Certification Reproduction System
- AUTH-RM-004-009 Portable Manifest and Evidence Integrity Verification
- AUTH-RM-004-010 Certification Environment and Dependency Lock
- AUTH-RM-004-011 Independent Evidence Generation and Evidence Provenance

## Implementation

The executable implementation is in `src/argos/control_panel/authorization_portable_certification.py`.

`AuthorizationsOfficePortableCertificationSupport` consumes the AUTH-RM-003 independent certification package and produces an `AuthorizationPortableCertificationPackage` containing:

- canonical candidate and evidence manifests using portable relative paths and SHA-256 digests;
- independent candidate integrity and manifest reconciliation results;
- repository-wide constitutional closure discovery;
- bidirectional traceability from authority through requirement, implementation, evidence, and verdict;
- independent portable rule execution records;
- durable persistence evidence crossing a fresh operating-system process boundary;
- replay, interruption, checkpoint, and recovery evidence;
- clean-room reproduction records for isolated executions;
- certification environment and dependency lock evidence;
- current-execution evidence provenance records.

## Verification

The focused executable tests are in `Tests/test_authorization_portable_certification.py`.

They verify:

- complete AUTH-RM-004-001 through AUTH-RM-004-011 order coverage;
- canonical portable manifest ordering and path integrity;
- independent rule execution for every traceability record;
- authentic durable persistence through fresh-process readback;
- replay and recovery verification;
- isolated clean-room reproduction;
- complete current-execution evidence provenance.

## Certification Boundary

AUTH-RM-004 makes the Authorizations certification package portable and independently reproducible. It does not redefine Authorizations Office doctrine, authorization semantics, office ownership, bridge behavior, or enterprise workflow behavior.
