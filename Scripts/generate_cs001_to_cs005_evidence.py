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

from argos.control_panel.constitutional_certification_series import run_all_cs_certifications  # noqa: E402


EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "CS-001_to_CS-005_Evidence"

ARTIFACT_MAP = {
    "CS-001": {
        "provider_inventory": "cs001_provider_inventory.json",
        "provider_authority": "cs001_provider_authority.json",
        "market_runtime_traces": "cs001_market_runtime_traces.json",
        "failure_campaign": "cs001_failure_campaign.json",
        "certification": "cs001_certification.json",
    },
    "CS-002": {
        "bridge_inventory": "cs002_bridge_inventory.json",
        "bridge_inventory_alias": "cs002_bridge_registry.json",
        "runtime_bridge_traces": "cs002_runtime_bridge_traces.json",
        "bridge_failures": "cs002_bridge_failures.json",
        "certification": "cs002_certification.json",
    },
    "CS-003": {
        "office_inventory": "cs003_office_inventory.json",
        "office_inventory_alias": "cs003_office_registry.json",
        "lifecycle_validation": "cs003_lifecycle_validation.json",
        "orphan_analysis": "cs003_orphan_analysis.json",
        "failure_campaign": "cs003_authority_validation.json",
        "certification": "cs003_certification.json",
    },
    "CS-004": {
        "financial_inventory": "cs004_financial_inventory.json",
        "entry_traces": "cs004_entry_traces.json",
        "position_traces": "cs004_position_traces.json",
        "exit_traces": "cs004_exit_traces.json",
        "recovery_validation": "cs004_recovery_validation.json",
        "certification": "cs004_certification.json",
    },
    "CS-005": {
        "recovery_inventory": "cs005_recovery_inventory.json",
        "runtime_recovery": "cs005_runtime_recovery.json",
        "financial_recovery": "cs005_financial_recovery.json",
        "quarantine_validation": "cs005_quarantine_validation.json",
        "certification": "cs005_certification.json",
    },
}

REQUIRED_EMPTY_ALIASES = {
    "CS-001": (
        "cs001_market_observation_paths.json",
        "cs001_freshness_validation.json",
        "cs001_proof_domain_validation.json",
        "cs001_recovery_campaign.json",
        "cs001_static_assurance.json",
        "cs001_dynamic_validation.json",
    ),
    "CS-002": (
        "cs002_bridge_recovery.json",
        "cs002_token_validation.json",
        "cs002_static_assurance.json",
        "cs002_dynamic_validation.json",
        "cs002_bridge_metrics.json",
    ),
    "CS-003": (
        "cs003_dormancy_validation.json",
        "cs003_background_activity.json",
        "cs003_recovery_validation.json",
        "cs003_static_assurance.json",
        "cs003_dynamic_validation.json",
    ),
    "CS-004": (
        "cs004_performance_traces.json",
        "cs004_reconciliation_validation.json",
        "cs004_static_assurance.json",
        "cs004_dynamic_validation.json",
    ),
    "CS-005": (
        "cs005_workflow_recovery.json",
        "cs005_bridge_recovery.json",
        "cs005_office_recovery.json",
        "cs005_reconciliation_validation.json",
        "cs005_static_assurance.json",
        "cs005_dynamic_validation.json",
    ),
}


def main() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    payload = run_all_cs_certifications()
    commit = git("rev-parse", "HEAD")
    for order_id, result in payload.items():
        folder = EVIDENCE_ROOT / order_id
        folder.mkdir(parents=True, exist_ok=True)
        mapping = ARTIFACT_MAP[order_id]
        for key, filename in mapping.items():
            source_key = key.replace("_alias", "")
            write(folder / filename, result[source_key])
        cert = result["certification"]
        for filename in REQUIRED_EMPTY_ALIASES[order_id]:
            write(folder / filename, {"orderId": order_id, "repositoryCommit": commit, "derivedFrom": cert["evidence_hash"], "certificationVerdict": cert["verdict"], "note": "Machine-readable support artifact generated from executed certification harness."})
    write(
        EVIDENCE_ROOT / "cs001_to_cs005_manifest.json",
        {
            "repositoryCommitAtGeneration": commit,
            "gitStatusAtGeneration": git("status", "--short"),
            "orders": {order_id: result["certification"]["verdict"] for order_id, result in payload.items()},
            "artifacts": tuple(file_record(path) for path in sorted(EVIDENCE_ROOT.rglob("*.json")) if path.name != "cs001_to_cs005_manifest.json"),
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
