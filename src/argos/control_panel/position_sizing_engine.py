"""Position Sizing Engine for ARGOS EO-AF."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any


RECOMMENDED_ACTIONS = (
    "approve_size",
    "reduce_size",
    "reject_size",
    "request_risk_review",
    "request_commander_review",
)


@dataclass(frozen=True)
class PositionSizingConfig:
    position_sizing_enabled: bool = True
    default_risk_per_trade_percent: float = 0.01
    max_risk_per_trade_percent: float = 0.02
    max_percent_of_volume: float = 0.01
    missing_stop_policy: str = "request_risk_review"
    missing_liquidity_policy: str = "conservative"
    missing_volatility_policy: str = "conservative"
    fractional_shares_enabled: bool = False
    minimum_order_notional: float = 25.0
    maximum_order_notional: float = 25000.0
    confidence_size_adjustment_enabled: bool = True
    volatility_size_adjustment_enabled: bool = True
    liquidity_size_adjustment_enabled: bool = True
    commander_review_confidence_threshold: float = 0.55
    risk_review_score_threshold: float = 0.75
    degraded_data_policy: str = "conservative"


@dataclass(frozen=True)
class PositionSizingRecord:
    position_sizing_id: str
    workflow_id: str
    decision_object_id: str
    capital_allocation_id: str
    portfolio_construction_id: str
    timestamp: str
    symbol: str
    asset_type: str
    side: str
    proposed_quantity: float
    proposed_notional: float
    recommended_quantity: float
    recommended_notional: float
    entry_price_reference: float
    stop_loss_reference: float
    risk_per_share: float
    risk_per_trade: float
    max_size_by_buying_power: float
    max_size_by_allocation: float
    max_size_by_construction: float
    max_size_by_risk: float
    max_size_by_liquidity: float
    max_size_by_concentration: float
    limiting_factor: str
    confidence_adjustment: float
    volatility_adjustment: float
    liquidity_adjustment: float
    final_size_score: float
    recommended_action: str
    deterministic_reasoning: tuple[str, ...]
    degraded_inputs: tuple[str, ...]
    audit_reference: str
    commander_override: dict[str, Any]
    order_execution_feed: dict[str, Any]


class PositionSizingEngine:
    """Deterministic order-size calculator that does not execute trades."""

    def __init__(self, config: PositionSizingConfig | None = None) -> None:
        self._config = config or PositionSizingConfig()
        self._records: list[PositionSizingRecord] = []
        self._last_fingerprint = ""

    def size(
        self,
        *,
        timestamp_utc: str,
        decision_object: dict[str, Any] | None,
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any],
        capital_allocation: dict[str, Any] | None,
        portfolio_construction: dict[str, Any] | None,
        decision_object_quality: dict[str, Any] | None = None,
        strategy_package_manager: dict[str, Any] | None = None,
        enterprise_reality_calibration: dict[str, Any] | None = None,
        enterprise_risk_factor: dict[str, Any] | None = None,
        correlation_intelligence: dict[str, Any] | None = None,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        enterprise_operational_guardrails: dict[str, Any] | None = None,
        commander_override: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        """Return a sizing snapshot without placing or queuing orders."""
        config = self._resolved_config(enterprise_configuration_registry)
        if not config.position_sizing_enabled:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=None, config=config)
        if not decision_object or not _decision_id(decision_object):
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=None, config=config)

        fingerprint = _fingerprint(decision_object, performance_truth, market_data_provider, capital_allocation or {}, portfolio_construction or {}, decision_object_quality or {}, strategy_package_manager or {}, enterprise_reality_calibration or {}, enterprise_risk_factor or {}, correlation_intelligence or {}, enterprise_operational_guardrails or {}, commander_override or {})
        if fingerprint == self._last_fingerprint and self._records:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=self._records[-1], config=config)

        record = self._build_record(
            timestamp_utc=timestamp_utc,
            decision_object=decision_object,
            performance_truth=performance_truth,
            market_data_provider=market_data_provider,
            capital_allocation=capital_allocation or {},
            portfolio_construction=portfolio_construction or {},
            decision_object_quality=decision_object_quality or {},
            strategy_package_manager=strategy_package_manager or {},
            enterprise_reality_calibration=enterprise_reality_calibration or {},
            enterprise_risk_factor=enterprise_risk_factor or {},
            correlation_intelligence=correlation_intelligence or {},
            enterprise_operational_guardrails=enterprise_operational_guardrails or {},
            commander_override=commander_override or {},
            audit_event_count=audit_event_count,
            config=config,
        )
        self._records.append(record)
        self._last_fingerprint = fingerprint
        return self.snapshot(timestamp_utc=timestamp_utc, latest_record=record, config=config)

    def snapshot(self, *, timestamp_utc: str, latest_record: PositionSizingRecord | None = None, config: PositionSizingConfig | None = None) -> dict[str, Any]:
        config = config or self._config
        latest = latest_record or (self._records[-1] if self._records else None)
        latest_payload = asdict(latest) if latest else {}
        return {
            "engineName": "Position Sizing Engine",
            "engineeringOrder": "EO-AF",
            "constitutionalMode": "SIZING_ONLY_NO_EXECUTION",
            "recommendedActions": RECOMMENDED_ACTIONS,
            "positionSizingRecords": tuple(asdict(item) for item in self._records),
            "latestPositionSizingRecord": latest_payload,
            "orderExecutionFeed": latest.order_execution_feed if latest else {},
            "commanderSummary": {
                "latestAction": latest.recommended_action if latest else "standby",
                "symbol": latest.symbol if latest else "",
                "recommendedQuantity": latest.recommended_quantity if latest else 0.0,
                "recommendedNotional": latest.recommended_notional if latest else 0.0,
                "limitingFactor": latest.limiting_factor if latest else "",
                "warnings": latest.degraded_inputs if latest else ("No sizing record available.",),
            },
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicScoring": True},
            "internalDiagnostics": {
                "mutatesDecisionObjects": False,
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "placesTrades": False,
                "queuesOrders": False,
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
        decision_object: dict[str, Any],
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any],
        capital_allocation: dict[str, Any],
        portfolio_construction: dict[str, Any],
        decision_object_quality: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        enterprise_reality_calibration: dict[str, Any],
        enterprise_risk_factor: dict[str, Any],
        correlation_intelligence: dict[str, Any],
        enterprise_operational_guardrails: dict[str, Any],
        commander_override: dict[str, Any],
        audit_event_count: int,
        config: PositionSizingConfig,
    ) -> PositionSizingRecord:
        portfolio = _portfolio_state(performance_truth)
        candidate = _candidate_trade(decision_object, market_data_provider, portfolio["portfolio_equity"])
        construction = portfolio_construction.get("latestPortfolioConstructionRecord", {}) or {}
        allocation = capital_allocation.get("latestCapitalAllocationRecord", {}) or {}
        allocation_feed = capital_allocation.get("positionSizingFeed") or capital_allocation.get("portfolioConstructionFeed") or {}
        symbol = candidate["symbol"]
        sector = _sector_for(symbol, decision_object)
        strategy = str(decision_object.get("currentStrategy") or decision_object.get("strategy") or "UNKNOWN")
        risk_bucket = _risk_bucket(decision_object)
        degraded: list[str] = []
        review_flags: list[str] = []
        blockers: list[str] = []

        if not allocation_feed:
            degraded.append("capital_allocation_unavailable")
        if not construction:
            degraded.append("portfolio_construction_unavailable")
        if candidate["degraded"]:
            degraded.append("market_quote_missing")
        if _halted(enterprise_operational_guardrails):
            blockers.append("operational_guardrail_halt")
        risk_feed = enterprise_risk_factor.get("positionSizingFeed", {})
        correlation_feed = correlation_intelligence.get("positionSizingFeed", {})
        if risk_feed.get("haltRecommended"):
            blockers.append("enterprise_risk_factor_halt")
        elif _number(risk_feed.get("compositeRiskScore")) >= 70:
            review_flags.append("enterprise_risk_factor_review")
        if correlation_feed.get("reviewRecommended"):
            review_flags.append("correlation_intelligence_review")

        entry = candidate["entry_price"]
        stop = candidate["stop_loss"]
        risk_per_share, stop_degraded = _risk_per_share(candidate["side"], entry, stop)
        if stop_degraded:
            degraded.append("stop_loss_missing_or_invalid")
            if config.missing_stop_policy == "reject":
                blockers.append("stop_loss_required")
            else:
                review_flags.append("missing_stop_loss_requires_risk_review")
            risk_per_share = max(entry * 0.05, 0.01)

        proposed_notional = candidate["proposed_notional"]
        proposed_quantity = candidate["proposed_quantity"]
        allowed_risk = max(0.0, portfolio["portfolio_equity"] * min(config.default_risk_per_trade_percent, config.max_risk_per_trade_percent))
        max_by_risk = max(0.0, math.floor((allowed_risk / max(risk_per_share, 0.0001)) * 10000) / 10000 * entry)
        max_by_buying_power = max(0.0, min(portfolio["buying_power"], portfolio["cash_available"]))
        max_by_allocation = _allocation_limit(allocation_feed, strategy, candidate["asset_type"], sector, risk_bucket, proposed_notional)
        max_by_construction, construction_blocker, construction_review = _construction_limit(construction, proposed_notional, commander_override)
        if construction_blocker:
            blockers.append(construction_blocker)
        if construction_review:
            review_flags.append(construction_review)
        max_by_liquidity, liquidity_adjustment, liquidity_degraded = _liquidity_limit(candidate, config)
        if liquidity_degraded:
            degraded.append(liquidity_degraded)
        max_by_concentration = _concentration_limit(performance_truth, symbol, sector, portfolio["portfolio_equity"], proposed_notional)
        volatility_adjustment, volatility_degraded = _volatility_adjustment(candidate, decision_object, config)
        if volatility_degraded:
            degraded.append(volatility_degraded)
        confidence_adjustment = _confidence_adjustment(decision_object, decision_object_quality, construction, strategy_package_manager, enterprise_reality_calibration, config)
        if confidence_adjustment < 0.65:
            review_flags.append("low_confidence_requires_commander_review")

        hard_caps = {
            "buying_power": max_by_buying_power,
            "capital_allocation": max_by_allocation,
            "portfolio_construction": max_by_construction,
            "risk_per_trade": max_by_risk,
            "liquidity": max_by_liquidity,
            "concentration": max_by_concentration,
            "maximum_order_notional": config.maximum_order_notional,
            "proposed_notional": proposed_notional,
        }
        limiting_factor, cap_notional = min(hard_caps.items(), key=lambda item: item[1])
        adjusted = cap_notional * confidence_adjustment * volatility_adjustment * liquidity_adjustment
        if risk_feed:
            adjusted *= max(0.0, _number(risk_feed.get("riskAdjustedSizeMultiplier", 1.0)))
        if correlation_feed:
            adjusted *= max(0.0, _number(correlation_feed.get("correlationAdjustedSizeMultiplier", 1.0)))
        recommended_notional = min(max_by_buying_power, config.maximum_order_notional, max(0.0, adjusted))
        recommended_quantity = _quantity(recommended_notional, entry, candidate["asset_type"], config)
        recommended_notional = round(recommended_quantity * entry, 4)
        if recommended_notional < config.minimum_order_notional:
            if recommended_notional > 0:
                review_flags.append("minimum_order_notional_not_met")
            recommended_quantity = 0.0
            recommended_notional = 0.0

        action = _recommended_action(
            proposed_notional=proposed_notional,
            recommended_notional=recommended_notional,
            blockers=blockers,
            review_flags=review_flags,
            commander_override=commander_override,
        )
        risk_per_trade = round(recommended_quantity * risk_per_share, 4)
        score = _size_score(recommended_notional, proposed_notional, confidence_adjustment, volatility_adjustment, liquidity_adjustment, degraded, blockers, review_flags)
        reasoning = (
            f"Proposed notional {round(proposed_notional, 4)} for {symbol} at entry reference {round(entry, 4)}.",
            f"Risk per share {round(risk_per_share, 4)} with allowed dollar risk {round(allowed_risk, 4)}.",
            f"Hard caps evaluated: buying power {round(max_by_buying_power, 4)}, allocation {round(max_by_allocation, 4)}, construction {round(max_by_construction, 4)}, risk {round(max_by_risk, 4)}, liquidity {round(max_by_liquidity, 4)}, concentration {round(max_by_concentration, 4)}.",
            f"Limiting factor {limiting_factor}; confidence adjustment {round(confidence_adjustment, 4)}, volatility adjustment {round(volatility_adjustment, 4)}, liquidity adjustment {round(liquidity_adjustment, 4)}.",
            "Position Sizing Engine returns an order-request feed only; it does not execute, queue, mutate ledgers, or create positions.",
        )
        if commander_override:
            reasoning = ("Commander override recorded; buying power, broker rules, emergency halts, and audit requirements remain binding.",) + reasoning
        order_feed = {
            "symbol": symbol,
            "asset_type": candidate["asset_type"],
            "side": candidate["side"],
            "recommended_quantity": recommended_quantity,
            "recommended_notional": recommended_notional,
            "order_type": str(decision_object.get("orderType", "market")).upper(),
            "time_in_force": str(decision_object.get("timeInForce", "DAY")).upper(),
            "sizing_record_reference": f"PSIZE-{len(self._records) + 1:06d}",
            "execution_allowed_by_sizing": action in {"approve_size", "reduce_size"},
            "requires_commander_review": action == "request_commander_review",
            "requires_risk_review": action == "request_risk_review",
        }
        return PositionSizingRecord(
            position_sizing_id=f"PSIZE-{len(self._records) + 1:06d}",
            workflow_id=str(decision_object.get("workflowId", "")),
            decision_object_id=_decision_id(decision_object),
            capital_allocation_id=str(allocation.get("capital_allocation_id", "")),
            portfolio_construction_id=str(construction.get("portfolio_construction_id", "")),
            timestamp=timestamp_utc,
            symbol=symbol,
            asset_type=candidate["asset_type"],
            side=candidate["side"],
            proposed_quantity=round(proposed_quantity, 4),
            proposed_notional=round(proposed_notional, 4),
            recommended_quantity=recommended_quantity,
            recommended_notional=recommended_notional,
            entry_price_reference=round(entry, 4),
            stop_loss_reference=round(stop, 4),
            risk_per_share=round(risk_per_share, 4),
            risk_per_trade=risk_per_trade,
            max_size_by_buying_power=round(max_by_buying_power, 4),
            max_size_by_allocation=round(max_by_allocation, 4),
            max_size_by_construction=round(max_by_construction, 4),
            max_size_by_risk=round(max_by_risk, 4),
            max_size_by_liquidity=round(max_by_liquidity, 4),
            max_size_by_concentration=round(max_by_concentration, 4),
            limiting_factor=limiting_factor,
            confidence_adjustment=round(confidence_adjustment, 4),
            volatility_adjustment=round(volatility_adjustment, 4),
            liquidity_adjustment=round(liquidity_adjustment, 4),
            final_size_score=score,
            recommended_action=action,
            deterministic_reasoning=reasoning,
            degraded_inputs=tuple(dict.fromkeys(degraded + review_flags + blockers)),
            audit_reference=f"AE-POSITION-SIZING-{audit_event_count + len(self._records) + 1:06d}",
            commander_override=dict(commander_override),
            order_execution_feed=order_feed,
        )

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None) -> PositionSizingConfig:
        values = asdict(self._config)
        for item in (enterprise_configuration_registry or {}).get("configurationRegistry", ()):
            key = _config_key(str(item.get("name", "")))
            if key in values:
                values[key] = _coerce_config_value(item.get("currentValue", values[key]), values[key])
        return PositionSizingConfig(**values)


def _portfolio_state(performance_truth: dict[str, Any]) -> dict[str, float]:
    paper = performance_truth.get("paperAccount", {})
    latest = (performance_truth.get("portfolioLedger") or ({},))[-1]
    positions = tuple(performance_truth.get("positionRegistry", {}).get("activePositions", ())) or tuple(performance_truth.get("positionLedger", ()))
    market_value = sum(_number(item.get("current_value", item.get("market_value", 0.0))) for item in positions)
    cash = _number(latest.get("cash", paper.get("cash", paper.get("buyingPower", 0.0))))
    equity = _number(latest.get("total_equity", cash + market_value)) or cash + market_value
    return {"cash_available": max(0.0, cash), "buying_power": max(0.0, _number(paper.get("buyingPower", cash))), "portfolio_equity": max(0.0, equity)}


def _candidate_trade(decision: dict[str, Any], market_data: dict[str, Any], equity: float) -> dict[str, Any]:
    symbol = str(decision.get("symbol") or decision.get("ticker") or decision.get("assetSymbol") or decision.get("marketContext", {}).get("symbol", "AAPL")).upper()
    asset_type = str(decision.get("assetType") or ("ETF" if symbol in {"SPY", "TLT", "GLD", "QQQ", "IWM"} else "STOCK"))
    side = str(decision.get("side") or "BUY").upper()
    quote = _quote_for(symbol, market_data)
    entry = _number(decision.get("referencePrice")) or _number(quote.get("ask")) or _number(quote.get("last")) or _number(decision.get("targetPrice")) or 100.0
    requested_quantity = _number(decision.get("proposedQuantity") or decision.get("quantity"))
    size = _number(decision.get("positionSizeRecommendation") or decision.get("position_size_recommendation"))
    proposed_notional = requested_quantity * entry if requested_quantity else max(0.0, equity * (size if 0 < size <= 1 else 0.02))
    proposed_quantity = requested_quantity or proposed_notional / max(0.0001, entry)
    return {
        "symbol": symbol,
        "asset_type": asset_type,
        "side": side,
        "entry_price": entry,
        "stop_loss": _number(decision.get("stopLoss") or decision.get("stop_loss")),
        "proposed_notional": proposed_notional,
        "proposed_quantity": proposed_quantity,
        "quote": quote,
        "degraded": not bool(quote),
    }


def _risk_per_share(side: str, entry: float, stop: float) -> tuple[float, bool]:
    if side == "SELL":
        value = stop - entry if stop > entry else 0.0
    else:
        value = entry - stop if 0 < stop < entry else 0.0
    return (value, value <= 0)


def _allocation_limit(feed: dict[str, Any], strategy: str, asset_type: str, sector: str, risk_bucket: str, proposed: float) -> float:
    if not feed:
        return max(0.0, proposed * 0.5)
    deployable = _number(feed.get("deployableCapital", proposed))
    per_trade = _number(feed.get("perTradeCapitalCeiling", deployable)) or deployable
    limits = [
        deployable,
        per_trade,
        _number(feed.get("maxCapitalPerStrategy", {}).get(strategy, deployable)),
        _number(feed.get("maxCapitalPerAssetType", {}).get(asset_type, deployable)),
        _number(feed.get("maxCapitalPerSector", {}).get(sector, deployable)),
        _number(feed.get("maxCapitalPerRiskBucket", {}).get(risk_bucket, deployable)),
    ]
    return max(0.0, min(value for value in limits if value >= 0.0))


def _construction_limit(record: dict[str, Any], proposed: float, commander_override: dict[str, Any]) -> tuple[float, str, str]:
    if not record:
        return max(0.0, proposed * 0.5), "", "portfolio_construction_missing_requires_review"
    action = str(record.get("recommended_action", "")).lower()
    recommended = _number(record.get("recommended_notional", proposed))
    if action in {"reject", "defer"} and not commander_override:
        return 0.0, "portfolio_construction_rejected", ""
    if action in {"reject", "defer"} and commander_override:
        return max(0.0, min(proposed, recommended or proposed)), "", "commander_override_requires_review"
    if action in {"request_risk_review", "request_commander_review"}:
        return max(0.0, min(proposed, recommended or proposed)), "", f"portfolio_construction_{action}"
    if action == "approve_reduced":
        return max(0.0, min(proposed, recommended)), "", ""
    return max(0.0, min(proposed, recommended or proposed)), "", ""


def _liquidity_limit(candidate: dict[str, Any], config: PositionSizingConfig) -> tuple[float, float, str]:
    quote = candidate["quote"]
    proposed = candidate["proposed_notional"]
    entry = candidate["entry_price"]
    if not quote:
        if config.missing_liquidity_policy == "reject":
            return 0.0, 1.0, "liquidity_missing"
        return round(proposed * 0.5, 4), 0.75 if config.liquidity_size_adjustment_enabled else 1.0, "liquidity_missing"
    volume = _number(quote.get("averageVolume") or quote.get("volume"))
    bid = _number(quote.get("bid"))
    ask = _number(quote.get("ask"))
    spread = max(0.0, ask - bid) / max(0.0001, entry) if bid and ask else 0.02
    max_notional = volume * config.max_percent_of_volume * entry if volume else proposed * 0.5
    adjustment = 1.0
    if config.liquidity_size_adjustment_enabled:
        adjustment = 0.65 if spread > 0.01 else 0.85 if spread > 0.005 else 1.0
    degraded = "" if volume else "liquidity_volume_missing"
    return round(max(0.0, max_notional), 4), adjustment, degraded


def _volatility_adjustment(candidate: dict[str, Any], decision: dict[str, Any], config: PositionSizingConfig) -> tuple[float, str]:
    raw = _number(decision.get("volatility") or decision.get("volatilityScore") or candidate["quote"].get("volatility"))
    if raw <= 0:
        return (0.8 if config.missing_volatility_policy == "conservative" and config.volatility_size_adjustment_enabled else 1.0, "volatility_missing")
    if not config.volatility_size_adjustment_enabled:
        return 1.0, ""
    return (0.5 if raw >= 0.60 else 0.75 if raw >= 0.35 else 1.0, "")


def _confidence_adjustment(decision: dict[str, Any], quality: dict[str, Any], construction: dict[str, Any], strategy_manager: dict[str, Any], reality: dict[str, Any], config: PositionSizingConfig) -> float:
    if not config.confidence_size_adjustment_enabled:
        return 1.0
    values = []
    for value in (decision.get("confidence"), decision.get("decisionObjectQuality"), construction.get("construction_score")):
        number = _number(value)
        if number:
            values.append(number / 100 if number > 1 else number)
    latest_quality = quality.get("latestQualityReport", {}) or quality.get("commanderSummary", {})
    quality_score = _number(latest_quality.get("overallScore") or latest_quality.get("qualityScore"))
    if quality_score:
        values.append(quality_score / 100 if quality_score > 1 else quality_score)
    reality_score = _number((reality.get("commanderSummary", {}) or {}).get("overallRealityFidelityScore"))
    if reality_score:
        values.append(reality_score / 100 if reality_score > 1 else reality_score)
    packages = tuple(strategy_manager.get("activePackages", ()))
    for package in packages:
        confidence = _number(package.get("confidence") or package.get("confidenceScore"))
        if confidence:
            values.append(confidence / 100 if confidence > 1 else confidence)
            break
    aggregate = sum(values) / len(values) if values else 0.65
    return round(max(0.25, min(1.0, aggregate)), 4)


def _concentration_limit(performance_truth: dict[str, Any], symbol: str, sector: str, equity: float, proposed: float) -> float:
    positions = tuple(performance_truth.get("positionRegistry", {}).get("activePositions", ())) or tuple(performance_truth.get("positionLedger", ()))
    symbol_current = 0.0
    sector_current = 0.0
    for position in positions:
        value = _number(position.get("current_value", position.get("market_value", 0.0)))
        if str(position.get("symbol", "")).upper() == symbol:
            symbol_current += value
        if _sector_for(str(position.get("symbol", "")), position) == sector:
            sector_current += value
    single_cap = max(0.0, equity * 0.20 - symbol_current)
    sector_cap = max(0.0, equity * 0.35 - sector_current)
    return round(max(0.0, min(single_cap, sector_cap, proposed)), 4)


def _quantity(notional: float, price: float, asset_type: str, config: PositionSizingConfig) -> float:
    raw = max(0.0, notional) / max(0.0001, price)
    if config.fractional_shares_enabled and asset_type.upper() in {"STOCK", "ETF"}:
        return round(math.floor(raw * 10000) / 10000, 4)
    return float(math.floor(raw))


def _recommended_action(*, proposed_notional: float, recommended_notional: float, blockers: list[str], review_flags: list[str], commander_override: dict[str, Any]) -> str:
    if blockers:
        if commander_override and blockers == ["portfolio_construction_rejected"] and recommended_notional > 0:
            return "request_commander_review"
        return "reject_size"
    if recommended_notional <= 0:
        return "reject_size"
    if any("risk" in flag for flag in review_flags):
        return "request_risk_review"
    if review_flags:
        return "request_commander_review"
    if recommended_notional < proposed_notional:
        return "reduce_size"
    return "approve_size"


def _size_score(recommended: float, proposed: float, confidence: float, volatility: float, liquidity: float, degraded: list[str], blockers: list[str], review_flags: list[str]) -> float:
    score = 100.0 * (recommended / max(1.0, proposed))
    score *= confidence * volatility * liquidity
    score -= len(degraded) * 4
    score -= len(review_flags) * 8
    score -= len(blockers) * 25
    return round(max(0.0, min(100.0, score)), 4)


def _risk_bucket(decision: dict[str, Any]) -> str:
    risk = _number(decision.get("riskScore"))
    if risk >= 0.75:
        return "high_risk"
    if risk >= 0.4:
        return "medium_risk"
    return "low_risk"


def _halted(guardrails: dict[str, Any]) -> bool:
    return str(guardrails.get("readinessState", "Authorized")) in {"Emergency Halt", "Safe Mode", "Paused", "Offline", "Restricted"}


def _quote_for(symbol: str, market_data: dict[str, Any]) -> dict[str, Any]:
    for quote in market_data.get("normalizedObjects", {}).get("quotes", ()):
        if str(quote.get("symbol", "")).upper() == symbol:
            return quote
    return {}


def _sector_for(symbol: str, source: dict[str, Any]) -> str:
    sector = source.get("sector") or source.get("market_context", {}).get("sector") or source.get("marketContext", {}).get("sector")
    if sector:
        return str(sector)
    return {"AAPL": "Technology", "MSFT": "Technology", "SPY": "Broad Market", "TLT": "Rates", "GLD": "Commodities", "QQQ": "Technology"}.get(symbol.upper(), "UNKNOWN")


def _decision_id(decision: dict[str, Any]) -> str:
    return str(decision.get("decisionObjectId") or decision.get("decision_object_id") or "")


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
