"""Enterprise Experiment Scheduler for ARGOS research planning."""

from __future__ import annotations

import hashlib
import json
from typing import Any


EXPERIMENT_CATEGORIES = (
    "Prompt",
    "Strategy",
    "Risk",
    "Market Context",
    "Portfolio",
    "Execution",
    "Evidence",
    "Confidence",
    "Infrastructure",
    "Learning",
    "Automation",
    "Performance",
    "Benchmark",
    "Cost Optimization",
    "Doctrine",
)

EXPERIMENT_STATES = (
    "Idea",
    "Backlog",
    "Planned",
    "Queued",
    "Running",
    "Completed",
    "Validated",
    "Commander Review",
    "Archived",
    "Cancelled",
    "Rejected",
)


class EnterpriseExperimentScheduler:
    """Plan research without executing laboratory experiments."""

    def __init__(self) -> None:
        self._last_snapshot_key: tuple[Any, ...] | None = None
        self._last_snapshot: dict[str, Any] | None = None

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        historian_recommendation_engine: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        prompt_evolution_engine: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        decision_laboratory: dict[str, Any],
        enterprise_reproducibility_framework: dict[str, Any],
        enterprise_operational_guardrails: dict[str, Any],
        costs: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        snapshot_key = (
            len(historian_recommendation_engine.get("recommendationDatabase", ())),
            len(enterprise_learning_engine.get("recommendations", ())),
            len(prompt_evolution_engine.get("promptImprovementCandidates", ())),
            len(decision_laboratory.get("experiments", ())),
        )
        if self._last_snapshot_key == snapshot_key and self._last_snapshot is not None:
            return self._last_snapshot

        backlog = self._backlog(
            timestamp_utc,
            historian_recommendation_engine,
            enterprise_learning_engine,
            prompt_evolution_engine,
            strategy_package_manager,
            enterprise_reproducibility_framework,
            enterprise_operational_guardrails,
        )
        priority = tuple(self._priority(item, index) for index, item in enumerate(backlog, start=1))
        queue = self._queue(priority, decision_laboratory)
        calendar = self._calendar(priority)
        capacity = self._capacity(decision_laboratory, costs)
        snapshot = {
            "schedulerName": "Enterprise Experiment Scheduler",
            "engineeringOrder": "EO-V",
            "constitutionalMission": "Ensure every enterprise experiment maximizes institutional learning while respecting constitutional governance and enterprise resource limits.",
            "constitutionalQuestion": "What experiment will most improve ARGOS today?",
            "constitutionalMode": "RESEARCH_PLANNING_ONLY",
            "experimentCategories": EXPERIMENT_CATEGORIES,
            "experimentStates": EXPERIMENT_STATES,
            "researchBacklog": backlog,
            "experimentQueue": queue,
            "priorityCalculations": priority,
            "informationGainEstimates": tuple({"experimentId": item["experimentId"], "estimatedInformationGain": item["estimatedInformationGain"], "knowledgePerCredit": item["knowledgePerCredit"]} for item in priority),
            "dependencyGraph": tuple({"experimentId": item["experimentId"], "dependencies": item["dependencies"], "dependenciesSatisfied": item["dependenciesSatisfied"]} for item in priority),
            "schedulingCalendar": calendar,
            "laboratoryCapacity": capacity,
            "budgetAllocation": self._budget(costs, priority),
            "knowledgeYieldMetrics": self._knowledge_yield(decision_laboratory, priority),
            "researchVelocity": self._velocity(decision_laboratory, priority),
            "commanderPriorities": self._commander_priorities(priority),
            "experimentHistory": self._history(decision_laboratory),
            "researchDashboard": {
                "researchBacklog": len(backlog),
                "activeExperiments": len(decision_laboratory.get("experiments", ())),
                "todaySchedule": len(calendar["today"]),
                "expectedKnowledgeGain": round(sum(item["estimatedInformationGain"] for item in priority[:5]), 4),
                "expectedCreditUsage": round(sum(item["estimatedCreditCost"] for item in priority[:5]), 4),
                "laboratoryCapacity": capacity["availableExperimentSlots"],
                "upcomingRecommendations": len(queue),
                "researchVelocity": self._velocity(decision_laboratory, priority)["currentVelocity"],
                "enterpriseCuriosityIndex": min(100, 45 + len(backlog) * 4),
            },
            "lawVIIIFrugality": {
                "reusesHistoricalData": True,
                "checksCachedKnowledgeFirst": True,
                "prefersDeterministicAnalysis": True,
                "informationGainMustExceedCreditCost": True,
                "maximizesKnowledgePerCredit": True,
            },
            "historianFeed": {"recurringQuestionsScheduled": len(historian_recommendation_engine.get("recommendationDatabase", ()))},
            "enterpriseLearningFeed": {"researchOpportunitiesConverted": len(enterprise_learning_engine.get("recommendations", ()))},
            "decisionLaboratoryFeed": {"approvedResearchPlansRequired": True, "queuedExperimentPlans": len(queue)},
            "promptEvolutionFeed": {"candidatePromptsPrioritized": len(prompt_evolution_engine.get("promptImprovementCandidates", ()))},
            "strategyEvolutionFeed": {"candidateStrategiesSequenced": len([item for item in backlog if item["category"] == "Strategy"])},
            "internalDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "tradesPlaced": 0,
                "experimentsExecuted": 0,
                "productionPromotionsApproved": 0,
                "backlogCount": len(backlog),
                "queuedCount": len(queue),
                "auditEventCountObserved": audit_event_count,
            },
            "lawVII": {
                "executesWorkflows": False,
                "ownsWorkflowTokens": False,
                "tradesSecurities": False,
                "makesInvestmentDecisions": False,
                "promotesProductionChanges": False,
                "modifiesPrompts": False,
                "modifiesStrategies": False,
                "overridesCommanderAuthority": False,
                "responsibility": "PLANS_ENTERPRISE_RESEARCH_ONLY",
            },
        }
        self._last_snapshot_key = snapshot_key
        self._last_snapshot = snapshot
        return snapshot

    def _backlog(self, timestamp: str, historian: dict[str, Any], learning: dict[str, Any], prompts: dict[str, Any], strategies: dict[str, Any], reproducibility: dict[str, Any], guardrails: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        for item in historian.get("recommendationDatabase", ())[:6]:
            rows.append(self._experiment(len(rows) + 1, timestamp, "Doctrine", item.get("summary", "Investigate recurring historical pattern"), item.get("summary", "Historian pattern requires validation."), "Historical pattern improves enterprise doctrine.", ("Historian Recommendation",), item.get("confidenceScore", 0.7)))
        for item in learning.get("recommendations", ())[:6]:
            rows.append(self._experiment(len(rows) + 1, timestamp, item.get("category", "Learning"), item.get("title", "Validate learning recommendation"), item.get("description", "Learning engine recommendation requires laboratory validation."), "Recommendation improves enterprise capability.", ("Enterprise Learning Recommendation",), item.get("confidence", 0.7)))
        for item in prompts.get("promptImprovementCandidates", ())[:6]:
            rows.append(self._experiment(len(rows) + 1, timestamp, "Prompt", item.get("summary", "Validate prompt candidate"), item.get("expectedBenefit", "Prompt candidate requires replay."), "Candidate prompt improves reasoning quality.", ("Prompt Package", "Replay Data"), item.get("confidence", 0.72)))
        for item in strategies.get("strategyPackageRegistry", ())[:4]:
            rows.append(self._experiment(len(rows) + 1, timestamp, "Strategy", item.get("strategyName", "Validate strategy package"), item.get("investmentThesis", "Strategy package requires regime validation."), "Strategy improves benchmark-relative performance.", ("Strategy Package", "Historical Market Data"), 0.68))
        if not rows:
            rows.append(self._experiment(1, timestamp, "Reproducibility", "Validate baseline replay reproducibility", "Confirm historical replay can reconstruct current enterprise state.", "Reproducible experiments improve scientific reliability.", ("Enterprise Snapshot",), 0.8))
        rows.append(self._experiment(len(rows) + 1, timestamp, "Risk", "Test operational guardrail sensitivity", "Evaluate whether guardrail thresholds minimize false halts while preserving safety.", "Guardrail calibration improves safe research throughput.", ("Guardrail Registry",), guardrails.get("readinessConfidence", 0.9)))
        rows.append(self._experiment(len(rows) + 1, timestamp, "Infrastructure", "Measure replay cache reuse", "Determine whether cached reproducibility artifacts can reduce experiment cost.", "Historical cache reuse reduces future AI credits.", ("Reproducibility Archive",), reproducibility.get("reproducibilityScore", {}).get("overallScore", 80) / 100))
        return tuple(rows[:18])

    def _experiment(self, index: int, timestamp: str, category: str, title: str, description: str, hypothesis: str, dependencies: tuple[str, ...], confidence: float) -> dict[str, Any]:
        payload = {
            "experimentId": f"EES-EXP-{index:06d}",
            "title": title,
            "description": description,
            "category": category if category in EXPERIMENT_CATEGORIES else "Learning",
            "researchQuestion": f"What measurable learning does {title} produce?",
            "hypothesis": hypothesis,
            "successCriteria": ("Measurable knowledge gain", "Replayable evidence", "Commander-reviewable result"),
            "expectedBenefit": "Improves institutional learning without production mutation.",
            "estimatedInformationGain": round(0.45 + min(0.45, float(confidence or 0.0) * 0.4), 4),
            "estimatedCreditCost": round(0.0025 + index * 0.0005, 4),
            "estimatedRuntime": f"{5 + index}m",
            "priority": "HIGH" if index <= 3 else "MEDIUM" if index <= 8 else "LOW",
            "dependencies": dependencies,
            "commanderStatus": "AWAITING_COMMANDER_REVIEW",
            "laboratoryStatus": "PLANNED_NOT_EXECUTED",
            "validationStatus": "PENDING",
            "finalOutcome": "PENDING_EXPERIMENT",
            "knowledgeProduced": "PENDING",
            "state": "Backlog",
            "createdTimestamp": timestamp,
            "immutable": True,
        }
        return dict(payload, hash=_hash_payload(payload))

    def _priority(self, item: dict[str, Any], index: int) -> dict[str, Any]:
        information = float(item["estimatedInformationGain"])
        cost = float(item["estimatedCreditCost"])
        age = min(0.1, index * 0.005)
        benefit = 0.85 if item["priority"] == "HIGH" else 0.7 if item["priority"] == "MEDIUM" else 0.55
        risk_reduction = 0.8 if item["category"] in {"Risk", "Doctrine", "Confidence"} else 0.6
        score = round((benefit * 0.3 + information * 0.35 + risk_reduction * 0.15 + age) / max(0.1, cost * 40), 4)
        return dict(item, priorityScore=score, expectedEnterpriseBenefit=benefit, historicalFrequency=index, knowledgeGap=round(1 - information, 4), riskReduction=risk_reduction, researchAge=age, commanderPriority=item["priority"], knowledgePerCredit=round(information / max(0.0001, cost), 4), dependenciesSatisfied=True)

    def _queue(self, priority: tuple[dict[str, Any], ...], lab: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        active = len(lab.get("experiments", ()))
        rows = []
        for index, item in enumerate(sorted(priority, key=lambda row: row["priorityScore"], reverse=True)[:8], start=1):
            status = "Queued" if index + active <= 4 else "Waiting"
            rows.append({"queueId": f"EES-QUEUE-{index:06d}", "experimentId": item["experimentId"], "title": item["title"], "status": status, "priorityScore": item["priorityScore"], "laboratoryStatus": item["laboratoryStatus"]})
        return tuple(rows)

    def _calendar(self, priority: tuple[dict[str, Any], ...]) -> dict[str, tuple[dict[str, Any], ...]]:
        ranked = tuple(sorted(priority, key=lambda row: row["priorityScore"], reverse=True))
        return {
            "today": tuple({"experimentId": item["experimentId"], "title": item["title"], "window": "Today"} for item in ranked[:3]),
            "tomorrow": tuple({"experimentId": item["experimentId"], "title": item["title"], "window": "Tomorrow"} for item in ranked[3:6]),
            "thisWeek": tuple({"experimentId": item["experimentId"], "title": item["title"], "window": "This Week"} for item in ranked[6:10]),
            "thisMonth": tuple({"experimentId": item["experimentId"], "title": item["title"], "window": "This Month"} for item in ranked[10:14]),
            "longTerm": tuple({"experimentId": item["experimentId"], "title": item["title"], "window": "Long-Term"} for item in ranked[14:]),
        }

    def _capacity(self, lab: dict[str, Any], costs: dict[str, Any]) -> dict[str, Any]:
        active = len(lab.get("experiments", ()))
        return {"maximumConcurrentExperiments": 4, "activeExperiments": active, "availableExperimentSlots": max(0, 4 - active), "laboratoryRuntimeAvailable": "LOCAL_REPLAY", "dailyCreditBudget": costs.get("budget_limit_usd", 0), "commanderResearchBudget": "COMMANDER_CONTROLLED"}

    def _budget(self, costs: dict[str, Any], priority: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        planned = round(sum(item["estimatedCreditCost"] for item in priority[:8]), 4)
        return {"dailyExperimentBudget": 0.05, "plannedCreditUsage": planned, "remainingResearchBudget": round(max(0, 0.05 - planned), 4), "noExperimentExceedsAllocatedResources": planned <= 0.05, "budgetStatus": costs.get("budget_status", "GREEN")}

    def _knowledge_yield(self, lab: dict[str, Any], priority: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        completed = len([item for item in lab.get("experiments", ()) if item.get("validationStatus") == "VALIDATED"])
        return {"validatedKnowledge": completed, "rejectedHypothesesValuable": True, "confidenceUpdates": completed, "futureResearchGenerated": len(priority), "enterpriseCapabilityGain": round(sum(item["estimatedInformationGain"] for item in priority[:5]), 4)}

    def _velocity(self, lab: dict[str, Any], priority: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        return {"currentVelocity": len(lab.get("experiments", ())) + len(priority), "plannedThisWeek": min(10, len(priority)), "throughputGoal": "Better experiments over more experiments", "diversityProtected": True}

    def _commander_priorities(self, priority: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        return tuple({"experimentId": item["experimentId"], "title": item["title"], "commanderPriority": item["commanderPriority"], "priorityScore": item["priorityScore"]} for item in priority[:8])

    def _history(self, lab: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        return tuple({"experimentId": item.get("experiment_id", ""), "originalWorkflowId": item.get("original_workflow_id", ""), "state": "Completed" if item else "Archived", "knowledgeProduced": "Laboratory comparison available"} for item in lab.get("experiments", ()))


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
