# MO-SP-005 to MO-SP-008 Implementation Report

## Scope

Implemented the next External Search Parameters doctrine set as deterministic, registry-backed runtime components:

- `MO-SP-005` Analyst Verification Search Engine.
- `MO-SP-006` Risk Adversarial Search Doctrine.
- `MO-SP-007` Canonical market, corporate, regulatory, legal, and macroeconomic search doctrine.
- `MO-SP-008` Broker, account, order, and execution search doctrine.

## Repository Integration

The implementation extends existing ARGOS office boundaries:

- Intelligence: `src/argos/intelligence/search_doctrine.py`
- Analyst: `src/argos/analyst/verification_search.py`
- Risk: `src/argos/risk/adversarial_search.py`
- Trader/Broker: `src/argos/trader/broker_search_doctrine.py`

The new modules reuse the MO-SP-001 `SourceAuthorizationGateway` where external source authorization is required. No new authority path, generic search path, or provider bypass was introduced.

## Constitutional Controls

- Canonical fact types resolve through exactly one active search plan.
- Unknown fact types fail with `PLAN_NOT_FOUND`; no generic search fallback exists.
- Analyst verification uses only registered verification questions.
- Analyst outcomes include `VERIFIED`, `PARTIALLY_VERIFIED`, `CONFLICTED`, `UNKNOWN`, `UNAVAILABLE`, `RETURN_TO_SEEKER`, and `ESCALATE_TO_RISK`.
- Risk plans are built before execution and include universal searches plus deterministic conditional activation.
- Missing Risk observations produce explicit incomplete or escalation states; absence of evidence is not treated as proof of safety.
- Broker facts require predeclared broker retrieval plans, authorized offices, matching paper/live environment, and raw evidence references.
- Broker reconciliation produces explicit immutable mismatch records and trade-eligibility effects.

## Synthetic Truth Protections

The implementation rejects or quarantines:

- model memory;
- generated summaries;
- snippets as authoritative evidence;
- unregistered generic searches;
- unavailable broker facts;
- stale or unsupported broker facts;
- missing originating evidence;
- duplicate reporting treated as independent corroboration.

## Test Evidence

Command executed:

```powershell
python -m unittest Tests.test_mosp005_to_008_search_doctrine Tests.test_mosp001_source_registry Tests.test_mosp004_seeker_evidence_acquisition
```

Result:

```text
Ran 25 tests in 0.278s
OK
```
