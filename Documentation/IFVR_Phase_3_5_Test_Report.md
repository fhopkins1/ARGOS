# IFVR Phase III.5 Test Report

## Commands

- `py -3 -m py_compile src\argos\control_panel\truth_domain.py src\argos\control_panel\performance_truth_engine.py src\argos\trader\paper_brokerage.py src\argos\control_panel\closed_position_truth.py src\argos\control_panel\enterprise_persistence.py`
- `py -3 -m unittest Tests.test_ifvr001_phase35_truth_envelope -v`
- `py -3 -m unittest Tests.test_ifvr001_phase35_truth_envelope Tests.test_ifvr001_runtime_convergence Tests.test_or006_enterprise_persistence -v`
- `py -3 -m unittest Tests.test_or003_paper_brokerage Tests.test_or004_position_lifecycle -v`

## Result

All listed focused and adjacent regression commands passed.

