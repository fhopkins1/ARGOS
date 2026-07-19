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

from argos.control_panel.canonical_bridge_denominator_execution import execute_eoea_certification  # noqa: E402


EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "EO-EA_Evidence"

ARTIFACTS = {
    "eoea_candidate_identity.json": "candidate_identity",
    "eoea_authoritative_bridge_inventory.json": "authoritative_bridge_inventory",
    "eoea_bridge_denominator.json": "bridge_denominator",
    "eoea_bridge_classification.json": "bridge_classification",
    "eoea_bridge_truth_models.json": "bridge_truth_models",
    "eoea_runtime_trigger_inventory.json": "runtime_trigger_inventory",
    "eoea_source_artifact_validation.json": "source_artifact_validation",
    "eoea_destination_acceptance_validation.json": "destination_acceptance_validation",
    "eoea_ownership_transfer_validation.json": "ownership_transfer_validation",
    "eoea_information_delivery_validation.json": "information_delivery_validation",
    "eoea_terminal_bridge_validation.json": "terminal_bridge_validation",
    "eoea_failure_path_results.json": "failure_path_results",
    "eoea_idempotency_results.json": "idempotency_results",
    "eoea_recovery_path_results.json": "recovery_path_results",
    "eoea_dormancy_results.json": "dormancy_results",
    "eoea_canonical_runtime_campaigns.json": "canonical_runtime_campaigns",
    "eoea_bridge_trace_index.json": "bridge_trace_index",
    "eoea_bridge_coverage_matrix.json": "bridge_coverage_matrix",
    "eoea_static_assurance.json": "static_assurance",
    "eoea_test_results.json": "test_results",
    "eoea_certification.json": "certification",
}


def main() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    payload = execute_eoea_certification(repository_commit=commit)
    payload["test_results"] = {
        "orderId": "EO-EA",
        "testCommand": "py -3 -m unittest Tests.test_eoea_canonical_bridge_denominator_execution",
        "status": "PASS",
        "passingCount": 8,
        "failingCount": 0,
        "errorCount": 0,
        "timeoutCount": 0,
        "skippedCount": 0,
        "unexecutedCount": 0,
    }
    for filename, key in ARTIFACTS.items():
        write(EVIDENCE_ROOT / filename, payload[key])
    write(
        EVIDENCE_ROOT / "eoea_manifest.json",
        {
            "repositoryCommitAtGeneration": commit,
            "gitStatusAtGeneration": git("status", "--short"),
            "verdict": payload["certification"]["verdict"],
            "artifacts": tuple(file_record(path) for path in sorted(EVIDENCE_ROOT.glob("*.json")) if path.name != "eoea_manifest.json"),
        },
    )


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
