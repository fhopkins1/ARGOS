# OR-007 Enterprise Certification Framework

## Purpose
OR-007 is the end-to-end enterprise certification gate for ARGOS paper operation. Certification is evidence-based: runtime behavior, authority boundaries, persistence, replay, LAW VII workflow control, synthetic truth isolation, and long-duration readiness must all pass before continuous paper trading can be certified.

## Certification Standard
- Runtime may orchestrate work, but must not create broker fills, mutate positions directly, or act as portfolio truth.
- Paper broker owns execution truth.
- Position registry and lifecycle manager own position truth.
- Performance truth records realized outcomes only after authoritative broker/position events.
- Workflow token ownership must remain LAW VII compliant.
- Persistence must survive restart and crash recovery without substituting snapshots for authoritative state.
- Commander and UI surfaces must be read-only or clearly quarantined as proof/simulation surfaces.
- Synthetic, proof, placeholder, and simulation data must not be confused with PAPER operational truth.
- Long-duration unattended paper operation must complete without unbounded resource growth, duplicate work, or authority drift.

## Evidence Classes
- Focused test evidence: OR-003 through OR-007 focused regression bundle.
- Deterministic campaign evidence: `EnterpriseCertificationHarness.run_campaign`.
- Static boundary evidence: synthetic truth and enterprise boundary scans.
- Documentation evidence: OR-003 through OR-007 architecture and readiness reports.

## Verdict Rule
Any failed readiness category, critical finding, or not-certified subsystem prevents continuous paper trading certification. Successful focused tests are necessary but not sufficient.

## Current Framework Result
Final OR-007 status is **NOT CERTIFIED** for continuous paper trading because full-suite and long-duration evidence are incomplete, and legacy proof/self-training Commander surfaces remain.
