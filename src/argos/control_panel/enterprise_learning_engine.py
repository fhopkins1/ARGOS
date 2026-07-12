from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


LEARNING_CATEGORIES = (
    "Prompt Improvement",
    "Strategy Improvement",
    "Risk Improvement",
    "Evidence Improvement",
    "Confidence Calibration",
    "Workflow Optimization",
    "Runtime Optimization",
    "Resource Optimization",
    "Knowledge Gaps",
    "Market Context Gaps",
    "Decision Consistency",
    "Execution Timing",
    "False Positives",
    "False Negatives",
    "Behavior Drift",
    "Capability Growth",
    "Institutional Weakness",
    "Institutional Strength",
)


@dataclass(frozen=True)
class LearningObservation:
    observationId: str
    creationTime: str
    workflowId: str
    decisionObjectId: str
    relatedStrategy: str
    relatedPrompt: str
    relatedMarketConditions: str
    observedOutcome: float
    expectedOutcome: float
    difference: float
    evidence: tuple[str, ...]
    confidence: float
    category: tuple[str, ...]
    suggestedImprovement: str
    recommendationPriority: str
    laboratoryStatus: str
    commanderStatus: str
    productionStatus: str


@dataclass(frozen=True)
class LearningRecommendation:
    recommendationId: str
    title: str
    category: str
    priority: str
    expectedBenefit: str
    evidenceStrength: str
    confidence: float
    relatedPrompt: str
    relatedStrategy: str
    relatedOffice: str
    laboratoryStatus: str
    commanderApprovalStatus: str
    productionStatus: str


