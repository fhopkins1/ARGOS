# EO-DD Test Report

Targeted EO-DD tests cover:
- transaction taxonomy registration
- immutable intent persistence
- EO-DC approval rejection
- non-paper/live-domain rejection
- transaction idempotency
- missing participant acknowledgment commit block
- successful clean reconciliation commit
- partial acknowledgment not complete
- acknowledgment idempotency
- blocking reconciliation discrepancies
- nonterminal recovery replay
- read-only Commander model

Command used:
`$env:PYTHONPATH='src'; py -3 -m unittest Tests.test_eodd_transaction_reconciliation -v`

Result: 11 tests passed.

Focused adjacent command:
`$env:PYTHONPATH='src'; py -3 -m unittest Tests.test_eodd_transaction_reconciliation Tests.test_eodc_truth_promotion Tests.test_eoda_constitutional_invariants Tests.test_ifvr001_phase35_truth_envelope Tests.test_or006_enterprise_persistence Tests.test_or003_paper_brokerage Tests.test_or004_position_lifecycle -v`

Result: 50 tests passed.

Full discovery command:
`$env:PYTHONPATH='src'; py -3 -m unittest discover -s Tests -v`

Result: bounded 120-second run timed out after surfacing existing dashboard-area failures in `test_argos_control_panel_dashboard`. EO-DD targeted and focused dependencies remained green.
