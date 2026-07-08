"""Academy Fusion Office."""

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


ACADEMY_FUSION_OFFICE_ID = "ACADEMY-OFFICE-006"
ACADEMY_FUSION_STAFF_ID = "STF-093"


class AcademyOfficeSignalType(str, Enum):
    """Academy office signal type."""

    INSTRUCTION = "instruction"
    CURRICULUM = "curriculum"
    ASSESSMENT = "assessment"
    CASE_STUDY = "case_study"
    TUTORING = "tutoring"


class LearningInterventionPriority(str, Enum):
    """Learning intervention priority."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass(frozen=True)
class AcademyOfficeSignal:
    """Cross-office educational signal."""

    signal_id: str
    signal_type: AcademyOfficeSignalType
    source_office_id: str
    learner_id: str
    competency_domain: CompetencyDomain
    score: float
    knowledge_gap: bool
    evidence_ids: tuple[str, ...]
    recommended_action: str


@dataclass(frozen=True)
class EducationalIntegrationArchitecture:
    """Educational integration architecture."""

    architecture_id: str
    integrated_office_types: tuple[AcademyOfficeSignalType, ...]
    evidence_based: bool
    historically_traceable: bool
    deterministic_principles: tuple[str, ...]


@dataclass(frozen=True)
class StudentEducationalModel:
    """Student educational model."""

    model_id: str
    learner_id: str
    learner_level: LearnerLevel
    competency_scores: tuple[tuple[CompetencyDomain, float], ...]
    knowledge_gap_domains: tuple[CompetencyDomain, ...]
    mastery_domains: tuple[CompetencyDomain, ...]
    traceability_reference_ids: tuple[str, ...]


@dataclass(frozen=True)
class PersonalizedLearningOrchestrationFramework:
    """Personalized learning orchestration framework."""

    orchestration_id: str
    learner_id: str
    prioritized_interventions: tuple[str, ...]
    intervention_priority: LearningInterventionPriority
    optimized_sequence: tuple[AcademyOfficeSignalType, ...]


@dataclass(frozen=True)
class CrossOfficeCoordinationFramework:
    """Cross-office coordination process."""

    coordination_id: str
    learner_id: str
    coordinated_office_ids: tuple[str, ...]
    coordination_actions: tuple[str, ...]
    consistent: bool


@dataclass(frozen=True)
class EducationalOptimizationFramework:
    """Educational optimization methodology."""

    optimization_id: str
    learner_id: str
    optimization_basis: tuple[str, ...]
    recommended_sequence: tuple[str, ...]
    expected_learning_gain: float


@dataclass(frozen=True)
class LearningFeedbackArchitecture:
    """Learning feedback loop."""

    feedback_id: str
    learner_id: str
    feedback_sources: tuple[AcademyOfficeSignalType, ...]
    loop_actions: tuple[str, ...]
    feedback_loop_documented: bool


@dataclass(frozen=True)
class EducationalQualityAssuranceFramework:
    """Educational quality assurance framework."""

    qa_id: str
    traceability_complete: bool
    all_recommendations_evidence_based: bool
    cross_office_consistency: bool
    validation_errors: tuple[str, ...]
    valid: bool


@dataclass(frozen=True)
class AcademyIntelligenceDashboard:
    """Academy Intelligence Dashboard."""

    dashboard_id: str
    learner_id: str
    signal_count: int
    integrated_office_count: int
    knowledge_gap_count: int
    intervention_count: int
    traceability_complete: bool
    academy_learning_health: str


@dataclass(frozen=True)
class AcademyFusionSystemPrompt:
    """Academy Fusion Office prompt."""

    prompt_id: str
    version: str
    prompt_text: str


class AcademyFusionOffice:
    """Educational intelligence center for the Academy."""

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

    def system_prompt(self) -> AcademyFusionSystemPrompt:
        """Return governing Academy Fusion Office prompt."""
        return AcademyFusionSystemPrompt(
            "PROMPT-ACADEMY-FUSION-084",
            "1.0.0",
            (
                "You are the Academy Fusion Office of ARGOS.\n\n"
                "Integrate every educational capability into a unified, personalized learning system. Continuously "
                "synthesize instruction, curriculum, assessment, historical case studies, tutoring, competency "
                "development, and educational analytics into adaptive educational strategies that maximize each "
                "student's financial reasoning, investment judgment, and long-term mastery."
            ),
        )

    def integrate_learning_system(
        self,
        learner_id: str,
        learner_level: LearnerLevel,
        office_signals: tuple[AcademyOfficeSignal, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Integrate Academy office outputs into a unified learning strategy."""
        self.configuration_service.validate_startup()
        ordered_signals = tuple(sorted(office_signals, key=lambda signal: signal.signal_id))
        architecture = EducationalIntegrationArchitecture(
            f"EIA-{document_sequence:06d}",
            tuple(sorted({signal.signal_type for signal in ordered_signals}, key=lambda item: item.value)),
            True,
            True,
            (
                "Fuse every Academy office signal without discarding disagreement.",
                "Prioritize knowledge gaps by deterministic score and domain.",
                "Require evidence traceability for every educational recommendation.",
                "Coordinate interventions across offices through explicit records.",
            ),
        )
        model = _student_model(learner_id, learner_level, ordered_signals, document_sequence)
        orchestration = _orchestration(learner_id, ordered_signals, model, document_sequence)
        coordination = _coordination(learner_id, ordered_signals, document_sequence)
        optimization = _optimization(learner_id, ordered_signals, model, document_sequence)
        feedback = LearningFeedbackArchitecture(
            f"LFA-{document_sequence:06d}",
            learner_id,
            tuple(sorted({signal.signal_type for signal in ordered_signals}, key=lambda item: item.value)),
            (
                "Route assessment gaps to Curriculum Office.",
                "Route misconception signals to Finance Tutor Office.",
                "Route historical practice needs to Case Study Office.",
                "Route validated progress back to Academy analytics.",
            ),
            True,
        )
        qa = _quality_assurance(ordered_signals, coordination, document_sequence)
        dashboard = AcademyIntelligenceDashboard(
            f"AID-{document_sequence:06d}",
            learner_id,
            len(ordered_signals),
            len(architecture.integrated_office_types),
            len(model.knowledge_gap_domains),
            len(orchestration.prioritized_interventions),
            qa.traceability_complete,
            "healthy" if qa.valid else "attention",
        )
        return {
            "educational_integration_architecture": self._persist_contract(
                "EDUCATIONAL_INTEGRATION_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Educational Integration Architecture.",
                {"educational_integration_architecture": architecture, "academy_fusion_system_prompt": self.system_prompt()},
            ),
            "student_educational_model": self._persist_contract(
                "STUDENT_EDUCATIONAL_MODEL",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Student Educational Model.",
                {"student_educational_model": model},
            ),
            "personalized_learning_orchestration_framework": self._persist_contract(
                "PERSONALIZED_LEARNING_ORCHESTRATION_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Personalized Learning Orchestration Framework.",
                {"personalized_learning_orchestration_framework": orchestration},
            ),
            "cross_office_coordination_framework": self._persist_contract(
                "CROSS_OFFICE_COORDINATION_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Cross-Office Coordination Framework.",
                {"cross_office_coordination_framework": coordination},
            ),
            "educational_optimization_framework": self._persist_contract(
                "EDUCATIONAL_OPTIMIZATION_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Educational Optimization Framework.",
                {"educational_optimization_framework": optimization},
            ),
            "learning_feedback_architecture": self._persist_contract(
                "LEARNING_FEEDBACK_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence + 5,
                "Learning Feedback Architecture.",
                {"learning_feedback_architecture": feedback, "educational_quality_assurance_framework": qa},
            ),
            "academy_intelligence_dashboard": self._persist_contract(
                "ACADEMY_INTELLIGENCE_DASHBOARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 6,
                "Academy Intelligence Dashboard.",
                {"academy_intelligence_dashboard": dashboard},
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


def _student_model(
    learner_id: str,
    learner_level: LearnerLevel,
    signals: tuple[AcademyOfficeSignal, ...],
    document_sequence: int,
) -> StudentEducationalModel:
    grouped: dict[CompetencyDomain, list[float]] = {}
    for signal in signals:
        grouped.setdefault(signal.competency_domain, []).append(signal.score)
    scores = tuple(
        (domain, round(sum(values) / len(values), 4))
        for domain, values in sorted(grouped.items(), key=lambda item: item[0].value)
    )
    gaps = tuple(domain for domain, score in scores if score < 0.70 or any(signal.knowledge_gap and signal.competency_domain == domain for signal in signals))
    mastery = tuple(domain for domain, score in scores if score >= 0.85 and domain not in gaps)
    evidence = tuple(sorted({item for signal in signals for item in signal.evidence_ids}))
    return StudentEducationalModel(
        f"SEM-{document_sequence:06d}",
        learner_id,
        learner_level,
        scores,
        gaps,
        mastery,
        evidence,
    )


def _orchestration(
    learner_id: str,
    signals: tuple[AcademyOfficeSignal, ...],
    model: StudentEducationalModel,
    document_sequence: int,
) -> PersonalizedLearningOrchestrationFramework:
    gap_domains = set(model.knowledge_gap_domains)
    interventions = tuple(
        signal.recommended_action
        for signal in sorted(signals, key=lambda item: (item.score, item.competency_domain.value, item.signal_id))
        if signal.knowledge_gap or signal.competency_domain in gap_domains
    )
    priority = LearningInterventionPriority.URGENT if any(signal.score < 0.50 for signal in signals) else LearningInterventionPriority.HIGH if interventions else LearningInterventionPriority.NORMAL
    sequence = tuple(sorted({signal.signal_type for signal in signals if signal.knowledge_gap or signal.competency_domain in gap_domains}, key=lambda item: item.value))
    if not sequence:
        sequence = (AcademyOfficeSignalType.INSTRUCTION, AcademyOfficeSignalType.CASE_STUDY, AcademyOfficeSignalType.TUTORING)
    return PersonalizedLearningOrchestrationFramework(
        f"PLOF-{document_sequence:06d}",
        learner_id,
        interventions,
        priority,
        sequence,
    )


def _coordination(
    learner_id: str,
    signals: tuple[AcademyOfficeSignal, ...],
    document_sequence: int,
) -> CrossOfficeCoordinationFramework:
    office_ids = tuple(sorted({signal.source_office_id for signal in signals}))
    return CrossOfficeCoordinationFramework(
        f"COCF-{document_sequence:06d}",
        learner_id,
        office_ids,
        tuple(f"Coordinate {signal.signal_type.value} signal {signal.signal_id}" for signal in signals),
        len(office_ids) == len({signal.source_office_id for signal in signals}),
    )


def _optimization(
    learner_id: str,
    signals: tuple[AcademyOfficeSignal, ...],
    model: StudentEducationalModel,
    document_sequence: int,
) -> EducationalOptimizationFramework:
    gaps = tuple(domain.value for domain in model.knowledge_gap_domains)
    average_score = round(sum(signal.score for signal in signals) / len(signals), 4) if signals else 0.0
    gain = round(max(0.0, 0.85 - average_score), 4)
    return EducationalOptimizationFramework(
        f"EOF-{document_sequence:06d}",
        learner_id,
        tuple(f"gap={gap}" for gap in gaps) or ("maintain_mastery",),
        tuple(f"Improve {gap.replace('_', ' ')} through coordinated Academy sequence." for gap in gaps) or ("Advance to synthesis case study.",),
        gain,
    )


def _quality_assurance(
    signals: tuple[AcademyOfficeSignal, ...],
    coordination: CrossOfficeCoordinationFramework,
    document_sequence: int,
) -> EducationalQualityAssuranceFramework:
    errors = []
    if not signals:
        errors.append("missing_academy_office_signals")
    if any(not signal.evidence_ids for signal in signals):
        errors.append("signal_missing_evidence")
    if not coordination.consistent:
        errors.append("cross_office_coordination_inconsistent")
    valid = not errors
    return EducationalQualityAssuranceFramework(
        f"EQAF-{document_sequence:06d}",
        bool(signals) and not any(not signal.evidence_ids for signal in signals),
        bool(signals) and all(signal.recommended_action for signal in signals),
        coordination.consistent,
        tuple(sorted(errors)),
        valid,
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
        produced_by_staff_id=ACADEMY_FUSION_STAFF_ID,
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
        return {_json_ready(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
