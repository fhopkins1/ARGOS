from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ORDER_ID = "HISTORIAN-ECS003-AUDIT-002"
OUTPUT_DIR = Path("Documentation") / "HISTORIAN_ECS003_AUDIT_002"
ATTACHMENT_PATH = Path(
    r"C:\Users\Fletc\.codex\attachments\1bce4325-e873-4bc0-86ab-b6a609691268\pasted-text.txt"
)
EXECUTION_UTC = "2026-07-31T23:20:00+00:00"

IMPLEMENTATION_ROOTS = (Path("src") / "argos" / "historian", Path("src") / "argos" / "control_panel")
EVIDENCE_INPUTS = (
    Path("Documentation") / "HISTORIAN_ECS003_AUDIT_001",
    Path("Documentation") / "HISTORIAN_MO001_INFORMATION_JOURNEY_HARDENING",
    Path("Documentation") / "HISTORIAN_RM002_IMPLEMENTATION_CERTIFICATION",
    Path("Documentation") / "HISTORIAN_RM003_ENTERPRISE_CERTIFICATION",
)


@dataclass(frozen=True)
class AuditFinding:
    finding_id: str
    severity: str
    finding_type: str
    governing_authority: str
    objective_evidence: tuple[dict[str, Any], ...]
    certification_impact: str
    deficiency_classification: str
    required_remediation: str


@dataclass(frozen=True)
class AuditReport:
    report_id: str
    title: str
    disposition: str
    objective_evidence: tuple[dict[str, Any], ...]
    findings: tuple[str, ...]


def _sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate_digest() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _implementation_files() -> tuple[Path, ...]:
    result: list[Path] = []
    for root in IMPLEMENTATION_ROOTS:
        if root.exists():
            result.extend(sorted(path for path in root.rglob("*.py") if path.is_file()))
    return tuple(result)


def _symbol_inventory(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    classes: list[str] = []
    functions: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
    return {
        "path": str(path),
        "sha256": _sha256(path),
        "classes": sorted(classes),
        "functions": sorted(functions),
    }


def _term_hits(terms: tuple[str, ...]) -> dict[str, list[str]]:
    hits = {term: [] for term in terms}
    for path in _implementation_files():
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for term in terms:
            if term.lower() in text or term.lower().replace(" ", "_") in text:
                hits[term].append(str(path))
    return hits


def _line(path: Path, needle: str, evidence_id: str) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines() if path.exists() else []
    lowered = needle.lower()
    for index, line in enumerate(lines, start=1):
        if lowered in line.lower():
            return {
                "evidence_id": evidence_id,
                "path": str(path),
                "line": index,
                "excerpt": line.strip()[:240],
                "evidence_type": "source_line",
            }
    return {
        "evidence_id": evidence_id,
        "path": str(path),
        "line": 0,
        "excerpt": f"Search text not found: {needle}",
        "evidence_type": "negative_source_search",
    }


def _source_index() -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "path": str(path),
            "exists": path.exists(),
            "file_count": len([item for item in path.rglob("*") if item.is_file()]) if path.exists() else 0,
        }
        for path in EVIDENCE_INPUTS
    )


def _finding(
    finding_id: str,
    finding_type: str,
    evidence: tuple[dict[str, Any], ...],
    impact: str,
    deficiency: str,
    remediation: str,
) -> AuditFinding:
    return AuditFinding(
        finding_id=finding_id,
        severity="BLOCKING",
        finding_type=finding_type,
        governing_authority="HISTORIAN-ECS003-AUDIT-002; ECS-003; HISTORIAN-MO-001; HISTORIAN-RM-002; HISTORIAN-RM-003",
        objective_evidence=evidence,
        certification_impact=impact,
        deficiency_classification=deficiency,
        required_remediation=remediation,
    )


