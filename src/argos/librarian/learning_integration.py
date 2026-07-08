"""Learning Integration Office."""

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

from .group import LIBRARIAN_GROUP_ID


LEARNING_INTEGRATION_OFFICE_ID = "LIBRARIAN-OFFICE-005"
LEARNING_INTEGRATION_STAFF_ID = "STF-085"


class LearningSourceType(str, Enum):
    """Enterprise learning source taxonomy."""

    HISTORIAN_VALIDATION = "historian_validation"
    PERFORMANCE_MEASUREMENT = "performance_measurement"
    HYPOTHESIS_VALIDATION = "hypothesis_validation"
    MODEL_CALIBRATION = "model_calibration"
    DECISION_EVALUATION = "decision_evaluation"
    EVIDENCE_EVALUATION = "evidence_evaluation"
    READINESS_REVIEW = "readiness_review"
    INCIDENT_REVIEW = "incident_review"


class PropagationTargetType(str, Enum):
    """Knowledge propagation target taxonomy."""

    DOCTRINE = "doctrine"
    SPECIFICATION = "specification"
    WORKFLOW = "workflow"
    PROMPT = "prompt"
    SOFTWARE_IMPROVEMENT = "software_improvement"
    ACADEMY_CURRICULUM = "academy_curriculum"
    OPERATIONAL_METRIC = "operational_metric"
    GOVERNANCE_STANDARD = "governance_standard"


class ImprovementStatus(str, Enum):
    """Continuous improvement lifecycle status."""

    IDENTIFIED = "identified"
    PRIORITIZED = "prioritized"
    PROPAGATION_READY = "propagation_ready"
    VALIDATION_REQUIRED = "validation_required"
    VALIDATED_GAIN = "validated_gain"
    STAGNANT = "stagnant"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ValidatedLearningSource:
    """Validated organizational learning source."""

    learning_id: str
    source_type: LearningSourceType
    title: str
    evidence_ids: tuple[str, ...]
    provenance_ids: tuple[str, ...]
    affected_group_ids: tuple[str, ...]
    repeated_mistake_ids: tuple[str, ...]
    expected_performance_delta: float
    confidence: float


@dataclass(frozen=True)
class EnterpriseLearningPipeline:
    """Enterprise learning pipeline artifact."""

    pipeline_id: str
    source_count: int
    validated_source_count: int
    propagation_target_count: int
    governance_required: bool
    pipeline_established: bool


@dataclass(frozen=True)
class KnowledgePropagationRecord:
    """Knowledge propagation framework record."""

    propagation_id: str
    learning_id: str
    target_type: PropagationTargetType
    target_reference_id: str
    governance_gate: str
    propagated: bool


@dataclass(frozen=True)
class OrganizationalImprovementRecord:
    """Organizational improvement framework record."""

    improvement_id: str
    learning_id: str
    priority_score: float
    status: ImprovementStatus
    deterministic_reason: str


@dataclass(frozen=True)
class ContinuousImprovementRecord:
    """Continuous improvement engine record."""

    engine_record_id: str
    learning_id: str
    repeated_mistake_eliminated: bool
    stagnation_detected: bool
    measurable_enhancement_ids: tuple[str, ...]
    next_review_cycle: str


@dataclass(frozen=True)
class LearningPrioritizationStandard:
    """Learning prioritization standard."""

    standard_id: str
    methodology: str
    ranked_learning_ids: tuple[str, ...]
    score_by_learning_id: dict[str, float]


@dataclass(frozen=True)
class IntegrationValidationRecord:
    """Integration validation process result."""

    validation_id: str
    learning_id: str
    baseline_metric: float
    observed_metric: float
    observable_gain: float
    performance_gain_verified: bool
    traceability_complete: bool


@dataclass(frozen=True)
class FeedbackLoopRecord:
    """Feedback loop architecture record."""

    feedback_loop_id: str
    learning_id: str
    historian_feedback_required: bool
    librarian_feedback_required: bool
    academy_feedback_required: bool
    next_feedback_artifact_ids: tuple[str, ...]


@dataclass(frozen=True)
class EnterpriseMaturityModel:
    """Enterprise maturity model."""

    maturity_model_id: str
    maturity_score: float
    maturity_level: str
    stagnation_count: int
    repeated_mistake_count: int
    validated_gain_count: int


@dataclass(frozen=True)
class OrganizationalLearningDashboard:
    """Organizational learning dashboard metrics."""

    dashboard_id: str
    learning_count: int
    propagation_count: int
    prioritized_count: int
    validated_gain_count: int
    stagnation_count: int
    maturity_score: float
    learning_health: str


@dataclass(frozen=True)
class LearningIntegrationSystemPrompt:
    """Learning Integration Office prompt."""

    prompt_id: str
    version: str
    prompt_text: str


