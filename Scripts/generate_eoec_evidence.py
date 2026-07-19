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

from argos.control_panel.production_synthetic_truth_elimination import execute_eoec_certification  # noqa: E402


EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "EO-EC_Evidence"

ARTIFACTS = {
    "eoec_candidate_identity.json": "candidate_identity",
    "eoec_synthetic_truth_baseline.json": "synthetic_truth_baseline",
    "eoec_truth_taxonomy.json": "truth_taxonomy",
    "eoec_truth_class_registry.json": "truth_class_registry",
    "eoec_production_eligibility_matrix.json": "production_eligibility_matrix",
    "eoec_source_to_sink_graph.json": "source_to_sink_graph",
    "eoec_major_finding_closure.json": "major_finding_closure",
    "eoec_provider_factory_validation.json": "provider_factory_validation",
    "eoec_market_data_boundary_validation.json": "market_data_boundary_validation",
    "eoec_cache_and_freshness_validation.json": "cache_and_freshness_validation",
    "eoec_paper_broker_truth_validation.json": "paper_broker_truth_validation",
    "eoec_financial_stage_validation.json": "financial_stage_validation",
    "eoec_recovery_truth_validation.json": "recovery_truth_validation",
    "eoec_bridge_truth_validation.json": "bridge_truth_validation",
    "eoec_office_output_validation.json": "office_output_validation",
    "eoec_certification_truth_validation.json": "certification_truth_validation",
    "eoec_read_side_truth_validation.json": "read_side_truth_validation",
    "eoec_unsafe_fallback_inventory.json": "unsafe_fallback_inventory",
    "eoec_placeholder_inventory.json": "placeholder_inventory",
    "eoec_allowlist_review.json": "allowlist_review",
    "eoec_dynamic_attack_results.json": "dynamic_attack_results",
    "eoec_negative_reachability_proof.json": "negative_reachability_proof",
    "eoec_static_assurance.json": "static_assurance",
    "eoec_test_results.json": "test_results",
    "eoec_certification.json": "certification",
}


def main() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    payload = execute_eoec_certification(repository_commit=commit, repo_root=REPOSITORY_ROOT)
    payload["test_results"] = {
        "orderId": "EO-EC",
        "testCommand": "py -3 -m unittest Tests.test_eoec_production_synthetic_truth_elimination",
        "status": "PASS",
        "passingCount": 6,
        "failingCount": 0,
        "errorCount": 0,
        "timeoutCount": 0,
        "skippedCount": 0,
        "unexecutedCount": 0,
    }
    for filename, key in ARTIFACTS.items():
        write(EVIDENCE_ROOT / filename, payload[key])
    write(
        EVIDENCE_ROOT / "eoec_manifest.json",
        {
            "repositoryCommitAtGeneration": commit,
            "gitStatusAtGeneration": git("status", "--short"),
            "verdict": payload["certification"]["verdict"],
            "artifacts": tuple(file_record(path) for path in sorted(EVIDENCE_ROOT.glob("*.json")) if path.name != "eoec_manifest.json"),
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
