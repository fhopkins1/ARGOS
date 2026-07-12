# AUDIT Test Commands

## Compile
```text
command: C:\Users\Fletc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m compileall -q src Tests
exit_code: 0
started: 2026-07-12T23:01:26.9133670Z
ended: 2026-07-12T23:01:27.2281946Z
duration_seconds: 0.315


```

## JavaScript Syntax
```text
command: node --check ui\argos_control_panel\app.js
exit_code: 0
started: 2026-07-12T23:05:26.7531854Z
ended: 2026-07-12T23:05:26.8311622Z
duration_seconds: 0.078


```

## Targeted Bundle
```text
command: C:\Users\Fletc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest Tests.test_or007_enterprise_certification Tests.test_or006_enterprise_persistence Tests.test_or005_canonical_runtime Tests.test_or004_position_lifecycle Tests.test_or003_paper_brokerage Tests.test_position_management_office Tests.test_persistence_framework Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_cl_workflow_handoff_requires_law_vii_metadata_and_does_not_transfer_token -v
exit_code: 0
started: 2026-07-12T23:01:36.1687634Z
ended: 2026-07-12T23:01:38.1198477Z
duration_seconds: 1.951


```

## Full Test Discovery
```text
command: C:\Users\Fletc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover Tests -v
exit_code: -1
started: 2026-07-12T23:01:46.2898873Z
ended: 2026-07-12T23:05:12.8115360Z
duration_seconds: 206.522


```

The full discovery run exceeded the audit window and was interrupted by terminating only the specific Python unittest process. Partial output is preserved.
