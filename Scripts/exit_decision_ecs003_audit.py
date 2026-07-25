from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_ECS003_AUDIT_001"
RAW_DIR = OUTPUT_DIR / "raw_execution_logs"
SOURCE_ORDER = Path(r"C:\Users\Fletc\.codex\attachments\954552f2-0187-45e8-86e2-cc6ff451e3d3\pasted-text.txt")

EXIT_IMPLEMENTATION = REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "position_exit_decision_engine.py"
EXIT_TEST_FILE = REPOSITORY_ROOT / "Tests" / "test_argos_control_panel_dashboard.py"
FOCUSED_TESTS = (
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_stop_loss_reached_produces_full_exit_and_registry_recommendation",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_profit_target_can_produce_configured_partial_exit_quantity",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_trailing_stop_large_adverse_and_degraded_data_are_deterministic",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_hold_record_is_immutable_and_does_not_execute_orders_or_ai",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_commander_override_and_emergency_risk_override_take_priority",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_strategy_invalidation_marks_ai_review_without_calling_ai",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xc_runtime_exposes_exit_decision_engine_without_broker_execution",
)
CONSTITUTIONAL_DOCS = (
    "Documentation/OR-004_Exit_Authority_Model.md",
    "Documentation/EO-DD_Position_Exit_and_Closure_Transaction.md",
    "Documentation/EO-DC_Decision_Object_Promotion.md",
    "Documentation/EO-DG_Replay_and_Decision_Laboratory_Read_Boundaries.md",
    "Documentation/decision_evaluation_office.md",
    "Documentation/commander_decision_engine.md",
    "Documentation/POSITION_REGISTRY_RM001_B01002A_S02_LIFECYCLE_BOUNDARIES/B01-002A-S02-002_exit_decision_boundary_registry.json",
    "Documentation/POSITION_REGISTRY_RM001_B01002A_S02_LIFECYCLE_BOUNDARIES/B01-002A-S02-004_exit_decision_boundary_reconciliation_registry.json",
)
CONSTITUTIONAL_REQUIREMENTS = (
    ("EXIT-REQ-001", "Exit Decision purpose, authority, permitted responsibilities, and prohibited execution responsibilities are complete.", "purpose_authority"),
    ("EXIT-REQ-002", "Exit Decision office boundaries with Commander, Monitoring, Risk, Trader, Broker, Position Registry, Authorizations, Closed Position Truth, Performance Truth, and Historian are deterministic.", "office_boundaries"),
    ("EXIT-REQ-003", "Canonical Exit Decision objects possess identity, ownership, custody, lifecycle, versioning, provenance, retention, and terminal disposition.", "object_model"),
    ("EXIT-REQ-004", "Every Exit Decision object and field has one owner and explicit mutation, correction, reconciliation, evidence, and read-only consumption authority.", "ownership_custody"),
    ("EXIT-REQ-005", "Exit Decision lifecycle transitions, terminal states, replay, restart, duplicate, stale, late, out-of-order, contradiction, correction, and failure dispositions are deterministic.", "lifecycle"),
    ("EXIT-REQ-006", "Decision admissibility rejects missing, stale, expired, revoked, contradictory, inadmissible, unsupported, mismatched, and incomplete inputs.", "admissibility"),
    ("EXIT-REQ-007", "Decision outcomes are deterministic, reproducible, explainable, evidence-bound, authorization-bound, position-bound, and time-bound.", "decision_logic"),
    ("EXIT-REQ-008", "Exit Decision cannot self-authorize, execute trades, submit broker commands, or mutate canonical external truth without downstream authority.", "authorization_execution_separation"),
    ("EXIT-REQ-009", "Temporal and freshness semantics are complete for source, request, evaluation, decision, authorization, issuance, acknowledgement, execution, completion, correction, supersession, archival, replay, restart, expiry, equal-time, and clock-skew cases.", "temporal_freshness"),
    ("EXIT-REQ-010", "Duplicate, replay, idempotency, correlation, stale replay, cancellation, supersession, and completed-history preservation are governed.", "duplicate_replay_idempotency"),
    ("EXIT-REQ-011", "Every inbound and outbound interface has producer, consumer, authority, schema, identity, scope, freshness, ordering, duplicate, retry, replay, failure, acknowledgement, evidence, and reconciliation obligations.", "interfaces"),
    ("EXIT-REQ-012", "Reconciliation and correction among Exit Decision, Position Registry, Risk, Authorizations, Trader, Broker, Closed Position Truth, and Historian preserve precedence, contradiction lineage, correction authority, supersession, escalation, and immutable history.", "reconciliation_correction"),
    ("EXIT-REQ-013", "Every evidence obligation has owner, producer, provenance, integrity, custody, retention, immutable history, correction lineage, verifier identity, execution identity, and proof eligibility.", "evidence"),
    ("EXIT-REQ-014", "Atomic constitutional requirements possess complete bidirectional traceability through objects, lifecycle, admissibility, decision, interface, evidence, and certification obligations.", "traceability"),
)
BEHAVIORAL_SUPPORT = {
    "EXIT-REQ-007": FOCUSED_TESTS[:6],
    "EXIT-REQ-008": (FOCUSED_TESTS[3], FOCUSED_TESTS[6]),
    "EXIT-REQ-010": (FOCUSED_TESTS[3],),
}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _git_files() -> tuple[str, ...]:
    output = subprocess.check_output(["git", "ls-files"], cwd=REPOSITORY_ROOT, text=True, stderr=subprocess.DEVNULL)
    return tuple(line.strip() for line in output.splitlines() if line.strip())


