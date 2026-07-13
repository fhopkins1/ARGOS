# IFVR Phase III.5 Learning Data Governance

## Closed Position Defaults

`ClosedPositionTruthConfig.learning_event_enabled` now defaults to `False`.

## Degraded Evidence

Degraded lifecycle evidence is analytical-only and carries `learning_promotion_allowed: false`.

## Promotion Rule

Learning promotion requires authoritative Closed Position Truth. Analytical-only degraded records may be reviewed, but they are not learning-grade operational truth.

