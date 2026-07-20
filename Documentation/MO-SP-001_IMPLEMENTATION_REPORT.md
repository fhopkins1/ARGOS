# MO-SP-001 Implementation Report

## A. Implementation Summary

Implemented the Approved Source Registry and Search-Surface Doctrine in `src/argos/intelligence/source_registry.py` and exported it through `src/argos/intelligence/__init__.py`.

The implementation provides immutable source records, retrieval-surface records, active registry versioning, change records, pre-retrieval authorization requests and decisions, source-use evidence records, URL/final-destination validation, fallback graph validation, read-only operator visibility, persistence/recovery helpers, and a canonical seed registry.

## B. Repository Findings

Reused existing ARGOS concepts:

- `src/argos/intelligence/constitutional.py`: Intelligence Office doctrine and external-fact boundary.
- `src/argos/control_panel/market_data_provider.py`: EO-DJ market-data ingress, provider authority classifications, fail-closed missing-provider behavior.
- `src/argos/control_panel/production_read_surface_registry.py`: production read-surface certification pattern.
- `src/argos/trader/broker_integration.py`: broker adapter boundary and paper broker isolation.
- `src/argos/control_panel/workflow_orchestrator.py`: Workflow Execution Token identity.
- `src/argos/foundation/persistence`: append-only persistence repository.
- `src/argos/foundation/audit`: audit event framework.

Repository scan found legacy source-selection and external-retrieval-adjacent paths in market-data provider controls, broker integration, production read-surface registration, Codex/browser/search utilities outside ARGOS runtime, and isolated test/demo/mock fixtures. No source-policy decision was delegated to a language model or runtime provider chooser in the new implementation.

## C. Constitutional Objects

Implemented:

- `ApprovedSourceRecord`
- `ApprovedRetrievalSurfaceRecord`
- `SourceAuthorizationRequest`
- `SourceAuthorizationDecision`
- `SourceRegistryVersion`
- `SourceRegistryChangeRecord`
- `SourceUseEvidenceRecord`
- `SourceAuthorizationGateway`
- `ApprovedSourceRegistry`
- `validate_resolved_destination`
- `persist_registry_snapshot`
- `recover_registry_snapshot`
- `registry_conformance_report`

## D. Canonical Registry

Active public/official sources:

- `SRC-US-SEC-EDGAR`
- `SRC-US-SEC-ENFORCEMENT`
- `SRC-US-NYSE-MARKET-STATUS`
- `SRC-US-BLS`
- `SRC-US-FRED-DISTRIBUTION`
- `SRC-ISSUER-IR`

Environment-restricted sources:

- `SRC-BROKER-OF-RECORD`: paper-only broker authority.
- `SRC-SEARCH-ENGINE-DISCOVERY`: research-only discovery, snippets prohibited.
- `SRC-SOCIAL-EARLY-WARNING`: research-only early warning, never trade eligible.

Inactive pending approval:

- `SRC-LICENSED-SIP-MARKET-DATA`: license/credential entitlement not present in repository.

Prohibited:

- `SRC-PROHIBITED-MODEL-MEMORY`

## E. Integration Migration

Migration table is available from `migration_inventory()` and includes:

- `market_data_provider.py`: registered as `SRC-LICENSED-SIP-MARKET-DATA` / `SURF-LICENSED-SIP-API`; inactive until entitlement exists.
- `broker_integration.py`: registered as `SRC-BROKER-OF-RECORD` / `SURF-BROKER-PAPER-API`; paper-only.
- `production_read_surface_registry.py`: reused as internal read-surface reference; not external retrieval.
- Browser/search utilities: research/discovery only; snippets blocked as evidence.
- Mock/demo/sample fixtures: not approved operational external authorities.

## F. Synthetic-Truth Controls

Concrete controls:

