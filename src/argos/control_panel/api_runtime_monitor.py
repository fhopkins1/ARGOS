"""API Runtime Monitor for the ARGOS Control Panel."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from typing import Any

from argos.foundation.contracts import utc_timestamp


class RuntimeState(str, Enum):
    """Deterministic API-consuming runtime states."""

    DORMANT = "Dormant"
    SLEEPING = "Sleeping"
    STANDBY = "Standby"
    RUNNING = "Running"
    WAITING = "Waiting"
    BLOCKED = "Blocked"
    ERRORED = "Errored"
    TERMINATED = "Terminated"


VALID_AI_WAKE_TRIGGERS = {
    "Trade candidate generated",
    "Risk threshold crossed",
    "Position anomaly detected",
    "Executive approval required",
    "Unusual market event detected",
    "Commander-requested explanation",
}


@dataclass(frozen=True)
class RuntimeEntity:
    """Visible API-consuming runtime entity."""

    entity_id: str
    entity_name: str
    organization: str
    office: str
    current_state: str
    operating_mode: str
    current_task: str
    trigger_source: str
    trigger_event: str
    predecessor_office: str
    downstream_target: str
    start_time_utc: str
    last_activity_time_utc: str
    runtime_duration_seconds: int
    maximum_runtime_seconds: int
    api_calls_this_task: int
    tokens_this_task: int
    cost_this_task_usd: float
    cost_today_usd: float
    budget_remaining_usd: float
    expected_output: str
    sleep_condition: str
    audit_identifier: str
    activation_id: str


@dataclass(frozen=True)
class ApiCallRecord:
    """Deterministic API call log entry."""

    call_id: str
    timestamp_utc: str
    model: str
    organization: str
    office: str
    workflow: str
    workflow_id: str
    workflow_token_id: str
    usage_classification: str
    execution_mode: str
    provider: str
    validation_status: str
    fallback_used: bool
    task_identifier: str
    trigger_source: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    runtime_ms: int
    output_summary: str
    downstream_activations: tuple[str, ...]
    audit_identifier: str


@dataclass(frozen=True)
class RuntimeAlert:
    """API runtime safety alert."""

    alert_id: str
    category: str
    severity: str
    summary: str
    evidence: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class ActivationTrace:
    """Visible activation chain."""

    trace_id: str
    chain: tuple[str, ...]
    latest_activation_id: str
    status: str
    audit_identifier: str


@dataclass(frozen=True)
class RuntimeControlRecord:
    """Commander control action for API runtime management."""

    control_id: str
    action: str
    target: str
    value: str
    status: str
    timestamp_utc: str
    audit_identifier: str


class ApiRuntimeMonitor:
    """Visible runtime monitor for API-consuming entities and model calls."""

    def __init__(self) -> None:
        self._entities: dict[str, RuntimeEntity] = _baseline_entities()
        self._office_totals_usd: dict[str, float] = {entity.office: 0.0 for entity in self._entities.values()}
        self._cost_series: list[dict[str, Any]] = []
        self._api_calls: list[ApiCallRecord] = []
        self._alerts: list[RuntimeAlert] = []
        self._traces: list[ActivationTrace] = []
        self._controls: list[RuntimeControlRecord] = []
        self._blocked_offices: set[str] = set()
        self._runtime_limits: dict[str, int] = {}
        self._task_budgets: dict[str, float] = {}
        self._low_cost_mode = False
        self._paper_trading_safe_mode = True
        self._approved_continuations: set[str] = set()
        self._denied_continuations: set[str] = set()

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        costs: dict[str, Any],
        credit_governor: dict[str, Any],
        paper_trading_active: bool,
        audit_event_count: int,
    ) -> dict[str, Any]:
        """Return current visible API runtime state."""
        has_logged_calls = bool(self._api_calls)
        entities_source = self._entities if has_logged_calls else _baseline_entities()
        entities = tuple(asdict(item) for item in sorted(entities_source.values(), key=lambda entity: entity.entity_id))
        active = tuple(item for item in entities if item["current_state"] == RuntimeState.RUNNING.value)
        sleeping = tuple(item for item in entities if item["current_state"] in {RuntimeState.SLEEPING.value, RuntimeState.DORMANT.value, RuntimeState.STANDBY.value})
        blocked = tuple(item for item in entities if item["current_state"] == RuntimeState.BLOCKED.value)
        session_cost = sum(item.estimated_cost_usd for item in self._api_calls) if has_logged_calls else 0.0
        today_cost = float(costs.get("today_api_credits_usd", 0.0))
        month_cost = float(costs.get("month_to_date_api_credits_usd", 0.0))
        office_totals = self._office_totals_usd if has_logged_calls else {entity.office: 0.0 for entity in entities_source.values()}
        cost_series = self._cost_series[-60:] if has_logged_calls else ()
        return {
            "usageClassification": {
                "realApiUsage": "Provider API calls recorded only through the API Execution Gateway real_api_pilot path.",
                "dryRunApiUsage": "Gateway dry-run credit proof and deterministic placeholders; no external provider call.",
                "simulatedPaperTradingTelemetry": "Paper trading status and portfolio simulation; does not create API spend.",
                "workflowTokenAuthorizedApiUsage": "Requires workflow_id, workflow_token_id, office, Executing workflow status, token ownership, and remaining budget.",
            },
            "entities": entities,
            "activeApiEntities": active,
            "sleepingApiEntities": sleeping,
            "blockedApiEntities": blocked,
            "currentCostBurnRateUsdPerHour": round(sum(entity.cost_this_task_usd for entity in entities_source.values() if entity.current_state == RuntimeState.RUNNING.value) * 12, 4),
            "costThisSessionUsd": round(session_cost, 4),
            "costTodayUsd": round(today_cost, 4),
            "costThisMonthUsd": round(month_cost, 4),
            "officeCostTotalsUsd": dict(sorted(office_totals.items())),
            "officeCostSeries": tuple(cost_series),
            "activeActivationChains": tuple(asdict(item) for item in self._traces[-20:]) if has_logged_calls else (),
            "recentApiCalls": tuple(asdict(item) for item in reversed(self._api_calls[-30:])),
            "loopDetectionAlerts": tuple(asdict(item) for item in self._alerts if item.category == "Recursive Activation") if has_logged_calls else (),
            "runtimeAlerts": tuple(asdict(item) for item in self._alerts[-30:]),
            "budgetStops": tuple(item for item in credit_governor.get("detections", ()) if item.get("category") == "Budget Overrun") if has_logged_calls else (),
            "controls": tuple(asdict(item) for item in reversed(self._controls[-20:])),
            "configuration": {
                "lowCostMode": self._low_cost_mode,
                "paperTradingSafeMode": self._paper_trading_safe_mode,
                "blockedOffices": tuple(sorted(self._blocked_offices)),
                "runtimeLimits": dict(self._runtime_limits),
                "taskBudgets": dict(self._task_budgets),
                "validAiWakeTriggers": tuple(sorted(VALID_AI_WAKE_TRIGGERS)),
            },
            "metrics": {
                "activeCount": len(active),
                "sleepingCount": len(sleeping),
                "blockedCount": len(blocked),
                "apiCallsLogged": len(self._api_calls),
                "realApiCallsLogged": sum(1 for item in self._api_calls if item.execution_mode == "real_api_pilot"),
                "dryRunApiCallsLogged": sum(1 for item in self._api_calls if item.execution_mode == "dry_run"),
                "totalTokensLogged": sum(item.total_tokens for item in self._api_calls),
                "estimatedCostLoggedUsd": round(sum(item.estimated_cost_usd for item in self._api_calls), 4),
                "realApiCostLoggedUsd": round(sum(item.estimated_cost_usd for item in self._api_calls if item.execution_mode == "real_api_pilot"), 4),
                "dryRunCostLoggedUsd": round(sum(item.estimated_cost_usd for item in self._api_calls if item.execution_mode == "dry_run"), 4),
                "alertCount": len(self._alerts),
                "auditReference": f"AE-API-RUNTIME-{audit_event_count + len(self._api_calls) + 1:06d}",
                "lastUpdatedUtc": timestamp_utc,
            },
        }

    def register_activation(self, activation: Any, timestamp_utc: str) -> None:
        """Represent a credit-governed activation as a visible runtime entity."""
        if not getattr(activation, "workflow_id", "") or not getattr(activation, "workflow_token_id", "") or not getattr(activation, "receiving_office", ""):
            self.record_law_vii_violation(
                "LAW_VII_VIOLATION_UNSCOPED_API_USAGE",
                "API runtime activation was blocked because workflow_id, workflow_token_id, or office was missing.",
                (getattr(activation, "activation_id", ""), getattr(activation, "receiving_office", "")),
            )
            return
        if getattr(activation, "law_vii_validation", "") != "LAW_VII_API_USAGE_AUTHORIZED":
            self.record_law_vii_violation(
                activation.law_vii_validation,
                activation.reason,
                (activation.activation_id, activation.workflow_id, activation.receiving_office),
            )
            return
        key = _entity_key(activation.organization, activation.receiving_office)
        baseline = self._entities.get(key) or _entity(
            len(self._entities) + 1,
            activation.organization,
            activation.receiving_office,
            RuntimeState.DORMANT,
        )
        state = RuntimeState.RUNNING if activation.status == "APPROVED" else RuntimeState.BLOCKED
        if activation.receiving_office in self._blocked_offices:
            state = RuntimeState.BLOCKED
        maximum_runtime_seconds = self._runtime_limits.get(activation.receiving_office, activation.maximum_runtime_minutes * 60)
        cost = round(float(activation.maximum_credit_budget_usd) if state == RuntimeState.RUNNING else 0.0, 4)
        tokens = _tokens_for_budget(cost) if state == RuntimeState.RUNNING else 0
        entity = replace(
            baseline,
            current_state=state.value,
            operating_mode="Event Driven",
            current_task=activation.task_identifier,
            trigger_source=activation.activating_source,
            trigger_event=_trigger_event(activation.purpose),
            predecessor_office=activation.activating_source,
            downstream_target=activation.return_route,
            start_time_utc=timestamp_utc,
            last_activity_time_utc=timestamp_utc,
            runtime_duration_seconds=0,
            maximum_runtime_seconds=maximum_runtime_seconds,
            api_calls_this_task=1 if state == RuntimeState.RUNNING else 0,
            tokens_this_task=tokens,
            cost_this_task_usd=cost,
            cost_today_usd=cost,
            budget_remaining_usd=round(max(0.0, activation.maximum_credit_budget_usd - cost), 4),
            expected_output=activation.required_output,
            sleep_condition="Structured result emitted or Commander termination",
            audit_identifier=activation.audit_identifier,
            activation_id=activation.activation_id,
        )
        self._entities[key] = entity
        self._append_trace(activation)
        if state == RuntimeState.RUNNING:
            self.record_office_usage(activation.organization, activation.receiving_office, cost, timestamp_utc)
            self._api_calls.append(_api_call(len(self._api_calls) + 1, activation, tokens, cost, timestamp_utc))
            self._detect_runtime_conditions(False)
        else:
            self._append_alert("Unauthorized API Activation", "WARNING", activation.reason, (activation.activation_id, activation.receiving_office))

    def record_office_usage(self, organization: str, office: str, amount_usd: float, timestamp_utc: str) -> None:
        """Add deterministic API spend to one office running total."""
        del organization
        amount = round(max(0.0, float(amount_usd)), 4)
        if office not in self._office_totals_usd:
            self._office_totals_usd[office] = 0.0
        self._office_totals_usd[office] = round(self._office_totals_usd[office] + amount, 4)
        if amount:
            self._append_cost_sample(timestamp_utc)

    def record_law_vii_violation(self, code: str, summary: str, evidence: tuple[str, ...]) -> None:
        """Record a blocked API accounting attempt without adding usage."""
        self._append_alert(code, "CRITICAL", summary, evidence)

    def complete_activation(self, activation_id: str, timestamp_utc: str) -> None:
        """Return a visible runtime entity to sleep after completion."""
        for key, entity in tuple(self._entities.items()):
            if entity.activation_id == activation_id:
                self._entities[key] = replace(
                    entity,
                    current_state=RuntimeState.SLEEPING.value,
                    last_activity_time_utc=timestamp_utc,
                    sleep_condition="Structured result emitted; office returned to dormancy.",
                )
                return

    def control(self, action: str, target: str, value: str = "") -> RuntimeControlRecord:
        """Apply Commander runtime controls."""
        normalized = action.strip().lower().replace("-", "_").replace(" ", "_")
        timestamp = utc_timestamp()
        status = "APPLIED"
        if normalized == "terminate_api_process":
            self._set_entity_state(target, RuntimeState.TERMINATED, timestamp)
        elif normalized == "pause_office":
            self._set_entity_state(target, RuntimeState.WAITING, timestamp)
        elif normalized == "force_sleep":
            self._set_entity_state(target, RuntimeState.SLEEPING, timestamp)
        elif normalized == "block_office_activation":
            self._blocked_offices.add(target)
            self._set_entity_state(target, RuntimeState.BLOCKED, timestamp)
        elif normalized == "approve_continuation":
            self._approved_continuations.add(target)
        elif normalized == "deny_continuation":
            self._denied_continuations.add(target)
            self._set_entity_state(target, RuntimeState.TERMINATED, timestamp)
        elif normalized == "set_runtime_limit":
            self._runtime_limits[target] = max(1, int(float(value or 60))) * 60
        elif normalized == "set_task_budget":
            self._task_budgets[target] = round(max(0.0, float(value or 0)), 4)
        elif normalized == "enable_low_cost_mode":
            self._low_cost_mode = True
        elif normalized == "enable_paper_trading_safe_mode":
            self._paper_trading_safe_mode = True
        elif normalized == "inspect_activation_trace":
            status = "INSPECTED"
        else:
            status = "REJECTED"
        record = RuntimeControlRecord(
            control_id=f"ARM-CTRL-{len(self._controls) + 1:06d}",
            action=normalized,
            target=target,
            value=value,
            status=status,
            timestamp_utc=timestamp,
            audit_identifier=f"AE-API-RUNTIME-CTRL-{len(self._controls) + 1:06d}",
        )
        self._controls.append(record)
        return record

    def reset_session(self) -> RuntimeControlRecord:
        """Clear volatile API runtime session state without erasing audit records."""
        timestamp = utc_timestamp()
        self._entities = _baseline_entities()
        self._office_totals_usd = {entity.office: 0.0 for entity in self._entities.values()}
        self._cost_series = []
        self._api_calls = []
        self._alerts = []
        self._traces = []
        self._blocked_offices = set()
        self._approved_continuations = set()
        self._denied_continuations = set()
        record = RuntimeControlRecord(
            control_id=f"ARM-CTRL-{len(self._controls) + 1:06d}",
            action="reset_session",
            target="API Runtime Monitor",
            value="",
            status="APPLIED",
            timestamp_utc=timestamp,
            audit_identifier=f"AE-API-RUNTIME-CTRL-{len(self._controls) + 1:06d}",
        )
        self._controls.append(record)
        return record

    def _tick_active_entities(self, timestamp_utc: str) -> None:
        for key, entity in tuple(self._entities.items()):
            if entity.current_state != RuntimeState.RUNNING.value:
                continue
            updated = replace(
                entity,
                runtime_duration_seconds=entity.runtime_duration_seconds + 5,
                last_activity_time_utc=timestamp_utc,
            )
            self._entities[key] = updated
            if updated.runtime_duration_seconds > updated.maximum_runtime_seconds:
                self._entities[key] = replace(updated, current_state=RuntimeState.TERMINATED.value)
                self._append_alert("Long-Running Process", "CRITICAL", "Maximum runtime exceeded; runtime terminated.", (updated.entity_id, updated.current_task))

    def _detect_runtime_conditions(self, paper_trading_active: bool) -> None:
        active = [entity for entity in self._entities.values() if entity.current_state == RuntimeState.RUNNING.value]
        signatures: dict[tuple[str, str, str], int] = {}
        for trace in self._traces[-12:]:
            signature = tuple(trace.chain)
            signatures[signature] = signatures.get(signature, 0) + 1
            if signatures[signature] > 1 and trace.latest_activation_id not in self._approved_continuations:
                self._append_alert("Recursive Activation", "CRITICAL", "Activation chain repeated without Commander approval or new evidence.", (trace.trace_id, trace.latest_activation_id))
        for entity in active:
            if not entity.trigger_source:
                self._append_alert("Missing Trigger Source", "WARNING", "API entity is running without a trigger source.", (entity.entity_id,))
            if not entity.sleep_condition:
                self._append_alert("Missing Sleep Condition", "WARNING", "API entity is running without a sleep condition.", (entity.entity_id,))
            if paper_trading_active and self._paper_trading_safe_mode and entity.trigger_event not in VALID_AI_WAKE_TRIGGERS:
                self._entities[_entity_key(entity.organization, entity.office)] = replace(entity, current_state=RuntimeState.TERMINATED.value)
                self._append_alert("Paper Trading Overactivation", "CRITICAL", "Paper trading API reasoning lacked deterministic threshold validation.", (entity.entity_id, entity.trigger_event))

    def _append_trace(self, activation: Any) -> None:
        chain = (activation.activating_source, activation.receiving_office, activation.return_route)
        self._traces.append(
            ActivationTrace(
                trace_id=f"ARM-TRACE-{len(self._traces) + 1:06d}",
                chain=chain,
                latest_activation_id=activation.activation_id,
                status=activation.status,
                audit_identifier=activation.audit_identifier,
            )
        )

    def _append_alert(self, category: str, severity: str, summary: str, evidence: tuple[str, ...]) -> None:
        signature = (category, summary, evidence)
        for alert in self._alerts:
            if (alert.category, alert.summary, alert.evidence) == signature:
                return
        self._alerts.append(
            RuntimeAlert(
                alert_id=f"ARM-ALERT-{len(self._alerts) + 1:06d}",
                category=category,
                severity=severity,
                summary=summary,
                evidence=evidence,
                status="OPEN",
            )
        )

    def _set_entity_state(self, target: str, state: RuntimeState, timestamp_utc: str) -> None:
        for key, entity in tuple(self._entities.items()):
            if target in {entity.entity_id, entity.office, entity.entity_name, entity.activation_id}:
                self._entities[key] = replace(entity, current_state=state.value, last_activity_time_utc=timestamp_utc)
                return

    def _append_cost_sample(self, timestamp_utc: str) -> None:
        sample = {
            "timestampUtc": timestamp_utc,
            "totalsUsd": dict(sorted((office, round(total, 4)) for office, total in self._office_totals_usd.items())),
        }
        if self._cost_series and self._cost_series[-1] == sample:
            return
        self._cost_series.append(sample)
        if len(self._cost_series) > 240:
            self._cost_series = self._cost_series[-240:]


def _baseline_entities() -> dict[str, RuntimeEntity]:
    offices = (
        ("Executive", "Commander"),
        ("Seeker", "Fusion Office"),
        ("Analyst", "Analytical Fusion Office"),
        ("Risk", "Risk Fusion Office"),
        ("Trader", "Trader Fusion Office"),
        ("Historian", "Historian Fusion Office"),
        ("Librarian", "Librarian Fusion Office"),
        ("Academy", "Academy Fusion Office"),
    )
    return {
        _entity_key(organization, office): _entity(index, organization, office, RuntimeState.DORMANT)
        for index, (organization, office) in enumerate(offices, 1)
    }


def _entity(index: int, organization: str, office: str, state: RuntimeState) -> RuntimeEntity:
    timestamp = utc_timestamp()
    return RuntimeEntity(
        entity_id=f"ARM-ENT-{index:06d}",
        entity_name=f"{organization} / {office}",
        organization=organization,
        office=office,
        current_state=state.value,
        operating_mode="Dormant by Default",
        current_task="",
        trigger_source="",
        trigger_event="",
        predecessor_office="",
        downstream_target="",
        start_time_utc=timestamp,
        last_activity_time_utc=timestamp,
        runtime_duration_seconds=0,
        maximum_runtime_seconds=300,
        api_calls_this_task=0,
        tokens_this_task=0,
        cost_this_task_usd=0.0,
        cost_today_usd=0.0,
        budget_remaining_usd=0.0,
        expected_output="",
        sleep_condition="Valid activation request required",
        audit_identifier=f"AE-API-RUNTIME-{index:06d}",
        activation_id="",
    )


def _api_call(index: int, activation: Any, tokens: int, cost: float, timestamp_utc: str) -> ApiCallRecord:
    prompt_tokens = round(tokens * 0.65)
    completion_tokens = max(0, tokens - prompt_tokens)
    real_pilot = activation.purpose == "Real API Pilot"
    execution_mode = "real_api_pilot" if real_pilot else "dry_run"
    provider = "openai" if real_pilot else "none"
    usage_classification = "real API usage" if real_pilot else "workflow-token-authorized dry-run API usage"
    return ApiCallRecord(
        call_id=f"ARM-CALL-{index:06d}",
        timestamp_utc=timestamp_utc,
        model="argos-real-api-pilot" if real_pilot else "argos-governed-dry-run",
        organization=activation.organization,
        office=activation.receiving_office,
        workflow=activation.workflow,
        workflow_id=activation.workflow_id,
        workflow_token_id=activation.workflow_token_id,
        usage_classification=usage_classification,
        execution_mode=execution_mode,
        provider=provider,
        validation_status=activation.law_vii_validation,
        fallback_used=False,
        task_identifier=activation.task_identifier,
        trigger_source=activation.activating_source,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=tokens,
        estimated_cost_usd=cost,
        runtime_ms=max(25, activation.maximum_runtime_minutes * 250),
        output_summary=activation.required_output,
        downstream_activations=(activation.return_route,),
        audit_identifier=activation.audit_identifier,
    )


def _entity_key(organization: str, office: str) -> str:
    return f"{organization}::{office}"


def _trigger_event(purpose: str) -> str:
    if purpose == "Commander explanation":
        return "Commander-requested explanation"
    if purpose == "Executive synthesis":
        return "Executive approval required"
    if purpose == "Conflict analysis":
        return "Risk threshold crossed"
    if purpose == "Ambiguous reasoning":
        return "Trade candidate generated"
    return "Unusual market event detected"


def _tokens_for_budget(cost: float) -> int:
    return int(round(max(0.0, cost) / 0.000015)) if cost else 0
