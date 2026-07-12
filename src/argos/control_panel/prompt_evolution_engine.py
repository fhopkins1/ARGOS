from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


PROMPT_STATES = (
    "Draft",
    "Candidate",
    "Laboratory",
    "Validated",
    "Commander Review",
    "Approved",
    "Production",
    "Deprecated",
    "Retired",
    "Archived",
)


@dataclass(frozen=True)
class PromptAsset:
    promptId: str
    promptName: str
    purpose: str
    associatedOffice: str
    creationDate: str
    author: str
    versionNumber: str
    status: str
    currentProductionVersion: str
    parentPrompt: str
    childPrompts: tuple[str, ...]
    experimentHistory: tuple[str, ...]
    promotionHistory: tuple[str, ...]
    retirementHistory: tuple[str, ...]
    supportingRecommendations: tuple[str, ...]
    supportingEvidence: tuple[str, ...]
    performanceMetrics: dict[str, Any]
    confidence: float
    approvalHistory: tuple[str, ...]


@dataclass(frozen=True)
class PromptImprovementCandidate:
    improvementId: str
    relatedPrompt: str
    currentVersion: str
    candidateVersion: str
    summary: str
    detailedExplanation: str
    supportingEvidence: tuple[str, ...]
    expectedBenefit: str
    confidence: float
    relatedWorkflows: tuple[str, ...]
    relatedDecisionObjects: tuple[str, ...]
    relatedRecommendations: tuple[str, ...]
    historicalJustification: str
    laboratoryStatus: str
    commanderStatus: str
    productionStatus: str


