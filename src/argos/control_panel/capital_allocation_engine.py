"""Capital Allocation Engine for ARGOS EO-AE."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class CapitalAllocationConfig:
    capital_allocation_enabled: bool = True
    required_cash_reserve_percent: float = 0.10
    max_allocation_per_strategy: float = 0.30
    max_allocation_per_asset_type: float = 0.70
    max_allocation_per_sector: float = 0.35
    max_allocation_per_risk_bucket: float = 0.40
    max_allocation_increase_per_review: float = 0.05
    minimum_trade_sample_before_allocation_increase: int = 20
    drawdown_penalty_threshold: float = 0.08
    benchmark_underperformance_penalty: float = 0.05
    reality_fidelity_degraded_threshold: float = 80.0
    reality_fidelity_unsafe_threshold: float = 60.0
    experimental_capital_cap: float = 0.05
    emergency_allocation_halt: bool = False
    default_degraded_data_behavior: str = "conservative"


@dataclass(frozen=True)
class CapitalAllocationRecord:
    capital_allocation_id: str
    timestamp: str
    portfolio_equity: float
    cash: float
    buying_power: float
    deployable_capital: float
    required_cash_reserve: float
    total_allocated_capital: float
    unallocated_capital: float
    allocation_by_strategy: tuple[dict[str, Any], ...]
    allocation_by_asset_type: tuple[dict[str, Any], ...]
    allocation_by_sector: tuple[dict[str, Any], ...]
    allocation_by_risk_bucket: tuple[dict[str, Any], ...]
    allocation_by_market_regime: tuple[dict[str, Any], ...]
    allocation_policy_version: str
    risk_constraints_applied: tuple[str, ...]
    commander_policy_reference: str
    performance_inputs_used: tuple[str, ...]
    degraded_inputs: tuple[str, ...]
    allocation_score: float
    deterministic_reasoning: tuple[str, ...]
    audit_reference: str


class CapitalAllocationEngine:
    """Deterministic portfolio-level capital budget authority."""

    def __init__(self, config: CapitalAllocationConfig | None = None) -> None:
        self._config = config or CapitalAllocationConfig()
        self._records: list[CapitalAllocationRecord] = []
        self._last_fingerprint = ""

    def allocate(
        self,
        *,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        market_context_engine: dict[str, Any],
        enterprise_benchmark_engine: dict[str, Any],
        trade_attribution_engine: dict[str, Any],
        enterprise_reality_calibration: dict[str, Any],
        enterprise_operational_guardrails: dict[str, Any],
        enterprise_configuration_registry: dict[str, Any] | None = None,
        enterprise_risk_factor: dict[str, Any] | None = None,
        correlation_intelligence: dict[str, Any] | None = None,
        commander_policy: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        """Produce capital budgets without executing or sizing trades."""
        config = self._resolved_config(enterprise_configuration_registry, commander_policy)
        if not config.capital_allocation_enabled:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=None, config=config)
        fingerprint = _fingerprint(performance_truth, strategy_package_manager, market_context_engine, enterprise_benchmark_engine, trade_attribution_engine, enterprise_reality_calibration, enterprise_operational_guardrails, enterprise_risk_factor or {}, correlation_intelligence or {}, commander_policy or {})
        if fingerprint == self._last_fingerprint and self._records:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=self._records[-1], config=config)
        record = self._build_record(
            timestamp_utc=timestamp_utc,
            performance_truth=performance_truth,
            strategy_package_manager=strategy_package_manager,
            market_context_engine=market_context_engine,
            enterprise_benchmark_engine=enterprise_benchmark_engine,
            trade_attribution_engine=trade_attribution_engine,
            enterprise_reality_calibration=enterprise_reality_calibration,
            enterprise_operational_guardrails=enterprise_operational_guardrails,
            enterprise_risk_factor=enterprise_risk_factor or {},
            correlation_intelligence=correlation_intelligence or {},
            commander_policy=commander_policy or {},
            audit_event_count=audit_event_count,
            config=config,
        )
        self._records.append(record)
        self._last_fingerprint = fingerprint
        return self.snapshot(timestamp_utc=timestamp_utc, latest_record=record, config=config)

    def snapshot(self, *, timestamp_utc: str, latest_record: CapitalAllocationRecord | None = None, config: CapitalAllocationConfig | None = None) -> dict[str, Any]:
        config = config or self._config
        latest = latest_record or (self._records[-1] if self._records else None)
        latest_payload = asdict(latest) if latest else {}
        integration = _integration_payload(latest)
        return {
            "engineName": "Capital Allocation Engine",
            "engineeringOrder": "EO-AE",
            "constitutionalMode": "CAPITAL_BUDGETING_ONLY",
            "capitalAllocationRecords": tuple(asdict(item) for item in self._records),
            "latestCapitalAllocationRecord": latest_payload,
            "portfolioConstructionFeed": integration,
            "positionSizingFeed": {
                **integration,
                "perTradeCapitalCeiling": round((latest.deployable_capital if latest else 0.0) * 0.2, 4),
                "reducedSizeRecommendationWhenConstrained": True,
            },
            "commanderSummary": {
                "deployableCapital": latest.deployable_capital if latest else 0.0,
                "requiredCashReserve": latest.required_cash_reserve if latest else 0.0,
                "allocationScore": latest.allocation_score if latest else 0.0,
                "policyVersion": latest.allocation_policy_version if latest else "ARGOS-CAPITAL-POLICY-1.0",
                "warnings": latest.degraded_inputs if latest else ("No allocation record available.",),
            },
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicScoring": True},
            "internalDiagnostics": {
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "placesTrades": False,
                "finalPositionSizing": False,
                "workflowTokensOwned": 0,
                "apiCreditsConsumed": 0.0,
                "recordCount": len(self._records),
                "timestamp": timestamp_utc,
            },
        }

    def _build_record(
        self,
        *,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        market_context_engine: dict[str, Any],
        enterprise_benchmark_engine: dict[str, Any],
        trade_attribution_engine: dict[str, Any],
        enterprise_reality_calibration: dict[str, Any],
        enterprise_operational_guardrails: dict[str, Any],
        enterprise_risk_factor: dict[str, Any],
        correlation_intelligence: dict[str, Any],
        commander_policy: dict[str, Any],
        audit_event_count: int,
        config: CapitalAllocationConfig,
    ) -> CapitalAllocationRecord:
        portfolio = _portfolio_state(performance_truth)
        exposures = _exposures(performance_truth)
        pending = _pending_commitments(performance_truth)
        reality = _reality_state(enterprise_reality_calibration)
        degraded = []
        constraints = []
        if not exposures["sector_metadata_available"]:
            degraded.append("sector_metadata_missing")
        if not strategy_package_manager.get("activePackages"):
            degraded.append("strategy_package_data_limited")
        if reality["state"] in {"degraded", "unsafe", "blocked"}:
            degraded.append(f"reality_fidelity_{reality['state']}")
        required_reserve = round(portfolio["portfolio_equity"] * config.required_cash_reserve_percent, 4)
        base_available = min(portfolio["buying_power"], portfolio["cash"], portfolio["portfolio_equity"])
        deployable = max(0.0, base_available - required_reserve - pending)
        if _halted(enterprise_operational_guardrails) or config.emergency_allocation_halt or reality["state"] in {"unsafe", "blocked"}:
            constraints.append("emergency_or_reality_halt")
            deployable = 0.0
        elif reality["score"] < config.reality_fidelity_degraded_threshold:
            constraints.append("reality_fidelity_degraded_reduction")
            deployable = round(deployable * 0.5, 4)
        risk_feed = enterprise_risk_factor.get("capitalAllocationFeed", {})
        if risk_feed.get("haltRecommended"):
            constraints.append("enterprise_risk_factor_halt")
            deployable = 0.0
        elif risk_feed:
            multiplier = _number(risk_feed.get("riskAdjustedCapitalMultiplier", 1.0))
            if multiplier < 1.0:
                constraints.append("enterprise_risk_factor_reduction")
                deployable = round(deployable * max(0.0, multiplier), 4)
        correlation_feed = correlation_intelligence.get("capitalAllocationFeed", {})
        if correlation_feed:
            multiplier = _number(correlation_feed.get("correlationAdjustedCapitalMultiplier", 1.0))
            if multiplier < 1.0:
                constraints.append("correlation_intelligence_reduction")
                deployable = round(deployable * max(0.0, multiplier), 4)
        max_increase = portfolio["portfolio_equity"] * config.max_allocation_increase_per_review
        deployable = min(deployable, max(0.0, portfolio["buying_power"]), max(0.0, max_increase if _sample_count(performance_truth) < config.minimum_trade_sample_before_allocation_increase else deployable))
        strategy_rows = _strategy_budgets(deployable, portfolio["portfolio_equity"], exposures, strategy_package_manager, performance_truth, config)
        asset_rows = _bucket_budgets(deployable, portfolio["portfolio_equity"], exposures["asset_types"], config.max_allocation_per_asset_type, ("STOCK", "ETF"))
        sector_rows = _sector_budgets(deployable, portfolio["portfolio_equity"], exposures["sectors"], config)
        risk_rows = _risk_budgets(deployable, config)
        regime_rows = _regime_budgets(deployable, market_context_engine)
        allocated = round(sum(item["budget"] for item in strategy_rows), 4)
        score = _allocation_score(portfolio, deployable, degraded, constraints, reality, enterprise_benchmark_engine, trade_attribution_engine)
        reasoning = (
            f"Deployable capital = min(equity, cash, buying power) {round(base_available, 4)} - reserve {required_reserve} - pending {pending}.",
            f"Reality fidelity {reality['score']} with state {reality['state']}.",
            f"Allocation increase capped at {round(max_increase, 4)} until sample size reaches {config.minimum_trade_sample_before_allocation_increase}.",
            "Capital Allocation Engine sets budgets only; Portfolio Construction and Position Sizing consume limits.",
        )
        return CapitalAllocationRecord(
            capital_allocation_id=f"CALLOC-{len(self._records) + 1:06d}",
            timestamp=timestamp_utc,
            portfolio_equity=round(portfolio["portfolio_equity"], 4),
            cash=round(portfolio["cash"], 4),
            buying_power=round(portfolio["buying_power"], 4),
            deployable_capital=round(deployable, 4),
            required_cash_reserve=required_reserve,
            total_allocated_capital=allocated,
            unallocated_capital=round(max(0.0, deployable - allocated), 4),
            allocation_by_strategy=tuple(strategy_rows),
            allocation_by_asset_type=tuple(asset_rows),
            allocation_by_sector=tuple(sector_rows),
            allocation_by_risk_bucket=tuple(risk_rows),
            allocation_by_market_regime=tuple(regime_rows),
            allocation_policy_version=str(commander_policy.get("policyVersion", "ARGOS-CAPITAL-POLICY-1.0")),
            risk_constraints_applied=tuple(constraints or ("cash_reserve", "buying_power", "pending_orders", "max_allocation_increase")),
            commander_policy_reference=str(commander_policy.get("policyId", "")),
            performance_inputs_used=tuple(_performance_inputs(performance_truth, enterprise_benchmark_engine, trade_attribution_engine)),
            degraded_inputs=tuple(degraded),
            allocation_score=score,
            deterministic_reasoning=reasoning,
            audit_reference=f"AE-CAPITAL-ALLOCATION-{audit_event_count + len(self._records) + 1:06d}",
        )

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None, commander_policy: dict[str, Any] | None) -> CapitalAllocationConfig:
        values = asdict(self._config)
        for item in (enterprise_configuration_registry or {}).get("configurationRegistry", ()):
            key = _config_key(str(item.get("name", "")))
            if key in values:
                values[key] = _coerce_config_value(item.get("currentValue", values[key]), values[key])
        policy = commander_policy or {}
        aliases = {
            "minimumCashReservePercent": "required_cash_reserve_percent",
            "maxSingleStrategyAllocation": "max_allocation_per_strategy",
            "maxExperimentalCapital": "experimental_capital_cap",
            "emergencyAllocationHalt": "emergency_allocation_halt",
        }
        for key, target in aliases.items():
            if key in policy:
                values[target] = _coerce_config_value(policy[key], values[target])
        return CapitalAllocationConfig(**values)


def _integration_payload(record: CapitalAllocationRecord | None) -> dict[str, Any]:
    if not record:
        return {"deployableCapital": 0.0, "cashReserveRequirement": 0.0, "allocationWarnings": ("No capital allocation record available.",), "maxCapitalPerStrategy": {}, "maxCapitalPerAssetType": {}, "maxCapitalPerSector": {}, "maxCapitalPerRiskBucket": {}}
    return {
        "deployableCapital": record.deployable_capital,
        "cashReserveRequirement": record.required_cash_reserve,
        "allocationWarnings": record.degraded_inputs,
        "maxCapitalPerStrategy": {item["strategy"]: item["remainingBudget"] for item in record.allocation_by_strategy},
        "maxCapitalPerAssetType": {item["bucket"]: item["remainingBudget"] for item in record.allocation_by_asset_type},
        "maxCapitalPerSector": {item["bucket"]: item["remainingBudget"] for item in record.allocation_by_sector},
        "maxCapitalPerRiskBucket": {item["bucket"]: item["remainingBudget"] for item in record.allocation_by_risk_bucket},
    }


def _portfolio_state(performance_truth: dict[str, Any]) -> dict[str, float]:
    paper = performance_truth.get("paperAccount", {})
    latest = (performance_truth.get("portfolioLedger") or ({},))[-1]
    positions = tuple(performance_truth.get("positionRegistry", {}).get("activePositions", ())) or tuple(performance_truth.get("positionLedger", ()))
    market_value = sum(_number(item.get("current_value", item.get("market_value", 0.0))) for item in positions)
    cash = _number(latest.get("cash", paper.get("cash", paper.get("buyingPower", 0.0))))
    equity = _number(latest.get("total_equity", cash + market_value)) or cash + market_value
    return {"cash": max(0.0, cash), "buying_power": max(0.0, _number(paper.get("buyingPower", cash))), "portfolio_equity": max(0.0, equity)}


def _exposures(performance_truth: dict[str, Any]) -> dict[str, Any]:
    positions = tuple(performance_truth.get("positionRegistry", {}).get("activePositions", ())) or tuple(performance_truth.get("positionLedger", ()))
    asset_types: dict[str, float] = {}
    sectors: dict[str, float] = {}
    strategies: dict[str, float] = {}
    sector_metadata = True
    for position in positions:
        value = _number(position.get("current_value", position.get("market_value", 0.0)))
        asset = str(position.get("asset_type", "UNKNOWN") or "UNKNOWN")
        sector = str(position.get("sector", "") or _sector_for(str(position.get("symbol", ""))))
        strategy = str(position.get("strategy_id", position.get("currentStrategy", "UNKNOWN")) or "UNKNOWN")
        if sector == "UNKNOWN":
            sector_metadata = False
        asset_types[asset] = asset_types.get(asset, 0.0) + value
        sectors[sector] = sectors.get(sector, 0.0) + value
        strategies[strategy] = strategies.get(strategy, 0.0) + value
    return {"asset_types": asset_types, "sectors": sectors, "strategies": strategies, "sector_metadata_available": sector_metadata}


def _pending_commitments(performance_truth: dict[str, Any]) -> float:
    orders = tuple(performance_truth.get("orderLedger", ()))
    return round(sum(_number(order.get("estimated_notional", order.get("cash_impact", 0.0))) for order in orders if str(order.get("status", "")).upper() in {"QUEUED", "PENDING", "SUBMITTED", "PARTIALLY_FILLED"}), 4)


def _strategy_budgets(deployable: float, equity: float, exposures: dict[str, Any], strategy_manager: dict[str, Any], truth: dict[str, Any], config: CapitalAllocationConfig) -> list[dict[str, Any]]:
    packages = tuple(strategy_manager.get("activePackages", ())) or ({"strategyName": "Workflow Proof Strategy", "currentStatus": "Active", "packageHealth": "HEALTHY"},)
    sample_count = _sample_count(truth)
    rows = []
    for package in packages:
        strategy = str(package.get("strategyName", package.get("packageName", "Workflow Proof Strategy")))
        current = exposures["strategies"].get(strategy, 0.0)
        cap = equity * config.max_allocation_per_strategy
        if "Experimental" in str(package.get("packageType", "")):
            cap = min(cap, equity * config.experimental_capital_cap)
        if sample_count < config.minimum_trade_sample_before_allocation_increase:
            cap = min(cap, current + equity * config.max_allocation_increase_per_review)
        if str(package.get("packageHealth", "HEALTHY")).upper() not in {"HEALTHY", "NOMINAL"}:
            cap *= 0.5
        if abs(_number(package.get("maximumDrawdown", package.get("drawdown", 0.0)))) >= config.drawdown_penalty_threshold:
            cap *= 0.5
        budget = max(0.0, min(deployable, cap - current))
        rows.append({"strategy": strategy, "status": package.get("currentStatus", "Active"), "currentCapital": round(current, 4), "budget": round(budget, 4), "remainingBudget": round(budget, 4), "cap": round(cap, 4), "sampleSize": sample_count})
    return rows


def _bucket_budgets(deployable: float, equity: float, current: dict[str, float], cap_percent: float, defaults: tuple[str, ...]) -> list[dict[str, Any]]:
    keys = tuple(dict.fromkeys((*defaults, *current.keys())))
    rows = []
    for key in keys:
        used = current.get(key, 0.0)
        cap = equity * cap_percent
        budget = max(0.0, min(deployable, cap - used))
        rows.append({"bucket": key, "currentCapital": round(used, 4), "budget": round(budget, 4), "remainingBudget": round(budget, 4), "cap": round(cap, 4)})
    return rows


def _sector_budgets(deployable: float, equity: float, sectors: dict[str, float], config: CapitalAllocationConfig) -> list[dict[str, Any]]:
    if not sectors:
        return ({"bucket": "UNKNOWN", "currentCapital": 0.0, "budget": round(min(deployable, equity * config.max_allocation_per_sector * 0.5), 4), "remainingBudget": round(min(deployable, equity * config.max_allocation_per_sector * 0.5), 4), "cap": round(equity * config.max_allocation_per_sector * 0.5, 4), "degraded": True},)
    return _bucket_budgets(deployable, equity, sectors, config.max_allocation_per_sector, ())


def _risk_budgets(deployable: float, config: CapitalAllocationConfig) -> list[dict[str, Any]]:
    weights = {"low_risk": 0.40, "medium_risk": 0.35, "high_risk": 0.15, "experimental": config.experimental_capital_cap, "commander_approved_exception": 0.05}
    return [{"bucket": key, "budget": round(deployable * weight, 4), "remainingBudget": round(deployable * weight, 4), "capPercent": weight} for key, weight in weights.items()]


def _regime_budgets(deployable: float, market_context: dict[str, Any]) -> list[dict[str, Any]]:
    latest = market_context.get("latestMarketContext", {})
    regime = str(latest.get("marketRegime", "UNKNOWN"))
    confidence = _number(latest.get("confidence", 0.0))
    degraded = not regime or regime == "UNKNOWN" or confidence < 0.7
    multiplier = 0.75 if degraded or confidence < 0.7 else 1.0
    return [{"marketRegime": regime or "UNKNOWN", "budget": round(deployable * multiplier, 4), "remainingBudget": round(deployable * multiplier, 4), "confidence": confidence, "degraded": degraded}]


def _reality_state(reality: dict[str, Any]) -> dict[str, Any]:
    summary = reality.get("commanderSummary", {})
    return {"score": _number(summary.get("overallRealityFidelityScore", 100.0)), "state": str(summary.get("learningReliabilityState", "reliable"))}


def _halted(guardrails: dict[str, Any]) -> bool:
    return str(guardrails.get("readinessState", "Authorized")) in {"Emergency Halt", "Safe Mode", "Paused", "Offline", "Restricted"}


def _sample_count(truth: dict[str, Any]) -> int:
    return len(truth.get("tradeLedger", ())) + len(truth.get("closedPositionTruth", ()))


def _performance_inputs(truth: dict[str, Any], benchmark: dict[str, Any], attribution: dict[str, Any]) -> list[str]:
    inputs = ["Performance Truth Engine"]
    if truth.get("closedPositionTruth"):
        inputs.append("Closed Position Truth")
    if benchmark.get("tradeLevelComparisons") or benchmark.get("portfolioLevelComparisons"):
        inputs.append("Enterprise Benchmark Engine")
    if attribution.get("attributionRepository"):
        inputs.append("Trade Attribution Engine")
    return inputs


def _allocation_score(portfolio: dict[str, float], deployable: float, degraded: list[str], constraints: list[str], reality: dict[str, Any], benchmark: dict[str, Any], attribution: dict[str, Any]) -> float:
    score = 100.0
    if portfolio["portfolio_equity"] <= 0 or portfolio["buying_power"] <= 0:
        score -= 35
    if deployable <= 0:
        score -= 30
    score -= len(degraded) * 8
    score -= len(constraints) * 15
    score -= max(0.0, 85.0 - reality["score"]) * 0.4
    if not benchmark.get("tradeLevelComparisons") and not benchmark.get("portfolioLevelComparisons"):
        score -= 5
    if not attribution.get("attributionRepository"):
        score -= 5
    return round(max(0.0, min(100.0, score)), 4)


def _sector_for(symbol: str) -> str:
    return {"AAPL": "Technology", "MSFT": "Technology", "SPY": "Broad Market", "TLT": "Rates", "GLD": "Commodities", "QQQ": "Technology"}.get(symbol.upper(), "UNKNOWN")


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _fingerprint(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _config_key(name: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in name.strip().lower())


def _coerce_config_value(value: Any, default: Any) -> Any:
    if isinstance(default, bool):
        return str(value).lower() in {"1", "true", "yes", "enabled"}
    if isinstance(default, int):
        return int(_number(value))
    if isinstance(default, float):
        raw = _number(value)
        return raw / 100 if raw > 1.0 else raw
    return value
