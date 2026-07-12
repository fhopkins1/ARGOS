from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


RECOMMENDATION_CATEGORIES = (
    "Prompt Improvement",
    "Strategy Improvement",
    "Risk Doctrine",
    "Evidence Weighting",
    "Confidence Calibration",
    "Workflow Optimization",
    "Runtime Optimization",
    "Knowledge Acquisition",
    "Market Context Expansion",
    "Office Coordination",
    "Resource Efficiency",
    "Credit Optimization",
    "Decision Consistency",
    "Behavior Drift Correction",
    "Institutional Doctrine",
    "Capability Development",
    "Long-Term Research",
)


@dataclass(frozen=True)
class HistoricalPattern:
    patternId: str
    category: str
    summary: str
    supportingWorkflows: tuple[str, ...]
    supportingDecisionObjects: tuple[str, ...]
    supportingTruthRecords: tuple[str, ...]
    historicalFrequency: int
    historicalSuccessRate: float
    marketDiversity: int
    promptDiversity: int
    strategyDiversity: int
    evidenceStrength: str
    confidenceScore: float


@dataclass(frozen=True)
class HistorianRecommendation:
    recommendationId: str
    creationDate: str
    authorOffice: str
    category: tuple[str, ...]
    summary: str
    detailedExplanation: str
    supportingEvidence: tuple[str, ...]
    supportingWorkflows: tuple[str, ...]
    supportingDecisionObjects: tuple[str, ...]
    supportingTruthRecords: tuple[str, ...]
    historicalFrequency: int
    historicalSuccessRate: float
    estimatedEnterpriseBenefit: str
    confidenceScore: float
    priority: str
    laboratoryStatus: str
    commanderStatus: str
    productionStatus: str
    relatedPromptVersions: tuple[str, ...]
    relatedStrategyVersions: tuple[str, ...]
    relatedExperiments: tuple[str, ...]
    relatedRecommendations: tuple[str, ...]


@dataclass(frozen=True)
class InstitutionalLesson:
    lessonId: str
    lessonTitle: str
    description: str
    historicalEvidence: tuple[str, ...]
    supportingWorkflows: tuple[str, ...]
    supportingDecisionObjects: tuple[str, ...]
    supportingRecommendations: tuple[str, ...]
    confidence: float
    enterpriseValue: str
    applicableStrategies: tuple[str, ...]
    applicablePrompts: tuple[str, ...]
    applicableMarketConditions: tuple[str, ...]
    dateEstablished: str
    dateLastConfirmed: str


