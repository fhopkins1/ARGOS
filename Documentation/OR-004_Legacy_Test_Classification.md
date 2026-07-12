# OR-004 Legacy Test Classification

## Focused Passing Tests

- `Tests.test_or004_position_lifecycle`: OR-004 position lifecycle behavior.
- `Tests.test_or003_paper_brokerage`: broker-realistic order behavior.
- `Tests.test_position_management_office`: existing PMO behavior.

## Broad Dashboard Failures Observed

The dashboard monolith was capped because it is large and had already produced non-OR-004 failures. Observed failing tests included:

- Broker-realistic dashboard scenarios for deposited cash, partial fill quantity, buying power rejection, and sell realized P&L.
- Controlled cognitive pilot bounded workflow completion.
- Decision laboratory replay/comparison preservation.
- Daily learning paper workflow record counting.
- Benchmark paper trade snapshot/report feeding.

## Classification

- OR-004 position lifecycle unit coverage: remediated.
- OR-003 broker core unit coverage: preserved.
- PMO legacy unit coverage: preserved.
- Dashboard integration coverage: not remediated in OR-004; requires separate integration classification and likely fixture updates or dashboard bridge remediation.

## Readiness Impact

The remaining dashboard failures prevent a claim that all enterprise paper-trading surfaces are green. They do not invalidate the targeted OR-004 broker-confirmed lifecycle path verified in this remediation.
