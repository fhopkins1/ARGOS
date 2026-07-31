from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any


ORDER_ID = "HISTORIAN-ECS003-AUDIT-001"
OUTPUT_DIR = Path("Documentation") / "HISTORIAN_ECS003_AUDIT_001"
ATTACHMENT_PATH = Path(
    r"C:\Users\Fletc\.codex\attachments\71b78f6c-4bb2-4ab7-86a0-32b5ffc0227f\pasted-text.txt"
)

REQUIRED_FIELDS = (
    "constitutional_deficiency",
    "governing_constitutional_authority",
    "objective_evidence",
    "constitutional_impact",
    "recommended_remediation_objective",
)


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    path: str
    line: int
    excerpt: str
    evidence_type: str


@dataclass(frozen=True)
class Finding:
    finding_id: str
    severity: str
    category: str
    constitutional_deficiency: str
    governing_constitutional_authority: str
    objective_evidence: tuple[EvidenceReference, ...]
    constitutional_impact: str
    recommended_remediation_objective: str


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig").splitlines()


def _find_line(path: str, needle: str) -> EvidenceReference:
    local_path = Path(path)
    if not local_path.exists():
        return EvidenceReference(
            evidence_id=f"EVID-MISSING-{path.replace('/', '_').replace('\\', '_')}",
            path=path,
            line=0,
            excerpt=f"Repository artifact not found: {path}",
            evidence_type="missing_artifact",
        )
    lines = _read_lines(local_path)
    lowered = needle.lower()
    for index, line in enumerate(lines, start=1):
        if lowered in line.lower():
            return EvidenceReference(
                evidence_id=f"EVID-{local_path.stem.upper()}-{index:04d}",
                path=path,
                line=index,
                excerpt=line.strip()[:240],
                evidence_type="repository_text",
            )
    return EvidenceReference(
        evidence_id=f"EVID-{local_path.stem.upper()}-NO-MATCH",
        path=path,
        line=0,
        excerpt=f"Search text not found: {needle}",
        evidence_type="negative_repository_search",
    )


@lru_cache(maxsize=1)
def _tracked_text_files() -> tuple[Path, ...]:
    try:
        output = subprocess.check_output(["git", "ls-files"], text=True)
        candidates = [Path(line.strip()) for line in output.splitlines() if line.strip()]
    except (OSError, subprocess.CalledProcessError):
        roots = (Path("Documentation"), Path("src"), Path("Tests"), Path("Scripts"))
        candidates = [path for root in roots if root.exists() for path in root.rglob("*")]
    return tuple(
        path
        for path in candidates
        if path.is_file()
        and path.suffix.lower() in {".md", ".py", ".json"}
        and "clean_room" not in {part.lower() for part in path.parts}
        and "clean_room_runs" not in {part.lower() for part in path.parts}
        and "clean_room_workspace" not in {part.lower() for part in path.parts}
    )


def _search_count(pattern: str) -> int:
    count = 0
    for path in _tracked_text_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if pattern.lower() in text.lower():
            count += 1
    return count


def _negative_search_evidence(evidence_id: str, pattern: str, note: str) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=evidence_id,
        path="repository_search",
        line=0,
        excerpt=f"{note}; repository files containing '{pattern}': {_search_count(pattern)}",
        evidence_type="repository_search_summary",
    )


