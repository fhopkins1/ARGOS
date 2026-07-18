"""Generate IFVA-001 full constitutional audit evidence.

This script is an audit harness. It observes the repository, executes bounded
canonical-runtime probes, preserves raw command output, and writes a single ZIP
for independent review. It does not enable live trading and does not mark ARGOS
ready for paper operation.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import zipfile
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.canonical_enterprise_runtime import CanonicalEnterpriseRuntime
from argos.control_panel.read_only_integrity import ReadOnlyIntegrityGuard
from argos.control_panel.runtime_bridge_certification import (
    RuntimeBridgeCertificationHarness,
    office_inventory,
    required_runtime_bridge_matrix,
    static_call_graph,
)
from argos.control_panel.synthetic_truth_quarantine import SyntheticTruthEradicationEngine
from argos.control_panel.test_evidence_office import TestCompletenessEvidenceOffice
from argos.control_panel.transaction_reconciliation import (
    ParticipantState,
    TransactionReconciliationCoordinator,
)
from argos.foundation.contracts import utc_timestamp


PACKAGE_ROOT = REPO_ROOT / "Documentation" / "IFVA-001_Evidence" / "ARGOS_FULL_CONSTITUTIONAL_AUDIT_EVIDENCE"
ZIP_PATH = REPO_ROOT / "Documentation" / "IFVA-001_Evidence" / "ARGOS_FULL_CONSTITUTIONAL_AUDIT_EVIDENCE.zip"

DIRS = (
    "00_identity",
    "01_repository_inventory",
    "02_runtime_architecture",
    "03_office_inventory",
    "04_bridge_inventory",
    "05_authority_and_law_vii",
    "06_truth_domains_and_provenance",
    "07_synthetic_truth",
    "08_canonical_runtime_traces",
    "09_financial_lifecycle_traces",
    "10_transaction_and_reconciliation",
    "11_persistence_and_recovery",
    "12_replay",
    "13_read_only_integrity",
    "14_fault_and_failure_traces",
    "15_api_cost_and_resource_metrics",
    "16_tests_and_coverage",
    "17_ci_and_static_analysis",
    "18_known_defects_and_limitations",
    "19_audit_scorecards",
    "20_raw_logs",
    "21_machine_readable_graphs",
    "22_manifests_and_hashes",
)


def main() -> None:
    if PACKAGE_ROOT.exists():
        shutil.rmtree(PACKAGE_ROOT)
    PACKAGE_ROOT.mkdir(parents=True, exist_ok=True)
    for name in DIRS:
        (PACKAGE_ROOT / name).mkdir(parents=True, exist_ok=True)

    started = utc_timestamp()
    identity = candidate_identity()
    write_identity(identity)
    write_repository_inventory()

    runtime_trace = capture_runtime_trace()
    write_json(PACKAGE_ROOT / "08_canonical_runtime_traces" / "canonical_runtime_trace.json", runtime_trace)

    bridge_report, bridge_harness = capture_bridge_evidence(identity)
    synthetic_report = capture_synthetic_truth(identity)
    transaction_trace = capture_transaction_trace()
    persistence_trace = capture_persistence_trace()
    read_trace = capture_read_only_trace(runtime_trace)

    write_json(PACKAGE_ROOT / "10_transaction_and_reconciliation" / "transaction_trace.json", transaction_trace)
    write_json(PACKAGE_ROOT / "11_persistence_and_recovery" / "persistence_restore_trace.json", persistence_trace)
    write_json(PACKAGE_ROOT / "12_replay" / "replay_isolation_trace.json", replay_trace())
    write_json(PACKAGE_ROOT / "13_read_only_integrity" / "read_only_guard_trace.json", read_trace)
    write_json(PACKAGE_ROOT / "14_fault_and_failure_traces" / "fault_and_failure_trace.json", fault_trace(runtime_trace, transaction_trace))
    write_json(PACKAGE_ROOT / "15_api_cost_and_resource_metrics" / "api_cost_resource_metrics.json", api_cost_metrics(runtime_trace))

    test_results = run_test_evidence()
    write_json(PACKAGE_ROOT / "16_tests_and_coverage" / "bounded_test_results.json", test_results)
    write_static_analysis()

    defects = known_defects(identity, bridge_report, synthetic_report, test_results)
    scorecard = audit_scorecard(identity, bridge_report, synthetic_report, test_results, defects)
    write_json(PACKAGE_ROOT / "18_known_defects_and_limitations" / "known_defects.json", defects)
    write_text(PACKAGE_ROOT / "18_known_defects_and_limitations" / "known_limitations.md", limitations_md(defects))
    write_json(PACKAGE_ROOT / "19_audit_scorecards" / "audit_scorecard.json", scorecard)
    write_text(PACKAGE_ROOT / "19_audit_scorecards" / "audit_scorecard.md", scorecard_md(scorecard))

    write_graphs(bridge_harness, transaction_trace, runtime_trace)
    write_manifests(started, identity, scorecard)
    write_readme(identity, scorecard)
    zip_package()


def candidate_identity() -> dict[str, Any]:
    status = run_command(("git", "status", "--short"), 30)
    tracked = run_command(("git", "ls-files"), 30)["stdout"].splitlines()
    untracked = [line for line in status["stdout"].splitlines() if line.startswith("??")]
    modified = [line for line in status["stdout"].splitlines() if line and not line.startswith("??")]
    lockfiles = [p for p in ("pyproject.toml", "requirements.txt", "package-lock.json", "uv.lock", "poetry.lock") if (REPO_ROOT / p).exists()]
    env_names = discover_environment_names()
    return {
        "repository_name": REPO_ROOT.name,
        "repository_root": str(REPO_ROOT),
        "branch": git_text("rev-parse", "--abbrev-ref", "HEAD"),
        "candidate_commit_sha": git_text("rev-parse", "HEAD"),
        "parent_commit_sha": git_text("rev-parse", "HEAD^"),
        "git_status_short": status["stdout"],
        "tracked_file_count": len(tracked),
        "untracked_file_count": len(untracked),
        "modified_file_count": len(modified),
        "operating_system": platform.platform(),
        "python_version": platform.python_version(),
        "node_version": command_stdout(("node", "--version"), 15),
        "package_manager_versions": {
            "pip": command_stdout((sys.executable, "-m", "pip", "--version"), 30),
            "npm": command_stdout(("npm", "--version"), 15),
        },
        "test_framework_versions": {"unittest": "stdlib", "pytest": command_stdout((sys.executable, "-m", "pytest", "--version"), 15)},
        "dependency_lockfile_hashes": {path: file_hash(REPO_ROOT / path) for path in lockfiles},
        "environment_variables": {
            name: {
                "state": "set" if os.getenv(name) else "unset",
                "value": "redacted" if os.getenv(name) else "",
                "required": name in {"ARGOS_RUNTIME_MODE", "ARGOS_TRUTH_DOMAIN", "ARGOS_LIVE_TRADING_ENABLED"},
                "optional": name not in {"ARGOS_RUNTIME_MODE", "ARGOS_TRUTH_DOMAIN", "ARGOS_LIVE_TRADING_ENABLED"},
            }
            for name in env_names
        },
        "active_runtime_mode": os.getenv("ARGOS_RUNTIME_MODE", "paper_idle"),
        "active_truth_domain": os.getenv("ARGOS_TRUTH_DOMAIN", "PAPER"),
        "broker_configuration": {"broker": "DeterministicPaperBrokerage", "account": "ACCT-PAPER-001", "live_trading_enabled": False},
        "persistence_backend": "InMemoryPersistenceRepository plus checkpointable runtime snapshots",
        "live_trading_status": "disabled",
        "generated_at_utc": utc_timestamp(),
    }


def write_identity(identity: dict[str, Any]) -> None:
    out = PACKAGE_ROOT / "00_identity"
    write_json(out / "00_repository_identity.json", identity)
    write_text(out / "00_repository_identity.md", identity_md(identity))
    write_json(out / "00_environment.json", {"platform": platform.platform(), "python": platform.python_version(), "cwd": str(REPO_ROOT)})
    write_json(out / "00_dependency_versions.json", identity["package_manager_versions"] | {"testFrameworks": identity["test_framework_versions"]})
    write_text(out / "00_git_status.txt", identity["git_status_short"])
    write_text(out / "00_candidate_commit.txt", identity["candidate_commit_sha"] + "\n")


def write_repository_inventory() -> None:
    files = sorted(p for p in REPO_ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and "IFVA-001_Evidence" not in p.parts)
    rows = [{"path": rel(p), "size": p.stat().st_size, "sha256": file_hash(p)} for p in files]
    write_json(PACKAGE_ROOT / "01_repository_inventory" / "tracked_and_local_file_inventory.json", rows)
    write_csv(PACKAGE_ROOT / "01_repository_inventory" / "file_inventory.csv", ("path", "size", "sha256"), rows)
    write_json(PACKAGE_ROOT / "01_repository_inventory" / "source_module_inventory.json", source_inventory())


def capture_runtime_trace() -> dict[str, Any]:
    runtime = CanonicalEnterpriseRuntime(live_trading_enabled=False)
    events: list[dict[str, Any]] = []
    try:
        events.append({"event": "constructed", "status": runtime.runtime_status(), "snapshot": runtime.read_only_snapshot()})
        events.append({"event": "start", "status": runtime.start(), "snapshot": runtime.read_only_snapshot()})
        admission = runtime.admit_scheduled_obligation("IFVA-001-AUDIT-SCHEDULED-OBLIGATION")
        events.append({"event": "admit_scheduled_obligation", "record": jsonable(admission), "snapshot": runtime.read_only_snapshot()})
        mandate = runtime.create_strategic_mandate(subject="IFVA-001 audit probe")
        seeker = runtime.request_seeker_work(mandate_id=mandate["mandate_id"], mission_id=admission.scheduler_mission_id, workflow_id=admission.workflow_id)
        events.append({"event": "strategic_to_seeker_bridge", "mandate": mandate, "result": seeker})
        events.append({"event": "persistence_snapshot", "snapshot": runtime.enterprise_persistence_snapshot()})
        events.append({"event": "halt", "status": runtime.halt(reason="IFVA-001 bounded evidence capture complete.")})
    except Exception as exc:  # Preserve actual failure for audit.
        events.append({"event": "exception", "type": type(exc).__name__, "message": str(exc)})
    return {"live_trading_enabled": False, "events": events}


def capture_bridge_evidence(identity: dict[str, Any]) -> tuple[dict[str, Any], RuntimeBridgeCertificationHarness]:
    harness = RuntimeBridgeCertificationHarness()
    report = harness.certify(repo_root=REPO_ROOT, commit_sha=identity["candidate_commit_sha"], branch=identity["branch"])
    out = PACKAGE_ROOT / "04_bridge_inventory"
    harness.write_evidence_bundle(out, report)
    write_json(out / "required_bridge_matrix.json", required_runtime_bridge_matrix())
    write_json(PACKAGE_ROOT / "03_office_inventory" / "office_inventory.json", office_inventory())
    write_json(PACKAGE_ROOT / "04_bridge_inventory" / "bridge_certification_report.json", report)
    write_json(PACKAGE_ROOT / "08_canonical_runtime_traces" / "bridge_dynamic_traces.json", harness.traces)
    write_json(PACKAGE_ROOT / "05_authority_and_law_vii" / "law_vii_and_authority_bridge_model.json", harness.commander_read_model(report))
    return jsonable(report), harness


def capture_synthetic_truth(identity: dict[str, Any]) -> dict[str, Any]:
    harness = SyntheticTruthEradicationEngine()
    report = harness.audit(repo_root=REPO_ROOT, commit_sha=identity["candidate_commit_sha"], branch=identity["branch"])
    out = PACKAGE_ROOT / "07_synthetic_truth"
    harness.write_evidence_bundle(out, report)
    write_json(out / "synthetic_truth_audit_report.json", report)
    write_json(PACKAGE_ROOT / "06_truth_domains_and_provenance" / "truth_domain_and_provenance_report.json", harness.commander_read_model(report))
    return jsonable(report)


def capture_transaction_trace() -> dict[str, Any]:
    coordinator = TransactionReconciliationCoordinator()
    decision = {"decision_id": "IFVA-EODC-DECISION-001", "decision": "APPROVED", "status": "APPROVED"}
    trace: dict[str, Any] = {"live_trading_enabled": False, "events": []}
    try:
        intent = coordinator.coordinate_broker_fill(
            eodc_decision=decision,
            source_authority="DeterministicPaperBrokerage",
            source_event_id="IFVA-FILL-EVENT-001",
            mission_id="IFVA-MISSION-001",
            workflow_id="IFVA-WORKFLOW-001",
            workflow_execution_token_id="IFVA-TOKEN-001",
            asset_id="AAPL",
            account_id="ACCT-PAPER-001",
            order_id="IFVA-ORDER-001",
            fill_id="IFVA-FILL-001",
            idempotency_key="IFVA-TX-OPENING-FILL-001",
        )
        trace["events"].append({"event": "intent_created", "intent": jsonable(intent)})
        for authority in ("Paper Broker", "Position Registry", "Performance Truth", "Historian"):
            ack = coordinator.acknowledge_participant(
                intent.transaction_id,
                authority,
                evidence_reference=f"IFVA evidence for {authority}",
                output_version="ifva-001",
                participant_state=ParticipantState.ACKNOWLEDGED,
            )
            trace["events"].append({"event": "participant_acknowledged", "ack": jsonable(ack)})
        state = coordinator.evaluate_commit(intent.transaction_id)
        result = coordinator.reconcile_transaction(intent.transaction_id, performance_truth_snapshot={"paper": True, "source": "IFVA bounded trace"})
        trace["events"].append({"event": "evaluate_commit", "state": state.value})
        trace["events"].append({"event": "reconcile_transaction", "result": jsonable(result)})
        trace["snapshot"] = jsonable(coordinator.snapshot(intent.transaction_id))
        trace["integrity_findings"] = coordinator.journal.validate_integrity()
        trace["commander_read_model"] = coordinator.commander_read_model()
    except Exception as exc:
        trace["events"].append({"event": "exception", "type": type(exc).__name__, "message": str(exc)})
    return trace


def capture_persistence_trace() -> dict[str, Any]:
    trace: dict[str, Any] = {"events": []}
    runtime = CanonicalEnterpriseRuntime(live_trading_enabled=False)
    try:
        runtime.start()
        runtime.admit_scheduled_obligation("IFVA-001-PERSISTENCE-PROBE")
        snapshot = runtime.enterprise_persistence_snapshot()
        digest_before = stable_hash(snapshot)
        restored = CanonicalEnterpriseRuntime(live_trading_enabled=False)
        restored.restore_enterprise_persistence_snapshot(snapshot["runtime"])
        restored_snapshot = restored.read_only_snapshot()
        trace["events"].append({"event": "snapshot_created", "digest": digest_before, "snapshot_keys": sorted(snapshot.keys())})
        trace["events"].append({"event": "runtime_restore_invoked", "restored_snapshot": restored_snapshot})
        trace["deterministic_restart_verdict"] = "PARTIAL"
        trace["limitation"] = "Runtime continuity fields restore; full component state rehydration evidence remains incomplete in this bounded harness."
    except Exception as exc:
        trace["events"].append({"event": "exception", "type": type(exc).__name__, "message": str(exc)})
        trace["deterministic_restart_verdict"] = "FAILED"
    return trace


def capture_read_only_trace(runtime_trace: dict[str, Any]) -> dict[str, Any]:
    state = {"runtime": runtime_trace, "counter": 0}
    guard = ReadOnlyIntegrityGuard()
    try:
        response, result = guard.guard_read(
            "COMMANDER-RUNTIME-STATUS",
            lambda: {"runtimeEvents": len(runtime_trace.get("events", ()))},
            lambda: state,
            invocation_id="IFVA-READ-001",
            runtime_mode="paper",
            truth_domain="PAPER",
        )
        return {"response": response, "result": jsonable(result), "evidence_store": guard.evidence_store.snapshot()}
    except Exception as exc:
        return {"exception": {"type": type(exc).__name__, "message": str(exc)}}


def replay_trace() -> dict[str, Any]:
    return {
        "verdict": "PARTIAL",
        "live_trading_enabled": False,
        "replay_domain": "isolated evidence observation only",
        "evidence": "No live or paper authority was delegated to replay during IFVA-001.",
        "limitation": "No long replay campaign was executed in this bounded package run.",
    }


def fault_trace(runtime_trace: dict[str, Any], transaction_trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime_exceptions": [event for event in runtime_trace.get("events", ()) if event.get("event") == "exception"],
        "transaction_exceptions": [event for event in transaction_trace.get("events", ()) if event.get("event") == "exception"],
        "failure_policy": "fail closed; preserve adverse evidence",
    }


def api_cost_metrics(runtime_trace: dict[str, Any]) -> dict[str, Any]:
    snapshots = [event.get("snapshot", {}) for event in runtime_trace.get("events", ()) if isinstance(event, dict)]
    return {
        "live_api_enabled": False,
        "real_api_pilot_enabled": False,
        "api_request_trace_count": 0,
        "runtime_snapshot_count": len(snapshots),
        "limitation": "No external broker or market-data API calls were issued by IFVA-001.",
    }


def run_test_evidence() -> dict[str, Any]:
    out = PACKAGE_ROOT / "16_tests_and_coverage"
    office = TestCompletenessEvidenceOffice()
    office.generate_audit_package(out / "EO-DI_embedded_package", repo_root=REPO_ROOT)
    commands = {
        "focused_ifva_support_slice": (
            sys.executable,
            "-m",
            "unittest",
            "Tests.test_eodi_test_evidence_office",
            "Tests.test_eodb_runtime_bridge_certification",
            "Tests.test_eodh_synthetic_truth_quarantine",
            "Tests.test_eodg_read_only_integrity",
            "Tests.test_eodd_transaction_reconciliation",
            "Tests.test_or005_canonical_runtime",
            "Tests.test_or006_enterprise_persistence",
            "Tests.test_or007_enterprise_certification",
        ),
        "full_unittest_discover_120s": (sys.executable, "-m", "unittest", "discover", "-s", "Tests"),
    }
    results = {}
    for name, command in commands.items():
        timeout = 120 if name.startswith("full_") else 180
        result = run_command(command, timeout)
        results[name] = result
        write_text(PACKAGE_ROOT / "20_raw_logs" / f"{name}.log", command_log(command, result))
    return results


def write_static_analysis() -> None:
    call_edges = static_call_graph(REPO_ROOT / "src" / "argos" / "control_panel")
    write_json(PACKAGE_ROOT / "17_ci_and_static_analysis" / "static_call_graph.json", call_edges)
    write_csv(
        PACKAGE_ROOT / "17_ci_and_static_analysis" / "static_call_graph.csv",
        ("source_file", "line_number", "edge_type", "source_symbol", "target_symbol"),
        [jsonable(edge) for edge in call_edges],
    )
    compile_result = run_command((sys.executable, "-m", "compileall", "-q", "src", "Tests"), 180)
    write_text(PACKAGE_ROOT / "17_ci_and_static_analysis" / "compileall.log", command_log((sys.executable, "-m", "compileall", "-q", "src", "Tests"), compile_result))


def known_defects(identity: dict[str, Any], bridge_report: dict[str, Any], synthetic_report: dict[str, Any], test_results: dict[str, Any]) -> list[dict[str, Any]]:
    defects = []
    if bridge_report.get("verdict") != "PASS":
        defects.append(defect("IFVA-DEFECT-BRIDGE", "Bridge certification is not PASS.", "MAJOR", bridge_report.get("findings", ())))
    if synthetic_report.get("verdict") != "PASS":
        defects.append(defect("IFVA-DEFECT-SYNTHETIC", "Synthetic-truth audit is not PASS.", "MAJOR", synthetic_report.get("unresolved_findings", ())))
    full = test_results.get("full_unittest_discover_120s", {})
    if full.get("timed_out"):
        defects.append(defect("IFVA-DEFECT-FULL-SUITE-TIMEOUT", "Full unittest discovery timed out at 120 seconds.", "MAJOR", full))
    if identity["git_status_short"].strip():
        defects.append(defect("IFVA-DEFECT-DIRTY-CANDIDATE", "Candidate had local changes at evidence start.", "MINOR", identity["git_status_short"]))
    defects.append(defect("IFVA-LIMITATION-NO-LIVE", "Live trading was intentionally disabled and not audited.", "INFORMATIONAL", {"live_trading_enabled": False}))
    defects.append(defect("IFVA-LIMITATION-BOUNDED-ENDURANCE", "No low-cost continuous paper-trading endurance run was completed.", "MAJOR", {}))
    return defects


def audit_scorecard(identity: dict[str, Any], bridge_report: dict[str, Any], synthetic_report: dict[str, Any], test_results: dict[str, Any], defects: list[dict[str, Any]]) -> dict[str, Any]:
    blocking = [item for item in defects if item["severity"] in {"CRITICAL", "MAJOR"}]
    focused = test_results.get("focused_ifva_support_slice", {})
    return {
        "verdict": "FAIL" if blocking else "PASS",
        "candidate_commit_sha": identity["candidate_commit_sha"],
        "branch": identity["branch"],
        "generated_at_utc": utc_timestamp(),
        "certifies_argos": False,
        "certifies_low_cost_continuous_paper_trading": False,
        "live_trading_enabled": False,
        "bridge_verdict": bridge_report.get("verdict", "UNKNOWN"),
        "synthetic_truth_verdict": synthetic_report.get("verdict", "UNKNOWN"),
        "focused_ifva_support_slice_exit_code": focused.get("exit_code"),
        "full_suite_timed_out": bool(test_results.get("full_unittest_discover_120s", {}).get("timed_out")),
        "defect_count": len(defects),
        "blocking_defect_count": len(blocking),
        "readiness_assessment": "neither certified nor continuous-paper-ready; proof/simulation evidence package available for independent audit",
    }


def write_graphs(bridge_harness: RuntimeBridgeCertificationHarness, transaction_trace: dict[str, Any], runtime_trace: dict[str, Any]) -> None:
    nodes = [{"id": bridge.bridge_id, "type": "bridge", "source": bridge.source_authority, "target": bridge.target_authority} for bridge in required_runtime_bridge_matrix()]
    edges = [{"source": bridge.source_authority, "target": bridge.target_authority, "bridge_id": bridge.bridge_id} for bridge in required_runtime_bridge_matrix()]
    write_json(PACKAGE_ROOT / "21_machine_readable_graphs" / "office_bridge_graph.json", {"nodes": nodes, "edges": edges})
    write_json(PACKAGE_ROOT / "21_machine_readable_graphs" / "runtime_trace_graph.json", {"events": runtime_trace.get("events", ())})
    write_json(PACKAGE_ROOT / "21_machine_readable_graphs" / "transaction_graph.json", transaction_trace)
    write_json(PACKAGE_ROOT / "21_machine_readable_graphs" / "dynamic_bridge_trace_graph.json", bridge_harness.traces)


def write_manifests(started: str, identity: dict[str, Any], scorecard: dict[str, Any]) -> None:
    files = sorted(p for p in PACKAGE_ROOT.rglob("*") if p.is_file())
    manifest = [{"path": str(p.relative_to(PACKAGE_ROOT)).replace("\\", "/"), "size": p.stat().st_size, "sha256": file_hash(p)} for p in files]
    write_json(PACKAGE_ROOT / "22_manifests_and_hashes" / "evidence_manifest.json", manifest)
    write_text(PACKAGE_ROOT / "22_manifests_and_hashes" / "evidence_hashes.sha256", "\n".join(f"{item['sha256']}  {item['path']}" for item in manifest) + "\n")
    write_json(
        PACKAGE_ROOT / "22_manifests_and_hashes" / "generation_manifest.json",
        {"started_at_utc": started, "completed_at_utc": utc_timestamp(), "candidate": identity["candidate_commit_sha"], "scorecard": scorecard},
    )


def write_readme(identity: dict[str, Any], scorecard: dict[str, Any]) -> None:
    write_text(
        PACKAGE_ROOT / "README_AUDIT_PACKAGE.md",
        "\n".join(
            (
                "# ARGOS Full Constitutional Audit Evidence",
                "",
                f"Candidate commit: `{identity['candidate_commit_sha']}`",
                f"Branch: `{identity['branch']}`",
                f"Verdict: `{scorecard['verdict']}`",
                "",
                "This package preserves executable evidence and adverse findings for IFVA-001.",
                "It does not authorize live trading and does not certify low-cost continuous paper trading.",
                "",
                "Primary review files:",
                "- `00_identity/00_repository_identity.json`",
                "- `08_canonical_runtime_traces/canonical_runtime_trace.json`",
                "- `19_audit_scorecards/audit_scorecard.json`",
                "- `18_known_defects_and_limitations/known_defects.json`",
                "- `22_manifests_and_hashes/evidence_hashes.sha256`",
                "",
            )
        ),
    )


def zip_package() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE_ROOT.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(PACKAGE_ROOT.parent))
    write_text(REPO_ROOT / "Documentation" / "IFVA-001_Evidence" / "ARGOS_FULL_CONSTITUTIONAL_AUDIT_EVIDENCE.zip.sha256", file_hash(ZIP_PATH) + "  " + ZIP_PATH.name + "\n")


def source_inventory() -> list[dict[str, Any]]:
    rows = []
    for path in sorted((REPO_ROOT / "src" / "argos").rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
            rows.append({"path": rel(path), "classes": classes, "functions": functions})
        except Exception as exc:
            rows.append({"path": rel(path), "parse_error": str(exc)})
    return rows


def discover_environment_names() -> list[str]:
    names = {"ARGOS_RUNTIME_MODE", "ARGOS_TRUTH_DOMAIN", "ARGOS_LIVE_TRADING_ENABLED"}
    for path in (REPO_ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in ("os.getenv(", "os.environ.get("):
            start = 0
            while True:
                idx = text.find(marker, start)
                if idx < 0:
                    break
                frag = text[idx + len(marker) : idx + len(marker) + 120]
                quote = "'" if "'" in frag[:5] else '"'
                if quote in frag:
                    parts = frag.split(quote)
                    if len(parts) > 1 and parts[1].isidentifier():
                        names.add(parts[1])
                start = idx + len(marker)
    return sorted(names)


def defect(defect_id: str, title: str, severity: str, evidence: Any) -> dict[str, Any]:
    return {"defect_id": defect_id, "title": title, "severity": severity, "status": "OPEN", "evidence": evidence}


def limitations_md(defects: list[dict[str, Any]]) -> str:
    return "# IFVA-001 Known Defects and Limitations\n\n" + "\n".join(f"- {item['defect_id']}: {item['title']} ({item['severity']})" for item in defects) + "\n"


def scorecard_md(scorecard: dict[str, Any]) -> str:
    return "\n".join(
        (
            "# IFVA-001 Audit Scorecard",
            "",
            f"Verdict: {scorecard['verdict']}",
            f"Candidate commit: {scorecard['candidate_commit_sha']}",
            f"Bridge verdict: {scorecard['bridge_verdict']}",
            f"Synthetic-truth verdict: {scorecard['synthetic_truth_verdict']}",
            f"Blocking defects: {scorecard['blocking_defect_count']}",
            "Live trading enabled: false",
            "Certifies low-cost continuous paper trading: false",
            "",
        )
    )


def identity_md(identity: dict[str, Any]) -> str:
    return "\n".join(
        (
            "# IFVA-001 Repository Identity",
            "",
            f"Repository: {identity['repository_name']}",
            f"Root: `{identity['repository_root']}`",
            f"Branch: `{identity['branch']}`",
            f"Candidate commit: `{identity['candidate_commit_sha']}`",
            f"Parent commit: `{identity['parent_commit_sha']}`",
            f"Tracked files: {identity['tracked_file_count']}",
            f"Untracked files at start: {identity['untracked_file_count']}",
            f"Modified files at start: {identity['modified_file_count']}",
            f"Python: {identity['python_version']}",
            f"Node: {identity['node_version']}",
            "Live trading status: disabled",
            "",
        )
    )


def run_command(command: tuple[str, ...], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout)
        return {
            "command": list(command),
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "duration_seconds": round(time.monotonic() - started, 3),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": list(command),
            "exit_code": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "duration_seconds": round(time.monotonic() - started, 3),
            "timed_out": True,
            "timeout_seconds": timeout,
        }
    except FileNotFoundError as exc:
        return {"command": list(command), "exit_code": None, "stdout": "", "stderr": str(exc), "duration_seconds": 0, "timed_out": False}


def command_stdout(command: tuple[str, ...], timeout: int) -> str:
    result = run_command(command, timeout)
    return (result.get("stdout") or result.get("stderr") or "").strip()


def command_log(command: tuple[str, ...], result: dict[str, Any]) -> str:
    return f"$ {' '.join(command)}\nexit={result.get('exit_code')} timed_out={result.get('timed_out')} duration={result.get('duration_seconds')}\n\nSTDOUT\n{result.get('stdout','')}\n\nSTDERR\n{result.get('stderr','')}\n"


def git_text(*args: str) -> str:
    return command_stdout(("git",) + args, 30)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(payload), indent=2, sort_keys=True, default=str), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, headers: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(headers), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    main()
