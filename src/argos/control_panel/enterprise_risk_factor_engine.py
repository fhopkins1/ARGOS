"""Enterprise Risk Factor Engine for ARGOS EO-AG."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class EnterpriseRiskFactorConfig:
    risk_factor_engine_enabled: bool = True
    low_risk_threshold: float = 20.0
    moderate_risk_threshold: float = 40.0
    elevated_risk_threshold: float = 60.0
    high_risk_threshold: float = 80.0
    halt_trading_threshold: float = 85.0
    max_single_position_weight: float = 0.20
    max_top_3_concentration: float = 0.50
    max_top_5_concentration: float = 0.70
    max_sector_weight: float = 0.35
    max_asset_type_weight: float = 0.75
    max_strategy_weight: float = 0.35
    wide_spread_threshold: float = 0.01
    high_volatility_threshold: float = 0.35
    critical_volatility_threshold: float = 0.60
    drawdown_high_threshold: float = 0.08
    execution_risk_threshold: float = 40.0
    data_quality_risk_threshold: float = 40.0
    reality_fidelity_degraded_threshold: float = 80.0
    reality_fidelity_unsafe_threshold: float = 60.0
    degraded_data_policy: str = "conservative"
    conservative_scoring_mode: bool = True


@dataclass(frozen=True)
class RiskFactorRecord:
    risk_factor_record_id: str
    timestamp: str
    portfolio_equity: float
    cash: float
    buying_power: float
    total_market_value: float
    long_exposure: float
    short_exposure: float
    gross_exposure: float
    net_exposure: float
    market_risk_score: float
    sector_risk_score: float
    asset_type_risk_score: float
    concentration_risk_score: float
    strategy_risk_score: float
    liquidity_risk_score: float
    volatility_risk_score: float
    correlation_risk_score: float
    drawdown_risk_score: float
    execution_risk_score: float
    data_quality_risk_score: float
    reality_fidelity_risk_score: float
    composite_risk_score: float
    risk_level: str
    top_risk_factors: tuple[dict[str, Any], ...]
    degraded_inputs: tuple[str, ...]
    recommended_risk_actions: tuple[str, ...]
    audit_reference: str
    exposure_summary: dict[str, Any]


class EnterpriseRiskFactorEngine:
    """Deterministic enterprise-wide portfolio risk decomposition."""

    def __init__(self, config: EnterpriseRiskFactorConfig | None = None) -> None:
        self._config = config or EnterpriseRiskFactorConfig()
        self._records: list[RiskFactorRecord] = []
        self._last_fingerprint = ""

    def evaluate(
        self,
        *,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any],
        market_context_engine: dict[str, Any],
        enterprise_reality_calibration: dict[str, Any],
        enterprise_benchmark_engine: dict[str, Any] | None = None,
        closed_position_truth: dict[str, Any] | None = None,
        correlation_intelligence: dict[str, Any] | None = None,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        config = self._resolved_config(enterprise_configuration_registry)
        if not config.risk_factor_engine_enabled:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=None, config=config)
        fingerprint = _fingerprint(performance_truth, market_data_provider, market_context_engine, enterprise_reality_calibration, enterprise_benchmark_engine or {}, closed_position_truth or {}, correlation_intelligence or {})
        if fingerprint == self._last_fingerprint and self._records:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=self._records[-1], config=config)
        record = self._build_record(
            timestamp_utc=timestamp_utc,
            performance_truth=performance_truth,
            market_data_provider=market_data_provider,
            market_context_engine=market_context_engine,
            enterprise_reality_calibration=enterprise_reality_calibration,
            enterprise_benchmark_engine=enterprise_benchmark_engine or {},
            closed_position_truth=closed_position_truth or {},
            correlation_intelligence=correlation_intelligence or {},
            audit_event_count=audit_event_count,
            config=config,
        )
        self._records.append(record)
        self._last_fingerprint = fingerprint
        return self.snapshot(timestamp_utc=timestamp_utc, latest_record=record, config=config)

    def snapshot(self, *, timestamp_utc: str, latest_record: RiskFactorRecord | None = None, config: EnterpriseRiskFactorConfig | None = None) -> dict[str, Any]:
        config = config or self._config
        latest = latest_record or (self._records[-1] if self._records else None)
        latest_payload = asdict(latest) if latest else {}
        halt = bool(latest and latest.composite_risk_score >= config.halt_trading_threshold)
        feed = {
            "compositeRiskScore": latest.composite_risk_score if latest else 0.0,
            "riskLevel": latest.risk_level if latest else "unknown",
            "topRiskFactors": latest.top_risk_factors if latest else (),
            "recommendedRiskActions": latest.recommended_risk_actions if latest else (),
            "degradedInputs": latest.degraded_inputs if latest else ("No risk factor record available.",),
            "haltRecommended": halt,
            "riskAdjustedCapitalMultiplier": _capital_multiplier(latest.composite_risk_score if latest else 100.0),
            "riskAdjustedSizeMultiplier": _size_multiplier(latest.composite_risk_score if latest else 100.0),
        }
        return {
            "engineName": "Enterprise Risk Factor Engine",
            "engineeringOrder": "EO-AG",
            "constitutionalMode": "RISK_MEASUREMENT_ONLY",
            "riskFactorRecords": tuple(asdict(item) for item in self._records),
            "latestRiskFactorRecord": latest_payload,
            "riskOfficeFeed": feed,
            "portfolioConstructionFeed": feed,
            "capitalAllocationFeed": feed,
            "positionSizingFeed": feed,
            "enterpriseHealthMetrics": {
                "latestCompositeRiskScore": latest.composite_risk_score if latest else 0.0,
                "latestRiskLevel": latest.risk_level if latest else "unknown",
                "criticalRiskFactorCount": sum(1 for item in (latest.top_risk_factors if latest else ()) if item["score"] >= 80),
                "degradedInputCount": len(latest.degraded_inputs) if latest else 1,
                "riskRecordAge": "CURRENT" if latest and latest.timestamp == timestamp_utc else "RECENT" if latest else "NO_RECORD",
                "recommendedHaltFlag": halt,
                "realityFidelityRiskScore": latest.reality_fidelity_risk_score if latest else 0.0,
                "executionRiskScore": latest.execution_risk_score if latest else 0.0,
            },
            "commanderSummary": {
                "compositeRiskScore": latest.composite_risk_score if latest else 0.0,
                "riskLevel": latest.risk_level if latest else "unknown",
                "topRiskFactors": latest.top_risk_factors if latest else (),
                "recommendedRiskActions": latest.recommended_risk_actions if latest else ("Generate first risk factor record.",),
            },
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicScoring": True},
            "internalDiagnostics": {
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "placesTrades": False,
                "enforcesPolicyDirectly": False,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "recordCount": len(self._records),
                "timestamp": timestamp_utc,
            },
        }

    def _build_record(
        self,
        *,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any],
        market_context_engine: dict[str, Any],
        enterprise_reality_calibration: dict[str, Any],
        enterprise_benchmark_engine: dict[str, Any],
        closed_position_truth: dict[str, Any],
        correlation_intelligence: dict[str, Any],
        audit_event_count: int,
        config: EnterpriseRiskFactorConfig,
    ) -> RiskFactorRecord:
        portfolio = _portfolio_state(performance_truth)
        exposures = _exposures(performance_truth, portfolio["portfolio_equity"])
        quotes = _quotes(market_data_provider)
        degraded: list[str] = []
        if not exposures["sector_metadata_available"]:
            degraded.append("sector_metadata_missing")
        if not exposures["strategy_metadata_available"]:
            degraded.append("strategy_metadata_missing")
        if not quotes and exposures["positions"]:
            degraded.append("liquidity_data_missing")
        if not enterprise_benchmark_engine.get("tradeLevelComparisons") and not performance_truth.get("benchmarkHistory"):
            degraded.append("benchmark_data_limited")
        market_risk = _market_risk(market_context_engine, portfolio, config, degraded)
        sector_risk = _weight_risk(exposures["largest_sector_weight"], config.max_sector_weight, 15 if exposures["sector_metadata_available"] else 35)
        asset_risk = _weight_risk(exposures["largest_asset_type_weight"], config.max_asset_type_weight, 10)
        concentration_risk = _concentration_risk(exposures, config)
        strategy_risk = _weight_risk(exposures["largest_strategy_weight"], config.max_strategy_weight, 25 if exposures["strategy_metadata_available"] else 35)
        liquidity_risk = _liquidity_risk(exposures["positions"], quotes, config, degraded)
        volatility_risk = _volatility_risk(exposures["positions"], quotes, market_context_engine, config, degraded)
        correlation_risk = _correlation_risk(exposures, degraded, correlation_intelligence)
        drawdown_risk = _drawdown_risk(performance_truth, closed_position_truth, config, degraded)
        execution_risk = _execution_risk(performance_truth)
        data_quality_risk = _data_quality_risk(degraded, market_data_provider, performance_truth)
        reality_risk = _reality_risk(enterprise_reality_calibration, config)
        scores = {
            "market_risk_score": market_risk,
            "sector_risk_score": sector_risk,
            "asset_type_risk_score": asset_risk,
            "concentration_risk_score": concentration_risk,
            "strategy_risk_score": strategy_risk,
            "liquidity_risk_score": liquidity_risk,
            "volatility_risk_score": volatility_risk,
            "correlation_risk_score": correlation_risk,
            "drawdown_risk_score": drawdown_risk,
            "execution_risk_score": execution_risk,
            "data_quality_risk_score": data_quality_risk,
            "reality_fidelity_risk_score": reality_risk,
        }
        composite = round(sum(scores.values()) / len(scores), 4)
        level = _risk_level(composite, config)
        top = tuple({"factor": key, "score": value} for key, value in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:5])
        actions = _recommended_actions(scores, composite, degraded, config)
        return RiskFactorRecord(
            risk_factor_record_id=f"RFAC-{len(self._records) + 1:06d}",
            timestamp=timestamp_utc,
            portfolio_equity=round(portfolio["portfolio_equity"], 4),
            cash=round(portfolio["cash"], 4),
            buying_power=round(portfolio["buying_power"], 4),
            total_market_value=round(portfolio["total_market_value"], 4),
            long_exposure=round(exposures["long_exposure"], 4),
            short_exposure=round(exposures["short_exposure"], 4),
            gross_exposure=round(exposures["gross_exposure"], 4),
            net_exposure=round(exposures["net_exposure"], 4),
            market_risk_score=market_risk,
            sector_risk_score=sector_risk,
            asset_type_risk_score=asset_risk,
            concentration_risk_score=concentration_risk,
            strategy_risk_score=strategy_risk,
            liquidity_risk_score=liquidity_risk,
            volatility_risk_score=volatility_risk,
            correlation_risk_score=correlation_risk,
            drawdown_risk_score=drawdown_risk,
            execution_risk_score=execution_risk,
            data_quality_risk_score=data_quality_risk,
            reality_fidelity_risk_score=reality_risk,
            composite_risk_score=composite,
            risk_level=level,
            top_risk_factors=top,
            degraded_inputs=tuple(dict.fromkeys(degraded)),
            recommended_risk_actions=actions,
            audit_reference=f"AE-RISK-FACTOR-{audit_event_count + len(self._records) + 1:06d}",
            exposure_summary=exposures["summary"],
        )

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None) -> EnterpriseRiskFactorConfig:
        values = asdict(self._config)
        for item in (enterprise_configuration_registry or {}).get("configurationRegistry", ()):
            key = _config_key(str(item.get("name", "")))
            if key in values:
                values[key] = _coerce_config_value(item.get("currentValue", values[key]), values[key])
        return EnterpriseRiskFactorConfig(**values)


def _portfolio_state(truth: dict[str, Any]) -> dict[str, float]:
    paper = truth.get("paperAccount", {})
    latest = (truth.get("portfolioLedger") or ({},))[-1]
    positions = tuple(truth.get("positionRegistry", {}).get("activePositions", ())) or tuple(truth.get("positionLedger", ()))
    total_market = sum(_value(item) for item in positions)
    cash = _number(latest.get("cash", paper.get("cash", paper.get("buyingPower", 0.0))))
    equity = _number(latest.get("total_equity", cash + total_market)) or cash + total_market
    return {"cash": max(0.0, cash), "buying_power": max(0.0, _number(paper.get("buyingPower", cash))), "portfolio_equity": max(0.0, equity), "total_market_value": max(0.0, total_market)}


def _exposures(truth: dict[str, Any], equity: float) -> dict[str, Any]:
    positions = tuple(truth.get("positionRegistry", {}).get("activePositions", ())) or tuple(truth.get("positionLedger", ()))
    sector_metadata = True
    strategy_metadata = True
    sectors: dict[str, float] = {}
    assets: dict[str, float] = {}
    strategies: dict[str, float] = {}
    symbols: dict[str, float] = {}
    values = []
    long_exposure = 0.0
    short_exposure = 0.0
    for pos in positions:
        value = _value(pos)
        side = str(pos.get("side", "LONG")).upper()
        symbol = str(pos.get("symbol", "")).upper()
        sector = str(pos.get("sector") or _sector_for(symbol))
        strategy = str(pos.get("strategy_id") or pos.get("currentStrategy") or "")
        asset = str(pos.get("asset_type", "UNKNOWN") or "UNKNOWN")
        if sector == "UNKNOWN":
            sector_metadata = False
        if not strategy:
            strategy = "UNKNOWN"
            strategy_metadata = False
        if side in {"SHORT", "SELL"}:
            short_exposure += value
        else:
            long_exposure += value
        symbols[symbol] = symbols.get(symbol, 0.0) + value
        sectors[sector] = sectors.get(sector, 0.0) + value
        assets[asset] = assets.get(asset, 0.0) + value
        strategies[strategy] = strategies.get(strategy, 0.0) + value
        values.append(value)
    denominator = max(1.0, equity)
    weights = sorted((value / denominator for value in values), reverse=True)
    summary = {
        "positionWeights": tuple(round(weight, 6) for weight in weights),
        "sectorWeights": {key: round(value / denominator, 6) for key, value in sectors.items()},
        "assetTypeWeights": {key: round(value / denominator, 6) for key, value in assets.items()},
        "strategyWeights": {key: round(value / denominator, 6) for key, value in strategies.items()},
        "largestPositionWeight": round(weights[0], 6) if weights else 0.0,
        "top3PositionWeight": round(sum(weights[:3]), 6),
        "top5PositionWeight": round(sum(weights[:5]), 6),
    }
    return {
        "positions": positions,
        "long_exposure": long_exposure,
        "short_exposure": short_exposure,
        "gross_exposure": long_exposure + short_exposure,
        "net_exposure": long_exposure - short_exposure,
        "largest_position_weight": summary["largestPositionWeight"],
        "top3_weight": summary["top3PositionWeight"],
        "top5_weight": summary["top5PositionWeight"],
        "largest_sector_weight": max((value / denominator for value in sectors.values()), default=0.0),
        "largest_asset_type_weight": max((value / denominator for value in assets.values()), default=0.0),
        "largest_strategy_weight": max((value / denominator for value in strategies.values()), default=0.0),
        "duplicate_symbol_count": sum(1 for value in symbols.values() if value > 0) - len(symbols),
        "sector_metadata_available": sector_metadata,
        "strategy_metadata_available": strategy_metadata,
        "summary": summary,
    }


def _market_risk(context: dict[str, Any], portfolio: dict[str, float], config: EnterpriseRiskFactorConfig, degraded: list[str]) -> float:
    latest = context.get("latestMarketContext", {})
    regime = str(latest.get("marketRegime", "UNKNOWN")).lower()
    confidence = _number(latest.get("confidence"))
    risk = 20.0
    if any(token in regime for token in ("bear", "risk_off", "crisis", "volatile")):
        risk += 35
    if confidence and confidence < 0.7:
        risk += 15
    if not latest:
        risk += 20
        degraded.append("market_regime_missing")
    cash_ratio = portfolio["cash"] / max(1.0, portfolio["portfolio_equity"])
    if cash_ratio < 0.05:
        risk += 15
    return _clamp(risk)


def _weight_risk(weight: float, limit: float, missing_base: float) -> float:
    if weight <= 0:
        return missing_base
    return _clamp(10 + max(0.0, weight / max(0.0001, limit) - 0.5) * 80)


def _concentration_risk(exposures: dict[str, Any], config: EnterpriseRiskFactorConfig) -> float:
    risk = 10.0
    risk += max(0.0, exposures["largest_position_weight"] - config.max_single_position_weight * 0.5) / max(0.0001, config.max_single_position_weight) * 45
    risk += max(0.0, exposures["top3_weight"] - config.max_top_3_concentration * 0.7) / max(0.0001, config.max_top_3_concentration) * 30
    risk += max(0.0, exposures["top5_weight"] - config.max_top_5_concentration * 0.8) / max(0.0001, config.max_top_5_concentration) * 20
    return _clamp(risk)


def _liquidity_risk(positions: tuple[dict[str, Any], ...], quotes: dict[str, dict[str, Any]], config: EnterpriseRiskFactorConfig, degraded: list[str]) -> float:
    if not positions:
        return 5.0
    risks = []
    for pos in positions:
        symbol = str(pos.get("symbol", "")).upper()
        quote = quotes.get(symbol, {})
        if not quote:
            risks.append(55.0)
            continue
        last = _number(quote.get("last") or quote.get("ask") or quote.get("bid"))
        bid = _number(quote.get("bid"))
        ask = _number(quote.get("ask"))
        volume = _number(quote.get("averageVolume") or quote.get("volume"))
        spread = (ask - bid) / max(0.0001, last) if bid and ask and last else config.wide_spread_threshold * 2
        participation = _value(pos) / max(1.0, volume * max(0.0001, last)) if volume and last else 0.1
        risks.append(_clamp(spread / config.wide_spread_threshold * 35 + participation / 0.05 * 35))
    if any(risk >= 55 for risk in risks) and "liquidity_data_missing" not in degraded:
        degraded.append("liquidity_data_missing")
    return round(sum(risks) / max(1, len(risks)), 4)


def _volatility_risk(positions: tuple[dict[str, Any], ...], quotes: dict[str, dict[str, Any]], context: dict[str, Any], config: EnterpriseRiskFactorConfig, degraded: list[str]) -> float:
    values = []
    for pos in positions:
        quote = quotes.get(str(pos.get("symbol", "")).upper(), {})
        vol = _number(pos.get("volatility") or quote.get("volatility"))
        if vol:
            values.append(vol)
    regime = str(context.get("latestMarketContext", {}).get("volatilityState", "")).lower()
    if not values and positions:
        degraded.append("volatility_data_missing")
        return 45.0
    avg = sum(values) / len(values) if values else 0.0
    risk = avg / max(0.0001, config.critical_volatility_threshold) * 80
    if "high" in regime or "elevated" in regime:
        risk += 15
    return _clamp(risk)


def _correlation_risk(exposures: dict[str, Any], degraded: list[str], correlation_intelligence: dict[str, Any]) -> float:
    feed = correlation_intelligence.get("riskFactorFeed", {})
    if feed:
        degraded.extend(str(item) for item in feed.get("degradedInputs", ()) if item)
        return _clamp(_number(feed.get("correlationRiskScore")))
    degraded.append("correlation_proxy_used")
    overlap = max(exposures["largest_sector_weight"], exposures["largest_asset_type_weight"], exposures["largest_strategy_weight"])
    return _clamp(20 + overlap * 75)


def _drawdown_risk(truth: dict[str, Any], closed: dict[str, Any], config: EnterpriseRiskFactorConfig, degraded: list[str]) -> float:
    rows = tuple(truth.get("portfolioLedger", ()))
    values = [_number(row.get("total_equity")) for row in rows if _number(row.get("total_equity"))]
    drawdowns = []
    peak = 0.0
    for value in values:
        peak = max(peak, value)
        if peak:
            drawdowns.append((peak - value) / peak)
    max_dd = max(drawdowns, default=0.0)
    closed_records = tuple(closed.get("latestClosedPositionTruthRecords", ())) or tuple(truth.get("closedPositionTruth", ()))
    for record in closed_records:
        max_dd = max(max_dd, abs(_number(record.get("max_drawdown_during_trade"))))
    if not values and not closed_records:
        degraded.append("drawdown_history_missing")
        return 35.0
    return _clamp(max_dd / max(0.0001, config.drawdown_high_threshold) * 70)


def _execution_risk(truth: dict[str, Any]) -> float:
    realism = truth.get("executionRealism", {})
    orders = tuple(truth.get("orderLedger", ()))
    if not orders:
        return 15.0
    rejected = _number(realism.get("rejectedOrders")) or sum(1 for order in orders if str(order.get("status", "")).upper() == "REJECTED")
    partial = _number(realism.get("partialFills")) or sum(1 for order in orders if str(order.get("status", "")).upper() in {"PARTIALLY_FILLED", "PARTIAL"})
    warnings = len(realism.get("fantasyTradeWarnings", ()))
    slippage = abs(_number(realism.get("slippageCost")))
    rate = (rejected * 45 + partial * 20 + warnings * 25) / max(1, len(orders))
    return _clamp(rate + min(20.0, slippage))


def _data_quality_risk(degraded: list[str], provider: dict[str, Any], truth: dict[str, Any]) -> float:
    risk = len(set(degraded)) * 8
    risk += provider.get("normalizationDiagnostics", {}).get("invalidObjectsRejected", 0) * 12
    if not truth.get("sourceOfTruth"):
        risk += 20
    return _clamp(risk)


def _reality_risk(reality: dict[str, Any], config: EnterpriseRiskFactorConfig) -> float:
    summary = reality.get("commanderSummary", {})
    score = _number(summary.get("overallRealityFidelityScore", 100.0))
    state = str(summary.get("learningReliabilityState", "reliable"))
    risk = 100.0 - score
    if state == "degraded":
        risk += 20
    if state in {"unsafe", "blocked"} or score < config.reality_fidelity_unsafe_threshold:
        risk += 45
    return _clamp(risk)


def _recommended_actions(scores: dict[str, float], composite: float, degraded: list[str], config: EnterpriseRiskFactorConfig) -> tuple[str, ...]:
    actions = []
    if composite >= config.halt_trading_threshold:
        actions.append("halt_trading")
    elif composite >= config.high_risk_threshold:
        actions.append("block_new_positions")
    elif composite >= config.elevated_risk_threshold:
        actions.append("request_risk_office_review")
    if scores["concentration_risk_score"] >= 60 or scores["sector_risk_score"] >= 60:
        actions.append("reduce_sector_exposure")
    if scores["strategy_risk_score"] >= 60:
        actions.append("reduce_strategy_exposure")
    if scores["liquidity_risk_score"] >= 60:
        actions.append("request_commander_review")
    if scores["reality_fidelity_risk_score"] >= 60:
        actions.append("require_reality_calibration")
    if degraded:
        actions.append("require_data_quality_repair")
    if not actions:
        actions.append("no_action")
    return tuple(dict.fromkeys(actions))


def _risk_level(score: float, config: EnterpriseRiskFactorConfig) -> str:
    if score <= config.low_risk_threshold:
        return "low"
    if score <= config.moderate_risk_threshold:
        return "moderate"
    if score <= config.elevated_risk_threshold:
        return "elevated"
    if score <= config.high_risk_threshold:
        return "high"
    return "critical"


def _capital_multiplier(score: float) -> float:
    if score >= 85:
        return 0.0
    if score >= 70:
        return 0.35
    if score >= 55:
        return 0.65
    return 1.0


def _size_multiplier(score: float) -> float:
    if score >= 85:
        return 0.0
    if score >= 70:
        return 0.5
    if score >= 55:
        return 0.75
    return 1.0


def _quotes(provider: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("symbol", "")).upper(): item for item in provider.get("normalizedObjects", {}).get("quotes", ())}


def _value(position: dict[str, Any]) -> float:
    return _number(position.get("current_value", position.get("market_value", _number(position.get("quantity")) * _number(position.get("current_price", position.get("average_cost"))))))


def _sector_for(symbol: str) -> str:
    return {"AAPL": "Technology", "MSFT": "Technology", "SPY": "Broad Market", "TLT": "Rates", "GLD": "Commodities", "QQQ": "Technology"}.get(symbol.upper(), "UNKNOWN")


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)


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
