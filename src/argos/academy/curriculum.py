"""Curriculum Office."""

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

from .framework import ACADEMY_GROUP_ID, CompetencyDomain, LearnerLevel


CURRICULUM_OFFICE_ID = "ACADEMY-OFFICE-002"
CURRICULUM_STAFF_ID = "STF-089"


class CurriculumAdaptationTrigger(str, Enum):
    """Curriculum adaptation trigger."""

    HISTORIAN_DISCOVERY = "historian_discovery"
    INSTITUTIONAL_KNOWLEDGE_CHANGE = "institutional_knowledge_change"
    DOCTRINE_CHANGE = "doctrine_change"
    COMPETENCY_EVOLUTION = "competency_evolution"
    STUDENT_PERFORMANCE_CHANGE = "student_performance_change"
    EDUCATIONAL_ANALYTICS = "educational_analytics"


@dataclass(frozen=True)
class CompetencyProfile:
    """Learner competency profile."""

    learner_id: str
    current_level: LearnerLevel
    demonstrated_competencies: tuple[CompetencyDomain, ...]
    knowledge_gap_domains: tuple[CompetencyDomain, ...]
    learning_velocity: float
    educational_goals: tuple[str, ...]
    investment_interests: tuple[str, ...]
    preferred_learning_style: str


@dataclass(frozen=True)
class CurriculumModule:
    """Curriculum module."""

    module_id: str
    title: str
    competency_domain: CompetencyDomain
    lesson_ids: tuple[str, ...]
    case_study_ids: tuple[str, ...]
    guided_practice_ids: tuple[str, ...]
    assessment_ids: tuple[str, ...]
    advanced_topic_ids: tuple[str, ...]
    reinforcement_ids: tuple[str, ...]
    validated_knowledge_ids: tuple[str, ...]
    doctrine_ids: tuple[str, ...]
    specification_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class PrerequisiteRelationship:
    """Deterministic prerequisite relationship."""

    relationship_id: str
    prerequisite_competency: CompetencyDomain
    dependent_competency: CompetencyDomain
    rationale: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class CurriculumVersionRecord:
    """Curriculum version history record."""

    version_id: str
    curriculum_id: str
    version: str
    parent_version_id: str | None
    revision_trigger: CurriculumAdaptationTrigger
    immutable: bool
    timestamp_utc: str


@dataclass(frozen=True)
class CurriculumMap:
    """Curriculum map."""

    curriculum_id: str
    learner_id: str
    modules: tuple[CurriculumModule, ...]
    prerequisites: tuple[PrerequisiteRelationship, ...]
    required_competencies: tuple[CompetencyDomain, ...]
    version_record: CurriculumVersionRecord


@dataclass(frozen=True)
class LearningPathway:
    """Personalized learning pathway."""

    pathway_id: str
    learner_id: str
    ordered_module_ids: tuple[str, ...]
    skipped_demonstrated_competencies: tuple[CompetencyDomain, ...]
    personalization_factors: tuple[str, ...]
    competency_driven: bool


@dataclass(frozen=True)
class CurriculumTraceabilityRecord:
    """Curriculum traceability record."""

    traceability_id: str
    curriculum_id: str
    lesson_ids: tuple[str, ...]
    competency_domains: tuple[CompetencyDomain, ...]
    assessment_ids: tuple[str, ...]
    case_file_ids: tuple[str, ...]
    institutional_knowledge_ids: tuple[str, ...]
    doctrine_ids: tuple[str, ...]
    specification_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    complete: bool


@dataclass(frozen=True)
class CurriculumEffectivenessMetrics:
    """Curriculum effectiveness metrics."""

    metrics_id: str
    curriculum_effectiveness: float
    knowledge_retention: float
    competency_growth: float
    learning_velocity: float
    educational_efficiency: float
    long_term_financial_improvement: float
    student_engagement: float
    assessment_outcomes: float


@dataclass(frozen=True)
class CurriculumAdaptationRecord:
    """Curriculum adaptation record."""

    adaptation_id: str
    curriculum_id: str
    trigger: CurriculumAdaptationTrigger
    assessment_result_ids: tuple[str, ...]
    adapted_module_ids: tuple[str, ...]
    deterministic_reason: str


