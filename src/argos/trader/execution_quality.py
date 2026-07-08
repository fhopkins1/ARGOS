"""Execution Quality Office."""

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

from .offices import TRADER_GROUP_ID


EXECUTION_QUALITY_OFFICE_ID = "TRADER-OFFICE-004"
EXECUTION_QUALITY_STAFF_ID = "STF-064"


class ExecutionQualityAnomalySeverity(str, Enum):
    """Execution quality anomaly severity."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class CompletedExecutionRecord:
    """Completed execution record consumed by EQO."""

    execution_record_id: str
    executive_decision_id: str
    execution_strategy_id: str
    order_id: str
    broker_id: str
    broker_execution_id: str
    market_condition_id: str
    position_id: str
    audit_id: str
    requested_price: float
    requested_quantity: float
    average_fill_price: float
    filled_quantity: float
    best_available_market_price: float
    bid_ask_spread: float
    fill_latency_ms: int
    order_completion_time_ms: int
    commission_cost: float
    fees: float
    realized_market_impact: float
    asset_class: str
    exchange: str
    liquidity_regime: str
    volatility_regime: str
    time_of_day: str
    order_type: str


@dataclass(frozen=True)
class ExecutionQualityMetrics:
    """Deterministic execution quality metrics."""

    requested_price: float
    average_fill_price: float
    best_available_market_price: float
    slippage: float
    bid_ask_spread: float
    fill_percentage: float
    fill_latency_ms: int
    order_completion_time_ms: int
    commission_cost: float
    fees: float
    realized_market_impact: float
    execution_efficiency_score: float
    broker_performance_score: float


@dataclass(frozen=True)
class ExecutionQualityComparison:
    """Comparison dimensions for enterprise quality analysis."""

    broker_id: str
    asset_class: str
    exchange: str
    market_condition_id: str
    liquidity_regime: str
    volatility_regime: str
    time_of_day: str
    order_type: str
    execution_strategy_id: str


@dataclass(frozen=True)
class ExecutionQualityAnomaly:
    """Execution quality anomaly."""

    anomaly_id: str
    classification: str
    severity: ExecutionQualityAnomalySeverity
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionQualityRecommendation:
    """Non-automatic improvement recommendation."""

    recommendation_id: str
    category: str
    recommendation: str
    historian_validation_required: bool
    automatically_alters_execution: bool = False


@dataclass(frozen=True)
class ExecutionQualityTrace:
    """Traceability map for EQO output."""

    executive_decision_id: str
    execution_strategy_id: str
    order_id: str
    broker_execution_id: str
    market_condition_id: str
    position_id: str
    historian_analysis_id: str
    audit_id: str


@dataclass(frozen=True)
class ExecutionQualityCaseFile:
    """Case file for execution quality anomalies."""

    case_file_id: str
    execution_record_id: str
    anomalies: tuple[ExecutionQualityAnomaly, ...]
    trace: ExecutionQualityTrace
    reconstructable: bool


@dataclass(frozen=True)
class ExecutionQualityHistorianDataset:
    """Historian-facing EQO dataset."""

    dataset_id: str
    metrics: ExecutionQualityMetrics
    comparison: ExecutionQualityComparison
    trace: ExecutionQualityTrace


@dataclass(frozen=True)
class ExecutionQualitySystemPrompt:
    """EQO governing prompt artifact."""

    prompt_id: str
    version: str
    prompt_text: str


class ExecutionQualityMetricEngine:
    """Calculate deterministic EQO metrics."""

    def measure(self, record: CompletedExecutionRecord) -> ExecutionQualityMetrics:
        slippage = round(record.average_fill_price - record.requested_price, 4)
        fill_percentage = round(record.filled_quantity / record.requested_quantity, 4) if record.requested_quantity else 0.0
        price_efficiency = max(0.0, 1.0 - abs(record.average_fill_price - record.best_available_market_price) / max(record.best_available_market_price, 0.0001))
        fill_efficiency = min(1.0, fill_percentage)
        cost_penalty = min(0.35, (record.commission_cost + record.fees + abs(record.realized_market_impact)) / max(record.requested_price * max(record.filled_quantity, 1), 1))
        latency_penalty = min(0.25, record.fill_latency_ms / 20000)
        execution_efficiency = round(max(0.0, min(1.0, price_efficiency * 0.45 + fill_efficiency * 0.35 + (1 - cost_penalty) * 0.1 + (1 - latency_penalty) * 0.1)), 4)
        broker_score = round(max(0.0, min(1.0, fill_efficiency * 0.45 + (1 - latency_penalty) * 0.3 + (1 - cost_penalty) * 0.25)), 4)
        return ExecutionQualityMetrics(
            record.requested_price,
            record.average_fill_price,
            record.best_available_market_price,
            slippage,
            record.bid_ask_spread,
            fill_percentage,
            record.fill_latency_ms,
            record.order_completion_time_ms,
            record.commission_cost,
            record.fees,
            record.realized_market_impact,
            execution_efficiency,
            broker_score,
        )


class ExecutionQualityComparator:
    """Build deterministic comparison dimensions."""

    def compare(self, record: CompletedExecutionRecord) -> ExecutionQualityComparison:
        return ExecutionQualityComparison(
            record.broker_id,
            record.asset_class,
            record.exchange,
            record.market_condition_id,
            record.liquidity_regime,
            record.volatility_regime,
            record.time_of_day,
            record.order_type,
            record.execution_strategy_id,
        )


class ExecutionQualityAnomalyDetector:
    """Detect deterministic execution quality anomalies."""

    def detect(self, record: CompletedExecutionRecord, metrics: ExecutionQualityMetrics) -> tuple[ExecutionQualityAnomaly, ...]:
        anomalies: list[ExecutionQualityAnomaly] = []
        if abs(metrics.slippage) > max(record.bid_ask_spread * 2, record.requested_price * 0.01):
            anomalies.append(_anomaly("excessive_slippage", "high", f"slippage:{metrics.slippage}"))
        if metrics.fill_percentage < 0.95:
            anomalies.append(_anomaly("poor_fill_quality", "medium", f"fill_percentage:{metrics.fill_percentage}"))
        if record.fill_latency_ms > 5000:
            anomalies.append(_anomaly("latency_spike", "medium", f"latency_ms:{record.fill_latency_ms}"))
        if record.commission_cost + record.fees > record.requested_price * max(record.filled_quantity, 1) * 0.01:
            anomalies.append(_anomaly("high_transaction_costs", "high", f"costs:{record.commission_cost + record.fees}"))
        if abs(record.realized_market_impact) > record.requested_price * 0.02:
            anomalies.append(_anomaly("unexpected_market_impact", "high", f"impact:{record.realized_market_impact}"))
        if metrics.execution_efficiency_score < 0.7:
            anomalies.append(_anomaly("failed_optimization", "medium", f"efficiency:{metrics.execution_efficiency_score}"))
        if metrics.broker_performance_score < 0.65:
            anomalies.append(_anomaly("unusual_broker_behavior", "medium", f"broker_score:{metrics.broker_performance_score}"))
        if record.average_fill_price < 0 or record.best_available_market_price <= 0:
            anomalies.append(_anomaly("execution_drift", "critical", "invalid_price_reference"))
        return tuple(anomalies)


class ExecutionQualityRecommendationEngine:
    """Generate non-automatic continuous improvement recommendations."""

    def recommend(self, anomalies: tuple[ExecutionQualityAnomaly, ...]) -> tuple[ExecutionQualityRecommendation, ...]:
        mapping = {
            "excessive_slippage": ("execution_strategy_improvements", "Review slicing and price-limit policy for similar liquidity regimes."),
            "poor_fill_quality": ("fill_quality_improvement", "Evaluate order type and venue selection for low fill-percentage scenarios."),
            "latency_spike": ("latency_reduction", "Review broker latency and routing path before future executions."),
            "high_transaction_costs": ("cost_reduction", "Compare broker and fee schedule alternatives through Historian validation."),
            "unexpected_market_impact": ("market_impact_reduction", "Reduce participation rate or adjust slicing for similar market conditions."),
            "failed_optimization": ("future_execution_optimization", "Run Historian study on strategy effectiveness before doctrine changes."),
            "unusual_broker_behavior": ("broker_selection", "Compare broker performance against peer brokers for similar order types."),
            "execution_drift": ("order_routing_improvements", "Investigate price reference integrity and routing controls."),
        }
        recommendations = []
        for index, anomaly in enumerate(anomalies, start=1):
            category, text = mapping.get(anomaly.classification, ("execution_quality_review", "Submit anomaly for Historian validation."))
            recommendations.append(ExecutionQualityRecommendation(f"EQR-{index:03d}", category, text, True))
        return tuple(recommendations)


class ExecutionQualityOffice:
    """Enterprise authority for deterministic execution quality evaluation."""

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
        self.metrics = ExecutionQualityMetricEngine()
        self.comparator = ExecutionQualityComparator()
        self.detector = ExecutionQualityAnomalyDetector()
        self.recommendations = ExecutionQualityRecommendationEngine()

    def evaluate_execution(
        self,
        record: CompletedExecutionRecord,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Evaluate one completed execution and emit deterministic reports."""
        self.configuration_service.validate_startup()
        metrics = self.metrics.measure(record)
        comparison = self.comparator.compare(record)
        trace = ExecutionQualityTrace(
            record.executive_decision_id,
            record.execution_strategy_id,
            record.order_id,
            record.broker_execution_id,
            record.market_condition_id,
            record.position_id,
            f"HIST-{record.execution_record_id}",
            record.audit_id,
        )
        anomalies = self.detector.detect(record, metrics)
        recommendations = self.recommendations.recommend(anomalies)
        dataset = ExecutionQualityHistorianDataset(f"EQD-{document_sequence:06d}", metrics, comparison, trace)
        base_payload = {
            "office_id": EXECUTION_QUALITY_OFFICE_ID,
            "office_name": "Execution Quality Office",
            "execution_quality_system_prompt": self.system_prompt(),
            "completed_execution_record": record,
            "trace": trace,
            "history_overwritten": False,
            "statistics_discarded": False,
            "execution_behavior_modified": False,
        }
        artifacts = {
            "execution_quality_report": {
                **base_payload,
                "metrics": metrics,
                "comparison": comparison,
                "recommendations": recommendations,
                "scientific_validation_required": True,
            },
            "execution_quality_historian_dataset": {
                **base_payload,
                "historian_dataset": dataset,
            },
        }
        if anomalies:
            artifacts["execution_quality_case_file"] = {
                **base_payload,
                "case_file": ExecutionQualityCaseFile(f"EQCF-{document_sequence:06d}", record.execution_record_id, anomalies, trace, True),
                "recommendations": recommendations,
            }
        contracts = {}
        for offset, (name, payload) in enumerate(artifacts.items()):
            contracts[name] = self._persist_contract(
                _contract_type_for(name),
                case_file_id,
                trade_cycle_id,
                document_sequence + offset,
                (record.executive_decision_id, record.audit_id),
                f"Execution Quality Office {name.replace('_', ' ')}.",
                payload,
            )
        return contracts

    def system_prompt(self) -> ExecutionQualitySystemPrompt:
        """Return EQO governing prompt."""
        return ExecutionQualitySystemPrompt(
            "PROMPT-EQO-056",
            "1.0.0",
            (
                "You are the Execution Quality Office (EQO) of ARGOS. Continuously evaluate the quality, "
                "efficiency, and effectiveness of every executed order and position. Do not determine what should "
                "be traded, execute trades, or modify completed executions. Scientifically evaluate execution "
                "performance, detect anomalies, generate deterministic quality reports, supply Historian data, and "
                "provide recommendations that never automatically alter execution behavior."
            ),
        )

    def _persist_contract(
        self,
        contract_type: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        parent_contract_ids: tuple[str, ...],
        human_summary: str,
        payload: dict[str, Any],
    ) -> OperationalContract:
        contract = _contract(contract_type, case_file_id, trade_cycle_id, document_sequence, parent_contract_ids, human_summary, payload)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        return contract


def _anomaly(classification: str, severity: str, evidence: str) -> ExecutionQualityAnomaly:
    return ExecutionQualityAnomaly(
        f"EQA-{hashlib.sha256(f'{classification}:{evidence}'.encode('utf-8')).hexdigest()[:8].upper()}",
        classification,
        ExecutionQualityAnomalySeverity(severity),
        (evidence,),
    )


def _contract_type_for(name: str) -> str:
    return {
        "execution_quality_report": "EXECUTION_QUALITY",
        "execution_quality_case_file": "EXECUTION_QUALITY_CASE",
        "execution_quality_historian_dataset": "EXECUTION_QUALITY_DATASET",
    }[name]


def _contract(
    contract_type: str,
    case_file_id: str,
    trade_cycle_id: str,
    document_sequence: int,
    parent_contract_ids: tuple[str, ...],
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
        parent_contract_ids=parent_contract_ids,
        produced_by_staff_id=EXECUTION_QUALITY_STAFF_ID,
        produced_by_group_id=TRADER_GROUP_ID,
        intended_consumer_group_id=TRADER_GROUP_ID,
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=human_summary,
        machine_payload=normalized_payload,
        signature_hash=signature_hash,
        source_reference_ids=parent_contract_ids,
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
