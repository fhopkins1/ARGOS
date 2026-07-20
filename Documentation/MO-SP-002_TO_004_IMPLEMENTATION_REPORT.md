# MO-SP-002 Through MO-SP-004 Implementation Report

## Summary

MO-SP-002 and MO-SP-003 were delivered as constitutional doctrine documents because both orders explicitly prohibit code implementation. MO-SP-004 was implemented as a deterministic Seeker evidence acquisition engine.

## Deliverables

- `Documentation/MO-SP-002_Intelligence_Collection_Retrieval_Doctrine.md`
- `Documentation/MO-SP-003_Sentinel_Search_Monitoring_Doctrine.md`
- `src/argos/seeker/evidence_acquisition.py`
- `Tests/test_mosp004_seeker_evidence_acquisition.py`

## MO-SP-004 Constitutional Objects

Implemented:

- `SeekerInvestigationRequest`
- `InvestigationAuthorization`
- `InvestigationClass`
- `InvestigationSearchPlan`
- `SearchStep`
- `SearchQuery`
- `EntityResolution`
- `EvidenceDocument`
- `MissingEvidenceRecord`
- `SourceProvenance`
- `BudgetState`
- `EvidencePackage`
- `SeekerEvidenceAcquisitionEngine`

The engine uses `SourceAuthorizationGateway` from MO-SP-001 before retrieval. It preserves collected, missing, unavailable, negative, and contrary evidence. It terminates deterministically on budget exhaustion, authority rejection, required-source unavailability, or completion.

## Source Registry Update

MO-SP-004 requires Seeker acquisition for broker discrepancy and portfolio discrepancy investigations. The MO-SP-001 broker source was updated to authorize `Seeker` for broker/account reconciliation evidence acquisition while preserving paper-only environment restrictions.

## Synthetic-Truth Controls

The Seeker engine does not interpret evidence, rank truth, reconcile conflicts, score sources, recommend trades, infer missing facts, fabricate documents, or silently skip mandatory searches.

Missing evidence remains one of:

- `UNKNOWN`
- `UNAVAILABLE`
- `NOT_FOUND`
- `NOT_APPLICABLE`
- `SOURCE_DOWN`
- `TIMEOUT`
- `AUTHORIZATION_FAILED`
- `RATE_LIMITED`
- `STALE`
- `CONFLICTED`

## Verification

Focused tests:

- `py -3 -m unittest Tests.test_mosp004_seeker_evidence_acquisition Tests.test_mosp001_source_registry Tests.test_eoint_constitutional_intelligence`
- Result: 25 tests passed.

Compile validation:

- `py -3 -m compileall -q src Tests Scripts`
- Result: passed.

Full-suite discovery was not rerun for this batch because the immediately prior bounded full-suite attempt remained active for several minutes and showed unrelated existing error/failure markers before termination.

## Acceptance Notes

- MO-SP-002: PASS as doctrine deliverable.
- MO-SP-003: PASS as doctrine deliverable.
- MO-SP-004: PASS for focused implementation tests.
- Repository-wide migration of every external-adjacent legacy caller remains governed by the MO-SP-001 report as a documented follow-on boundary.
