# EO-DA Truth Domain Gating Model

`TruthDomainInvariantGate` integrates with the Phase III.5 `OperationalTruthEnvelope`.

## Rejection Classes

The gate rejects missing envelopes, proof, simulation, live, degraded analytical objects, unvalidated provenance, uncertified operational truth, missing workflow/mission/token/source event, and unauthorized authorities.

The gate is used as assurance evidence and as a transition precondition interface. It delegates actual envelope validation to `truth_domain.py` to avoid duplicate truth models.

