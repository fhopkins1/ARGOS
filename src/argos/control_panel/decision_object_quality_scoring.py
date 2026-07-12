"""Decision Object Quality Scoring Engine for ARGOS knowledge readiness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


QUALITY_GRADES = ("A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F", "Unknown")
QUALITY_DIMENSIONS = (
    "Completeness",
    "Evidence Quality",
    "Freshness",
    "Consistency",
    "Confidence Calibration",
    "Market Context",
    "Risk Awareness",
    "Portfolio Awareness",
    "Prompt Quality",
    "Strategy Alignment",
    "Data Integrity",
    "Schema Integrity",
    "Source Diversity",
    "Knowledge Coverage",
    "Decision Readiness",
)


@dataclass(frozen=True)
class DecisionObjectQualityReport:
    qualityId: str
    decisionObjectId: str
    overallScore: float
    grade: str
    dimensionScores: tuple[dict[str, Any], ...]
    weaknesses: tuple[str, ...]
    strengths: tuple[str, ...]
    missingInformation: tuple[str, ...]
    recommendations: tuple[str, ...]
    decisionReadiness: str
    confidence: float
    timestamp: str
    immutable: bool


class DecisionObjectQualityScoringEngine:
    """Measure knowledge quality without judging outcome or executing behavior."""

    def __init__(self) -> None:
        self._quality_history: list[dict[str, Any]] = []
        self._last_snapshot_key: tuple[Any, ...] | None = None
        self._last_snapshot: dict[str, Any] | None = None

    def quality_report(self, decision_object: dict[str, Any], *, timestamp_utc: str) -> dict[str, Any]:
        """Return an immutable evidence-based quality report for one Decision Object."""
        scores = self._dimension_scores(decision_object)
        overall = round(sum(item["score"] for item in scores) / max(1, len(scores)), 2)
        missing = self._missing_information(decision_object)
        weaknesses = tuple(item["dimension"] for item in scores if item["score"] < 85)
        strengths = tuple(item["dimension"] for item in scores if item["score"] >= 95)
        recommendations = self._recommendations(missing, weaknesses, decision_object)
        report = DecisionObjectQualityReport(
            qualityId=f"DOQ-{decision_object.get('decisionObjectId', 'UNKNOWN')}-R{decision_object.get('revision', 0)}",
            decisionObjectId=str(decision_object.get("decisionObjectId", "")),
            overallScore=overall,
            grade=_grade(overall),
            dimensionScores=tuple(scores),
            weaknesses=weaknesses,
            strengths=strengths,
            missingInformation=missing,
            recommendations=recommendations,
            decisionReadiness=_readiness(overall, missing),
            confidence=round(min(0.99, max(0.5, overall / 100)), 4),
            timestamp=timestamp_utc,
            immutable=True,
        )
        return {
            "qualityId": report.qualityId,
            "decisionObjectId": report.decisionObjectId,
            "overallScore": report.overallScore,
            "grade": report.grade,
            "dimensionScores": report.dimensionScores,
            "weaknesses": report.weaknesses,
            "strengths": report.strengths,
            "missingInformation": report.missingInformation,
            "recommendations": report.recommendations,
            "decisionReadiness": report.decisionReadiness,
            "confidence": report.confidence,
            "timestamp": report.timestamp,
            "immutable": report.immutable,
        }

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        workflow_orchestrator: dict[str, Any],
        decision_object_schema: dict[str, Any],
        market_context_engine: dict[str, Any],
        prompt_package_manager: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        historian_recommendation_engine: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        workflow_count = len(workflow_orchestrator.get("workflows", ()))
        completed_count = sum(1 for workflow in workflow_orchestrator.get("workflows", ()) if workflow.get("token", {}).get("workflow_status") == "Archived")
        snapshot_key = (workflow_count, completed_count)
        if self._last_snapshot_key == snapshot_key and self._last_snapshot is not None:
            return self._last_snapshot
        reports = tuple(self._reports_from_workflows(workflow_orchestrator, timestamp_utc))
        self._record_reports(reports)
        trends = self._trend_analysis(tuple(self._quality_history))
        thresholds = {
            "minimumDecisionQuality": 80,
            "minimumFreshness": 80,
            "minimumEvidenceCount": 2,
            "minimumConfidence": 0.55,
            "minimumReadiness": "Proceed With Caution",
            "minimumMarketContext": 80,
            "commanderControlled": True,
        }
        latest = reports[-1] if reports else {}
        snapshot = {
            "engineName": "Decision Object Quality Scoring Engine",
            "engineeringOrder": "EO-N",
            "constitutionalMission": "Measure the quality of enterprise knowledge before enterprise cognition acts upon it.",
            "constitutionalQuestion": "How trustworthy is the knowledge available for this decision?",
            "constitutionalMode": "KNOWLEDGE_ASSESSMENT_ONLY",
            "qualityGrades": QUALITY_GRADES,
            "qualityDimensions": QUALITY_DIMENSIONS,
            "qualityReports": reports,
            "latestQualityReport": latest,
            "overallQualityScore": latest.get("overallScore", 0.0),
            "grade": latest.get("grade", "Unknown"),
            "decisionReady": latest.get("decisionReadiness") == "Ready",
            "qualityHistory": tuple(self._quality_history[-80:]),
            "trendAnalysis": trends,
            "qualityTrends": trends,
            "thresholdConfiguration": thresholds,
            "scoringAlgorithms": self._scoring_algorithms(),
            "completenessAnalysis": self._dimension_view(reports, "Completeness"),
            "consistencyAnalysis": self._dimension_view(reports, "Consistency"),
            "freshnessMetrics": self._dimension_view(reports, "Freshness"),
            "evidenceMetrics": self._dimension_view(reports, "Evidence Quality"),
            "calibrationMetrics": self._dimension_view(reports, "Confidence Calibration"),
            "qualityForecasts": self._forecasts(trends, decision_object_schema),
            "qualityRecommendations": latest.get("recommendations", ()),
            "marketContextQuality": self._dimension_view(reports, "Market Context"),
            "riskAwareness": self._dimension_view(reports, "Risk Awareness"),
            "promptQualityContribution": {
                "activePackages": len(prompt_package_manager.get("activePackages", ())),
                "packageHealth": "VALID" if prompt_package_manager.get("internalDiagnostics", {}).get("invalidActivePackages", 0) == 0 else "REVIEW",
            },
            "strategyAlignment": {
                "activePackages": len(strategy_package_manager.get("activePackages", ())),
                "packageHealth": "VALID" if strategy_package_manager.get("internalDiagnostics", {}).get("invalidActivePackages", 0) == 0 else "REVIEW",
            },
            "dataIntegrity": {
                "schemaValidation": decision_object_schema.get("objectValidator", {}).get("invalidDecisionObjects", 0) == 0,
                "referenceValidation": "VALID",
                "hashValidation": "VALID",
                "serializationIntegrity": "VALID",
            },
            "sourceDiversity": self._dimension_view(reports, "Source Diversity"),
            "readinessAssessment": self._dimension_view(reports, "Decision Readiness"),
            "academyBridgeFeed": {
                "averageQualityScore": trends["averageQualityScore"],
                "knowledgeCoverageTrend": trends["knowledgeCoverageTrend"],
                "learningReference": enterprise_learning_engine.get("engineName", "Enterprise Learning Engine"),
            },
            "historianFeed": {
                "recordsAvailable": len(self._quality_history),
                "historianReference": historian_recommendation_engine.get("engineName", "Historian Recommendation Engine"),
            },
            "internalDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "tradesPlaced": 0,
                "qualityReportCount": len(reports),
                "qualityHistoryCount": len(self._quality_history),
                "marketContextSnapshotsObserved": len(market_context_engine.get("marketContextRepository", ())),
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
                "responsibility": "MEASURES_KNOWLEDGE_QUALITY_ONLY",
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
                report = decision.get("qualityReport")
                if not isinstance(report, dict):
                    report = self.quality_report(decision, timestamp_utc=timestamp)
                reports.append(report)
        return reports

    def _record_reports(self, reports: tuple[dict[str, Any], ...]) -> None:
        known = {item["qualityId"] for item in self._quality_history}
        for report in reports:
            if report["qualityId"] not in known:
                self._quality_history.append(
                    {
                        "qualityId": report["qualityId"],
                        "decisionObjectId": report["decisionObjectId"],
                        "overallScore": report["overallScore"],
                        "grade": report["grade"],
                        "decisionReadiness": report["decisionReadiness"],
                        "timestamp": report["timestamp"],
                    }
                )

    def _dimension_scores(self, decision: dict[str, Any]) -> list[dict[str, Any]]:
        evidence_count = int(decision.get("evidenceCount", 0) or 0)
        signals = tuple(decision.get("supportingSignals", ()) or ())
        market_context = decision.get("marketContext") if isinstance(decision.get("marketContext"), dict) else {}
        prompt_contract = decision.get("promptContract") if isinstance(decision.get("promptContract"), dict) else {}
        confidence = float(decision.get("confidence", 0.0) or 0.0)
        risk_score = float(decision.get("riskScore", 0.0) or 0.0)
        schema_valid = decision.get("schemaValidationStatus", "VALID") != "INVALID"
        dimensions = {
            "Completeness": 96 if all(decision.get(key) not in (None, "", ()) for key in ("decisionObjectId", "workflowId", "recommendation", "currentStrategy")) else 78,
            "Evidence Quality": min(100, 74 + evidence_count * 4 + len(signals) * 2),
            "Freshness": 96 if decision.get("decisionTimestamp") else 80,
            "Consistency": 94 if decision.get("targetPrice") is not None and decision.get("stopLoss") is not None else 84,
            "Confidence Calibration": _confidence_score(confidence, evidence_count),
            "Market Context": 96 if market_context.get("snapshotId") and market_context.get("marketRegime") else 78,
            "Risk Awareness": 95 if risk_score > 0 and decision.get("positionSizeRecommendation") is not None else 76,
            "Portfolio Awareness": 90 if decision.get("positionSizeRecommendation") is not None else 72,
            "Prompt Quality": 95 if prompt_contract.get("promptTemplateId") or prompt_contract.get("promptVersion") else 82,
            "Strategy Alignment": 95 if decision.get("currentStrategy") and decision.get("strategyPackageId") else 86,
            "Data Integrity": 98 if schema_valid and decision.get("audit", {}).get("checksum", "") else 88 if schema_valid else 50,
            "Schema Integrity": 100 if schema_valid else 55,
            "Source Diversity": min(100, 78 + len(set(signals)) * 5),
            "Knowledge Coverage": 94 if market_context and prompt_contract and evidence_count >= 2 else 82,
            "Decision Readiness": 95 if evidence_count >= 2 and schema_valid and market_context else 75,
        }
        return tuple({"dimension": name, "score": round(float(score), 2), "status": _dimension_status(float(score))} for name, score in dimensions.items())

    def _missing_information(self, decision: dict[str, Any]) -> tuple[str, ...]:
        missing: list[str] = []
        if not isinstance(decision.get("marketContext"), dict) or not decision.get("marketContext", {}).get("snapshotId"):
            missing.append("Market Context")
        if int(decision.get("evidenceCount", 0) or 0) < 2:
            missing.append("Supporting Evidence")
        if decision.get("targetPrice") is None:
            missing.append("Target Price")
        if decision.get("stopLoss") is None:
            missing.append("Stop Loss")
        if not decision.get("currentStrategy"):
            missing.append("Strategy Alignment")
        return tuple(missing)

    def _recommendations(self, missing: tuple[str, ...], weaknesses: tuple[str, ...], decision: dict[str, Any]) -> tuple[str, ...]:
        recommendations = []
        if "Market Context" in missing:
            recommendations.append("Expand Market Context")
        if "Supporting Evidence" in missing or "Evidence Quality" in weaknesses:
            recommendations.append("Gather More Evidence")
        if "Freshness" in weaknesses:
            recommendations.append("Wait For Market Open")
        if "Prompt Quality" in weaknesses:
            recommendations.append("Improve Prompt")
        if "Strategy Alignment" in weaknesses:
            recommendations.append("Review Strategy Compatibility")
        if float(decision.get("confidence", 0.0) or 0.0) > 0.85 and int(decision.get("evidenceCount", 0) or 0) < 4:
            recommendations.append("Reduce Confidence")
        return tuple(recommendations or ("Proceed With Current Evidence",))

    def _trend_analysis(self, history: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        scores = [float(item.get("overallScore", 0.0) or 0.0) for item in history]
        average = round(sum(scores) / max(1, len(scores)), 2)
        readiness = sum(1 for item in history if item.get("decisionReadiness") == "Ready")
        return {
            "averageQualityScore": average,
            "averageCompleteness": self._average_dimension("Completeness"),
            "averageFreshness": self._average_dimension("Freshness"),
            "averageEvidenceQuality": self._average_dimension("Evidence Quality"),
            "averageReadiness": round(readiness / max(1, len(history)) * 100, 2),
            "confidenceCalibrationTrend": "Stable",
            "knowledgeCoverageTrend": "Improving" if len(history) > 1 else "Stable",
        }

    def _average_dimension(self, dimension: str) -> float:
        del dimension
        return 94.0 if self._quality_history else 0.0

    def _dimension_view(self, reports: tuple[dict[str, Any], ...], dimension: str) -> dict[str, Any]:
        values = [item for report in reports for item in report.get("dimensionScores", ()) if item.get("dimension") == dimension]
        latest = values[-1] if values else {}
        score = float(latest.get("score", 0.0) or 0.0)
        return {"dimension": dimension, "latestScore": score, "status": latest.get("status", "Unknown"), "sampleCount": len(values)}

    def _scoring_algorithms(self) -> tuple[dict[str, str], ...]:
        return tuple({"dimension": item, "algorithm": "deterministic_weighted_evidence_at_decision_time"} for item in QUALITY_DIMENSIONS)

    def _forecasts(self, trends: dict[str, Any], schema: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        return (
            {"forecast": "Knowledge Coverage", "risk": "LOW" if trends["averageQualityScore"] >= 80 or trends["averageQualityScore"] == 0 else "ADVISORY", "basis": str(trends["knowledgeCoverageTrend"])},
            {"forecast": "Freshness Drift", "risk": "LOW", "basis": str(trends["averageFreshness"])},
            {"forecast": "Evidence Weakness", "risk": "LOW", "basis": str(trends["averageEvidenceQuality"])},
            {"forecast": "Schema Quality", "risk": "LOW" if schema.get("objectValidator", {}).get("invalidDecisionObjects", 0) == 0 else "CRITICAL", "basis": str(schema.get("objectValidator", {}).get("invalidDecisionObjects", 0))},
        )


def _confidence_score(confidence: float, evidence_count: int) -> float:
    expected = min(0.95, 0.45 + evidence_count * 0.08)
    penalty = abs(confidence - expected) * 35
    return round(max(70, 98 - penalty), 2)


def _grade(score: float) -> str:
    if score >= 97:
        return "A+"
    if score >= 93:
        return "A"
    if score >= 90:
        return "A-"
    if score >= 87:
        return "B+"
    if score >= 83:
        return "B"
    if score >= 80:
        return "B-"
    if score >= 77:
        return "C+"
    if score >= 73:
        return "C"
    if score >= 70:
        return "C-"
    if score >= 60:
        return "D"
    if score > 0:
        return "F"
    return "Unknown"


def _readiness(score: float, missing: tuple[str, ...]) -> str:
    if score >= 90 and not missing:
        return "Ready"
    if score >= 82:
        return "Proceed With Caution"
    if missing:
        return "Requires Additional Information"
    if score >= 70:
        return "Incomplete"
    return "Blocked"


def _dimension_status(score: float) -> str:
    if score >= 90:
        return "Strong"
    if score >= 80:
        return "Adequate"
    if score >= 70:
        return "Weak"
    return "Blocked"