class EnterpriseLearningEngine:
    """Deterministic institutional learning layer for completed ARGOS workflows."""

    def __init__(self, *, minimum_evidence_count: int = 1) -> None:
        self.minimum_evidence_count = max(1, minimum_evidence_count)

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
        historian_recommendation_engine: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        historian_recommendation_engine = historian_recommendation_engine or {}
        observations = self._observations(
            timestamp_utc=timestamp_utc,
            workflow_runtime_monitor=workflow_runtime_monitor,
            performance_truth=performance_truth,
            strategy_performance=strategy_performance,
            decision_laboratory=decision_laboratory,
            prompt_contract=prompt_contract,
            api_runtime_monitor=api_runtime_monitor,
        )
        recommendations = self._recommendations(observations) + self._historian_recommendations(historian_recommendation_engine)
        backlog = tuple(
            {
                "rank": index,
                "recommendationId": item.recommendationId,
                "title": item.title,
                "category": item.category,
                "priority": item.priority,
                "laboratoryStatus": item.laboratoryStatus,
                "commanderApprovalStatus": item.commanderApprovalStatus,
                "productionStatus": item.productionStatus,
            }
            for index, item in enumerate(recommendations, start=1)
        )
        knowledge_gaps = self._knowledge_gaps(observations, performance_truth, prompt_contract, strategy_performance, decision_laboratory)
        metrics = self._metrics(observations, recommendations, decision_laboratory, knowledge_gaps)
        return {
            "engineName": "Enterprise Learning Engine",
            "engineeringOrder": "EO-A",
            "constitutionalMission": "Every completed workflow should increase the future capability of the enterprise.",
            "constitutionalMode": "ADVISORY_ONLY",
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
                "performanceTruthRecords": len(performance_truth.get("tradeLedger", ())) + len(performance_truth.get("portfolioLedger", ())),
                "completedWorkflows": len(workflow_runtime_monitor.get("recentCompletedWorkflows", ())),
                "decisionLaboratoryReplays": len(decision_laboratory.get("workflowReplay", ())),
                "promptTemplates": len(prompt_contract.get("templates", ())),
                "strategyVersions": len(strategy_performance.get("strategyLeaderboard", ())),
                "runtimeAlerts": len(api_runtime_monitor.get("alerts", ())),
                "creditGovernorEvents": len(credit_governor.get("policyEvents", ())),
                "auditEvents": audit_event_count,
                "historianRecommendations": len(historian_recommendation_engine.get("recommendationDatabase", ())),
            },
            "observationCount": len(observations),
            "observations": tuple(asdict(item) for item in observations),
            "recommendations": tuple(asdict(item) for item in recommendations),
            "improvementBacklog": backlog,
            "knowledgeGaps": knowledge_gaps,
            "metrics": metrics,
            "categoryDefinitions": LEARNING_CATEGORIES,
            "recommendationThresholds": {
                "minimumEvidenceCount": self.minimum_evidence_count,
                "minimumConfidence": 0.55,
                "requiresLaboratoryValidation": True,
                "requiresCommanderApproval": True,
                "productionMutationAllowed": False,
            },
            "learningRules": (
                "Every completed workflow produces one immutable learning observation.",
                "Recommendations aggregate category evidence before entering the laboratory queue.",
                "Production prompts and strategies remain unchanged until laboratory validation and Commander approval.",
                "The engine observes and recommends only; it never executes work or owns workflow tokens.",
            ),
            "learningPipeline": (
                "Workflow Complete",
                "Performance Truth Recorded",
                "Historian Analysis",
                "Learning Observation Created",
                "Observation Classified",
                "Evidence Aggregated",
                "Recommendation Candidate",
                "Laboratory Queue",
                "Commander Review",
                "Production Promotion",
            ),
            "validationHistory": tuple(decision_laboratory.get("performanceComparisons", ())),
            "historianRecommendationInputs": tuple(historian_recommendation_engine.get("recommendationDatabase", ())),
            "promotionHistory": (),
            "internalDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "recommendationSpamGuard": "CATEGORY_AGGREGATION",
                "isolatedEventPolicy": "WEAK_EVIDENCE_UNTIL_REPEATED",
            },
        }

    def _observations(
        self,
        *,
        timestamp_utc: str,
        workflow_runtime_monitor: dict[str, Any],
        performance_truth: dict[str, Any],
        strategy_performance: dict[str, Any],
        decision_laboratory: dict[str, Any],
        prompt_contract: dict[str, Any],
        api_runtime_monitor: dict[str, Any],
    ) -> tuple[LearningObservation, ...]:
        completed = tuple(workflow_runtime_monitor.get("recentCompletedWorkflows", ()))
        truth_by_workflow = {item.get("workflow_id", ""): item for item in performance_truth.get("portfolioLedger", ())}
        replay_by_workflow = {item.get("workflowId", ""): item for item in decision_laboratory.get("workflowReplay", ())}
        decision_by_workflow = {item.get("workflowId", ""): item for item in strategy_performance.get("decisionObjectEvolution", ())}
        recommendations: list[LearningObservation] = []
        for index, workflow in enumerate(completed, start=1):
            workflow_id = workflow.get("workflowIdentifier") or workflow.get("workflow_id") or f"WORKFLOW-{index:06d}"
            replay = replay_by_workflow.get(workflow_id, {})
            decision = decision_by_workflow.get(workflow_id, {})
            truth = truth_by_workflow.get(workflow_id, {})
            decision_id = replay.get("decisionObjectId") or decision.get("decisionObjectId") or f"DO-{workflow_id}"
            expected = _float(decision.get("expectedReturn") or replay.get("expectedReturn") or decision.get("confidence"), 0.0)
            observed = _float(truth.get("total_return") or truth.get("totalReturn") or replay.get("portfolioOutcome"), 0.0)
            difference = round(observed - expected, 4)
            categories = self._categories(difference, decision, truth, prompt_contract, strategy_performance, api_runtime_monitor)
            confidence = self._confidence(index, difference, performance_truth, decision_laboratory, strategy_performance)
            priority = "HIGH" if abs(difference) >= 2.0 or "Risk Improvement" in categories else ("MEDIUM" if abs(difference) >= 0.5 else "LOW")
            evidence = (
                f"Workflow {workflow_id} completed with status {workflow.get('status', 'Archived')}.",
                f"Observed outcome {observed:.4f}; expected outcome {expected:.4f}; delta {difference:.4f}.",
                f"Truth records available: {len(performance_truth.get('tradeLedger', ())) + len(performance_truth.get('portfolioLedger', ())) }.",
                f"Decision Laboratory replay packages available: {len(decision_laboratory.get('workflowReplay', ())) }.",
            )
            recommendations.append(
                LearningObservation(
                    observationId=f"ELE-OBS-{index:06d}",
                    creationTime=timestamp_utc,
                    workflowId=workflow_id,
                    decisionObjectId=decision_id,
                    relatedStrategy=str(replay.get("strategy") or decision.get("strategy") or "paper_momentum_baseline"),
                    relatedPrompt=_related_prompt(prompt_contract),
                    relatedMarketConditions=_market_conditions(strategy_performance),
                    observedOutcome=observed,
                    expectedOutcome=expected,
                    difference=difference,
                    evidence=evidence,
                    confidence=confidence,
                    category=categories,
                    suggestedImprovement=self._suggestion(categories, difference),
                    recommendationPriority=priority,
                    laboratoryStatus="QUEUED_FOR_VALIDATION",
                    commanderStatus="AWAITING_REVIEW",
                    productionStatus="BLOCKED_PENDING_COMMANDER_APPROVAL",
                )
            )
        return tuple(recommendations)

    def _categories(
        self,
        difference: float,
        decision: dict[str, Any],
        truth: dict[str, Any],
        prompt_contract: dict[str, Any],
        strategy_performance: dict[str, Any],
        api_runtime_monitor: dict[str, Any],
    ) -> tuple[str, ...]:
        categories = ["Capability Growth", "Workflow Optimization", "Evidence Improvement"]
        if prompt_contract.get("templates"):
            categories.append("Prompt Improvement")
        if strategy_performance.get("strategyLeaderboard"):
            categories.append("Strategy Improvement")
        if abs(difference) >= 0.25 or decision.get("confidence") is not None:
            categories.append("Confidence Calibration")
        if _float(decision.get("risk") or truth.get("drawdown"), 0.0) > 0:
            categories.append("Risk Improvement")
        if api_runtime_monitor.get("calls") or api_runtime_monitor.get("events"):
            categories.append("Runtime Optimization")
            categories.append("Resource Optimization")
        if not truth:
            categories.append("Knowledge Gaps")
            categories.append("Market Context Gaps")
        if difference >= 0:
            categories.append("Institutional Strength")
        else:
            categories.append("Institutional Weakness")
        return tuple(dict.fromkeys(categories))

    def _confidence(
        self,
        sample_index: int,
        difference: float,
        performance_truth: dict[str, Any],
        decision_laboratory: dict[str, Any],
        strategy_performance: dict[str, Any],
    ) -> float:
        sample_factor = min(0.22, sample_index * 0.04)
        truth_factor = min(0.2, (len(performance_truth.get("tradeLedger", ())) + len(performance_truth.get("portfolioLedger", ()))) * 0.03)
        replay_factor = min(0.18, len(decision_laboratory.get("workflowReplay", ())) * 0.03)
        consistency_factor = 0.12 if abs(difference) <= 1.0 else 0.06
        scorecard_factor = min(0.12, _float(strategy_performance.get("enterpriseScorecard", {}).get("decisionQuality"), 75.0) / 1000)
        return round(min(0.98, 0.38 + sample_factor + truth_factor + replay_factor + consistency_factor + scorecard_factor), 2)

    def _suggestion(self, categories: tuple[str, ...], difference: float) -> str:
        if "Risk Improvement" in categories and difference < 0:
            return "Validate tighter risk doctrine and confidence thresholds in the Decision Laboratory."
        if "Prompt Improvement" in categories and "Confidence Calibration" in categories:
            return "Compare prompt wording against observed confidence error before any production prompt promotion."
        if "Strategy Improvement" in categories:
            return "Replay the related strategy path and test refinement candidates against Performance Truth."
        if "Knowledge Gaps" in categories:
            return "Acquire missing market context and truth records before increasing recommendation priority."
        return "Retain the workflow as institutional evidence and monitor for repeatable improvement patterns."

    def _recommendations(self, observations: tuple[LearningObservation, ...]) -> tuple[LearningRecommendation, ...]:
        category_groups: dict[str, list[LearningObservation]] = {}
        for observation in observations:
            for category in observation.category:
                category_groups.setdefault(category, []).append(observation)
        recommendations: list[LearningRecommendation] = []
        for category, grouped in sorted(category_groups.items()):
            if len(grouped) < self.minimum_evidence_count:
                continue
            confidence = round(sum(item.confidence for item in grouped) / len(grouped), 2)
            if confidence < 0.55:
                continue
            recommendations.append(
                LearningRecommendation(
                    recommendationId=f"ELE-REC-{len(recommendations) + 1:06d}",
                    title=_recommendation_title(category),
                    category=category,
                    priority=_recommendation_priority(category, grouped),
                    expectedBenefit=_expected_benefit(category),
                    evidenceStrength=_evidence_strength(len(grouped)),
                    confidence=confidence,
                    relatedPrompt=grouped[-1].relatedPrompt,
                    relatedStrategy=grouped[-1].relatedStrategy,
                    relatedOffice=_related_office(category),
                    laboratoryStatus="QUEUED_FOR_VALIDATION",
                    commanderApprovalStatus="AWAITING_COMMANDER_REVIEW",
                    productionStatus="BLOCKED_PENDING_COMMANDER_APPROVAL",
                )
            )
        return tuple(recommendations[:12])

    def _historian_recommendations(self, historian_recommendation_engine: dict[str, Any]) -> tuple[LearningRecommendation, ...]:
        recommendations = []
        for item in tuple(historian_recommendation_engine.get("recommendationDatabase", ()))[:6]:
            categories = tuple(item.get("category", ()))
            recommendations.append(
                LearningRecommendation(
                    recommendationId=f"ELE-HRE-{len(recommendations) + 1:06d}",
                    title=item.get("summary", "Evaluate Historian recommendation"),
                    category=categories[0] if categories else "Institutional Doctrine",
                    priority=str(item.get("priority", "Medium")).upper().replace(" ", "_"),
                    expectedBenefit=item.get("estimatedEnterpriseBenefit", "Improves institutional wisdom."),
                    evidenceStrength=_evidence_strength(int(item.get("historicalFrequency", 0))),
                    confidence=float(item.get("confidenceScore", 0.0) or 0.0),
                    relatedPrompt=", ".join(tuple(item.get("relatedPromptVersions", ()))[:3]) or "Historian Pattern Archive",
                    relatedStrategy=", ".join(tuple(item.get("relatedStrategyVersions", ()))[:3]) or "Historian Pattern Archive",
                    relatedOffice="Historian",
                    laboratoryStatus=item.get("laboratoryStatus", "QUEUED_FOR_VALIDATION"),
                    commanderApprovalStatus=item.get("commanderStatus", "AWAITING_COMMANDER_REVIEW"),
                    productionStatus=item.get("productionStatus", "BLOCKED_PENDING_COMMANDER_APPROVAL"),
                )
            )
        return tuple(recommendations)

    def _knowledge_gaps(
        self,
        observations: tuple[LearningObservation, ...],
        performance_truth: dict[str, Any],
        prompt_contract: dict[str, Any],
        strategy_performance: dict[str, Any],
        decision_laboratory: dict[str, Any],
    ) -> tuple[dict[str, Any], ...]:
        gaps: list[dict[str, Any]] = []
        if len(observations) < 10:
            gaps.append(_gap("Sparse historical observations", "HIGH", "Need more completed workflow evidence before high-confidence promotion."))
        if not performance_truth.get("tradeLedger"):
            gaps.append(_gap("Insufficient trade outcomes", "MEDIUM", "No trade ledger records available for cross-workflow evidence aggregation."))
        if not prompt_contract.get("templates"):
            gaps.append(_gap("Prompt uncertainty", "MEDIUM", "Prompt templates are not available for prompt-level attribution."))
        if not strategy_performance.get("strategyLeaderboard"):
            gaps.append(_gap("Limited strategy versions", "MEDIUM", "Strategy leaderboard has not accumulated comparative performance evidence."))
        if not decision_laboratory.get("performanceComparisons"):
            gaps.append(_gap("Replay validation pending", "HIGH", "Recommendations require isolated laboratory replay before Commander promotion review."))
        return tuple(gaps)

    def _metrics(
        self,
        observations: tuple[LearningObservation, ...],
        recommendations: tuple[LearningRecommendation, ...],
        decision_laboratory: dict[str, Any],
        knowledge_gaps: tuple[dict[str, Any], ...],
    ) -> dict[str, Any]:
        average_confidence = round(sum(item.confidence for item in recommendations) / max(1, len(recommendations)), 2)
        validated = len(decision_laboratory.get("performanceComparisons", ()))
        coverage = max(0, min(100, 100 - (len(knowledge_gaps) * 12) + (len(observations) * 3)))
        maturity = max(20, min(100, 52 + len(observations) * 4 + len(recommendations) * 2 + validated * 5 - len(knowledge_gaps) * 3))
        return {
            "observationsToday": len(observations),
            "recommendationsToday": len(recommendations),
            "recommendationsPending": len(recommendations),
            "validatedImprovements": validated,
            "rejectedImprovements": 0,
            "laboratoryQueue": len(recommendations),
            "commanderReviews": len(recommendations),
            "averageConfidence": average_confidence,
            "learningVelocity": len(observations) + len(recommendations),
            "capabilityGrowth": min(99, 62 + len(observations) * 3 + len(recommendations)),
            "knowledgeCoverage": coverage,
            "institutionalMaturity": maturity,
        }


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _related_prompt(prompt_contract: dict[str, Any]) -> str:
    templates = tuple(prompt_contract.get("templates", ()))
    latest = templates[-1] if templates else {}
    return str(latest.get("prompt_template_id") or latest.get("template_id") or "PROMPT-CONTRACT-BASELINE")


