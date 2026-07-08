"""Performance Measurement Office."""

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

from .group import HISTORIAN_GROUP_ID, OrganizationalPerformanceMetrics


PERFORMANCE_MEASUREMENT_OFFICE_ID = "HISTORIAN-OFFICE-002"
PERFORMANCE_MEASUREMENT_STAFF_ID = "STF-071"


class PerformanceTrendDirection(str, Enum):
    """Trend direction classification."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


@dataclass(frozen=True)
class GroupPerformanceDataset:
    """Standardized empirical dataset for one organizational group."""

    dataset_id: str
    group_name: str
    period_id: str
    decision_count: int
    successful_outcomes: int
    evidence_items: int
    validated_evidence_items: int
    predicted_risk_events: int
    realized_risk_events: int
    completed_processes: int
    failed_processes: int
    audit_record_ids: tuple[str, ...]
    source_case_ids: tuple[str, ...]


@dataclass(frozen=True)
class GroupPerformanceEvaluation:
    """Standardized group performance evaluation."""

    evaluation_id: str
    group_name: str
    period_id: str
    metrics: OrganizationalPerformanceMetrics
    composite_score: float
    ranking_score: float
    source_dataset_id: str
    trace_ids: tuple[str, ...]


@dataclass(frozen=True)
class OrganizationalScorecard:
    """Enterprise organizational scorecard."""

    scorecard_id: str
    period_id: str
    evaluations: tuple[GroupPerformanceEvaluation, ...]
    deterministic_rankings: tuple[str, ...]
    generated_from_dataset_ids: tuple[str, ...]


@dataclass(frozen=True)
class PerformanceTrend:
    """Long-term organizational performance trend."""

    trend_id: str
    group_name: str
    metric_name: str
    direction: PerformanceTrendDirection
    start_value: float
    end_value: float
    delta: float
    periods: tuple[str, ...]


@dataclass(frozen=True)
class HistoricalComparisonRecord:
    """Historical comparison record."""

    comparison_id: str
    current_period_id: str
    baseline_period_id: str
    improved_groups: tuple[str, ...]
    declined_groups: tuple[str, ...]
    stable_groups: tuple[str, ...]


@dataclass(frozen=True)
class MetricCalculationTrace:
    """Trace for deterministic metric calculation."""

    trace_id: str
    dataset_id: str
    formula_version: str
    input_fields: tuple[str, ...]
    output_metric_names: tuple[str, ...]
    source_audit_ids: tuple[str, ...]


@dataclass(frozen=True)
class PerformanceMeasurementStandards:
    """Librarian deliverable for performance measurement standards."""

    standards_id: str
    metric_definitions: dict[str, str]
    methodology: str
    reproducibility_required: bool


class PerformanceMeasurementOffice:
    """Deterministic organizational performance authority."""

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
        self._archive: dict[str, OrganizationalScorecard] = {}
        self._datasets: dict[str, GroupPerformanceDataset] = {}

    @property
    def historical_performance_archive(self) -> tuple[OrganizationalScorecard, ...]:
        """Return immutable historical scorecard archive."""
        return tuple(self._archive[key] for key in sorted(self._archive))

    def standards(self) -> PerformanceMeasurementStandards:
        """Return performance measurement standards for Librarian consumption."""
        return PerformanceMeasurementStandards(
            "PMS-062",
            {
                "decision_accuracy": "successful_outcomes / decision_count",
                "evidence_quality": "validated_evidence_items / evidence_items",
                "risk_prediction_accuracy": "1 - abs(predicted_risk_events - realized_risk_events) / max(predicted_risk_events, realized_risk_events, 1)",
                "process_reliability": "completed_processes / (completed_processes + failed_processes)",
                "composite_score": "mean of standardized performance metrics",
            },
            "All metrics are calculated from preserved empirical datasets using deterministic formulas.",
            True,
        )

    def generate_reports(
        self,
        datasets: tuple[GroupPerformanceDataset, ...],
        historical_scorecards: tuple[OrganizationalScorecard, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Generate deterministic performance reports and archives."""
        self.configuration_service.validate_startup()
        if not datasets:
            raise ValueError("performance measurement requires at least one dataset")
        for dataset in datasets:
            if dataset.dataset_id in self._datasets:
                raise ValueError(f"performance dataset already archived: {dataset.dataset_id}")
            self._datasets[dataset.dataset_id] = dataset
        evaluations = tuple(_evaluate_dataset(dataset) for dataset in datasets)
        scorecard = _scorecard(evaluations, document_sequence)
        trends = _trends(scorecard, historical_scorecards, document_sequence + 1)
        comparison = _comparison(scorecard, historical_scorecards[-1] if historical_scorecards else None, document_sequence + 2)
        traces = tuple(_trace(dataset) for dataset in datasets)
        self._archive[scorecard.scorecard_id] = scorecard
        return {
            "organizational_performance_report": self._persist_contract(
                "ORGANIZATIONAL_PERFORMANCE_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Organizational Performance Report.",
                {
                    "office_id": PERFORMANCE_MEASUREMENT_OFFICE_ID,
                    "office_name": "Performance Measurement Office",
                    "performance_metrics": evaluations,
                    "metric_calculation_traces": traces,
                    "performance_measurement_standards": self.standards(),
                    "active_operations_influenced": False,
                    "historical_performance_overwritten": False,
                },
            ),
            "executive_performance_report": self._persist_contract(
                "EXECUTIVE_PERFORMANCE_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Executive Performance Report.",
                {"executive_performance": tuple(item for item in evaluations if item.group_name == "Executive Group")},
            ),
            "organizational_scorecard": self._persist_contract(
                "ORGANIZATIONAL_SCORECARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Organizational Scorecard.",
                {"organizational_scorecard": scorecard, "organizational_rankings_deterministic": True},
            ),
            "performance_trend_report": self._persist_contract(
                "PERFORMANCE_TREND_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Performance Trend Report.",
                {
                    "performance_trends": trends,
                    "historical_comparison_record": comparison,
                    "performance_trend_archive_immutable": True,
                    "historical_performance_database_updated": True,
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


def _evaluate_dataset(dataset: GroupPerformanceDataset) -> GroupPerformanceEvaluation:
    decision_accuracy = _ratio(dataset.successful_outcomes, dataset.decision_count)
    evidence_quality = _ratio(dataset.validated_evidence_items, dataset.evidence_items)
    risk_accuracy = 1.0 - (abs(dataset.predicted_risk_events - dataset.realized_risk_events) / max(dataset.predicted_risk_events, dataset.realized_risk_events, 1))
    process_reliability = _ratio(dataset.completed_processes, dataset.completed_processes + dataset.failed_processes)
    metrics = OrganizationalPerformanceMetrics(
        investment_return=round((dataset.successful_outcomes - dataset.realized_risk_events) / max(dataset.decision_count, 1), 6),
        decision_accuracy=round(decision_accuracy, 6),
        risk_prediction_accuracy=round(risk_accuracy, 6),
        execution_quality=round(process_reliability if dataset.group_name == "Trader Group" else (decision_accuracy + process_reliability) / 2, 6),
        evidence_quality=round(evidence_quality, 6),
        prompt_effectiveness=round((evidence_quality + process_reliability) / 2, 6),
        organizational_consistency=round((decision_accuracy + evidence_quality + process_reliability) / 3, 6),
        model_performance=round((risk_accuracy + decision_accuracy) / 2, 6),
        process_reliability=round(process_reliability, 6),
        learning_velocity=round((dataset.validated_evidence_items + dataset.completed_processes) / max(dataset.evidence_items + dataset.completed_processes + dataset.failed_processes, 1), 6),
    )
    composite = round(mean((
        metrics.decision_accuracy,
        metrics.risk_prediction_accuracy,
        metrics.execution_quality,
        metrics.evidence_quality,
        metrics.organizational_consistency,
        metrics.process_reliability,
        metrics.learning_velocity,
    )), 6)
    return GroupPerformanceEvaluation(
        f"GPE-{hashlib.sha256(dataset.dataset_id.encode('utf-8')).hexdigest()[:8].upper()}",
        dataset.group_name,
        dataset.period_id,
        metrics,
        composite,
        composite,
        dataset.dataset_id,
        (*dataset.audit_record_ids, *dataset.source_case_ids),
    )


def _scorecard(evaluations: tuple[GroupPerformanceEvaluation, ...], document_sequence: int) -> OrganizationalScorecard:
    ranked = tuple(
        item.group_name
        for item in sorted(evaluations, key=lambda item: (-item.ranking_score, item.group_name))
    )
    period_ids = tuple(sorted({item.period_id for item in evaluations}))
    return OrganizationalScorecard(
        f"OS-{document_sequence:06d}",
        period_ids[0] if len(period_ids) == 1 else "+".join(period_ids),
        evaluations,
        ranked,
        tuple(item.source_dataset_id for item in evaluations),
    )


def _trends(scorecard: OrganizationalScorecard, historical_scorecards: tuple[OrganizationalScorecard, ...], document_sequence: int) -> tuple[PerformanceTrend, ...]:
    if not historical_scorecards:
        return tuple(
            PerformanceTrend(f"PTR-{document_sequence:06d}-{index:02d}", item.group_name, "composite_score", PerformanceTrendDirection.STABLE, item.composite_score, item.composite_score, 0.0, (scorecard.period_id,))
            for index, item in enumerate(scorecard.evaluations, start=1)
        )
    baseline = {item.group_name: item.composite_score for item in historical_scorecards[-1].evaluations}
    trends = []
    for index, item in enumerate(scorecard.evaluations, start=1):
        start = baseline.get(item.group_name, item.composite_score)
        delta = round(item.composite_score - start, 6)
        direction = PerformanceTrendDirection.IMPROVING if delta > 0.01 else PerformanceTrendDirection.DECLINING if delta < -0.01 else PerformanceTrendDirection.STABLE
        trends.append(PerformanceTrend(f"PTR-{document_sequence:06d}-{index:02d}", item.group_name, "composite_score", direction, start, item.composite_score, delta, (historical_scorecards[-1].period_id, scorecard.period_id)))
    return tuple(trends)


def _comparison(scorecard: OrganizationalScorecard, baseline: OrganizationalScorecard | None, document_sequence: int) -> HistoricalComparisonRecord:
    if baseline is None:
        return HistoricalComparisonRecord(f"HCR-{document_sequence:06d}", scorecard.period_id, scorecard.period_id, (), (), tuple(item.group_name for item in scorecard.evaluations))
    baseline_scores = {item.group_name: item.composite_score for item in baseline.evaluations}
    improved = []
    declined = []
    stable = []
    for item in scorecard.evaluations:
        delta = item.composite_score - baseline_scores.get(item.group_name, item.composite_score)
        if delta > 0.01:
            improved.append(item.group_name)
        elif delta < -0.01:
            declined.append(item.group_name)
        else:
            stable.append(item.group_name)
    return HistoricalComparisonRecord(f"HCR-{document_sequence:06d}", scorecard.period_id, baseline.period_id, tuple(improved), tuple(declined), tuple(stable))


def _trace(dataset: GroupPerformanceDataset) -> MetricCalculationTrace:
    return MetricCalculationTrace(
        f"MCT-{hashlib.sha256(dataset.dataset_id.encode('utf-8')).hexdigest()[:8].upper()}",
        dataset.dataset_id,
        "PMO-FORMULA-1.0.0",
        (
            "decision_count",
            "successful_outcomes",
            "evidence_items",
            "validated_evidence_items",
            "predicted_risk_events",
            "realized_risk_events",
            "completed_processes",
            "failed_processes",
        ),
        (
            "investment_return",
            "decision_accuracy",
            "risk_prediction_accuracy",
            "execution_quality",
            "evidence_quality",
            "prompt_effectiveness",
            "organizational_consistency",
            "model_performance",
            "process_reliability",
            "learning_velocity",
        ),
        dataset.audit_record_ids,
    )


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
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
        produced_by_staff_id=PERFORMANCE_MEASUREMENT_STAFF_ID,
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
