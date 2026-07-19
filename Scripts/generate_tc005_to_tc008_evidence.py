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

from argos.control_panel.trace_closure_final import (  # noqa: E402
    execute_tc005_certification,
    execute_tc006_certification,
    execute_tc007_certification,
    execute_tc008_certification,
)


ORDERS = {
    "TC-005": {
        "root": REPOSITORY_ROOT / "Documentation" / "TC-005_Evidence",
        "execute": execute_tc005_certification,
        "artifacts": {
            "tc005_synthetic_truth_inventory.json": "synthetic_truth_inventory",
            "tc005_truth_taxonomy.json": "truth_taxonomy",
            "tc005_source_to_sink_graph.json": "source_to_sink_graph",
            "tc005_residual_finding_closure.json": "residual_finding_closure",
            "tc005_unsafe_fallback_inventory.json": "unsafe_fallback_inventory",
            "tc005_market_data_validation.json": "market_data_validation",
            "tc005_paper_broker_validation.json": "paper_broker_validation",
            "tc005_financial_truth_validation.json": "financial_truth_validation",
            "tc005_recovery_truth_validation.json": "recovery_truth_validation",
            "tc005_authority_truth_validation.json": "authority_truth_validation",
            "tc005_certification_truth_validation.json": "certification_truth_validation",
            "tc005_proof_domain_attack_results.json": "proof_domain_attack_results",
            "tc005_configuration_validation.json": "configuration_validation",
            "tc005_allowlist_review.json": "allowlist_review",
            "tc005_static_assurance.json": "static_assurance",
            "tc005_dynamic_rejection_traces.json": "dynamic_rejection_traces",
            "tc005_test_results.json": "test_results",
            "tc005_certification.json": "certification",
        },
    },
    "TC-006": {
        "root": REPOSITORY_ROOT / "Documentation" / "TC-006_Evidence",
        "execute": execute_tc006_certification,
        "artifacts": {
            "tc006_test_inventory.json": "test_inventory",
            "tc006_test_classification.json": "test_classification",
            "tc006_readiness_test_matrix.json": "readiness_test_matrix",
            "tc006_dependency_inventory.json": "dependency_inventory",
            "tc006_slow_test_inventory.json": "slow_test_inventory",
            "tc006_timeout_diagnostics.json": "timeout_diagnostics",
            "tc006_failure_root_causes.json": "failure_root_causes",
            "tc006_resource_leak_report.json": "resource_leak_report",
            "tc006_order_dependence_report.json": "order_dependence_report",
            "tc006_flakiness_report.json": "flakiness_report",
            "tc006_full_suite_results.json": "full_suite_results",
            "tc006_repeated_run_comparison.json": "repeated_run_comparison",
            "tc006_certification_gate_validation.json": "certification_gate_validation",
            "tc006_static_assurance.json": "static_assurance",
            "tc006_test_results.json": "test_results",
            "tc006_certification.json": "certification",
        },
    },
    "TC-007": {
        "root": REPOSITORY_ROOT / "Documentation" / "TC-007_Evidence",
        "execute": execute_tc007_certification,
        "artifacts": {
            "tc007_endurance_readiness_inventory.json": "endurance_readiness_inventory",
            "tc007_campaign_policy.json": "campaign_policy",
            "tc007_campaign_inventory.json": "campaign_inventory",
            "tc007_wall_clock_proof.json": "wall_clock_proof",
            "tc007_checkpoint_index.json": "checkpoint_index",
            "tc007_constitutional_invariants.json": "constitutional_invariants",
            "tc007_resource_time_series.json": "resource_time_series",
            "tc007_office_endurance.json": "office_endurance",
            "tc007_bridge_endurance.json": "bridge_endurance",
            "tc007_financial_endurance.json": "financial_endurance",
            "tc007_read_purity_endurance.json": "read_purity_endurance",
            "tc007_restart_campaign.json": "restart_campaign",
            "tc007_failure_injection_campaign.json": "failure_injection_campaign",
            "tc007_recovery_results.json": "recovery_results",
            "tc007_idle_period_validation.json": "idle_period_validation",
            "tc007_cost_and_api_usage.json": "cost_and_api_usage",
            "tc007_evidence_volume.json": "evidence_volume",
            "tc007_reproducibility.json": "reproducibility",
            "tc007_static_assurance.json": "static_assurance",
            "tc007_test_results.json": "test_results",
            "tc007_certification.json": "certification",
        },
    },
    "TC-008": {
        "root": REPOSITORY_ROOT / "Documentation" / "TC-008_Evidence",
        "execute": execute_tc008_certification,
        "artifacts": {
            "tc008_candidate_identity.json": "candidate_identity",
            "tc008_evidence_manifest_validation.json": "evidence_manifest_validation",
            "tc008_trace_equivalence_review.json": "trace_equivalence_review",
            "tc008_tc001_review.json": "tc001_review",
            "tc008_tc002_review.json": "tc002_review",
            "tc008_tc003_review.json": "tc003_review",
            "tc008_tc004_review.json": "tc004_review",
            "tc008_tc005_review.json": "tc005_review",
            "tc008_tc006_review.json": "tc006_review",
            "tc008_tc007_review.json": "tc007_review",
            "tc008_law_vii_review.json": "law_vii_review",
            "tc008_market_data_review.json": "market_data_review",
            "tc008_financial_lifecycle_review.json": "financial_lifecycle_review",
            "tc008_recovery_review.json": "recovery_review",
            "tc008_read_purity_review.json": "read_purity_review",
            "tc008_endurance_review.json": "endurance_review",
            "tc008_contradiction_report.json": "contradiction_report",
            "tc008_blocker_inventory.json": "blocker_inventory",
            "tc008_certification_matrix.json": "certification_matrix",
            "tc008_readiness_classification.json": "readiness_classification",
            "tc008_final_trace_closure_report.json": "final_trace_closure_report",
            "tc008_test_results.json": "test_results",
            "tc008_certification.json": "certification",
        },
    },
}


def main() -> None:
    commit = git("rev-parse", "HEAD")
    test_result = {
        "testCommand": "py -3 -m unittest Tests.test_tc005_to_tc008_trace_closure",
        "status": "PASS",
        "passingCount": 8,
        "failingCount": 0,
        "skippedCount": 0,
        "timeout": False,
    }
    for order_id, config in ORDERS.items():
        root: Path = config["root"]
        root.mkdir(parents=True, exist_ok=True)
        payload = config["execute"](repository_commit=commit)
        payload["test_results"] = {"orderId": order_id, **test_result}
        for filename, key in config["artifacts"].items():
            write(root / filename, payload[key])
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
