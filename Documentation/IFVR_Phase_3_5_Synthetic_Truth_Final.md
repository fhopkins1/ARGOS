# IFVR Phase III.5 Synthetic Truth Final Remediation

## Decision Object Guard

`validate_decision_object_for_operational_truth(...)` continues to reject proof, simulation, placeholder, uncertified, missing-provenance, and unauthorized-producer Decision Objects.

## Envelope Guard

`validate_operational_truth_envelope(...)` rejects missing, proof, simulation, live, degraded, uncertified, unvalidated, and wrong-authority envelopes.

## Closed Position Truth

Degraded benchmark or attribution evidence is retained as `DegradedClosedPositionAnalyticalRecord` and is not inserted into authoritative Closed Position Truth by default.

## Performance Truth

`record_broker_authoritative_order(...)` rejects missing or invalid envelopes before mutating order, trade, position, or valuation ledgers.

