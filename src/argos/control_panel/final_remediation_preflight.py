"""EO-EK through EO-EO gated certification evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

from argos.foundation.contracts import utc_timestamp


FINAL_REMEDIATION_PREFLIGHT_VERSION = "EO-EK-EO-EO.1"


@dataclass(frozen=True)
class FinalRemediationOrder:
    order_id: str
    evidence_dir: str
    artifact_names: tuple[str, ...]
    required_pass_orders: tuple[str, ...]
    minimum_duration_seconds: int
    blocked_action: str
    readiness_domain: str


EOEK_ARTIFACTS = (
    "eoek_candidate_identity.json",
    "eoek_entry_gate.json",
    "eoek_authoritative_test_denominator.json",
    "eoek_campaign_plan.json",
    "eoek_campaign_environment_matrix.json",
    "eoek_campaign_a_results.json",
    "eoek_campaign_b_results.json",
    "eoek_campaign_c_results.json",
    "eoek_campaign_d_results.json",
    "eoek_campaign_e_results.json",
    "eoek_campaign_f_results.json",
    "eoek_collection_equivalence.json",
    "eoek_result_equivalence.json",
    "eoek_constitutional_output_equivalence.json",
    "eoek_state_hash_model.json",
    "eoek_state_hash_results.json",
    "eoek_pre_campaign_cleanliness.json",
    "eoek_post_campaign_cleanliness.json",
    "eoek_process_leak_results.json",
    "eoek_thread_leak_results.json",
    "eoek_async_leak_results.json",
    "eoek_socket_leak_results.json",
    "eoek_file_handle_leak_results.json",
    "eoek_temporary_state_results.json",
    "eoek_memory_stability.json",
    "eoek_cpu_duration_stability.json",
    "eoek_randomness_control.json",
    "eoek_clock_control.json",
    "eoek_order_dependence_analysis.json",
    "eoek_flakiness_analysis.json",
    "eoek_test_order_manifests.json",
    "eoek_campaign_result_matrix.json",
    "eoek_campaign_accounting.json",
    "eoek_performance_bounds.json",
    "eoek_static_assurance.json",
    "eoek_infrastructure_test_results.json",
    "eoek_certification.json",
)

EOEL_ARTIFACTS = (
    "eoel_candidate_identity.json",
    "eoel_entry_gate.json",
    "eoel_campaign_definition.json",
    "eoel_campaign_configuration.json",
    "eoel_workload_plan.json",
    "eoel_thresholds.json",
    "eoel_pre_campaign_cleanliness.json",
    "eoel_startup_validation.json",
    "eoel_duration_proof.json",
    "eoel_telemetry_manifest.json",
    "eoel_hash_chain_manifest.json",
    "eoel_checkpoint_index.json",
    "eoel_law_vii_monitoring.json",
    "eoel_token_monitoring.json",
    "eoel_office_lifecycle_monitoring.json",
    "eoel_bridge_monitoring.json",
    "eoel_authority_provenance_monitoring.json",
    "eoel_synthetic_truth_monitoring.json",
    "eoel_financial_lifecycle_monitoring.json",
    "eoel_position_integrity_monitoring.json",
    "eoel_performance_truth_monitoring.json",
    "eoel_persistence_monitoring.json",
    "eoel_recovery_readiness_monitoring.json",
    "eoel_read_purity_monitoring.json",
    "eoel_proof_domain_monitoring.json",
    "eoel_cost_monitoring.json",
    "eoel_queue_monitoring.json",
    "eoel_runtime_liveness.json",
    "eoel_deadlock_stall_monitoring.json",
    "eoel_process_monitoring.json",
    "eoel_thread_async_monitoring.json",
    "eoel_memory_monitoring.json",
    "eoel_cpu_monitoring.json",
    "eoel_file_handle_monitoring.json",
    "eoel_socket_monitoring.json",
    "eoel_disk_evidence_growth.json",
    "eoel_resource_trend_analysis.json",
    "eoel_failure_injection_results.json",
    "eoel_idle_period_validation.json",
    "eoel_warning_inventory.json",
    "eoel_abort_inventory.json",
    "eoel_campaign_metrics.json",
    "eoel_graceful_shutdown.json",
    "eoel_post_shutdown_validation.json",
    "eoel_post_campaign_restart_validation.json",
    "eoel_evidence_continuity.json",
    "eoel_infrastructure_test_results.json",
    "eoel_certification.json",
)

EOEM_ARTIFACTS = (
    "eoem_candidate_identity.json",
    "eoem_entry_gate.json",
    "eoem_campaign_a_identity_validation.json",
    "eoem_candidate_equivalence.json",
    "eoem_environment_variance_policy.json",
    "eoem_starting_state_equivalence.json",
    "eoem_campaign_b_definition.json",
    "eoem_campaign_b_configuration.json",
    "eoem_campaign_b_workload_plan.json",
    "eoem_doctrine_equivalence.json",
    "eoem_threshold_equivalence.json",
    "eoem_telemetry_equivalence.json",
    "eoem_checkpoint_equivalence.json",
    "eoem_pre_campaign_cleanliness.json",
    "eoem_startup_validation.json",
    "eoem_duration_proof.json",
    "eoem_campaign_b_telemetry_manifest.json",
    "eoem_campaign_b_hash_chain_manifest.json",
    "eoem_campaign_b_checkpoint_index.json",
    "eoem_campaign_b_law_vii_monitoring.json",
    "eoem_campaign_b_token_monitoring.json",
    "eoem_campaign_b_office_lifecycle.json",
    "eoem_campaign_b_bridge_monitoring.json",
    "eoem_campaign_b_authority_provenance.json",
    "eoem_campaign_b_synthetic_truth.json",
    "eoem_campaign_b_financial_lifecycle.json",
    "eoem_campaign_b_position_integrity.json",
    "eoem_campaign_b_performance_truth.json",
    "eoem_campaign_b_persistence.json",
    "eoem_campaign_b_recovery_readiness.json",
    "eoem_campaign_b_read_purity.json",
    "eoem_campaign_b_proof_domain.json",
    "eoem_campaign_b_cost.json",
    "eoem_campaign_b_queues.json",
    "eoem_campaign_b_liveness.json",
    "eoem_campaign_b_deadlock_stalls.json",
    "eoem_campaign_b_processes.json",
    "eoem_campaign_b_threads_async.json",
    "eoem_campaign_b_memory.json",
    "eoem_campaign_b_cpu.json",
    "eoem_campaign_b_file_handles.json",
    "eoem_campaign_b_sockets.json",
    "eoem_campaign_b_disk_growth.json",
    "eoem_campaign_b_failure_injections.json",
    "eoem_campaign_b_idle_validation.json",
    "eoem_campaign_b_warnings.json",
    "eoem_campaign_b_aborts.json",
    "eoem_campaign_b_metrics.json",
    "eoem_campaign_b_shutdown.json",
    "eoem_campaign_b_post_shutdown.json",
    "eoem_normalization_model.json",
    "eoem_comparison_classification.json",
    "eoem_difference_inventory.json",
    "eoem_reproducibility_scorecard.json",
    "eoem_constitutional_reproducibility.json",
    "eoem_bridge_reproducibility.json",
    "eoem_financial_reproducibility.json",
    "eoem_persistence_reproducibility.json",
    "eoem_recovery_reproducibility.json",
    "eoem_resource_reproducibility.json",
    "eoem_queue_reproducibility.json",
    "eoem_cost_reproducibility.json",
    "eoem_shutdown_reproducibility.json",
    "eoem_statistical_trend_comparison.json",
    "eoem_evidence_continuity.json",
    "eoem_infrastructure_test_results.json",
    "eoem_certification.json",
)

EOEN_ARTIFACTS = (
    "eoen_candidate_identity.json",
    "eoen_duration_proof.json",
    "eoen_scheduler_stability.json",
    "eoen_timer_stability.json",
    "eoen_memory_trends.json",
    "eoen_cpu_trends.json",
    "eoen_queue_trends.json",
    "eoen_bridge_trends.json",
    "eoen_office_activity.json",
    "eoen_token_integrity.json",
    "eoen_authority_monitoring.json",
    "eoen_provenance_monitoring.json",
    "eoen_truth_monitoring.json",
    "eoen_financial_monitoring.json",
    "eoen_persistence_monitoring.json",
    "eoen_recovery_readiness.json",
    "eoen_cost_monitoring.json",
    "eoen_idle_validation.json",
    "eoen_checkpoint_index.json",
    "eoen_hash_chain.json",
    "eoen_shutdown.json",
    "eoen_restart_validation.json",
    "eoen_morning_state_reconciliation.json",
    "eoen_level2_comparison.json",
    "eoen_resource_statistics.json",
    "eoen_campaign_metrics.json",
    "eoen_certification.json",
)

EOEO_ARTIFACTS = (
    "eoeo_candidate_identity.json",
    "eoeo_repository_manifest.json",
    "eoeo_evidence_manifest.json",
    "eoeo_denominator_reconciliation.json",
    "eoeo_cross_certification_matrix.json",
    "eoeo_contradiction_report.json",
    "eoeo_operational_scorecard.json",
    "eoeo_final_readiness_report.md",
    "eoeo_auditor_guide.md",
    "eoeo_operator_guide.md",
    "eoeo_developer_guide.md",
    "eoeo_certification.json",
)

FINAL_REMEDIATION_ORDERS: dict[str, FinalRemediationOrder] = {
    "EO-EK": FinalRemediationOrder("EO-EK", "EO-EK_Evidence", EOEK_ARTIFACTS, ("EO-EJ",), 0, "six repeated full-suite campaigns", "Repeated deterministic certification"),
    "EO-EL": FinalRemediationOrder("EO-EL", "EO-EL_Evidence", EOEL_ARTIFACTS, ("EO-EJ", "EO-EK"), 7200, "Level 2 Campaign A", "Level 2 endurance campaign A"),
    "EO-EM": FinalRemediationOrder("EO-EM", "EO-EM_Evidence", EOEM_ARTIFACTS, ("EO-EJ", "EO-EK", "EO-EL"), 7200, "Level 2 Campaign B reproducibility", "Level 2 reproducibility"),
    "EO-EN": FinalRemediationOrder("EO-EN", "EO-EN_Evidence", EOEN_ARTIFACTS, ("EO-EJ", "EO-EK", "EO-EL", "EO-EM"), 28800, "Level 3 overnight campaign", "Level 3 endurance"),
    "EO-EO": FinalRemediationOrder("EO-EO", "EO-EO_Evidence", EOEO_ARTIFACTS, ("EO-EJ", "EO-EK", "EO-EL", "EO-EM", "EO-EN"), 0, "single-commit final paper certification packaging", "Final readiness packaging"),
}


def execute_final_remediation_preflight(
    order_id: str,
    repository_commit: str = "WORKTREE",
    *,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    root = Path(repo_root)
    order = FINAL_REMEDIATION_ORDERS[order_id]
    generated_at = utc_timestamp()
    candidate = _candidate_identity(order, repository_commit, root, generated_at)
    prerequisite_verdicts = _prerequisite_verdicts(order, root)
    blockers = tuple(
        {
            "orderId": item["orderId"],
            "requiredVerdict": "PASS",
            "observedVerdict": item["verdict"],
            "source": item["source"],
            "blockingReason": f"{item['orderId']} is required to PASS before {order.order_id} can begin {order.blocked_action}.",
        }
        for item in prerequisite_verdicts
        if item["verdict"] != "PASS"
    )
    campaign_started = False if blockers else False
    verdict = "FAIL" if blockers else "INCOMPLETE"
    certification = {
        "orderId": order.order_id,
        "schemaVersion": FINAL_REMEDIATION_PREFLIGHT_VERSION,
        "repositoryCommit": repository_commit,
        "verdict": verdict,
        "readinessClassification": _readiness_classification(order.order_id, blockers),
        "campaignStarted": campaign_started,
        "requiredDurationSeconds": order.minimum_duration_seconds,
        "observedDurationSeconds": 0,
        "entryGatePassed": not blockers,
        "entryBlockers": blockers,
        "adverseEvidencePreserved": True,
        "noDurationFabricated": True,
        "noHistoricalEvidencePromoted": True,
        "timestampUtc": generated_at,
    }
    payload: dict[str, Any] = {
        "candidate_identity": candidate,
        "entry_gate": {
            "orderId": order.order_id,
            "requiredPrerequisites": order.required_pass_orders,
            "prerequisiteVerdicts": prerequisite_verdicts,
            "passed": not blockers,
            "blockers": blockers,
            "disposition": "RUNTIME_NOT_STARTED_ENTRY_GATE_FAILED" if blockers else "READY_FOR_MANUAL_WALL_CLOCK_EXECUTION",
        },
        "certification": certification,
    }
    for artifact in order.artifact_names:
        key = artifact.rsplit(".", 1)[0]
        if artifact.endswith("_certification.json"):
            payload[key] = certification
        elif artifact.endswith("_candidate_identity.json"):
            payload[key] = candidate
        elif artifact.endswith("_entry_gate.json"):
            payload[key] = payload["entry_gate"]
        elif artifact.endswith(".md"):
            payload[key] = _markdown_artifact(order, artifact, certification, blockers)
        else:
            payload[key] = _blocked_artifact(order, artifact, candidate, blockers)
    certification["evidenceHash"] = _stable_hash({k: v for k, v in payload.items() if k != "certification"})
    if f"{order.order_id.lower().replace('-', '')}_certification" in payload:
        payload[f"{order.order_id.lower().replace('-', '')}_certification"] = certification
    return payload


def execute_eoek_preflight(repository_commit: str = "WORKTREE", *, repo_root: str | Path = ".") -> dict[str, Any]:
    return execute_final_remediation_preflight("EO-EK", repository_commit, repo_root=repo_root)


def execute_eoel_preflight(repository_commit: str = "WORKTREE", *, repo_root: str | Path = ".") -> dict[str, Any]:
    return execute_final_remediation_preflight("EO-EL", repository_commit, repo_root=repo_root)


def execute_eoem_preflight(repository_commit: str = "WORKTREE", *, repo_root: str | Path = ".") -> dict[str, Any]:
    return execute_final_remediation_preflight("EO-EM", repository_commit, repo_root=repo_root)


def execute_eoen_preflight(repository_commit: str = "WORKTREE", *, repo_root: str | Path = ".") -> dict[str, Any]:
    return execute_final_remediation_preflight("EO-EN", repository_commit, repo_root=repo_root)


def execute_eoeo_preflight(repository_commit: str = "WORKTREE", *, repo_root: str | Path = ".") -> dict[str, Any]:
    return execute_final_remediation_preflight("EO-EO", repository_commit, repo_root=repo_root)


def _candidate_identity(order: FinalRemediationOrder, repository_commit: str, repo_root: Path, generated_at: str) -> dict[str, Any]:
    return {
        "orderId": order.order_id,
        "schemaVersion": FINAL_REMEDIATION_PREFLIGHT_VERSION,
        "repositoryCommit": repository_commit,
        "branch": _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD"),
        "generatedAtUtc": generated_at,
        "python": sys.version,
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "workingTreeStatus": _git(repo_root, "status", "--short"),
        "sourceTreeHash": _tree_hash(repo_root / "src"),
        "testTreeHash": _tree_hash(repo_root / "Tests"),
    }


def _prerequisite_verdicts(order: FinalRemediationOrder, repo_root: Path) -> tuple[dict[str, str], ...]:
    return tuple(_load_order_verdict(repo_root, prerequisite) for prerequisite in order.required_pass_orders)


def _load_order_verdict(repo_root: Path, order_id: str) -> dict[str, str]:
    stem = order_id.lower().replace("-", "")
    path = repo_root / "Documentation" / f"{order_id}_Evidence" / f"{stem}_certification.json"
    if not path.exists():
        return {"orderId": order_id, "verdict": "MISSING", "source": str(path)}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"orderId": order_id, "verdict": "UNREADABLE", "source": str(path)}
    return {"orderId": order_id, "verdict": str(payload.get("verdict", "UNKNOWN")), "source": str(path)}


def _blocked_artifact(
    order: FinalRemediationOrder,
    artifact_name: str,
    candidate: dict[str, Any],
    blockers: tuple[dict[str, str], ...],
) -> dict[str, Any]:
    duration_artifact = "duration" in artifact_name or "campaign" in artifact_name
    return {
        "orderId": order.order_id,
        "artifact": artifact_name,
        "schemaVersion": FINAL_REMEDIATION_PREFLIGHT_VERSION,
        "repositoryCommit": candidate["repositoryCommit"],
        "status": "BLOCKED_BY_ENTRY_GATE" if blockers else "NOT_EXECUTED_IN_PREFLIGHT",
        "readinessDomain": order.readiness_domain,
        "blockedAction": order.blocked_action,
        "campaignStarted": False,
        "requiredDurationSeconds": order.minimum_duration_seconds if duration_artifact else 0,
        "observedDurationSeconds": 0,
        "entryBlockers": blockers,
        "adverseEvidencePreserved": True,
        "noSyntheticDurationUsed": True,
        "noRuntimeResultFabricated": True,
    }


def _markdown_artifact(
    order: FinalRemediationOrder,
    artifact_name: str,
    certification: dict[str, Any],
    blockers: tuple[dict[str, str], ...],
) -> str:
    blocker_lines = "\n".join(f"- {item['orderId']}: {item['observedVerdict']} ({item['blockingReason']})" for item in blockers)
    return (
        f"# {order.order_id} {artifact_name}\n\n"
        f"Verdict: {certification['verdict']}\n\n"
        f"Readiness classification: {certification['readinessClassification']}\n\n"
        "Entry blockers:\n"
        f"{blocker_lines or '- None recorded'}\n\n"
        "No wall-clock campaign duration or final PAPER certification was fabricated.\n"
    )


def _readiness_classification(order_id: str, blockers: tuple[dict[str, str], ...]) -> str:
    if not blockers:
        return "CONTROLLED_REMEDIATION"
    if order_id == "EO-EO":
        return "CONTROLLED REMEDIATION"
    return "NOT_CERTIFIED"


def _tree_hash(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file() and "__pycache__" not in item.parts:
            digest.update(str(item.relative_to(path)).encode("utf-8"))
            digest.update(item.read_bytes())
    return digest.hexdigest()


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, capture_output=True, check=False)
    return result.stdout.strip()
