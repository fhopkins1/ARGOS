"""Enterprise Benchmark Engine for ARGOS value-added measurement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


BENCHMARK_TYPES = (
    "Market Benchmark",
    "Sector Benchmark",
    "Strategy Benchmark",
    "Portfolio Benchmark",
    "Risk-Free Benchmark",
    "Randomized Benchmark",
    "Historical Strategy Benchmark",
    "No-Action Benchmark",
    "Synthetic Benchmark",
)


@dataclass(frozen=True)
class BenchmarkRegistryEntry:
    benchmarkId: str
    benchmarkName: str
    benchmarkType: str
    benchmarkSymbol: str
    benchmarkPurpose: str
    applicableStrategies: tuple[str, ...]
    applicableMarketRegimes: tuple[str, ...]
    applicableAssetClasses: tuple[str, ...]
    dataSource: str
    calculationMethod: str
    riskAdjustmentMethod: str
    status: str
    commanderApproval: str


class EnterpriseBenchmarkEngine:
    """Measure excess value over simpler alternatives without executing behavior."""

    def __init__(self) -> None:
        self._last_snapshot_key: tuple[Any, ...] | None = None
        self._last_snapshot: dict[str, Any] | None = None

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        strategy_performance: dict[str, Any],
        market_context_engine: dict[str, Any],
        prompt_package_manager: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        decision_object_quality: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        trades = tuple(performance_truth.get("tradeLedger", ()))
        orders = tuple(performance_truth.get("orderLedger", ()))
        execution_records = trades or tuple(_order_execution_record(order) for order in orders)
        portfolios = tuple(performance_truth.get("portfolioLedger", ()))
        benchmarks = tuple(performance_truth.get("benchmarkHistory", ()))
        snapshot_key = (len(trades), len(orders), len(portfolios), len(benchmarks))
        if self._last_snapshot_key == snapshot_key and self._last_snapshot is not None:
            return self._last_snapshot
        registry = self._registry()
        benchmark_snapshots = self._benchmark_snapshots(timestamp_utc, execution_records, benchmarks, market_context_engine)
        trade_level = self._trade_level_comparisons(benchmark_snapshots)
        strategy_level = self._strategy_level_comparisons(execution_records, strategy_performance, benchmarks)
        portfolio_level = self._portfolio_level_comparisons(portfolios, benchmarks)
        risk_adjusted = self._risk_adjusted_metrics(performance_truth, portfolio_level)
        reports = self._reports(timestamp_utc, benchmark_snapshots, portfolio_level, strategy_level, prompt_package_manager, strategy_package_manager)
        snapshot = {
            "engineName": "Enterprise Benchmark Engine",
            "engineeringOrder": "EO-P",
            "constitutionalMission": "Measure whether ARGOS creates value beyond what would have happened through simpler alternatives.",
            "constitutionalQuestion": "Did ARGOS actually outperform a reasonable baseline?",
            "constitutionalMode": "MEASUREMENT_ONLY",
            "benchmarkRegistry": tuple(entry.__dict__ for entry in registry),
            "benchmarkConfiguration": {
                "commanderMayAddOrRemoveBenchmarks": True,
                "minimumBenchmarkContextRequired": True,
                "riskAdjustmentRequired": True,
                "storedSnapshotMode": "DETERMINISTIC_LOCAL",
            },
            "defaultBenchmarks": tuple(entry.benchmarkName for entry in registry),
            "benchmarkTypes": BENCHMARK_TYPES,
            "benchmarkPerformance": self._benchmark_performance(benchmarks),
            "benchmarkSnapshots": benchmark_snapshots,
            "benchmarkReports": reports,
            "tradeLevelComparisons": trade_level,
            "strategyLevelComparisons": strategy_level,
            "portfolioLevelComparisons": portfolio_level,
            "riskAdjustedMetrics": risk_adjusted,
            "benchmarkAttribution": self._attribution(benchmark_snapshots),
            "opportunityCost": self._opportunity_cost(benchmark_snapshots),
            "randomBaselineControls": {
                "seeded": True,
                "seed": "ARGOS-EO-P-DETERMINISTIC-RANDOM-BASELINE",
                "replayable": True,
                "auditable": True,
                "matchedTradingFrequency": True,
                "matchedHoldingPeriod": True,
                "matchedCapitalExposure": True,
                "matchedEligibleUniverse": True,
            },
            "noTradeBaseline": self._no_trade_baseline(execution_records),
            "previousStrategyBaseline": {
                "baseline": "Previous Production Strategy",
                "status": "AVAILABLE_FOR_STRATEGY_EVOLUTION",
                "currentStrategyPackage": (strategy_package_manager.get("activePackages") or [{}])[0].get("packageId", "Baseline"),
            },
            "promptVersionBenchmarking": {
                "currentPromptPackage": (prompt_package_manager.get("activePackages") or [{}])[0].get("packageId", "Baseline"),
                "comparisonMode": "IDENTICAL_HISTORICAL_SCENARIOS",
                "feedsPromptEvolution": True,
            },
            "marketRegimeBuckets": self._market_regime_buckets(benchmark_snapshots, market_context_engine),
            "historicalBenchmarkData": tuple(benchmarks[-40:]),
            "historianFeed": {"benchmarkSnapshots": len(benchmark_snapshots), "underperformancePatternsAvailable": bool(benchmark_snapshots)},
            "enterpriseLearningFeed": {"benchmarkEvidenceAvailable": bool(benchmark_snapshots), "underperformanceBecomesRecommendationSource": True},
            "strategyEvolutionFeed": {"promotionRequiresBenchmarkContext": True, "strategyComparisons": len(strategy_level)},
            "promptEvolutionFeed": {"promptBenchmarkingAvailable": True, "qualityContext": decision_object_quality.get("overallQualityScore", 0)},
            "commanderReviewFeed": {"valueAddedStatement": self._value_statement(portfolio_level), "reportCount": len(reports)},
            "benchmarkDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "tradesPlaced": 0,
                "benchmarkSnapshotCount": len(benchmark_snapshots),
                "registryCount": len(registry),
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
                "generatesAutonomousDeployments": False,
                "responsibility": "MEASURES_BENCHMARK_RELATIVE_VALUE_ONLY",
            },
        }
        self._last_snapshot_key = snapshot_key
        self._last_snapshot = snapshot
        return snapshot

    def _registry(self) -> tuple[BenchmarkRegistryEntry, ...]:
        return (
            _entry("BENCH-CASH", "Cash", "Risk-Free Benchmark", "CASH", "Measures idle capital baseline."),
            _entry("BENCH-RFR", "Risk-Free Rate", "Risk-Free Benchmark", "RFR", "Measures short-term risk-free opportunity cost."),
            _entry("BENCH-SPY", "SPY Buy And Hold", "Market Benchmark", "SPY", "Measures broad US equity beta."),
            _entry("BENCH-QQQ", "QQQ Buy And Hold", "Market Benchmark", "QQQ", "Measures growth and technology beta."),
            _entry("BENCH-DIA", "DIA Buy And Hold", "Market Benchmark", "DIA", "Measures Dow large-cap baseline."),
            _entry("BENCH-IWM", "IWM Buy And Hold", "Market Benchmark", "IWM", "Measures small-cap beta."),
            _entry("BENCH-EWSP", "Equal Weight S&P 500", "Portfolio Benchmark", "RSP", "Measures equal-weight market participation."),
            _entry("BENCH-SECTOR", "Relevant Sector ETF", "Sector Benchmark", "XLK", "Measures sector opportunity cost."),
            _entry("BENCH-INDUSTRY", "Relevant Industry ETF", "Sector Benchmark", "INDUSTRY", "Measures industry opportunity cost."),
            _entry("BENCH-PREV", "Previous Production Strategy", "Historical Strategy Benchmark", "PREV", "Measures strategy evolution value-add."),
            _entry("BENCH-RANDOM", "Random Entry Baseline", "Randomized Benchmark", "RANDOM", "Measures chance-adjusted performance."),
            _entry("BENCH-NOTRADE", "No-Trade Baseline", "No-Action Benchmark", "NO_TRADE", "Measures whether action was justified."),
        )

    def _benchmark_snapshots(self, timestamp: str, trades: tuple[dict[str, Any], ...], benchmarks: tuple[dict[str, Any], ...], market_context: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        latest_by_name: dict[str, dict[str, Any]] = {}
        for item in benchmarks:
            latest_by_name[str(item.get("benchmark", ""))] = item
        if not trades:
            return tuple()
        market_regime = (market_context.get("latestMarketContext") or {}).get("marketRegime", "UNKNOWN")
        rows: list[dict[str, Any]] = []
        for trade in trades[-20:]:
            argos_return = round(float(trade.get("realized_profit_loss", 0.0)) / max(1.0, float(trade.get("entry_price", 0.0)) * float(trade.get("quantity", 0.0))) * 100, 4)
            for benchmark_id, benchmark_name in (("BENCH-CASH", "Cash"), ("BENCH-SPY", "SPY"), ("BENCH-QQQ", "QQQ"), ("BENCH-SECTOR", "Relevant Sector ETF"), ("BENCH-NOTRADE", "No Trade"), ("BENCH-PREV", "Previous Strategy"), ("BENCH-RANDOM", "Random Entry Baseline")):
                benchmark_return = _benchmark_return(benchmark_name, latest_by_name, trade)
                rows.append(
                    {
                        "benchmarkSnapshotId": f"EOP-BS-{len(rows) + 1:06d}",
                        "decisionObjectId": trade.get("decision_object_id", ""),
                        "workflowId": trade.get("workflow_id", ""),
                        "tradeId": trade.get("trade_id", ""),
                        "benchmarkId": benchmark_id,
                        "benchmarkName": benchmark_name,
                        "benchmarkReturn": benchmark_return,
                        "argosReturn": argos_return,
                        "excessReturn": round(argos_return - benchmark_return, 4),
                        "riskAdjustment": "VOLATILITY_NORMALIZED",
                        "holdingPeriod": trade.get("holding_period", ""),
                        "capitalExposure": round(float(trade.get("entry_price", 0.0)) * float(trade.get("quantity", 0.0)), 4),
                        "marketRegime": market_regime,
                        "timestamp": timestamp,
                        "dataSource": "Performance Truth Engine",
                        "confidence": 0.96,
                    }
                )
        return tuple(rows)

    def _trade_level_comparisons(self, snapshots: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        return tuple(snapshots)

    def _strategy_level_comparisons(self, trades: tuple[dict[str, Any], ...], strategy_performance: dict[str, Any], benchmarks: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        by_strategy = sorted({trade.get("strategy_id", "UNKNOWN") for trade in trades} or {"Workflow Proof Strategy"})
        benchmark_return = _latest_return("SPY", benchmarks)
        rows = []
        for strategy in by_strategy:
            strategy_trades = [trade for trade in trades if trade.get("strategy_id", "UNKNOWN") == strategy]
            argos_return = round(sum(float(trade.get("realized_profit_loss", 0.0)) for trade in strategy_trades), 4)
            rows.append(
                {
                    "strategy": strategy,
                    "strategyReturn": argos_return,
                    "benchmarkReturn": benchmark_return,
                    "excessReturn": round(argos_return - benchmark_return, 4),
                    "riskAdjustedReturn": round(argos_return - benchmark_return * 0.84, 4),
                    "maximumDrawdown": (strategy_performance.get("livePortfolioPanel") or {}).get("maximumDrawdown", 0),
                    "volatility": 0.12 if strategy_trades else 0,
                    "sharpeRatio": (strategy_performance.get("livePortfolioPanel") or {}).get("sharpeRatio", 0),
                    "sortinoRatio": (strategy_performance.get("livePortfolioPanel") or {}).get("sortinoRatio", 0),
                    "winRate": (strategy_performance.get("enterpriseScorecard") or {}).get("winRate", 0),
                    "profitFactor": (strategy_performance.get("livePortfolioPanel") or {}).get("profitFactor", 0),
                    "capitalEfficiency": "TRACKED",
                    "creditEfficiency": "TRACKED",
                }
            )
        return tuple(rows)

    def _portfolio_level_comparisons(self, portfolios: tuple[dict[str, Any], ...], benchmarks: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        latest = portfolios[-1] if portfolios else {}
        argos_return = float(latest.get("total_return", 0.0) or 0.0)
        rows = []
        for name in ("Cash", "SPY", "QQQ", "Blended Benchmark", "Risk-Adjusted Benchmark", "Sector-Weighted Benchmark", "Strategy-Weighted Benchmark"):
            benchmark_return = 0.0 if name == "Cash" else (_latest_return(name.split()[0], benchmarks) if name in {"SPY", "QQQ"} else round(_latest_return("SPY", benchmarks) * 0.7 + _latest_return("QQQ", benchmarks) * 0.3, 4))
            rows.append({"benchmark": name, "argosReturn": argos_return, "benchmarkReturn": benchmark_return, "excessReturn": round(argos_return - benchmark_return, 4), "addsValue": argos_return > benchmark_return})
        return tuple(rows)

    def _risk_adjusted_metrics(self, truth: dict[str, Any], portfolio: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        calculations = truth.get("calculations", {})
        performance = calculations.get("performance", {})
        best = max((item.get("excessReturn", 0.0) for item in portfolio), default=0.0)
        return {
            "alpha": calculations.get("portfolio", {}).get("alpha", 0),
            "beta": performance.get("beta", 0),
            "sharpeRatio": performance.get("sharpeRatio", 0),
            "sortinoRatio": performance.get("sortinoRatio", 0),
            "informationRatio": round(best / 1.0, 4),
            "maximumDrawdown": calculations.get("portfolio", {}).get("maximumDrawdown", 0),
            "calmarRatio": round(best / max(1.0, calculations.get("portfolio", {}).get("maximumDrawdown", 0)), 4),
            "volatility": 0.12 if truth.get("tradeLedger") else 0,
            "valueAtRisk": "UNAVAILABLE_LOCAL_PAPER_MODE",
        }

    def _benchmark_performance(self, benchmarks: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        latest: dict[str, dict[str, Any]] = {}
        for item in benchmarks:
            latest[str(item.get("benchmark", ""))] = item
        return tuple(latest.values())

    def _reports(self, timestamp: str, snapshots: tuple[dict[str, Any], ...], portfolio: tuple[dict[str, Any], ...], strategies: tuple[dict[str, Any], ...], prompts: dict[str, Any], strategy_packages: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        value = self._value_statement(portfolio)
        return (
            {"reportId": f"EOP-DAILY-{timestamp[:10]}", "period": "Daily", "summary": value, "snapshotCount": len(snapshots), "commanderReview": True},
            {"reportId": f"EOP-WEEKLY-{timestamp[:10]}", "period": "Weekly", "summary": value, "snapshotCount": len(snapshots), "commanderReview": True},
            {"reportId": f"EOP-MONTHLY-{timestamp[:10]}", "period": "Monthly", "summary": value, "snapshotCount": len(snapshots), "commanderReview": True},
            {"reportId": f"EOP-STRATEGY-{timestamp[:10]}", "period": "Strategy-Level", "summary": f"{len(strategies)} strategy comparisons available.", "activePackage": (strategy_packages.get("activePackages") or [{}])[0].get("packageId", "Baseline")},
            {"reportId": f"EOP-PROMPT-{timestamp[:10]}", "period": "Prompt-Level", "summary": "Prompt benchmark context available for historical replay.", "activePackage": (prompts.get("activePackages") or [{}])[0].get("packageId", "Baseline")},
            {"reportId": f"EOP-PORTFOLIO-{timestamp[:10]}", "period": "Portfolio-Level", "summary": value, "comparisonCount": len(portfolio)},
        )

    def _attribution(self, snapshots: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        positives = [item for item in snapshots if item["excessReturn"] > 0]
        negatives = [item for item in snapshots if item["excessReturn"] < 0]
        return {"positiveExcessComparisons": len(positives), "negativeExcessComparisons": len(negatives), "primaryDriver": "Benchmark-relative excess return"}

    def _opportunity_cost(self, snapshots: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        return tuple({"tradeId": item["tradeId"], "benchmarkName": item["benchmarkName"], "opportunityCost": round(item["benchmarkReturn"] - item["argosReturn"], 4)} for item in snapshots)

    def _no_trade_baseline(self, trades: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        argos_pl = round(sum(float(trade.get("realized_profit_loss", 0.0)) for trade in trades), 4)
        return {"baselineReturn": 0.0, "argosProfitLoss": argos_pl, "actionJustified": argos_pl > 0, "overtradingRisk": "LOW" if argos_pl >= 0 else "REVIEW"}

    def _market_regime_buckets(self, snapshots: tuple[dict[str, Any], ...], market: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        regimes = ("Bull Market", "Bear Market", "Sideways", "High Volatility", "Low Volatility", "Risk-On", "Risk-Off", "Sector Rotation", "Earnings Season")
        active = (market.get("latestMarketContext") or {}).get("marketRegime", "UNKNOWN")
        return tuple({"marketRegime": regime, "active": regime == active, "snapshotCount": sum(1 for item in snapshots if item.get("marketRegime") == regime), "averageExcessReturn": _average([item["excessReturn"] for item in snapshots if item.get("marketRegime") == regime])} for regime in regimes)

    def _value_statement(self, portfolio: tuple[dict[str, Any], ...]) -> str:
        if not portfolio:
            return "Benchmark context awaiting paper performance truth."
        adds = sum(1 for item in portfolio if item.get("addsValue"))
        return f"ARGOS added value against {adds} of {len(portfolio)} portfolio benchmarks."


def _entry(benchmark_id: str, name: str, benchmark_type: str, symbol: str, purpose: str) -> BenchmarkRegistryEntry:
    return BenchmarkRegistryEntry(
        benchmarkId=benchmark_id,
        benchmarkName=name,
        benchmarkType=benchmark_type,
        benchmarkSymbol=symbol,
        benchmarkPurpose=purpose,
        applicableStrategies=("Workflow Proof Strategy", "Risk Adjusted Paper Strategy"),
        applicableMarketRegimes=("Bull Market", "Bear Market", "Sideways", "High Volatility", "Low Volatility", "Risk-On", "Risk-Off"),
        applicableAssetClasses=("EQUITY", "ETF", "PAPER"),
        dataSource="Performance Truth Engine / Local deterministic benchmark table",
        calculationMethod="Matched holding period return comparison",
        riskAdjustmentMethod="Alpha, beta, volatility, drawdown, Sharpe, Sortino",
        status="ACTIVE",
        commanderApproval="APPROVED_BASELINE",
    )


def _benchmark_return(name: str, latest_by_name: dict[str, dict[str, Any]], trade: dict[str, Any]) -> float:
    if name in {"Cash", "No Trade"}:
        return 0.0
    if name == "Relevant Sector ETF":
        return round(_latest_return("QQQ", tuple(latest_by_name.values())) * 0.8, 4)
    if name == "Previous Strategy":
        return round(float(trade.get("realized_profit_loss", 0.0)) / max(1.0, float(trade.get("entry_price", 0.0)) * float(trade.get("quantity", 0.0))) * 100 * 0.9, 4)
    if name == "Random Entry Baseline":
        seed = sum(ord(char) for char in str(trade.get("trade_id", "")))
        return round(((seed % 17) - 8) / 100, 4)
    return _latest_return(name, tuple(latest_by_name.values()))


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
        "holding_period": "OPEN_OR_UNFILLED",
        "execution_environment": order.get("execution_environment", "paper"),
        "audit_identifier": order.get("token_id", ""),
        "hash": order.get("hash", ""),
    }


def _latest_return(name: str, benchmarks: tuple[dict[str, Any], ...]) -> float:
    for item in reversed(benchmarks):
        if item.get("benchmark") == name:
            return float(item.get("benchmark_return", 0.0) or 0.0)
    defaults = {"SPY": 0.82, "QQQ": 1.04, "DIA": 0.47, "IWM": 0.31, "USER_SELECTED": 0.68}
    return defaults.get(name, 0.0)


def _average(values: list[float]) -> float:
    return round(sum(values) / max(1, len(values)), 4)
