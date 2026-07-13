# EO-DC Decision Object Promotion

`TruthPromotionAuthority.promote_decision_object()` is the canonical Decision Object gate.

It validates PAPER domain, provenance, certification status, source authority, workflow lineage, mission lineage, token lineage, fallback use, degraded reasons, runtime authorship, placeholder authorship, proof, simulation, test, replay, and live indicators.

Paper Broker validation now calls this gate before Trader/Broker order processing can proceed.