def _market_conditions(strategy_performance: dict[str, Any]) -> str:
    benchmarks = tuple(strategy_performance.get("marketBenchmarks", ()))
    if not benchmarks:
        return "paper_market_context"
    leader = benchmarks[0]
    return f"{leader.get('symbol', 'SPY')} return {leader.get('benchmarkReturnPercent', 0)}%"


def _recommendation_title(category: str) -> str:
    return {
        "Prompt Improvement": "Compare prompt structure against observed decision quality",
        "Strategy Improvement": "Validate strategy refinement against Performance Truth",
        "Risk Improvement": "Test tighter risk doctrine before production promotion",
        "Confidence Calibration": "Calibrate confidence against observed outcomes",
        "Workflow Optimization": "Refine office sequencing and workflow timing",
        "Runtime Optimization": "Reduce runtime variance in repeated workflow stages",
        "Resource Optimization": "Improve credit efficiency without weakening evidence",
        "Knowledge Gaps": "Acquire missing enterprise knowledge before higher autonomy",
        "Market Context Gaps": "Expand market-regime context in future evidence packages",
    }.get(category, f"Strengthen {category.lower()} evidence")


def _recommendation_priority(category: str, observations: list[LearningObservation]) -> str:
    if category in {"Risk Improvement", "Knowledge Gaps", "Confidence Calibration"}:
        return "HIGH"
    if any(item.recommendationPriority == "HIGH" for item in observations):
        return "HIGH"
    if len(observations) >= 10:
        return "HIGH"
    return "MEDIUM"


