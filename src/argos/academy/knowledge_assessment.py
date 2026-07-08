"""Knowledge Assessment Office."""

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


KNOWLEDGE_ASSESSMENT_OFFICE_ID = "ACADEMY-OFFICE-003"
KNOWLEDGE_ASSESSMENT_STAFF_ID = "STF-090"


class AssessmentMeasure(str, Enum):
    """Assessment measurement dimension."""

    EVIDENCE_EVALUATION = "evidence_evaluation"
    DECISION_QUALITY = "decision_quality"
    RISK_RECOGNITION = "risk_recognition"
    CRITICAL_THINKING = "critical_thinking"
    INSTITUTIONAL_KNOWLEDGE_APPLICATION = "institutional_knowledge_application"


class AssessmentItemDifficulty(str, Enum):
    """Assessment item difficulty."""

    FOUNDATION = "foundation"
    APPLIED = "applied"
    ADVANCED = "advanced"
    SYNTHESIS = "synthesis"


@dataclass(frozen=True)
class CompetencyAssessmentFramework:
    """Competency assessment framework."""

    framework_id: str
    measured_dimensions: tuple[AssessmentMeasure, ...]
    memorization_primary: bool
    decision_based: bool
    deterministic_principles: tuple[str, ...]


@dataclass(frozen=True)
class AssessmentItem:
    """Decision-based assessment item."""

    item_id: str
    competency_domain: CompetencyDomain
    difficulty: AssessmentItemDifficulty
    scenario_id: str
    required_evidence_ids: tuple[str, ...]
    measured_dimensions: tuple[AssessmentMeasure, ...]


@dataclass(frozen=True)
class AssessmentResponse:
    """Student assessment response scores."""

    response_id: str
    item_id: str
    competency_domain: CompetencyDomain
    evidence_evaluation_score: float
    decision_quality_score: float
    risk_recognition_score: float
    critical_thinking_score: float
    institutional_knowledge_score: float
    cited_evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class CompetencyScore:
    """Per-domain competency score."""

    competency_domain: CompetencyDomain
    score: float
    learner_level: LearnerLevel
    knowledge_gap: bool


@dataclass(frozen=True)
class StudentCompetencyProfile:
    """Student competency profile standard."""

    profile_id: str
    learner_id: str
    assessment_id: str
    competency_scores: tuple[CompetencyScore, ...]
    knowledge_gap_domains: tuple[CompetencyDomain, ...]
    demonstrated_competencies: tuple[CompetencyDomain, ...]
    learning_path_guidance: tuple[str, ...]


@dataclass(frozen=True)
class AdaptiveAssessmentArchitecture:
    """Adaptive testing architecture."""

    architecture_id: str
    assessment_id: str
    selected_item_ids: tuple[str, ...]
    next_item_ids: tuple[str, ...]
    adaptation_basis: tuple[str, ...]
    deterministic: bool


@dataclass(frozen=True)
class DecisionBasedEvaluationFramework:
    """Decision-based evaluation framework."""

    framework_id: str
    scenario_item_ids: tuple[str, ...]
    measured_dimensions: tuple[AssessmentMeasure, ...]
    evaluates_reasoning_not_memorization: bool


@dataclass(frozen=True)
class EducationalFeedbackRecord:
    """Actionable educational feedback."""

    feedback_id: str
    learner_id: str
    assessment_id: str
    strengths: tuple[CompetencyDomain, ...]
    knowledge_gaps: tuple[CompetencyDomain, ...]
    recommended_curriculum_actions: tuple[str, ...]
    actionable: bool


@dataclass(frozen=True)
class LongitudinalLearningAnalytics:
    """Longitudinal measurement process."""

    analytics_id: str
    learner_id: str
    assessment_id: str
    prior_assessment_ids: tuple[str, ...]
    current_average_score: float
    learning_velocity: float
    competency_growth: float
    longitudinal_process_documented: bool


@dataclass(frozen=True)
class AssessmentValidationRecord:
    """Assessment validation process."""

    validation_id: str
    assessment_id: str
    traceability_complete: bool
    deterministic_scoring: bool
    validation_errors: tuple[str, ...]
    valid: bool


@dataclass(frozen=True)
class AssessmentDashboard:
    """Knowledge assessment dashboard."""

    dashboard_id: str
    learner_id: str
    assessed_competency_count: int
    knowledge_gap_count: int
    average_score: float
    learning_velocity: float
    validation_ready: bool
    assessment_health: str


@dataclass(frozen=True)
class KnowledgeAssessmentPrompt:
    """Knowledge Assessment Office prompt."""

    prompt_id: str
    version: str
    prompt_text: str