class LearningIntegrationOffice:
    """Bridge validated organizational learning into governed enterprise improvement."""

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
        self._learning_sources: dict[str, ValidatedLearningSource] = {}
        self._propagation_records: list[KnowledgePropagationRecord] = []
        self._validation_records: list[IntegrationValidationRecord] = []

    @property
    def learning_sources(self) -> tuple[ValidatedLearningSource, ...]:
        """Return deterministic learning sources."""
        return tuple(self._learning_sources[learning_id] for learning_id in sorted(self._learning_sources))

    def system_prompt(self) -> LearningIntegrationSystemPrompt:
        """Return governing Learning Integration prompt."""
        return LearningIntegrationSystemPrompt(
            "PROMPT-LIO-075",
            "1.0.0",
            (
                "You are the Learning Integration Office of ARGOS.\n\n"
                "Continuously identify validated organizational learning and ensure it propagates throughout the "
                "enterprise. Transform evidence into doctrine, specifications, workflows, prompts, software "
                "improvements, Academy curriculum, and measurable operational enhancements. Verify that every "
                "implemented improvement produces observable performance gains while maintaining complete "
                "traceability, historical lineage, and deterministic governance."
            ),
        )

    def integrate_learning(
        self,
        sources: tuple[ValidatedLearningSource, ...],
        propagation_targets: dict[str, tuple[tuple[PropagationTargetType, str], ...]],
        baseline_metrics: dict[str, float],
        observed_metrics: dict[str, float],
        next_review_cycle: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Integrate validated learning into deterministic enterprise improvement artifacts."""
        self.configuration_service.validate_startup()
        for source in sources:
            self._learning_sources[source.learning_id] = source

        validated_sources = tuple(source for source in self.learning_sources if source.evidence_ids and source.provenance_ids)
        prioritization = _prioritization(validated_sources)
        propagation = tuple(
            record
            for source in validated_sources
            for record in _propagation_records(source, propagation_targets.get(source.learning_id, ()), document_sequence)
        )
        self._propagation_records.extend(propagation)
        improvements = tuple(_improvement_record(source, prioritization.score_by_learning_id.get(source.learning_id, 0.0), document_sequence) for source in validated_sources)
        validations = tuple(_validation_record(source, baseline_metrics, observed_metrics, document_sequence) for source in validated_sources)
        self._validation_records.extend(validations)
        continuous = tuple(_continuous_record(source, validation, next_review_cycle, document_sequence) for source, validation in zip(validated_sources, validations))
        feedback = tuple(_feedback_record(source, document_sequence) for source in validated_sources)
        maturity = _maturity(validated_sources, validations, continuous, document_sequence)
        pipeline = EnterpriseLearningPipeline(
            f"ELP-{document_sequence:06d}",
            len(self.learning_sources),
            len(validated_sources),
            len(propagation),
            bool(propagation),
            True,
        )
        dashboard = OrganizationalLearningDashboard(
            f"OLD-{document_sequence:06d}",
            len(self.learning_sources),
            len(self._propagation_records),
            len(improvements),
            sum(1 for validation in validations if validation.performance_gain_verified),
            maturity.stagnation_count,
            maturity.maturity_score,
            "healthy" if maturity.maturity_score >= 0.6 and not maturity.stagnation_count else "attention",
        )
        return {
            "enterprise_learning_pipeline": self._persist_contract(
                "ENTERPRISE_LEARNING_PIPELINE",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Enterprise Learning Pipeline.",
                {"enterprise_learning_pipeline": pipeline, "learning_sources": validated_sources, "system_prompt": self.system_prompt()},
            ),
            "knowledge_propagation_framework": self._persist_contract(
                "KNOWLEDGE_PROPAGATION_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Knowledge Propagation Framework.",
                {"knowledge_propagation_records": propagation, "propagation_targets": propagation_targets},
            ),
            "organizational_improvement_framework": self._persist_contract(
                "ORGANIZATIONAL_IMPROVEMENT_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Organizational Improvement Framework.",
                {"organizational_improvement_records": improvements, "learning_prioritization_standard": prioritization},
            ),
            "continuous_improvement_engine": self._persist_contract(
                "CONTINUOUS_IMPROVEMENT_ENGINE",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Continuous Improvement Engine.",
                {"continuous_improvement_records": continuous, "integration_validation_records": validations},
            ),
            "feedback_loop_architecture": self._persist_contract(
                "FEEDBACK_LOOP_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Feedback Loop Architecture.",
                {"feedback_loop_records": feedback, "enterprise_maturity_model": maturity},
            ),
            "organizational_learning_dashboard": self._persist_contract(
                "ORGANIZATIONAL_LEARNING_DASHBOARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 5,
                "Organizational Learning Dashboard.",
                {"organizational_learning_dashboard": dashboard, "enterprise_learning_metrics_specified": True},
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


def _prioritization(sources: tuple[ValidatedLearningSource, ...]) -> LearningPrioritizationStandard:
    scores = {
        source.learning_id: round((source.expected_performance_delta * 0.5) + (source.confidence * 0.3) + (len(source.repeated_mistake_ids) * 0.2), 6)
        for source in sources
    }
    ranked = tuple(sorted(scores, key=lambda learning_id: (-scores[learning_id], learning_id)))
    return LearningPrioritizationStandard(
        "LPS-DETERMINISTIC-001",
        "score = expected_performance_delta*0.5 + confidence*0.3 + repeated_mistake_count*0.2",
        ranked,
        scores,
    )


def _propagation_records(
    source: ValidatedLearningSource,
    targets: tuple[tuple[PropagationTargetType, str], ...],
    document_sequence: int,
) -> tuple[KnowledgePropagationRecord, ...]:
    records = []
    for index, (target_type, target_reference_id) in enumerate(targets, start=1):
        records.append(
            KnowledgePropagationRecord(
                f"KPR-{document_sequence:06d}-{index:03d}",
                source.learning_id,
                target_type,
                target_reference_id,
                _governance_gate(target_type),
                bool(source.evidence_ids and source.provenance_ids),
            )
        )
    return tuple(records)


def _governance_gate(target_type: PropagationTargetType) -> str:
    gates = {
        PropagationTargetType.DOCTRINE: "Doctrine Management Office approval required.",
        PropagationTargetType.SPECIFICATION: "Specification Repository Office approval required.",
        PropagationTargetType.WORKFLOW: "Executive and owning office validation required.",
        PropagationTargetType.PROMPT: "Prompt Repository versioning required.",
        PropagationTargetType.SOFTWARE_IMPROVEMENT: "Engineering Order and tests required.",
        PropagationTargetType.ACADEMY_CURRICULUM: "Academy curriculum review required.",
        PropagationTargetType.OPERATIONAL_METRIC: "Historian measurement validation required.",
        PropagationTargetType.GOVERNANCE_STANDARD: "Librarian governance approval required.",
    }
    return gates[target_type]


def _improvement_record(source: ValidatedLearningSource, priority_score: float, document_sequence: int) -> OrganizationalImprovementRecord:
    status = ImprovementStatus.PROPAGATION_READY if source.evidence_ids and source.provenance_ids and priority_score > 0 else ImprovementStatus.IDENTIFIED
    return OrganizationalImprovementRecord(
        f"OIR-{document_sequence:06d}-{source.learning_id}",
        source.learning_id,
        priority_score,
        status,
        "Priority calculated from expected performance delta, confidence, and repeated mistake pressure.",
    )


def _validation_record(
    source: ValidatedLearningSource,
    baseline_metrics: dict[str, float],
    observed_metrics: dict[str, float],
    document_sequence: int,
) -> IntegrationValidationRecord:
    baseline = baseline_metrics.get(source.learning_id, 0.0)
    observed = observed_metrics.get(source.learning_id, baseline)
    gain = round(observed - baseline, 6)
    return IntegrationValidationRecord(
        f"IVR-{document_sequence:06d}-{source.learning_id}",
        source.learning_id,
        baseline,
        observed,
        gain,
        gain > 0,
        bool(source.evidence_ids and source.provenance_ids),
    )


def _continuous_record(
    source: ValidatedLearningSource,
    validation: IntegrationValidationRecord,
    next_review_cycle: str,
    document_sequence: int,
) -> ContinuousImprovementRecord:
    return ContinuousImprovementRecord(
        f"CIR-{document_sequence:06d}-{source.learning_id}",
        source.learning_id,
        bool(source.repeated_mistake_ids and validation.performance_gain_verified),
        not validation.performance_gain_verified,
        (validation.validation_id,) if validation.performance_gain_verified else (),
        next_review_cycle,
    )


def _feedback_record(source: ValidatedLearningSource, document_sequence: int) -> FeedbackLoopRecord:
    return FeedbackLoopRecord(
        f"FLR-{document_sequence:06d}-{source.learning_id}",
        source.learning_id,
        True,
        True,
        True,
        (f"HIST-FEEDBACK-{source.learning_id}", f"LIB-FEEDBACK-{source.learning_id}", f"ACADEMY-FEEDBACK-{source.learning_id}"),
    )


def _maturity(
    sources: tuple[ValidatedLearningSource, ...],
    validations: tuple[IntegrationValidationRecord, ...],
    continuous: tuple[ContinuousImprovementRecord, ...],
    document_sequence: int,
) -> EnterpriseMaturityModel:
    if not sources:
        score = 0.0
    else:
        validated_gain_count = sum(1 for validation in validations if validation.performance_gain_verified)
        traceable_count = sum(1 for validation in validations if validation.traceability_complete)
        score = round(((validated_gain_count + traceable_count) / (len(sources) * 2)), 6)
    stagnation_count = sum(1 for record in continuous if record.stagnation_detected)
    repeated_mistake_count = sum(len(source.repeated_mistake_ids) for source in sources)
    level = "optimizing" if score >= 0.8 else "managed" if score >= 0.6 else "developing" if score > 0 else "initial"
    return EnterpriseMaturityModel(
        f"EMM-{document_sequence:06d}",
        score,
        level,
        stagnation_count,
        repeated_mistake_count,
        sum(1 for validation in validations if validation.performance_gain_verified),
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
        produced_by_staff_id=LEARNING_INTEGRATION_STAFF_ID,
        produced_by_group_id=LIBRARIAN_GROUP_ID,
        intended_consumer_group_id=LIBRARIAN_GROUP_ID,
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
