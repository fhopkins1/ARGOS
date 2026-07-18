# EO-DI Test Report

Focused EO-DI tests:

`py -3 -m unittest Tests.test_eodi_test_evidence_office`

Result: 14 tests passed in 47.571 seconds.

Series D and OR readiness slice:

`py -3 -m unittest Tests.test_eodi_test_evidence_office Tests.test_eoda_constitutional_invariants Tests.test_eodb_runtime_bridge_certification Tests.test_eodc_truth_promotion Tests.test_eodd_transaction_reconciliation Tests.test_eode_fault_injection_lab Tests.test_eodf_long_duration_operations_lab Tests.test_eodg_read_only_integrity Tests.test_eodh_synthetic_truth_quarantine Tests.test_or003_paper_brokerage Tests.test_or004_position_lifecycle Tests.test_or005_canonical_runtime Tests.test_or006_enterprise_persistence Tests.test_or007_enterprise_certification`

Result: 136 tests passed in 54.804 seconds.

Full repository suite:

`py -3 -m unittest discover -s Tests`

Result: `FULL_SUITE_TIMEOUT_120S`.