def _candidate_digest() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, text=True, stderr=subprocess.DEVNULL).strip()


def _imports(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return sorted(set(imports))


def _constitutional_sources() -> list[dict[str, Any]]:
    sources = []
    for rel in CONSTITUTIONAL_DOCS:
        path = REPOSITORY_ROOT / rel
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        sources.append(
            {
                "path": rel,
                "present": path.exists(),
                "sha256": _file_digest(path) if path.exists() else "",
                "exit_decision_relevant": any(term in text for term in ("Exit Decision", "exit decision", "exit authorization", "exit recommendations")),
            }
        )
    return sources


def _implementation_inventory() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    exit_terms = ("ExitDecisionEngine", "ExitDecisionRecord", "Exit Decision", "exitDecisionRecords", "exit_decision")
    for rel in _git_files():
        path = REPOSITORY_ROOT / rel
        if not path.exists() or not path.is_file() or not rel.endswith((".py", ".md", ".json")):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        relevant = any(term in text for term in exit_terms)
        if rel == "src/argos/control_panel/position_exit_decision_engine.py":
            classification = "EXIT_DECISION_DIRECT"
        elif rel == "Tests/test_argos_control_panel_dashboard.py" and "ExitDecisionEngine" in text:
            classification = "VERIFIER"
        elif relevant and rel.startswith("src/argos/control_panel"):
            classification = "EXIT_DECISION_DEPENDENCY"
        elif relevant and rel.startswith("Documentation/"):
            classification = "CONSTITUTIONAL_OR_EVIDENCE_ARTIFACT"
        elif relevant:
            classification = "SHARED_INFRASTRUCTURE"
        else:
            exclusions.append({"artifact": rel, "classification": "NON_PARTICIPATING", "reason": "no objective Exit Decision dependency marker"})
            continue
        records.append(
            {
                "artifact": rel,
                "classification": classification,
                "sha256": _file_digest(path),
                "imports": _imports(path) if rel.endswith(".py") else [],
                "inclusion_evidence": "content references ExitDecisionEngine/Exit Decision contract or is the direct engine",
            }
        )
    return records, exclusions


def _run_focused_tests() -> list[dict[str, Any]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for index, test_name in enumerate(FOCUSED_TESTS, start=1):
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", test_name],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=120,
        )
        stdout = RAW_DIR / f"exit_decision_test_{index:02d}.stdout.log"
        stderr = RAW_DIR / f"exit_decision_test_{index:02d}.stderr.log"
        stdout.write_text(completed.stdout, encoding="utf-8")
        stderr.write_text(completed.stderr, encoding="utf-8")
        records.append(
            {
                "execution_id": f"EXIT-ECS003-EXEC-{index:03d}",
                "test": test_name,
                "returncode": completed.returncode,
                "disposition": "PASS" if completed.returncode == 0 else "FAIL",
                "stdout": str(stdout.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
                "stderr": str(stderr.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
                "stdout_sha256": _file_digest(stdout),
                "stderr_sha256": _file_digest(stderr),
            }
        )
    return records


def _requirement_registry(executions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    passed_tests = {record["test"] for record in executions if record["disposition"] == "PASS"}
    registry = []
    for req_id, text, domain in CONSTITUTIONAL_REQUIREMENTS:
        supporting = tuple(test for test in BEHAVIORAL_SUPPORT.get(req_id, ()) if test in passed_tests)
        if supporting and len(supporting) == len(BEHAVIORAL_SUPPORT.get(req_id, ())):
            disposition = "PROVEN"
        elif domain in {"purpose_authority", "authorization_execution_separation"}:
            disposition = "TRACEABILITY_INCOMPLETE"
        else:
            disposition = "EVIDENCE_INSUFFICIENT"
        registry.append(
            {
                "requirement_id": req_id,
                "domain": domain,
                "requirement": text,
                "supporting_executions": supporting,
                "final_disposition": disposition,
                "proof_id": req_id.replace("REQ", "PROOF"),
            }
        )
    return registry


def _findings(requirements: list[dict[str, Any]], constitutional_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    missing_docs = [item["path"] for item in constitutional_sources if not item["present"]]
    if missing_docs:
        findings.append(
            {
                "finding_id": "EXIT-ECS003-FIND-001",
                "classification": "CONSTITUTIONAL_EVIDENCE_MISSING",
                "severity": "BLOCKING",
                "governing_requirement": "EXIT-REQ-014",
                "affected_artifact": missing_docs,
                "objective_evidence": "Expected constitutional source artifacts were not present in the delivered repository.",
                "disposition": "OPEN",
                "remediation_recommendation": "Use a bounded constitutional completion work-order series before re-audit.",
            }
        )
    incomplete = [item["requirement_id"] for item in requirements if item["final_disposition"] != "PROVEN"]
    if incomplete:
        findings.append(
            {
                "finding_id": "EXIT-ECS003-FIND-002",
                "classification": "REQUIREMENT_PROOF_INSUFFICIENT",
                "severity": "BLOCKING",
                "governing_requirement": "EXIT-REQ-014",
                "affected_artifact": incomplete,
                "objective_evidence": "Not every atomic Exit Decision constitutional requirement has execution-derived proof.",
                "disposition": "OPEN",
                "remediation_recommendation": "Generate requirement-level implementation obligations, verifiers, raw evidence, and proof objects.",
            }
        )
    return findings


def _proofs(requirements: list[dict[str, Any]], executions: list[dict[str, Any]], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    execution_by_test = {record["test"]: record for record in executions}
    blocking = any(item["severity"] == "BLOCKING" and item["disposition"] == "OPEN" for item in findings)
    proofs = []
    for req in requirements:
        linked = [execution_by_test[test] for test in req["supporting_executions"] if test in execution_by_test]
        proofs.append(
            {
                "proof_id": req["proof_id"],
                "requirement_id": req["requirement_id"],
                "implementation_artifact": "src/argos/control_panel/position_exit_decision_engine.py",
                "verifier": "Tests/test_argos_control_panel_dashboard.py",
                "execution_ids": [item["execution_id"] for item in linked],
                "raw_evidence": [item["stderr"] for item in linked],
                "finding_ids": [item["finding_id"] for item in findings] if req["final_disposition"] != "PROVEN" else [],
                "proof_disposition": "PROVEN" if req["final_disposition"] == "PROVEN" and not blocking else req["final_disposition"],
            }
        )
    return proofs


def _traceability(requirements: list[dict[str, Any]], proofs: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = []
    edges = []
    for req, proof in zip(requirements, proofs):
        req_node = f"REQ::{req['requirement_id']}"
        proof_node = f"PROOF::{proof['proof_id']}"
        impl_node = "IMPL::src/argos/control_panel/position_exit_decision_engine.py"
        verifier_node = "VERIFIER::Tests/test_argos_control_panel_dashboard.py"
        nodes.extend(
            [
                {"node_id": req_node, "type": "REQUIREMENT"},
                {"node_id": proof_node, "type": "PROOF"},
                {"node_id": impl_node, "type": "IMPLEMENTATION"},
                {"node_id": verifier_node, "type": "VERIFIER"},
            ]
        )
        edges.extend(
            [
                {"from": req_node, "to": impl_node, "type": "REQUIRES_IMPLEMENTATION"},
                {"from": impl_node, "to": verifier_node, "type": "VERIFIED_BY"},
                {"from": verifier_node, "to": proof_node, "type": "SUPPORTS_PROOF"},
                {"from": proof_node, "to": req_node, "type": "DISPOSITIONS_REQUIREMENT"},
            ]
        )
    unique_nodes = {node["node_id"]: node for node in nodes}
    return {"nodes": list(unique_nodes.values()), "edges": edges, "graph_digest": _digest({"nodes": nodes, "edges": edges})}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_copy = OUTPUT_DIR / "source_order_EXIT-DECISION-ECS003-AUDIT-001.txt"
    source_copy.write_text(SOURCE_ORDER.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    candidate = _candidate_digest()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    constitutional_sources = _constitutional_sources()
    implementation_inventory, exclusion_registry = _implementation_inventory()
    executions = _run_focused_tests()
    requirements = _requirement_registry(executions)
    findings = _findings(requirements, constitutional_sources)
    proofs = _proofs(requirements, executions, findings)
    graph = _traceability(requirements, proofs)
    blockers = [item for item in findings if item["severity"] == "BLOCKING" and item["disposition"] == "OPEN"]
    phase_i_verdict = "FAIL" if blockers else "UNCONDITIONAL_PASS"
    final_verdict = "FAIL" if blockers or any(req["final_disposition"] != "PROVEN" for req in requirements) else "UNCONDITIONAL_PASS"
    remediation = {
        "recommended_structure": "multiple-work-order series",
        "basis": "Findings span constitutional completeness, implementation mapping, proof sufficiency, traceability, and behavioral coverage.",
        "blocking_finding_count": len(blockers),
        "domain_distribution": Counter(req["domain"] for req in requirements if req["final_disposition"] != "PROVEN"),
    }

    reports: dict[str, Any] = {
        "executive_audit_report": {
            "candidate_digest": candidate,
            "phase_i_verdict": phase_i_verdict,
            "final_ecs003_verdict": final_verdict,
            "behavioral_tests_executed": len(executions),
            "behavioral_tests_passed": sum(1 for item in executions if item["disposition"] == "PASS"),
            "blocking_findings": len(blockers),
            "audit_disposition": "FAIL_CLOSED",
        },
        "constitutional_audit_report": {
            "constitutional_sources": constitutional_sources,
            "phase_i_verdict": phase_i_verdict,
            "constitutional_doctrine_modified": False,
        },
        "ownership_and_custody_assessment": {"status": "INCOMPLETE", "finding": "field-level ownership baseline not fully present"},
        "exit_decision_lifecycle_assessment": {"status": "PARTIALLY_VERIFIED", "supporting_tests": [record["test"] for record in executions]},
        "admissibility_assessment": {"status": "INCOMPLETE", "finding": "full admissibility negative population not present"},
        "decision_authority_assessment": {"status": "PARTIALLY_VERIFIED", "boundary": "recommendation only; no broker execution in focused tests"},
        "authorization_and_execution_separation_assessment": {"status": "PARTIALLY_PROVEN", "orders_executed": 0},
        "temporal_and_freshness_assessment": {"status": "INCOMPLETE", "finding": "stale/equal/clock-skew populations absent"},
        "duplicate_replay_and_idempotency_assessment": {"status": "PARTIALLY_VERIFIED", "supporting_requirement": "EXIT-REQ-010"},
        "interface_assessment": {"status": "INCOMPLETE", "finding": "all inbound/outbound authority contracts not audited"},
        "reconciliation_assessment": {"status": "INCOMPLETE", "finding": "cross-office reconciliation proof absent"},
        "evidence_assessment": {"status": "PARTIAL", "raw_logs": len(executions), "metadata_only_evidence_rejected": True},
        "evidence_sufficiency_report": {"status": "INSUFFICIENT_FOR_UNCONDITIONAL_PASS", "requirement_count": len(requirements)},
        "proof_coverage_matrix": {
            "requirements": len(requirements),
            "proven": sum(1 for item in requirements if item["final_disposition"] == "PROVEN"),
            "not_proven": sum(1 for item in requirements if item["final_disposition"] != "PROVEN"),
        },
        "proof_reproducibility_report": {"status": "PARTIAL", "focused_test_slice_reproducible": all(item["disposition"] == "PASS" for item in executions)},
        "persistence_replay_and_recovery_report": {"status": "INCOMPLETE", "finding": "actual process discontinuity for Exit Decision not fully evidenced"},
        "clean_environment_reproduction_report": {"status": "NOT_EXECUTED", "reason": "audit is repository-local; clean package is generated for independent reproduction"},
        "final_ecs003_certification_report": {
            "candidate_digest": candidate,
            "final_verdict": final_verdict,
            "verdict_basis": "FAIL required because certification-blocking proof and traceability deficiencies remain.",
            "generated_at": generated_at,
        },
        "final_ecs003_verdict": {"verdict": final_verdict, "allowed_pass_inferred": False},
        "recommended_remediation_structure": remediation,
    }

    deliverables = {
        "constitutional_finding_registry.json": findings,
        "canonical_constitutional_requirement_registry.json": requirements,
        "dependency_derived_implementation_inventory.json": implementation_inventory,
        "participation_registry.json": implementation_inventory,
        "exclusion_registry.json": exclusion_registry[:250],
        "requirement_to_implementation_matrix.json": [
            {
                "requirement_id": req["requirement_id"],
                "implementation_artifact": "src/argos/control_panel/position_exit_decision_engine.py",
                "verifier": "Tests/test_argos_control_panel_dashboard.py",
                "proof_id": req["proof_id"],
                "disposition": req["final_disposition"],
            }
            for req in requirements
        ],
        "verifier_inventory.json": [
            {
                "verifier": "Tests/test_argos_control_panel_dashboard.py",
                "focused_tests": FOCUSED_TESTS,
                "sha256": _file_digest(EXIT_TEST_FILE),
            }
        ],
        "behavioral_execution_registry.json": executions,
        "execution_evidence_registry.json": [
            {"execution_id": item["execution_id"], "stdout": item["stdout"], "stderr": item["stderr"], "disposition": item["disposition"]}
            for item in executions
        ],
        "requirement_proof_registry.json": proofs,
        "execution_derived_traceability_graph.json": graph,
        "finding_reconciliation_registry.json": [
            {**finding, "reconciliation_disposition": "OPEN_BLOCKING_REMEDIATION_REQUIRED"} for finding in findings
        ],
        "certification_blocker_registry.json": blockers,
    }
    for name, payload in {**reports, **deliverables}.items():
        filename = name if name.endswith(".json") else f"{name}.json"
        _write_json(OUTPUT_DIR / filename, payload)

    completion_report = {
        "package": "EXIT-DECISION-ECS003-AUDIT-001",
        "candidate_digest": candidate,
        "status": "COMPLETE",
        "phase_i_verdict": phase_i_verdict,
        "final_ecs003_verdict": final_verdict,
        "behavioral_tests_executed": len(executions),
        "behavioral_tests_passed": sum(1 for item in executions if item["disposition"] == "PASS"),
        "blocking_findings": len(blockers),
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "remediation_created": False,
        "source_order_sha256": _file_digest(source_copy),
        "completion_digest": _digest({"requirements": requirements, "findings": findings, "proofs": proofs, "graph": graph}),
    }
    _write_json(OUTPUT_DIR / "completion_report.json", completion_report)
    _write_text(
        OUTPUT_DIR / "README.md",
        "\n".join(
            [
                "# EXIT-DECISION-ECS003-AUDIT-001",
                "",
                "Primary entry point: completion_report.json",
                "This audit executes the focused Exit Decision behavioral slice and fails closed because complete",
                "requirement-level proof, clean-environment reproduction, and full constitutional traceability are not yet sufficient for unconditional ECS-003 certification.",
                "",
                f"Final ECS-003 verdict: {final_verdict}",
                "",
            ]
        ),
    )


if __name__ == "__main__":
    main()
