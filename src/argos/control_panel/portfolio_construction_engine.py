"""Portfolio Construction Engine for ARGOS EO-AC."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


RECOMMENDED_ACTIONS = (
    "approve",
    "approve_reduced",
    "defer",
    "reject",
    "request_risk_review",
    "request_commander_review",
)


@dataclass(frozen=True)
class PortfolioConstructionConfig:
    portfolio_construction_enabled: bool = True
    max_single_position_percent: float = 0.20
    max_sector_percent: float = 0.35
    max_asset_type_percent: float = 0.75
    max_strategy_percent: float = 0.35
    max_open_positions: int = 10
    max_daily_new_positions: int = 5
    max_open_orders: int = 5
    minimum_cash_reserve_percent: float = 0.05
    approve_reduced_size_enabled: bool = True
    correlation_awareness_enabled: bool = True
    liquidity_checks_enabled: bool = True
    approve_score_threshold: float = 75.0
    commander_review_threshold: float = 55.0
    degraded_data_policy: str = "conservative"


@dataclass(frozen=True)
class PortfolioConstructionRecord:
    portfolio_construction_id: str
    workflow_id: str
    decision_object_id: str
    timestamp: str
    symbol: str
    asset_type: str
    proposed_side: str
    proposed_quantity: float
    proposed_notional: float
    recommended_action: str
    recommended_quantity: float
    recommended_notional: float
    allocation_percent: float
    cash_available: float
    portfolio_equity: float
    current_exposure: float
    projected_exposure: float
    concentration_impact: dict[str, Any]
    sector_impact: dict[str, Any]
    asset_type_impact: dict[str, Any]
    strategy_impact: dict[str, Any]
    correlation_impact: dict[str, Any]
    liquidity_assessment: dict[str, Any]
    risk_budget_impact: dict[str, Any]
    construction_score: float
    rejection_reason: str
    deterministic_reasoning: tuple[str, ...]
    next_engine: str
    audit_reference: str
    degraded: bool
    commander_override: dict[str, Any]


class PortfolioConstructionEngine:
    """Deterministic portfolio-fit evaluator for proposed trades."""

    def __init__(self, config: PortfolioConstructionConfig | None = None) -> None:
        self._config = config or PortfolioConstructionConfig()
        self._records: list[PortfolioConstructionRecord] = []
        self._last_fingerprint = ""

    def evaluate(
        self,
        *,
        timestamp_utc: str,
        decision_object: dict[str, Any] | None,
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        enterprise_operational_guardrails: dict[str, Any] | None = None,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        capital_allocation: dict[str, Any] | None = None,
        enterprise_risk_factor: dict[str, Any] | None = None,
        correlation_intelligence: dict[str, Any] | None = None,
        commander_override: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        """Evaluate a candidate Decision Object without executing orders."""
        config = self._resolved_config(enterprise_configuration_registry)
        if not config.portfolio_construction_enabled:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=None, config=config)

        if not decision_object or not _decision_id(decision_object):
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=None, config=config)

        fingerprint = _fingerprint(decision_object, performance_truth, market_data_provider, strategy_package_manager, enterprise_operational_guardrails or {}, capital_allocation or {}, enterprise_risk_factor or {}, correlation_intelligence or {}, commander_override or {})
        if fingerprint == self._last_fingerprint and self._records:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=self._records[-1], config=config)

        record = self._build_record(
            timestamp_utc=timestamp_utc,
            decision_object=decision_object,
            performance_truth=performance_truth,
            market_data_provider=market_data_provider,
            strategy_package_manager=strategy_package_manager,
            enterprise_operational_guardrails=enterprise_operational_guardrails or {},
            capital_allocation=capital_allocation or {},
            enterprise_risk_factor=enterprise_risk_factor or {},
            correlation_intelligence=correlation_intelligence or {},
            commander_override=commander_override or {},
            audit_event_count=audit_event_count,
            config=config,
        )
        self._records.append(record)
        self._last_fingerprint = fingerprint
        return self.snapshot(timestamp_utc=timestamp_utc, latest_record=record, config=config)

    def snapshot(self, *, timestamp_utc: str, latest_record: PortfolioConstructionRecord | None = None, config: PortfolioConstructionConfig | None = None) -> dict[str, Any]:
        config = config or self._config
        latest = latest_record or (self._records[-1] if self._records else None)
        latest_payload = asdict(latest) if latest else {}
        approval = bool(latest and latest.recommended_action in {"approve", "approve_reduced"})
        override = bool(latest and latest.commander_override)
        risk_blocked = bool(latest and latest.risk_budget_impact.get("status") == "BLOCKED")
        return {
            "engineName": "Portfolio Construction Engine",
            "engineeringOrder": "EO-AC",
            "constitutionalMode": "PORTFOLIO_FIT_REVIEW_ONLY",
            "recommendedActions": RECOMMENDED_ACTIONS,
            "portfolioConstructionRecords": tuple(asdict(item) for item in self._records),
            "latestPortfolioConstructionRecord": latest_payload,
            "decisionWorkflowGate": {
                "portfolioConstructionRequiredBeforeExecution": True,
                "latestDecisionObjectId": latest.decision_object_id if latest else "",
                "executionMayProceed": (approval or override) and not risk_blocked,
                "commanderOverrideRecorded": override,
                "brokerRulesStillRequired": True,
                "emergencyHaltStillBlocks": True,
                "directDecisionObjectMutation": False,
            },
            "commanderSummary": {
                "latestAction": latest.recommended_action if latest else "standby",
                "constructionScore": latest.construction_score if latest else 0.0,
                "symbol": latest.symbol if latest else "",
                "allocationPercent": latest.allocation_percent if latest else 0.0,
                "rejectionReason": latest.rejection_reason if latest else "",
                "nextEngine": latest.next_engine if latest else "Analyst Decision Object",
            },
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicScoring": True},
            "internalDiagnostics": {
                "mutatesDecisionObjects": False,
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "placesTrades": False,
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
        strategy_package_manager: dict[str, Any],
        enterprise_operational_guardrails: dict[str, Any],
        capital_allocation: dict[str, Any],
        enterprise_risk_factor: dict[str, Any],
        correlation_intelligence: dict[str, Any],
        commander_override: dict[str, Any],
        audit_event_count: int,
        config: PortfolioConstructionConfig,
    ) -> PortfolioConstructionRecord:
        portfolio = _portfolio_state(performance_truth)
        candidate = _candidate_trade(decision_object, market_data_provider, portfolio["portfolio_equity"])
        exposures = _exposures(performance_truth)
        symbol = candidate["symbol"]
        sector = _sector_for(symbol, decision_object)
        strategy = str(decision_object.get("currentStrategy") or decision_object.get("strategy") or "UNKNOWN")
        proposed = candidate["proposed_notional"]
        equity = max(1.0, portfolio["portfolio_equity"])
        cash_after = portfolio["cash_available"] - proposed
        reserve_required = equity * config.minimum_cash_reserve_percent
        current_symbol = exposures["symbols"].get(symbol, 0.0)
        projected_symbol = current_symbol + proposed
        sector_current = exposures["sectors"].get(sector, 0.0)
        asset_type_current = exposures["asset_types"].get(candidate["asset_type"], 0.0)
        strategy_current = exposures["strategies"].get(strategy, 0.0)
        open_order_symbol = symbol in exposures["open_order_symbols"]
        concentration = _impact(projected_symbol / equity, config.max_single_position_percent)
        sector_impact = _impact((sector_current + proposed) / equity, config.max_sector_percent)
        asset_impact = _impact((asset_type_current + proposed) / equity, config.max_asset_type_percent)
        strategy_impact = _impact((strategy_current + proposed) / equity, config.max_strategy_percent)
        correlation = _correlation_impact(symbol, sector, strategy, exposures, open_order_symbol, config)
        liquidity = _liquidity_assessment(candidate, market_data_provider, config)
        risk = _risk_budget(decision_object, proposed, equity, enterprise_operational_guardrails)
        allocation_limit = _allocation_limit(capital_allocation, strategy, candidate["asset_type"], sector)
        risk_feed = enterprise_risk_factor.get("portfolioConstructionFeed", {})
        correlation_feed = correlation_intelligence.get("portfolioConstructionFeed", {})
        degraded = candidate["degraded"] or liquidity["dataQuality"] == "DEGRADED"
        reasoning: list[str] = []
        blockers: list[str] = []
        reducers: list[str] = []

        if portfolio["open_positions"] >= config.max_open_positions:
            blockers.append("max_open_positions_exceeded")
        if exposures["open_order_count"] >= config.max_open_orders:
            blockers.append("max_open_orders_exceeded")
        if cash_after < reserve_required:
            blockers.append("minimum_cash_reserve_violation")
        for label, impact in (("single_position_concentration", concentration), ("sector_concentration", sector_impact), ("asset_type_concentration", asset_impact), ("strategy_concentration", strategy_impact)):
            if impact["status"] == "VIOLATION":
                reducers.append(label)
        if correlation["duplicateSymbol"] or correlation["openOrderDuplicate"]:
            reducers.append("duplicate_symbol_or_open_order_exposure")
        if liquidity["status"] in {"POOR", "DEGRADED"}:
            reducers.append("poor_liquidity")
        if risk["status"] == "BLOCKED":
            blockers.append(risk["reason"])
        if risk["status"] == "REVIEW":
            reducers.append("risk_review_required")
        if allocation_limit["status"] == "CONSTRAINED":
            reducers.append("capital_allocation_budget_constrained")
        if risk_feed.get("haltRecommended"):
            blockers.append("enterprise_risk_factor_halt")
        elif _number(risk_feed.get("compositeRiskScore")) >= 70:
            reducers.append("enterprise_risk_factor_high")
        if correlation_feed.get("reviewRecommended"):
            reducers.append("correlation_intelligence_review")

        reduced_notional = _reduced_notional(proposed, equity, config, portfolio["cash_available"], reserve_required, current_symbol, sector_current)
        reduced_notional = min(reduced_notional, allocation_limit["remainingBudget"])
        if risk_feed:
            reduced_notional = round(reduced_notional * max(0.0, _number(risk_feed.get("riskAdjustedSizeMultiplier", 1.0))), 4)
        if correlation_feed:
            reduced_notional = round(reduced_notional * max(0.0, _number(correlation_feed.get("correlationAdjustedSizeMultiplier", 1.0))), 4)
        score = _construction_score(concentration, sector_impact, asset_impact, strategy_impact, correlation, liquidity, risk, portfolio, degraded, blockers)
        recommended_action = _recommended_action(score, blockers, reducers, reduced_notional, proposed, config, commander_override)
        rejection_reason = ", ".join(blockers or reducers) if recommended_action in {"reject", "defer", "request_risk_review", "request_commander_review"} else ""
        if commander_override:
            reasoning.append("Commander override recorded; broker rules, emergency halts, buying power, and audit requirements remain binding.")
        reasoning.extend((
            f"Candidate {symbol} proposed notional {round(proposed, 4)} against equity {round(equity, 4)}.",
            f"Projected symbol concentration {round(concentration['projectedPercent'] * 100, 4)}%.",
            f"Cash after proposal {round(cash_after, 4)} with reserve requirement {round(reserve_required, 4)}.",
            f"Liquidity status {liquidity['status']}; risk status {risk['status']}.",
            f"Capital allocation remaining budget {round(allocation_limit['remainingBudget'], 4)}.",
            f"Enterprise risk factor score {_number(risk_feed.get('compositeRiskScore')) if risk_feed else 'unavailable'}.",
        ))
        recommended_notional = reduced_notional if recommended_action == "approve_reduced" else (proposed if recommended_action == "approve" else 0.0)
        recommended_quantity = round(recommended_notional / max(0.0001, candidate["reference_price"]), 4)
        return PortfolioConstructionRecord(
            portfolio_construction_id=f"PCON-{len(self._records) + 1:06d}",
            workflow_id=str(decision_object.get("workflowId", "")),
            decision_object_id=_decision_id(decision_object),
            timestamp=timestamp_utc,
            symbol=symbol,
            asset_type=candidate["asset_type"],
            proposed_side=candidate["side"],
            proposed_quantity=candidate["proposed_quantity"],
            proposed_notional=round(proposed, 4),
            recommended_action=recommended_action,
            recommended_quantity=recommended_quantity,
            recommended_notional=round(recommended_notional, 4),
            allocation_percent=round(recommended_notional / equity, 6),
            cash_available=round(portfolio["cash_available"], 4),
            portfolio_equity=round(equity, 4),
            current_exposure=round(exposures["long_exposure"] / equity, 6),
            projected_exposure=round((exposures["long_exposure"] + recommended_notional) / equity, 6),
            concentration_impact=concentration,
            sector_impact={**sector_impact, "sector": sector},
            asset_type_impact={**asset_impact, "assetType": candidate["asset_type"]},
            strategy_impact={**strategy_impact, "strategy": strategy},
            correlation_impact=correlation,
            liquidity_assessment=liquidity,
            risk_budget_impact=risk,
            construction_score=score,
            rejection_reason=rejection_reason,
            deterministic_reasoning=tuple(reasoning),
            next_engine=_next_engine(recommended_action),
            audit_reference=f"AE-PORTFOLIO-CONSTRUCTION-{audit_event_count + len(self._records) + 1:06d}",
            degraded=degraded,
            commander_override=dict(commander_override),
        )

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None) -> PortfolioConstructionConfig:
        values = asdict(self._config)
        for item in (enterprise_configuration_registry or {}).get("configurationRegistry", ()):
            key = _config_key(str(item.get("name", "")))
            if key in values:
                values[key] = _coerce_config_value(item.get("currentValue", values[key]), values[key])
        return PortfolioConstructionConfig(**values)


def _portfolio_state(performance_truth: dict[str, Any]) -> dict[str, Any]:
    paper = performance_truth.get("paperAccount", {})
    latest = (performance_truth.get("portfolioLedger") or ({},))[-1]
    positions = tuple(performance_truth.get("positionRegistry", {}).get("activePositions", ())) or tuple(performance_truth.get("positionLedger", ()))
    market_value = sum(_number(item.get("current_value", item.get("market_value", 0.0))) for item in positions)
    cash = _number(latest.get("cash", paper.get("cash", paper.get("buyingPower", 0.0))))
    equity = _number(latest.get("total_equity", cash + market_value))
    if equity <= 0:
        equity = cash + market_value
    return {"cash_available": cash, "buying_power": _number(paper.get("buyingPower", cash)), "portfolio_equity": max(0.0, equity), "open_positions": len(positions)}


def _candidate_trade(decision: dict[str, Any], market_data: dict[str, Any], equity: float) -> dict[str, Any]:
    symbol = str(decision.get("symbol") or decision.get("ticker") or decision.get("assetSymbol") or decision.get("marketContext", {}).get("symbol", "AAPL")).upper()
    asset_type = str(decision.get("assetType") or ("ETF" if symbol in {"SPY", "TLT", "GLD", "QQQ", "IWM"} else "STOCK"))
    side = str(decision.get("side") or "BUY").upper()
    quote = _quote_for(symbol, market_data)
    reference_price = _number(decision.get("referencePrice")) or _number(quote.get("ask")) or _number(quote.get("last")) or _number(decision.get("targetPrice")) or 100.0
    requested_quantity = _number(decision.get("proposedQuantity") or decision.get("quantity"))
    size = _number(decision.get("positionSizeRecommendation") or decision.get("position_size_recommendation"))
    proposed_notional = requested_quantity * reference_price if requested_quantity else max(0.0, equity * (size if 0 < size <= 1 else 0.02))
    proposed_quantity = requested_quantity or round(proposed_notional / max(0.0001, reference_price), 4)
    return {"symbol": symbol, "asset_type": asset_type, "side": side, "reference_price": reference_price, "proposed_notional": proposed_notional, "proposed_quantity": proposed_quantity, "quote": quote, "degraded": not bool(quote)}


def _exposures(performance_truth: dict[str, Any]) -> dict[str, Any]:
    positions = tuple(performance_truth.get("positionRegistry", {}).get("activePositions", ())) or tuple(performance_truth.get("positionLedger", ()))
    orders = tuple(performance_truth.get("orderLedger", ()))
    symbols: dict[str, float] = {}
    sectors: dict[str, float] = {}
    asset_types: dict[str, float] = {}
    strategies: dict[str, float] = {}
    for position in positions:
        symbol = str(position.get("symbol", "")).upper()
        value = _number(position.get("current_value", position.get("market_value", 0.0)))
        symbols[symbol] = symbols.get(symbol, 0.0) + value
        sectors[_sector_for(symbol, position)] = sectors.get(_sector_for(symbol, position), 0.0) + value
        asset = str(position.get("asset_type", "UNKNOWN"))
        asset_types[asset] = asset_types.get(asset, 0.0) + value
        strategy = str(position.get("strategy_id", position.get("currentStrategy", "UNKNOWN")))
        strategies[strategy] = strategies.get(strategy, 0.0) + value
    open_orders = [order for order in orders if str(order.get("status", "")).upper() in {"QUEUED", "PENDING", "SUBMITTED", "PARTIALLY_FILLED"}]
    return {"symbols": symbols, "sectors": sectors, "asset_types": asset_types, "strategies": strategies, "open_order_symbols": {str(order.get("symbol", "")).upper() for order in open_orders}, "open_order_count": len(open_orders), "long_exposure": sum(symbols.values())}


def _impact(projected_percent: float, limit: float) -> dict[str, Any]:
    return {"projectedPercent": round(projected_percent, 6), "limitPercent": round(limit, 6), "status": "VIOLATION" if projected_percent > limit else "OK", "excessPercent": round(max(0.0, projected_percent - limit), 6)}


def _correlation_impact(symbol: str, sector: str, strategy: str, exposures: dict[str, Any], open_order_duplicate: bool, config: PortfolioConstructionConfig) -> dict[str, Any]:
    duplicate = symbol in exposures["symbols"]
    same_sector = sector in exposures["sectors"]
    same_strategy = strategy in exposures["strategies"]
    overlap = sum(1 for flag in (duplicate, same_sector, same_strategy, open_order_duplicate) if flag)
    return {"mode": "simple_overlap" if config.correlation_awareness_enabled else "disabled", "duplicateSymbol": duplicate, "sameSector": same_sector, "sameStrategy": same_strategy, "openOrderDuplicate": open_order_duplicate, "overlapCount": overlap, "status": "HIGH_OVERLAP" if overlap >= 2 else "OK"}


def _liquidity_assessment(candidate: dict[str, Any], market_data: dict[str, Any], config: PortfolioConstructionConfig) -> dict[str, Any]:
    quote = candidate["quote"]
    if not config.liquidity_checks_enabled:
        return {"status": "NOT_CHECKED", "dataQuality": "DEGRADED", "spreadPercent": 0.0, "partialFillRisk": "UNKNOWN"}
    if not quote:
        return {"status": "DEGRADED", "dataQuality": "DEGRADED", "spreadPercent": 0.0, "partialFillRisk": "UNKNOWN"}
    bid = _number(quote.get("bid"))
    ask = _number(quote.get("ask"))
    last = _number(quote.get("last")) or (bid + ask) / 2
    spread = (ask - bid) / max(0.0001, last)
    volume = _number(quote.get("volume"))
    notional = candidate["proposed_notional"]
    poor = spread > 0.01 or (volume and notional > volume * last * 0.05)
    return {"status": "POOR" if poor else "GOOD", "dataQuality": "NORMAL", "spreadPercent": round(spread, 6), "averageVolume": volume, "partialFillRisk": "HIGH" if poor else "LOW", "expectedSlippage": round(spread * notional, 4)}


def _risk_budget(decision: dict[str, Any], proposed_notional: float, equity: float, guardrails: dict[str, Any]) -> dict[str, Any]:
    readiness = str(guardrails.get("readinessState", "Authorized"))
    if readiness in {"Emergency Halt", "Safe Mode", "Paused", "Offline"}:
        return {"status": "BLOCKED", "reason": "risk_halt_active", "capitalAtRiskPercent": 0.0}
    risk_score = _number(decision.get("riskScore"))
    stop = _number(decision.get("stopLoss"))
    reference = _number(decision.get("referencePrice") or decision.get("targetPrice")) or 100.0
    stop_risk = max(0.0, (reference - stop) / max(0.0001, reference)) if stop else max(0.02, risk_score * 0.1)
    capital_at_risk = proposed_notional * stop_risk
    risk_percent = capital_at_risk / max(1.0, equity)
    status = "REVIEW" if risk_percent > 0.02 or risk_score > 0.75 else "OK"
    return {"status": status, "reason": "risk_budget_review_required" if status == "REVIEW" else "", "riskScore": risk_score, "capitalAtRisk": round(capital_at_risk, 4), "capitalAtRiskPercent": round(risk_percent, 6), "maxPositionRiskPercent": 0.02}


def _allocation_limit(capital_allocation: dict[str, Any], strategy: str, asset_type: str, sector: str) -> dict[str, Any]:
    feed = capital_allocation.get("portfolioConstructionFeed", {})
    deployable = _number(feed.get("deployableCapital", 0.0))
    if not feed:
        return {"status": "UNKNOWN", "remainingBudget": float("inf")}
    limits = [
        deployable,
        _number(feed.get("maxCapitalPerStrategy", {}).get(strategy, deployable)),
        _number(feed.get("maxCapitalPerAssetType", {}).get(asset_type, deployable)),
        _number(feed.get("maxCapitalPerSector", {}).get(sector, deployable)),
    ]
    remaining = max(0.0, min(value for value in limits if value >= 0.0))
    return {"status": "CONSTRAINED" if remaining <= 0.0 or remaining < deployable else "AVAILABLE", "remainingBudget": remaining}


def _construction_score(concentration: dict[str, Any], sector: dict[str, Any], asset: dict[str, Any], strategy: dict[str, Any], correlation: dict[str, Any], liquidity: dict[str, Any], risk: dict[str, Any], portfolio: dict[str, Any], degraded: bool, blockers: list[str]) -> float:
    score = 100.0
    score -= 35 if blockers else 0
    for impact in (concentration, sector, asset, strategy):
        score -= impact["excessPercent"] * 180
    score -= correlation["overlapCount"] * 7
    score -= 18 if liquidity["status"] == "POOR" else 8 if liquidity["status"] == "DEGRADED" else 0
    score -= 30 if risk["status"] == "BLOCKED" else 15 if risk["status"] == "REVIEW" else 0
    score -= 8 if degraded else 0
    score += min(5.0, portfolio["cash_available"] / max(1.0, portfolio["portfolio_equity"]) * 5)
    return round(max(0.0, min(100.0, score)), 4)


def _recommended_action(score: float, blockers: list[str], reducers: list[str], reduced_notional: float, proposed: float, config: PortfolioConstructionConfig, commander_override: dict[str, Any]) -> str:
    if blockers and not commander_override:
        if "risk_halt_active" in blockers or "enterprise_risk_factor_halt" in blockers:
            return "reject"
        return "defer"
    if blockers and commander_override:
        return "request_risk_review"
    if reducers and config.approve_reduced_size_enabled and 0 < reduced_notional < proposed:
        return "approve_reduced"
    if score >= config.approve_score_threshold:
        return "approve"
    if score < config.commander_review_threshold:
        return "reject"
    return "request_commander_review"


def _reduced_notional(proposed: float, equity: float, config: PortfolioConstructionConfig, cash: float, reserve: float, current_symbol: float, current_sector: float) -> float:
    caps = (
        max(0.0, equity * config.max_single_position_percent - current_symbol),
        max(0.0, equity * config.max_sector_percent - current_sector),
        max(0.0, cash - reserve),
        proposed,
    )
    return round(max(0.0, min(caps)), 4)


def _next_engine(action: str) -> str:
    if action in {"approve", "approve_reduced"}:
        return "Risk Review"
    if action == "request_risk_review":
        return "Risk Office"
    if action == "request_commander_review":
        return "Commander Review"
    return "Analyst Revision"


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
    payload = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _config_key(name: str) -> str:
    normalized = "".join(character if character.isalnum() else "_" for character in name.strip().lower())
    return normalized


def _coerce_config_value(value: Any, default: Any) -> Any:
    if isinstance(default, bool):
        return str(value).lower() in {"1", "true", "yes", "enabled"}
    if isinstance(default, int):
        return int(_number(value))
    if isinstance(default, float):
        raw = _number(value)
        return raw / 100 if raw > 1.0 and "percent" in str(default) else raw
    return value
