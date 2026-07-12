"""Deterministic Event Detection Engine for ARGOS EO-CC."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp


class EventDomain(str, Enum):
    MARKET = "market"
    PORTFOLIO = "portfolio"
    POSITION = "position"
    BROKER = "broker"
    ORDER = "order"
    RISK = "risk"
    INTELLIGENCE = "intelligence"
    INFORMATION = "information"
    ENTERPRISE = "enterprise"
    COMMANDER = "commander"
    SCHEDULE = "schedule"
    SECURITY = "security"


class EventSeverity(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class EventUrgency(str, Enum):
    DEFERRED = "deferred"
    ROUTINE = "routine"
    PROMPT = "prompt"
    IMMEDIATE = "immediate"
    EMERGENCY = "emergency"


class EventMateriality(str, Enum):
    IMMATERIAL = "immaterial"
    MINOR = "minor"
    MATERIAL = "material"
    MAJOR = "major"
    ENTERPRISE_CRITICAL = "enterprise_critical"


class EventStatus(str, Enum):
    CANDIDATE = "candidate"
    VALIDATING = "validating"
    SUPPRESSED = "suppressed"
    DUPLICATE = "duplicate"
    CORRELATED = "correlated"
    VALIDATED = "validated"
    ROUTED = "routed"
    ACKNOWLEDGED = "acknowledged"
    MISSION_PROPOSED = "mission_proposed"
    MISSION_AUTHORIZED = "mission_authorized"
    RESOLVED = "resolved"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    FAILED = "failed"


class DetectorState(str, Enum):
    DISABLED = "disabled"
    STARTING = "starting"
    MONITORING = "monitoring"
    DEGRADED = "degraded"
    FAILED = "failed"
    COOLDOWN = "cooldown"
    SUSPENDED = "suspended"
    STOPPED = "stopped"


@dataclass(frozen=True)
class CandidateEvent:
    candidate_event_id: str
    detector_id: str
    detector_version: str
    domain: EventDomain
    event_type: str
    source_system: str
    source_record_id: str
    source_timestamp: str
    observed_at: str
    subject_type: str
    subject_id: str
    ticker: str
    position_id: str
    order_id: str
    workflow_id: str
    mission_id: str
    office_id: str
    prior_value: Any
    current_value: Any
    units: str
    comparison_method: str
    trigger_rule_id: str
    trigger_threshold: Any
    raw_payload_reference: str
    metadata: dict[str, Any]
    candidate_confidence: float
    created_at: str


@dataclass(frozen=True)
class ValidatedEvent:
    event_id: str
    candidate_event_id: str
    event_key: str
    deduplication_key: str
    correlation_key: str
    event_group_id: str
    domain: EventDomain
    event_type: str
    title: str
    summary: str
    source_system: str
    source_record_id: str
    source_timestamp: str
    observed_at: str
    validated_at: str
    subject_type: str
    subject_id: str
    ticker: str
    position_id: str
    order_id: str
    workflow_id: str
    mission_id: str
    office_id: str
    severity: EventSeverity
    urgency: EventUrgency
    materiality: EventMateriality
    confidence: float
    financial_exposure: Decimal | None
    estimated_downside: Decimal | None
    estimated_time_sensitivity_seconds: int | None
    prior_value: Any
    current_value: Any
    delta_value: Any
    delta_percent: Decimal | None
    units: str
    trigger_rule_id: str
    detector_id: str
    detector_version: str
    recommended_mission_type: str
    recommended_offices: tuple[str, ...]
    required_duty_officer: str
    status: EventStatus
    expires_at: str
    provenance: dict[str, Any]
    metadata: dict[str, Any]
    content_hash: str


@dataclass(frozen=True)
class DetectionRule:
    rule_id: str
    name: str
    description: str
    domain: EventDomain
    event_type: str
    enabled: bool
    detector_id: str
    subject_scope: dict[str, Any]
    comparison_method: str
    warning_threshold: Any
    trigger_threshold: Any
    critical_threshold: Any
    persistence_seconds: int
    debounce_seconds: int
    cooldown_seconds: int
    expiry_seconds: int
    hysteresis_value: Any
    minimum_confidence: float
    default_severity: EventSeverity
    default_urgency: EventUrgency
    default_materiality: EventMateriality
    recommended_mission_type: str
    recommended_offices: tuple[str, ...]
    market_hours_policy: str
    operating_mode_policy: tuple[str, ...]


@dataclass(frozen=True)
class DetectorHealth:
    detector_id: str
    name: str
    domain: EventDomain
    state: DetectorState
    observation_interval_seconds: int
    last_observation: str
    last_success: str
    consecutive_failures: int
    observation_count: int
    candidate_count: int
    validated_count: int
    suppression_count: int
    local_cost_estimate: float


@dataclass(frozen=True)
class SuppressedEvent:
    suppression_id: str
    candidate_event_id: str
    detector_id: str
    subject_id: str
    timestamp: str
    reason: str
    original_event_id: str
    cooldown_remaining_seconds: int
    duplicate_count: int
    estimated_cost_avoided: float


@dataclass(frozen=True)
class EventGroup:
    event_group_id: str
    correlation_key: str
    group_title: str
    constituent_event_ids: tuple[str, ...]
    aggregate_severity: EventSeverity
    aggregate_materiality: EventMateriality
    recommended_mission_type: str
    status: str


class EventDetectionEngine:
    """Lightweight deterministic event detection, validation, and routing."""

    def __init__(self) -> None:
        self._rules = _default_rules()
        self._detectors = _default_detector_health(self._rules)
        self._candidates: list[CandidateEvent] = []
        self._events: dict[str, ValidatedEvent] = {}
        self._suppressed: list[SuppressedEvent] = []
        self._groups: dict[str, EventGroup] = {}
        self._last_values: dict[str, Any] = {}
        self._dedupe: dict[str, str] = {}
        self._cooldowns: dict[str, str] = {}
        self._dead_letters: list[dict[str, Any]] = []
        self._routing_records: list[dict[str, Any]] = []
        self._resolution_records: list[dict[str, Any]] = []
        self._manual_overrides: list[dict[str, Any]] = []
        self._storm_records: list[dict[str, Any]] = []
        self.enabled = True
        self.global_event_rate_limit = 50

    def snapshot(self) -> dict[str, Any]:
        events = tuple(_snapshot_dataclass(event) for event in self._events.values())
        candidates = tuple(_snapshot_dataclass(item) for item in self._candidates[-50:])
        suppressed = tuple(_snapshot_dataclass(item) for item in self._suppressed[-50:])
        return {
            "engineName": "Event Detection Engine",
            "engineeringOrder": "EO-CC",
            "engineState": "monitoring" if self.enabled else "disabled",
            "activeDetectors": sum(1 for item in self._detectors.values() if item.state == DetectorState.MONITORING),
            "degradedDetectors": sum(1 for item in self._detectors.values() if item.state == DetectorState.DEGRADED),
            "failedDetectors": sum(1 for item in self._detectors.values() if item.state == DetectorState.FAILED),
            "eventsDetectedToday": len(self._candidates),
            "validatedEventsToday": len(self._events),
            "suppressedEventsToday": len(self._suppressed),
            "activeCriticalEvents": sum(1 for item in self._events.values() if item.status not in {EventStatus.RESOLVED, EventStatus.EXPIRED} and item.severity in {EventSeverity.CRITICAL, EventSeverity.EMERGENCY}),
            "missionTriggersSubmitted": sum(1 for item in self._routing_records if item.get("scheduler_mission_id")),
            "estimatedLocalMonitoringCost": round(sum(item.local_cost_estimate for item in self._detectors.values()), 4),
            "externalDataApiCost": 0.0,
            "activeEvents": events,
            "candidateEvents": candidates,
            "detectorHealth": tuple(_snapshot_dataclass(item) for item in self._detectors.values()),
            "eventFlow": {
                "observed": sum(item.observation_count for item in self._detectors.values()),
                "candidate": len(self._candidates),
                "validated": len(self._events),
                "suppressed": len(self._suppressed),
                "routed": sum(1 for item in self._events.values() if item.status in {EventStatus.ROUTED, EventStatus.MISSION_PROPOSED}),
                "missionProposed": sum(1 for item in self._events.values() if item.status == EventStatus.MISSION_PROPOSED),
                "missionAuthorized": sum(1 for item in self._events.values() if item.status == EventStatus.MISSION_AUTHORIZED),
                "resolved": sum(1 for item in self._events.values() if item.status == EventStatus.RESOLVED),
            },
            "suppressionAndDeduplication": suppressed,
            "eventGroups": tuple(_snapshot_dataclass(group) for group in self._groups.values()),
            "rules": tuple(_snapshot_dataclass(rule) for rule in self._rules.values()),
            "routingRecords": _json_safe(tuple(self._routing_records[-50:])),
            "deadLetters": _json_safe(tuple(self._dead_letters[-20:])),
            "resolutionHistory": _json_safe(tuple(self._resolution_records[-20:])),
            "manualOverrides": _json_safe(tuple(self._manual_overrides[-20:])),
            "metrics": self._metrics(),
            "costMetrics": {
                "localCpuTimeMs": len(self._candidates),
                "localProcessingEstimate": round(len(self._candidates) * 0.00001, 6),
                "paidDataSourceCost": 0.0,
                "apiGatewayCost": 0.0,
                "externalCallsAvoided": len(self._suppressed),
                "costByDetector": {key: item.local_cost_estimate for key, item in self._detectors.items()},
            },
            "lawCC": {
                "detectionIsAuthorization": False,
                "routineAiInvocations": 0,
                "officeActivations": 0,
                "workflowStarts": 0,
                "brokerWrites": 0,
                "ledgerMutations": 0,
            },
            "replay": {"available": True, "productionMutation": False},
        }

    def observe(self, sources: dict[str, Any], *, eos: Any = None, duty_officers: Any = None, route: bool = True) -> dict[str, Any]:
        """Run one bounded local observation pass and optionally route validated events."""
        if not self.enabled:
            return self.snapshot()
        candidates: list[CandidateEvent] = []
        detector_sources = (
            self._detect_market(sources),
            self._detect_portfolio(sources),
            self._detect_positions(sources),
            self._detect_broker_orders(sources),
            self._detect_risk(sources),
            self._detect_intelligence(sources),
            self._detect_enterprise(sources),
            self._detect_commander(sources),
            self._detect_schedule(sources),
        )
        for detector_candidates in detector_sources:
            candidates.extend(detector_candidates)
        if len(candidates) > self.global_event_rate_limit:
            candidates = self._storm_filter(candidates)
        for candidate in candidates:
            event = self._validate_candidate(candidate)
            if event and route:
                self._route_event(event, eos=eos, duty_officers=duty_officers)
        return self.snapshot()

    def replay(self, observations: tuple[dict[str, Any], ...], *, thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
        """Dry-run historical observations without production mutation."""
        engine = EventDetectionEngine()
        if thresholds:
            engine._rules = {key: _rule_with_threshold(rule, thresholds.get(rule.event_type, rule.trigger_threshold)) for key, rule in engine._rules.items()}
        for observation in observations:
            engine.observe(observation, route=False)
        result = engine.snapshot()
        result["replayMode"] = True
        result["productionMutation"] = False
        return result

    def recover_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Restore immutable ledger and checkpoints without re-emitting events."""
        for item in snapshot.get("activeEvents", ()):
            event = _event_from_dict(item)
            self._events[event.event_id] = event
            self._dedupe[event.deduplication_key] = event.event_id
        for item in snapshot.get("suppressionAndDeduplication", ()):
            self._suppressed.append(SuppressedEvent(**item))

    def resolve_event(self, event_id: str, *, reason: str = "Commander resolved event.") -> None:
        event = self._events[event_id]
        self._events[event_id] = replace(event, status=EventStatus.RESOLVED)
        self._resolution_records.append({"event_id": event_id, "timestamp": utc_timestamp(), "reason": reason})

    def _validate_candidate(self, candidate: CandidateEvent) -> ValidatedEvent | None:
        rule = self._rules[candidate.trigger_rule_id]
        self._candidates.append(candidate)
        self._touch_detector(candidate.detector_id, candidate=True)
        if not candidate.source_system or not candidate.event_type or candidate.candidate_confidence < rule.minimum_confidence:
            self._suppress(candidate, "validation_failed", "")
            return None
        if candidate.metadata.get("transient") or int(candidate.metadata.get("persistence_count", 1)) * 10 < rule.persistence_seconds:
            self._suppress(candidate, "persistence_requirement_not_met", "")
            return None
        dedupe_key = _dedupe_key(candidate)
        duplicate = self._dedupe.get(dedupe_key)
        if duplicate and not self._critical_bypass(candidate):
            self._suppress(candidate, "duplicate_event", duplicate)
            return None
        cooldown_until = self._cooldowns.get(dedupe_key, "")
        if cooldown_until and _parse_time(cooldown_until) > _parse_time(utc_timestamp()) and not self._critical_bypass(candidate):
            self._suppress(candidate, "cooldown_active", duplicate or "")
            return None
        event = self._event_from_candidate(candidate, rule, dedupe_key)
        self._events[event.event_id] = event
        self._dedupe[dedupe_key] = event.event_id
        self._cooldowns[dedupe_key] = (_parse_time(utc_timestamp()) + timedelta(seconds=rule.cooldown_seconds)).isoformat().replace("+00:00", "Z")
        self._correlate(event)
        self._touch_detector(candidate.detector_id, validated=True)
        return event

    def _event_from_candidate(self, candidate: CandidateEvent, rule: DetectionRule, dedupe_key: str) -> ValidatedEvent:
        delta = _delta(candidate.prior_value, candidate.current_value)
        delta_percent = _delta_percent(candidate.prior_value, candidate.current_value)
        severity, urgency, materiality = _score_event(candidate, rule, delta_percent)
        event_id = f"EDE-EVT-{len(self._events) + 1:06d}"
        correlation_key = f"{candidate.domain.value}:{candidate.subject_id or candidate.ticker or candidate.event_type}"
        body = {
            "candidate_event_id": candidate.candidate_event_id,
            "domain": candidate.domain.value,
            "event_type": candidate.event_type,
            "subject_id": candidate.subject_id,
            "current_value": candidate.current_value,
            "source_timestamp": candidate.source_timestamp,
        }
        content_hash = sha256(json.dumps(body, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        return ValidatedEvent(
            event_id=event_id,
            candidate_event_id=candidate.candidate_event_id,
            event_key=f"{candidate.domain.value}:{candidate.event_type}:{candidate.subject_id}",
            deduplication_key=dedupe_key,
            correlation_key=correlation_key,
            event_group_id=f"EDE-GRP-{sha256(correlation_key.encode('utf-8')).hexdigest()[:8].upper()}",
            domain=candidate.domain,
            event_type=candidate.event_type,
            title=f"{candidate.domain.value.title()} {candidate.event_type.replace('_', ' ').title()}",
            summary=f"{candidate.subject_id or candidate.ticker} triggered {candidate.event_type} by {candidate.comparison_method}.",
            source_system=candidate.source_system,
            source_record_id=candidate.source_record_id,
            source_timestamp=candidate.source_timestamp,
            observed_at=candidate.observed_at,
            validated_at=utc_timestamp(),
            subject_type=candidate.subject_type,
            subject_id=candidate.subject_id,
            ticker=candidate.ticker,
            position_id=candidate.position_id,
            order_id=candidate.order_id,
            workflow_id=candidate.workflow_id,
            mission_id=candidate.mission_id,
            office_id=candidate.office_id,
            severity=severity,
            urgency=urgency,
            materiality=materiality,
            confidence=min(1.0, max(candidate.candidate_confidence, rule.minimum_confidence)),
            financial_exposure=_decimal(candidate.metadata.get("financial_exposure")),
            estimated_downside=_decimal(candidate.metadata.get("estimated_downside")),
            estimated_time_sensitivity_seconds=int(candidate.metadata.get("time_sensitivity_seconds", 0) or 0),
            prior_value=candidate.prior_value,
            current_value=candidate.current_value,
            delta_value=delta,
            delta_percent=delta_percent,
            units=candidate.units,
            trigger_rule_id=rule.rule_id,
            detector_id=candidate.detector_id,
            detector_version=candidate.detector_version,
            recommended_mission_type=rule.recommended_mission_type,
            recommended_offices=rule.recommended_offices,
            required_duty_officer=_duty_officer(candidate.domain, rule.recommended_offices),
            status=EventStatus.VALIDATED,
            expires_at=(_parse_time(utc_timestamp()) + timedelta(seconds=rule.expiry_seconds)).isoformat().replace("+00:00", "Z") if rule.expiry_seconds else "",
            provenance={
                "source_system": candidate.source_system,
                "source_record_id": candidate.source_record_id,
                "source_timestamp": candidate.source_timestamp,
                "observation_timestamp": candidate.observed_at,
                "comparison_method": candidate.comparison_method,
                "trigger_rule": candidate.trigger_rule_id,
                "detector_version": candidate.detector_version,
                "raw_source_metadata": candidate.metadata,
            },
            metadata=candidate.metadata,
            content_hash=content_hash,
        )

    def _route_event(self, event: ValidatedEvent, *, eos: Any, duty_officers: Any) -> None:
        record = {"event_id": event.event_id, "timestamp": utc_timestamp(), "duty_officer": event.required_duty_officer, "scheduler_mission_id": "", "status": "validated"}
        mission = None
        if eos and event.materiality in {EventMateriality.MATERIAL, EventMateriality.MAJOR, EventMateriality.ENTERPRISE_CRITICAL}:
            try:
                mission = eos.register_event_trigger(event.event_type, event.event_id, event.recommended_offices or ("Risk",), priority=_event_priority(event))
                record["scheduler_mission_id"] = mission.mission_id
            except Exception as exc:  # defensive; detector failure must not crash runtime
                self._dead_letters.append({"event_id": event.event_id, "stage": "scheduler_trigger", "reason": str(exc), "timestamp": utc_timestamp()})
        if duty_officers and event.required_duty_officer:
            request = {
                "sourceOfficeId": "Event Detection Engine",
                "targetOfficeId": event.required_duty_officer,
                "missionId": mission.mission_id if mission else event.mission_id,
                "workflowId": event.workflow_id or "EDE-EVENT-WORKFLOW",
                "executionTokenId": (mission.execution_token_id if mission else "EDE-PENDING-WORKFLOW-TOKEN"),
                "requestType": _request_type(event),
                "taskDescription": event.summary,
                "priority": "Critical" if event.severity in {EventSeverity.CRITICAL, EventSeverity.EMERGENCY} else "High",
                "criticality": "Critical" if event.severity in {EventSeverity.CRITICAL, EventSeverity.EMERGENCY} else "Normal",
                "eventReference": event.event_id,
                "estimatedValue": _event_value(event),
                "estimatedCost": 0.01,
            }
            try:
                decision = duty_officers.submit_request(request, eos.snapshot() if hasattr(eos, "snapshot") else {})
                record["duty_decision_id"] = decision.decision_id
                record["duty_disposition"] = decision.disposition
            except Exception as exc:
                self._dead_letters.append({"event_id": event.event_id, "stage": "duty_officer_route", "reason": str(exc), "timestamp": utc_timestamp()})
        status = EventStatus.MISSION_PROPOSED if record["scheduler_mission_id"] else EventStatus.ROUTED
        self._events[event.event_id] = replace(event, status=status)
        record["status"] = status.value
        self._routing_records.append(record)

    def _detect_market(self, sources: dict[str, Any]) -> list[CandidateEvent]:
        provider = sources.get("marketDataProviderAbstractionLayer") or sources.get("market_data_provider") or {}
        quotes = provider.get("normalizedObjects", {}).get("quotes", ())
        out = []
        for quote in quotes:
            symbol = str(quote.get("symbol", ""))
            if not symbol:
                continue
            current = float(quote.get("last") or quote.get("price") or 0)
            if not current:
                continue
            key = f"market:{symbol}:last"
            prior = self._last_values.get(key)
            self._last_values[key] = current
            if prior is None:
                continue
            percent = abs(float(_delta_percent(prior, current) or 0))
            if percent >= float(self._rules["market_price_movement"].trigger_threshold):
                out.append(self._candidate("market_price_detector", EventDomain.MARKET, "price_movement", "MarketDataProvider", symbol, prior, current, "percent_change", "market_price_movement", ticker=symbol, units="USD", metadata={"delta_percent": percent, "persistence_count": 3}))
        if provider.get("freshness", {}).get("status") == "STALE":
            out.append(self._candidate("market_feed_detector", EventDomain.MARKET, "stale_market_data", "MarketDataProvider", "market_feed", "fresh", "stale", "state_transition", "market_data_stale", metadata={"persistence_count": 3}))
        return out

    def _detect_portfolio(self, sources: dict[str, Any]) -> list[CandidateEvent]:
        truth = sources.get("performanceTruthEngine") or sources.get("performance_truth") or {}
        ledger = tuple(truth.get("portfolioLedger", ()))
        if not ledger:
            return []
        latest = ledger[-1]
        equity = float(latest.get("total_equity", latest.get("portfolio_value", 0)) or 0)
        key = "portfolio:equity"
        prior = self._last_values.get(key)
        self._last_values[key] = equity
        if prior and prior > 0:
            dd = ((prior - equity) / prior) * 100
            if dd >= float(self._rules["portfolio_drawdown"].trigger_threshold):
                return [self._candidate("portfolio_drawdown_detector", EventDomain.PORTFOLIO, "portfolio_drawdown", "PerformanceTruthEngine", "portfolio", prior, equity, "drawdown_percent", "portfolio_drawdown", units="USD", metadata={"estimated_downside": prior - equity, "persistence_count": 3})]
        return []

    def _detect_positions(self, sources: dict[str, Any]) -> list[CandidateEvent]:
        surveillance = sources.get("positionSurveillanceEngine") or sources.get("position_surveillance") or {}
        monitoring = sources.get("positionMonitoringNetwork") or sources.get("position_monitoring_network") or {}
        out = []
        for event in tuple(monitoring.get("eventDetectionFeed", ())):
            event_type = str(event.get("event_type", "position_monitoring_event"))
            severity = str(event.get("severity", "")).lower()
            if event_type and severity in {"high", "critical"}:
                out.append(
                    self._candidate(
                        "position_monitoring_network_detector",
                        EventDomain.POSITION,
                        event_type,
                        "PositionMonitoringNetwork",
                        str(event.get("position_id", event.get("subject_id", ""))),
                        "",
                        event.get("evidence", {}).get("currentPrice", event.get("evidence", {}).get("riskScore", "")),
                        "position_monitoring_event",
                        "position_threshold_event",
                        ticker=str(event.get("ticker", "")),
                        position_id=str(event.get("position_id", "")),
                        units="",
                        metadata={"financial_exposure": event.get("financial_exposure", 0), "persistence_count": 3},
                    )
                )
        for snapshot in tuple(surveillance.get("latestSnapshots", ())):
            events = tuple(snapshot.get("detected_events", ()))
            relevant = [item for item in events if item in {"stop_loss_approached", "stop_loss_reached", "profit_target_approached", "profit_target_reached", "trailing_stop_reached", "large_adverse_move"}]
            for event_type in relevant:
                out.append(self._candidate("position_threshold_detector", EventDomain.POSITION, event_type, "PositionSurveillanceEngine", str(snapshot.get("position_id", "")), snapshot.get("average_cost"), snapshot.get("current_price"), "surveillance_event", "position_threshold_event", ticker=str(snapshot.get("symbol", "")), position_id=str(snapshot.get("position_id", "")), units="USD", metadata={"financial_exposure": snapshot.get("current_value", 0), "persistence_count": 3}))
        return out

    def _detect_broker_orders(self, sources: dict[str, Any]) -> list[CandidateEvent]:
        truth = sources.get("performanceTruthEngine") or {}
        out = []
        for order in tuple(truth.get("orderLedger", ())):
            status = str(order.get("status", "")).upper()
            if status in {"REJECTED", "PARTIALLY_FILLED", "FILLED", "CANCELLED", "EXPIRED"}:
                out.append(self._candidate("broker_order_detector", EventDomain.ORDER, f"order_{status.lower()}", "PerformanceTruthEngine", str(order.get("order_id", order.get("execution_id", ""))), "", status, "broker_status_transition", "broker_order_status", ticker=str(order.get("symbol", "")), order_id=str(order.get("order_id", "")), metadata={"persistence_count": 3}))
        return out

    def _detect_risk(self, sources: dict[str, Any]) -> list[CandidateEvent]:
        risk = sources.get("enterpriseRiskFactorEngine") or {}
        score = float((risk.get("latestRiskFactorRecord") or risk.get("dashboardFeed") or {}).get("composite_risk_score", risk.get("compositeEnterpriseRiskScore", 0)) or 0)
        if score >= float(self._rules["risk_limit_breach"].trigger_threshold):
            return [self._candidate("risk_limit_detector", EventDomain.RISK, "risk_limit_breached", "EnterpriseRiskFactorEngine", "enterprise_risk", 0, score, "threshold", "risk_limit_breach", metadata={"persistence_count": 3})]
        return []

    def _detect_intelligence(self, sources: dict[str, Any]) -> list[CandidateEvent]:
        sic = sources.get("strategicIntelligenceCommand") or {}
        products = tuple(sic.get("strategicReports", ()) or sic.get("reports", ()))
        if products and len(products) != self._last_values.get("intelligence:product_count"):
            prior = self._last_values.get("intelligence:product_count", 0)
            self._last_values["intelligence:product_count"] = len(products)
            return [self._candidate("intelligence_product_detector", EventDomain.INTELLIGENCE, "high_confidence_product_published", "StrategicIntelligenceCommand", "strategic_products", prior, len(products), "count_change", "intelligence_product_published", metadata={"persistence_count": 3})]
        return []

    def _detect_enterprise(self, sources: dict[str, Any]) -> list[CandidateEvent]:
        health = sources.get("enterpriseHealthMonitor") or {}
        alerts = tuple(health.get("alerts", ()) or health.get("criticalAlerts", ()))
        if alerts:
            alert = alerts[-1]
            return [self._candidate("enterprise_health_detector", EventDomain.ENTERPRISE, "enterprise_health_alert", "EnterpriseHealthMonitor", str(alert.get("alert_id", "health-alert")), "", alert.get("severity", "warning"), "health_alert", "enterprise_health_failure", metadata={"persistence_count": 3})]
        return []

    def _detect_commander(self, sources: dict[str, Any]) -> list[CandidateEvent]:
        eab = sources.get("eab") or {}
        events = tuple(eab.get("events", ()))
        out = []
        for event in events[-3:]:
            if event.get("event_category") == "COMMAND" or event.get("organization") == "Commander Interface":
                event_id = str(event.get("event_id", event.get("task_identifier", "")))
                if event_id and event_id != self._last_values.get(f"commander:{event_id}"):
                    self._last_values[f"commander:{event_id}"] = event_id
                    out.append(self._candidate("commander_policy_detector", EventDomain.COMMANDER, "commander_directive", "EnterpriseActivityBus", event_id, "", event.get("summary", ""), "commander_event", "commander_directive", metadata={"persistence_count": 3}))
        return out

    def _detect_schedule(self, sources: dict[str, Any]) -> list[CandidateEvent]:
        eos = sources.get("enterpriseOperationsScheduler") or {}
        next_mission = eos.get("nextMission", {})
        if next_mission and next_mission.get("mission_id") != self._last_values.get("schedule:next_mission"):
            self._last_values["schedule:next_mission"] = next_mission.get("mission_id")
            return [self._candidate("schedule_boundary_detector", EventDomain.SCHEDULE, "scheduled_mission_due", "EnterpriseOperationsScheduler", next_mission.get("mission_id", ""), "", next_mission.get("scheduled_start", ""), "schedule_boundary", "scheduled_mission_due", mission_id=next_mission.get("mission_id", ""), metadata={"persistence_count": 3})]
        return []

    def _candidate(self, detector_id: str, domain: EventDomain, event_type: str, source: str, subject: str, prior: Any, current: Any, method: str, rule_id: str, *, ticker: str = "", position_id: str = "", order_id: str = "", mission_id: str = "", units: str = "", metadata: dict[str, Any] | None = None) -> CandidateEvent:
        timestamp = utc_timestamp()
        return CandidateEvent(
            candidate_event_id=f"EDE-CAN-{len(self._candidates) + 1:06d}",
            detector_id=detector_id,
            detector_version="EO-CC-1.0",
            domain=domain,
            event_type=event_type,
            source_system=source,
            source_record_id=str(subject),
            source_timestamp=timestamp,
            observed_at=timestamp,
            subject_type="ticker" if ticker else "record",
            subject_id=str(subject),
            ticker=ticker,
            position_id=position_id,
            order_id=order_id,
            workflow_id="",
            mission_id=mission_id,
            office_id="",
            prior_value=prior,
            current_value=current,
            units=units,
            comparison_method=method,
            trigger_rule_id=rule_id,
            trigger_threshold=self._rules[rule_id].trigger_threshold,
            raw_payload_reference=f"{source}:{subject}",
            metadata=metadata or {},
            candidate_confidence=0.95,
            created_at=timestamp,
        )

    def _suppress(self, candidate: CandidateEvent, reason: str, original_event_id: str) -> None:
        duplicate_count = sum(1 for item in self._suppressed if item.original_event_id == original_event_id) + 1 if original_event_id else 0
        self._suppressed.append(
            SuppressedEvent(
                suppression_id=f"EDE-SUP-{len(self._suppressed) + 1:06d}",
                candidate_event_id=candidate.candidate_event_id,
                detector_id=candidate.detector_id,
                subject_id=candidate.subject_id,
                timestamp=utc_timestamp(),
                reason=reason,
                original_event_id=original_event_id,
                cooldown_remaining_seconds=0,
                duplicate_count=duplicate_count,
                estimated_cost_avoided=0.001,
            )
        )
        self._touch_detector(candidate.detector_id, suppressed=True)

    def _correlate(self, event: ValidatedEvent) -> None:
        group = self._groups.get(event.event_group_id)
        ids = (*group.constituent_event_ids, event.event_id) if group else (event.event_id,)
        severity = event.severity if not group else _max_severity((group.aggregate_severity, event.severity))
        materiality = event.materiality if not group else _max_materiality((group.aggregate_materiality, event.materiality))
        self._groups[event.event_group_id] = EventGroup(event.event_group_id, event.correlation_key, event.title, ids, severity, materiality, event.recommended_mission_type, "open")

    def _storm_filter(self, candidates: list[CandidateEvent]) -> list[CandidateEvent]:
        preserved = [item for item in candidates if item.domain in {EventDomain.POSITION, EventDomain.BROKER, EventDomain.ORDER, EventDomain.RISK} or item.event_type in {"enterprise_health_alert", "commander_directive"}]
        capacity = max(0, self.global_event_rate_limit - len(preserved))
        kept = [*preserved, *candidates[:capacity]]
        self._storm_records.append({"timestamp": utc_timestamp(), "input_count": len(candidates), "preserved_count": len(kept), "suppressed_count": max(0, len(candidates) - len(kept))})
        for candidate in candidates[capacity + len(preserved):]:
            self._suppress(candidate, "event_storm_rate_limit", "")
        return kept

    def _critical_bypass(self, candidate: CandidateEvent) -> bool:
        return candidate.event_type in {"stop_loss_reached", "risk_limit_breached", "enterprise_health_alert", "order_rejected"}

    def _touch_detector(self, detector_id: str, *, candidate: bool = False, validated: bool = False, suppressed: bool = False) -> None:
        detector = self._detectors.get(detector_id)
        if not detector:
            return
        self._detectors[detector_id] = replace(
            detector,
            state=DetectorState.MONITORING,
            last_observation=utc_timestamp(),
            last_success=utc_timestamp(),
            observation_count=detector.observation_count + (1 if candidate else 0),
            candidate_count=detector.candidate_count + (1 if candidate else 0),
            validated_count=detector.validated_count + (1 if validated else 0),
            suppression_count=detector.suppression_count + (1 if suppressed else 0),
        )

    def _metrics(self) -> dict[str, Any]:
        events = tuple(self._events.values())
        return {
            "eventsByDomain": _count_by(events, lambda item: item.domain.value),
            "eventsBySeverity": _count_by(events, lambda item: item.severity.value),
            "eventsByMateriality": _count_by(events, lambda item: item.materiality.value),
            "eventsByUrgency": _count_by(events, lambda item: item.urgency.value),
            "activeUnresolvedEvents": sum(1 for item in events if item.status not in {EventStatus.RESOLVED, EventStatus.EXPIRED}),
            "eventsRoutedToDutyOfficers": sum(1 for item in self._routing_records if item.get("duty_decision_id")),
            "schedulerTriggerRequests": sum(1 for item in self._routing_records if item.get("scheduler_mission_id")),
            "schedulerApprovedMissions": 0,
            "eventsResolvedLocally": 0,
            "eventsResolvedFromCache": 0,
            "falsePositiveCount": sum(1 for item in self._resolution_records if item.get("false_positive")),
            "costAvoidedThroughSuppression": round(sum(item.estimated_cost_avoided for item in self._suppressed), 4),
            "estimatedAiCallsAvoided": len(self._suppressed),
            "eventStormOccurrences": len(self._storm_records),
            "averageEventsPerAuthorizedMission": 0,
            "detectors": {key: _snapshot_dataclass(value) for key, value in self._detectors.items()},
        }


def _default_rules() -> dict[str, DetectionRule]:
    def rule(rule_id: str, domain: EventDomain, event_type: str, detector: str, threshold: Any, offices: tuple[str, ...], mission: str, severity=EventSeverity.MODERATE, urgency=EventUrgency.PROMPT, materiality=EventMateriality.MATERIAL) -> DetectionRule:
        return DetectionRule(rule_id, event_type.replace("_", " ").title(), f"Detect {event_type}.", domain, event_type, True, detector, {}, "threshold", None, threshold, threshold, 20, 10, 300, 3600, None, 0.8, severity, urgency, materiality, mission, offices, "session_aware", ("Full Paper Trading", "Position Management Only", "Capital Preservation", "Observation Only"))

    return {
        "market_price_movement": rule("market_price_movement", EventDomain.MARKET, "price_movement", "market_price_detector", 2.0, ("Risk",), "market_event_review"),
        "market_data_stale": rule("market_data_stale", EventDomain.MARKET, "stale_market_data", "market_feed_detector", "STALE", ("Executive",), "data_repair_review", EventSeverity.HIGH),
        "portfolio_drawdown": rule("portfolio_drawdown", EventDomain.PORTFOLIO, "portfolio_drawdown", "portfolio_drawdown_detector", 1.0, ("Risk",), "risk_review", EventSeverity.HIGH),
        "position_threshold_event": rule("position_threshold_event", EventDomain.POSITION, "position_threshold_event", "position_threshold_detector", "detected_event", ("Risk", "Trader"), "position_safety_review", EventSeverity.CRITICAL, EventUrgency.IMMEDIATE, EventMateriality.MAJOR),
        "broker_order_status": rule("broker_order_status", EventDomain.ORDER, "broker_order_status", "broker_order_detector", "status_change", ("Trader", "Risk"), "broker_reconciliation", EventSeverity.HIGH),
        "risk_limit_breach": rule("risk_limit_breach", EventDomain.RISK, "risk_limit_breached", "risk_limit_detector", 80, ("Risk", "Executive"), "risk_control_review", EventSeverity.CRITICAL, EventUrgency.IMMEDIATE, EventMateriality.ENTERPRISE_CRITICAL),
        "intelligence_product_published": rule("intelligence_product_published", EventDomain.INTELLIGENCE, "high_confidence_product_published", "intelligence_product_detector", 1, ("Strategic Intelligence",), "strategic_synthesis_review"),
        "enterprise_health_failure": rule("enterprise_health_failure", EventDomain.ENTERPRISE, "enterprise_health_alert", "enterprise_health_detector", "alert", ("Executive",), "enterprise_recovery_review", EventSeverity.CRITICAL),
        "commander_directive": rule("commander_directive", EventDomain.COMMANDER, "commander_directive", "commander_policy_detector", "directive", ("Executive",), "commander_directed_review", EventSeverity.HIGH),
        "scheduled_mission_due": rule("scheduled_mission_due", EventDomain.SCHEDULE, "scheduled_mission_due", "schedule_boundary_detector", "due", ("Executive",), "scheduled_mission_review", EventSeverity.INFORMATIONAL, EventUrgency.ROUTINE, EventMateriality.MINOR),
    }


def _default_detector_health(rules: dict[str, DetectionRule]) -> dict[str, DetectorHealth]:
    detectors = {}
    for rule in rules.values():
        detectors[rule.detector_id] = DetectorHealth(rule.detector_id, rule.detector_id.replace("_", " ").title(), rule.domain, DetectorState.MONITORING, 30, "", "", 0, 0, 0, 0, 0, 0.0)
    return detectors


def _dedupe_key(candidate: CandidateEvent) -> str:
    return sha256(f"{candidate.domain.value}|{candidate.event_type}|{candidate.subject_id}|{candidate.source_record_id}".encode("utf-8")).hexdigest()[:24]


def _score_event(candidate: CandidateEvent, rule: DetectionRule, delta_percent: Decimal | None) -> tuple[EventSeverity, EventUrgency, EventMateriality]:
    severity = rule.default_severity
    urgency = rule.default_urgency
    materiality = rule.default_materiality
    numeric_threshold = _float_or_none(rule.critical_threshold if rule.critical_threshold not in {None, ""} else rule.trigger_threshold)
    if delta_percent is not None and numeric_threshold is not None and abs(float(delta_percent)) >= numeric_threshold:
        severity = EventSeverity.CRITICAL if severity != EventSeverity.EMERGENCY else severity
        urgency = EventUrgency.IMMEDIATE
        materiality = EventMateriality.MAJOR
    if candidate.domain in {EventDomain.POSITION, EventDomain.BROKER, EventDomain.ORDER, EventDomain.RISK}:
        urgency = EventUrgency.IMMEDIATE if urgency != EventUrgency.EMERGENCY else urgency
        materiality = EventMateriality.MAJOR if materiality not in {EventMateriality.ENTERPRISE_CRITICAL} else materiality
    return severity, urgency, materiality


def _request_type(event: ValidatedEvent) -> str:
    mapping = {
        EventDomain.POSITION: "position_threshold",
        EventDomain.RISK: "risk_review",
        EventDomain.ORDER: "order_status",
        EventDomain.BROKER: "broker_reconciliation",
        EventDomain.INTELLIGENCE: "strategic_theme_review",
        EventDomain.COMMANDER: "commander_directive",
        EventDomain.ENTERPRISE: "escalation",
    }
    return mapping.get(event.domain, "risk_review")


def _duty_officer(domain: EventDomain, offices: tuple[str, ...]) -> str:
    if domain in {EventDomain.POSITION, EventDomain.RISK, EventDomain.PORTFOLIO}:
        return "Risk"
    if domain in {EventDomain.ORDER, EventDomain.BROKER}:
        return "Trader"
    if domain == EventDomain.INTELLIGENCE:
        return "Strategic Intelligence"
    if domain == EventDomain.INFORMATION:
        return "Librarian"
    if domain in {EventDomain.ENTERPRISE, EventDomain.COMMANDER, EventDomain.SCHEDULE}:
        return "Executive"
    return offices[0] if offices else "Executive"


def _event_priority(event: ValidatedEvent) -> str:
    if event.domain in {EventDomain.POSITION, EventDomain.RISK, EventDomain.ORDER, EventDomain.BROKER}:
        return "Position Safety"
    if event.severity in {EventSeverity.CRITICAL, EventSeverity.EMERGENCY}:
        return "Emergency"
    return "Commander-Directed"


def _event_value(event: ValidatedEvent) -> float:
    if event.materiality == EventMateriality.ENTERPRISE_CRITICAL:
        return 100.0
    if event.materiality == EventMateriality.MAJOR:
        return 90.0
    if event.materiality == EventMateriality.MATERIAL:
        return 75.0
    return 35.0


def _delta(prior: Any, current: Any) -> Any:
    try:
        return round(float(current) - float(prior), 6)
    except (TypeError, ValueError):
        return {"from": prior, "to": current}


def _delta_percent(prior: Any, current: Any) -> Decimal | None:
    try:
        prior_f = float(prior)
        if prior_f == 0:
            return None
        return Decimal(str(round(((float(current) - prior_f) / prior_f) * 100, 6)))
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _decimal(value: Any) -> Decimal | None:
    if value in {None, ""}:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _parse_time(value: str) -> datetime:
    if not value:
        return datetime.now(UTC)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(UTC)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _max_severity(values: tuple[EventSeverity, ...]) -> EventSeverity:
    order = {item: index for index, item in enumerate(EventSeverity)}
    return max(values, key=lambda item: order[item])


def _max_materiality(values: tuple[EventMateriality, ...]) -> EventMateriality:
    order = {item: index for index, item in enumerate(EventMateriality)}
    return max(values, key=lambda item: order[item])


def _enum_values(item: Any) -> dict[str, Any]:
    output = {}
    for key, value in asdict(item).items():
        if isinstance(value, Enum):
            output[key] = value.value
        elif isinstance(value, tuple) and value and isinstance(value[0], Enum):
            output[key] = tuple(entry.value for entry in value)
    return output


def _snapshot_dataclass(item: Any) -> dict[str, Any]:
    return _json_safe(asdict(item))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, tuple):
        return tuple(_json_safe(item) for item in value)
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value


def _count_by(items: tuple[ValidatedEvent, ...], key_fn: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        key = key_fn(item)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _rule_with_threshold(rule: DetectionRule, threshold: Any) -> DetectionRule:
    return replace(rule, trigger_threshold=threshold, critical_threshold=threshold)


def _event_from_dict(item: dict[str, Any]) -> ValidatedEvent:
    data = dict(item)
    for key, enum_type in (("domain", EventDomain), ("severity", EventSeverity), ("urgency", EventUrgency), ("materiality", EventMateriality), ("status", EventStatus)):
        data[key] = enum_type(data[key])
    data["recommended_offices"] = tuple(data.get("recommended_offices", ()))
    data["financial_exposure"] = _decimal(data.get("financial_exposure"))
    data["estimated_downside"] = _decimal(data.get("estimated_downside"))
    data["delta_percent"] = _decimal(data.get("delta_percent"))
    return ValidatedEvent(**{key: data.get(key) for key in ValidatedEvent.__dataclass_fields__})
