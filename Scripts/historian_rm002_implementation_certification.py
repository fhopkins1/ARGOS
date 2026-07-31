from __future__ import annotations

import ast
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ORDER_ID = "HISTORIAN-RM-002"
OUTPUT_DIR = Path("Documentation") / "HISTORIAN_RM002_IMPLEMENTATION_CERTIFICATION"
ATTACHMENT_PATH = Path(
    r"C:\Users\Fletc\.codex\attachments\bea98e14-4cb7-4e5f-9a66-26ea99c69fbb\pasted-text.txt"
)
BASELINE_PATH = Path("Documentation") / "HISTORIAN_MO001_INFORMATION_JOURNEY_HARDENING" / "enterprise_information_journey_baseline.json"
EXECUTION_UTC = "2026-07-31T14:35:00+00:00"

HISTORIAN_SRC = Path("src") / "argos" / "historian"
CONTROL_PANEL_SRC = Path("src") / "argos" / "control_panel"

IMPLEMENTATION_FILES = (
    HISTORIAN_SRC / "__init__.py",
    HISTORIAN_SRC / "search_reconstruction.py",
    HISTORIAN_SRC / "readiness.py",
    HISTORIAN_SRC / "prompt_evaluation.py",
    HISTORIAN_SRC / "performance.py",
    HISTORIAN_SRC / "model_calibration.py",
    HISTORIAN_SRC / "hypothesis.py",
    HISTORIAN_SRC / "group.py",
    HISTORIAN_SRC / "fusion.py",
    HISTORIAN_SRC / "evidence_evaluation.py",
    HISTORIAN_SRC / "decision_evaluation.py",
    CONTROL_PANEL_SRC / "historian_recommendation_engine.py",
    CONTROL_PANEL_SRC / "enterprise_learning_engine.py",
)


@dataclass(frozen=True)
class ImplementationArtifact:
    artifact_id: str
    path: str
    exists: bool
    classes: tuple[str, ...]
    functions: tuple[str, ...]
    imports: tuple[str, ...]
    digest: str


@dataclass(frozen=True)
class VerificationResult:
    order_id: str
    title: str
    disposition: str
    verified_items: tuple[str, ...]
    failed_items: tuple[str, ...]
    objective_evidence: tuple[dict[str, Any], ...]
    findings: tuple[dict[str, Any], ...]


def _file_digest(path: Path) -> str:
    import hashlib

    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_artifact(path: Path) -> ImplementationArtifact:
    if not path.exists():
        return ImplementationArtifact(_artifact_id(path), str(path), False, (), (), (), "MISSING")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    classes: list[str] = []
    functions: list[str] = []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return ImplementationArtifact(
        _artifact_id(path),
        str(path),
        True,
        tuple(sorted(set(classes))),
        tuple(sorted(set(functions))),
        tuple(sorted(set(item for item in imports if item))),
        _file_digest(path),
    )


def _artifact_id(path: Path) -> str:
    return "HIST-IMPL-" + path.as_posix().upper().replace("/", "-").replace(".", "-").replace(" ", "-")


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _line_evidence(path: Path, needle: str, evidence_id: str) -> dict[str, Any]:
    lines = _read_text(path).splitlines()
    needle_lower = needle.lower()
    for index, line in enumerate(lines, start=1):
        if needle_lower in line.lower():
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


