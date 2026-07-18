# EO-DB Test Report

Focused EO-DB tests:

`py -3 -m unittest Tests.test_eodb_runtime_bridge_certification`

Result: 12 tests passed in 13.896 seconds.

Adjacent assurance tests:

`py -3 -m unittest Tests.test_eodb_runtime_bridge_certification Tests.test_eoda_constitutional_invariants Tests.test_eodc_truth_promotion Tests.test_eodd_transaction_reconciliation Tests.test_eode_fault_injection_lab Tests.test_eodf_long_duration_operations_lab Tests.test_eodg_read_only_integrity`

Result: 84 tests passed in 20.837 seconds.

OR readiness tests:

`py -3 -m unittest Tests.test_or003_paper_brokerage Tests.test_or004_position_lifecycle Tests.test_or005_canonical_runtime Tests.test_or006_enterprise_persistence Tests.test_or007_enterprise_certification`

Result: 24 tests passed in 5.354 seconds.

Full repository suite:

`py -3 -m unittest discover -s Tests`

Result: `FULL_SUITE_TIMEOUT_120S`.

`pytest` was not available for the local `py -3` interpreter, so focused tests were run with `unittest`.