def _findings() -> list[Finding]:
    group_doc = "Documentation/historian_group_framework.md"
    readiness_doc = "Documentation/historian_operational_readiness.md"
    read_boundary_doc = "Documentation/EO-DG_Truth_and_Historian_Read_Boundaries.md"
    recommendation_engine = "src/argos/control_panel/historian_recommendation_engine.py"
    learning_engine = "src/argos/control_panel/enterprise_learning_engine.py"
    historian_init = "src/argos/historian/__init__.py"
    search_archive = "src/argos/historian/search_reconstruction.py"

    return [
        Finding(
            finding_id="HIST-ECS003-FIND-001",
            severity="BLOCKING",
            category="mission_boundary",
            constitutional_deficiency=(
                "The available Historian doctrine describes the Historian Group as a scientific "
                "evaluation and organizational learning function, while the ECS-003 audit order "
                "requires a custody-only Historian that never learns, infers, summarizes, "
                "optimizes, recommends, ranks, predicts, authorizes, or modifies historical records."
            ),
            governing_constitutional_authority=(
                "HISTORIAN-ECS003-AUDIT-001 mission under audit; Enterprise Truth Doctrine; "
                "Workflow Ownership Doctrine; Enterprise Improvement Group Doctrine."
            ),
            objective_evidence=(
                _find_line(group_doc, "scientific evaluation organization"),
                _find_line(group_doc, "Produce historical evaluations and validated learning records"),
                _find_line(recommendation_engine, "Historian Recommendation Engine"),
                _find_line(learning_engine, "Historian Analysis"),
            ),
            constitutional_impact=(
                "Historian custody authority is blended with learning and recommendation activity, "
                "creating unresolved ownership leakage between immutable memory, Enterprise "
                "Learning, and Decision Laboratory functions."
            ),
            recommended_remediation_objective=(
                "Publish a Historian constitutional charter that separates immutable custody from "
                "learning, analysis, recommendation, optimization, and laboratory authority."
            ),
        ),
        Finding(
            finding_id="HIST-ECS003-FIND-002",
            severity="BLOCKING",
            category="historical_custody",
            constitutional_deficiency=(
                "No canonical Historian custody registry was found that assigns exactly one "
                "historical custodian for every artifact class named by the audit order."
            ),
            governing_constitutional_authority=(
                "HISTORIAN-ECS003-AUDIT-001 Historical Custody Audit; Evidence Doctrine; Audit Doctrine."
            ),
            objective_evidence=(
                _find_line(historian_init, "Historian Group scientific evaluation organization"),
                _find_line(read_boundary_doc, "append Historian records"),
                _negative_search_evidence(
                    "EVID-HIST-CUSTODY-REGISTRY-SEARCH",
                    "canonical Historian custody registry",
                    "No explicit repository-wide canonical Historian custody registry was located",
                ),
            ),
            constitutional_impact=(
                "Sentinel observations, Search missions, Evidence objects, Analyst assessments, "
                "Risk decisions, Authorization objects, Decision Objects, Broker objects, Execution "
                "objects, Monitoring observations, Exit decisions, Closed Position Truth, Performance "
                "Truth, and Enterprise Learning hypotheses do not share one audited Historian custody baseline."
            ),
            recommended_remediation_objective=(
                "Create an authoritative Historian historical custody registry covering every "
                "enterprise artifact class with owner, custodian, producer, transfer trigger, retention, "
                "and reconstruction obligation."
            ),
        ),
        Finding(
            finding_id="HIST-ECS003-FIND-003",
            severity="BLOCKING",
            category="enterprise_information_journey",
            constitutional_deficiency=(
                "The Enterprise Information Journey is not governed as a complete historical object "
                "with deterministic identity, initiation, completion, ownership, relationships, "
                "supersession, archival, and reconstruction rules."
            ),
            governing_constitutional_authority=(
                "HISTORIAN-ECS003-AUDIT-001 Enterprise Journey Audit; Workflow Ownership Doctrine."
            ),
            objective_evidence=(
                _negative_search_evidence(
                    "EVID-ENTERPRISE-JOURNEY-SEARCH",
                    "Enterprise Information Journey",
                    "The exact constitutional object requested by the audit is not materially present",
                ),
                _find_line(search_archive, "HistoricalReconstruction"),
                _find_line(readiness_doc, "Historical workflow execution"),
            ),
            constitutional_impact=(
                "A completed workflow may be reconstructable only through office-specific evidence "
                "fragments rather than one deterministic journey record from observation through final archive."
            ),
            recommended_remediation_objective=(
                "Define an Enterprise Information Journey constitution with canonical identity, "
                "event classes, edge classes, archival triggers, and reconstruction acceptance criteria."
            ),
        ),
        Finding(
            finding_id="HIST-ECS003-FIND-004",
            severity="MAJOR",
            category="missing_information",
            constitutional_deficiency=(
                "The repository contains partial temporal classifications for historical search, but "
                "the complete missing-information taxonomy required by the audit is not established "
                "for all historical artifacts."
            ),
            governing_constitutional_authority=(
                "HISTORIAN-ECS003-AUDIT-001 Missing Information Audit; Evidence Doctrine."
            ),
            objective_evidence=(
                _find_line(search_archive, "AVAILABLE_NOT_COLLECTED"),
                _find_line(search_archive, "SOURCE_UNAVAILABLE"),
                _negative_search_evidence(
                    "EVID-MISSING-INFO-TAXONOMY-SEARCH",
                    "requested but unavailable",
                    "The requested missing-information state appears without a canonical Historian-wide taxonomy",
                ),
            ),
            constitutional_impact=(
                "Enterprise history can preserve selected negative states while still losing distinctions "
                "between not requested, requested unavailable, stale, contradictory, corrupted, redacted, "
                "and not applicable information."
            ),
            recommended_remediation_objective=(
                "Publish a Historian missing-information taxonomy and require every office archive "
                "transfer to preserve one terminal missing-information state where data is absent."
            ),
        ),
        Finding(
            finding_id="HIST-ECS003-FIND-005",
            severity="MAJOR",
            category="language_preservation",
            constitutional_deficiency=(
                "No Historian-wide doctrine was found that separates raw language, structured records, "
                "semantic interpretation, constitutional truth, and enterprise hypotheses."
            ),
            governing_constitutional_authority=(
                "HISTORIAN-ECS003-AUDIT-001 Language Preservation Audit; Enterprise Truth Doctrine."
            ),
            objective_evidence=(
                _find_line(search_archive, "canonical_query_text"),
                _find_line(group_doc, "Every conclusion must be supported by measurable evidence"),
                _negative_search_evidence(
                    "EVID-LANGUAGE-PRESERVATION-SEARCH",
                    "raw language",
                    "Historian-specific separation of raw language from semantic interpretation was not found",
                ),
            ),
            constitutional_impact=(
                "Historical meaning can drift if the preserved raw text, normalized record, interpreted "
                "meaning, and accepted constitutional truth are not independently identified and traceable."
            ),
            recommended_remediation_objective=(
                "Define a language preservation constitution that binds raw text, normalized fields, "
                "semantic interpretation, truth disposition, and hypothesis use through immutable lineage."
            ),
        ),
        Finding(
            finding_id="HIST-ECS003-FIND-006",
            severity="MAJOR",
            category="historical_graph",
            constitutional_deficiency=(
                "Historical graph governance is not complete for node identity, edge identity, "
                "ownership, versioning, supersession, correction, graph integrity, replay, and reconstruction."
            ),
            governing_constitutional_authority=(
                "HISTORIAN-ECS003-AUDIT-001 Historical Graph Audit; Audit Doctrine."
            ),
            objective_evidence=(
                _find_line(search_archive, "EvidenceTemporalRelationship"),
                _find_line(search_archive, "CorrectionRevisionLink"),
                _negative_search_evidence(
                    "EVID-HISTORICAL-GRAPH-SEARCH",
                    "historical graph",
                    "No canonical Historian historical graph baseline was located",
                ),
            ),
            constitutional_impact=(
                "Historical reconstruction may omit relationship classes or silently rely on local object "
                "structures rather than an enterprise graph with audited edge semantics."
            ),
            recommended_remediation_objective=(
                "Create a Historian historical graph constitution with mandatory node and edge schemas, "
                "versioning, correction lineage, supersession lineage, and replay equivalence rules."
            ),
        ),
        Finding(
            finding_id="HIST-ECS003-FIND-007",
            severity="BLOCKING",
            category="interfaces",
            constitutional_deficiency=(
                "The Historian interface model is not completely specified for every office named by "
                "the audit order, including Sentinel, Seeker, Analyst, Risk, Authorization, Trader, "
                "Broker, Monitoring, Exit Decision, Closed Position Truth, Performance Truth, "
                "Enterprise Learning, Decision Laboratory, and Commander."
            ),
            governing_constitutional_authority=(
                "HISTORIAN-ECS003-AUDIT-001 Interface Audit; Workflow Ownership Doctrine."
            ),
            objective_evidence=(
                _find_line(read_boundary_doc, "Historian views may display existing facts"),
                _find_line(group_doc, "Collect enterprise performance data"),
                _negative_search_evidence(
                    "EVID-HISTORIAN-INTERFACE-SEARCH",
                    "Historian Interface Registry",
                    "No complete Historian interface registry was found",
                ),
            ),
            constitutional_impact=(
                "Undefined interfaces allow hidden coupling, implicit archive append authority, and "
                "ambiguous consumer/provider responsibilities."
            ),
            recommended_remediation_objective=(
                "Establish a Historian interface registry defining provider, consumer, custody transfer, "
                "validation, rejection, correction, and evidence obligations for each named office."
            ),
        ),
        Finding(
            finding_id="HIST-ECS003-FIND-008",
            severity="MAJOR",
            category="learning_readiness",
            constitutional_deficiency=(
                "Enterprise Learning and Decision Laboratory readiness depends on historical analysis "
                "and recommendations, but no custody-only Historian doctrine guarantees that learning "
                "consumes immutable history without allowing Historian inference or recommendation authority."
            ),
            governing_constitutional_authority=(
                "HISTORIAN-ECS003-AUDIT-001 Enterprise Learning Readiness Audit; Enterprise Improvement Group Doctrine."
            ),
            objective_evidence=(
                _find_line(learning_engine, "Historian Analysis"),
                _find_line(recommendation_engine, "recommendationDatabase"),
                _find_line(recommendation_engine, "requiresEnterpriseLearningEvaluation"),
            ),
            constitutional_impact=(
                "Learning outputs may be historically useful, but the constitutional owner of learning "
                "hypotheses, recommendations, counterfactuals, and historical memory remains blurred."
            ),
            recommended_remediation_objective=(
                "Move learning, hypothesis, recommendation, ranking, and optimization authorities into "
                "explicit non-Historian offices while preserving read-only Historian custody interfaces."
            ),
        ),
        Finding(
            finding_id="HIST-ECS003-FIND-009",
            severity="MAJOR",
            category="counterfactual_readiness",
            constitutional_deficiency=(
                "The architecture does not fully require preservation of rejected actions, ignored "
                "opportunities, denied authorizations, alternative decisions, and counterfactual paths "
                "as first-class historical records."
            ),
            governing_constitutional_authority=(
                "HISTORIAN-ECS003-AUDIT-001 Historical Completeness Audit and Counterfactual Readiness Audit."
            ),
            objective_evidence=(
                _find_line(search_archive, "AVAILABLE_NOT_COLLECTED"),
                _find_line(learning_engine, "Decision Laboratory"),
                _negative_search_evidence(
                    "EVID-IGNORED-OPPORTUNITIES-SEARCH",
                    "opportunities ignored",
                    "No canonical requirement for preserving ignored opportunities was located",
                ),
            ),
            constitutional_impact=(
                "Enterprise history may become selection-biased by preserving completed or observed "
                "events more reliably than paths not taken."
            ),
            recommended_remediation_objective=(
                "Create counterfactual and negative-history doctrine covering rejected actions, ignored "
                "opportunities, denied authorities, abandoned workflows, and alternative decisions."
            ),
        ),
        Finding(
            finding_id="HIST-ECS003-FIND-010",
            severity="BLOCKING",
            category="certification_readiness",
            constitutional_deficiency=(
                "The Historian Office is not ready for ECS-003 certification because core constitutional "
                "baselines for custody, journeys, missing information, language preservation, graph "
                "relationships, interfaces, and learning separation are absent or incomplete."
            ),
            governing_constitutional_authority=(
                "HISTORIAN-ECS003-AUDIT-001 final decision requirements; Enterprise Constitutional Standard ECS-003."
            ),
            objective_evidence=(
                _find_line(readiness_doc, "deterministic certification authority"),
                _find_line(readiness_doc, "Organizational learning capability"),
                _negative_search_evidence(
                    "EVID-HISTORIAN-ECS003-BASELINE-SEARCH",
                    "Historian ECS-003 certification baseline",
                    "No final Historian ECS-003 constitutional certification baseline was located",
                ),
            ),
            constitutional_impact=(
                "The office requires constitutional remediation before implementation quality can be "
                "meaningfully certified against ECS-003."
            ),
            recommended_remediation_objective=(
                "Open a Historian constitutional remediation program before implementation verification, "
                "with one order each for mission boundary, custody, journey, provenance, completeness, "
                "interfaces, traceability, replay, and certification readiness."
            ),
        ),
    ]


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