def _repository_digest() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _load_baseline() -> dict[str, Any]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _contains_any(artifacts: tuple[ImplementationArtifact, ...], terms: tuple[str, ...]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {term: [] for term in terms}
    for artifact in artifacts:
        if not artifact.exists:
            continue
        text = _read_text(Path(artifact.path)).lower()
        symbol_text = " ".join(artifact.classes + artifact.functions).lower()
        for term in terms:
            normalized = term.lower().replace(" ", "_")
            if term.lower() in text or normalized in text or normalized in symbol_text:
                hits[term].append(artifact.path)
    return hits


def _finding(finding_id: str, category: str, severity: str, deficiency: str, evidence: tuple[dict[str, Any], ...], remediation: str) -> dict[str, Any]:
    return {
        "finding_id": finding_id,
        "category": category,
        "severity": severity,
        "constitutional_deficiency": deficiency,
        "governing_authority": "HISTORIAN-RM-002; HISTORIAN-MO-001; Enterprise Constitutional Standard ECS-003",
        "objective_evidence": list(evidence),
        "certification_impact": "Blocks Historian implementation certification until remediated or formally dispositioned.",
        "recommended_remediation_objective": remediation,
        "status": "OPEN",
    }


def _verification_results(artifacts: tuple[ImplementationArtifact, ...], baseline: dict[str, Any]) -> tuple[VerificationResult, ...]:
    journey_terms = (
        "Enterprise Information Journey",
        "Journey Identity",
        "Journey Event",
        "Journey Reference",
        "Journey Graph Edge",
        "Journey Certification Gate",
    )
    journey_hits = _contains_any(artifacts, journey_terms)
    edge_terms = tuple(baseline["graph_edge_classes"])
    edge_hits = _contains_any(artifacts, edge_terms)
    missing_terms = tuple(baseline["missing_information_states"])
    missing_hits = _contains_any(artifacts, missing_terms)
    prohibition_terms = tuple(baseline["historian_prohibitions"])
    prohibition_hits = _contains_any(artifacts, prohibition_terms)

    implementation_evidence = (
        {
            "evidence_id": "HIST-RM002-EVID-INVENTORY-001",
            "evidence_type": "implementation_inventory",
            "artifact_count": len(artifacts),
            "existing_artifact_count": len([artifact for artifact in artifacts if artifact.exists]),
            "class_count": sum(len(artifact.classes) for artifact in artifacts),
            "function_count": sum(len(artifact.functions) for artifact in artifacts),
        },
        _line_evidence(HISTORIAN_SRC / "search_reconstruction.py", "HistoricalReconstruction", "HIST-RM002-EVID-RECONSTRUCTION-001"),
        _line_evidence(CONTROL_PANEL_SRC / "historian_recommendation_engine.py", "Historian Recommendation Engine", "HIST-RM002-EVID-RECOMMENDATION-001"),
    )

    journey_failed = tuple(term for term, paths in journey_hits.items() if not paths)
    graph_failed = tuple(term for term, paths in edge_hits.items() if not paths)
    missing_failed = tuple(term for term, paths in missing_hits.items() if not paths)
    custody_artifacts = (
        "Sentinel Events",
        "Authorization Objects",
        "Broker Objects",
        "Execution Events",
        "Decision Laboratory artifacts",
    )

    results = [
        VerificationResult(
            "HISTORIAN-RM-002-B01",
            "Repository and Historical Inventory Verification",
            "VERIFIED_WITH_FINDINGS",
            tuple(artifact.path for artifact in artifacts if artifact.exists),
            (),
            implementation_evidence,
            (
                _finding(
                    "HIST-RM002-FIND-B01-001",
                    "implementation_inventory",
                    "MAJOR",
                    "Historian implementation artifacts exist, but the inventory is dominated by evaluation, learning, recommendation, and reconstruction modules rather than a complete Enterprise Information Journey implementation.",
                    implementation_evidence,
                    "Create explicit Journey implementation artifacts and bind existing reconstruction modules to the hardened Journey baseline.",
                ),
            ),
        ),
        VerificationResult(
            "HISTORIAN-RM-002-B02",
            "Enterprise Information Journey Verification",
            "FAIL",
            tuple(term for term, paths in journey_hits.items() if paths),
            journey_failed,
            (
                {"evidence_id": "HIST-RM002-EVID-B02-JOURNEY-HITS", "journey_term_hits": journey_hits},
                _line_evidence(HISTORIAN_SRC / "search_reconstruction.py", "HistoricalReconstruction", "HIST-RM002-EVID-B02-RECONSTRUCTION"),
            ),
            (
                _finding(
                    "HIST-RM002-FIND-B02-001",
                    "enterprise_information_journey",
                    "BLOCKING",
                    "The implementation does not expose the hardened Enterprise Information Journey record families required by HISTORIAN-MO-001.",
                    ({"evidence_id": "HIST-RM002-EVID-B02-JOURNEY-HITS", "journey_term_hits": journey_hits},),
                    "Implement Journey Identity, Event, Reference, Graph Edge, and Certification Gate records with lifecycle, supersession, archival, and reconstruction behavior.",
                ),
            ),
        ),
        VerificationResult(
            "HISTORIAN-RM-002-B03",
            "Historical Custody Verification",
            "FAIL",
            ("Closed Position Truth custody references", "Exit Decision historical custody references"),
            custody_artifacts,
            (
                {"evidence_id": "HIST-RM002-EVID-B03-CUSTODY-SCOPE", "required_artifact_classes": custody_artifacts},
                _line_evidence(HISTORIAN_SRC / "__init__.py", "Historian Group scientific evaluation organization", "HIST-RM002-EVID-B03-MODULE-MISSION"),
            ),
            (
                _finding(
                    "HIST-RM002-FIND-B03-001",
                    "historical_custody",
                    "BLOCKING",
                    "No implementation-level custody registry proves exactly one constitutional custodian for every historical artifact class required by RM-002-B03.",
                    ({"evidence_id": "HIST-RM002-EVID-B03-CUSTODY-SCOPE", "required_artifact_classes": custody_artifacts},),
                    "Materialize a Historian custody registry and verifier covering every required artifact class.",
                ),
            ),
        ),
        VerificationResult(
            "HISTORIAN-RM-002-B04",
            "Provenance and Historical Graph Verification",
            "FAIL",
            tuple(term for term, paths in edge_hits.items() if paths),
            graph_failed,
            ({"evidence_id": "HIST-RM002-EVID-B04-GRAPH-HITS", "graph_edge_hits": edge_hits},),
            (
                _finding(
                    "HIST-RM002-FIND-B04-001",
                    "provenance_graph",
                    "BLOCKING",
                    "The implementation does not demonstrate all hardened provenance graph edge classes.",
                    ({"evidence_id": "HIST-RM002-EVID-B04-GRAPH-HITS", "graph_edge_hits": edge_hits},),
                    "Implement and verify identity-bound graph nodes and all mandatory Journey graph edge classes.",
                ),
            ),
        ),
        VerificationResult(
            "HISTORIAN-RM-002-B05",
            "Historical Completeness Verification",
            "FAIL",
            ("failed_searches", "skipped_searches", "conflicts_known_at_cutoff"),
            ("ignored opportunities", "denied authorizations", "dormant observations", "rejected alternatives", "information deficiencies"),
            (
                _line_evidence(HISTORIAN_SRC / "search_reconstruction.py", "failed_searches", "HIST-RM002-EVID-B05-FAILED-SEARCHES"),
                _line_evidence(HISTORIAN_SRC / "search_reconstruction.py", "skipped_searches", "HIST-RM002-EVID-B05-SKIPPED-SEARCHES"),
            ),
            (
                _finding(
                    "HIST-RM002-FIND-B05-001",
                    "historical_completeness",
                    "BLOCKING",
                    "Historical search reconstruction preserves some failed and skipped search states, but does not prove complete preservation of rejected actions, ignored opportunities, denied authorizations, dormant observations, and rejected alternatives.",
                    (
                        _line_evidence(HISTORIAN_SRC / "search_reconstruction.py", "failed_searches", "HIST-RM002-EVID-B05-FAILED-SEARCHES"),
                    ),
                    "Add negative-history record families and verifiers for every RM-002-B05 historical completeness class.",
                ),
            ),
        ),
        VerificationResult(
            "HISTORIAN-RM-002-B06",
            "Language and Missing-Information Verification",
            "FAIL",
            tuple(term for term, paths in missing_hits.items() if paths),
            missing_failed,
            (
                {"evidence_id": "HIST-RM002-EVID-B06-MISSING-HITS", "missing_information_hits": missing_hits},
                _line_evidence(HISTORIAN_SRC / "search_reconstruction.py", "canonical_query_text", "HIST-RM002-EVID-B06-LANGUAGE"),
            ),
            (
                _finding(
                    "HIST-RM002-FIND-B06-001",
                    "language_missing_information",
                    "BLOCKING",
                    "The implementation does not preserve every hardened missing-information state and does not expose raw, structured, semantic, interpretation, and truth language layers as required.",
                    ({"evidence_id": "HIST-RM002-EVID-B06-MISSING-HITS", "missing_information_hits": missing_hits},),
                    "Implement language-layer preservation and the complete HIST-MO-001 missing-information taxonomy.",
                ),
            ),
        ),
        VerificationResult(
            "HISTORIAN-RM-002-B07",
            "Historical Reconstruction and Replay Verification",
            "VERIFIED_WITH_FINDINGS",
            ("HistoricalSearchRecord", "HistoricalInformationCutoff", "HistoricalReconstruction", "HistorianSearchArchive.reconstruct"),
            ("complete Enterprise Information Journey reconstruction", "counterfactual input reconstruction"),
            (
                _line_evidence(HISTORIAN_SRC / "search_reconstruction.py", "class HistorianSearchArchive", "HIST-RM002-EVID-B07-ARCHIVE"),
                _line_evidence(HISTORIAN_SRC / "search_reconstruction.py", "def reconstruct", "HIST-RM002-EVID-B07-RECONSTRUCT"),
            ),
            (
                _finding(
                    "HIST-RM002-FIND-B07-001",
                    "reconstruction_replay",
                    "MAJOR",
                    "Search reconstruction exists, but no verifier proves complete Enterprise Information Journey, provenance graph, workflow history, replay input, and counterfactual input reconstruction.",
                    (
                        _line_evidence(HISTORIAN_SRC / "search_reconstruction.py", "def reconstruct", "HIST-RM002-EVID-B07-RECONSTRUCT"),
                    ),
                    "Extend reconstruction from search archive scope to full Journey graph replay and counterfactual reconstruction scope.",
                ),
            ),
        ),
        VerificationResult(
            "HISTORIAN-RM-002-B08",
            "Interface Verification",
            "FAIL",
            ("Performance Truth read boundary", "Closed Position Truth archival references"),
            ("Sentinel", "Authorization", "Trader", "Broker", "Monitoring", "Decision Laboratory", "Commander"),
            (
                _line_evidence(Path("Documentation") / "EO-DG_Truth_and_Historian_Read_Boundaries.md", "Historian views may display existing facts", "HIST-RM002-EVID-B08-READ-BOUNDARY"),
                _line_evidence(Path("Documentation") / "historian_group_framework.md", "Collect enterprise performance data", "HIST-RM002-EVID-B08-COLLECT-DATA"),
            ),
            (
                _finding(
                    "HIST-RM002-FIND-B08-001",
                    "interfaces",
                    "BLOCKING",
                    "No implementation verifier proves every constitutional Historian interface, custody transfer, provenance preservation, and contract listed by RM-002-B08.",
                    (
                        _line_evidence(Path("Documentation") / "EO-DG_Truth_and_Historian_Read_Boundaries.md", "Historian views may display existing facts", "HIST-RM002-EVID-B08-READ-BOUNDARY"),
                    ),
                    "Implement a Historian interface contract registry and independent interface verifiers for every named office.",
                ),
            ),
        ),
        VerificationResult(
            "HISTORIAN-RM-002-B09",
            "Enterprise Learning Readiness Verification",
            "FAIL",
            ("Enterprise Learning consumes historian recommendations",),
            ("learning-ready Journey projection without Historian learning",),
            (
                _line_evidence(CONTROL_PANEL_SRC / "enterprise_learning_engine.py", "Historian Analysis", "HIST-RM002-EVID-B09-HISTORIAN-ANALYSIS"),
                _line_evidence(CONTROL_PANEL_SRC / "historian_recommendation_engine.py", "recommendationDatabase", "HIST-RM002-EVID-B09-RECOMMENDATIONS"),
            ),
            (
                _finding(
                    "HIST-RM002-FIND-B09-001",
                    "enterprise_learning_readiness",
                    "BLOCKING",
                    "Learning readiness is coupled to Historian analysis and recommendations rather than a custody-only Journey learning projection.",
                    (
                        _line_evidence(CONTROL_PANEL_SRC / "enterprise_learning_engine.py", "Historian Analysis", "HIST-RM002-EVID-B09-HISTORIAN-ANALYSIS"),
                        _line_evidence(CONTROL_PANEL_SRC / "historian_recommendation_engine.py", "recommendationDatabase", "HIST-RM002-EVID-B09-RECOMMENDATIONS"),
                    ),
                    "Replace Historian learning/recommendation coupling with read-only Journey Learning Projection inputs.",
                ),
            ),
        ),
        VerificationResult(
            "HISTORIAN-RM-002-B10",
            "Counterfactual Readiness Verification",
            "FAIL",
            ("Decision Laboratory references exist",),
            ("alternative authorizations", "alternative execution paths", "alternative exits", "TYPHON scenarios"),
            (
                _line_evidence(CONTROL_PANEL_SRC / "enterprise_learning_engine.py", "Decision Laboratory", "HIST-RM002-EVID-B10-LAB"),
                {"evidence_id": "HIST-RM002-EVID-B10-TYPHON-SEARCH", "typhon_hits": _contains_any(artifacts, ("TYPHON",))["TYPHON"]},
            ),
            (
                _finding(
                    "HIST-RM002-FIND-B10-001",
                    "counterfactual_readiness",
                    "BLOCKING",
                    "The implementation does not prove preservation of alternative evidence, authorizations, execution paths, exits, and TYPHON scenario inputs as Journey branches.",
                    ({"evidence_id": "HIST-RM002-EVID-B10-TYPHON-SEARCH", "typhon_hits": _contains_any(artifacts, ("TYPHON",))["TYPHON"]},),
                    "Implement counterfactual path records and verifiers for all RM-002-B10 alternative path classes.",
                ),
            ),
        ),
        VerificationResult(
            "HISTORIAN-RM-002-B11",
            "Determinism and Fail-Closed Verification",
            "FAIL",
            ("append-only duplicate search rejection", "immutable cutoff rejection"),
            ("duplicate Journey identities", "ownership conflicts", "graph corruption", "interface failures", "unsafe reconstruction failures"),
            (
                _line_evidence(HISTORIAN_SRC / "search_reconstruction.py", "historical search records are append-only by identifier", "HIST-RM002-EVID-B11-APPEND-ONLY"),
                _line_evidence(HISTORIAN_SRC / "search_reconstruction.py", "information cutoffs are immutable", "HIST-RM002-EVID-B11-CUTOFF-IMMUTABLE"),
            ),
            (
                _finding(
                    "HIST-RM002-FIND-B11-001",
                    "determinism_fail_closed",
                    "BLOCKING",
                    "Some append-only behavior exists, but fail-closed behavior is not verified across missing artifacts, corrupted provenance, duplicate Journey identities, ownership conflicts, graph corruption, interface failures, and reconstruction failures.",
                    (
                        _line_evidence(HISTORIAN_SRC / "search_reconstruction.py", "information cutoffs are immutable", "HIST-RM002-EVID-B11-CUTOFF-IMMUTABLE"),
                    ),
                    "Add deterministic fail-closed verifiers for every RM-002-B11 failure class.",
                ),
            ),
        ),
        VerificationResult(
            "HISTORIAN-RM-002-B12",
            "Constitutional Implementation Completeness Review",
            "FAIL_CLOSED",
            ("repository inventory", "partial search reconstruction", "partial append-only safeguards"),
            (
                "Enterprise Information Journey implementation",
                "complete custody implementation",
                "complete provenance graph implementation",
                "language preservation implementation",
                "complete missing-information implementation",
                "complete replay support",
                "custody-only learning readiness",
                "counterfactual readiness",
            ),
            implementation_evidence,
            (
                _finding(
                    "HIST-RM002-FIND-B12-001",
                    "implementation_completeness",
                    "BLOCKING",
                    "The Historian implementation does not fully satisfy the constitutional architecture established under HISTORIAN-RM-001 and HISTORIAN-MO-001.",
                    implementation_evidence,
                    "Open a bounded Historian implementation remediation program before HISTORIAN-RM-003 enterprise certification.",
                ),
            ),
        ),
    ]
    if any(prohibition_hits[term] for term in prohibition_terms):
        results.append(
            VerificationResult(
                "HISTORIAN-RM-002-B00",
                "Custody-Only Prohibition Conflict Scan",
                "FAIL",
                (),
                tuple(term for term, paths in prohibition_hits.items() if paths),
                ({"evidence_id": "HIST-RM002-EVID-B00-PROHIBITION-HITS", "prohibition_hits": prohibition_hits},),
                (
                    _finding(
                        "HIST-RM002-FIND-B00-001",
                        "custody_only_boundary",
                        "BLOCKING",
                        "Implementation files contain concepts tied to prohibited Historian activities from the hardened baseline.",
                        ({"evidence_id": "HIST-RM002-EVID-B00-PROHIBITION-HITS", "prohibition_hits": prohibition_hits},),
                        "Remove or reassign prohibited learning, inference, recommendation, ranking, prediction, authorization, and mutation semantics from Historian implementation scope.",
                    ),
                ),
            )
        )
    return tuple(results)


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
    baseline = _load_baseline()
    artifacts = tuple(_parse_artifact(path) for path in IMPLEMENTATION_FILES)
    results = _verification_results(artifacts, baseline)
    findings = tuple(finding for result in results for finding in result.findings)
    blocking = tuple(finding["finding_id"] for finding in findings if finding["severity"] == "BLOCKING")

    if ATTACHMENT_PATH.exists():
        (OUTPUT_DIR / "source_order.txt").write_text(ATTACHMENT_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    _write_json("implementation_inventory.json", artifacts)
    _write_json("verification_results_registry.json", results)
    for result in results:
        _write_json(f"{result.order_id.lower().replace('-', '_')}.json", result)
    _write_json("certification_findings_registry.json", findings)
    _write_json(
        "certification_blocker_registry.json",
        [finding for finding in findings if finding["severity"] == "BLOCKING"],
    )
    _write_json(
        "historian_rm002_certification_matrix.json",
        [
            {
                "order_id": result.order_id,
                "title": result.title,
                "disposition": result.disposition,
                "verified_count": len(result.verified_items),
                "failed_count": len(result.failed_items),
                "finding_count": len(result.findings),
            }
            for result in results
        ],
    )
    _write_json(
        "implementation_completeness_report.json",
        {
            "order_id": ORDER_ID,
            "generated_at_utc": EXECUTION_UTC,
            "candidate_digest": _repository_digest(),
            "baseline_id": baseline["baseline_id"],
            "implementation_certification_only": True,
            "constitutional_architecture_modified": False,
            "runtime_behavior_modified": False,
            "verification_order_count": len(results),
            "blocking_findings": blocking,
            "final_disposition": "FAIL_CLOSED" if blocking else "PASS",
            "rm003_authorized": False if blocking else True,
            "decision": (
                "Historian RM-002 implementation certification fails closed. "
                "Implementation remediation is required before HISTORIAN-RM-003 enterprise certification."
                if blocking
                else "Historian RM-002 implementation certification passes and authorizes HISTORIAN-RM-003."
            ),
        },
    )
    manifest = {
        "order_id": ORDER_ID,
        "generated_at_utc": EXECUTION_UTC,
        "candidate_digest": _repository_digest(),
        "deliverables": sorted(path.name for path in OUTPUT_DIR.iterdir() if path.is_file()),
        "verification_order_count": len(results),
        "artifact_count": len(artifacts),
        "blocking_findings": len(blocking),
        "final_disposition": "FAIL_CLOSED" if blocking else "PASS",
    }
    _write_json("campaign_manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
