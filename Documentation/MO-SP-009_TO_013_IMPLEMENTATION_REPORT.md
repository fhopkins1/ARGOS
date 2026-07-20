# MO-SP-009 to MO-SP-013 Implementation Report

## Scope

Implemented the next ARGOS External Search Parameters doctrine set:

- `MO-SP-009` Trader search prohibition and information eligibility doctrine.
- `MO-SP-010` Historian search retention and historical reconstruction doctrine.
- `MO-SP-011` Search cost, caching, priority, and resource-governance doctrine.
- `MO-SP-012` Search failure, source outage, and escalation doctrine.
- `MO-SP-013` Search evidence, reproducibility, and certification doctrine.

## Repository Integration

The implementation extends existing ARGOS office boundaries:

- Trader eligibility: `src/argos/trader/information_eligibility.py`
- Historian reconstruction: `src/argos/historian/search_reconstruction.py`
- Search operations governance: `src/argos/intelligence/search_operations.py`

The new code is exported through the existing `argos.trader`, `argos.historian`, and `argos.intelligence` package surfaces.

## Controls Implemented

- Trader cannot perform research, source substitution, evidence reinterpretation, or synthetic continuity.
- Trader execution packages must carry required approvals, identifiers, freshness records, source certification, integrity verification, signatures, and broker/market validations.
- Historian preserves decision-time knowledge separately from available-but-not-collected evidence, later publications, corrections, revisions, and retrospective interpretations.
- Resource governance assigns deterministic priority classes `P0` through `P7`, cost classes `C0` through `C5`, budget outcomes, cache outcomes, and safety reserve behavior.
- Failure doctrine classifies retrieval, outage, authentication, schema, stale, cache, and evidence-storage failures into explicit workflow states and escalation rules.
- Search Evidence Records are immutable, certifiable, and required for institutional evidence consumption, including failed searches and zero-result searches.

## Test Evidence

Command executed:

```powershell
python -m unittest Tests.test_mosp009_to_013_search_governance Tests.test_mosp005_to_008_search_doctrine
```

Result:

```text
Ran 14 tests in 0.085s
OK
```
