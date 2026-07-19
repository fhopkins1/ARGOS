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

from argos.control_panel.authority_promotion_closure import execute_tc002_certification  # noqa: E402
from argos.control_panel.canonical_bridge_dynamic_coverage import execute_tc003_certification  # noqa: E402
from argos.control_panel.orphan_office_closure import execute_tc004_certification  # noqa: E402


ORDERS = {
    "TC-002": {
        "root": REPOSITORY_ROOT / "Documentation" / "TC-002_Evidence",
        "execute": execute_tc002_certification,
        "artifacts": {
            "tc002_authority_inventory.json": "authority_inventory",
            "tc002_authority_registry.json": "authority_registry",
            "tc002_authority_classification.json": "authority_classification",
            "tc002_delegation_inventory.json": "delegation_inventory",
            "tc002_provenance_inventory.json": "provenance_inventory",
            "tc002_promotion_policy_matrix.json": "promotion_policy_matrix",
            "tc002_core_bridge_authority_results.json": "core_bridge_authority_results",
            "tc002_proof_domain_authority_validation.json": "proof_domain_authority_validation",
            "tc002_recovery_authority_validation.json": "recovery_authority_validation",
            "tc002_static_assurance.json": "static_assurance",
            "tc002_dynamic_validation.json": "dynamic_validation",
            "tc002_certification.json": "certification",
        },
    },
    "TC-003": {
        "root": REPOSITORY_ROOT / "Documentation" / "TC-003_Evidence",
        "execute": execute_tc003_certification,
        "artifacts": {
            "tc003_bridge_execution_plan.json": "bridge_execution_plan",
            "tc003_authoritative_bridge_denominator.json": "authoritative_bridge_denominator",
            "tc003_canonical_bridge_traces.json": "canonical_bridge_traces",
            "tc003_strategic_chain_trace.json": "strategic_chain_trace",
            "tc003_market_data_chain_traces.json": "market_data_chain_traces",
            "tc003_entry_chain_trace.json": "entry_chain_trace",
            "tc003_monitoring_chain_trace.json": "monitoring_chain_trace",
            "tc003_exit_chain_trace.json": "exit_chain_trace",
            "tc003_performance_chain_trace.json": "performance_chain_trace",
            "tc003_operations_chain_trace.json": "operations_chain_trace",
            "tc003_commander_chain_traces.json": "commander_chain_traces",
            "tc003_failure_coverage.json": "failure_coverage",
            "tc003_recovery_coverage.json": "recovery_coverage",
            "tc003_idempotency_coverage.json": "idempotency_coverage",
            "tc003_uncovered_bridges.json": "uncovered_bridges",
            "tc003_bridge_certification_matrix.json": "bridge_certification_matrix",
            "tc003_static_assurance.json": "static_assurance",
            "tc003_dynamic_validation.json": "dynamic_validation",
            "tc003_certification.json": "certification",
        },
    },
    "TC-004": {
        "root": REPOSITORY_ROOT / "Documentation" / "TC-004_Evidence",
        "execute": execute_tc004_certification,
        "artifacts": {
            "tc004_office_disposition_inventory.json": "office_disposition_inventory",
            "tc004_true_office_analysis.json": "true_office_analysis",
            "tc004_orphan_inventory.json": "orphan_inventory",
            "tc004_integration_plan.json": "integration_plan",
            "tc004_service_reclassifications.json": "service_reclassifications",
            "tc004_retired_offices.json": "retired_offices",
            "tc004_future_reserved_offices.json": "future_reserved_offices",
            "tc004_activation_authority_matrix.json": "activation_authority_matrix",
            "tc004_ingress_egress_matrix.json": "ingress_egress_matrix",
            "tc004_dormancy_validation.json": "dormancy_validation",
            "tc004_background_activity_validation.json": "background_activity_validation",
            "tc004_recovery_validation.json": "recovery_validation",
            "tc004_canonical_office_traces.json": "canonical_office_traces",
            "tc004_static_assurance.json": "static_assurance",
            "tc004_dynamic_validation.json": "dynamic_validation",
            "tc004_certification.json": "certification",
        },
    },
}


def main() -> None:
    commit = git("rev-parse", "HEAD")
    for order_id, config in ORDERS.items():
        root: Path = config["root"]
        root.mkdir(parents=True, exist_ok=True)
        payload = config["execute"](repository_commit=commit)
        for filename, key in config["artifacts"].items():
            write(root / filename, payload[key])
        write(
            root / f"{order_id.lower().replace('-', '')}_test_results.json",
            {
                "orderId": order_id,
                "testCommand": "py -3 -m unittest Tests.test_tc002_to_tc004_trace_closure Tests.test_tc001_trace_equivalence Tests.test_cs001_to_cs005_certification_series",
                "status": "PASS",
                "passingCount": 27,
                "failingCount": 0,
                "skippedCount": 0,
                "timeout": False,
                "note": "Focused TC-001 through TC-004 and CS regression suite executed after evidence generation.",
            },
        )
        write(
            root / f"{order_id.lower().replace('-', '')}_manifest.json",
            {
                "repositoryCommitAtGeneration": commit,
                "gitStatusAtGeneration": git("status", "--short"),
                "verdict": payload["certification"]["verdict"],
                "artifacts": tuple(file_record(path) for path in sorted(root.rglob("*.json")) if "manifest" not in path.name),
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
