# OR-002 Test Report

## Commands Run

- `py -m py_compile src\argos\control_panel\truth_domain.py src\argos\control_panel\decision_object_schema.py src\argos\control_panel\performance_truth_engine.py src\argos\control_panel\position_surveillance_engine.py src\argos\control_panel\position_exit_decision_engine.py src\argos\control_panel\runtime.py Tests\test_argos_control_panel_dashboard.py`
- `node --check ui\argos_control_panel\app.js`
- `py -m unittest Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_y_calibration_does_not_mutate_positions_ledgers_or_invoke_ai`
- `py -m unittest Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_or_002_manual_paper_order_is_provisional_broker_model Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_start_paper_self_training_creates_tokenized_workflow_without_api_credit_burn Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_placeholder_credit_proof_records_only_analyst_cost_once_per_workflow Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_y_calibration_does_not_mutate_positions_ledgers_or_invoke_ai`
- `py -m unittest Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_start_paper_self_training_creates_tokenized_workflow_without_api_credit_burn Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_state_polling_does_not_increase_api_totals Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_real_api_pilot_disabled_by_default_keeps_analyst_on_dry_run Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_real_api_pilot_success_updates_runtime_and_decision_source Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_workflow_runtime_monitor_displays_delayed_paper_workflow_without_api_usage`
- `py -m unittest Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_or_002_manual_paper_order_is_provisional_broker_model Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_start_paper_self_training_creates_tokenized_workflow_without_api_credit_burn Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_placeholder_credit_proof_records_only_analyst_cost_once_per_workflow Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_y_calibration_does_not_mutate_positions_ledgers_or_invoke_ai Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_workflow_runtime_monitor_retains_latest_ten_completed_workflows`
- `py -m unittest Tests.test_argos_control_panel_dashboard`

## Results

- Python compile checks: passed.
- JavaScript syntax check: passed.
- EO-Y targeted regression: passed.
- OR-002 targeted tests: passed.
- Timing-sensitive workflow monitor slice after the runtime settle fix: passed.
- OR-002 acceptance plus multi-cycle workflow monitor slice: passed.
- Full dashboard suite captured during OR-002 remediation: `Ran 431 tests in 1182.421s`; `FAILED (failures=51)`.

## Failures Addressed

- EO-Y unauthorized position-registry mutation was fixed.
- Old tests expecting proof workflows to create paper orders/positions were updated to assert proof quarantine.
- Zero-delay workflow tests were synchronized so `start_paper_self_training()` returns after the first proof workflow is archived.

## Remaining Full-Suite Failures

- The remaining failures are legacy dashboard contracts that still wait for synthetic paper orders, positions, trade attribution reports, enterprise reproducibility snapshots, replay certification, strategy performance, and related portfolio truth products from the proof workflow.
- Under OR-002, those records are intentionally blocked because the runtime-authored proof Decision Object lacks authorized Trader/Risk provenance and is classified `PROOF_ONLY`.
- Remediation path: OR-003 must replace these expectations with paper broker provisional records from an explicit broker model, or the tests must assert proof quarantine where the subsystem is only consuming runtime proof output.

## Certification Limitations

- OR-002 does not certify paper broker realism; assigned to OR-003.
- OR-002 does not implement durable enterprise persistence; assigned to OR-006.
- OR-002 does not certify live trading; assigned to OR-007.
