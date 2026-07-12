"""Commander Daily Review Workspace for ARGOS daily governance."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


WORKSPACE_SECTIONS = (
    "Morning Readiness",
    "Enterprise Operations",
    "Commander Approval Queue",
    "Enterprise Learning",
    "End-of-Day Review",
)


@dataclass(frozen=True)
class CommanderJournalEntry:
    journalId: str
    timestamp: str
    category: str
    entry: str
    immutable: bool
    auditReference: str


class CommanderDailyReviewWorkspace:
    """Aggregate daily Commander context without executing enterprise actions."""

    def __init__(self) -> None:
        self._journal: list[CommanderJournalEntry] = []
        self._daily_reports: list[dict[str, Any]] = []
        self._last_snapshot_key: tuple[Any, ...] | None = None
        self._last_snapshot: dict[str, Any] | None = None

    def add_journal_entry(self, *, timestamp_utc: str, category: str, entry: str) -> dict[str, Any]:
        clean_entry = " ".join(str(entry).split())
        clean_category = str(category or "Daily Observations").strip() or "Daily Observations"
        journal_entry = CommanderJournalEntry(
            journalId=f"CDRW-JOURNAL-{len(self._journal) + 1:06d}",
            timestamp=timestamp_utc,
            category=clean_category,
            entry=clean_entry,
            immutable=True,
            auditReference=f"AE-CDRW-JOURNAL-{len(self._journal) + 1:06d}",
        )
        self._journal.append(journal_entry)
        return asdict(journal_entry)

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        control: dict[str, Any],
        costs: dict[str, Any],
        workflow_runtime_monitor: dict[str, Any],
        performance_truth: dict[str, Any],
        strategy_performance: dict[str, Any],
        historian_recommendation_engine: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        decision_laboratory: dict[str, Any],
        prompt_evolution_engine: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        prompt_package_manager: dict[str, Any],
        market_context_engine: dict[str, Any],
        enterprise_configuration_registry: dict[str, Any],
        credit_governor: dict[str, Any],
        enterprise_health_monitor: dict[str, Any],
        enterprise_failure_recovery: dict[str, Any],
        decision_object_quality: dict[str, Any],
        enterprise_benchmark_engine: dict[str, Any],
        api_runtime_monitor: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        snapshot_key = (
            len(self._journal),
            workflow_runtime_monitor.get("metrics", {}).get("workflowCount", 0),
            workflow_runtime_monitor.get("metrics", {}).get("completedWorkflows", 0),
            decision_object_quality.get("internalDiagnostics", {}).get("qualityReportCount", 0),
            enterprise_benchmark_engine.get("benchmarkDiagnostics", {}).get("benchmarkSnapshotCount", 0),
        )
        if self._last_snapshot_key == snapshot_key and self._last_snapshot is not None:
            return self._last_snapshot
        daily_report = self._daily_report(
            timestamp_utc,
            workflow_runtime_monitor,
            performance_truth,
            enterprise_learning_engine,
            enterprise_health_monitor,
            enterprise_failure_recovery,
            decision_object_quality,
        )
        if not self._daily_reports or self._daily_reports[-1]["reportId"] != daily_report["reportId"]:
            self._daily_reports.append(daily_report)
        approval_queue = self._approval_queue(
            historian_recommendation_engine,
            enterprise_learning_engine,
            decision_laboratory,
            prompt_evolution_engine,
            strategy_package_manager,
            enterprise_configuration_registry,
        )
        scorecard = self._enterprise_scorecard(
            enterprise_health_monitor,
            strategy_performance,
            enterprise_learning_engine,
            decision_object_quality,
            prompt_package_manager,
            strategy_package_manager,
            credit_governor,
            workflow_runtime_monitor,
            market_context_engine,
            enterprise_benchmark_engine,
        )
        snapshot = {
            "workspaceName": "Commander Daily Review Workspace",
            "engineeringOrder": "EO-O",
            "constitutionalMission": "Provide the Commander with one complete operational workspace from which the enterprise can be understood, directed, improved, and approved.",
            "constitutionalQuestion": "If I had only ten minutes each day to operate ARGOS, what would I need to know?",
            "constitutionalMode": "COMMANDER_OPERATING_TABLE_ONLY",
            "workspaceSections": WORKSPACE_SECTIONS,
            "morningReadiness": self._morning_readiness(control, costs, enterprise_health_monitor, workflow_runtime_monitor, market_context_engine, prompt_package_manager, strategy_package_manager, credit_governor),
            "enterpriseOperations": self._enterprise_operations(enterprise_health_monitor, workflow_runtime_monitor, strategy_performance, decision_object_quality, costs, api_runtime_monitor, market_context_engine),
            "commanderApprovalQueue": approval_queue,
            "enterpriseLearning": self._enterprise_learning(enterprise_learning_engine, historian_recommendation_engine, decision_object_quality),
            "endOfDayReview": daily_report,
            "enterpriseScorecard": scorecard,
            "commanderJournal": tuple(asdict(item) for item in self._journal[-30:]),
            "enterpriseTimeline": self._enterprise_timeline(timestamp_utc, workflow_runtime_monitor, performance_truth, historian_recommendation_engine, approval_queue),
            "priorityPanel": self._priority_panel(enterprise_health_monitor, enterprise_failure_recovery, approval_queue, decision_object_quality),
            "commanderInsights": self._commander_insights(scorecard, decision_object_quality, enterprise_learning_engine, market_context_engine, enterprise_benchmark_engine),
            "reviewChecklist": {
                "morning": ("Review Enterprise Health", "Review Market Context", "Review Alerts", "Review Strategy", "Confirm Readiness"),
                "evening": ("Review Performance", "Review Learning", "Review Recommendations", "Approve Promotions", "Record Journal", "Prepare Tomorrow"),
            },
            "dailyReportsArchive": tuple(self._daily_reports[-20:]),
            "engineeringModeLinks": (
                "Health Diagnostics",
                "Workflow Diagnostics",
                "Provider Diagnostics",
                "Laboratory Reports",
                "Configuration Manager",
                "Prompt Repository",
                "Strategy Repository",
                "Recovery History",
                "Quality Reports",
                "Audit Records",
            ),
            "lawVII": {
                "executesWorkflows": False,
                "ownsWorkflowTokens": False,
                "makesInvestmentDecisions": False,
                "automaticallyApprovesPromotions": False,
                "modifiesDoctrineAutonomously": False,
                "overridesConstitutionalGovernance": False,
                "responsibility": "IMPROVES_COMMANDER_EFFECTIVENESS_ONLY",
            },
            "internalDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "tradesPlaced": 0,
                "approvalQueueCount": len(approval_queue),
                "journalEntryCount": len(self._journal),
                "dailyReportCount": len(self._daily_reports),
                "auditEventCountObserved": audit_event_count,
            },
        }
        self._last_snapshot_key = snapshot_key
        self._last_snapshot = snapshot
        return snapshot

    def _morning_readiness(self, control: dict[str, Any], costs: dict[str, Any], health: dict[str, Any], workflow: dict[str, Any], market: dict[str, Any], prompts: dict[str, Any], strategies: dict[str, Any], credit: dict[str, Any]) -> dict[str, Any]:
        latest_market = market.get("latestMarketContext", {}) if isinstance(market.get("latestMarketContext"), dict) else {}
        return {
            "enterpriseHealth": health.get("status", "Unknown"),
            "enterpriseHealthScore": health.get("enterpriseHealthScore", 0),
            "workflowSystem": workflow.get("tokenIntegrity", {}).get("status", "VALID"),
            "marketDataProviders": health.get("commanderHealthDashboard", {}).get("providerHealth", "Healthy"),
            "creditBudget": costs.get("budget_status", credit.get("budgetStatus", "GREEN")),
            "paperTradingStatus": "Active" if control.get("paper_trading_active") else "Inactive",
            "activePromptPackage": (prompts.get("activePackages") or [{}])[0].get("packageId", "Baseline"),
            "activeStrategyPackage": (strategies.get("activePackages") or [{}])[0].get("packageId", "Baseline"),
            "marketRegime": latest_market.get("marketRegime", "UNKNOWN"),
            "openAlerts": health.get("commanderHealthDashboard", {}).get("currentAlerts", 0),
            "todaysEconomicEvents": ("Economic calendar unavailable in local paper mode",),
            "tradingCalendar": "Paper trading calendar active",
            "readiness": "Ready" if health.get("status") == "Healthy" else "Review Required",
        }

    def _enterprise_operations(self, health: dict[str, Any], workflow: dict[str, Any], strategy: dict[str, Any], quality: dict[str, Any], costs: dict[str, Any], api: dict[str, Any], market: dict[str, Any]) -> dict[str, Any]:
        active = workflow.get("activeWorkflow") or {}
        return {
            "enterpriseHealthScore": health.get("enterpriseHealthScore", 0),
            "workflowCount": workflow.get("metrics", {}).get("workflowCount", 0),
            "activeWorkflow": active.get("workflowIdentifier", "None"),
            "workflowQueue": workflow.get("metrics", {}).get("queuedWorkflows", 0),
            "currentOffice": active.get("currentOwner", "None"),
            "decisionObjectQuality": quality.get("overallQualityScore", 0),
            "creditBurn": costs.get("session_api_credits_usd", 0),
            "apiUsage": api.get("metrics", {}).get("apiCallsLogged", 0),
            "marketContextStatus": (market.get("latestMarketContext") or {}).get("validationStatus", "Standing By"),
            "providerHealth": health.get("commanderHealthDashboard", {}).get("providerHealth", "Healthy"),
            "portfolioStatus": strategy.get("enterpriseScorecard", {}).get("capitalTrustPosture", "PAPER_ONLY"),
            "enterpriseCapability": strategy.get("enterpriseScorecard", {}).get("decisionQuality", 0),
        }

    def _approval_queue(self, historian: dict[str, Any], learning: dict[str, Any], lab: dict[str, Any], prompt_evolution: dict[str, Any], strategies: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        queue: list[dict[str, Any]] = []
        for item in prompt_evolution.get("promptImprovementCandidates", ())[:3]:
            queue.append(_approval("Prompt Promotion", item.get("summary", "Prompt improvement candidate"), item.get("expectedBenefit", "Improve prompt quality"), item.get("confidence", 0.75), "Medium"))
        for item in strategies.get("promotionQueue", ())[:3]:
            queue.append(_approval("Strategy Promotion", item.get("strategyName", "Strategy package review"), item.get("expectedBenefit", "Improve strategy quality"), 0.8, "Medium"))
        for item in config.get("promotionQueue", ())[:3]:
            queue.append(_approval("Configuration Change", item.get("configurationId", "Configuration review"), item.get("commanderApproval", "Commander approval required"), 0.9, "Low"))
        for item in lab.get("experiments", ())[:3]:
            queue.append(_approval("Laboratory Validation", item.get("experiment_id", "Laboratory validation"), "Review experiment before production use", 0.75, "Medium"))
        for item in historian.get("recommendationDatabase", ())[:3]:
            queue.append(_approval("Historian Recommendation", item.get("summary", "Historian recommendation"), item.get("detailedExplanation", "Review historical evidence"), item.get("confidence", 0.7), item.get("priority", "Medium")))
        for item in learning.get("recommendations", ())[:3]:
            queue.append(_approval("Enterprise Learning", item.get("title", "Learning recommendation"), item.get("expectedBenefit", "Institutional improvement"), item.get("confidence", 0.7), item.get("priority", "Medium")))
        if not queue:
            queue.append(_approval("Daily Review", "No production approvals pending", "Commander may continue monitoring.", 1.0, "Low"))
        return tuple(dict(item, approvalId=f"CDRW-APPROVAL-{index:06d}") for index, item in enumerate(queue, start=1))

    def _enterprise_learning(self, learning: dict[str, Any], historian: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
        metrics = learning.get("metrics", {})
        return {
            "recommendationsGenerated": metrics.get("recommendationsGenerated", len(learning.get("recommendations", ()))),
            "validatedImprovements": metrics.get("validatedImprovements", 0),
            "rejectedImprovements": metrics.get("rejectedImprovements", 0),
            "knowledgeGrowth": metrics.get("knowledgeGrowth", 0),
            "learningVelocity": metrics.get("learningVelocity", 0),
            "capabilityGrowth": metrics.get("capabilityGrowth", 0),
            "historianLessons": len(historian.get("institutionalLessonLibrary", ())),
            "academyProgress": quality.get("academyBridgeFeed", {}).get("knowledgeCoverageTrend", "Stable"),
            "qualityTrends": quality.get("trendAnalysis", {}).get("knowledgeCoverageTrend", "Stable"),
            "decisionObjectQuality": quality.get("overallQualityScore", 0),
        }

    def _enterprise_scorecard(self, health: dict[str, Any], strategy: dict[str, Any], learning: dict[str, Any], quality: dict[str, Any], prompts: dict[str, Any], strategies: dict[str, Any], credit: dict[str, Any], workflow: dict[str, Any], market: dict[str, Any], benchmark: dict[str, Any]) -> dict[str, Any]:
        scorecard = strategy.get("enterpriseScorecard", {})
        return {
            "enterpriseHealth": health.get("enterpriseHealthScore", 0),
            "enterpriseCapability": scorecard.get("decisionQuality", 0),
            "portfolioPerformance": scorecard.get("totalReturn", 0),
            "decisionQuality": quality.get("overallQualityScore", 0),
            "knowledgeGrowth": learning.get("metrics", {}).get("knowledgeGrowth", 0),
            "promptQuality": 100 if prompts.get("internalDiagnostics", {}).get("invalidActivePackages", 0) == 0 else 70,
            "strategyQuality": 100 if strategies.get("internalDiagnostics", {}).get("invalidActivePackages", 0) == 0 else 70,
            "learningVelocity": learning.get("metrics", {}).get("learningVelocity", 0),
            "creditEfficiency": credit.get("efficiency", "HIGH"),
            "workflowReliability": 100 if workflow.get("tokenIntegrity", {}).get("status") == "VALID" else 50,
            "riskDiscipline": scorecard.get("riskDiscipline", 100),
            "marketAwareness": 100 if market.get("latestMarketContext") else 85,
            "benchmarkValueAdded": benchmark.get("commanderReviewFeed", {}).get("valueAddedStatement", "Benchmark context awaiting truth."),
        }

    def _daily_report(self, timestamp: str, workflow: dict[str, Any], truth: dict[str, Any], learning: dict[str, Any], health: dict[str, Any], recovery: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
        return {
            "reportId": f"CDRW-DAILY-{timestamp[:10]}",
            "timestamp": timestamp,
            "tradingSummary": f"{len(truth.get('tradeLedger', ())) } paper trades recorded.",
            "performanceSummary": truth.get("calculations", {}).get("portfolio", {}),
            "workflowSummary": workflow.get("metrics", {}),
            "learningSummary": learning.get("metrics", {}),
            "enterpriseHealth": health.get("status", "Unknown"),
            "recommendations": len(learning.get("recommendations", ())),
            "promotions": "Commander approval required before production.",
            "failures": recovery.get("recoveryStatistics", {}).get("totalFailures", 0),
            "recoveryEvents": recovery.get("recoveryStatistics", {}).get("totalRecoveries", 0),
            "knowledgeGaps": len(learning.get("knowledgeGaps", ())),
            "commanderDecisions": len(self._journal),
            "tomorrowsPriorities": ("Review health", "Review learning", "Review approval queue"),
            "immutable": True,
        }

    def _enterprise_timeline(self, timestamp: str, workflow: dict[str, Any], truth: dict[str, Any], historian: dict[str, Any], approvals: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
        return (
            {"timestamp": timestamp, "event": "Market Open", "status": "Paper calendar ready"},
            {"timestamp": timestamp, "event": "Workflow Creation", "status": str(workflow.get("metrics", {}).get("workflowCount", 0))},
            {"timestamp": timestamp, "event": "Decision Objects", "status": str(len(workflow.get("recentCompletedWorkflows", ())))},
            {"timestamp": timestamp, "event": "Performance Truth", "status": str(len(truth.get("portfolioLedger", ())))},
            {"timestamp": timestamp, "event": "Historian", "status": str(len(historian.get("recommendationDatabase", ())))},
            {"timestamp": timestamp, "event": "Commander Decisions", "status": str(len(approvals))},
            {"timestamp": timestamp, "event": "Enterprise Growth", "status": "Tracked"},
        )

    def _priority_panel(self, health: dict[str, Any], recovery: dict[str, Any], approvals: tuple[dict[str, Any], ...], quality: dict[str, Any]) -> tuple[dict[str, str], ...]:
        priorities = [
            {"priority": "Critical", "category": "Health", "summary": "Review enterprise health alerts" if health.get("commanderHealthDashboard", {}).get("currentAlerts", 0) else "No critical health alerts"},
            {"priority": "High", "category": "Learning", "summary": f"{len(approvals)} approval queue items"},
            {"priority": "Medium", "category": "Infrastructure", "summary": recovery.get("safeEnterpriseState", {}).get("status", "SAFE")},
            {"priority": "Research", "category": "Market Context", "summary": f"Decision quality {quality.get('overallQualityScore', 0)}"},
        ]
        return tuple(priorities)

    def _commander_insights(self, scorecard: dict[str, Any], quality: dict[str, Any], learning: dict[str, Any], market: dict[str, Any], benchmark: dict[str, Any]) -> tuple[str, ...]:
        return (
            f"Decision Object quality is {quality.get('overallQualityScore', 0)} with grade {quality.get('grade', 'Unknown')}.",
            f"Enterprise health is {scorecard.get('enterpriseHealth', 0)}.",
            benchmark.get("commanderReviewFeed", {}).get("valueAddedStatement", "Benchmark context awaiting performance truth."),
            f"Knowledge coverage trend is {quality.get('trendAnalysis', {}).get('knowledgeCoverageTrend', 'Stable')}.",
            f"Learning velocity is {learning.get('metrics', {}).get('learningVelocity', 0)}.",
            f"Market regime is {(market.get('latestMarketContext') or {}).get('marketRegime', 'UNKNOWN')}.",
        )


def _approval(kind: str, summary: str, evidence: str, confidence: float, risk: str) -> dict[str, Any]:
    return {
        "type": kind,
        "summary": summary,
        "evidence": evidence,
        "confidence": round(float(confidence or 0), 4),
        "expectedBenefit": evidence,
        "risk": risk,
        "commanderActions": ("Approve", "Reject", "Request More Information", "Defer"),
    }
