# EO-DF Test Report

Targeted EO-DF tests cover:
- campaign registration
- duplicate campaign rejection
- invalid duration rejection
- commit requirement
- dirty working-tree policy
- live campaign rejection
- EO-DA, EO-DC, EO-DD, and persistence admission blockers
- required telemetry domains
- evidence hash generation
- metric storage isolation
- bounded workload pass
- memory leak fail
- duplicate loop fail
- growing queue fail
- restart and recovery evidence
- read-only load with zero mutation and cost
- truth-domain/live admission failure
- transaction/reconciliation endurance
- accelerated event-time distinction
- resumability
- determinism comparison
- Commander controls
- CI architecture boundaries
- missing metric evidence failure
- package exports

Targeted command:
`$env:PYTHONPATH='src'; py -3 -m unittest Tests.test_eodf_long_duration_operations_lab -v`

Result: 17 tests passed.

Focused adjacent command:
`$env:PYTHONPATH='src'; py -3 -m unittest Tests.test_eodf_long_duration_operations_lab Tests.test_eode_fault_injection_lab Tests.test_eodd_transaction_reconciliation Tests.test_eodc_truth_promotion Tests.test_eoda_constitutional_invariants Tests.test_ifvr001_phase35_truth_envelope Tests.test_or006_enterprise_persistence Tests.test_or007_enterprise_certification Tests.test_or003_paper_brokerage Tests.test_or004_position_lifecycle -v`

Result: 80 tests passed.

Full discovery command:
`$env:PYTHONPATH='src'; py -3 -m unittest discover -s Tests -v`

Result: bounded 120-second run timed out after surfacing existing dashboard-area failures in `test_argos_control_panel_dashboard`. EO-DF targeted and focused dependencies remained green.
