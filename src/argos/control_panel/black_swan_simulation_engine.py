"""Black Swan Simulation Engine for ARGOS EO-BD."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SCENARIO_TYPES = (
    "market_crash",
    "flash_crash",
    "overnight_gap",
    "liquidity_vanishes",
    "trading_halt",
    "broker_restriction",
    "data_blackout",
    "correlated_collapse",
    "etf_dislocation",
    "stop_failure",
    "execution_failure",
    "combined_black_swan",
)


@dataclass(frozen=True)
class BlackSwanSimulationConfig:
    black_swan_simulation_enabled: bool = True
    default_market_gap_percent: float = -0.30
    default_volatility_multiplier: float = 5.0
    default_spread_multiplier: float = 20.0
    default_liquidity_collapse_factor: float = 0.05
    default_slippage_multiplier: float = 8.0
    default_recovery_assumption: str = "multi_session_uncertain"
    stop_failure_modeling_enabled: bool = True
    halt_modeling_enabled: bool = True
    broker_restriction_modeling_enabled: bool = True
    data_blackout_modeling_enabled: bool = True
    correlated_collapse_enabled: bool = True
    moderate_black_swan_threshold: float = 35.0
    high_black_swan_threshold: float = 65.0
    critical_black_swan_threshold: float = 85.0
    ruin_risk_critical_threshold: float = 80.0
    minimum_survival_score: float = 40.0
    conservative_black_swan_mode: bool = True


@dataclass(frozen=True)
class BlackSwanScenarioRecord:
    black_swan_scenario_id: str
    scenario_name: str
    scenario_type: str
    created_at: str
    market_gap_percent: float
    sector_gap_shocks: dict[str, float]
    symbol_gap_shocks: dict[str, float]
    volatility_multiplier: float
    spread_multiplier: float
    liquidity_collapse_factor: float
    slippage_multiplier: float
    correlation_to_one_enabled: bool
    trading_halt_symbols: tuple[str, ...]
    data_outage_symbols: tuple[str, ...]
    broker_restriction_mode: str
    stop_failure_mode: str
    execution_failure_mode: str
    recovery_assumption: str
    duration_assumption: str
    assumptions: tuple[str, ...]
    configuration_snapshot: dict[str, Any]
    audit_reference: str


@dataclass(frozen=True)
class BlackSwanSimulationRecord:
    black_swan_simulation_id: str
    black_swan_scenario_id: str
    timestamp: str
    portfolio_equity_before: float
    shocked_portfolio_equity: float
    shocked_total_pnl: float
    shocked_total_pnl_percent: float
    max_immediate_drawdown_percent: float
    cash_after_event: float
    buying_power_after_event: float
    positions_simulated: int
    positions_impaired: int
    positions_halted: int
    positions_unexitable: int
    positions_below_stop: int
    positions_gap_through_stop: int
    shocked_position_results: tuple[dict[str, Any], ...]
    sector_impairment_results: tuple[dict[str, Any], ...]
    strategy_impairment_results: tuple[dict[str, Any], ...]
    correlation_cluster_impairment: tuple[dict[str, Any], ...]
    liquidity_failure_results: tuple[dict[str, Any], ...]
    execution_failure_results: tuple[dict[str, Any], ...]
    data_failure_results: tuple[dict[str, Any], ...]
    broker_restriction_results: tuple[dict[str, Any], ...]
    stop_failure_results: tuple[dict[str, Any], ...]
    survival_score: float
    ruin_risk_score: float
    liquidity_survival_score: float
    execution_survival_score: float
    composite_black_swan_risk_score: float
    black_swan_level: str
    recommended_actions: tuple[str, ...]
    degraded_inputs: tuple[str, ...]
    audit_reference: str


class BlackSwanSimulationEngine:
    """Bounded discontinuity simulator that never mutates live trading state."""

    def __init__(self, config: BlackSwanSimulationConfig | None = None) -> None:
        self._config = config or BlackSwanSimulationConfig()
        self._scenarios: list[BlackSwanScenarioRecord] = []
        self._simulations: list[BlackSwanSimulationRecord] = []

    def create_scenario(
        self,
        *,
        scenario_name: str,
        created_at: str,
        scenario_type: str = "combined_black_swan",
        market_gap_percent: float | None = None,
        sector_gap_shocks: dict[str, float] | None = None,
        symbol_gap_shocks: dict[str, float] | None = None,
        volatility_multiplier: float | None = None,
        spread_multiplier: float | None = None,
        liquidity_collapse_factor: float | None = None,
        slippage_multiplier: float | None = None,
        correlation_to_one_enabled: bool | None = None,
        trading_halt_symbols: tuple[str, ...] = (),
        data_outage_symbols: tuple[str, ...] = (),
        broker_restriction_mode: str = "normal",
        stop_failure_mode: str = "gap_through_stop",
        execution_failure_mode: str = "degraded",
        recovery_assumption: str | None = None,
        duration_assumption: str = "one_discontinuous_event",
        assumptions: tuple[str, ...] = (),
        configuration_snapshot: dict[str, Any] | None = None,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        config = self._resolved_config(enterprise_configuration_registry)
        scenario = BlackSwanScenarioRecord(
            black_swan_scenario_id=f"BSW-SCEN-{len(self._scenarios) + 1:06d}",
            scenario_name=scenario_name,
            scenario_type=scenario_type if scenario_type in SCENARIO_TYPES else "combined_black_swan",
            created_at=created_at,
            market_gap_percent=_number(market_gap_percent if market_gap_percent is not None else config.default_market_gap_percent),
            sector_gap_shocks={str(key): _number(value) for key, value in (sector_gap_shocks or {}).items()},
            symbol_gap_shocks={str(key).upper(): _number(value) for key, value in (symbol_gap_shocks or {}).items()},
            volatility_multiplier=_number(volatility_multiplier if volatility_multiplier is not None else config.default_volatility_multiplier),
            spread_multiplier=max(1.0, _number(spread_multiplier if spread_multiplier is not None else config.default_spread_multiplier)),
            liquidity_collapse_factor=max(0.0, min(1.0, _number(liquidity_collapse_factor if liquidity_collapse_factor is not None else config.default_liquidity_collapse_factor))),
            slippage_multiplier=max(1.0, _number(slippage_multiplier if slippage_multiplier is not None else config.default_slippage_multiplier)),
            correlation_to_one_enabled=config.correlated_collapse_enabled if correlation_to_one_enabled is None else bool(correlation_to_one_enabled),
            trading_halt_symbols=tuple(str(symbol).upper() for symbol in trading_halt_symbols),
            data_outage_symbols=tuple(str(symbol).upper() for symbol in data_outage_symbols),
            broker_restriction_mode=str(broker_restriction_mode or "normal"),
            stop_failure_mode=str(stop_failure_mode or "gap_through_stop"),
            execution_failure_mode=str(execution_failure_mode or "degraded"),
            recovery_assumption=str(recovery_assumption or config.default_recovery_assumption),
            duration_assumption=duration_assumption,
            assumptions=assumptions or ("Discontinuous one-step event; no live orders; no ledger mutation.",),
            configuration_snapshot=configuration_snapshot or {"blackSwanSimulation": asdict(config)},
            audit_reference=f"AE-BLACK-SWAN-SCENARIO-{audit_event_count + len(self._scenarios) + 1:06d}",
        )
        self._scenarios.append(scenario)
        return self.snapshot(latest_scenario=scenario, timestamp_utc=created_at, config=config)

    def run_simulation(
        self,
        *,
        scenario: dict[str, Any] | BlackSwanScenarioRecord,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any] | None = None,
        correlation_intelligence: dict[str, Any] | None = None,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        config = self._resolved_config(enterprise_configuration_registry)
        if not config.black_swan_simulation_enabled:
            return self.snapshot(timestamp_utc=timestamp_utc, config=config)
        scenario_record = _scenario_from_payload(scenario)
        portfolio = _portfolio_state(performance_truth)
        positions = tuple(dict(item) for item in _positions(performance_truth))
        quotes = _quotes(market_data_provider or {})
        degraded: list[str] = []
        if positions and not quotes:
            degraded.append("market_data_blackout")
        if not (correlation_intelligence or {}).get("riskFactorFeed"):
            degraded.append("correlation_proxy_used")

        results = tuple(_position_result(position, quotes.get(str(position.get("symbol", "")).upper(), {}), scenario_record, config, degraded) for position in positions)
        shocked_market_value = sum(item["shocked_value"] for item in results)
        equity_before = portfolio["portfolio_equity"]
        shocked_equity = round(portfolio["cash"] + shocked_market_value, 4)
        pnl = round(shocked_equity - equity_before, 4)
        pnl_percent = round(pnl / max(1.0, equity_before), 6)
        drawdown = round(max(0.0, -pnl_percent), 6)
        buying_power = round(portfolio["buying_power"] + pnl, 4)
        sector = _bucket_results(results, "sector", equity_before)
        strategy = _bucket_results(results, "strategy", equity_before)
        clusters = _clusters(results, correlation_intelligence or {}, equity_before, scenario_record)
        liquidity = tuple(item["liquidity_failure"] for item in results)
        execution = tuple(item["execution_failure"] for item in results)
        data = tuple(item["data_failure"] for item in results if item["data_failure"]["dataState"] != "AVAILABLE")
        broker = tuple(item["broker_restriction"] for item in results if item["broker_restriction"]["restricted"])
        stops = tuple(item["stop_failure"] for item in results if item["stop_failure"]["stopFailure"])
        liquidity_survival = _survival_from_failures(liquidity, "liquidityFailureSeverity")
        execution_survival = _survival_from_failures(execution, "executionFailureSeverity")
        stop_score = _survival_from_failures(stops, "stopFailureSeverity") if stops else 100.0
        data_score = max(0.0, 100.0 - len(data) / max(1, len(results)) * 70.0)
        survival = _clamp(100 - drawdown * 180 - (100 - liquidity_survival) * 0.25 - (100 - execution_survival) * 0.25 - (100 - stop_score) * 0.2 - (100 - data_score) * 0.1)
        ruin = _clamp(drawdown * 220 + sum(1 for item in results if item["unexitable"]) / max(1, len(results)) * 35 + (100 - liquidity_survival) * 0.2 + (100 - execution_survival) * 0.2)
        composite = _clamp((100 - survival) * 0.45 + ruin * 0.35 + (100 - liquidity_survival) * 0.10 + (100 - execution_survival) * 0.10)
        level = _level(composite, ruin, config)
        actions = _actions(level, survival, ruin, liquidity, execution, data, stops, broker, degraded)
        record = BlackSwanSimulationRecord(
            black_swan_simulation_id=f"BSW-SIM-{len(self._simulations) + 1:06d}",
            black_swan_scenario_id=scenario_record.black_swan_scenario_id,
            timestamp=timestamp_utc,
            portfolio_equity_before=round(equity_before, 4),
            shocked_portfolio_equity=shocked_equity,
            shocked_total_pnl=pnl,
            shocked_total_pnl_percent=pnl_percent,
            max_immediate_drawdown_percent=drawdown,
            cash_after_event=round(portfolio["cash"], 4),
            buying_power_after_event=buying_power,
            positions_simulated=len(results),
            positions_impaired=sum(1 for item in results if item["impaired"]),
            positions_halted=sum(1 for item in results if item["halted"]),
            positions_unexitable=sum(1 for item in results if item["unexitable"]),
            positions_below_stop=sum(1 for item in results if item["below_stop"]),
            positions_gap_through_stop=sum(1 for item in results if item["gap_through_stop"]),
            shocked_position_results=results,
            sector_impairment_results=sector,
            strategy_impairment_results=strategy,
            correlation_cluster_impairment=clusters,
            liquidity_failure_results=liquidity,
            execution_failure_results=execution,
            data_failure_results=data,
            broker_restriction_results=broker,
            stop_failure_results=stops,
            survival_score=survival,
            ruin_risk_score=ruin,
            liquidity_survival_score=liquidity_survival,
            execution_survival_score=execution_survival,
            composite_black_swan_risk_score=composite,
            black_swan_level=level,
            recommended_actions=actions,
            degraded_inputs=tuple(dict.fromkeys(degraded)),
            audit_reference=f"AE-BLACK-SWAN-SIMULATION-{audit_event_count + len(self._simulations) + 1:06d}",
        )
        self._simulations.append(record)
        return self.snapshot(latest_scenario=scenario_record, latest_simulation=record, timestamp_utc=timestamp_utc, config=config)

    def snapshot(
        self,
        *,
        latest_scenario: BlackSwanScenarioRecord | None = None,
        latest_simulation: BlackSwanSimulationRecord | None = None,
        timestamp_utc: str = "",
        config: BlackSwanSimulationConfig | None = None,
    ) -> dict[str, Any]:
        config = config or self._config
        latest_scenario = latest_scenario or (self._scenarios[-1] if self._scenarios else None)
        latest_simulation = latest_simulation or (self._simulations[-1] if self._simulations else None)
        feed = _feed(latest_simulation)
        return {
            "engineName": "Black Swan Simulation Engine",
            "engineeringOrder": "EO-BD",
            "constitutionalMode": "EXTREME_EVENT_ANALYTICS_ONLY_NO_TRADING",
            "supportedScenarioTypes": SCENARIO_TYPES,
            "blackSwanScenarioRecords": tuple(asdict(item) for item in self._scenarios),
            "blackSwanSimulationRecords": tuple(asdict(item) for item in self._simulations),
            "latestBlackSwanScenarioRecord": asdict(latest_scenario) if latest_scenario else {},
            "latestBlackSwanSimulationRecord": asdict(latest_simulation) if latest_simulation else {},
            "riskFactorFeed": feed,
            "correlationIntelligenceFeed": feed,
            "portfolioConstructionFeed": feed,
            "capitalAllocationFeed": feed,
            "positionSizingFeed": feed,
            "traderCommandBridgeFeed": feed,
            "enterpriseHealthMetrics": {
                "latestCompositeBlackSwanRiskScore": latest_simulation.composite_black_swan_risk_score if latest_simulation else 0.0,
                "latestBlackSwanLevel": latest_simulation.black_swan_level if latest_simulation else "unknown",
                "latestSurvivalScore": latest_simulation.survival_score if latest_simulation else 100.0,
                "latestRuinRiskScore": latest_simulation.ruin_risk_score if latest_simulation else 0.0,
                "unexitablePositions": latest_simulation.positions_unexitable if latest_simulation else 0,
                "degradedBlackSwanInputs": len(latest_simulation.degraded_inputs) if latest_simulation else 0,
                "simulationRecordAge": "CURRENT" if latest_simulation and latest_simulation.timestamp == timestamp_utc else "RECENT" if latest_simulation else "NO_RECORD",
            },
            "commanderSummary": {
                "latestBlackSwanLevel": latest_simulation.black_swan_level if latest_simulation else "standby",
                "survivalScore": latest_simulation.survival_score if latest_simulation else 100.0,
                "ruinRiskScore": latest_simulation.ruin_risk_score if latest_simulation else 0.0,
                "positionsUnexitable": latest_simulation.positions_unexitable if latest_simulation else 0,
                "recommendedActions": latest_simulation.recommended_actions if latest_simulation else ("Create and run a black swan scenario.",),
            },
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "boundedScenarioRequired": True, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicSimulation": True},
            "internalDiagnostics": {
                "mutatesPositions": False,
                "mutatesPortfolioLedger": False,
                "mutatesPerformanceTruth": False,
                "createsExecutionRecords": False,
                "createsClosedPositionTruth": False,
                "placesTrades": False,
                "modifiesStrategyState": False,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "scenarioCount": len(self._scenarios),
                "simulationCount": len(self._simulations),
                "timestamp": timestamp_utc,
            },
        }

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None) -> BlackSwanSimulationConfig:
        values = asdict(self._config)
        for item in (enterprise_configuration_registry or {}).get("configurationRegistry", ()):
            key = _config_key(str(item.get("name", "")))
            if key in values:
                values[key] = _coerce_config_value(item.get("currentValue", values[key]), values[key])
        return BlackSwanSimulationConfig(**values)


def _position_result(position: dict[str, Any], quote: dict[str, Any], scenario: BlackSwanScenarioRecord, config: BlackSwanSimulationConfig, degraded: list[str]) -> dict[str, Any]:
    symbol = str(position.get("symbol", "")).upper()
    sector = str(position.get("sector") or _sector_for(symbol))
    strategy = str(position.get("currentStrategy") or position.get("strategy_id") or "UNKNOWN")
    quantity = abs(_number(position.get("quantity")))
    pre_price = _number(quote.get("last") or position.get("current_price") or position.get("average_cost"))
    data_out = symbol in scenario.data_outage_symbols
    if data_out or not pre_price:
        degraded.append(f"data_blackout:{symbol}")
        pre_price = _number(position.get("current_price") or position.get("average_cost"))
    gap = scenario.market_gap_percent + scenario.sector_gap_shocks.get(sector, 0.0) + scenario.symbol_gap_shocks.get(symbol, 0.0)
    if scenario.correlation_to_one_enabled and sector != "UNKNOWN":
        gap += min(0.0, scenario.market_gap_percent * 0.35)
    shocked_price = round(max(0.0001, pre_price * (1 + gap)), 4)
    value = round(quantity * shocked_price, 4)
    average = _number(position.get("average_cost", pre_price))
    pnl = round((shocked_price - average) * quantity, 4)
    stop = _number(position.get("stop_loss") or position.get("stopLoss"))
    gap_through_stop = bool(config.stop_failure_modeling_enabled and stop and pre_price > stop and shocked_price < stop)
    below_stop = bool(stop and shocked_price < stop)
    halted = bool(config.halt_modeling_enabled and symbol in scenario.trading_halt_symbols)
    sell_disabled = config.broker_restriction_modeling_enabled and scenario.broker_restriction_mode in {"sell_disabled", "reject_all", "symbol_restricted"}
    execution_failed = scenario.execution_failure_mode in {"reject_all", "failed", "no_market_orders"} or sell_disabled
    volume = _number(quote.get("volume") or quote.get("averageVolume"))
    collapsed_volume = volume * scenario.liquidity_collapse_factor
    fill_capacity = 0.0 if halted or execution_failed else min(quantity, collapsed_volume * 0.005 if collapsed_volume else 0.0)
    unexitable = halted or sell_disabled or fill_capacity <= 0.0
    spread = _spread(quote, pre_price) * scenario.spread_multiplier
    slippage_beyond_stop = round(max(0.0, (stop - shocked_price) * quantity) if stop else 0.0, 4)
    stop_failure_severity = _clamp((slippage_beyond_stop / max(1.0, _number(position.get("current_value", value)))) * 140 + (35 if gap_through_stop else 0) + (25 if unexitable and below_stop else 0))
    liquidity_severity = _clamp((1 - scenario.liquidity_collapse_factor) * 75 + (40 if fill_capacity <= 0 else 0) + min(20.0, spread / max(0.0001, shocked_price) * 100))
    execution_severity = _clamp((scenario.spread_multiplier - 1) * 2 + (scenario.slippage_multiplier - 1) * 4 + (45 if execution_failed else 0) + (35 if halted else 0))
    data_state = "BLACKOUT" if data_out else "STALE_OR_LIMITED" if not quote else "AVAILABLE"
    data_severity = 75.0 if data_state == "BLACKOUT" else 25.0 if data_state == "STALE_OR_LIMITED" else 0.0
    impaired = drawdown_like(pnl, position) > 0.15 or unexitable or gap_through_stop or data_out
    return {
        "position_id": str(position.get("position_id", "")),
        "symbol": symbol,
        "sector": sector,
        "strategy": strategy,
        "quantity": quantity,
        "pre_event_price": round(pre_price, 4),
        "market_gap_percent": round(gap, 6),
        "shocked_price": shocked_price,
        "shocked_value": value,
        "shocked_unrealized_pnl": pnl,
        "shocked_unrealized_pnl_percent": round(pnl / max(1.0, _number(position.get("current_value", value))), 6),
        "halted": halted,
        "unexitable": unexitable,
        "impaired": impaired,
        "below_stop": below_stop,
        "gap_through_stop": gap_through_stop,
        "estimated_executable_price": 0.0 if unexitable else round(max(0.0001, shocked_price - spread / 2 - shocked_price * 0.01 * scenario.slippage_multiplier), 4),
        "executable_quantity": round(fill_capacity, 4),
        "residual_exposure": round(max(0.0, quantity - fill_capacity) * shocked_price, 4),
        "liquidation_uncertainty": "EXTREME" if unexitable else "HIGH" if scenario.liquidity_collapse_factor < 0.15 else "ELEVATED",
        "liquidity_failure": {
            "symbol": symbol,
            "liquidityCollapseFactor": scenario.liquidity_collapse_factor,
            "collapsedVolume": round(collapsed_volume, 4),
            "executableQuantity": round(fill_capacity, 4),
            "marketOrderDanger": "EXTREME" if scenario.spread_multiplier >= 10 or fill_capacity <= 0 else "HIGH",
            "liquidityFailureSeverity": liquidity_severity,
        },
        "execution_failure": {
            "symbol": symbol,
            "spreadMultiplier": scenario.spread_multiplier,
            "explodedSpread": round(spread, 6),
            "executionFailureMode": scenario.execution_failure_mode,
            "marketOrdersDisabled": scenario.execution_failure_mode in {"no_market_orders", "failed"},
            "executionFailureSeverity": execution_severity,
        },
        "data_failure": {"symbol": symbol, "dataState": data_state, "dataFailureSeverity": data_severity},
        "broker_restriction": {"symbol": symbol, "mode": scenario.broker_restriction_mode, "restricted": sell_disabled or scenario.broker_restriction_mode not in {"normal", ""}},
        "stop_failure": {
            "symbol": symbol,
            "stopLevel": stop,
            "preEventPrice": round(pre_price, 4),
            "shockedPrice": shocked_price,
            "gapThroughStop": gap_through_stop,
            "stopFailure": gap_through_stop or (below_stop and unexitable),
            "slippageBeyondStop": slippage_beyond_stop,
            "stopFailureSeverity": stop_failure_severity,
            "residualExposure": round(max(0.0, quantity - fill_capacity) * shocked_price, 4),
            "liquidationUncertainty": "EXTREME" if unexitable else "HIGH" if gap_through_stop else "NORMAL",
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


def _bucket_results(results: tuple[dict[str, Any], ...], key: str, equity: float) -> tuple[dict[str, Any], ...]:
    buckets: dict[str, dict[str, float]] = {}
    for item in results:
        name = str(item.get(key, "UNKNOWN") or "UNKNOWN")
        bucket = buckets.setdefault(name, {"value": 0.0, "pnl": 0.0, "impaired": 0.0, "unexitable": 0.0})
        bucket["value"] += _number(item.get("shocked_value"))
        bucket["pnl"] += _number(item.get("shocked_unrealized_pnl"))
        bucket["impaired"] += 1 if item.get("impaired") else 0
        bucket["unexitable"] += 1 if item.get("unexitable") else 0
    return tuple({key: name, "shocked_value": round(row["value"], 4), "shocked_pnl": round(row["pnl"], 4), "portfolio_weight_after_event": round(row["value"] / max(1.0, equity), 6), "impaired_count": int(row["impaired"]), "unexitable_count": int(row["unexitable"])} for name, row in sorted(buckets.items()))


def _clusters(results: tuple[dict[str, Any], ...], correlation: dict[str, Any], equity: float, scenario: BlackSwanScenarioRecord) -> tuple[dict[str, Any], ...]:
    groups = tuple(correlation.get("riskFactorFeed", {}).get("overlapGroups", ()))
    if not groups:
        return tuple({**item, "cluster_id": f"PROXY-SECTOR-{item['sector']}", "source": "sector_proxy"} for item in _bucket_results(results, "sector", equity) if item["sector"] != "UNKNOWN")
    by_symbol = {item["symbol"]: item for item in results}
    rows = []
    for group in groups:
        members = tuple(str(symbol).upper() for symbol in group.get("members", ()))
        matched = tuple(by_symbol[symbol] for symbol in members if symbol in by_symbol)
        if matched:
            rows.append({"cluster_id": str(group.get("group_id", f"BSW-CORR-{len(rows) + 1:06d}")), "source": "EO-AH", "members": members, "correlationToOne": scenario.correlation_to_one_enabled, "shocked_value": round(sum(item["shocked_value"] for item in matched), 4), "shocked_pnl": round(sum(item["shocked_unrealized_pnl"] for item in matched), 4), "clusterImpairmentSeverity": _clamp(abs(sum(item["shocked_unrealized_pnl"] for item in matched)) / max(1.0, equity) * 300 + len(matched) * 10)})
    return tuple(rows)


def _survival_from_failures(rows: tuple[dict[str, Any], ...], key: str) -> float:
    if not rows:
        return 100.0
    return _clamp(100.0 - sum(_number(item.get(key)) for item in rows) / max(1, len(rows)))


def _level(composite: float, ruin: float, config: BlackSwanSimulationConfig) -> str:
    if composite >= config.critical_black_swan_threshold or ruin >= config.ruin_risk_critical_threshold:
        return "critical"
    if composite >= config.high_black_swan_threshold:
        return "high"
    if composite >= config.moderate_black_swan_threshold:
        return "elevated"
    return "low"


def _actions(level: str, survival: float, ruin: float, liquidity: tuple[dict[str, Any], ...], execution: tuple[dict[str, Any], ...], data: tuple[dict[str, Any], ...], stops: tuple[dict[str, Any], ...], broker: tuple[dict[str, Any], ...], degraded: list[str]) -> tuple[str, ...]:
    actions: list[str] = []
    if level == "critical" or survival < 30 or ruin > 80:
        actions.extend(("halt_trading", "request_commander_review"))
    elif level in {"high", "elevated"}:
        actions.append("request_risk_review")
    if any(_number(item.get("liquidityFailureSeverity")) >= 60 for item in liquidity):
        actions.extend(("reduce_illiquid_exposure", "avoid_market_orders", "require_limit_orders"))
    if any(_number(item.get("executionFailureSeverity")) >= 60 for item in execution) or broker:
        actions.append("block_new_positions")
    if stops:
        actions.extend(("tighten_risk_budget", "increase_cash_reserve"))
    if data or degraded:
        actions.extend(("require_data_quality_repair", "require_reality_calibration"))
    if not actions:
        actions.append("no_action")
    return tuple(dict.fromkeys(actions))


def _feed(record: BlackSwanSimulationRecord | None) -> dict[str, Any]:
    if not record:
        return {"blackSwanSimulationAvailable": False, "latestCompositeBlackSwanRiskScore": 0.0, "blackSwanLevel": "unknown", "recommendedActions": ("Run black swan simulation.",)}
    return {
        "blackSwanSimulationAvailable": True,
        "latestBlackSwanSimulationId": record.black_swan_simulation_id,
        "latestCompositeBlackSwanRiskScore": record.composite_black_swan_risk_score,
        "blackSwanLevel": record.black_swan_level,
        "survivalScore": record.survival_score,
        "ruinRiskScore": record.ruin_risk_score,
        "positionsUnexitable": record.positions_unexitable,
        "positionsGapThroughStop": record.positions_gap_through_stop,
        "recommendedActions": record.recommended_actions,
        "degradedInputs": record.degraded_inputs,
        "blackSwanAdjustedCapitalMultiplier": 0.0 if record.black_swan_level == "critical" else 0.35 if record.black_swan_level == "high" else 0.65 if record.black_swan_level == "elevated" else 1.0,
        "blackSwanAdjustedSizeMultiplier": 0.0 if record.black_swan_level == "critical" else 0.5 if record.black_swan_level == "high" else 0.75 if record.black_swan_level == "elevated" else 1.0,
    }


def _scenario_from_payload(payload: dict[str, Any] | BlackSwanScenarioRecord) -> BlackSwanScenarioRecord:
    if isinstance(payload, BlackSwanScenarioRecord):
        return payload
    return BlackSwanScenarioRecord(**dict(payload))


def drawdown_like(pnl: float, position: dict[str, Any]) -> float:
    return abs(min(0.0, pnl)) / max(1.0, _number(position.get("current_value", 0.0)))


def _spread(quote: dict[str, Any], price: float) -> float:
    bid = _number(quote.get("bid"))
    ask = _number(quote.get("ask"))
    return max(0.01, ask - bid) if bid and ask else max(0.01, price * 0.002)


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
