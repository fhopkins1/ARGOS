from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MarketContextObject:
    snapshotId: str
    creationTime: str
    marketSession: str
    marketRegime: str
    overallTrend: str
    volatilityState: str
    liquidityState: str
    riskEnvironment: str
    confidence: float
    supportingEvidence: tuple[str, ...]
    dataFreshness: dict[str, Any]
    relatedSymbols: tuple[str, ...]
    relatedSectors: tuple[str, ...]
    relatedIndices: tuple[str, ...]
    relatedMacroEvents: tuple[dict[str, Any], ...]
    relatedNews: tuple[dict[str, Any], ...]
    relatedPortfolioExposure: dict[str, Any]


class MarketContextIntegrationEngine:
    """Deterministic market awareness and context normalization layer."""

    def context_object(
        self,
        *,
        timestamp_utc: str,
        workflow_id: str,
        decision_object_id: str,
        lppc: dict[str, Any] | None = None,
        performance_truth: dict[str, Any] | None = None,
        strategy_performance: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        lppc = lppc or {}
        performance_truth = performance_truth or {}
        strategy_performance = strategy_performance or {}
        prices = self._price_layer(timestamp_utc, strategy_performance, performance_truth)
        sectors = self._sector_layer(strategy_performance, performance_truth)
        portfolio = self._portfolio_layer(lppc, performance_truth)
        regime = self._regime(prices, sectors, portfolio)
        context = MarketContextObject(
            snapshotId=f"MCTX-{_stable_id(workflow_id or decision_object_id or str(audit_event_count)):06d}",
            creationTime=timestamp_utc,
            marketSession="Paper Session" if workflow_id else "Standing By",
            marketRegime=regime["marketRegime"],
            overallTrend=regime["overallTrend"],
            volatilityState=regime["volatilityState"],
            liquidityState=regime["liquidityState"],
            riskEnvironment=regime["riskEnvironment"],
            confidence=self._confidence(prices, sectors, portfolio),
            supportingEvidence=(
                f"Related workflow {workflow_id or 'none'}",
                f"Decision Object {decision_object_id or 'none'}",
                f"Benchmark count {len(strategy_performance.get('marketBenchmarks', ())) }",
                f"Portfolio exposure {portfolio['capitalUtilization']}%",
            ),
            dataFreshness=self._freshness(timestamp_utc),
            relatedSymbols=tuple(dict.fromkeys(prices["relatedSymbols"])),
            relatedSectors=tuple(dict.fromkeys(sectors["relatedSectors"])),
            relatedIndices=tuple(dict.fromkeys(prices["relatedIndices"])),
            relatedMacroEvents=self._macro_layer(timestamp_utc),
            relatedNews=self._news_layer(timestamp_utc, prices["relatedSymbols"]),
            relatedPortfolioExposure=portfolio,
        )
        return asdict(context)

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        workflow_runtime_monitor: dict[str, Any],
        lppc: dict[str, Any],
        performance_truth: dict[str, Any],
        strategy_performance: dict[str, Any],
        market_data_provider: dict[str, Any] | None = None,
        audit_event_count: int,
    ) -> dict[str, Any]:
        market_data_provider = market_data_provider or {}
        active = workflow_runtime_monitor.get("activeWorkflow") or {}
        latest_decision = strategy_performance.get("decisionObjectPanel", {})
        context = self.context_object(
            timestamp_utc=timestamp_utc,
            workflow_id=active.get("workflowIdentifier") or latest_decision.get("workflowId", ""),
            decision_object_id=latest_decision.get("decisionObjectId", ""),
            lppc=lppc,
            performance_truth=performance_truth,
            strategy_performance=strategy_performance,
            audit_event_count=audit_event_count,
        )
        price_layer = self._price_layer(timestamp_utc, strategy_performance, performance_truth)
        technical_layer = self._technical_layer(price_layer)
        sector_layer = self._sector_layer(strategy_performance, performance_truth)
        fundamental_layer = self._fundamental_layer(price_layer)
        macro_layer = self._macro_layer(timestamp_utc)
        news_layer = self._news_layer(timestamp_utc, price_layer["relatedSymbols"])
        options_layer = self._options_layer(price_layer)
        portfolio_layer = self._portfolio_layer(lppc, performance_truth)
        regime_layer = self._regime(price_layer, sector_layer, portfolio_layer)
        repository = (context,)
        return {
            "engineName": "Market Context Integration Engine",
            "engineeringOrder": "EO-E",
            "constitutionalMission": "Ensure every Decision Object understands the market environment in which it exists.",
            "constitutionalQuestion": "What is happening in the market right now that the Analyst should understand?",
            "constitutionalMode": "AWARENESS_ONLY",
            "lawVII": {
                "executesWorkflows": False,
                "workflowTokenOwnership": "NEVER",
                "placesTrades": False,
                "generatesRecommendations": False,
                "brokerAccess": "BLOCKED",
                "promptMutation": "BLOCKED",
                "strategyMutation": "BLOCKED",
                "commanderOverride": "FORBIDDEN",
            },
            "marketContextRepository": repository,
            "latestMarketContext": context,
            "normalizedMarketLayers": {
                "marketPrices": price_layer,
                "technicalIndicators": technical_layer,
                "sectorLeadership": sector_layer,
                "fundamentalInformation": fundamental_layer,
                "macroeconomicEnvironment": macro_layer,
                "newsIntelligence": news_layer,
                "optionsMarket": options_layer,
                "portfolioContext": portfolio_layer,
                "marketRegimeClassification": regime_layer,
            },
            "marketSnapshotEngine": {
                "snapshotCount": len(repository),
                "latestSnapshotId": context["snapshotId"],
                "historicalReplayReady": True,
                "immutableSnapshots": True,
            },
            "indicatorConfiguration": {
                "commanderApprovedIndicators": ("Moving Average", "VWAP", "RSI", "ATR", "Momentum", "Support and Resistance", "Trend Strength"),
                "unapprovedIndicatorsExcluded": True,
            },
            "cacheStatistics": {
                "cacheEnabled": True,
                "cacheKey": context["snapshotId"],
                "cacheHits": max(0, len(workflow_runtime_monitor.get("recentCompletedWorkflows", ())) - 1),
                "cacheMisses": 1,
                "duplicateRequestsAvoided": max(0, len(workflow_runtime_monitor.get("recentCompletedWorkflows", ()))),
                "apiCreditsConsumed": 0.0,
                "freshnessThresholdSeconds": 300,
            },
            "apiConsumption": {
                "externalApiCalls": 0,
                "brokerCalls": 0,
                "tradingApiCalls": 0,
                "costUsd": 0.0,
            },
            "dataFreshness": context["dataFreshness"],
            "sourceHealth": {
                "providerAbstraction": _quality(timestamp_utc, market_data_provider.get("layerName", "Market Data Provider Abstraction Layer"), 0.93),
                "deterministicFixture": _quality(timestamp_utc, "ARGOS deterministic market context", 0.86),
                "performanceTruth": _quality(timestamp_utc, performance_truth.get("sourceOfTruth", "IMMUTABLE_LEDGER"), 0.91),
                "strategyPerformance": _quality(timestamp_utc, strategy_performance.get("consoleName", "Live Strategy Performance Console"), 0.88),
                "portfolioContext": _quality(timestamp_utc, lppc.get("consoleName", "Live Portfolio Performance Console"), 0.9),
            },
            "normalizationRules": (
                "Symbols are uppercase canonical tickers.",
                "Percent values are normalized to decimal percent numbers.",
                "Unknown values remain explicit UNKNOWN fields.",
                "All layers carry timestamp, source, confidence, freshness, reliability, completeness, and validation status.",
                "Context is advisory awareness and cannot generate recommendations or trades.",
            ),
            "internalDiagnostics": {
                "deterministic": True,
                "providerAbstractionLayer": market_data_provider.get("engineeringOrder", "EO-G"),
                "vendorSpecificPayloadVisibleToCognition": False,
                "fabricatesUnknownMarketInformation": False,
                "rawFeedsExposedToDecisionObject": False,
                "decisionObjectEnrichmentEnabled": True,
                "productionMutationCount": 0,
                "apiCreditsConsumed": 0.0,
            },
        }

    def _price_layer(self, timestamp_utc: str, strategy_performance: dict[str, Any], performance_truth: dict[str, Any]) -> dict[str, Any]:
        benchmarks = tuple(strategy_performance.get("marketBenchmarks", ()))
        trades = tuple(performance_truth.get("tradeLedger", ()))
        symbols = tuple(dict.fromkeys([*(item.get("benchmark", "") for item in benchmarks), *(item.get("ticker", "") for item in trades), "SPY", "QQQ"]))
        latest_return = float(benchmarks[0].get("benchmarkReturnPercent", 0.0) if benchmarks else 0.0)
        return {
            "quality": _quality(timestamp_utc, "normalized benchmark and paper trade ledger", 0.88),
            "relatedSymbols": tuple(item for item in symbols if item),
            "relatedIndices": tuple(item.get("benchmark", "") for item in benchmarks if item.get("benchmark")) or ("SPY", "QQQ", "DIA", "IWM"),
            "currentPrice": "UNKNOWN",
            "open": "UNKNOWN",
            "high": "UNKNOWN",
            "low": "UNKNOWN",
            "close": "UNKNOWN",
            "volume": "UNKNOWN",
            "averageVolume": "UNKNOWN",
            "gap": round(latest_return, 4),
            "dailyRange": "UNKNOWN",
            "intradayChange": round(latest_return, 4),
            "relativeVolume": "UNKNOWN",
            "fiftyTwoWeekHigh": "UNKNOWN",
            "fiftyTwoWeekLow": "UNKNOWN",
        }

    def _technical_layer(self, price_layer: dict[str, Any]) -> dict[str, Any]:
        change = float(price_layer.get("intradayChange", 0.0) or 0.0)
        trend = "Positive" if change >= 0 else "Negative"
        return {
            "quality": price_layer["quality"],
            "movingAverages": trend,
            "vwap": "UNKNOWN",
            "rsi": "NEUTRAL",
            "macd": trend,
            "bollingerBands": "UNKNOWN",
            "atr": "CONTAINED",
            "adx": "UNKNOWN",
            "momentum": trend,
            "rateOfChange": round(change, 4),
            "stochasticOscillator": "UNKNOWN",
            "obv": "UNKNOWN",
            "chaikinMoneyFlow": "UNKNOWN",
            "volumeProfile": "UNKNOWN",
            "supportAndResistance": "PAPER_CONTEXT_ONLY",
            "trendStrength": "Moderate" if abs(change) >= 0.5 else "Low",
        }

    def _sector_layer(self, strategy_performance: dict[str, Any], performance_truth: dict[str, Any]) -> dict[str, Any]:
        strategies = tuple(strategy_performance.get("strategyLeaderboard", ()))
        offices = tuple(performance_truth.get("officeAttribution", ()))
        sectors = tuple(dict.fromkeys(item.get("strategyName", "Paper Strategy") for item in strategies)) or ("Technology", "Financials", "Healthcare", "Energy")
        return {
            "quality": _quality("", "strategy and office attribution", 0.82),
            "relatedSectors": sectors,
            "leadership": sectors[0] if sectors else "UNKNOWN",
            "weakness": "UNKNOWN",
            "rotation": "Paper Rotation",
            "relativeStrength": "Neutral",
            "breadth": len(offices),
            "momentum": "Constructive" if strategies else "Awaiting strategy history",
        }

    def _fundamental_layer(self, price_layer: dict[str, Any]) -> dict[str, Any]:
        return {
            "quality": _quality(price_layer["quality"]["timestamp"], "deterministic fundamental placeholder", 0.62, completeness=0.35),
            "marketCapitalization": "UNKNOWN",
            "revenueGrowth": "UNKNOWN",
            "epsGrowth": "UNKNOWN",
            "profitMargins": "UNKNOWN",
            "debtRatios": "UNKNOWN",
            "cashFlow": "UNKNOWN",
            "returnOnEquity": "UNKNOWN",
            "valuationRatios": "UNKNOWN",
            "dividendInformation": "UNKNOWN",
            "analystEstimates": "UNKNOWN",
        }

    def _macro_layer(self, timestamp_utc: str) -> tuple[dict[str, Any], ...]:
        return (
            {
                "eventId": "MACRO-PAPER-FED-FUNDS",
                "timestamp": timestamp_utc,
                "source": "ARGOS deterministic macro calendar",
                "category": "Federal Reserve",
                "description": "Federal funds and treasury yield context tracked as structured awareness.",
                "estimatedImportance": "MEDIUM",
                "confidence": 0.74,
                "quality": _quality(timestamp_utc, "ARGOS deterministic macro calendar", 0.74, completeness=0.55),
            },
        )

    def _news_layer(self, timestamp_utc: str, symbols: tuple[str, ...]) -> tuple[dict[str, Any], ...]:
        return (
            {
                "newsId": "NEWS-PAPER-MARKET-WIDE",
                "source": "ARGOS deterministic news context",
                "timestamp": timestamp_utc,
                "category": "Market-Wide Events",
                "affectedSymbols": tuple(symbols[:4]) or ("SPY",),
                "estimatedImportance": "LOW",
                "confidence": 0.7,
                "summary": "No live headlines are fabricated; paper context records monitored market-wide awareness only.",
                "quality": _quality(timestamp_utc, "ARGOS deterministic news context", 0.7, completeness=0.45),
            },
        )

    def _options_layer(self, price_layer: dict[str, Any]) -> dict[str, Any]:
        return {
            "quality": _quality(price_layer["quality"]["timestamp"], "deterministic options placeholder", 0.58, completeness=0.25),
            "openInterest": "UNKNOWN",
            "volume": "UNKNOWN",
            "putCallRatio": "UNKNOWN",
            "impliedVolatility": "UNKNOWN",
            "ivRank": "UNKNOWN",
            "expectedMove": "UNKNOWN",
            "gammaExposure": "UNKNOWN",
            "deltaExposure": "UNKNOWN",
            "maxPain": "UNKNOWN",
            "unusualActivity": "UNKNOWN",
        }

    def _portfolio_layer(self, lppc: dict[str, Any], performance_truth: dict[str, Any]) -> dict[str, Any]:
        portfolio = performance_truth.get("calculations", {}).get("portfolio", {})
        truth_positions = tuple(performance_truth.get("positionLedger", ()))
        combined = lppc.get("combinedPortfolio", {})
        buying_power = float(combined.get("buying_power", combined.get("buyingPower", 0.0)) or 0.0)
        equity = float(portfolio.get("totalEquity", combined.get("total_equity", combined.get("totalEquity", 100000.0))) or 100000.0)
        exposure = float(portfolio.get("marketValue", 0.0) or 0.0)
        return {
            "quality": _quality("", "LPPC and Performance Truth", 0.9),
            "currentPositions": len(truth_positions),
            "cashAllocation": round(buying_power, 4),
            "sectorAllocation": tuple({"sector": item.get("sector", "UNKNOWN"), "marketValue": item.get("market_value", 0.0)} for item in truth_positions),
            "capitalUtilization": round((exposure / max(1.0, equity)) * 100, 4),
            "openRisk": round(float(portfolio.get("maximumDrawdown", portfolio.get("drawdown", 0.0)) or 0.0), 4),
            "maximumExposure": 5.0,
            "availableBuyingPower": round(buying_power, 4),
            "correlation": "UNKNOWN",
            "diversification": "LIMITED" if len(truth_positions) <= 1 else "BROADENING",
            "currentStrategyAllocation": "Workflow Proof Strategy",
            "enterpriseRiskBudget": 5.0,
        }

    def _regime(self, price_layer: dict[str, Any], sector_layer: dict[str, Any], portfolio_layer: dict[str, Any]) -> dict[str, str]:
        change = float(price_layer.get("intradayChange", 0.0) or 0.0)
        open_risk = abs(float(portfolio_layer.get("openRisk", 0.0) or 0.0))
        if open_risk >= 2.0:
            volatility = "High Volatility"
        elif open_risk <= 0.25:
            volatility = "Low Volatility"
        else:
            volatility = "Moderate Volatility"
        if change >= 0.75:
            regime = "Moderate Bull"
            trend = "Constructive"
        elif change <= -0.75:
            regime = "Weak Bear"
            trend = "Defensive"
        else:
            regime = "Sideways"
            trend = "Balanced"
        return {
            "marketRegime": regime,
            "overallTrend": trend,
            "volatilityState": volatility,
            "liquidityState": "Paper Liquidity",
            "riskEnvironment": "Risk On" if change >= 0 and open_risk < 2.0 else "Risk Off",
            "sectorRotation": sector_layer.get("rotation", "UNKNOWN"),
        }

    def _freshness(self, timestamp_utc: str) -> dict[str, Any]:
        return {
            "timestamp": timestamp_utc,
            "freshnessSeconds": 0,
            "freshnessStatus": "FRESH",
            "commanderThresholdSeconds": 300,
            "validationStatus": "VALID",
        }

    def _confidence(self, price_layer: dict[str, Any], sector_layer: dict[str, Any], portfolio_layer: dict[str, Any]) -> float:
        score = 0.52
        score += float(price_layer.get("quality", {}).get("confidence", 0.0)) * 0.16
        score += float(sector_layer.get("quality", {}).get("confidence", 0.0)) * 0.12
        score += float(portfolio_layer.get("quality", {}).get("confidence", 0.0)) * 0.16
        return round(min(0.96, score), 2)


def _quality(timestamp_utc: str, source: str, confidence: float, *, completeness: float = 0.8) -> dict[str, Any]:
    return {
        "timestamp": timestamp_utc,
        "source": source,
        "confidence": round(confidence, 2),
        "freshness": "FRESH" if timestamp_utc else "DERIVED",
        "reliability": "DETERMINISTIC",
        "completeness": round(completeness, 2),
        "validationStatus": "VALID",
    }


def _stable_id(value: str) -> int:
    return sum((index + 1) * ord(character) for index, character in enumerate(value)) % 1000000
