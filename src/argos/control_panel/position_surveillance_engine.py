"""Deterministic surveillance for active ARGOS Position Objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .position_registry import PositionObject, PositionRegistry


@dataclass(frozen=True)
class PositionSurveillanceConfig:
    """Thresholds used by deterministic position surveillance."""

    target_approach_percent: float = 0.02
    stop_approach_percent: float = 0.02
    trailing_stop_approach_percent: float = 0.02
    large_move_percent: float = 0.03
    unusual_gain_percent: float = 0.05
    unusual_loss_percent: float = 0.05
    spread_widening_percent: float = 0.01
    volatility_spike_percent: float = 0.04
    risk_threshold: float = 0.75
    max_holding_minutes: int = 390
    max_holding_approach_percent: float = 0.9


@dataclass(frozen=True)
class PositionSurveillanceEvent:
    """Material deterministic event found during surveillance."""

    event_id: str
    position_id: str
    event_type: str
    severity: str
    timestamp: str
    evidence: dict[str, Any]


@dataclass(frozen=True)
class PositionEscalationRecord:
    """Escalation handoff for later exit evaluation engines."""

    escalation_id: str
    position_id: str
    event_type: str
    severity: str
    timestamp: str
    evidence: dict[str, Any]
    recommended_next_engine: str
    ai_review_may_be_justified: bool


@dataclass(frozen=True)
class PositionSurveillanceSnapshot:
    """Append-only record of one observed Position Object condition."""

    snapshot_id: str
    position_id: str
    workflow_id: str
    decision_object_id: str
    timestamp: str
    symbol: str
    asset_type: str
    quantity: float
    average_cost: float
    current_price: float
    current_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    stop_loss: float
    profit_target: float
    trailing_stop: float
    distance_to_stop: float
    distance_to_target: float
    time_in_trade: str
    market_session: str
    spread: float
    bid: float
    ask: float
    volume: float
    volatility: float
    risk_score: float
    thesis_health_score: float
    surveillance_status: str
    detected_events: tuple[str, ...]
    escalation_required: bool
    escalation_reason: str


class PositionSurveillanceEngine:
    """Single-pass deterministic surveillance of active positions."""

    def __init__(self, config: PositionSurveillanceConfig | None = None) -> None:
        self._config = config or PositionSurveillanceConfig()
        self._snapshots: list[PositionSurveillanceSnapshot] = []
        self._events: list[PositionSurveillanceEvent] = []
        self._escalations: list[PositionEscalationRecord] = []

    def surveil(
        self,
        *,
        position_registry: PositionRegistry,
        market_data_provider: dict[str, Any],
        timestamp_utc: str,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        mutate_registry: bool = True,
    ) -> dict[str, Any]:
        """Observe active positions once and return immediately."""
        config = self._resolved_config(enterprise_configuration_registry)
        active_positions = position_registry.active_positions()
        pass_snapshots: list[PositionSurveillanceSnapshot] = []
        pass_events: list[PositionSurveillanceEvent] = []
        pass_escalations: list[PositionEscalationRecord] = []
        quotes = _quotes_by_symbol(market_data_provider)
        market_session = _market_session(market_data_provider)

        for position in active_positions:
            quote = quotes.get(position.symbol.upper())
            if quote is None:
                snapshot, events, escalations = self._degraded_snapshot(position, timestamp_utc, market_session)
            else:
                updated = self._update_position(position_registry, position, quote, timestamp_utc) if mutate_registry else self._observed_position(position, quote, timestamp_utc)
                snapshot, events, escalations = self._surveillance_snapshot(updated, quote, market_session, timestamp_utc, config)
            self._snapshots.append(snapshot)
            self._events.extend(events)
            self._escalations.extend(escalations)
            pass_snapshots.append(snapshot)
            pass_events.extend(events)
            pass_escalations.extend(escalations)

        return self.snapshot(
            timestamp_utc=timestamp_utc,
            latest_snapshots=tuple(pass_snapshots),
            latest_events=tuple(pass_events),
            latest_escalations=tuple(pass_escalations),
            config=config,
            mutated_registry_this_pass=mutate_registry and bool(pass_snapshots),
        )

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        latest_snapshots: tuple[PositionSurveillanceSnapshot, ...] = (),
        latest_events: tuple[PositionSurveillanceEvent, ...] = (),
        latest_escalations: tuple[PositionEscalationRecord, ...] = (),
        config: PositionSurveillanceConfig | None = None,
        mutated_registry_this_pass: bool = False,
    ) -> dict[str, Any]:
        resolved = config or self._config
        return {
            "engineName": "Position Surveillance Engine",
            "engineeringOrder": "EO-XB",
            "constitutionalMission": "Maintain auditable, deterministic awareness of active capital at risk without deciding exits.",
            "lawVII": {
                "executesWorkflows": False,
                "workflowTokenOwnership": "NEVER",
                "placesTrades": False,
                "generatesInvestmentDecisions": False,
                "mutatesPositionsThroughRegistryOnly": True,
                "readOnlyObservationModeAvailable": True,
            },
            "lawVIII": {
                "routineAiCallsUsed": 0,
                "deterministicSurveillance": True,
                "aiReviewOnlyFlaggedForLaterEngines": True,
            },
            "configuration": asdict(resolved),
            "surveillanceSnapshots": tuple(asdict(item) for item in self._snapshots),
            "latestSnapshots": tuple(asdict(item) for item in latest_snapshots),
            "surveillanceEvents": tuple(asdict(item) for item in self._events),
            "latestEvents": tuple(asdict(item) for item in latest_events),
            "escalations": tuple(asdict(item) for item in self._escalations),
            "latestEscalations": tuple(asdict(item) for item in latest_escalations),
            "metrics": {
                "activePositionsSurveilled": len(latest_snapshots),
                "totalSnapshotCount": len(self._snapshots),
                "totalEventCount": len(self._events),
                "totalEscalationCount": len(self._escalations),
                "latestEscalationCount": len(latest_escalations),
            },
            "diagnostics": {
                "appendOnlySnapshots": True,
                "backgroundWorkerActive": False,
                "returnsImmediately": True,
                "aiCallsUsed": 0,
                "marketDataPath": "Market Data Provider Abstraction Layer normalizedObjects.quotes",
                "safeDegradationOnMissingData": True,
                "mutatedRegistryThisPass": mutated_registry_this_pass,
                "timestampUtc": timestamp_utc,
            },
        }

    def _update_position(self, registry: PositionRegistry, position: PositionObject, quote: dict[str, Any], timestamp: str) -> PositionObject:
        price = float(quote.get("last") or quote.get("current_price") or quote.get("price") or 0.0)
        time_in_trade = _time_in_trade(position.entry_time, timestamp)
        risk = _risk_score(position, price, self._config)
        confidence = _thesis_health(position, price)
        return registry.update_surveillance_state(
            position.position_id,
            current_price=price,
            time_in_trade=time_in_trade,
            current_risk=risk,
            current_confidence=confidence,
            reason="position surveillance state refresh",
            source="PositionSurveillanceEngine",
        )

    def _observed_position(self, position: PositionObject, quote: dict[str, Any], timestamp: str) -> PositionObject:
        """Return a surveillance-only position view without registry mutation."""
        price = float(quote.get("last") or quote.get("current_price") or quote.get("price") or 0.0)
        value = round(position.quantity * price, 4)
        risk = _risk_score(position, price, self._config)
        confidence = _thesis_health(position, price)
        return PositionObject(
            **{
                **asdict(position),
                "current_price": round(price, 4),
                "current_value": value,
                "unrealized_pnl": round((price - position.average_cost) * position.quantity, 4),
                "time_in_trade": _time_in_trade(position.entry_time, timestamp),
                "current_risk": risk,
                "current_confidence": confidence,
            }
        )

    def _surveillance_snapshot(
        self,
        position: PositionObject,
        quote: dict[str, Any],
        market_session: str,
        timestamp: str,
        config: PositionSurveillanceConfig,
    ) -> tuple[PositionSurveillanceSnapshot, tuple[PositionSurveillanceEvent, ...], tuple[PositionEscalationRecord, ...]]:
        current_price = float(quote.get("last") or position.current_price)
        bid = float(quote.get("bid") or 0.0)
        ask = float(quote.get("ask") or 0.0)
        spread = round(float(quote.get("spread") if quote.get("spread") is not None else max(0.0, ask - bid)), 4)
        volume = float(quote.get("volume") or 0.0)
        volatility = float(quote.get("volatility") or 0.0)
        distance_to_stop = round(current_price - position.stop_loss, 4) if position.stop_loss else 0.0
        distance_to_target = round(position.profit_target - current_price, 4) if position.profit_target else 0.0
        events = self._detect_events(position, current_price, spread, volatility, market_session, config)
        escalations = tuple(self._escalation(event) for event in events if event.severity in {"WARNING", "CRITICAL"})
        snapshot = PositionSurveillanceSnapshot(
            snapshot_id=f"PSS-{len(self._snapshots) + 1:06d}",
            position_id=position.position_id,
            workflow_id=position.workflow_id,
            decision_object_id=position.decision_object_id,
            timestamp=timestamp,
            symbol=position.symbol,
            asset_type=position.asset_type,
            quantity=position.quantity,
            average_cost=position.average_cost,
            current_price=round(current_price, 4),
            current_value=position.current_value,
            unrealized_pnl=position.unrealized_pnl,
            unrealized_pnl_percent=_pnl_percent(position),
            stop_loss=position.stop_loss,
            profit_target=position.profit_target,
            trailing_stop=position.trailing_stop,
            distance_to_stop=distance_to_stop,
            distance_to_target=distance_to_target,
            time_in_trade=position.time_in_trade,
            market_session=market_session,
            spread=spread,
            bid=bid,
            ask=ask,
            volume=volume,
            volatility=volatility,
            risk_score=position.current_risk,
            thesis_health_score=position.current_confidence,
            surveillance_status="DEGRADED" if any(event.event_type == "price_data_stale" for event in events) else "NOMINAL",
            detected_events=tuple(event.event_type for event in events),
            escalation_required=bool(escalations),
            escalation_reason=", ".join(event.event_type for event in escalations),
        )
        return snapshot, events, escalations

    def _degraded_snapshot(
        self,
        position: PositionObject,
        timestamp: str,
        market_session: str,
    ) -> tuple[PositionSurveillanceSnapshot, tuple[PositionSurveillanceEvent, ...], tuple[PositionEscalationRecord, ...]]:
        event = PositionSurveillanceEvent(
            event_id=f"PSE-{len(self._events) + 1:06d}",
            position_id=position.position_id,
            event_type="market_data_missing",
            severity="WARNING",
            timestamp=timestamp,
            evidence={"symbol": position.symbol, "reason": "No normalized quote available for active position."},
        )
        escalation = self._escalation(event)
        snapshot = PositionSurveillanceSnapshot(
            snapshot_id=f"PSS-{len(self._snapshots) + 1:06d}",
            position_id=position.position_id,
            workflow_id=position.workflow_id,
            decision_object_id=position.decision_object_id,
            timestamp=timestamp,
            symbol=position.symbol,
            asset_type=position.asset_type,
            quantity=position.quantity,
            average_cost=position.average_cost,
            current_price=position.current_price,
            current_value=position.current_value,
            unrealized_pnl=position.unrealized_pnl,
            unrealized_pnl_percent=_pnl_percent(position),
            stop_loss=position.stop_loss,
            profit_target=position.profit_target,
            trailing_stop=position.trailing_stop,
            distance_to_stop=0.0,
            distance_to_target=0.0,
            time_in_trade=position.time_in_trade,
            market_session=market_session,
            spread=0.0,
            bid=0.0,
            ask=0.0,
            volume=0.0,
            volatility=0.0,
            risk_score=position.current_risk,
            thesis_health_score=position.current_confidence,
            surveillance_status="DEGRADED",
            detected_events=(event.event_type,),
            escalation_required=True,
            escalation_reason=event.event_type,
        )
        return snapshot, (event,), (escalation,)

    def _detect_events(
        self,
        position: PositionObject,
        current_price: float,
        spread: float,
        volatility: float,
        market_session: str,
        config: PositionSurveillanceConfig,
    ) -> tuple[PositionSurveillanceEvent, ...]:
        events: list[PositionSurveillanceEvent] = []
        pnl_percent = _pnl_percent(position)

        def add(event_type: str, severity: str, evidence: dict[str, Any]) -> None:
            events.append(PositionSurveillanceEvent(f"PSE-{len(self._events) + len(events) + 1:06d}", position.position_id, event_type, severity, utc_timestamp(), evidence))

        if position.profit_target:
            if current_price >= position.profit_target:
                add("profit_target_reached", "CRITICAL", {"currentPrice": current_price, "profitTarget": position.profit_target})
            elif _within_percent(current_price, position.profit_target, config.target_approach_percent):
                add("profit_target_approached", "WARNING", {"currentPrice": current_price, "profitTarget": position.profit_target})
        if position.stop_loss:
            if current_price <= position.stop_loss:
                add("stop_loss_reached", "CRITICAL", {"currentPrice": current_price, "stopLoss": position.stop_loss})
            elif _within_percent(current_price, position.stop_loss, config.stop_approach_percent):
                add("stop_loss_approached", "WARNING", {"currentPrice": current_price, "stopLoss": position.stop_loss})
        if position.trailing_stop:
            if current_price <= position.trailing_stop:
                add("trailing_stop_reached", "CRITICAL", {"currentPrice": current_price, "trailingStop": position.trailing_stop})
            elif _within_percent(current_price, position.trailing_stop, config.trailing_stop_approach_percent):
                add("trailing_stop_approached", "WARNING", {"currentPrice": current_price, "trailingStop": position.trailing_stop})
        if pnl_percent <= -config.large_move_percent:
            add("large_adverse_move", "WARNING", {"unrealizedPnlPercent": pnl_percent})
        if pnl_percent >= config.large_move_percent:
            add("large_favorable_move", "NOTICE", {"unrealizedPnlPercent": pnl_percent})
        if pnl_percent <= -config.unusual_loss_percent:
            add("unusual_unrealized_loss", "CRITICAL", {"unrealizedPnlPercent": pnl_percent})
        if pnl_percent >= config.unusual_gain_percent:
            add("unusual_unrealized_gain", "WARNING", {"unrealizedPnlPercent": pnl_percent})
        if volatility >= config.volatility_spike_percent:
            add("volatility_spike", "WARNING", {"volatility": volatility})
        if current_price and spread / current_price >= config.spread_widening_percent:
            add("spread_widening", "WARNING", {"spread": spread, "currentPrice": current_price})
        if market_session.upper() not in {"OPEN", "PAPER_OPEN"}:
            add("market_closed", "NOTICE", {"marketSession": market_session})
        if position.current_risk >= config.risk_threshold:
            add("risk_threshold_exceeded", "WARNING", {"riskScore": position.current_risk, "threshold": config.risk_threshold})
        if _minutes_in_trade(position.time_in_trade) >= config.max_holding_minutes * config.max_holding_approach_percent:
            add("max_holding_time_approached", "WARNING", {"timeInTrade": position.time_in_trade, "maxHoldingMinutes": config.max_holding_minutes})
        return tuple(events)

    def _escalation(self, event: PositionSurveillanceEvent) -> PositionEscalationRecord:
        ai_review = event.event_type in {"volatility_spike", "risk_threshold_exceeded", "unusual_unrealized_loss"}
        return PositionEscalationRecord(
            escalation_id=f"PSESC-{len(self._escalations) + 1:06d}",
            position_id=event.position_id,
            event_type=event.event_type,
            severity=event.severity,
            timestamp=event.timestamp,
            evidence=event.evidence,
            recommended_next_engine="EO-XC Position Exit Evaluation Engine",
            ai_review_may_be_justified=ai_review,
        )

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None) -> PositionSurveillanceConfig:
        if not enterprise_configuration_registry:
            return self._config
        entries = enterprise_configuration_registry.get("configurationRegistry", ())
        values = asdict(self._config)
        name_map = {
            "Position Surveillance Target Approach Percent": "target_approach_percent",
            "Position Surveillance Stop Approach Percent": "stop_approach_percent",
            "Position Surveillance Large Move Percent": "large_move_percent",
            "Position Surveillance Risk Threshold": "risk_threshold",
            "Position Surveillance Max Holding Minutes": "max_holding_minutes",
        }
        for entry in entries:
            key = name_map.get(str(entry.get("configurationName", "")))
            if key:
                try:
                    values[key] = type(values[key])(entry.get("configuredValue"))
                except (TypeError, ValueError):
                    continue
        return PositionSurveillanceConfig(**values)


def _quotes_by_symbol(provider: dict[str, Any]) -> dict[str, dict[str, Any]]:
    quotes = provider.get("normalizedObjects", {}).get("quotes", ())
    return {str(quote.get("symbol", "")).upper(): quote for quote in quotes if isinstance(quote, dict) and quote.get("symbol")}


def _market_session(provider: dict[str, Any]) -> str:
    statuses = provider.get("normalizedObjects", {}).get("marketStatus", ())
    if statuses and isinstance(statuses[0], dict):
        return str(statuses[0].get("status", "UNKNOWN"))
    return "UNKNOWN"


def _time_in_trade(entry_time: str, timestamp: str) -> str:
    try:
        entry = datetime.fromisoformat(entry_time.replace("Z", "+00:00"))
        current = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        minutes = max(0, int((current - entry).total_seconds() // 60))
        return f"{minutes}m"
    except ValueError:
        return "0m"


def _minutes_in_trade(value: str) -> int:
    if value.endswith("m"):
        try:
            return int(value[:-1])
        except ValueError:
            return 0
    return 0


def _risk_score(position: PositionObject, current_price: float, config: PositionSurveillanceConfig) -> float:
    pnl_percent = (current_price - position.average_cost) / max(1.0, position.average_cost)
    stop_pressure = 0.0
    if position.stop_loss and current_price > position.stop_loss:
        stop_pressure = max(0.0, 1.0 - ((current_price - position.stop_loss) / max(1.0, current_price * config.stop_approach_percent * 5)))
    return round(min(1.0, max(0.0, position.current_risk + abs(min(0.0, pnl_percent)) + stop_pressure * 0.2)), 4)


def _thesis_health(position: PositionObject, current_price: float) -> float:
    pnl_percent = (current_price - position.average_cost) / max(1.0, position.average_cost)
    return round(min(1.0, max(0.0, position.current_confidence + pnl_percent)), 4)


def _pnl_percent(position: PositionObject) -> float:
    basis = max(1.0, position.average_cost * position.quantity)
    return round(position.unrealized_pnl / basis, 6)


def _within_percent(current: float, target: float, percent: float) -> bool:
    if target <= 0:
        return False
    return abs(target - current) / target <= percent