class HistorianRecommendationEngine:
    """Deterministic historical pattern and recommendation layer for the Historian."""

    def __init__(self, *, minimum_historical_frequency: int = 2) -> None:
        self.minimum_historical_frequency = max(2, minimum_historical_frequency)

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        workflow_runtime_monitor: dict[str, Any],
        performance_truth: dict[str, Any],
        strategy_performance: dict[str, Any],
        decision_laboratory: dict[str, Any],
        prompt_contract: dict[str, Any],
        api_runtime_monitor: dict[str, Any],
        credit_governor: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        patterns = self._patterns(performance_truth, strategy_performance, decision_laboratory, prompt_contract, api_runtime_monitor)
        recommendations = self._recommendations(timestamp_utc, patterns, prompt_contract, strategy_performance, decision_laboratory)
        lessons = self._lessons(timestamp_utc, patterns, recommendations, prompt_contract, strategy_performance)
        gaps = self._knowledge_gaps(patterns, performance_truth, decision_laboratory, prompt_contract, strategy_performance)
        metrics = self._metrics(patterns, recommendations, lessons, gaps, decision_laboratory)
        completed = tuple(workflow_runtime_monitor.get("recentCompletedWorkflows", ()))
        return {
            "engineName": "Historian Recommendation Engine",
            "engineeringOrder": "EO-B",
            "constitutionalMission": "Convert enterprise experience into actionable institutional wisdom.",
            "constitutionalMode": "ADVISORY_ONLY",
            "constitutionalQuestion": "What does history consistently teach us?",
            "lawVII": {
                "executesWorkflows": False,
                "workflowTokenOwnership": "NEVER",
                "brokerAccess": "BLOCKED",
                "tradingApiAccess": "BLOCKED",
                "productionPromptMutation": "BLOCKED",
                "productionStrategyMutation": "BLOCKED",
                "commanderOverride": "FORBIDDEN",
                "autonomousDeployment": "FORBIDDEN",
            },
            "inputs": {
                "completedWorkflows": len(completed),
                "performanceTruthRecords": len(performance_truth.get("tradeLedger", ())) + len(performance_truth.get("portfolioLedger", ())),
                "decisionObjects": len(strategy_performance.get("decisionObjectEvolution", ())),
                "promptVersions": len(prompt_contract.get("templates", ())),
                "strategyVersions": len(strategy_performance.get("strategyLeaderboard", ())),
                "laboratoryResults": len(decision_laboratory.get("performanceComparisons", ())),
                "runtimeMetrics": len(api_runtime_monitor.get("events", ())) + len(api_runtime_monitor.get("calls", ())),
                "creditPolicyEvents": len(credit_governor.get("policyEvents", ())),
                "auditEvents": audit_event_count,
            },
            "historicalPatternDatabase": tuple(asdict(item) for item in patterns),
            "recommendationDatabase": tuple(asdict(item) for item in recommendations),
            "institutionalLessonLibrary": tuple(asdict(item) for item in lessons),
            "knowledgeGapReports": gaps,
            "recommendationStatistics": metrics,
            "recommendationThresholds": {
                "minimumHistoricalFrequency": self.minimum_historical_frequency,
                "minimumConfidenceScore": 0.6,
                "isolatedEventRecommendationsAllowed": False,
                "requiresEnterpriseLearningEvaluation": True,
                "requiresLaboratoryValidation": True,
                "requiresCommanderApproval": True,
                "productionMutationAllowed": False,
            },
            "patternDetectionAlgorithms": (
                "Aggregate completed workflows by category, prompt, strategy, and outcome.",
                "Reject recommendation drafts when historical frequency is below threshold.",
                "Increase confidence with repeated outcomes, replay coverage, prompt stability, and strategy stability.",
                "Treat sparse coverage as Academy research priorities, not production changes.",
            ),
            "recommendationLifecycle": (
                "Historical Pattern",
                "Evidence Aggregation",
                "Recommendation Draft",
                "Enterprise Learning Engine",
                "Decision Laboratory",
                "Replay Validation",
                "Counterfactual Validation",
                "Commander Review",
                "Production Promotion",
            ),
            "validationHistory": tuple(decision_laboratory.get("performanceComparisons", ())),
            "commanderApprovalHistory": (),
            "promotionHistory": (),
            "internalDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "recommendationSpamGuard": "MINIMUM_HISTORICAL_FREQUENCY",
                "historianOwnsWorkflowTokens": False,
                "activeWorkflowParticipation": False,
            },
        }

    def _patterns(
        self,
        performance_truth: dict[str, Any],
        strategy_performance: dict[str, Any],
        decision_laboratory: dict[str, Any],
        prompt_contract: dict[str, Any],
        api_runtime_monitor: dict[str, Any],
    ) -> tuple[HistoricalPattern, ...]:
        workflows = tuple(item.get("workflowId", "") for item in strategy_performance.get("decisionObjectEvolution", ()))
        if not workflows:
            workflows = tuple(item.get("workflow_id", "") for item in performance_truth.get("workflowAttribution", ()))
        decision_objects = tuple(item.get("decisionObjectId", "") for item in strategy_performance.get("decisionObjectEvolution", ()))
        truth_records = tuple(
            item.get("trade_id") or item.get("valuation_id") or item.get("workflow_id", "")
            for item in tuple(performance_truth.get("tradeLedger", ())) + tuple(performance_truth.get("portfolioLedger", ()))
        )
        prompts = tuple(item.get("prompt_template_id") or item.get("promptVersion") or item.get("version", "") for item in prompt_contract.get("templates", ()))
        strategies = tuple(item.get("strategyName") or item.get("strategy_name") or "paper_momentum_baseline" for item in strategy_performance.get("strategyLeaderboard", ()))
        frequency = len(tuple(item for item in workflows if item)) or len(tuple(item for item in truth_records if item))
        success_rate = _historical_success_rate(performance_truth, strategy_performance)
        market_diversity = max(1, len(strategy_performance.get("marketBenchmarks", ())))
        patterns = [
            HistoricalPattern(
                patternId="HRE-PAT-000001",
                category="Confidence Calibration",
                summary="Decision confidence should be calibrated against repeated observed outcomes.",
                supportingWorkflows=_take(workflows, 12),
                supportingDecisionObjects=_take(decision_objects, 12),
                supportingTruthRecords=_take(truth_records, 12),
                historicalFrequency=frequency,
                historicalSuccessRate=success_rate,
                marketDiversity=market_diversity,
                promptDiversity=max(1, len(set(item for item in prompts if item))),
                strategyDiversity=max(1, len(set(item for item in strategies if item))),
                evidenceStrength=_evidence_strength(frequency),
                confidenceScore=_confidence(frequency, success_rate, len(decision_laboratory.get("workflowReplay", ())), len(decision_laboratory.get("performanceComparisons", ()))),
            ),
            HistoricalPattern(
                patternId="HRE-PAT-000002",
                category="Risk Doctrine",
                summary="Risk doctrine requires repeated validation against drawdown and position outcome history.",
                supportingWorkflows=_take(workflows, 12),
                supportingDecisionObjects=_take(decision_objects, 12),
                supportingTruthRecords=_take(truth_records, 12),
                historicalFrequency=frequency,
                historicalSuccessRate=success_rate,
                marketDiversity=market_diversity,
                promptDiversity=max(1, len(set(item for item in prompts if item))),
                strategyDiversity=max(1, len(set(item for item in strategies if item))),
                evidenceStrength=_evidence_strength(frequency),
                confidenceScore=_confidence(frequency, success_rate, len(decision_laboratory.get("workflowReplay", ())), len(decision_laboratory.get("performanceComparisons", ()))),
            ),
        ]
        if prompts:
            patterns.append(
                HistoricalPattern(
                    patternId="HRE-PAT-000003",
                    category="Prompt Improvement",
                    summary="Prompt versions are stable enough for historical comparison after repeated workflow replay.",
                    supportingWorkflows=_take(workflows, 12),
                    supportingDecisionObjects=_take(decision_objects, 12),
                    supportingTruthRecords=_take(truth_records, 12),
                    historicalFrequency=frequency,
                    historicalSuccessRate=success_rate,
                    marketDiversity=market_diversity,
                    promptDiversity=len(set(item for item in prompts if item)),
                    strategyDiversity=max(1, len(set(item for item in strategies if item))),
                    evidenceStrength=_evidence_strength(frequency),
                    confidenceScore=_confidence(frequency, success_rate, len(decision_laboratory.get("workflowReplay", ())), len(decision_laboratory.get("performanceComparisons", ()))),
                )
            )
        if strategies:
            patterns.append(
                HistoricalPattern(
                    patternId="HRE-PAT-000004",
                    category="Strategy Improvement",
                    summary="Strategy behavior can be compared across completed workflows and Performance Truth records.",
                    supportingWorkflows=_take(workflows, 12),
                    supportingDecisionObjects=_take(decision_objects, 12),
                    supportingTruthRecords=_take(truth_records, 12),
                    historicalFrequency=frequency,
                    historicalSuccessRate=success_rate,
                    marketDiversity=market_diversity,
                    promptDiversity=max(1, len(set(item for item in prompts if item))),
                    strategyDiversity=len(set(item for item in strategies if item)),
                    evidenceStrength=_evidence_strength(frequency),
                    confidenceScore=_confidence(frequency, success_rate, len(decision_laboratory.get("workflowReplay", ())), len(decision_laboratory.get("performanceComparisons", ()))),
                )
            )
        if api_runtime_monitor.get("events") or api_runtime_monitor.get("calls"):
            patterns.append(
                HistoricalPattern(
                    patternId="HRE-PAT-000005",
                    category="Runtime Optimization",
                    summary="Runtime and credit behavior should be studied across repeated workflow executions.",
                    supportingWorkflows=_take(workflows, 12),
                    supportingDecisionObjects=_take(decision_objects, 12),
                    supportingTruthRecords=_take(truth_records, 12),
                    historicalFrequency=frequency,
                    historicalSuccessRate=success_rate,
                    marketDiversity=market_diversity,
                    promptDiversity=max(1, len(set(item for item in prompts if item))),
                    strategyDiversity=max(1, len(set(item for item in strategies if item))),
                    evidenceStrength=_evidence_strength(frequency),
                    confidenceScore=_confidence(frequency, success_rate, len(decision_laboratory.get("workflowReplay", ())), len(decision_laboratory.get("performanceComparisons", ()))),
                )
            )
        return tuple(patterns)

    def _recommendations(
        self,
        timestamp_utc: str,
        patterns: tuple[HistoricalPattern, ...],
        prompt_contract: dict[str, Any],
        strategy_performance: dict[str, Any],
        decision_laboratory: dict[str, Any],
    ) -> tuple[HistorianRecommendation, ...]:
        recommendations: list[HistorianRecommendation] = []
        prompt_versions = tuple(item.get("prompt_template_id") or item.get("promptVersion") or item.get("version", "") for item in prompt_contract.get("templates", ()))
        strategy_versions = tuple(item.get("strategyName") or item.get("strategy_name") or "paper_momentum_baseline" for item in strategy_performance.get("strategyLeaderboard", ()))
        experiments = tuple(item.get("experiment_id", "") for item in decision_laboratory.get("experiments", ()))
        for pattern in patterns:
            if pattern.historicalFrequency < self.minimum_historical_frequency or pattern.confidenceScore < 0.6:
                continue
            recommendations.append(
                HistorianRecommendation(
                    recommendationId=f"HRE-REC-{len(recommendations) + 1:06d}",
                    creationDate=timestamp_utc,
                    authorOffice="Historian",
                    category=_recommendation_categories(pattern.category),
                    summary=_summary(pattern.category),
                    detailedExplanation=(
                        f"Historical pattern {pattern.patternId} occurred {pattern.historicalFrequency} times with "
                        f"{pattern.historicalSuccessRate}% success rate. The Historian recommends laboratory validation "
                        "before Commander review; production remains blocked."
                    ),
                    supportingEvidence=(
                        pattern.summary,
                        f"Evidence strength {pattern.evidenceStrength}.",
                        f"Market diversity {pattern.marketDiversity}; prompt diversity {pattern.promptDiversity}; strategy diversity {pattern.strategyDiversity}.",
                    ),
                    supportingWorkflows=pattern.supportingWorkflows,
                    supportingDecisionObjects=pattern.supportingDecisionObjects,
                    supportingTruthRecords=pattern.supportingTruthRecords,
                    historicalFrequency=pattern.historicalFrequency,
                    historicalSuccessRate=pattern.historicalSuccessRate,
                    estimatedEnterpriseBenefit=_benefit(pattern.category),
                    confidenceScore=pattern.confidenceScore,
                    priority=_priority(pattern.category, pattern.confidenceScore, pattern.historicalFrequency),
                    laboratoryStatus="QUEUED_FOR_VALIDATION",
                    commanderStatus="AWAITING_COMMANDER_REVIEW",
                    productionStatus="BLOCKED_PENDING_COMMANDER_APPROVAL",
                    relatedPromptVersions=_take(prompt_versions, 8),
                    relatedStrategyVersions=_take(strategy_versions, 8),
                    relatedExperiments=_take(experiments, 8),
                    relatedRecommendations=(),
                )
            )
        return tuple(recommendations)

    def _lessons(
        self,
        timestamp_utc: str,
        patterns: tuple[HistoricalPattern, ...],
        recommendations: tuple[HistorianRecommendation, ...],
        prompt_contract: dict[str, Any],
        strategy_performance: dict[str, Any],
    ) -> tuple[InstitutionalLesson, ...]:
        lessons: list[InstitutionalLesson] = []
        rec_by_category = {item.category[0]: item for item in recommendations if item.category}
        prompt_versions = tuple(item.get("prompt_template_id") or item.get("promptVersion") or item.get("version", "") for item in prompt_contract.get("templates", ()))
        strategy_versions = tuple(item.get("strategyName") or item.get("strategy_name") or "paper_momentum_baseline" for item in strategy_performance.get("strategyLeaderboard", ()))
        for pattern in patterns:
            if pattern.historicalFrequency < self.minimum_historical_frequency:
                continue
            related = rec_by_category.get(_recommendation_categories(pattern.category)[0])
            lessons.append(
                InstitutionalLesson(
                    lessonId=f"HRE-LESSON-{len(lessons) + 1:06d}",
                    lessonTitle=f"{pattern.category} requires repeated evidence",
                    description=f"The Historian observed a recurring {pattern.category.lower()} pattern and archived it as institutional doctrine candidate evidence.",
                    historicalEvidence=pattern.supportingTruthRecords,
                    supportingWorkflows=pattern.supportingWorkflows,
                    supportingDecisionObjects=pattern.supportingDecisionObjects,
                    supportingRecommendations=(related.recommendationId,) if related else (),
                    confidence=pattern.confidenceScore,
                    enterpriseValue=_benefit(pattern.category),
                    applicableStrategies=_take(strategy_versions, 8),
                    applicablePrompts=_take(prompt_versions, 8),
                    applicableMarketConditions=("paper_market_context",),
                    dateEstablished=timestamp_utc,
                    dateLastConfirmed=timestamp_utc,
                )
            )
        if not lessons:
            return (
                InstitutionalLesson(
                    lessonId="HRE-LESSON-000000",
                    lessonTitle="Awaiting accumulated historical evidence",
                    description="The Historian has not yet reached the minimum historical frequency required for permanent doctrine.",
                    historicalEvidence=(),
                    supportingWorkflows=(),
                    supportingDecisionObjects=(),
                    supportingRecommendations=(),
                    confidence=1.0,
                    enterpriseValue="Prevents anecdotal production changes.",
                    applicableStrategies=(),
                    applicablePrompts=(),
                    applicableMarketConditions=("paper_market_context",),
                    dateEstablished=timestamp_utc,
                    dateLastConfirmed=timestamp_utc,
                ),
            )
        return tuple(lessons)

    def _knowledge_gaps(
        self,
        patterns: tuple[HistoricalPattern, ...],
        performance_truth: dict[str, Any],
        decision_laboratory: dict[str, Any],
        prompt_contract: dict[str, Any],
        strategy_performance: dict[str, Any],
    ) -> tuple[dict[str, Any], ...]:
        gaps: list[dict[str, Any]] = []
        max_frequency = max((item.historicalFrequency for item in patterns), default=0)
        if max_frequency < self.minimum_historical_frequency:
            gaps.append(_gap("Sparse historical observations", "Critical", "Historian requires repeated workflows before recommendation promotion."))
        if len(decision_laboratory.get("performanceComparisons", ())) < 1:
            gaps.append(_gap("Sparse replay coverage", "High", "Decision Laboratory validation is pending for historical recommendations."))
        if not performance_truth.get("tradeLedger"):
            gaps.append(_gap("Limited trade outcome history", "High", "Trade ledger depth is insufficient for long-term strategy doctrine."))
        if len(prompt_contract.get("templates", ())) < 2:
            gaps.append(_gap("Prompt uncertainty", "Medium", "Prompt version diversity is limited for historical prompt comparison."))
        if not strategy_performance.get("strategyLeaderboard"):
            gaps.append(_gap("Weak strategy version history", "Medium", "Strategy leaderboard needs more comparable outcomes."))
        return tuple(gaps)

    def _metrics(
        self,
        patterns: tuple[HistoricalPattern, ...],
        recommendations: tuple[HistorianRecommendation, ...],
        lessons: tuple[InstitutionalLesson, ...],
        gaps: tuple[dict[str, Any], ...],
        decision_laboratory: dict[str, Any],
    ) -> dict[str, Any]:
        confidence = round(sum(item.confidenceScore for item in recommendations) / max(1, len(recommendations)), 2)
        return {
            "patternsDetected": len(patterns),
            "recommendationsGenerated": len(recommendations),
            "recommendationsPending": len(recommendations),
            "lessonsArchived": len(lessons),
            "knowledgeGaps": len(gaps),
            "laboratoryQueue": len(recommendations),
            "commanderReviews": len(recommendations),
            "validatedRecommendations": len(decision_laboratory.get("performanceComparisons", ())),
            "averageConfidence": confidence,
            "historicalCoverage": max((item.historicalFrequency for item in patterns), default=0),
            "institutionalWisdom": min(100, 48 + len(patterns) * 4 + len(recommendations) * 5 + len(lessons) * 3),
        }


