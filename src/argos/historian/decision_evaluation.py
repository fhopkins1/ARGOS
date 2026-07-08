"""Decision Evaluation Office."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from statistics import mean
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository

from .group import HISTORIAN_GROUP_ID


DECISION_EVALUATION_OFFICE_ID = "HISTORIAN-OFFICE-006"
DECISION_EVALUATION_STAFF_ID = "STF-075"


class DecisionStatus(str, Enum):
    """Decision registry status."""

    REGISTERED = "registered"
    EVALUATED = "evaluated"
    ARCHIVED = "archived"


class DecisionQualityBand(str, Enum):
    """Decision quality band."""

    EXEMPLARY = "exemplary"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    DEFICIENT = "deficient"


@dataclass(frozen=True)
class OrganizationalDecision:
    """Major organizational decision subject to evaluation."""

    decision_id: str
    decision_type: str
    owning_group: str
    rationale_id: str
    evidence_ids: tuple[str, ...]
    alternative_ids: tuple[str, ...]
    governance_gate_ids: tuple[str, ...]
    timestamp_utc: str
    audit_record_id: str


@dataclass(frozen=True)
class DecisionRegistryRecord:
    """Immutable decision registry record."""

    registry_id: str
    decision: OrganizationalDecision
    status: DecisionStatus
    registered_timestamp_utc: str
    evaluation_record_ids: tuple[str, ...]


@dataclass(frozen=True)
class DecisionEvaluationInput:
    """Empirical decision-quality input."""

    input_id: str
    decision_id: str
    reasoning_steps: int
    supported_reasoning_steps: int
    evidence_required: int
    evidence_supplied: int
    alternatives_required: int
    alternatives_considered: int
    governance_gates_required: int
    governance_gates_satisfied: int
    known_contradictions_addressed: int
    known_contradictions_total: int
    pattern_tags: tuple[str, ...]
    audit_record_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReasoningEvaluationDataset:
    """Reasoning quality dataset."""

    dataset_id: str
    decision_id: str
    reasoning_quality_score: float
    supported_steps: int
    total_steps: int
    contradiction_handling_score: float


@dataclass(frozen=True)
class EvidenceSufficiencyAssessment:
    """Evidence sufficiency assessment."""

    assessment_id: str
    decision_id: str
    evidence_sufficiency_score: float
    required_evidence: int
    supplied_evidence: int
    sufficient: bool


@dataclass(frozen=True)
class AlternativeAnalysisAssessment:
    """Alternative-analysis assessment."""

    assessment_id: str
    decision_id: str
    alternative_analysis_score: float
    alternatives_required: int
    alternatives_considered: int
    sufficient: bool


@dataclass(frozen=True)
class DecisionDisciplineMetrics:
    """Decision discipline metrics."""

    metrics_id: str
    decision_id: str
    governance_compliance_score: float
    evidence_discipline_score: float
    alternative_discipline_score: float
    overall_discipline_score: float


@dataclass(frozen=True)
class DecisionQualityEvaluation:
    """Deterministic decision quality evaluation."""

    evaluation_id: str
    decision_id: str
    reasoning_score: float
    evidence_score: float
    alternative_score: float
    discipline_score: float
    decision_quality_score: float
    quality_band: DecisionQualityBand
    profitability_considered: bool
    trace_ids: tuple[str, ...]


@dataclass(frozen=True)
class DecisionPatternRecord:
    """Recurring decision pattern record."""

    pattern_id: str
    pattern_tag: str
    occurrence_count: int
    affected_decision_ids: tuple[str, ...]
    recurring: bool


@dataclass(frozen=True)
class DecisionRecommendation:
    """Evidence-based organizational recommendation."""

    recommendation_id: str
    decision_id: str
    recommendation: str
    evidence_based: bool
    recommended_consumers: tuple[str, ...]
    directly_modifies_behavior: bool


@dataclass(frozen=True)
class DecisionIntegrityAssessment:
    """Decision integrity assessment."""

    integrity_id: str
    decision_id: str
    historical_archive_immutable: bool
    trace_complete: bool
    governance_compliance_preserved: bool


@dataclass(frozen=True)
class DecisionEvaluationStandards:
    """Librarian deliverable for decision evaluation methodology."""

    standards_id: str
    reasoning_methodology: str
    evidence_methodology: str
    governance_methodology: str
    outcome_independence_rule: str


class DecisionEvaluationOffice:
    """Deterministic authority for organizational decision quality."""

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
        self._registry: dict[str, DecisionRegistryRecord] = {}
        self._decision_archive: list[dict[str, object]] = []

    @property
    def decision_registry(self) -> tuple[DecisionRegistryRecord, ...]:
        """Return immutable decision registry."""
        return tuple(self._registry[key] for key in sorted(self._registry))

    @property
    def historical_decision_archive(self) -> tuple[dict[str, object], ...]:
        """Return preserved historical decision archive."""
        return tuple(self._decision_archive)

    def standards(self) -> DecisionEvaluationStandards:
        """Return Decision Evaluation standards for Librarian consumption."""
        return DecisionEvaluationStandards(
            "DES-066",
            "Reasoning quality is supported_reasoning_steps / reasoning_steps, adjusted for contradiction handling.",
            "Evidence sufficiency is evidence_supplied / evidence_required and ignores investment profitability.",
            "Decision discipline measures governance gates, evidence discipline, and alternative discipline.",
            "Decision quality evaluates reasoning before outcomes; profitability shall not be used as an input.",
        )

    def register_decision(
        self,
        decision: OrganizationalDecision,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Register a major organizational decision."""
        self.configuration_service.validate_startup()
        if decision.decision_id in self._registry:
            raise ValueError(f"decision already registered: {decision.decision_id}")
        record = DecisionRegistryRecord(
            f"DRR-{hashlib.sha256(decision.decision_id.encode('utf-8')).hexdigest()[:8].upper()}",
            decision,
            DecisionStatus.REGISTERED,
            utc_timestamp(),
            (),
        )
        self._registry[decision.decision_id] = record
        return self._persist_contract(
            "DECISION_REGISTRY",
            case_file_id,
            trade_cycle_id,
            document_sequence,
            "Decision Registry.",
            {
                "decision_registry_record": record,
                "historical_decision_archive_immutable": True,
            },
        )

    def evaluate_decision(
        self,
        decision_id: str,
        evaluation_input: DecisionEvaluationInput,
        historical_inputs: tuple[DecisionEvaluationInput, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Evaluate organizational decision quality independent of profitability."""
        self.configuration_service.validate_startup()
        if decision_id not in self._registry:
            raise ValueError(f"unknown decision: {decision_id}")
        if evaluation_input.decision_id != decision_id:
            raise ValueError("evaluation input decision_id must match registered decision")
        registry = self._registry[decision_id]
        reasoning = _reasoning_dataset(evaluation_input)
        evidence = _evidence_assessment(evaluation_input)
        alternatives = _alternative_assessment(evaluation_input)
        discipline = _discipline_metrics(evaluation_input, evidence, alternatives)
        quality = _quality_evaluation(evaluation_input, reasoning, evidence, alternatives, discipline)
        patterns = _patterns((evaluation_input, *historical_inputs))
        recommendation = _recommendation(quality, evidence, alternatives, discipline)
        integrity = DecisionIntegrityAssessment(
            f"DIA-{hashlib.sha256(decision_id.encode('utf-8')).hexdigest()[:8].upper()}",
            decision_id,
            True,
            True,
            True,
        )
        updated_registry = DecisionRegistryRecord(
            registry.registry_id,
            registry.decision,
            DecisionStatus.EVALUATED,
            registry.registered_timestamp_utc,
            (*registry.evaluation_record_ids, quality.evaluation_id),
        )
        self._registry[decision_id] = updated_registry
        self._decision_archive.append(
            _json_ready(
                {
                    "decision_id": decision_id,
                    "evaluation_id": quality.evaluation_id,
                    "decision_quality_score": quality.decision_quality_score,
                    "quality_band": quality.quality_band,
                    "pattern_tags": evaluation_input.pattern_tags,
                }
            )
        )
        return {
            "decision_evaluation_report": self._persist_contract(
                "DECISION_EVALUATION_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Decision Evaluation Report.",
                {
                    "office_id": DECISION_EVALUATION_OFFICE_ID,
                    "office_name": "Decision Evaluation Office",
                    "decision_registry_record": updated_registry,
                    "reasoning_evaluation_dataset": reasoning,
                    "evidence_sufficiency_assessment": evidence,
                    "alternative_analysis_assessment": alternatives,
                    "decision_quality_evaluation": quality,
                    "decision_integrity_assessment": integrity,
                    "decision_evaluation_standards": self.standards(),
                },
            ),
            "decision_pattern_report": self._persist_contract(
                "DECISION_PATTERN_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Decision Pattern Report.",
                {"decision_pattern_register": patterns},
            ),
            "organizational_decision_summary": self._persist_contract(
                "ORGANIZATIONAL_DECISION_SUMMARY",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Organizational Decision Summary.",
                {
                    "decision_registry": self.decision_registry,
                    "organizational_recommendation_register": (recommendation,),
                    "historical_decision_archive_complete": True,
                },
            ),
            "decision_discipline_report": self._persist_contract(
                "DECISION_DISCIPLINE_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Decision Discipline Report.",
                {
                    "decision_discipline_metrics": discipline,
                    "governance_compliance_archive": integrity,
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


def _reasoning_dataset(evaluation_input: DecisionEvaluationInput) -> ReasoningEvaluationDataset:
    reasoning_score = _ratio(evaluation_input.supported_reasoning_steps, evaluation_input.reasoning_steps)
    contradiction_score = _ratio(evaluation_input.known_contradictions_addressed, evaluation_input.known_contradictions_total)
    return ReasoningEvaluationDataset(
        f"RED-{hashlib.sha256(evaluation_input.input_id.encode('utf-8')).hexdigest()[:8].upper()}",
        evaluation_input.decision_id,
        round((reasoning_score * 0.75) + (contradiction_score * 0.25), 6),
        evaluation_input.supported_reasoning_steps,
        evaluation_input.reasoning_steps,
        round(contradiction_score, 6),
    )


def _evidence_assessment(evaluation_input: DecisionEvaluationInput) -> EvidenceSufficiencyAssessment:
    score = _ratio(evaluation_input.evidence_supplied, evaluation_input.evidence_required)
    return EvidenceSufficiencyAssessment(
        f"ESA-{hashlib.sha256(f'{evaluation_input.input_id}:evidence'.encode('utf-8')).hexdigest()[:8].upper()}",
        evaluation_input.decision_id,
        round(min(score, 1.0), 6),
        evaluation_input.evidence_required,
        evaluation_input.evidence_supplied,
        score >= 1.0,
    )


def _alternative_assessment(evaluation_input: DecisionEvaluationInput) -> AlternativeAnalysisAssessment:
    score = _ratio(evaluation_input.alternatives_considered, evaluation_input.alternatives_required)
    return AlternativeAnalysisAssessment(
        f"AAA-{hashlib.sha256(f'{evaluation_input.input_id}:alternatives'.encode('utf-8')).hexdigest()[:8].upper()}",
        evaluation_input.decision_id,
        round(min(score, 1.0), 6),
        evaluation_input.alternatives_required,
        evaluation_input.alternatives_considered,
        score >= 1.0,
    )


def _discipline_metrics(
    evaluation_input: DecisionEvaluationInput,
    evidence: EvidenceSufficiencyAssessment,
    alternatives: AlternativeAnalysisAssessment,
) -> DecisionDisciplineMetrics:
    governance = min(_ratio(evaluation_input.governance_gates_satisfied, evaluation_input.governance_gates_required), 1.0)
    overall = mean((governance, evidence.evidence_sufficiency_score, alternatives.alternative_analysis_score))
    return DecisionDisciplineMetrics(
        f"DDM-{hashlib.sha256(f'{evaluation_input.input_id}:discipline'.encode('utf-8')).hexdigest()[:8].upper()}",
        evaluation_input.decision_id,
        round(governance, 6),
        evidence.evidence_sufficiency_score,
        alternatives.alternative_analysis_score,
        round(overall, 6),
    )


def _quality_evaluation(
    evaluation_input: DecisionEvaluationInput,
    reasoning: ReasoningEvaluationDataset,
    evidence: EvidenceSufficiencyAssessment,
    alternatives: AlternativeAnalysisAssessment,
    discipline: DecisionDisciplineMetrics,
) -> DecisionQualityEvaluation:
    score = round(mean((reasoning.reasoning_quality_score, evidence.evidence_sufficiency_score, alternatives.alternative_analysis_score, discipline.overall_discipline_score)), 6)
    if score >= 0.9:
        band = DecisionQualityBand.EXEMPLARY
    elif score >= 0.75:
        band = DecisionQualityBand.ACCEPTABLE
    elif score >= 0.55:
        band = DecisionQualityBand.NEEDS_IMPROVEMENT
    else:
        band = DecisionQualityBand.DEFICIENT
    return DecisionQualityEvaluation(
        f"DQE-{hashlib.sha256(evaluation_input.input_id.encode('utf-8')).hexdigest()[:8].upper()}",
        evaluation_input.decision_id,
        reasoning.reasoning_quality_score,
        evidence.evidence_sufficiency_score,
        alternatives.alternative_analysis_score,
        discipline.overall_discipline_score,
        score,
        band,
        False,
        evaluation_input.audit_record_ids,
    )


def _patterns(inputs: tuple[DecisionEvaluationInput, ...]) -> tuple[DecisionPatternRecord, ...]:
    tags: dict[str, list[str]] = {}
    for item in inputs:
        for tag in item.pattern_tags:
            tags.setdefault(tag, []).append(item.decision_id)
    return tuple(
        DecisionPatternRecord(
            f"DPR-{hashlib.sha256(tag.encode('utf-8')).hexdigest()[:8].upper()}",
            tag,
            len(decision_ids),
            tuple(sorted(decision_ids)),
            len(decision_ids) >= 2,
        )
        for tag, decision_ids in sorted(tags.items())
    )


def _recommendation(
    quality: DecisionQualityEvaluation,
    evidence: EvidenceSufficiencyAssessment,
    alternatives: AlternativeAnalysisAssessment,
    discipline: DecisionDisciplineMetrics,
) -> DecisionRecommendation:
    if quality.quality_band in {DecisionQualityBand.EXEMPLARY, DecisionQualityBand.ACCEPTABLE}:
        text = "Preserve current decision process and continue monitoring."
    elif not evidence.sufficient:
        text = "Require stronger evidence sufficiency before comparable future decisions."
    elif not alternatives.sufficient:
        text = "Require explicit alternative analysis before comparable future decisions."
    elif discipline.governance_compliance_score < 1.0:
        text = "Strengthen governance gate compliance before comparable future decisions."
    else:
        text = "Review decision reasoning support and contradiction handling."
    return DecisionRecommendation(
        f"DREC-{hashlib.sha256(f'{quality.decision_id}:{quality.decision_quality_score}'.encode('utf-8')).hexdigest()[:8].upper()}",
        quality.decision_id,
        text,
        True,
        ("Librarian Group", "Executive Group", "Future Engineering Orders"),
        False,
    )


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return numerator / denominator


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
        produced_by_staff_id=DECISION_EVALUATION_STAFF_ID,
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
