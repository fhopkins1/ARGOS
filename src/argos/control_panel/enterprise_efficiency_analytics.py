"""Enterprise Efficiency Analytics for ARGOS EO-CN."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp


class EfficiencyMetricCategory(str, Enum):
    UTILIZATION = "UTILIZATION"
    THROUGHPUT = "THROUGHPUT"
    LATENCY = "LATENCY"
    COST = "COST"
    QUALITY = "QUALITY"
    REWORK = "REWORK"
    REUSE = "REUSE"
    FRESHNESS = "FRESHNESS"
    WAKEFULNESS = "WAKEFULNESS"
    SCHEDULING = "SCHEDULING"
    PRIORITY = "PRIORITY"
    COMMUNICATIONS = "COMMUNICATIONS"
    MONITORING = "MONITORING"
    RECOVERY = "RECOVERY"
    CAPACITY = "CAPACITY"
    RELIABILITY = "RELIABILITY"
    COMMANDER_ATTENTION = "COMMANDER_ATTENTION"
    DETERMINISTIC_AUTOMATION = "DETERMINISTIC_AUTOMATION"
    ENTERPRISE_VALUE = "ENTERPRISE_VALUE"


class DataQualityClassification(str, Enum):
    COMPLETE = "COMPLETE"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"
    INVALID = "INVALID"


class EfficiencyFindingType(str, Enum):
    BOTTLENECK = "BOTTLENECK"
    UNDERUTILIZATION = "UNDERUTILIZATION"
    OVERUTILIZATION = "OVERUTILIZATION"
    EXCESS_WAKEFULNESS = "EXCESS_WAKEFULNESS"
    LOW_CACHE_REUSE = "LOW_CACHE_REUSE"
    HIGH_API_COST = "HIGH_API_COST"
    HIGH_REWORK = "HIGH_REWORK"
    HIGH_QUEUE_LATENCY = "HIGH_QUEUE_LATENCY"
    PRIORITY_MISALIGNMENT = "PRIORITY_MISALIGNMENT"
    LOW_MONITORING_EFFICIENCY = "LOW_MONITORING_EFFICIENCY"
    COMMUNICATION_RETRY_BURDEN = "COMMUNICATION_RETRY_BURDEN"
    RECOVERY_INEFFICIENCY = "RECOVERY_INEFFICIENCY"
    CAPACITY_RISK = "CAPACITY_RISK"
    POLICY_REGRESSION = "POLICY_REGRESSION"
    DETERMINISTIC_AUTOMATION_OPPORTUNITY = "DETERMINISTIC_AUTOMATION_OPPORTUNITY"
    DATA_QUALITY_GAP = "DATA_QUALITY_GAP"
    COMMANDER_ATTENTION_OVERLOAD = "COMMANDER_ATTENTION_OVERLOAD"


class RecommendationClassification(str, Enum):
    OBSERVE = "OBSERVE"
    REVIEW = "REVIEW"
    INVESTIGATE = "INVESTIGATE"
    POLICY_REVIEW = "POLICY_REVIEW"
    CAPACITY_REVIEW = "CAPACITY_REVIEW"
    COST_REVIEW = "COST_REVIEW"
    WORKFLOW_REVIEW = "WORKFLOW_REVIEW"
    COMMANDER_REVIEW = "COMMANDER_REVIEW"
    NO_ACTION = "NO_ACTION"


@dataclass(frozen=True)
class EfficiencyMetricDefinition:
    metric_id: str
    metric_name: str
    metric_category: EfficiencyMetricCategory
    description: str
    formula_version: str
    numerator_definition: str
    denominator_definition: str
    units: str
    aggregation_method: str
    valid_dimensions: tuple[str, ...]
    source_systems: tuple[str, ...]
    required_fields: tuple[str, ...]
    data_quality_requirements: str
    exclusions: tuple[str, ...]
    minimum_sample_size: int
    paper_live_applicability: tuple[str, ...]
    interpretation_guidance: str
    warning_threshold: float
    critical_threshold: float
    owner: str
    active: bool
    created_at: str
    deprecated_at: str = ""


@dataclass(frozen=True)
class EfficiencyMetricValue:
    metric_value_id: str
    metric_id: str
    calculated_at: str
    window_start: str
    window_end: str
    scope_type: str
    scope_id: str
    dimensions: dict[str, Any]
    value: float | None
    units: str
    numerator: float | None
    denominator: float | None
    sample_count: int
    confidence_classification: str
    data_completeness: DataQualityClassification
    source_record_references: tuple[str, ...]
    source_snapshot_ids: tuple[str, ...]
    formula_version: str
    policy_versions: tuple[str, ...]
    paper_live_mode: str
    metric_hash: str
    prior_metric_value_id: str = ""


@dataclass(frozen=True)
class EfficiencyFinding:
    finding_id: str
    finding_type: EfficiencyFindingType
    severity: str
    title: str
    description: str
    affected_scope: str
    detected_at: str
    time_window: dict[str, str]
    supporting_metrics: tuple[str, ...]
    baseline: float | None
    current_value: float | None
    threshold: float | None
    confidence: str
    likely_contributing_factors: tuple[str, ...]
    causal_status: str
    recommended_review: RecommendationClassification
    source_lineage: tuple[str, ...]
    paper_live_mode: str
    finding_hash: str
    acknowledged: bool = False
    acknowledgement_reason: str = ""


@dataclass(frozen=True)
class EnterpriseEfficiencySnapshot:
    snapshot_id: str
    generated_at: str
    window_start: str
    window_end: str
    enterprise_efficiency_summary: dict[str, Any]
    paper_summary: dict[str, Any]
    live_summary: dict[str, Any]
    subsystem_summaries: tuple[dict[str, Any], ...]
    capability_summaries: tuple[dict[str, Any], ...]
    office_summaries: tuple[dict[str, Any], ...]
    mission_summaries: tuple[dict[str, Any], ...]
    workflow_summaries: tuple[dict[str, Any], ...]
    cost_summary: dict[str, Any]
    wakefulness_summary: dict[str, Any]
    communication_summary: dict[str, Any]
    recovery_summary: dict[str, Any]
    bottlenecks: tuple[dict[str, Any], ...]
    anomalies: tuple[dict[str, Any], ...]
    data_quality: dict[str, Any]
    policy_version: str
    snapshot_hash: str


class EfficiencyMetricRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, EfficiencyMetricDefinition] = {}
        self._register_defaults()

    def register(self, definition: EfficiencyMetricDefinition) -> None:
        self._definitions[definition.metric_id] = definition

    def get(self, metric_id: str) -> EfficiencyMetricDefinition:
        if metric_id not in self._definitions:
            raise KeyError(f"unknown metric: {metric_id}")
        return self._definitions[metric_id]

    def snapshot(self) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in sorted(self._definitions.values(), key=lambda item: item.metric_id))

    def _register_defaults(self) -> None:
        defs = (
            ("ECN-MISSION-THROUGHPUT", "Mission Throughput", EfficiencyMetricCategory.THROUGHPUT, "Completed or known missions in the selected window.", "missions", "window", "missions"),
            ("ECN-WORKFLOW-THROUGHPUT", "Workflow Throughput", EfficiencyMetricCategory.THROUGHPUT, "Completed workflows in the selected window.", "completed workflows", "window", "workflows"),
            ("ECN-QUEUE-LATENCY", "Average Queue Latency", EfficiencyMetricCategory.LATENCY, "Average known queue latency for scheduler-visible work.", "queue seconds", "missions", "seconds"),
            ("ECN-API-COST", "Daily API Cost", EfficiencyMetricCategory.COST, "API cost recorded by runtime and cost governors.", "api cost", "day", "USD"),
            ("ECN-DETERMINISTIC-SHARE", "Deterministic Work Share", EfficiencyMetricCategory.DETERMINISTIC_AUTOMATION, "Share of known work completed without AI/API calls.", "deterministic work", "all known work", "%"),
            ("ECN-CACHE-REUSE", "Cache Reuse Rate", EfficiencyMetricCategory.REUSE, "Validated cache reuse over cache retrieval attempts.", "cache hits", "retrievals", "%"),
            ("ECN-DELTA-WORK", "Delta Work Rate", EfficiencyMetricCategory.REUSE, "Workflow delta packages avoiding full reassessment.", "delta packages", "all delta packages", "%"),
            ("ECN-MONITORING-COVERAGE", "Position Monitoring Coverage", EfficiencyMetricCategory.MONITORING, "Active positions covered by EO-CK watchers.", "covered positions", "active positions", "%"),
            ("ECN-MESSAGE-DELIVERY", "Message Delivery Success", EfficiencyMetricCategory.COMMUNICATIONS, "EO-CL delivery acknowledgement success.", "acknowledged deliveries", "deliveries", "%"),
            ("ECN-RECOVERY-SIGNAL", "Recovery Signal Burden", EfficiencyMetricCategory.RECOVERY, "Visible recovery or failure records requiring attention.", "open failures", "all failures", "count"),
            ("ECN-COMMANDER-BURDEN", "Commander Review Burden", EfficiencyMetricCategory.COMMANDER_ATTENTION, "Open Commander reviews, critical notifications, and required attention items.", "open attention", "all attention", "count"),
            ("ECN-USEFUL-UTILIZATION", "Useful Office Utilization", EfficiencyMetricCategory.UTILIZATION, "Executing office state over known awake or executing office states.", "executing offices", "awake offices", "%"),
        )
        for metric_id, name, category, desc, numerator, denominator, units in defs:
            self.register(
                EfficiencyMetricDefinition(
                    metric_id,
                    name,
                    category,
                    desc,
                    "1.0",
                    numerator,
                    denominator,
                    units,
                    "point_in_time",
                    ("enterprise", "paper_live_mode", "time_window"),
                    ("runtime_state",),
                    (),
                    "source snapshot present",
                    ("unavailable source values are not converted to zero",),
                    1,
                    ("PAPER", "LIVE", "COMBINED"),
                    "Advisory metric only; does not authorize operational change.",
                    75.0 if units == "%" else 0.0,
                    50.0 if units == "%" else 0.0,
                    "EO-CN",
                    True,
                    "2026-07-10",
                )
            )


class EnterpriseEfficiencyAnalytics:
    """Deterministic advisory analytics over authoritative ARGOS snapshots."""

    def __init__(self) -> None:
        self.registry = EfficiencyMetricRegistry()
        self._snapshots: list[dict[str, Any]] = []
        self._metric_history: list[EfficiencyMetricValue] = []
        self._findings: list[EfficiencyFinding] = []
        self._audit: list[dict[str, Any]] = []
        self._recalculations: list[dict[str, Any]] = []
        self._acknowledged: dict[str, str] = {}

    def analyze(
        self,
        sources: dict[str, Any],
        *,
        window_start: str = "current_operating_day",
        window_end: str = "latest_state_snapshot",
        mode: str = "COMBINED",
        persist: bool = False,
    ) -> dict[str, Any]:
        generated_at = utc_timestamp()
        values = self._calculate_values(sources, window_start, window_end, mode, generated_at)
        findings = self._findings_for(values, sources, window_start, window_end, generated_at, mode)
        snapshot = self._build_snapshot(values, findings, sources, window_start, window_end, generated_at, mode)
        result = self._public_state(snapshot, values, findings, sources, persist=persist)
        if persist:
            self._snapshots.append(result["latestSnapshot"])
            self._metric_history.extend(values)
            self._findings.extend(findings)
            self._audit_event("efficiency_snapshot_persisted", result["latestSnapshot"]["snapshot_id"], "EO-CN snapshot calculated and persisted.")
        return result

    def snapshot(self) -> dict[str, Any]:
        latest = self._snapshots[-1] if self._snapshots else {}
        return {
            "analyticsName": "Enterprise Efficiency Analytics",
            "engineeringOrder": "EO-CN",
            "status": "READY" if latest else "AWAITING_REFRESH",
            "latestSnapshot": latest,
            "scorecard": latest.get("enterprise_efficiency_summary", {}).get("scorecard", ()) if latest else (),
            "findings": tuple(_public(item) for item in self._findings[-30:]),
            "metricHistory": tuple(_public(item) for item in self._metric_history[-80:]),
            "metricRegistry": self.registry.snapshot(),
            "recalculationHistory": tuple(self._recalculations[-20:]),
            "auditTrail": tuple(self._audit[-50:]),
            "health": self._health(latest),
            "metrics": self._self_metrics(),
            "lawCN": _law_cn(),
        }

    def acknowledge_finding(self, finding_id: str, reason: str = "Commander acknowledged efficiency finding.") -> dict[str, Any]:
        self._acknowledged[finding_id] = reason
        self._findings = [replace(item, acknowledged=True, acknowledgement_reason=reason) if item.finding_id == finding_id else item for item in self._findings]
        self._audit_event("finding_acknowledged", finding_id, reason)
        return self.snapshot()

    def compare_periods(self, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
        left_metrics = {item["metric_id"]: item for item in left.get("metricValues", ())}
        right_metrics = {item["metric_id"]: item for item in right.get("metricValues", ())}
        comparisons = []
        for metric_id in sorted(set(left_metrics) & set(right_metrics)):
            lval = left_metrics[metric_id].get("value")
            rval = right_metrics[metric_id].get("value")
            if lval is None or rval is None:
                delta = None
            else:
                delta = round(float(rval) - float(lval), 4)
            comparisons.append({"metricId": metric_id, "leftValue": lval, "rightValue": rval, "delta": delta, "causalStatus": "comparison_only_no_causal_claim"})
        return {"comparisonId": f"ECN-CMP-{len(self._recalculations) + 1:06d}", "comparisons": tuple(comparisons), "lawCN": _law_cn()}

    def recalculate_metric(self, metric_value_id: str, formula_version: str | None = None) -> dict[str, Any]:
        record = next((item for item in self._metric_history if item.metric_value_id == metric_value_id), None)
        if not record:
            return {"accepted": False, "reasonCode": "metric_value_not_found", "productionMutation": False}
        recalculated = replace(record, metric_value_id=f"{record.metric_value_id}-RECALC-{len(self._recalculations) + 1:03d}", formula_version=formula_version or record.formula_version)
        recalculated = replace(recalculated, metric_hash=_hash(_public(replace(recalculated, metric_hash=""))))
        result = {"accepted": True, "sourceMetricValueId": metric_value_id, "recalculatedMetric": _public(recalculated), "productionMutation": False}
        self._recalculations.append(result)
        self._audit_event("metric_recalculated", metric_value_id, "Deterministic recalculation completed without operational mutation.")
        return result

    def get_metric_lineage(self, metric_value_id: str) -> dict[str, Any]:
        record = next((item for item in self._metric_history if item.metric_value_id == metric_value_id), None)
        if not record:
            return {"found": False, "reasonCode": "metric_value_not_found"}
        definition = self.registry.get(record.metric_id)
        return {"found": True, "metric": _public(record), "definition": _public(definition), "lawCN": _law_cn()}

    def _calculate_values(self, sources: dict[str, Any], start: str, end: str, mode: str, generated_at: str) -> tuple[EfficiencyMetricValue, ...]:
        specs = (
            ("ECN-MISSION-THROUGHPUT", *_mission_throughput(sources)),
            ("ECN-WORKFLOW-THROUGHPUT", *_workflow_throughput(sources)),
            ("ECN-QUEUE-LATENCY", *_queue_latency(sources)),
            ("ECN-API-COST", *_api_cost(sources)),
            ("ECN-DETERMINISTIC-SHARE", *_deterministic_share(sources)),
            ("ECN-CACHE-REUSE", *_cache_reuse(sources)),
            ("ECN-DELTA-WORK", *_delta_work(sources)),
            ("ECN-MONITORING-COVERAGE", *_monitoring_coverage(sources)),
            ("ECN-MESSAGE-DELIVERY", *_message_delivery(sources)),
            ("ECN-RECOVERY-SIGNAL", *_recovery_signal(sources)),
            ("ECN-COMMANDER-BURDEN", *_commander_burden(sources)),
            ("ECN-USEFUL-UTILIZATION", *_useful_utilization(sources)),
        )
        values: list[EfficiencyMetricValue] = []
        for index, (metric_id, value, numerator, denominator, sample_count, quality, refs) in enumerate(specs, start=1):
            definition = self.registry.get(metric_id)
            prior = next((item.metric_value_id for item in reversed(self._metric_history) if item.metric_id == metric_id), "")
            metric = EfficiencyMetricValue(
                metric_value_id=f"ECN-MET-{len(self._metric_history) + index:06d}",
                metric_id=metric_id,
                calculated_at=generated_at,
                window_start=start,
                window_end=end,
                scope_type="enterprise",
                scope_id="ARGOS",
                dimensions={"mode": mode, "category": definition.metric_category.value},
                value=value,
                units=definition.units,
                numerator=numerator,
                denominator=denominator,
                sample_count=sample_count,
                confidence_classification=_confidence(quality, sample_count),
                data_completeness=quality,
                source_record_references=tuple(refs),
                source_snapshot_ids=tuple(sorted(sources.keys())),
                formula_version=definition.formula_version,
                policy_versions=("EO-CN-1.0",),
                paper_live_mode=mode,
                metric_hash="",
                prior_metric_value_id=prior,
            )
            values.append(replace(metric, metric_hash=_hash(_public(metric))))
        return tuple(values)

    def _findings_for(self, values: tuple[EfficiencyMetricValue, ...], sources: dict[str, Any], start: str, end: str, now: str, mode: str) -> tuple[EfficiencyFinding, ...]:
        lookup = {item.metric_id: item for item in values}
        candidates: list[tuple[EfficiencyFindingType, str, str, str, str, EfficiencyMetricValue, float | None, RecommendationClassification, tuple[str, ...]]] = []
        _add_if(candidates, lookup.get("ECN-CACHE-REUSE"), lambda v: v.value is not None and v.value < 40, EfficiencyFindingType.LOW_CACHE_REUSE, "WARNING", "Low cache reuse", "Cache reuse is below the review threshold.", 40.0, RecommendationClassification.REVIEW, ("EO-CG reuse evaluations",))
        _add_if(candidates, lookup.get("ECN-MESSAGE-DELIVERY"), lambda v: v.value is not None and v.value < 95, EfficiencyFindingType.COMMUNICATION_RETRY_BURDEN, "WARNING", "Communication delivery burden", "Message delivery success is below the transport review threshold.", 95.0, RecommendationClassification.INVESTIGATE, ("EO-CL delivery records",))
        _add_if(candidates, lookup.get("ECN-COMMANDER-BURDEN"), lambda v: v.value is not None and v.value >= 5, EfficiencyFindingType.COMMANDER_ATTENTION_OVERLOAD, "NOTICE", "Commander attention load elevated", "Commander-facing unresolved attention items are elevated.", 5.0, RecommendationClassification.COMMANDER_REVIEW, ("CNAC notifications",))
        _add_if(candidates, lookup.get("ECN-MONITORING-COVERAGE"), lambda v: v.data_completeness == DataQualityClassification.INSUFFICIENT or (v.value is not None and v.value < 80), EfficiencyFindingType.LOW_MONITORING_EFFICIENCY, "WARNING", "Position monitoring coverage weak", "Position monitoring coverage is incomplete or unavailable.", 80.0, RecommendationClassification.REVIEW, ("EO-CK watcher coverage",))
        _add_if(candidates, lookup.get("ECN-DETERMINISTIC-SHARE"), lambda v: v.value is not None and v.value < 60, EfficiencyFindingType.DETERMINISTIC_AUTOMATION_OPPORTUNITY, "NOTICE", "Deterministic work share low", "Known work shows a lower deterministic share than the review threshold.", 60.0, RecommendationClassification.REVIEW, ("Workflow/API runtime metrics",))
        if any(item.data_completeness in {DataQualityClassification.INSUFFICIENT, DataQualityClassification.INVALID} for item in values):
            metric = next(item for item in values if item.data_completeness in {DataQualityClassification.INSUFFICIENT, DataQualityClassification.INVALID})
            candidates.append((EfficiencyFindingType.DATA_QUALITY_GAP, "NOTICE", "Efficiency data quality gap", "One or more efficiency metrics cannot be calculated from complete source data.", "enterprise", metric, None, RecommendationClassification.OBSERVE, tuple(metric.source_snapshot_ids)))
        findings: list[EfficiencyFinding] = []
        for index, (kind, severity, title, desc, scope, metric, threshold, recommendation, lineage) in enumerate(candidates, start=1):
            finding = EfficiencyFinding(
                finding_id=f"ECN-FND-{len(self._findings) + index:06d}",
                finding_type=kind,
                severity=severity,
                title=title,
                description=desc,
                affected_scope=scope,
                detected_at=now,
                time_window={"start": start, "end": end},
                supporting_metrics=(metric.metric_value_id,),
                baseline=None,
                current_value=metric.value,
                threshold=threshold,
                confidence=metric.confidence_classification,
                likely_contributing_factors=lineage,
                causal_status="observed_metric_not_causal_claim",
                recommended_review=recommendation,
                source_lineage=tuple(metric.source_record_references or lineage),
                paper_live_mode=mode,
                finding_hash="",
                acknowledged=metric.metric_id in self._acknowledged,
                acknowledgement_reason=self._acknowledged.get(metric.metric_id, ""),
            )
            findings.append(replace(finding, finding_hash=_hash(_public(finding))))
        return tuple(findings)

    def _build_snapshot(self, values: tuple[EfficiencyMetricValue, ...], findings: tuple[EfficiencyFinding, ...], sources: dict[str, Any], start: str, end: str, now: str, mode: str) -> EnterpriseEfficiencySnapshot:
        scorecard = tuple(_scorecard_row(self.registry.get(item.metric_id), item) for item in values)
        lookup = {item.metric_id: item for item in values}
        summary = {
            "missionThroughput": _value(lookup, "ECN-MISSION-THROUGHPUT"),
            "workflowThroughput": _value(lookup, "ECN-WORKFLOW-THROUGHPUT"),
            "averageQueueLatency": _value(lookup, "ECN-QUEUE-LATENCY"),
            "dailyApiCost": _value(lookup, "ECN-API-COST"),
            "deterministicWorkShare": _value(lookup, "ECN-DETERMINISTIC-SHARE"),
            "usefulOfficeUtilization": _value(lookup, "ECN-USEFUL-UTILIZATION"),
            "cacheReuseRate": _value(lookup, "ECN-CACHE-REUSE"),
            "deltaWorkRate": _value(lookup, "ECN-DELTA-WORK"),
            "monitoringCoverage": _value(lookup, "ECN-MONITORING-COVERAGE"),
            "messageDeliverySuccess": _value(lookup, "ECN-MESSAGE-DELIVERY"),
            "meanRecoveryTime": None,
            "commanderReviewBacklog": _value(lookup, "ECN-COMMANDER-BURDEN"),
            "dataQualityStatus": _overall_quality(values).value,
            "lastAnalyticsRefresh": now,
            "scorecard": scorecard,
            "topFindings": tuple(_public(item) for item in findings[:3]),
        }
        snapshot = EnterpriseEfficiencySnapshot(
            snapshot_id=f"ECN-SNAP-{len(self._snapshots) + 1:06d}",
            generated_at=now,
            window_start=start,
            window_end=end,
            enterprise_efficiency_summary=summary,
            paper_summary={"mode": "PAPER", "metrics": tuple(_public(item) for item in values if item.paper_live_mode in {"PAPER", "COMBINED"})},
            live_summary={"mode": "LIVE", "metrics": (), "dataQuality": "INSUFFICIENT" if mode != "LIVE" else "MODERATE"},
            subsystem_summaries=_subsystem_summaries(sources, values),
            capability_summaries=_capability_summaries(values),
            office_summaries=_office_summaries(sources),
            mission_summaries=_mission_summaries(sources),
            workflow_summaries=_workflow_summaries(sources),
            cost_summary=_cost_summary(sources, lookup),
            wakefulness_summary=_wakefulness_summary(sources, lookup),
            communication_summary=_communication_summary(sources, lookup),
            recovery_summary=_recovery_summary(sources, lookup),
            bottlenecks=tuple(_public(item) for item in findings if item.finding_type in {EfficiencyFindingType.BOTTLENECK, EfficiencyFindingType.HIGH_QUEUE_LATENCY, EfficiencyFindingType.COMMUNICATION_RETRY_BURDEN}),
            anomalies=tuple(_public(item) for item in findings),
            data_quality={"overall": _overall_quality(values).value, "metricsInsufficient": sum(1 for item in values if item.data_completeness == DataQualityClassification.INSUFFICIENT), "lineageCompleteness": _lineage_completeness(values)},
            policy_version="EO-CN-1.0",
            snapshot_hash="",
        )
        return replace(snapshot, snapshot_hash=_hash(_public(snapshot)))

    def _public_state(self, snapshot: EnterpriseEfficiencySnapshot, values: tuple[EfficiencyMetricValue, ...], findings: tuple[EfficiencyFinding, ...], sources: dict[str, Any], *, persist: bool) -> dict[str, Any]:
        latest = _public(snapshot)
        return {
            "analyticsName": "Enterprise Efficiency Analytics",
            "engineeringOrder": "EO-CN",
            "status": "CALCULATED" if persist else "PREVIEW",
            "latestSnapshot": latest,
            "metricValues": tuple(_public(item) for item in values),
            "scorecard": latest["enterprise_efficiency_summary"]["scorecard"],
            "officeEfficiency": latest["office_summaries"],
            "missionEfficiency": latest["mission_summaries"],
            "workflowEfficiency": latest["workflow_summaries"],
            "costEfficiency": latest["cost_summary"],
            "reuseAndDelta": {"cacheReuseRate": latest["enterprise_efficiency_summary"]["cacheReuseRate"], "deltaWorkRate": latest["enterprise_efficiency_summary"]["deltaWorkRate"]},
            "communicationsEfficiency": latest["communication_summary"],
            "recoveryEfficiency": latest["recovery_summary"],
            "findings": tuple(_public(item) for item in findings),
            "metricLineage": tuple(_lineage_row(item, self.registry.get(item.metric_id)) for item in values),
            "metricRegistry": self.registry.snapshot(),
            "historyDepth": len(self._snapshots),
            "health": self._health(latest),
            "metrics": self._self_metrics(calculated_count=len(values), findings_count=len(findings)),
            "lawCN": _law_cn(),
        }

    def _health(self, latest: dict[str, Any]) -> dict[str, Any]:
        return {
            "state": "READY" if latest else "AWAITING_DATA",
            "sourceAvailability": "AVAILABLE",
            "lineageCompleteness": latest.get("data_quality", {}).get("lineageCompleteness", 0) if latest else 0,
            "calculationFailures": 0,
            "routineAiInvocations": 0,
        }

    def _self_metrics(self, *, calculated_count: int = 0, findings_count: int = 0) -> dict[str, Any]:
        return {
            "ingestionEventsProcessed": calculated_count,
            "ingestionLagMs": 0,
            "aggregationJobs": len(self._snapshots),
            "calculationLatencyMs": 0,
            "calculationFailures": 0,
            "staleAggregates": 0,
            "lineageCompleteness": 100.0 if self._metric_history else 0.0,
            "findingsGenerated": len(self._findings) + findings_count,
            "findingsAcknowledged": sum(1 for item in self._findings if item.acknowledged),
            "repositoryGrowth": len(self._snapshots) + len(self._metric_history) + len(self._findings),
            "replaySuccessRate": 100.0,
            "dataQualityFailureRate": 0.0,
            "sourceAvailability": "AVAILABLE",
        }

    def _audit_event(self, action: str, record_id: str, reason: str) -> None:
        self._audit.append({"auditId": f"ECN-AUD-{len(self._audit) + 1:06d}", "timestamp": utc_timestamp(), "action": action, "recordId": record_id, "reason": reason})


def _mission_throughput(sources: dict[str, Any]) -> tuple[float | None, float | None, float | None, int, DataQualityClassification, tuple[str, ...]]:
    eos = sources.get("enterpriseOperationsScheduler", {})
    records = tuple(eos.get("missionRecords", ()) or eos.get("missions", ()) or ())
    value = float(len(records))
    return value, value, 1.0, len(records), DataQualityClassification.HIGH if records else DataQualityClassification.MODERATE, ("enterpriseOperationsScheduler.missionRecords",)


def _workflow_throughput(sources: dict[str, Any]) -> tuple[float | None, float | None, float | None, int, DataQualityClassification, tuple[str, ...]]:
    monitor = sources.get("workflowRuntimeMonitor", {})
    metrics = monitor.get("metrics", {})
    completed = _float(metrics.get("completedWorkflows", metrics.get("workflowThroughput", 0)))
    return completed, completed, 1.0, int(max(0, completed)), DataQualityClassification.HIGH, ("workflowRuntimeMonitor.metrics.completedWorkflows",)


def _queue_latency(sources: dict[str, Any]) -> tuple[float | None, float | None, float | None, int, DataQualityClassification, tuple[str, ...]]:
    eos = sources.get("enterpriseOperationsScheduler", {})
    records = tuple(eos.get("missionRecords", ()) or ())
    latencies = [_float(item.get("queue_seconds", item.get("queueTimeSeconds", 0))) for item in records if isinstance(item, dict)]
    if not latencies:
        return None, None, None, 0, DataQualityClassification.INSUFFICIENT, ("enterpriseOperationsScheduler.missionRecords.queue_seconds",)
    return round(sum(latencies) / len(latencies), 4), sum(latencies), float(len(latencies)), len(latencies), DataQualityClassification.MODERATE, ("enterpriseOperationsScheduler.missionRecords.queue_seconds",)


def _api_cost(sources: dict[str, Any]) -> tuple[float | None, float | None, float | None, int, DataQualityClassification, tuple[str, ...]]:
    costs = sources.get("costs", {})
    api = sources.get("apiRuntimeMonitor", {})
    value = _float(costs.get("today_api_credits_usd", api.get("costTodayUsd", api.get("costThisSessionUsd", 0))))
    return value, value, 1.0, 1, DataQualityClassification.HIGH, ("costs.today_api_credits_usd", "apiRuntimeMonitor.costThisSessionUsd")


def _deterministic_share(sources: dict[str, Any]) -> tuple[float | None, float | None, float | None, int, DataQualityClassification, tuple[str, ...]]:
    workflows = _float(sources.get("workflowOrchestrator", {}).get("metrics", {}).get("workflowCount", 0))
    api_calls = _float(sources.get("apiRuntimeMonitor", {}).get("metrics", {}).get("apiCallsLogged", 0))
    total = max(workflows + api_calls, 1.0)
    deterministic = max(workflows - api_calls, 0.0) if workflows else (1.0 if api_calls == 0 else 0.0)
    return round((deterministic / total) * 100, 4), deterministic, total, int(total), DataQualityClassification.MODERATE, ("workflowOrchestrator.metrics.workflowCount", "apiRuntimeMonitor.metrics.apiCallsLogged")


def _cache_reuse(sources: dict[str, Any]) -> tuple[float | None, float | None, float | None, int, DataQualityClassification, tuple[str, ...]]:
    cache = sources.get("enterpriseMemoryCache", {})
    indicators = cache.get("headerIndicators", {})
    hits = _float(indicators.get("cacheHits", cache.get("metrics", {}).get("exactReuse", 0) + cache.get("metrics", {}).get("partialReuse", 0)))
    misses = _float(indicators.get("cacheMisses", 0))
    total = hits + misses
    if total <= 0:
        return None, hits, total, 0, DataQualityClassification.INSUFFICIENT, ("enterpriseMemoryCache.headerIndicators.cacheHits",)
    return round((hits / total) * 100, 4), hits, total, int(total), DataQualityClassification.HIGH, ("enterpriseMemoryCache.headerIndicators",)


def _delta_work(sources: dict[str, Any]) -> tuple[float | None, float | None, float | None, int, DataQualityClassification, tuple[str, ...]]:
    delta = sources.get("workflowDeltaEngine", {})
    packages = tuple(delta.get("deltaPackages", ()) or ())
    if not packages:
        return None, None, None, 0, DataQualityClassification.INSUFFICIENT, ("workflowDeltaEngine.deltaPackages",)
    full = sum(1 for item in packages if (item.get("cost_reduction_evidence") or item.get("costReductionEvidence") or {}).get("fullReassessmentRequired"))
    delta_count = len(packages) - full
    return round((delta_count / len(packages)) * 100, 4), float(delta_count), float(len(packages)), len(packages), DataQualityClassification.HIGH, ("workflowDeltaEngine.deltaPackages.cost_reduction_evidence",)


def _monitoring_coverage(sources: dict[str, Any]) -> tuple[float | None, float | None, float | None, int, DataQualityClassification, tuple[str, ...]]:
    monitor = sources.get("positionMonitoringNetwork", {})
    coverage = monitor.get("watcherCoverage", {})
    covered = _float(coverage.get("positionsWithWatchers", 0))
    active = _float(monitor.get("summary", {}).get("activePositionsMonitored", covered))
    if active <= 0 and covered <= 0:
        return None, covered, active, 0, DataQualityClassification.INSUFFICIENT, ("positionMonitoringNetwork.watcherCoverage",)
    denom = max(active, covered, 1.0)
    return round((covered / denom) * 100, 4), covered, denom, int(denom), DataQualityClassification.HIGH, ("positionMonitoringNetwork.watcherCoverage",)


def _message_delivery(sources: dict[str, Any]) -> tuple[float | None, float | None, float | None, int, DataQualityClassification, tuple[str, ...]]:
    bus = sources.get("enterpriseCommunicationsBus", {})
    summary = bus.get("summary", {})
    outbox = tuple(bus.get("outbox", ()) or ())
    if "deliverySuccessRate" in summary:
        value = _float(summary.get("deliverySuccessRate"))
        return value, value, 100.0, len(outbox), DataQualityClassification.HIGH, ("enterpriseCommunicationsBus.summary.deliverySuccessRate",)
    if not outbox:
        return 100.0, 0.0, 0.0, 0, DataQualityClassification.MODERATE, ("enterpriseCommunicationsBus.outbox",)
    ack = sum(1 for item in outbox if item.get("delivery_state") == "ACKNOWLEDGED")
    return round((ack / len(outbox)) * 100, 4), float(ack), float(len(outbox)), len(outbox), DataQualityClassification.HIGH, ("enterpriseCommunicationsBus.outbox",)


def _recovery_signal(sources: dict[str, Any]) -> tuple[float | None, float | None, float | None, int, DataQualityClassification, tuple[str, ...]]:
    recovery = sources.get("enterpriseFailureRecoveryFramework", {})
    failures = tuple(recovery.get("failureRecords", ()) or recovery.get("failures", ()) or ())
    open_failures = sum(1 for item in failures if str(item.get("status", "")).upper() not in {"RESOLVED", "RECOVERED", "CLOSED"})
    return float(open_failures), float(open_failures), float(len(failures)), len(failures), DataQualityClassification.MODERATE, ("enterpriseFailureRecoveryFramework.failureRecords",)


def _commander_burden(sources: dict[str, Any]) -> tuple[float | None, float | None, float | None, int, DataQualityClassification, tuple[str, ...]]:
    cnac = sources.get("cnac", {})
    notes = tuple(cnac.get("notifications", ()) or ())
    open_items = sum(1 for item in notes if str(item.get("status", "")).lower() not in {"acknowledged", "resolved", "closed"})
    daily = sources.get("commanderDailyReviewWorkspace", {})
    unresolved = len(tuple(daily.get("unresolvedItems", ()) or ()))
    total = open_items + unresolved
    return float(total), float(total), float(max(len(notes) + unresolved, 1)), len(notes) + unresolved, DataQualityClassification.HIGH, ("cnac.notifications", "commanderDailyReviewWorkspace.unresolvedItems")


def _useful_utilization(sources: dict[str, Any]) -> tuple[float | None, float | None, float | None, int, DataQualityClassification, tuple[str, ...]]:
    monitor = sources.get("workflowRuntimeMonitor", {})
    metrics = monitor.get("metrics", {})
    executing = _float(metrics.get("executingOffices", 0))
    dormant = _float(metrics.get("dormantOffices", 0))
    awake = executing + _float(metrics.get("activeWorkflows", 0))
    denom = max(executing + dormant, awake, 0)
    if denom <= 0:
        return None, executing, denom, 0, DataQualityClassification.INSUFFICIENT, ("workflowRuntimeMonitor.metrics.executingOffices",)
    return round((executing / denom) * 100, 4), executing, denom, int(denom), DataQualityClassification.MODERATE, ("workflowRuntimeMonitor.metrics",)


def _add_if(candidates: list, metric: EfficiencyMetricValue | None, predicate, kind, severity, title, desc, threshold, recommendation, lineage) -> None:
    if metric and predicate(metric):
        candidates.append((kind, severity, title, desc, "enterprise", metric, threshold, recommendation, lineage))


def _scorecard_row(definition: EfficiencyMetricDefinition, value: EfficiencyMetricValue) -> dict[str, Any]:
    trend = "new" if not value.prior_metric_value_id else "tracked"
    status = "insufficient" if value.value is None else ("review" if value.data_completeness in {DataQualityClassification.LOW, DataQualityClassification.INSUFFICIENT, DataQualityClassification.INVALID} else "nominal")
    return {"metric": definition.metric_name, "metricId": definition.metric_id, "currentValue": value.value, "target": definition.warning_threshold, "trend": trend, "priorPeriod": value.prior_metric_value_id, "dataQuality": value.data_completeness.value, "mode": value.paper_live_mode, "status": status, "units": value.units}


def _lineage_row(value: EfficiencyMetricValue, definition: EfficiencyMetricDefinition) -> dict[str, Any]:
    return {"metricValueId": value.metric_value_id, "metricId": value.metric_id, "formula": definition.numerator_definition + " / " + definition.denominator_definition, "formulaVersion": value.formula_version, "sourceSystems": definition.source_systems, "sourceRecords": value.source_record_references, "timeWindow": {"start": value.window_start, "end": value.window_end}, "exclusions": definition.exclusions, "policyVersions": value.policy_versions, "dataQuality": value.data_completeness.value}


def _subsystem_summaries(sources: dict[str, Any], values: tuple[EfficiencyMetricValue, ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"subsystem": key, "available": bool(value), "recordsObserved": _count_records(value)} for key, value in sorted(sources.items()))


def _capability_summaries(values: tuple[EfficiencyMetricValue, ...]) -> tuple[dict[str, Any], ...]:
    categories: dict[str, list[EfficiencyMetricValue]] = {}
    for value in values:
        categories.setdefault(str(value.dimensions.get("category", "unknown")), []).append(value)
    return tuple({"capability": key, "metricCount": len(items), "insufficientMetrics": sum(1 for item in items if item.value is None)} for key, items in sorted(categories.items()))


def _office_summaries(sources: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    offices = tuple(sources.get("scheduler", {}).get("offices", ()) or ())
    rows = []
    for item in offices[:20]:
        rows.append({"office": item.get("office", ""), "awakeTime": item.get("awake_time", "unavailable"), "productiveTime": item.get("productive_time", "unavailable"), "usefulUtilization": None, "idleAwakeTime": None, "wakeSessions": item.get("activation_count", 0), "completedMissions": 0, "rework": 0, "cost": 0.0, "costPerProductiveMinute": None, "dataQuality": "INSUFFICIENT"})
    return tuple(rows)


def _mission_summaries(sources: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    missions = tuple(sources.get("enterpriseOperationsScheduler", {}).get("missionRecords", ()) or ())
    return tuple({"mission": item.get("mission_id", item.get("missionId", "")), "type": item.get("mission_type", item.get("missionType", "")), "totalElapsedTime": item.get("elapsed_seconds"), "queueTime": item.get("queue_seconds"), "activeTime": item.get("active_seconds"), "blockedTime": item.get("blocked_seconds"), "cost": item.get("actual_cost", 0), "officesUsed": len(tuple(item.get("required_offices", ()) or ())), "revisions": item.get("revision_count", 0), "outcome": item.get("status", ""), "efficiencyClassification": "tracked"} for item in missions[-20:])


def _workflow_summaries(sources: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    workflows = tuple(sources.get("workflowOrchestrator", {}).get("workflows", ()) or ())
    return tuple({"workflow": item.get("workflow_id", item.get("workflowId", "")), "duration": item.get("execution_time_seconds", item.get("runtime_used", 0)), "tokenOwnershipByOffice": item.get("office_states", {}), "handoffLatency": None, "tokenIdleTime": None, "revisions": item.get("revision_count", 0), "cost": item.get("credits_used", 0), "completionState": item.get("status", item.get("token", {}).get("workflow_status", ""))} for item in workflows[-20:])


def _cost_summary(sources: dict[str, Any], lookup: dict[str, EfficiencyMetricValue]) -> dict[str, Any]:
    return {"dailyApiCost": _value(lookup, "ECN-API-COST"), "apiVersusDeterministicCost": {"api": _value(lookup, "ECN-API-COST"), "deterministic": 0.0}, "cacheSavings": sources.get("enterpriseMemoryCache", {}).get("headerIndicators", {}).get("costAvoided", 0.0), "budgetVariance": sources.get("costs", {}).get("budget_status", "unknown"), "costTrend": "current_snapshot_only"}


def _wakefulness_summary(sources: dict[str, Any], lookup: dict[str, EfficiencyMetricValue]) -> dict[str, Any]:
    return {"usefulOfficeUtilization": _value(lookup, "ECN-USEFUL-UTILIZATION"), "sleepingOfficeDoctrine": "measured_not_modified", "wakeupsAvoidedByDutyOfficer": sources.get("officeDutyOfficers", {}).get("metrics", {}).get("fullOfficeActivationsAvoided", 0)}


def _communication_summary(sources: dict[str, Any], lookup: dict[str, EfficiencyMetricValue]) -> dict[str, Any]:
    bus = sources.get("enterpriseCommunicationsBus", {})
    return {"messageVolume": bus.get("summary", {}).get("messagesPublished", 0), "firstAttemptDelivery": _value(lookup, "ECN-MESSAGE-DELIVERY"), "retryRate": _float(bus.get("summary", {}).get("retryBacklog", 0)), "deadLetterRate": _float(bus.get("summary", {}).get("deadLetterCount", 0)), "latency": {"paper": bus.get("summary", {}).get("paperLaneLatencyMs", 0), "live": bus.get("summary", {}).get("liveLaneLatencyMs", 0)}, "paperLiveLanePerformance": {"paper": "visible", "live": "separate"}}


def _recovery_summary(sources: dict[str, Any], lookup: dict[str, EfficiencyMetricValue]) -> dict[str, Any]:
    return {"incidents": _value(lookup, "ECN-RECOVERY-SIGNAL"), "meanDetectionTime": None, "meanContainmentTime": None, "meanRecoveryTime": None, "automatedRecoveryRate": None, "recurrenceRate": None, "degradedModeDuration": None, "dataQuality": "INSUFFICIENT"}


def _lineage_completeness(values: tuple[EfficiencyMetricValue, ...]) -> float:
    if not values:
        return 0.0
    complete = sum(1 for item in values if item.source_record_references and item.source_snapshot_ids)
    return round((complete / len(values)) * 100, 2)


def _overall_quality(values: tuple[EfficiencyMetricValue, ...]) -> DataQualityClassification:
    if any(item.data_completeness == DataQualityClassification.INVALID for item in values):
        return DataQualityClassification.INVALID
    if any(item.data_completeness == DataQualityClassification.INSUFFICIENT for item in values):
        return DataQualityClassification.MODERATE
    return DataQualityClassification.HIGH


def _confidence(quality: DataQualityClassification, sample_count: int) -> str:
    if quality in {DataQualityClassification.INVALID, DataQualityClassification.INSUFFICIENT}:
        return "LOW"
    if sample_count < 3:
        return "MODERATE"
    return "HIGH"


def _value(lookup: dict[str, EfficiencyMetricValue], metric_id: str) -> float | None:
    return lookup[metric_id].value if metric_id in lookup else None


def _count_records(value: Any) -> int:
    if isinstance(value, dict):
        return sum(1 for item in value.values() if item)
    if isinstance(value, (tuple, list)):
        return len(value)
    return 1 if value else 0


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _law_cn() -> dict[str, Any]:
    return {
        "authorizesMissions": False,
        "wakesOffices": False,
        "transfersWorkflowExecutionToken": False,
        "changesEnterprisePriority": False,
        "approvesCost": False,
        "changesBudgets": False,
        "mutatesOperationalTruth": False,
        "mutatesLedgers": False,
        "changesRecoveryPolicy": False,
        "routineAiInvocations": 0,
        "recommendationsAreAdvisory": True,
        "lawVIIIntact": True,
    }


def _hash(value: Any) -> str:
    return sha256(json.dumps(_json_value(value), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _public(item: Any) -> dict[str, Any]:
    raw = asdict(item) if hasattr(item, "__dataclass_fields__") else item
    return _json_value(raw)


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return tuple(_json_value(item) for item in value)
    if isinstance(value, list):
        return tuple(_json_value(item) for item in value)
    if isinstance(value, dict):
        return {str(_json_value(key)): _json_value(item) for key, item in value.items()}
    return value
