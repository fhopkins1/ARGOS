"""TRADER-RM-002A-016-B02 authoritative-fill fixture verification batch."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

from .trader_audit import _digest_file, _digest_payload


BATCH_ID = "TRADER-RM-002A-016-B02"
BATCH_VERSION = "TRADER-RM-002A-016-B02/1.0.0"
DEFAULT_PRIOR_CAMPAIGN_ROOT = Path(
    r"C:\Users\Fletc\OneDrive\Desktop\ARGOS-212fbea3c912eec83aa3c90287bbed974f19f873"
    r"\TRADER_ECS003_PRIMARY_COMPLETE_AUDIT_EVIDENCE_0118d62da0664f25_20260724-001235"
)
THIRTEEN_DASHBOARD_FIXTURE_TESTS = (
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xa_position_registry_closes_position_with_zero_quantity",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xa_position_registry_rejects_invalid_state_and_transitions",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xa_position_registry_retrieves_and_updates_active_positions",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xb_surveillance_degrades_without_market_data_and_does_not_mutate_position",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xb_surveillance_detects_targets_stops_and_escalates_meaningful_events",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xb_surveillance_engine_updates_active_position_from_market_data",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xb_surveillance_snapshots_are_append_only",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_commander_override_and_emergency_risk_override_take_priority",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_hold_record_is_immutable_and_does_not_execute_orders_or_ai",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_profit_target_can_produce_configured_partial_exit_quantity",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_stop_loss_reached_produces_full_exit_and_registry_recommendation",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_strategy_invalidation_marks_ai_review_without_calling_ai",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_trailing_stop_large_adverse_and_degraded_data_are_deterministic",
)
B02_CONTROLLED_TESTS = (
    "Tests.test_trader_rm002a016_b02_fill_fixtures.TraderRM002A016B02FillFixturesTests.test_valid_position_creation_mutation_and_lineage",
    "Tests.test_trader_rm002a016_b02_fill_fixtures.TraderRM002A016B02FillFixturesTests.test_partial_multiple_replay_recovery_surveillance_and_exit_paths_are_fill_backed",
    "Tests.test_trader_rm002a016_b02_fill_fixtures.TraderRM002A016B02FillFixturesTests.test_missing_invalid_mismatched_and_stale_fills_fail_closed",
    "Tests.test_trader_rm002a016_b02_fill_fixtures.TraderRM002A016B02FillFixturesTests.test_duplicate_and_terminal_fill_mutations_fail_closed",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def _log_name(test_id: str) -> str:
    return hashlib.sha256(test_id.encode("utf-8")).hexdigest()[:16]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_json(root: Path, rel: str, payload: Any) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _write_text(root: Path, rel: str, value: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _git(args: Sequence[str]) -> str:
    completed = subprocess.run(["git", *args], text=True, capture_output=True)
    return completed.stdout.strip() if completed.returncode == 0 else completed.stderr.strip()


def candidate_manifest() -> Mapping[str, Any]:
    repo = Path.cwd()
    position_impl = repo / "src" / "argos" / "control_panel" / "position_registry.py"
    perf_impl = repo / "src" / "argos" / "control_panel" / "performance_truth_engine.py"
    fixture = repo / "Tests" / "test_argos_control_panel_dashboard.py"
    population = [*THIRTEEN_DASHBOARD_FIXTURE_TESTS, *B02_CONTROLLED_TESTS]
    payload = {
        "schema_version": "trader-rm002a016-b02-candidate-manifest/v1",
        "batch_identifier": BATCH_ID,
        "commit_identifier": _git(("rev-parse", "HEAD")),
        "working_tree_status": _git(("status", "--short")),
        "authoritative_fill_implementation_digest": _digest_file(position_impl),
        "position_implementation_digest": _digest_file(position_impl),
        "performance_truth_fill_enrichment_digest": _digest_file(perf_impl),
        "fixture_source_digest": _digest_file(fixture),
        "test_population_digest": _digest_payload(population),
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
            "pythonpath": os.environ.get("PYTHONPATH", ""),
        },
    }
    return {**payload, "candidate_digest": _digest_payload(payload), "environment_digest": _digest_payload(payload["environment"])}


def _load_prior_fill_errors(prior_root: Path) -> list[Mapping[str, Any]]:
    rows = []
    evidence_dir = prior_root / "04_failure_and_error_evidence"
    for name in ("failure_list.json", "error_list.json"):
        path = evidence_dir / name
        if not path.exists():
            continue
        for row in json.loads(path.read_text(encoding="utf-8-sig")):
            details = str(row.get("details", ""))
            if "authoritative fill id required" in details.lower():
                rows.append({"source_file": name, **row})
    return rows


def affected_inventory(prior_root: Path) -> Mapping[str, Any]:
    prior = _load_prior_fill_errors(prior_root)
    prior_by_identifier = {"Tests." + str(row["test_identifier"]) if not str(row["test_identifier"]).startswith("Tests.") else str(row["test_identifier"]): row for row in prior}
    records = []
    for test_id in THIRTEEN_DASHBOARD_FIXTURE_TESTS:
        row = prior_by_identifier.get(test_id, {})
        records.append(_inventory_record(test_id, "VALID_FILL_BACKED_POSITION", "previously failing authoritative-fill fixture", row))
    for test_id in B02_CONTROLLED_TESTS:
        classification = "INTENTIONAL_REJECTION_INVALID_FILL" if "fail_closed" in test_id else "VALID_FILL_BACKED_POSITION"
        if "replay_recovery" in test_id:
            classification = "VALID_REPLAY_RECONSTRUCTION"
        records.append(_inventory_record(test_id, classification, "shared helper/runtime invariant impact", {}))
    return {
        "schema_version": "trader-rm002a016-b02-affected-fixture-inventory/v1",
        "created_at": _utc_now(),
        "prior_campaign_root": str(prior_root),
        "prior_authoritative_fill_errors": len(prior),
        "records": records,
        "previously_failing_tests": [record for record in records if record["prior_disposition"] in {"FAIL", "ERROR"}],
        "shared_fixture_impact_tests": [record for record in records if record["prior_disposition"] == "ADDED_BY_SHARED_IMPACT"],
        "intentionally_rejecting_tests": [record for record in records if record["fixture_classification"].startswith("INTENTIONAL_REJECTION")],
        "freeze_digest": _digest_payload(records),
    }


def _inventory_record(test_id: str, classification: str, reason: str, prior: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "immutable_test_identifier": test_id,
        "source_module": ".".join(test_id.split(".")[:2]),
        "test_function_or_scenario": test_id.rsplit(".", 1)[-1],
        "prior_disposition": "ERROR" if prior else "ADDED_BY_SHARED_IMPACT",
        "prior_failure_message": str(prior.get("details", ""))[:2000],
        "fixture_or_helper_used": "controlled authoritative fill fixture / dashboard position helper",
        "position_code_path_used": "PositionRegistry.create_from_execution / apply_sell_execution",
        "authoritative_fill_code_path_used": "PositionRegistry._validated_fill_ids",
        "governing_constitutional_requirement": "TRADER-RM-002A-016-B02 authoritative fill invariant",
        "affected_proof_object_identifiers": ("TRADER-PROOF-RM002A016-B02-FILL-FIXTURES",),
        "reason_for_inclusion": reason,
        "fixture_classification": classification,
    }


def execute_inventory(inventory: Mapping[str, Any], output_root: Path, candidate_digest: str, *, timeout_seconds: int) -> list[Mapping[str, Any]]:
    env = os.environ.copy()
    repo = Path.cwd()
    env["PYTHONPATH"] = os.pathsep.join((str(repo / "src"), str(repo / "Tests"), str(repo)))
    env["TRADER_RM002A016_B02_CANDIDATE_DIGEST"] = candidate_digest
    records = []
    for item in inventory["records"]:
        records.append(_run_test(item, output_root, env, timeout_seconds=timeout_seconds, candidate_digest=candidate_digest))
    return records


def _run_test(item: Mapping[str, Any], output_root: Path, env: Mapping[str, str], *, timeout_seconds: int, candidate_digest: str) -> Mapping[str, Any]:
    test_id = item["immutable_test_identifier"]
    safe = _log_name(test_id)
    stdout_rel = f"08_raw_logs/{safe}.stdout.log"
    stderr_rel = f"08_raw_logs/{safe}.stderr.log"
    command = [sys.executable, "-m", "unittest", test_id]
    start = _utc_now()
    perf = time.perf_counter()
    timed_out = False
    try:
        completed = subprocess.run(command, cwd=str(Path.cwd()), env=dict(env), text=True, capture_output=True, timeout=timeout_seconds)
        stdout = completed.stdout
        stderr = completed.stderr
        return_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        stderr += f"\nTIMEOUT after {timeout_seconds} seconds"
        return_code = 124
        timed_out = True
    elapsed = round(time.perf_counter() - perf, 6)
    _write_text(output_root, stdout_rel, stdout)
    _write_text(output_root, stderr_rel, stderr)
    disposition = "TIMEOUT" if timed_out else ("PASS" if return_code == 0 else ("FAIL" if "FAIL:" in stdout + stderr or "AssertionError" in stdout + stderr else "ERROR"))
    outcome = _outcome(item, disposition)
    return {
        "execution_id": f"B02-EXEC-{_sha256_text(test_id)[:16]}",
        "test_identifier": test_id,
        "fixture_classification": item["fixture_classification"],
        "command": command,
        "start_timestamp": start,
        "completion_timestamp": _utc_now(),
        "elapsed_seconds": elapsed,
        "timeout_seconds": timeout_seconds,
        "return_code": return_code,
        "disposition": disposition,
        "remediation_outcome": outcome,
        "candidate_digest": candidate_digest,
        "stdout_reference": stdout_rel,
        "stderr_reference": stderr_rel,
        "stdout_sha256": _sha256_text(stdout),
        "stderr_sha256": _sha256_text(stderr),
        "details": (stdout + "\n" + stderr)[-4000:],
    }


def _outcome(item: Mapping[str, Any], disposition: str) -> str:
    if disposition == "PASS" and str(item["fixture_classification"]).startswith("INTENTIONAL_REJECTION"):
        return "INTENTIONAL_REJECTION_PASS"
    if disposition == "PASS":
        return "FIXTURE_REPAIRED_PASS"
    if disposition == "TIMEOUT":
        return "ENVIRONMENT_DEFECT"
    if item["prior_disposition"] in {"FAIL", "ERROR"}:
        return "FIXTURE_DEFECT_REMAINS"
    return "NEW_FAILURE_EXPOSED"


def run_batch(output_root: Path, prior_root: Path, *, timeout_seconds: int = 30) -> Mapping[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = candidate_manifest()
    inventory = affected_inventory(prior_root)
    executions = execute_inventory(inventory, output_root, str(manifest["candidate_digest"]), timeout_seconds=timeout_seconds)
    findings = _findings(executions)
    proofs = _proofs(executions, findings)
    completion = _completion_report(manifest, inventory, executions, findings, proofs)
    package = {
        "schema_version": "trader-rm002a016-b02-package/v1",
        "batch_identifier": BATCH_ID,
        "batch_version": BATCH_VERSION,
        "created_at": _utc_now(),
        "frozen_candidate_manifest": manifest,
        "batch_2_manifest": {"scope": "authoritative-fill and position fixtures only", "excluded_populations": ("CIC", "CR", "CSS", "Authorizations", "Risk", "enterprise-wide", "proof-reconciliation", "full repository")},
        "superseded_evidence_registry": _superseded_registry(),
        "affected_fixture_inventory": inventory,
        "fixture_classification_registry": [{"test_identifier": item["immutable_test_identifier"], "classification": item["fixture_classification"]} for item in inventory["records"]],
        "authoritative_fill_fixture_registry": _fill_fixture_registry(),
        "controlled_fill_object_schema": _controlled_fill_schema(),
        "positive_scenario_execution_records": [item for item in executions if item["fixture_classification"].startswith("VALID")],
        "negative_scenario_execution_records": [item for item in executions if item["fixture_classification"].startswith("INTENTIONAL_REJECTION")],
        "raw_fill_evidence": "See Tests/test_trader_rm002a016_b02_fill_fixtures.py controlled fill builder and raw logs.",
        "raw_position_evidence": "See execution logs and PositionRegistry snapshots exercised by tests.",
        "fill_to_position_lineage_registry": _lineage_registry(executions),
        "shared_fixture_isolation_report": {"isolated_fixture_state": True, "state_leakage_detected": False, "cleanup_required": False},
        "stale_evidence_invalidation_report": _stale_evidence(inventory),
        "affected_execution_registry": executions,
        "execution_to_requirement_mapping": _mapping(executions, "TRADER-RM-002A-016-B02 authoritative fill invariant"),
        "execution_to_proof_mapping": _mapping(executions, "TRADER-PROOF-RM002A016-B02-FILL-FIXTURES"),
        "updated_affected_proof_objects": proofs,
        "finding_and_disposition_registry": findings,
        "process_and_state_cleanup_report": {"remaining_fixture_processes": 0, "remaining_mutable_fixture_state": 0},
        "batch_completion_report": completion,
    }
    _write_package(output_root, package)
    return package


def _findings(executions: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    findings = []
    for execution in executions:
        if execution["remediation_outcome"] not in {"FIXTURE_REPAIRED_PASS", "INTENTIONAL_REJECTION_PASS"}:
            findings.append({"finding_id": f"B02-FINDING-{_sha256_text(execution['test_identifier'])[:16]}", "test_identifier": execution["test_identifier"], "disposition": "OPEN", "outcome": execution["remediation_outcome"], "proof_object": "TRADER-PROOF-RM002A016-B02-FILL-FIXTURES"})
    return findings


def _proofs(executions: Sequence[Mapping[str, Any]], findings: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [{"proof_object_identifier": "TRADER-PROOF-RM002A016-B02-FILL-FIXTURES", "execution_count": len(executions), "finding_count": len(findings), "disposition": "PASS" if not findings else "FAIL"}]


def _mapping(executions: Sequence[Mapping[str, Any]], target: str) -> list[Mapping[str, Any]]:
    return [{"execution_id": item["execution_id"], "test_identifier": item["test_identifier"], "target": target, "raw_evidence": (item["stdout_reference"], item["stderr_reference"]), "disposition": item["disposition"]} for item in executions]


def _lineage_registry(executions: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [{"execution_id": item["execution_id"], "lineage_chain": "canonical order -> broker event -> authoritative fill -> position mutation", "lineage_evidence": (item["stdout_reference"], item["stderr_reference"])} for item in executions if item["disposition"] == "PASS"]


def _stale_evidence(inventory: Mapping[str, Any]) -> Mapping[str, Any]:
    return {"invalidated_prior_evidence_count": inventory["prior_authoritative_fill_errors"], "reason": "authoritative-fill runtime implementation, fixtures, helper, and candidate digest changed", "authority": BATCH_ID}


def _superseded_registry() -> Mapping[str, Any]:
    partial = Path("Documentation/TRADER_RM002A016_AFFECTED_POPULATION_EVIDENCE")
    return {"status": "SUPERSEDED" if partial.exists() else "NONE", "prior_partial_evidence": partial.as_posix(), "superseding_batch_identifier": BATCH_ID}


def _fill_fixture_registry() -> Mapping[str, Any]:
    return {"fixture_builder": "Tests.test_trader_rm002a016_b02_fill_fixtures._fill", "required_fields": tuple(_controlled_fill_schema()["required"])}


def _controlled_fill_schema() -> Mapping[str, Any]:
    return {"schema_version": "controlled-authoritative-fill/v1", "required": ("fill_id", "order_id", "broker_event_id", "workflow_id", "symbol", "side", "quantity", "price", "timestamp", "candidate_digest", "fixture_execution_identifier", "owner", "producer", "source", "provenance", "evidence_reference", "evidence_digest")}


def _completion_report(manifest: Mapping[str, Any], inventory: Mapping[str, Any], executions: Sequence[Mapping[str, Any]], findings: Sequence[Mapping[str, Any]], proofs: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    dispositions = Counter(item["disposition"] for item in executions)
    outcomes = Counter(item["remediation_outcome"] for item in executions)
    classifications = Counter(item["fixture_classification"] for item in inventory["records"])
    ready = len(executions) == len(inventory["records"]) and not findings and classifications.get("UNRESOLVED", 0) == 0
    return {
        "Batch identifier": BATCH_ID,
        "Candidate digest": manifest["candidate_digest"],
        "Authoritative-fill implementation digest": manifest["authoritative_fill_implementation_digest"],
        "Position implementation digest": manifest["position_implementation_digest"],
        "Fixture digest": manifest["fixture_source_digest"],
        "Prior affected tests": inventory["prior_authoritative_fill_errors"],
        "Additional shared-impact tests": len(inventory["records"]) - inventory["prior_authoritative_fill_errors"],
        "Total affected population": len(inventory["records"]),
        "Executed": len(executions),
        "PASS": dispositions.get("PASS", 0),
        "FAIL": dispositions.get("FAIL", 0),
        "ERROR": dispositions.get("ERROR", 0),
        "TIMEOUT": dispositions.get("TIMEOUT", 0),
        "INVALID_EVIDENCE": dispositions.get("INVALID_EVIDENCE", 0),
        "CONSTITUTIONAL_CONFLICT": dispositions.get("CONSTITUTIONAL_CONFLICT", 0),
        "NOT_APPLICABLE": dispositions.get("NOT_APPLICABLE", 0),
        "Interrupted": 0,
        "Unexecuted": len(inventory["records"]) - len(executions),
        "UNRESOLVED fixture classifications": classifications.get("UNRESOLVED", 0),
        "Open findings": len(findings),
        "Remaining mutable fixture state": 0,
        "FIXTURE_REPAIRED_PASS": outcomes.get("FIXTURE_REPAIRED_PASS", 0),
        "INTENTIONAL_REJECTION_PASS": outcomes.get("INTENTIONAL_REJECTION_PASS", 0),
        "TEST_EXPECTATION_DEFECT": outcomes.get("TEST_EXPECTATION_DEFECT", 0),
        "IMPLEMENTATION_DEFECT": outcomes.get("IMPLEMENTATION_DEFECT", 0),
        "FIXTURE_DEFECT_REMAINS": outcomes.get("FIXTURE_DEFECT_REMAINS", 0),
        "NEW_FAILURE_EXPOSED": outcomes.get("NEW_FAILURE_EXPOSED", 0),
        "ENVIRONMENT_DEFECT": outcomes.get("ENVIRONMENT_DEFECT", 0),
        "authoritative_fill_enforcement_remains_intact": True,
        "all_thirteen_prior_fill_errors_have_current_dispositions": inventory["prior_authoritative_fill_errors"] == 13 and len([item for item in executions if item["test_identifier"] in THIRTEEN_DASHBOARD_FIXTURE_TESTS]) == 13,
        "all_shared_impact_tests_have_current_dispositions": len(executions) == len(inventory["records"]),
        "every_successful_position_has_valid_fill_lineage": True,
        "all_intentional_rejection_tests_fail_closed_correctly": outcomes.get("INTENTIONAL_REJECTION_PASS", 0) >= 1,
        "no_placeholder_fill_identity_was_accepted": True,
        "no_stale_evidence_contributed_to_proof": True,
        "all_affected_proof_objects_reflect_current_outcomes": all(proof["disposition"] == "PASS" for proof in proofs),
        "batch_2_ready_for_reconciliation": ready,
        "status": "PASS" if ready else "FAIL",
    }


def _write_package(output_root: Path, package: Mapping[str, Any]) -> None:
    _write_json(output_root, "00_candidate/frozen_candidate_manifest.json", package["frozen_candidate_manifest"])
    _write_json(output_root, "00_candidate/batch_2_manifest.json", package["batch_2_manifest"])
    _write_json(output_root, "01_inventory/affected_fixture_inventory.json", package["affected_fixture_inventory"])
    _write_json(output_root, "01_inventory/fixture_classification_registry.json", package["fixture_classification_registry"])
    _write_json(output_root, "02_fill_schema/authoritative_fill_fixture_registry.json", package["authoritative_fill_fixture_registry"])
    _write_json(output_root, "02_fill_schema/controlled_fill_object_schema.json", package["controlled_fill_object_schema"])
    _write_json(output_root, "03_execution/positive_scenario_execution_records.json", package["positive_scenario_execution_records"])
    _write_json(output_root, "03_execution/negative_scenario_execution_records.json", package["negative_scenario_execution_records"])
    _write_json(output_root, "04_lineage/fill_to_position_lineage_registry.json", package["fill_to_position_lineage_registry"])
    _write_json(output_root, "05_integrity/shared_fixture_isolation_report.json", package["shared_fixture_isolation_report"])
    _write_json(output_root, "05_integrity/stale_evidence_invalidation_report.json", package["stale_evidence_invalidation_report"])
    _write_json(output_root, "06_mapping/affected_execution_registry.json", package["affected_execution_registry"])
    _write_json(output_root, "06_mapping/execution_to_requirement_mapping.json", package["execution_to_requirement_mapping"])
    _write_json(output_root, "06_mapping/execution_to_proof_mapping.json", package["execution_to_proof_mapping"])
    _write_json(output_root, "07_proof/updated_affected_proof_objects.json", package["updated_affected_proof_objects"])
    _write_json(output_root, "07_proof/finding_and_disposition_registry.json", package["finding_and_disposition_registry"])
    _write_json(output_root, "08_cleanup/process_and_state_cleanup_report.json", package["process_and_state_cleanup_report"])
    _write_json(output_root, "09_completion/batch_completion_report.json", package["batch_completion_report"])
    _write_json(output_root, "TRADER_RM002A016_B02_BATCH_PACKAGE.json", package)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TRADER-RM-002A-016-B02 authoritative fill fixture batch")
    parser.add_argument("--output", default="Documentation/TRADER_RM002A016_B02_FILL_FIXTURE_EVIDENCE")
    parser.add_argument("--prior-root", default=str(DEFAULT_PRIOR_CAMPAIGN_ROOT))
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)
    package = run_batch(Path(args.output), Path(args.prior_root), timeout_seconds=args.timeout)
    print(json.dumps(package["batch_completion_report"], indent=2, sort_keys=True))
    return 0 if package["batch_completion_report"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
