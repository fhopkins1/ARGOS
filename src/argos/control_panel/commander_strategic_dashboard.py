"""Commander Strategic Dashboard aggregation service for ARGOS EO-BI."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
URGENCY_RANK = {"NOW": 4, "IMMEDIATE": 4, "SOON": 3, "TODAY": 2, "WATCH": 1, "ROUTINE": 0}


@dataclass(frozen=True)
class CommanderStrategicDashboardConfig:
    """Display and safety defaults for the Commander Strategic Dashboard."""

    enabled: bool = True
    refresh_policy: str = "state_poll_observation_only"
    stale_data_threshold_seconds: int = 900
    stress_result_freshness_seconds: int = 3600
    monte_carlo_result_freshness_seconds: int = 3600
    reality_fidelity_warning_threshold: float = 80.0
    reality_fidelity_unsafe_threshold: float = 60.0
    critical_risk_threshold: float = 80.0
    intelligence_cost_warning_threshold_usd: float = 25.0
    attention_queue_max_items: int = 12
    engineering_mode_enabled: bool = True
    default_landing_dashboard: str = "commander_strategic_dashboard"


class CommanderStrategicDashboard:
    """Deterministic no-trade aggregation for the Commander strategic view."""

    def __init__(self, config: CommanderStrategicDashboardConfig | None = None) -> None:
        self._config = config or CommanderStrategicDashboardConfig()

    def snapshot(self, *, timestamp_utc: str, **sources: dict[str, Any]) -> dict[str, Any]:
        """Build a coherent Commander dashboard payload from authoritative source snapshots."""
        config = self._resolved_config(sources.get("enterprise_configuration_registry") or {})
        sections = {
            "command_state": self._command_state(timestamp_utc, sources),
            "capital_state": self._capital_state(timestamp_utc, sources),
            "readiness": self._readiness(timestamp_utc, sources),
            "reality_fidelity": self._reality_fidelity(timestamp_utc, sources),
            "strategic_risk": self._strategic_risk(timestamp_utc, sources),
            "correlation": self._correlation(timestamp_utc, sources),
            "active_portfolio": self._active_portfolio(timestamp_utc, sources),
            "performance": self._performance(timestamp_utc, sources),
            "attribution": self._attribution(timestamp_utc, sources),
            "stress_and_survival": self._stress_and_survival(timestamp_utc, sources),
            "capital_allocation": self._capital_allocation(timestamp_utc, sources),
            "learning_and_research": self._learning_and_research(timestamp_utc, sources),
            "intelligence_efficiency": self._intelligence_efficiency(timestamp_utc, sources),
        }
        attention = self._attention_queue(timestamp_utc, sections, sources, config)
        recommendation = self._strategic_recommendation(sections, attention)
        return {
            "dashboardName": "Commander Strategic Dashboard",
            "engineeringOrder": "EO-BI",
            "constitutionalMode": "STRATEGIC_OBSERVATION_ONLY",
            **sections,
            "attention_queue": attention[: config.attention_queue_max_items],
            "strategic_recommendation": recommendation,
            "data_freshness": self._data_freshness(timestamp_utc, sections),
            "navigation": self._navigation(),
            "commander_actions": self._commander_actions(),
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "placesTrades": False, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicAggregation": True},
            "internalDiagnostics": {
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "mutatesTruthRecords": False,
                "placesTrades": False,
                "apiCreditsConsumed": 0.0,
                "engineeringDetailsHiddenByDefault": True,
                "sourceCount": len(sources),
                "timestampUtc": timestamp_utc,
            },
        }

    def _command_state(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        control = sources.get("control") or {}
        workflow = sources.get("workflow_runtime_monitor") or {}
        active = workflow.get("activeWorkflow") or {}
        market = sources.get("market_data_provider") or {}
        return self._section(timestamp, {
            "enterpriseOperatingMode": sources.get("environment", "development"),
            "tradingMode": "LIVE" if control.get("real_world_trading_active") else "PAPER" if control.get("paper_trading_active") else "DORMANT",
            "tradingStatus": "HALTED" if control.get("user_funds_halted") else "ACTIVE" if control.get("paper_trading_active") else "STANDBY",
            "activeWorkflow": active.get("workflowIdentifier", "none"),
            "activeOffice": active.get("currentOwner") or active.get("currentStage") or "none",
            "workflowTokenState": active.get("tokenState") or workflow.get("commanderStatusLine", "standby"),
            "lawVIIStatus": "COMPLIANT",
            "lawVIIIStatus": "COMPLIANT",
            "currentTime": timestamp,
            "marketSession": (market.get("marketSession") or market.get("commanderVisibility", {}).get("marketSession") or "unknown"),
            "latestDashboardDataTimestamp": timestamp,
            "systemWideAlertSeverity": _system_alert(sources),
        }, source_record_timestamp=timestamp)

    def _capital_state(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        truth = sources.get("performance_truth") or {}
        calculations = truth.get("calculations", {}).get("portfolio", {})
        ledger = _latest(truth.get("portfolioLedger", ()))
        equity = _number(ledger.get("total_equity", calculations.get("portfolioValue", None)))
        cash = _number(ledger.get("cash", calculations.get("cash", None)))
        buying_power = _number(ledger.get("buying_power", truth.get("paperAccount", {}).get("buyingPower", cash)))
        positions = tuple(truth.get("positionLedger", ())) or tuple(truth.get("positionRegistry", {}).get("activePositions", ()))
        deployed = round(sum(_number(item.get("current_value", item.get("market_value", 0.0))) for item in positions), 4)
        benchmark = sources.get("enterprise_benchmark_engine") or {}
        benchmark_return = _number((benchmark.get("portfolioLevelComparisons") or [{}])[-1].get("benchmarkReturn", ledger.get("benchmark_return", 0.0))) if benchmark.get("portfolioLevelComparisons") else _number(ledger.get("benchmark_return", 0.0))
        heartbeat = tuple({
            "timestamp": row.get("timestamp", timestamp),
            "portfolioEquity": _number(row.get("total_equity")),
            "cash": _number(row.get("cash")),
            "deployedCapital": deployed,
            "buyingPower": _number(row.get("buying_power", buying_power)),
            "realizedPnl": _number(calculations.get("realizedPnl")),
            "unrealizedPnl": _number(calculations.get("unrealizedPnl")),
        } for row in tuple(truth.get("portfolioLedger", ()))[-16:])
        return self._section(timestamp, {
            "portfolioEquity": equity,
            "cash": cash,
            "buyingPower": buying_power,
            "settledCash": _number(truth.get("paperAccount", {}).get("settledCash", cash)),
            "deployedCapital": deployed,
            "unallocatedCapital": round(max(0.0, cash - deployed), 4),
            "dailyPnl": _number(calculations.get("realizedPnl", ledger.get("daily_pnl", 0.0))),
            "totalPnl": _number(calculations.get("totalPnl", ledger.get("total_pnl", 0.0))),
            "unrealizedPnl": _number(calculations.get("unrealizedPnl")),
            "realizedPnl": _number(calculations.get("realizedPnl")),
            "currentDrawdown": _number(ledger.get("drawdown", calculations.get("maximumDrawdown", 0.0))),
            "returnSinceInception": _number(ledger.get("total_return", calculations.get("totalReturnPercent", 0.0))),
            "benchmarkRelativeReturn": round(_number(ledger.get("alpha", calculations.get("alpha", 0.0))) or (equity and benchmark_return), 4),
            "capitalHeartbeat": heartbeat,
            "unexplainedCapitalMovement": bool((truth.get("executionRealism") or {}).get("portfolioMutationWarnings", 0)),
        }, source_record_timestamp=str(ledger.get("timestamp", timestamp) or timestamp), stale=not bool(ledger), degraded=not bool(truth))

    def _readiness(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        health = sources.get("enterprise_health_monitor") or {}
        reality = sources.get("enterprise_reality_calibration") or {}
        surveillance = sources.get("position_surveillance") or {}
        execution = sources.get("trader_command_bridge", {}).get("executionRealismHealth", {})
        state = "ready"
        if _system_alert(sources) == "CRITICAL":
            state = "unsafe"
        elif _system_alert(sources) in {"HIGH", "MEDIUM"}:
            state = "degraded"
        return self._section(timestamp, {
            "overallEnterpriseHealth": health.get("commanderHealthDashboard", {}).get("overallStatus") or health.get("runtimeHealth", {}).get("status", "unknown"),
            "workflowHealth": health.get("workflowHealth", {}).get("status", "unknown"),
            "marketDataHealth": health.get("marketDataHealth", {}).get("status", "unknown"),
            "executionHealth": execution.get("status", "unknown"),
            "positionSurveillanceHealth": "ready" if surveillance.get("metrics", {}).get("activePositionsSurveilled", 0) >= 0 else "unknown",
            "constitutionalHealth": "COMPLIANT",
            "realityFidelity": reality.get("commanderSummary", {}).get("learningReliabilityState", "unknown"),
            "learningReliability": reality.get("learningReliabilityGate", {}).get("state", "unknown"),
            "reproducibilityStatus": sources.get("enterprise_reproducibility_framework", {}).get("commanderReviewFeed", {}).get("reproducibilitySummary", "unknown"),
            "tradingReadiness": state,
            "readinessState": state,
        }, source_record_timestamp=timestamp, degraded=state != "ready")

    def _reality_fidelity(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        reality = sources.get("enterprise_reality_calibration") or {}
        summary = reality.get("commanderSummary") or {}
        report = reality.get("latestCalibrationReport") or {}
        score = _number(summary.get("overallRealityFidelityScore"))
        return self._section(timestamp, {
            "overallRealityFidelityScore": score,
            "learningReliabilityState": summary.get("learningReliabilityState", "unknown"),
            "executionFidelityScore": _number(report.get("execution_fidelity_score")),
            "valuationFidelityScore": _number(report.get("valuation_fidelity_score")),
            "truthReliabilityScore": _number(report.get("truth_reliability_score")),
            "latestCalibrationTimestamp": summary.get("latestCalibrationTimestamp", ""),
            "activeDriftWarnings": tuple(item.get("drift_type", "drift") for item in report.get("detected_drift_events", ())),
            "unsafeLearningWarning": reality.get("learningReliabilityGate", {}).get("warning", ""),
        }, source_record_timestamp=str(report.get("timestamp", timestamp) or timestamp), stale=not bool(report), degraded=score < 80.0)

    def _strategic_risk(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        risk = sources.get("enterprise_risk_factor") or {}
        summary = risk.get("commanderSummary") or {}
        record = risk.get("latestRiskFactorRecord") or {}
        return self._section(timestamp, {
            "compositeEnterpriseRiskScore": _number(summary.get("compositeRiskScore")),
            "riskLevel": summary.get("riskLevel", "unknown"),
            "topRiskFactors": tuple(summary.get("topRiskFactors", ())),
            "concentrationRisk": _number(record.get("concentration_risk_score")),
            "liquidityRisk": _number(record.get("liquidity_risk_score")),
            "volatilityRisk": _number(record.get("volatility_risk_score")),
            "correlationRisk": _number(record.get("correlation_risk_score")),
            "drawdownRisk": _number(record.get("drawdown_risk_score")),
            "executionRisk": _number(record.get("execution_risk_score")),
            "realityFidelityRisk": _number(record.get("reality_fidelity_risk_score")),
            "recommendedRiskAction": "; ".join(summary.get("recommendedRiskActions", ())),
            "tradingHaltRecommendation": bool(risk.get("riskOfficeFeed", {}).get("haltRecommended")),
        }, source_record_timestamp=str(record.get("timestamp", timestamp) or timestamp), stale=not bool(record), degraded=bool(record.get("degraded_inputs")))

    def _correlation(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        corr = sources.get("correlation_intelligence") or {}
        summary = corr.get("commanderSummary") or {}
        record = corr.get("latestCorrelationIntelligenceRecord") or {}
        overlaps = tuple(corr.get("riskFactorFeed", {}).get("overlapGroups", ()))
        return self._section(timestamp, {
            "hiddenConcentrationScore": _number(summary.get("hiddenConcentrationScore")),
            "diversificationQualityScore": _number(summary.get("diversificationQualityScore")),
            "correlationRiskScore": _number(summary.get("correlationRiskScore")),
            "largestCorrelatedCluster": _largest_named(overlaps),
            "largestSectorOverlap": _largest_named(record.get("sector_overlap_groups", ())),
            "largestStrategyOrThesisOverlap": _largest_named(tuple(record.get("strategy_overlap_groups", ())) + tuple(record.get("thesis_overlap_groups", ()))),
            "highCorrelationPairCount": len(record.get("high_correlation_pairs", ())),
        }, source_record_timestamp=str(record.get("timestamp", timestamp) or timestamp), stale=not bool(record), degraded=bool(record.get("degraded_inputs")))

    def _active_portfolio(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        trader = sources.get("trader_command_bridge") or {}
        summary = trader.get("summary") or {}
        positions = tuple(trader.get("activePositions", ()))
        return self._section(timestamp, {
            "activePositions": summary.get("totalOpenPositions", summary.get("total_open_positions", len(positions))),
            "totalMarketValue": _number(summary.get("totalMarketValue", summary.get("total_market_value"))),
            "positionsRequiringAttention": _number(summary.get("positionsRequiringAttention", summary.get("positions_requiring_attention"))),
            "positionsNearStop": sum(1 for item in positions if str(item.get("latestSurveillanceStatus", "")).lower() == "stop_approaching"),
            "positionsNearTarget": sum(1 for item in positions if str(item.get("latestSurveillanceStatus", "")).lower() == "target_approaching"),
            "positionsWithDegradedSurveillance": sum(1 for item in positions if "DEGRADED" in str(item.get("latestSurveillanceStatus", "")).upper()),
            "positionsWithExitRecommendations": _number(summary.get("exitsRecommended", summary.get("exits_recommended"))),
            "pendingExitOrders": _number(summary.get("pendingOrders", summary.get("pending_orders"))),
            "largestPosition": _largest_position(positions),
            "largestLossContributor": _largest_position(positions, key="unrealizedPnl", reverse=False),
            "largestGainContributor": _largest_position(positions, key="unrealizedPnl", reverse=True),
            "route": "trader_bridge",
        }, source_record_timestamp=timestamp, stale=False, degraded=summary.get("surveillanceHealth", summary.get("surveillance_health")) == "DEGRADED")

    def _performance(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        truth = sources.get("performance_truth") or {}
        closed = sources.get("closed_position_truth") or {}
        benchmark = sources.get("enterprise_benchmark_engine") or {}
        records = tuple(closed.get("closedPositionTruthRecords", ()))
        calculations = truth.get("calculations", {}).get("portfolio", {})
        return self._section(timestamp, {
            "realizedPerformance": _number(calculations.get("realizedPnl")),
            "unrealizedPerformance": _number(calculations.get("unrealizedPnl")),
            "simulatedReplayPerformance": sources.get("market_replay_engine", {}).get("commanderSummary", {}).get("latestReplayReturn", "standby"),
            "enterpriseReturn": _number(calculations.get("totalReturnPercent")),
            "benchmarkReturn": _benchmark_return(benchmark),
            "alpha": _number(calculations.get("alpha")),
            "cashBaseline": benchmark.get("noTradeBaseline", {}).get("cashBaselineReturn", 0.0),
            "noTradeBaseline": benchmark.get("noTradeBaseline", {}),
            "randomBaseline": benchmark.get("randomBaselineControls", {}),
            "winRate": _win_rate(records),
            "averageClosedTradeReturn": _average(tuple(_number(item.get("realized_pnl_percent")) for item in records)),
            "profitFactor": _profit_factor(records),
            "maxDrawdown": _number(calculations.get("maximumDrawdown")),
            "recentCompletedTrades": len(records[-5:]),
            "tradeCount": len(records),
            "sampleSizeConfidence": "low" if len(records) < 30 else "medium" if len(records) < 100 else "high",
        }, source_record_timestamp=str(_latest(records).get("created_at", timestamp) or timestamp), stale=not bool(records), degraded=False)

    def _attribution(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        attribution = sources.get("trade_attribution_engine") or {}
        analysis = attribution.get("contributionAnalysis", {})
        return self._section(timestamp, {
            "strategyContribution": analysis.get("Strategy", {}).get("averageContributionScore", 0),
            "marketContribution": analysis.get("Market", {}).get("averageContributionScore", 0),
            "executionContribution": analysis.get("Execution", {}).get("averageContributionScore", 0),
            "riskContribution": analysis.get("Risk", {}).get("averageContributionScore", 0),
            "positionManagementContribution": analysis.get("Position Management", {}).get("averageContributionScore", 0),
            "promptContribution": analysis.get("Prompt", {}).get("averageContributionScore", 0),
            "unexplainedContribution": analysis.get("Unexplained", {}).get("averageContributionScore", 0),
            "attributionConfidence": attribution.get("confidenceAnalysis", {}).get("overallConfidence", "low"),
        }, source_record_timestamp=timestamp, stale=not bool(attribution.get("attributionRepository")), degraded=False)

    def _stress_and_survival(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        stress = sources.get("stress_testing") or {}
        black = sources.get("black_swan_simulation") or {}
        monte = sources.get("monte_carlo_portfolio") or {}
        stress_summary = stress.get("commanderSummary") or {}
        black_summary = black.get("commanderSummary") or {}
        monte_summary = monte.get("commanderSummary") or {}
        return self._section(timestamp, {
            "latestStressLevel": stress_summary.get("latestStressLevel", "standby"),
            "stressedDrawdown": _number(stress_summary.get("stressedDrawdownPercent")),
            "stopCascadeRisk": stress.get("enterpriseHealthMetrics", {}).get("stopCascadeRisk", False),
            "blackSwanSurvivalScore": _number(black_summary.get("survivalScore")),
            "ruinRiskScore": _number(black_summary.get("ruinRiskScore")),
            "monteCarloProbabilityOfLoss": _number(monte_summary.get("probabilityOfLoss")),
            "monteCarloProbabilityOfRuin": _number(monte_summary.get("probabilityOfRuin")),
            "monteCarloDrawdownBreachProbability": _number((monte.get("latestMonteCarloResultRecord") or {}).get("probability_of_drawdown_threshold_breach")),
            "modelConfidence": _number(monte.get("enterpriseHealthMetrics", {}).get("latestModelConfidence")),
            "latestStressTimestamp": (stress.get("latestStressTestRecord") or {}).get("timestamp", ""),
            "latestBlackSwanTimestamp": (black.get("latestBlackSwanSimulationRecord") or {}).get("timestamp", ""),
            "latestMonteCarloTimestamp": (monte.get("latestMonteCarloResultRecord") or {}).get("completed_at", ""),
        }, source_record_timestamp=timestamp, stale=not any((stress.get("latestStressTestRecord"), black.get("latestBlackSwanSimulationRecord"), monte.get("latestMonteCarloResultRecord"))), degraded=False)

    def _capital_allocation(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        allocation = sources.get("capital_allocation") or {}
        construction = sources.get("portfolio_construction") or {}
        latest = allocation.get("latestCapitalAllocationRecord") or {}
        return self._section(timestamp, {
            "deployableCapital": _number(latest.get("deployable_capital", allocation.get("commanderSummary", {}).get("deployableCapital"))),
            "requiredCashReserve": _number(latest.get("required_cash_reserve", allocation.get("commanderSummary", {}).get("requiredCashReserve"))),
            "currentStrategyAllocations": tuple(latest.get("strategy_budgets", ())),
            "currentAssetTypeAllocations": tuple(latest.get("asset_type_budgets", ())),
            "currentRiskBucketAllocations": tuple(latest.get("risk_bucket_budgets", ())),
            "constrainedOrBlockedCategories": tuple(latest.get("constraints", ())),
            "remainingCapitalBudget": _number(latest.get("remaining_capital_budget", latest.get("deployable_capital", 0.0))),
            "allocationWarnings": allocation.get("commanderSummary", {}).get("warnings", ()),
            "defensiveAggressivePosture": "defensive" if _number(construction.get("commanderSummary", {}).get("constructionScore")) < 55 else "balanced",
        }, source_record_timestamp=str(latest.get("timestamp", timestamp) or timestamp), stale=not bool(latest), degraded=bool(latest.get("degraded_inputs")))

    def _learning_and_research(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        learning = sources.get("enterprise_learning_engine") or {}
        historian = sources.get("historian_recommendation_engine") or {}
        scheduler = sources.get("enterprise_experiment_scheduler") or {}
        prompt = sources.get("prompt_evolution_engine") or {}
        strategy = sources.get("strategy_package_manager") or {}
        return self._section(timestamp, {
            "completedTradeObservations": sources.get("closed_position_truth", {}).get("metrics", {}).get("truthRecordCount", 0),
            "newHistorianLessons": len(historian.get("recommendationDatabase", ())),
            "learningCandidates": len(learning.get("recommendations", ())),
            "promotedKnowledge": len(learning.get("promotedKnowledge", ())),
            "blockedOrDegradedLearning": learning.get("metrics", {}).get("blockedObservations", 0),
            "activeExperiments": scheduler.get("researchDashboard", {}).get("activeExperiments", 0),
            "queuedExperiments": len(scheduler.get("experimentQueue", ())),
            "completedExperiments": len(scheduler.get("experimentHistory", ())),
            "experimentKnowledgeYield": scheduler.get("knowledgeYieldMetrics", {}).get("expectedKnowledgeYield", scheduler.get("researchDashboard", {}).get("expectedKnowledgeGain", 0)),
            "strategyCandidatesAwaitingReview": len(strategy.get("promotionQueue", ())),
            "promptCandidatesAwaitingReview": len(prompt.get("promptImprovementCandidates", ())),
        }, source_record_timestamp=timestamp, stale=False, degraded=False)

    def _intelligence_efficiency(self, timestamp: str, sources: dict[str, Any]) -> dict[str, Any]:
        costs = sources.get("costs") or {}
        credit = sources.get("credit_governor") or {}
        api = sources.get("api_runtime_monitor") or {}
        spend = credit.get("spendReport", {})
        return self._section(timestamp, {
            "currentCreditExpenditureRate": _number(spend.get("burnRatePerHourUsd", 0.0)),
            "creditsUsedToday": _number(costs.get("today_api_credits_usd")),
            "intelligencePerCredit": api.get("metrics", {}).get("intelligencePerCredit", "deterministic-first"),
            "deterministicResolutionRate": api.get("metrics", {}).get("deterministicResolutionRate", 1.0),
            "cacheUtilization": api.get("metrics", {}).get("cacheUtilization", 0.0),
            "llmInvocationCount": api.get("metrics", {}).get("apiCallsLogged", 0),
            "aiJustificationFailures": len(tuple(credit.get("detections", ()))),
            "throttlingState": credit.get("mode", "dry_run"),
            "projectedDailyCreditCost": _number(spend.get("projectedDailySpendUsd", costs.get("today_api_credits_usd", 0.0))),
        }, source_record_timestamp=timestamp, degraded=_number(costs.get("today_api_credits_usd")) > self._config.intelligence_cost_warning_threshold_usd)

    def _attention_queue(self, timestamp: str, sections: dict[str, Any], sources: dict[str, Any], config: CommanderStrategicDashboardConfig) -> tuple[dict[str, Any], ...]:
        items: list[dict[str, Any]] = []
        def add(severity: str, urgency: str, source: str, reason: str, evidence: str, action: str, route: str) -> None:
            items.append({"severity": severity, "urgency": urgency, "sourceEngine": source, "reason": reason, "evidenceSummary": evidence, "recommendedAction": action, "timestamp": timestamp, "linkToDetailedWorkspace": route, "acknowledgementState": "UNACKNOWLEDGED"})
        risk = sections["strategic_risk"]["data"]
        reality = sections["reality_fidelity"]["data"]
        stress = sections["stress_and_survival"]["data"]
        intelligence = sections["intelligence_efficiency"]["data"]
        if risk["tradingHaltRecommendation"] or _number(risk["compositeEnterpriseRiskScore"]) >= config.critical_risk_threshold:
            add("CRITICAL", "NOW", "Enterprise Risk Factor Engine", "Critical enterprise risk state", f"Risk score {risk['compositeEnterpriseRiskScore']} / {risk['riskLevel']}", "halt_trading", "risk_bridge")
        if _number(reality["overallRealityFidelityScore"]) < config.reality_fidelity_unsafe_threshold:
            add("CRITICAL", "NOW", "Enterprise Reality Calibration Engine", "Unsafe reality fidelity", f"Fidelity score {reality['overallRealityFidelityScore']}", "require_reality_calibration", "reality_calibration")
        elif _number(reality["overallRealityFidelityScore"]) < config.reality_fidelity_warning_threshold:
            add("HIGH", "TODAY", "Enterprise Reality Calibration Engine", "Reality fidelity degraded", f"Fidelity score {reality['overallRealityFidelityScore']}", "require_reality_calibration", "reality_calibration")
        if sections["active_portfolio"]["data"]["positionsWithExitRecommendations"]:
            add("HIGH", "SOON", "Trader Command Bridge", "Exit recommendation pending", f"{sections['active_portfolio']['data']['positionsWithExitRecommendations']} positions flagged", "manage_existing_positions_only", "trader_bridge")
        if sections["correlation"]["data"]["highCorrelationPairCount"]:
            add("MEDIUM", "WATCH", "Correlation Intelligence Engine", "Hidden concentration possible", f"{sections['correlation']['data']['highCorrelationPairCount']} high-correlation pairs", "require_risk_reduction", "risk_bridge")
        if stress["latestStressLevel"] in {"high", "critical"} or _number(stress["ruinRiskScore"]) >= 65:
            add("HIGH", "TODAY", "Stress and Survival Engines", "Survival analysis elevated", f"Stress {stress['latestStressLevel']} / ruin {stress['ruinRiskScore']}", "request_stress_test", "engineering_mode")
        if _number(intelligence["creditsUsedToday"]) > config.intelligence_cost_warning_threshold_usd:
            add("MEDIUM", "TODAY", "Enterprise Credit Governor", "Credit usage exceeds warning threshold", f"Today {intelligence['creditsUsedToday']}", "require_experiment_review", "engineering_mode")
        if not items:
            add("INFO", "ROUTINE", "Commander Strategic Dashboard", "No urgent Commander action", "Strategic posture has no critical dashboard alerts.", "continue_normal_operations", "command_bridge")
        return tuple(sorted(items, key=lambda item: (-SEVERITY_RANK.get(item["severity"], 0), -URGENCY_RANK.get(item["urgency"], 0), item["timestamp"])))

    def _strategic_recommendation(self, sections: dict[str, Any], attention: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        reasons = tuple(item["reason"] for item in attention if item["severity"] in {"CRITICAL", "HIGH"})
        risk = _number(sections["strategic_risk"]["data"]["compositeEnterpriseRiskScore"])
        fidelity = _number(sections["reality_fidelity"]["data"]["overallRealityFidelityScore"])
        if any(item["recommendedAction"] == "halt_trading" for item in attention):
            code = "halt_trading"
        elif fidelity < 60:
            code = "require_reality_calibration"
        elif risk >= 80:
            code = "require_risk_reduction"
        elif sections["active_portfolio"]["data"]["positionsWithExitRecommendations"]:
            code = "manage_existing_positions_only"
        elif fidelity < 80 or risk >= 60:
            code = "continue_with_reduced_risk"
        else:
            code = "continue_normal_operations"
        return {"recommendation": code, "deterministic": True, "reasoning": reasons or ("No critical deterministic alerts.",), "aiUsed": False}

    def _data_freshness(self, timestamp: str, sections: dict[str, Any]) -> dict[str, Any]:
        return {key: {name: value for name, value in section.items() if name in {"generated_at", "source_record_timestamp", "stale", "degraded"}} for key, section in sections.items()}

    def _section(self, timestamp: str, data: dict[str, Any], *, source_record_timestamp: str = "", stale: bool = False, degraded: bool = False) -> dict[str, Any]:
        return {"generated_at": timestamp, "source_record_timestamp": source_record_timestamp or timestamp, "stale": bool(stale), "degraded": bool(degraded), "data": data}

    def _navigation(self) -> tuple[dict[str, str], ...]:
        return (
            {"label": "Trader Command Bridge", "route": "trader_bridge"},
            {"label": "Risk Bridge", "route": "risk_bridge"},
            {"label": "Analyst Bridge", "route": "analyst_bridge_placeholder"},
            {"label": "Historian Bridge", "route": "historian_bridge"},
            {"label": "Academy Bridge", "route": "academy_bridge"},
            {"label": "Strategic Intelligence Bridge", "route": "strategic_intelligence_bridge"},
            {"label": "Commander Daily Review Workspace", "route": "command_bridge"},
            {"label": "Decision Laboratory", "route": "engineering_mode"},
            {"label": "Experiment Scheduler", "route": "engineering_mode"},
            {"label": "Engineering Mode", "route": "engineering_mode"},
            {"label": "Enterprise Health Details", "route": "engineering_mode"},
            {"label": "Reality Calibration Details", "route": "engineering_mode"},
        )

    def _commander_actions(self) -> dict[str, Any]:
        return {
            "supportedViaAuthorizedServices": ("acknowledge_alert", "request_review", "pause_new_entries", "halt_trading", "request_reality_calibration", "request_stress_test", "request_monte_carlo_run"),
            "directPositionMutation": False,
            "directLedgerMutation": False,
            "directTruthMutation": False,
            "authorizationPath": "Command Console / bridge authorized runtime actions",
        }

    def _resolved_config(self, registry: dict[str, Any]) -> CommanderStrategicDashboardConfig:
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        dashboard = configs.get("commanderStrategicDashboard", {}) if isinstance(configs, dict) else {}
        if not isinstance(dashboard, dict):
            return self._config
        values = asdict(self._config)
        for key, value in dashboard.items():
            if key in values:
                values[key] = value
        return CommanderStrategicDashboardConfig(**values)


def _latest(rows: Any) -> dict[str, Any]:
    rows = tuple(rows or ())
    return dict(rows[-1]) if rows else {}


def _number(value: Any) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return round(float(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _average(values: tuple[float, ...]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _win_rate(records: tuple[dict[str, Any], ...]) -> float:
    return round(sum(1 for item in records if _number(item.get("net_realized_pnl")) > 0) / len(records) * 100, 4) if records else 0.0


def _profit_factor(records: tuple[dict[str, Any], ...]) -> float:
    gains = sum(max(0.0, _number(item.get("net_realized_pnl"))) for item in records)
    losses = abs(sum(min(0.0, _number(item.get("net_realized_pnl"))) for item in records))
    return round(gains / losses, 4) if losses else round(gains, 4)


def _benchmark_return(benchmark: dict[str, Any]) -> float:
    rows = tuple(benchmark.get("portfolioLevelComparisons", ()))
    return _number((rows[-1] if rows else {}).get("benchmarkReturn", 0.0))


def _largest_named(rows: Any) -> str:
    rows = tuple(rows or ())
    if not rows:
        return ""
    row = max((dict(item) for item in rows), key=lambda item: _number(item.get("weight", item.get("score", item.get("exposure", 0.0)))))
    return str(row.get("name") or row.get("cluster") or row.get("sector") or row.get("strategy") or row.get("thesis") or row.get("symbols") or "")


def _largest_position(positions: tuple[dict[str, Any], ...], *, key: str = "currentValue", reverse: bool = True) -> dict[str, Any]:
    if not positions:
        return {}
    aliases = {"currentValue": ("currentValue", "current_value", "marketValue"), "unrealizedPnl": ("unrealizedPnl", "unrealized_pnl")}
    keys = aliases.get(key, (key,))
    def value(item: dict[str, Any]) -> float:
        return next((_number(item.get(name)) for name in keys if name in item), 0.0)
    return dict(sorted(positions, key=value, reverse=reverse)[0])


def _system_alert(sources: dict[str, Any]) -> str:
    risk = _number((sources.get("enterprise_risk_factor") or {}).get("commanderSummary", {}).get("compositeRiskScore"))
    reality = _number((sources.get("enterprise_reality_calibration") or {}).get("commanderSummary", {}).get("overallRealityFidelityScore", 100.0))
    if risk >= 85 or reality < 60:
        return "CRITICAL"
    if risk >= 70 or reality < 80:
        return "HIGH"
    if risk >= 50:
        return "MEDIUM"
    return "LOW"
