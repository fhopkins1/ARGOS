"""Stress Testing Engine for ARGOS EO-BC."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


SCENARIO_TYPES = (
    "market_drawdown",
    "sector_drawdown",
    "single_name_shock",
    "volatility_spike",
    "liquidity_crisis",
    "spread_widening",
    "correlated_selloff",
    "execution_failure",
    "data_outage",
    "combined_stress",
)


@dataclass(frozen=True)
class StressTestingConfig:
    stress_testing_enabled: bool = True
    default_market_shock_percent: float = -0.10
    default_volatility_multiplier: float = 2.0
    default_spread_multiplier: float = 3.0
    default_liquidity_multiplier: float = 0.50
    default_slippage_multiplier: float = 2.0
    moderate_stress_threshold: float = 30.0
    elevated_stress_threshold: float = 50.0
    high_stress_threshold: float = 70.0
    critical_stress_threshold: float = 85.0
    stop_cascade_count_threshold: int = 2
    stop_cascade_portfolio_percent_threshold: float = 0.25
    critical_drawdown_threshold: float = 0.15
    max_sector_exposure_percent: float = 0.35
    max_position_loss_percent: float = 0.08
    max_concentration_percent: float = 0.25
    minimum_buying_power_after_stress: float = 0.0
    conservative_stress_mode: bool = True
    degraded_data_policy: str = "conservative"


@dataclass(frozen=True)
class StressScenarioRecord:
    stress_scenario_id: str
    scenario_name: str
    scenario_type: str
    created_at: str
    market_shock_percent: float
    sector_shocks: dict[str, float]
    symbol_shocks: dict[str, float]
    volatility_multiplier: float
    spread_multiplier: float
    liquidity_multiplier: float
    slippage_multiplier: float
    correlation_shock: float
    benchmark_shocks: dict[str, float]
    data_outage_symbols: tuple[str, ...]
    broker_rejection_mode: str
    market_closed_mode: bool
    execution_degradation_mode: str
    assumptions: tuple[str, ...]
    configuration_snapshot: dict[str, Any]
    audit_reference: str


@dataclass(frozen=True)
class StressTestRecord:
    stress_test_id: str
    stress_scenario_id: str
    timestamp: str
    portfolio_equity_before: float
    stressed_portfolio_equity: float
    stressed_total_pnl: float
    stressed_total_pnl_percent: float
    stressed_drawdown_percent: float
    cash_after_stress: float
    buying_power_after_stress: float
    positions_tested: int
    positions_at_stop: int
    positions_below_stop: int
    positions_at_target_after_stress: int
    stressed_position_results: tuple[dict[str, Any], ...]
    sector_stress_results: tuple[dict[str, Any], ...]
    strategy_stress_results: tuple[dict[str, Any], ...]
    correlation_cluster_results: tuple[dict[str, Any], ...]
    liquidity_stress_results: tuple[dict[str, Any], ...]
    execution_stress_results: tuple[dict[str, Any], ...]
    risk_rule_violations: tuple[dict[str, Any], ...]
    margin_or_buying_power_warnings: tuple[str, ...]
    stop_cascade_risk: dict[str, Any]
    composite_stress_score: float
    stress_level: str
    recommended_actions: tuple[str, ...]
    degraded_inputs: tuple[str, ...]
    audit_reference: str


class StressTestingEngine:
    """Deterministic hostile-scenario evaluator with isolated analytical records."""

    def __init__(self, config: StressTestingConfig | None = None) -> None:
        self._config = config or StressTestingConfig()
        self._scenarios: list[StressScenarioRecord] = []
        self._tests: list[StressTestRecord] = []

    def create_scenario(
        self,
        *,
        scenario_name: str,
        scenario_type: str = "combined_stress",
        created_at: str,
        market_shock_percent: float | None = None,
        sector_shocks: dict[str, float] | None = None,
        symbol_shocks: dict[str, float] | None = None,
        volatility_multiplier: float | None = None,
        spread_multiplier: float | None = None,
        liquidity_multiplier: float | None = None,
        slippage_multiplier: float | None = None,
        correlation_shock: float = 0.0,
        benchmark_shocks: dict[str, float] | None = None,
        data_outage_symbols: tuple[str, ...] = (),
        broker_rejection_mode: str = "normal",
        market_closed_mode: bool = False,
        execution_degradation_mode: str = "normal",
        assumptions: tuple[str, ...] = (),
        configuration_snapshot: dict[str, Any] | None = None,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        config = self._resolved_config(enterprise_configuration_registry)
        normalized_type = scenario_type if scenario_type in SCENARIO_TYPES else "combined_stress"
        scenario = StressScenarioRecord(
            stress_scenario_id=f"STR-SCEN-{len(self._scenarios) + 1:06d}",
            scenario_name=scenario_name,
            scenario_type=normalized_type,
            created_at=created_at,
            market_shock_percent=_number(market_shock_percent if market_shock_percent is not None else config.default_market_shock_percent),
            sector_shocks={str(key): _number(value) for key, value in (sector_shocks or {}).items()},
            symbol_shocks={str(key).upper(): _number(value) for key, value in (symbol_shocks or {}).items()},
            volatility_multiplier=_number(volatility_multiplier if volatility_multiplier is not None else config.default_volatility_multiplier),
            spread_multiplier=max(1.0, _number(spread_multiplier if spread_multiplier is not None else config.default_spread_multiplier)),
            liquidity_multiplier=max(0.0, _number(liquidity_multiplier if liquidity_multiplier is not None else config.default_liquidity_multiplier)),
            slippage_multiplier=max(1.0, _number(slippage_multiplier if slippage_multiplier is not None else config.default_slippage_multiplier)),
            correlation_shock=_number(correlation_shock),
            benchmark_shocks={str(key).upper(): _number(value) for key, value in (benchmark_shocks or {}).items()},
            data_outage_symbols=tuple(str(symbol).upper() for symbol in data_outage_symbols),
            broker_rejection_mode=str(broker_rejection_mode or "normal"),
            market_closed_mode=bool(market_closed_mode),
            execution_degradation_mode=str(execution_degradation_mode or "normal"),
            assumptions=assumptions or ("Deterministic one-step stress; no live orders; no ledger mutation.",),
            configuration_snapshot=configuration_snapshot or {"stressTesting": asdict(config)},
            audit_reference=f"AE-STRESS-SCENARIO-{audit_event_count + len(self._scenarios) + 1:06d}",
        )
        self._scenarios.append(scenario)
        return self.snapshot(latest_scenario=scenario, timestamp_utc=created_at, config=config)

    def run_stress_test(
        self,
        *,
        scenario: dict[str, Any] | StressScenarioRecord,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any] | None = None,
        position_surveillance: dict[str, Any] | None = None,
        position_exit_decision: dict[str, Any] | None = None,
        enterprise_risk_factor: dict[str, Any] | None = None,
        correlation_intelligence: dict[str, Any] | None = None,
        portfolio_construction: dict[str, Any] | None = None,
        capital_allocation: dict[str, Any] | None = None,
        position_sizing: dict[str, Any] | None = None,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        config = self._resolved_config(enterprise_configuration_registry)
        if not config.stress_testing_enabled:
            return self.snapshot(timestamp_utc=timestamp_utc, config=config)
        scenario_record = _scenario_from_payload(scenario)
        portfolio = _portfolio_state(performance_truth)
        positions = tuple(dict(item) for item in _positions(performance_truth))
        quotes = _quotes(market_data_provider or {})
        degraded: list[str] = []
        if positions and not quotes:
            degraded.append("market_data_missing")
        if not (correlation_intelligence or {}).get("riskFactorFeed"):
            degraded.append("correlation_proxy_used")

        position_results = tuple(
            _position_stress_result(position, quotes.get(str(position.get("symbol", "")).upper(), {}), scenario_record, config, degraded)
            for position in positions
        )
        stressed_market_value = sum(item["stressed_value"] for item in position_results)
        equity_before = portfolio["portfolio_equity"]
        stressed_equity = round(portfolio["cash"] + stressed_market_value, 4)
        pnl = round(stressed_equity - equity_before, 4)
        pnl_percent = round(pnl / max(1.0, equity_before), 6)
        drawdown = round(max(0.0, -pnl_percent), 6)
        buying_power_after = round(portfolio["buying_power"] + pnl, 4)
        positions_at_stop = sum(1 for item in position_results if item["stop_triggered"] or item["trailing_stop_triggered"])
        positions_below_stop = sum(1 for item in position_results if item["below_stop"])
        positions_at_target = sum(1 for item in position_results if item["target_reached_after_stress"])
        sector_results = _bucket_results(position_results, "sector", equity_before)
        strategy_results = _bucket_results(position_results, "strategy", equity_before)
        cluster_results = _correlation_clusters(position_results, correlation_intelligence or {}, equity_before, degraded, scenario_record)
        liquidity_results = tuple(item["liquidity_stress"] for item in position_results)
        execution_results = tuple(item["execution_stress"] for item in position_results)
        risk_violations = _risk_rule_violations(position_results, sector_results, drawdown, buying_power_after, config, enterprise_risk_factor or {})
        buying_warnings = _buying_power_warnings(buying_power_after, config, performance_truth)
        cascade = _stop_cascade(position_results, equity_before, scenario_record, config)
        score = _composite_score(drawdown, positions_at_stop, position_results, cluster_results, liquidity_results, execution_results, risk_violations, degraded, config)
        level = _stress_level(score, config)
        actions = _recommended_actions(score, level, risk_violations, cascade, buying_warnings, degraded)
        record = StressTestRecord(
            stress_test_id=f"STR-TEST-{len(self._tests) + 1:06d}",
            stress_scenario_id=scenario_record.stress_scenario_id,
            timestamp=timestamp_utc,
            portfolio_equity_before=round(equity_before, 4),
            stressed_portfolio_equity=stressed_equity,
            stressed_total_pnl=pnl,
            stressed_total_pnl_percent=pnl_percent,
            stressed_drawdown_percent=drawdown,
            cash_after_stress=round(portfolio["cash"], 4),
            buying_power_after_stress=buying_power_after,
            positions_tested=len(position_results),
            positions_at_stop=positions_at_stop,
            positions_below_stop=positions_below_stop,
            positions_at_target_after_stress=positions_at_target,
            stressed_position_results=position_results,
            sector_stress_results=sector_results,
            strategy_stress_results=strategy_results,
            correlation_cluster_results=cluster_results,
            liquidity_stress_results=liquidity_results,
            execution_stress_results=execution_results,
            risk_rule_violations=risk_violations,
            margin_or_buying_power_warnings=buying_warnings,
            stop_cascade_risk=cascade,
            composite_stress_score=score,
            stress_level=level,
            recommended_actions=actions,
            degraded_inputs=tuple(dict.fromkeys(degraded)),
            audit_reference=f"AE-STRESS-TEST-{audit_event_count + len(self._tests) + 1:06d}",
        )
        self._tests.append(record)
        return self.snapshot(latest_scenario=scenario_record, latest_test=record, timestamp_utc=timestamp_utc, config=config)

    def snapshot(
        self,
        *,
        latest_scenario: StressScenarioRecord | None = None,
        latest_test: StressTestRecord | None = None,
        timestamp_utc: str = "",
        config: StressTestingConfig | None = None,
    ) -> dict[str, Any]:
        config = config or self._config
        latest_scenario = latest_scenario or (self._scenarios[-1] if self._scenarios else None)
        latest_test = latest_test or (self._tests[-1] if self._tests else None)
        feed = _integration_feed(latest_test)
        return {
            "engineName": "Stress Testing Engine",
            "engineeringOrder": "EO-BC",
            "constitutionalMode": "ANALYTICAL_STRESS_ONLY_NO_TRADING",
            "supportedScenarioTypes": SCENARIO_TYPES,
            "stressScenarioRecords": tuple(asdict(item) for item in self._scenarios),
            "stressTestRecords": tuple(asdict(item) for item in self._tests),
            "latestStressScenarioRecord": asdict(latest_scenario) if latest_scenario else {},
            "latestStressTestRecord": asdict(latest_test) if latest_test else {},
            "riskFactorFeed": feed,
            "portfolioConstructionFeed": feed,
            "capitalAllocationFeed": feed,
            "positionSizingFeed": feed,
            "traderCommandBridgeFeed": feed,
            "enterpriseHealthMetrics": {
                "latestCompositeStressScore": latest_test.composite_stress_score if latest_test else 0.0,
                "latestStressLevel": latest_test.stress_level if latest_test else "unknown",
                "stressRecordAge": "CURRENT" if latest_test and latest_test.timestamp == timestamp_utc else "RECENT" if latest_test else "NO_RECORD",
                "stopCascadeRisk": bool(latest_test and latest_test.stop_cascade_risk.get("cascadeRisk")),
                "riskRuleViolationCount": len(latest_test.risk_rule_violations) if latest_test else 0,
                "degradedStressInputs": len(latest_test.degraded_inputs) if latest_test else 0,
            },
            "commanderSummary": {
                "latestStressLevel": latest_test.stress_level if latest_test else "standby",
                "compositeStressScore": latest_test.composite_stress_score if latest_test else 0.0,
                "stressedDrawdownPercent": latest_test.stressed_drawdown_percent if latest_test else 0.0,
                "positionsAtStop": latest_test.positions_at_stop if latest_test else 0,
                "recommendedActions": latest_test.recommended_actions if latest_test else ("Create and run a stress scenario.",),
            },
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "boundedScenarioRequired": True, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicStressMechanics": True},
            "internalDiagnostics": {
                "mutatesPositions": False,
                "mutatesPortfolioLedger": False,
                "mutatesPerformanceTruth": False,
                "createsExecutionRecords": False,
                "createsClosedPositionTruth": False,
                "placesTrades": False,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "scenarioCount": len(self._scenarios),
                "testCount": len(self._tests),
                "timestamp": timestamp_utc,
            },
        }

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None) -> StressTestingConfig:
        values = asdict(self._config)
        for item in (enterprise_configuration_registry or {}).get("configurationRegistry", ()):
            key = _config_key(str(item.get("name", "")))
            if key in values:
                values[key] = _coerce_config_value(item.get("currentValue", values[key]), values[key])
        return StressTestingConfig(**values)


def _position_stress_result(position: dict[str, Any], quote: dict[str, Any], scenario: StressScenarioRecord, config: StressTestingConfig, degraded: list[str]) -> dict[str, Any]:
    symbol = str(position.get("symbol", "")).upper()
    sector = str(position.get("sector") or _sector_for(symbol))
    side = str(position.get("side", "LONG")).upper()
    quantity = abs(_number(position.get("quantity")))
    base_price = _number(quote.get("last") or quote.get("mid") or position.get("current_price") or position.get("average_cost"))
    if symbol in scenario.data_outage_symbols or not base_price:
        degraded.append(f"price_data_outage:{symbol}")
        base_price = _number(position.get("current_price") or position.get("average_cost"))
    shock = scenario.market_shock_percent + scenario.sector_shocks.get(sector, 0.0) + scenario.symbol_shocks.get(symbol, 0.0)
    if scenario.correlation_shock and sector != "UNKNOWN":
        shock += scenario.correlation_shock
    stressed_price = round(max(0.0001, base_price * (1 + shock)), 4)
    if side in {"SHORT", "SELL"}:
        stressed_pnl = round((_number(position.get("average_cost")) - stressed_price) * quantity, 4)
    else:
        stressed_pnl = round((stressed_price - _number(position.get("average_cost", base_price))) * quantity, 4)
    stressed_value = round(stressed_price * quantity, 4)
    stop = _number(position.get("stop_loss") or position.get("stopLoss"))
    target = _number(position.get("profit_target") or position.get("targetPrice") or position.get("target"))
    trailing = _number(position.get("trailing_stop") or position.get("trailingStop"))
    stop_triggered = bool(stop and ((side in {"SHORT", "SELL"} and stressed_price >= stop) or (side not in {"SHORT", "SELL"} and stressed_price <= stop)))
    trailing_triggered = bool(trailing and ((side in {"SHORT", "SELL"} and stressed_price >= trailing) or (side not in {"SHORT", "SELL"} and stressed_price <= trailing)))
    target_reached = bool(target and ((side in {"SHORT", "SELL"} and stressed_price <= target) or (side not in {"SHORT", "SELL"} and stressed_price >= target)))
    distance_stop = _distance(stressed_price, stop, side, is_stop=True)
    distance_target = _distance(stressed_price, target, side, is_stop=False)
    spread = _spread(quote, base_price) * scenario.spread_multiplier
    volume = _number(quote.get("volume") or quote.get("averageVolume"))
    stressed_volume = volume * scenario.liquidity_multiplier
    notional = stressed_value
    participation = notional / max(1.0, stressed_volume * stressed_price) if stressed_volume and stressed_price else 1.0
    slippage = round(notional * min(0.25, (spread / max(0.0001, stressed_price)) * scenario.slippage_multiplier + participation * 0.05), 4)
    fill_capacity = round(max(0.0, min(quantity, (stressed_volume * 0.01) if stressed_volume else 0.0)), 4)
    liquidation = round(max(0.0, stressed_value - slippage), 4)
    severity = _clamp(abs(stressed_pnl) / max(1.0, _number(position.get("current_value", stressed_value))) * 80 + (25 if stop_triggered or trailing_triggered else 0) + (15 if participation > 0.05 else 0))
    return {
        "position_id": str(position.get("position_id", "")),
        "symbol": symbol,
        "sector": sector,
        "strategy": str(position.get("currentStrategy") or position.get("strategy_id") or "UNKNOWN"),
        "asset_type": str(position.get("asset_type", "UNKNOWN")),
        "side": side,
        "quantity": quantity,
        "base_price": round(base_price, 4),
        "shock_percent": round(shock, 6),
        "stressed_price": stressed_price,
        "stressed_value": stressed_value,
        "stressed_unrealized_pnl": stressed_pnl,
        "stressed_unrealized_pnl_percent": round(stressed_pnl / max(1.0, _number(position.get("current_value", stressed_value))), 6),
        "distance_to_stop_after_stress": distance_stop,
        "distance_to_target_after_stress": distance_target,
        "stop_triggered": stop_triggered,
        "trailing_stop_triggered": trailing_triggered,
        "below_stop": bool(stop and ((side not in {"SHORT", "SELL"} and stressed_price < stop) or (side in {"SHORT", "SELL"} and stressed_price > stop))),
        "target_reached_after_stress": target_reached,
        "target_remains_plausible": not stop_triggered and not trailing_triggered and bool(target),
        "estimated_exit_slippage": slippage,
        "estimated_liquidation_proceeds": liquidation,
        "position_stress_severity": severity,
        "liquidity_stress": {
            "symbol": symbol,
            "liquidityMultiplier": scenario.liquidity_multiplier,
            "stressedVolume": round(stressed_volume, 4),
            "participationRate": round(participation, 6),
            "fillCapacity": fill_capacity,
            "liquiditySeverity": _clamp(participation * 120 + (1 - min(1.0, scenario.liquidity_multiplier)) * 45),
        },
        "execution_stress": {
            "symbol": symbol,
            "spreadMultiplier": scenario.spread_multiplier,
            "stressedSpread": round(spread, 6),
            "slippageMultiplier": scenario.slippage_multiplier,
            "estimatedSlippage": slippage,
            "partialFillLikely": fill_capacity < quantity,
            "rejectionLikely": scenario.broker_rejection_mode in {"reject_all", "strict"} or scenario.market_closed_mode,
            "executionSeverity": _clamp((scenario.spread_multiplier - 1) * 12 + (scenario.slippage_multiplier - 1) * 10 + (30 if fill_capacity < quantity else 0) + (40 if scenario.market_closed_mode else 0)),
        },
    }


def _portfolio_state(truth: dict[str, Any]) -> dict[str, float]:
    paper = truth.get("paperAccount", {})
    latest = (truth.get("portfolioLedger") or ({},))[-1]
    positions = _positions(truth)
    market = sum(_value(item) for item in positions)
    cash = _number(latest.get("cash", paper.get("cash", paper.get("buyingPower", 0.0))))
    equity = _number(latest.get("total_equity", cash + market)) or cash + market
    return {"cash": cash, "buying_power": _number(paper.get("buyingPower", cash)), "portfolio_equity": max(1.0, equity)}


def _positions(truth: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(truth.get("positionRegistry", {}).get("activePositions", ())) or tuple(truth.get("positionLedger", ()))


def _quotes(provider: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("symbol", "")).upper(): item for item in provider.get("normalizedObjects", {}).get("quotes", ())}


def _bucket_results(position_results: tuple[dict[str, Any], ...], key: str, equity: float) -> tuple[dict[str, Any], ...]:
    buckets: dict[str, dict[str, float]] = {}
    for item in position_results:
        name = str(item.get(key, "UNKNOWN") or "UNKNOWN")
        bucket = buckets.setdefault(name, {"stressed_value": 0.0, "stressed_pnl": 0.0, "stop_count": 0.0})
        bucket["stressed_value"] += _number(item.get("stressed_value"))
        bucket["stressed_pnl"] += _number(item.get("stressed_unrealized_pnl"))
        bucket["stop_count"] += 1 if item.get("stop_triggered") or item.get("trailing_stop_triggered") else 0
    return tuple(
        {
            key: name,
            "stressed_value": round(values["stressed_value"], 4),
            "stressed_pnl": round(values["stressed_pnl"], 4),
            "portfolio_weight_after_stress": round(values["stressed_value"] / max(1.0, equity), 6),
            "stop_count": int(values["stop_count"]),
        }
        for name, values in sorted(buckets.items())
    )


def _correlation_clusters(position_results: tuple[dict[str, Any], ...], correlation: dict[str, Any], equity: float, degraded: list[str], scenario: StressScenarioRecord) -> tuple[dict[str, Any], ...]:
    feed = correlation.get("riskFactorFeed", {})
    groups = tuple(feed.get("overlapGroups", ()))
    if not groups:
        grouped = _bucket_results(position_results, "sector", equity)
        return tuple({**item, "cluster_id": f"PROXY-SECTOR-{item['sector']}", "source": "sector_proxy", "shockPercent": scenario.market_shock_percent + scenario.sector_shocks.get(item["sector"], 0.0)} for item in grouped if item["sector"] != "UNKNOWN")
    by_symbol = {item["symbol"]: item for item in position_results}
    rows = []
    for group in groups:
        members = tuple(str(symbol).upper() for symbol in group.get("members", ()))
        member_rows = tuple(by_symbol[symbol] for symbol in members if symbol in by_symbol)
        if not member_rows:
            continue
        rows.append({
            "cluster_id": str(group.get("group_id", f"CORR-{len(rows) + 1:06d}")),
            "cluster_type": str(group.get("group_type", "overlap")),
            "members": members,
            "source": "EO-AH",
            "stressed_value": round(sum(item["stressed_value"] for item in member_rows), 4),
            "stressed_pnl": round(sum(item["stressed_unrealized_pnl"] for item in member_rows), 4),
            "portfolio_weight_after_stress": round(sum(item["stressed_value"] for item in member_rows) / max(1.0, equity), 6),
            "clusterSeverity": _clamp(abs(sum(item["stressed_unrealized_pnl"] for item in member_rows)) / max(1.0, equity) * 300 + len(member_rows) * 5),
        })
    return tuple(rows)


def _risk_rule_violations(position_results: tuple[dict[str, Any], ...], sector_results: tuple[dict[str, Any], ...], drawdown: float, buying_power: float, config: StressTestingConfig, risk_factor: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    if drawdown >= config.critical_drawdown_threshold:
        rows.append({"rule": "critical_drawdown_threshold", "value": drawdown, "limit": config.critical_drawdown_threshold, "severity": "CRITICAL"})
    for item in sector_results:
        if _number(item.get("portfolio_weight_after_stress")) > config.max_sector_exposure_percent:
            rows.append({"rule": "max_sector_exposure", "sector": item.get("sector"), "value": item.get("portfolio_weight_after_stress"), "limit": config.max_sector_exposure_percent, "severity": "HIGH"})
    for item in position_results:
        if abs(_number(item.get("stressed_unrealized_pnl_percent"))) > config.max_position_loss_percent:
            rows.append({"rule": "max_position_loss", "symbol": item.get("symbol"), "value": item.get("stressed_unrealized_pnl_percent"), "limit": -config.max_position_loss_percent, "severity": "HIGH"})
    largest_weight = max((_number(item.get("stressed_value")) for item in position_results), default=0.0)
    total = sum(_number(item.get("stressed_value")) for item in position_results)
    if total and largest_weight / max(1.0, total) > config.max_concentration_percent:
        rows.append({"rule": "max_concentration", "value": round(largest_weight / max(1.0, total), 6), "limit": config.max_concentration_percent, "severity": "HIGH"})
    if buying_power < config.minimum_buying_power_after_stress:
        rows.append({"rule": "minimum_buying_power_after_stress", "value": buying_power, "limit": config.minimum_buying_power_after_stress, "severity": "CRITICAL"})
    if risk_factor.get("riskOfficeFeed", {}).get("haltRecommended"):
        rows.append({"rule": "enterprise_risk_factor_halt_already_recommended", "value": True, "limit": False, "severity": "CRITICAL"})
    return tuple(rows)


def _stop_cascade(position_results: tuple[dict[str, Any], ...], equity: float, scenario: StressScenarioRecord, config: StressTestingConfig) -> dict[str, Any]:
    triggered = tuple(item for item in position_results if item["stop_triggered"] or item["trailing_stop_triggered"])
    liquidation = sum(item["estimated_liquidation_proceeds"] for item in triggered)
    percent = round(liquidation / max(1.0, equity), 6)
    cascade = len(triggered) >= config.stop_cascade_count_threshold or percent >= config.stop_cascade_portfolio_percent_threshold
    return {
        "cascadeRisk": cascade,
        "stopsTriggered": len(triggered),
        "portfolioPercentNeedingExit": percent,
        "expectedLiquidationPressure": round(liquidation, 4),
        "estimatedSlippageImpact": round(sum(item["estimated_exit_slippage"] for item in triggered), 4),
        "liquidityMultiplier": scenario.liquidity_multiplier,
        "recommendedMitigation": "request_risk_review" if cascade else "monitor",
    }


def _composite_score(drawdown: float, stop_count: int, positions: tuple[dict[str, Any], ...], clusters: tuple[dict[str, Any], ...], liquidity: tuple[dict[str, Any], ...], execution: tuple[dict[str, Any], ...], violations: tuple[dict[str, Any], ...], degraded: list[str], config: StressTestingConfig) -> float:
    drawdown_score = min(35.0, drawdown / max(0.0001, config.critical_drawdown_threshold) * 35)
    stop_score = min(20.0, stop_count / max(1, len(positions)) * 35)
    liquidity_score = min(15.0, sum(_number(item.get("liquiditySeverity")) for item in liquidity) / max(1, len(liquidity)) * 0.15)
    execution_score = min(12.0, sum(_number(item.get("executionSeverity")) for item in execution) / max(1, len(execution)) * 0.12)
    cluster_score = min(10.0, max((_number(item.get("clusterSeverity")) for item in clusters), default=0.0) * 0.12)
    violation_score = min(15.0, len(violations) * 4)
    data_score = min(10.0, len(set(degraded)) * 2.5)
    return _clamp(drawdown_score + stop_score + liquidity_score + execution_score + cluster_score + violation_score + data_score)


def _stress_level(score: float, config: StressTestingConfig) -> str:
    if score >= config.critical_stress_threshold:
        return "critical"
    if score >= config.high_stress_threshold:
        return "high"
    if score >= config.elevated_stress_threshold:
        return "elevated"
    if score >= config.moderate_stress_threshold:
        return "moderate"
    return "low"


def _recommended_actions(score: float, level: str, violations: tuple[dict[str, Any], ...], cascade: dict[str, Any], buying_warnings: tuple[str, ...], degraded: list[str]) -> tuple[str, ...]:
    actions: list[str] = []
    if level == "critical" or any(item.get("severity") == "CRITICAL" for item in violations):
        actions.extend(("halt_trading", "request_commander_review"))
    elif level in {"high", "elevated"}:
        actions.append("request_risk_review")
    if cascade.get("cascadeRisk"):
        actions.extend(("reduce_position", "increase_cash_reserve"))
    if any(item.get("rule") == "max_sector_exposure" for item in violations):
        actions.append("reduce_sector_exposure")
    if any(item.get("rule") == "max_concentration" for item in violations):
        actions.append("reduce_correlated_cluster")
    if buying_warnings:
        actions.append("block_new_positions")
    if degraded:
        actions.append("require_reality_calibration")
    if not actions:
        actions.append("no_action")
    return tuple(dict.fromkeys(actions))


def _integration_feed(record: StressTestRecord | None) -> dict[str, Any]:
    if not record:
        return {"stressTestingAvailable": False, "latestCompositeStressScore": 0.0, "stressLevel": "unknown", "recommendedActions": ("Run stress test.",)}
    return {
        "stressTestingAvailable": True,
        "latestStressTestId": record.stress_test_id,
        "latestCompositeStressScore": record.composite_stress_score,
        "stressLevel": record.stress_level,
        "stressedDrawdownPercent": record.stressed_drawdown_percent,
        "positionsAtStop": record.positions_at_stop,
        "stopCascadeRisk": record.stop_cascade_risk,
        "riskRuleViolations": record.risk_rule_violations,
        "recommendedActions": record.recommended_actions,
        "degradedInputs": record.degraded_inputs,
        "stressAdjustedCapitalMultiplier": 0.0 if record.stress_level == "critical" else 0.35 if record.stress_level == "high" else 0.65 if record.stress_level == "elevated" else 1.0,
        "stressAdjustedSizeMultiplier": 0.0 if record.stress_level == "critical" else 0.5 if record.stress_level == "high" else 0.75 if record.stress_level == "elevated" else 1.0,
    }


def _buying_power_warnings(buying_power: float, config: StressTestingConfig, truth: dict[str, Any]) -> tuple[str, ...]:
    warnings = []
    if buying_power < config.minimum_buying_power_after_stress:
        warnings.append("buying_power_negative_after_stress")
    if truth.get("brokerProfile", {}).get("marginPermissions") and buying_power < 0:
        warnings.append("margin_call_possible")
    return tuple(warnings)


def _scenario_from_payload(payload: dict[str, Any] | StressScenarioRecord) -> StressScenarioRecord:
    if isinstance(payload, StressScenarioRecord):
        return payload
    data = dict(payload)
    return StressScenarioRecord(**data)


def _distance(price: float, level: float, side: str, *, is_stop: bool) -> float:
    if not level:
        return 0.0
    if side in {"SHORT", "SELL"}:
        raw = (level - price) / max(0.0001, price) if is_stop else (price - level) / max(0.0001, price)
    else:
        raw = (price - level) / max(0.0001, price) if is_stop else (level - price) / max(0.0001, price)
    return round(raw, 6)


def _spread(quote: dict[str, Any], price: float) -> float:
    bid = _number(quote.get("bid"))
    ask = _number(quote.get("ask"))
    return max(0.01, ask - bid) if bid and ask else max(0.01, price * 0.001)


def _value(position: dict[str, Any]) -> float:
    return _number(position.get("current_value", position.get("market_value", _number(position.get("quantity")) * _number(position.get("current_price", position.get("average_cost"))))))


def _sector_for(symbol: str) -> str:
    return {"AAPL": "Technology", "MSFT": "Technology", "QQQ": "Technology", "SPY": "Broad Market", "TLT": "Rates", "GLD": "Commodities"}.get(symbol.upper(), "UNKNOWN")


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)


def _config_key(name: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in name.strip().lower())


def _coerce_config_value(value: Any, default: Any) -> Any:
    if isinstance(default, bool):
        return str(value).lower() in {"1", "true", "yes", "enabled"}
    if isinstance(default, int):
        return int(_number(value))
    if isinstance(default, float):
        raw = _number(value)
        return raw / 100 if abs(raw) > 1.0 and "percent" in str(default) else raw
    return value


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()