def _build_findings() -> tuple[AuditFinding, ...]:
    baseline = _read_json(Path("Documentation") / "HISTORIAN_MO001_INFORMATION_JOURNEY_HARDENING" / "enterprise_information_journey_baseline.json")
    rm002 = _read_json(Path("Documentation") / "HISTORIAN_RM002_IMPLEMENTATION_CERTIFICATION" / "implementation_completeness_report.json")
    rm003 = _read_json(Path("Documentation") / "HISTORIAN_RM003_ENTERPRISE_CERTIFICATION" / "completion_report.json")
    journey_hits = _term_hits(tuple(baseline["canonical_record_families"]))
    edge_hits = _term_hits(tuple(baseline["graph_edge_classes"]))
    missing_hits = _term_hits(tuple(baseline["missing_information_states"]))
    typhon_hits = _term_hits(("TYPHON",))
    return (
        _finding(
            "HIST-ECS003-AUDIT002-FIND-001",
            "precondition_failure",
            (
                {"evidence_id": "HIST-AUDIT002-EVID-RM002", "rm002_final_disposition": rm002["final_disposition"], "rm003_authorized": rm002["rm003_authorized"], "blocking_findings": rm002["blocking_findings"]},
                {"evidence_id": "HIST-AUDIT002-EVID-RM003", "rm003_final_certification": rm003["final_certification"], "audit002_authorized": rm003["hist_ecs003_audit_002_authorized"]},
            ),
            "Final ECS-003 certification cannot pass because predecessor implementation and enterprise certification gates are not satisfied.",
            "certification deficiency",
            "Remediate RM-002 blockers and rerun RM-003 before requesting final independent certification.",
        ),
        _finding(
            "HIST-ECS003-AUDIT002-FIND-002",
            "enterprise_information_journey_behavior",
            ({"evidence_id": "HIST-AUDIT002-EVID-JOURNEY-HITS", "journey_record_family_hits": journey_hits},),
            "Enterprise Information Journey creation, accumulation, termination, and reconstruction cannot be behaviorally demonstrated.",
            "implementation deficiency",
            "Implement executable Journey Identity, Event, Reference, Graph Edge, and Certification Gate behavior with independent verifiers.",
        ),
        _finding(
            "HIST-ECS003-AUDIT002-FIND-003",
            "provenance_graph",
            ({"evidence_id": "HIST-AUDIT002-EVID-GRAPH-HITS", "graph_edge_hits": edge_hits},),
            "The mandatory provenance graph cannot be independently regenerated or replayed.",
            "implementation deficiency",
            "Implement all mandatory graph edge classes and deterministic graph reconstruction verification.",
        ),
        _finding(
            "HIST-ECS003-AUDIT002-FIND-004",
            "missing_information_language",
            (
                {"evidence_id": "HIST-AUDIT002-EVID-MISSING-HITS", "missing_information_hits": missing_hits},
                _line(Path("src") / "argos" / "historian" / "search_reconstruction.py", "canonical_query_text", "HIST-AUDIT002-EVID-LANGUAGE-001"),
            ),
            "Language preservation and full missing-information taxonomy preservation cannot be proven through execution.",
            "implementation deficiency",
            "Implement raw/structured/semantic/source language preservation and all MO-001 missing-information states.",
        ),
        _finding(
            "HIST-ECS003-AUDIT002-FIND-005",
            "historical_custody_cross_office",
            (
                {"evidence_id": "HIST-AUDIT002-EVID-CROSS-OFFICE-SCOPE", "required_offices": ("Sentinel", "Seeker", "Analyst", "Risk", "Authorization", "Trader", "Broker", "Monitoring", "Exit Decision", "Closed Position Truth", "Performance Truth", "Enterprise Learning", "Decision Laboratory", "Commander")},
            ),
            "Cross-office custody continuity and ownership continuity cannot be independently verified for every required office.",
            "implementation deficiency",
            "Materialize cross-office Historian interface and custody verifiers for every required office.",
        ),
        _finding(
            "HIST-ECS003-AUDIT002-FIND-006",
            "counterfactual_mutation_replay",
            (
                {"evidence_id": "HIST-AUDIT002-EVID-TYPHON-HITS", "typhon_hits": typhon_hits["TYPHON"]},
                _line(Path("src") / "argos" / "historian" / "search_reconstruction.py", "def reconstruct", "HIST-AUDIT002-EVID-RECONSTRUCT-001"),
            ),
            "Counterfactual replay, mutation validation, and fail-closed behavior cannot be fully exercised against absent Journey implementation.",
            "implementation deficiency",
            "Implement counterfactual path records, mutation detectors, and fail-closed Journey replay validation.",
        ),
        _finding(
            "HIST-ECS003-AUDIT002-FIND-007",
            "custody_only_violation_risk",
            (
                _line(Path("src") / "argos" / "control_panel" / "historian_recommendation_engine.py", "recommendationDatabase", "HIST-AUDIT002-EVID-RECOMMENDATION-001"),
                _line(Path("src") / "argos" / "control_panel" / "enterprise_learning_engine.py", "Historian Analysis", "HIST-AUDIT002-EVID-LEARNING-001"),
            ),
            "Historian-adjacent implementation still exposes analysis/recommendation semantics that conflict with custody-only certification unless formally reassigned.",
            "constitutional and implementation deficiency",
            "Separate learning/recommendation behavior from Historian custody implementation and verify custody-only boundaries.",
        ),
    )


