"""Historian Group scientific evaluation framework."""

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


HISTORIAN_GROUP_ID = "DEP-007"
HISTORIAN_CHIEF_OFFICE_ID = "HISTORIAN-OFFICE-001"
HISTORIAN_CHIEF_STAFF_ID = "STF-070"


class ValidationStatus(str, Enum):
    """Historical validation status."""

    PENDING = "pending"
    VALIDATED = "validated"
    INCONCLUSIVE = "inconclusive"
    REJECTED = "rejected"


@dataclass(frozen=True)
class HistorianOfficeTemplate:
    """Historian office template."""

    office_id: str
    name: str
    mission: str


@dataclass(frozen=True)
class HistorianGroupArchitecture:
    """Historian Group organizational architecture."""

    architecture_id: str
    offices: tuple[str, ...]
    upstream_groups: tuple[str, ...]
    downstream_groups: tuple[str, ...]


@dataclass(frozen=True)
class HistoricalCase:
    """Historical case for a significant organizational action."""

    case_identifier: str
    executive_decision_id: str
    supporting_evidence_ids: tuple[str, ...]
    competing_analysis_ids: tuple[str, ...]
    risk_assessment_id: str
    execution_history_id: str
    position_history_id: str
    market_conditions_id: str
    final_outcome: str
    lessons_learned: tuple[str, ...]
    validation_status: ValidationStatus
    audit_identifier: str


@dataclass(frozen=True)
class OrganizationalPerformanceMetrics:
    """Measured enterprise performance metrics."""

    investment_return: float
    decision_accuracy: float
    risk_prediction_accuracy: float
    execution_quality: float
    evidence_quality: float
    prompt_effectiveness: float
    organizational_consistency: float
    model_performance: float
    process_reliability: float
    learning_velocity: float


@dataclass(frozen=True)
class HistoricalEvaluation:
    """Scientific evaluation of historical outcomes."""

    evaluation_id: str
    historical_case_id: str
    what_succeeded: tuple[str, ...]
    what_failed: tuple[str, ...]
    correct_assumptions: tuple[str, ...]
    incorrect_assumptions: tuple[str, ...]
    process_improvements: tuple[str, ...]
    doctrine_change_candidates: tuple[str, ...]
    institutional_knowledge_candidates: tuple[str, ...]
    measurable_evidence_ids: tuple[str, ...]
    anecdotal_evidence_accepted: bool
    conclusion: str


@dataclass(frozen=True)
class ValidatedLearningRecord:
    """Validated institutional learning candidate."""

    learning_id: str
    source_case_id: str
    validation_status: ValidationStatus
    conclusion: str
    supporting_metric_ids: tuple[str, ...]
    recommended_consumers: tuple[str, ...]
    directly_modifies_behavior: bool


@dataclass(frozen=True)
class HistorianSystemPrompt:
    """Historian governing prompt artifact."""

    prompt_id: str
    version: str
    prompt_text: str


