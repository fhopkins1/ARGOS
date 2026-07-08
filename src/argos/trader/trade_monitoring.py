"""Trade Monitoring Office."""

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
from .offices import TRADER_GROUP_ID
from .order_management import ManagedOrderRecord, OrderLifecycleState
from .position_management import PortfolioState, PositionRecord


TRADE_MONITORING_OFFICE_ID = "TRADER-OFFICE-006"
TRADE_MONITORING_STAFF_ID = "STF-066"


class AlertPriority(str, Enum):
    """TMO alert priorities."""

    INFORMATION = "information"
    NOTICE = "notice"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass(frozen=True)
class MarketStatusSnapshot:
    """Market and exchange status."""

    market_open: bool
    exchange_status: str
    trading_session: str
    data_feed_healthy: bool
    market_halt: bool = False


@dataclass(frozen=True)
class SystemHealthSnapshot:
    """Trader system health."""

    system_latency_ms: int
    api_health: str
    execution_throughput: float
    resource_utilization: float
    infrastructure_healthy: bool


@dataclass(frozen=True)
class TradeMonitoringSnapshot:
    """Complete TMO monitoring input snapshot."""

    snapshot_id: str
    orders: tuple[ManagedOrderRecord, ...]
    positions: tuple[PositionRecord, ...]
    portfolio_state: PortfolioState
    broker_health: tuple[BrokerHealthStatus, ...]
    market_status: MarketStatusSnapshot
    system_health: SystemHealthSnapshot
    risk_status: str
    execution_quality_status: str


@dataclass(frozen=True)
class TradeMonitoringAlert:
    """TMO alert."""

    alert_id: str
    severity: AlertPriority
    timestamp_utc: str
    source_system: str
    affected_components: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    recommended_response: str
    current_status: str
    executive_notified: bool


@dataclass(frozen=True)
class TradeMonitoringCaseFile:
    """Case File for TMO anomalies."""

    case_file_id: str
    alerts: tuple[TradeMonitoringAlert, ...]
    reconstructable: bool


@dataclass(frozen=True)
class OperationalTimelineEvent:
    """Permanent operational timeline event."""

    event_id: str
    event_type: str
    source: str
    timestamp_utc: str
    payload: dict[str, object]


@dataclass(frozen=True)
class TradeMonitoringDashboard:
    """Operational dashboard."""

    dashboard_id: str
    trader_group_health: str
    broker_status: dict[str, str]
    order_status: dict[str, int]
    position_status: dict[str, int]
    execution_activity: dict[str, object]
    system_health: dict[str, object]
    active_alerts: tuple[TradeMonitoringAlert, ...]
    historical_trends: dict[str, object]


@dataclass(frozen=True)
class TradeMonitoringSystemPrompt:
    """TMO governing prompt artifact."""

    prompt_id: str
    version: str
    prompt_text: str


