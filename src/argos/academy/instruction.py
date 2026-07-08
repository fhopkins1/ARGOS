"""Instruction Office."""

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


INSTRUCTION_OFFICE_ID = "ACADEMY-OFFICE-001"
INSTRUCTION_STAFF_ID = "STF-088"


class LessonComponentType(str, Enum):
    """Lesson component type."""

    CONCEPT = "concept"
    EVIDENCE = "evidence"
    HISTORICAL_CASE = "historical_case"
    DECISION_RECONSTRUCTION = "decision_reconstruction"
    PRACTICE_PROMPT = "practice_prompt"
    REFLECTION = "reflection"
    ASSESSMENT = "assessment"


@dataclass(frozen=True)
class InstructionSourceMaterial:
    """Validated instructional source material."""

    source_id: str
    title: str
    competency_domain: CompetencyDomain
    institutional_knowledge_ids: tuple[str, ...]
    doctrine_ids: tuple[str, ...]
    case_file_ids: tuple[str, ...]
    research_reference_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    historical_outcome_ids: tuple[str, ...]


@dataclass(frozen=True)
class InstructionArchitecture:
    """Instruction Architecture."""

    architecture_id: str
    office_id: str
    philosophy: str
    teaches_reasoning_process: bool
    avoids_investment_instructions: bool
    evidence_traceability_required: bool


@dataclass(frozen=True)
class LessonDesignStandard:
    """Lesson design standard."""

    standard_id: str
    lesson_id: str
    learner_level: LearnerLevel
    components: tuple[LessonComponentType, ...]
    progressive_sequence: tuple[str, ...]


