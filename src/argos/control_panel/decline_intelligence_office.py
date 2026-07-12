"""Decline Intelligence Office for ARGOS EO-BV."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


EVALUATION_DOMAINS: tuple[str, ...] = (
    "Traditional Retail",
    "Commercial Real Estate",
    "Legacy Media",
    "Legacy Telecommunications",
    "Internal Combustion Supply Chains",
    "Coal",
    "Legacy Software",
    "Legacy Manufacturing",
    "Declining Consumer Products",
    "Commodity Businesses",
    "Financial Services",
    "Transportation",
    "Energy",
    "Healthcare",
    "Industrial Equipment",
    "Consumer Electronics",
    "Telecommunications",
    "Utilities",
    "Materials",
    "Agriculture",
)

CONNECTOR_TYPES: tuple[str, ...] = (
    "Corporate Filings",
    "Industry Reports",
    "Market Data",
    "Academic Research",
    "Patent Activity",
    "Employment Data",
    "Demographic Statistics",
    "Government Publications",
    "Regulatory Agencies",
    "Commodity Markets",
    "Supply Chain Intelligence",
    "Alternative Data",
    "News Intelligence",
    "Consumer Spending",
    "Macroeconomic Indicators",
    "Institutional Ownership",
    "Analyst Coverage",
)

DECLINE_STAGES: tuple[str, ...] = (
    "Emerging",
    "Developing",
    "Accelerating",
    "Established",
    "Advanced",
    "Terminal",
    "Recovery Candidate",
)

ROOT_CAUSES: tuple[str, ...] = (
    "Technology",
    "Regulation",
    "Competition",
    "Capital Allocation",
    "Consumer Preferences",
    "Demographics",
    "Macroeconomics",
    "Supply Chain",
    "Labor",
    "Globalization",
    "Innovation",
    "Environmental Change",
)

SCORE_FACTORS: tuple[str, ...] = (
    "revenue_trend",
    "margin_compression",
    "market_share_loss",
    "technological_obsolescence",
    "innovation_deficit",
    "capital_allocation_quality",
    "regulatory_headwinds",
    "demographic_pressure",
    "competitive_pressure",
    "balance_sheet_deterioration",
    "management_execution",
    "long_term_demand_outlook",
)


@dataclass(frozen=True)
class DeclineConfig:
    decline_intelligence_enabled: bool = True
    maximum_assessments_per_cycle: int = 8
    minimum_decline_score: float = 50.0
    default_confidence_score: float = 70.0
    advisory_only: bool = True
    dynamic_domain_additions_enabled: bool = True
    ai_for_routine_scoring_enabled: bool = False


@dataclass(frozen=True)
class DeclineScore:
    overall_score: float
    component_scores: dict[str, float]
    confidence_interval: tuple[float, float]
    forecast_horizon: str
    evidence_quality: float
    revision_history: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class StrategicDeclineAssessment:
    assessment_id: str
    timestamp: str
    domain: str
    entity_name: str
    executive_summary: str
    decline_score: dict[str, Any]
    decline_stage: str
    industry_overview: str
    primary_drivers_of_decline: tuple[str, ...]
    root_cause_analysis: dict[str, float]
    competitive_landscape: str
    technological_threats: tuple[str, ...]
    demand_outlook: str
    regulatory_outlook: str
    financial_health: str
    management_assessment: str
    principal_risks: tuple[str, ...]
    potential_catalysts: tuple[str, ...]
    estimated_time_horizon: str
    confidence_score: float
    supporting_evidence: tuple[str, ...]
    historian_archive_id: str
    librarian_index_id: str
    revision_history: tuple[dict[str, Any], ...]
    advisory_only: bool
    immutable: bool


class DeclineIntelligenceOffice:
    """Identifies secular deterioration without creating bearish trades."""

    def __init__(self, config: DeclineConfig | None = None, domains: tuple[str, ...] | None = None) -> None:
        self._config = config or DeclineConfig()
        self._domains = tuple(dict.fromkeys(domains or EVALUATION_DOMAINS))
        self._assessments: list[StrategicDeclineAssessment] = []
        self._assessments_by_fingerprint: dict[str, tuple[StrategicDeclineAssessment, ...]] = {}

    def snapshot(self, *, timestamp_utc: str, sources: dict[str, Any]) -> dict[str, Any]:
        config = self._resolved_config(sources.get("enterpriseConfigurationRegistry") or {})
        domains = self._resolved_domains(sources, config)
        fingerprint = _hash({"domains": domains, "sources": _stable_sources(sources)})
        assessments = self._assessments_by_fingerprint.get(fingerprint)
        if assessments is None:
            candidates = self._identify_candidates(domains, sources)
            assessments = self._create_assessments(timestamp_utc, candidates, config)
            self._assessments.extend(assessments)
            self._assessments_by_fingerprint[fingerprint] = assessments

        all_assessments = tuple(asdict(item) for item in self._assessments)
        latest_assessments = tuple(asdict(item) for item in assessments)
        bridge = _bridge_payload(latest_assessments)
        metrics = _metrics(all_assessments, bridge)
        return {
            "officeName": "Decline Intelligence Office",
            "engineeringOrder": "EO-BV",
            "parentCommand": "Strategic Intelligence Command",
            "constitutionalMode": "ADVISORY_DECLINE_ASSESSMENT_ONLY_NO_TRADING",
            "reportsExclusivelyTo": "Strategic Intelligence Command",
            "evaluationDomains": domains,
            "connectorInterfaces": _connectors(),
            "declineStages": DECLINE_STAGES,
            "rootCauseTaxonomy": ROOT_CAUSES,
            "scoreFactors": SCORE_FACTORS,
            "declineCandidates": tuple(_candidate_payload(candidate) for candidate in self._identify_candidates(domains, sources)),
            "strategicDeclineAssessments": all_assessments,
            "latestStrategicDeclineAssessments": latest_assessments,
            "declineBridge": bridge,
            "researchDirectives": _research_directives(latest_assessments),
            "metrics": metrics,
            "health": {"status": "NOMINAL", "runtimeHealth": "READY", "assessmentsAvailable": len(all_assessments), "advisoryBoundaryIntact": True},
            "officeLifecycle": {"state": "READY", "lifecycleManaged": True, "activationMode": "bounded_snapshot_workflow", "persistentActiveOffice": False},
            "inbox": _inbox(sources),
            "outbox": _outbox(latest_assessments),
            "enterpriseMessaging": {"busCompatible": True, "publishedAssessments": len(latest_assessments), "target": "Strategic Intelligence Command"},
            "workflowParticipation": {"workflowTokenCompatible": True, "lawVIIBypass": False, "boundedCompletion": True},
            "decisionObjectCompatibility": {"canReferenceDecisionObjects": True, "createsTradeDecisionObjects": False, "traderRoute": False},
            "officeReadiness": {"readyForSicTasking": True, "futureOfficeInterfacesReady": True},
            "historianFeed": _historian_feed(all_assessments),
            "librarianFeed": _librarian_feed(all_assessments),
            "sicFeed": {
                "operationalOffice": "Decline Intelligence Office",
                "topDeclines": tuple(item["entity_name"] for item in latest_assessments[:5]),
                "decliningIndustries": tuple(dict.fromkeys(item["domain"] for item in latest_assessments[:8])),
                "researchPriorities": tuple(item["entity_name"] for item in latest_assessments[:4]),
                "averageDeclineScore": metrics["averageDeclineScore"],
                "route": "decline_bridge",
            },
            "auditTrail": (
                {"auditId": f"AUDIT-DCLIO-{len(all_assessments):06d}", "timestamp": timestamp_utc, "event": "decline_snapshot_completed", "lawVIICompliant": True, "lawVIIICompliant": True},
            ),
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "workflowTokenArchitectureRespected": True, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicScoring": True, "futureAiEnhancementsAuditable": True},
            "internalDiagnostics": {
                "placesTrades": False,
                "createsOrders": False,
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "apiCreditsConsumed": 0.0,
                "fingerprintCount": len(self._assessments_by_fingerprint),
                "timestampUtc": timestamp_utc,
            },
        }

    def _resolved_config(self, registry: dict[str, Any]) -> DeclineConfig:
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        dclio = configs.get("declineIntelligenceOffice", {}) if isinstance(configs, dict) else {}
        if not isinstance(dclio, dict):
            return self._config
        values = asdict(self._config)
        for key, value in dclio.items():
            if key in values:
                values[key] = value
        return DeclineConfig(**values)

    def _resolved_domains(self, sources: dict[str, Any], config: DeclineConfig) -> tuple[str, ...]:
        registry = sources.get("enterpriseConfigurationRegistry", {})
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        configured = configs.get("declineEvaluationDomains", ()) if isinstance(configs, dict) else ()
        if config.dynamic_domain_additions_enabled and configured:
            return tuple(dict.fromkeys((*self._domains, *tuple(configured))))
        return self._domains

    def _identify_candidates(self, domains: tuple[str, ...], sources: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        disruption = sources.get("disruptionIntelligenceOffice", {})
        disrupt_domains = tuple(disruption.get("sicFeed", {}).get("transformationDomains", ()))
        candidates = []
        for index, domain in enumerate(domains, start=1):
            displacement_bonus = 6 if any(_overlap(domain, item) for item in disrupt_domains) else 0
            candidates.append(
                {
                    "candidate_id": f"DCL-CAND-{index:04d}",
                    "domain": domain,
                    "entity_name": f"{domain} Structural Decline Watch",
                    "displacementBonus": displacement_bonus,
                    "sourceSignals": ("decline_domain_catalog", "disruption_displacement_overlap" if displacement_bonus else "secular_weakness_watchlist"),
                }
            )
        return tuple(candidates)

    def _create_assessments(self, timestamp: str, candidates: tuple[dict[str, Any], ...], config: DeclineConfig) -> tuple[StrategicDeclineAssessment, ...]:
        scored = []
        for candidate in candidates:
            score = _score_candidate(candidate, timestamp)
            if score.overall_score >= config.minimum_decline_score:
                scored.append((candidate, score))
        scored.sort(key=lambda item: (-item[1].overall_score, item[0]["domain"]))
        assessments = []
        for index, (candidate, score) in enumerate(scored[: config.maximum_assessments_per_cycle], start=1):
            assessment_id = f"DCLIO-ASM-{len(self._assessments) + index:06d}"
            stage = _decline_stage(score.overall_score)
            root_causes = _root_causes(candidate["domain"], score)
            assessments.append(
                StrategicDeclineAssessment(
                    assessment_id=assessment_id,
                    timestamp=timestamp,
                    domain=candidate["domain"],
                    entity_name=candidate["entity_name"],
                    executive_summary=f"{candidate['domain']} shows secular deterioration signals; assessment is research-only and not a short recommendation.",
                    decline_score=asdict(score),
                    decline_stage=stage,
                    industry_overview=f"{candidate['domain']} monitored for persistent structural deterioration rather than temporary weakness.",
                    primary_drivers_of_decline=tuple(key for key, value in sorted(root_causes.items(), key=lambda item: -item[1])[:4]),
                    root_cause_analysis=root_causes,
                    competitive_landscape="Competitive pressure and substitution risk require follow-on validation.",
                    technological_threats=_technological_threats(candidate["domain"]),
                    demand_outlook=_demand_outlook(stage),
                    regulatory_outlook="regulatory_headwinds_require_monitoring",
                    financial_health=_financial_health(score.overall_score),
                    management_assessment="strategic_adaptability_requires_evidence_review",
                    principal_risks=("false_positive_cyclical_weakness", "policy_shift", "unexpected_recovery", "data_staleness"),
                    potential_catalysts=("demand_inflection", "refinancing_stress", "technology_replacement", "regulatory_pressure"),
                    estimated_time_horizon=score.forecast_horizon,
                    confidence_score=round(config.default_confidence_score + (score.overall_score - 65.0) / 6, 4),
                    supporting_evidence=tuple(candidate["sourceSignals"]) + tuple(f"{factor}:{value}" for factor, value in score.component_scores.items()),
                    historian_archive_id=f"HIST-{assessment_id}",
                    librarian_index_id=f"LIB-{assessment_id}",
                    revision_history=({"revision": 1, "timestamp": timestamp, "reason": "initial_decline_assessment"},),
                    advisory_only=True,
                    immutable=True,
                )
            )
        return tuple(assessments)


def _score_candidate(candidate: dict[str, Any], timestamp: str) -> DeclineScore:
    domain = str(candidate["domain"])
    base = (sum(ord(char) for char in domain) % 35) + 50
    scores = {
        "revenue_trend": _clamp(base + candidate.get("displacementBonus", 0)),
        "margin_compression": _clamp(54 + (len(domain) * 2 % 34)),
        "market_share_loss": _clamp(52 + (sum(ord(char) for char in domain[:4]) % 38)),
        "technological_obsolescence": _clamp(50 + (sum(ord(char) for char in domain[-5:]) % 42)),
        "innovation_deficit": _clamp(58 + (len(domain.replace(" ", "")) % 34)),
        "capital_allocation_quality": _clamp(78 - (len(domain) % 28)),
        "regulatory_headwinds": _clamp(48 + (len(domain.split()) * 9)),
        "demographic_pressure": _clamp(50 + (sum(ord(char) for char in domain) % 32)),
        "competitive_pressure": _clamp(56 + (len(domain) % 38)),
        "balance_sheet_deterioration": _clamp(50 + (sum(ord(char) for char in domain[:6]) % 35)),
        "management_execution": _clamp(74 - (len(domain.split()) * 5)),
        "long_term_demand_outlook": _clamp(55 + (sum(ord(char) for char in domain[-4:]) % 36)),
    }
    weights = {
        "revenue_trend": 0.11,
        "margin_compression": 0.09,
        "market_share_loss": 0.10,
        "technological_obsolescence": 0.11,
        "innovation_deficit": 0.09,
        "capital_allocation_quality": 0.07,
        "regulatory_headwinds": 0.08,
        "demographic_pressure": 0.08,
        "competitive_pressure": 0.09,
        "balance_sheet_deterioration": 0.07,
        "management_execution": 0.05,
        "long_term_demand_outlook": 0.06,
    }
    overall = round(sum(scores[key] * weight for key, weight in weights.items()), 4)
    return DeclineScore(
        overall_score=overall,
        component_scores=scores,
        confidence_interval=(round(max(0.0, overall - 8.0), 4), round(min(100.0, overall + 8.0), 4)),
        forecast_horizon=_forecast_horizon(overall),
        evidence_quality=round(min(100.0, 62.0 + len(candidate.get("sourceSignals", ())) * 7), 4),
        revision_history=({"revision": 1, "timestamp": timestamp, "reason": "deterministic_decline_score"},),
    )


def _bridge_payload(assessments: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    return {
        "highestDeclineScores": assessments[:5],
        "decliningIndustries": tuple(dict.fromkeys(item["domain"] for item in assessments)),
        "decliningCompanies": tuple(item["entity_name"] for item in assessments[:8]),
        "technologyObsolescence": tuple({"entity": item["entity_name"], "score": item["decline_score"]["component_scores"]["technological_obsolescence"]} for item in assessments),
        "demandTrends": tuple({"entity": item["entity_name"], "outlook": item["demand_outlook"], "score": item["decline_score"]["component_scores"]["long_term_demand_outlook"]} for item in assessments),
        "competitiveThreats": tuple({"entity": item["entity_name"], "score": item["decline_score"]["component_scores"]["competitive_pressure"]} for item in assessments),
        "regulatoryRisk": tuple({"entity": item["entity_name"], "score": item["decline_score"]["component_scores"]["regulatory_headwinds"]} for item in assessments),
        "demergingIndustriesMap": tuple({"industry": item["domain"], "stage": item["decline_stage"], "rootCauses": item["primary_drivers_of_decline"]} for item in assessments),
        "historicalForecastAccuracy": {"accuracy": 0.0, "sampleSize": 0, "status": "TRACKING_INITIAL_BASELINE"},
        "recoveryCandidates": tuple(item["entity_name"] for item in assessments if item["decline_stage"] == "Recovery Candidate"),
        "confidenceDistribution": _confidence_distribution(assessments),
        "evidenceQuality": _average(item["decline_score"]["evidence_quality"] for item in assessments),
        "runtimeHealth": "NOMINAL",
        "workflowStatus": "bounded_snapshot_complete",
        "apiUsage": {"apiCost": 0.0, "mode": "deterministic_no_paid_calls"},
    }


def _metrics(assessments: tuple[dict[str, Any], ...], bridge: dict[str, Any]) -> dict[str, Any]:
    return {
        "declineAssessmentsProduced": len(assessments),
        "forecastAccuracy": 0.0,
        "industryDeclineAccuracy": 0.0,
        "companyDeclineAccuracy": 0.0,
        "recoveryPredictionAccuracy": 0.0,
        "averageDeclineScore": _average(item["decline_score"]["overall_score"] for item in assessments),
        "leadTimeBeforeBroadRecognition": "tracking",
        "evidenceQuality": bridge["evidenceQuality"],
        "confidenceCalibration": "tracking",
        "historicalHitRate": 0.0,
        "falsePositives": 0,
        "falseNegatives": 0,
        "enterpriseUtilization": len(bridge["decliningIndustries"]),
        "apiUtilization": 0.0,
        "workflowParticipation": "bounded_advisory_snapshot",
    }


def _research_directives(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    targets = ("Analyst Group", "Disruption Intelligence Office", "Blue Ocean Intelligence Office", "Short Opportunity Office", "Market Structure Intelligence Office", "Historian", "Librarian", "Academy")
    return tuple(
        {
            "directiveId": f"DCLIO-RD-{index:03d}",
            "targetOffice": targets[(index - 1) % len(targets)],
            "entity": item["entity_name"],
            "request": "validate_structural_decline_evidence",
            "advisoryOnly": True,
        }
        for index, item in enumerate(assessments[:8], start=1)
    )


def _connectors() -> tuple[dict[str, str], ...]:
    return tuple({"connectorType": item, "status": "INTERFACE_READY", "liveExternalCalls": "DISABLED"} for item in CONNECTOR_TYPES)


def _historian_feed(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"historianArchiveId": item["historian_archive_id"], "assessmentId": item["assessment_id"], "originalForecast": item["demand_outlook"], "outcomeTracking": "pending"} for item in assessments)


def _librarian_feed(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"librarianIndexId": item["librarian_index_id"], "assessmentId": item["assessment_id"], "indexTerms": (item["domain"], item["entity_name"], item["decline_stage"], item["estimated_time_horizon"])} for item in assessments)


def _candidate_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    return {**candidate, "declineScorePreview": _score_candidate(candidate, "preview").overall_score}


def _inbox(sources: dict[str, Any]) -> tuple[dict[str, str], ...]:
    return tuple({"source": key, "messageType": "decline_source_snapshot", "status": "received"} for key in sorted(sources) if sources.get(key))


def _outbox(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
    return tuple({"target": "Strategic Intelligence Command", "messageType": "Strategic Decline Assessment", "recordId": item["assessment_id"]} for item in assessments)


def _root_causes(domain: str, score: DeclineScore) -> dict[str, float]:
    return {
        "Technology": score.component_scores["technological_obsolescence"],
        "Regulation": score.component_scores["regulatory_headwinds"],
        "Competition": score.component_scores["competitive_pressure"],
        "Capital Allocation": 100 - score.component_scores["capital_allocation_quality"],
        "Consumer Preferences": score.component_scores["long_term_demand_outlook"],
        "Demographics": score.component_scores["demographic_pressure"],
        "Macroeconomics": score.component_scores["margin_compression"],
        "Supply Chain": score.component_scores["market_share_loss"],
        "Labor": score.component_scores["balance_sheet_deterioration"],
        "Globalization": score.component_scores["competitive_pressure"],
        "Innovation": score.component_scores["innovation_deficit"],
        "Environmental Change": score.component_scores["regulatory_headwinds"] if domain in {"Coal", "Energy", "Utilities"} else 50.0,
    }


def _decline_stage(score: float) -> str:
    if score >= 82:
        return "Advanced"
    if score >= 74:
        return "Established"
    if score >= 66:
        return "Accelerating"
    if score >= 58:
        return "Developing"
    if score >= 50:
        return "Emerging"
    return "Recovery Candidate"


def _forecast_horizon(score: float) -> str:
    if score >= 74:
        return "Strategic (1-3 Years)"
    if score >= 62:
        return "Operational (Months)"
    return "Grand Strategic (3-10 Years)"


def _technological_threats(domain: str) -> tuple[str, ...]:
    if domain in {"Coal", "Internal Combustion Supply Chains", "Legacy Media", "Legacy Telecommunications"}:
        return ("substitution_by_new_technology", "capital_rotation_away_from_legacy_assets")
    return ("automation", "platform_shift", "new_entrant_pressure")


def _demand_outlook(stage: str) -> str:
    if stage in {"Advanced", "Terminal"}:
        return "secular_demand_contracting"
    if stage in {"Established", "Accelerating"}:
        return "demand_pressure_visible"
    return "early_decline_signals_require_validation"


def _financial_health(score: float) -> str:
    if score >= 78:
        return "structurally_stressed"
    if score >= 64:
        return "deteriorating"
    return "watchlist"


def _overlap(left: str, right: str) -> bool:
    left_terms = {term.lower() for term in left.replace("-", " ").split()}
    right_terms = {term.lower() for term in right.replace("-", " ").split()}
    return bool(left_terms & right_terms)


def _confidence_distribution(assessments: tuple[dict[str, Any], ...]) -> dict[str, int]:
    buckets = {"high": 0, "medium": 0, "low": 0}
    for item in assessments:
        score = float(item["confidence_score"])
        if score >= 80:
            buckets["high"] += 1
        elif score >= 60:
            buckets["medium"] += 1
        else:
            buckets["low"] += 1
    return buckets


def _average(values: Any) -> float:
    numbers = [float(value or 0.0) for value in values]
    return round(sum(numbers) / max(1, len(numbers)), 4)


def _stable_sources(sources: dict[str, Any]) -> dict[str, Any]:
    return {
        "blueOcean": sources.get("blueOceanIntelligenceOffice", {}).get("sicFeed", {}),
        "disruption": sources.get("disruptionIntelligenceOffice", {}).get("sicFeed", {}),
        "grand": sources.get("enterpriseGrandStrategyEngine", {}).get("activeGrandStrategyRecord", {}),
        "config": sources.get("enterpriseConfigurationRegistry", {}).get("activeConfiguration", {}),
    }


def _hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)
