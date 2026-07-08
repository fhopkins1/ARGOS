"""Academy Framework."""

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


ACADEMY_GROUP_ID = "DEP-009"
ACADEMY_CHIEF_OFFICE_ID = "ACADEMY-OFFICE-001"
ACADEMY_CHIEF_STAFF_ID = "STF-087"


class CompetencyDomain(str, Enum):
    """Financial competency domain."""

    EVIDENCE_REASONING = "evidence_reasoning"
    MARKET_STRUCTURE = "market_structure"
    RISK_DISCIPLINE = "risk_discipline"
    PORTFOLIO_JUDGMENT = "portfolio_judgment"
    BEHAVIORAL_AWARENESS = "behavioral_awareness"
    EXECUTION_LITERACY = "execution_literacy"
    HISTORICAL_LEARNING = "historical_learning"


class LearnerLevel(str, Enum):
    """Learner level."""

    NOVICE = "novice"
    DEVELOPING = "developing"
    COMPETENT = "competent"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass(frozen=True)
class AcademyOfficeTemplate:
    """Academy office template."""

    office_id: str
    name: str
    mission: str


@dataclass(frozen=True)
class AcademyArchitecture:
    """Academy Architecture."""

    architecture_id: str
    mission: str
    office_templates: tuple[AcademyOfficeTemplate, ...]
    user_facing: bool
    librarian_certification_required: bool


@dataclass(frozen=True)
class EducationalPhilosophyFramework:
    """Educational philosophy framework."""

    framework_id: str
    evidence_based: bool
    deterministic: bool
    personalized: bool
    doctrine_traceable: bool
    principle_statements: tuple[str, ...]


@dataclass(frozen=True)
class FinancialCompetencyRecord:
    """Financial competency model record."""

    competency_id: str
    domain: CompetencyDomain
    learner_level: LearnerLevel
    measurable_outcomes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]


@dataclass(frozen=True)
class PersonalizedLearningFramework:
    """Personalized learning framework."""

    framework_id: str
    learner_id: str
    current_level: LearnerLevel
    target_level: LearnerLevel
    recommended_competency_ids: tuple[str, ...]
    personalization_rules: tuple[str, ...]


@dataclass(frozen=True)
class EducationalPipelineStage:
    """Educational pipeline stage."""

    stage_id: str
    name: str
    input_artifact_types: tuple[str, ...]
    output_artifact_types: tuple[str, ...]
    traceability_required: bool


@dataclass(frozen=True)
class EducationalPipelineModel:
    """Educational pipeline model."""

    pipeline_id: str
    stages: tuple[EducationalPipelineStage, ...]
    institutional_knowledge_ids: tuple[str, ...]
    pipeline_operational: bool


@dataclass(frozen=True)
class AcademyGovernanceFramework:
    """Academy governance framework."""

    governance_id: str
    librarian_certification_id: str
    approved_knowledge_ids: tuple[str, ...]
    prohibited_unvalidated_content: bool
    traceability_required: bool
    governance_requirements: tuple[str, ...]


@dataclass(frozen=True)
class EducationalSuccessMetric:
    """Educational success metric."""

    metric_id: str
    name: str
    deterministic_measurement: str
    target_threshold: float


@dataclass(frozen=True)
class EducationalDashboard:
    """Educational dashboard."""

    dashboard_id: str
    competency_count: int
    pipeline_stage_count: int
    traceability_coverage: float
    personalization_ready: bool
    governance_ready: bool
    educational_health: str


@dataclass(frozen=True)
class AcademySystemPrompt:
    """Academy System Prompt."""

    prompt_id: str
    version: str
    prompt_text: str