@dataclass(frozen=True)
class EducationalTranslationFramework:
    """Educational translation framework."""

    translation_id: str
    source_id: str
    translated_concept: str
    plain_language_summary: str
    reasoning_steps: tuple[str, ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class HistoricalLearningFramework:
    """Historical learning framework."""

    historical_learning_id: str
    case_file_ids: tuple[str, ...]
    historical_outcome_ids: tuple[str, ...]
    lesson_from_history: str
    uncertainty_preserved: bool


@dataclass(frozen=True)
class DecisionReconstructionStandard:
    """Decision reconstruction standard."""

    reconstruction_id: str
    lesson_id: str
    decision_model_id: str
    reconstructed_steps: tuple[str, ...]
    alternative_paths: tuple[str, ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class PersonalizedInstructionFramework:
    """Personalized instruction framework."""

    personalization_id: str
    learner_id: str
    learner_level: LearnerLevel
    target_competency: CompetencyDomain
    pacing: str
    adaptation_rules: tuple[str, ...]


@dataclass(frozen=True)
class LessonValidationProcess:
    """Lesson validation process."""

    validation_id: str
    lesson_id: str
    traceability_complete: bool
    doctrine_supported: bool
    historical_context_present: bool
    no_investment_instruction: bool
    lesson_valid: bool


@dataclass(frozen=True)
class InstructionMetric:
    """Instruction educational metric."""

    metric_id: str
    name: str
    deterministic_measurement: str
    target_threshold: float


@dataclass(frozen=True)
class InstructionDashboard:
    """Instruction dashboard."""

    dashboard_id: str
    lesson_count: int
    valid_lesson_count: int
    traceability_coverage: float
    historical_coverage: float
    personalization_ready: bool
    instruction_health: str


@dataclass(frozen=True)
class AcademyInstructionPrompt:
    """Academy Instruction Prompt."""

    prompt_id: str
    version: str
    prompt_text: str


class InstructionOffice:
    """Translate validated ARGOS intelligence into personalized instruction."""

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

    def system_prompt(self) -> AcademyInstructionPrompt:
        """Return governing Instruction Office prompt."""
        return AcademyInstructionPrompt(
            "PROMPT-INSTRUCTION-079",
            "1.0.0",
            (
                "You are the Instruction Office of the ARGOS Academy.\n\n"
                "Translate ARGOS's validated institutional intelligence into personalized, evidence-based financial "
                "instruction. Produce lessons that remain fully traceable to historical evidence, doctrine, case "
                "files, research, and institutional knowledge while presenting complex financial concepts in a "
                "progressively understandable manner. Teach users how ARGOS reasons rather than merely what ARGOS "
                "concludes."
            ),
        )

    def create_instruction(
        self,
        learner_id: str,
        learner_level: LearnerLevel,
        source_materials: tuple[InstructionSourceMaterial, ...],
        decision_model_id: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Create deterministic instructional artifacts from validated source material."""
        self.configuration_service.validate_startup()
        ordered = tuple(sorted(source_materials, key=lambda item: item.source_id))
        lesson_id = f"LESSON-{document_sequence:06d}"
        architecture = InstructionArchitecture(
            f"IA-{document_sequence:06d}",
            INSTRUCTION_OFFICE_ID,
            "Teach ARGOS reasoning through evidence, reconstruction, practice, and reflection.",
            True,
            True,
            True,
        )
        design = LessonDesignStandard(
            f"LDS-{document_sequence:06d}",
            lesson_id,
            learner_level,
            tuple(LessonComponentType),
            _progressive_sequence(learner_level),
        )
        translations = tuple(_translation(source, document_sequence) for source in ordered)
        historical = tuple(_historical(source, document_sequence) for source in ordered)
        reconstruction = _reconstruction(lesson_id, decision_model_id, ordered, document_sequence)
        personalized = PersonalizedInstructionFramework(
            f"PIF-{document_sequence:06d}",
            learner_id,
            learner_level,
            ordered[0].competency_domain if ordered else CompetencyDomain.EVIDENCE_REASONING,
            _pacing(learner_level),
            (
                "Use simpler language when learner level is novice or developing.",
                "Require evidence recall before advancing to decision reconstruction.",
                "Increase case complexity only after validation success.",
            ),
        )
        validation = _validation(lesson_id, ordered, reconstruction, document_sequence)
        metrics = _metrics(document_sequence)
        dashboard = InstructionDashboard(
            f"IDASH-{document_sequence:06d}",
            1,
            1 if validation.lesson_valid else 0,
            1.0 if validation.traceability_complete else 0.0,
            1.0 if validation.historical_context_present else 0.0,
            bool(learner_id and ordered),
            "healthy" if validation.lesson_valid and learner_id else "attention",
        )
        return {
            "instruction_architecture": self._persist_contract(
                "INSTRUCTION_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Instruction Architecture.",
                {"instruction_architecture": architecture, "academy_instruction_prompt": self.system_prompt()},
            ),
            "lesson_design_standard": self._persist_contract(
                "LESSON_DESIGN_STANDARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Lesson Design Standard.",
                {"lesson_design_standard": design, "deterministic_instructional_principles_documented": True},
            ),
            "educational_translation_framework": self._persist_contract(
                "EDUCATIONAL_TRANSLATION_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Educational Translation Framework.",
                {"educational_translation_records": translations},
            ),
            "historical_learning_framework": self._persist_contract(
                "HISTORICAL_LEARNING_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Historical Learning Framework.",
                {"historical_learning_records": historical, "decision_reconstruction_standard": reconstruction},
            ),
            "personalized_instruction_framework": self._persist_contract(
                "PERSONALIZED_INSTRUCTION_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Personalized Instruction Framework.",
                {"personalized_instruction_framework": personalized, "lesson_validation_process": validation},
            ),
            "instruction_dashboard": self._persist_contract(
                "INSTRUCTION_DASHBOARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 5,
                "Instruction Dashboard.",
                {"instruction_dashboard": dashboard, "instruction_metrics": metrics},
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


def _progressive_sequence(level: LearnerLevel) -> tuple[str, ...]:
    if level in {LearnerLevel.NOVICE, LearnerLevel.DEVELOPING}:
        return ("plain_language_concept", "evidence_walkthrough", "historical_case", "guided_reconstruction", "reflection")
    return ("source_review", "argument_map", "decision_reconstruction", "alternative_explanations", "independent_application")


def _translation(source: InstructionSourceMaterial, document_sequence: int) -> EducationalTranslationFramework:
    concept = source.competency_domain.value.replace("_", " ")
    return EducationalTranslationFramework(
        f"ETF-{document_sequence:06d}-{source.source_id}",
        source.source_id,
        concept,
        f"{source.title} teaches {concept} through verified ARGOS evidence.",
        (
            "Identify the evidence.",
            "Separate observation from interpretation.",
            "Reconstruct the reasoning chain.",
            "State what would change the conclusion.",
        ),
        source.evidence_ids,
    )


def _historical(source: InstructionSourceMaterial, document_sequence: int) -> HistoricalLearningFramework:
    return HistoricalLearningFramework(
        f"HLF-{document_sequence:06d}-{source.source_id}",
        source.case_file_ids,
        source.historical_outcome_ids,
        f"Historical cases for {source.title} are used to teach uncertainty-aware financial reasoning.",
        True,
    )


def _reconstruction(
    lesson_id: str,
    decision_model_id: str,
    sources: tuple[InstructionSourceMaterial, ...],
    document_sequence: int,
) -> DecisionReconstructionStandard:
    evidence_ids = tuple(sorted({evidence for source in sources for evidence in source.evidence_ids}))
    return DecisionReconstructionStandard(
        f"DRS-{document_sequence:06d}",
        lesson_id,
        decision_model_id,
        (
            "Recover the original question.",
            "List evidence available at decision time.",
            "Map assumptions and alternatives.",
            "Compare expected reasoning to observed outcome.",
        ),
        ("More evidence required", "Alternative hypothesis", "Reject unsupported conclusion"),
        evidence_ids,
    )


def _validation(
    lesson_id: str,
    sources: tuple[InstructionSourceMaterial, ...],
    reconstruction: DecisionReconstructionStandard,
    document_sequence: int,
) -> LessonValidationProcess:
    traceability = all(source.evidence_ids and source.institutional_knowledge_ids for source in sources)
    doctrine = all(source.doctrine_ids for source in sources)
    historical = all(source.case_file_ids and source.historical_outcome_ids for source in sources)
    no_investment_instruction = True
    return LessonValidationProcess(
        f"LVP-{document_sequence:06d}",
        lesson_id,
        traceability,
        doctrine,
        historical,
        no_investment_instruction,
        traceability and doctrine and historical and bool(reconstruction.evidence_ids) and no_investment_instruction,
    )


def _pacing(level: LearnerLevel) -> str:
    return "guided" if level in {LearnerLevel.NOVICE, LearnerLevel.DEVELOPING} else "independent"


def _metrics(document_sequence: int) -> tuple[InstructionMetric, ...]:
    return (
        InstructionMetric(f"IM-{document_sequence:06d}-001", "Reasoning Reconstruction Accuracy", "correct_reconstruction_steps / required_steps", 0.85),
        InstructionMetric(f"IM-{document_sequence:06d}-002", "Evidence Trace Recall", "cited_evidence_ids / required_evidence_ids", 0.90),
        InstructionMetric(f"IM-{document_sequence:06d}-003", "Historical Case Understanding", "correct_case_interpretations / assessed_cases", 0.85),
        InstructionMetric(f"IM-{document_sequence:06d}-004", "Independent Judgment Quality", "rubric_supported_judgments / submitted_judgments", 0.80),
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
        produced_by_staff_id=INSTRUCTION_STAFF_ID,
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
