"""Monte Carlo Portfolio Engine for ARGOS EO-BE."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import random
from typing import Any


@dataclass(frozen=True)
class MonteCarloPortfolioConfig:
    monte_carlo_enabled: bool = True
    default_simulation_count: int = 250
    maximum_simulation_count: int = 1000
    default_time_horizon: int = 20
    maximum_time_horizon: int = 252
    default_time_step: str = "1D"
    default_return_model: str = "seeded_correlated_gaussian"
    default_random_seed_policy: str = "explicit_seed_required"
    fat_tail_mode: str = "conservative_shock_overlay"
    jump_risk_mode: str = "seeded_rare_jump"
    default_loss_threshold: float = -0.05
    default_ruin_threshold: float = -0.30
    default_target_return: float = 0.05
    value_at_risk_confidence: float = 0.95
    expected_shortfall_confidence: float = 0.95
    path_storage_enabled: bool = False
    sampled_path_count: int = 5
    degraded_data_policy: str = "conservative"
    conservative_assumption_mode: bool = True
    minimum_model_confidence: float = 55.0


@dataclass(frozen=True)
class MonteCarloScenarioRecord:
    monte_carlo_scenario_id: str
    scenario_name: str
    created_at: str
    portfolio_snapshot_reference: str
    simulation_count: int
    time_horizon: int
    time_step: str
    random_seed: int
    return_model: str
    volatility_model: str
    correlation_model: str
    drift_assumptions: dict[str, float]
    volatility_assumptions: dict[str, float]
    correlation_assumptions: dict[str, Any]
    fat_tail_assumptions: dict[str, Any]
    jump_risk_assumptions: dict[str, Any]
    liquidity_assumptions: dict[str, Any]
    execution_cost_assumptions: dict[str, Any]
    rebalance_policy: str
    cash_flow_assumptions: dict[str, Any]
    benchmark_symbols: tuple[str, ...]
    configuration_snapshot: dict[str, Any]
    model_version: str
    audit_reference: str


@dataclass(frozen=True)
class MonteCarloResultRecord:
    monte_carlo_result_id: str
    monte_carlo_scenario_id: str
    started_at: str
    completed_at: str
    simulation_count_completed: int
    status: str
    initial_portfolio_equity: float
    terminal_value_mean: float
    terminal_value_median: float
    terminal_value_percentiles: dict[str, float]
    return_mean: float
    return_median: float
    return_percentiles: dict[str, float]
    volatility_estimate: float
    max_drawdown_mean: float
    max_drawdown_median: float
    max_drawdown_percentiles: dict[str, float]
    probability_of_loss: float
    probability_of_target_achievement: float
    probability_of_drawdown_threshold_breach: float
    probability_of_ruin: float
    probability_of_liquidity_failure: float
    probability_of_stop_cascade: float
    expected_shortfall: float
    value_at_risk: float
    benchmark_comparison: dict[str, Any]
    strategy_contribution_distribution: tuple[dict[str, Any], ...]
    concentration_failure_probability: float
    correlation_failure_probability: float
    model_confidence: float
    degraded_inputs: tuple[str, ...]
    reproducibility_hash: str
    recommended_actions: tuple[str, ...]
    audit_reference: str


class MonteCarloPortfolioEngine:
    """Bounded seeded portfolio distribution estimator."""

    def __init__(self, config: MonteCarloPortfolioConfig | None = None) -> None:
        self._config = config or MonteCarloPortfolioConfig()
        self._scenarios: list[MonteCarloScenarioRecord] = []
        self._results: list[MonteCarloResultRecord] = []

    def create_scenario(
        self,
        *,
        scenario_name: str,
        created_at: str,
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any] | None = None,
        correlation_intelligence: dict[str, Any] | None = None,
        simulation_count: int | None = None,
        time_horizon: int | None = None,
        random_seed: int = 1729,
        return_model: str | None = None,
        rebalance_policy: str = "no_rebalance",
        benchmark_symbols: tuple[str, ...] = ("SPY", "QQQ", "CASH"),
        enterprise_configuration_registry: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        config = self._resolved_config(enterprise_configuration_registry)
        count = min(max(1, int(simulation_count or config.default_simulation_count)), config.maximum_simulation_count)
        horizon = min(max(1, int(time_horizon or config.default_time_horizon)), config.maximum_time_horizon)
        positions = _positions(performance_truth)
        symbols = tuple(str(position.get("symbol", "")).upper() for position in positions)
        degraded: list[str] = []
        drifts, vols = _drift_volatility(symbols, market_data_provider or {}, degraded)
        corr, corr_mode = _correlation(symbols, correlation_intelligence or {}, degraded)
        scenario = MonteCarloScenarioRecord(
            monte_carlo_scenario_id=f"MCP-SCEN-{len(self._scenarios) + 1:06d}",
            scenario_name=scenario_name,
            created_at=created_at,
            portfolio_snapshot_reference=_hash(performance_truth)[:24],
            simulation_count=count,
            time_horizon=horizon,
            time_step=config.default_time_step,
            random_seed=int(random_seed),
            return_model=return_model or config.default_return_model,
            volatility_model="historical_returns_or_conservative_fallback",
            correlation_model=corr_mode,
            drift_assumptions=drifts,
            volatility_assumptions=vols,
            correlation_assumptions={"symbols": symbols, "matrix": corr, "degradedInputs": tuple(dict.fromkeys(degraded))},
            fat_tail_assumptions={"mode": config.fat_tail_mode, "shockEveryApproxPaths": 20},
            jump_risk_assumptions={"mode": config.jump_risk_mode, "jumpProbability": 0.03, "jumpMagnitude": -0.08},
            liquidity_assumptions={"liquidityFailureThreshold": 0.08, "missingLiquidityPolicy": config.degraded_data_policy},
            execution_cost_assumptions={"spreadCostBps": 5, "slippageCostBps": 10},
            rebalance_policy=rebalance_policy,
            cash_flow_assumptions={"externalCashFlows": 0.0},
            benchmark_symbols=benchmark_symbols,
            configuration_snapshot={"monteCarloPortfolio": asdict(config)},
            model_version="EO-BE-MC-1.0",
            audit_reference=f"AE-MONTE-CARLO-SCENARIO-{audit_event_count + len(self._scenarios) + 1:06d}",
        )
        self._scenarios.append(scenario)
        return self.snapshot(latest_scenario=scenario, timestamp_utc=created_at, config=config)

    def run_simulation(
        self,
        *,
        scenario: dict[str, Any] | MonteCarloScenarioRecord,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any] | None = None,
        correlation_intelligence: dict[str, Any] | None = None,
        enterprise_benchmark_engine: dict[str, Any] | None = None,
        enterprise_reality_calibration: dict[str, Any] | None = None,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        config = self._resolved_config(enterprise_configuration_registry)
        if not config.monte_carlo_enabled:
            return self.snapshot(timestamp_utc=timestamp_utc, config=config)
        scenario_record = _scenario_from_payload(scenario)
        portfolio = _portfolio_state(performance_truth)
        positions = tuple(dict(item) for item in _positions(performance_truth))[:20]
        degraded = list(scenario_record.correlation_assumptions.get("degradedInputs", ()))
        if len(_positions(performance_truth)) > len(positions):
            degraded.append("asset_count_bounded")
        rng = random.Random(scenario_record.random_seed)
        symbols = tuple(str(position.get("symbol", "")).upper() for position in positions)
        corr = scenario_record.correlation_assumptions.get("matrix", {})
        cholesky = _safe_cholesky(symbols, corr, degraded)
        weights = _weights(positions, portfolio["portfolio_equity"])
        terminal_values: list[float] = []
        returns: list[float] = []
        drawdowns: list[float] = []
        path_vols: list[float] = []
        losses = targets = drawdown_breaches = ruins = liquidity_failures = stop_cascades = concentration_failures = correlation_failures = 0
        strategy_returns: dict[str, list[float]] = {}

        for _ in range(scenario_record.simulation_count):
            equity = portfolio["portfolio_equity"]
            peak = equity
            min_equity = equity
            path_returns: list[float] = []
            stop_trigger_steps = 0
            strategy_path: dict[str, float] = {}
            for step in range(scenario_record.time_horizon):
                normals = _correlated_normals(rng, cholesky)
                portfolio_return = 0.0
                simultaneous_stops = 0
                for index, position in enumerate(positions):
                    symbol = symbols[index]
                    drift = scenario_record.drift_assumptions.get(symbol, 0.0)
                    vol = scenario_record.volatility_assumptions.get(symbol, 0.02)
                    asset_return = drift + vol * normals[index]
                    if scenario_record.jump_risk_assumptions.get("mode") != "disabled" and rng.random() < _number(scenario_record.jump_risk_assumptions.get("jumpProbability", 0.0)):
                        asset_return += _number(scenario_record.jump_risk_assumptions.get("jumpMagnitude", -0.08))
                    asset_return -= 0.0015
                    portfolio_return += weights.get(symbol, 0.0) * asset_return
                    if _number(position.get("stop_loss") or position.get("stopLoss")) and asset_return <= -0.04:
                        simultaneous_stops += 1
                    strategy = str(position.get("currentStrategy") or position.get("strategy_id") or "UNKNOWN")
                    strategy_path[strategy] = strategy_path.get(strategy, 0.0) + weights.get(symbol, 0.0) * asset_return
                if simultaneous_stops >= 2:
                    stop_trigger_steps += 1
                    portfolio_return -= 0.004 * simultaneous_stops
                equity = max(0.0, equity * (1 + portfolio_return))
                peak = max(peak, equity)
                min_equity = min(min_equity, equity)
                path_returns.append(portfolio_return)
            terminal = round(equity, 4)
            total_return = round((terminal - portfolio["portfolio_equity"]) / max(1.0, portfolio["portfolio_equity"]), 8)
            drawdown = round((peak - min_equity) / max(1.0, peak), 8)
            terminal_values.append(terminal)
            returns.append(total_return)
            drawdowns.append(drawdown)
            path_vols.append(_stddev(path_returns))
            losses += total_return < 0
            targets += total_return >= config.default_target_return
            drawdown_breaches += drawdown >= abs(config.default_loss_threshold)
            ruins += total_return <= config.default_ruin_threshold
            liquidity_failures += drawdown >= 0.12 or stop_trigger_steps > 0
            stop_cascades += stop_trigger_steps > 0
            concentration_failures += max(weights.values(), default=0.0) >= 0.35 and total_return < 0
            correlation_failures += any(abs(value) >= 0.75 for row in corr.values() for value in row.values() if value != 1.0) and total_return < 0
            for strategy, value in strategy_path.items():
                strategy_returns.setdefault(strategy, []).append(round(value, 8))

        record_payload = {
            "scenario": asdict(scenario_record),
            "terminal": terminal_values,
            "returns": returns,
            "drawdowns": drawdowns,
            "initial": portfolio["portfolio_equity"],
            "seed": scenario_record.random_seed,
        }
        confidence = _model_confidence(scenario_record, degraded, enterprise_reality_calibration or {}, scenario_record.simulation_count, config)
        result = MonteCarloResultRecord(
            monte_carlo_result_id=f"MCP-RESULT-{len(self._results) + 1:06d}",
            monte_carlo_scenario_id=scenario_record.monte_carlo_scenario_id,
            started_at=timestamp_utc,
            completed_at=timestamp_utc,
            simulation_count_completed=scenario_record.simulation_count,
            status="COMPLETED_DEGRADED" if degraded else "COMPLETED",
            initial_portfolio_equity=round(portfolio["portfolio_equity"], 4),
            terminal_value_mean=round(sum(terminal_values) / max(1, len(terminal_values)), 4),
            terminal_value_median=_percentile(terminal_values, 50),
            terminal_value_percentiles=_percentiles(terminal_values),
            return_mean=round(sum(returns) / max(1, len(returns)), 8),
            return_median=_percentile(returns, 50),
            return_percentiles=_percentiles(returns),
            volatility_estimate=round(sum(path_vols) / max(1, len(path_vols)), 8),
            max_drawdown_mean=round(sum(drawdowns) / max(1, len(drawdowns)), 8),
            max_drawdown_median=_percentile(drawdowns, 50),
            max_drawdown_percentiles=_percentiles(drawdowns),
            probability_of_loss=round(losses / max(1, len(returns)), 6),
            probability_of_target_achievement=round(targets / max(1, len(returns)), 6),
            probability_of_drawdown_threshold_breach=round(drawdown_breaches / max(1, len(returns)), 6),
            probability_of_ruin=round(ruins / max(1, len(returns)), 6),
            probability_of_liquidity_failure=round(liquidity_failures / max(1, len(returns)), 6),
            probability_of_stop_cascade=round(stop_cascades / max(1, len(returns)), 6),
            expected_shortfall=_expected_shortfall(returns, config.expected_shortfall_confidence),
            value_at_risk=_var(returns, config.value_at_risk_confidence),
            benchmark_comparison=_benchmark_comparison(returns, scenario_record, enterprise_benchmark_engine or {}),
            strategy_contribution_distribution=tuple({"strategy": key, "meanContribution": round(sum(values) / max(1, len(values)), 8), "lossProbability": round(sum(1 for value in values if value < 0) / max(1, len(values)), 6)} for key, values in sorted(strategy_returns.items())),
            concentration_failure_probability=round(concentration_failures / max(1, len(returns)), 6),
            correlation_failure_probability=round(correlation_failures / max(1, len(returns)), 6),
            model_confidence=confidence,
            degraded_inputs=tuple(dict.fromkeys(degraded)),
            reproducibility_hash=_hash(record_payload),
            recommended_actions=_actions(returns, drawdowns, degraded, confidence, config),
            audit_reference=f"AE-MONTE-CARLO-RESULT-{audit_event_count + len(self._results) + 1:06d}",
        )
        self._results.append(result)
        return self.snapshot(latest_scenario=scenario_record, latest_result=result, timestamp_utc=timestamp_utc, config=config)

    def snapshot(
        self,
        *,
        latest_scenario: MonteCarloScenarioRecord | None = None,
        latest_result: MonteCarloResultRecord | None = None,
        timestamp_utc: str = "",
        config: MonteCarloPortfolioConfig | None = None,
    ) -> dict[str, Any]:
        config = config or self._config
        latest_scenario = latest_scenario or (self._scenarios[-1] if self._scenarios else None)
        latest_result = latest_result or (self._results[-1] if self._results else None)
        feed = _feed(latest_result)
        return {
            "engineName": "Monte Carlo Portfolio Engine",
            "engineeringOrder": "EO-BE",
            "constitutionalMode": "SEEDED_PORTFOLIO_DISTRIBUTION_ANALYTICS_ONLY",
            "monteCarloScenarioRecords": tuple(asdict(item) for item in self._scenarios),
            "monteCarloResultRecords": tuple(asdict(item) for item in self._results),
            "latestMonteCarloScenarioRecord": asdict(latest_scenario) if latest_scenario else {},
            "latestMonteCarloResultRecord": asdict(latest_result) if latest_result else {},
            "riskFactorFeed": feed,
            "portfolioConstructionFeed": feed,
            "capitalAllocationFeed": feed,
            "positionSizingFeed": feed,
            "stressTestingFeed": feed,
            "blackSwanSimulationFeed": feed,
            "enterpriseExperimentSchedulerFeed": feed,
            "enterpriseHealthMetrics": {
                "latestMonteCarloResultStatus": latest_result.status if latest_result else "NO_RECORD",
                "latestModelConfidence": latest_result.model_confidence if latest_result else 0.0,
                "probabilityOfLoss": latest_result.probability_of_loss if latest_result else 0.0,
                "probabilityOfRuin": latest_result.probability_of_ruin if latest_result else 0.0,
                "simulationCountCompleted": latest_result.simulation_count_completed if latest_result else 0,
                "resultRecordAge": "CURRENT" if latest_result and latest_result.completed_at == timestamp_utc else "RECENT" if latest_result else "NO_RECORD",
            },
            "commanderSummary": {
                "terminalValueMean": latest_result.terminal_value_mean if latest_result else 0.0,
                "probabilityOfLoss": latest_result.probability_of_loss if latest_result else 0.0,
                "probabilityOfRuin": latest_result.probability_of_ruin if latest_result else 0.0,
                "valueAtRisk": latest_result.value_at_risk if latest_result else 0.0,
                "expectedShortfall": latest_result.expected_shortfall if latest_result else 0.0,
                "recommendedActions": latest_result.recommended_actions if latest_result else ("Create and run a Monte Carlo scenario.",),
            },
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "explicitBoundsRequired": True, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicSeededSimulation": True},
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
                "resultCount": len(self._results),
                "timestamp": timestamp_utc,
            },
        }

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None) -> MonteCarloPortfolioConfig:
        values = asdict(self._config)
        for item in (enterprise_configuration_registry or {}).get("configurationRegistry", ()):
            key = _config_key(str(item.get("name", "")))
            if key in values:
                values[key] = _coerce_config_value(item.get("currentValue", values[key]), values[key])
        return MonteCarloPortfolioConfig(**values)


def _positions(truth: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(truth.get("positionRegistry", {}).get("activePositions", ())) or tuple(truth.get("positionLedger", ()))


def _portfolio_state(truth: dict[str, Any]) -> dict[str, float]:
    paper = truth.get("paperAccount", {})
    latest = (truth.get("portfolioLedger") or ({},))[-1]
    market = sum(_value(item) for item in _positions(truth))
    cash = _number(latest.get("cash", paper.get("cash", paper.get("buyingPower", 0.0))))
    equity = _number(latest.get("total_equity", cash + market)) or cash + market
    return {"cash": cash, "buying_power": _number(paper.get("buyingPower", cash)), "portfolio_equity": max(1.0, equity)}


def _drift_volatility(symbols: tuple[str, ...], provider: dict[str, Any], degraded: list[str]) -> tuple[dict[str, float], dict[str, float]]:
    histories: dict[str, list[float]] = {}
    for row in provider.get("normalizedObjects", {}).get("returnHistory", ()) + provider.get("normalizedObjects", {}).get("returns", ()):
        histories[str(row.get("symbol", "")).upper()] = [_number(value) for value in row.get("returns", row.get("values", ()))]
    drifts: dict[str, float] = {}
    vols: dict[str, float] = {}
    for symbol in symbols:
        values = histories.get(symbol, ())
        if len(values) >= 4:
            drifts[symbol] = round(sum(values) / len(values), 8)
            vols[symbol] = max(0.0001, round(_stddev(values), 8))
        else:
            degraded.append(f"volatility_fallback:{symbol}")
            drifts[symbol] = 0.0001
            vols[symbol] = 0.025
    return drifts, vols


def _correlation(symbols: tuple[str, ...], correlation: dict[str, Any], degraded: list[str]) -> tuple[dict[str, dict[str, float]], str]:
    record = correlation.get("latestCorrelationIntelligenceRecord", {})
    matrix = record.get("correlation_matrix", {})
    if _valid_matrix(symbols, matrix):
        return {symbol: {other: round(_number(matrix.get(symbol, {}).get(other, 1.0 if symbol == other else 0.0)), 6) for other in symbols} for symbol in symbols}, "EO-AH_correlation_matrix"
    if symbols:
        degraded.append("correlation_matrix_fallback")
    return {symbol: {other: 1.0 if symbol == other else 0.25 for other in symbols} for symbol in symbols}, "conservative_metadata_fallback"


def _valid_matrix(symbols: tuple[str, ...], matrix: dict[str, Any]) -> bool:
    if not symbols or not matrix:
        return False
    for symbol in symbols:
        row = matrix.get(symbol)
        if not isinstance(row, dict):
            return False
        for other in symbols:
            if other not in row:
                return False
            value = _number(row.get(other))
            if value < -1 or value > 1:
                return False
    return True


def _safe_cholesky(symbols: tuple[str, ...], matrix: dict[str, dict[str, float]], degraded: list[str]) -> list[list[float]]:
    n = len(symbols)
    if n == 0:
        return []
    a = [[_number(matrix.get(left, {}).get(right, 1.0 if left == right else 0.0)) for right in symbols] for left in symbols]
    l = [[0.0] * n for _ in range(n)]
    try:
        for i in range(n):
            for j in range(i + 1):
                value = a[i][j] - sum(l[i][k] * l[j][k] for k in range(j))
                if i == j:
                    if value <= 0:
                        raise ValueError("matrix not positive definite")
                    l[i][j] = math.sqrt(value)
                else:
                    l[i][j] = value / max(0.000001, l[j][j])
        return l
    except ValueError:
        degraded.append("correlation_matrix_psd_fallback")
        return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def _correlated_normals(rng: random.Random, cholesky: list[list[float]]) -> list[float]:
    raw = [_normal(rng) for _ in cholesky]
    return [sum(row[index] * raw[index] for index in range(len(raw))) for row in cholesky]


def _normal(rng: random.Random) -> float:
    u1 = max(1e-12, rng.random())
    u2 = rng.random()
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def _weights(positions: tuple[dict[str, Any], ...], equity: float) -> dict[str, float]:
    return {str(position.get("symbol", "")).upper(): _value(position) / max(1.0, equity) for position in positions}


def _percentiles(values: list[float]) -> dict[str, float]:
    return {key: _percentile(values, pct) for key, pct in (("p01", 1), ("p05", 5), ("p25", 25), ("p50", 50), ("p75", 75), ("p95", 95), ("p99", 99))}


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct / 100.0
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return round(ordered[int(index)], 8)
    return round(ordered[low] + (ordered[high] - ordered[low]) * (index - low), 8)


def _var(returns: list[float], confidence: float) -> float:
    return _percentile(returns, round((1 - confidence) * 100, 4))


def _expected_shortfall(returns: list[float], confidence: float) -> float:
    threshold = _var(returns, confidence)
    tail = [value for value in returns if value <= threshold]
    return round(sum(tail) / max(1, len(tail)), 8)


def _benchmark_comparison(returns: list[float], scenario: MonteCarloScenarioRecord, benchmark: dict[str, Any]) -> dict[str, Any]:
    baseline = 0.0
    if benchmark.get("portfolioLevelComparisons"):
        baseline = _number(benchmark["portfolioLevelComparisons"][0].get("benchmarkReturn"))
    return {"benchmarkSymbols": scenario.benchmark_symbols, "horizon": scenario.time_horizon, "compatibleHorizon": True, "meanReturnVsBenchmark": round((sum(returns) / max(1, len(returns))) - baseline, 8), "baselineReturn": baseline}


def _model_confidence(scenario: MonteCarloScenarioRecord, degraded: list[str], reality: dict[str, Any], count: int, config: MonteCarloPortfolioConfig) -> float:
    score = 82.0
    score -= len(set(degraded)) * 6
    if scenario.return_model == "seeded_correlated_gaussian":
        score -= 8
    if count < 100:
        score -= 10
    reality_score = _number(reality.get("commanderSummary", {}).get("overallRealityFidelityScore", 100.0))
    if reality_score:
        score -= max(0.0, 90.0 - reality_score) * 0.35
    return _clamp(score)


def _actions(returns: list[float], drawdowns: list[float], degraded: list[str], confidence: float, config: MonteCarloPortfolioConfig) -> tuple[str, ...]:
    loss_prob = sum(1 for value in returns if value < 0) / max(1, len(returns))
    ruin_prob = sum(1 for value in returns if value <= config.default_ruin_threshold) / max(1, len(returns))
    dd_prob = sum(1 for value in drawdowns if value >= abs(config.default_loss_threshold)) / max(1, len(drawdowns))
    actions = []
    if ruin_prob >= 0.10:
        actions.extend(("request_commander_review", "block_new_positions"))
    if loss_prob >= 0.55 or dd_prob >= 0.35:
        actions.append("request_risk_review")
    if confidence < config.minimum_model_confidence:
        actions.extend(("require_more_data", "rerun_with_conservative_assumptions"))
    if degraded:
        actions.append("require_reality_calibration")
    if not actions:
        actions.append("no_action")
    return tuple(dict.fromkeys(actions))


def _feed(record: MonteCarloResultRecord | None) -> dict[str, Any]:
    if not record:
        return {"monteCarloAvailable": False, "recommendedActions": ("Run Monte Carlo simulation.",)}
    return {
        "monteCarloAvailable": True,
        "latestMonteCarloResultId": record.monte_carlo_result_id,
        "probabilityOfLoss": record.probability_of_loss,
        "probabilityOfRuin": record.probability_of_ruin,
        "probabilityOfStopCascade": record.probability_of_stop_cascade,
        "valueAtRisk": record.value_at_risk,
        "expectedShortfall": record.expected_shortfall,
        "modelConfidence": record.model_confidence,
        "recommendedActions": record.recommended_actions,
        "monteCarloCapitalMultiplier": 0.35 if record.probability_of_ruin >= 0.10 else 0.65 if record.probability_of_loss >= 0.55 else 1.0,
        "monteCarloSizeMultiplier": 0.5 if record.probability_of_ruin >= 0.10 else 0.75 if record.probability_of_loss >= 0.55 else 1.0,
    }


def _scenario_from_payload(payload: dict[str, Any] | MonteCarloScenarioRecord) -> MonteCarloScenarioRecord:
    if isinstance(payload, MonteCarloScenarioRecord):
        return payload
    return MonteCarloScenarioRecord(**dict(payload))


def _stddev(values: list[float] | tuple[float, ...]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _value(position: dict[str, Any]) -> float:
    return _number(position.get("current_value", position.get("market_value", _number(position.get("quantity")) * _number(position.get("current_price", position.get("average_cost"))))))


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


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