def _expected_benefit(category: str) -> str:
    return {
        "Prompt Improvement": "Higher prompt reliability and cleaner Decision Object attribution.",
        "Strategy Improvement": "Better strategy selection after laboratory replay.",
        "Risk Improvement": "Improved loss discipline and Commander trust.",
        "Confidence Calibration": "Closer alignment between belief and observed outcomes.",
        "Workflow Optimization": "More consistent workflow throughput and office coordination.",
        "Runtime Optimization": "Lower runtime variance and clearer operational diagnostics.",
        "Resource Optimization": "Lower credit burn per validated workflow.",
        "Knowledge Gaps": "Broader evidence coverage for future recommendations.",
    }.get(category, "Incremental enterprise capability growth.")


def _evidence_strength(count: int) -> str:
    if count >= 100:
        return "STRONG"
    if count >= 10:
        return "MODERATE"
    return "WEAK"


def _related_office(category: str) -> str:
    return {
        "Prompt Improvement": "Academy",
        "Strategy Improvement": "Trader",
        "Risk Improvement": "Risk",
        "Evidence Improvement": "Librarian",
        "Confidence Calibration": "Analyst",
        "Workflow Optimization": "Executive",
        "Runtime Optimization": "Executive",
        "Resource Optimization": "Executive",
        "Knowledge Gaps": "Librarian",
        "Market Context Gaps": "Seeker",
    }.get(category, "Academy")


def _gap(title: str, priority: str, summary: str) -> dict[str, Any]:
    stable = sum((index + 1) * ord(character) for index, character in enumerate(f"{title}:{priority}")) % 1000000
    return {
        "gapId": f"ELE-GAP-{stable:06d}",
        "title": title,
        "priority": priority,
        "summary": summary,
        "acquisitionStatus": "QUEUED_FOR_FUTURE_EVIDENCE",
    }
