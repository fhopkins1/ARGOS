from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.full_suite_failure_error_closure import execute_eoej_certification  # noqa: E402


EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "EO-EJ_Evidence"

ARTIFACTS = {
    "eoej_candidate_identity.json": "candidate_identity",
    "eoej_authoritative_test_denominator.json": "authoritative_test_denominator",
    "eoej_collection_results.json": "collection_results",
    "eoej_baseline_full_suite_results.json": "baseline_full_suite_results",
    "eoej_adverse_test_architecture_inventory.json": "adverse_test_architecture_inventory",
    "eoej_failure_inventory.json": "failure_inventory",
    "eoej_error_inventory.json": "error_inventory",
    "eoej_root_cause_taxonomy.json": "root_cause_taxonomy",
    "eoej_failure_cascade_analysis.json": "failure_cascade_analysis",
    "eoej_collection_defect_closure.json": "collection_defect_closure",
    "eoej_stale_expectation_review.json": "stale_expectation_review",
    "eoej_production_defect_closure.json": "production_defect_closure",
    "eoej_fixture_defect_closure.json": "fixture_defect_closure",
    "eoej_setup_teardown_closure.json": "setup_teardown_closure",
    "eoej_global_state_isolation.json": "global_state_isolation",
    "eoej_environment_isolation.json": "environment_isolation",
    "eoej_persistence_isolation.json": "persistence_isolation",
    "eoej_port_network_closure.json": "port_network_closure",
    "eoej_subprocess_closure.json": "subprocess_closure",
    "eoej_thread_async_closure.json": "thread_async_closure",
    "eoej_order_dependence_results.json": "order_dependence_results",
    "eoej_nondeterminism_results.json": "nondeterminism_results",
    "eoej_timeout_contributor_closure.json": "timeout_contributor_closure",
    "eoej_skip_xfail_review.json": "skip_xfail_review",
    "eoej_test_retirement_inventory.json": "test_retirement_inventory",
    "eoej_targeted_retest_results.json": "targeted_retest_results",
    "eoej_segment_results.json": "segment_results",
    "eoej_complete_verification_run.json": "complete_verification_run",
    "eoej_result_accounting.json": "result_accounting",
    "eoej_failure_closure_matrix.json": "failure_closure_matrix",
    "eoej_static_assurance.json": "static_assurance",
    "eoej_test_results.json": "test_results",
    "eoej_certification.json": "certification",
}


def main() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    payload = execute_eoej_certification(commit, repo_root=REPOSITORY_ROOT)
    for filename, key in ARTIFACTS.items():
        write(EVIDENCE_ROOT / filename, payload[key])
    write(
        EVIDENCE_ROOT / "eoej_manifest.json",
        {
            "repositoryCommitAtGeneration": commit,
            "gitStatusAtGeneration": git("status", "--short"),
            "verdict": payload["certification"]["verdict"],
            "artifacts": tuple(file_record(path) for path in sorted(EVIDENCE_ROOT.glob("*.json")) if path.name != "eoej_manifest.json"),
        },
    )


def write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def file_record(path: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(REPOSITORY_ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def git(*args: str) -> str:
    result = subprocess.run(("git", *args), cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip()


if __name__ == "__main__":
    main()
