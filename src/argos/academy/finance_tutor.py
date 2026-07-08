"""Finance Tutor Office."""

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


FINANCE_TUTOR_OFFICE_ID = "ACADEMY-OFFICE-005"
FINANCE_TUTOR_STAFF_ID = "STF-092"


class ExplanationDepth(str, Enum):
    """Explanation depth level."""

    FOUNDATIONAL = "foundational"
    APPLIED = "applied"
    ADVANCED = "advanced"
    EXPERT = "expert"


class TutorInteractionMode(str, Enum):
    """Tutor interaction mode."""

    SOCRATIC = "socratic"
    EXPLANATORY = "explanatory"
    DECISION_COACHING = "decision_coaching"
    MISCONCEPTION_REPAIR = "misconception_repair"


@dataclass(frozen=True)
class StudentLearningContext:
    """Student tutoring context."""

    learner_id: str
    learner_level: LearnerLevel
    demonstrated_competencies: tuple[CompetencyDomain, ...]
    misconceptions: tuple[str, ...]
    educational_goals: tuple[str, ...]
    learning_history_ids: tuple[str, ...]


@dataclass(frozen=True)
class TutorKnowledgeReference:
    """Traceable tutoring knowledge reference."""

    reference_id: str
    source_type: str
    title: str
    evidence_ids: tuple[str, ...]
    doctrine_ids: tuple[str, ...]
    case_study_ids: tuple[str, ...]


@dataclass(frozen=True)
class PersonalizedTutoringFramework:
    """Personalized tutoring framework."""

    framework_id: str
    learner_id: str
    evidence_based: bool
    adapts_to_competencies: bool
    prohibits_investment_advice: bool
    traceability_required: bool


@dataclass(frozen=True)
class AdaptiveGuidanceArchitecture:
    """Adaptive guidance architecture."""

    architecture_id: str
    learner_id: str
    guidance_mode: TutorInteractionMode
    adaptation_basis: tuple[str, ...]
    next_guidance_actions: tuple[str, ...]


@dataclass(frozen=True)
class SocraticReasoningFramework:
    """Socratic reasoning framework."""

    framework_id: str
    question_sequence: tuple[str, ...]
    immediate_conclusion_preferred: bool
    strengthens_understanding: bool


@dataclass(frozen=True)
class ExplanationDepthStandard:
    """Multi-level explanation architecture."""

    standard_id: str
    selected_depth: ExplanationDepth
    explanation_layers: tuple[str, ...]
    learner_level: LearnerLevel


@dataclass(frozen=True)
class DecisionCoachingFramework:
    """Decision coaching process."""

    coaching_id: str
    learner_id: str
    decision_prompt: str
    required_reasoning_steps: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    coaching_not_advice: bool


@dataclass(frozen=True)
class MisconceptionDetectionRecord:
    """Misconception detection framework."""

    detection_id: str
    learner_id: str
    detected_misconceptions: tuple[str, ...]
    repair_prompts: tuple[str, ...]
    confidence: float


@dataclass(frozen=True)
class EducationalConversationModel:
    """Educational conversation model."""

    model_id: str
    learner_id: str
    turn_sequence: tuple[str, ...]
    referenced_knowledge_ids: tuple[str, ...]
    continuous_coaching_enabled: bool


@dataclass(frozen=True)
class TutorAnalyticsDashboard:
    """Tutor analytics dashboard."""

    dashboard_id: str
    learner_id: str
    reference_count: int
    misconception_count: int
    guidance_mode: TutorInteractionMode
    explanation_depth: ExplanationDepth
    traceability_complete: bool
    tutor_health: str


@dataclass(frozen=True)
class FinanceTutorSystemPrompt:
    """Finance Tutor Office prompt."""

    prompt_id: str
    version: str
    prompt_text: str


