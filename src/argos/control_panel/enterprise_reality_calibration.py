"""Enterprise Reality Calibration Engine for ARGOS EO-Y."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class CalibrationDriftEvent:
    drift_type: str
    severity: str
    evidence: tuple[str, ...]
    affected_records: tuple[str, ...]
    recommended_action: str


@dataclass(frozen=True)
class CalibrationReport:
    calibration_report_id: str
    timestamp: str
    calibration_window_start: str
    calibration_window_end: str
    total_orders_reviewed: int
    total_executions_reviewed: int
    total_positions_reviewed: int
    total_closed_positions_reviewed: int
    market_data_fidelity_score: float
    execution_fidelity_score: float
    liquidity_fidelity_score: float
    valuation_fidelity_score: float
    benchmark_fidelity_score: float
    truth_reliability_score: float
    learning_reliability_score: float
    overall_reality_fidelity_score: float
    detected_drift_events: tuple[dict[str, Any], ...]
    severe_anomalies: tuple[dict[str, Any], ...]
    degraded_learning_warning: str
    recommended_action: str
    audit_reference: str


@dataclass(frozen=True)
class RealityCalibrationConfig:
    reality_calibration_enabled: bool = True
    calibration_interval: str = "state_poll_guarded"
    calibration_window: str = "latest_paper_truth_window"
    minimum_acceptable_reality_fidelity_score: float = 80.0
    degraded_learning_threshold: float = 80.0
    unsafe_learning_threshold: float = 60.0
    blocked_learning_threshold: float = 40.0
    execution_anomaly_threshold: int = 1
    valuation_anomaly_threshold: int = 1
    severe_drift_threshold: int = 1
    block_learning_when_unsafe: bool = True
    emit_commander_alert_when_severe: bool = True
    conservative_scoring_mode: bool = True


class EnterpriseRealityCalibrationEngine:
    """Deterministic simulation fidelity evaluator."""

    def __init__(self, config: RealityCalibrationConfig | None = None) -> None:
        self._config = config or RealityCalibrationConfig()
        self._reports: list[CalibrationReport] = []
        self._last_fingerprint = ""

    def calibrate(
        self,
        *,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any],
        position_surveillance: dict[str, Any],
        closed_position_truth: dict[str, Any],
        enterprise_benchmark_engine: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        enterprise_configuration_registry: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        """Evaluate current paper-reality fidelity without mutating trading state."""
        config = self._resolved_config(enterprise_configuration_registry)
        if not config.reality_calibration_enabled:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_report=None, config=config)

        fingerprint = _fingerprint(performance_truth, market_data_provider, position_surveillance, closed_position_truth, enterprise_benchmark_engine, enterprise_learning_engine)
        if fingerprint == self._last_fingerprint and self._reports:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_report=self._reports[-1], config=config)

        report = self._build_report(
            timestamp_utc=timestamp_utc,
            performance_truth=performance_truth,
            market_data_provider=market_data_provider,
            position_surveillance=position_surveillance,
            closed_position_truth=closed_position_truth,
            enterprise_benchmark_engine=enterprise_benchmark_engine,
            enterprise_learning_engine=enterprise_learning_engine,
            audit_event_count=audit_event_count,
            config=config,
        )
        self._reports.append(report)
        self._last_fingerprint = fingerprint
        return self.snapshot(timestamp_utc=timestamp_utc, latest_report=report, config=config)

    def snapshot(self, *, timestamp_utc: str, latest_report: CalibrationReport | None = None, config: RealityCalibrationConfig | None = None) -> dict[str, Any]:
        """Return append-only calibration history and Commander-facing state."""
        config = config or self._config
        latest = latest_report or (self._reports[-1] if self._reports else None)
        latest_payload = asdict(latest) if latest else {}
        reliability = _learning_state(float(latest.overall_reality_fidelity_score) if latest else 0.0, config)
        severe_count = len(latest.severe_anomalies) if latest else 0
        return {
            "engineName": "Enterprise Reality Calibration Engine",
            "engineeringOrder": "EO-Y",
            "constitutionalMode": "OBSERVATION_ONLY",
            "calibrationReports": tuple(asdict(item) for item in self._reports),
            "latestCalibrationReport": latest_payload,
            "learningReliabilityGate": {
                "state": reliability,
                "blockLearningPromotion": reliability in {"unsafe", "blocked"} and config.block_learning_when_unsafe,
                "warning": latest.degraded_learning_warning if latest else "No calibration report available.",
                "historianWarningEmitted": bool(latest and latest.degraded_learning_warning),
            },
            "enterpriseHealthMetrics": _health_metrics(latest, timestamp_utc),
            "commanderSummary": {
                "overallRealityFidelityScore": latest.overall_reality_fidelity_score if latest else 0.0,
                "learningReliabilityState": reliability,
                "severeAnomalies": severe_count,
                "recommendedAction": latest.recommended_action if latest else "Generate first calibration report.",
                "latestCalibrationTimestamp": latest.timestamp if latest else "",
            },
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "calibrationPassTerminates": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicScoring": True},
            "configuration": asdict(config),
            "internalDiagnostics": {
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "placesTrades": False,
                "generatesInvestmentDecisions": False,
                "liveBrokerageCalls": 0,
                "paidApiCalls": 0,
                "reportCount": len(self._reports),
            },
        }

    def _build_report(
        self,
        *,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any],
        position_surveillance: dict[str, Any],
        closed_position_truth: dict[str, Any],
        enterprise_benchmark_engine: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        audit_event_count: int,
        config: RealityCalibrationConfig,
    ) -> CalibrationReport:
        orders = tuple(performance_truth.get("orderLedger", ()))
        executions = tuple(item for item in orders if str(item.get("status", "")).upper() in {"FILLED", "PARTIALLY_FILLED", "PARTIAL"})
        positions = tuple(performance_truth.get("positionLedger", ())) or tuple(performance_truth.get("positionRegistry", {}).get("activePositions", ()))
        closed_records = tuple(closed_position_truth.get("closedPositionTruthRecords", ())) or tuple(performance_truth.get("closedPositionTruth", ()))
        valuations = tuple(performance_truth.get("portfolioLedger", ()))
        benchmarks = tuple(performance_truth.get("benchmarkHistory", ()))
        drift_events = []
        drift_events.extend(_execution_drift_events(orders, config))
        drift_events.extend(_valuation_drift_events(performance_truth, valuations, positions, config))
        drift_events.extend(_truth_drift_events(performance_truth, closed_records))
        drift_events.extend(_market_data_drift_events(market_data_provider, position_surveillance))
        drift_events.extend(_benchmark_drift_events(benchmarks, enterprise_benchmark_engine))
        drift_events.extend(_learning_drift_events(enterprise_learning_engine, closed_records))
        score_inputs = _score_inputs(
            orders=orders,
            executions=executions,
            positions=positions,
            closed_records=closed_records,
            valuations=valuations,
            benchmarks=benchmarks,
            market_data_provider=market_data_provider,
            drift_events=tuple(drift_events),
            enterprise_learning_engine=enterprise_learning_engine,
        )
        overall = _average((
            score_inputs["market_data"],
            score_inputs["execution"],
            score_inputs["liquidity"],
            score_inputs["valuation"],
            score_inputs["benchmark"],
            score_inputs["truth"],
            score_inputs["learning"],
        ))
        severe = tuple(asdict(item) for item in drift_events if item.severity in {"SEVERE", "CRITICAL"})
        reliability = _learning_state(overall, config)
        warning = "" if reliability == "reliable" else f"Learning reliability is {reliability}; new observations should be treated as degraded evidence."
        return CalibrationReport(
            calibration_report_id=f"ERC-{len(self._reports) + 1:06d}",
            timestamp=timestamp_utc,
            calibration_window_start=_window_start(orders, valuations, closed_records, timestamp_utc),
            calibration_window_end=timestamp_utc,
            total_orders_reviewed=len(orders),
            total_executions_reviewed=len(executions),
            total_positions_reviewed=len(positions),
            total_closed_positions_reviewed=len(closed_records),
            market_data_fidelity_score=score_inputs["market_data"],
            execution_fidelity_score=score_inputs["execution"],
            liquidity_fidelity_score=score_inputs["liquidity"],
            valuation_fidelity_score=score_inputs["valuation"],
            benchmark_fidelity_score=score_inputs["benchmark"],
            truth_reliability_score=score_inputs["truth"],
            learning_reliability_score=score_inputs["learning"],
            overall_reality_fidelity_score=overall,
            detected_drift_events=tuple(asdict(item) for item in drift_events),
            severe_anomalies=severe,
            degraded_learning_warning=warning,
            recommended_action=_recommended_action(reliability, severe),
            audit_reference=f"AE-REALITY-CAL-{audit_event_count + len(self._reports) + 1:06d}",
        )

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None) -> RealityCalibrationConfig:
        values = asdict(self._config)
        for item in (enterprise_configuration_registry or {}).get("configurationRegistry", ()):
            key = _config_key(str(item.get("name", "")))
            if key in values:
                values[key] = _coerce_config_value(item.get("currentValue", values[key]), values[key])
        return RealityCalibrationConfig(**values)


def _execution_drift_events(orders: tuple[dict[str, Any], ...], config: RealityCalibrationConfig) -> list[CalibrationDriftEvent]:
    events: list[CalibrationDriftEvent] = []
    filled = [item for item in orders if str(item.get("status", "")).upper() in {"FILLED", "PARTIALLY_FILLED", "PARTIAL"}]
    partial = [item for item in filled if str(item.get("status", "")).upper() in {"PARTIALLY_FILLED", "PARTIAL"}]
    for order in filled:
        order_id = str(order.get("order_id", "ORDER-UNKNOWN"))
        side = str(order.get("side", "")).upper()
        bid = _number(order.get("bid_price"))
        ask = _number(order.get("ask_price"))
        fill = _number(order.get("average_fill_price"))
        tolerance = max(0.01, (ask - bid) * 0.5)
        if bid and ask and fill and (fill < bid - tolerance or fill > ask + tolerance):
            events.append(_drift("fill_outside_bid_ask_envelope", "SEVERE", (f"{side} fill {fill} outside plausible {bid}-{ask} envelope.",), (order_id,), "Review broker simulator fill price assumptions."))
        if side == "BUY" and ask and fill and fill < bid - tolerance:
            events.append(_drift("buy_fill_too_favorable", "WARNING", (f"BUY filled at {fill} below bid {bid}.",), (order_id,), "Calibrate BUY fills toward ask-side execution."))
        if side == "SELL" and bid and fill and fill > ask + tolerance:
            events.append(_drift("sell_fill_too_favorable", "WARNING", (f"SELL filled at {fill} above ask {ask}.",), (order_id,), "Calibrate SELL fills toward bid-side execution."))
        session = str(order.get("market_session", "")).upper()
        if session in {"CLOSED", "MARKET_CLOSED"}:
            events.append(_drift("impossible_closed_market_fill", "CRITICAL", (f"Filled order recorded during {session}.",), (order_id,), "Block learning from this execution until broker session rules are fixed."))
        if abs(_number(order.get("slippage"))) > config.minimum_acceptable_reality_fidelity_score:
            events.append(_drift("slippage_outside_configured_bounds", "WARNING", (f"Slippage {order.get('slippage')} exceeds conservative bounds.",), (order_id,), "Review slippage model inputs."))
    large_filled = [item for item in filled if _number(item.get("requested_quantity")) >= max(100.0, _number(item.get("available_volume")) * 0.75)]
    if len(large_filled) >= 5 and not partial:
        events.append(_drift("partial_fill_absence_for_large_orders", "WARNING", ("Large orders filled without any partial fills.",), tuple(str(item.get("order_id", "")) for item in large_filled[:5]), "Increase partial-fill realism for large orders."))
    return events


def _valuation_drift_events(performance_truth: dict[str, Any], valuations: tuple[dict[str, Any], ...], positions: tuple[dict[str, Any], ...], config: RealityCalibrationConfig) -> list[CalibrationDriftEvent]:
    events: list[CalibrationDriftEvent] = []
    broker = performance_truth.get("brokerProfile", {})
    margin_enabled = bool(broker.get("marginPermissions") or broker.get("configuration", {}).get("allowMargin"))
    for row in valuations:
        row_id = str(row.get("audit_identifier") or row.get("timestamp") or "PORTFOLIO-VALUATION")
        cash = _number(row.get("cash"))
        market_value = _number(row.get("market_value"))
        total_equity = _number(row.get("total_equity"))
        if abs((cash + market_value) - total_equity) > 0.05:
            events.append(_drift("portfolio_value_without_accounting_support", "SEVERE", (f"cash {cash} + market value {market_value} != total equity {total_equity}.",), (row_id,), "Reconcile portfolio valuation before learning promotion."))
        if cash < -0.01 and not margin_enabled:
            events.append(_drift("negative_cash_without_margin", "CRITICAL", (f"Cash account has negative cash {cash}.",), (row_id,), "Block learning and repair buying-power accounting."))
    for current, previous in zip(valuations[1:], valuations[:-1]):
        prior = max(1.0, abs(_number(previous.get("total_equity"))))
        jump = abs(_number(current.get("total_equity")) - _number(previous.get("total_equity"))) / prior * 100
        if jump >= 2.5:
            events.append(_drift("excessive_short_term_portfolio_appreciation", "SEVERE", (f"Portfolio equity moved {round(jump, 4)}% between valuation records.",), (str(previous.get("audit_identifier", "")), str(current.get("audit_identifier", ""))), "Require execution or market movement evidence for the equity jump."))
    for position in positions:
        price = _number(position.get("current_price", position.get("average_cost")))
        quantity = _number(position.get("quantity"))
        expected_value = round(price * quantity, 4)
        actual = _number(position.get("current_value", position.get("market_value")))
        if actual and abs(actual - expected_value) > 0.05:
            events.append(_drift("position_value_mismatch", "WARNING", (f"Position value {actual} differs from price*quantity {expected_value}.",), (str(position.get("position_id", position.get("symbol", ""))),), "Refresh mark-to-market valuation."))
    return events


def _truth_drift_events(performance_truth: dict[str, Any], closed_records: tuple[dict[str, Any], ...]) -> list[CalibrationDriftEvent]:
    events: list[CalibrationDriftEvent] = []
    truth_ids = {str(item.get("closed_position_truth_id", "")) for item in closed_records if item.get("closed_position_truth_id")}
    for trade in performance_truth.get("tradeLedger", ()):
        trade_id = str(trade.get("trade_id", "TRADE-UNKNOWN"))
        closed_ref = str(trade.get("closed_position_truth_id", ""))
        if not closed_ref and not truth_ids:
            events.append(_drift("performance_truth_without_closed_position_truth", "SEVERE", ("Completed trade exists without Closed Position Truth evidence.",), (trade_id,), "Degrade learning until round-trip truth is available."))
    seen: set[str] = set()
    for record in closed_records:
        record_id = str(record.get("closed_position_truth_id", "CPT-UNKNOWN"))
        if record_id in seen:
            events.append(_drift("duplicate_closed_position_truth", "WARNING", ("Duplicate Closed Position Truth identifier found.",), (record_id,), "Deduplicate truth publication before learning."))
        seen.add(record_id)
        if not record.get("exit_execution_order_id") and not record.get("exit_order_id"):
            events.append(_drift("closed_position_truth_without_exit_execution", "SEVERE", ("Closed Position Truth lacks exit execution evidence.",), (record_id,), "Mark lifecycle evidence incomplete."))
        snapshots = tuple(record.get("surveillance_snapshot_ids", ()))
        if not snapshots:
            events.append(_drift("closed_position_truth_without_surveillance_history", "WARNING", ("Closed Position Truth lacks surveillance snapshot evidence.",), (record_id,), "Treat lifecycle analytics as degraded."))
        benchmark = record.get("benchmark_comparison", {})
        if not benchmark:
            events.append(_drift("closed_position_truth_without_benchmark", "WARNING", ("Closed Position Truth lacks benchmark comparison.",), (record_id,), "Mark benchmark fidelity degraded."))
    return events


def _market_data_drift_events(market_data_provider: dict[str, Any], position_surveillance: dict[str, Any]) -> list[CalibrationDriftEvent]:
    events: list[CalibrationDriftEvent] = []
    diagnostics = market_data_provider.get("normalizationDiagnostics", {})
    if diagnostics.get("invalidObjectsRejected", 0):
        events.append(_drift("market_data_normalization_rejections", "WARNING", ("Market data provider rejected normalized objects.",), ("MDPA",), "Review provider normalization diagnostics."))
    if market_data_provider.get("commanderVisibility", {}).get("dataFreshness") == "STALE":
        events.append(_drift("market_data_stale", "SEVERE", ("Commander visibility reports stale market data.",), ("MDPA",), "Pause learning from stale market data windows."))
    degraded = [item for item in position_surveillance.get("surveillanceSnapshots", ()) if str(item.get("surveillance_status", "")).upper() == "DEGRADED"]
    if degraded:
        events.append(_drift("surveillance_snapshot_data_degraded", "WARNING", ("Position surveillance contains degraded snapshots.",), tuple(str(item.get("snapshot_id", "")) for item in degraded[:5]), "Treat affected position observations as degraded."))
    return events


def _benchmark_drift_events(benchmarks: tuple[dict[str, Any], ...], benchmark_engine: dict[str, Any]) -> list[CalibrationDriftEvent]:
    if benchmarks or benchmark_engine.get("tradeLevelComparisons") or benchmark_engine.get("benchmarkComparisons"):
        return []
    return [_drift("benchmark_values_missing", "WARNING", ("No benchmark evidence available for calibration window.",), ("BENCHMARK",), "Reduce benchmark fidelity until benchmark comparisons are present.")]


def _learning_drift_events(learning: dict[str, Any], closed_records: tuple[dict[str, Any], ...]) -> list[CalibrationDriftEvent]:
    observations = tuple(learning.get("learningObservations", ())) + tuple(learning.get("observations", ()))
    if observations and not closed_records:
        return [_drift("learning_observations_without_round_trip_truth", "SEVERE", ("Learning observations exist without Closed Position Truth support.",), tuple(str(item.get("observationId", "")) for item in observations[:5]), "Degrade or block learning promotion.")]
    return []


def _score_inputs(**values: Any) -> dict[str, float]:
    drift_events = tuple(values["drift_events"])
    counts = {kind: sum(1 for item in drift_events if kind in item.drift_type) for kind in ("market", "fill", "slippage", "partial", "portfolio", "position", "benchmark", "truth", "learning")}
    market_data = _score(100, counts["market"] * 15 + (0 if values["market_data_provider"].get("normalizedObjects") else 20))
    execution = _score(100 if values["orders"] else 82, counts["fill"] * 25 + counts["slippage"] * 10)
    liquidity = _score(92 if values["orders"] else 78, counts["partial"] * 15)
    valuation = _score(100 if values["valuations"] else 75, counts["portfolio"] * 25 + counts["position"] * 10)
    benchmark = _score(100 if values["benchmarks"] else 76, counts["benchmark"] * 20)
    truth = _score(100 if values["closed_records"] else 74, counts["truth"] * 24)
    learning = _score(96 if values["enterprise_learning_engine"] else 78, counts["learning"] * 25 + counts["truth"] * 8)
    severe_penalty = sum(18 for item in drift_events if item.severity == "SEVERE") + sum(30 for item in drift_events if item.severity == "CRITICAL")
    return {
        "market_data": market_data,
        "execution": _score(execution, severe_penalty * 0.35),
        "liquidity": liquidity,
        "valuation": _score(valuation, severe_penalty * 0.45),
        "benchmark": benchmark,
        "truth": _score(truth, severe_penalty * 0.4),
        "learning": _score(learning, severe_penalty * 0.5),
    }


def _health_metrics(report: CalibrationReport | None, timestamp: str) -> dict[str, Any]:
    if not report:
        return {"latestRealityFidelityScore": 0.0, "latestLearningReliabilityState": "blocked", "severeDriftCount": 0, "calibrationAge": "NO_REPORT", "degradedTruthCount": 0, "unsafeLearningCount": 0, "executionAnomalyCount": 0, "valuationAnomalyCount": 0}
    events = tuple(report.detected_drift_events)
    return {
        "latestRealityFidelityScore": report.overall_reality_fidelity_score,
        "latestLearningReliabilityState": _learning_state(report.overall_reality_fidelity_score, RealityCalibrationConfig()),
        "severeDriftCount": len(report.severe_anomalies),
        "calibrationAge": "CURRENT" if report.timestamp == timestamp else "RECENT",
        "degradedTruthCount": sum(1 for item in events if "truth" in item.get("drift_type", "")),
        "unsafeLearningCount": 1 if report.learning_reliability_score < 60 else 0,
        "executionAnomalyCount": sum(1 for item in events if item.get("drift_type", "").startswith(("fill", "impossible", "slippage", "partial"))),
        "valuationAnomalyCount": sum(1 for item in events if "portfolio" in item.get("drift_type", "") or "cash" in item.get("drift_type", "") or "position_value" in item.get("drift_type", "")),
    }


def _drift(drift_type: str, severity: str, evidence: tuple[str, ...], affected_records: tuple[str, ...], recommended_action: str) -> CalibrationDriftEvent:
    return CalibrationDriftEvent(drift_type, severity, evidence, affected_records, recommended_action)


def _score(base: float, penalty: float) -> float:
    return round(max(0.0, min(100.0, float(base) - float(penalty))), 4)


def _average(values: tuple[float, ...]) -> float:
    return round(sum(values) / max(1, len(values)), 4)


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _learning_state(score: float, config: RealityCalibrationConfig) -> str:
    if score < config.blocked_learning_threshold:
        return "blocked"
    if score < config.unsafe_learning_threshold:
        return "unsafe"
    if score < config.degraded_learning_threshold:
        return "degraded"
    return "reliable"


def _recommended_action(reliability: str, severe: tuple[dict[str, Any], ...]) -> str:
    if reliability in {"blocked", "unsafe"}:
        return "Block promotion of new learning observations and review severe drift evidence."
    if severe:
        return "Degrade learning confidence and investigate severe calibration drift."
    if reliability == "degraded":
        return "Allow learning only as degraded evidence until calibration improves."
    return "Reality calibration nominal; learning evidence may remain eligible."


def _window_start(orders: tuple[dict[str, Any], ...], valuations: tuple[dict[str, Any], ...], closed_records: tuple[dict[str, Any], ...], fallback: str) -> str:
    timestamps = [str(item.get("timestamp", "")) for item in orders + valuations if item.get("timestamp")]
    timestamps.extend(str(item.get("created_at", "")) for item in closed_records if item.get("created_at"))
    return min(timestamps) if timestamps else fallback


def _fingerprint(*parts: dict[str, Any]) -> str:
    payload = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _config_key(name: str) -> str:
    normalized = "".join(character if character.isalnum() else "_" for character in name.strip().lower())
    aliases = {
        "reality_calibration_enabled": "reality_calibration_enabled",
        "minimum_acceptable_reality_fidelity_score": "minimum_acceptable_reality_fidelity_score",
        "block_learning_when_unsafe": "block_learning_when_unsafe",
        "conservative_scoring_mode": "conservative_scoring_mode",
    }
    return aliases.get(normalized, normalized)


def _coerce_config_value(value: Any, default: Any) -> Any:
    if isinstance(default, bool):
        return str(value).lower() in {"1", "true", "yes", "enabled"}
    if isinstance(default, float):
        return _number(value)
    return value
