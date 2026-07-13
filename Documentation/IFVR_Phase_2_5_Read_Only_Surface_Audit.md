# IFVR Phase 2.5 Read-Only Surface Audit

## Canonical Read Surface
`CanonicalEnterpriseRuntime.read_only_snapshot()` remains the certified read surface. It is repeatedly digest-tested for no mutation.

## Compatibility Read Surface
`ControlPanelRuntime.state()` remains broad and assembles many dashboard panels. Critical paper authorities are now shared with the canonical runtime, but the method is still too large to certify as a pure read projection in this pass.

## Remediation Completed
- Added provider snapshot endpoint `/api/runtime/provider`.
- Kept canonical snapshot digest stable.
- Prevented server startup from eagerly constructing the legacy dashboard graph.

## Remaining Risk
Full decomposition of legacy dashboard state assembly into pure projections is still pending. This is why IFVR-001 is a conditional convergence result rather than a full pass.
