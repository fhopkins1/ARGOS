# OR-005 Part 1 Test Report

## Commands

```powershell
& 'C:\Users\Fletc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m py_compile src\argos\control_panel\canonical_enterprise_runtime.py src\argos\control_panel\__init__.py Tests\test_or005_canonical_runtime.py
```

Result: passed.

```powershell
& 'C:\Users\Fletc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest Tests.test_or005_canonical_runtime Tests.test_or004_position_lifecycle Tests.test_or003_paper_brokerage Tests.test_position_management_office -v
```

Result: 19 tests passed.

## Coverage

- OR-005 canonical runtime: 7 passed.
- OR-004 lifecycle: 3 passed.
- OR-003 paper brokerage: 3 passed.
- Position Management Office: 6 passed.

## Known Failures

Full dashboard suite was not rerun to completion in Part 1 because the previous OR-004 run exposed existing dashboard failures. Classification: `UI_READ_MODEL`, `BROKER`, `DEFECT`, and `LEGACY` pending deeper triage. These block full OR-005 completion but not the focused Part 1 canonical runtime foundation.

## Acceptance Verdict

Conditional pass for Part 1 foundation. OR-005 is not complete.