class KnowledgeAssessmentOffice:
    """Empirical measurement engine for Academy learning."""

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

    def system_prompt(self) -> KnowledgeAssessmentPrompt:
        """Return governing Knowledge Assessment Office prompt."""
        return KnowledgeAssessmentPrompt(
            "PROMPT-KNOWLEDGE-ASSESSMENT-081",
            "1.0.0",
            (
                "You are the Knowledge Assessment Office of the ARGOS Academy.\n\n"
                "Evaluate each student's financial reasoning, investment judgment, competency development, and "
                "application of validated institutional knowledge. Design adaptive assessments that measure evidence "
                "evaluation, decision quality, risk recognition, and critical thinking rather than memorization. "
                "Maintain evolving competency profiles, provide actionable educational feedback, identify knowledge "
                "gaps, and guide personalized learning paths."
            ),
        )

    def evaluate_assessment(
        self,
        assessment_id: str,
        learner_id: str,
        assessment_items: tuple[AssessmentItem, ...],
        responses: tuple[AssessmentResponse, ...],
        prior_assessment_scores: tuple[float, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Evaluate student knowledge deterministically."""
        self.configuration_service.validate_startup()
        ordered_items = tuple(sorted(assessment_items, key=lambda item: item.item_id))
        ordered_responses = tuple(sorted(responses, key=lambda response: response.response_id))
        framework = CompetencyAssessmentFramework(
            f"CAF-{document_sequence:06d}",
            tuple(AssessmentMeasure),
            False,
            True,
            (
                "Score reasoning evidence before conclusions.",
                "Measure decision quality, risk recognition, and critical thinking.",
                "Require evidence traceability for assessment validity.",
                "Adapt future assessment items from measured competency gaps.",
            ),
        )
        profile = _student_profile(learner_id, assessment_id, ordered_responses, ordered_items, document_sequence)
        adaptive = _adaptive_architecture(assessment_id, ordered_items, profile, document_sequence)
        decision_framework = DecisionBasedEvaluationFramework(
            f"DBEF-{document_sequence:06d}",
            tuple(item.item_id for item in ordered_items),
            tuple(AssessmentMeasure),
            True,
        )
        feedback = _feedback(learner_id, assessment_id, profile, document_sequence)
        analytics = _longitudinal(learner_id, assessment_id, profile, prior_assessment_scores, document_sequence)
        validation = _validation(assessment_id, ordered_items, ordered_responses, document_sequence)
        dashboard = AssessmentDashboard(
            f"ADASH-{document_sequence:06d}",
            learner_id,
            len(profile.competency_scores),
            len(profile.knowledge_gap_domains),
            _average_score(profile.competency_scores),
            analytics.learning_velocity,
            validation.valid,
            "healthy" if validation.valid and analytics.current_average_score >= 0.70 else "attention",
        )
        return {
            "competency_assessment_framework": self._persist_contract(
                "COMPETENCY_ASSESSMENT_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Competency Assessment Framework.",
                {"competency_assessment_framework": framework, "knowledge_assessment_prompt": self.system_prompt()},
            ),
            "adaptive_assessment_architecture": self._persist_contract(
                "ADAPTIVE_ASSESSMENT_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Adaptive Assessment Architecture.",
                {"adaptive_assessment_architecture": adaptive},
            ),
            "student_competency_profile_standard": self._persist_contract(
                "STUDENT_COMPETENCY_PROFILE_STANDARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Student Competency Profile Standard.",
                {"student_competency_profile": profile},
            ),
            "decision_based_evaluation_framework": self._persist_contract(
                "DECISION_BASED_EVALUATION_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Decision-Based Evaluation Framework.",
                {"decision_based_evaluation_framework": decision_framework, "assessment_items": ordered_items},
            ),
            "educational_feedback_framework": self._persist_contract(
                "EDUCATIONAL_FEEDBACK_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Educational Feedback Framework.",
                {"educational_feedback_record": feedback},
            ),
            "longitudinal_learning_analytics": self._persist_contract(
                "LONGITUDINAL_LEARNING_ANALYTICS",
                case_file_id,
                trade_cycle_id,
                document_sequence + 5,
                "Longitudinal Learning Analytics.",
                {"longitudinal_learning_analytics": analytics},
            ),
            "assessment_dashboard": self._persist_contract(
                "ASSESSMENT_DASHBOARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 6,
                "Assessment Dashboard.",
                {"assessment_dashboard": dashboard, "assessment_validation_record": validation},
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


def _student_profile(
    learner_id: str,
    assessment_id: str,
    responses: tuple[AssessmentResponse, ...],
    assessment_items: tuple[AssessmentItem, ...],
    document_sequence: int,
) -> StudentCompetencyProfile:
    item_by_id = {item.item_id: item for item in assessment_items}
    response_groups: dict[CompetencyDomain, list[float]] = {}
    for response in responses:
        item = item_by_id.get(response.item_id)
        coverage = _evidence_coverage(item.required_evidence_ids if item else (), response.cited_evidence_ids)
        score = round(_response_score(response) * (0.8 + (0.2 * coverage)), 4)
        response_groups.setdefault(response.competency_domain, []).append(score)
    competency_scores = []
    for domain in sorted(response_groups, key=lambda item: item.value):
        score = round(sum(response_groups[domain]) / len(response_groups[domain]), 4)
        competency_scores.append(CompetencyScore(domain, score, _level_from_score(score), score < 0.70))
    gaps = tuple(score.competency_domain for score in competency_scores if score.knowledge_gap)
    demonstrated = tuple(score.competency_domain for score in competency_scores if score.score >= 0.80)
    return StudentCompetencyProfile(
        f"SCP-{document_sequence:06d}",
        learner_id,
        assessment_id,
        tuple(competency_scores),
        gaps,
        demonstrated,
        tuple(f"Prioritize {domain.value.replace('_', ' ')}" for domain in gaps),
    )


def _adaptive_architecture(
    assessment_id: str,
    assessment_items: tuple[AssessmentItem, ...],
    profile: StudentCompetencyProfile,
    document_sequence: int,
) -> AdaptiveAssessmentArchitecture:
    gap_domains = set(profile.knowledge_gap_domains)
    next_items = tuple(item.item_id for item in assessment_items if item.competency_domain in gap_domains)
    if not next_items:
        next_items = tuple(item.item_id for item in assessment_items if item.difficulty in (AssessmentItemDifficulty.ADVANCED, AssessmentItemDifficulty.SYNTHESIS))
    return AdaptiveAssessmentArchitecture(
        f"AAA-{document_sequence:06d}",
        assessment_id,
        tuple(item.item_id for item in assessment_items),
        tuple(sorted(next_items)),
        tuple(f"knowledge_gap={domain.value}" for domain in sorted(gap_domains, key=lambda item: item.value)) or ("advance_difficulty",),
        True,
    )


def _feedback(
    learner_id: str,
    assessment_id: str,
    profile: StudentCompetencyProfile,
    document_sequence: int,
) -> EducationalFeedbackRecord:
    strengths = tuple(score.competency_domain for score in profile.competency_scores if score.score >= 0.80)
    gaps = profile.knowledge_gap_domains
    return EducationalFeedbackRecord(
        f"EFR-{document_sequence:06d}",
        learner_id,
        assessment_id,
        strengths,
        gaps,
        tuple(f"Assign reinforced curriculum module for {domain.value.replace('_', ' ')}" for domain in gaps),
        True,
    )


def _longitudinal(
    learner_id: str,
    assessment_id: str,
    profile: StudentCompetencyProfile,
    prior_assessment_scores: tuple[float, ...],
    document_sequence: int,
) -> LongitudinalLearningAnalytics:
    current = _average_score(profile.competency_scores)
    prior_average = round(sum(prior_assessment_scores) / len(prior_assessment_scores), 4) if prior_assessment_scores else current
    growth = round(current - prior_average, 4)
    velocity = round(growth / max(len(prior_assessment_scores), 1), 4)
    return LongitudinalLearningAnalytics(
        f"LLA-{document_sequence:06d}",
        learner_id,
        assessment_id,
        tuple(f"ASSESS-PRIOR-{index:03d}" for index, _ in enumerate(prior_assessment_scores, start=1)),
        current,
        velocity,
        growth,
        True,
    )


def _validation(
    assessment_id: str,
    assessment_items: tuple[AssessmentItem, ...],
    responses: tuple[AssessmentResponse, ...],
    document_sequence: int,
) -> AssessmentValidationRecord:
    item_ids = {item.item_id for item in assessment_items}
    response_item_ids = {response.item_id for response in responses}
    errors = []
    if not assessment_items:
        errors.append("missing_assessment_items")
    if not responses:
        errors.append("missing_assessment_responses")
    if response_item_ids - item_ids:
        errors.append("response_for_unknown_item")
    if any(not item.required_evidence_ids for item in assessment_items):
        errors.append("item_missing_required_evidence")
    return AssessmentValidationRecord(
        f"AVR-{document_sequence:06d}",
        assessment_id,
        not errors,
        True,
        tuple(sorted(errors)),
        not errors,
    )


def _response_score(response: AssessmentResponse) -> float:
    return round(
        (
            response.evidence_evaluation_score
            + response.decision_quality_score
            + response.risk_recognition_score
            + response.critical_thinking_score
            + response.institutional_knowledge_score
        )
        / 5,
        4,
    )


def _evidence_coverage(required: tuple[str, ...], cited: tuple[str, ...]) -> float:
    if not required:
        return 0.0
    return round(len(set(required) & set(cited)) / len(set(required)), 4)


def _average_score(scores: tuple[CompetencyScore, ...]) -> float:
    if not scores:
        return 0.0
    return round(sum(score.score for score in scores) / len(scores), 4)


def _level_from_score(score: float) -> LearnerLevel:
    if score >= 0.90:
        return LearnerLevel.EXPERT
    if score >= 0.80:
        return LearnerLevel.ADVANCED
    if score >= 0.70:
        return LearnerLevel.COMPETENT
    if score >= 0.55:
        return LearnerLevel.DEVELOPING
    return LearnerLevel.NOVICE


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
        produced_by_staff_id=KNOWLEDGE_ASSESSMENT_STAFF_ID,
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
