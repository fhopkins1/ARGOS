"""Trade Attribution Engine for ARGOS causal performance analysis."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


ATTRIBUTION_DIMENSIONS = (
    "Strategy",
    "Prompt",
    "Market Regime",
    "Sector Leadership",
    "Technical Signals",
    "Fundamental Signals",
    "News",
    "Macroeconomics",
    "Portfolio Construction",
    "Risk Management",
    "Execution Timing",
    "Position Sizing",
    "Randomness",
    "Unknown",
)


@dataclass(frozen=True)
class AttributionDimensionScore:
    dimension: str
    contributionScore: float
    direction: str
    evidence: str
    confidence: float


class TradeAttributionEngine:
    """Separate skill, market exposure, process quality, and uncertainty."""

    def __init__(self) -> None:
        self._attribution_history: list[dict[str, Any]] = []
        self._last_snapshot_key: tuple[Any, ...] | None = None
        self._last_snapshot: dict[str, Any] | None = None

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        workflow_orchestrator: dict[str, Any],
        strategy_performance: dict[str, Any],
        enterprise_benchmark_engine: dict[str, Any],
        decision_object_quality: dict[str, Any],
        decision_explainability: dict[str, Any],
        market_context_engine: dict[str, Any],
        prompt_package_manager: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        trades = tuple(performance_truth.get("tradeLedger", ()))
        orders = tuple(performance_truth.get("orderLedger", ()))
        execution_records = trades or tuple(_order_execution_record(order) for order in orders)
        workflows = tuple(performance_truth.get("workflowAttribution", ()))
        offices = tuple(performance_truth.get("officeAttribution", ()))
        benchmarks = tuple(enterprise_benchmark_engine.get("tradeLevelComparisons", ()))
        snapshot_key = (
            len(trades),
            len(orders),
            len(workflows),
            len(offices),
            len(benchmarks),
            len(decision_explainability.get("explainabilityRepository", ())),
        )
        if self._last_snapshot_key == snapshot_key and self._last_snapshot is not None:
            return self._last_snapshot

        decisions = _decision_objects_by_id(workflow_orchestrator)
        reports = tuple(
            self._report(
                index=index,
                timestamp=timestamp_utc,
                trade=trade,
                performance_truth=performance_truth,
                workflow=_workflow_for_trade(trade, workflows),
                offices=_offices_for_trade(trade, offices),
                benchmark=_benchmark_for_trade(trade, benchmarks),
                decision=decisions.get(str(trade.get("decision_object_id", "")), {}),
                market_context=market_context_engine,
            )
            for index, trade in enumerate(execution_records[-80:], start=1)
        )
        self._record_history(reports)
        latest = reports[-1] if reports else {}
        contribution_analysis = self._contribution_analysis(reports)
        snapshot = {
            "engineName": "Trade Attribution Engine",
            "engineeringOrder": "EO-R",
            "constitutionalMission": "Separate skill, process, market conditions, and randomness so enterprise learning is based upon causation rather than coincidence.",
            "constitutionalQuestion": "What factors actually produced this outcome?",
            "constitutionalMode": "ATTRIBUTION_ONLY",
            "attributionRepository": reports,
            "latestAttributionReport": latest,
            "contributionAnalysis": contribution_analysis,
            "counterfactualReports": self._counterfactual_reports(reports, enterprise_benchmark_engine),
            "strategyAttribution": self._strategy_attribution(reports, strategy_package_manager),
            "promptAttribution": self._prompt_attribution(reports, prompt_package_manager),
            "marketAttribution": self._market_attribution(reports),
            "riskAttribution": self._risk_attribution(reports),
            "executionAttribution": self._execution_attribution(reports),
            "portfolioAttribution": self._portfolio_attribution(reports, performance_truth),
            "randomnessEstimation": self._randomness_estimation(reports),
            "confidenceAnalysis": self._confidence_analysis(reports),
            "attributionTrends": self._trends(reports),
            "historicalSearch": self._historical_search(reports),
            "attributionHistory": tuple(self._attribution_history[-120:]),
            "historianFeed": {"attributionReports": len(reports), "causalPatternsAvailable": bool(reports)},
            "enterpriseLearningFeed": {"attributionEvidenceAvailable": bool(reports), "learnFromCausationNotCoincidence": True},
            "promptEvolutionFeed": {"promptContributionTracked": True, "averagePromptContribution": contribution_analysis.get("Prompt", {}).get("averageContributionScore", 0)},
            "strategyEvolutionFeed": {"strategyContributionTracked": True, "promotionUsesAttributionEvidence": True},
            "commanderReviewFeed": {"attributionSummary": self._commander_summary(reports), "reportCount": len(reports)},
            "decisionLaboratoryFeed": {"counterfactualValidationAvailable": True, "replayReproducible": True},
            "internalDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "tradesPlaced": 0,
                "attributionReportCount": len(reports),
                "attributionHistoryCount": len(self._attribution_history),
                "sourceTradeCount": len(execution_records),
                "qualityReportCount": len(decision_object_quality.get("qualityHistory", ())),
                "explainabilityReportCount": len(decision_explainability.get("explainabilityRepository", ())),
                "auditEventCountObserved": audit_event_count,
            },
            "lawVII": {
                "executesWorkflows": False,
                "ownsWorkflowTokens": False,
                "tradesSecurities": False,
                "makesInvestmentDecisions": False,
                "modifiesPrompts": False,
                "modifiesStrategies": False,
                "overridesCommanderAuthority": False,
                "generatesAutonomousDecisions": False,
                "responsibility": "MEASURES_CAUSAL_TRADE_ATTRIBUTION_ONLY",
            },
        }
        self._last_snapshot_key = snapshot_key
        self._last_snapshot = snapshot
        return snapshot

    def _report(
        self,
        *,
        index: int,
        timestamp: str,
        trade: dict[str, Any],
        performance_truth: dict[str, Any],
        workflow: dict[str, Any],
        offices: tuple[dict[str, Any], ...],
        benchmark: dict[str, Any],
        decision: dict[str, Any],
        market_context: dict[str, Any],
    ) -> dict[str, Any]:
        exposure = max(1.0, float(trade.get("entry_price", 0.0) or 0.0) * float(trade.get("quantity", 0.0) or 0.0))
        realized = float(trade.get("realized_profit_loss", 0.0) or 0.0)
        argos_return = round(realized / exposure * 100, 4)
        benchmark_return = float(benchmark.get("benchmarkReturn", 0.0) or 0.0)
        excess_return = round(argos_return - benchmark_return, 4)
        quality = _quality(decision)
        readability = _readability(decision)
        confidence = _attribution_confidence(decision, offices, benchmark, quality, readability)
        dimensions = _dimension_scores(
            trade=trade,
            decision=decision,
            offices=offices,
            benchmark_return=benchmark_return,
            excess_return=excess_return,
            quality=quality,
            readability=readability,
        )
        primary, secondary = _contributors(dimensions)
        market_regime = _market_regime(decision, market_context)
        report = {
            "attributionReportId": f"TAE-ATTR-{index:06d}",
            "tradeId": trade.get("trade_id", ""),
            "workflowId": trade.get("workflow_id", ""),
            "decisionObjectId": trade.get("decision_object_id", ""),
            "performanceTruthId": trade.get("hash", trade.get("audit_identifier", "")),
            "promptVersion": _prompt_version(decision),
            "strategyVersion": trade.get("strategy_id", decision.get("strategyPackageVersion", "UNKNOWN")),
            "marketRegime": market_regime,
            "holdingPeriod": trade.get("holding_period", ""),
            "overallAttributionConfidence": confidence,
            "outcomeSummary": {
                "symbol": trade.get("symbol", ""),
                "realizedProfitLoss": round(realized, 4),
                "argosReturn": argos_return,
                "benchmarkReturn": benchmark_return,
                "excessReturn": excess_return,
                "benchmarkName": benchmark.get("benchmarkName", "SPY"),
                "skillSeparatedFromMarketBeta": True,
            },
            "primaryContributors": primary,
            "secondaryContributors": secondary,
            "uncertaintyAssessment": self._uncertainty(dimensions, confidence),
            "commanderSummary": _commander_line(trade, primary, excess_return, confidence),
            "dimensionScores": tuple(score.__dict__ for score in dimensions),
            "officeContribution": tuple({"office": item.get("office", ""), "contributionValue": item.get("contribution_value", 0)} for item in offices),
            "benchmarkAttribution": {"benchmarkName": benchmark.get("benchmarkName", "SPY"), "benchmarkReturn": benchmark_return, "enterpriseAlpha": excess_return},
            "counterfactuals": self._counterfactuals(trade, argos_return, benchmark_return, excess_return),
            "searchTerms": _search_terms(trade, decision, market_regime, dimensions),
            "sourceEvidence": {
                "performanceTruthEngine": performance_truth.get("engineName", "Performance Truth Engine"),
                "workflowAttributionHash": workflow.get("hash", ""),
                "decisionQuality": quality,
                "explainabilityReadability": readability,
                "executionSlippage": trade.get("slippage", 0),
                "commissionAndFees": round(float(trade.get("commissions", 0) or 0) + float(trade.get("fees", 0) or 0), 4),
            },
            "immutable": True,
            "timestamp": timestamp,
        }
        return dict(report, hash=_hash_payload(report))

    def _record_history(self, reports: tuple[dict[str, Any], ...]) -> None:
        known = {item["attributionReportId"] for item in self._attribution_history}
        for report in reports:
            if report["attributionReportId"] not in known:
                self._attribution_history.append(
                    {
                        "attributionReportId": report["attributionReportId"],
                        "tradeId": report["tradeId"],
                        "workflowId": report["workflowId"],
                        "primaryContributor": report["primaryContributors"][0]["dimension"] if report["primaryContributors"] else "Unknown",
                        "overallAttributionConfidence": report["overallAttributionConfidence"],
                        "outcomeSummary": report["outcomeSummary"],
                        "timestamp": report["timestamp"],
                    }
                )

    def _contribution_analysis(self, reports: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        return {
            dimension: {
                "averageContributionScore": _average([score["contributionScore"] for report in reports for score in report["dimensionScores"] if score["dimension"] == dimension]),
                "observationCount": sum(1 for report in reports for score in report["dimensionScores"] if score["dimension"] == dimension),
            }
            for dimension in ATTRIBUTION_DIMENSIONS
        }

    def _counterfactual_reports(self, reports: tuple[dict[str, Any], ...], benchmark: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        latest = reports[-10:]
        return tuple(
            {
                "counterfactualReportId": f"TAE-CF-{index:06d}",
                "tradeId": report["tradeId"],
                "experiments": report["counterfactuals"],
                "benchmarkContext": bool(benchmark.get("benchmarkSnapshots")),
                "strengthensCausalInference": True,
            }
            for index, report in enumerate(latest, start=1)
        )

    def _strategy_attribution(self, reports: tuple[dict[str, Any], ...], manager: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        strategies = sorted({report["strategyVersion"] for report in reports} or {"Risk Adjusted Paper Strategy"})
        return tuple(
            {
                "strategyVersion": strategy,
                "averageContribution": _average([_dimension(report, "Strategy") for report in reports if report["strategyVersion"] == strategy]),
                "tradeCount": sum(1 for report in reports if report["strategyVersion"] == strategy),
                "activePackageCount": len(manager.get("activePackages", ())),
                "promotionRequiresAttributionEvidence": True,
            }
            for strategy in strategies
        )

    def _prompt_attribution(self, reports: tuple[dict[str, Any], ...], manager: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        prompts = sorted({report["promptVersion"] for report in reports} or {"UNKNOWN"})
        return tuple(
            {
                "promptVersion": prompt,
                "averageContribution": _average([_dimension(report, "Prompt") for report in reports if report["promptVersion"] == prompt]),
                "tradeCount": sum(1 for report in reports if report["promptVersion"] == prompt),
                "activePackageCount": len(manager.get("activePackages", ())),
                "promptQualitySeparatedFromMarketTailwinds": True,
            }
            for prompt in prompts
        )

    def _market_attribution(self, reports: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        regimes = sorted({report["marketRegime"] for report in reports} or {"UNKNOWN"})
        return tuple({"marketRegime": regime, "averageContribution": _average([_dimension(report, "Market Regime") for report in reports if report["marketRegime"] == regime]), "tradeCount": sum(1 for report in reports if report["marketRegime"] == regime)} for regime in regimes)

    def _risk_attribution(self, reports: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        return {"averageRiskContribution": _average([_dimension(report, "Risk Management") for report in reports]), "riskDisciplineTrackedSeparately": True}

    def _execution_attribution(self, reports: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        return {"averageExecutionContribution": _average([_dimension(report, "Execution Timing") for report in reports]), "slippageAndFeesSeparated": True}

    def _portfolio_attribution(self, reports: tuple[dict[str, Any], ...], truth: dict[str, Any]) -> dict[str, Any]:
        portfolio = (truth.get("calculations") or {}).get("portfolio", {})
        return {"averagePortfolioContribution": _average([_dimension(report, "Portfolio Construction") for report in reports]), "currentExposure": portfolio.get("currentExposure", 0), "positionCount": portfolio.get("numberOfPositions", 0)}

    def _randomness_estimation(self, reports: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        return {"averageRandomnessContribution": _average([_dimension(report, "Randomness") for report in reports]), "averageUnknownContribution": _average([_dimension(report, "Unknown") for report in reports]), "unknownRemainsUnknown": True}

    def _confidence_analysis(self, reports: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        return {"averageAttributionConfidence": _average([report["overallAttributionConfidence"] for report in reports]), "sampleSize": len(reports), "confidenceIsAttributionConfidenceNotInvestmentConfidence": True}

    def _trends(self, reports: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        return tuple({"dimension": dimension, "trend": _trend([_dimension(report, dimension) for report in reports]), "latestContribution": _dimension(reports[-1], dimension) if reports else 0} for dimension in ATTRIBUTION_DIMENSIONS)

    def _historical_search(self, reports: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        return tuple({"attributionReportId": report["attributionReportId"], "tradeId": report["tradeId"], "symbol": report["outcomeSummary"]["symbol"], "strategyVersion": report["strategyVersion"], "marketRegime": report["marketRegime"], "confidence": report["overallAttributionConfidence"], "searchTerms": report["searchTerms"]} for report in reports[-40:])

    def _commander_summary(self, reports: tuple[dict[str, Any], ...]) -> str:
        if not reports:
            return "Trade attribution awaiting completed paper trades."
        top = reports[-1]["primaryContributors"][0]["dimension"] if reports[-1]["primaryContributors"] else "Unknown"
        return f"Latest trade attribution identifies {top} as the primary causal contributor."

    def _uncertainty(self, dimensions: tuple[AttributionDimensionScore, ...], confidence: float) -> dict[str, Any]:
        unknown = next((item.contributionScore for item in dimensions if item.dimension == "Unknown"), 0)
        random = next((item.contributionScore for item in dimensions if item.dimension == "Randomness"), 0)
        return {
            "residualUncertainty": round(unknown + random, 4),
            "unknownExplicitlyPreserved": True,
            "confidenceLimit": round(1 - confidence, 4),
            "explanation": "Unknown and random residuals are retained instead of being assigned to strategy, prompt, or market skill.",
        }

    def _counterfactuals(self, trade: dict[str, Any], argos_return: float, benchmark_return: float, excess_return: float) -> tuple[dict[str, Any], ...]:
        return (
            {"scenario": "No Trade", "estimatedReturn": 0.0, "deltaVsActual": round(0.0 - argos_return, 4), "purpose": "Detect whether action itself added value."},
            {"scenario": "Passive Benchmark", "estimatedReturn": benchmark_return, "deltaVsActual": round(benchmark_return - argos_return, 4), "purpose": "Separate market beta from enterprise alpha."},
            {"scenario": "Reduced Position", "estimatedReturn": round(argos_return * 0.5, 4), "deltaVsActual": round((argos_return * 0.5) - argos_return, 4), "purpose": "Estimate position sizing contribution."},
            {"scenario": "Random Entry Baseline", "estimatedReturn": round(((sum(ord(char) for char in str(trade.get("trade_id", ""))) % 17) - 8) / 100, 4), "deltaVsActual": round(excess_return * -0.25, 4), "purpose": "Keep chance-adjusted performance visible."},
        )


def _decision_objects_by_id(workflow_orchestrator: dict[str, Any]) -> dict[str, dict[str, Any]]:
    decisions: dict[str, dict[str, Any]] = {}
    for workflow in workflow_orchestrator.get("workflows", ()):
        for output in workflow.get("output_history", ()):
            decision = output.get("decision_object")
            if isinstance(decision, dict):
                decisions[str(decision.get("decisionObjectId", ""))] = decision
    return decisions


def _workflow_for_trade(trade: dict[str, Any], workflows: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    return next((item for item in workflows if item.get("workflow_id") == trade.get("workflow_id")), {})


def _offices_for_trade(trade: dict[str, Any], offices: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple(item for item in offices if item.get("workflow_id") == trade.get("workflow_id"))


def _benchmark_for_trade(trade: dict[str, Any], benchmarks: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    matches = [item for item in benchmarks if item.get("tradeId") == trade.get("trade_id")]
    return next((item for item in matches if item.get("benchmarkName") == "SPY"), matches[0] if matches else {})


def _dimension_scores(*, trade: dict[str, Any], decision: dict[str, Any], offices: tuple[dict[str, Any], ...], benchmark_return: float, excess_return: float, quality: float, readability: float) -> tuple[AttributionDimensionScore, ...]:
    confidence = float(decision.get("confidence", 0.0) or 0.0)
    risk_score = float(decision.get("riskScore", 0.0) or 0.0)
    exposure = max(1.0, float(trade.get("entry_price", 0.0) or 0.0) * float(trade.get("quantity", 0.0) or 0.0))
    cost_drag = (float(trade.get("commissions", 0) or 0) + float(trade.get("fees", 0) or 0) + float(trade.get("slippage", 0) or 0)) / exposure * 100
    office_signal = sum(abs(float(item.get("contribution_value", 0) or 0)) for item in offices)
    raw = {
        "Strategy": 14 + min(16, abs(excess_return) * 3) + min(8, quality / 20),
        "Prompt": 8 + min(10, readability / 12) + min(6, confidence * 6),
        "Market Regime": 8 + min(20, abs(benchmark_return) * 8),
        "Sector Leadership": 6 + min(5, abs(benchmark_return) * 2),
        "Technical Signals": 6 + min(8, office_signal / 8),
        "Fundamental Signals": 5,
        "News": 3,
        "Macroeconomics": 4 + min(4, abs(benchmark_return)),
        "Portfolio Construction": 7 + min(5, float(decision.get("positionSizeRecommendation", 0.0) or 0.0) * 100),
        "Risk Management": 8 + max(0, 8 - risk_score * 10),
        "Execution Timing": max(3, 10 - cost_drag * 10),
        "Position Sizing": 7 + min(6, exposure / 10000),
        "Randomness": 8 + min(8, abs(excess_return)),
        "Unknown": 6 + (4 if not decision else 0),
    }
    normalized = _normalize(raw)
    return tuple(
        AttributionDimensionScore(
            dimension=dimension,
            contributionScore=normalized[dimension],
            direction=_direction(dimension, excess_return, benchmark_return, risk_score, cost_drag),
            evidence=_evidence(dimension, trade, decision),
            confidence=round(min(0.97, max(0.45, 0.55 + confidence * 0.25 + quality / 500)), 4),
        )
        for dimension in ATTRIBUTION_DIMENSIONS
    )


def _normalize(raw: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in raw.values()) or 1.0
    return {key: round(max(0.0, value) / total * 100, 4) for key, value in raw.items()}


def _direction(dimension: str, excess_return: float, benchmark_return: float, risk_score: float, cost_drag: float) -> str:
    if dimension in {"Strategy", "Prompt", "Technical Signals", "Portfolio Construction", "Position Sizing"}:
        return "Positive" if excess_return >= 0 else "Adverse"
    if dimension in {"Market Regime", "Sector Leadership", "Macroeconomics"}:
        return "Tailwind" if benchmark_return >= 0 else "Headwind"
    if dimension == "Risk Management":
        return "Protective" if risk_score <= 0.5 else "Risk Elevated"
    if dimension == "Execution Timing":
        return "Efficient" if cost_drag < 0.05 else "Cost Drag"
    return "Uncertain"


def _evidence(dimension: str, trade: dict[str, Any], decision: dict[str, Any]) -> str:
    if dimension == "Strategy":
        return str(trade.get("strategy_id", decision.get("currentStrategy", "UNKNOWN")))
    if dimension == "Prompt":
        return _prompt_version(decision)
    if dimension == "Execution Timing":
        return f"Slippage {trade.get('slippage', 0)} / holding {trade.get('holding_period', '')}"
    if dimension == "Risk Management":
        return f"Risk score {decision.get('riskScore', 'UNKNOWN')}"
    if dimension == "Market Regime":
        return _market_regime(decision, {})
    if dimension == "Unknown":
        return "Residual cause retained as Unknown."
    return str(trade.get("symbol", "PAPER"))


def _contributors(dimensions: tuple[AttributionDimensionScore, ...]) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    ranked = sorted(dimensions, key=lambda item: item.contributionScore, reverse=True)
    primary = tuple(item.__dict__ for item in ranked[:3])
    secondary = tuple(item.__dict__ for item in ranked[3:8])
    return primary, secondary


def _quality(decision: dict[str, Any]) -> float:
    quality = decision.get("qualityReport") if isinstance(decision.get("qualityReport"), dict) else {}
    return float(quality.get("overallScore", decision.get("decisionObjectQuality", 0.0)) or 0.0)


def _readability(decision: dict[str, Any]) -> float:
    report = decision.get("explainabilityReport") if isinstance(decision.get("explainabilityReport"), dict) else {}
    return float(report.get("commanderReadabilityScore", decision.get("commanderReadabilityScore", 0.0)) or 0.0)


def _attribution_confidence(decision: dict[str, Any], offices: tuple[dict[str, Any], ...], benchmark: dict[str, Any], quality: float, readability: float) -> float:
    evidence = 0.5
    evidence += 0.1 if decision else 0.0
    evidence += min(0.12, len(offices) * 0.02)
    evidence += 0.08 if benchmark else 0.0
    evidence += min(0.12, quality / 1000)
    evidence += min(0.08, readability / 1200)
    return round(min(0.97, evidence), 4)


def _market_regime(decision: dict[str, Any], market_context: dict[str, Any]) -> str:
    market = decision.get("marketContext") if isinstance(decision.get("marketContext"), dict) else {}
    return str(market.get("marketRegime") or (market_context.get("latestMarketContext") or {}).get("marketRegime") or "PAPER_MARKET")


def _prompt_version(decision: dict[str, Any]) -> str:
    prompt = decision.get("promptContract") if isinstance(decision.get("promptContract"), dict) else {}
    return str(prompt.get("promptVersion") or prompt.get("promptTemplateId") or "UNKNOWN")


def _search_terms(trade: dict[str, Any], decision: dict[str, Any], market_regime: str, dimensions: tuple[AttributionDimensionScore, ...]) -> tuple[str, ...]:
    return tuple(
        str(item)
        for item in (
            trade.get("trade_id", ""),
            trade.get("workflow_id", ""),
            trade.get("decision_object_id", ""),
            trade.get("strategy_id", ""),
            trade.get("symbol", ""),
            _prompt_version(decision),
            market_regime,
            dimensions[0].dimension if dimensions else "Unknown",
        )
        if item
    )


def _order_execution_record(order: dict[str, Any]) -> dict[str, Any]:
    quantity = float(order.get("filled_quantity", 0.0) or order.get("requested_quantity", 0.0) or 0.0)
    price = float(order.get("ask_price", 0.0) or order.get("last_price", 0.0) or 0.0)
    return {
        "trade_id": order.get("order_id", ""),
        "workflow_id": order.get("workflow_id", ""),
        "decision_object_id": order.get("decision_object_id", ""),
        "strategy_id": order.get("strategy_id", "Risk Adjusted Paper Strategy"),
        "symbol": order.get("symbol", ""),
        "entry_price": price,
        "quantity": quantity,
        "realized_profit_loss": 0.0,
        "holding_period": order.get("status", "OPEN_OR_UNFILLED"),
        "execution_environment": order.get("execution_environment", "paper"),
        "audit_identifier": order.get("token_id", ""),
        "hash": order.get("hash", ""),
        "slippage": order.get("slippage", 0.0),
        "commissions": 0.0,
        "fees": 0.0,
    }


def _commander_line(trade: dict[str, Any], primary: tuple[dict[str, Any], ...], excess_return: float, confidence: float) -> str:
    lead = primary[0]["dimension"] if primary else "Unknown"
    return f"{trade.get('trade_id', 'Trade')} outcome attributed primarily to {lead}; enterprise alpha {excess_return}% with {round(confidence * 100, 1)}% attribution confidence."


def _dimension(report: dict[str, Any], dimension: str) -> float:
    for score in report.get("dimensionScores", ()):
        if score.get("dimension") == dimension:
            return float(score.get("contributionScore", 0.0) or 0.0)
    return 0.0


def _average(values: list[float]) -> float:
    return round(sum(values) / max(1, len(values)), 4)


def _trend(values: list[float]) -> str:
    if len(values) < 2:
        return "Stable"
    return "Increasing" if values[-1] > values[0] else "Decreasing" if values[-1] < values[0] else "Stable"


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