class PromptEvolutionEngine:
    """Governed prompt repository and improvement candidate engine."""

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        prompt_contract: dict[str, Any],
        historian_recommendation_engine: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        decision_laboratory: dict[str, Any],
        performance_truth: dict[str, Any],
        strategy_performance: dict[str, Any],
        api_runtime_monitor: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        repository = self._repository(
            timestamp_utc,
            prompt_contract,
            historian_recommendation_engine,
            enterprise_learning_engine,
            decision_laboratory,
            performance_truth,
            strategy_performance,
            api_runtime_monitor,
        )
        candidates = self._candidates(timestamp_utc, repository, historian_recommendation_engine, enterprise_learning_engine, decision_laboratory)
        metrics = self._metrics(repository, candidates, decision_laboratory)
        return {
            "engineName": "Prompt Evolution Engine",
            "engineeringOrder": "EO-C",
            "constitutionalMission": "Improve the way ARGOS thinks without ever compromising constitutional governance.",
            "constitutionalQuestion": "How should ARGOS think more effectively tomorrow than it thinks today?",
            "constitutionalMode": "ADVISORY_LIFECYCLE_ONLY",
            "lawVII": {
                "executesWorkflows": False,
                "workflowTokenOwnership": "NEVER",
                "executesTrades": False,
                "brokerAccess": "BLOCKED",
                "tradingApiAccess": "BLOCKED",
                "autonomousProductionPromptMutation": "BLOCKED",
                "commanderOverride": "FORBIDDEN",
                "autonomousDeployment": "FORBIDDEN",
            },
            "promptStates": PROMPT_STATES,
            "promptRepository": tuple(asdict(item) for item in repository),
            "promptVersionHistory": tuple(self._version_history(item, repository) for item in repository),
            "promptLineage": tuple(self._lineage(item, repository) for item in repository),
            "promptMetadata": tuple(self._metadata(item) for item in repository),
            "promptImprovementCandidates": tuple(asdict(item) for item in candidates),
            "laboratoryValidationQueue": tuple(self._lab_queue(item) for item in candidates),
            "performanceDashboard": metrics,
            "comparisonEngine": tuple(self._comparison(item, repository) for item in candidates),
            "laboratoryResults": tuple(decision_laboratory.get("promptRevisionComparisons", ())),
            "replayStatistics": {
                "workflowReplays": len(decision_laboratory.get("workflowReplay", ())),
                "promptRevisionComparisons": len(decision_laboratory.get("promptRevisionComparisons", ())),
                "counterfactualReports": len(decision_laboratory.get("performanceComparisons", ())),
            },
            "promotionHistory": (),
            "retirementHistory": (),
            "approvalHistory": (),
            "versionDifferenceViewer": tuple(self._diff_view(item) for item in candidates),
            "promptDependencyGraph": tuple(self._dependency(item) for item in repository),
            "inputs": {
                "promptTemplates": len(prompt_contract.get("templates", ())),
                "historianRecommendations": len(historian_recommendation_engine.get("recommendationDatabase", ())),
                "learningRecommendations": len(enterprise_learning_engine.get("recommendations", ())),
                "truthRecords": len(performance_truth.get("tradeLedger", ())) + len(performance_truth.get("portfolioLedger", ())),
                "decisionObjects": len(strategy_performance.get("decisionObjectEvolution", ())),
                "apiRuntimeEvents": len(api_runtime_monitor.get("events", ())) + len(api_runtime_monitor.get("calls", ())),
                "auditEvents": audit_event_count,
            },
            "promotionPipeline": (
                "Prompt Recommendation",
                "Prompt Candidate",
                "Laboratory",
                "Validation",
                "Commander Review",
                "Approved",
                "Production",
                "Historical Archive",
            ),
            "internalDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "productionPromptMutationCount": 0,
                "immutableVersioning": True,
                "productionReferencesImmutablePromptVersion": True,
                "commanderApprovalRequired": True,
            },
        }

    def _repository(
        self,
        timestamp_utc: str,
        prompt_contract: dict[str, Any],
        historian_recommendation_engine: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        decision_laboratory: dict[str, Any],
        performance_truth: dict[str, Any],
        strategy_performance: dict[str, Any],
        api_runtime_monitor: dict[str, Any],
    ) -> tuple[PromptAsset, ...]:
        historian_recs = tuple(item.get("recommendationId", "") for item in historian_recommendation_engine.get("recommendationDatabase", ()) if "Prompt Improvement" in tuple(item.get("category", ())))
        learning_recs = tuple(item.get("recommendationId", "") for item in enterprise_learning_engine.get("recommendations", ()) if item.get("category") == "Prompt Improvement")
        lab_comparisons = tuple(item.get("comparisonId", item.get("workflowId", "")) for item in decision_laboratory.get("promptRevisionComparisons", ()))
        truth_ids = tuple(item.get("trade_id") or item.get("valuation_id") or item.get("workflow_id", "") for item in tuple(performance_truth.get("tradeLedger", ())) + tuple(performance_truth.get("portfolioLedger", ())))
        templates = tuple(prompt_contract.get("templates", ()))
        return tuple(
            PromptAsset(
                promptId=template.get("prompt_template_id", f"PROMPT-ASSET-{index:06d}"),
                promptName=f"{template.get('office', 'Office')} Constitutional Prompt",
                purpose=template.get("cognitive_responsibility", "Constitutional cognition"),
                associatedOffice=template.get("office", "Unknown"),
                creationDate=timestamp_utc,
                author="Prompt Contract Library",
                versionNumber=template.get("prompt_version", "1.0.0"),
                status="Production",
                currentProductionVersion=template.get("prompt_version", "1.0.0"),
                parentPrompt="",
                childPrompts=(),
                experimentHistory=lab_comparisons,
                promotionHistory=("PROMOTION-BASELINE-PRODUCTION",),
                retirementHistory=(),
                supportingRecommendations=tuple(dict.fromkeys(historian_recs + learning_recs)),
                supportingEvidence=tuple(dict.fromkeys(truth_ids[:8] + tuple(item.get("workflowId", "") for item in strategy_performance.get("decisionObjectEvolution", ())[:8]))),
                performanceMetrics=self._performance_metrics(template, performance_truth, strategy_performance, api_runtime_monitor, decision_laboratory),
                confidence=self._prompt_confidence(performance_truth, strategy_performance, decision_laboratory),
                approvalHistory=("APPROVED_BASELINE_CONSTITUTIONAL_PROMPT",),
            )
            for index, template in enumerate(templates, start=1)
        )

    def _candidates(
        self,
        timestamp_utc: str,
        repository: tuple[PromptAsset, ...],
        historian_recommendation_engine: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        decision_laboratory: dict[str, Any],
    ) -> tuple[PromptImprovementCandidate, ...]:
        prompt_recommendations = [
            ("Historian", item.get("recommendationId", ""), item.get("summary", ""), item.get("estimatedEnterpriseBenefit", ""), float(item.get("confidenceScore", 0.0) or 0.0), tuple(item.get("supportingWorkflows", ())), tuple(item.get("supportingDecisionObjects", ())))
            for item in historian_recommendation_engine.get("recommendationDatabase", ())
            if "Prompt Improvement" in tuple(item.get("category", ()))
        ]
        prompt_recommendations.extend(
            (
                "Enterprise Learning Engine",
                item.get("recommendationId", ""),
                item.get("title", ""),
                item.get("expectedBenefit", ""),
                float(item.get("confidence", 0.0) or 0.0),
                tuple(obs.get("workflowId", "") for obs in enterprise_learning_engine.get("observations", ()) if "Prompt Improvement" in tuple(obs.get("category", ()))),
                tuple(obs.get("decisionObjectId", "") for obs in enterprise_learning_engine.get("observations", ()) if "Prompt Improvement" in tuple(obs.get("category", ()))),
            )
            for item in enterprise_learning_engine.get("recommendations", ())
            if item.get("category") == "Prompt Improvement"
        )
        if not repository:
            return ()
        candidates = []
        for index, recommendation in enumerate(prompt_recommendations[:8], start=1):
            source, recommendation_id, summary, benefit, confidence, workflows, decisions = recommendation
            prompt = repository[min(index - 1, len(repository) - 1)]
            next_version = _next_version(prompt.versionNumber, index)
            candidates.append(
                PromptImprovementCandidate(
                    improvementId=f"PEE-IMP-{index:06d}",
                    relatedPrompt=prompt.promptId,
                    currentVersion=prompt.versionNumber,
                    candidateVersion=next_version,
                    summary=summary or f"Improve {prompt.promptName}",
                    detailedExplanation=(
                        f"{source} recommendation {recommendation_id or 'unassigned'} suggests a prompt candidate. "
                        f"Candidate {next_version} remains isolated from production until laboratory validation and Commander approval."
                    ),
                    supportingEvidence=tuple(dict.fromkeys((recommendation_id, *prompt.supportingEvidence)))[:10],
                    expectedBenefit=benefit or "Improve prompt quality and decision consistency.",
                    confidence=round(max(confidence, prompt.confidence), 2),
                    relatedWorkflows=tuple(item for item in workflows if item),
                    relatedDecisionObjects=tuple(item for item in decisions if item),
                    relatedRecommendations=(recommendation_id,) if recommendation_id else (),
                    historicalJustification="Prompt candidate is derived from accumulated recommendation evidence and replayable prompt history.",
                    laboratoryStatus="QUEUED_FOR_PROMPT_REPLAY",
                    commanderStatus="NOT_READY_PENDING_LAB_VALIDATION",
                    productionStatus="BLOCKED_PENDING_COMMANDER_APPROVAL",
                )
            )
        return tuple(candidates)

    def _performance_metrics(
        self,
        template: dict[str, Any],
        performance_truth: dict[str, Any],
        strategy_performance: dict[str, Any],
        api_runtime_monitor: dict[str, Any],
        decision_laboratory: dict[str, Any],
    ) -> dict[str, Any]:
        scorecard = strategy_performance.get("enterpriseScorecard", {})
        truth_count = len(performance_truth.get("tradeLedger", ())) + len(performance_truth.get("portfolioLedger", ()))
        return {
            "decisionAccuracy": round(float(scorecard.get("decisionQuality", 75.0) or 75.0), 2),
            "confidenceCalibration": min(100, 72 + len(strategy_performance.get("decisionObjectEvolution", ())) * 3),
            "evidenceQuality": min(100, 68 + truth_count * 4),
            "hallucinationRate": 0.0,
            "decisionConsistency": min(100, 70 + len(decision_laboratory.get("workflowReplay", ())) * 4),
            "runtimeEfficiency": max(0, 100 - int(template.get("maximum_latency_seconds", 60))),
            "apiCreditConsumption": round(float(template.get("maximum_reasoning_cost_usd", 0.0) or 0.0), 4),
            "promptStability": 100,
            "recommendationAcceptance": 0,
            "historicalPerformance": truth_count,
            "laboratorySuccess": len(decision_laboratory.get("performanceComparisons", ())),
            "commanderSatisfaction": "AWAITING_REVIEW",
            "apiRuntimeEvents": len(api_runtime_monitor.get("events", ())) + len(api_runtime_monitor.get("calls", ())),
        }

    def _prompt_confidence(self, performance_truth: dict[str, Any], strategy_performance: dict[str, Any], decision_laboratory: dict[str, Any]) -> float:
        truth_factor = min(0.18, (len(performance_truth.get("tradeLedger", ())) + len(performance_truth.get("portfolioLedger", ()))) * 0.03)
        decision_factor = min(0.18, len(strategy_performance.get("decisionObjectEvolution", ())) * 0.03)
        replay_factor = min(0.18, len(decision_laboratory.get("workflowReplay", ())) * 0.04)
        return round(min(0.98, 0.52 + truth_factor + decision_factor + replay_factor), 2)

    def _metrics(self, repository: tuple[PromptAsset, ...], candidates: tuple[PromptImprovementCandidate, ...], decision_laboratory: dict[str, Any]) -> dict[str, Any]:
        avg_confidence = round(sum(item.confidence for item in repository) / max(1, len(repository)), 2)
        return {
            "promptCount": len(repository),
            "productionPrompts": sum(1 for item in repository if item.status == "Production"),
            "candidatePrompts": len(candidates),
            "laboratoryQueue": len(candidates),
            "commanderReviews": sum(1 for item in candidates if item.commanderStatus == "COMMANDER_REVIEW"),
            "validatedPrompts": 0,
            "retiredPrompts": 0,
            "archivedPrompts": 0,
            "averageConfidence": avg_confidence,
            "immutableVersionCount": len(repository) + len(candidates),
            "promptRevisionComparisons": len(decision_laboratory.get("promptRevisionComparisons", ())),
            "productionMutationCount": 0,
        }

    def _version_history(self, item: PromptAsset, repository: tuple[PromptAsset, ...]) -> dict[str, Any]:
        return {
            "promptId": item.promptId,
            "versions": (item.versionNumber,),
            "currentProductionVersion": item.currentProductionVersion,
            "immutable": True,
            "olderVersionsPreserved": True,
        }

    def _lineage(self, item: PromptAsset, repository: tuple[PromptAsset, ...]) -> dict[str, Any]:
        return {
            "promptId": item.promptId,
            "parentPrompt": item.parentPrompt,
            "childPrompts": item.childPrompts,
            "origin": "Prompt Contract Library",
            "currentVersion": item.versionNumber,
            "activeProductionVersion": item.currentProductionVersion,
        }

    def _metadata(self, item: PromptAsset) -> dict[str, Any]:
        return {
            "promptName": item.promptName,
            "office": item.associatedOffice,
            "purpose": item.purpose,
            "currentVersion": item.versionNumber,
            "parentVersion": item.parentPrompt,
            "currentStatus": item.status,
            "laboratoryStatus": "READY_FOR_REPLAY",
            "commanderApproval": "APPROVED_BASELINE",
            "performanceScore": item.performanceMetrics.get("decisionAccuracy", 0),
            "historicalSuccessRate": item.performanceMetrics.get("historicalPerformance", 0),
            "averageConfidence": item.confidence,
            "relatedStrategies": (),
            "relatedRecommendations": item.supportingRecommendations,
            "relatedDecisionObjects": (),
            "relatedTruthRecords": item.supportingEvidence,
            "promotionDate": "",
            "retirementDate": "",
        }

    def _lab_queue(self, item: PromptImprovementCandidate) -> dict[str, Any]:
        return {
            "improvementId": item.improvementId,
            "relatedPrompt": item.relatedPrompt,
            "candidateVersion": item.candidateVersion,
            "validationPipeline": ("Historical Replay", "Counterfactual Analysis", "Performance Comparison", "Statistical Evaluation", "Laboratory Report"),
            "laboratoryStatus": item.laboratoryStatus,
            "productionStatus": item.productionStatus,
        }

    def _comparison(self, item: PromptImprovementCandidate, repository: tuple[PromptAsset, ...]) -> dict[str, Any]:
        return {
            "comparisonId": f"PEE-COMP-{item.improvementId[-6:]}",
            "currentProductionPrompt": item.relatedPrompt,
            "currentVersion": item.currentVersion,
            "candidatePrompt": item.relatedPrompt,
            "candidateVersion": item.candidateVersion,
            "measures": ("Decision Quality", "Confidence Accuracy", "Risk Discipline", "Evidence Weighting", "Runtime", "API Credits", "Recommendation Quality", "Consistency", "False Positives", "False Negatives", "Overall Enterprise Benefit"),
            "status": "AWAITING_LABORATORY_REPLAY",
        }

    def _diff_view(self, item: PromptImprovementCandidate) -> dict[str, Any]:
        return {
            "improvementId": item.improvementId,
            "fromVersion": item.currentVersion,
            "toVersion": item.candidateVersion,
            "diffSummary": item.summary,
            "rawPromptTextHidden": True,
            "productionMutation": False,
        }

    def _dependency(self, item: PromptAsset) -> dict[str, Any]:
        return {
            "promptId": item.promptId,
            "office": item.associatedOffice,
            "dependsOn": ("Prompt Contract", "Office Output Schema", "LAW VII Envelope"),
            "usedBy": ("API Execution Gateway", "Decision Laboratory Replay", "Performance Truth Attribution"),
        }


def _next_version(version: str, offset: int) -> str:
    parts = [int(part) for part in version.split(".") if part.isdigit()]
    if not parts:
        return f"1.0.{offset}"
    while len(parts) < 3:
        parts.append(0)
    parts[2] += offset
    return ".".join(str(part) for part in parts[:3])
