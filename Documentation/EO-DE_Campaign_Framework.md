# EO-DE Campaign Framework

`FaultInjectionRecoveryLaboratory` executes deterministic campaigns without financial mutation authority.

Campaign flow:
- prepare deterministic fault evidence
- inject the requested fault
- evaluate EO-DA evidence
- evaluate EO-DC promotion behavior
- evaluate EO-DD transaction and reconciliation behavior
- evaluate recovery evidence
- record resource snapshot
- emit Commander alert
- calculate determinism signature
- preserve campaign report

Campaigns may run all catalog faults or a selected tuple of fault ids. Repeated runs compare deterministic signatures by fault id and classify nondeterminism.

EO-DE does not certify ARGOS. It produces resilience evidence for later Series D certification.