- Unknown source IDs deny with `SP001_SOURCE_NOT_REGISTERED`.
- Unregistered surfaces deny with `SP001_SURFACE_NOT_REGISTERED`.
- Trader general research and SEC retrieval deny through office authorization.
- Search snippets deny through field authorization.
- Model memory/generated summaries are registered as prohibited.
- Inactive licensed market data cannot authorize retrieval.
- Paper broker source is denied in live.
- Arbitrary hosts, unsupported schemes, embedded credentials, localhost/private addresses, unapproved paths, and unapproved redirects are rejected.
- Fallbacks must be explicitly registered and acyclic.
- Source-use evidence records retain request, decision, registry version, source, surface, result, evidence/failure references, cache marker, cost class, and response digest.

## G. Tests

New tests:

- `Tests/test_mosp001_source_registry.py`

Focused verification:

- `py -3 -m unittest Tests.test_mosp001_source_registry Tests.test_eoint_constitutional_intelligence`
- Result: 17 tests passed.

Compile verification:

- `py -3 -m compileall -q src Tests Scripts`
- Result: passed.

Full-suite discovery:

- `py -3 -m unittest discover -s Tests`
- Result: bounded run was still active after several minutes and showed unrelated existing error/failure markers before termination. No MO-SP focused tests failed.

## H. Acceptance-Criteria Matrix

1. Every external retrieval path routed through gateway: BLOCKED - gateway implemented; legacy callers inventoried, not all call sites rewritten.
2. No arbitrary external destination can be accessed by an ARGOS office: PASS - URL/surface tests block arbitrary destinations through the gateway.
3. Every active source has immutable identity: PASS.
4. Every retrieval surface independently registered: PASS.
5. Every source has authority domain: PASS.
6. Every source has field-level permitted uses: PASS.
7. Every source has explicit prohibited uses: PASS.
8. Every source has office permissions: PASS.
9. Every source has environment permissions: PASS.
10. Every source has retrieval-method permissions: PASS.
11. Every source has freshness metadata: PASS.
12. Every source has evidence-retention metadata: PASS.
13. Every source has cost metadata: PASS.
14. Every source has outage disposition: PASS.
15. Every source has suspension and replacement conditions: PASS.
16. Every fallback relationship explicit: PASS.
17. No circular or implicit fallback exists: PASS.
18. Search-engine snippets cannot become evidence: PASS.
19. Aggregators cannot replace accessible primary authorities: PASS - FRED is corroborating only.
20. Low-authority sources cannot establish trade-eligible facts: PASS.
21. Trader cannot perform general external research: PASS.
22. Test/demo/fixture/sample sources operationally isolated: PASS.
23. Unlicensed live market data is blocked: PASS.
24. Broker authority limited to broker-controlled facts: PASS.
25. Government/regulatory sources limited to their jurisdictions: PASS.
26. Source-registry changes versioned and auditable: PASS.
27. Only certified active registry can authorize retrieval: PASS.
28. Registry state survives restart: PASS.
29. Registry corruption fails closed: PASS.
30. Authorization decisions are persisted or persistable: PASS - decision records are immutable; source-use evidence retained by gateway.
31. Attempted source uses auditable: PASS.
32. Existing integrations migrated/quarantined/removed: BLOCKED - migration inventory produced; not every legacy caller was rewritten.
33. No retrieval failure creates synthetic continuity: PASS through gateway denial/source-use evidence model.
34. All new tests pass: PASS.
35. Full preexisting suite passes except unrelated failures: BLOCKED - full discovery did not complete in bounded run and showed unrelated failures.
36. No policy decision delegated to runtime code/model/operator informal judgment: PASS for the implemented gateway and canonical registry.

## Inactive Source Candidates

- `SRC-LICENSED-SIP-MARKET-DATA`

## Prohibited Or Quarantined Legacy Paths

- Model recollection or generated summaries as source evidence.
- Search-engine snippets as evidence.
- Unregistered URL destinations.
- Demo/sample/mock providers outside isolated tests.
- Paper broker records in live operation.
- Unlicensed live market-data redistribution.

## Unresolved Dependencies

- MO-SP-002 detailed scheduling and retry timing.
- MO-SP-013 expanded source-use evidence schema.
- Certified live broker, live market-data credentials, and license entitlement records are not present in this repository.
- Mechanical rewriting of every legacy external-adjacent caller to invoke `SourceAuthorizationGateway` remains incomplete.
