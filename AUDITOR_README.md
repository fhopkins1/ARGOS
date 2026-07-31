# Performance Truth Independent Runtime Reproduction

This guide is the active auditor entrypoint for `PERFORMANCE-TRUTH-ECS003-AUDIT-004A`.
It is specific to the Performance Truth Office.

## Supported Environment

- Windows, macOS, or Linux with a writable filesystem.
- Python 3.11 or newer.
- No submitted evidence package is required or accepted as proof.
- No Git metadata is required inside the candidate ZIP.
- All required inputs are resolved from the extracted repository package by
  repository-relative path.
- Absolute developer-local paths, user-profile paths, parent traversal, hidden
  local files, and network retrieval are rejected.

## Canonical Command

```text
python audit_reproduce.py --candidate <repository-package.zip> --output <empty-output-directory>
```

The output directory must be new or empty. The command exits nonzero if the
candidate ZIP is missing, the output directory is not empty, extraction fails,
runtime validation fails, zero runtime tests are collected or executed, any
controlling execution fails, any phase lacks required evidence, or any blocking
finding is produced.

## Generated Outputs

The reproduction output includes:

- `candidate_hash.json`
- `environment.json`
- `repository_inventory.json`
- `performance_truth_discovery.json`
- `command_manifest.json`
- `test_inventory.json`
- `test_results.json`
- `behavioral_results.json`
- `replay_results.json`
- `fail_closed_results.json`
- `mutation_results.json`
- `stress_results.json`
- `findings.json`
- `execution_summary.json`
- `generated_artifact_inventory.json`
- `output_hash_manifest.json`
- `stdout/` and `stderr/` command logs
- `transcripts/` command records

## Exit Codes

- `0`: execution completed and all required validations passed.
- `2`: command-line or filesystem input failure.
- `3`: candidate extraction or repository discovery failure.
- `4`: build, test, runtime, replay, fail-closed, mutation, or stress failure.

## Repeat Runs

Use a new empty output directory for each run:

```text
python audit_reproduce.py --candidate ARGOS.zip --output audit-run-001
python audit_reproduce.py --candidate ARGOS.zip --output audit-run-002
```

The entrypoint records the candidate ZIP hash and writes all runtime evidence
to the requested output directory. It does not issue an ECS-003 certification
decision and does not use historical reports as proof. PASS-classified phase
evidence is emitted only when its controlling command completed successfully
and the raw command output exists in the same run output directory.