@dataclass(frozen=True)
class CurriculumDashboard:
    """Curriculum dashboard."""

    dashboard_id: str
    module_count: int
    prerequisite_count: int
    pathway_length: int
    traceability_complete: bool
    curriculum_effectiveness: float
    version_count: int
    curriculum_health: str


@dataclass(frozen=True)
class CurriculumSystemPrompt:
    """Curriculum Office prompt."""

    prompt_id: str
    version: str
    prompt_text: str


class CurriculumOffice:
    """Educational architect for personalized Academy pathways."""

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
        self._version_history: list[CurriculumVersionRecord] = []

    @property
    def curriculum_version_history(self) -> tuple[CurriculumVersionRecord, ...]:
        """Return immutable curriculum version history."""
        return tuple(self._version_history)

    def system_prompt(self) -> CurriculumSystemPrompt:
        """Return governing Curriculum Office prompt."""
        return CurriculumSystemPrompt(
            "PROMPT-CURRICULUM-080",
            "1.0.0",
            (
                "You are the Curriculum Office (CO) of the ARGOS Academy.\n\n"
                "Your responsibility is to design, maintain, and continuously optimize personalized educational "
                "pathways that transform ARGOS's validated institutional intelligence into measurable financial "
                "competence. You do not create new institutional knowledge, determine financial truth, or evaluate "
                "student competency. You organize educational experiences into the sequence most likely to maximize "
                "each student's long-term financial reasoning, investment judgment, and decision-making ability."
            ),
        )

    def design_curriculum(
        self,
        curriculum_id: str,
        version: str,
        learner_profile: CompetencyProfile,
        modules: tuple[CurriculumModule, ...],
        prerequisites: tuple[PrerequisiteRelationship, ...],
        assessment_result_ids: tuple[str, ...],
        effectiveness_metrics: CurriculumEffectivenessMetrics,
        revision_trigger: CurriculumAdaptationTrigger,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Design a deterministic personalized curriculum."""
        self.configuration_service.validate_startup()
        ordered_modules = tuple(sorted(modules, key=lambda item: item.module_id))
        ordered_prerequisites = tuple(sorted(prerequisites, key=lambda item: item.relationship_id))
        missing = _missing_prerequisites(ordered_modules, ordered_prerequisites)
        version_record = CurriculumVersionRecord(
            f"CVR-{document_sequence:06d}",
            curriculum_id,
            version,
            self._version_history[-1].version_id if self._version_history else None,
            revision_trigger,
            True,
            utc_timestamp(),
        )
        self._version_history.append(version_record)
        curriculum = CurriculumMap(
            curriculum_id,
            learner_profile.learner_id,
            ordered_modules,
            ordered_prerequisites,
            tuple(sorted({module.competency_domain for module in ordered_modules}, key=lambda item: item.value)),
            version_record,
        )
        pathway = _pathway(curriculum, learner_profile)
        traceability = _traceability(curriculum)
        adaptation = CurriculumAdaptationRecord(
            f"CAR-{document_sequence:06d}",
            curriculum_id,
            revision_trigger,
            assessment_result_ids,
            pathway.ordered_module_ids,
            "Curriculum adapted from assessment results, learner profile, prerequisite graph, and validated source coverage.",
        )
        dashboard = CurriculumDashboard(
            f"CDASH-{document_sequence:06d}",
            len(ordered_modules),
            len(ordered_prerequisites),
            len(pathway.ordered_module_ids),
            traceability.complete and not missing,
            effectiveness_metrics.curriculum_effectiveness,
            len(self._version_history),
            "healthy" if traceability.complete and not missing and effectiveness_metrics.curriculum_effectiveness >= 0.75 else "attention",
        )
        return {
            "curriculum_architecture": self._persist_contract(
                "CURRICULUM_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Curriculum Architecture.",
                {"curriculum_system_prompt": self.system_prompt(), "competency_driven": True, "creates_new_institutional_knowledge": False},
            ),
            "curriculum_map": self._persist_contract(
                "CURRICULUM_MAP",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Curriculum Map.",
                {"curriculum_map": curriculum, "missing_prerequisite_relationships": missing},
            ),
            "personalized_learning_pathway": self._persist_contract(
                "PERSONALIZED_LEARNING_PATHWAY",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Personalized Learning Pathway.",
                {"learning_pathway": pathway, "learner_profile": learner_profile},
            ),
            "curriculum_traceability_record": self._persist_contract(
                "CURRICULUM_TRACEABILITY_RECORD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Curriculum Traceability Record.",
                {"curriculum_traceability_record": traceability, "previous_curriculum_versions_discarded": False},
            ),
            "curriculum_adaptation_record": self._persist_contract(
                "CURRICULUM_ADAPTATION_RECORD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Curriculum Adaptation Record.",
                {"curriculum_adaptation_record": adaptation, "curriculum_effectiveness_metrics": effectiveness_metrics},
            ),
            "curriculum_dashboard": self._persist_contract(
                "CURRICULUM_DASHBOARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 5,
                "Curriculum Dashboard.",
                {"curriculum_dashboard": dashboard, "curriculum_version_history": self.curriculum_version_history},
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


def _pathway(curriculum: CurriculumMap, learner_profile: CompetencyProfile) -> LearningPathway:
    demonstrated = set(learner_profile.demonstrated_competencies)
    remaining = [module for module in curriculum.modules if module.competency_domain not in demonstrated]
    prerequisite_order = _competency_order(curriculum.prerequisites)
    remaining.sort(key=lambda module: (prerequisite_order.get(module.competency_domain, 999), module.module_id))
    factors = (
        f"learning_velocity={learner_profile.learning_velocity}",
        f"preferred_learning_style={learner_profile.preferred_learning_style}",
        f"goals={','.join(learner_profile.educational_goals)}",
        f"interests={','.join(learner_profile.investment_interests)}",
    )
    return LearningPathway(
        f"LP-{hashlib.sha256(curriculum.curriculum_id.encode('utf-8')).hexdigest()[:8].upper()}",
        learner_profile.learner_id,
        tuple(module.module_id for module in remaining),
        tuple(sorted(demonstrated, key=lambda item: item.value)),
        factors,
        True,
    )


def _competency_order(prerequisites: tuple[PrerequisiteRelationship, ...]) -> dict[CompetencyDomain, int]:
    order: dict[CompetencyDomain, int] = {}
    for relationship in prerequisites:
        order.setdefault(relationship.prerequisite_competency, len(order))
        order.setdefault(relationship.dependent_competency, len(order))
    return order


def _missing_prerequisites(
    modules: tuple[CurriculumModule, ...],
    prerequisites: tuple[PrerequisiteRelationship, ...],
) -> tuple[str, ...]:
    domains = {module.competency_domain for module in modules}
    missing = []
    for relationship in prerequisites:
        if relationship.prerequisite_competency not in domains or relationship.dependent_competency not in domains:
            missing.append(relationship.relationship_id)
    return tuple(sorted(missing))


def _traceability(curriculum: CurriculumMap) -> CurriculumTraceabilityRecord:
    lesson_ids = tuple(sorted({item for module in curriculum.modules for item in module.lesson_ids}))
    assessment_ids = tuple(sorted({item for module in curriculum.modules for item in module.assessment_ids}))
    case_file_ids = tuple(sorted({item for module in curriculum.modules for item in module.case_study_ids}))
    knowledge_ids = tuple(sorted({item for module in curriculum.modules for item in module.validated_knowledge_ids}))
    doctrine_ids = tuple(sorted({item for module in curriculum.modules for item in module.doctrine_ids}))
    specification_ids = tuple(sorted({item for module in curriculum.modules for item in module.specification_ids}))
    evidence_ids = tuple(sorted({item for module in curriculum.modules for item in module.evidence_ids} | {item for rel in curriculum.prerequisites for item in rel.evidence_ids}))
    return CurriculumTraceabilityRecord(
        f"CTR-{hashlib.sha256(curriculum.curriculum_id.encode('utf-8')).hexdigest()[:8].upper()}",
        curriculum.curriculum_id,
        lesson_ids,
        curriculum.required_competencies,
        assessment_ids,
        case_file_ids,
        knowledge_ids,
        doctrine_ids,
        specification_ids,
        evidence_ids,
        all((lesson_ids, assessment_ids, case_file_ids, knowledge_ids, doctrine_ids, specification_ids, evidence_ids)),
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
        produced_by_staff_id=CURRICULUM_STAFF_ID,
        produced_by_group_id=ACADEMY_GROUP_ID,
        intended_consumer_group_id=ACADEMY_GROUP_ID,
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
