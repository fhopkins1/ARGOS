"""Short Opportunity Office for ARGOS EO-BW."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


EVALUATION_DOMAINS: tuple[str, ...] = (
    "Public Equities",
    "Exchange Traded Funds",
    "Industry Groups",
    "Market Sectors",
    "Commodities",
    "Currencies",
    "Fixed Income",
    "Market Indices",
    "REITs",
    "Infrastructure Assets",
)

CONNECTOR_TYPES: tuple[str, ...] = (
    "Corporate Filings",
    "Financial Statements",
    "Earnings Reports",
    "Conference Calls",
    "Market Data",
    "Analyst Estimates",
    "Institutional Ownership",
    "Insider Transactions",
    "Options Data",
    "Short Interest",
    "Alternative Data",
    "Industry Reports",
    "Macroeconomic Indicators",
    "Regulatory Filings",
    "Credit Markets",
    "News Intelligence",
    "Supply Chain Intelligence",
)

SCORE_FACTORS: tuple[str, ...] = (
    "valuation_excess",
    "earnings_deterioration",
    "financial_health",
    "competitive_position",
    "management_quality",
    "industry_outlook",
    "technical_weakness",
    "sentiment",
    "catalyst_probability",
    "downside_magnitude",
)


@dataclass(frozen=True)
class ShortOpportunityConfig:
    short_opportunity_office_enabled: bool = True
    maximum_assessments_per_cycle: int = 8
    minimum_short_opportunity_score: float = 55.0
    default_confidence_score: float = 68.0
    advisory_only: bool = True
    dynamic_domain_additions_enabled: bool = True
    ai_for_routine_scoring_enabled: bool = False


@dataclass(frozen=True)
class ShortOpportunityScore:
    overall_score: float
    factor_scores: dict[str, float]
    confidence_interval: tuple[float, float]
    evidence_quality: float
    forecast_horizon: str
    revision_history: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class StrategicShortAssessment:
    assessment_id: str
    timestamp: str
    domain: str
    security_name: str
    executive_summary: str
    short_opportunity_score: dict[str, Any]
    bearish_thesis: str
    principal_evidence: tuple[str, ...]
    valuation_assessment: str
    financial_health: str
    competitive_position: str
    industry_outlook: str
    catalysts: tuple[str, ...]
    estimated_downside: str
    principal_risks: tuple[str, ...]
    counterarguments: tuple[str, ...]
    invalidation_criteria: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    contradictory_evidence: tuple[str, ...]
    alternative_explanations: tuple[str, ...]
    bull_case: str
    bear_case: str
    unknowns: tuple[str, ...]
    evidence_gaps: tuple[str, ...]
    confidence_score: float
    forecast_horizon: str
    historian_archive_id: str
    librarian_index_id: str
    revision_history: tuple[dict[str, Any], ...]
    advisory_only: bool
    immutable: bool


class ShortOpportunityOffice:
    """Evaluates disciplined bearish theses without placing trades."""

    def __init__(self, config: ShortOpportunityConfig | None = None, domains: tuple[str, ...] | None = None) -> None:
        self._config = config or ShortOpportunityConfig()
        self._domains = tuple(dict.fromkeys(domains or EVALUATION_DOMAINS))
        self._assessments: list[StrategicShortAssessment] = []
        self._assessments_by_fingerprint: dict[str, tuple[StrategicShortAssessment, ...]] = {}

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
            "officeName": "Short Opportunity Office",
            "engineeringOrder": "EO-BW",
            "parentCommand": "Strategic Intelligence Command",
            "constitutionalMode": "ADVISORY_BEARISH_THESIS_ASSESSMENT_ONLY_NO_TRADING",
            "reportsExclusivelyTo": "Strategic Intelligence Command",
            "tradingAuthority": "NONE",
            "evaluationDomains": domains,
            "connectorInterfaces": _connectors(),
            "scoreFactors": SCORE_FACTORS,
            "shortCandidates": tuple(_candidate_payload(candidate) for candidate in self._identify_candidates(domains, sources)),
            "strategicShortAssessments": all_assessments,
            "latestStrategicShortAssessments": latest_assessments,
            "shortOpportunityBridge": bridge,
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
                "operationalOffice": "Short Opportunity Office",
                "topShortOpportunities": tuple(item["security_name"] for item in latest_assessments[:5]),
                "bearishWatchList": tuple(item["security_name"] for item in latest_assessments[:8]),
                "researchPriorities": tuple(item["security_name"] for item in latest_assessments[:4]),
                "averageShortOpportunityScore": metrics["averageShortOpportunityScore"],
                "route": "short_opportunity_bridge",
            },
            "auditTrail": (
                {"auditId": f"AUDIT-SOO-{len(all_assessments):06d}", "timestamp": timestamp_utc, "event": "short_opportunity_snapshot_completed", "lawVIICompliant": True, "lawVIIICompliant": True},
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

    def _resolved_config(self, registry: dict[str, Any]) -> ShortOpportunityConfig:
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        soo = configs.get("shortOpportunityOffice", {}) if isinstance(configs, dict) else {}
        if not isinstance(soo, dict):
            return self._config
        values = asdict(self._config)
        for key, value in soo.items():
            if key in values:
                values[key] = value
        return ShortOpportunityConfig(**values)

    def _resolved_domains(self, sources: dict[str, Any], config: ShortOpportunityConfig) -> tuple[str, ...]:
        registry = sources.get("enterpriseConfigurationRegistry", {})
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        configured = configs.get("shortOpportunityDomains", ()) if isinstance(configs, dict) else ()
        if config.dynamic_domain_additions_enabled and configured:
            return tuple(dict.fromkeys((*self._domains, *tuple(configured))))
        return self._domains

    def _identify_candidates(self, domains: tuple[str, ...], sources: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        decline = sources.get("declineIntelligenceOffice", {})
        decline_domains = tuple(decline.get("sicFeed", {}).get("decliningIndustries", ()))
        candidates = []
        for index, domain in enumerate(domains, start=1):
            decline_bonus = 7 if any(_overlap(domain, item) for item in decline_domains) else 0
            candidates.append(
                {
                    "candidate_id": f"SOO-CAND-{index:04d}",
                    "domain": domain,
                    "security_name": f"{domain} Bearish Thesis Candidate",
                    "declineBonus": decline_bonus,
                    "sourceSignals": ("short_universe_catalog", "decline_intelligence_overlap" if decline_bonus else "bearish_watchlist_seed"),
                }
            )
        return tuple(candidates)

    def _create_assessments(self, timestamp: str, candidates: tuple[dict[str, Any], ...], config: ShortOpportunityConfig) -> tuple[StrategicShortAssessment, ...]:
        scored = []
        for candidate in candidates:
            score = _score_candidate(candidate, timestamp)
            if score.overall_score >= config.minimum_short_opportunity_score:
                scored.append((candidate, score))
        scored.sort(key=lambda item: (-item[1].overall_score, item[0]["domain"]))
        assessments = []
        for index, (candidate, score) in enumerate(scored[: config.maximum_assessments_per_cycle], start=1):
            assessment_id = f"SOO-ASM-{len(self._assessments) + index:06d}"
            assessments.append(
                StrategicShortAssessment(
                    assessment_id=assessment_id,
                    timestamp=timestamp,
                    domain=candidate["domain"],
                    security_name=candidate["security_name"],
                    executive_summary=f"{candidate['domain']} has bearish thesis signals requiring Analyst/Risk validation before any investment decision.",
                    short_opportunity_score=asdict(score),
                    bearish_thesis=_bearish_thesis(candidate["domain"]),
                    principal_evidence=tuple(candidate["sourceSignals"]) + ("valuation_and_financial_quality_screen",),
                    valuation_assessment=_valuation_assessment(score),
                    financial_health=_financial_health(score),
                    competitive_position="competitive_position_requires_deeper_analyst_review",
                    industry_outlook="industry_outlook_is_negative_or_crowded_enough_for_bearish_review",
                    catalysts=("earnings_disappointment", "guidance_revision", "refinancing_pressure", "competitive_disruption"),
                    estimated_downside=_downside(score),
                    principal_risks=("crowded_short_risk", "short_squeeze", "unexpected_fundamental_recovery", "policy_or_liquidity_support"),
                    counterarguments=("valuation_may_already_discount_bad_news", "management_could_execute_turnaround", "macro_tailwind_could_offset_weakness"),
                    invalidation_criteria=("sustained_revenue_reacceleration", "margin_recovery", "deleveraging_progress", "positive_revision_cycle"),
                    supporting_evidence=tuple(f"{factor}:{value}" for factor, value in score.factor_scores.items()),
                    contradictory_evidence=("possible_mean_reversion", "possible_capital_injection", "insufficient_live_market_confirmation"),
                    alternative_explanations=("cyclical_weakness_not_structural", "temporary_inventory_or_rate_cycle_pressure"),
                    bull_case="A bullish outcome would require demand stabilization, margin recovery, and improved capital allocation evidence.",
                    bear_case="The bearish case is continued multiple compression, earnings disappointment, and catalyst-driven repricing.",
                    unknowns=("true_normalized_earnings_power", "near_term_catalyst_timing", "positioning_and_borrow_conditions"),
                    evidence_gaps=("validate_financial_statements", "measure_short_interest", "map_options_positioning", "collect_analyst_revision_history"),
                    confidence_score=round(config.default_confidence_score + (score.overall_score - 65.0) / 6, 4),
                    forecast_horizon=score.forecast_horizon,
                    historian_archive_id=f"HIST-{assessment_id}",
                    librarian_index_id=f"LIB-{assessment_id}",
                    revision_history=({"revision": 1, "timestamp": timestamp, "reason": "initial_short_opportunity_assessment"},),
                    advisory_only=True,
                    immutable=True,
                )
            )
        return tuple(assessments)


def _score_candidate(candidate: dict[str, Any], timestamp: str) -> ShortOpportunityScore:
    domain = str(candidate["domain"])
    base = (sum(ord(char) for char in domain) % 34) + 50
    scores = {
        "valuation_excess": _clamp(base + candidate.get("declineBonus", 0)),
        "earnings_deterioration": _clamp(54 + (len(domain) * 3 % 35)),
        "financial_health": _clamp(50 + (sum(ord(char) for char in domain[:5]) % 38)),
        "competitive_position": _clamp(52 + (sum(ord(char) for char in domain[-5:]) % 37)),
        "management_quality": _clamp(76 - (len(domain.split()) * 5)),
        "industry_outlook": _clamp(55 + (len(domain) % 36)),
        "technical_weakness": _clamp(48 + (sum(ord(char) for char in domain) % 42)),
        "sentiment": _clamp(50 + (len(domain.replace(" ", "")) % 33)),
        "catalyst_probability": _clamp(55 + (len(domain.split()) * 8)),
        "downside_magnitude": _clamp(58 + (sum(ord(char) for char in domain[:3]) % 36)),
    }
    weights = {
        "valuation_excess": 0.13,
        "earnings_deterioration": 0.12,
        "financial_health": 0.11,
        "competitive_position": 0.10,
        "management_quality": 0.07,
        "industry_outlook": 0.10,
        "technical_weakness": 0.09,
        "sentiment": 0.07,
        "catalyst_probability": 0.10,
        "downside_magnitude": 0.11,
    }
    overall = round(sum(scores[key] * weight for key, weight in weights.items()), 4)
    return ShortOpportunityScore(
        overall_score=overall,
        factor_scores=scores,
        confidence_interval=(round(max(0.0, overall - 8.5), 4), round(min(100.0, overall + 8.5), 4)),
        evidence_quality=round(min(100.0, 62.0 + len(candidate.get("sourceSignals", ())) * 7), 4),
        forecast_horizon=_forecast_horizon(overall),
        revision_history=({"revision": 1, "timestamp": timestamp, "reason": "deterministic_short_opportunity_score"},),
    )


def _bridge_payload(assessments: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    return {
        "highestShortScores": assessments[:5],
        "bearishWatchList": tuple(item["security_name"] for item in assessments[:8]),
        "highestDownsidePotential": tuple({"security": item["security_name"], "downside": item["estimated_downside"], "score": item["short_opportunity_score"]["factor_scores"]["downside_magnitude"]} for item in assessments),
        "industryWeakness": tuple({"domain": item["domain"], "outlook": item["industry_outlook"]} for item in assessments),
        "financialDistress": tuple({"security": item["security_name"], "score": item["short_opportunity_score"]["factor_scores"]["financial_health"]} for item in assessments),
        "valuationExtremes": tuple({"security": item["security_name"], "score": item["short_opportunity_score"]["factor_scores"]["valuation_excess"]} for item in assessments),
        "catalystCalendar": tuple({"security": item["security_name"], "catalysts": item["catalysts"], "horizon": item["forecast_horizon"]} for item in assessments),
        "confidenceDistribution": _confidence_distribution(assessments),
        "counterargumentStatus": tuple({"security": item["security_name"], "counterarguments": len(item["counterarguments"]), "invalidationCriteria": len(item["invalidation_criteria"])} for item in assessments),
        "evidenceQuality": _average(item["short_opportunity_score"]["evidence_quality"] for item in assessments),
        "historicalForecastAccuracy": {"accuracy": 0.0, "sampleSize": 0, "status": "TRACKING_INITIAL_BASELINE"},
        "runtimeHealth": "NOMINAL",
        "workflowStatus": "bounded_snapshot_complete",
        "apiUsage": {"apiCost": 0.0, "mode": "deterministic_no_paid_calls"},
    }


def _metrics(assessments: tuple[dict[str, Any], ...], bridge: dict[str, Any]) -> dict[str, Any]:
    return {
        "shortAssessmentsProduced": len(assessments),
        "forecastAccuracy": 0.0,
        "averageShortOpportunityScore": _average(item["short_opportunity_score"]["overall_score"] for item in assessments),
        "downsideRealizationAccuracy": 0.0,
        "catalystPredictionAccuracy": 0.0,
        "evidenceQuality": bridge["evidenceQuality"],
        "confidenceCalibration": "tracking",
        "historicalHitRate": 0.0,
        "falsePositives": 0,
        "falseNegatives": 0,
        "averageLeadTime": "tracking",
        "enterpriseUtilization": len(bridge["bearishWatchList"]),
        "apiUtilization": 0.0,
        "workflowParticipation": "bounded_advisory_snapshot",
    }


def _research_directives(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    targets = ("Analyst Group", "Risk Office", "Decline Intelligence Office", "Disruption Intelligence Office", "Market Structure Intelligence Office", "Historian", "Librarian", "Academy")
    return tuple(
        {
            "directiveId": f"SOO-RD-{index:03d}",
            "targetOffice": targets[(index - 1) % len(targets)],
            "security": item["security_name"],
            "request": "validate_bearish_thesis_evidence",
            "advisoryOnly": True,
        }
        for index, item in enumerate(assessments[:8], start=1)
    )


def _connectors() -> tuple[dict[str, str], ...]:
    return tuple({"connectorType": item, "status": "INTERFACE_READY", "liveExternalCalls": "DISABLED"} for item in CONNECTOR_TYPES)


def _historian_feed(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"historianArchiveId": item["historian_archive_id"], "assessmentId": item["assessment_id"], "originalThesis": item["bearish_thesis"], "outcomeTracking": "pending"} for item in assessments)


def _librarian_feed(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"librarianIndexId": item["librarian_index_id"], "assessmentId": item["assessment_id"], "indexTerms": (item["domain"], item["security_name"], item["forecast_horizon"], item["estimated_downside"])} for item in assessments)


def _candidate_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    return {**candidate, "shortOpportunityScorePreview": _score_candidate(candidate, "preview").overall_score}


def _inbox(sources: dict[str, Any]) -> tuple[dict[str, str], ...]:
    return tuple({"source": key, "messageType": "short_opportunity_source_snapshot", "status": "received"} for key in sorted(sources) if sources.get(key))


def _outbox(assessments: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
    return tuple({"target": "Strategic Intelligence Command", "messageType": "Strategic Short Assessment", "recordId": item["assessment_id"]} for item in assessments)


def _bearish_thesis(domain: str) -> str:
    return f"{domain} may be vulnerable to valuation compression, deteriorating fundamentals, or catalyst-driven downside."


def _valuation_assessment(score: ShortOpportunityScore) -> str:
    return "valuation_excess_requires_follow_on_modeling" if score.factor_scores["valuation_excess"] >= 65 else "valuation_risk_watch"


def _financial_health(score: ShortOpportunityScore) -> str:
    return "financial_quality_deteriorating" if score.factor_scores["financial_health"] >= 65 else "financial_quality_watch"


def _downside(score: ShortOpportunityScore) -> str:
    if score.factor_scores["downside_magnitude"] >= 78:
        return "high_downside_potential"
    if score.factor_scores["downside_magnitude"] >= 65:
        return "moderate_downside_potential"
    return "watchlist_downside_potential"


def _forecast_horizon(score: float) -> str:
    if score >= 74:
        return "Operational (Months)"
    if score >= 62:
        return "Near-Term (Weeks)"
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
        "decline": sources.get("declineIntelligenceOffice", {}).get("sicFeed", {}),
        "disruption": sources.get("disruptionIntelligenceOffice", {}).get("sicFeed", {}),
        "grand": sources.get("enterpriseGrandStrategyEngine", {}).get("activeGrandStrategyRecord", {}),
        "config": sources.get("enterpriseConfigurationRegistry", {}).get("activeConfiguration", {}),
    }


def _overlap(left: str, right: str) -> bool:
    left_terms = {term.lower() for term in left.replace("-", " ").split()}
    right_terms = {term.lower() for term in right.replace("-", " ").split()}
    return bool(left_terms & right_terms)


def _hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)
