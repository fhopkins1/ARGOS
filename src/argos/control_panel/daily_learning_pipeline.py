from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class DailyLearningRecord:
    learningSessionId: str
    tradingDate: str
    workflowCount: int
    decisionObjectCount: int
    performanceTruthCount: int
    historianObservations: int
    recommendationsGenerated: int
    recommendationsValidated: int
    laboratoryExperiments: int
    promptCandidates: int
    strategyCandidates: int
    commanderReviews: int
    approvedPromotions: int
    rejectedPromotions: int
    enterpriseCapabilityChange: float
    knowledgeGrowth: int
    confidenceGrowth: float
    creditConsumption: float
    runtimeStatistics: dict[str, Any]
    lessonsLearned: tuple[str, ...]
    outstandingQuestions: tuple[str, ...]
    commanderSummary: str


class DailyEnterpriseLearningPipeline:
    """Deterministic coordinator for the daily ARGOS learning lifecycle."""

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        workflow_runtime_monitor: dict[str, Any],
        performance_truth: dict[str, Any],
        historian_recommendation_engine: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        decision_laboratory: dict[str, Any],
        prompt_evolution_engine: dict[str, Any],
        market_context_engine: dict[str, Any],
        strategy_performance: dict[str, Any],
        academy_metrics: dict[str, Any] | None = None,
        costs: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        costs = costs or {}
        academy_metrics = academy_metrics or {}
        record = self._record(
            timestamp_utc,
            workflow_runtime_monitor,
            performance_truth,
            historian_recommendation_engine,
            enterprise_learning_engine,
            decision_laboratory,
            prompt_evolution_engine,
            market_context_engine,
            strategy_performance,
            costs,
        )
        backlog = self._improvement_backlog(historian_recommendation_engine, enterprise_learning_engine, prompt_evolution_engine, market_context_engine)
        capability = self._capability_index(record, enterprise_learning_engine, prompt_evolution_engine, market_context_engine)
        knowledge = self._knowledge_metrics(record, historian_recommendation_engine, enterprise_learning_engine, prompt_evolution_engine, market_context_engine)
        briefing = self._commander_briefing(record, backlog, capability, knowledge)
        return {
            "pipelineName": "Daily Enterprise Learning Pipeline",
            "engineeringOrder": "EO-F",
            "constitutionalMission": "Ensure that every market day leaves ARGOS wiser, more disciplined, and more capable than the day before.",
            "constitutionalQuestion": "How does today's experience improve tomorrow's enterprise?",
            "constitutionalMode": "LEARNING_ORCHESTRATION_ONLY",
            "lawVII": {
                "executesWorkflows": False,
                "workflowTokenOwnership": "NEVER",
                "tradesSecurities": False,
                "brokerAccess": "BLOCKED",
                "autonomousProductionDeployment": "BLOCKED",
                "promptMutation": "BLOCKED",
                "strategyMutation": "BLOCKED",
                "commanderOverride": "FORBIDDEN",
            },
            "dailyLearningRecords": (asdict(record),),
            "activeDailyLearningRecord": asdict(record),
            "learningTimeline": self._timeline(record),
            "learningOrchestrator": {
                "collectObservations": enterprise_learning_engine.get("observationCount", 0),
                "aggregateEvidence": len(historian_recommendation_engine.get("historicalPatternDatabase", ())),
                "prioritizeRecommendations": len(backlog),
                "queueLaboratoryExperiments": len(self._validation_queue(enterprise_learning_engine, historian_recommendation_engine, prompt_evolution_engine)),
                "prepareCommanderReviewPackages": record.commanderReviews,
                "archiveCompletedLearningSessions": 1,
                "deterministic": True,
            },
            "improvementBacklog": backlog,
            "recommendationQueue": self._recommendation_queue(historian_recommendation_engine, enterprise_learning_engine),
            "validationQueue": self._validation_queue(enterprise_learning_engine, historian_recommendation_engine, prompt_evolution_engine),
            "promotionQueue": self._promotion_queue(prompt_evolution_engine),
            "enterpriseCapabilityIndex": capability,
            "knowledgeGrowthMetrics": knowledge,
            "learningVelocity": {
                "observations": enterprise_learning_engine.get("metrics", {}).get("observationsToday", 0),
                "recommendations": record.recommendationsGenerated,
                "lessons": len(record.lessonsLearned),
                "velocityScore": record.workflowCount + record.recommendationsGenerated + len(record.lessonsLearned),
            },
            "commanderBriefing": briefing,
            "academyHandoff": self._academy_handoff(record, historian_recommendation_engine, enterprise_learning_engine, academy_metrics),
            "longTermEnterpriseMemory": {
                "dailyLearningRecords": 1,
                "weeklyReports": 0,
                "monthlyReports": 0,
                "quarterlyReports": 0,
                "annualReports": 0,
                "capabilityHistory": (capability,),
                "learningVelocityHistory": (),
                "recommendationHistory": tuple(item.get("recommendationId", "") for item in self._recommendation_queue(historian_recommendation_engine, enterprise_learning_engine)),
                "promptHistory": tuple(item.get("promptId", "") for item in prompt_evolution_engine.get("promptRepository", ())),
                "strategyHistory": tuple(item.get("strategyName", "") for item in strategy_performance.get("strategyLeaderboard", ())),
                "doctrineHistory": tuple(record.lessonsLearned),
                "commanderDecisions": (),
            },
            "historicalReports": {
                "daily": briefing,
                "weekly": "Awaiting additional daily records.",
                "monthly": "Awaiting additional daily records.",
            },
            "pipelineDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "productionChangesDeployed": 0,
                "commanderSovereigntyPreserved": True,
                "auditEventCount": audit_event_count,
                "historicalReplayReady": True,
            },
            "internalStatistics": {
                "componentCount": 10,
                "recordsProduced": 1,
                "backlogItems": len(backlog),
                "validationItems": len(self._validation_queue(enterprise_learning_engine, historian_recommendation_engine, prompt_evolution_engine)),
                "promotionItems": len(self._promotion_queue(prompt_evolution_engine)),
            },
            "performanceLogs": (
                "Daily learning pipeline snapshot generated without API calls.",
                "Learning orchestration remains advisory and Commander gated.",
            ),
        }

    def _record(
        self,
        timestamp_utc: str,
        workflow_runtime_monitor: dict[str, Any],
        performance_truth: dict[str, Any],
        historian_recommendation_engine: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        decision_laboratory: dict[str, Any],
        prompt_evolution_engine: dict[str, Any],
        market_context_engine: dict[str, Any],
        strategy_performance: dict[str, Any],
        costs: dict[str, Any],
    ) -> DailyLearningRecord:
        date = timestamp_utc[:10] if timestamp_utc else datetime.now(UTC).date().isoformat()
        workflows = workflow_runtime_monitor.get("metrics", {}).get("completedWorkflows", len(workflow_runtime_monitor.get("recentCompletedWorkflows", ())))
        decisions = len(strategy_performance.get("decisionObjectEvolution", ()))
        truth_count = len(performance_truth.get("orderLedger", ())) + len(performance_truth.get("tradeLedger", ())) + len(performance_truth.get("portfolioLedger", ()))
        historian_recs = len(historian_recommendation_engine.get("recommendationDatabase", ()))
        learning_recs = len(enterprise_learning_engine.get("recommendations", ()))
        prompt_candidates = len(prompt_evolution_engine.get("promptImprovementCandidates", ()))
        lessons = tuple(item.get("lessonTitle", "") for item in historian_recommendation_engine.get("institutionalLessonLibrary", ()) if item.get("lessonTitle"))
        questions = tuple(item.get("title", "") for item in enterprise_learning_engine.get("knowledgeGaps", ())) + tuple(item.get("title", "") for item in historian_recommendation_engine.get("knowledgeGapReports", ()))
        return DailyLearningRecord(
            learningSessionId=f"DLP-{date.replace('-', '')}",
            tradingDate=date,
            workflowCount=int(workflows),
            decisionObjectCount=decisions,
            performanceTruthCount=truth_count,
            historianObservations=len(historian_recommendation_engine.get("historicalPatternDatabase", ())),
            recommendationsGenerated=historian_recs + learning_recs,
            recommendationsValidated=len(decision_laboratory.get("performanceComparisons", ())),
            laboratoryExperiments=len(decision_laboratory.get("experiments", ())),
            promptCandidates=prompt_candidates,
            strategyCandidates=0,
            commanderReviews=historian_recs + learning_recs + prompt_candidates,
            approvedPromotions=0,
            rejectedPromotions=0,
            enterpriseCapabilityChange=round(float(enterprise_learning_engine.get("metrics", {}).get("capabilityGrowth", 62)) - 62, 2),
            knowledgeGrowth=truth_count + decisions + len(lessons) + len(market_context_engine.get("marketContextRepository", ())),
            confidenceGrowth=round(float(enterprise_learning_engine.get("metrics", {}).get("averageConfidence", 0.0) or 0.0), 2),
            creditConsumption=round(float(costs.get("today_api_credits_usd", 0.0) or 0.0), 4),
            runtimeStatistics={
                "timelineEvents": workflow_runtime_monitor.get("metrics", {}).get("timelineEventCount", 0),
                "activeWorkflows": workflow_runtime_monitor.get("metrics", {}).get("activeWorkflows", 0),
                "commanderAlerts": workflow_runtime_monitor.get("metrics", {}).get("commanderAlertCount", 0),
            },
            lessonsLearned=lessons or ("Awaiting accumulated institutional lessons.",),
            outstandingQuestions=questions or ("No outstanding learning questions.",),
            commanderSummary="Daily learning record prepared for Commander review. No production changes are authorized by the pipeline.",
        )

    def _timeline(self, record: DailyLearningRecord) -> tuple[dict[str, Any], ...]:
        stages = (
            ("Market Open", record.workflowCount >= 0),
            ("Workflow Creation", record.workflowCount > 0),
            ("Decision Objects", record.decisionObjectCount > 0),
            ("Performance Truth", record.performanceTruthCount > 0),
            ("Historical Analysis", record.historianObservations > 0),
            ("Recommendation Generation", record.recommendationsGenerated > 0),
            ("Laboratory Validation", record.recommendationsValidated > 0),
            ("Prompt Candidates", record.promptCandidates > 0),
            ("Strategy Candidates", record.strategyCandidates > 0),
            ("Academy Review", len(record.lessonsLearned) > 0),
            ("Commander Review", record.commanderReviews > 0),
            ("Approved Improvements", record.approvedPromotions > 0),
            ("Enterprise Growth", record.enterpriseCapabilityChange > 0),
        )
        return tuple({"stage": stage, "status": "COMPLETE" if complete else "QUEUED", "replayable": True} for stage, complete in stages)

    def _improvement_backlog(self, historian: dict[str, Any], learning: dict[str, Any], prompt: dict[str, Any], market: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        items: list[dict[str, Any]] = []
        for item in learning.get("improvementBacklog", ()):
            items.append({"source": "Enterprise Learning Engine", "category": item.get("category", "Doctrine Improvements"), "title": item.get("title", ""), "priority": item.get("priority", "MEDIUM"), "status": item.get("productionStatus", "BLOCKED")})
        for item in historian.get("recommendationDatabase", ()):
            items.append({"source": "Historian", "category": ", ".join(item.get("category", ())), "title": item.get("summary", ""), "priority": item.get("priority", "Medium"), "status": item.get("productionStatus", "BLOCKED")})
        for item in prompt.get("promptImprovementCandidates", ()):
            items.append({"source": "Prompt Evolution", "category": "Prompt Improvements", "title": item.get("summary", ""), "priority": "Medium", "status": item.get("productionStatus", "BLOCKED")})
        for item in market.get("latestMarketContext", {}).get("relatedNews", ()):
            items.append({"source": "Market Context", "category": "Market Context Expansion", "title": item.get("summary", ""), "priority": item.get("estimatedImportance", "LOW"), "status": "CONTEXT_ONLY"})
        return tuple({"rank": index, **item} for index, item in enumerate(items[:20], start=1))

    def _recommendation_queue(self, historian: dict[str, Any], learning: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        rows = []
        for item in historian.get("recommendationDatabase", ()):
            rows.append({"recommendationId": item.get("recommendationId", ""), "source": "Historian", "title": item.get("summary", ""), "laboratoryStatus": item.get("laboratoryStatus", ""), "commanderStatus": item.get("commanderStatus", ""), "productionStatus": item.get("productionStatus", "")})
        for item in learning.get("recommendations", ()):
            rows.append({"recommendationId": item.get("recommendationId", ""), "source": "Enterprise Learning", "title": item.get("title", ""), "laboratoryStatus": item.get("laboratoryStatus", ""), "commanderStatus": item.get("commanderApprovalStatus", ""), "productionStatus": item.get("productionStatus", "")})
        return tuple(rows)

    def _validation_queue(self, learning: dict[str, Any], historian: dict[str, Any], prompt: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        rows = []
        for item in self._recommendation_queue(historian, learning):
            rows.append({"validationId": f"DLP-VAL-{len(rows) + 1:06d}", **item, "validationStatus": "QUEUED_FOR_LABORATORY"})
        for item in prompt.get("laboratoryValidationQueue", ()):
            rows.append({"validationId": f"DLP-VAL-{len(rows) + 1:06d}", "recommendationId": item.get("improvementId", ""), "source": "Prompt Evolution", "title": item.get("relatedPrompt", ""), "laboratoryStatus": item.get("laboratoryStatus", ""), "productionStatus": item.get("productionStatus", ""), "validationStatus": "QUEUED_FOR_PROMPT_REPLAY"})
        return tuple(rows)

    def _promotion_queue(self, prompt: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        return tuple(
            {
                "promotionId": f"DLP-PROMO-{index:06d}",
                "candidateId": item.get("improvementId", ""),
                "candidateType": "Prompt Candidate",
                "commanderStatus": item.get("commanderStatus", ""),
                "productionStatus": item.get("productionStatus", ""),
                "automaticDeployment": False,
            }
            for index, item in enumerate(prompt.get("promptImprovementCandidates", ()), start=1)
        )

    def _capability_index(self, record: DailyLearningRecord, learning: dict[str, Any], prompt: dict[str, Any], market: dict[str, Any]) -> dict[str, Any]:
        learning_metrics = learning.get("metrics", {})
        prompt_metrics = prompt.get("performanceDashboard", {})
        context = market.get("latestMarketContext", {})
        dimensions = {
            "decisionQuality": min(100, 72 + record.decisionObjectCount * 2),
            "promptQuality": min(100, 70 + prompt_metrics.get("promptCount", 0) * 2 + prompt_metrics.get("candidatePrompts", 0)),
            "strategyQuality": min(100, 70 + record.strategyCandidates * 3),
            "knowledgeDepth": min(100, 64 + record.knowledgeGrowth * 2),
            "riskDiscipline": 86,
            "confidenceAccuracy": round(float(learning_metrics.get("averageConfidence", 0.72) or 0.72) * 100, 2),
            "learningVelocity": min(100, 60 + record.recommendationsGenerated + len(record.lessonsLearned)),
            "marketUnderstanding": round(float(context.get("confidence", 0.72) or 0.72) * 100, 2),
            "executionConsistency": 84,
            "institutionalMaturity": learning_metrics.get("institutionalMaturity", 55),
        }
        score = round(sum(float(value) for value in dimensions.values()) / len(dimensions), 2)
        return {"score": score, "dimensions": dimensions, "trend": "IMPROVING" if record.enterpriseCapabilityChange > 0 else "BASELINE"}

    def _knowledge_metrics(self, record: DailyLearningRecord, historian: dict[str, Any], learning: dict[str, Any], prompt: dict[str, Any], market: dict[str, Any]) -> dict[str, Any]:
        return {
            "decisionObjects": record.decisionObjectCount,
            "truthRecords": record.performanceTruthCount,
            "observations": learning.get("observationCount", 0),
            "recommendations": record.recommendationsGenerated,
            "validatedLessons": len(historian.get("institutionalLessonLibrary", ())),
            "promptVersions": prompt.get("performanceDashboard", {}).get("immutableVersionCount", 0),
            "strategyVersions": record.strategyCandidates,
            "laboratoryExperiments": record.laboratoryExperiments,
            "commanderApprovals": record.approvedPromotions,
            "institutionalDoctrine": len(record.lessonsLearned),
            "marketContextSnapshots": len(market.get("marketContextRepository", ())),
            "knowledgeCoverage": learning.get("metrics", {}).get("knowledgeCoverage", 0),
        }

    def _commander_briefing(self, record: DailyLearningRecord, backlog: tuple[dict[str, Any], ...], capability: dict[str, Any], knowledge: dict[str, Any]) -> dict[str, Any]:
        return {
            "briefingId": f"CMD-BRIEF-{record.learningSessionId}",
            "enterpriseSummary": record.commanderSummary,
            "tradingSummary": f"{record.workflowCount} workflows, {record.decisionObjectCount} Decision Objects, {record.performanceTruthCount} truth records.",
            "learningSummary": f"{record.recommendationsGenerated} recommendations and {len(record.lessonsLearned)} lessons captured.",
            "recommendations": tuple(item.get("title", "") for item in backlog[:8]),
            "validatedImprovements": record.recommendationsValidated,
            "rejectedCandidates": record.rejectedPromotions,
            "knowledgeGaps": record.outstandingQuestions,
            "capabilityGrowth": capability,
            "enterpriseMaturity": capability["dimensions"]["institutionalMaturity"],
            "creditConsumption": record.creditConsumption,
            "outstandingDecisions": tuple(item.get("title", "") for item in backlog if item.get("status") != "CONTEXT_ONLY")[:8],
            "commanderActionItems": ("Review queued recommendations.", "Authorize or reject validated candidates.", "Confirm Academy research priorities."),
        }

    def _academy_handoff(self, record: DailyLearningRecord, historian: dict[str, Any], learning: dict[str, Any], academy_metrics: dict[str, Any]) -> dict[str, Any]:
        return {
            "trainingPriorities": tuple(record.outstandingQuestions[:5]),
            "researchInitiatives": tuple(item.get("title", "") for item in historian.get("knowledgeGapReports", ()))[:5],
            "knowledgeAcquisition": tuple(item.get("title", "") for item in learning.get("knowledgeGaps", ()))[:5],
            "promptEducation": tuple(item for item in record.lessonsLearned if "Prompt" in item or "prompt" in item),
            "strategyEducation": tuple(item for item in record.lessonsLearned if "Strategy" in item or "strategy" in item),
            "institutionalDoctrine": record.lessonsLearned,
            "academyMetrics": academy_metrics,
            "handoffStatus": "READY_FOR_ACADEMY_REVIEW",
        }
