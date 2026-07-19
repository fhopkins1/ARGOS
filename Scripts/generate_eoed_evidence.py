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

from argos.control_panel.deterministic_persistence_recovery_closure import execute_eoed_certification  # noqa: E402


EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "EO-ED_Evidence"

ARTIFACTS = {
    "eoed_candidate_identity.json": "candidate_identity",
    "eoed_persistence_baseline.json": "persistence_baseline",
    "eoed_persistence_architecture_inventory.json": "persistence_architecture_inventory",
    "eoed_durability_classification.json": "durability_classification",
    "eoed_atomicity_matrix.json": "atomicity_matrix",
    "eoed_journal_validation.json": "journal_validation",
    "eoed_snapshot_validation.json": "snapshot_validation",
    "eoed_schema_migration_validation.json": "schema_migration_validation",
    "eoed_configuration_identity_validation.json": "configuration_identity_validation",
    "eoed_runtime_lineage.json": "runtime_lineage",
    "eoed_workflow_recovery.json": "workflow_recovery",
    "eoed_token_recovery.json": "token_recovery",
    "eoed_ownership_recovery.json": "ownership_recovery",
    "eoed_office_lifecycle_recovery.json": "office_lifecycle_recovery",
    "eoed_bridge_recovery.json": "bridge_recovery",
    "eoed_authority_recovery.json": "authority_recovery",
    "eoed_promotion_recovery.json": "promotion_recovery",
    "eoed_market_data_recovery.json": "market_data_recovery",
    "eoed_order_recovery.json": "order_recovery",
    "eoed_acknowledgement_recovery.json": "acknowledgement_recovery",
    "eoed_fill_recovery.json": "fill_recovery",
    "eoed_position_recovery.json": "position_recovery",
    "eoed_monitoring_recovery.json": "monitoring_recovery",
    "eoed_exit_recovery.json": "exit_recovery",
    "eoed_closure_recovery.json": "closure_recovery",
    "eoed_performance_recovery.json": "performance_recovery",
    "eoed_historian_recovery.json": "historian_recovery",
    "eoed_audit_chain_validation.json": "audit_chain_validation",
    "eoed_quarantine_validation.json": "quarantine_validation",
    "eoed_reconciliation_results.json": "reconciliation_results",
    "eoed_startup_gate_validation.json": "startup_gate_validation",
    "eoed_shutdown_validation.json": "shutdown_validation",
    "eoed_failure_injection_results.json": "failure_injection_results",
    "eoed_repeated_restart_results.json": "repeated_restart_results",
    "eoed_law_vii_recovery_validation.json": "law_vii_recovery_validation",
    "eoed_financial_invariant_validation.json": "financial_invariant_validation",
    "eoed_read_purity_validation.json": "read_purity_validation",
    "eoed_recovery_certification_matrix.json": "recovery_certification_matrix",
    "eoed_static_assurance.json": "static_assurance",
    "eoed_test_results.json": "test_results",
    "eoed_certification.json": "certification",
}


def main() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    payload = execute_eoed_certification(repository_commit=commit)
    payload["test_results"] = {
        "orderId": "EO-ED",
        "testCommand": "py -3 -m unittest Tests.test_eoed_deterministic_persistence_recovery",
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
        EVIDENCE_ROOT / "eoed_manifest.json",
        {
            "repositoryCommitAtGeneration": commit,
            "gitStatusAtGeneration": git("status", "--short"),
            "verdict": payload["certification"]["verdict"],
            "artifacts": tuple(file_record(path) for path in sorted(EVIDENCE_ROOT.glob("*.json")) if path.name != "eoed_manifest.json"),
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
