# IFVR Phase 2.5 Stateful Authority Uniqueness

## Canonical Authority Diagnostics
`CanonicalEnterpriseRuntime.stateful_authority_diagnostics()` now enumerates canonical stateful authorities with implementation class, runtime attribute, identity, duplicate flag, and construction site.

## Authorities Checked
- workflow orchestrator
- scheduler
- mission planner
- duty officers
- communications bus
- paper broker
- performance truth
- position monitoring
- doctrine/policy
- position lifecycle

## Startup Enforcement
`CanonicalEnterpriseRuntime._validate_startup()` fails closed with `DUPLICATE_STATEFUL_AUTHORITY` if component identity diagnostics reveal unsafe duplicate authority aliases.

## Test Evidence
`Tests.test_ifvr001_runtime_convergence.IFVR001RuntimeConvergenceTests.test_stateful_authority_diagnostics_are_unique` starts the canonical runtime and asserts no duplicate stateful authorities.