class FinanceTutorOffice:
    """Personal evidence-based financial mentor for Academy students."""

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

    def system_prompt(self) -> FinanceTutorSystemPrompt:
        """Return governing Finance Tutor Office prompt."""
        return FinanceTutorSystemPrompt(
            "PROMPT-FINANCE-TUTOR-083",
            "1.0.0",
            (
                "You are the Finance Tutor Office of the ARGOS Academy.\n\n"
                "Serve as each student's personal financial mentor by drawing upon the complete validated "
                "institutional intelligence of ARGOS. Guide students through evidence-based financial reasoning "
                "using historical examples, case studies, doctrine, institutional knowledge, and supporting "
                "references. Prefer guided questioning over immediate conclusions when doing so strengthens "
                "understanding, while maintaining complete traceability to supporting evidence."
            ),
        )

    def create_tutoring_session(
        self,
        session_id: str,
        student_context: StudentLearningContext,
        knowledge_references: tuple[TutorKnowledgeReference, ...],
        student_question: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Create deterministic tutoring artifacts."""
        self.configuration_service.validate_startup()
        ordered_references = tuple(sorted(knowledge_references, key=lambda item: item.reference_id))
        mode = _guidance_mode(student_context)
        depth = _depth(student_context.learner_level)
        evidence_ids = tuple(sorted({item for reference in ordered_references for item in reference.evidence_ids}))
        framework = PersonalizedTutoringFramework(
            f"PTF-{document_sequence:06d}",
            student_context.learner_id,
            True,
            True,
            True,
            True,
        )
        guidance = AdaptiveGuidanceArchitecture(
            f"AGA-{document_sequence:06d}",
            student_context.learner_id,
            mode,
            _adaptation_basis(student_context),
            _next_actions(student_context, mode),
        )
        socratic = SocraticReasoningFramework(
            f"SRF-{document_sequence:06d}",
            _socratic_questions(student_question, student_context),
            False,
            True,
        )
        explanation = ExplanationDepthStandard(
            f"EDS-{document_sequence:06d}",
            depth,
            _explanation_layers(depth),
            student_context.learner_level,
        )
        coaching = DecisionCoachingFramework(
            f"DCF-{document_sequence:06d}",
            student_context.learner_id,
            student_question,
            (
                "State the financial claim.",
                "Separate evidence from assumptions.",
                "Identify risks and invalidation conditions.",
                "Compare alternatives before conclusion.",
            ),
            evidence_ids,
            True,
        )
        misconceptions = MisconceptionDetectionRecord(
            f"MDR-{document_sequence:06d}",
            student_context.learner_id,
            tuple(sorted(student_context.misconceptions)),
            tuple(f"Re-examine: {item}" for item in sorted(student_context.misconceptions)),
            1.0 if student_context.misconceptions else 0.0,
        )
        conversation = EducationalConversationModel(
            f"ECM-{document_sequence:06d}",
            student_context.learner_id,
            (
                "Clarify learner question.",
                "Ask guided evidence question.",
                "Connect to validated reference.",
                "Coach decision reasoning.",
                "Assign next reflective step.",
            ),
            tuple(reference.reference_id for reference in ordered_references),
            True,
        )
        traceability_complete = bool(evidence_ids and ordered_references)
        dashboard = TutorAnalyticsDashboard(
            f"TDASH-{document_sequence:06d}",
            student_context.learner_id,
            len(ordered_references),
            len(misconceptions.detected_misconceptions),
            mode,
            depth,
            traceability_complete,
            "healthy" if traceability_complete else "attention",
        )
        return {
            "personalized_tutoring_framework": self._persist_contract(
                "PERSONALIZED_TUTORING_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Personalized Tutoring Framework.",
                {"personalized_tutoring_framework": framework, "finance_tutor_system_prompt": self.system_prompt()},
            ),
            "adaptive_guidance_architecture": self._persist_contract(
                "ADAPTIVE_GUIDANCE_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Adaptive Guidance Architecture.",
                {"adaptive_guidance_architecture": guidance, "student_learning_context": student_context},
            ),
            "socratic_reasoning_framework": self._persist_contract(
                "SOCRATIC_REASONING_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Socratic Reasoning Framework.",
                {"socratic_reasoning_framework": socratic},
            ),
            "explanation_depth_standard": self._persist_contract(
                "EXPLANATION_DEPTH_STANDARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Explanation Depth Standard.",
                {"explanation_depth_standard": explanation},
            ),
            "decision_coaching_framework": self._persist_contract(
                "DECISION_COACHING_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Decision Coaching Framework.",
                {"decision_coaching_framework": coaching, "knowledge_references": ordered_references},
            ),
            "educational_conversation_model": self._persist_contract(
                "EDUCATIONAL_CONVERSATION_MODEL",
                case_file_id,
                trade_cycle_id,
                document_sequence + 5,
                "Educational Conversation Model.",
                {"misconception_detection_framework": misconceptions, "educational_conversation_model": conversation},
            ),
            "tutor_analytics_dashboard": self._persist_contract(
                "TUTOR_ANALYTICS_DASHBOARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 6,
                "Tutor Analytics Dashboard.",
                {"tutor_analytics_dashboard": dashboard},
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


def _guidance_mode(context: StudentLearningContext) -> TutorInteractionMode:
    if context.misconceptions:
        return TutorInteractionMode.MISCONCEPTION_REPAIR
    if context.learner_level in (LearnerLevel.NOVICE, LearnerLevel.DEVELOPING):
        return TutorInteractionMode.SOCRATIC
    if context.learner_level in (LearnerLevel.COMPETENT, LearnerLevel.ADVANCED):
        return TutorInteractionMode.DECISION_COACHING
    return TutorInteractionMode.EXPLANATORY


def _depth(level: LearnerLevel) -> ExplanationDepth:
    return {
        LearnerLevel.NOVICE: ExplanationDepth.FOUNDATIONAL,
        LearnerLevel.DEVELOPING: ExplanationDepth.APPLIED,
        LearnerLevel.COMPETENT: ExplanationDepth.APPLIED,
        LearnerLevel.ADVANCED: ExplanationDepth.ADVANCED,
        LearnerLevel.EXPERT: ExplanationDepth.EXPERT,
    }[level]


def _adaptation_basis(context: StudentLearningContext) -> tuple[str, ...]:
    return (
        f"learner_level={context.learner_level.value}",
        f"demonstrated_competencies={','.join(domain.value for domain in sorted(context.demonstrated_competencies, key=lambda item: item.value))}",
        f"misconceptions={','.join(sorted(context.misconceptions))}",
        f"educational_goals={','.join(context.educational_goals)}",
        f"learning_history={','.join(context.learning_history_ids)}",
    )


def _next_actions(context: StudentLearningContext, mode: TutorInteractionMode) -> tuple[str, ...]:
    if mode == TutorInteractionMode.MISCONCEPTION_REPAIR:
        return tuple(f"Repair misconception: {item}" for item in sorted(context.misconceptions))
    if mode == TutorInteractionMode.SOCRATIC:
        return ("Ask evidence-first question.", "Request risk identification.", "Prompt student justification.")
    if mode == TutorInteractionMode.DECISION_COACHING:
        return ("Evaluate decision frame.", "Compare alternatives.", "Calibrate confidence.")
    return ("Provide source-backed synthesis.", "Ask expert reflection question.")


def _socratic_questions(question: str, context: StudentLearningContext) -> tuple[str, ...]:
    focus = context.educational_goals[0] if context.educational_goals else "financial reasoning"
    return (
        f"What evidence would you need before answering: {question}",
        f"What risk could make your current interpretation of {focus} wrong?",
        "Which alternative explanation remains plausible?",
        "How would you know your confidence should change?",
    )


def _explanation_layers(depth: ExplanationDepth) -> tuple[str, ...]:
    layers = {
        ExplanationDepth.FOUNDATIONAL: ("definition", "simple example", "evidence pointer"),
        ExplanationDepth.APPLIED: ("concept", "historical case", "risk implication", "practice question"),
        ExplanationDepth.ADVANCED: ("argument map", "counterargument", "case comparison", "confidence calibration"),
        ExplanationDepth.EXPERT: ("doctrine lineage", "model limitation", "edge case", "research extension"),
    }
    return layers[depth]


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
        produced_by_staff_id=FINANCE_TUTOR_STAFF_ID,
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