def _take(values: tuple[str, ...], count: int) -> tuple[str, ...]:
    return tuple(item for item in values if item)[:count]


def _historical_success_rate(performance_truth: dict[str, Any], strategy_performance: dict[str, Any]) -> float:
    strategy_rows = tuple(strategy_performance.get("strategyLeaderboard", ()))
    if strategy_rows:
        return round(sum(float(item.get("winRate", 0.0)) for item in strategy_rows) / max(1, len(strategy_rows)), 2)
    portfolio_rows = tuple(performance_truth.get("portfolioLedger", ()))
    if portfolio_rows:
        wins = sum(1 for item in portfolio_rows if float(item.get("total_return", item.get("totalReturn", 0.0)) or 0.0) >= 0)
        return round(wins / max(1, len(portfolio_rows)) * 100, 2)
    return 0.0


def _confidence(frequency: int, success_rate: float, replay_count: int, validation_count: int) -> float:
    frequency_factor = min(0.24, frequency * 0.08)
    success_factor = min(0.24, success_rate / 400)
    replay_factor = min(0.16, replay_count * 0.04)
    validation_factor = min(0.14, validation_count * 0.05)
    stability_factor = 0.12 if frequency >= 2 else 0.04
    return round(min(0.98, 0.28 + frequency_factor + success_factor + replay_factor + validation_factor + stability_factor), 2)


