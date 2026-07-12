"""Market Replay Engine for ARGOS EO-BA."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class MarketReplayConfig:
    market_replay_enabled: bool = True
    default_replay_granularity: str = "1D"
    default_initial_cash: float = 100000.0
    default_benchmark_symbols: tuple[str, ...] = ("SPY", "QQQ", "CASH")
    lookahead_bias_guard_enabled: bool = True
    replay_data_quality_threshold: float = 70.0
    replay_execution_model: str = "broker_realistic_replay"
    replay_spread_model: str = "deterministic_mid_spread"
    replay_slippage_model: str = "spread_plus_liquidity"
    replay_liquidity_model: str = "volume_participation_cap"
    replay_learning_promotion_policy: str = "manual_review_required"
    replay_artifact_isolation_policy: str = "replay_ledgers_isolated"
    reproducibility_required: bool = True
    conservative_missing_data_policy: str = "degrade"


@dataclass(frozen=True)
class ReplayScenarioRecord:
    replay_scenario_id: str
    scenario_name: str
    replay_start: str
    replay_end: str
    symbols: tuple[str, ...]
    benchmark_symbols: tuple[str, ...]
    data_sources: tuple[str, ...]
    data_window: dict[str, str]
    replay_granularity: str
    initial_cash: float
    initial_positions: tuple[dict[str, Any], ...]
    strategy_versions: tuple[dict[str, Any], ...]
    prompt_versions: tuple[dict[str, Any], ...]
    configuration_snapshot: dict[str, Any]
    market_data_snapshot_reference: str
    point_in_time_policy: str
    lookahead_bias_guard_enabled: bool
    execution_model: str
    slippage_model: str
    spread_model: str
    liquidity_model: str
    created_at: str
    audit_reference: str


@dataclass(frozen=True)
class ReplayRunRecord:
    replay_run_id: str
    replay_scenario_id: str
    started_at: str
    completed_at: str
    status: str
    workflow_ids: tuple[str, ...]
    decision_object_ids: tuple[str, ...]
    order_ids: tuple[str, ...]
    execution_ids: tuple[str, ...]
    position_ids: tuple[str, ...]
    closed_position_truth_ids: tuple[str, ...]
    performance_truth_ids: tuple[str, ...]
    benchmark_results: tuple[dict[str, Any], ...]
    replay_return: float
    replay_alpha: float
    max_drawdown: float
    trade_count: int
    win_rate: float
    average_trade_return: float
    execution_realism_summary: dict[str, Any]
    reality_calibration_summary: dict[str, Any]
    reproducibility_hash: str
    degraded_inputs: tuple[str, ...]
    failure_reason: str
    audit_reference: str
    replay_orders: tuple[dict[str, Any], ...]
    replay_positions: tuple[dict[str, Any], ...]
    replay_closed_position_truth: tuple[dict[str, Any], ...]
    replay_performance_truth: dict[str, Any]
    learning_eligibility: str
    replay_audit_trail: tuple[dict[str, Any], ...]


class ReplayClock:
    """Bounded deterministic replay clock independent of wall time."""

    def __init__(self, start: str, end: str, granularity: str = "1D") -> None:
        self.start = _parse_time(start)
        self.end = _parse_time(end)
        self.granularity = granularity
        self.current = self.start

    def timestamp(self) -> str:
        return _format_time(self.current)

    def advance(self) -> str:
        step = _granularity_delta(self.granularity)
        self.current = min(self.end, self.current + step)
        while self.current.weekday() >= 5 and self.current < self.end:
            self.current = min(self.end, self.current + timedelta(days=1))
        return self.timestamp()

    def done(self) -> bool:
        return self.current >= self.end


class HistoricalReplayMarketProvider:
    """Point-in-time historical market data provider for replay runs."""

    def __init__(self, historical_data: dict[str, Any], *, lookahead_guard: bool = True) -> None:
        self._data = historical_data
        self._lookahead_guard = lookahead_guard
        self.lookahead_violations: list[dict[str, Any]] = []

    def latest_quote(self, symbol: str, replay_timestamp: str) -> dict[str, Any]:
        rows = self._bars_for(symbol)
        cutoff = _parse_time(replay_timestamp)
        eligible = [row for row in rows if _parse_time(str(row.get("timestamp"))) <= cutoff]
        future = [row for row in rows if _parse_time(str(row.get("timestamp"))) > cutoff]
        if self._lookahead_guard and future and not eligible:
            self.lookahead_violations.append({"symbol": symbol.upper(), "timestamp": replay_timestamp, "reason": "future_data_requested_without_prior_bar"})
        if not eligible:
            return {"symbol": symbol.upper(), "status": "MISSING", "replayTimestamp": replay_timestamp}
        row = eligible[-1]
        price = _number(row.get("close", row.get("last", row.get("price"))))
        spread = max(0.01, price * 0.0004)
        return {
            "symbol": symbol.upper(),
            "bid": round(_number(row.get("bid", price - spread / 2)), 4),
            "ask": round(_number(row.get("ask", price + spread / 2)), 4),
            "last": round(price, 4),
            "close": round(price, 4),
            "volume": _number(row.get("volume", 0.0)),
            "timestamp": str(row.get("timestamp")),
            "replayTimestamp": replay_timestamp,
            "dataStatus": "POINT_IN_TIME",
            "degraded": "bid" not in row or "ask" not in row,
        }

    def normalized_snapshot(self, symbols: tuple[str, ...], replay_timestamp: str) -> dict[str, Any]:
        quotes = tuple(self.latest_quote(symbol, replay_timestamp) for symbol in symbols)
        return {"normalizedObjects": {"quotes": quotes, "marketStatus": ({"status": "REPLAY_OPEN", "timestamp": replay_timestamp},)}, "lookaheadViolations": tuple(self.lookahead_violations)}

    def _bars_for(self, symbol: str) -> list[dict[str, Any]]:
        normalized = self._data.get("bars", self._data.get("priceHistory", {}))
        if isinstance(normalized, dict):
            return sorted(tuple(normalized.get(symbol.upper(), normalized.get(symbol, ()))), key=lambda row: str(row.get("timestamp", "")))
        return sorted(tuple(row for row in normalized if str(row.get("symbol", "")).upper() == symbol.upper()), key=lambda row: str(row.get("timestamp", "")))


class MarketReplayEngine:
    """Bounded historical replay harness with isolated replay artifacts."""

    def __init__(self, config: MarketReplayConfig | None = None) -> None:
        self._config = config or MarketReplayConfig()
        self._scenarios: list[ReplayScenarioRecord] = []
        self._runs: list[ReplayRunRecord] = []

    def create_scenario(
        self,
        *,
        scenario_name: str,
        replay_start: str,
        replay_end: str,
        symbols: tuple[str, ...],
        historical_market_data: dict[str, Any],
        benchmark_symbols: tuple[str, ...] | None = None,
        replay_granularity: str | None = None,
        initial_cash: float | None = None,
        initial_positions: tuple[dict[str, Any], ...] = (),
        strategy_versions: tuple[dict[str, Any], ...] = (),
        prompt_versions: tuple[dict[str, Any], ...] = (),
        configuration_snapshot: dict[str, Any] | None = None,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        created_at: str | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        config = self._resolved_config(enterprise_configuration_registry)
        created = created_at or replay_start
        scenario = ReplayScenarioRecord(
            replay_scenario_id=f"MRE-SCEN-{len(self._scenarios) + 1:06d}",
            scenario_name=scenario_name,
            replay_start=replay_start,
            replay_end=replay_end,
            symbols=tuple(symbol.upper() for symbol in symbols),
            benchmark_symbols=benchmark_symbols or config.default_benchmark_symbols,
            data_sources=tuple(historical_market_data.get("dataSources", ("deterministic_mock_history",))),
            data_window={"start": replay_start, "end": replay_end},
            replay_granularity=replay_granularity or config.default_replay_granularity,
            initial_cash=_number(initial_cash if initial_cash is not None else config.default_initial_cash),
            initial_positions=initial_positions,
            strategy_versions=strategy_versions,
            prompt_versions=prompt_versions,
            configuration_snapshot=configuration_snapshot or {"marketReplay": asdict(config)},
            market_data_snapshot_reference=_hash({"symbols": symbols, "data": historical_market_data}),
            point_in_time_policy="prices_and_benchmarks_at_or_before_replay_timestamp_only",
            lookahead_bias_guard_enabled=config.lookahead_bias_guard_enabled,
            execution_model=config.replay_execution_model,
            slippage_model=config.replay_slippage_model,
            spread_model=config.replay_spread_model,
            liquidity_model=config.replay_liquidity_model,
            created_at=created,
            audit_reference=f"AE-MARKET-REPLAY-SCENARIO-{audit_event_count + len(self._scenarios) + 1:06d}",
        )
        self._scenarios.append(scenario)
        return self.snapshot(latest_scenario=scenario, timestamp_utc=created)

    def run_replay(
        self,
        *,
        scenario: dict[str, Any] | ReplayScenarioRecord,
        historical_market_data: dict[str, Any],
        timestamp_utc: str | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        scenario_record = _scenario_from_payload(scenario)
        clock = ReplayClock(scenario_record.replay_start, scenario_record.replay_end, scenario_record.replay_granularity)
        provider = HistoricalReplayMarketProvider(historical_market_data, lookahead_guard=scenario_record.lookahead_bias_guard_enabled)
        audit = [_audit("scenario_creation", scenario_record.replay_scenario_id), _audit("replay_start", scenario_record.replay_scenario_id)]
        degraded: list[str] = []
        cash = scenario_record.initial_cash
        positions: dict[str, dict[str, Any]] = {str(item.get("symbol", "")).upper(): dict(item) for item in scenario_record.initial_positions}
        orders: list[dict[str, Any]] = []
        closed: list[dict[str, Any]] = []
        equity_curve: list[float] = []
        decision_ids: list[str] = []
        workflow_ids: list[str] = []
        execution_ids: list[str] = []
        position_ids: list[str] = []
        timestamps: list[str] = []

        while True:
            now = clock.timestamp()
            timestamps.append(now)
            snapshot = provider.normalized_snapshot(scenario_record.symbols + scenario_record.benchmark_symbols, now)
            quotes = {str(quote.get("symbol", "")).upper(): quote for quote in snapshot["normalizedObjects"]["quotes"]}
            if any(quote.get("status") == "MISSING" for quote in quotes.values()):
                degraded.append("historical_market_data_missing")
                audit.append(_audit("degraded_data", now))
            if not orders:
                for symbol in scenario_record.symbols:
                    quote = quotes.get(symbol, {})
                    if quote.get("status") == "MISSING":
                        continue
                    quantity = _floor_quantity(min(cash / max(1, len(scenario_record.symbols)), scenario_record.initial_cash * 0.25) / max(0.0001, _number(quote.get("ask"))))
                    if quantity <= 0:
                        continue
                    order = _replay_order(len(orders) + 1, scenario_record, symbol, "BUY", quantity, quote, cash)
                    cash = max(0.0, cash + order["cash_impact"])
                    orders.append(order)
                    execution_ids.append(order["execution_id"])
                    position_id = f"REPLAY-POS-{len(position_ids) + 1:06d}"
                    position_ids.append(position_id)
                    positions[symbol] = {"position_id": position_id, "symbol": symbol, "quantity": quantity, "average_cost": order["average_fill_price"], "current_price": quote["last"], "current_value": round(quantity * quote["last"], 4), "execution_environment": "replay"}
                    decision_ids.append(f"REPLAY-DO-{len(decision_ids) + 1:06d}")
                    workflow_ids.append(f"REPLAY-WF-{len(workflow_ids) + 1:06d}")
                    audit.append(_audit("truth_creation", order["order_id"]))
            for symbol, position in list(positions.items()):
                quote = quotes.get(symbol, {})
                if quote.get("status") != "MISSING":
                    position["current_price"] = quote["last"]
                    position["current_value"] = round(_number(position["quantity"]) * quote["last"], 4)
            equity_curve.append(round(cash + sum(_number(item.get("current_value")) for item in positions.values()), 4))
            if clock.done():
                break
            clock.advance()

        final_quotes = {str(quote.get("symbol", "")).upper(): quote for quote in provider.normalized_snapshot(scenario_record.symbols, scenario_record.replay_end)["normalizedObjects"]["quotes"]}
        for symbol, position in list(positions.items()):
            quote = final_quotes.get(symbol, {})
            if quote.get("status") == "MISSING":
                degraded.append("exit_market_data_missing")
                continue
            order = _replay_order(len(orders) + 1, scenario_record, symbol, "SELL", _number(position["quantity"]), quote, cash)
            cash = cash + order["cash_impact"]
            orders.append(order)
            execution_ids.append(order["execution_id"])
            realized = round((_number(order["average_fill_price"]) - _number(position["average_cost"])) * _number(position["quantity"]), 4)
            closed_id = f"REPLAY-CPT-{len(closed) + 1:06d}"
            closed.append({"closed_position_truth_id": closed_id, "symbol": symbol, "realized_pnl": realized, "entry_price": position["average_cost"], "exit_price": order["average_fill_price"], "execution_environment": "replay", "mode": "replay", "audit_reference": closed_id})
            audit.append(_audit("truth_creation", closed_id))
            del positions[symbol]
        if provider.lookahead_violations:
            degraded.append("lookahead_guard_violation")
            audit.append(_audit("lookahead_guard_violation", scenario_record.replay_scenario_id))

        ending_equity = cash + sum(_number(item.get("current_value")) for item in positions.values())
        replay_return = round((ending_equity - scenario_record.initial_cash) / max(1.0, scenario_record.initial_cash), 6)
        benchmark_results = tuple(_benchmark_result(symbol, scenario_record, historical_market_data) for symbol in scenario_record.benchmark_symbols)
        benchmark_return = next((item["benchmarkReturn"] for item in benchmark_results if item["benchmarkSymbol"] == "SPY"), 0.0)
        run_payload = {
            "scenario": asdict(scenario_record),
            "orders": orders,
            "closed": closed,
            "equity": equity_curve,
            "benchmarks": benchmark_results,
            "degraded": tuple(dict.fromkeys(degraded)),
        }
        reproducibility = _hash(run_payload)
        eligibility = _learning_eligibility(degraded, scenario_record, benchmark_results)
        completed = timestamp_utc or scenario_record.replay_end
        audit.append(_audit("replay_completion", scenario_record.replay_scenario_id))
        record = ReplayRunRecord(
            replay_run_id=f"MRE-RUN-{len(self._runs) + 1:06d}",
            replay_scenario_id=scenario_record.replay_scenario_id,
            started_at=scenario_record.replay_start,
            completed_at=completed,
            status="COMPLETED" if "lookahead_guard_violation" not in degraded else "COMPLETED_DEGRADED",
            workflow_ids=tuple(workflow_ids),
            decision_object_ids=tuple(decision_ids),
            order_ids=tuple(order["order_id"] for order in orders),
            execution_ids=tuple(execution_ids),
            position_ids=tuple(position_ids),
            closed_position_truth_ids=tuple(item["closed_position_truth_id"] for item in closed),
            performance_truth_ids=(f"REPLAY-PTRUTH-{len(self._runs) + 1:06d}",),
            benchmark_results=benchmark_results,
            replay_return=replay_return,
            replay_alpha=round(replay_return - benchmark_return, 6),
            max_drawdown=_max_drawdown(equity_curve),
            trade_count=len(closed),
            win_rate=round(sum(1 for item in closed if _number(item.get("realized_pnl")) > 0) / max(1, len(closed)), 4),
            average_trade_return=round(sum(_number(item.get("realized_pnl")) for item in closed) / max(1.0, scenario_record.initial_cash), 6),
            execution_realism_summary={"executionModel": scenario_record.execution_model, "orders": len(orders), "rejectedOrders": 0, "partialFills": 0, "mode": "replay"},
            reality_calibration_summary={"mode": "replay", "lookaheadViolations": len(provider.lookahead_violations), "degradedInputs": tuple(dict.fromkeys(degraded))},
            reproducibility_hash=reproducibility,
            degraded_inputs=tuple(dict.fromkeys(degraded)),
            failure_reason="",
            audit_reference=f"AE-MARKET-REPLAY-RUN-{audit_event_count + len(self._runs) + 1:06d}",
            replay_orders=tuple(orders),
            replay_positions=tuple(positions.values()),
            replay_closed_position_truth=tuple(closed),
            replay_performance_truth={"performance_truth_id": f"REPLAY-PTRUTH-{len(self._runs) + 1:06d}", "execution_environment": "replay", "orders": tuple(orders), "closedPositionTruth": tuple(closed), "isolatedFromPaper": True},
            learning_eligibility=eligibility,
            replay_audit_trail=tuple(audit),
        )
        self._runs.append(record)
        return self.snapshot(latest_scenario=scenario_record, latest_run=record, timestamp_utc=completed)

    def snapshot(self, *, latest_scenario: ReplayScenarioRecord | None = None, latest_run: ReplayRunRecord | None = None, timestamp_utc: str = "") -> dict[str, Any]:
        latest_scenario = latest_scenario or (self._scenarios[-1] if self._scenarios else None)
        latest_run = latest_run or (self._runs[-1] if self._runs else None)
        return {
            "engineName": "Market Replay Engine",
            "engineeringOrder": "EO-BA",
            "constitutionalMode": "BOUNDED_HISTORICAL_REPLAY_ONLY",
            "replayScenarioRecords": tuple(asdict(item) for item in self._scenarios),
            "replayRunRecords": tuple(asdict(item) for item in self._runs),
            "latestReplayScenarioRecord": asdict(latest_scenario) if latest_scenario else {},
            "latestReplayRunRecord": asdict(latest_run) if latest_run else {},
            "replayClock": {"usesWallClock": False, "boundedScenarioRequired": True, "granularity": latest_scenario.replay_granularity if latest_scenario else self._config.default_replay_granularity},
            "pointInTimeGuard": {"lookaheadBiasGuardEnabled": self._config.lookahead_bias_guard_enabled, "futureDataAllowed": False},
            "commanderSummary": {"latestStatus": latest_run.status if latest_run else "standby", "learningEligibility": latest_run.learning_eligibility if latest_run else "research_only", "replayReturn": latest_run.replay_return if latest_run else 0.0},
            "configuration": asdict(self._config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "explicitScenarioBoundsRequired": True, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicReplay": True},
            "internalDiagnostics": {"mutatesPaperLedgers": False, "placesLiveTrades": False, "apiCreditsConsumed": 0.0, "workflowTokensOwned": 0, "scenarioCount": len(self._scenarios), "runCount": len(self._runs), "timestamp": timestamp_utc},
        }

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None) -> MarketReplayConfig:
        values = asdict(self._config)
        for item in (enterprise_configuration_registry or {}).get("configurationRegistry", ()):
            key = _config_key(str(item.get("name", "")))
            if key in values:
                values[key] = _coerce_config_value(item.get("currentValue", values[key]), values[key])
        return MarketReplayConfig(**values)


def _replay_order(index: int, scenario: ReplayScenarioRecord, symbol: str, side: str, quantity: float, quote: dict[str, Any], cash_before: float) -> dict[str, Any]:
    price = _number(quote.get("ask" if side == "BUY" else "bid", quote.get("last")))
    spread = abs(_number(quote.get("ask")) - _number(quote.get("bid")))
    slippage = round(spread * quantity * 0.05, 4)
    notional = round(quantity * price, 4)
    cash_impact = round(-notional - slippage if side == "BUY" else notional - slippage, 4)
    return {"order_id": f"REPLAY-ORD-{index:06d}", "execution_id": f"REPLAY-EXEC-{index:06d}", "symbol": symbol, "side": side, "requested_quantity": quantity, "filled_quantity": quantity, "average_fill_price": price, "estimated_notional": notional, "slippage": slippage, "cash_impact": cash_impact, "status": "FILLED", "execution_environment": "replay", "market_session": "REPLAY_OPEN", "timestamp": quote.get("replayTimestamp", scenario.replay_start), "buying_power_before": round(cash_before, 4), "buying_power_after": round(cash_before + cash_impact, 4)}


def _benchmark_result(symbol: str, scenario: ReplayScenarioRecord, data: dict[str, Any]) -> dict[str, Any]:
    provider = HistoricalReplayMarketProvider(data, lookahead_guard=True)
    start = provider.latest_quote(symbol, scenario.replay_start)
    end = provider.latest_quote(symbol, scenario.replay_end)
    start_price = _number(start.get("last"))
    end_price = _number(end.get("last"))
    ret = round((end_price - start_price) / max(1.0, start_price), 6) if start_price and end_price else 0.0
    return {"benchmarkSymbol": symbol, "benchmarkReturn": ret, "pointInTime": True, "status": "COMPLETE" if start_price and end_price else "DEGRADED"}


def _learning_eligibility(degraded: list[str], scenario: ReplayScenarioRecord, benchmarks: tuple[dict[str, Any], ...]) -> str:
    if "lookahead_guard_violation" in degraded:
        return "blocked"
    if any(item.get("status") == "DEGRADED" for item in benchmarks) or degraded:
        return "degraded"
    if scenario.lookahead_bias_guard_enabled:
        return "eligible" if scenario.point_in_time_policy else "research_only"
    return "research_only"


def _scenario_from_payload(payload: dict[str, Any] | ReplayScenarioRecord) -> ReplayScenarioRecord:
    if isinstance(payload, ReplayScenarioRecord):
        return payload
    data = dict(payload)
    return ReplayScenarioRecord(**data)


def _parse_time(value: str) -> datetime:
    text = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _format_time(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _granularity_delta(value: str) -> timedelta:
    text = value.upper()
    if text.endswith("H"):
        return timedelta(hours=max(1, int(text[:-1] or "1")))
    if text.endswith("M"):
        return timedelta(minutes=max(1, int(text[:-1] or "1")))
    return timedelta(days=max(1, int(text[:-1] or "1") if text.endswith("D") else 1))


def _floor_quantity(value: float) -> float:
    return float(int(max(0.0, value)))


def _max_drawdown(values: list[float]) -> float:
    peak = 0.0
    drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        if peak:
            drawdown = min(drawdown, round((value - peak) / peak, 6))
    return drawdown


def _audit(event_type: str, reference: str) -> dict[str, Any]:
    return {"event_type": event_type, "reference": reference, "mode": "replay"}


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _config_key(name: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in name.strip().lower())


def _coerce_config_value(value: Any, default: Any) -> Any:
    if isinstance(default, bool):
        return str(value).lower() in {"1", "true", "yes", "enabled"}
    if isinstance(default, tuple):
        return tuple(str(item).strip() for item in str(value).split(",") if str(item).strip())
    if isinstance(default, float):
        return _number(value)
    return value
