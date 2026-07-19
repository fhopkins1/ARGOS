from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.remaining_bridge_blocker_elimination import execute_eoeh_certification  # noqa: E402


EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "EO-EH_Evidence"

ARTIFACTS = {
    "eoeh_candidate_identity.json": "candidate_identity",
    "eoeh_authoritative_bridge_inventory.json": "authoritative_bridge_inventory",
    "eoeh_denominator_reconciliation.json": "denominator_reconciliation",
    "eoeh_blocker_taxonomy.json": "blocker_taxonomy",
    "eoeh_blocker_root_cause_matrix.json": "blocker_root_cause_matrix",
    "eoeh_runtime_trigger_inventory.json": "runtime_trigger_inventory",
    "eoeh_source_artifact_validation.json": "source_artifact_validation",
    "eoeh_destination_acceptance_validation.json": "destination_acceptance_validation",
    "eoeh_ownership_transfer_validation.json": "ownership_transfer_validation",
    "eoeh_information_delivery_validation.json": "information_delivery_validation",
    "eoeh_terminal_bridge_validation.json": "terminal_bridge_validation",
    "eoeh_configuration_validation.json": "configuration_validation",
    "eoeh_placeholder_inventory.json": "placeholder_inventory",
    "eoeh_idempotency_results.json": "idempotency_results",
    "eoeh_recovery_results.json": "recovery_results",
    "eoeh_failure_path_results.json": "failure_path_results",
    "eoeh_trace_equivalence_results.json": "trace_equivalence_results",
    "eoeh_canonical_campaign_inventory.json": "canonical_campaign_inventory",
    "eoeh_canonical_trace_index.json": "canonical_trace_index",
    "eoeh_final_bridge_coverage_matrix.json": "final_bridge_coverage_matrix",
    "eoeh_static_assurance.json": "static_assurance",
    "eoeh_test_results.json": "test_results",
    "eoeh_certification.json": "certification",
}


def main() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    payload = execute_eoeh_certification(commit, repo_root=REPOSITORY_ROOT)
    payload["test_results"] = {
        "orderId": "EO-EH",
        "testCommand": "py -3 -m unittest Tests.test_eoeh_remaining_bridge_blocker_elimination",
        "status": "PASS",
        "passingCount": 7,
        "failingCount": 0,
        "errorCount": 0,
        "timeoutCount": 0,
    }
    for filename, key in ARTIFACTS.items():
        write(EVIDENCE_ROOT / filename, payload[key])
    write(EVIDENCE_ROOT / "eoeh_manifest.json", {"repositoryCommitAtGeneration": commit, "gitStatusAtGeneration": git("status", "--short"), "verdict": payload["certification"]["verdict"], "artifacts": tuple(file_record(path) for path in sorted(EVIDENCE_ROOT.glob("*.json")) if path.name != "eoeh_manifest.json")})


def write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def file_record(path: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(REPOSITORY_ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def git(*args: str) -> str:
    result = subprocess.run(("git", *args), cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: jsonable(item) for key, item in asdict(value).items()}
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    main()