class AcademyFramework:
    """User-facing evidence-based financial education framework."""

    mission = "Enable every user to benefit from the complete accumulated knowledge of ARGOS through deterministic, evidence-based financial education."

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

    def system_prompt(self) -> AcademySystemPrompt:
        """Return governing Academy prompt."""
        return AcademySystemPrompt(
            "PROMPT-ACADEMY-078",
            "1.0.0",
            (
                "You are the Academy of ARGOS.\n\n"
                "Your mission is to enable every user to benefit from the complete accumulated knowledge of ARGOS "
                "through deterministic, evidence-based financial education.\n\n"
                "Transform validated institutional knowledge into personalized learning experiences that improve "
                "financial reasoning, investment judgment, and decision-making ability. Teach only knowledge "
                "supported by empirical evidence, historical market experience, validated doctrine, and scientific "
                "investigation. Continuously personalize instruction, maintain complete traceability to supporting "
                "evidence, and ensure that every lesson evolves as ARGOS continues to learn."
            ),
        )

    def establish_academy(
        self,
        learner_id: str,
        current_level: LearnerLevel,
        target_level: LearnerLevel,
        institutional_knowledge_ids: tuple[str, ...],
        evidence_reference_ids: tuple[str, ...],
        librarian_certification_id: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Establish Academy framework artifacts deterministically."""
        self.configuration_service.validate_startup()
        architecture = AcademyArchitecture(
            f"AA-{document_sequence:06d}",
            self.mission,
            academy_office_templates(),
            True,
            True,
        )
        philosophy = EducationalPhilosophyFramework(
            f"EPF-{document_sequence:06d}",
            True,
            True,
            True,
            True,
            (
                "Teach only empirically validated knowledge.",
                "Separate education from investment recommendation.",
                "Personalize learning while preserving evidence traceability.",
                "Revise lessons only through governed Librarian knowledge updates.",
            ),
        )
        competencies = _competencies(current_level, evidence_reference_ids, document_sequence)
        personalized = PersonalizedLearningFramework(
            f"PLF-{document_sequence:06d}",
            learner_id,
            current_level,
            target_level,
            tuple(record.competency_id for record in competencies if _level_rank(record.learner_level) <= _level_rank(target_level)),
            (
                "Prioritize lower-scoring competency domains first.",
                "Require evidence references for every lesson recommendation.",
                "Escalate learner only after deterministic assessment evidence.",
            ),
        )
        pipeline = EducationalPipelineModel(
            f"EPM-{document_sequence:06d}",
            _pipeline_stages(document_sequence),
            institutional_knowledge_ids,
            bool(institutional_knowledge_ids and evidence_reference_ids),
        )
        governance = AcademyGovernanceFramework(
            f"AGF-{document_sequence:06d}",
            librarian_certification_id,
            institutional_knowledge_ids,
            True,
            True,
            (
                "Consume only certified Librarian knowledge packages.",
                "Expose evidence references for every lesson.",
                "Do not provide individualized investment instructions.",
                "Refresh educational material when doctrine or validated knowledge changes.",
            ),
        )
        metrics = _success_metrics(document_sequence)
        traceability_coverage = 1.0 if evidence_reference_ids and institutional_knowledge_ids else 0.0
        dashboard = EducationalDashboard(
            f"EDU-DASH-{document_sequence:06d}",
            len(competencies),
            len(pipeline.stages),
            traceability_coverage,
            bool(personalized.recommended_competency_ids),
            bool(governance.librarian_certification_id and governance.approved_knowledge_ids),
            "healthy" if pipeline.pipeline_operational and traceability_coverage == 1.0 else "attention",
        )
        return {
            "academy_architecture": self._persist_contract(
                "ACADEMY_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Academy Architecture.",
                {"academy_architecture": architecture, "academy_system_prompt": self.system_prompt()},
            ),
            "educational_philosophy_framework": self._persist_contract(
                "EDUCATIONAL_PHILOSOPHY_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Educational Philosophy Framework.",
                {"educational_philosophy_framework": philosophy, "deterministic_educational_principles_established": True},
            ),
            "financial_competency_framework": self._persist_contract(
                "FINANCIAL_COMPETENCY_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Financial Competency Framework.",
                {"financial_competency_records": competencies},
            ),
            "personalized_learning_framework": self._persist_contract(
                "PERSONALIZED_LEARNING_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Personalized Learning Framework.",
                {"personalized_learning_framework": personalized},
            ),
            "educational_pipeline_model": self._persist_contract(
                "EDUCATIONAL_PIPELINE_MODEL",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Educational Pipeline Model.",
                {"educational_pipeline_model": pipeline, "academy_governance_framework": governance},
            ),
            "educational_dashboard": self._persist_contract(
                "EDUCATIONAL_DASHBOARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 5,
                "Educational Dashboard.",
                {"educational_dashboard": dashboard, "educational_success_metrics": metrics},
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


def academy_office_templates() -> tuple[AcademyOfficeTemplate, ...]:
    """Return Academy office templates."""
    return (
        AcademyOfficeTemplate("ACADEMY-OFFICE-001", "Instruction Office", "Deliver deterministic evidence-based instruction."),
        AcademyOfficeTemplate("ACADEMY-OFFICE-002", "Curriculum Office", "Convert governed knowledge into curriculum paths."),
        AcademyOfficeTemplate("ACADEMY-OFFICE-003", "Knowledge Assessment Office", "Measure learner competency and educational outcomes."),
        AcademyOfficeTemplate("ACADEMY-OFFICE-004", "Case Study Office", "Teach from traceable historical market and ARGOS cases."),
        AcademyOfficeTemplate("ACADEMY-OFFICE-005", "Finance Tutor Office", "Personalize financial reasoning support for users."),
        AcademyOfficeTemplate("ACADEMY-OFFICE-006", "Academy Fusion Office", "Fuse Academy outcomes and readiness signals."),
    )


def _competencies(level: LearnerLevel, evidence_reference_ids: tuple[str, ...], document_sequence: int) -> tuple[FinancialCompetencyRecord, ...]:
    return tuple(
        FinancialCompetencyRecord(
            f"FCR-{document_sequence:06d}-{index:03d}",
            domain,
            level,
            (
                f"Explain {domain.value.replace('_', ' ')} using evidence.",
                f"Apply {domain.value.replace('_', ' ')} to deterministic case material.",
            ),
            evidence_reference_ids,
        )
        for index, domain in enumerate(CompetencyDomain, start=1)
    )


def _pipeline_stages(document_sequence: int) -> tuple[EducationalPipelineStage, ...]:
    stages = (
        ("knowledge_intake", ("validated_institutional_knowledge",), ("governed_learning_source",)),
        ("curriculum_mapping", ("governed_learning_source",), ("curriculum_unit",)),
        ("personalized_instruction", ("curriculum_unit", "learner_profile"), ("lesson_plan",)),
        ("assessment", ("lesson_plan", "learner_response"), ("competency_evidence",)),
        ("feedback", ("competency_evidence",), ("learning_improvement_signal",)),
    )
    return tuple(
        EducationalPipelineStage(f"EPS-{document_sequence:06d}-{index:03d}", name, inputs, outputs, True)
        for index, (name, inputs, outputs) in enumerate(stages, start=1)
    )


def _success_metrics(document_sequence: int) -> tuple[EducationalSuccessMetric, ...]:
    return (
        EducationalSuccessMetric(f"ESM-{document_sequence:06d}-001", "Competency Gain", "post_assessment_score - baseline_score", 0.10),
        EducationalSuccessMetric(f"ESM-{document_sequence:06d}-002", "Evidence Recall", "correct_evidence_references / required_references", 0.90),
        EducationalSuccessMetric(f"ESM-{document_sequence:06d}-003", "Reasoning Quality", "rubric_passed_reasoning_steps / required_steps", 0.85),
        EducationalSuccessMetric(f"ESM-{document_sequence:06d}-004", "Doctrine Alignment", "doctrine_aligned_responses / assessed_responses", 0.95),
    )


def _level_rank(level: LearnerLevel) -> int:
    return {
        LearnerLevel.NOVICE: 1,
        LearnerLevel.DEVELOPING: 2,
        LearnerLevel.COMPETENT: 3,
        LearnerLevel.ADVANCED: 4,
        LearnerLevel.EXPERT: 5,
    }[level]


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
        produced_by_staff_id=ACADEMY_CHIEF_STAFF_ID,
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
