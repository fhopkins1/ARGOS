# IFVR Phase III.5 Authority Model

## Operational Authorities

The operational authority allowlist is centralized in `truth_domain.py` as `AUTHORIZED_OPERATIONAL_AUTHORITIES`.

## Current Write Boundaries

- `DeterministicPaperBrokerage` originates broker-authoritative paper events.
- `PerformanceTruthEngine` consumes broker events only after envelope validation.
- `DurableEnterprisePersistenceStore` persists operational broker, position, and performance truth snapshots only after envelope validation.
- `ClosedPositionTruthBuilder` no longer promotes degraded lifecycle evidence into authoritative records by default.

## Live Trading

Live remains disabled. The envelope validator rejects `LIVE` truth domains with `LIVE_DISABLED`.

