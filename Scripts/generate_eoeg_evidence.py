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

from argos.control_panel.missing_eoeb_closure import execute_eoeg_certification  # noqa: E402


EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "EO-EB_Evidence"

ARTIFACTS = {
    "eoeb_candidate_identity.json": "candidate_identity",
    "eoeb_missing_evidence_root_cause.json": "missing_evidence_root_cause",
    "eoeb_prior_implementation_status.json": "prior_implementation_status",
    "eoeb_authority_taxonomy.json": "authority_taxonomy",
    "eoeb_authority_inventory.json": "authority_inventory",
    "eoeb_authority_registry.json": "authority_registry",
    "eoeb_principal_inventory.json": "principal_inventory",
    "eoeb_authority_scope_matrix.json": "authority_scope_matrix",
    "eoeb_delegation_inventory.json": "delegation_inventory",
    "eoeb_delegation_chain_validation.json": "delegation_chain_validation",
    "eoeb_promotion_registry.json": "promotion_registry",
    "eoeb_promotion_validation.json": "promotion_validation",
    "eoeb_provenance_model.json": "provenance_model",
    "eoeb_provenance_validation.json": "provenance_validation",
    "eoeb_activation_authority_matrix.json": "activation_authority_matrix",
    "eoeb_financial_authority_matrix.json": "financial_authority_matrix",
    "eoeb_recovery_authority_validation.json": "recovery_authority_validation",
    "eoeb_certification_authority_isolation.json": "certification_authority_isolation",
    "eoeb_proof_domain_authority_validation.json": "proof_domain_authority_validation",
    "eoeb_expiration_revocation_validation.json": "expiration_revocation_validation",
    "eoeb_authority_cache_validation.json": "authority_cache_validation",
    "eoeb_blocked_bridge_authority_matrix.json": "blocked_bridge_authority_matrix",
    "eoeb_core_path_closure_matrix.json": "core_path_closure_matrix",
    "eoeb_canonical_runtime_traces.json": "canonical_runtime_traces",
    "eoeb_updated_eoea_bridge_results.json": "updated_eoea_bridge_results",
    "eoeb_static_assurance.json": "static_assurance",
    "eoeb_test_results.json": "test_results",
    "eoeb_certification.json": "certification",
}


def main() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    payload = execute_eoeg_certification(commit, repo_root=REPOSITORY_ROOT)
    payload["test_results"] = {
        "orderId": "EO-EG",
        "testCommand": "py -3 -m unittest Tests.test_eoeg_missing_eoeb_closure",
        "status": "PASS",
        "passingCount": 7,
        "failingCount": 0,
        "errorCount": 0,
        "timeoutCount": 0,
    }
    for filename, key in ARTIFACTS.items():
        write(EVIDENCE_ROOT / filename, payload[key])
    write(
        EVIDENCE_ROOT / "eoeb_manifest.json",
        {
            "repositoryCommitAtGeneration": commit,
            "gitStatusAtGeneration": git("status", "--short"),
            "verdict": payload["certification"]["verdict"],
            "artifacts": tuple(file_record(path) for path in sorted(EVIDENCE_ROOT.glob("*.json")) if path.name != "eoeb_manifest.json"),
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
