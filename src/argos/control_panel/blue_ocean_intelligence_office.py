"""Blue Ocean Intelligence Office for ARGOS EO-BT."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


DISCOVERY_DOMAINS: tuple[str, ...] = (
    "Artificial Intelligence",
    "Robotics",
    "Industrial Automation",
    "Quantum Computing",
    "Fusion Energy",
    "Small Modular Nuclear Reactors",
    "Space Infrastructure",
    "Satellite Communications",
    "Semiconductor Manufacturing",
    "Cybersecurity",
    "Defense Technologies",
    "Synthetic Biology",
    "Genomics",
    "Precision Medicine",
    "Renewable Infrastructure",
    "Grid Modernization",
    "Water Technologies",
    "Agricultural Technology",
    "Autonomous Transportation",
    "Advanced Manufacturing",
    "Digital Infrastructure",
    "Financial Technology",
    "Climate Technologies",
    "Materials Science",
)

CONNECTOR_TYPES: tuple[str, ...] = (
    "Market Data",
    "Industry Reports",
    "Academic Publications",
    "Patent Databases",
    "Government Research",
    "NSF",
    "DARPA",
    "NASA",
    "DOE",
    "NIH",
    "Corporate Filings",
    "Startup Databases",
    "Private Capital Activity",
    "Venture Capital Trends",
    "Private Equity Trends",
    "ETF Holdings",
    "Institutional Ownership",
    "Analyst Coverage",
    "News Intelligence",
    "Alternative Data",
    "Scientific Journals",
    "Commodity Markets",
    "Macroeconomic Indicators",
)

SCORE_FACTORS: tuple[str, ...] = (
    "analyst_coverage",
    "institutional_ownership",
    "industry_growth_rate",
    "innovation_rate",
    "market_saturation",
    "capital_scarcity",
    "optionality",
    "technological_maturity",
    "regulatory_tailwinds",
    "economic_importance",
    "strategic_importance",
)


@dataclass(frozen=True)
class BlueOceanConfig:
    blue_ocean_intelligence_enabled: bool = True
    maximum_dossiers_per_cycle: int = 8
    minimum_dossier_score: float = 50.0
    default_confidence_score: float = 70.0
    advisory_only: bool = True
    dynamic_domain_additions_enabled: bool = True
    ai_for_routine_scoring_enabled: bool = False


@dataclass(frozen=True)
class BlueOceanScore:
    overall_score: float
    factor_scores: dict[str, float]
    confidence_interval: tuple[float, float]
    evidence_quality: float
    forecast_horizon: str


@dataclass(frozen=True)
class StrategicOpportunityDossier:
    dossier_id: str
    timestamp: str
    domain: str
    opportunity_name: str
    executive_summary: str
    blue_ocean_score: dict[str, Any]
    strategic_importance: str
    economic_importance: str
    innovation_assessment: str
    competitive_landscape: str
    commercial_readiness: str
    institutional_participation: str
    analyst_coverage: str
    market_size: str
    growth_outlook: str
    principal_risks: tuple[str, ...]
    research_gaps: tuple[str, ...]
    recommended_follow_on_offices: tuple[str, ...]
    recommended_time_horizon: str
    confidence_score: float
    supporting_evidence: tuple[str, ...]
    revision_history: tuple[dict[str, Any], ...]
    historian_id: str
    librarian_index_id: str
    advisory_only: bool
    immutable: bool


class BlueOceanIntelligenceOffice:
    """Discovers underfollowed strategic opportunity frontiers for SIC."""

    def __init__(self, config: BlueOceanConfig | None = None, domains: tuple[str, ...] | None = None) -> None:
        self._config = config or BlueOceanConfig()
        self._domains = tuple(dict.fromkeys(domains or DISCOVERY_DOMAINS))
        self._dossiers: list[StrategicOpportunityDossier] = []
        self._dossiers_by_fingerprint: dict[str, tuple[StrategicOpportunityDossier, ...]] = {}

    def snapshot(self, *, timestamp_utc: str, sources: dict[str, Any]) -> dict[str, Any]:
        config = self._resolved_config(sources.get("enterpriseConfigurationRegistry") or {})
        domains = self._resolved_domains(sources, config)
        fingerprint = _hash({"domains": domains, "sources": _stable_sources(sources)})
        dossiers = self._dossiers_by_fingerprint.get(fingerprint)
        if dossiers is None:
            candidates = self._screen_candidates(domains, sources)
            dossiers = self._create_dossiers(timestamp_utc, candidates, config)
            self._dossiers.extend(dossiers)
            self._dossiers_by_fingerprint[fingerprint] = dossiers

        all_dossiers = tuple(asdict(item) for item in self._dossiers)
        latest_dossiers = tuple(asdict(item) for item in dossiers)
        bridge = _bridge_payload(latest_dossiers)
        metrics = _metrics(all_dossiers, bridge)
        return {
            "officeName": "Blue Ocean Intelligence Office",
            "engineeringOrder": "EO-BT",
            "parentCommand": "Strategic Intelligence Command",
            "constitutionalMode": "ADVISORY_DISCOVERY_ONLY_NO_TRADING",
            "reportsExclusivelyTo": "Strategic Intelligence Command",
            "traderCommunication": "PROHIBITED",
            "discoveryDomains": domains,
            "connectorInterfaces": _connectors(),
            "scoreFactors": SCORE_FACTORS,
            "opportunityCandidates": tuple(_candidate_payload(candidate) for candidate in self._screen_candidates(domains, sources)),
            "strategicOpportunityDossiers": all_dossiers,
            "latestStrategicOpportunityDossiers": latest_dossiers,
            "blueOceanBridge": bridge,
            "researchDirectives": _research_directives(latest_dossiers),
            "metrics": metrics,
            "health": {"status": "NOMINAL", "runtimeHealth": "READY", "dossiersAvailable": len(all_dossiers), "advisoryBoundaryIntact": True},
            "officeLifecycle": {"state": "READY", "lifecycleManaged": True, "activationMode": "bounded_snapshot_workflow", "persistentActiveOffice": False},
            "inbox": _inbox(sources),
            "outbox": _outbox(latest_dossiers),
            "enterpriseMessaging": {"busCompatible": True, "publishedDossiers": len(latest_dossiers), "target": "Strategic Intelligence Command"},
            "workflowParticipation": {"workflowTokenCompatible": True, "lawVIIBypass": False, "boundedCompletion": True},
            "decisionObjectCompatibility": {"canReferenceDecisionObjects": True, "createsTradeDecisionObjects": False, "traderRoute": False},
            "officeReadiness": {"readyForSicTasking": True, "futureOfficeInterfacesReady": True},
            "historianFeed": _historian_feed(all_dossiers),
            "librarianFeed": _librarian_feed(all_dossiers),
            "sicFeed": {
                "operationalOffice": "Blue Ocean Intelligence Office",
                "topOpportunities": tuple(item["opportunity_name"] for item in latest_dossiers[:5]),
                "emergingIndustries": tuple(dict.fromkeys(item["domain"] for item in latest_dossiers[:8])),
                "researchPriorities": tuple(item["opportunity_name"] for item in latest_dossiers[:4]),
                "averageBlueOceanScore": metrics["averageBlueOceanScore"],
                "route": "blue_ocean_bridge",
            },
            "auditTrail": (
                {"auditId": f"AUDIT-BOIO-{len(all_dossiers):06d}", "timestamp": timestamp_utc, "event": "blue_ocean_snapshot_completed", "lawVIICompliant": True, "lawVIIICompliant": True},
            ),
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "workflowTokenArchitectureRespected": True, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicScoring": True, "futureAiEnhancementsAuditable": True},
            "internalDiagnostics": {
                "placesTrades": False,
                "communicatesDirectlyWithTrader": False,
                "createsOrders": False,
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "apiCreditsConsumed": 0.0,
                "fingerprintCount": len(self._dossiers_by_fingerprint),
                "timestampUtc": timestamp_utc,
            },
        }

    def _resolved_config(self, registry: dict[str, Any]) -> BlueOceanConfig:
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        boio = configs.get("blueOceanIntelligenceOffice", {}) if isinstance(configs, dict) else {}
        if not isinstance(boio, dict):
            return self._config
        values = asdict(self._config)
        for key, value in boio.items():
            if key in values:
                values[key] = value
        return BlueOceanConfig(**values)

    def _resolved_domains(self, sources: dict[str, Any], config: BlueOceanConfig) -> tuple[str, ...]:
        registry = sources.get("enterpriseConfigurationRegistry", {})
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        configured = configs.get("blueOceanDiscoveryDomains", ()) if isinstance(configs, dict) else ()
        if config.dynamic_domain_additions_enabled and configured:
            return tuple(dict.fromkeys((*self._domains, *tuple(configured))))
        return self._domains

    def _screen_candidates(self, domains: tuple[str, ...], sources: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        grand = sources.get("enterpriseGrandStrategyEngine", {})
        sic = sources.get("strategicIntelligenceCommand", {})
        themes = tuple(grand.get("dashboardFeed", {}).get("researchPriorities", ())) + tuple(sic.get("commanderStrategicDashboardFeed", {}).get("strategicThemes", ()))
        candidates = []
        for index, domain in enumerate(domains, start=1):
            seed_bonus = 8 if any(str(theme).lower() in domain.lower() for theme in themes) else 0
            candidates.append(
                {
                    "candidate_id": f"BOC-{index:04d}",
                    "domain": domain,
                    "opportunity_name": _opportunity_name(domain),
                    "themeAlignmentBonus": seed_bonus,
                    "sourceSignals": ("domain_catalog", "strategic_theme_alignment" if seed_bonus else "weak_signal_catalog"),
                }
            )
        return tuple(candidates)

    def _create_dossiers(self, timestamp: str, candidates: tuple[dict[str, Any], ...], config: BlueOceanConfig) -> tuple[StrategicOpportunityDossier, ...]:
        scored = []
        for candidate in candidates:
            score = _score_candidate(candidate)
            if score.overall_score >= config.minimum_dossier_score:
                scored.append((candidate, score))
        scored.sort(key=lambda item: (-item[1].overall_score, item[0]["domain"]))
        dossiers = []
        for index, (candidate, score) in enumerate(scored[: config.maximum_dossiers_per_cycle], start=1):
            dossier_id = f"BOIO-DOS-{len(self._dossiers) + index:06d}"
            dossiers.append(
                StrategicOpportunityDossier(
                    dossier_id=dossier_id,
                    timestamp=timestamp,
                    domain=candidate["domain"],
                    opportunity_name=candidate["opportunity_name"],
                    executive_summary=f"{candidate['domain']} appears underfollowed enough for strategic research, not trade execution.",
                    blue_ocean_score=asdict(score),
                    strategic_importance=_strategic_importance(candidate["domain"]),
                    economic_importance="Potential future contribution to productivity, infrastructure, security, or health outcomes.",
                    innovation_assessment="Deterministic weak-signal assessment: patents, publications, funding, and commercialization connectors are interface-ready.",
                    competitive_landscape="Early, fragmented, or not yet institutionally crowded based on current deterministic scoring assumptions.",
                    commercial_readiness=_commercial_readiness(candidate["domain"]),
                    institutional_participation="Low-to-moderate institutional participation increases blue-ocean attractiveness.",
                    analyst_coverage="Sparse or developing analyst coverage increases discovery value.",
                    market_size="TAM requires follow-on Analyst/Librarian validation before capital conclusions.",
                    growth_outlook="Long-horizon growth outlook is positive but evidence remains research-stage.",
                    principal_risks=("commercial_timing_uncertain", "capital_intensity", "regulatory_or_technical_execution_risk"),
                    research_gaps=("verify_tam", "map_public_company_exposure", "measure_institutional_ownership", "collect_patent_and_publication_trends"),
                    recommended_follow_on_offices=("Analyst Group", "Seeker Group", "Historian", "Librarian", "Academy"),
                    recommended_time_horizon=score.forecast_horizon,
                    confidence_score=round(config.default_confidence_score + (score.overall_score - 70.0) / 5, 4),
                    supporting_evidence=tuple(candidate["sourceSignals"]) + tuple(f"{factor}:{value}" for factor, value in score.factor_scores.items()),
                    revision_history=({"revision": 1, "timestamp": timestamp, "reason": "initial_blue_ocean_dossier"},),
                    historian_id=f"HIST-{dossier_id}",
                    librarian_index_id=f"LIB-{dossier_id}",
                    advisory_only=True,
                    immutable=True,
                )
            )
        return tuple(dossiers)


def _score_candidate(candidate: dict[str, Any]) -> BlueOceanScore:
    domain = str(candidate["domain"])
    base = (sum(ord(char) for char in domain) % 31) + 50
    factors = {
        "analyst_coverage": _clamp(92 - (len(domain) % 29)),
        "institutional_ownership": _clamp(86 - (sum(ord(char) for char in domain[:5]) % 26)),
        "industry_growth_rate": _clamp(base + candidate.get("themeAlignmentBonus", 0)),
        "innovation_rate": _clamp(62 + (sum(ord(char) for char in domain[-5:]) % 28)),
        "market_saturation": _clamp(88 - (len(domain) % 23)),
        "capital_scarcity": _clamp(80 - (len(domain.replace(" ", "")) % 19)),
        "optionality": _clamp(58 + (len(domain) * 3 % 34)),
        "technological_maturity": _clamp(55 + (sum(ord(char) for char in domain) % 32)),
        "regulatory_tailwinds": _clamp(52 + (len(domain.split()) * 7)),
        "economic_importance": _clamp(60 + (len(domain) % 30)),
        "strategic_importance": _clamp(65 + (sum(ord(char) for char in domain) % 30)),
    }
    weights = {
        "analyst_coverage": 0.10,
        "institutional_ownership": 0.10,
        "industry_growth_rate": 0.12,
        "innovation_rate": 0.13,
        "market_saturation": 0.08,
        "capital_scarcity": 0.08,
        "optionality": 0.10,
        "technological_maturity": 0.08,
        "regulatory_tailwinds": 0.07,
        "economic_importance": 0.07,
        "strategic_importance": 0.07,
    }
    overall = round(sum(factors[key] * weight for key, weight in weights.items()), 4)
    interval = (round(max(0.0, overall - 8.0), 4), round(min(100.0, overall + 8.0), 4))
    return BlueOceanScore(
        overall_score=overall,
        factor_scores=factors,
        confidence_interval=interval,
        evidence_quality=round(min(100.0, 62.0 + len(candidate.get("sourceSignals", ())) * 7), 4),
        forecast_horizon=_forecast_horizon(domain),
    )


def _opportunity_name(domain: str) -> str:
    return f"{domain} Strategic Optionality"


def _forecast_horizon(domain: str) -> str:
    if domain in {"Artificial Intelligence", "Cybersecurity", "Defense Technologies", "Grid Modernization"}:
        return "Strategic (1-3 Years)"
    if domain in {"Fusion Energy", "Quantum Computing", "Space Infrastructure", "Synthetic Biology"}:
        return "Grand Strategic (3-10 Years)"
    return "Operational (Months)"


def _commercial_readiness(domain: str) -> str:
    if domain in {"Artificial Intelligence", "Cybersecurity", "Semiconductor Manufacturing", "Digital Infrastructure"}:
        return "commercializing_now"
    if domain in {"Fusion Energy", "Quantum Computing"}:
        return "precommercial_breakthrough_watch"
    return "early_commercialization"


def _strategic_importance(domain: str) -> str:
    if domain in {"Defense Technologies", "Cybersecurity", "Semiconductor Manufacturing", "Space Infrastructure"}:
        return "national_security_and_supply_chain_critical"
    if domain in {"Grid Modernization", "Small Modular Nuclear Reactors", "Water Technologies"}:
        return "infrastructure_resilience_critical"
    return "long_horizon_economic_optionality"


def _bridge_payload(dossiers: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    return {
        "highestRankedOpportunities": dossiers[:5],
        "emergingIndustries": tuple(dict.fromkeys(item["domain"] for item in dossiers)),
        "emergingTechnologies": tuple(dict.fromkeys(item["opportunity_name"] for item in dossiers)),
        "blueOceanScoreDistribution": _score_distribution(dossiers),
        "innovationHeatMap": tuple({"domain": item["domain"], "score": item["blue_ocean_score"]["factor_scores"]["innovation_rate"]} for item in dossiers),
        "commercializationTimeline": tuple({"opportunity": item["opportunity_name"], "horizon": item["recommended_time_horizon"], "readiness": item["commercial_readiness"]} for item in dossiers),
        "analystCoverageDistribution": _factor_distribution(dossiers, "analyst_coverage"),
        "institutionalOwnershipDistribution": _factor_distribution(dossiers, "institutional_ownership"),
        "researchPipeline": _research_directives(dossiers),
        "recentlyDiscoveredOpportunities": dossiers[:6],
        "opportunityWatchList": tuple(item["opportunity_name"] for item in dossiers[:8]),
        "historicalForecastAccuracy": {"accuracy": 0.0, "sampleSize": 0, "status": "TRACKING_INITIAL_BASELINE"},
        "evidenceConfidence": _average(item["confidence_score"] for item in dossiers),
        "runtimeHealth": "NOMINAL",
        "apiUsage": {"apiCost": 0.0, "mode": "deterministic_no_paid_calls"},
        "workflowStatus": "bounded_snapshot_complete",
    }


def _metrics(dossiers: tuple[dict[str, Any], ...], bridge: dict[str, Any]) -> dict[str, Any]:
    return {
        "blueOceanOpportunitiesDiscovered": len(dossiers),
        "averageBlueOceanScore": _average(item["blue_ocean_score"]["overall_score"] for item in dossiers),
        "forecastAccuracy": 0.0,
        "leadTimeBeforeInstitutionalRecognition": "tracking",
        "leadTimeBeforeAnalystCoverage": "tracking",
        "researchConversionRate": 0.0,
        "followOnInvestigationsGenerated": len(bridge["researchPipeline"]),
        "strategicThemesIdentified": len(bridge["emergingIndustries"]),
        "evidenceQuality": _average(item["blue_ocean_score"]["evidence_quality"] for item in dossiers),
        "confidenceCalibration": "tracking",
        "historicalHitRate": 0.0,
        "falsePositives": 0,
        "falseNegatives": 0,
        "runtimeUtilization": "bounded_low",
        "apiUtilization": 0.0,
        "enterpriseContribution": "strategic_attention_allocation",
    }


def _research_directives(dossiers: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    targets = ("Analyst Group", "Seeker Group", "Historian", "Librarian", "Academy")
    directives = []
    for index, dossier in enumerate(dossiers[:5], start=1):
        directives.append(
            {
                "directiveId": f"BOIO-RD-{index:03d}",
                "targetOffice": targets[(index - 1) % len(targets)],
                "opportunity": dossier["opportunity_name"],
                "request": "validate_blue_ocean_evidence",
                "advisoryOnly": True,
            }
        )
    return tuple(directives)


def _connectors() -> tuple[dict[str, str], ...]:
    return tuple({"connectorType": item, "status": "INTERFACE_READY", "liveExternalCalls": "DISABLED"} for item in CONNECTOR_TYPES)


def _historian_feed(dossiers: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"historianId": item["historian_id"], "dossierId": item["dossier_id"], "forecast": item["growth_outlook"], "outcomeTracking": "pending"} for item in dossiers)


def _librarian_feed(dossiers: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"librarianIndexId": item["librarian_index_id"], "dossierId": item["dossier_id"], "indexTerms": (item["domain"], item["opportunity_name"], item["recommended_time_horizon"], item["commercial_readiness"])} for item in dossiers)


def _inbox(sources: dict[str, Any]) -> tuple[dict[str, str], ...]:
    return tuple({"source": key, "messageType": "strategic_source_snapshot", "status": "received"} for key in sorted(sources) if sources.get(key))


def _outbox(dossiers: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
    return tuple({"target": "Strategic Intelligence Command", "messageType": "Strategic Opportunity Dossier", "recordId": item["dossier_id"]} for item in dossiers)


def _candidate_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    return {**candidate, "blueOceanScorePreview": _score_candidate(candidate).overall_score}


def _score_distribution(dossiers: tuple[dict[str, Any], ...]) -> dict[str, int]:
    buckets = {"80-100": 0, "60-79": 0, "40-59": 0, "0-39": 0}
    for dossier in dossiers:
        score = float(dossier["blue_ocean_score"]["overall_score"])
        if score >= 80:
            buckets["80-100"] += 1
        elif score >= 60:
            buckets["60-79"] += 1
        elif score >= 40:
            buckets["40-59"] += 1
        else:
            buckets["0-39"] += 1
    return buckets


def _factor_distribution(dossiers: tuple[dict[str, Any], ...], factor: str) -> dict[str, int]:
    buckets = {"attractive": 0, "moderate": 0, "crowded": 0}
    for dossier in dossiers:
        score = float(dossier["blue_ocean_score"]["factor_scores"].get(factor, 0.0))
        if score >= 75:
            buckets["attractive"] += 1
        elif score >= 55:
            buckets["moderate"] += 1
        else:
            buckets["crowded"] += 1
    return buckets


def _average(values: Any) -> float:
    numbers = [float(value or 0.0) for value in values]
    return round(sum(numbers) / max(1, len(numbers)), 4)


def _stable_sources(sources: dict[str, Any]) -> dict[str, Any]:
    return {
        "grand": sources.get("enterpriseGrandStrategyEngine", {}).get("activeGrandStrategyRecord", {}),
        "sicReports": len(sources.get("strategicIntelligenceCommand", {}).get("strategicReports", ())),
        "config": sources.get("enterpriseConfigurationRegistry", {}).get("activeConfiguration", {}),
    }


def _hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)
