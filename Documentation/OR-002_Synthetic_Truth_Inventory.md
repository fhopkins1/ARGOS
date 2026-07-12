# OR-002 Synthetic Truth Inventory

## Summary

OR-002 audited the active ARGOS runtime for records that could appear authoritative without authoritative enterprise provenance. The main active issue was not legitimate simulation; it was proof/demo workflow output entering certified PAPER truth.

## Inventory

| File | Symbol | Prior Behavior | Risk | Classification | Remediation | Final Status |
|---|---|---|---|---|---|---|
| `src/argos/control_panel/runtime.py` | `_paper_decision_object` | Runtime authored paper Decision Objects with placeholder/proof financial fields. | Runtime could appear to act as Seeker, Analyst, Risk, Trader, and Historian. | Quarantine as proof mode | Replaced active usage with `_proof_decision_object`; records carry `PROOF`, `PROOF_ONLY`, `PROOF_MODE_NOT_ACTIONABLE`, rejected provenance, and missing material field provenance. | Quarantined |
| `src/argos/control_panel/runtime.py` | `_complete_paper_trading_session_workflow` | Placeholder stages advanced through all offices and called Performance Truth on archive. | Archived proof workflow could create paper orders, fills, positions, portfolio values, and attribution. | Remove from certified PAPER | Stage output now says proof-mode/incomplete; archive still calls Performance Truth, but Performance Truth rejects the unproven record instead of mutating ledgers. | Blocked from PAPER truth |
| `src/argos/control_panel/performance_truth_engine.py` | `record_completed_workflow` | Created broker order, fill/position/trade/valuation/outcome/attribution from the latest workflow Decision Object. | Missing or placeholder Decision Objects could create synthetic operational truth. | Replace with provenance validation | Added fail-closed validation through `truth_domain.validate_decision_object_for_operational_truth`; rejected records are audit-visible and do not mutate ledgers. | Remediated |
| `src/argos/control_panel/performance_truth_engine.py` | `_simulate_broker_order` | Paper broker records had broker realism fields but lacked explicit truth-domain metadata. | Paper model could be mistaken for certified/live broker truth. | Preserve as paper brokerage model | Added `truthMetadata` to intended order payload: `PAPER`, `PAPER_PROVISIONAL_BROKER_MODEL`, `PAPER_BROKER_PROVISIONAL_OR003`. | Preserved for OR-003 |
| `src/argos/control_panel/position_surveillance_engine.py` | `surveil` | Runtime state polling called surveillance with live registry mutation. | Repeated Commander/dashboard state reads could append position history. | Add read-only mode | Added `mutate_registry`; runtime uses `False`, direct operational surveillance defaults to `True`. | Remediated |
| `src/argos/control_panel/position_exit_decision_engine.py` | `evaluate` | Runtime state polling could recommend exits into registry if triggers appeared. | Advisory state assembly could mutate position truth. | Add read-only mode | Added `mutate_registry`; runtime uses `False`, direct evaluation defaults to `True`. | Remediated |
| `ui/argos_control_panel/app.js` | `bridgePortfolio`, Command Bridge render | No portfolio ledger caused a generic simulated performance fallback. | Proof workflows could be visually confused with operational portfolio truth. | Dashboard truth labeling | Added explicit labels for certified PAPER, proof quarantine, and simulation. | Remediated |
| `src/argos/control_panel/market_data_provider.py` | Mock/synthetic provider outputs | Mock and synthetic market provider fixtures remain available. | Could be mistaken for live observed market data if used operationally. | Document for later OR | Not deleted; classified as provisional/test/paper infrastructure requiring OR-003/OR-005 integration hardening. | Deferred |
| `src/argos/control_panel/market_replay_engine.py`, `stress_testing_engine.py`, `black_swan_simulation_engine.py`, `monte_carlo_portfolio_engine.py`, `decision_laboratory.py` | Simulation outputs | Analytical simulations create modeled outputs. | Simulation output must not enter operational truth. | Preserve as analytical simulation | No direct mutation path to Performance Truth was introduced; remaining certification assigned to OR-005/OR-007. | Preserved |

## Required Dispositions

- Remove from certified PAPER: runtime-authored proof decisions and workflow-generated financial truth.
- Preserve with labels: paper broker modeling.
- Preserve as simulation: replay/stress/Monte Carlo/black-swan/decision-lab systems.
- Defer to OR-003: paper broker realism certification.
- Defer to OR-006: durable persistence of rejected truth/audit records.