class HistorianGroupFramework:
    """Scientific conscience of ARGOS."""

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
        self._cases: dict[str, HistoricalCase] = {}
        self._evaluations: dict[str, HistoricalEvaluation] = {}
        self._learning_records: dict[str, ValidatedLearningRecord] = {}

    def architecture(self) -> HistorianGroupArchitecture:
        """Return Historian Group architecture."""
        return HistorianGroupArchitecture(
            "HIST-ARCH-001",
            tuple(template.name for template in historian_office_templates()),
            ("Executive Group", "Seeker Department", "Analyst Department", "Risk Office", "Trader Group"),
            ("Librarian Group", "Executive Group", "Future Engineering Orders"),
        )

    def system_prompt(self) -> HistorianSystemPrompt:
        """Return Historian Group governing prompt."""
        return HistorianSystemPrompt(
            "PROMPT-HISTORIAN-061",
            "1.0.0",
            (
                "You are the Historian Group of ARGOS.\n\n"
                "Your responsibility is to serve as the scientific evaluation organization of the ARGOS "
                "Deterministic Cognitive Enterprise.\n\n"
                "You continuously measure, evaluate, validate, and improve the organization by determining "
                "what actually happened, why it happened, and how the enterprise should evolve based upon "
                "empirical evidence.\n\n"
                "You do not gather market intelligence.\n"
                "You do not make investment decisions.\n"
                "You do not execute trades.\n"
                "You evaluate organizational performance after execution has occurred.\n\n"
                "Your mission is to convert operational history into validated institutional knowledge. "
                "Never accept anecdotal evidence. Every conclusion shall be supported by measurable evidence. "
                "Never overwrite historical records. Never discard organizational evidence. Every conclusion "
                "shall remain permanently reconstructable. Recommendations shall never directly modify "
                "organizational behavior."
            ),
        )

    def create_historical_case(
        self,
        historical_case: HistoricalCase,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Persist a historical case."""
        self.configuration_service.validate_startup()
        if historical_case.case_identifier in self._cases:
            raise ValueError(f"historical case already exists: {historical_case.case_identifier}")
        self._cases[historical_case.case_identifier] = historical_case
        return self._persist_contract(
            "HISTORICAL_CASE",
            case_file_id,
            trade_cycle_id,
            document_sequence,
            "Historical Case.",
            {
                "historian_system_prompt": self.system_prompt(),
                "historical_case": historical_case,
                "historical_record_overwritten": False,
                "organizational_evidence_discarded": False,
            },
        )

    def evaluate_case(
        self,
        historical_case_id: str,
        metrics: OrganizationalPerformanceMetrics,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Evaluate a historical case and generate validated learning."""
        self.configuration_service.validate_startup()
        if historical_case_id not in self._cases:
            raise ValueError(f"unknown historical case: {historical_case_id}")
        historical_case = self._cases[historical_case_id]
        evaluation = _evaluation(historical_case, metrics, document_sequence)
        learning = _learning_record(evaluation, metrics, document_sequence + 1)
        self._evaluations[evaluation.evaluation_id] = evaluation
        self._learning_records[learning.learning_id] = learning
        return {
            "historical_evaluation": self._persist_contract(
                "HISTORICAL_EVALUATION",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Historical Evaluation.",
                {
                    "historical_case_id": historical_case_id,
                    "performance_metrics": metrics,
                    "historical_evaluation": evaluation,
                    "measurable_evidence_required": True,
                    "anecdotal_evidence_accepted": False,
                    "conclusion_reconstructable": True,
                },
            ),
            "validated_learning_record": self._persist_contract(
                "VALIDATED_LEARNING_RECORD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Validated Learning Record.",
                {
                    "validated_learning_record": learning,
                    "recommendations_directly_modify_behavior": False,
                    "recommended_consumers": learning.recommended_consumers,
                },
            ),
        }

    def historical_case(self, case_identifier: str) -> HistoricalCase:
        """Return a historical case."""
        return self._cases[case_identifier]

    def learning_record(self, learning_id: str) -> ValidatedLearningRecord:
        """Return a validated learning record."""
        return self._learning_records[learning_id]

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


def historian_office_templates() -> tuple[HistorianOfficeTemplate, ...]:
    """Return initial Historian office templates."""
    return (
        HistorianOfficeTemplate("HISTORIAN-OFFICE-001", "Historical Case Office", "Maintain historical cases for significant organizational actions."),
        HistorianOfficeTemplate("HISTORIAN-OFFICE-002", "Performance Measurement Office", "Measure returns, decision accuracy, risk prediction, execution quality, and process reliability."),
        HistorianOfficeTemplate("HISTORIAN-OFFICE-003", "Hypothesis Validation Office", "Validate assumptions, hypotheses, prompts, models, and evidence quality against outcomes."),
        HistorianOfficeTemplate("HISTORIAN-OFFICE-004", "Organizational Learning Office", "Convert validated evaluations into learning records for Librarian, Executive, and future Engineering Orders."),
    )


def _evaluation(historical_case: HistoricalCase, metrics: OrganizationalPerformanceMetrics, document_sequence: int) -> HistoricalEvaluation:
    succeeded = []
    failed = []
    if metrics.decision_accuracy >= 0.5:
        succeeded.append("decision_accuracy")
    else:
        failed.append("decision_accuracy")
    if metrics.risk_prediction_accuracy >= 0.5:
        succeeded.append("risk_prediction_accuracy")
    else:
        failed.append("risk_prediction_accuracy")
    if metrics.execution_quality >= 0.75:
        succeeded.append("execution_quality")
    else:
        failed.append("execution_quality")
    conclusion = "validated_learning_available" if succeeded else "insufficient_success_requires_review"
    return HistoricalEvaluation(
        f"HEVAL-{document_sequence:06d}",
        historical_case.case_identifier,
        tuple(succeeded),
        tuple(failed),
        tuple(item for item in historical_case.lessons_learned if "correct" in item.lower()),
        tuple(item for item in historical_case.lessons_learned if "incorrect" in item.lower()),
        ("tighten_evidence_thresholds",) if failed else ("preserve_current_process",),
        ("review_doctrine" if failed else "no_doctrine_change_required",),
        ("institutionalize_measured_lesson",) if succeeded else (),
        historical_case.supporting_evidence_ids,
        False,
        conclusion,
    )


def _learning_record(evaluation: HistoricalEvaluation, metrics: OrganizationalPerformanceMetrics, document_sequence: int) -> ValidatedLearningRecord:
    status = ValidationStatus.VALIDATED if evaluation.what_succeeded and metrics.evidence_quality >= 0.5 else ValidationStatus.INCONCLUSIVE
    return ValidatedLearningRecord(
        f"VLR-{document_sequence:06d}",
        evaluation.historical_case_id,
        status,
        evaluation.conclusion,
        ("investment_return", "decision_accuracy", "risk_prediction_accuracy", "execution_quality", "evidence_quality"),
        ("Librarian Group", "Executive Group", "Future Engineering Orders"),
        False,
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
        produced_by_staff_id=HISTORIAN_CHIEF_STAFF_ID,
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