class TradeMonitoringDetector:
    """Detect deterministic operational anomalies."""

    def detect(self, snapshot: TradeMonitoringSnapshot) -> tuple[TradeMonitoringAlert, ...]:
        alerts: list[TradeMonitoringAlert] = []
        for order in snapshot.orders:
            if order.current_state in {OrderLifecycleState.SUBMITTED, OrderLifecycleState.WORKING} and not order.broker_messages:
                alerts.append(_alert("stalled_orders", AlertPriority.WARNING, "Order Management Office", (order.identifiers.order_id,), "request_broker_status"))
            if order.current_state == OrderLifecycleState.SUBMITTED and not order.broker_messages:
                alerts.append(_alert("missing_broker_responses", AlertPriority.CRITICAL, "Broker Integration Office", (order.identifiers.order_id,), "notify_executive_and_broker_integration"))
            fill_ids = [fill.fill_id for fill in order.fills]
            if len(fill_ids) != len(set(fill_ids)):
                alerts.append(_alert("duplicate_executions", AlertPriority.CRITICAL, "Order Management Office", (order.identifiers.order_id,), "freeze_order_and_review"))

        for health in snapshot.broker_health:
            if health.connection_status != BrokerConnectionStatus.CONNECTED:
                alerts.append(_alert("broker_disconnects", AlertPriority.CRITICAL, "Broker Integration Office", (health.broker_id,), "notify_executive_and_pause_affected_routes"))
            if health.broker_latency_ms > 1000 or health.execution_latency_ms > 1000:
                alerts.append(_alert("excessive_execution_latency", AlertPriority.WARNING, "Broker Integration Office", (health.broker_id,), "review_latency_and_routing"))
            if not health.api_available:
                alerts.append(_alert("communication_failures", AlertPriority.CRITICAL, "Broker Integration Office", (health.broker_id,), "failover_or_pause"))

        if snapshot.market_status.market_halt:
            alerts.append(_alert("market_halts", AlertPriority.EMERGENCY, "Market Status", (snapshot.market_status.exchange_status,), "notify_executive_immediately"))
        if snapshot.market_status.trading_session not in {"regular", "pre_market", "post_market", "closed"}:
            alerts.append(_alert("trading_session_changes", AlertPriority.NOTICE, "Market Status", (snapshot.market_status.trading_session,), "review_session_policy"))
        if not snapshot.market_status.data_feed_healthy:
            alerts.append(_alert("data_feed_interruptions", AlertPriority.CRITICAL, "Data Feed", ("market_data",), "pause_data_dependent_monitoring"))

        for position in snapshot.positions:
            if abs(position.exposure) > 1_000_000:
                alerts.append(_alert("position_limit_violations", AlertPriority.CRITICAL, "Position Management Office", (position.position_id,), "notify_risk_and_executive"))
        if snapshot.portfolio_state.total_exposure > 5_000_000:
            alerts.append(_alert("unexpected_portfolio_exposure", AlertPriority.CRITICAL, "Position Management Office", (snapshot.portfolio_state.portfolio_id,), "notify_risk_and_executive"))

        if snapshot.system_health.system_latency_ms > 1000:
            alerts.append(_alert("system_performance_degradation", AlertPriority.WARNING, "Infrastructure", ("system_latency",), "investigate_system_load"))
        if snapshot.system_health.resource_utilization > 0.9 or not snapshot.system_health.infrastructure_healthy:
            alerts.append(_alert("infrastructure_failures", AlertPriority.EMERGENCY, "Infrastructure", ("resource_utilization",), "activate_operational_contingency"))
        if snapshot.execution_quality_status == "attention":
            alerts.append(_alert("execution_failures", AlertPriority.WARNING, "Execution Quality Office", ("execution_quality",), "review_execution_quality_case_files"))
        return tuple(alerts)


class OperationalTimelineBuilder:
    """Build permanent operational timelines."""

    def build(self, snapshot: TradeMonitoringSnapshot, alerts: tuple[TradeMonitoringAlert, ...]) -> tuple[OperationalTimelineEvent, ...]:
        events: list[OperationalTimelineEvent] = []
        for order in snapshot.orders:
            events.append(_timeline_event("order_event", "Order Management Office", {"order_id": order.identifiers.order_id, "state": order.current_state.value}))
        for position in snapshot.positions:
            events.append(_timeline_event("position_event", "Position Management Office", {"position_id": position.position_id, "status": position.position_status.value}))
        for health in snapshot.broker_health:
            events.append(_timeline_event("broker_event", "Broker Integration Office", {"broker_id": health.broker_id, "status": health.connection_status.value}))
        events.append(_timeline_event("market_event", "Market Status", _json_ready(snapshot.market_status)))
        events.append(_timeline_event("infrastructure_event", "Infrastructure", _json_ready(snapshot.system_health)))
        for alert in alerts:
            events.append(_timeline_event("alert_event", "Trade Monitoring Office", _json_ready(alert)))
        return tuple(events)


