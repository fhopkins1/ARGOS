# CIC-01, CIC-02, and CIC-03 Revision Report

## Summary

This revision adds a canonical CIC-01 candidate-integrity contract, binds CIC-02 recovery foundation outputs to that contract, and moves CIC-03 CSS execution from logical subsystem names into six physically separate subsystem packages.

## CIC-01 Candidate Contract

The CIC-01 contract is implemented in `src/argos/candidate_integrity.py`.

Identity-defining fields include repository identifier, Git object format, full repository commit, commit tree hash, parent commits, tracked-state digest, staged-index digest, relevant-untracked digest, submodule digest, Git LFS pointer digest, candidate snapshot format version, identity schema version, implementation version, candidate snapshot digest, and certification input lock digest.

Volatile metadata such as timestamps and local paths is excluded from canonical contract digests.

## Evidence Isolation

`generate_cic01_evidence` rejects evidence output paths inside the candidate worktree. The deterministic fixture tests generate evidence in an external temporary directory and prove the candidate remains unchanged after evidence generation.

## CIC-02 Rebinding

`src/argos/control_panel/certification_recovery_foundation.py` now validates the CIC-01 candidate contract, records the contract digest, issues immutable CR-7, CR-10, and CIC-02 verdict records, rejects mutable-summary substitution, and validates mixed-candidate package agreement.

CIC-02 remains fail-closed when no valid CIC-01 contract is supplied.

## CIC-03 Physical CSS Separation

The six CSS subsystems now have physical packages under `src/argos/css/`:

- `css001_orchestration`
- `css002_lifecycle_triggers`
- `css003_verifier_framework`
- `css004_repository_truth`
- `css005_governance_interface`
- `css006_drift_interface`

Each package exposes its own contract, implementation, version, evidence schema, evidence generator helper, failure-code namespace, and entry point. The top-level `css_separation.py` module now acts as a compatibility coordinator that invokes those public subsystem entry points.

## Current Candidate Limitation

The current workspace is not a clean certification candidate because pre-existing IFVA evidence files are modified and untracked. CIC-01 correctly rejects this workspace for certification evidence generation with tracked, index, and relevant-untracked failure codes.

The clean-candidate acceptance behavior is demonstrated through deterministic temporary Git fixtures in `Tests/test_cic01_candidate_integrity.py`.
