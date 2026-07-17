# EO-DF Prechange Audit

Recorded before implementation:
- Branch: `main`
- Full commit SHA: `d80d6ab4fc3d4fb753efc73cd3a09b3b41be77e6`
- Git status: clean
- Python version: `Python 3.14.5`
- Node version: `v24.16.0`
- Operating system: Windows host reported by PowerShell
- Persistence backend: `DurableEnterprisePersistenceStore`
- Runtime configuration: paper/control runtime, live disabled
- Truth-domain configuration: paper/test/replay/simulation/proof/live isolated
- Policy version: repository policy manager active; campaign definitions freeze policy version
- Doctrine version: repository doctrine manager active; campaign definitions freeze doctrine version
- Active paper broker: `DeterministicPaperBrokerage`
- Live-trading status: disabled
- Expected campaign environment: local deterministic laboratory
- Existing long-duration state: OR-007 reports no completed unattended long-duration campaign
- Existing fault-injection framework: EO-DE `FaultInjectionRecoveryLaboratory`

EO-DF reuses EO-DE for fault campaigns and does not create a second fault-injection authority.

