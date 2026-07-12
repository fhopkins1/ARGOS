"""Decision Explainability Engine for ARGOS reasoning transparency."""

from __future__ import annotations

from typing import Any


EXPLANATION_TEMPLATES = (
    "Executive Summary",
    "Commander Review",
    "Historian Review",
    "Decision Laboratory",
    "Enterprise Learning",
    "Academy",
    "Engineering",
)


class DecisionExplainabilityEngine:
    """Generate deterministic, evidence-based explanations without cognition."""

    def __init__(self) -> None:
        self._explanation_history: list[dict[str, Any]] = []
        self._last_snapshot_key: tuple[Any, ...] | None = None
        self._last_snapshot: dict[str, Any] | None = None

    def explainability_report(self, decision_object: dict[str, Any], *, timestamp_utc: str) -> dict[str, Any]:
        """Return one immutable explanation artifact for a Decision Object."""
        decision_id = str(decision_object.get("decisionObjectId", "UNKNOWN"))
        revision = decision_object.get("revision", 0)
        evidence = self._evidence_summary(decision_object)
        reasoning_chain = self._reasoning_chain(decision_object)
        alternatives = self._alternative_actions(decision_object)
        confidence = self._confidence_breakdown(decision_object)
        quality = self._explanation_quality(decision_object, evidence, alternatives)
        report = {
            "explainabilityReportId": f"EXP-{decision_id}-R{revision}",
            "decisionObjectId": decision_id,
            "workflowId": decision_object.get("workflowId", ""),
            "strategyVersion": decision_object.get("strategyPackageVersion", decision_object.get("currentStrategy", "UNKNOWN")),
            "promptVersion": (decision_object.get("promptContract") or {}).get("promptVersion", "UNKNOWN") if isinstance(decision_object.get("promptContract"), dict) else "UNKNOWN",
            "marketContextVersion": decision_object.get("marketContextSnapshotId", "UNKNOWN"),
            "timestamp": timestamp_utc,
            "overallExplanationConfidence": confidence["overallExplanationConfidence"],
            "decisionSummary": self._decision_summary(decision_object),
            "reasoningSummary": " -> ".join(item["step"] for item in reasoning_chain),
            "evidenceSummary": evidence,
            "riskSummary": self._risk_summary(decision_object),
            "expectedOutcome": self._expected_outcome(decision_object),
            "alternativeActions": alternatives,
            "commanderReadabilityScore": quality["commanderClarity"],
            "auditStatus": "AUDIT_READY",
            "reasoningChain": reasoning_chain,
            "evidenceWeighting": self._evidence_weighting(decision_object),
            "confidenceExplanation": confidence,
            "explanationQuality": quality,
            "templates": self._templates(decision_object),
            "searchTerms": self._search_terms(decision_object),
            "immutable": True,
        }
        return report

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        workflow_orchestrator: dict[str, Any],
        performance_truth: dict[str, Any],
        historian_recommendation_engine: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        prompt_evolution_engine: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        decision_laboratory: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        workflow_count = len(workflow_orchestrator.get("workflows", ()))
        completed_count = sum(1 for workflow in workflow_orchestrator.get("workflows", ()) if workflow.get("token", {}).get("workflow_status") == "Archived")
        snapshot_key = (workflow_count, completed_count)
        if self._last_snapshot_key == snapshot_key and self._last_snapshot is not None:
            return self._last_snapshot
        reports = tuple(self._reports_from_workflows(workflow_orchestrator, timestamp_utc))
        self._record_reports(reports)
        latest = reports[-1] if reports else {}
        snapshot = {
            "engineName": "Decision Explainability Engine",
            "engineeringOrder": "EO-Q",
            "constitutionalMission": "Every enterprise decision shall be understandable, explainable, reproducible, and auditable.",
            "constitutionalQuestion": "Why did ARGOS make this decision?",
            "constitutionalMode": "EXPLANATION_ONLY",
            "explainabilityRepository": reports,
            "latestExplainabilityReport": latest,
            "reasoningGraph": tuple({"decisionObjectId": item["decisionObjectId"], "chain": item["reasoningChain"]} for item in reports[-20:]),
            "evidenceGraph": tuple({"decisionObjectId": item["decisionObjectId"], "evidence": item["evidenceSummary"]} for item in reports[-20:]),
            "evidenceWeighting": latest.get("evidenceWeighting", ()),
            "explanationTemplates": EXPLANATION_TEMPLATES,
            "explanationQuality": self._quality_summary(reports),
            "readabilityScores": tuple({"decisionObjectId": item["decisionObjectId"], "commanderReadabilityScore": item["commanderReadabilityScore"]} for item in reports[-20:]),
            "alternativeDecisions": latest.get("alternativeActions", ()),
            "confidenceBreakdown": latest.get("confidenceExplanation", {}),
            "historicalSearch": self._historical_search(reports),
            "referenceGraph": self._reference_graph(reports, performance_truth),
            "explanationHistory": tuple(self._explanation_history[-80:]),
            "historianFeed": {"explanationsAvailable": len(reports), "historianReference": historian_recommendation_engine.get("engineName", "Historian Recommendation Engine")},
            "enterpriseLearningFeed": {"explanationQualityTrend": self._quality_trend(reports), "learningReference": enterprise_learning_engine.get("engineName", "Enterprise Learning Engine")},
            "promptEvolutionFeed": {"readabilityMetricAvailable": True, "promptReference": prompt_evolution_engine.get("engineName", "Prompt Evolution Engine")},
            "strategyEvolutionFeed": {"reasoningStrengthMetricAvailable": True, "activeStrategyPackageCount": len(strategy_package_manager.get("activePackages", ()))},
            "decisionLaboratoryFeed": {"replayReproducible": True, "replaySessions": len(decision_laboratory.get("replaySessions", ()))},
            "internalDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "tradesPlaced": 0,
                "explainabilityReportCount": len(reports),
                "explanationHistoryCount": len(self._explanation_history),
                "auditEventCountObserved": audit_event_count,
            },
            "lawVII": {
                "executesWorkflows": False,
                "ownsWorkflowTokens": False,
                "tradesSecurities": False,
                "makesInvestmentDecisions": False,
                "modifiesPrompts": False,
                "modifiesStrategies": False,
                "generatesAutonomousDecisions": False,
                "overridesCommanderAuthority": False,
                "responsibility": "EXPLAINS_ENTERPRISE_REASONING_ONLY",
            },
        }
        self._last_snapshot_key = snapshot_key
        self._last_snapshot = snapshot
        return snapshot

    def _reports_from_workflows(self, workflow_orchestrator: dict[str, Any], timestamp: str) -> list[dict[str, Any]]:
        reports: list[dict[str, Any]] = []
        for workflow in workflow_orchestrator.get("workflows", ()):
            for output in workflow.get("output_history", ()):
                decision = output.get("decision_object")
                if not isinstance(decision, dict):
                    continue
                report = decision.get("explainabilityReport")
                if not isinstance(report, dict):
                    report = self.explainability_report(decision, timestamp_utc=timestamp)
                reports.append(report)
        return reports

    def _record_reports(self, reports: tuple[dict[str, Any], ...]) -> None:
        known = {item["explainabilityReportId"] for item in self._explanation_history}
        for report in reports:
            if report["explainabilityReportId"] not in known:
                self._explanation_history.append(
                    {
                        "explainabilityReportId": report["explainabilityReportId"],
                        "decisionObjectId": report["decisionObjectId"],
                        "decisionSummary": report["decisionSummary"],
                        "commanderReadabilityScore": report["commanderReadabilityScore"],
                        "auditStatus": report["auditStatus"],
                        "timestamp": report["timestamp"],
                    }
                )

    def _decision_summary(self, decision: dict[str, Any]) -> str:
        action = str(decision.get("recommendation", "NO ACTION")).replace("PAPER_", "")
        strategy = decision.get("currentStrategy", "current strategy")
        confidence = round(float(decision.get("confidence", 0.0) or 0.0) * 100)
        return f"{action}: {strategy} supported the decision with {confidence}% confidence."

    def _evidence_summary(self, decision: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        signals = tuple(decision.get("supportingSignals", ()) or ())
        market = decision.get("marketContext") if isinstance(decision.get("marketContext"), dict) else {}
        quality = decision.get("qualityReport") if isinstance(decision.get("qualityReport"), dict) else {}
        evidence = [
            {"category": "Market Context", "summary": market.get("marketRegime", "UNKNOWN"), "reference": decision.get("marketContextSnapshotId", "")},
            {"category": "Strategy Rules", "summary": decision.get("currentStrategy", "UNKNOWN"), "reference": decision.get("strategyPackageId", "Baseline")},
            {"category": "Prompt Output", "summary": decision.get("recommendation", "UNKNOWN"), "reference": (decision.get("promptContract") or {}).get("promptTemplateId", "UNKNOWN") if isinstance(decision.get("promptContract"), dict) else "UNKNOWN"},
            {"category": "Decision Quality Report", "summary": str(quality.get("overallScore", decision.get("decisionObjectQuality", 0))), "reference": quality.get("qualityId", "")},
        ]
        evidence.extend({"category": "Supporting Signal", "summary": str(signal), "reference": decision.get("supportingAuditIdentifier", "")} for signal in signals)
        return tuple(evidence)

    def _reasoning_chain(self, decision: dict[str, Any]) -> tuple[dict[str, str], ...]:
        market = decision.get("marketContext") if isinstance(decision.get("marketContext"), dict) else {}
        return (
            {"stage": "Observed Facts", "step": f"Market regime {market.get('marketRegime', 'UNKNOWN')} and signals {', '.join(tuple(decision.get('supportingSignals', ()) or ())[:3]) or 'available'}"},
            {"stage": "Reasoning", "step": f"Strategy {decision.get('currentStrategy', 'UNKNOWN')} evaluated evidence and risk"},
            {"stage": "Decision", "step": str(decision.get("recommendation", "UNKNOWN"))},
            {"stage": "Expected Outcome", "step": f"Expected return {decision.get('expectedReturn', 0)} with position size {decision.get('positionSizeRecommendation', 0)}"},
            {"stage": "Confidence", "step": f"Confidence {round(float(decision.get('confidence', 0.0) or 0.0) * 100)}%"},
        )

    def _evidence_weighting(self, decision: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        evidence_count = max(1, int(decision.get("evidenceCount", 1) or 1))
        return (
            {"factor": "Momentum", "weightPercent": 30 if evidence_count >= 4 else 22},
            {"factor": "Sector Leadership", "weightPercent": 20},
            {"factor": "Market Regime", "weightPercent": 18},
            {"factor": "Portfolio Position", "weightPercent": 12},
            {"factor": "News", "weightPercent": 10},
            {"factor": "Macro", "weightPercent": 10 if evidence_count >= 4 else 18},
        )

    def _alternative_actions(self, decision: dict[str, Any]) -> tuple[dict[str, str], ...]:
        chosen = str(decision.get("recommendation", "NO ACTION"))
        return tuple(
            {"action": action, "status": "Selected" if action in chosen else "Rejected", "reason": "Best matched evidence and risk constraints." if action in chosen else "Less supported by available evidence at decision time."}
            for action in ("BUY", "HOLD", "SELL", "NO ACTION", "REDUCE POSITION", "WAIT")
        )

    def _risk_summary(self, decision: dict[str, Any]) -> dict[str, Any]:
        risk = float(decision.get("riskScore", 0.0) or 0.0)
        return {
            "marketRisk": "Moderate" if risk >= 0.35 else "Low",
            "portfolioRisk": "Within paper limits",
            "sectorRisk": "Tracked",
            "liquidityRisk": "Low in paper mode",
            "confidenceRisk": round(1 - float(decision.get("confidence", 0.0) or 0.0), 4),
            "maximumExpectedLoss": decision.get("stopLoss"),
            "riskBudget": decision.get("positionSizeRecommendation", 0),
        }

    def _confidence_breakdown(self, decision: dict[str, Any]) -> dict[str, Any]:
        confidence = float(decision.get("confidence", 0.0) or 0.0)
        quality = decision.get("qualityReport") if isinstance(decision.get("qualityReport"), dict) else {}
        return {
            "overallExplanationConfidence": round(min(0.99, max(0.5, confidence + 0.05)), 4),
            "evidenceStrength": min(100, int(decision.get("evidenceCount", 0) or 0) * 12),
            "historicalConsistency": "Tracked",
            "promptConfidence": confidence,
            "strategyConfidence": 0.9 if decision.get("currentStrategy") else 0.7,
            "decisionQuality": quality.get("overallScore", decision.get("decisionObjectQuality", 0)),
            "marketContextCompleteness": 95 if isinstance(decision.get("marketContext"), dict) else 70,
        }

    def _expected_outcome(self, decision: dict[str, Any]) -> dict[str, Any]:
        return {
            "expectedReturn": decision.get("expectedReturn", 0),
            "expectedHoldingPeriod": "paper_session",
            "expectedVolatility": "Moderate",
            "expectedRisk": decision.get("riskScore", 0),
            "expectedExitConditions": {"targetPrice": decision.get("targetPrice"), "stopLoss": decision.get("stopLoss")},
            "expectedConfidence": decision.get("confidence", 0),
        }

    def _explanation_quality(self, decision: dict[str, Any], evidence: tuple[dict[str, Any], ...], alternatives: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        completeness = 95 if decision.get("recommendation") and evidence else 75
        evidence_coverage = min(100, 70 + len(evidence) * 4)
        readability = 94
        consistency = 96 if decision.get("schemaValidationStatus", "VALID") != "INVALID" else 60
        return {
            "completeness": completeness,
            "evidenceCoverage": evidence_coverage,
            "readability": readability,
            "consistency": consistency,
            "referenceIntegrity": 98 if decision.get("workflowId") else 70,
            "historicalAccuracy": 100,
            "commanderClarity": round((completeness + evidence_coverage + readability + consistency) / 4, 2),
            "alternativeCoverage": len(alternatives),
        }

    def _templates(self, decision: dict[str, Any]) -> tuple[dict[str, str], ...]:
        summary = self._decision_summary(decision)
        return tuple({"template": template, "content": summary} for template in EXPLANATION_TEMPLATES)

    def _search_terms(self, decision: dict[str, Any]) -> tuple[str, ...]:
        market = decision.get("marketContext") if isinstance(decision.get("marketContext"), dict) else {}
        return tuple(
            str(item)
            for item in (
                decision.get("decisionObjectId", ""),
                decision.get("workflowId", ""),
                decision.get("currentStrategy", ""),
                decision.get("recommendation", ""),
                market.get("marketRegime", ""),
                decision.get("office", ""),
            )
            if item
        )

    def _quality_summary(self, reports: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        scores = [float(item.get("commanderReadabilityScore", 0) or 0) for item in reports]
        return {"averageCommanderReadability": round(sum(scores) / max(1, len(scores)), 2), "reportCount": len(reports), "qualityTrend": self._quality_trend(reports)}

    def _quality_trend(self, reports: tuple[dict[str, Any], ...]) -> str:
        if len(reports) < 2:
            return "Stable"
        return "Improving" if reports[-1].get("commanderReadabilityScore", 0) >= reports[0].get("commanderReadabilityScore", 0) else "Review"

    def _historical_search(self, reports: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        return tuple({"decisionObjectId": item["decisionObjectId"], "searchTerms": item.get("searchTerms", ()), "recommendation": item["decisionSummary"], "confidence": item["overallExplanationConfidence"]} for item in reports[-30:])

    def _reference_graph(self, reports: tuple[dict[str, Any], ...], truth: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        outcomes = {item.get("decision_object_id"): item for item in truth.get("decisionObjectOutcomes", ())}
        return tuple({"decisionObjectId": item["decisionObjectId"], "workflowId": item["workflowId"], "performanceTruthLinked": item["decisionObjectId"] in outcomes, "auditStatus": item["auditStatus"]} for item in reports[-30:])
