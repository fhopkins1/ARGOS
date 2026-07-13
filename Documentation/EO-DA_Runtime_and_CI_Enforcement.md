# EO-DA Runtime and CI Enforcement

## Startup

`CanonicalEnterpriseRuntime._validate_startup()` now runs `ConstitutionalInvariantEngine().evaluate_startup(self)` after existing startup checks. Critical blocking EO-DA startup failures fail closed through `CanonicalRuntimeError`.

## Static Repository Validation

`ConstitutionalInvariantEngine.evaluate_static_architecture()` uses AST/source checks for:

- production paper route canonical provider delegation,
- Commander/server route financial-authority bypasses,
- API Gateway boundary presence,
- live trading default disabled.

## CI

`Tests/test_eoda_constitutional_invariants.py` exercises the EO-DA catalog, registries, static checks, startup checks, LAW VII monitor, truth gate, read-only guard, and reconciliation checks.

