"""Position Monitoring Network for ARGOS EO-CK."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp


class PositionWatcherType(str, Enum):
    STOP_LOSS = "stop_loss"
    PROFIT_TARGET = "profit_target"
    TRAILING_STOP = "trailing_stop"
    DRAWDOWN = "drawdown"
    EARNINGS_PROXIMITY = "earnings_proximity"
    VOLATILITY = "volatility"
    HOLDING_PERIOD = "holding_period"
    BROKER_STATE = "broker_state"
    RISK_TRIGGER = "risk_trigger"
    DATA_QUALITY = "data_quality"


class WatcherStatus(str, Enum):
    DORMANT = "dormant"
    WATCHING = "watching"
    DEGRADED = "degraded"
    TRIGGERED = "triggered"
    BLOCKED = "blocked"


class MonitoringEventSeverity(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class PositionWatcher:
    watcher_id: str
    watcher_type: PositionWatcherType
    position_id: str
    symbol: str
    threshold: float
    last_value: float
    status: WatcherStatus
    last_checked_at: str
    explanation: str


@dataclass(frozen=True)
class PositionMonitoringEvent:
    monitoring_event_id: str
    watcher_id: str
    watcher_type: PositionWatcherType
    position_id: str
    symbol: str
    event_type: str
    severity: MonitoringEventSeverity
    urgency: str
    materiality: str
    observed_value: float
    threshold_value: float
    distance_to_threshold: float
    source_record_id: str
    evidence: dict[str, Any]
    created_at: str
    content_hash: str


@dataclass(frozen=True)
class PositionMonitoringPass:
    monitoring_pass_id: str
    generated_at: str
    active_position_count: int
    watcher_count: int
    event_count: int
    degraded_watcher_count: int
    event_detection_feed_count: int
    content_hash: str


class PositionMonitoringNetwork:
    """Lightweight deterministic watchers for open positions; emits events only."""

    def __init__(self) -> None:
        self._watchers: dict[str, PositionWatcher] = {}
        self._events: list[PositionMonitoringEvent] = []
        self._passes: list[PositionMonitoringPass] = []
        self._audit: list[dict[str, Any]] = []
        self._dead_letters: list[dict[str, Any]] = []

    def scan(
        self,
        *,
        position_registry: dict[str, Any],
        market_data_provider: dict[str, Any],
        performance_truth: dict[str, Any] | None = None,
        timestamp_utc: str | None = None,
    ) -> dict[str, Any]:
        """Run one bounded watcher pass and return immediately."""
        timestamp = timestamp_utc or utc_timestamp()
        active_positions = tuple(position_registry.get("activePositions", ()) or ())
        quotes = _quotes_by_symbol(market_data_provider)
        broker_orders = tuple((performance_truth or {}).get("orderLedger", ()) or ())
        pass_events: list[PositionMonitoringEvent] = []
        degraded = 0
        for position in active_positions:
            quote = quotes.get(str(position.get("symbol", "")).upper())
            watchers, events = self._evaluate_position(position, quote, broker_orders, timestamp)
            for watcher in watchers:
                if watcher.status == WatcherStatus.DEGRADED:
                    degraded += 1
                self._watchers[watcher.watcher_id] = watcher
            self._events.extend(events)
            pass_events.extend(events)
        monitoring_pass = PositionMonitoringPass(
            f"PMN-PASS-{len(self._passes) + 1:06d}",
            timestamp,
            len(active_positions),
            len(self._watchers),
            len(pass_events),
            degraded,
            len(pass_events),
            "",
        )
        self._passes.append(_hash_pass(monitoring_pass))
        self._audit_event("monitoring_pass_completed", monitoring_pass.monitoring_pass_id, f"{len(pass_events)} events emitted for EO-CC.")
        return self.snapshot(latest_events=tuple(pass_events), timestamp_utc=timestamp)

    def snapshot(self, *, latest_events: tuple[PositionMonitoringEvent, ...] = (), timestamp_utc: str | None = None) -> dict[str, Any]:
        latest_pass = self._passes[-1] if self._passes else None
        return {
            "networkName": "Position Monitoring Network",
            "engineeringOrder": "EO-CK",
            "status": "DEGRADED" if any(item.status == WatcherStatus.DEGRADED for item in self._watchers.values()) else "WATCHING",
            "summary": {
                "activeWatchers": sum(1 for item in self._watchers.values() if item.status in {WatcherStatus.WATCHING, WatcherStatus.TRIGGERED}),
                "degradedWatchers": sum(1 for item in self._watchers.values() if item.status == WatcherStatus.DEGRADED),
                "triggeredWatchers": sum(1 for item in self._watchers.values() if item.status == WatcherStatus.TRIGGERED),
                "eventsEmitted": len(self._events),
                "latestEvents": len(latest_events),
                "activePositionsMonitored": latest_pass.active_position_count if latest_pass else 0,
            },
            "watcherRoster": tuple(_public(item) for item in sorted(self._watchers.values(), key=lambda item: (item.position_id, item.watcher_type.value))),
            "monitoringEvents": tuple(_public(item) for item in self._events[-80:]),
            "latestMonitoringEvents": tuple(_public(item) for item in latest_events),
            "monitoringPasses": tuple(_public(item) for item in self._passes[-20:]),
            "eventDetectionFeed": tuple(_event_detection_feed(item) for item in latest_events),
            "watcherCoverage": self._coverage(),
            "auditHistory": tuple(self._audit[-50:]),
            "deadLetters": tuple(self._dead_letters[-20:]),
            "lawCK": {
                "producesEventsOnly": True,
                "wakesOffices": False,
                "authorizesMissions": False,
                "placesTrades": False,
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "routineAiInvocations": 0,
                "returnsImmediately": True,
                "uncontrolledLoopsCreated": False,
                "feedsEOCC": True,
            },
            "integrationFeeds": {
                "eoCC": {"eventDetectionFeedAvailable": True, "eventsProduced": len(latest_events)},
                "eoCJ": {"positionSafetySignalsAvailable": True},
                "eoCA": {"directSchedulerAuthority": False},
            },
            "diagnostics": {"timestampUtc": timestamp_utc or utc_timestamp(), "backgroundWorkerActive": False, "restartRecovery": True},
        }

    def recover_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._watchers = {}
        self._events = []
        self._passes = []
        for item in snapshot.get("watcherRoster", ()):
            watcher = _watcher_from_public(item)
            self._watchers[watcher.watcher_id] = watcher
        for item in snapshot.get("monitoringEvents", ()):
            self._events.append(_event_from_public(item))
        for item in snapshot.get("monitoringPasses", ()):
            self._passes.append(_pass_from_public(item))
        self._audit_event("restart_recovery", "EO-CK", "Position Monitoring Network restored from snapshot.")

    def replay(self, *, position_registry: dict[str, Any], market_data_provider: dict[str, Any], performance_truth: dict[str, Any] | None = None) -> dict[str, Any]:
        engine = PositionMonitoringNetwork()
        result = engine.scan(position_registry=position_registry, market_data_provider=market_data_provider, performance_truth=performance_truth or {}, timestamp_utc=utc_timestamp())
        result["replayMode"] = True
        result["productionMutation"] = False
        return result

    def _evaluate_position(self, position: dict[str, Any], quote: dict[str, Any] | None, broker_orders: tuple[dict[str, Any], ...], timestamp: str) -> tuple[tuple[PositionWatcher, ...], tuple[PositionMonitoringEvent, ...]]:
        position_id = str(position.get("position_id", position.get("positionId", "")))
        symbol = str(position.get("symbol", "")).upper()
        current_price = _float(quote.get("last") if quote else position.get("current_price", position.get("currentPrice", 0)))
        average_cost = _float(position.get("average_cost", position.get("averageCost", 0)))
        quantity = _float(position.get("quantity", 0))
        current_value = _float(position.get("current_value", position.get("currentValue", current_price * quantity)))
        stop_loss = _float(position.get("stop_loss", position.get("stopLoss", 0)))
        profit_target = _float(position.get("profit_target", position.get("profitTarget", 0)))
        trailing_stop = _float(position.get("trailing_stop", position.get("trailingStop", 0)))
        risk = _float(position.get("current_risk", position.get("currentRisk", 0)))
        time_in_trade = str(position.get("time_in_trade", position.get("timeInTrade", "0m")))
        watchers: list[PositionWatcher] = []
        events: list[PositionMonitoringEvent] = []

        def watcher(watcher_type: PositionWatcherType, threshold: float, observed: float, explanation: str, degraded: bool = False) -> PositionWatcher:
            status = WatcherStatus.DEGRADED if degraded else WatcherStatus.WATCHING
            return PositionWatcher(f"PMN-W-{position_id}-{watcher_type.value}", watcher_type, position_id, symbol, round(threshold, 4), round(observed, 4), status, timestamp, explanation)

        def emit(w: PositionWatcher, event_type: str, severity: MonitoringEventSeverity, urgency: str, materiality: str, observed: float, threshold: float, evidence: dict[str, Any]) -> None:
            status = WatcherStatus.DEGRADED if w.status == WatcherStatus.DEGRADED else WatcherStatus.TRIGGERED
            triggered = replace(w, status=status, last_value=round(observed, 4), last_checked_at=timestamp)
            watchers[watchers.index(w)] = triggered
            event = PositionMonitoringEvent(
                f"PMN-EVT-{len(self._events) + len(events) + 1:06d}",
                triggered.watcher_id,
                triggered.watcher_type,
                position_id,
                symbol,
                event_type,
                severity,
                urgency,
                materiality,
                round(observed, 4),
                round(threshold, 4),
                round(observed - threshold, 4),
                position_id,
                evidence,
                timestamp,
                "",
            )
            events.append(_hash_event(event))

        data_watcher = watcher(PositionWatcherType.DATA_QUALITY, 1.0, 0.0 if quote is None else 1.0, "Market quote availability for active position.", degraded=quote is None)
        watchers.append(data_watcher)
        if quote is None:
            emit(data_watcher, "position_market_data_missing", MonitoringEventSeverity.HIGH, "immediate", "major", 0.0, 1.0, {"symbol": symbol, "positionId": position_id})
            return tuple(watchers), tuple(events)

        if stop_loss:
            w = watcher(PositionWatcherType.STOP_LOSS, stop_loss, current_price, "Stop-loss watcher.")
            watchers.append(w)
            if current_price <= stop_loss:
                emit(w, "position_stop_loss_breached", MonitoringEventSeverity.CRITICAL, "immediate", "major", current_price, stop_loss, {"stopLoss": stop_loss, "currentPrice": current_price, "currentValue": current_value})
            elif current_price <= stop_loss * 1.02:
                emit(w, "position_stop_loss_approaching", MonitoringEventSeverity.HIGH, "immediate", "material", current_price, stop_loss, {"stopLoss": stop_loss, "currentPrice": current_price})
        if profit_target:
            w = watcher(PositionWatcherType.PROFIT_TARGET, profit_target, current_price, "Profit-target watcher.")
            watchers.append(w)
            if current_price >= profit_target:
                emit(w, "position_profit_target_reached", MonitoringEventSeverity.HIGH, "prompt", "material", current_price, profit_target, {"profitTarget": profit_target, "currentPrice": current_price})
            elif current_price >= profit_target * 0.98:
                emit(w, "position_profit_target_approaching", MonitoringEventSeverity.MODERATE, "prompt", "material", current_price, profit_target, {"profitTarget": profit_target, "currentPrice": current_price})
        if trailing_stop:
            w = watcher(PositionWatcherType.TRAILING_STOP, trailing_stop, current_price, "Trailing-stop watcher.")
            watchers.append(w)
            if current_price <= trailing_stop:
                emit(w, "position_trailing_stop_breached", MonitoringEventSeverity.CRITICAL, "immediate", "major", current_price, trailing_stop, {"trailingStop": trailing_stop, "currentPrice": current_price})
        drawdown_threshold = average_cost * 0.95 if average_cost else 0.0
        w = watcher(PositionWatcherType.DRAWDOWN, drawdown_threshold, current_price, "Unrealized drawdown watcher.")
        watchers.append(w)
        if average_cost and current_price <= drawdown_threshold:
            emit(w, "position_drawdown_threshold_breached", MonitoringEventSeverity.HIGH, "immediate", "material", current_price, drawdown_threshold, {"averageCost": average_cost, "currentPrice": current_price})
        volatility = _float(quote.get("volatility", 0))
        w = watcher(PositionWatcherType.VOLATILITY, 0.04, volatility, "Volatility spike watcher.")
        watchers.append(w)
        if volatility >= 0.04:
            emit(w, "position_volatility_spike", MonitoringEventSeverity.HIGH, "prompt", "material", volatility, 0.04, {"volatility": volatility, "symbol": symbol})
        w = watcher(PositionWatcherType.HOLDING_PERIOD, 360.0, float(_minutes_in_trade(time_in_trade)), "Holding-period watcher.")
        watchers.append(w)
        if _minutes_in_trade(time_in_trade) >= 360:
            emit(w, "position_holding_period_limit_approaching", MonitoringEventSeverity.MODERATE, "prompt", "material", float(_minutes_in_trade(time_in_trade)), 360.0, {"timeInTrade": time_in_trade})
        w = watcher(PositionWatcherType.RISK_TRIGGER, 0.75, risk, "Position risk-score watcher.")
        watchers.append(w)
        if risk >= 0.75:
            emit(w, "position_risk_threshold_breached", MonitoringEventSeverity.HIGH, "immediate", "major", risk, 0.75, {"riskScore": risk})
        related_orders = tuple(order for order in broker_orders if str(order.get("symbol", "")).upper() == symbol and str(order.get("status", "")).upper() in {"REJECTED", "QUEUED", "PARTIALLY_FILLED"})
        w = watcher(PositionWatcherType.BROKER_STATE, 0.0, float(len(related_orders)), "Open broker/order state watcher.")
        watchers.append(w)
        if related_orders:
            emit(w, "position_broker_state_attention", MonitoringEventSeverity.HIGH, "immediate", "major", float(len(related_orders)), 0.0, {"orderCount": len(related_orders), "statuses": tuple(order.get("status", "") for order in related_orders)})
        w = watcher(PositionWatcherType.EARNINGS_PROXIMITY, 0.0, 0.0, "Earnings proximity watcher awaits corporate calendar feed.")
        watchers.append(w)
        return tuple(watchers), tuple(events)

    def _coverage(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        positions = set()
        for watcher in self._watchers.values():
            by_type[watcher.watcher_type.value] = by_type.get(watcher.watcher_type.value, 0) + 1
            positions.add(watcher.position_id)
        return {"positionsWithWatchers": len(positions), "watchersByType": by_type, "expectedWatcherTypes": tuple(item.value for item in PositionWatcherType)}

    def _audit_event(self, action: str, record_id: str, reason: str) -> None:
        self._audit.append({"auditId": f"PMN-AUD-{len(self._audit) + 1:06d}", "timestamp": utc_timestamp(), "action": action, "recordId": record_id, "reason": reason})


def _quotes_by_symbol(provider: dict[str, Any]) -> dict[str, dict[str, Any]]:
    quotes = provider.get("normalizedObjects", {}).get("quotes", ())
    return {str(quote.get("symbol", "")).upper(): quote for quote in quotes if isinstance(quote, dict) and quote.get("symbol")}


def _event_detection_feed(event: PositionMonitoringEvent) -> dict[str, Any]:
    return {
        "source": "PositionMonitoringNetwork",
        "source_event_id": event.monitoring_event_id,
        "domain": "position",
        "event_type": event.event_type,
        "subject_type": "position",
        "subject_id": event.position_id,
        "ticker": event.symbol,
        "position_id": event.position_id,
        "severity": event.severity.value,
        "urgency": event.urgency,
        "materiality": event.materiality,
        "financial_exposure": event.evidence.get("currentValue", 0.0),
        "summary": f"{event.symbol} {event.event_type}",
        "evidence": event.evidence,
        "created_at": event.created_at,
    }


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _minutes_in_trade(value: str) -> int:
    if value.endswith("m"):
        try:
            return int(value[:-1])
        except ValueError:
            return 0
    return 0


def _hash_event(event: PositionMonitoringEvent) -> PositionMonitoringEvent:
    return replace(event, content_hash=_hash(_public(replace(event, content_hash=""))))


def _hash_pass(item: PositionMonitoringPass) -> PositionMonitoringPass:
    return replace(item, content_hash=_hash(_public(replace(item, content_hash=""))))


def _hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _public(item: Any) -> dict[str, Any]:
    raw = asdict(item) if hasattr(item, "__dataclass_fields__") else item
    return _json_value(raw)


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return tuple(_json_value(item) for item in value)
    if isinstance(value, dict):
        return {str(_json_value(key)): _json_value(item) for key, item in value.items()}
    return value


def _watcher_from_public(item: dict[str, Any]) -> PositionWatcher:
    data = dict(item)
    data["watcher_type"] = PositionWatcherType(data["watcher_type"])
    data["status"] = WatcherStatus(data["status"])
    return PositionWatcher(**{key: data.get(key) for key in PositionWatcher.__dataclass_fields__})


def _event_from_public(item: dict[str, Any]) -> PositionMonitoringEvent:
    data = dict(item)
    data["watcher_type"] = PositionWatcherType(data["watcher_type"])
    data["severity"] = MonitoringEventSeverity(data["severity"])
    return PositionMonitoringEvent(**{key: data.get(key) for key in PositionMonitoringEvent.__dataclass_fields__})


def _pass_from_public(item: dict[str, Any]) -> PositionMonitoringPass:
    return PositionMonitoringPass(**{key: item.get(key) for key in PositionMonitoringPass.__dataclass_fields__})
