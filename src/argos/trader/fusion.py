"""Trader Fusion Office."""

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

from .broker_integration import BrokerConnectionStatus, BrokerHealthStatus
from .execution_quality import ExecutionQualityMetrics
from .offices import TRADER_GROUP_ID
from .order_management import ManagedOrderRecord, OrderLifecycleState
from .position_management import PortfolioState, PositionLifecycleState, PositionRecord
from .trade_monitoring import AlertPriority, SystemHealthSnapshot, TradeMonitoringAlert


TRADER_FUSION_OFFICE_ID = "TRADER-OFFICE-007"
TRADER_FUSION_STAFF_ID = "STF-067"


class TraderFusionSeverity(str, Enum):
    """Trader Fusion anomaly severity."""

    INFORMATION = "information"
    NOTICE = "notice"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class EnterpriseReadiness(str, Enum):
    """Enterprise execution readiness classification."""

    READY = "ready"
    DEGRADED = "degraded"
    AT_RISK = "at_risk"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class TraderFusionSnapshot:
    """Complete input snapshot for enterprise Trader fusion."""

    snapshot_id: str
    execution_request_ids: tuple[str, ...]
    orders: tuple[ManagedOrderRecord, ...]
    positions: tuple[PositionRecord, ...]
    portfolio_state: PortfolioState
    broker_health: tuple[BrokerHealthStatus, ...]
    execution_quality_order_ids: tuple[str, ...]
    execution_quality_metrics: tuple[ExecutionQualityMetrics, ...]
    monitoring_alerts: tuple[TradeMonitoringAlert, ...]
    system_health: SystemHealthSnapshot
    risk_status: str
    historian_record_ids: tuple[str, ...]


@dataclass(frozen=True)
class EnterpriseExecutionModel:
    """Unified execution picture for the Trader Group."""

    model_id: str
    active_orders: int
    position_count: int
    broker_health: dict[str, str]
    execution_performance: dict[str, float]
    portfolio_exposure: float
    system_health: dict[str, object]
    operational_alert_count: int
    execution_capacity: str
    historical_trends: dict[str, object]


@dataclass(frozen=True)
class TraderFusionAnomaly:
    """Cross-office fusion anomaly."""

    anomaly_id: str
    classification: str
    severity: TraderFusionSeverity
    affected_offices: tuple[str, ...]
    evidence: tuple[str, ...]
    recommended_response: str


@dataclass(frozen=True)
class TraderFusionAssessment:
    """Continuous enterprise execution assessment."""

    assessment_id: str
    trader_operational_health: str
    broker_performance_summary: str
    execution_performance_summary: str
    position_integrity_summary: str
    enterprise_readiness: EnterpriseReadiness
    operational_risk_assessment: str
    recommended_executive_actions: tuple[str, ...]
    advisory_only: bool
    reconstructable: bool


@dataclass(frozen=True)
class TraderFusionCaseFile:
    """Trader Fusion Case File for enterprise anomalies."""

    case_file_id: str
    anomalies: tuple[TraderFusionAnomaly, ...]
    executive_group_notified: bool
    evidence_preserved: bool


@dataclass(frozen=True)
class TraderFusionSystemPrompt:
    """TFO governing prompt artifact."""

    prompt_id: str
    version: str
    prompt_text: str


class TraderFusionEngine:
    """Build unified Trader execution models."""

    def build_model(self, snapshot: TraderFusionSnapshot) -> EnterpriseExecutionModel:
        active_states = {
            OrderLifecycleState.CREATED,
            OrderLifecycleState.VALIDATED,
            OrderLifecycleState.QUEUED,
            OrderLifecycleState.SUBMITTED,
            OrderLifecycleState.ACKNOWLEDGED,
            OrderLifecycleState.WORKING,
            OrderLifecycleState.PARTIALLY_FILLED,
        }
        active_orders = sum(1 for order in snapshot.orders if order.current_state in active_states)
        performance = _execution_performance(snapshot.execution_quality_metrics)
        capacity = "constrained" if snapshot.system_health.resource_utilization > 0.85 else "available"
        if any(item.connection_status != BrokerConnectionStatus.CONNECTED for item in snapshot.broker_health):
            capacity = "degraded"
        return EnterpriseExecutionModel(
            f"TFM-{hashlib.sha256(snapshot.snapshot_id.encode('utf-8')).hexdigest()[:8].upper()}",
            active_orders,
            len(snapshot.positions),
            {item.broker_id: item.connection_status.value for item in snapshot.broker_health},
            performance,
            snapshot.portfolio_state.total_exposure,
            _json_ready(snapshot.system_health),
            len(snapshot.monitoring_alerts),
            capacity,
            {
                "historian_records": len(snapshot.historian_record_ids),
                "execution_quality_samples": len(snapshot.execution_quality_metrics),
            },
        )


