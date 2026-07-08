"""Historian Fusion Office."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository

from .group import HISTORIAN_GROUP_ID


HISTORIAN_FUSION_OFFICE_ID = "HISTORIAN-OFFICE-008"
HISTORIAN_FUSION_STAFF_ID = "STF-077"


class LearningStatus(str, Enum):
    """Integrated organizational learning status."""

    VALIDATED = "validated"
    CONFLICTED = "conflicted"
    INSUFFICIENT = "insufficient"


@dataclass(frozen=True)
class HistorianOfficeFinding:
    """Validated output from a Historian office."""

    finding_id: str
    source_office_id: str
    report_id: str
    finding_type: str
    conclusion: str
    confidence: float
    evidence_ids: tuple[str, ...]
    pattern_tags: tuple[str, ...]
    supports_learning: bool
    contradiction_ids: tuple[str, ...]


@dataclass(frozen=True)
class HistorianFusionInput:
    """Complete Historian Fusion input package."""

    fusion_input_id: str
    performance_findings: tuple[HistorianOfficeFinding, ...]
    hypothesis_findings: tuple[HistorianOfficeFinding, ...]
    model_calibration_findings: tuple[HistorianOfficeFinding, ...]
    decision_findings: tuple[HistorianOfficeFinding, ...]
    evidence_findings: tuple[HistorianOfficeFinding, ...]


@dataclass(frozen=True)
class CrossEvaluationConsistencyRecord:
    """Cross-evaluation consistency analysis."""

    consistency_id: str
    integrated_finding_ids: tuple[str, ...]
    conflict_count: int
    conflicting_finding_ids: tuple[str, ...]
    consistency_score: float
    status: LearningStatus


@dataclass(frozen=True)
class OrganizationalPattern:
    """Cross-organizational pattern."""

    pattern_id: str
    pattern_tag: str
    occurrence_count: int
    source_finding_ids: tuple[str, ...]
    recurring: bool


@dataclass(frozen=True)
class OrganizationalLearningAssessment:
    """Validated organizational learning assessment."""

    assessment_id: str
    status: LearningStatus
    integrated_conclusion: str
    average_confidence: float
    evidence_ids: tuple[str, ...]
    contributing_report_ids: tuple[str, ...]
    consistency_record_id: str
    provenance_complete: bool


@dataclass(frozen=True)
class InstitutionalKnowledgeRecord:
    """Institutional knowledge promotion record."""

    knowledge_id: str
    source_assessment_id: str
    promoted: bool
    doctrine_promotion_recommended: bool
    provenance_ids: tuple[str, ...]
    librarian_package_id: str
    academy_package_id: str


@dataclass(frozen=True)
class OrganizationalEvolutionRecommendation:
    """Evidence-based organizational evolution recommendation."""

    recommendation_id: str
    source_assessment_id: str
    recommendation: str
    evidence_based: bool
    recommended_consumers: tuple[str, ...]
    directly_modifies_behavior: bool


@dataclass(frozen=True)
class HistorianFusionIntegrityAssessment:
    """Fusion integrity assessment."""

    integrity_id: str
    integrated_report_ids: tuple[str, ...]
    archive_immutable: bool
    provenance_preserved: bool
    trace_complete: bool


@dataclass(frozen=True)
class LibrarianKnowledgePackage:
    """Librarian deliverable."""

    package_id: str
    institutional_knowledge_ids: tuple[str, ...]
    doctrine_promotion_recommendations: tuple[str, ...]
    organizational_evolution_specifications: tuple[str, ...]


@dataclass(frozen=True)
class AcademyCurriculumPackage:
    """Academy deliverable."""

    package_id: str
    curriculum_topics: tuple[str, ...]
    best_practice_archive: tuple[str, ...]
    organizational_weakness_archive: tuple[str, ...]


class HistorianFusionOffice:
    """Deterministic integration authority for Historian Group."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.configuration_service = configuration_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self.prompt_repository = prompt_repository
        self._integration_archive: list[dict[str, object]] = []

    @property
    def historian_integration_archive(self) -> tuple[dict[str, object], ...]:
        """Return immutable Historian integration archive."""
        return tuple(self._integration_archive)

    def fuse(
        self,
        fusion_input: HistorianFusionInput,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Fuse all Historian office reports into integrated learning."""
        self.configuration_service.validate_startup()
        findings = _all_findings(fusion_input)
        if not findings:
            raise ValueError("Historian Fusion requires at least one office finding")
        _require_office_coverage(fusion_input)
        consistency = _consistency(findings, document_sequence)
        patterns = _patterns(findings)
        assessment = _assessment(findings, consistency, document_sequence)
        knowledge = _knowledge(assessment, document_sequence + 1)
        recommendation = _recommendation(assessment, patterns, consistency)
        librarian = _librarian_package(knowledge, recommendation)
        academy = _academy_package(patterns, consistency)
        integrity = HistorianFusionIntegrityAssessment(
            f"HFIA-{document_sequence:06d}",
            tuple(finding.report_id for finding in findings),
            True,
            True,
            True,
        )
        archive_record = {
            "assessment_id": assessment.assessment_id,
            "knowledge_id": knowledge.knowledge_id,
            "status": assessment.status.value,
            "report_ids": tuple(finding.report_id for finding in findings),
        }
        self._integration_archive.append(_json_ready(archive_record))
        return {
            "organizational_learning_assessment": self._persist_contract(
                "ORGANIZATIONAL_LEARNING_ASSESSMENT",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Organizational Learning Assessment.",
                {
                    "office_id": HISTORIAN_FUSION_OFFICE_ID,
                    "office_name": "Historian Fusion Office",
                    "historian_fusion_input": fusion_input,
                    "cross_evaluation_consistency_record": consistency,
                    "organizational_learning_assessment": assessment,
                    "organizational_pattern_database": patterns,
                    "organizational_learning_integrity_assessment": integrity,
                },
            ),
            "organizational_evolution_report": self._persist_contract(
                "ORGANIZATIONAL_EVOLUTION_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Organizational Evolution Report.",
                {
                    "organizational_evolution_recommendation": recommendation,
                    "organizational_evolution_history_updated": True,
                },
            ),
            "institutional_knowledge_report": self._persist_contract(
                "INSTITUTIONAL_KNOWLEDGE_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Institutional Knowledge Report.",
                {
                    "institutional_knowledge_record": knowledge,
                    "validated_institutional_knowledge_package": librarian,
                    "curriculum_development_package": academy,
                    "knowledge_promotion_preserves_provenance": True,
                },
            ),
            "historian_fusion_summary": self._persist_contract(
                "HISTORIAN_FUSION_SUMMARY",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Historian Fusion Summary.",
                {
                    "historian_integration_archive": self.historian_integration_archive,
                    "organizational_learning_registry": (assessment,),
                    "institutional_knowledge_register": (knowledge,),
                    "knowledge_promotion_register": (knowledge.knowledge_id,),
                    "librarian_interface_ready": True,
                    "academy_interface_ready": True,
                },
            ),
        }

    def _persist_contract(
        self,
        contract_type: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        human_summary: str,
        payload: dict[str, Any],
    ) -> OperationalContract:
        contract = _contract(contract_type, case_file_id, trade_cycle_id, document_sequence, human_summary, payload)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        return contract


def _all_findings(fusion_input: HistorianFusionInput) -> tuple[HistorianOfficeFinding, ...]:
    return (
        *fusion_input.performance_findings,
        *fusion_input.hypothesis_findings,
        *fusion_input.model_calibration_findings,
        *fusion_input.decision_findings,
        *fusion_input.evidence_findings,
    )


def _require_office_coverage(fusion_input: HistorianFusionInput) -> None:
    missing = []
    if not fusion_input.performance_findings:
        missing.append("Performance Measurement Office")
    if not fusion_input.hypothesis_findings:
        missing.append("Hypothesis Validation Office")
    if not fusion_input.model_calibration_findings:
        missing.append("Model Calibration Office")
    if not fusion_input.decision_findings:
        missing.append("Decision Evaluation Office")
    if not fusion_input.evidence_findings:
        missing.append("Evidence Evaluation Office")
    if missing:
        raise ValueError(f"missing Historian office findings: {', '.join(missing)}")


def _consistency(findings: tuple[HistorianOfficeFinding, ...], document_sequence: int) -> CrossEvaluationConsistencyRecord:
    conflicts = tuple(finding.finding_id for finding in findings if finding.contradiction_ids or not finding.supports_learning)
    score = round(1.0 - (len(conflicts) / max(len(findings), 1)), 6)
    status = LearningStatus.CONFLICTED if conflicts else LearningStatus.VALIDATED if score >= 0.8 else LearningStatus.INSUFFICIENT
    return CrossEvaluationConsistencyRecord(
        f"CECR-{document_sequence:06d}",
        tuple(finding.finding_id for finding in findings),
        len(conflicts),
        conflicts,
        score,
        status,
    )


def _patterns(findings: tuple[HistorianOfficeFinding, ...]) -> tuple[OrganizationalPattern, ...]:
    tags: dict[str, list[str]] = {}
    for finding in findings:
        for tag in finding.pattern_tags:
            tags.setdefault(tag, []).append(finding.finding_id)
    return tuple(
        OrganizationalPattern(
            f"OPD-{hashlib.sha256(tag.encode('utf-8')).hexdigest()[:8].upper()}",
            tag,
            len(ids),
            tuple(sorted(ids)),
            len(ids) >= 2,
        )
        for tag, ids in sorted(tags.items())
    )


def _assessment(
    findings: tuple[HistorianOfficeFinding, ...],
    consistency: CrossEvaluationConsistencyRecord,
    document_sequence: int,
) -> OrganizationalLearningAssessment:
    confidence = round(sum(finding.confidence for finding in findings) / len(findings), 6)
    evidence_ids = tuple(sorted({evidence_id for finding in findings for evidence_id in finding.evidence_ids}))
    reports = tuple(finding.report_id for finding in findings)
    status = consistency.status if confidence >= 0.65 else LearningStatus.INSUFFICIENT
    conclusion = "validated_organizational_learning" if status == LearningStatus.VALIDATED else "learning_requires_additional_resolution"
    return OrganizationalLearningAssessment(
        f"OLA-{document_sequence:06d}",
        status,
        conclusion,
        confidence,
        evidence_ids,
        reports,
        consistency.consistency_id,
        True,
    )


def _knowledge(assessment: OrganizationalLearningAssessment, document_sequence: int) -> InstitutionalKnowledgeRecord:
    promoted = assessment.status == LearningStatus.VALIDATED
    return InstitutionalKnowledgeRecord(
        f"IKR-{document_sequence:06d}",
        assessment.assessment_id,
        promoted,
        promoted,
        (*assessment.evidence_ids, *assessment.contributing_report_ids),
        f"VKP-{document_sequence:06d}",
        f"ACP-{document_sequence:06d}",
    )


def _recommendation(
    assessment: OrganizationalLearningAssessment,
    patterns: tuple[OrganizationalPattern, ...],
    consistency: CrossEvaluationConsistencyRecord,
) -> OrganizationalEvolutionRecommendation:
    recurring = tuple(pattern.pattern_tag for pattern in patterns if pattern.recurring)
    if assessment.status == LearningStatus.VALIDATED and recurring:
        text = f"Promote validated learning and address recurring patterns: {', '.join(recurring)}."
    elif consistency.conflict_count:
        text = "Resolve conflicting Historian evaluations before doctrine promotion."
    else:
        text = "Continue evidence collection before organizational evolution."
    return OrganizationalEvolutionRecommendation(
        f"OER-{hashlib.sha256(f'{assessment.assessment_id}:{text}'.encode('utf-8')).hexdigest()[:8].upper()}",
        assessment.assessment_id,
        text,
        True,
        ("Librarian Group", "Executive Group", "Academy", "Future Engineering Orders"),
        False,
    )


def _librarian_package(
    knowledge: InstitutionalKnowledgeRecord,
    recommendation: OrganizationalEvolutionRecommendation,
) -> LibrarianKnowledgePackage:
    return LibrarianKnowledgePackage(
        knowledge.librarian_package_id,
        (knowledge.knowledge_id,) if knowledge.promoted else (),
        (recommendation.recommendation,) if knowledge.doctrine_promotion_recommended else (),
        (recommendation.recommendation,),
    )


def _academy_package(
    patterns: tuple[OrganizationalPattern, ...],
    consistency: CrossEvaluationConsistencyRecord,
) -> AcademyCurriculumPackage:
    best_practices = tuple(pattern.pattern_tag for pattern in patterns if pattern.recurring)
    weaknesses = consistency.conflicting_finding_ids
    return AcademyCurriculumPackage(
        f"ACP-{hashlib.sha256(str(patterns).encode('utf-8')).hexdigest()[:8].upper()}",
        ("Evidence-based organizational learning", "Decision discipline", "Historical pattern recognition"),
        best_practices,
        weaknesses,
    )


def _contract(
    contract_type: str,
    case_file_id: str,
    trade_cycle_id: str,
    document_sequence: int,
    human_summary: str,
    payload: dict[str, Any],
) -> OperationalContract:
    created = utc_timestamp()
    normalized_payload = _json_ready(payload)
    signature_hash = hashlib.sha256(json.dumps(normalized_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id=generate_document_id(document_sequence),
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=case_file_id,
        trade_cycle_id=trade_cycle_id,
        parent_contract_ids=(),
        produced_by_staff_id=HISTORIAN_FUSION_STAFF_ID,
        produced_by_group_id=HISTORIAN_GROUP_ID,
        intended_consumer_group_id=HISTORIAN_GROUP_ID,
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=human_summary,
        machine_payload=normalized_payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
