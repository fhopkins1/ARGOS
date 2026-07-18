# EO-DJ Test Report

Targeted command:

`py -3 -m unittest Tests.test_eodj_market_data_boundary`

The EO-DJ suite covers provider authority policy, non-production proof-domain rejection, missing provider fail-closed behavior, deterministic observation identity, idempotent ingestion, conflict detection, freshness classifications, decision guard rejection, recovery missing-evidence behavior, default paper-broker rejection, and controlled end-to-end paper ingress.

Machine-readable test results are written to `Documentation/EO-DJ_Evidence/eo_dj_test_results.json`.
