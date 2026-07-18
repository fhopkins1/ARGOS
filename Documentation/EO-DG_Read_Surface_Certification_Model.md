# EO-DG Read Surface Certification Model

Read surface certification states:
- `CERTIFIED_READ_ONLY`
- `CONDITIONALLY_READ_ONLY`
- `NOT_CERTIFIED`
- `MUTATING_COMMAND`
- `PROOF_ONLY`
- `SIMULATION_ONLY`
- `TEST_ONLY`
- `DEPRECATED`
- `QUARANTINED`

Only certified read-only surfaces may be represented as constitutionally safe production reads. Conditional surfaces require further runtime and concurrency evidence.

