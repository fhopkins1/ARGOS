# AUTH-IOC-001 Auditor Reproduction Guide

This package is reproduced with one package-bound command. No Git repository,
development checkout, package installation, manual `PYTHONPATH`, network access,
or prior evidence directory is required.

## Supported Environment

- Python 3.11 or newer
- Windows, Linux, or macOS with UTF-8 capable filesystem paths
- No third-party Python dependencies are required

## Environment Validation

```bash
python -m argos.authorization_independent_certify --validate-environment --output auditor_environment
```

When validating from a freshly extracted candidate, this equivalent wrapper also
works without any environment-variable setup:

```bash
python audit_reproduce.py --validate-environment --output auditor_environment
```

## Candidate Hash Verification

```bash
python - <<'PY'
import hashlib, pathlib, sys
path = pathlib.Path(sys.argv[1])
h = hashlib.sha256(path.read_bytes()).hexdigest()
print(h)
PY AUTHORIZATIONS_REPOSITORY_<candidate-id>_<timestamp>_auth-ioc001-final.zip
```

## Full Reproduction

```bash
python audit_reproduce.py --candidate "/path/to/final_repository.zip" --output "/path/to/new_empty_audit_output"
```

Equivalent module command:

```bash
python -m argos.authorization_independent_certify --candidate "/path/to/final_repository.zip" --output "/path/to/new_empty_audit_output"
```

## Expected Successful Result

- Exit code: `0`
- Final decision file:
  `06_final/independent_certification_decision.json`
- Expected decision:
  `UNCONDITIONAL_INDEPENDENT_AUTHORIZATIONS_OFFICE_CERTIFICATION_PASS`
- Primary execution output:
  `01_primary_execution/certification_result.json`
- Clean-room output:
  `02_clean_room/run_001/certification_result.json`
  `02_clean_room/run_002/certification_result.json`

Troubleshooting is limited to installing a supported Python runtime and ensuring
the candidate path and output path are valid.
