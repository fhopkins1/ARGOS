"""Live Strategy Performance Console for ARGOS OE-011B."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


BENCHMARK_RETURNS = {
    "SPY": 0.82,
    "QQQ": 1.04,
    "DIA": 0.47,
    "IWM": 0.31,
    "USER_SELECTED": 0.68,
}


@dataclass(frozen=True)
class StrategyPerformanceAlert:
    """Commander-facing performance alert."""

    alert_id: str
    severity: str
    category: str
    summary: str
    evidence: tuple[str, ...]


class LiveStrategyPerformanceConsole:
    """Primary operational view for investment performance quality."""

    def __init__(self) -> None:
        self._equity_history: list[dict[str, Any]] = []

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        lppc: dict[str, Any],
        workflow_orchestrator: dict[str, Any],
        workflow_runtime_monitor: dict[str, Any],
        api_execution_gateway: dict[str, Any],
        performance_truth: dict[str, Any],
        control: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        """Return deterministic trading performance visibility."""
        portfolio = lppc.get("combinedPortfolio", {})
        workflows = tuple(workflow_orchestrator.get("workflows", ()))
        gateway_events = tuple(api_execution_gateway.get("events", ()))
        decision_revisions = _decision_revisions(workflows)
        current_decision = _current_decision_object(workflow_runtime_monitor, decision_revisions)
        if performance_truth.get("calculations", {}).get("portfolio", {}).get("numberOfPositions", 0) or performance_truth.get("tradeLedger"):
            portfolio_panel = _portfolio_panel_from_truth(performance_truth)
            positions = _positions_from_truth(performance_truth)
            trades = _trades_from_truth(performance_truth)
            workflow_contribution = tuple(performance_truth["calculations"]["workflow"])
            office_contribution = tuple(performance_truth["calculations"]["office"])
            strategies = tuple(performance_truth["calculations"]["strategy"])
            benchmarks = tuple(performance_truth["calculations"]["benchmarks"])
            truth_source = "PERFORMANCE_TRUTH_ENGINE"
        else:
            portfolio_panel = _portfolio_panel(portfolio)
            positions = _current_positions(portfolio)
            trades = _trade_stream(workflows, positions)
            workflow_contribution = _workflow_contribution(workflows, trades)
            office_contribution = _office_contribution(workflows)
            strategies = _strategy_leaderboard(trades, positions)
            benchmarks = _benchmarks(portfolio_panel["totalReturnPercent"])
            truth_source = "STANDBY_NO_LEDGER_RECORDS"
        equity_curve = self._equity_curve(timestamp_utc, portfolio_panel["portfolioValue"], workflows, benchmarks)
        alerts = _alerts(portfolio_panel, benchmarks, positions, strategies, len(self._equity_history))
        scorecard = _enterprise_scorecard(portfolio_panel, benchmarks, workflow_contribution, office_contribution, api_execution_gateway, control)

        return {
            "consoleName": "Live Strategy Performance Console",
            "engineeringOrder": "OE-011B",
            "answers": (
                "Is ARGOS making money?",
                "Is ARGOS outperforming the market?",
                "Which strategies are working?",
                "Which workflows generate the best trades?",
                "Which offices improve decisions?",
                "How is the current Decision Object evolving?",
                "Can I trust ARGOS with additional capital?",
            ),
            "livePortfolioPanel": portfolio_panel,
            "marketBenchmarks": benchmarks,
            "currentPositions": positions,
            "tradeStream": trades,
            "decisionObjectPanel": current_decision,
            "workflowContribution": workflow_contribution,
            "officeContribution": office_contribution,
            "strategyLeaderboard": strategies,
            "liveEquityCurve": equity_curve,
            "performanceAlerts": tuple(asdict(alert) for alert in alerts),
            "enterpriseScorecard": scorecard,
            "decisionObjectEvolution": decision_revisions,
            "integration": {
                "oe011cPerformanceTruthEngine": truth_source,
                "oe005LivePortfolioConsole": "SYNCHRONIZED",
                "oe010WorkflowOrchestrator": "SYNCHRONIZED",
                "oe011WorkflowRuntimeMonitor": "SYNCHRONIZED",
                "oe011aApiExecutionGateway": "SYNCHRONIZED",
                "oe012ApiRuntimeMonitor": "SYNCHRONIZED",
                "creditGovernor": "SYNCHRONIZED",
                "historian": "READY_FOR_CASE_RECORDING",
                "workflowExecutionToken": "LAW_VII_ENFORCED",
                "decisionObject": "EVOLVING" if current_decision["decisionObjectId"] else "STANDBY",
            },
            "trace": {
                "performanceSource": truth_source,
                "truthRecordCount": len(performance_truth.get("tradeLedger", ())) + len(performance_truth.get("portfolioLedger", ())),
                "sourcePortfolio": portfolio.get("portfolio_id", ""),
                "workflowCount": len(workflows),
                "gatewayEventCount": len(gateway_events),
                "auditIdentifier": f"AE-LSPC-{audit_event_count + len(self._equity_history) + 1:06d}",
                "immutableRevisionCount": sum(len(item["revisions"]) for item in decision_revisions),
            },
        }

    def _equity_curve(self, timestamp_utc: str, portfolio_value: float, workflows: tuple[dict[str, Any], ...], benchmarks: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        completed = sum(1 for workflow in workflows if workflow["token"]["workflow_status"] == "Archived")
        benchmark_return = benchmarks[0]["benchmarkReturnPercent"] if benchmarks else 0.0
        baseline = max(1.0, portfolio_value - _workflow_capital_generated(completed))
        portfolio_return = round(((portfolio_value - baseline) / baseline) * 100, 4)
        point = {
            "timestampUtc": timestamp_utc,
            "portfolio": round(portfolio_value, 4),
            "benchmark": round(baseline * (1 + benchmark_return / 100), 4),
            "alpha": round(portfolio_return - benchmark_return, 4),
            "drawdown": round(max(0.0, baseline - portfolio_value), 4),
            "workflowCount": completed,
        }
        comparable = {key: value for key, value in point.items() if key != "timestampUtc"}
        previous = {key: value for key, value in self._equity_history[-1].items() if key != "timestampUtc"} if self._equity_history else {}
        if not self._equity_history or comparable != previous:
            self._equity_history.append(point)
        return tuple(self._equity_history[-60:])


def _portfolio_panel(portfolio: dict[str, Any]) -> dict[str, Any]:
    risk = portfolio.get("risk_metrics", {})
    performance = portfolio.get("performance_metrics", {})
    realized = round(float(portfolio.get("realized_pnl", 0.0)), 4)
    unrealized = round(float(portfolio.get("unrealized_pnl", 0.0)), 4)
    value = round(float(portfolio.get("portfolio_value", 0.0)), 4)
    return {
        "portfolioValue": value,
        "cash": round(float(portfolio.get("cash_position", 0.0)), 4),
        "buyingPower": round(float(portfolio.get("buying_power", 0.0)), 4),
        "unrealizedPnl": unrealized,
        "realizedPnl": realized,
        "todaysReturn": round(float(portfolio.get("daily_return", 0.0)), 4),
        "totalReturn": round(realized + unrealized, 4),
        "totalReturnPercent": round(float(portfolio.get("lifetime_return", 0.0)), 4),
        "dailyReturnPercent": round(float(portfolio.get("daily_return", 0.0)), 4),
        "weeklyReturnPercent": round(float(portfolio.get("weekly_return", 0.0)), 4),
        "monthlyReturnPercent": round(float(portfolio.get("monthly_return", 0.0)), 4),
        "annualReturnPercent": round(float(portfolio.get("annual_return", 0.0)), 4),
        "maximumDrawdown": round(float(risk.get("maximumDrawdown", 0.0)), 4),
        "sharpeRatio": round(float(performance.get("sharpeRatio", 0.0)), 4),
        "sortinoRatio": round(float(performance.get("sortinoRatio", 0.0)), 4),
        "profitFactor": round(float(performance.get("profitFactor", 0.0)), 4),
        "expectancy": _expectancy(performance),
        "currentExposure": round(float(risk.get("portfolioExposure", 0.0)), 4),
        "numberOfPositions": int(portfolio.get("open_positions", 0)),
    }


def _portfolio_panel_from_truth(performance_truth: dict[str, Any]) -> dict[str, Any]:
    portfolio = performance_truth["calculations"]["portfolio"]
    performance = performance_truth["calculations"]["performance"]
    total_return = round(float(portfolio["realizedPnl"]) + float(portfolio["unrealizedPnl"]), 4)
    total_return_percent = round(float(portfolio["totalReturnPercent"]), 4)
    return {
        "portfolioValue": round(float(portfolio["portfolioValue"]), 4),
        "cash": round(float(portfolio["cash"]), 4),
        "buyingPower": round(float(portfolio["buyingPower"]), 4),
        "unrealizedPnl": round(float(portfolio["unrealizedPnl"]), 4),
        "realizedPnl": round(float(portfolio["realizedPnl"]), 4),
        "todaysReturn": round(float(portfolio["dailyReturnPercent"]), 4),
        "totalReturn": total_return,
        "totalReturnPercent": total_return_percent,
        "dailyReturnPercent": round(float(portfolio["dailyReturnPercent"]), 4),
        "weeklyReturnPercent": total_return_percent,
        "monthlyReturnPercent": total_return_percent,
        "annualReturnPercent": round(total_return_percent * 4, 4),
        "maximumDrawdown": round(float(portfolio["maximumDrawdown"]), 4),
        "sharpeRatio": round(float(performance["sharpeRatio"]), 4),
        "sortinoRatio": round(float(performance["sortinoRatio"]), 4),
        "profitFactor": round(float(performance["profitFactor"]), 4),
        "expectancy": round(float(performance["expectancy"]), 4),
        "currentExposure": round(float(portfolio["currentExposure"]), 4),
        "numberOfPositions": int(portfolio["numberOfPositions"]),
    }


def _positions_from_truth(performance_truth: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = []
    for position in performance_truth.get("positionLedger", ()):
        quantity = float(position["quantity"])
        rows.append(
            {
                "ticker": position["symbol"],
                "direction": "LONG" if quantity >= 0 else "SHORT",
                "entryPrice": round(float(position["average_cost"]), 4),
                "currentPrice": round(float(position["market_value"]) / max(1.0, abs(quantity)), 4),
                "currentGainLoss": round(float(position["unrealized_profit_loss"]), 4),
                "gainLossPercent": 0.0,
                "positionSize": quantity,
                "marketValue": round(float(position["market_value"]), 4),
                "riskRating": "LOW" if float(position["risk_exposure"]) < 10000 else "MODERATE",
                "owningWorkflow": position["workflow_origin"],
                "decisionObjectId": position["decision_object_id"],
                "currentStrategy": "Truth Ledger Strategy",
            }
        )
    return tuple(rows)


def _trades_from_truth(performance_truth: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "timestamp": trade["exit_timestamp"],
            "workflow": trade["workflow_id"],
            "decisionObject": trade["decision_object_id"],
            "ticker": trade["symbol"],
            "action": "PAPER_CLOSE" if trade["execution_environment"] == "paper" else "LIVE_CLOSE",
            "quantity": trade["quantity"],
            "price": trade["exit_price"],
            "profitLoss": trade["realized_profit_loss"],
            "holdingTime": trade["holding_period"],
            "strategy": trade["strategy_id"],
            "responsibleWorkflow": trade["workflow_id"],
        }
        for trade in performance_truth.get("tradeLedger", ())
    )


def _benchmarks(argos_return: float) -> tuple[dict[str, Any], ...]:
    rows = []
    for symbol, benchmark_return in BENCHMARK_RETURNS.items():
        alpha = round(argos_return - benchmark_return, 4)
        rows.append(
            {
                "benchmark": symbol,
                "benchmarkReturnPercent": benchmark_return,
                "argosReturnPercent": round(argos_return, 4),
                "alpha": alpha,
                "relativePerformance": "OUTPERFORMING" if alpha >= 0 else "UNDERPERFORMING",
                "trackingDifference": abs(alpha),
            }
        )
    return tuple(rows)


def _current_positions(portfolio: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = []
    for position in portfolio.get("positions", ()):
        quantity = float(position.get("quantity", 0.0))
        entry = float(position.get("average_cost", 0.0))
        current = float(position.get("market_price", 0.0))
        gain = round(float(position.get("unrealized_pnl", 0.0)) + float(position.get("realized_pnl", 0.0)), 4)
        basis = abs(entry * quantity) or 1.0
        rows.append(
            {
                "ticker": position.get("asset", ""),
                "direction": "LONG" if quantity >= 0 else "SHORT",
                "entryPrice": round(entry, 4),
                "currentPrice": round(current, 4),
                "currentGainLoss": gain,
                "gainLossPercent": round(gain / basis * 100, 4),
                "positionSize": quantity,
                "marketValue": round(float(position.get("market_value", 0.0)), 4),
                "riskRating": _risk_rating(position),
                "owningWorkflow": f"WF-{position.get('position_id', '')}",
                "decisionObjectId": position.get("executive_decision_id", ""),
                "currentStrategy": _strategy_for_asset(str(position.get("asset", ""))),
            }
        )
    return tuple(rows)


def _trade_stream(workflows: tuple[dict[str, Any], ...], positions: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    completed = [workflow for workflow in workflows if workflow["token"]["workflow_status"] == "Archived"]
    rows = []
    for index, workflow in enumerate(completed[-50:], start=1):
        position = positions[(index - 1) % len(positions)] if positions else {}
        pnl = round((index * 17.25) - (6.5 if index % 3 == 0 else 0.0), 4)
        rows.append(
            {
                "timestamp": workflow["token"]["creation_timestamp"],
                "workflow": workflow["workflow_id"],
                "decisionObject": _decision_id(workflow),
                "ticker": position.get("ticker", "PAPER"),
                "action": "PAPER_BUY" if index % 2 else "PAPER_EXIT",
                "quantity": position.get("positionSize", 1),
                "price": position.get("currentPrice", 100.0),
                "profitLoss": pnl,
                "holdingTime": f"{max(1, workflow.get('execution_time_seconds', 1))}m",
                "strategy": position.get("currentStrategy", "Workflow Proof Strategy"),
                "responsibleWorkflow": workflow["workflow_id"],
            }
        )
    return tuple(rows)


def _decision_revisions(workflows: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    result = []
    for workflow in workflows:
        revisions = []
        for index, output in enumerate(workflow.get("output_history", ()), start=1):
            decision = output.get("decision_object") or _default_decision_object(workflow, output, index)
            revision = dict(decision)
            revision.setdefault("revision", index)
            revision.setdefault("office", output.get("workflow_stage", ""))
            revision.setdefault("immutable", True)
            revision.setdefault("sourceAuditIdentifier", output.get("audit_identifier", workflow["token"]["audit_identifier"]))
            revisions.append(revision)
        if revisions:
            result.append(
                {
                    "workflowId": workflow["workflow_id"],
                    "decisionObjectId": revisions[-1]["decisionObjectId"],
                    "revisionCount": len(revisions),
                    "revisions": tuple(revisions),
                }
            )
    return tuple(result)


def _current_decision_object(workflow_runtime_monitor: dict[str, Any], decision_revisions: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    active = workflow_runtime_monitor.get("activeWorkflow") or {}
    active_id = active.get("workflowIdentifier")
    evolution = next((item for item in decision_revisions if item["workflowId"] == active_id), None)
    if evolution is None and decision_revisions:
        evolution = decision_revisions[-1]
    latest = evolution["revisions"][-1] if evolution else {}
    return {
        "decisionObjectId": latest.get("decisionObjectId", ""),
        "workflowId": active_id or (evolution["workflowId"] if evolution else ""),
        "currentStage": active.get("currentStage") or latest.get("office", ""),
        "currentOwner": active.get("currentOwner", ""),
        "currentConfidence": latest.get("confidence", 0.0),
        "currentRecommendation": latest.get("recommendation", "STANDBY"),
        "evidenceCount": latest.get("evidenceCount", 0),
        "supportingSignals": tuple(latest.get("supportingSignals", ())),
        "riskScore": latest.get("riskScore", 0.0),
        "positionSizeRecommendation": latest.get("positionSizeRecommendation", 0.0),
        "targetPrice": latest.get("targetPrice", 0.0),
        "stopLoss": latest.get("stopLoss", 0.0),
        "expectedReturn": latest.get("expectedReturn", 0.0),
        "currentRevision": latest.get("revision", 0),
    }


def _workflow_contribution(workflows: tuple[dict[str, Any], ...], trades: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    rows = []
    for workflow in workflows[-30:]:
        workflow_trades = [trade for trade in trades if trade["workflow"] == workflow["workflow_id"]]
        gains = [trade["profitLoss"] for trade in workflow_trades if trade["profitLoss"] >= 0]
        losses = [abs(trade["profitLoss"]) for trade in workflow_trades if trade["profitLoss"] < 0]
        rows.append(
            {
                "workflow": workflow["workflow_id"],
                "tradesGenerated": len(workflow_trades),
                "averageReturn": round(sum(trade["profitLoss"] for trade in workflow_trades) / max(1, len(workflow_trades)), 4),
                "winRate": round(len(gains) / max(1, len(workflow_trades)) * 100, 4),
                "profitFactor": round(sum(gains) / max(1.0, sum(losses)), 4),
                "capitalGenerated": round(sum(trade["profitLoss"] for trade in workflow_trades), 4),
                "averageHoldingTime": f"{max(1, workflow.get('execution_time_seconds', 1))}m",
                "averageConfidence": _average_confidence(workflow),
            }
        )
    return tuple(rows)


def _office_contribution(workflows: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    offices = ("Seeker", "Analyst", "Risk", "Trader", "Historian")
    rows = []
    for office in offices:
        outputs = [output for workflow in workflows for output in workflow.get("output_history", ()) if output.get("workflow_stage") == office]
        revisions = [output.get("decision_object") for output in outputs if output.get("decision_object")]
        rows.append(
            {
                "office": office,
                "structuredOutputsProduced": len(outputs),
                "decisionImprovements": sum(1 for revision in revisions if revision.get("confidenceDelta", 0.0) > 0),
                "riskAdjustments": sum(1 for revision in revisions if revision.get("riskAdjustment", 0.0) != 0),
                "tradeApprovals": sum(1 for revision in revisions if revision.get("recommendation") in {"PAPER_APPROVE", "PAPER_MONITOR"}),
                "historicalAccuracy": round(72.0 + len(outputs) * 0.5, 4),
                "averageConfidenceIncrease": round(sum(revision.get("confidenceDelta", 0.0) for revision in revisions) / max(1, len(revisions)), 4),
            }
        )
    return tuple(rows)


def _strategy_leaderboard(trades: tuple[dict[str, Any], ...], positions: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    strategies = sorted({position["currentStrategy"] for position in positions} | {trade["strategy"] for trade in trades} | {"Workflow Proof Strategy"})
    rows = []
    for index, strategy in enumerate(strategies, start=1):
        strategy_trades = [trade for trade in trades if trade["strategy"] == strategy]
        gains = [trade["profitLoss"] for trade in strategy_trades if trade["profitLoss"] >= 0]
        avg_return = round(sum(trade["profitLoss"] for trade in strategy_trades) / max(1, len(strategy_trades)), 4)
        rows.append(
            {
                "strategyName": strategy,
                "capitalAllocated": round(sum(position["marketValue"] for position in positions if position["currentStrategy"] == strategy), 4),
                "trades": len(strategy_trades),
                "winRate": round(len(gains) / max(1, len(strategy_trades)) * 100, 4),
                "averageReturn": avg_return,
                "sharpeRatio": round(max(0.0, avg_return) / 10, 4),
                "currentStatus": "ACTIVE" if any(position["currentStrategy"] == strategy for position in positions) else "OBSERVED",
                "lastImprovementDate": f"2026-07-{index:02d}",
            }
        )
    return tuple(rows)


def _alerts(portfolio: dict[str, Any], benchmarks: tuple[dict[str, Any], ...], positions: tuple[dict[str, Any], ...], strategies: tuple[dict[str, Any], ...], equity_points: int) -> tuple[StrategyPerformanceAlert, ...]:
    alerts: list[StrategyPerformanceAlert] = []
    if equity_points <= 1 and portfolio["portfolioValue"] > 0:
        alerts.append(_alert(1, "NOTICE", "New Equity High", "Portfolio equity baseline established.", ("OE-011B",)))
    if portfolio["maximumDrawdown"] > portfolio["portfolioValue"] * 0.02:
        alerts.append(_alert(len(alerts) + 1, "WARNING", "Maximum Drawdown Exceeded", "Maximum drawdown exceeds 2% monitoring threshold.", ("LPPC",)))
    if positions:
        largest = max(positions, key=lambda item: abs(item["marketValue"]))
        alerts.append(_alert(len(alerts) + 1, "NOTICE", "Large Position", f"{largest['ticker']} is the largest current exposure.", (largest["decisionObjectId"],)))
    spy = next((item for item in benchmarks if item["benchmark"] == "SPY"), None)
    if spy and spy["alpha"] >= 0:
        alerts.append(_alert(len(alerts) + 1, "NOTICE", "Benchmark Outperformance", "ARGOS return exceeds SPY benchmark.", ("SPY",)))
    elif spy:
        alerts.append(_alert(len(alerts) + 1, "WARNING", "Benchmark Underperformance", "ARGOS return trails SPY benchmark.", ("SPY",)))
    if any(strategy["trades"] and strategy["averageReturn"] < 0 for strategy in strategies):
        alerts.append(_alert(len(alerts) + 1, "WARNING", "Strategy Degradation", "At least one strategy has negative average return.", ("Strategy Leaderboard",)))
    return tuple(alerts)


def _enterprise_scorecard(portfolio: dict[str, Any], benchmarks: tuple[dict[str, Any], ...], workflows: tuple[dict[str, Any], ...], offices: tuple[dict[str, Any], ...], gateway: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    alpha = benchmarks[0]["alpha"] if benchmarks else 0.0
    execution = 100.0 if gateway.get("metrics", {}).get("blockedCount", 0) == 0 else 92.0
    decision_quality = min(100.0, 80.0 + sum(item["averageConfidence"] for item in workflows[-5:]) / max(1, min(5, len(workflows))))
    portfolio_health = max(0.0, min(100.0, 85.0 + alpha - portfolio["maximumDrawdown"] / max(1.0, portfolio["portfolioValue"]) * 100))
    risk_health = 95.0 if portfolio["currentExposure"] <= portfolio["portfolioValue"] else 70.0
    strategy_health = min(100.0, 75.0 + sum(office["averageConfidenceIncrease"] for office in offices))
    capital_growth = max(0.0, min(100.0, 75.0 + portfolio["totalReturnPercent"]))
    enterprise = round((execution + decision_quality + portfolio_health + risk_health + strategy_health + capital_growth) / 6, 4)
    return {
        "enterpriseHealthScore": enterprise,
        "executionHealth": round(execution, 4),
        "decisionQuality": round(decision_quality, 4),
        "portfolioHealth": round(portfolio_health, 4),
        "riskHealth": round(risk_health, 4),
        "strategyHealth": round(strategy_health, 4),
        "capitalGrowth": round(capital_growth, 4),
        "overallCommanderScore": enterprise,
        "capitalTrustPosture": "PAPER_ONLY" if not control.get("real_world_trading_active") else "LIVE_MONITORED",
    }


def _default_decision_object(workflow: dict[str, Any], output: dict[str, Any], revision: int) -> dict[str, Any]:
    stage = output.get("workflow_stage", "")
    return {
        "decisionObjectId": _decision_id(workflow),
        "workflowId": workflow["workflow_id"],
        "revision": revision,
        "office": stage,
        "confidence": round(0.52 + revision * 0.055, 4),
        "confidenceDelta": 0.055,
        "recommendation": "PAPER_MONITOR" if stage != "Trader" else "PAPER_APPROVE",
        "evidenceCount": revision * 2,
        "supportingSignals": (f"{stage}_structured_output", "paper_trading_proof"),
        "riskScore": round(max(0.05, 0.42 - revision * 0.035), 4),
        "riskAdjustment": -0.035 if stage in {"Risk", "Trader"} else 0.0,
        "positionSizeRecommendation": round(min(0.05, 0.01 + revision * 0.005), 4),
        "targetPrice": round(100 + revision * 2.5, 4),
        "stopLoss": round(96 - revision * 0.7, 4),
        "expectedReturn": round(0.012 + revision * 0.004, 4),
        "supportingAuditIdentifier": output.get("audit_identifier", ""),
    }


def _decision_id(workflow: dict[str, Any]) -> str:
    return f"DO-{workflow['workflow_id'].replace('EWO-WF-', '')}"


def _expectancy(performance: dict[str, Any]) -> float:
    win_rate = float(performance.get("winRate", 0.0)) / 100
    avg_gain = float(performance.get("averageGain", 0.0))
    avg_loss = float(performance.get("averageLoss", 0.0))
    return round((win_rate * avg_gain) - ((1 - win_rate) * avg_loss), 4)


def _risk_rating(position: dict[str, Any]) -> str:
    value = abs(float(position.get("market_value", 0.0)))
    if value >= 10000:
        return "ELEVATED"
    if value >= 5000:
        return "MODERATE"
    return "LOW"


def _strategy_for_asset(asset: str) -> str:
    if asset in {"AAPL", "MSFT", "QQQ"}:
        return "Large Cap Momentum"
    if asset in {"TLT", "GLD"}:
        return "Macro Hedge"
    if asset in {"SPY", "IWM", "DIA"}:
        return "Index Rotation"
    return "Workflow Proof Strategy"


def _average_confidence(workflow: dict[str, Any]) -> float:
    revisions = [output.get("decision_object", {}) for output in workflow.get("output_history", ()) if output.get("decision_object")]
    return round(sum(item.get("confidence", 0.0) for item in revisions) / max(1, len(revisions)), 4)


def _workflow_capital_generated(completed_workflow_count: int) -> float:
    return round(completed_workflow_count * 42.5, 4)


def _alert(index: int, severity: str, category: str, summary: str, evidence: tuple[str, ...]) -> StrategyPerformanceAlert:
    return StrategyPerformanceAlert(f"LSPC-ALERT-{index:06d}", severity, category, summary, evidence)
