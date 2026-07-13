"""Closed Position Truth records and lifecycle analytics for ARGOS EO-XE."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp


@dataclass(frozen=True)
class ClosedPositionTruthConfig:
    """Configuration for closed position truth creation."""

    enabled: bool = True
    require_benchmark_data: bool = False
    require_attribution_payload: bool = False
    allow_degraded_truth_creation: bool = False
    duplicate_truth_policy: str = "return_existing"
    lifecycle_analytics_enabled: bool = True
    learning_event_enabled: bool = False
    reconciliation_strictness: str = "strict"
    benchmark_defaults: tuple[str, ...] = ("SPY", "QQQ", "Cash")
    execution_quality_scoring_enabled: bool = True


@dataclass(frozen=True)
class ClosedPositionTruthRecord:
    """Immutable scientific observation of a completed position lifecycle."""

    closed_position_truth_id: str
    position_id: str
    workflow_id: str
    decision_object_id: str
    symbol: str
    asset_type: str
    side: str
    quantity_opened: float
    quantity_closed: float
    entry_time: str
    exit_time: str
    holding_period: str
    entry_price_average: float
    exit_price_average: float
    gross_realized_pnl: float
    net_realized_pnl: float
    realized_pnl_percent: float
    max_unrealized_gain: float
    max_unrealized_loss: float
    max_drawdown_during_trade: float
    distance_from_target_at_exit: float
    distance_from_stop_at_exit: float
    average_spread_paid: float
    total_slippage_cost: float
    execution_quality_score: float
    surveillance_event_count: int
    exit_timing_quality: float
    risk_adjusted_outcome: float
    entry_execution_ids: tuple[str, ...]
    exit_execution_ids: tuple[str, ...]
    surveillance_snapshot_ids: tuple[str, ...]
    exit_decision_id: str
    entry_thesis: str
    exit_reason: str
    lifecycle_summary: str
    benchmark_return: float
    alpha_vs_benchmark: float
    benchmark_payload: dict[str, Any]
    attribution_payload: dict[str, Any]
    learning_payload: dict[str, Any]
    audit_reference: str
    created_at: str
    hash: str


@dataclass(frozen=True)
class DegradedClosedPositionAnalyticalRecord:
    """Analytical-only lifecycle output that is not authoritative truth."""

    analytical_record_id: str
    position_id: str
    reason: str
    benchmark_payload: dict[str, Any]
    attribution_payload: dict[str, Any]
    truth_classification: str
    certification_status: str
    learning_promotion_allowed: bool
    created_at: str


class ClosedPositionTruthBuilder:
    """Build append-only Closed Position Truth records from completed positions."""

    def __init__(self, config: ClosedPositionTruthConfig | None = None) -> None:
        self._config = config or ClosedPositionTruthConfig()
        self._records: list[ClosedPositionTruthRecord] = []
        self._records_by_position: dict[str, ClosedPositionTruthRecord] = {}
        self._reconciliation_events: list[dict[str, Any]] = []
        self._learning_events: list[dict[str, Any]] = []
        self._degraded_analytical_records: list[DegradedClosedPositionAnalyticalRecord] = []

    def build(
        self,
        *,
        position_registry: dict[str, Any],
        performance_truth: dict[str, Any],
        position_surveillance: dict[str, Any],
        exit_decision_engine: dict[str, Any],
        enterprise_benchmark_engine: dict[str, Any] | None = None,
        trade_attribution_engine: dict[str, Any] | None = None,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        timestamp_utc: str,
    ) -> dict[str, Any]:
        """Create truth records for eligible closed positions once."""
        config = self._resolved_config(enterprise_configuration_registry)
        if not config.enabled:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_records=(), config=config)
        latest_records: list[ClosedPositionTruthRecord] = []
        for position in position_registry.get("allPositions", ()):
            position_id = str(position.get("position_id", ""))
            if position_id in self._records_by_position:
                continue
            record = self._build_one(
                position=position,
                performance_truth=performance_truth,
                position_surveillance=position_surveillance,
                exit_decision_engine=exit_decision_engine,
                enterprise_benchmark_engine=enterprise_benchmark_engine or {},
                trade_attribution_engine=trade_attribution_engine or {},
                config=config,
                timestamp=timestamp_utc,
            )
            if record:
                self._records.append(record)
                self._records_by_position[position_id] = record
                latest_records.append(record)
                if config.learning_event_enabled:
                    self._learning_events.append(_learning_event(record))
        return self.snapshot(timestamp_utc=timestamp_utc, latest_records=tuple(latest_records), config=config)

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        latest_records: tuple[ClosedPositionTruthRecord, ...] = (),
        config: ClosedPositionTruthConfig | None = None,
    ) -> dict[str, Any]:
        resolved = config or self._config
        return {
            "engineName": "Closed Position Truth Builder",
            "engineeringOrder": "EO-XE",
            "constitutionalMission": "Convert complete closed position lifecycles into immutable learning-grade truth records.",
            "configuration": asdict(resolved),
            "closedPositionTruthRecords": tuple(asdict(item) for item in self._records),
            "latestClosedPositionTruthRecords": tuple(asdict(item) for item in latest_records),
            "degradedAnalyticalRecords": tuple(asdict(item) for item in self._degraded_analytical_records),
            "reconciliationEvents": tuple(self._reconciliation_events),
            "learningEvents": tuple(self._learning_events),
            "metrics": {
                "truthRecordCount": len(self._records),
                "latestTruthRecordCount": len(latest_records),
                "degradedAnalyticalRecordCount": len(self._degraded_analytical_records),
                "reconciliationEventCount": len(self._reconciliation_events),
                "learningEventCount": len(self._learning_events),
            },
            "diagnostics": {
                "appendOnly": True,
                "idempotent": True,
                "backgroundWorkerActive": False,
                "returnsImmediately": True,
                "aiCallsUsed": 0,
                "timestampUtc": timestamp_utc,
            },
            "lawVII": {
                "executesWorkflows": False,
                "ownsWorkflowTokens": False,
                "placesTrades": False,
                "mutatesPositionObjects": False,
                "responsibility": "CLOSED_POSITION_TRUTH_ONLY",
            },
            "lawVIII": {
                "routineAiCallsUsed": 0,
                "deterministicLifecycleAnalytics": True,
                "aiInterpretationDeferred": True,
            },
        }

    def _build_one(
        self,
        *,
        position: dict[str, Any],
        performance_truth: dict[str, Any],
        position_surveillance: dict[str, Any],
        exit_decision_engine: dict[str, Any],
        enterprise_benchmark_engine: dict[str, Any],
        trade_attribution_engine: dict[str, Any],
        config: ClosedPositionTruthConfig,
        timestamp: str,
    ) -> ClosedPositionTruthRecord | None:
        position_id = str(position.get("position_id", ""))
        if position.get("lifecycle_status") != "closed":
            self._reconcile(position_id, "position_not_closed", "Closed Position Truth requires lifecycle_status=closed.", position)
            return None
        if float(position.get("quantity", 0.0) or 0.0) != 0.0:
            self._reconcile(position_id, "closed_position_has_quantity", "Position is marked closed but open quantity remains.", position)
            return None

        symbol = str(position.get("symbol", ""))
        decision_id = str(position.get("decision_object_id", ""))
        orders = tuple(
            order
            for order in performance_truth.get("orderLedger", ())
            if order.get("symbol") == symbol and order.get("decision_object_id") == decision_id and order.get("status") in {"FILLED", "PARTIALLY_FILLED", "SETTLED"}
        )
        entry_orders = tuple(order for order in orders if order.get("side") == "BUY" and float(order.get("filled_quantity", 0.0) or 0.0) > 0)
        exit_orders = tuple(order for order in orders if order.get("side") == "SELL" and float(order.get("filled_quantity", 0.0) or 0.0) > 0)
        if not entry_orders:
            self._reconcile(position_id, "missing_entry_execution", "No filled entry execution was found.", {"symbol": symbol, "decisionObjectId": decision_id})
            return None
        if not exit_orders:
            self._reconcile(position_id, "missing_exit_execution", "No filled exit execution was found.", {"symbol": symbol, "decisionObjectId": decision_id})
            return None

        quantity_opened = round(sum(float(order.get("filled_quantity", 0.0) or 0.0) for order in entry_orders), 4)
        quantity_closed = round(sum(float(order.get("filled_quantity", 0.0) or 0.0) for order in exit_orders), 4)
        if abs(quantity_opened - quantity_closed) > 0.0001:
            self._reconcile(position_id, "quantity_mismatch", "Opened and closed quantities do not match.", {"opened": quantity_opened, "closed": quantity_closed})
            return None

        entry_price = _weighted_average(entry_orders)
        exit_price = _weighted_average(exit_orders)
        gross_pnl = round((exit_price - entry_price) * quantity_closed, 4)
        net_pnl = round(sum(float(order.get("realized_profit_loss", 0.0) or 0.0) for order in exit_orders), 4)
        if abs(net_pnl - round(gross_pnl - sum(float(order.get("slippage", 0.0) or 0.0) for order in exit_orders), 4)) > 0.05:
            self._reconcile(position_id, "realized_pnl_mismatch", "Realized P/L does not reconcile to executions.", {"gross": gross_pnl, "net": net_pnl})
            return None

        snapshots = _surveillance_for_position(position_surveillance, position_id)
        exit_decision = _exit_decision_for_position(exit_decision_engine, position_id)
        benchmark = _benchmark_payload(enterprise_benchmark_engine, position, net_pnl, entry_price, quantity_opened, config)
        if benchmark["status"] == "DEGRADED" and config.require_benchmark_data:
            self._reconcile(position_id, "benchmark_data_missing", "Benchmark data is required but unavailable.", benchmark)
            return None

        attribution = _attribution_payload(trade_attribution_engine, position, exit_decision, benchmark, net_pnl)
        if attribution["status"] == "DEGRADED" and config.require_attribution_payload:
            self._reconcile(position_id, "attribution_payload_missing", "Attribution payload is required but unavailable.", attribution)
            return None
        if (benchmark["status"] == "DEGRADED" or attribution["status"] == "DEGRADED") and not config.allow_degraded_truth_creation:
            self._record_degraded_analytical(position_id, benchmark, attribution, timestamp)
            return None

        entry_time = str(entry_orders[0].get("timestamp", position.get("entry_time", "")))
        exit_time = str(exit_orders[-1].get("timestamp", position.get("updated_at", "")))
        if _minutes_between(entry_time, exit_time) < 0:
            self._reconcile(position_id, "entry_exit_time_inconsistency", "Exit time precedes entry time.", {"entry": entry_time, "exit": exit_time})
            return None

        record_payload = {
            "closed_position_truth_id": f"CPT-{len(self._records) + 1:06d}",
            "position_id": position_id,
            "workflow_id": str(position.get("workflow_id", "")),
            "decision_object_id": decision_id,
            "symbol": symbol,
            "asset_type": str(position.get("asset_type", "")),
            "side": str(position.get("side", "")),
            "quantity_opened": quantity_opened,
            "quantity_closed": quantity_closed,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "holding_period": _holding_period(entry_time, exit_time),
            "entry_price_average": entry_price,
            "exit_price_average": exit_price,
            "gross_realized_pnl": gross_pnl,
            "net_realized_pnl": net_pnl,
            "realized_pnl_percent": round(net_pnl / max(1.0, entry_price * quantity_opened), 6),
            "max_unrealized_gain": _max_unrealized(snapshots),
            "max_unrealized_loss": _min_unrealized(snapshots),
            "max_drawdown_during_trade": _max_drawdown(snapshots),
            "distance_from_target_at_exit": round(exit_price - float(position.get("profit_target", 0.0) or 0.0), 4) if position.get("profit_target") else 0.0,
            "distance_from_stop_at_exit": round(exit_price - float(position.get("stop_loss", 0.0) or 0.0), 4) if position.get("stop_loss") else 0.0,
            "average_spread_paid": round(sum(float(order.get("spread_cost", 0.0) or 0.0) for order in orders) / max(1, len(orders)), 4),
            "total_slippage_cost": round(sum(float(order.get("slippage", 0.0) or 0.0) for order in orders), 4),
            "execution_quality_score": _execution_quality(orders),
            "surveillance_event_count": sum(len(snapshot.get("detected_events", ())) for snapshot in snapshots),
            "exit_timing_quality": _exit_timing_quality(exit_decision, net_pnl),
            "risk_adjusted_outcome": round(net_pnl / max(1.0, float(position.get("current_risk", 0.0) or 0.0) + 1.0), 4),
            "entry_execution_ids": tuple(str(order.get("order_id", "")) for order in entry_orders),
            "exit_execution_ids": tuple(str(order.get("order_id", "")) for order in exit_orders),
            "surveillance_snapshot_ids": tuple(str(snapshot.get("snapshot_id", "")) for snapshot in snapshots),
            "exit_decision_id": str(exit_decision.get("exit_decision_id", "")),
            "entry_thesis": str(position.get("entry_thesis", "")),
            "exit_reason": str(exit_decision.get("trigger_type", "executed_exit")),
            "lifecycle_summary": f"{symbol} opened at {entry_price:.4f}, closed at {exit_price:.4f}, net P/L {net_pnl:.4f}.",
            "benchmark_return": benchmark["benchmarkReturn"],
            "alpha_vs_benchmark": benchmark["alphaVsBenchmark"],
            "benchmark_payload": benchmark,
            "attribution_payload": attribution,
            "learning_payload": {},
            "audit_reference": f"EO-XE-AUD-{len(self._records) + 1:06d}-{position_id}",
            "created_at": timestamp,
        }
        record_payload["learning_payload"] = _learning_payload(record_payload, exit_decision, attribution)
        record_payload["hash"] = _hash_payload(record_payload)
        return ClosedPositionTruthRecord(**record_payload)

    def _reconcile(self, position_id: str, event_type: str, message: str, evidence: dict[str, Any]) -> None:
        event = {"eventId": f"CPT-REC-{len(self._reconciliation_events) + 1:06d}", "positionId": position_id, "eventType": event_type, "message": message, "evidence": evidence, "timestamp": utc_timestamp()}
        duplicate = any(item["positionId"] == position_id and item["eventType"] == event_type for item in self._reconciliation_events)
        if not duplicate:
            self._reconciliation_events.append(event)

    def _record_degraded_analytical(self, position_id: str, benchmark: dict[str, Any], attribution: dict[str, Any], timestamp: str) -> None:
        duplicate = any(item.position_id == position_id for item in self._degraded_analytical_records)
        if duplicate:
            return
        self._degraded_analytical_records.append(
            DegradedClosedPositionAnalyticalRecord(
                analytical_record_id=f"CPT-ANALYTICAL-{len(self._degraded_analytical_records) + 1:06d}",
                position_id=position_id,
                reason="degraded_benchmark_or_attribution",
                benchmark_payload=benchmark,
                attribution_payload=attribution,
                truth_classification="DEGRADED_ANALYTICAL_ONLY",
                certification_status="DEGRADED_ANALYTICAL_ONLY",
                learning_promotion_allowed=False,
                created_at=timestamp,
            )
        )
        self._reconcile(position_id, "degraded_analytical_only", "Degraded lifecycle evidence was retained outside authoritative Closed Position Truth.", {"benchmark": benchmark, "attribution": attribution})

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None) -> ClosedPositionTruthConfig:
        if not enterprise_configuration_registry:
            return self._config
        values = asdict(self._config)
        name_map = {
            "Closed Position Truth Enabled": "enabled",
            "Closed Position Truth Require Benchmark Data": "require_benchmark_data",
            "Closed Position Truth Require Attribution Payload": "require_attribution_payload",
            "Closed Position Truth Allow Degraded Creation": "allow_degraded_truth_creation",
            "Closed Position Truth Learning Event Enabled": "learning_event_enabled",
        }
        for entry in enterprise_configuration_registry.get("configurationRegistry", ()):
            key = name_map.get(str(entry.get("configurationName", "")))
            if key:
                values[key] = bool(entry.get("configuredValue"))
        return ClosedPositionTruthConfig(**values)


def _weighted_average(orders: tuple[dict[str, Any], ...]) -> float:
    quantity = sum(float(order.get("filled_quantity", 0.0) or 0.0) for order in orders)
    notional = sum(float(order.get("filled_quantity", 0.0) or 0.0) * float(order.get("average_fill_price", 0.0) or 0.0) for order in orders)
    return round(notional / max(1.0, quantity), 4)


def _surveillance_for_position(position_surveillance: dict[str, Any], position_id: str) -> tuple[dict[str, Any], ...]:
    snapshots = tuple(position_surveillance.get("surveillanceSnapshots", ())) + tuple(position_surveillance.get("latestSnapshots", ()))
    unique: dict[str, dict[str, Any]] = {}
    for snapshot in snapshots:
        if str(snapshot.get("position_id", "")) == position_id:
            unique[str(snapshot.get("snapshot_id", len(unique)))] = snapshot
    return tuple(unique.values())


def _exit_decision_for_position(exit_decision_engine: dict[str, Any], position_id: str) -> dict[str, Any]:
    records = tuple(exit_decision_engine.get("exitDecisionRecords", ())) + tuple(exit_decision_engine.get("latestDecisions", ()))
    for record in reversed(records):
        if str(record.get("position_id", "")) == position_id:
            return record
    return {}


def _benchmark_payload(engine: dict[str, Any], position: dict[str, Any], net_pnl: float, entry_price: float, quantity: float, config: ClosedPositionTruthConfig) -> dict[str, Any]:
    decision_id = str(position.get("decision_object_id", ""))
    comparisons = tuple(engine.get("tradeLevelComparisons", ()))
    spy = next((item for item in comparisons if item.get("decisionObjectId") == decision_id and item.get("benchmarkName") in {"SPY", "SPY Buy And Hold"}), None)
    argos_return = round(net_pnl / max(1.0, entry_price * quantity) * 100, 4)
    if spy:
        benchmark_return = float(spy.get("benchmarkReturn", 0.0) or 0.0)
        return {"status": "COMPLETE", "benchmarkName": spy.get("benchmarkName", "SPY"), "benchmarkReturn": benchmark_return, "argosReturn": argos_return, "alphaVsBenchmark": round(argos_return - benchmark_return, 4), "defaultBenchmarks": config.benchmark_defaults}
    return {"status": "DEGRADED", "benchmarkName": "SPY", "benchmarkReturn": 0.0, "argosReturn": argos_return, "alphaVsBenchmark": argos_return, "warning": "Benchmark data unavailable; degraded benchmark section created.", "defaultBenchmarks": config.benchmark_defaults}


def _attribution_payload(engine: dict[str, Any], position: dict[str, Any], exit_decision: dict[str, Any], benchmark: dict[str, Any], net_pnl: float) -> dict[str, Any]:
    reports = tuple(engine.get("attributionRepository", ()))
    decision_id = str(position.get("decision_object_id", ""))
    report = next((item for item in reports if item.get("decisionObjectId") == decision_id), None)
    if report:
        return {"status": "COMPLETE", "source": "Trade Attribution Engine", "attributionReportId": report.get("attributionReportId", ""), "dimensionScores": report.get("dimensionScores", ())}
    return {
        "status": "PREPARED",
        "source": "EO-XE adapter",
        "entryDecisionContribution": "READY_FOR_ATTRIBUTION_ENGINE",
        "exitDecisionContribution": exit_decision.get("trigger_type", ""),
        "positionManagementContribution": "SURVEILLANCE_HISTORY_ATTACHED",
        "executionQualityContribution": "EXECUTION_ANALYTICS_ATTACHED",
        "marketContribution": benchmark.get("benchmarkReturn", 0.0),
        "strategyContribution": "STRATEGY_PACKAGE_CONTEXT_PENDING",
        "promptContribution": "PROMPT_CONTEXT_PENDING",
        "riskContribution": "RISK_CONTEXT_ATTACHED",
        "netRealizedPnl": net_pnl,
    }


def _learning_payload(record: dict[str, Any], exit_decision: dict[str, Any], attribution: dict[str, Any]) -> dict[str, Any]:
    return {
        "expected": record.get("entry_thesis", ""),
        "happened": record.get("lifecycle_summary", ""),
        "targetReached": record.get("exit_reason") == "profit_target_reached",
        "stopReached": record.get("exit_reason") in {"stop_loss_reached", "trailing_stop_reached"},
        "exitType": exit_decision.get("decision", "executed_exit"),
        "executionQualityHelped": record.get("execution_quality_score", 0.0) >= 80,
        "strategyAssumptionsHeld": record.get("net_realized_pnl", 0.0) >= 0,
        "promptAnalysisUseful": attribution.get("promptContribution", "") != "NEGATIVE",
        "riskControlsHelped": record.get("max_drawdown_during_trade", 0.0) >= -0.05,
        "influenceFutureStrategyEvaluation": True,
    }


def _learning_event(record: ClosedPositionTruthRecord) -> dict[str, Any]:
    return {"eventId": f"CPT-LEARN-{record.closed_position_truth_id}", "closedPositionTruthId": record.closed_position_truth_id, "positionId": record.position_id, "symbol": record.symbol, "netRealizedPnl": record.net_realized_pnl, "learningPayload": record.learning_payload, "timestamp": record.created_at}


def _max_unrealized(snapshots: tuple[dict[str, Any], ...]) -> float:
    return round(max((float(item.get("unrealized_pnl", 0.0) or 0.0) for item in snapshots), default=0.0), 4)


def _min_unrealized(snapshots: tuple[dict[str, Any], ...]) -> float:
    return round(min((float(item.get("unrealized_pnl", 0.0) or 0.0) for item in snapshots), default=0.0), 4)


def _max_drawdown(snapshots: tuple[dict[str, Any], ...]) -> float:
    peak = 0.0
    drawdown = 0.0
    for snapshot in snapshots:
        value = float(snapshot.get("unrealized_pnl", 0.0) or 0.0)
        peak = max(peak, value)
        drawdown = min(drawdown, value - peak)
    return round(drawdown, 4)


def _execution_quality(orders: tuple[dict[str, Any], ...]) -> float:
    notional = sum(float(order.get("estimated_notional", 0.0) or 0.0) for order in orders)
    costs = sum(float(order.get("slippage", 0.0) or 0.0) + float(order.get("spread_cost", 0.0) or 0.0) for order in orders)
    return round(max(0.0, 100.0 - costs / max(1.0, notional) * 1000.0), 4)


def _exit_timing_quality(exit_decision: dict[str, Any], net_pnl: float) -> float:
    if not exit_decision:
        return 50.0
    if exit_decision.get("trigger_type") == "profit_target_reached" and net_pnl >= 0:
        return 95.0
    if exit_decision.get("trigger_type") in {"stop_loss_reached", "large_adverse_move"}:
        return 80.0
    return 70.0 if net_pnl >= 0 else 55.0


def _holding_period(entry_time: str, exit_time: str) -> str:
    minutes = _minutes_between(entry_time, exit_time)
    if minutes < 60:
        return f"{minutes}m"
    return f"{minutes // 60}h {minutes % 60}m"


def _minutes_between(start: str, end: str) -> int:
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        return int((end_dt - start_dt).total_seconds() // 60)
    except ValueError:
        return 0


def _hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
