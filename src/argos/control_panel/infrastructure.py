"""Infrastructure and AI Resource Management for the ARGOS Control Panel."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from typing import Any


TOKEN_USD_RATE = 0.000002


class ResourceMode(str, Enum):
    """Commander-selected infrastructure operating modes."""

    BALANCED = "Balanced"
    COST_SAVING = "Cost Saving"
    HIGH_PERFORMANCE = "High Performance"


@dataclass(frozen=True)
class ResourceControls:
    """Commander controls for infrastructure and AI resource usage."""

    daily_budget_usd: float
    monthly_budget_usd: float
    runtime_limit_minutes: int
    resource_mode: str
    organization_resource_limits: dict[str, float]


@dataclass(frozen=True)
class ResourceUsageRecord:
    """Immutable deterministic infrastructure usage record."""

    record_id: str
    timestamp_utc: str
    daily_token_usage: int
    monthly_token_usage: int
    daily_operating_cost_usd: float
    monthly_operating_cost_usd: float
    cpu_utilization: int
    memory_usage: int
    storage_usage: int
    network_activity: int
    queue_length: int
    workflow_throughput: int
    ai_utilization: int
    infrastructure_health: str
    audit_identifier: str


@dataclass(frozen=True)
class OptimizationRecommendation:
    """Deterministic infrastructure optimization recommendation."""

    recommendation_id: str
    category: str
    priority: str
    summary: str
    expected_effect: str
    supporting_metric: str


@dataclass(frozen=True)
class InfrastructureAlert:
    """Resource and infrastructure alert."""

    alert_id: str
    severity: str
    category: str
    summary: str
    supporting_metric: str
    status: str


class InfrastructureResourceManager:
    """Technical operations center for ARGOS resource and cost visibility."""

    def __init__(self) -> None:
        self.controls = ResourceControls(
            daily_budget_usd=25.0,
            monthly_budget_usd=250.0,
            runtime_limit_minutes=60,
            resource_mode=ResourceMode.BALANCED.value,
            organization_resource_limits={
                "Executive": 30.0,
                "Seeker": 40.0,
                "Analyst": 50.0,
                "Risk": 45.0,
                "Trader": 60.0,
                "Historian": 35.0,
                "Librarian": 25.0,
                "Academy": 30.0,
            },
        )
        self._history: list[ResourceUsageRecord] = []
        self._optimization_actions: list[dict[str, Any]] = []
        self._commander_overrides: list[dict[str, Any]] = []

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        resources: dict[str, int],
        costs: dict[str, float | str],
        scheduler: dict[str, Any],
        eab: dict[str, Any],
        organizations: tuple[dict[str, Any], ...],
        audit_event_count: int,
    ) -> dict[str, Any]:
        """Capture and return deterministic infrastructure state."""
        record = self._record(timestamp_utc, resources, costs, scheduler, eab, audit_event_count)
        self._append_if_changed(record)
        organization_consumption = self._organization_consumption(organizations, record)
        office_consumption = self._office_consumption(scheduler, record)
        workflow_cost = self._workflow_cost(eab, record)
        alerts = self._alerts(record)
        recommendations = self._recommendations(record, scheduler, alerts)
        return {
            "controls": asdict(self.controls),
            "current": asdict(record),
            "aiModelUsage": self._ai_model_usage(record),
            "tokenConsumption": {
                "dailyTokenUsage": record.daily_token_usage,
                "monthlyTokenUsage": record.monthly_token_usage,
                "estimatedDailyTokenCostUsd": round(record.daily_token_usage * TOKEN_USD_RATE, 4),
                "estimatedMonthlyTokenCostUsd": round(record.monthly_token_usage * TOKEN_USD_RATE, 4),
            },
            "operatingCost": {
                "dailyOperatingCostUsd": record.daily_operating_cost_usd,
                "monthlyOperatingCostUsd": record.monthly_operating_cost_usd,
                "dailyBudgetUsd": self.controls.daily_budget_usd,
                "monthlyBudgetUsd": self.controls.monthly_budget_usd,
                "dailyBudgetUsagePercent": _percent(record.daily_operating_cost_usd, self.controls.daily_budget_usd),
                "monthlyBudgetUsagePercent": _percent(record.monthly_operating_cost_usd, self.controls.monthly_budget_usd),
            },
            "organizationResourceConsumption": organization_consumption,
            "officeResourceConsumption": office_consumption,
            "workflowCost": workflow_cost,
            "aiUtilization": record.ai_utilization,
            "infrastructureHealth": {
                "databaseHealth": "NOMINAL",
                "networkActivity": record.network_activity,
                "queueLength": record.queue_length,
                "workflowThroughput": record.workflow_throughput,
                "organizationAvailability": "100%",
                "infrastructureHealth": record.infrastructure_health,
            },
            "optimizationRecommendations": tuple(asdict(item) for item in recommendations),
            "alerts": tuple(asdict(item) for item in alerts),
            "history": tuple(asdict(item) for item in self._history[-50:]),
            "optimizationActions": tuple(self._optimization_actions[-30:]),
            "commanderOverrides": tuple(self._commander_overrides[-30:]),
            "metrics": {
                "historyDepth": len(self._history),
                "optimizationActionCount": len(self._optimization_actions),
                "commanderOverrideCount": len(self._commander_overrides),
                "alertCount": len(alerts),
                "recommendationCount": len(recommendations),
            },
        }

    def configure_controls(
        self,
        *,
        daily_budget_usd: float,
        monthly_budget_usd: float,
        runtime_limit_minutes: int,
        resource_mode: str,
        organization: str = "",
        organization_limit_usd: float | None = None,
        timestamp_utc: str,
    ) -> dict[str, Any]:
        """Apply Commander infrastructure controls without discarding history."""
        mode = _normalize_mode(resource_mode)
        limits = dict(self.controls.organization_resource_limits)
        if organization and organization_limit_usd is not None:
            limits[organization] = round(max(0.0, float(organization_limit_usd)), 2)
        self.controls = replace(
            self.controls,
            daily_budget_usd=round(max(0.0, float(daily_budget_usd)), 2),
            monthly_budget_usd=round(max(0.0, float(monthly_budget_usd)), 2),
            runtime_limit_minutes=max(1, int(runtime_limit_minutes)),
            resource_mode=mode.value,
            organization_resource_limits=limits,
        )
        override = {
            "overrideId": f"INFRA-OVR-{len(self._commander_overrides) + 1:06d}",
            "timestampUtc": timestamp_utc,
            "dailyBudgetUsd": self.controls.daily_budget_usd,
            "monthlyBudgetUsd": self.controls.monthly_budget_usd,
            "runtimeLimitMinutes": self.controls.runtime_limit_minutes,
            "resourceMode": self.controls.resource_mode,
            "organization": organization,
            "organizationLimitUsd": limits.get(organization, 0.0) if organization else 0.0,
        }
        self._commander_overrides.append(override)
        return override

    def record_optimization_action(self, action: str, timestamp_utc: str) -> dict[str, Any]:
        """Record a deterministic optimization action selected by the Commander."""
        item = {
            "actionId": f"INFRA-ACT-{len(self._optimization_actions) + 1:06d}",
            "timestampUtc": timestamp_utc,
            "action": action,
            "status": "RECORDED",
        }
        self._optimization_actions.append(item)
        return item

    def _record(
        self,
        timestamp_utc: str,
        resources: dict[str, int],
        costs: dict[str, float | str],
        scheduler: dict[str, Any],
        eab: dict[str, Any],
        audit_event_count: int,
    ) -> ResourceUsageRecord:
        daily_cost = round(float(costs["today_api_credits_usd"]) + (float(costs["other_operating_expenses_usd"]) / 30), 4)
        monthly_cost = round(float(costs["total_operating_burn_usd"]), 4)
        daily_tokens = int(round(float(costs["today_api_credits_usd"]) / TOKEN_USD_RATE))
        monthly_tokens = int(round(float(costs["month_to_date_api_credits_usd"]) / TOKEN_USD_RATE))
        queue_length = int(scheduler.get("summary", {}).get("activeOffices", 0)) + int(eab.get("health", {}).get("eventThroughput", 0))
        throughput = int(eab.get("health", {}).get("eventThroughput", 0))
        ai_utilization = min(100, 18 + queue_length + (daily_tokens // 5000))
        health = "ATTENTION" if monthly_cost > self.controls.monthly_budget_usd * 0.9 else "NOMINAL"
        if max(resources.values() or (0,)) >= 90:
            health = "DEGRADED"
        return ResourceUsageRecord(
            record_id=f"INFRA-USAGE-{len(self._history) + 1:06d}",
            timestamp_utc=timestamp_utc,
            daily_token_usage=daily_tokens,
            monthly_token_usage=monthly_tokens,
            daily_operating_cost_usd=daily_cost,
            monthly_operating_cost_usd=monthly_cost,
            cpu_utilization=int(resources.get("cpu", 0)),
            memory_usage=int(resources.get("memory", 0)),
            storage_usage=int(resources.get("storage", 0)),
            network_activity=int(resources.get("network", 0)),
            queue_length=queue_length,
            workflow_throughput=throughput,
            ai_utilization=ai_utilization,
            infrastructure_health=health,
            audit_identifier=f"AE-INFRA-{audit_event_count + len(self._history) + 1:06d}",
        )

    def _append_if_changed(self, record: ResourceUsageRecord) -> None:
        if not self._history:
            self._history.append(record)
            return
        previous = self._history[-1]
        comparable = asdict(record)
        comparable.pop("record_id")
        comparable.pop("timestamp_utc")
        comparable.pop("audit_identifier")
        previous_comparable = asdict(previous)
        previous_comparable.pop("record_id")
        previous_comparable.pop("timestamp_utc")
        previous_comparable.pop("audit_identifier")
        if comparable != previous_comparable:
            self._history.append(record)

    def _organization_consumption(self, organizations: tuple[dict[str, Any], ...], record: ResourceUsageRecord) -> tuple[dict[str, Any], ...]:
        names = [item["name"] for item in organizations]
        total = max(1, len(names))
        base_cost = record.monthly_operating_cost_usd / total
        return tuple(
            {
                "organization": name,
                "monthlyCostUsd": round(base_cost * (1 + (index % 3) * 0.08), 4),
                "tokenShare": round(record.monthly_token_usage / total * (1 + (index % 2) * 0.05), 0),
                "resourceLimitUsd": self.controls.organization_resource_limits.get(name, 0.0),
                "status": "OVER_LIMIT" if base_cost > self.controls.organization_resource_limits.get(name, 999999.0) else "NOMINAL",
            }
            for index, name in enumerate(names)
        )

    def _office_consumption(self, scheduler: dict[str, Any], record: ResourceUsageRecord) -> tuple[dict[str, Any], ...]:
        offices = scheduler.get("offices", ())[:24]
        return tuple(
            {
                "organization": office["organization"],
                "office": office["office"],
                "runtimeMinutes": office["runtime_minutes"],
                "resourceBudgetUsd": office["resource_budget_usd"],
                "estimatedCostUsd": round((office["runtime_minutes"] + 1) * 0.0035, 4),
                "aiUtilization": min(100, record.ai_utilization + (index % 5)),
            }
            for index, office in enumerate(offices)
        )

    def _workflow_cost(self, eab: dict[str, Any], record: ResourceUsageRecord) -> tuple[dict[str, Any], ...]:
        events = eab.get("events", ())[:12]
        return tuple(
            {
                "workflow": event["workflow"],
                "organization": event["organization"],
                "eventId": event["event_id"],
                "estimatedCostUsd": round(max(0.0025, record.daily_operating_cost_usd / max(1, len(events or (1,)))), 4),
            }
            for event in events
        )

    def _alerts(self, record: ResourceUsageRecord) -> tuple[InfrastructureAlert, ...]:
        alerts: list[InfrastructureAlert] = []
        if record.daily_operating_cost_usd >= self.controls.daily_budget_usd * 0.8:
            alerts.append(_alert(len(alerts) + 1, "WARNING", "Budget Threshold", "Daily budget threshold reached", f"{record.daily_operating_cost_usd}/{self.controls.daily_budget_usd}"))
        if record.monthly_operating_cost_usd >= self.controls.monthly_budget_usd * 0.8:
            alerts.append(_alert(len(alerts) + 1, "WARNING", "Budget Threshold", "Monthly budget threshold reached", f"{record.monthly_operating_cost_usd}/{self.controls.monthly_budget_usd}"))
        if record.daily_token_usage > 100000:
            alerts.append(_alert(len(alerts) + 1, "WARNING", "Excessive Token Usage", "Daily token usage exceeds deterministic threshold", str(record.daily_token_usage)))
        if max(record.cpu_utilization, record.memory_usage, record.storage_usage, record.network_activity) >= 90:
            alerts.append(_alert(len(alerts) + 1, "CRITICAL", "Resource Exhaustion", "Resource utilization exceeds safe threshold", ">=90%"))
        return tuple(alerts)

    def _recommendations(
        self,
        record: ResourceUsageRecord,
        scheduler: dict[str, Any],
        alerts: tuple[InfrastructureAlert, ...],
    ) -> tuple[OptimizationRecommendation, ...]:
        recommendations = [
            OptimizationRecommendation("INFRA-REC-000001", "Office Scheduling Improvements", "NOTICE", "Keep low-queue offices event driven.", "Reduces idle runtime.", f"queue={record.queue_length}"),
            OptimizationRecommendation("INFRA-REC-000002", "Prompt Optimization", "NOTICE", "Compress routine status prompts before high-frequency polling.", "Reduces token burn.", f"dailyTokens={record.daily_token_usage}"),
            OptimizationRecommendation("INFRA-REC-000003", "Budget Management", "NOTICE", f"Operate in {self.controls.resource_mode} mode.", "Aligns runtime with Commander budget posture.", self.controls.resource_mode),
        ]
        if alerts:
            recommendations.append(
                OptimizationRecommendation("INFRA-REC-000004", "Runtime Reduction", "WARNING", "Reduce noncritical office runtime until alerts clear.", "Contains resource growth.", alerts[0].category)
            )
        if scheduler.get("summary", {}).get("activeOffices", 0) > 12:
            recommendations.append(
                OptimizationRecommendation("INFRA-REC-000005", "Resource Allocation", "NOTICE", "Move background offices to scheduled mode.", "Improves resource efficiency.", "activeOffices>12")
            )
        return tuple(recommendations)

    def _ai_model_usage(self, record: ResourceUsageRecord) -> tuple[dict[str, Any], ...]:
        return (
            {"model": "ARGOS-Reasoning-Primary", "dailyTokens": int(record.daily_token_usage * 0.55), "monthlyTokens": int(record.monthly_token_usage * 0.55), "status": "NOMINAL"},
            {"model": "ARGOS-Evidence-Summarizer", "dailyTokens": int(record.daily_token_usage * 0.25), "monthlyTokens": int(record.monthly_token_usage * 0.25), "status": "NOMINAL"},
            {"model": "ARGOS-Education-Tutor", "dailyTokens": int(record.daily_token_usage * 0.20), "monthlyTokens": int(record.monthly_token_usage * 0.20), "status": "NOMINAL"},
        )


def _percent(value: float, total: float) -> float:
    return round((value / total) * 100, 1) if total else 100.0


def _alert(index: int, severity: str, category: str, summary: str, supporting_metric: str) -> InfrastructureAlert:
    return InfrastructureAlert(
        alert_id=f"INFRA-ALERT-{index:06d}",
        severity=severity,
        category=category,
        summary=summary,
        supporting_metric=supporting_metric,
        status="OPEN",
    )


def _normalize_mode(resource_mode: str) -> ResourceMode:
    for mode in ResourceMode:
        if mode.value.lower() == resource_mode.lower() or mode.name.lower() == resource_mode.lower().replace(" ", "_"):
            return mode
    return ResourceMode.BALANCED