def _evidence_strength(frequency: int) -> str:
    if frequency >= 100:
        return "STRONG"
    if frequency >= 10:
        return "MODERATE"
    if frequency >= 2:
        return "WEAK_ACCUMULATED"
    return "ISOLATED_EVENT"


def _recommendation_categories(category: str) -> tuple[str, ...]:
    mapping = {
        "Risk Doctrine": ("Risk Doctrine", "Institutional Doctrine"),
        "Prompt Improvement": ("Prompt Improvement", "Capability Development"),
        "Strategy Improvement": ("Strategy Improvement", "Decision Consistency"),
        "Runtime Optimization": ("Runtime Optimization", "Resource Efficiency"),
        "Confidence Calibration": ("Confidence Calibration", "Decision Consistency"),
    }
    return mapping.get(category, (category, "Capability Development"))


def _summary(category: str) -> str:
    return {
        "Confidence Calibration": "Calibrate confidence against accumulated historical outcomes.",
        "Risk Doctrine": "Validate risk doctrine against repeated drawdown and outcome history.",
        "Prompt Improvement": "Compare prompt versions through historical replay before any production update.",
        "Strategy Improvement": "Validate strategy refinements against repeated Performance Truth records.",
        "Runtime Optimization": "Study runtime patterns for repeatable workflow efficiency gains.",
    }.get(category, f"Investigate recurring {category.lower()} behavior.")


def _benefit(category: str) -> str:
    return {
        "Confidence Calibration": "Improves decision quality and Commander trust.",
        "Risk Doctrine": "Reduces downside exposure and improves capital discipline.",
        "Prompt Improvement": "Improves prompt quality and evidence weighting.",
        "Strategy Improvement": "Improves strategy quality and repeatability.",
        "Runtime Optimization": "Improves workflow efficiency and credit efficiency.",
    }.get(category, "Improves enterprise capability and institutional maturity.")


def _priority(category: str, confidence: float, frequency: int) -> str:
    if category in {"Risk Doctrine", "Confidence Calibration"} and confidence >= 0.75:
        return "High"
    if frequency >= 100 and confidence >= 0.85:
        return "Critical"
    if confidence >= 0.7:
        return "Medium"
    if frequency < 10:
        return "Research Candidate"
    return "Low"


def _gap(title: str, priority: str, summary: str) -> dict[str, Any]:
    stable = sum((index + 1) * ord(character) for index, character in enumerate(f"{title}:{priority}")) % 1000000
    return {
        "gapId": f"HRE-GAP-{stable:06d}",
        "title": title,
        "priority": priority,
        "summary": summary,
        "academyPriority": "RESEARCH_QUEUE",
    }
