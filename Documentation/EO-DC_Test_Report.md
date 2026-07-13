# EO-DC Test Report

## Commands

- `py -3 -m py_compile src\argos\control_panel\truth_promotion.py src\argos\control_panel\performance_truth_engine.py src\argos\control_panel\enterprise_persistence.py src\argos\trader\paper_brokerage.py src\argos\control_panel\__init__.py Tests\test_eodc_truth_promotion.py`
- `py -3 -m unittest Tests.test_eodc_truth_promotion -v`
- `py -3 -m unittest Tests.test_eodc_truth_promotion Tests.test_eoda_constitutional_invariants Tests.test_ifvr001_phase35_truth_envelope Tests.test_or006_enterprise_persistence Tests.test_or003_paper_brokerage Tests.test_or004_position_lifecycle -v`
- Bounded full discovery attempt: `py -3 -m unittest discover -s Tests -v` with 120 second cap.

## Results

EO-DC targeted: 10 passed.

Focused adjacent regression sweep: 39 passed.

Full discovery was attempted after EO-DC with a 120 second cap. It timed out and surfaced known legacy dashboard failures before timeout, including broker-realistic paper trading, controlled cognitive pilot, and Decision Laboratory dashboard expectations. EO-DC does not certify continuous paper trading.