class TradeMonitoringOffice:
    """Enterprise operations center for Trader Group monitoring."""

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
        self.detector = TradeMonitoringDetector()
        self.timeline = OperationalTimelineBuilder()
        self._history: list[OperationalTimelineEvent] = []

    @property
    def monitoring_history(self) -> tuple[OperationalTimelineEvent, ...]:
        """Return permanent monitoring history."""
        return tuple(self._history)

    def monitor(
        self,
        snapshot: TradeMonitoringSnapshot,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Monitor Trader operations and emit reports."""
        self.configuration_service.validate_startup()
        alerts = self.detector.detect(snapshot)
        timeline = self.timeline.build(snapshot, alerts)
        self._history.extend(timeline)
        dashboard = self._dashboard(snapshot, alerts)
        artifacts = {
            "trade_monitoring_report": self._report_contract(snapshot, alerts, timeline, dashboard, case_file_id, trade_cycle_id, document_sequence),
            "trade_monitoring_dashboard": self._dashboard_contract(dashboard, case_file_id, trade_cycle_id, document_sequence + 1),
        }
        if alerts:
            artifacts["trade_monitoring_case_file"] = self._case_file_contract(alerts, timeline, case_file_id, trade_cycle_id, document_sequence + 2)
        return artifacts

    def system_prompt(self) -> TradeMonitoringSystemPrompt:
        """Return TMO governing prompt."""
        return TradeMonitoringSystemPrompt(
            "PROMPT-TMO-058",
            "1.0.0",
            (
                "You are the Trade Monitoring Office (TMO) of ARGOS.\n\n"
                "Your responsibility is to continuously monitor the operational health, execution status, and "
                "real-time behavior of the entire Trader Group.\n\n"
                "You do not determine what should be traded.\n"
                "You do not execute trades.\n"
                "You do not modify positions.\n\n"
                "Your responsibility is to detect operational anomalies, execution failures, unexpected "
                "conditions, and deviations from expected behavior while maintaining complete enterprise "
                "situational awareness.\n\n"
                "You operate continuously.\n\n"
                "Responsibilities include monitoring active orders, execution progress, open positions, broker "
                "connectivity, execution latency, execution failures, market status, system health, portfolio "
                "activity, enterprise alerts, and abnormal-condition escalation.\n\n"
                "Continuously monitor active orders, pending orders, filled orders, partial fills, cancelled "
                "orders, open positions, portfolio exposure, broker connectivity, market status, exchange "
                "status, system latency, API health, data feed health, execution throughput, and resource "
                "utilization.\n\n"
                "Detect and report stalled orders, missing broker responses, unexpected position changes, "
                "duplicate executions, communication failures, broker disconnects, market halts, trading "
                "session changes, position limit violations, unexpected portfolio exposure, excessive execution "
                "latency, data feed interruptions, system performance degradation, and infrastructure failures.\n\n"
                "Every detected anomaly shall generate a Trade Monitoring Case File. Every alert shall include "
                "an alert identifier, severity, timestamp, source system, affected components, supporting "
                "evidence, recommended response, and current status.\n\n"
                "Maintain deterministic synchronization with the Order Management Office, Broker Integration "
                "Office, Position Management Office, Execution Quality Office, Risk Office, Executive Dashboard, "
                "and Historian Group.\n\n"
                "Support alert priorities: information, notice, warning, critical, and emergency. Critical "
                "alerts shall immediately notify the Executive Group.\n\n"
                "Maintain complete operational timelines for order events, position events, broker events, "
                "market events, infrastructure events, and alert events.\n\n"
                "Never discard monitoring history. Never suppress operational anomalies. Every monitored event "
                "shall remain permanently reconstructable.\n\n"
                "Provide continuous operational dashboards displaying Trader Group health, broker status, order "
                "status, position status, execution activity, system health, active alerts, and historical "
                "trends.\n\n"
                "Optimize for determinism, situational awareness, early detection, reliability, recoverability, "
                "auditability, operational transparency, and enterprise synchronization.\n\n"
                "The Trade Monitoring Office is the enterprise operations center of the ARGOS Trader Group, "
                "providing continuous real-time visibility into every execution, broker, position, and "
                "operational component while ensuring abnormalities are detected, documented, escalated, and "
                "preserved for future organizational learning."
            ),
        )

    def _dashboard(self, snapshot: TradeMonitoringSnapshot, alerts: tuple[TradeMonitoringAlert, ...]) -> TradeMonitoringDashboard:
        order_status: dict[str, int] = {}
        for order in snapshot.orders:
            order_status[order.current_state.value] = order_status.get(order.current_state.value, 0) + 1
        position_status: dict[str, int] = {}
        for position in snapshot.positions:
            position_status[position.position_status.value] = position_status.get(position.position_status.value, 0) + 1
        critical_count = sum(1 for alert in alerts if alert.severity in {AlertPriority.CRITICAL, AlertPriority.EMERGENCY})
        health = "critical" if critical_count else "healthy"
        return TradeMonitoringDashboard(
            "TMD-058",
            health,
            {item.broker_id: item.connection_status.value for item in snapshot.broker_health},
            order_status,
            position_status,
            {"orders_monitored": len(snapshot.orders), "positions_monitored": len(snapshot.positions)},
            _json_ready(snapshot.system_health),
            alerts,
            {"timeline_events": len(self._history), "active_alert_count": len(alerts)},
        )

    def _report_contract(
        self,
        snapshot: TradeMonitoringSnapshot,
        alerts: tuple[TradeMonitoringAlert, ...],
        timeline: tuple[OperationalTimelineEvent, ...],
        dashboard: TradeMonitoringDashboard,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        payload = {
            "office_id": TRADE_MONITORING_OFFICE_ID,
            "office_name": "Trade Monitoring Office",
            "trade_monitoring_system_prompt": self.system_prompt(),
            "snapshot": snapshot,
            "alerts": alerts,
            "operational_timeline": timeline,
            "dashboard": dashboard,
            "history_discarded": False,
            "anomalies_suppressed": False,
            "orders_modified": False,
            "positions_modified": False,
        }
        return self._persist_contract("TRADE_MONITORING_REPORT", case_file_id, trade_cycle_id, document_sequence, (), "Trade Monitoring Report.", payload)

    def _dashboard_contract(self, dashboard: TradeMonitoringDashboard, case_file_id: str, trade_cycle_id: str, document_sequence: int) -> OperationalContract:
        return self._persist_contract("TRADE_MONITORING_DASHBOARD", case_file_id, trade_cycle_id, document_sequence, (), "Trade Monitoring Dashboard.", {"dashboard": dashboard})

    def _case_file_contract(
        self,
        alerts: tuple[TradeMonitoringAlert, ...],
        timeline: tuple[OperationalTimelineEvent, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        case_file = TradeMonitoringCaseFile(f"TMCF-{document_sequence:06d}", alerts, True)
        payload = {
            "office_id": TRADE_MONITORING_OFFICE_ID,
            "office_name": "Trade Monitoring Office",
            "case_file": case_file,
            "operational_timeline": timeline,
            "executive_group_notified": any(alert.executive_notified for alert in alerts),
        }
        return self._persist_contract("TRADE_MONITORING_CASE", case_file_id, trade_cycle_id, document_sequence, (), "Trade Monitoring Case File.", payload)

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


def _alert(
    classification: str,
    severity: AlertPriority,
    source_system: str,
    affected: tuple[str, ...],
    response: str,
) -> TradeMonitoringAlert:
    return TradeMonitoringAlert(
        f"TMA-{hashlib.sha256(f'{classification}:{source_system}:{affected}'.encode('utf-8')).hexdigest()[:8].upper()}",
        severity,
        utc_timestamp(),
        source_system,
        affected,
        (classification,),
        response,
        "active",
        severity in {AlertPriority.CRITICAL, AlertPriority.EMERGENCY},
    )


def _timeline_event(event_type: str, source: str, payload: dict[str, object]) -> OperationalTimelineEvent:
    return OperationalTimelineEvent(
        f"TME-{hashlib.sha256(f'{event_type}:{source}:{json.dumps(payload, sort_keys=True, separators=(",", ":"))}'.encode('utf-8')).hexdigest()[:8].upper()}",
        event_type,
        source,
        utc_timestamp(),
        payload,
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
        produced_by_staff_id=TRADE_MONITORING_STAFF_ID,
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
