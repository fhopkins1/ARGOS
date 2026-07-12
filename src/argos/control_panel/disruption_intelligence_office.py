"""Disruption Intelligence Office for ARGOS EO-BU."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


EVALUATION_DOMAINS: tuple[str, ...] = (
    "Artificial Intelligence",
    "Machine Learning",
    "Robotics",
    "Industrial Automation",
    "Quantum Computing",
    "Fusion Energy",
    "Small Modular Reactors",
    "Semiconductor Manufacturing",
    "Advanced Packaging",
    "Biotechnology",
    "Synthetic Biology",
    "Gene Editing",
    "Autonomous Vehicles",
    "Defense Technology",
    "Space Infrastructure",
    "Cybersecurity",
    "Cloud Infrastructure",
    "Digital Payments",
    "Financial Technology",
    "Climate Technology",
    "Water Infrastructure",
    "Advanced Manufacturing",
    "Materials Science",
    "Supply Chain Automation",
    "Agricultural Technology",
)

CONNECTOR_TYPES: tuple[str, ...] = (
    "Academic Publications",
    "Patent Databases",
    "Corporate Filings",
    "Government Research",
    "Research Laboratories",
    "Technology Conferences",
    "Scientific Journals",
    "Industry Reports",
    "Engineering Publications",
    "Startup Databases",
    "Private Capital Activity",
    "Venture Capital",
    "Private Equity",
    "Institutional Research",
    "Alternative Data",
    "News Intelligence",
    "Macroeconomic Data",
    "Regulatory Agencies",
    "Commodity Markets",
    "Supply Chain Intelligence",
)

ADOPTION_STAGES: tuple[str, ...] = (
    "Concept",
    "Laboratory",
    "Prototype",
    "Pilot",
    "Early Adoption",
    "Growth",
    "Mass Adoption",
    "Mature",
    "Declining",
)

SCORE_FACTORS: tuple[str, ...] = (
    "innovation_magnitude",
    "commercial_readiness",
    "adoption_velocity",
    "cost_advantage",
    "productivity_improvement",
    "market_replacement_potential",
    "competitive_advantage",
    "intellectual_property",
    "scalability",
    "capital_efficiency",
    "regulatory_outlook",
    "strategic_importance",
)


@dataclass(frozen=True)
class DisruptionConfig:
    disruption_intelligence_enabled: bool = True
    maximum_assessments_per_cycle: int = 8
    minimum_disruption_score: float = 55.0
    default_confidence_score: float = 71.0
    advisory_only: bool = True
    dynamic_domain_additions_enabled: bool = True
    ai_for_routine_scoring_enabled: bool = False


@dataclass(frozen=True)
class DisruptionScore:
    overall_score: float
    component_scores: dict[str, float]
    confidence_interval: tuple[float, float]
    evidence_quality: float
    forecast_horizon: str
    revision_history: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class StrategicDisruptionAssessment:
    assessment_id: str
    timestamp: str
    domain: str
    innovation_name: str
    executive_summary: str
    disruption_score: dict[str, Any]
    technology_description: str
    industry_impact: dict[str, str]
    commercial_readiness: str
    adoption_stage: str
    innovation_assessment: str
    competitive_landscape: str
    incumbent_vulnerability: str
    expected_adoption_curve: str
    capital_requirements: str
    market_size: str
    strategic_importance: str
    principal_risks: tuple[str, ...]
    research_gaps: tuple[str, ...]
    recommended_follow_on_offices: tuple[str, ...]
    forecast_horizon: str
    confidence_score: float
    supporting_evidence: tuple[str, ...]
    historian_archive_id: str
    librarian_index_id: str
    revision_history: tuple[dict[str, Any], ...]
    advisory_only: bool
    immutable: bool


class DisruptionIntelligenceOffice:
    """Evaluates innovations likely to structurally alter competitive landscapes."""

    def __init__(self, config: DisruptionConfig | None = None, domains: tuple[str, ...] | None = None) -> None:
        self._config = config or DisruptionConfig()
        self._domains = tuple(dict.fromkeys(domains or EVALUATION_DOMAINS))
        self._assessments: list[StrategicDisruptionAssessment] = []
        self._assessments_by_fingerprint: dict[str, tuple[StrategicDisruptionAssessment, ...]] = {}

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
            "officeName": "Disruption Intelligence Office",
            "engineeringOrder": "EO-BU",
            "parentCommand": "Strategic Intelligence Command",
            "constitutionalMode": "ADVISORY_DISRUPTION_ASSESSMENT_ONLY_NO_TRADING",
            "reportsExclusivelyTo": "Strategic Intelligence Command",
            "evaluationDomains": domains,
            "connectorInterfaces": _connectors(),
            "adoptionStages": ADOPTION_STAGES,
            "scoreFactors": SCORE_FACTORS,
            "innovationCandidates": tuple(_candidate_payload(candidate) for candidate in self._identify_candidates(domains, sources)),
            "strategicDisruptionAssessments": all_assessments,
            "latestStrategicDisruptionAssessments": latest_assessments,
            "disruptionBridge": bridge,
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
                "operationalOffice": "Disruption Intelligence Office",
                "topDisruptions": tuple(item["innovation_name"] for item in latest_assessments[:5]),
                "transformationDomains": tuple(dict.fromkeys(item["domain"] for item in latest_assessments[:8])),
                "researchPriorities": tuple(item["innovation_name"] for item in latest_assessments[:4]),
                "averageDisruptionScore": metrics["averageDisruptionScore"],
                "route": "disruption_bridge",
            },
            "auditTrail": (
                {"auditId": f"AUDIT-DIO-{len(all_assessments):06d}", "timestamp": timestamp_utc, "event": "disruption_snapshot_completed", "lawVIICompliant": True, "lawVIIICompliant": True},
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

    def _resolved_config(self, registry: dict[str, Any]) -> DisruptionConfig:
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        dio = configs.get("disruptionIntelligenceOffice", {}) if isinstance(configs, dict) else {}
        if not isinstance(dio, dict):
            return self._config
        values = asdict(self._config)
        for key, value in dio.items():
            if key in values:
                values[key] = value
        return DisruptionConfig(**values)

    def _resolved_domains(self, sources: dict[str, Any], config: DisruptionConfig) -> tuple[str, ...]:
        registry = sources.get("enterpriseConfigurationRegistry", {})
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        configured = configs.get("disruptionEvaluationDomains", ()) if isinstance(configs, dict) else ()
        if config.dynamic_domain_additions_enabled and configured:
            return tuple(dict.fromkeys((*self._domains, *tuple(configured))))
        return self._domains

    def _identify_candidates(self, domains: tuple[str, ...], sources: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        blue = sources.get("blueOceanIntelligenceOffice", {})
        blue_domains = tuple(blue.get("sicFeed", {}).get("emergingIndustries", ()))
        candidates = []
        for index, domain in enumerate(domains, start=1):
            alignment_bonus = 7 if domain in blue_domains else 0
            candidates.append(
                {
                    "candidate_id": f"DIC-{index:04d}",
                    "domain": domain,
                    "innovation_name": f"{domain} Disruption Vector",
                    "alignmentBonus": alignment_bonus,
                    "sourceSignals": ("innovation_catalog", "blue_ocean_overlap" if alignment_bonus else "technology_watchlist"),
                }
            )
        return tuple(candidates)

    def _create_assessments(self, timestamp: str, candidates: tuple[dict[str, Any], ...], config: DisruptionConfig) -> tuple[StrategicDisruptionAssessment, ...]:
        scored = []
        for candidate in candidates:
            score = _score_candidate(candidate, timestamp)
            if score.overall_score >= config.minimum_disruption_score:
                scored.append((candidate, score))
        scored.sort(key=lambda item: (-item[1].overall_score, item[0]["domain"]))
        assessments = []
        for index, (candidate, score) in enumerate(scored[: config.maximum_assessments_per_cycle], start=1):
            assessment_id = f"DIO-ASM-{len(self._assessments) + index:06d}"
            adoption = _adoption_stage(candidate["domain"])
            assessments.append(
                StrategicDisruptionAssessment(
                    assessment_id=assessment_id,
                    timestamp=timestamp,
                    domain=candidate["domain"],
                    innovation_name=candidate["innovation_name"],
                    executive_summary=f"{candidate['domain']} shows potential to structurally alter incumbent economics; assessment is research-only.",
                    disruption_score=asdict(score),
                    technology_description=f"{candidate['domain']} evaluated as a disruptive technology/business-model vector.",
                    industry_impact=_industry_impact(candidate["domain"]),
                    commercial_readiness=_commercial_readiness(adoption),
                    adoption_stage=adoption,
                    innovation_assessment="Deterministic assessment of innovation magnitude, adoption velocity, cost advantage, and replacement potential.",
                    competitive_landscape="Potential disruptors may pressure incumbents through productivity gains, cost reduction, or new capability curves.",
                    incumbent_vulnerability=_incumbent_vulnerability(score.overall_score),
                    expected_adoption_curve=_adoption_curve(adoption),
                    capital_requirements="Requires follow-on validation of capex intensity, unit economics, and scaling constraints.",
                    market_size="Market size requires Analyst and Librarian validation before capital conclusions.",
                    strategic_importance=_strategic_importance(candidate["domain"]),
                    principal_risks=("commercial_adoption_delay", "incumbent_response", "regulatory_uncertainty", "capital_intensity"),
                    research_gaps=("map_incumbent_exposure", "validate_adoption_curve", "measure_cost_advantage", "collect_patent_and_filing_evidence"),
                    recommended_follow_on_offices=("Analyst Group", "Blue Ocean Intelligence", "Capital Rotation Intelligence", "Market Structure Intelligence", "Historian", "Librarian", "Academy"),
                    forecast_horizon=score.forecast_horizon,
                    confidence_score=round(config.default_confidence_score + (score.overall_score - 70.0) / 5, 4),
                    supporting_evidence=tuple(candidate["sourceSignals"]) + tuple(f"{factor}:{value}" for factor, value in score.component_scores.items()),
                    historian_archive_id=f"HIST-{assessment_id}",
                    librarian_index_id=f"LIB-{assessment_id}",
                    revision_history=({"revision": 1, "timestamp": timestamp, "reason": "initial_disruption_assessment"},),
                    advisory_only=True,
                    immutable=True,
                )
            )
        return tuple(assessments)


def _score_candidate(candidate: dict[str, Any], timestamp: str) -> DisruptionScore:
    domain = str(candidate["domain"])
    base = (sum(ord(char) for char in domain) % 33) + 52
    scores = {
        "innovation_magnitude": _clamp(base + candidate.get("alignmentBonus", 0)),
        "commercial_readiness": _clamp(52 + ADOPTION_STAGES.index(_adoption_stage(domain)) * 6),
        "adoption_velocity": _clamp(58 + (len(domain) * 3 % 31)),
        "cost_advantage": _clamp(50 + (sum(ord(char) for char in domain[:4]) % 38)),
        "productivity_improvement": _clamp(56 + (len(domain.replace(" ", "")) % 36)),
        "market_replacement_potential": _clamp(54 + (sum(ord(char) for char in domain[-4:]) % 37)),
        "competitive_advantage": _clamp(58 + (len(domain) % 32)),
        "intellectual_property": _clamp(55 + (sum(ord(char) for char in domain) % 36)),
        "scalability": _clamp(57 + (len(domain.split()) * 8)),
        "capital_efficiency": _clamp(78 - (len(domain) % 25)),
        "regulatory_outlook": _clamp(50 + (len(domain.split()) * 9)),
        "strategic_importance": _clamp(63 + (sum(ord(char) for char in domain) % 34)),
    }
    weights = {
        "innovation_magnitude": 0.12,
        "commercial_readiness": 0.10,
        "adoption_velocity": 0.10,
        "cost_advantage": 0.09,
        "productivity_improvement": 0.09,
        "market_replacement_potential": 0.10,
        "competitive_advantage": 0.08,
        "intellectual_property": 0.08,
        "scalability": 0.08,
        "capital_efficiency": 0.06,
        "regulatory_outlook": 0.05,
        "strategic_importance": 0.05,
    }
    overall = round(sum(scores[key] * weight for key, weight in weights.items()), 4)
    return DisruptionScore(
        overall_score=overall,
        component_scores=scores,
        confidence_interval=(round(max(0.0, overall - 7.5), 4), round(min(100.0, overall + 7.5), 4)),
        evidence_quality=round(min(100.0, 63.0 + len(candidate.get("sourceSignals", ())) * 7), 4),
        forecast_horizon=_forecast_horizon(domain),
        revision_history=({"revision": 1, "timestamp": timestamp, "reason": "deterministic_disruption_score"},),
    )


def _bridge_payload(assessments: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    return {
        "highestDisruptionScores": assessments[:5],
        "technologyReadiness": tuple({"technology": item["innovation_name"], "readiness": item["commercial_readiness"], "stage": item["adoption_stage"]} for item in assessments),
        "commercializationTimeline": tuple({"technology": item["innovation_name"], "horizon": item["forecast_horizon"], "adoptionCurve": item["expected_adoption_curve"]} for item in assessments),
        "industryRiskMap": tuple({"industry": item["domain"], "incumbentVulnerability": item["incumbent_vulnerability"], "replacementPotential": item["disruption_score"]["component_scores"]["market_replacement_potential"]} for item in assessments),
        "innovationHeatMap": tuple({"domain": item["domain"], "score": item["disruption_score"]["component_scores"]["innovation_magnitude"]} for item in assessments),
        "adoptionCurveDistribution": _distribution(item["adoption_stage"] for item in assessments),
        "emergingDisruptors": tuple(dict.fromkeys(item["innovation_name"] for item in assessments[:8])),
        "incumbentVulnerability": _distribution(item["incumbent_vulnerability"] for item in assessments),
        "strategicWatchList": tuple(item["innovation_name"] for item in assessments[:8]),
        "historicalForecastAccuracy": {"accuracy": 0.0, "sampleSize": 0, "status": "TRACKING_INITIAL_BASELINE"},
        "confidenceDistribution": _confidence_distribution(assessments),
        "evidenceQuality": _average(item["disruption_score"]["evidence_quality"] for item in assessments),
        "runtimeHealth": "NOMINAL",
        "workflowStatus": "bounded_snapshot_complete",
        "apiUsage": {"apiCost": 0.0, "mode": "deterministic_no_paid_calls"},
    }


def _metrics(assessments: tuple[dict[str, Any], ...], bridge: dict[str, Any]) -> dict[str, Any]:
    return {
        "disruptionAssessmentsProduced": len(assessments),
        "forecastAccuracy": 0.0,
        "commercializationAccuracy": 0.0,
        "technologyAdoptionAccuracy": 0.0,
        "industryTransformationAccuracy": 0.0,
        "averageDisruptionScore": _average(item["disruption_score"]["overall_score"] for item in assessments),
        "leadTimeBeforeWidespreadAdoption": "tracking",
        "leadTimeBeforeInstitutionalRecognition": "tracking",
        "evidenceQuality": bridge["evidenceQuality"],
        "confidenceCalibration": "tracking",
        "historicalHitRate": 0.0,
        "falsePositives": 0,
        "falseNegatives": 0,
        "enterpriseUtilization": len(bridge["strategicWatchList"]),
        "apiUtilization": 0.0,
        "workflowParticipation": "bounded_advisory_snapshot",
    }


def _research_directives(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    targets = ("Analyst Group", "Blue Ocean Intelligence", "Capital Rotation Intelligence", "Market Structure Intelligence", "Historian", "Librarian", "Academy")
    return tuple(
        {
            "directiveId": f"DIO-RD-{index:03d}",
            "targetOffice": targets[(index - 1) % len(targets)],
            "innovation": item["innovation_name"],
            "request": "validate_disruption_evidence",
            "advisoryOnly": True,
        }
        for index, item in enumerate(assessments[:7], start=1)
    )


def _connectors() -> tuple[dict[str, str], ...]:
    return tuple({"connectorType": item, "status": "INTERFACE_READY", "liveExternalCalls": "DISABLED"} for item in CONNECTOR_TYPES)


def _historian_feed(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"historianArchiveId": item["historian_archive_id"], "assessmentId": item["assessment_id"], "originalForecast": item["expected_adoption_curve"], "outcomeTracking": "pending"} for item in assessments)


def _librarian_feed(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"librarianIndexId": item["librarian_index_id"], "assessmentId": item["assessment_id"], "indexTerms": (item["domain"], item["innovation_name"], item["adoption_stage"], item["forecast_horizon"])} for item in assessments)


def _industry_impact(domain: str) -> dict[str, str]:
    return {
        "revenuePools": "possible_reallocation",
        "margins": "cost_curve_pressure",
        "supplyChains": "supplier_power_shift",
        "labor": "productivity_mix_change",
        "capitalAllocation": "research_attention_required",
        "infrastructure": "platform_or_capex_dependency",
        "competition": "incumbent_vulnerability_possible",
        "consumerBehavior": "adoption_curve_uncertain",
        "governmentPolicy": "regulatory_watch_required",
        "internationalCompetitiveness": _strategic_importance(domain),
    }


def _adoption_stage(domain: str) -> str:
    if domain in {"Artificial Intelligence", "Machine Learning", "Cybersecurity", "Cloud Infrastructure", "Digital Payments"}:
        return "Growth"
    if domain in {"Robotics", "Industrial Automation", "Autonomous Vehicles", "Advanced Packaging"}:
        return "Early Adoption"
    if domain in {"Fusion Energy", "Quantum Computing", "Gene Editing"}:
        return "Prototype"
    return "Pilot"


def _commercial_readiness(stage: str) -> str:
    return {
        "Concept": "research",
        "Laboratory": "research",
        "Prototype": "prototype",
        "Pilot": "pilot",
        "Early Adoption": "early_commercialization",
        "Growth": "scaling",
        "Mass Adoption": "scaling",
        "Mature": "mature",
        "Declining": "declining",
    }.get(stage, "pilot")


def _forecast_horizon(domain: str) -> str:
    if _adoption_stage(domain) in {"Growth", "Early Adoption"}:
        return "Strategic (1-3 Years)"
    if _adoption_stage(domain) == "Prototype":
        return "Grand Strategic (3-10 Years)"
    return "Operational (Months)"


def _adoption_curve(stage: str) -> str:
    return f"{stage} -> next_stage_watch"


def _incumbent_vulnerability(score: float) -> str:
    if score >= 78:
        return "HIGH"
    if score >= 66:
        return "MEDIUM"
    return "LOW"


def _strategic_importance(domain: str) -> str:
    if domain in {"Defense Technology", "Cybersecurity", "Semiconductor Manufacturing", "Space Infrastructure"}:
        return "national_security_critical"
    if domain in {"Water Infrastructure", "Small Modular Reactors", "Supply Chain Automation"}:
        return "infrastructure_resilience_critical"
    return "economic_resilience_and_productivity"


def _candidate_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    return {**candidate, "disruptionScorePreview": _score_candidate(candidate, "preview").overall_score}


def _inbox(sources: dict[str, Any]) -> tuple[dict[str, str], ...]:
    return tuple({"source": key, "messageType": "disruption_source_snapshot", "status": "received"} for key in sorted(sources) if sources.get(key))


def _outbox(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
    return tuple({"target": "Strategic Intelligence Command", "messageType": "Strategic Disruption Assessment", "recordId": item["assessment_id"]} for item in assessments)


def _distribution(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


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
        "grand": sources.get("enterpriseGrandStrategyEngine", {}).get("activeGrandStrategyRecord", {}),
        "config": sources.get("enterpriseConfigurationRegistry", {}).get("activeConfiguration", {}),
    }


def _hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)
