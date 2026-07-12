# ARGOS

ARGOS is a deterministic cognitive enterprise scaffold for AI-assisted financial intelligence, paper-trading research, operational controls, replay, analytics, and education.

The repository is no longer only the original EO-001 skeleton. It contains a runnable local control panel, enterprise runtime modules, workflow orchestration, paper/proof workflow infrastructure, analytics engines, tests, and documentation.

## Current Operational Status

- Live trading is disabled, blocked by configuration, and uncertified.
- Real broker credentials are not included and must not be added as part of Operational Readiness work before OR-007.
- The active self-training workflow is quarantined as PROOF mode unless future Engineering Orders wire authoritative office products into PAPER operation.
- Paper brokerage modeling is provisional and assigned to OR-003 for realism certification.
- Operational persistence remains incomplete until OR-006; most runtime truth is in process memory.
- Production readiness is not claimed.

## Truth Domains

- TEST: automated tests and fixtures only.
- PROOF: workflow, UI, LAW VII, and credit-accounting demonstrations; not operational truth.
- SIMULATION: replay, stress testing, Monte Carlo, counterfactual, and analytical outputs; cannot mutate operational ledgers.
- PAPER: broker-realistic paper records, allowed only with provenance, authority chain, and paper/live isolation.
- LIVE: disabled and fail-closed until separately certified.

## Governing Principles

- Determinism: every process must be reproducible, auditable, version-controlled, and traceable.
- Separation of duties: no office evaluates or authorizes its own work.
- Evidence before doctrine: information progresses through Information, Evidence, Validated Knowledge, Doctrine, and Education.
- Auditability: decisions, outputs, recommendations, trades, lessons, and knowledge updates must be traceable to evidence and system state.
- Human control: override, kill switches, approval gates, and operational boundaries are mandatory.
- Safety and financial boundaries: live trading authority requires explicit implementation gates, broker controls, persistence, recovery, and user approval.

## Running the Local Control Panel

```powershell
.\Launch_ARGOS_Control_Panel.cmd
```

or:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\launch_argos_control_panel.ps1
```

Default URL:

```text
http://127.0.0.1:8765/
```

