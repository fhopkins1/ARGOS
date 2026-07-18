# EO-DG Test Report

Targeted EO-DG tests cover:
- digest normalization
- authoritative mutation detection
- profile-specific domain separation
- registry validation and duplicate rejection
- protected state and digest coverage
- synchronous read guard
- async read guard
- streaming read guard
- 1,000-call polling stress
- counter mutation detection
- unregistered, live, and wrong-domain rejection
- mutating command rejection
- server route audit
- Commander limitations
- package exports
- static financial-boundary checks

Targeted command:
`$env:PYTHONPATH='src'; py -3 -m unittest Tests.test_eodg_read_only_integrity -v`

Result: 15 tests passed.

Focused adjacent command:
`$env:PYTHONPATH='src'; py -3 -m unittest Tests.test_eodg_read_only_integrity Tests.test_eodf_long_duration_operations_lab Tests.test_eode_fault_injection_lab Tests.test_eodd_transaction_reconciliation Tests.test_eodc_truth_promotion Tests.test_eoda_constitutional_invariants Tests.test_ifvr001_phase35_truth_envelope Tests.test_ifvr001_runtime_convergence Tests.test_or005_canonical_runtime Tests.test_or006_enterprise_persistence Tests.test_or007_enterprise_certification Tests.test_or003_paper_brokerage Tests.test_or004_position_lifecycle -v`

Result: 109 tests passed.

Full discovery command:
`$env:PYTHONPATH='src'; py -3 -m unittest discover -s Tests -v`

Result: bounded 120-second run timed out after surfacing existing dashboard-area failures in `test_argos_control_panel_dashboard`. EO-DG targeted and focused dependencies remained green.
