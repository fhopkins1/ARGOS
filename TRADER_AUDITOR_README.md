# TRADER-IC-000 Auditor Reproduction Guide

This candidate includes a package-bound Trader Office audit runner. It requires
Python 3.11 or newer and no Git repository, package installation, network
access, development checkout, or manual `PYTHONPATH`.

Run from a freshly extracted candidate:

```bash
python audit_trader_reproduce.py --candidate "/path/to/TRADER_REPOSITORY.zip" --output "/path/to/new_empty_audit_output"
```

Expected successful exit code: `0`

Expected final decision:

```text
TRADER_IC_000_AUDIT_ENABLEMENT_PASS
```

Primary outputs:

- `00_identity/candidate_identity.json`
- `01_primary_execution/certification_result.json`
- `03_clean_room/run_001/certification_result.json`
- `03_clean_room/run_002/certification_result.json`
- `04_comparison/normalized_comparison.json`
- `06_final/final_reconciliation.json`
- `07_manifests/evidence_manifest.json`