class TraderFusionConsistencyEngine:
    """Detect cross-office inconsistencies and enterprise execution risks."""

    def detect(self, snapshot: TraderFusionSnapshot, model: EnterpriseExecutionModel) -> tuple[TraderFusionAnomaly, ...]:
        anomalies: list[TraderFusionAnomaly] = []
        order_position_ids = {order.identifiers.position_id for order in snapshot.orders if order.identifiers.position_id}
        position_ids = {position.position_id for position in snapshot.positions}
        missing_positions = tuple(sorted(order_position_ids - position_ids))
        if missing_positions:
            anomalies.append(_anomaly("position_reconciliation_failures", TraderFusionSeverity.CRITICAL, ("Order Management Office", "Position Management Office"), missing_positions, "reconcile_order_position_state"))

        order_ids = {order.identifiers.order_id for order in snapshot.orders}
        quality_order_ids = set(snapshot.execution_quality_order_ids)
        missing_quality = tuple(sorted(order_ids - quality_order_ids))
        filled_order_ids = {order.identifiers.order_id for order in snapshot.orders if order.current_state in {OrderLifecycleState.FILLED, OrderLifecycleState.PARTIALLY_FILLED}}
        if filled_order_ids and filled_order_ids - quality_order_ids:
            anomalies.append(_anomaly("conflicting_execution_records", TraderFusionSeverity.WARNING, ("Order Management Office", "Execution Quality Office"), tuple(sorted(filled_order_ids - quality_order_ids)), "request_execution_quality_review"))

        if missing_quality and len(snapshot.execution_quality_metrics) == 0:
            anomalies.append(_anomaly("execution_bottlenecks", TraderFusionSeverity.NOTICE, ("Trade Execution Office", "Execution Quality Office"), missing_quality, "confirm_execution_quality_pipeline"))

        degraded_brokers = tuple(item.broker_id for item in snapshot.broker_health if item.connection_status != BrokerConnectionStatus.CONNECTED)
        if degraded_brokers:
            anomalies.append(_anomaly("broker_degradation", TraderFusionSeverity.CRITICAL, ("Broker Integration Office", "Trade Monitoring Office"), degraded_brokers, "notify_executive_and_review_broker_routes"))

        if snapshot.system_health.system_latency_ms > 1000:
            anomalies.append(_anomaly("systemic_latency", TraderFusionSeverity.WARNING, ("Trade Monitoring Office", "Broker Integration Office"), ("system_latency",), "investigate_latency_sources"))
        if model.execution_capacity != "available":
            anomalies.append(_anomaly("capacity_constraints", TraderFusionSeverity.WARNING, ("Trade Monitoring Office", "Trader Fusion Office"), (model.execution_capacity,), "reduce_nonessential_execution_load"))
        if abs(snapshot.portfolio_state.total_exposure - sum(position.exposure for position in snapshot.positions)) > 0.01:
            anomalies.append(_anomaly("portfolio_inconsistencies", TraderFusionSeverity.CRITICAL, ("Position Management Office", "Risk Office"), (snapshot.portfolio_state.portfolio_id,), "reconcile_portfolio_exposure"))
        if any(alert.severity in {AlertPriority.CRITICAL, AlertPriority.EMERGENCY} for alert in snapshot.monitoring_alerts):
            anomalies.append(_anomaly("enterprise_execution_risk", TraderFusionSeverity.CRITICAL, ("Trade Monitoring Office", "Executive Group"), tuple(alert.alert_id for alert in snapshot.monitoring_alerts), "surface_to_executive_group"))
        if snapshot.risk_status not in {"contained", "normal", "certified"}:
            anomalies.append(_anomaly("operational_drift", TraderFusionSeverity.WARNING, ("Risk Office", "Trader Fusion Office"), (snapshot.risk_status,), "request_risk_status_review"))
        return tuple(anomalies)


