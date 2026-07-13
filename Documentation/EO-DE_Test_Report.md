# EO-DE Test Report

Targeted EO-DE tests cover:
- catalog coverage
- execution of every catalog fault
- evidence preservation
- no financial mutation
- no synthetic truth
- deterministic repeated campaigns
- EO-DC truth-domain contamination rejection
- EO-DD reconciliation blocking for broker/position faults
- recovery-required state for recovery/persistence faults
- read-only fault zero-mutation behavior
- bounded resource pressure
- Commander acknowledgment and halt immutability
- package exports

Targeted command:
`$env:PYTHONPATH='src'; py -3 -m unittest Tests.test_eode_fault_injection_lab -v`

Result: 10 tests passed.

Focused adjacent command:
`$env:PYTHONPATH='src'; py -3 -m unittest Tests.test_eode_fault_injection_lab Tests.test_eodd_transaction_reconciliation Tests.test_eodc_truth_promotion Tests.test_eoda_constitutional_invariants Tests.test_ifvr001_phase35_truth_envelope Tests.test_or006_enterprise_persistence Tests.test_or003_paper_brokerage Tests.test_or004_position_lifecycle -v`

Result: 60 tests passed.

Full discovery command:
`$env:PYTHONPATH='src'; py -3 -m unittest discover -s Tests -v`

Result: bounded 120-second run timed out after surfacing existing dashboard-area failures in `test_argos_control_panel_dashboard`. EO-DE targeted and focused dependencies remained green.
