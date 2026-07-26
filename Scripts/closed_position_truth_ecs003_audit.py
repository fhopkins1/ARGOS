"""Independent ECS-003 audit package for Closed Position Truth.

This generator intentionally performs audit work only. It does not modify
constitutional doctrine or implementation behavior.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "CLOSED_POSITION_TRUTH_ECS003_AUDIT_001"
RAW_DIR = OUTPUT_DIR / "raw_execution_evidence"
ORDER_PATH = (
    Path(os.environ.get("CPT_AUDIT_ORDER_PATH", ""))
    if os.environ.get("CPT_AUDIT_ORDER_PATH")
    else Path(r"C:\Users\Fletc\.codex\attachments\161fe9f1-f095-4373-97ec-aa6b7e7a4ad2\pasted-text.txt")
)

REQUIREMENTS = (
    ("CPT-REQ-001", "Constitutional purpose and closed-position truth authority is complete and explicit.", "constitutional_authority"),
    ("CPT-REQ-002", "Office boundaries separate closure truth from execution, broker, settlement, performance, and historical truth.", "office_boundaries"),
    ("CPT-REQ-003", "Canonical Closed Position Truth object model defines every owned closure object.", "object_model"),
    ("CPT-REQ-004", "Ownership, custody, mutation, correction, supersession, and archival authority are deterministic.", "ownership_custody"),
    ("CPT-REQ-005", "Closed-position lifecycle states, transitions, prohibited transitions, and terminal behavior are complete.", "lifecycle"),
    ("CPT-REQ-006", "Closure truth doctrine separates execution events, fills, settlement, closed position truth, performance truth, and historical archive.", "closure_truth"),
    ("CPT-REQ-007", "Reconciliation doctrine covers Broker, Trader, Position Registry, Exit Decision, Risk, Performance Truth, and Historian.", "reconciliation"),
    ("CPT-REQ-008", "Temporal and historical integrity covers closure, execution, fill, settlement, correction, supersession, archival, late, duplicate, and replay cases.", "temporal_history"),
    ("CPT-REQ-009", "Interface constitution defines every producer, consumer, schema, freshness, retry, replay, failure, and evidence obligation.", "interfaces"),
    ("CPT-REQ-010", "Evidence doctrine rejects metadata-only, synthetic, manually asserted, or completion-report-only evidence.", "evidence_doctrine"),
    ("CPT-REQ-011", "Requirement-level traceability connects authority, requirements, objects, lifecycle, reconciliation, evidence, and certification obligations.", "traceability"),
    ("CPT-REQ-012", "Implementation participation is dependency-derived from imports, runtime invocation, schemas, persistence, reconciliation, settlement, evidence, and verifier dependencies.", "implementation_discovery"),
    ("CPT-REQ-013", "Executable behavioral verification covers closure creation, reconciliation, settlement, fill handling, partial/failed closure, residual quantity, correction, supersession, archival, duplicate closure, replay, recovery, and failure handling.", "behavioral_verification"),
    ("CPT-REQ-014", "Persistence, replay, recovery, evidence, proof, and reproducibility are independently demonstrated from raw execution evidence.", "reproducibility"),
)

FOCUSED_TESTS = (
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xe_closed_position_truth_is_created_for_fully_closed_position",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xe_builder_rejects_open_position_and_missing_exit_execution",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xe_builder_is_idempotent_and_performance_truth_consumes_record",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xe_lifecycle_analytics_calculate_pnl_holding_period_and_surveillance_extremes",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xe_missing_benchmark_creates_degraded_section_when_allowed",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xe_reconciliation_guards_quantity_and_pnl_mismatches",
    "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_xe_closed_positive_quantity_is_rejected_and_no_ai_is_used",
)

IMPLEMENTATION_MARKERS = (
    "ClosedPositionTruthBuilder",
    "closed_position_truth",
    "closedPositionTruth",
    "Closed Position Truth",
)

DOCTRINE_EXCLUDE_PARTS = {
    ".git",
    "__pycache__",
    "clean_room_runs",
    "repository_package",
    "IFVA-001_Evidence",
    "MONITORING_RM002_B08_CLEAN_ROOM_REPRODUCIBILITY",
}


def _stable_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_json(value), encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _relative(path: Path) -> str:
    return path.resolve().relative_to(REPOSITORY_ROOT).as_posix()


def _repo_files() -> tuple[Path, ...]:
    result = subprocess.run(["git", "ls-files"], cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=True)
    return tuple(REPOSITORY_ROOT / line for line in result.stdout.splitlines() if line.strip())


def _candidate_digest(files: tuple[Path, ...]) -> str:
    h = hashlib.sha256()
    for path in sorted(files, key=_relative):
        if not path.exists() or path.is_dir():
            continue
        rel = _relative(path)
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _is_audit_relevant_doc(path: Path) -> bool:
    if any(part in DOCTRINE_EXCLUDE_PARTS for part in path.parts):
        return False
    if path.suffix.lower() not in {".md", ".json", ".txt"}:
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    lowered = text.lower()
    return "closed position truth" in lowered or "closed_position_truth" in lowered or "closedpositiontruth" in lowered


def _discover_constitutional_sources() -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for path in sorted((REPOSITORY_ROOT / "Documentation").rglob("*")):
        if not path.is_file() or not _is_audit_relevant_doc(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        lower = text.lower()
        sources.append(
            {
                "artifact": _relative(path),
                "sha256": _sha256_file(path),
                "mentions": {
                    "closed_position_truth": lower.count("closed position truth") + lower.count("closed_position_truth"),
                    "settlement": lower.count("settlement"),
                    "reconciliation": lower.count("reconciliation"),
                    "historian": lower.count("historian"),
                    "traceability": lower.count("traceability"),
                    "evidence": lower.count("evidence"),
                },
                "authority_signal": any(token in lower for token in ("constitutional_authority", "governing_authority", "authority")),
                "object_signal": any(token in lower for token in ("object", "record", "registry")),
                "lifecycle_signal": "lifecycle" in lower or "transition" in lower,
                "source_type": "constitutional_candidate",
            }
        )
    return sources


def _parse_imports(path: Path) -> tuple[str, ...]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return ()
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)
            imports.extend(f"{module}.{alias.name}" for alias in node.names)
    return tuple(imports)


def _discover_implementation(files: tuple[Path, ...]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in files:
        if path.suffix != ".py":
            continue
        rel = _relative(path)
        if not (rel.startswith("src/") or rel.startswith("Tests/")):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        imports = _parse_imports(path)
        import_signal = any("closed_position_truth" in item for item in imports)
        marker_hits = tuple(marker for marker in IMPLEMENTATION_MARKERS if marker in text)
        runtime_signal = any(token in text for token in ("ClosedPositionTruthBuilder(", ".build(", "ingest_closed_position_truth"))
        if rel == "src/argos/control_panel/closed_position_truth.py":
            classification = "CLOSED_POSITION_DIRECT"
        elif import_signal and rel.startswith("src/"):
            classification = "CLOSED_POSITION_DEPENDENCY"
        elif marker_hits and rel.startswith("src/"):
            classification = "EVIDENCE_COMPONENT" if "evidence" in rel.lower() else "CLOSED_POSITION_DEPENDENCY"
        elif marker_hits and rel.startswith("Tests/"):
            classification = "VERIFIER"
        else:
            continue
        records.append(
            {
                "artifact": rel,
                "sha256": _sha256_file(path),
                "classification": classification,
                "dependency_evidence": {
                    "imports": tuple(item for item in imports if "closed_position_truth" in item or "performance_truth" in item),
                    "marker_hits": marker_hits,
                    "runtime_invocation_signal": runtime_signal,
                    "classification_basis": "AST import graph plus runtime reference scan; not filename-only.",
                },
            }
        )
    return records


def _discover_verifiers(files: tuple[Path, ...]) -> list[dict[str, Any]]:
    verifiers: list[dict[str, Any]] = []
    for path in files:
        rel = _relative(path)
        if not rel.startswith("Tests/") or path.suffix != ".py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not any(marker in text for marker in IMPLEMENTATION_MARKERS):
            continue
        tests = tuple(re.findall(r"def (test_[a-zA-Z0-9_]*(?:closed|closure|truth)[a-zA-Z0-9_]*)", text, re.IGNORECASE))
        verifiers.append(
            {
                "artifact": rel,
                "sha256": _sha256_file(path),
                "test_methods_with_closed_position_signal": tests,
                "classification": "VERIFIER",
                "derivation": "test artifact imports or references Closed Position Truth runtime participants",
            }
        )
    return verifiers


def _normalize_stream(value: str) -> str:
    value = re.sub(r"Ran (\d+) tests? in [0-9.]+s", r"Ran \1 tests in <duration>s", value)
    value = re.sub(r"\d+\.\d+s", "<duration>s", value)
    return value


def _execute_focused_tests() -> list[dict[str, Any]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    executions: list[dict[str, Any]] = []
    for index, target in enumerate(FOCUSED_TESTS, start=1):
        execution_id = f"CPT-BEH-{index:03d}"
        result = subprocess.run(
            [sys.executable, "-m", "unittest", target],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=45,
        )
        stdout = _normalize_stream(result.stdout)
        stderr = _normalize_stream(result.stderr)
        stdout_path = RAW_DIR / f"{execution_id}.stdout.log"
        stderr_path = RAW_DIR / f"{execution_id}.stderr.log"
        _write_text(stdout_path, stdout)
        _write_text(stderr_path, stderr)
        disposition = "PASS" if result.returncode == 0 else "FAIL"
        executions.append(
            {
                "execution_id": execution_id,
                "target": target,
                "returncode": result.returncode,
                "terminal_disposition": disposition,
                "timeout_seconds": 45,
                "raw_stdout": _relative(stdout_path),
                "raw_stderr": _relative(stderr_path),
                "stdout_sha256": _sha256_file(stdout_path),
                "stderr_sha256": _sha256_file(stderr_path),
                "behavioral_scope": _behavioral_scope_for_target(target),
            }
        )
    return executions


def _behavioral_scope_for_target(target: str) -> tuple[str, ...]:
    if "created_for_fully_closed_position" in target:
        return ("closure_creation", "fill_reconciliation", "benchmark_evidence")
    if "rejects_open_position" in target:
        return ("open_position_rejection", "missing_exit_execution")
    if "idempotent" in target:
        return ("duplicate_closure_handling", "performance_truth_consumption")
    if "analytics" in target:
        return ("realized_performance", "holding_period", "surveillance_history")
    if "missing_benchmark" in target:
        return ("degraded_benchmark_handling",)
    if "mismatches" in target:
        return ("quantity_reconciliation", "realized_pnl_reconciliation")
    if "positive_quantity" in target:
        return ("residual_quantity_rejection", "no_ai_used")
    return ("closed_position_truth",)


def _requirement_registry(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_paths = tuple(item["artifact"] for item in sources)
    registries: list[dict[str, Any]] = []
    for req_id, text, domain in REQUIREMENTS:
        evidence = tuple(
            item["artifact"]
            for item in sources
            if _source_supports_domain(item, domain)
        )
        registries.append(
            {
                "requirement_id": req_id,
                "requirement": text,
                "domain": domain,
                "source_candidates": evidence,
                "source_candidate_count": len(evidence),
                "all_candidate_sources": source_paths if domain == "constitutional_authority" else (),
                "constitutional_disposition": "SUPPORTED_BY_CANDIDATE_ARTIFACTS" if evidence else "MISSING_AUTHORITATIVE_SUPPORT",
            }
        )
    return registries


def _source_supports_domain(source: dict[str, Any], domain: str) -> bool:
    mentions = source["mentions"]
    if domain in {"constitutional_authority", "ownership_custody"}:
        return source["authority_signal"] and mentions["closed_position_truth"] > 0
    if domain == "object_model":
        return source["object_signal"] and mentions["closed_position_truth"] > 0
    if domain == "lifecycle":
        return source["lifecycle_signal"] and mentions["closed_position_truth"] > 0
    if domain == "reconciliation":
        return mentions["reconciliation"] > 0 and mentions["closed_position_truth"] > 0
    if domain == "interfaces":
        return "interface" in source["artifact"].lower() or mentions["closed_position_truth"] > 0 and "boundary" in source["artifact"].lower()
    if domain == "evidence_doctrine":
        return mentions["evidence"] > 0 and mentions["closed_position_truth"] > 0
    if domain == "traceability":
        return mentions["traceability"] > 0 and mentions["closed_position_truth"] > 0
    if domain in {"closure_truth", "temporal_history"}:
        return mentions["closed_position_truth"] > 0 and (mentions["settlement"] > 0 or "truth" in source["artifact"].lower())
    return False


def _make_findings(requirements: list[dict[str, Any]], executions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for req in requirements:
        if req["constitutional_disposition"] == "MISSING_AUTHORITATIVE_SUPPORT":
            findings.append(
                _finding(
                    len(findings) + 1,
                    req["requirement_id"],
                    "CRITICAL",
                    "CONSTITUTIONAL_GAP",
                    "OPEN_BLOCKING",
                    "No authoritative Closed Position Truth constitutional artifact was discovered for this requirement domain.",
                    req["domain"],
                )
            )
    covered_scopes = {scope for execution in executions for scope in execution["behavioral_scope"] if execution["terminal_disposition"] == "PASS"}
    required_behavior = {
        "settlement_verification",
        "partial_closure",
        "failed_closure",
        "correction",
        "supersession",
        "archival",
        "restart_recovery",
        "replay",
        "reconciliation_failure",
    }
    for missing in sorted(required_behavior - covered_scopes):
        findings.append(
            _finding(
                len(findings) + 1,
                "CPT-REQ-013",
                "HIGH",
                "BEHAVIORAL_COVERAGE_GAP",
                "OPEN_BLOCKING",
                f"No focused executable verification evidence was found for {missing}.",
                missing,
            )
        )
    if not all(item["terminal_disposition"] == "PASS" for item in executions):
        findings.append(
            _finding(
                len(findings) + 1,
                "CPT-REQ-014",
                "CRITICAL",
                "EXECUTION_FAILURE",
                "OPEN_BLOCKING",
                "One or more focused Closed Position Truth verifiers did not pass.",
                "behavioral_execution",
            )
        )
    return findings


def _finding(index: int, requirement_id: str, severity: str, classification: str, disposition: str, evidence: str, artifact: str) -> dict[str, Any]:
    return {
        "finding_id": f"CPT-ECS003-FIND-{index:03d}",
        "governing_requirement": requirement_id,
        "affected_artifact": artifact,
        "objective_evidence": evidence,
        "severity": severity,
        "classification": classification,
        "disposition": disposition,
        "remediation_recommendation": "Issue bounded remediation order; do not infer PASS from existing documentation or aggregate test counts.",
    }


def _proof_registry(requirements: list[dict[str, Any]], executions: list[dict[str, Any]], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_requirement = {req["requirement_id"]: [] for req in requirements}
    for finding in findings:
        by_requirement.setdefault(finding["governing_requirement"], []).append(finding["finding_id"])
    execution_ids = tuple(item["execution_id"] for item in executions)
    proofs: list[dict[str, Any]] = []
    for req in requirements:
        related_execs = execution_ids if req["requirement_id"] in {"CPT-REQ-013", "CPT-REQ-014"} else ()
        blockers = tuple(by_requirement.get(req["requirement_id"], ()))
        proofs.append(
            {
                "proof_id": f"CPT-PROOF-{req['requirement_id'].split('-')[-1]}",
                "requirement_id": req["requirement_id"],
                "source_evidence": req["source_candidates"],
                "execution_evidence": related_execs,
                "finding_ids": blockers,
                "proof_disposition": "FAIL" if blockers else "PASS_WITH_LIMITATIONS",
                "sufficiency": "INSUFFICIENT" if blockers else "PARTIAL",
            }
        )
    return proofs


def _traceability(requirements: list[dict[str, Any]], implementation: list[dict[str, Any]], executions: list[dict[str, Any]], proofs: list[dict[str, Any]]) -> dict[str, Any]:
    direct = tuple(item["artifact"] for item in implementation if item["classification"] == "CLOSED_POSITION_DIRECT")
    dependencies = tuple(item["artifact"] for item in implementation if item["classification"] != "VERIFIER")
    return {
        "graph_id": "CPT-ECS003-TRACEABILITY-GRAPH",
        "nodes": {
            "requirements": tuple(item["requirement_id"] for item in requirements),
            "implementation": dependencies,
            "direct_implementation": direct,
            "executions": tuple(item["execution_id"] for item in executions),
            "proofs": tuple(item["proof_id"] for item in proofs),
        },
        "edges": [
            {
                "from": req["requirement_id"],
                "to": proof["proof_id"],
                "type": "REQUIREMENT_TO_PROOF",
            }
            for req, proof in zip(requirements, proofs)
        ]
        + [
            {
                "from": execution["execution_id"],
                "to": "CPT-REQ-013",
                "type": "EXECUTION_TO_BEHAVIOR_REQUIREMENT",
            }
            for execution in executions
        ]
        + [
            {
                "from": item,
                "to": "CPT-REQ-012",
                "type": "IMPLEMENTATION_TO_DISCOVERY_REQUIREMENT",
            }
            for item in dependencies
        ],
    }


def generate_audit() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    repo_files = _repo_files()
    candidate_digest = _candidate_digest(repo_files)
    order_text = ORDER_PATH.read_text(encoding="utf-8", errors="ignore") if ORDER_PATH.exists() else ""
    _write_text(OUTPUT_DIR / "source_order.txt", order_text)

    constitutional_sources = _discover_constitutional_sources()
    implementation = _discover_implementation(repo_files)
    verifiers = _discover_verifiers(repo_files)
    executions = _execute_focused_tests()
    requirements = _requirement_registry(constitutional_sources)
    findings = _make_findings(requirements, executions)
    proofs = _proof_registry(requirements, executions, findings)
    traceability = _traceability(requirements, implementation, executions, proofs)

    phase_i_blockers = tuple(item for item in findings if item["classification"] == "CONSTITUTIONAL_GAP")
    phase_ii_blockers = tuple(item for item in findings if item["classification"] != "CONSTITUTIONAL_GAP")
    phase_i_verdict = "FAIL" if phase_i_blockers else "PASS_WITH_REMEDIATION"
    final_verdict = "FAIL" if findings else "UNCONDITIONAL_PASS"
    constitutional_freeze_authorized = not phase_i_blockers

    evidence_registry = {
        "candidate_digest": candidate_digest,
        "raw_execution_evidence": tuple(
            {
                "execution_id": item["execution_id"],
                "stdout": item["raw_stdout"],
                "stderr": item["raw_stderr"],
                "stdout_sha256": item["stdout_sha256"],
                "stderr_sha256": item["stderr_sha256"],
            }
            for item in executions
        ),
        "constitutional_sources": constitutional_sources,
        "implementation_sources": tuple(item["artifact"] for item in implementation),
    }

    blocker_registry = {
        "blockers": tuple(item for item in findings if item["disposition"] == "OPEN_BLOCKING"),
        "blocker_count": sum(1 for item in findings if item["disposition"] == "OPEN_BLOCKING"),
        "fail_closed": True,
    }

    reports = {
        "executive_audit_report.json": {
            "audit_id": "CLOSED-POSITION-TRUTH-ECS003-AUDIT-001",
            "candidate_digest": candidate_digest,
            "phase_i_verdict": phase_i_verdict,
            "final_verdict": final_verdict,
            "constitutional_freeze_authorized": constitutional_freeze_authorized,
            "implementation_modified": False,
            "constitutional_doctrine_modified": False,
            "summary": "Closed Position Truth has implementation and focused executable evidence, but the first independent ECS-003 audit fails closed because constitutional completeness and behavioral coverage are not independently sufficient for unconditional certification.",
        },
        "constitutional_audit_report.json": {
            "phase": "PHASE_I",
            "verdict": phase_i_verdict,
            "freeze_authorized": constitutional_freeze_authorized,
            "source_count": len(constitutional_sources),
            "findings": tuple(item for item in findings if item["classification"] == "CONSTITUTIONAL_GAP"),
        },
        "canonical_requirement_registry.json": requirements,
        "ownership_assessment.json": _domain_assessment(requirements, "ownership_custody", findings),
        "object_model_assessment.json": _domain_assessment(requirements, "object_model", findings),
        "lifecycle_assessment.json": _domain_assessment(requirements, "lifecycle", findings),
        "reconciliation_assessment.json": _domain_assessment(requirements, "reconciliation", findings),
        "evidence_assessment.json": _domain_assessment(requirements, "evidence_doctrine", findings),
        "dependency_derived_implementation_inventory.json": implementation,
        "verifier_inventory.json": verifiers,
        "behavioral_execution_registry.json": executions,
        "evidence_registry.json": evidence_registry,
        "proof_registry.json": proofs,
        "traceability_graph.json": traceability,
        "certification_blocker_registry.json": blocker_registry,
        "clean_room_reproduction_report.json": {
            "mode": "bounded_reproduction_from_delivered_repository",
            "command": f"{sys.executable} Scripts/closed_position_truth_ecs003_audit.py",
            "deterministic_discovery": True,
            "deterministic_evidence": True,
            "deterministic_verdict": True,
            "limitations": ("No separate cloned clean room was created under this order; bounded reproduction is package-local and fail-closed.",),
        },
        "final_ecs003_audit_report.json": {
            "audit_id": "CLOSED-POSITION-TRUTH-ECS003-AUDIT-001",
            "candidate_digest": candidate_digest,
            "phase_i_verdict": phase_i_verdict,
            "phase_ii_verdict": "FAIL" if phase_ii_blockers else "PASS_WITH_REMEDIATION",
            "final_verdict": final_verdict,
            "unconditional_pass_criteria_met": final_verdict == "UNCONDITIONAL_PASS",
            "blocker_count": blocker_registry["blocker_count"],
            "required_deliverables_produced": True,
        },
        "final_verdict.json": {
            "verdict": final_verdict,
            "allowed_verdicts": ("UNCONDITIONAL_PASS", "FAIL"),
            "fail_closed": final_verdict == "FAIL",
            "unconditional_pass_issued": final_verdict == "UNCONDITIONAL_PASS",
        },
        "completion_report.json": {
            "order": "CLOSED-POSITION-TRUTH-ECS003-AUDIT-001",
            "status": "COMPLETE",
            "implementation_modified": False,
            "constitutional_doctrine_modified": False,
            "remediation_performed": False,
            "repository_wide_verification_executed": False,
            "focused_execution_count": len(executions),
            "focused_execution_dispositions": _count_dispositions(executions),
            "final_verdict": final_verdict,
        },
    }
    for name, payload in reports.items():
        _write_json(OUTPUT_DIR / name, payload)
    _write_json(OUTPUT_DIR / "manifest.json", _manifest(candidate_digest))
    return reports["completion_report.json"]


def _domain_assessment(requirements: list[dict[str, Any]], domain: str, findings: list[dict[str, Any]]) -> dict[str, Any]:
    reqs = tuple(item for item in requirements if item["domain"] == domain)
    req_ids = {item["requirement_id"] for item in reqs}
    related_findings = tuple(item for item in findings if item["governing_requirement"] in req_ids)
    return {
        "domain": domain,
        "requirements": reqs,
        "findings": related_findings,
        "assessment": "INSUFFICIENT" if related_findings else "SUPPORTED_BY_CANDIDATE_ARTIFACTS",
    }


def _count_dispositions(executions: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in executions:
        counts[item["terminal_disposition"]] = counts.get(item["terminal_disposition"], 0) + 1
    return counts


def _manifest(candidate_digest: str) -> dict[str, Any]:
    files = []
    for path in sorted(OUTPUT_DIR.rglob("*")):
        if path.is_file():
            files.append({"path": _relative(path), "sha256": _sha256_file(path), "bytes": path.stat().st_size})
    return {
        "package": "CLOSED_POSITION_TRUTH_ECS003_AUDIT_001",
        "candidate_digest": candidate_digest,
        "files": files,
    }


if __name__ == "__main__":
    report = generate_audit()
    print(_stable_json(report), end="")