def _registry(findings: list[Finding], category: str) -> list[dict[str, Any]]:
    return [_json_ready(finding) for finding in findings if finding.category == category]


def _assessment(name: str, findings: list[Finding], categories: tuple[str, ...], status: str) -> dict[str, Any]:
    selected = [finding for finding in findings if finding.category in categories]
    return {
        "assessment_id": f"{ORDER_ID}-{name}",
        "status": status,
        "finding_count": len(selected),
        "blocking_findings": [finding.finding_id for finding in selected if finding.severity == "BLOCKING"],
        "major_findings": [finding.finding_id for finding in selected if finding.severity == "MAJOR"],
        "summary": "Constitutional remediation required before ECS-003 certification.",
        "findings": [_json_ready(finding) for finding in selected],
    }


def _completion_report(findings: list[Finding]) -> dict[str, Any]:
    blocking = [finding.finding_id for finding in findings if finding.severity == "BLOCKING"]
    return {
        "order_id": ORDER_ID,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "audit_scope": "constitutional_architecture_only",
        "implementation_quality_evaluated": False,
        "runtime_behavior_modified": False,
        "constitutional_authority_modified": False,
        "findings_total": len(findings),
        "blocking_findings": blocking,
        "major_findings": [finding.finding_id for finding in findings if finding.severity == "MAJOR"],
        "ecs003_certification_recommendation": "REQUIRES_CONSTITUTIONAL_REMEDIATION",
        "additional_doctrine_required": True,
        "architectural_redesign_required": True,
        "implementation_verification_authorized": False,
        "decision": (
            "Historian does not presently satisfy ECS-003 constitutional architecture requirements. "
            "The next authorized activity is constitutional remediation, not implementation certification."
        ),
    }


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    findings = _findings()
    for finding in findings:
        missing = [field for field in REQUIRED_FIELDS if not getattr(finding, field)]
        if missing:
            raise ValueError(f"{finding.finding_id} missing required fields: {missing}")

    if ATTACHMENT_PATH.exists():
        (OUTPUT_DIR / "source_order.txt").write_text(ATTACHMENT_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    _write_json("constitutional_findings_register.json", findings)
    _write_json("missing_responsibility_register.json", _registry(findings, "mission_boundary") + _registry(findings, "learning_readiness"))
    _write_json("ownership_findings_register.json", _registry(findings, "historical_custody") + _registry(findings, "interfaces"))
    _write_json("historical_completeness_assessment.json", _assessment("HISTORICAL-COMPLETENESS", findings, ("missing_information", "counterfactual_readiness"), "INCOMPLETE"))
    _write_json("provenance_assessment.json", _assessment("PROVENANCE", findings, ("language_preservation", "historical_graph"), "INCOMPLETE"))
    _write_json("enterprise_journey_assessment.json", _assessment("ENTERPRISE-JOURNEY", findings, ("enterprise_information_journey",), "INCOMPLETE"))
    _write_json("interface_assessment.json", _assessment("INTERFACE", findings, ("interfaces",), "INCOMPLETE"))
    _write_json("enterprise_learning_readiness_assessment.json", _assessment("ENTERPRISE-LEARNING", findings, ("learning_readiness",), "NOT_READY"))
    _write_json("counterfactual_readiness_assessment.json", _assessment("COUNTERFACTUAL", findings, ("counterfactual_readiness",), "NOT_READY"))
    _write_json("constitutional_risk_assessment.json", _assessment("CONSTITUTIONAL-RISK", findings, tuple({finding.category for finding in findings}), "HIGH"))
    _write_json("ecs003_certification_recommendation.json", _completion_report(findings))
    _write_json("completion_report.json", _completion_report(findings))

    index = {
        "order_id": ORDER_ID,
        "deliverables": sorted(path.name for path in OUTPUT_DIR.iterdir() if path.is_file()),
        "constitutional_findings": len(findings),
        "recommendation": "REQUIRES_CONSTITUTIONAL_REMEDIATION",
    }
    _write_json("audit_manifest.json", index)
    return index


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
