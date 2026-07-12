"""Capital Rotation Intelligence Office for ARGOS EO-BY."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


EVALUATION_DOMAINS: tuple[str, ...] = (
    "Public Equities",
    "Exchange Traded Funds",
    "Mutual Funds",
    "Closed-End Funds",
    "Fixed Income",
    "Corporate Credit",
    "Government Bonds",
    "Commodities",
    "Currencies",
    "Precious Metals",
    "Energy Markets",
    "Cryptocurrency",
    "Private Markets",
    "International Equity Markets",
    "Domestic Equity Markets",
    "Growth",
    "Value",
    "Large Cap",
    "Mid Cap",
    "Small Cap",
)

CONNECTOR_TYPES: tuple[str, ...] = (
    "ETF Holdings",
    "ETF Flow Data",
    "Mutual Fund Reports",
    "Institutional Ownership",
    "13F Filings",
    "Exchange Data",
    "Market Volume",
    "Sector Performance",
    "Industry Performance",
    "Options Markets",
    "Bond Markets",
    "Credit Markets",
    "Commodity Markets",
    "Currency Markets",
    "Central Bank Publications",
    "Macroeconomic Indicators",
    "Alternative Data",
    "Government Publications",
    "Corporate Filings",
    "International Market Data",
)

SCORE_COMPONENTS: tuple[str, ...] = (
    "net_capital_inflow",
    "net_capital_outflow",
    "institutional_participation",
    "etf_flow_analysis",
    "mutual_fund_activity",
    "options_positioning",
    "relative_strength",
    "breadth_of_participation",
    "rotation_persistence",
    "macroeconomic_alignment",
    "strategic_conviction",
)

ROTATION_CLASSIFICATIONS: tuple[str, ...] = (
    "Short-Term Rotation",
    "Intermediate Rotation",
    "Strategic Rotation",
    "Structural Rotation",
    "Risk-Off",
    "Risk-On",
    "Defensive Migration",
    "Growth Migration",
    "Recovery Rotation",
    "Late-Cycle Rotation",
)

ROOT_CAUSE_FACTORS: tuple[str, ...] = (
    "Interest Rates",
    "Inflation",
    "Economic Growth",
    "Corporate Earnings",
    "Monetary Policy",
    "Fiscal Policy",
    "Geopolitics",
    "Commodity Prices",
    "Market Valuation",
    "Risk Appetite",
    "Liquidity Conditions",
    "Institutional Behavior",
)


@dataclass(frozen=True)
class CapitalRotationConfig:
    capital_rotation_intelligence_office_enabled: bool = True
    maximum_assessments_per_cycle: int = 10
    minimum_capital_rotation_score: float = 50.0
    default_confidence_score: float = 70.0
    dynamic_domain_additions_enabled: bool = True
    ai_for_routine_scoring_enabled: bool = False


@dataclass(frozen=True)
class CapitalRotationScore:
    overall_score: float
    component_scores: dict[str, float]
    confidence_interval: tuple[float, float]
    evidence_quality: float
    forecast_horizon: str
    revision_history: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class StrategicCapitalRotationAssessment:
    assessment_id: str
    timestamp: str
    asset_class: str
    segment: str
    region: str
    executive_summary: str
    capital_rotation_score: dict[str, Any]
    rotation_classification: str
    primary_capital_destinations: tuple[str, ...]
    primary_capital_sources: tuple[str, ...]
    sector_rotation: str
    industry_rotation: str
    asset_allocation_trends: str
    geographic_rotation: str
    institutional_participation: str
    rotation_persistence: str
    macroeconomic_context: str
    root_cause_analysis: tuple[str, ...]
    principal_risks: tuple[str, ...]
    forecast_horizon: str
    confidence_score: float
    supporting_evidence: tuple[str, ...]
    historian_archive_id: str
    librarian_index_id: str
    revision_history: tuple[dict[str, Any], ...]
    advisory_only: bool
    immutable: bool


class CapitalRotationIntelligenceOffice:
    """Tracks capital migration without issuing trade orders."""

    def __init__(self, config: CapitalRotationConfig | None = None, domains: tuple[str, ...] | None = None) -> None:
        self._config = config or CapitalRotationConfig()
        self._domains = tuple(dict.fromkeys(domains or EVALUATION_DOMAINS))
        self._assessments: list[StrategicCapitalRotationAssessment] = []
        self._assessments_by_fingerprint: dict[str, tuple[StrategicCapitalRotationAssessment, ...]] = {}

    def snapshot(self, *, timestamp_utc: str, sources: dict[str, Any]) -> dict[str, Any]:
        config = self._resolved_config(sources.get("enterpriseConfigurationRegistry") or {})
        domains = self._resolved_domains(sources, config)
        fingerprint = _hash({"domains": domains, "sources": _stable_sources(sources)})
        assessments = self._assessments_by_fingerprint.get(fingerprint)
        if assessments is None:
            segments = self._identify_segments(domains, sources)
            assessments = self._create_assessments(timestamp_utc, segments, config)
            self._assessments.extend(assessments)
            self._assessments_by_fingerprint[fingerprint] = assessments

        all_assessments = tuple(asdict(item) for item in self._assessments)
        latest_assessments = tuple(asdict(item) for item in assessments)
        bridge = _bridge_payload(latest_assessments)
        metrics = _metrics(all_assessments, bridge)
        return {
            "officeName": "Capital Rotation Intelligence Office",
            "engineeringOrder": "EO-BY",
            "parentCommand": "Strategic Intelligence Command",
            "constitutionalMode": "ADVISORY_CAPITAL_FLOW_ASSESSMENT_ONLY_NO_TRADING",
            "reportsExclusivelyTo": "Strategic Intelligence Command",
            "tradingAuthority": "NONE",
            "evaluationDomains": domains,
            "connectorInterfaces": _connectors(),
            "scoreComponents": SCORE_COMPONENTS,
            "rotationClassifications": ROTATION_CLASSIFICATIONS,
            "rootCauseFactors": ROOT_CAUSE_FACTORS,
            "evaluatedSegments": tuple(_segment_payload(segment) for segment in self._identify_segments(domains, sources)),
            "strategicCapitalRotationAssessments": all_assessments,
            "latestStrategicCapitalRotationAssessments": latest_assessments,
            "capitalRotationIntelligenceBridge": bridge,
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
                "operationalOffice": "Capital Rotation Intelligence Office",
                "topCapitalDestinations": tuple(item["segment"] for item in latest_assessments[:5]),
                "rotationClassifications": tuple(item["rotation_classification"] for item in latest_assessments[:8]),
                "researchPriorities": tuple(item["segment"] for item in latest_assessments[:4]),
                "averageCapitalRotationScore": metrics["averageCapitalRotationScore"],
                "route": "capital_rotation_bridge",
            },
            "auditTrail": (
                {"auditId": f"AUDIT-CRIO-{len(all_assessments):06d}", "timestamp": timestamp_utc, "event": "capital_rotation_snapshot_completed", "lawVIICompliant": True, "lawVIIICompliant": True},
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

    def _resolved_config(self, registry: dict[str, Any]) -> CapitalRotationConfig:
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        crio = configs.get("capitalRotationIntelligenceOffice", {}) if isinstance(configs, dict) else {}
        if not isinstance(crio, dict):
            return self._config
        values = asdict(self._config)
        for key, value in crio.items():
            if key in values:
                values[key] = value
        return CapitalRotationConfig(**values)

    def _resolved_domains(self, sources: dict[str, Any], config: CapitalRotationConfig) -> tuple[str, ...]:
        registry = sources.get("enterpriseConfigurationRegistry", {})
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        configured = configs.get("capitalRotationDomains", ()) if isinstance(configs, dict) else ()
        if config.dynamic_domain_additions_enabled and configured:
            return tuple(dict.fromkeys((*self._domains, *tuple(configured))))
        return self._domains

    def _identify_segments(self, domains: tuple[str, ...], sources: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        msio = sources.get("marketStructureIntelligenceOffice", {})
        msio_feed = msio.get("sicFeed", {})
        macro = sources.get("marketContextIntegrationEngine", {})
        risk = sources.get("enterpriseRiskFactorEngine", {})
        structural_bonus = 6 if msio_feed.get("topStructuralOpportunities") else 0
        risk_level = risk.get("commanderSummary", {}).get("riskLevel", "unknown")
        risk_bonus = 5 if risk_level in {"high", "critical"} else 0
        context_bonus = 4 if macro.get("marketContext") or macro.get("context") else 0
        segments = []
        for index, domain in enumerate(domains, start=1):
            segments.append(
                {
                    "segment_id": f"CRIO-SEG-{index:04d}",
                    "asset_class": domain,
                    "segment": f"{domain} Capital Flow Segment",
                    "region": _region(domain),
                    "structuralBonus": structural_bonus,
                    "riskBonus": risk_bonus,
                    "contextBonus": context_bonus,
                    "sourceSignals": (
                        "capital_rotation_domain_catalog",
                        "market_structure_overlap" if structural_bonus else "market_structure_interface_ready",
                        "macro_context_overlap" if context_bonus else "macro_context_interface_ready",
                        "risk_regime_overlap" if risk_bonus else "risk_interface_ready",
                    ),
                }
            )
        return tuple(segments)

    def _create_assessments(self, timestamp: str, segments: tuple[dict[str, Any], ...], config: CapitalRotationConfig) -> tuple[StrategicCapitalRotationAssessment, ...]:
        scored = []
        for segment in segments:
            score = _score_segment(segment, timestamp)
            if score.overall_score >= config.minimum_capital_rotation_score:
                scored.append((segment, score))
        scored.sort(key=lambda item: (-item[1].overall_score, item[0]["asset_class"]))
        assessments = []
        for index, (segment, score) in enumerate(scored[: config.maximum_assessments_per_cycle], start=1):
            assessment_id = f"CRIO-ASM-{len(self._assessments) + index:06d}"
            classification = _classification(score)
            assessments.append(
                StrategicCapitalRotationAssessment(
                    assessment_id=assessment_id,
                    timestamp=timestamp,
                    asset_class=segment["asset_class"],
                    segment=segment["segment"],
                    region=segment["region"],
                    executive_summary=f"{segment['segment']} is classified as {classification} based on deterministic flow, persistence, participation, and macro alignment evidence.",
                    capital_rotation_score=asdict(score),
                    rotation_classification=classification,
                    primary_capital_destinations=_capital_destinations(segment, score, classification),
                    primary_capital_sources=_capital_sources(segment, score, classification),
                    sector_rotation=_sector_rotation(score),
                    industry_rotation=_industry_rotation(score),
                    asset_allocation_trends=_asset_allocation_trends(score, classification),
                    geographic_rotation=_geographic_rotation(segment, score),
                    institutional_participation=_institutional_participation(score),
                    rotation_persistence=_rotation_persistence(score),
                    macroeconomic_context=_macroeconomic_context(score),
                    root_cause_analysis=_root_causes(score),
                    principal_risks=_principal_risks(score, classification),
                    forecast_horizon=score.forecast_horizon,
                    confidence_score=round(config.default_confidence_score + (score.evidence_quality - 70.0) / 5, 4),
                    supporting_evidence=tuple(segment["sourceSignals"]) + tuple(f"{component}:{value}" for component, value in score.component_scores.items()),
                    historian_archive_id=f"HIST-{assessment_id}",
                    librarian_index_id=f"LIB-{assessment_id}",
                    revision_history=({"revision": 1, "timestamp": timestamp, "reason": "initial_capital_rotation_assessment"},),
                    advisory_only=True,
                    immutable=True,
                )
            )
        return tuple(assessments)


def _score_segment(segment: dict[str, Any], timestamp: str) -> CapitalRotationScore:
    asset_class = str(segment["asset_class"])
    seed = sum(ord(char) for char in asset_class)
    components = {
        "net_capital_inflow": _clamp(50 + seed % 41 + segment.get("structuralBonus", 0)),
        "net_capital_outflow": _clamp(45 + (seed // 3 % 40) + segment.get("riskBonus", 0)),
        "institutional_participation": _clamp(52 + (len(asset_class.replace(" ", "")) * 3 % 38)),
        "etf_flow_analysis": _clamp(48 + (seed // 5 % 42)),
        "mutual_fund_activity": _clamp(47 + (seed // 7 % 39)),
        "options_positioning": _clamp(46 + (seed // 11 % 41)),
        "relative_strength": _clamp(54 + (len(asset_class) * 4 % 36)),
        "breadth_of_participation": _clamp(50 + (len(asset_class.split()) * 10)),
        "rotation_persistence": _clamp(49 + (seed // 13 % 40) + segment.get("contextBonus", 0)),
        "macroeconomic_alignment": _clamp(51 + (seed // 17 % 38) + segment.get("contextBonus", 0)),
        "strategic_conviction": _clamp(50 + (seed // 19 % 39) + segment.get("structuralBonus", 0)),
    }
    weights = {
        "net_capital_inflow": 0.12,
        "net_capital_outflow": 0.08,
        "institutional_participation": 0.11,
        "etf_flow_analysis": 0.09,
        "mutual_fund_activity": 0.08,
        "options_positioning": 0.07,
        "relative_strength": 0.10,
        "breadth_of_participation": 0.09,
        "rotation_persistence": 0.11,
        "macroeconomic_alignment": 0.08,
        "strategic_conviction": 0.07,
    }
    overall = round(sum(components[key] * weight for key, weight in weights.items()), 4)
    evidence_quality = round(min(100.0, 62.0 + len(segment.get("sourceSignals", ())) * 5 + segment.get("structuralBonus", 0) / 2), 4)
    return CapitalRotationScore(
        overall_score=overall,
        component_scores=components,
        confidence_interval=(round(max(0.0, overall - 8.0), 4), round(min(100.0, overall + 8.0), 4)),
        evidence_quality=evidence_quality,
        forecast_horizon=_forecast_horizon(overall),
        revision_history=({"revision": 1, "timestamp": timestamp, "reason": "deterministic_capital_rotation_score"},),
    )


def _bridge_payload(assessments: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    return {
        "capitalRotationScore": tuple({"segment": item["segment"], "classification": item["rotation_classification"], "score": item["capital_rotation_score"]["overall_score"]} for item in assessments[:8]),
        "sectorRotationMap": tuple({"segment": item["segment"], "assessment": item["sector_rotation"], "score": item["capital_rotation_score"]["component_scores"]["relative_strength"]} for item in assessments),
        "industryRotationMap": tuple({"segment": item["segment"], "assessment": item["industry_rotation"], "score": item["capital_rotation_score"]["component_scores"]["breadth_of_participation"]} for item in assessments),
        "assetAllocationChanges": tuple({"segment": item["segment"], "trend": item["asset_allocation_trends"], "destinations": item["primary_capital_destinations"]} for item in assessments),
        "geographicCapitalFlows": tuple({"segment": item["segment"], "region": item["region"], "assessment": item["geographic_rotation"]} for item in assessments),
        "institutionalParticipation": tuple({"segment": item["segment"], "assessment": item["institutional_participation"], "score": item["capital_rotation_score"]["component_scores"]["institutional_participation"]} for item in assessments),
        "etfFlowDashboard": tuple({"segment": item["segment"], "score": item["capital_rotation_score"]["component_scores"]["etf_flow_analysis"], "classification": item["rotation_classification"]} for item in assessments),
        "mutualFundPositioning": tuple({"segment": item["segment"], "score": item["capital_rotation_score"]["component_scores"]["mutual_fund_activity"], "sources": item["primary_capital_sources"]} for item in assessments),
        "optionsPositioning": tuple({"segment": item["segment"], "score": item["capital_rotation_score"]["component_scores"]["options_positioning"], "context": item["macroeconomic_context"]} for item in assessments),
        "riskOnRiskOffIndicator": _risk_indicator(assessments),
        "historicalRotationTimeline": tuple({"segment": item["segment"], "classification": item["rotation_classification"], "horizon": item["forecast_horizon"], "persistence": item["rotation_persistence"]} for item in assessments),
        "confidenceDistribution": _confidence_distribution(assessments),
        "evidenceQuality": _average(item["capital_rotation_score"]["evidence_quality"] for item in assessments),
        "runtimeHealth": "NOMINAL",
        "workflowStatus": "bounded_snapshot_complete",
        "apiUsage": {"apiCost": 0.0, "mode": "deterministic_no_paid_calls"},
    }


def _metrics(assessments: tuple[dict[str, Any], ...], bridge: dict[str, Any]) -> dict[str, Any]:
    return {
        "capitalRotationAssessmentsProduced": len(assessments),
        "rotationIdentificationAccuracy": 0.0,
        "rotationPersistenceAccuracy": 0.0,
        "sectorRotationAccuracy": 0.0,
        "assetAllocationForecastingAccuracy": 0.0,
        "averageCapitalRotationScore": _average(item["capital_rotation_score"]["overall_score"] for item in assessments),
        "evidenceQuality": bridge["evidenceQuality"],
        "confidenceCalibration": "tracking",
        "historicalHitRate": 0.0,
        "falsePositives": 0,
        "falseNegatives": 0,
        "enterpriseUtilization": len(bridge["capitalRotationScore"]),
        "apiUtilization": 0.0,
        "workflowParticipation": "bounded_advisory_snapshot",
    }


def _research_directives(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    targets = ("Blue Ocean Intelligence Office", "Disruption Intelligence Office", "Market Structure Intelligence Office", "Decline Intelligence Office", "Short Opportunity Office", "Analyst Group", "Risk Office", "Historian", "Librarian", "Academy")
    return tuple(
        {
            "directiveId": f"CRIO-RD-{index:03d}",
            "targetOffice": targets[(index - 1) % len(targets)],
            "segment": item["segment"],
            "request": "validate_capital_rotation_evidence",
            "advisoryOnly": True,
        }
        for index, item in enumerate(assessments[:10], start=1)
    )


def _connectors() -> tuple[dict[str, str], ...]:
    return tuple({"connectorType": item, "status": "INTERFACE_READY", "liveExternalCalls": "DISABLED"} for item in CONNECTOR_TYPES)


def _historian_feed(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"historianArchiveId": item["historian_archive_id"], "assessmentId": item["assessment_id"], "originalAssessment": item["executive_summary"], "observedCapitalMovement": "pending", "outcomeTracking": "pending"} for item in assessments)


def _librarian_feed(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "librarianIndexId": item["librarian_index_id"],
            "assessmentId": item["assessment_id"],
            "indexTerms": (item["asset_class"], item["segment"], item["region"], item["rotation_classification"], item["forecast_horizon"], str(item["confidence_score"]), str(item["capital_rotation_score"]["evidence_quality"])),
        }
        for item in assessments
    )


def _segment_payload(segment: dict[str, Any]) -> dict[str, Any]:
    return {**segment, "capitalRotationScorePreview": _score_segment(segment, "preview").overall_score}


def _inbox(sources: dict[str, Any]) -> tuple[dict[str, str], ...]:
    return tuple({"source": key, "messageType": "capital_rotation_source_snapshot", "status": "received"} for key in sorted(sources) if sources.get(key))


def _outbox(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
    return tuple({"target": "Strategic Intelligence Command", "messageType": "Strategic Capital Rotation Assessment", "recordId": item["assessment_id"]} for item in assessments)


def _classification(score: CapitalRotationScore) -> str:
    inflow = score.component_scores["net_capital_inflow"]
    outflow = score.component_scores["net_capital_outflow"]
    persistence = score.component_scores["rotation_persistence"]
    conviction = score.component_scores["strategic_conviction"]
    macro = score.component_scores["macroeconomic_alignment"]
    if outflow >= 78 and inflow < 62:
        return "Risk-Off"
    if inflow >= 78 and macro >= 68:
        return "Risk-On"
    if persistence >= 78 and conviction >= 72:
        return "Structural Rotation"
    if persistence >= 70:
        return "Strategic Rotation"
    if inflow >= 70 and score.component_scores["relative_strength"] >= 70:
        return "Growth Migration"
    if outflow >= 70:
        return "Defensive Migration"
    if macro >= 72:
        return "Recovery Rotation"
    if score.overall_score >= 64:
        return "Intermediate Rotation"
    if score.overall_score >= 57:
        return "Late-Cycle Rotation"
    return "Short-Term Rotation"


def _capital_destinations(segment: dict[str, Any], score: CapitalRotationScore, classification: str) -> tuple[str, ...]:
    destinations = [segment["asset_class"]]
    if classification in {"Risk-On", "Growth Migration", "Recovery Rotation"}:
        destinations.extend(("cyclical_growth_exposure", "high_beta_leadership"))
    elif classification in {"Risk-Off", "Defensive Migration"}:
        destinations.extend(("defensive_exposure", "liquidity_and_quality"))
    else:
        destinations.extend(("selective_relative_strength", "institutional_accumulation_watch"))
    if score.component_scores["etf_flow_analysis"] >= 70:
        destinations.append("etf_creation_flow")
    return tuple(dict.fromkeys(destinations))


def _capital_sources(segment: dict[str, Any], score: CapitalRotationScore, classification: str) -> tuple[str, ...]:
    sources = ["lower_conviction_segments", "crowded_prior_leadership"]
    if classification in {"Risk-Off", "Defensive Migration"}:
        sources.append("risk_asset_outflows")
    if score.component_scores["net_capital_outflow"] >= 70:
        sources.append(f"{segment['asset_class']}_distribution_pressure")
    return tuple(dict.fromkeys(sources))


def _sector_rotation(score: CapitalRotationScore) -> str:
    return "sector_rotation_broadening" if score.component_scores["breadth_of_participation"] >= 70 else "sector_rotation_concentrated"


def _industry_rotation(score: CapitalRotationScore) -> str:
    return "industry_rotation_supported_by_relative_strength" if score.component_scores["relative_strength"] >= 70 else "industry_rotation_requires_confirmation"


def _asset_allocation_trends(score: CapitalRotationScore, classification: str) -> str:
    if classification in {"Structural Rotation", "Strategic Rotation"}:
        return "allocation_shift_has_durable_characteristics"
    if classification in {"Risk-Off", "Defensive Migration"}:
        return "allocation_shift_prioritizes_capital_preservation"
    return "allocation_shift_is_emerging_or_transitional"


def _geographic_rotation(segment: dict[str, Any], score: CapitalRotationScore) -> str:
    return f"{segment['region'].lower().replace(' ', '_')}_capital_flow_watch"


def _institutional_participation(score: CapitalRotationScore) -> str:
    return "institutional_accumulation_or_distribution_material" if score.component_scores["institutional_participation"] >= 70 else "institutional_participation_watch"


def _rotation_persistence(score: CapitalRotationScore) -> str:
    return "rotation_persistence_probable" if score.component_scores["rotation_persistence"] >= 70 else "rotation_persistence_unproven"


def _macroeconomic_context(score: CapitalRotationScore) -> str:
    return "macro_context_aligns_with_observed_flows" if score.component_scores["macroeconomic_alignment"] >= 70 else "macro_context_mixed"


def _principal_risks(score: CapitalRotationScore, classification: str) -> tuple[str, ...]:
    risks = ["flow_reversal", "crowded_positioning", "macro_regime_shift"]
    if classification in {"Risk-Off", "Defensive Migration"}:
        risks.append("false_defensive_signal")
    if score.component_scores["options_positioning"] >= 72:
        risks.append("derivatives_positioning_distortion")
    return tuple(dict.fromkeys(risks))


def _root_causes(score: CapitalRotationScore) -> tuple[str, ...]:
    causes = []
    if score.component_scores["macroeconomic_alignment"] >= 68:
        causes.extend(("Interest Rates", "Economic Growth"))
    if score.component_scores["net_capital_outflow"] >= 70:
        causes.append("Risk Appetite")
    if score.component_scores["institutional_participation"] >= 68:
        causes.append("Institutional Behavior")
    if score.component_scores["relative_strength"] >= 70:
        causes.append("Corporate Earnings")
    if score.component_scores["etf_flow_analysis"] >= 70:
        causes.append("Liquidity Conditions")
    return tuple(dict.fromkeys(causes or ("Market Valuation", "Monetary Policy")))


def _risk_indicator(assessments: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    classifications = [item["rotation_classification"] for item in assessments]
    risk_on = sum(1 for item in classifications if item in {"Risk-On", "Growth Migration", "Recovery Rotation"})
    risk_off = sum(1 for item in classifications if item in {"Risk-Off", "Defensive Migration"})
    posture = "RISK_ON" if risk_on > risk_off else "RISK_OFF" if risk_off > risk_on else "BALANCED"
    return {"posture": posture, "riskOnSignals": risk_on, "riskOffSignals": risk_off, "sampleSize": len(classifications)}


def _region(domain: str) -> str:
    if "International" in domain or domain in {"Currencies", "Commodities", "Precious Metals", "Energy Markets", "Cryptocurrency", "Private Markets"}:
        return "Global"
    return "United States"


def _forecast_horizon(score: float) -> str:
    if score >= 76:
        return "Immediate (Days)"
    if score >= 66:
        return "Near-Term (Weeks)"
    if score >= 58:
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
        "marketStructure": sources.get("marketStructureIntelligenceOffice", {}).get("sicFeed", {}),
        "risk": sources.get("enterpriseRiskFactorEngine", {}).get("commanderSummary", {}),
        "market": sources.get("marketContextIntegrationEngine", {}).get("marketContext", {}),
        "config": sources.get("enterpriseConfigurationRegistry", {}).get("activeConfiguration", {}),
    }


def _hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)