def _reports(findings: tuple[AuditFinding, ...]) -> tuple[AuditReport, ...]:
    blocker_ids = tuple(f.finding_id for f in findings)
    common = (
        {"evidence_id": "HIST-AUDIT002-EVID-CANDIDATE", "candidate_digest": _candidate_digest()},
        {"evidence_id": "HIST-AUDIT002-EVID-SOURCE-INDEX", "submitted_evidence_inputs": _source_index()},
    )
    titles = (
        ("independent_repository_discovery_report", "Independent Repository Discovery Report"),
        ("independent_implementation_inventory", "Independent Implementation Inventory"),
        ("enterprise_information_journey_verification_report", "Enterprise Information Journey Verification Report"),
        ("historical_custody_verification_report", "Historical Custody Verification Report"),
        ("provenance_graph_verification_report", "Provenance Graph Verification Report"),
        ("historical_reconstruction_report", "Historical Reconstruction Report"),
        ("language_preservation_verification_report", "Language Preservation Verification Report"),
        ("missing_information_verification_report", "Missing Information Verification Report"),
        ("enterprise_learning_readiness_report", "Enterprise Learning Readiness Report"),
        ("counterfactual_readiness_report", "Counterfactual Readiness Report"),
        ("mutation_validation_report", "Mutation Validation Report"),
        ("fail_closed_validation_report", "Fail-Closed Validation Report"),
        ("deterministic_replay_report", "Deterministic Replay Report"),
        ("cross_office_verification_report", "Cross-Office Verification Report"),
        ("evidence_regeneration_report", "Evidence Regeneration Report"),
    )
    return tuple(
        AuditReport(
            report_id=report_id,
            title=title,
            disposition="FAIL",
            objective_evidence=common,
            findings=blocker_ids,
        )
        for report_id, title in titles
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return _json_ready(asdict(value))
    return value


def _write_json(name: str, data: Any) -> None:
    (OUTPUT_DIR / name).write_text(json.dumps(_json_ready(data), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    findings = _build_findings()
    reports = _reports(findings)
    inventory = tuple(_symbol_inventory(path) for path in _implementation_files())

    if ATTACHMENT_PATH.exists():
        (OUTPUT_DIR / "source_order.txt").write_text(ATTACHMENT_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    _write_json("independent_implementation_inventory.json", inventory)
    _write_json("certification_findings_register.json", findings)
    for report in reports:
        _write_json(f"{report.report_id}.json", report)
    _write_json(
        "mutation_validation_matrix.json",
        {
            "mutation_classes": (
                "historical_records",
                "provenance",
                "journey_identity",
                "ownership",
                "graph_relationships",
                "language_artifacts",
                "missing_information_classifications",
                "reconstruction_inputs",
                "replay_inputs",
                "certification_artifacts",
            ),
            "execution_disposition": "BLOCKED_BY_ABSENT_EXECUTABLE_JOURNEY_IMPLEMENTATION",
            "certification_consequence": "FAIL",
            "supporting_findings": [finding.finding_id for finding in findings],
        },
    )
    _write_json(
        "final_ecs003_certification_decision.json",
        {
            "order_id": ORDER_ID,
            "generated_at_utc": EXECUTION_UTC,
            "candidate_digest": _candidate_digest(),
            "decision": "FAIL",
            "previous_certification_assumed_valid": False,
            "constitutional_architecture_modified": False,
            "implementation_modified": False,
            "tests_rewritten": False,
            "finding_count": len(findings),
            "blocking_findings": [finding.finding_id for finding in findings],
            "basis": "Independent audit could not reproduce required Historian ECS-003 constitutional, implementation, behavioral, custody, provenance, replay, learning-readiness, counterfactual-readiness, mutation, and fail-closed guarantees.",
        },
    )
    manifest = {
        "order_id": ORDER_ID,
        "generated_at_utc": EXECUTION_UTC,
        "candidate_digest": _candidate_digest(),
        "deliverables": sorted(path.name for path in OUTPUT_DIR.iterdir() if path.is_file()),
        "finding_count": len(findings),
        "final_decision": "FAIL",
    }
    _write_json("audit_manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
