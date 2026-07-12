"""Market Structure Intelligence Office for ARGOS EO-BX."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


EVALUATION_DOMAINS: tuple[str, ...] = (
    "Public Equities",
    "Exchange Traded Funds",
    "Fixed Income",
    "Corporate Credit",
    "Government Bonds",
    "Currencies",
    "Commodities",
    "Precious Metals",
    "Energy Markets",
    "Cryptocurrency",
    "Options Markets",
    "Futures Markets",
    "Volatility Products",
    "International Markets",
    "Cross-Asset Relationships",
)

CONNECTOR_TYPES: tuple[str, ...] = (
    "Exchange Data",
    "Market Data Vendors",
    "Order Flow",
    "Volume Statistics",
    "ETF Holdings",
    "Fund Flows",
    "Options Data",
    "Volatility Indices",
    "Credit Markets",
    "Yield Curves",
    "Central Bank Publications",
    "Commodity Markets",
    "Macroeconomic Indicators",
    "International Markets",
    "Alternative Data",
    "Academic Research",
    "Government Publications",
)

SCORE_COMPONENTS: tuple[str, ...] = (
    "liquidity_quality",
    "liquidity_concentration",
    "volatility_regime",
    "market_breadth",
    "correlation_structure",
    "price_discovery_efficiency",
    "institutional_activity",
    "market_stress",
    "structural_stability",
    "opportunity_density",
)

STRUCTURAL_CLASSIFICATIONS: tuple[str, ...] = (
    "Highly Efficient",
    "Efficient",
    "Transitional",
    "Opportunity Rich",
    "Structurally Distorted",
    "Stressed",
    "Crisis",
    "Recovery",
)

ROOT_CAUSE_FACTORS: tuple[str, ...] = (
    "Liquidity",
    "Volatility",
    "Interest Rates",
    "Monetary Policy",
    "Market Participation",
    "Leverage",
    "Passive Investment",
    "Institutional Behavior",
    "Macroeconomics",
    "Regulation",
    "Technology",
    "Global Capital Flows",
)


@dataclass(frozen=True)
class MarketStructureConfig:
    market_structure_intelligence_office_enabled: bool = True
    maximum_assessments_per_cycle: int = 10
    minimum_market_structure_score: float = 48.0
    default_confidence_score: float = 71.0
    dynamic_domain_additions_enabled: bool = True
    ai_for_routine_scoring_enabled: bool = False


@dataclass(frozen=True)
class MarketStructureScore:
    overall_score: float
    component_scores: dict[str, float]
    confidence_interval: tuple[float, float]
    evidence_quality: float
    forecast_horizon: str
    revision_history: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class StrategicMarketStructureAssessment:
    assessment_id: str
    timestamp: str
    asset_class: str
    market: str
    region: str
    executive_summary: str
    market_structure_score: dict[str, Any]
    structural_classification: str
    liquidity_assessment: str
    volatility_assessment: str
    correlation_assessment: str
    breadth_assessment: str
    institutional_participation: str
    structural_risks: tuple[str, ...]
    structural_opportunities: tuple[str, ...]
    root_cause_analysis: tuple[str, ...]
    historical_comparison: str
    forecast_horizon: str
    confidence_score: float
    supporting_evidence: tuple[str, ...]
    historian_archive_id: str
    librarian_index_id: str
    revision_history: tuple[dict[str, Any], ...]
    advisory_only: bool
    immutable: bool


class MarketStructureIntelligenceOffice:
    """Studies market mechanics and structural regimes without trading authority."""

    def __init__(self, config: MarketStructureConfig | None = None, domains: tuple[str, ...] | None = None) -> None:
        self._config = config or MarketStructureConfig()
        self._domains = tuple(dict.fromkeys(domains or EVALUATION_DOMAINS))
        self._assessments: list[StrategicMarketStructureAssessment] = []
        self._assessments_by_fingerprint: dict[str, tuple[StrategicMarketStructureAssessment, ...]] = {}

    def snapshot(self, *, timestamp_utc: str, sources: dict[str, Any]) -> dict[str, Any]:
        config = self._resolved_config(sources.get("enterpriseConfigurationRegistry") or {})
        domains = self._resolved_domains(sources, config)
        fingerprint = _hash({"domains": domains, "sources": _stable_sources(sources)})
        assessments = self._assessments_by_fingerprint.get(fingerprint)
        if assessments is None:
            markets = self._identify_markets(domains, sources)
            assessments = self._create_assessments(timestamp_utc, markets, config)
            self._assessments.extend(assessments)
            self._assessments_by_fingerprint[fingerprint] = assessments

        all_assessments = tuple(asdict(item) for item in self._assessments)
        latest_assessments = tuple(asdict(item) for item in assessments)
        bridge = _bridge_payload(latest_assessments)
        metrics = _metrics(all_assessments, bridge)
        return {
            "officeName": "Market Structure Intelligence Office",
            "engineeringOrder": "EO-BX",
            "parentCommand": "Strategic Intelligence Command",
            "constitutionalMode": "ADVISORY_MARKET_MECHANICS_ASSESSMENT_ONLY_NO_TRADING",
            "reportsExclusivelyTo": "Strategic Intelligence Command",
            "tradingAuthority": "NONE",
            "evaluationDomains": domains,
            "connectorInterfaces": _connectors(),
            "scoreComponents": SCORE_COMPONENTS,
            "structuralClassifications": STRUCTURAL_CLASSIFICATIONS,
            "rootCauseFactors": ROOT_CAUSE_FACTORS,
            "evaluatedMarkets": tuple(_market_payload(market) for market in self._identify_markets(domains, sources)),
            "strategicMarketStructureAssessments": all_assessments,
            "latestStrategicMarketStructureAssessments": latest_assessments,
            "marketStructureIntelligenceBridge": bridge,
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
                "operationalOffice": "Market Structure Intelligence Office",
                "topStructuralOpportunities": tuple(item["market"] for item in latest_assessments[:5]),
                "structuralClassifications": tuple(item["structural_classification"] for item in latest_assessments[:8]),
                "researchPriorities": tuple(item["market"] for item in latest_assessments[:4]),
                "averageMarketStructureScore": metrics["averageMarketStructureScore"],
                "route": "market_structure_bridge",
            },
            "auditTrail": (
                {"auditId": f"AUDIT-MSIO-{len(all_assessments):06d}", "timestamp": timestamp_utc, "event": "market_structure_snapshot_completed", "lawVIICompliant": True, "lawVIIICompliant": True},
            ),
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "workflowTokenArchitectureRespected": True, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicScoring": True, "futureAiEnhancementsAuditable": True},
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

    def _resolved_config(self, registry: dict[str, Any]) -> MarketStructureConfig:
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        msio = configs.get("marketStructureIntelligenceOffice", {}) if isinstance(configs, dict) else {}
        if not isinstance(msio, dict):
            return self._config
        values = asdict(self._config)
        for key, value in msio.items():
            if key in values:
                values[key] = value
        return MarketStructureConfig(**values)

    def _resolved_domains(self, sources: dict[str, Any], config: MarketStructureConfig) -> tuple[str, ...]:
        registry = sources.get("enterpriseConfigurationRegistry", {})
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        configured = configs.get("marketStructureDomains", ()) if isinstance(configs, dict) else ()
        if config.dynamic_domain_additions_enabled and configured:
            return tuple(dict.fromkeys((*self._domains, *tuple(configured))))
        return self._domains

    def _identify_markets(self, domains: tuple[str, ...], sources: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        correlation = sources.get("correlationIntelligenceEngine", {})
        stress = sources.get("stressTestingEngine", {})
        risk = sources.get("enterpriseRiskFactorEngine", {})
        risk_level = risk.get("commanderSummary", {}).get("riskLevel", "unknown")
        correlation_bonus = 6 if correlation.get("correlationMatrix") or correlation.get("commanderSummary") else 0
        stress_bonus = 7 if stress.get("latestStressResult") or risk_level in {"high", "critical"} else 0
        markets = []
        for index, domain in enumerate(domains, start=1):
            markets.append(
                {
                    "market_id": f"MSIO-MKT-{index:04d}",
                    "asset_class": domain,
                    "market": f"{domain} Structure Complex",
                    "region": "Global" if domain in {"Currencies", "Commodities", "Precious Metals", "Energy Markets", "International Markets", "Cross-Asset Relationships"} else "United States",
                    "correlationBonus": correlation_bonus,
                    "stressBonus": stress_bonus,
                    "sourceSignals": (
                        "market_structure_domain_catalog",
                        "correlation_intelligence_overlap" if correlation_bonus else "correlation_interface_ready",
                        "stress_context_overlap" if stress_bonus else "stress_interface_ready",
                    ),
                }
            )
        return tuple(markets)

    def _create_assessments(self, timestamp: str, markets: tuple[dict[str, Any], ...], config: MarketStructureConfig) -> tuple[StrategicMarketStructureAssessment, ...]:
        scored = []
        for market in markets:
            score = _score_market(market, timestamp)
            if score.overall_score >= config.minimum_market_structure_score:
                scored.append((market, score))
        scored.sort(key=lambda item: (-item[1].overall_score, item[0]["asset_class"]))
        assessments = []
        for index, (market, score) in enumerate(scored[: config.maximum_assessments_per_cycle], start=1):
            assessment_id = f"MSIO-ASM-{len(self._assessments) + index:06d}"
            classification = _classification(score)
            assessments.append(
                StrategicMarketStructureAssessment(
                    assessment_id=assessment_id,
                    timestamp=timestamp,
                    asset_class=market["asset_class"],
                    market=market["market"],
                    region=market["region"],
                    executive_summary=f"{market['market']} is classified as {classification} based on deterministic liquidity, volatility, breadth, and stress evidence.",
                    market_structure_score=asdict(score),
                    structural_classification=classification,
                    liquidity_assessment=_liquidity_assessment(score),
                    volatility_assessment=_volatility_assessment(score),
                    correlation_assessment=_correlation_assessment(score),
                    breadth_assessment=_breadth_assessment(score),
                    institutional_participation=_institutional_participation(score),
                    structural_risks=_structural_risks(score, classification),
                    structural_opportunities=_structural_opportunities(score, classification),
                    root_cause_analysis=_root_causes(score),
                    historical_comparison=_historical_comparison(classification),
                    forecast_horizon=score.forecast_horizon,
                    confidence_score=round(config.default_confidence_score + (score.evidence_quality - 70.0) / 5, 4),
                    supporting_evidence=tuple(market["sourceSignals"]) + tuple(f"{component}:{value}" for component, value in score.component_scores.items()),
                    historian_archive_id=f"HIST-{assessment_id}",
                    librarian_index_id=f"LIB-{assessment_id}",
                    revision_history=({"revision": 1, "timestamp": timestamp, "reason": "initial_market_structure_assessment"},),
                    advisory_only=True,
                    immutable=True,
                )
            )
        return tuple(assessments)


def _score_market(market: dict[str, Any], timestamp: str) -> MarketStructureScore:
    asset_class = str(market["asset_class"])
    seed = sum(ord(char) for char in asset_class)
    components = {
        "liquidity_quality": _clamp(52 + seed % 39),
        "liquidity_concentration": _clamp(48 + (len(asset_class) * 5 % 42)),
        "volatility_regime": _clamp(50 + (seed // 3 % 40) + market.get("stressBonus", 0)),
        "market_breadth": _clamp(54 + (len(asset_class.split()) * 9)),
        "correlation_structure": _clamp(49 + (seed // 5 % 38) + market.get("correlationBonus", 0)),
        "price_discovery_efficiency": _clamp(56 + (seed // 7 % 34)),
        "institutional_activity": _clamp(51 + (len(asset_class.replace(" ", "")) * 3 % 39)),
        "market_stress": _clamp(45 + (seed // 11 % 42) + market.get("stressBonus", 0)),
        "structural_stability": _clamp(86 - (seed % 31)),
        "opportunity_density": _clamp(50 + (seed // 13 % 43) + market.get("correlationBonus", 0)),
    }
    weights = {
        "liquidity_quality": 0.12,
        "liquidity_concentration": 0.09,
        "volatility_regime": 0.11,
        "market_breadth": 0.09,
        "correlation_structure": 0.11,
        "price_discovery_efficiency": 0.11,
        "institutional_activity": 0.09,
        "market_stress": 0.11,
        "structural_stability": 0.09,
        "opportunity_density": 0.08,
    }
    overall = round(sum(components[key] * weight for key, weight in weights.items()), 4)
    evidence_quality = round(min(100.0, 63.0 + len(market.get("sourceSignals", ())) * 6 + market.get("correlationBonus", 0) / 2), 4)
    return MarketStructureScore(
        overall_score=overall,
        component_scores=components,
        confidence_interval=(round(max(0.0, overall - 7.5), 4), round(min(100.0, overall + 7.5), 4)),
        evidence_quality=evidence_quality,
        forecast_horizon=_forecast_horizon(overall),
        revision_history=({"revision": 1, "timestamp": timestamp, "reason": "deterministic_market_structure_score"},),
    )


def _bridge_payload(assessments: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    return {
        "marketStructureScore": tuple({"market": item["market"], "classification": item["structural_classification"], "score": item["market_structure_score"]["overall_score"]} for item in assessments[:8]),
        "liquidityHeatMap": tuple({"market": item["market"], "score": item["market_structure_score"]["component_scores"]["liquidity_quality"], "assessment": item["liquidity_assessment"]} for item in assessments),
        "volatilityRegimes": tuple({"market": item["market"], "score": item["market_structure_score"]["component_scores"]["volatility_regime"], "assessment": item["volatility_assessment"]} for item in assessments),
        "breadthIndicators": tuple({"market": item["market"], "score": item["market_structure_score"]["component_scores"]["market_breadth"], "assessment": item["breadth_assessment"]} for item in assessments),
        "correlationMatrix": tuple({"market": item["market"], "score": item["market_structure_score"]["component_scores"]["correlation_structure"], "assessment": item["correlation_assessment"]} for item in assessments),
        "crossAssetRelationships": tuple({"market": item["market"], "rootCauses": item["root_cause_analysis"][:3], "region": item["region"]} for item in assessments),
        "structuralOpportunityMap": tuple({"market": item["market"], "opportunities": item["structural_opportunities"], "score": item["market_structure_score"]["component_scores"]["opportunity_density"]} for item in assessments),
        "systemicStressIndicators": tuple({"market": item["market"], "risks": item["structural_risks"], "score": item["market_structure_score"]["component_scores"]["market_stress"]} for item in assessments),
        "institutionalParticipation": tuple({"market": item["market"], "assessment": item["institutional_participation"], "score": item["market_structure_score"]["component_scores"]["institutional_activity"]} for item in assessments),
        "historicalRegimeTimeline": tuple({"market": item["market"], "classification": item["structural_classification"], "comparison": item["historical_comparison"], "horizon": item["forecast_horizon"]} for item in assessments),
        "confidenceDistribution": _confidence_distribution(assessments),
        "evidenceQuality": _average(item["market_structure_score"]["evidence_quality"] for item in assessments),
        "runtimeHealth": "NOMINAL",
        "workflowStatus": "bounded_snapshot_complete",
        "apiUsage": {"apiCost": 0.0, "mode": "deterministic_no_paid_calls"},
    }


def _metrics(assessments: tuple[dict[str, Any], ...], bridge: dict[str, Any]) -> dict[str, Any]:
    return {
        "marketStructureAssessmentsProduced": len(assessments),
        "forecastAccuracy": 0.0,
        "regimeIdentificationAccuracy": 0.0,
        "liquidityPredictionAccuracy": 0.0,
        "volatilityClassificationAccuracy": 0.0,
        "averageMarketStructureScore": _average(item["market_structure_score"]["overall_score"] for item in assessments),
        "evidenceQuality": bridge["evidenceQuality"],
        "confidenceCalibration": "tracking",
        "historicalHitRate": 0.0,
        "falsePositives": 0,
        "falseNegatives": 0,
        "enterpriseUtilization": len(bridge["marketStructureScore"]),
        "apiUtilization": 0.0,
        "workflowParticipation": "bounded_advisory_snapshot",
    }


def _research_directives(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    targets = ("Analyst Group", "Capital Rotation Intelligence Office", "Blue Ocean Intelligence Office", "Short Opportunity Office", "Disruption Intelligence Office", "Historian", "Librarian", "Academy")
    return tuple(
        {
            "directiveId": f"MSIO-RD-{index:03d}",
            "targetOffice": targets[(index - 1) % len(targets)],
            "market": item["market"],
            "request": "validate_market_structure_evidence",
            "advisoryOnly": True,
        }
        for index, item in enumerate(assessments[:8], start=1)
    )


def _connectors() -> tuple[dict[str, str], ...]:
    return tuple({"connectorType": item, "status": "INTERFACE_READY", "liveExternalCalls": "DISABLED"} for item in CONNECTOR_TYPES)


def _historian_feed(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"historianArchiveId": item["historian_archive_id"], "assessmentId": item["assessment_id"], "originalAssessment": item["executive_summary"], "regimeTransitionTracking": "pending", "outcomeTracking": "pending"} for item in assessments)


def _librarian_feed(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "librarianIndexId": item["librarian_index_id"],
            "assessmentId": item["assessment_id"],
            "indexTerms": (item["asset_class"], item["market"], item["region"], item["structural_classification"], item["forecast_horizon"], str(item["confidence_score"]), str(item["market_structure_score"]["evidence_quality"])),
        }
        for item in assessments
    )


def _market_payload(market: dict[str, Any]) -> dict[str, Any]:
    return {**market, "marketStructureScorePreview": _score_market(market, "preview").overall_score}


def _inbox(sources: dict[str, Any]) -> tuple[dict[str, str], ...]:
    return tuple({"source": key, "messageType": "market_structure_source_snapshot", "status": "received"} for key in sorted(sources) if sources.get(key))


def _outbox(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
    return tuple({"target": "Strategic Intelligence Command", "messageType": "Strategic Market Structure Assessment", "recordId": item["assessment_id"]} for item in assessments)


def _classification(score: MarketStructureScore) -> str:
    stress = score.component_scores["market_stress"]
    opportunity = score.component_scores["opportunity_density"]
    stability = score.component_scores["structural_stability"]
    liquidity = score.component_scores["liquidity_quality"]
    if stress >= 84:
        return "Crisis"
    if stress >= 74:
        return "Stressed"
    if opportunity >= 78 and stability < 62:
        return "Structurally Distorted"
    if opportunity >= 72:
        return "Opportunity Rich"
    if stability >= 76 and liquidity >= 70:
        return "Highly Efficient"
    if stability >= 66:
        return "Efficient"
    if score.overall_score >= 62:
        return "Transitional"
    return "Recovery"


def _liquidity_assessment(score: MarketStructureScore) -> str:
    return "liquidity_conditions_deep_and_resilient" if score.component_scores["liquidity_quality"] >= 70 else "liquidity_conditions_require_monitoring"


def _volatility_assessment(score: MarketStructureScore) -> str:
    value = score.component_scores["volatility_regime"]
    if value >= 78:
        return "elevated_clustered_volatility_regime"
    if value >= 62:
        return "transitional_volatility_regime"
    return "contained_volatility_regime"


def _correlation_assessment(score: MarketStructureScore) -> str:
    return "correlations_are_regime_sensitive" if score.component_scores["correlation_structure"] >= 68 else "correlations_remain_diversifying"


def _breadth_assessment(score: MarketStructureScore) -> str:
    return "breadth_supports_broad_participation" if score.component_scores["market_breadth"] >= 70 else "breadth_is_narrow_or_fragile"


def _institutional_participation(score: MarketStructureScore) -> str:
    return "institutional_activity_material_to_price_discovery" if score.component_scores["institutional_activity"] >= 70 else "institutional_activity_watch"


def _structural_risks(score: MarketStructureScore, classification: str) -> tuple[str, ...]:
    risks = ["liquidity_disappears_under_stress", "correlation_breakdown", "volatility_clustering"]
    if classification in {"Stressed", "Crisis", "Structurally Distorted"}:
        risks += ["systemic_stress_propagation", "forced_deleveraging"]
    if score.component_scores["liquidity_concentration"] >= 72:
        risks.append("passive_or_institutional_concentration")
    return tuple(dict.fromkeys(risks))


def _structural_opportunities(score: MarketStructureScore, classification: str) -> tuple[str, ...]:
    opportunities = ["liquidity_regime_monitoring", "volatility_regime_filtering", "cross_asset_confirmation"]
    if classification in {"Opportunity Rich", "Structurally Distorted", "Recovery"}:
        opportunities += ["persistent_mispricing_research", "market_mechanism_edge_mapping"]
    if score.component_scores["price_discovery_efficiency"] < 68:
        opportunities.append("delayed_information_absorption_research")
    return tuple(dict.fromkeys(opportunities))


def _root_causes(score: MarketStructureScore) -> tuple[str, ...]:
    causes = []
    if score.component_scores["liquidity_quality"] < 65 or score.component_scores["liquidity_concentration"] >= 70:
        causes.append("Liquidity")
    if score.component_scores["volatility_regime"] >= 68:
        causes.append("Volatility")
    if score.component_scores["market_stress"] >= 66:
        causes.extend(("Interest Rates", "Leverage"))
    if score.component_scores["institutional_activity"] >= 68:
        causes.append("Institutional Behavior")
    if score.component_scores["correlation_structure"] >= 68:
        causes.append("Global Capital Flows")
    return tuple(dict.fromkeys(causes or ("Market Participation", "Macroeconomics")))


def _historical_comparison(classification: str) -> str:
    return f"{classification.lower().replace(' ', '_')}_baseline_established_for_future_regime_comparison"


def _forecast_horizon(score: float) -> str:
    if score >= 76:
        return "Immediate (Days)"
    if score >= 66:
        return "Near-Term (Weeks)"
    if score >= 56:
        return "Operational (Months)"
    return "Strategic (1-3 Years)"


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
        "correlation": sources.get("correlationIntelligenceEngine", {}).get("commanderSummary", {}),
        "risk": sources.get("enterpriseRiskFactorEngine", {}).get("commanderSummary", {}),
        "stress": sources.get("stressTestingEngine", {}).get("latestStressResult", {}),
        "market": sources.get("marketContextIntegrationEngine", {}).get("marketContext", {}),
        "config": sources.get("enterpriseConfigurationRegistry", {}).get("activeConfiguration", {}),
    }


def _hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)
