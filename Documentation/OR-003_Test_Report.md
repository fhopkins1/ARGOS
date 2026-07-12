# OR-003 Test Report

Focused validation executed:

`python -m unittest Tests.test_or003_paper_brokerage -v`

Result:

3 tests passed.

Related regression validation executed:

`python -m unittest Tests.test_or003_paper_brokerage Tests.test_broker_integration_office Tests.test_order_management_office Tests.test_execution_quality_office Tests.test_live_portfolio_performance_console -v`

Result:

27 tests passed.

Covered:

- Broker-authoritative market order fill and settlement.
- Performance Truth records broker-authoritative paper order.
- Enterprise Communications Bus receives broker events.
- Invalid workflow token owner rejects without fill.
- Non-executable limit order does not fabricate a fill.

Repository-wide validation note:

`python -m unittest discover -s Tests -p 'test_*.py'` was started. It emitted multiple pre-existing failure markers and then stopped producing output before completion, so the specific failure list was not available from that run. The process was stopped to avoid leaving a hung validation session active. Focused OR-003 and touched-module regression suites passed.
