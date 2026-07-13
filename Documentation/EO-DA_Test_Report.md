# EO-DA Test Report

## Commands

- `py -3 -m py_compile src\argos\control_panel\constitutional_invariants.py src\argos\control_panel\canonical_enterprise_runtime.py src\argos\control_panel\__init__.py`
- `py -3 -m unittest Tests.test_eoda_constitutional_invariants -v`
- `py -3 -m unittest Tests.test_eoda_constitutional_invariants Tests.test_ifvr001_runtime_convergence Tests.test_ifvr001_phase35_truth_envelope Tests.test_or006_enterprise_persistence Tests.test_or003_paper_brokerage Tests.test_or004_position_lifecycle -v`
- Bounded full discovery attempt: `py -3 -m unittest discover -s Tests -v` with 120 second cap.

## Targeted Result

EO-DA targeted suite: 9 passed.

Focused adjacent regression sweep: 36 passed.

## Full Suite

Full discovery was attempted and stopped at the 120 second cap. It had already surfaced legacy dashboard failures before timeout, including broker-realistic paper trading and Decision Laboratory dashboard expectations. Full repository suite result: incomplete/failing, certification blocking for continuous paper trading.

EO-DA does not certify continuous paper trading.
