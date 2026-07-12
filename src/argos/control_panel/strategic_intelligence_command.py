"""Strategic Intelligence Command for ARGOS EO-BS."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


TIME_HORIZONS: tuple[str, ...] = (
    "Immediate (Days)",
    "Near-Term (Weeks)",
    "Operational (Months)",
    "Strategic (1-3 Years)",
    "Grand Strategic (3-10 Years)",
    "Generational (10+ Years)",
)

REPORT_TYPES: tuple[str, ...] = (
    "Strategic Opportunity Assessment",
    "Strategic Research Priority List",
    "Emerging Battlefield Report",
    "Structural Shift Report",
    "Strategic Watch List",
    "Threat Assessment",
)

SUBORDINATE_OFFICES: tuple[str, ...] = (
    "Blue Ocean Intelligence Office",
    "Disruption Intelligence Office",
    "Decline Intelligence Office",
    "Short Opportunity Office",
    "Market Structure Intelligence Office",
    "Capital Rotation Intelligence Office",
    "Strategic Synthesis Office",
)


@dataclass(frozen=True)
class StrategicIntelligenceConfig:
    strategic_intelligence_command_enabled: bool = True
    default_confidence_score: float = 72.0
    minimum_evidence_quality_score: float = 65.0
    maximum_reports_per_cycle: int = 6
    advisory_only: bool = True
    workflow_token_required: bool = True
    ai_for_routine_display_enabled: bool = False


@dataclass(frozen=True)
class StrategicIntelligenceReport:
    report_id: str
    report_type: str
    timestamp: str
    authoring_office: str
    title: str
    summary: str
    strategic_themes: tuple[str, ...]
    industries: tuple[str, ...]
    technologies: tuple[str, ...]
    geographic_regions: tuple[str, ...]
    companies: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    confidence_score: float
    evidence_quality_score: float
    time_horizon: str
    revision_history: tuple[dict[str, Any], ...]
    decision_traceability: tuple[str, ...]
    historian_archive_identifier: str
    librarian_index_terms: tuple[str, ...]
    advisory_only: bool
    immutable: bool


class StrategicIntelligenceCommand:
    """Peer enterprise command for strategic reconnaissance and attention allocation."""

    def __init__(self, config: StrategicIntelligenceConfig | None = None) -> None:
        self._config = config or StrategicIntelligenceConfig()
        self._reports: list[StrategicIntelligenceReport] = []
        self._reports_by_fingerprint: dict[str, tuple[StrategicIntelligenceReport, ...]] = {}

    def snapshot(self, *, timestamp_utc: str, sources: dict[str, Any]) -> dict[str, Any]:
        config = self._resolved_config(sources.get("enterpriseConfigurationRegistry") or {})
        fingerprint = _hash(_stable_sources(sources))
        reports = self._reports_by_fingerprint.get(fingerprint)
        if reports is None:
            reports = self._generate_reports(timestamp_utc=timestamp_utc, sources=sources, config=config)
            self._reports.extend(reports)
            self._reports_by_fingerprint[fingerprint] = reports

        report_payloads = tuple(asdict(report) for report in self._reports)
        latest_payloads = tuple(asdict(report) for report in reports)
        bridge = _bridge_payload(latest_payloads, config)
        metrics = _metrics(report_payloads, bridge)
        return {
            "commandName": "Strategic Intelligence Command",
            "engineeringOrder": "EO-BS",
            "constitutionalMode": "ADVISORY_STRATEGIC_RECONNAISSANCE_ONLY",
            "enterprisePeerOrganization": True,
            "authorityBoundary": {
                "executesTrades": False,
                "approvesTrades": False,
                "rejectsTrades": False,
                "overridesAnalyst": False,
                "overridesRisk": False,
                "overridesTrader": False,
                "modifiesPortfolios": False,
                "generatesBrokerOrders": False,
                "advisoryOnly": True,
            },
            "timeHorizonFramework": TIME_HORIZONS,
            "supportedReportTypes": REPORT_TYPES,
            "subordinateOfficeInterfaces": _subordinate_offices(
                timestamp_utc,
                sources.get("blueOceanIntelligenceOffice"),
                sources.get("disruptionIntelligenceOffice"),
                sources.get("declineIntelligenceOffice"),
                sources.get("shortOpportunityOffice"),
                sources.get("marketStructureIntelligenceOffice"),
                sources.get("capitalRotationIntelligenceOffice"),
                sources.get("strategicSynthesisOffice"),
            ),
            "strategicReports": report_payloads,
            "latestStrategicReports": latest_payloads,
            "strategicIntelligenceBridge": bridge,
            "metrics": metrics,
            "officeLifecycle": {
                "state": "READY",
                "lifecycleManaged": True,
                "activationMode": "bounded_snapshot_workflow",
                "workflowTokenRequired": config.workflow_token_required,
                "persistentActiveOffice": False,
            },
            "health": {
                "status": "NOMINAL",
                "reportsAvailable": len(report_payloads),
                "subordinateOfficeReadiness": "PLACEHOLDER_INTERFACES_READY",
                "advisoryBoundaryIntact": True,
            },
            "inbox": _inbox(sources),
            "outbox": _outbox(latest_payloads),
            "enterpriseMessaging": _enterprise_messaging(timestamp_utc, latest_payloads),
            "decisionQueue": _decision_queue(latest_payloads),
            "activityLog": _activity_log(timestamp_utc, latest_payloads),
            "auditTrail": _audit_trail(timestamp_utc, len(report_payloads), sources),
            "historianFeed": _historian_feed(report_payloads),
            "librarianFeed": _librarian_feed(report_payloads),
            "enterpriseWorkflowIntegration": {
                "participatesInWorkflowTokenArchitecture": True,
                "workflowParticipation": metrics["workflowParticipation"],
                "lawVIIBypass": False,
                "boundedCompletion": True,
                "keepsOfficeActive": False,
            },
            "executiveAssignmentFeed": _executive_assignment_feed(latest_payloads),
            "commanderStrategicDashboardFeed": {
                "strategicThemes": bridge["strategicThemes"],
                "researchPriorities": bridge["researchPriorities"],
                "watchList": bridge["strategicWatchList"],
                "blueOceanOpportunities": tuple((sources.get("blueOceanIntelligenceOffice", {}).get("sicFeed", {}) or {}).get("topOpportunities", ())),
                "disruptionOpportunities": tuple((sources.get("disruptionIntelligenceOffice", {}).get("sicFeed", {}) or {}).get("topDisruptions", ())),
                "declineWarnings": tuple((sources.get("declineIntelligenceOffice", {}).get("sicFeed", {}) or {}).get("topDeclines", ())),
                "shortOpportunities": tuple((sources.get("shortOpportunityOffice", {}).get("sicFeed", {}) or {}).get("topShortOpportunities", ())),
                "marketStructureOpportunities": tuple((sources.get("marketStructureIntelligenceOffice", {}).get("sicFeed", {}) or {}).get("topStructuralOpportunities", ())),
                "capitalRotationDestinations": tuple((sources.get("capitalRotationIntelligenceOffice", {}).get("sicFeed", {}) or {}).get("topCapitalDestinations", ())),
                "strategicSynthesis": (sources.get("strategicSynthesisOffice", {}).get("sicFeed", {}) or {}),
                "metrics": metrics,
                "commanderDirectives": bridge["commanderDirectives"],
                "route": "strategic_intelligence_bridge",
            },
            "commanderBriefingFeed": {
                "summary": "Strategic Intelligence Command is allocating long-horizon attention without trading authority.",
                "latestReports": tuple(item["report_id"] for item in latest_payloads),
                "topThemes": bridge["strategicThemes"][:3],
                "blueOceanOpportunities": tuple((sources.get("blueOceanIntelligenceOffice", {}).get("sicFeed", {}) or {}).get("topOpportunities", ())),
                "disruptionOpportunities": tuple((sources.get("disruptionIntelligenceOffice", {}).get("sicFeed", {}) or {}).get("topDisruptions", ())),
                "declineWarnings": tuple((sources.get("declineIntelligenceOffice", {}).get("sicFeed", {}) or {}).get("topDeclines", ())),
                "shortOpportunities": tuple((sources.get("shortOpportunityOffice", {}).get("sicFeed", {}) or {}).get("topShortOpportunities", ())),
                "marketStructureOpportunities": tuple((sources.get("marketStructureIntelligenceOffice", {}).get("sicFeed", {}) or {}).get("topStructuralOpportunities", ())),
                "capitalRotationDestinations": tuple((sources.get("capitalRotationIntelligenceOffice", {}).get("sicFeed", {}) or {}).get("topCapitalDestinations", ())),
                "strategicSynthesis": (sources.get("strategicSynthesisOffice", {}).get("sicFeed", {}) or {}),
                "threats": bridge["decliningIndustries"][:3],
            },
            "configuration": asdict(config),
            "lawVII": {
                "uncontrolledLoops": False,
                "persistentActiveOffice": False,
                "workflowTokenArchitectureRespected": True,
                "terminatesImmediately": True,
            },
            "lawVIII": {
                "routineAiInvocations": 0,
                "deterministicStrategicReconnaissance": True,
                "aiForRoutineDisplay": False,
            },
            "internalDiagnostics": {
                "placesTrades": False,
                "createsOrders": False,
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "mutatesPortfolios": False,
                "apiCreditsConsumed": 0.0,
                "fingerprintCount": len(self._reports_by_fingerprint),
                "timestampUtc": timestamp_utc,
            },
        }

    def _generate_reports(
        self,
        *,
        timestamp_utc: str,
        sources: dict[str, Any],
        config: StrategicIntelligenceConfig,
    ) -> tuple[StrategicIntelligenceReport, ...]:
        evidence = _evidence(sources)
        themes = _themes(sources, evidence)
        research = _research_priorities(sources, evidence)
        emerging = _emerging_industries(sources, evidence)
        declining = _declining_industries(sources, evidence)
        watch = _watch_targets(themes, emerging)
        confidence = _confidence(evidence, config)
        quality = _evidence_quality(evidence, config)
        templates = (
            (
                "Strategic Opportunity Assessment",
                "Strategic attention should concentrate on structurally durable themes with evidence-quality gates.",
                themes,
                emerging[:3],
                ("AI infrastructure", "grid modernization", "autonomous defense systems"),
                ("United States", "North America", "Developed Markets"),
                (),
                "Strategic (1-3 Years)",
            ),
            (
                "Strategic Research Priority List",
                "Future Seeker and Analyst work should prioritize evidence gaps before capital deployment expands.",
                research,
                emerging[:2],
                ("broker realism", "market data fidelity", "reproducible replay"),
                ("United States",),
                (),
                "Operational (Months)",
            ),
            (
                "Emerging Battlefield Report",
                "Several industries are becoming long-horizon battlefields and deserve organized monitoring.",
                themes[:3],
                emerging,
                ("AI accelerators", "power storage", "industrial automation"),
                ("United States", "Global Developed Markets"),
                (),
                "Grand Strategic (3-10 Years)",
            ),
            (
                "Structural Shift Report",
                "ARGOS should treat reality fidelity, capital preservation, and benchmark evidence as structural operating conditions.",
                ("capital preservation", "evidence maturity", "reality calibration"),
                ("brokerage infrastructure", "market data services", "risk analytics"),
                ("execution simulation", "audit-grade ledgers", "stress analytics"),
                ("United States",),
                (),
                "Near-Term (Weeks)",
            ),
            (
                "Strategic Watch List",
                "Long-duration targets are tracked for attention allocation, not immediate trade execution.",
                watch,
                emerging[:3],
                ("AI infrastructure", "energy grid", "defense autonomy"),
                ("United States", "Global"),
                ("SPY",),
                "Generational (10+ Years)",
            ),
            (
                "Threat Assessment",
                "Structurally weak or operationally degraded areas require explicit Commander visibility.",
                ("simulation drift", "low-fidelity data", "capital concentration"),
                declining,
                ("legacy workflows", "unvalidated automation", "unreconciled truth records"),
                ("United States", "Global"),
                (),
                "Immediate (Days)",
            ),
        )
        reports: list[StrategicIntelligenceReport] = []
        for offset, template in enumerate(templates[: config.maximum_reports_per_cycle], start=1):
            report_type, summary, report_themes, industries, tech, regions, companies, horizon = template
            report_id = f"SIC-{len(self._reports) + offset:06d}"
            reports.append(
                StrategicIntelligenceReport(
                    report_id=report_id,
                    report_type=report_type,
                    timestamp=timestamp_utc,
                    authoring_office="Strategic Intelligence Command",
                    title=report_type,
                    summary=summary,
                    strategic_themes=tuple(report_themes),
                    industries=tuple(industries),
                    technologies=tuple(tech),
                    geographic_regions=tuple(regions),
                    companies=tuple(companies),
                    supporting_evidence=tuple(_supporting_evidence(evidence, report_type)),
                    confidence_score=round(max(0.0, min(100.0, confidence - (offset - 1) * 1.5)), 4),
                    evidence_quality_score=round(max(config.minimum_evidence_quality_score, quality - (offset - 1)), 4),
                    time_horizon=horizon,
                    revision_history=(
                        {"revision": 1, "timestamp": timestamp_utc, "reason": "initial_eo_bs_strategic_product"},
                    ),
                    decision_traceability=tuple(_traceability(sources, report_type)),
                    historian_archive_identifier=f"HIST-SIC-{report_id}",
                    librarian_index_terms=tuple(dict.fromkeys((*report_themes, *industries, *tech, horizon, report_type))),
                    advisory_only=True,
                    immutable=True,
                )
            )
        return tuple(reports)

    def _resolved_config(self, registry: dict[str, Any]) -> StrategicIntelligenceConfig:
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        sic = configs.get("strategicIntelligenceCommand", {}) if isinstance(configs, dict) else {}
        if not isinstance(sic, dict):
            return self._config
        values = asdict(self._config)
        for key, value in sic.items():
            if key in values:
                values[key] = value
        return StrategicIntelligenceConfig(**values)


def _evidence(sources: dict[str, Any]) -> dict[str, Any]:
    grand = sources.get("enterpriseGrandStrategyEngine", {})
    active_strategy = grand.get("activeGrandStrategyRecord") or {}
    reality = sources.get("enterpriseRealityCalibrationEngine", {})
    risk = sources.get("enterpriseRiskFactorEngine", {})
    health = sources.get("enterpriseHealthMonitor", {})
    learning = sources.get("enterpriseLearningEngine", {})
    historian = sources.get("historianRecommendationEngine", {})
    scheduler = sources.get("enterpriseExperimentScheduler", {})
    credit = sources.get("creditGovernor", {})
    dashboard = sources.get("commanderStrategicDashboard", {})
    blue = sources.get("blueOceanIntelligenceOffice", {})
    blue_feed = blue.get("sicFeed", {})
    disruption = sources.get("disruptionIntelligenceOffice", {})
    disruption_feed = disruption.get("sicFeed", {})
    decline = sources.get("declineIntelligenceOffice", {})
    decline_feed = decline.get("sicFeed", {})
    short = sources.get("shortOpportunityOffice", {})
    short_feed = short.get("sicFeed", {})
    market_structure = sources.get("marketStructureIntelligenceOffice", {})
    market_structure_feed = market_structure.get("sicFeed", {})
    capital_rotation = sources.get("capitalRotationIntelligenceOffice", {})
    capital_rotation_feed = capital_rotation.get("sicFeed", {})
    strategic_synthesis = sources.get("strategicSynthesisOffice", {})
    strategic_synthesis_feed = strategic_synthesis.get("sicFeed", {})
    return {
        "strategicPosture": active_strategy.get("strategic_posture", "preservation"),
        "researchPriorities": tuple(item.get("name", item.get("priority", "")) for item in active_strategy.get("research_priorities", ())),
        "capabilityPriorities": tuple(item.get("name", item.get("capability", "")) for item in active_strategy.get("capability_priorities", ())),
        "realityFidelity": _number(reality.get("commanderSummary", {}).get("overallRealityFidelityScore"), 0.0),
        "riskScore": _number(risk.get("commanderSummary", {}).get("compositeRiskScore"), 0.0),
        "riskLevel": risk.get("commanderSummary", {}).get("riskLevel", "unknown"),
        "healthStatus": health.get("commanderHealthDashboard", {}).get("overallStatus") or health.get("runtimeHealth", {}).get("status", "unknown"),
        "learningRecommendations": len(learning.get("recommendations", ())),
        "historianRecommendations": len(historian.get("recommendationDatabase", ())),
        "queuedExperiments": len(scheduler.get("experimentQueue", ())),
        "activeExperiments": scheduler.get("researchDashboard", {}).get("activeExperiments", 0),
        "creditsToday": _number(credit.get("spendReport", {}).get("todaySpendUsd"), 0.0),
        "dashboardStatus": dashboard.get("strategic_recommendation", {}).get("recommendation", "unknown"),
        "blueOceanEmergingIndustries": tuple(blue_feed.get("emergingIndustries", ())),
        "blueOceanOpportunities": tuple(blue_feed.get("topOpportunities", ())),
        "blueOceanAverageScore": _number(blue_feed.get("averageBlueOceanScore"), 0.0),
        "disruptionDomains": tuple(disruption_feed.get("transformationDomains", ())),
        "disruptionOpportunities": tuple(disruption_feed.get("topDisruptions", ())),
        "disruptionAverageScore": _number(disruption_feed.get("averageDisruptionScore"), 0.0),
        "decliningIndustriesFromOffice": tuple(decline_feed.get("decliningIndustries", ())),
        "declineWarnings": tuple(decline_feed.get("topDeclines", ())),
        "declineAverageScore": _number(decline_feed.get("averageDeclineScore"), 0.0),
        "shortOpportunities": tuple(short_feed.get("topShortOpportunities", ())),
        "shortAverageScore": _number(short_feed.get("averageShortOpportunityScore"), 0.0),
        "marketStructureOpportunities": tuple(market_structure_feed.get("topStructuralOpportunities", ())),
        "marketStructureAverageScore": _number(market_structure_feed.get("averageMarketStructureScore"), 0.0),
        "capitalRotationDestinations": tuple(capital_rotation_feed.get("topCapitalDestinations", ())),
        "capitalRotationAverageScore": _number(capital_rotation_feed.get("averageCapitalRotationScore"), 0.0),
        "strategicSynthesisThemes": tuple(strategic_synthesis_feed.get("primaryThemes", ())),
        "strategicSynthesisConsensusScore": _number(strategic_synthesis_feed.get("consensusScore"), 0.0),
    }


def _themes(sources: dict[str, Any], evidence: dict[str, Any]) -> tuple[str, ...]:
    themes = [item for item in evidence["researchPriorities"] if item]
    themes.extend(item for item in evidence["capabilityPriorities"] if item)
    themes.extend(("reality fidelity", "benchmark evidence", "complete trade truth"))
    return tuple(dict.fromkeys(str(item).replace("_", " ") for item in themes))[:8]


def _research_priorities(sources: dict[str, Any], evidence: dict[str, Any]) -> tuple[str, ...]:
    priorities = list(_themes(sources, evidence)[:4])
    if evidence["riskScore"] >= 60:
        priorities.append("risk reduction evidence")
    if evidence["realityFidelity"] < 80:
        priorities.append("reality calibration repair")
    priorities.append("strategic opportunity mapping")
    return tuple(dict.fromkeys(priorities))


def _emerging_industries(sources: dict[str, Any], evidence: dict[str, Any]) -> tuple[str, ...]:
    return tuple(dict.fromkeys((
        *evidence.get("blueOceanEmergingIndustries", ()),
        *evidence.get("disruptionDomains", ()),
        "AI infrastructure",
        "energy grid modernization",
        "defense autonomy",
        "industrial automation",
        "market data infrastructure",
        "audit-grade financial software",
    )))


def _declining_industries(sources: dict[str, Any], evidence: dict[str, Any]) -> tuple[str, ...]:
    items = ["unvalidated paper-trading claims", "low-fidelity market data workflows", "manual reconciliation bottlenecks"]
    items.extend(evidence.get("decliningIndustriesFromOffice", ()))
    if evidence["realityFidelity"] < 80:
        items.append("simulation-only learning without calibration")
    if evidence["riskScore"] >= 60:
        items.append("high-concentration capital deployment")
    return tuple(dict.fromkeys(items))


def _watch_targets(themes: tuple[str, ...], emerging: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*themes[:4], *emerging[:4], "market structure regime shifts", "institutional capital rotation")))


def _confidence(evidence: dict[str, Any], config: StrategicIntelligenceConfig) -> float:
    score = config.default_confidence_score
    if evidence["realityFidelity"] >= 80:
        score += 8
    elif evidence["realityFidelity"] < 60:
        score -= 12
    if evidence["riskScore"] >= 80:
        score -= 8
    if evidence["historianRecommendations"]:
        score += 4
    if evidence["queuedExperiments"] or evidence["activeExperiments"]:
        score += 3
    return round(max(0.0, min(100.0, score)), 4)


def _evidence_quality(evidence: dict[str, Any], config: StrategicIntelligenceConfig) -> float:
    score = config.minimum_evidence_quality_score
    if evidence["realityFidelity"]:
        score += min(20.0, evidence["realityFidelity"] / 5)
    if evidence["researchPriorities"]:
        score += 5
    if evidence["capabilityPriorities"]:
        score += 5
    return round(max(0.0, min(100.0, score)), 4)


def _supporting_evidence(evidence: dict[str, Any], report_type: str) -> tuple[str, ...]:
    return (
        f"Enterprise Grand Strategy posture: {evidence['strategicPosture']}",
        f"Reality fidelity score: {evidence['realityFidelity']}",
        f"Composite risk score: {evidence['riskScore']} ({evidence['riskLevel']})",
        f"Enterprise health: {evidence['healthStatus']}",
        f"Research queue: {evidence['queuedExperiments']} queued / {evidence['activeExperiments']} active",
        f"Report type generated deterministically: {report_type}",
    )


def _traceability(sources: dict[str, Any], report_type: str) -> tuple[str, ...]:
    refs = ["Enterprise Grand Strategy Engine", "Enterprise Risk Factor Engine", "Enterprise Reality Calibration Engine"]
    if sources.get("historianRecommendationEngine"):
        refs.append("Historian Recommendation Engine")
    if sources.get("enterpriseLearningEngine"):
        refs.append("Enterprise Learning Engine")
    refs.append(f"EO-BS:{report_type}")
    return tuple(refs)


def _subordinate_offices(
    timestamp: str,
    blue_ocean: dict[str, Any] | None = None,
    disruption: dict[str, Any] | None = None,
    decline: dict[str, Any] | None = None,
    short: dict[str, Any] | None = None,
    market_structure: dict[str, Any] | None = None,
    capital_rotation: dict[str, Any] | None = None,
    strategic_synthesis: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    statuses = []
    blue_ready = bool(blue_ocean)
    disruption_ready = bool(disruption)
    decline_ready = bool(decline)
    short_ready = bool(short)
    market_structure_ready = bool(market_structure)
    capital_rotation_ready = bool(capital_rotation)
    strategic_synthesis_ready = bool(strategic_synthesis)
    for office in SUBORDINATE_OFFICES:
        operational = (
            (office == "Blue Ocean Intelligence Office" and blue_ready)
            or (office == "Disruption Intelligence Office" and disruption_ready)
            or (office == "Decline Intelligence Office" and decline_ready)
            or (office == "Short Opportunity Office" and short_ready)
            or (office == "Market Structure Intelligence Office" and market_structure_ready)
            or (office == "Capital Rotation Intelligence Office" and capital_rotation_ready)
            or (office == "Strategic Synthesis Office" and strategic_synthesis_ready)
        )
        route = (
            "blue_ocean_bridge" if office == "Blue Ocean Intelligence Office" and operational
            else "disruption_bridge" if office == "Disruption Intelligence Office" and operational
            else "decline_bridge" if office == "Decline Intelligence Office" and operational
            else "short_opportunity_bridge" if office == "Short Opportunity Office" and operational
            else "market_structure_bridge" if office == "Market Structure Intelligence Office" and operational
            else "capital_rotation_bridge" if office == "Capital Rotation Intelligence Office" and operational
            else "strategic_synthesis_bridge" if office == "Strategic Synthesis Office" and operational
            else "strategic_intelligence_bridge"
        )
        statuses.append(
            {
                "officeName": office,
                "status": "OPERATIONAL" if operational else "PLACEHOLDER_READY",
                "implementationState": (
                    "implemented_eo_bt" if office == "Blue Ocean Intelligence Office" and operational
                    else "implemented_eo_bu" if office == "Disruption Intelligence Office" and operational
                    else "implemented_eo_bv" if office == "Decline Intelligence Office" and operational
                    else "implemented_eo_bw" if office == "Short Opportunity Office" and operational
                    else "implemented_eo_bx" if office == "Market Structure Intelligence Office" and operational
                    else "implemented_eo_by" if office == "Capital Rotation Intelligence Office" and operational
                    else "implemented_eo_bz" if office == "Strategic Synthesis Office" and operational
                    else "future_engineering_order"
                ),
                "receivesDirectives": True,
                "mayTrade": False,
                "route": route,
                "lastHeartbeat": timestamp,
            }
        )
    return tuple(statuses)


def _bridge_payload(reports: tuple[dict[str, Any], ...], config: StrategicIntelligenceConfig) -> dict[str, Any]:
    themes = _top_terms(reports, "strategic_themes")
    emerging = _top_terms(reports, "industries", exclude=("unvalidated paper-trading claims", "low-fidelity market data workflows", "manual reconciliation bottlenecks"))
    declining = tuple(term for report in reports if report.get("report_type") == "Threat Assessment" for term in report.get("industries", ()))
    priorities = tuple(term for report in reports if report.get("report_type") == "Strategic Research Priority List" for term in report.get("strategic_themes", ()))
    watch = tuple(term for report in reports if report.get("report_type") == "Strategic Watch List" for term in report.get("strategic_themes", ()))
    return {
        "summary": {
            "status": "NOMINAL",
            "reportsGenerated": len(reports),
            "averageConfidence": _average(report.get("confidence_score") for report in reports),
            "averageEvidenceQuality": _average(report.get("evidence_quality_score") for report in reports),
            "advisoryOnly": config.advisory_only,
        },
        "strategicThemes": themes,
        "emergingIndustries": emerging,
        "decliningIndustries": declining,
        "researchPriorities": priorities,
        "globalHeatMap": _heat_map(themes, emerging),
        "timeHorizonDistribution": _distribution(report.get("time_horizon") for report in reports),
        "strategicWatchList": watch,
        "confidenceDistribution": _confidence_distribution(reports),
        "subordinateOfficeStatus": _subordinate_offices(reports[-1]["timestamp"] if reports else ""),
        "historicalPerformance": {
            "forecastingAccuracy": 0.0,
            "sampleSize": 0,
            "status": "TRACKING_INITIAL_BASELINE",
            "falsePositiveRate": 0.0,
            "falseNegativeRate": 0.0,
        },
        "commanderDirectives": (
            "Allocate attention to long-horizon structural themes without generating trades.",
            "Route tactical trade discovery through Seeker and Analyst only.",
            "Archive every strategic product through Historian and Librarian feeds.",
        ),
    }


def _metrics(reports: tuple[dict[str, Any], ...], bridge: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategicReportsGenerated": len(reports),
        "averageConfidence": bridge["summary"]["averageConfidence"],
        "averageEvidenceQuality": bridge["summary"]["averageEvidenceQuality"],
        "strategicThemePersistence": round(min(1.0, len(bridge["strategicThemes"]) / 8), 4),
        "falsePositiveRate": 0.0,
        "falseNegativeRate": 0.0,
        "leadTimeBeforeMarketRecognition": "tracking",
        "commanderUtilization": len(bridge["commanderDirectives"]),
        "researchPrioritizationEffectiveness": round(min(1.0, len(bridge["researchPriorities"]) / 5), 4),
        "historicalForecastingAccuracy": 0.0,
        "enterpriseAttentionAllocation": bridge["globalHeatMap"],
        "officeHealth": "NOMINAL",
        "workflowParticipation": "bounded_advisory_snapshot",
        "apiCost": 0.0,
        "runtimeUtilization": "bounded_low",
    }


def _inbox(sources: dict[str, Any]) -> tuple[dict[str, str], ...]:
    return tuple(
        {"source": name, "messageType": "authoritative_snapshot", "status": "received"}
        for name in sorted(sources)
        if sources.get(name)
    )


def _outbox(reports: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
    return tuple({"target": "Commander", "messageType": report["report_type"], "recordId": report["report_id"]} for report in reports)


def _enterprise_messaging(timestamp: str, reports: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    return {"lastPublishedAt": timestamp, "publishedMessages": len(reports), "busCompatible": True, "requiresWorkflowToken": True}


def _decision_queue(reports: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "decisionId": f"SIC-DQ-{index:03d}",
            "decisionType": "research_attention_review",
            "sourceReport": report["report_id"],
            "status": "COMMANDER_REVIEW_OPTIONAL",
        }
        for index, report in enumerate(reports[:3], start=1)
    )


def _activity_log(timestamp: str, reports: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
    return tuple({"timestamp": timestamp, "activity": f"Generated {report['report_type']}", "recordId": report["report_id"]} for report in reports)


def _audit_trail(timestamp: str, report_count: int, sources: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return (
        {
            "auditId": f"AUDIT-SIC-{report_count:06d}",
            "timestamp": timestamp,
            "event": "strategic_intelligence_snapshot_completed",
            "sourceCount": len(sources),
            "advisoryOnly": True,
            "lawVIICompliant": True,
            "lawVIIICompliant": True,
        },
    )


def _historian_feed(reports: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "archiveIdentifier": report["historian_archive_identifier"],
            "reportId": report["report_id"],
            "reportType": report["report_type"],
            "supportingEvidence": report["supporting_evidence"],
            "revisionHistory": report["revision_history"],
            "forecastAccuracy": "pending_outcomes",
            "lessonsLearned": (),
        }
        for report in reports
    )


def _librarian_feed(reports: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "documentId": report["report_id"],
            "indexTerms": report["librarian_index_terms"],
            "timeHorizon": report["time_horizon"],
            "confidenceLevel": report["confidence_score"],
            "semanticCollections": ("strategic_themes", "industries", "technologies", "geographic_regions"),
        }
        for report in reports
    )


def _executive_assignment_feed(reports: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "assignmentId": f"EXEC-SIC-{index:03d}",
            "sourceReport": report["report_id"],
            "recommendedOwner": "Executive",
            "assignment": "review_research_priority",
            "mayCreateTrades": False,
        }
        for index, report in enumerate(reports[:3], start=1)
    )


def _heat_map(themes: tuple[str, ...], emerging: tuple[str, ...]) -> tuple[dict[str, Any], ...]:
    items = tuple(dict.fromkeys((*themes[:4], *emerging[:4])))
    denominator = max(1, len(items))
    return tuple({"domain": item, "attentionPercent": round(100 / denominator, 2), "state": "watch"} for item in items)


def _top_terms(reports: tuple[dict[str, Any], ...], key: str, *, exclude: tuple[str, ...] = ()) -> tuple[str, ...]:
    terms: list[str] = []
    excluded = set(exclude)
    for report in reports:
        for term in report.get(key, ()):
            if term and term not in excluded:
                terms.append(str(term))
    return tuple(dict.fromkeys(terms))[:8]


def _distribution(values: Any) -> dict[str, int]:
    counts = {horizon: 0 for horizon in TIME_HORIZONS}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def _confidence_distribution(reports: tuple[dict[str, Any], ...]) -> dict[str, int]:
    buckets = {"high": 0, "medium": 0, "low": 0}
    for report in reports:
        score = _number(report.get("confidence_score"), 0.0)
        if score >= 80:
            buckets["high"] += 1
        elif score >= 60:
            buckets["medium"] += 1
        else:
            buckets["low"] += 1
    return buckets


def _average(values: Any) -> float:
    numbers = [_number(value, 0.0) for value in values]
    return round(sum(numbers) / max(1, len(numbers)), 4)


def _stable_sources(sources: dict[str, Any]) -> dict[str, Any]:
    return {
        "grandStrategy": sources.get("enterpriseGrandStrategyEngine", {}).get("activeGrandStrategyRecord", {}),
        "risk": sources.get("enterpriseRiskFactorEngine", {}).get("commanderSummary", {}),
        "reality": sources.get("enterpriseRealityCalibrationEngine", {}).get("commanderSummary", {}),
        "learningCount": len(sources.get("enterpriseLearningEngine", {}).get("recommendations", ())),
        "historianCount": len(sources.get("historianRecommendationEngine", {}).get("recommendationDatabase", ())),
        "experimentQueue": len(sources.get("enterpriseExperimentScheduler", {}).get("experimentQueue", ())),
    }


def _hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
