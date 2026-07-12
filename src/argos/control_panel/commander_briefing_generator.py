"""Commander Briefing Generator for ARGOS EO-BN."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any


class BriefingType(str, Enum):
    MORNING_READINESS = "morning_readiness"
    INTRADAY_UPDATE = "intraday_update"
    END_OF_DAY = "end_of_day"
    CRITICAL_INCIDENT = "critical_incident"
    WEEKLY_STRATEGIC = "weekly_strategic"
    LEARNING_AND_EXPERIMENT = "learning_and_experiment"
    PORTFOLIO_AND_RISK = "portfolio_and_risk"
    AD_HOC = "ad_hoc"


@dataclass(frozen=True)
class CommanderBriefingGeneratorConfig:
    enabled: bool = True
    enabled_briefing_types: tuple[str, ...] = tuple(item.value for item in BriefingType)
    morning_briefing_policy: str = "deterministic_on_request_or_state_snapshot"
    intraday_briefing_policy: str = "material_changes_only"
    end_of_day_briefing_policy: str = "realized_unrealized_truth_distinction"
    weekly_briefing_policy: str = "complete_trade_and_benchmark_evidence_first"
    risk_material_change_threshold: float = 10.0
    capital_material_change_threshold_percent: float = 0.01
    reality_material_change_threshold: float = 5.0
    credit_rate_material_change_threshold_usd: float = 5.0
    freshness_threshold_seconds: int = 900
    maximum_items_per_section: int = 8
    unresolved_item_carryover_enabled: bool = True
    deterministic_summary_enabled: bool = True
    optional_narrative_enabled: bool = False
    narrative_ai_authorization_required: bool = True
    maximum_narrative_credit_cost: float = 0.01
    contradiction_validation_enabled: bool = True
    briefing_retention_limit: int = 120
    export_formats_enabled: tuple[str, ...] = ("json", "markdown", "plain_text")


@dataclass(frozen=True)
class CommanderBriefingRecord:
    commander_briefing_id: str
    briefing_type: str
    briefing_window_start: str
    briefing_window_end: str
    generated_at: str
    enterprise_mode: str
    overall_status: str
    executive_summary: str
    capital_summary: dict[str, Any]
    portfolio_summary: dict[str, Any]
    performance_summary: dict[str, Any]
    benchmark_summary: dict[str, Any]
    risk_summary: dict[str, Any]
    position_summary: dict[str, Any]
    execution_summary: dict[str, Any]
    reality_fidelity_summary: dict[str, Any]
    enterprise_health_summary: dict[str, Any]
    stress_and_survival_summary: dict[str, Any]
    learning_summary: dict[str, Any]
    experiment_summary: dict[str, Any]
    strategy_evolution_summary: dict[str, Any]
    prompt_evolution_summary: dict[str, Any]
    intelligence_efficiency_summary: dict[str, Any]
    material_changes: tuple[dict[str, Any], ...]
    critical_alerts: tuple[dict[str, Any], ...]
    decisions_required: tuple[dict[str, Any], ...]
    recommended_actions: tuple[str, ...]
    recommended_action_rationales: tuple[dict[str, str], ...]
    deferred_items: tuple[dict[str, Any], ...]
    data_freshness: dict[str, Any]
    degraded_sources: tuple[str, ...]
    evidence_references: tuple[dict[str, Any], ...]
    narrative_mode: str
    narrative_authorization_reference: str
    audit_reference: str
    recommended_operating_posture: str
    immutable: bool
    hash: str


TEMPLATES: dict[str, dict[str, Any]] = {
    BriefingType.MORNING_READINESS.value: {"sections": ("readiness", "capital", "risk", "reality", "positions", "attention")},
    BriefingType.INTRADAY_UPDATE.value: {"sections": ("material_changes", "positions", "orders", "risk", "credit", "decisions")},
    BriefingType.END_OF_DAY.value: {"sections": ("capital", "performance", "trades", "truth", "learning", "carryover")},
    BriefingType.CRITICAL_INCIDENT.value: {"sections": ("incident", "evidence", "containment", "decisions", "actions")},
    BriefingType.WEEKLY_STRATEGIC.value: {"sections": ("performance", "benchmark", "attribution", "risk_trends", "learning", "priorities")},
    BriefingType.LEARNING_AND_EXPERIMENT.value: {"sections": ("learning", "experiments", "promotions", "credit")},
    BriefingType.PORTFOLIO_AND_RISK.value: {"sections": ("capital", "positions", "risk", "correlation", "stress")},
    BriefingType.AD_HOC.value: {"sections": ("summary", "attention", "evidence")},
}


class CommanderBriefingGenerator:
    """Create traceable deterministic Commander briefings from source records."""

    def __init__(self, config: CommanderBriefingGeneratorConfig | None = None) -> None:
        self._config = config or CommanderBriefingGeneratorConfig()
        self._records: list[CommanderBriefingRecord] = []
        self._records_by_fingerprint: dict[str, CommanderBriefingRecord] = {}
        self._unresolved_critical_signatures: set[str] = set()
        self._narrative_attempts: list[dict[str, Any]] = []

    def generate(
        self,
        *,
        briefing_type: str,
        briefing_window_start: str,
        briefing_window_end: str,
        generated_at: str,
        sources: dict[str, Any],
        narrative_requested: bool = False,
        narrative_authorization: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        config = self._resolved_config(sources.get("enterpriseConfigurationRegistry") or sources.get("enterprise_configuration_registry") or {})
        normalized_type = _briefing_type(briefing_type)
        template = TEMPLATES[normalized_type]
        source_pack = self._source_pack(sources)
        material_changes = self._material_changes(source_pack)
        priority_items = self._priority_items(source_pack, material_changes)
        decisions = tuple(item for item in priority_items if item["actionable"])
        freshness = self._freshness(generated_at, source_pack)
        degraded = tuple(name for name, meta in freshness.items() if meta["degraded"] or meta["unavailable"])
        posture = self._posture(source_pack, priority_items, degraded)
        critical = tuple(item for item in priority_items if item["severity"] in {"CRITICAL", "EMERGENCY"})
        narrative_mode, narrative_reference = self._narrative_mode(
            structured_available=True,
            requested=narrative_requested,
            authorization=narrative_authorization,
            config=config,
        )
        evidence = self._evidence(source_pack)
        payload_without_ids = {
            "briefing_type": normalized_type,
            "briefing_window_start": briefing_window_start,
            "briefing_window_end": briefing_window_end,
            "template": template,
            "source_fingerprint": _hash(_stable_pack(source_pack)),
            "material_changes": material_changes,
            "posture": posture,
        }
        fingerprint = _hash(payload_without_ids)
        existing = self._records_by_fingerprint.get(fingerprint)
        if existing:
            return self.snapshot(latest_record=existing, timestamp_utc=generated_at)
        record_number = len(self._records) + 1
        record = CommanderBriefingRecord(
            commander_briefing_id=f"CBG-{record_number:06d}",
            briefing_type=normalized_type,
            briefing_window_start=briefing_window_start,
            briefing_window_end=briefing_window_end,
            generated_at=generated_at,
            enterprise_mode=source_pack["command"].get("tradingMode", "DORMANT"),
            overall_status=self._overall_status(priority_items, degraded),
            executive_summary=self._executive_summary(source_pack, material_changes, decisions, posture),
            capital_summary=source_pack["capital"],
            portfolio_summary=source_pack["portfolio"],
            performance_summary=source_pack["performance"],
            benchmark_summary=source_pack["benchmark"],
            risk_summary=source_pack["risk"],
            position_summary=source_pack["positions"],
            execution_summary=source_pack["execution"],
            reality_fidelity_summary=source_pack["reality"],
            enterprise_health_summary=source_pack["health"],
            stress_and_survival_summary=source_pack["stress"],
            learning_summary=source_pack["learning"],
            experiment_summary=source_pack["experiments"],
            strategy_evolution_summary=source_pack["strategy"],
            prompt_evolution_summary=source_pack["prompt"],
            intelligence_efficiency_summary=source_pack["intelligence"],
            material_changes=material_changes,
            critical_alerts=critical,
            decisions_required=decisions,
            recommended_actions=tuple(dict.fromkeys(item["recommendedAction"] for item in priority_items if item["recommendedAction"])),
            recommended_action_rationales=_action_rationales(priority_items),
            deferred_items=tuple(item for item in priority_items if not item["actionable"]),
            data_freshness=freshness,
            degraded_sources=degraded,
            evidence_references=evidence,
            narrative_mode=narrative_mode,
            narrative_authorization_reference=narrative_reference,
            audit_reference=f"AE-CBG-{record_number:06d}",
            recommended_operating_posture=posture,
            immutable=True,
            hash=fingerprint,
        )
        self._records.append(record)
        self._records_by_fingerprint[fingerprint] = record
        for item in critical:
            self._unresolved_critical_signatures.add(_hash({"reason": item["reason"], "source": item["sourceEngine"]}))
        return self.snapshot(latest_record=record, timestamp_utc=generated_at)

    def snapshot(self, *, timestamp_utc: str, latest_record: CommanderBriefingRecord | None = None) -> dict[str, Any]:
        latest = latest_record or (self._records[-1] if self._records else None)
        latest_payload = asdict(latest) if latest else {}
        return {
            "generatorName": "Commander Briefing Generator",
            "engineeringOrder": "EO-BN",
            "constitutionalMode": "BRIEFING_PRESENTATION_ONLY",
            "supportedBriefingTypes": tuple(item.value for item in BriefingType),
            "briefingTemplates": TEMPLATES,
            "briefingRecords": tuple(asdict(item) for item in self._records[-self._config.briefing_retention_limit :]),
            "latestBriefingRecord": latest_payload,
            "latestDashboardFeed": _dashboard_feed(latest_payload),
            "dailyReviewFeed": _daily_review_feed(latest_payload),
            "notificationFeed": _notification_feed(latest_payload),
            "exportFormats": self._config.export_formats_enabled,
            "optionalNarrative": {
                "enabled": self._config.optional_narrative_enabled,
                "structuredBriefingRequired": True,
                "authorizationRequired": self._config.narrative_ai_authorization_required,
                "contradictionValidationEnabled": self._config.contradiction_validation_enabled,
                "attempts": tuple(self._narrative_attempts[-10:]),
            },
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "executesTrades": False, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicBriefing": True, "optionalNarrativeRequiresAuthorization": True},
            "configuration": asdict(self._config),
            "internalDiagnostics": {
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "mutatesTruthRecords": False,
                "mutatesPrompts": False,
                "mutatesStrategies": False,
                "apiCreditsConsumed": 0.0,
                "recordCount": len(self._records),
                "unresolvedCriticalSignatureCount": len(self._unresolved_critical_signatures),
                "timestampUtc": timestamp_utc,
            },
        }

    def export(self, briefing_id: str, export_format: str = "json") -> str:
        record = next((item for item in self._records if item.commander_briefing_id == briefing_id), None)
        if not record:
            raise ValueError(f"unknown briefing: {briefing_id}")
        data = asdict(record)
        if export_format == "json":
            return json.dumps(data, indent=2, sort_keys=True)
        if export_format == "markdown":
            return f"# {record.briefing_type.replace('_', ' ').title()}\n\n{record.executive_summary}\n\n## Recommended Actions\n" + "\n".join(f"- {item}" for item in record.recommended_actions)
        if export_format == "plain_text":
            return f"{record.briefing_type}: {record.executive_summary}"
        raise ValueError(f"unsupported export format: {export_format}")

    def render_optional_narrative(self, structured_briefing_id: str, authorization: dict[str, Any] | None, narrative: str) -> dict[str, Any]:
        record = next((item for item in self._records if item.commander_briefing_id == structured_briefing_id), None)
        if not record:
            result = {"status": "REJECTED", "reason": "structured_briefing_required", "structuredBriefingId": structured_briefing_id}
            self._narrative_attempts.append(result)
            return result
        if not self._config.optional_narrative_enabled or not authorization or authorization.get("status") != "APPROVED":
            result = {"status": "REJECTED", "reason": "law_viii_authorization_required", "structuredBriefingId": structured_briefing_id}
            self._narrative_attempts.append(result)
            return result
        contradiction = self._narrative_contradiction(record, narrative)
        if contradiction:
            result = {"status": "REJECTED", "reason": contradiction, "structuredBriefingId": structured_briefing_id}
            self._narrative_attempts.append(result)
            return result
        result = {"status": "ACCEPTED", "reason": "authorized_readability_render", "structuredBriefingId": structured_briefing_id, "authorizationReference": authorization.get("authorizationReference", "")}
        self._narrative_attempts.append(result)
        return result

    def _source_pack(self, sources: dict[str, Any]) -> dict[str, Any]:
        dashboard = sources.get("commanderStrategicDashboard", {})
        truth = sources.get("performanceTruthEngine", {})
        trader = sources.get("traderCommandBridge", {})
        cdrw = sources.get("commanderDailyReviewWorkspace", {})
        grand = sources.get("enterpriseGrandStrategyEngine", {})
        strategic = sources.get("strategicIntelligenceCommand", {})
        grand_feed = grand.get("briefingFeed", {})
        return {
            "sourceAvailable": bool(dashboard),
            "command": _data(dashboard, "command_state"),
            "capital": _data(dashboard, "capital_state"),
            "portfolio": _data(dashboard, "active_portfolio"),
            "performance": _data(dashboard, "performance"),
            "benchmark": {"benchmarkReturn": _data(dashboard, "performance").get("benchmarkReturn"), "sampleSizeConfidence": _data(dashboard, "performance").get("sampleSizeConfidence")},
            "risk": _data(dashboard, "strategic_risk"),
            "positions": {"openPositions": _data(dashboard, "active_portfolio").get("activePositions"), "exitRecommendations": _data(dashboard, "active_portfolio").get("positionsWithExitRecommendations"), "surveillanceHealth": trader.get("summary", {}).get("surveillance_health", "unknown")},
            "execution": {"pendingOrders": _data(dashboard, "active_portfolio").get("pendingExitOrders"), "executionHealth": trader.get("summary", {}).get("execution_health", "unknown"), "rejectedOrders": truth.get("executionRealism", {}).get("rejectedOrders", 0), "partialFills": truth.get("executionRealism", {}).get("partialFills", 0)},
            "reality": _data(dashboard, "reality_fidelity"),
            "health": _data(dashboard, "readiness"),
            "stress": _data(dashboard, "stress_and_survival"),
            "learning": _data(dashboard, "learning_and_research"),
            "experiments": {"queuedExperiments": _data(dashboard, "learning_and_research").get("queuedExperiments"), "activeExperiments": _data(dashboard, "learning_and_research").get("activeExperiments")},
            "strategy": {"candidatesAwaitingReview": _data(dashboard, "learning_and_research").get("strategyCandidatesAwaitingReview", 0), "activePackage": cdrw.get("morningReadiness", {}).get("activeStrategyPackage", "Baseline"), "grandStrategyPosture": grand_feed.get("posture", ""), "grandStrategyVersion": grand_feed.get("strategyVersion", ""), "grandStrategySummary": grand_feed.get("summary", "")},
            "strategicIntelligence": {"reportsGenerated": len(strategic.get("strategicReports", ())), "topThemes": tuple(strategic.get("commanderBriefingFeed", {}).get("topThemes", ())), "latestReports": tuple(strategic.get("commanderBriefingFeed", {}).get("latestReports", ()))},
            "prompt": {"candidatesAwaitingReview": _data(dashboard, "learning_and_research").get("promptCandidatesAwaitingReview", 0), "activePackage": cdrw.get("morningReadiness", {}).get("activePromptPackage", "Baseline")},
            "intelligence": _data(dashboard, "intelligence_efficiency"),
            "attention": tuple(dashboard.get("attention_queue", ())),
            "freshness": dashboard.get("data_freshness", {}),
            "truth": {"portfolioLedgerCount": len(truth.get("portfolioLedger", ())), "orderCount": len(truth.get("orderLedger", ())), "tradeCount": len(truth.get("tradeLedger", ()))},
        }

    def _material_changes(self, pack: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        changes: list[dict[str, Any]] = []
        risk = _number(pack["risk"].get("compositeEnterpriseRiskScore"))
        if risk >= self._config.risk_material_change_threshold:
            changes.append(_item("MEDIUM", "WATCH", "Enterprise Risk Factor Engine", "Risk score is material", f"Composite risk {risk}", "review_risk", False))
        fidelity = _number(pack["reality"].get("overallRealityFidelityScore"))
        if fidelity and fidelity < 60:
            changes.append(_item("CRITICAL", "NOW", "Enterprise Reality Calibration Engine", "Unsafe reality fidelity", f"Fidelity {fidelity}", "request_reality_calibration", True))
        elif fidelity and fidelity < 80:
            changes.append(_item("HIGH", "TODAY", "Enterprise Reality Calibration Engine", "Reality fidelity degraded", f"Fidelity {fidelity}", "request_reality_calibration", True))
        if _number(pack["positions"].get("exitRecommendations")) > 0:
            changes.append(_item("HIGH", "SOON", "Trader Command Bridge", "Position exit recommendation pending", f"{pack['positions']['exitRecommendations']} exit recommendations", "review_exit", True))
        return tuple(changes)

    def _priority_items(self, pack: dict[str, Any], changes: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        items = list(pack.get("attention", ())) + list(changes)
        normalized = []
        for item in items:
            normalized.append({
                "severity": str(item.get("severity", "INFO")).upper(),
                "urgency": str(item.get("urgency", "ROUTINE")).upper(),
                "confidence": item.get("confidence", "HIGH"),
                "sourceEngine": item.get("sourceEngine", item.get("source", "ARGOS")),
                "reason": item.get("reason", item.get("evidenceSummary", "Briefing item")),
                "affectedCapitalOrSystems": item.get("affectedCapitalOrSystems", item.get("sourceEngine", "ARGOS")),
                "recommendedAction": item.get("recommendedAction", item.get("recommended_action", "monitor")),
                "evidenceReferences": item.get("evidenceReferences", (item.get("sourceEngine", "ARGOS"),)),
                "actionable": str(item.get("recommendedAction", "")).lower() not in {"", "monitor", "continue_normal_operations"},
            })
        return tuple(sorted(normalized, key=lambda item: (-_severity_rank(item["severity"]), item["sourceEngine"])))[: self._config.maximum_items_per_section]

    def _freshness(self, generated_at: str, pack: dict[str, Any]) -> dict[str, Any]:
        freshness = {}
        for name, meta in (pack.get("freshness") or {}).items():
            freshness[name] = {
                "sourceTimestamp": meta.get("source_record_timestamp", ""),
                "freshnessState": "STALE" if meta.get("stale") else "CURRENT",
                "degraded": bool(meta.get("degraded")),
                "unavailable": bool(meta.get("stale") and not meta.get("source_record_timestamp")),
                "impact": "Briefing section may be incomplete." if meta.get("stale") or meta.get("degraded") else "None",
            }
        if not freshness and not pack.get("sourceAvailable"):
            freshness["commanderStrategicDashboard"] = {"sourceTimestamp": generated_at, "freshnessState": "UNAVAILABLE", "degraded": True, "unavailable": True, "impact": "Strategic dashboard source unavailable."}
        return freshness

    def _evidence(self, pack: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        return (
            {"recordType": "Performance Truth", "recordId": "performanceTruthEngine", "route": "engineering_mode"},
            {"recordType": "Trader Command Bridge", "recordId": "traderCommandBridge", "route": "trader_bridge"},
            {"recordType": "Commander Strategic Dashboard", "recordId": "commanderStrategicDashboard", "route": "command_bridge"},
            {"recordType": "Strategic Intelligence Command", "recordId": "strategicIntelligenceCommand", "route": "strategic_intelligence_bridge"},
            {"recordType": "Risk Factor Record", "recordId": "enterpriseRiskFactorEngine", "route": "risk_bridge"},
            {"recordType": "Calibration Report", "recordId": "enterpriseRealityCalibrationEngine", "route": "engineering_mode"},
        )

    def _posture(self, pack: dict[str, Any], items: tuple[dict[str, Any], ...], degraded: tuple[str, ...]) -> str:
        if any(item["recommendedAction"] == "halt_trading" for item in items):
            return "halt_trading"
        if _number(pack["reality"].get("overallRealityFidelityScore")) < 60:
            return "require_reality_calibration"
        if degraded:
            return "require_data_repair"
        if _number(pack["positions"].get("exitRecommendations")) > 0:
            return "manage_existing_positions_only"
        if _number(pack["risk"].get("compositeEnterpriseRiskScore")) >= 60:
            return "continue_with_reduced_risk"
        return "continue_normal_operations"

    def _overall_status(self, items: tuple[dict[str, Any], ...], degraded: tuple[str, ...]) -> str:
        if any(item["severity"] in {"CRITICAL", "EMERGENCY"} for item in items):
            return "critical"
        if degraded:
            return "degraded"
        if any(item["severity"] == "HIGH" for item in items):
            return "review_required"
        return "nominal"

    def _executive_summary(self, pack: dict[str, Any], changes: tuple[dict[str, Any], ...], decisions: tuple[dict[str, Any], ...], posture: str) -> str:
        condition = pack["health"].get("readinessState", pack["health"].get("tradingReadiness", "unknown"))
        capital = pack["capital"].get("portfolioEquity", "unavailable")
        primary_risk = pack["risk"].get("riskLevel", "unknown")
        change = changes[0]["reason"] if changes else "No material change exceeded configured thresholds."
        decision_text = f"{len(decisions)} decision(s) required" if decisions else "No Commander decision required"
        grand = pack.get("strategy", {}).get("grandStrategyPosture")
        grand_text = f" Grand Strategy posture {grand}." if grand else ""
        return f"Enterprise condition {condition}; capital equity {capital}; primary risk {primary_risk}; {change}; {decision_text}; recommended posture {posture}.{grand_text}"

    def _narrative_mode(self, *, structured_available: bool, requested: bool, authorization: dict[str, Any] | None, config: CommanderBriefingGeneratorConfig) -> tuple[str, str]:
        if not requested:
            return "DETERMINISTIC_ONLY", ""
        if not structured_available:
            return "REJECTED_STRUCTURED_BRIEFING_REQUIRED", ""
        if not config.optional_narrative_enabled:
            return "REJECTED_OPTIONAL_NARRATIVE_DISABLED", ""
        if config.narrative_ai_authorization_required and (not authorization or authorization.get("status") != "APPROVED"):
            return "REJECTED_LAW_VIII_AUTHORIZATION_REQUIRED", ""
        return "AUTHORIZED_AI_READABILITY_RENDER", str(authorization.get("authorizationReference", ""))

    def _narrative_contradiction(self, record: CommanderBriefingRecord, narrative: str) -> str:
        if record.recommended_operating_posture not in narrative:
            return "altered_or_missing_operating_posture"
        for alert in record.critical_alerts:
            if alert["reason"] not in narrative:
                return "missing_critical_alert"
        return ""

    def _resolved_config(self, registry: dict[str, Any]) -> CommanderBriefingGeneratorConfig:
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        briefing = configs.get("commanderBriefingGenerator", {}) if isinstance(configs, dict) else {}
        if not isinstance(briefing, dict):
            return self._config
        values = asdict(self._config)
        for key, value in briefing.items():
            if key in values:
                values[key] = tuple(value) if isinstance(values[key], tuple) and isinstance(value, list) else value
        return CommanderBriefingGeneratorConfig(**values)


def _briefing_type(value: str) -> str:
    normalized = str(value or BriefingType.AD_HOC.value).strip().lower().replace(" ", "_")
    aliases = {"daily_enterprise_report": BriefingType.AD_HOC.value, "daily": BriefingType.AD_HOC.value}
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in TEMPLATES else BriefingType.AD_HOC.value


def _data(dashboard: dict[str, Any], section: str) -> dict[str, Any]:
    value = dashboard.get(section, {})
    return dict(value.get("data", {})) if isinstance(value, dict) else {}


def _item(severity: str, urgency: str, source: str, reason: str, evidence: str, action: str, actionable: bool) -> dict[str, Any]:
    return {"severity": severity, "urgency": urgency, "sourceEngine": source, "reason": reason, "evidenceSummary": evidence, "recommendedAction": action, "actionable": actionable}


def _action_rationales(priority_items: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
    by_action: dict[str, dict[str, str]] = {}
    for item in priority_items:
        action = str(item.get("recommendedAction", ""))
        if not action or action in by_action:
            continue
        reason = str(item.get("reason", "system attention item"))
        evidence = str(item.get("evidenceSummary", "supporting evidence is recorded in the briefing"))
        source = str(item.get("sourceEngine", "ARGOS"))
        severity = str(item.get("severity", "INFO"))
        by_action[action] = {
            "action": action,
            "reasoning": f"{source} recommends {action.replace('_', ' ')} because {reason}. Evidence: {evidence}.",
            "sourceEngine": source,
            "severity": severity,
        }
    return tuple(by_action.values())


def _number(value: Any) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return round(float(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _stable_pack(pack: dict[str, Any]) -> dict[str, Any]:
    stable = dict(pack)
    strategic = stable.get("strategicIntelligence")
    if isinstance(strategic, dict):
        stable["strategicIntelligence"] = {
            "topThemes": tuple(strategic.get("topThemes", ())),
        }
    stable["attention"] = tuple(_strip_volatile(item) for item in stable.get("attention", ()))
    stable["freshness"] = {
        name: {
            "stale": meta.get("stale"),
            "degraded": meta.get("degraded"),
        }
        for name, meta in (pack.get("freshness") or {}).items()
        if isinstance(meta, dict)
    }
    return _strip_volatile(stable)


def _strip_volatile(value: Any) -> Any:
    volatile_keys = {
        "timestamp",
        "timestampUtc",
        "currentTime",
        "latestDashboardDataTimestamp",
        "generated_at",
        "generatedAt",
        "source_record_timestamp",
        "sourceTimestamp",
    }
    if isinstance(value, dict):
        return {key: _strip_volatile(item) for key, item in value.items() if key not in volatile_keys}
    if isinstance(value, (tuple, list)):
        return tuple(_strip_volatile(item) for item in value)
    return value


def _severity_rank(severity: str) -> int:
    return {"EMERGENCY": 5, "CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}.get(severity, 0)


def _dashboard_feed(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "latestBriefingType": record.get("briefing_type", ""),
        "generatedAt": record.get("generated_at", ""),
        "overallStatus": record.get("overall_status", ""),
        "executiveSummary": record.get("executive_summary", ""),
        "topCriticalAlerts": tuple(record.get("critical_alerts", ())[:3]),
        "decisionsRequired": tuple(record.get("decisions_required", ())[:5]),
        "recommendedActions": tuple(record.get("recommended_action_rationales", ())[:6]),
        "recommendedPosture": record.get("recommended_operating_posture", ""),
        "linkToFullBriefing": record.get("commander_briefing_id", ""),
    }


def _daily_review_feed(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "morningBriefing": record if record.get("briefing_type") == BriefingType.MORNING_READINESS.value else {},
        "endOfDayBriefing": record if record.get("briefing_type") == BriefingType.END_OF_DAY.value else {},
        "unresolvedItems": tuple(record.get("decisions_required", ())),
        "linkedEvidence": tuple(record.get("evidence_references", ())),
    }


def _notification_feed(record: dict[str, Any]) -> dict[str, Any]:
    critical = tuple(record.get("critical_alerts", ()))
    return {
        "criticalNotificationRequired": bool(record.get("briefing_type") == BriefingType.CRITICAL_INCIDENT.value and critical),
        "severity": critical[0]["severity"] if critical else "",
        "title": critical[0]["reason"] if critical else "",
        "affectedCapitalOrSystem": critical[0]["affectedCapitalOrSystems"] if critical else "",
        "requiredAction": critical[0]["recommendedAction"] if critical else "",
        "briefingLink": record.get("commander_briefing_id", ""),
    }
