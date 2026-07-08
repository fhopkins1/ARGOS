# EO-009 Foundation Testing Framework

ARGOS Foundation tests are deterministic, registered, and reportable. EO-009
defines test infrastructure for unit, integration, contract, regression, replay,
and failure-injection coverage.

## Components

- `TestSuiteRegistration`: maps a deterministic test module to Foundation
  components, Engineering Orders, and specifications.
- `foundation_test_registry()`: authoritative suite registry for current
  Foundation components.
- `TestRunner`: executes registered unittest modules.
- `ComplianceReporter`: produces machine-readable JSON and human-readable
  Markdown reports.

## Coverage Requirement

Every Foundation component must have at least one registered suite. Reports link
each suite to Engineering Orders and Project Bible/specification references.

## Determinism

The framework uses Python standard-library `unittest`, deterministic registry
ordering, structured result objects, and sorted JSON report output.