class TraderFusionOffice:
    """Enterprise execution intelligence center for ARGOS Trader Group."""

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
        self.fusion_engine = TraderFusionEngine()
        self.consistency_engine = TraderFusionConsistencyEngine()
        self._assessments: list[TraderFusionAssessment] = []

    @property
    def assessment_history(self) -> tuple[TraderFusionAssessment, ...]:
        """Return permanent fusion assessment history."""
        return tuple(self._assessments)

    def fuse(
        self,
        snapshot: TraderFusionSnapshot,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Fuse Trader office outputs into enterprise execution assessments."""
        self.configuration_service.validate_startup()
        model = self.fusion_engine.build_model(snapshot)
        anomalies = self.consistency_engine.detect(snapshot, model)
        assessment = self._assessment(snapshot, model, anomalies, document_sequence)
        self._assessments.append(assessment)
        artifacts = {
            "trader_fusion_assessment": self._assessment_contract(snapshot, model, anomalies, assessment, case_file_id, trade_cycle_id, document_sequence),
            "enterprise_execution_summary": self._summary_contract(model, assessment, case_file_id, trade_cycle_id, document_sequence + 1),
        }
        if anomalies:
            artifacts["trader_fusion_case_file"] = self._case_file_contract(anomalies, case_file_id, trade_cycle_id, document_sequence + 2)
        return artifacts

    def system_prompt(self) -> TraderFusionSystemPrompt:
        """Return TFO governing prompt."""
        return TraderFusionSystemPrompt(
            "PROMPT-TFO-059",
            "1.0.0",
            (
                "You are the Trader Fusion Office (TFO) of ARGOS.\n\n"
                "Your responsibility is to continuously integrate the outputs of every office within the Trader "
                "Group into a single deterministic operational assessment of enterprise execution.\n\n"
                "You do not determine what should be traded.\n"
                "You do not execute trades.\n"
                "You do not alter executive decisions.\n\n"
                "Continuously evaluate operational state, execution performance, portfolio status, broker "
                "health, and execution integrity for the Trader Group as a whole. Fuse execution information "
                "from Trade Execution, Order Management, Broker Integration, Execution Quality, Position "
                "Management, and Trade Monitoring into a unified execution picture.\n\n"
                "Detect cross-office inconsistencies, conflicting execution records, position reconciliation "
                "failures, broker degradation, execution bottlenecks, operational drift, systemic latency, "
                "capacity constraints, portfolio inconsistencies, and enterprise execution risk. Every anomaly "
                "shall generate a Trader Fusion Case File.\n\n"
                "Produce continuous enterprise assessments for Trader operational health, broker performance, "
                "execution performance, position integrity, enterprise readiness, operational risk, and "
                "recommended Executive actions.\n\n"
                "Maintain deterministic synchronization with the Executive Group, Risk Office, Historian Group, "
                "Librarian Group, Trader Offices, and Enterprise Audit Framework.\n\n"
                "Never modify execution history. Never overwrite operational evidence. Every fusion assessment "
                "shall remain permanently reconstructable. Recommendations shall remain advisory. Only the "
                "Executive Group may authorize organizational changes.\n\n"
                "Optimize for determinism, enterprise situational awareness, cross-system consistency, "
                "operational transparency, auditability, historical traceability, reliability, and continuous "
                "improvement."
            ),
        )

    def _assessment(
        self,
        snapshot: TraderFusionSnapshot,
        model: EnterpriseExecutionModel,
        anomalies: tuple[TraderFusionAnomaly, ...],
        document_sequence: int,
    ) -> TraderFusionAssessment:
        critical = any(item.severity in {TraderFusionSeverity.CRITICAL, TraderFusionSeverity.EMERGENCY} for item in anomalies)
        readiness = EnterpriseReadiness.NOT_READY if critical else EnterpriseReadiness.DEGRADED if anomalies else EnterpriseReadiness.READY
        health = "critical" if critical else "degraded" if anomalies else "healthy"
        broker_summary = "broker degradation detected" if any(item.connection_status != BrokerConnectionStatus.CONNECTED for item in snapshot.broker_health) else "brokers operational"
        execution_score = model.execution_performance.get("average_execution_efficiency_score", 1.0)
        execution_summary = "execution performance degraded" if execution_score < 0.75 else "execution performance acceptable"
        position_summary = "position integrity issue detected" if any(item.classification in {"position_reconciliation_failures", "portfolio_inconsistencies"} for item in anomalies) else "positions synchronized"
        actions = tuple(dict.fromkeys(item.recommended_response for item in anomalies)) or ("continue_monitoring",)
        return TraderFusionAssessment(
            f"TFA-{document_sequence:06d}",
            health,
            broker_summary,
            execution_summary,
            position_summary,
            readiness,
            "enterprise execution risk elevated" if anomalies else "enterprise execution risk contained",
            actions,
            True,
            True,
        )

    def _assessment_contract(
        self,
        snapshot: TraderFusionSnapshot,
        model: EnterpriseExecutionModel,
        anomalies: tuple[TraderFusionAnomaly, ...],
        assessment: TraderFusionAssessment,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        payload = {
            "office_id": TRADER_FUSION_OFFICE_ID,
            "office_name": "Trader Fusion Office",
            "trader_fusion_system_prompt": self.system_prompt(),
            "snapshot": snapshot,
            "enterprise_execution_model": model,
            "anomalies": anomalies,
            "assessment": assessment,
            "recommendations_advisory_only": True,
            "execution_history_modified": False,
            "operational_evidence_overwritten": False,
        }
        return self._persist_contract("TRADER_FUSION_ASSESSMENT", case_file_id, trade_cycle_id, document_sequence, (), "Trader Fusion Assessment.", payload)

    def _summary_contract(self, model: EnterpriseExecutionModel, assessment: TraderFusionAssessment, case_file_id: str, trade_cycle_id: str, document_sequence: int) -> OperationalContract:
        payload = {
            "office_id": TRADER_FUSION_OFFICE_ID,
            "office_name": "Trader Fusion Office",
            "enterprise_execution_summary": {
                "trader_operational_health": assessment.trader_operational_health,
                "broker_performance_summary": assessment.broker_performance_summary,
                "execution_performance_summary": assessment.execution_performance_summary,
                "position_integrity_summary": assessment.position_integrity_summary,
                "enterprise_readiness": assessment.enterprise_readiness,
                "operational_risk_assessment": assessment.operational_risk_assessment,
                "recommended_executive_actions": assessment.recommended_executive_actions,
                "active_orders": model.active_orders,
                "portfolio_exposure": model.portfolio_exposure,
                "operational_alert_count": model.operational_alert_count,
            },
        }
        return self._persist_contract("ENTERPRISE_EXECUTION_SUMMARY", case_file_id, trade_cycle_id, document_sequence, (), "Enterprise Execution Summary.", payload)

    def _case_file_contract(
        self,
        anomalies: tuple[TraderFusionAnomaly, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        case_file = TraderFusionCaseFile(
            f"TFCF-{document_sequence:06d}",
            anomalies,
            any(item.severity in {TraderFusionSeverity.CRITICAL, TraderFusionSeverity.EMERGENCY} for item in anomalies),
            True,
        )
        return self._persist_contract("TRADER_FUSION_CASE", case_file_id, trade_cycle_id, document_sequence, (), "Trader Fusion Case File.", {"case_file": case_file})

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


def _execution_performance(metrics: tuple[ExecutionQualityMetrics, ...]) -> dict[str, float]:
    if not metrics:
        return {
            "average_execution_efficiency_score": 1.0,
            "average_broker_performance_score": 1.0,
            "average_slippage": 0.0,
            "average_fill_latency_ms": 0.0,
        }
    count = float(len(metrics))
    return {
        "average_execution_efficiency_score": round(sum(item.execution_efficiency_score for item in metrics) / count, 6),
        "average_broker_performance_score": round(sum(item.broker_performance_score for item in metrics) / count, 6),
        "average_slippage": round(sum(item.slippage for item in metrics) / count, 6),
        "average_fill_latency_ms": round(sum(item.fill_latency_ms for item in metrics) / count, 6),
    }


def _anomaly(
    classification: str,
    severity: TraderFusionSeverity,
    affected_offices: tuple[str, ...],
    evidence: tuple[str, ...],
    response: str,
) -> TraderFusionAnomaly:
    return TraderFusionAnomaly(
        f"TFOA-{hashlib.sha256(f'{classification}:{affected_offices}:{evidence}'.encode('utf-8')).hexdigest()[:8].upper()}",
        classification,
        severity,
        affected_offices,
        evidence,
        response,
    )


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
        produced_by_staff_id=TRADER_FUSION_STAFF_ID,
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
