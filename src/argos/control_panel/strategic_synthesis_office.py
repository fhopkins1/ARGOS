"""Strategic Synthesis Office for ARGOS EO-BZ."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


SYNTHESIS_DIMENSIONS: tuple[str, ...] = (
    "Strategic Themes",
    "Industry Outlook",
    "Technology Outlook",
    "Capital Flows",
    "Market Structure",
    "Competitive Dynamics",
    "Macroeconomic Context",
    "Regulatory Environment",
    "Geopolitical Environment",
    "Risk Factors",
    "Confidence",
    "Evidence Quality",
    "Time Horizon",
)

CONSENSUS_COMPONENTS: tuple[str, ...] = (
    "agreement_between_offices",
    "supporting_evidence_strength",
    "historical_forecasting_accuracy",
    "evidence_independence",
    "confidence_calibration",
    "recency_of_information",
    "cross_validation",
    "contradictory_evidence",
    "unknowns",
    "forecast_consistency",
)

STRATEGIC_CLASSIFICATIONS: tuple[str, ...] = (
    "Highly Favorable",
    "Favorable",
    "Neutral",
    "Mixed",
    "Cautious",
    "Defensive",
    "Highly Defensive",
    "Opportunity Expansion",
    "Structural Transition",
)

UNCERTAINTY_SOURCES: tuple[str, ...] = (
    "Incomplete evidence",
    "Conflicting evidence",
    "Novel technologies",
    "Macroeconomic instability",
    "Regulatory uncertainty",
    "Geopolitical developments",
    "Market volatility",
    "Data quality",
    "Model disagreement",
    "Unknown unknowns",
)

STRATEGIC_OFFICES: tuple[str, ...] = (
    "blueOceanIntelligenceOffice",
    "disruptionIntelligenceOffice",
    "declineIntelligenceOffice",
    "shortOpportunityOffice",
    "marketStructureIntelligenceOffice",
    "capitalRotationIntelligenceOffice",
)


@dataclass(frozen=True)
class StrategicSynthesisConfig:
    strategic_synthesis_office_enabled: bool = True
    maximum_assessments_per_cycle: int = 1
    default_confidence_score: float = 73.0
    minimum_consensus_score: float = 45.0
    ai_for_routine_synthesis_enabled: bool = False


@dataclass(frozen=True)
class StrategicConsensusScore:
    overall_score: float
    component_scores: dict[str, float]
    confidence_interval: tuple[float, float]
    evidence_quality: float
    forecast_horizon: str
    revision_history: tuple[dict[str, Any], ...]
    consensus_contributors: tuple[str, ...]
    contradictory_contributors: tuple[str, ...]


@dataclass(frozen=True)
class CommanderStrategicAssessment:
    assessment_id: str
    timestamp: str
    executive_summary: str
    strategic_consensus_score: dict[str, Any]
    strategic_classification: str
    primary_strategic_themes: tuple[str, ...]
    emerging_opportunities: tuple[str, ...]
    emerging_risks: tuple[str, ...]
    areas_of_agreement: tuple[str, ...]
    areas_of_disagreement: tuple[dict[str, Any], ...]
    evidence_summary: tuple[str, ...]
    confidence_assessment: str
    time_horizon: str
    research_priorities: tuple[str, ...]
    strategic_recommendations: tuple[str, ...]
    key_unknowns: tuple[str, ...]
    uncertainty_map: tuple[dict[str, Any], ...]
    recommended_follow_on_offices: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    commander_strategic_briefing: dict[str, Any]
    historian_archive_id: str
    librarian_index_id: str
    revision_history: tuple[dict[str, Any], ...]
    advisory_only: bool
    immutable: bool


class StrategicSynthesisOffice:
    """Synthesizes subordinate strategic intelligence into one Commander assessment."""

    def __init__(self, config: StrategicSynthesisConfig | None = None) -> None:
        self._config = config or StrategicSynthesisConfig()
        self._assessments: list[CommanderStrategicAssessment] = []
        self._assessments_by_fingerprint: dict[str, tuple[CommanderStrategicAssessment, ...]] = {}

    def snapshot(self, *, timestamp_utc: str, sources: dict[str, Any]) -> dict[str, Any]:
        config = self._resolved_config(sources.get("enterpriseConfigurationRegistry") or {})
        evidence = _collect_evidence(sources)
        fingerprint = _hash({"evidence": evidence, "config": asdict(config)})
        assessments = self._assessments_by_fingerprint.get(fingerprint)
        if assessments is None:
            assessments = self._create_assessments(timestamp_utc, evidence, config)
            self._assessments.extend(assessments)
            self._assessments_by_fingerprint[fingerprint] = assessments

        all_assessments = tuple(asdict(item) for item in self._assessments)
        latest_assessments = tuple(asdict(item) for item in assessments)
        bridge = _bridge_payload(latest_assessments, evidence)
        metrics = _metrics(all_assessments, bridge)
        latest = latest_assessments[0] if latest_assessments else {}
        return {
            "officeName": "Strategic Synthesis Office",
            "engineeringOrder": "EO-BZ",
            "parentCommand": "Strategic Intelligence Command",
            "constitutionalMode": "ADVISORY_STRATEGIC_SYNTHESIS_ONLY_NO_TRADING",
            "reportsExclusivelyTo": "Strategic Intelligence Command",
            "tradingAuthority": "NONE",
            "synthesisDimensions": SYNTHESIS_DIMENSIONS,
            "consensusComponents": CONSENSUS_COMPONENTS,
            "strategicClassifications": STRATEGIC_CLASSIFICATIONS,
            "uncertaintySources": UNCERTAINTY_SOURCES,
            "sourceOfficeEvidence": evidence["officeEvidence"],
            "commanderStrategicAssessments": all_assessments,
            "latestCommanderStrategicAssessments": latest_assessments,
            "latestCommanderStrategicBriefing": latest.get("commander_strategic_briefing", {}),
            "strategicSynthesisBridge": bridge,
            "researchDirectives": _research_directives(latest_assessments),
            "metrics": metrics,
            "health": {"status": "NOMINAL", "runtimeHealth": "READY", "assessmentsAvailable": len(all_assessments), "advisoryBoundaryIntact": True},
            "officeLifecycle": {"state": "READY", "lifecycleManaged": True, "activationMode": "bounded_snapshot_workflow", "persistentActiveOffice": False},
            "inbox": _inbox(sources),
            "outbox": _outbox(latest_assessments),
            "enterpriseMessaging": {"busCompatible": True, "publishedAssessments": len(latest_assessments), "target": "Strategic Intelligence Command"},
            "workflowParticipation": {"workflowTokenCompatible": True, "lawVIIBypass": False, "boundedCompletion": True},
            "decisionObjectCompatibility": {"canReferenceDecisionObjects": True, "createsTradeDecisionObjects": False, "traderRoute": False},
            "historianFeed": _historian_feed(all_assessments),
            "librarianFeed": _librarian_feed(all_assessments),
            "sicFeed": {
                "operationalOffice": "Strategic Synthesis Office",
                "classification": latest.get("strategic_classification", "Neutral"),
                "primaryThemes": tuple(latest.get("primary_strategic_themes", ())),
                "researchPriorities": tuple(latest.get("research_priorities", ())),
                "consensusScore": metrics["averageStrategicConsensusScore"],
                "route": "strategic_synthesis_bridge",
            },
            "auditTrail": (
                {"auditId": f"AUDIT-SSO-{len(all_assessments):06d}", "timestamp": timestamp_utc, "event": "strategic_synthesis_snapshot_completed", "lawVIICompliant": True, "lawVIIICompliant": True},
            ),
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "workflowTokenArchitectureRespected": True, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicSynthesis": True, "futureAiEnhancementsAuditable": True},
            "internalDiagnostics": {
                "placesTrades": False,
                "createsOrders": False,
                "routesToTrader": False,
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "apiCreditsConsumed": 0.0,
                "fingerprintCount": len(self._assessments_by_fingerprint),
                "timestampUtc": timestamp_utc,
            },
        }

    def _resolved_config(self, registry: dict[str, Any]) -> StrategicSynthesisConfig:
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        sso = configs.get("strategicSynthesisOffice", {}) if isinstance(configs, dict) else {}
        if not isinstance(sso, dict):
            return self._config
        values = asdict(self._config)
        for key, value in sso.items():
            if key in values:
                values[key] = value
        return StrategicSynthesisConfig(**values)

    def _create_assessments(self, timestamp: str, evidence: dict[str, Any], config: StrategicSynthesisConfig) -> tuple[CommanderStrategicAssessment, ...]:
        consensus = _score_consensus(evidence, timestamp)
        if consensus.overall_score < config.minimum_consensus_score:
            return ()
        classification = _classification(consensus, evidence)
        assessment_id = f"SSO-ASM-{len(self._assessments) + 1:06d}"
        briefing = _commander_briefing(assessment_id, classification, consensus, evidence)
        return (
            CommanderStrategicAssessment(
                assessment_id=assessment_id,
                timestamp=timestamp,
                executive_summary=f"Strategic Synthesis classifies enterprise outlook as {classification} with {consensus.overall_score:.1f} consensus.",
                strategic_consensus_score=asdict(consensus),
                strategic_classification=classification,
                primary_strategic_themes=evidence["themes"][:8],
                emerging_opportunities=evidence["opportunities"][:8],
                emerging_risks=evidence["risks"][:8],
                areas_of_agreement=evidence["agreements"],
                areas_of_disagreement=evidence["disagreements"],
                evidence_summary=evidence["summary"],
                confidence_assessment=_confidence_assessment(consensus),
                time_horizon=consensus.forecast_horizon,
                research_priorities=evidence["researchPriorities"][:8],
                strategic_recommendations=_recommendations(classification, evidence),
                key_unknowns=_unknowns(evidence),
                uncertainty_map=_uncertainty_map(evidence, consensus),
                recommended_follow_on_offices=_follow_on_offices(evidence),
                supporting_evidence=evidence["supportingEvidence"],
                commander_strategic_briefing=briefing,
                historian_archive_id=f"HIST-{assessment_id}",
                librarian_index_id=f"LIB-{assessment_id}",
                revision_history=({"revision": 1, "timestamp": timestamp, "reason": "initial_commander_strategic_assessment"},),
                advisory_only=True,
                immutable=True,
            ),
        )


def _collect_evidence(sources: dict[str, Any]) -> dict[str, Any]:
    office_evidence = []
    for key in STRATEGIC_OFFICES:
        snapshot = sources.get(key, {}) or {}
        feed = snapshot.get("sicFeed", {}) or {}
        office_evidence.append(
            {
                "sourceKey": key,
                "office": snapshot.get("officeName", key),
                "status": snapshot.get("health", {}).get("status", "UNKNOWN"),
                "route": feed.get("route", ""),
                "score": _score_from_feed(feed),
                "themes": _terms_from_feed(feed),
                "evidenceQuality": _number(snapshot.get("metrics", {}).get("evidenceQuality"), 0.0),
                "researchPriorities": tuple(feed.get("researchPriorities", ())),
            }
        )
    themes = tuple(dict.fromkeys(term for item in office_evidence for term in item["themes"] if term))
    opportunities = tuple(dict.fromkeys(
        (*_feed_terms(sources, "blueOceanIntelligenceOffice", "topOpportunities"),
         *_feed_terms(sources, "disruptionIntelligenceOffice", "topDisruptions"),
         *_feed_terms(sources, "marketStructureIntelligenceOffice", "topStructuralOpportunities"),
         *_feed_terms(sources, "capitalRotationIntelligenceOffice", "topCapitalDestinations"))
    ))
    risks = tuple(dict.fromkeys((*_feed_terms(sources, "declineIntelligenceOffice", "topDeclines"), *_feed_terms(sources, "shortOpportunityOffice", "topShortOpportunities"))))
    research = tuple(dict.fromkeys(term for item in office_evidence for term in item["researchPriorities"] if term))
    scores = tuple(item["score"] for item in office_evidence if item["score"])
    high = tuple(item["office"] for item in office_evidence if item["score"] >= 68)
    low = tuple(item["office"] for item in office_evidence if item["score"] and item["score"] < 58)
    disagreements = _disagreements(office_evidence, opportunities, risks)
    return {
        "officeEvidence": tuple(office_evidence),
        "themes": themes or ("evidence integration", "strategic attention allocation"),
        "opportunities": opportunities or ("strategic opportunity validation",),
        "risks": risks or ("insufficient strategic evidence",),
        "researchPriorities": research or ("cross-office evidence validation",),
        "scores": scores,
        "agreements": tuple(f"{office} supports current strategic direction" for office in high) or ("Strategic offices provide usable evidence for synthesis",),
        "disagreements": disagreements,
        "summary": tuple(f"{item['office']}: score {item['score']:.1f}, evidence {item['evidenceQuality']:.1f}" for item in office_evidence),
        "supportingEvidence": tuple(f"{item['office']} via {item['route'] or 'sic_feed'}" for item in office_evidence),
    }


def _score_consensus(evidence: dict[str, Any], timestamp: str) -> StrategicConsensusScore:
    scores = evidence["scores"]
    average_score = _average(scores)
    spread = max(scores or (0.0,)) - min(scores or (0.0,))
    disagreements = len(evidence["disagreements"])
    components = {
        "agreement_between_offices": _clamp(82 - spread / 2 - disagreements * 4),
        "supporting_evidence_strength": _clamp(_average(item["evidenceQuality"] for item in evidence["officeEvidence"]) + 5),
        "historical_forecasting_accuracy": 55.0,
        "evidence_independence": _clamp(60 + len(evidence["officeEvidence"]) * 5),
        "confidence_calibration": _clamp(average_score),
        "recency_of_information": 86.0,
        "cross_validation": _clamp(55 + len(evidence["agreements"]) * 6),
        "contradictory_evidence": _clamp(78 - disagreements * 8),
        "unknowns": _clamp(75 - len(_unknowns(evidence)) * 4),
        "forecast_consistency": _clamp(80 - spread / 3),
    }
    weights = {
        "agreement_between_offices": 0.13,
        "supporting_evidence_strength": 0.13,
        "historical_forecasting_accuracy": 0.08,
        "evidence_independence": 0.10,
        "confidence_calibration": 0.10,
        "recency_of_information": 0.08,
        "cross_validation": 0.12,
        "contradictory_evidence": 0.10,
        "unknowns": 0.08,
        "forecast_consistency": 0.08,
    }
    overall = round(sum(components[key] * weight for key, weight in weights.items()), 4)
    return StrategicConsensusScore(
        overall_score=overall,
        component_scores=components,
        confidence_interval=(round(max(0.0, overall - 7.0), 4), round(min(100.0, overall + 7.0), 4)),
        evidence_quality=round(components["supporting_evidence_strength"], 4),
        forecast_horizon=_forecast_horizon(overall),
        revision_history=({"revision": 1, "timestamp": timestamp, "reason": "deterministic_strategic_consensus_score"},),
        consensus_contributors=tuple(item["office"] for item in evidence["officeEvidence"] if item["score"] >= average_score),
        contradictory_contributors=tuple(item["office"] for item in evidence["officeEvidence"] if item["score"] < average_score - 10),
    )


def _bridge_payload(assessments: tuple[dict[str, Any], ...], evidence: dict[str, Any]) -> dict[str, Any]:
    latest = assessments[0] if assessments else {}
    score = latest.get("strategic_consensus_score", {})
    return {
        "strategicConsensusScore": score,
        "consensusMatrix": tuple({"office": item["office"], "score": item["score"], "evidenceQuality": item["evidenceQuality"]} for item in evidence["officeEvidence"]),
        "officeAgreementMatrix": tuple({"office": item["office"], "alignment": "supportive" if item["score"] >= 68 else "watch", "themes": item["themes"]} for item in evidence["officeEvidence"]),
        "evidenceHeatMap": tuple({"office": item["office"], "score": item["evidenceQuality"]} for item in evidence["officeEvidence"]),
        "confidenceDistribution": _confidence_distribution(evidence["officeEvidence"]),
        "uncertaintyMap": tuple(latest.get("uncertainty_map", ())),
        "strategicThemes": tuple(latest.get("primary_strategic_themes", ())),
        "emergingRisks": tuple(latest.get("emerging_risks", ())),
        "researchPriorities": tuple(latest.get("research_priorities", ())),
        "commanderBriefing": latest.get("commander_strategic_briefing", {}),
        "historicalStrategicAssessments": tuple({"assessmentId": item["assessment_id"], "classification": item["strategic_classification"], "score": item["strategic_consensus_score"]["overall_score"]} for item in assessments),
        "forecastAccuracy": {"accuracy": 0.0, "sampleSize": 0, "status": "TRACKING_INITIAL_BASELINE"},
        "runtimeHealth": "NOMINAL",
        "workflowStatus": "bounded_snapshot_complete",
        "apiUsage": {"apiCost": 0.0, "mode": "deterministic_no_paid_calls"},
    }


def _metrics(assessments: tuple[dict[str, Any], ...], bridge: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategicAssessmentsProduced": len(assessments),
        "consensusAccuracy": 0.0,
        "forecastAccuracy": 0.0,
        "researchPrioritizationQuality": 0.0,
        "evidenceIntegrationQuality": _average(item.get("score") for item in bridge.get("evidenceHeatMap", ())),
        "conflictResolutionEffectiveness": 0.0,
        "confidenceCalibration": "tracking",
        "historicalHitRate": 0.0,
        "falsePositives": 0,
        "falseNegatives": 0,
        "averageStrategicConsensusScore": _number(bridge.get("strategicConsensusScore", {}).get("overall_score"), 0.0),
        "enterpriseUtilization": len(bridge.get("consensusMatrix", ())),
        "apiUtilization": 0.0,
        "workflowParticipation": "bounded_advisory_snapshot",
        "commanderUtilization": 1 if bridge.get("commanderBriefing") else 0,
    }


def _research_directives(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    targets = (
        "Blue Ocean Intelligence Office",
        "Disruption Intelligence Office",
        "Decline Intelligence Office",
        "Short Opportunity Office",
        "Market Structure Intelligence Office",
        "Capital Rotation Intelligence Office",
        "Analyst Group",
        "Seeker Group",
        "Risk Office",
        "Historian",
        "Librarian",
        "Academy",
        "Executive",
    )
    latest = assessments[0] if assessments else {}
    priorities = tuple(latest.get("research_priorities", ())) or ("cross_office_validation",)
    return tuple({"directiveId": f"SSO-RD-{index:03d}", "targetOffice": target, "researchPriority": priorities[(index - 1) % len(priorities)], "advisoryOnly": True} for index, target in enumerate(targets, start=1))


def _commander_briefing(assessment_id: str, classification: str, consensus: StrategicConsensusScore, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "briefingId": f"SSO-BRIEF-{assessment_id}",
        "currentStrategicOutlook": classification,
        "highestConfidenceThemes": evidence["themes"][:5],
        "highestRiskStructuralThreats": evidence["risks"][:5],
        "additionalResearchRequired": evidence["researchPriorities"][:5],
        "strategicConsensusTrend": "baseline_established",
        "changesSincePreviousBriefing": "initial_synthesis_cycle",
        "keyUncertainties": _unknowns(evidence),
        "recommendedEnterpriseAttentionAllocation": _follow_on_offices(evidence)[:6],
        "consensusScore": consensus.overall_score,
    }


def _classification(consensus: StrategicConsensusScore, evidence: dict[str, Any]) -> str:
    risk_count = len(evidence["risks"])
    opportunity_count = len(evidence["opportunities"])
    score = consensus.overall_score
    if score >= 82 and opportunity_count > risk_count:
        return "Highly Favorable"
    if score >= 74 and opportunity_count >= risk_count:
        return "Favorable"
    if opportunity_count > risk_count + 2:
        return "Opportunity Expansion"
    if risk_count > opportunity_count + 2 and score < 65:
        return "Defensive"
    if risk_count > opportunity_count:
        return "Cautious"
    if len(evidence["disagreements"]) >= 2:
        return "Mixed"
    if score >= 66:
        return "Structural Transition"
    return "Neutral"


def _disagreements(office_evidence: tuple[dict[str, Any], ...], opportunities: tuple[str, ...], risks: tuple[str, ...]) -> tuple[dict[str, Any], ...]:
    disagreements = []
    if opportunities and risks:
        disagreements.append({"topic": "opportunity_vs_risk_balance", "supportingPositions": opportunities[:4], "conflictingPositions": risks[:4], "assumptions": ("time_horizon_mismatch", "evidence_maturity_difference"), "uncertainty": "medium"})
    scores = [item["score"] for item in office_evidence if item["score"]]
    if scores and max(scores) - min(scores) > 18:
        disagreements.append({"topic": "confidence_dispersion", "supportingPositions": tuple(item["office"] for item in office_evidence if item["score"] >= max(scores) - 4), "conflictingPositions": tuple(item["office"] for item in office_evidence if item["score"] <= min(scores) + 4), "assumptions": ("different_domain_evidence",), "uncertainty": "high"})
    return tuple(disagreements)


def _recommendations(classification: str, evidence: dict[str, Any]) -> tuple[str, ...]:
    base = ["preserve_traceability_across_all_strategic_products", "route_tactical_decisions_through_existing_offices"]
    if classification in {"Highly Favorable", "Favorable", "Opportunity Expansion"}:
        base.append("increase_research_attention_to_high_consensus_opportunities")
    if classification in {"Cautious", "Defensive", "Highly Defensive", "Mixed"}:
        base.append("prioritize_risk_resolution_and_conflict_research")
    base.append("refresh_synthesis_after_follow_on_office_evidence")
    return tuple(base)


def _uncertainty_map(evidence: dict[str, Any], consensus: StrategicConsensusScore) -> tuple[dict[str, Any], ...]:
    unknowns = _unknowns(evidence)
    return tuple({"source": item, "severity": "high" if index < 2 and consensus.overall_score < 65 else "medium", "impact": "requires_follow_on_research"} for index, item in enumerate(unknowns))


def _unknowns(evidence: dict[str, Any]) -> tuple[str, ...]:
    unknowns = ["future_macro_regime", "evidence_sample_size", "forecast_persistence"]
    if evidence["disagreements"]:
        unknowns.append("cross_office_conflict_resolution")
    if len(evidence["officeEvidence"]) < len(STRATEGIC_OFFICES):
        unknowns.append("missing_office_evidence")
    return tuple(dict.fromkeys(unknowns))


def _follow_on_offices(evidence: dict[str, Any]) -> tuple[str, ...]:
    offices = [item["office"] for item in evidence["officeEvidence"] if item["score"] < 64 or item["evidenceQuality"] < 72]
    offices.extend(("Analyst Group", "Risk Office", "Historian", "Librarian"))
    return tuple(dict.fromkeys(offices))


def _historian_feed(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"historianArchiveId": item["historian_archive_id"], "assessmentId": item["assessment_id"], "consensusEvolution": "baseline", "outcomeTracking": "pending"} for item in assessments)


def _librarian_feed(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"librarianIndexId": item["librarian_index_id"], "assessmentId": item["assessment_id"], "indexTerms": (*item["primary_strategic_themes"], item["strategic_classification"], item["time_horizon"], str(item["strategic_consensus_score"]["overall_score"]))} for item in assessments)


def _inbox(sources: dict[str, Any]) -> tuple[dict[str, str], ...]:
    return tuple({"source": key, "messageType": "strategic_synthesis_source_snapshot", "status": "received"} for key in sorted(sources) if sources.get(key))


def _outbox(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
    return tuple({"target": "Strategic Intelligence Command", "messageType": "Commander Strategic Assessment", "recordId": item["assessment_id"]} for item in assessments)


def _feed_terms(sources: dict[str, Any], office: str, key: str) -> tuple[str, ...]:
    return tuple((sources.get(office, {}).get("sicFeed", {}) or {}).get(key, ()))


def _terms_from_feed(feed: dict[str, Any]) -> tuple[str, ...]:
    terms: list[str] = []
    for key in ("topOpportunities", "topDisruptions", "topDeclines", "topShortOpportunities", "topStructuralOpportunities", "topCapitalDestinations", "primaryThemes", "researchPriorities"):
        values = feed.get(key, ())
        if isinstance(values, (tuple, list)):
            terms.extend(str(value) for value in values)
    return tuple(dict.fromkeys(terms))


def _score_from_feed(feed: dict[str, Any]) -> float:
    for key in ("averageBlueOceanScore", "averageDisruptionScore", "averageDeclineScore", "averageShortOpportunityScore", "averageMarketStructureScore", "averageCapitalRotationScore", "consensusScore"):
        if key in feed:
            return _number(feed.get(key), 0.0)
    return 0.0


def _confidence_assessment(consensus: StrategicConsensusScore) -> str:
    if consensus.overall_score >= 75:
        return "high_confidence_with_traceable_cross_office_support"
    if consensus.overall_score >= 62:
        return "moderate_confidence_with_explicit_uncertainties"
    return "low_to_moderate_confidence_requires_follow_on_research"


def _forecast_horizon(score: float) -> str:
    if score >= 76:
        return "Strategic (1-3 Years)"
    if score >= 64:
        return "Operational (Months)"
    return "Near-Term (Weeks)"


def _confidence_distribution(office_evidence: tuple[dict[str, Any], ...]) -> dict[str, int]:
    buckets = {"high": 0, "medium": 0, "low": 0}
    for item in office_evidence:
        score = float(item["score"])
        if score >= 75:
            buckets["high"] += 1
        elif score >= 60:
            buckets["medium"] += 1
        else:
            buckets["low"] += 1
    return buckets


def _average(values: Any) -> float:
    numbers = [float(value or 0.0) for value in values]
    return round(sum(numbers) / max(1, len(numbers)), 4)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)
