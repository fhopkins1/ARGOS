"""Enterprise Operations Scheduler and office wake controls for ARGOS."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, time
from enum import Enum
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .ecc import ORGANIZATION_OFFICES
from .office_duty_officer import OfficeDutyOfficerRegistry, OfficeTaskingRequest


class OperatingMode(str, Enum):
    """Legacy per-office operating modes retained for dashboard compatibility."""

    DORMANT = "Dormant"
    EVENT_DRIVEN = "Event Driven"
    SCHEDULED = "Scheduled"
    BUSINESS_HOURS = "Business Hours"
    CONTINUOUS_OPERATION = "Continuous Operation"


class EnterpriseOperatingMode(str, Enum):
    """Enterprise-wide EOS operating postures."""

    FULL_PAPER_TRADING = "Full Paper Trading"
    OBSERVATION_ONLY = "Observation Only"
    POSITION_MANAGEMENT_ONLY = "Position Management Only"
    CAPITAL_PRESERVATION = "Capital Preservation"
    STRATEGIC_RESEARCH_ONLY = "Strategic Research Only"
    MAINTENANCE = "Maintenance"
    HALTED = "Halted"


MISSION_STATUSES = (
    "Planned",
    "Queued",
    "Awaiting Trigger",
    "Awaiting Market Session",
    "Awaiting Resources",
    "Authorized",
    "Running",
    "Partially Completed",
    "Completed",
    "Completed With Warnings",
    "Suspended",
    "Cancelled",
    "Failed",
    "Aborted",
    "Expired",
)

TERMINAL_MISSION_STATUSES = {"Completed", "Completed With Warnings", "Cancelled", "Failed", "Aborted", "Expired"}

VALID_MISSION_TRANSITIONS = {
    "Planned": {"Queued", "Awaiting Trigger", "Awaiting Market Session", "Awaiting Resources", "Cancelled", "Expired"},
    "Queued": {"Authorized", "Awaiting Market Session", "Awaiting Resources", "Suspended", "Cancelled", "Expired"},
    "Awaiting Trigger": {"Queued", "Cancelled", "Expired"},
    "Awaiting Market Session": {"Queued", "Cancelled", "Expired"},
    "Awaiting Resources": {"Queued", "Cancelled", "Failed"},
    "Authorized": {"Running", "Cancelled", "Suspended", "Failed"},
    "Running": {"Partially Completed", "Completed", "Completed With Warnings", "Suspended", "Failed", "Aborted", "Expired"},
    "Partially Completed": {"Completed", "Completed With Warnings", "Failed"},
    "Completed": set(),
    "Completed With Warnings": set(),
    "Suspended": {"Queued", "Cancelled", "Aborted"},
    "Cancelled": set(),
    "Failed": set(),
    "Aborted": set(),
    "Expired": set(),
}

PRIORITY_RANK = {
    "Emergency": 1,
    "Position Safety": 2,
    "Broker and Ledger Reconciliation": 3,
    "Risk Control": 4,
    "Required Trade Lifecycle Action": 5,
    "Commander-Directed": 6,
    "Tactical Opportunity Evaluation": 7,
    "Strategic Intelligence": 8,
    "Historical Review": 9,
    "Academy and Development": 10,
}

OFFICE_OPERATING_STATES = ("Offline", "Sleeping", "Monitoring", "Ready", "Queued", "Working", "Cooldown", "Suspended", "Degraded", "Faulted")


@dataclass(frozen=True)
class EnterpriseMission:
    """Canonical bounded EOS work package."""

    mission_id: str
    mission_type: str
    mission_name: str
    description: str
    created_at: str
    scheduled_start: str
    actual_start: str
    actual_end: str
    timezone: str
    trigger_type: str
    trigger_reference: str
    commander_directive_id: str
    priority: str
    criticality: str
    required_offices: tuple[str, ...]
    optional_offices: tuple[str, ...]
    prohibited_offices: tuple[str, ...]
    workflow_type: str
    execution_token_id: str
    maximum_runtime_seconds: int
    maximum_api_cost: float
    maximum_api_calls: int
    maximum_workflows: int
    minimum_data_freshness: str
    market_session_requirement: str
    concurrency_policy: str
    retry_policy: str
    completion_policy: str
    failure_policy: str
    status: str
    result_summary: str
    cost_summary: dict[str, Any]
    audit_reference: str
    template_id: str = ""
    idempotency_key: str = ""


@dataclass(frozen=True)
class MissionTransition:
    """Immutable EOS mission state transition evidence."""

    transition_id: str
    mission_id: str
    timestamp: str
    previous_state: str
    new_state: str
    reason: str
    authorizing_actor: str
    related_event_or_directive: str
    audit_record: str


@dataclass(frozen=True)
class OfficeActivationRequest:
    """Scheduler-approved office wake request tied to a mission."""

    activation_id: str
    mission_id: str
    office_id: str
    activation_reason: str
    assigned_task: str
    required_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    priority: str
    activation_time: str
    maximum_runtime: int
    maximum_api_cost: float
    maximum_api_calls: int
    wake_state_requested: str
    completion_criteria: str
    cooldown_requirement: str
    status: str
    audit_reference: str


@dataclass(frozen=True)
class MissionTemplate:
    """Configurable initial EOS mission template."""

    template_id: str
    mission_type: str
    mission_name: str
    description: str
    suggested_time: str
    enabled_by_default: bool
    priority: str
    criticality: str
    required_offices: tuple[str, ...]
    workflow_type: str
    maximum_runtime_seconds: int
    maximum_api_cost: float
    maximum_api_calls: int
    maximum_workflows: int
    market_session_requirement: str
    concurrency_policy: str
    duplicate_exclusion_seconds: int


@dataclass(frozen=True)
class OfficeSchedule:
    """Commander-configurable schedule and resource policy for one office."""

    schedule_id: str
    organization: str
    office: str
    operating_mode: OperatingMode
    status: str
    time_zone: str
    business_hours: str
    scheduled_tasks: tuple[str, ...]
    wake_triggers: tuple[str, ...]
    sleep_triggers: tuple[str, ...]
    runtime_limit_minutes: int
    resource_budget_usd: float
    runtime_minutes: int
    cpu_usage: int
    memory_usage: int
    token_consumption: int
    queue_length: int
    wake_count: int
    last_transition_utc: str
    requested_state: str = "Sleeping"
    assigned_mission: str = ""
    activation_reason: str = ""
    cost_incurred_usd: float = 0.0
    remaining_budget_usd: float = 0.0


class EnterpriseOperationsScheduler:
    """Central mission scheduler that authorizes bounded ARGOS work."""

    def __init__(self) -> None:
        self.enabled = False
        self.operating_mode = EnterpriseOperatingMode.OBSERVATION_ONLY
        self.daily_api_budget_usd = 25.0
        self.mission_cost_ceiling_usd = 5.0
        self.strategic_research_enabled = False
        self.new_entry_trading_enabled = False
        self.position_management_only = False
        self._templates = _default_mission_templates()
        self._missions: dict[str, EnterpriseMission] = {}
        self._transitions: list[MissionTransition] = []
        self._activations: list[OfficeActivationRequest] = []
        self._suppressed: list[dict[str, Any]] = []
        self._manual_overrides: list[dict[str, Any]] = []
        self._failure_records: list[dict[str, Any]] = []
        self._recovery_records: list[dict[str, Any]] = []
        self._event_interfaces: list[dict[str, Any]] = []
        self._api_cost_used_usd = 0.0
        self._api_calls_used = 0
        self.duty_officers = OfficeDutyOfficerRegistry()

    def snapshot(self, offices: tuple[dict[str, Any], ...] = ()) -> dict[str, Any]:
        """Return the Enterprise Operations Bridge payload."""
        mission_records = tuple(asdict(mission) for mission in self._missions.values())
        ordered = tuple(sorted(self._missions.values(), key=lambda item: (_priority_rank(item.priority), item.scheduled_start or item.created_at, item.mission_id)))
        active = tuple(item for item in ordered if item.status == "Running")
        upcoming = tuple(item for item in ordered if item.status in {"Planned", "Queued", "Awaiting Trigger", "Awaiting Market Session", "Awaiting Resources", "Authorized"})
        completed = tuple(item for item in ordered if item.status in {"Completed", "Completed With Warnings"})
        failed = tuple(item for item in ordered if item.status in {"Failed", "Aborted", "Expired"})
        now = utc_timestamp()
        market = market_calendar_snapshot(now)
        costs = self._cost_monitor()
        return {
            "schedulerName": "Enterprise Operations Scheduler",
            "engineeringOrder": "EO-CA",
            "enabled": self.enabled,
            "status": "HEALTHY" if self.enabled else "DISABLED_SAFE",
            "healthy": True,
            "currentOperatingMode": self.operating_mode.value,
            "currentTime": now,
            "timezone": "America/Cancun",
            "marketCalendar": market,
            "currentMarketSession": market["current_session"],
            "nextMission": asdict(upcoming[0]) if upcoming else {},
            "lastCompletedMission": asdict(completed[-1]) if completed else {},
            "activeMissionCount": len(active),
            "missionTemplates": tuple(asdict(template) for template in self._templates.values()),
            "missionRecords": mission_records,
            "missionTimeline": {
                "upcoming": tuple(asdict(item) for item in upcoming[:8]),
                "active": tuple(asdict(item) for item in active),
                "recentlyCompleted": tuple(asdict(item) for item in completed[-8:]),
                "suspended": tuple(asdict(item) for item in ordered if item.status == "Suspended"),
                "failed": tuple(asdict(item) for item in failed[-8:]),
            },
            "activeOfficeRoster": _office_roster(offices, self._activations),
            "activationRequests": tuple(asdict(item) for item in self._activations),
            "stateTransitions": tuple(asdict(item) for item in self._transitions),
            "missionCostMonitor": costs,
            "suppressedWork": tuple(self._suppressed),
            "manualOverrides": tuple(self._manual_overrides),
            "failureRecords": tuple(self._failure_records),
            "recoveryRecords": tuple(self._recovery_records),
            "eventTriggerInterfaces": tuple(self._event_interfaces),
            "metrics": self._metrics(tuple(self._missions.values()), costs),
            "lawVII": {
                "schedulerOwnsInvestmentDecisions": False,
                "workflowExecutionTokenRequired": True,
                "singleOwnerDisciplinePreserved": True,
                "uncontrolledLoopsCreated": False,
                "officeSelfWakeAuthority": False,
            },
            "apiGatewayIntegration": {
                "missionAuthorizationContextSupported": True,
                "requiresWorkflowTokenForCognitiveWork": True,
                "rejectsUnscopedScheduledGatewayContext": True,
                "routineSchedulingUsesAi": False,
            },
            "persistence": {
                "storage": "in_memory_runtime_repository",
                "appendOnlyMissionHistory": True,
                "restartRecoveryInterface": True,
                "persistedRecordFamilies": (
                    "mission_templates",
                    "mission_instances",
                    "mission_state_transitions",
                    "activation_requests",
                    "scheduling_decisions",
                    "duplicate_suppression_records",
                    "manual_overrides",
                    "failure_records",
                    "recovery_records",
                ),
            },
            "manualControls": {
                "enableScheduler": True,
                "disableScheduler": True,
                "pauseNoncriticalMissions": True,
                "resumeScheduling": True,
                "runMissionNow": True,
                "cancelQueuedMission": True,
                "suspendActiveNoncriticalMission": True,
                "capitalPreservationMode": True,
                "maintenanceMode": True,
                "disableStrategicResearch": True,
                "disableNewEntryTrading": True,
                "positionManagementOnly": True,
                "setDailyApiBudget": True,
                "setMissionCostCeilings": True,
            },
            "officeDutyOfficers": self.duty_officers.snapshot({}, offices),
            "futureIntegrationPoints": (
                "EO-CB Office Duty Officer",
                "EO-CC Event Detection Engine",
                "EO-CD Mission Planner",
                "EO-CE Enterprise Cost Governor",
                "EO-CF Information Freshness Engine",
                "EO-CI Office Wakefulness Manager",
                "EO-CK Position Monitoring Network",
                "EO-CM Commander Mission Generator",
                "EO-CN Enterprise Efficiency Analytics",
            ),
        }

    def set_enabled(self, enabled: bool, *, actor: str = "Commander", reason: str = "") -> None:
        self.enabled = bool(enabled)
        self._manual_overrides.append(_override_record("enable_scheduler" if enabled else "disable_scheduler", actor, reason or "Commander scheduler control"))

    def set_mode(self, mode: str, *, actor: str = "Commander", reason: str = "") -> None:
        target = _enterprise_mode(mode)
        self.operating_mode = target
        self.position_management_only = target == EnterpriseOperatingMode.POSITION_MANAGEMENT_ONLY
        self.new_entry_trading_enabled = target == EnterpriseOperatingMode.FULL_PAPER_TRADING
        self.strategic_research_enabled = target == EnterpriseOperatingMode.STRATEGIC_RESEARCH_ONLY
        self._manual_overrides.append(_override_record("set_operating_mode", actor, reason or target.value, {"mode": target.value}))

    def set_budget(self, daily_api_budget_usd: float, mission_cost_ceiling_usd: float, *, actor: str = "Commander") -> None:
        self.daily_api_budget_usd = max(0.0, round(float(daily_api_budget_usd), 4))
        self.mission_cost_ceiling_usd = max(0.0, round(float(mission_cost_ceiling_usd), 4))
        self._manual_overrides.append(
            _override_record(
                "set_scheduler_budget",
                actor,
                "Commander updated EOS budget ceilings.",
                {"daily_api_budget_usd": self.daily_api_budget_usd, "mission_cost_ceiling_usd": self.mission_cost_ceiling_usd},
            )
        )

    def create_scheduled_mission(self, template_id: str, *, scheduled_start: str = "", now: str | None = None) -> EnterpriseMission:
        template = self._template(template_id)
        timestamp = now or utc_timestamp()
        scheduled = scheduled_start or _scheduled_start(timestamp, template.suggested_time)
        idempotency_key = f"scheduled::{template.template_id}::{scheduled[:10]}::{scheduled[11:16]}"
        duplicate = self._duplicate_for(idempotency_key, template.duplicate_exclusion_seconds, timestamp)
        if duplicate:
            self._suppress("duplicate_scheduled_mission", duplicate.mission_id, f"{template.template_id} already launched inside exclusion window.", timestamp)
            return duplicate
        status = self._initial_status(template.market_session_requirement, timestamp)
        mission = self._mission_from_template(template, scheduled, timestamp, "Scheduled", template.template_id, "", idempotency_key, status)
        self._missions[mission.mission_id] = mission
        self._record_transition(mission.mission_id, "", status, "Scheduled mission created.", "Enterprise Operations Scheduler", template.template_id)
        return mission

    def create_commander_directed_mission(
        self,
        *,
        mission_name: str,
        required_offices: tuple[str, ...],
        directive_id: str = "",
        priority: str = "Commander-Directed",
        maximum_api_cost: float | None = None,
        maximum_api_calls: int = 1,
        maximum_runtime_seconds: int = 300,
        workflow_type: str = "commander_directed_mission",
    ) -> EnterpriseMission:
        timestamp = utc_timestamp()
        mission = EnterpriseMission(
            mission_id=self._next_mission_id(),
            mission_type="Commander-Directed",
            mission_name=mission_name or "Commander Directed Mission",
            description="Commander-directed bounded mission authorized through EOS.",
            created_at=timestamp,
            scheduled_start=timestamp,
            actual_start="",
            actual_end="",
            timezone="America/Cancun",
            trigger_type="Commander",
            trigger_reference=directive_id,
            commander_directive_id=directive_id,
            priority=priority,
            criticality="Commander",
            required_offices=tuple(required_offices),
            optional_offices=(),
            prohibited_offices=(),
            workflow_type=workflow_type,
            execution_token_id="PENDING_WORKFLOW_EXECUTION_TOKEN",
            maximum_runtime_seconds=max(1, int(maximum_runtime_seconds)),
            maximum_api_cost=min(self.mission_cost_ceiling_usd, max(0.0, float(maximum_api_cost if maximum_api_cost is not None else self.mission_cost_ceiling_usd))),
            maximum_api_calls=max(0, int(maximum_api_calls)),
            maximum_workflows=1,
            minimum_data_freshness="PT5M",
            market_session_requirement="Any",
            concurrency_policy="Parallel Nonconflicting Offices",
            retry_policy="No automatic retry",
            completion_policy="Return all activated offices to sleep.",
            failure_policy="Suspend mission and preserve audit evidence.",
            status="Queued" if self.enabled else "Planned",
            result_summary="Awaiting EOS dispatch.",
            cost_summary={"approved_api_cost_usd": maximum_api_cost or self.mission_cost_ceiling_usd, "actual_api_cost_usd": 0.0, "api_calls": 0},
            audit_reference=f"EOS-AUDIT-{len(self._transitions) + 1:06d}",
            idempotency_key=f"commander::{directive_id or mission_name}::{timestamp}",
        )
        self._missions[mission.mission_id] = mission
        self._record_transition(mission.mission_id, "", mission.status, "Commander-directed mission created.", "Commander", directive_id)
        return mission

    def register_event_trigger(self, event_type: str, event_reference: str, required_offices: tuple[str, ...], *, priority: str = "Position Safety") -> EnterpriseMission:
        timestamp = utc_timestamp()
        self._event_interfaces.append(
            {
                "event_type": event_type,
                "event_reference": event_reference,
                "received_at": timestamp,
                "validated": bool(event_type and event_reference),
                "futureEventDetectionEngineReady": True,
            }
        )
        if not event_type or not event_reference:
            raise ValueError("event-triggered mission requires validated event_type and event_reference")
        return self.create_commander_directed_mission(
            mission_name=f"Event Mission: {event_type}",
            required_offices=required_offices,
            directive_id=event_reference,
            priority=priority,
            maximum_api_cost=1.0,
            maximum_api_calls=1,
            workflow_type="event_triggered_mission",
        )

    def authorize_mission(self, mission_id: str, *, actor: str = "Enterprise Operations Scheduler") -> EnterpriseMission:
        mission = self._mission(mission_id)
        if mission.status == "Awaiting Market Session":
            return mission
        if not self.enabled and mission.trigger_type != "Commander":
            self._suppress("scheduler_disabled", mission_id, "Scheduler is disabled; scheduled mission remains planned.", utc_timestamp())
            return mission
        if self.operating_mode == EnterpriseOperatingMode.HALTED:
            return self._transition(mission, "Suspended", "Enterprise operating mode is Halted.", actor)
        restriction = self._mode_restriction(mission)
        if restriction:
            return self._transition(mission, "Suspended", restriction, actor)
        if self._api_cost_used_usd + mission.maximum_api_cost > self.daily_api_budget_usd:
            return self._transition(mission, "Awaiting Resources", "Daily API budget unavailable for mission.", actor)
        return self._transition(mission, "Authorized", "Mission passed budget, mode, market, and duplicate checks.", actor)

    def dispatch_mission(self, mission_id: str, *, workflow_id: str = "", token_id: str = "") -> EnterpriseMission:
        mission = self.authorize_mission(mission_id)
        if mission.status != "Authorized":
            return mission
        timestamp = utc_timestamp()
        token = token_id or "PENDING_WORKFLOW_EXECUTION_TOKEN"
        mission = replace(mission, execution_token_id=token, actual_start=timestamp)
        self._missions[mission.mission_id] = mission
        mission = self._transition(mission, "Running", "Mission dispatched with bounded office activation requests.", "Enterprise Operations Scheduler", workflow_id)
        for office_id in mission.required_offices:
            self._activations.append(
                OfficeActivationRequest(
                    activation_id=f"EOS-ACT-{len(self._activations) + 1:06d}",
                    mission_id=mission.mission_id,
                    office_id=office_id,
                    activation_reason=mission.mission_name,
                    assigned_task=mission.description,
                    required_inputs=("mission_record", "workflow_execution_token"),
                    expected_outputs=("mission_result", "cost_summary", "audit_reference"),
                    priority=mission.priority,
                    activation_time=timestamp,
                    maximum_runtime=mission.maximum_runtime_seconds,
                    maximum_api_cost=round(mission.maximum_api_cost / max(1, len(mission.required_offices)), 4),
                    maximum_api_calls=max(1, mission.maximum_api_calls // max(1, len(mission.required_offices))) if mission.maximum_api_calls else 0,
                    wake_state_requested="Working",
                    completion_criteria=mission.completion_policy,
                    cooldown_requirement="Return to Sleeping unless monitoring is explicitly required.",
                    status="AUTHORIZED",
                    audit_reference=f"EOS-AUDIT-{len(self._transitions) + len(self._activations) + 1:06d}",
                )
            )
        return mission

    def complete_mission(self, mission_id: str, *, actual_api_cost: float = 0.0, api_calls: int = 0, result_summary: str = "Mission completed.") -> EnterpriseMission:
        mission = self._mission(mission_id)
        actual_cost = round(max(0.0, float(actual_api_cost)), 4)
        calls = max(0, int(api_calls))
        self._api_cost_used_usd = round(self._api_cost_used_usd + actual_cost, 4)
        self._api_calls_used += calls
        completed = replace(
            mission,
            actual_end=utc_timestamp(),
            result_summary=result_summary,
            cost_summary={
                "approved_api_cost_usd": mission.maximum_api_cost,
                "actual_api_cost_usd": actual_cost,
                "api_calls": calls,
                "budget_remaining_usd": round(max(0.0, mission.maximum_api_cost - actual_cost), 4),
            },
        )
        self._missions[mission_id] = completed
        for index, activation in enumerate(self._activations):
            if activation.mission_id == mission_id and activation.status == "AUTHORIZED":
                self._activations[index] = replace(activation, status="COMPLETED")
        return self._transition(completed, "Completed", "Mission completed; activated offices return to safe inactive state.", "Enterprise Operations Scheduler")

    def cancel_mission(self, mission_id: str, *, reason: str = "Commander cancelled queued mission.") -> EnterpriseMission:
        mission = self._mission(mission_id)
        return self._transition(mission, "Cancelled", reason, "Commander")

    def suspend_mission(self, mission_id: str, *, reason: str = "Commander suspended noncritical mission.") -> EnterpriseMission:
        mission = self._mission(mission_id)
        return self._transition(mission, "Suspended", reason, "Commander")

    def recover_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        timestamp = utc_timestamp()
        recovered = 0
        for item in snapshot.get("missionRecords", ()):
            mission = _mission_from_dict(item)
            if mission.status == "Running":
                mission = replace(mission, status="Suspended", result_summary="Suspended during restart recovery pending owner verification.")
                recovered += 1
            self._missions[mission.mission_id] = mission
        self._recovery_records.append(
            {
                "recovery_id": f"EOS-REC-{len(self._recovery_records) + 1:06d}",
                "timestamp": timestamp,
                "running_missions_suspended": recovered,
                "reason": "Restart recovery reconciled incomplete missions without duplicating work.",
            }
        )

    def gateway_authorization_context(self, mission_id: str, office_id: str, workflow_id: str) -> dict[str, Any]:
        mission = self._mission(mission_id)
        activation = next((item for item in self._activations if item.mission_id == mission_id and item.office_id == office_id), None)
        allowed = bool(activation and activation.status in {"AUTHORIZED", "COMPLETED"} and mission.status in {"Running", "Completed"})
        return {
            "mission_id": mission_id,
            "office_id": office_id,
            "workflow_id": workflow_id,
            "authorized": allowed,
            "approved_model_class": "bounded_dry_run",
            "cost_ceiling": activation.maximum_api_cost if activation else 0.0,
            "call_ceiling": activation.maximum_api_calls if activation else 0,
            "remaining_mission_budget": max(0.0, mission.maximum_api_cost - float(mission.cost_summary.get("actual_api_cost_usd", 0.0))),
        }

    def _initial_status(self, market_session_requirement: str, timestamp: str) -> str:
        if market_session_requirement not in {"Any", "Closed"} and market_calendar_snapshot(timestamp)["current_session"] not in _allowed_sessions(market_session_requirement):
            return "Awaiting Market Session"
        return "Queued" if self.enabled else "Planned"

    def _mission_from_template(
        self,
        template: MissionTemplate,
        scheduled: str,
        timestamp: str,
        trigger_type: str,
        trigger_reference: str,
        commander_directive_id: str,
        idempotency_key: str,
        status: str,
    ) -> EnterpriseMission:
        return EnterpriseMission(
            mission_id=self._next_mission_id(),
            mission_type=template.mission_type,
            mission_name=template.mission_name,
            description=template.description,
            created_at=timestamp,
            scheduled_start=scheduled,
            actual_start="",
            actual_end="",
            timezone="America/Cancun",
            trigger_type=trigger_type,
            trigger_reference=trigger_reference,
            commander_directive_id=commander_directive_id,
            priority=template.priority,
            criticality=template.criticality,
            required_offices=template.required_offices,
            optional_offices=(),
            prohibited_offices=(),
            workflow_type=template.workflow_type,
            execution_token_id="PENDING_WORKFLOW_EXECUTION_TOKEN",
            maximum_runtime_seconds=template.maximum_runtime_seconds,
            maximum_api_cost=min(self.mission_cost_ceiling_usd, template.maximum_api_cost),
            maximum_api_calls=template.maximum_api_calls,
            maximum_workflows=template.maximum_workflows,
            minimum_data_freshness="PT5M",
            market_session_requirement=template.market_session_requirement,
            concurrency_policy=template.concurrency_policy,
            retry_policy="No automatic immediate rerun",
            completion_policy="Bounded completion returns offices to sleep or monitoring.",
            failure_policy="Suspend or fail with audit evidence; never duplicate completed work.",
            status=status,
            result_summary="Awaiting EOS dispatch.",
            cost_summary={"approved_api_cost_usd": min(self.mission_cost_ceiling_usd, template.maximum_api_cost), "actual_api_cost_usd": 0.0, "api_calls": 0},
            audit_reference=f"EOS-AUDIT-{len(self._transitions) + 1:06d}",
            template_id=template.template_id,
            idempotency_key=idempotency_key,
        )

    def _transition(self, mission: EnterpriseMission, new_state: str, reason: str, actor: str, related: str = "") -> EnterpriseMission:
        if new_state not in MISSION_STATUSES:
            raise ValueError(f"unsupported mission status: {new_state}")
        if new_state != mission.status and new_state not in VALID_MISSION_TRANSITIONS[mission.status]:
            raise ValueError(f"invalid mission transition: {mission.status} -> {new_state}")
        updated = replace(mission, status=new_state)
        self._missions[mission.mission_id] = updated
        if new_state != mission.status:
            self._record_transition(mission.mission_id, mission.status, new_state, reason, actor, related or mission.trigger_reference)
        return updated

    def _record_transition(self, mission_id: str, previous: str, new: str, reason: str, actor: str, related: str = "") -> None:
        self._transitions.append(
            MissionTransition(
                transition_id=f"EOS-TRN-{len(self._transitions) + 1:06d}",
                mission_id=mission_id,
                timestamp=utc_timestamp(),
                previous_state=previous,
                new_state=new,
                reason=reason,
                authorizing_actor=actor,
                related_event_or_directive=related,
                audit_record=f"EOS-AUDIT-{len(self._transitions) + 1:06d}",
            )
        )

    def _duplicate_for(self, idempotency_key: str, exclusion_seconds: int, timestamp: str) -> EnterpriseMission | None:
        current = _parse_timestamp(timestamp)
        for mission in self._missions.values():
            if mission.idempotency_key != idempotency_key or mission.status in TERMINAL_MISSION_STATUSES:
                continue
            age = abs((current - _parse_timestamp(mission.created_at)).total_seconds())
            if age <= exclusion_seconds:
                return mission
        return None

    def _suppress(self, category: str, mission_id: str, reason: str, timestamp: str) -> None:
        record = {
            "suppression_id": f"EOS-SUP-{len(self._suppressed) + 1:06d}",
            "timestamp": timestamp,
            "category": category,
            "mission_id": mission_id,
            "reason": reason,
            "estimated_api_cost_avoided": 0.001 if "duplicate" in category else 0.0,
        }
        self._suppressed.append(record)

    def _mode_restriction(self, mission: EnterpriseMission) -> str:
        trading = any(office in {"Seeker", "Analyst", "Trader"} for office in mission.required_offices)
        discovery = "Discovery" in mission.mission_name or mission.priority == "Tactical Opportunity Evaluation"
        strategic = mission.priority == "Strategic Intelligence"
        if self.operating_mode == EnterpriseOperatingMode.MAINTENANCE and mission.priority not in {"Emergency", "Broker and Ledger Reconciliation"}:
            return "Maintenance mode allows only health checks, reconciliation, and emergency recovery."
        if self.operating_mode == EnterpriseOperatingMode.CAPITAL_PRESERVATION and mission.priority not in {"Emergency", "Position Safety", "Broker and Ledger Reconciliation", "Risk Control"}:
            return "Capital Preservation mode blocks discretionary discovery and research."
        if self.operating_mode == EnterpriseOperatingMode.POSITION_MANAGEMENT_ONLY and discovery:
            return "Position Management Only mode blocks new-entry discovery while preserving position safety."
        if self.operating_mode == EnterpriseOperatingMode.STRATEGIC_RESEARCH_ONLY and trading:
            return "Strategic Research Only mode prohibits trading missions."
        if self.operating_mode == EnterpriseOperatingMode.OBSERVATION_ONLY and ("Trader" in mission.required_offices or discovery):
            return "Observation Only mode blocks new paper orders and new-entry discovery."
        if strategic and not self.strategic_research_enabled:
            return "Strategic research missions are disabled until budget controls are explicitly configured."
        return ""

    def _cost_monitor(self) -> dict[str, Any]:
        remaining = round(max(0.0, self.daily_api_budget_usd - self._api_cost_used_usd), 4)
        return {
            "dailyBudgetUsd": self.daily_api_budget_usd,
            "missionCostCeilingUsd": self.mission_cost_ceiling_usd,
            "actualCostUsd": self._api_cost_used_usd,
            "apiCalls": self._api_calls_used,
            "remainingDailyBudgetUsd": remaining,
            "costByOffice": _cost_by_office(self._activations),
            "costByWorkflow": {},
            "estimatedCostAvoidedUsd": round(sum(float(item.get("estimated_api_cost_avoided", 0.0)) for item in self._suppressed), 4),
            "budgetExhausted": remaining <= 0,
        }

    def _metrics(self, missions: tuple[EnterpriseMission, ...], costs: dict[str, Any]) -> dict[str, Any]:
        completed = [mission for mission in missions if mission.status in {"Completed", "Completed With Warnings"}]
        failed = [mission for mission in missions if mission.status == "Failed"]
        cancelled = [mission for mission in missions if mission.status == "Cancelled"]
        active_seconds = sum(max(0, _duration_seconds(mission.actual_start, mission.actual_end)) for mission in completed)
        return {
            "missionsCreated": len(missions),
            "missionsCompleted": len(completed),
            "missionsFailed": len(failed),
            "missionsCancelled": len(cancelled),
            "missionsSuppressedAsDuplicates": sum(1 for item in self._suppressed if "duplicate" in item["category"]),
            "averageMissionRuntimeSeconds": round(active_seconds / max(1, len(completed)), 2),
            "averageMissionApiCost": round(sum(float(mission.cost_summary.get("actual_api_cost_usd", 0.0)) for mission in completed) / max(1, len(completed)), 4),
            "costByMissionType": _cost_by_mission_type(missions),
            "costByOffice": costs["costByOffice"],
            "officeWakeFrequency": len(self._activations),
            "officeActiveTime": active_seconds,
            "officeSleepingTime": max(0, len(ORGANIZATION_OFFICES) * 3600 - active_seconds),
            "schedulerUtilization": "0%" if not missions else f"{round((len(completed) / len(missions)) * 100, 1)}%",
            "workflowCountPerMission": _average_workflows(missions),
            "candidatesEvaluatedPerMission": 0,
            "positionSafetyMissionsExecuted": sum(1 for mission in completed if mission.priority == "Position Safety"),
            "marketSessionViolationsPrevented": sum(1 for mission in missions if mission.status == "Awaiting Market Session"),
            "duplicateWorkflowsPrevented": sum(1 for item in self._suppressed if "duplicate" in item["category"]),
            "budgetTerminations": sum(1 for mission in missions if mission.status == "Awaiting Resources"),
            "manualOverrides": len(self._manual_overrides),
            "recoveryEvents": len(self._recovery_records),
            "estimatedApiCostAvoided": costs["estimatedCostAvoidedUsd"],
        }

    def _template(self, template_id: str) -> MissionTemplate:
        if template_id not in self._templates:
            raise ValueError(f"unknown EOS mission template: {template_id}")
        return self._templates[template_id]

    def _mission(self, mission_id: str) -> EnterpriseMission:
        if mission_id not in self._missions:
            raise ValueError(f"unknown EOS mission: {mission_id}")
        return self._missions[mission_id]

    def _next_mission_id(self) -> str:
        return f"EOS-MIS-{len(self._missions) + 1:06d}"


class OfficeScheduler:
    """Manage office activation, suspension, modes, budgets, and EOS analytics."""

    def __init__(self) -> None:
        self._offices = _baseline_offices()
        self.eos = EnterpriseOperationsScheduler()
        self._detections = {
            "runawayProcesses": 0,
            "scheduleConflicts": 0,
            "resourceExhaustion": 0,
            "missedActivations": 0,
            "unexpectedWakeEvents": 0,
            "stalledOffices": 0,
            "runtimeViolations": 0,
        }

    def snapshot(self) -> dict[str, Any]:
        """Return deterministic scheduler state, EOS mission state, and analytics."""
        offices = tuple(asdict(office) | {"operating_mode": office.operating_mode.value} for office in self._offices.values())
        active = [office for office in self._offices.values() if office.status == "ACTIVE"]
        sleeping = [office for office in self._offices.values() if office.status == "SLEEPING"]
        eos_snapshot = self.eos.snapshot(offices)
        odo_snapshot = self.eos.duty_officers.snapshot(eos_snapshot, offices)
        eos_snapshot = {**eos_snapshot, "officeDutyOfficers": odo_snapshot}
        return {
            "offices": offices,
            "summary": {
                "activeOffices": len(active),
                "sleepingOffices": len(sleeping),
                "totalOffices": len(self._offices),
                "estimatedComputeCostUsd": round(sum(_estimated_cost(office) for office in self._offices.values()), 4),
                "tokenConsumption": sum(office.token_consumption for office in self._offices.values()),
                "queueLength": sum(office.queue_length for office in self._offices.values()),
                "enterpriseOperatingMode": eos_snapshot["currentOperatingMode"],
                "eosEnabled": eos_snapshot["enabled"],
                "activeMissions": eos_snapshot["activeMissionCount"],
            },
            "analytics": {
                "officeUtilization": _percentage(len(active), len(self._offices)),
                "runtimeStatistics": {
                    "averageRuntimeMinutes": round(sum(office.runtime_minutes for office in self._offices.values()) / len(self._offices), 2),
                    "maxRuntimeMinutes": max(office.runtime_minutes for office in self._offices.values()),
                },
                "schedulingEfficiency": _scheduling_efficiency(self._offices.values()),
                "resourceAllocation": _resource_allocation(self._offices.values()),
                "wakeFrequency": sum(office.wake_count for office in self._offices.values()),
            },
            "detections": dict(self._detections),
            "enterpriseOperationsScheduler": eos_snapshot,
            "officeDutyOfficers": odo_snapshot,
        }

    def evaluate_duty_request(self, request: OfficeTaskingRequest | dict[str, Any]) -> dict[str, Any]:
        """Submit tasking through Office Duty Officer triage."""
        snapshot = self.snapshot()
        decision = self.eos.duty_officers.submit_request(request, snapshot["enterpriseOperationsScheduler"])
        return asdict(decision)

    def configure(
        self,
        *,
        organization: str,
        office: str,
        operating_mode: str,
        time_zone: str = "America/Cancun",
        business_hours: str = "09:30-16:00",
        scheduled_tasks: tuple[str, ...] = (),
        wake_triggers: tuple[str, ...] = (),
        sleep_triggers: tuple[str, ...] = (),
        runtime_limit_minutes: int = 60,
        resource_budget_usd: float = 5.0,
    ) -> OfficeSchedule:
        """Configure an office schedule and operating mode."""
        key = _key(organization, office)
        if key not in self._offices:
            raise ValueError(f"unknown office schedule target: {organization}/{office}")
        mode = _mode(operating_mode)
        office_state = self._offices[key]
        office_state = replace(
            office_state,
            operating_mode=mode,
            time_zone=time_zone,
            business_hours=business_hours,
            scheduled_tasks=tuple(scheduled_tasks),
            wake_triggers=tuple(wake_triggers),
            sleep_triggers=tuple(sleep_triggers),
            runtime_limit_minutes=max(1, int(runtime_limit_minutes)),
            resource_budget_usd=max(0.0, round(float(resource_budget_usd), 2)),
            remaining_budget_usd=max(0.0, round(float(resource_budget_usd), 2)),
            last_transition_utc=utc_timestamp(),
        )
        self._offices[key] = office_state
        _refresh_detections(office_state, self._detections)
        return office_state

    def activate(self, organization: str, office: str, trigger: str, mission_id: str = "") -> OfficeSchedule:
        """Wake an office only under EOS mission authority or Commander control."""
        office_state = self._office(organization, office)
        authorized_mission = mission_id
        if not authorized_mission:
            self.eos.set_enabled(True, reason="Commander direct office activation.")
            mission = self.eos.create_commander_directed_mission(
                mission_name=f"Commander Office Activation: {organization}/{office}",
                required_offices=(office,),
                directive_id=f"OFFICE-{office_state.schedule_id}",
                maximum_api_cost=min(office_state.resource_budget_usd, self.eos.mission_cost_ceiling_usd),
                maximum_api_calls=1,
                maximum_runtime_seconds=office_state.runtime_limit_minutes * 60,
            )
            self.eos.dispatch_mission(mission.mission_id, token_id="COMMANDER_AUTHORIZED_OFFICE_WAKE")
            authorized_mission = mission.mission_id
        status = "ACTIVE"
        office_state = replace(
            office_state,
            status=status,
            requested_state="Working",
            assigned_mission=authorized_mission,
            activation_reason=trigger or "Commander",
            wake_count=office_state.wake_count + 1,
            remaining_budget_usd=max(0.0, office_state.resource_budget_usd - office_state.cost_incurred_usd),
            last_transition_utc=utc_timestamp(),
        )
        self._offices[_key(organization, office)] = office_state
        if trigger and trigger not in office_state.wake_triggers and trigger not in {"Commander", "Critical Alert", "Enterprise Event", "Scheduled Event"}:
            self._detections["unexpectedWakeEvents"] += 1
        return office_state

    def suspend(self, organization: str, office: str, trigger: str) -> OfficeSchedule:
        """Suspend an office after completion or Commander request."""
        office_state = self._office(organization, office)
        office_state = replace(
            office_state,
            status="SLEEPING",
            requested_state="Sleeping",
            assigned_mission="",
            activation_reason=trigger or "Workflow Complete",
            last_transition_utc=utc_timestamp(),
        )
        self._offices[_key(organization, office)] = office_state
        return office_state

    def tick(self) -> None:
        """Advance deterministic runtime counters for active offices."""
        for key, office in tuple(self._offices.items()):
            if office.status != "ACTIVE":
                continue
            updated = replace(
                office,
                runtime_minutes=office.runtime_minutes + 1,
                token_consumption=office.token_consumption + 48,
                cpu_usage=min(100, office.cpu_usage + 1),
                memory_usage=min(100, office.memory_usage + 1),
                cost_incurred_usd=round(office.cost_incurred_usd + 0.0025, 4),
                remaining_budget_usd=max(0.0, round(office.resource_budget_usd - (office.cost_incurred_usd + 0.0025), 4)),
            )
            self._offices[key] = updated
            _refresh_detections(updated, self._detections)

    def _office(self, organization: str, office: str) -> OfficeSchedule:
        key = _key(organization, office)
        if key not in self._offices:
            raise ValueError(f"unknown office schedule target: {organization}/{office}")
        return self._offices[key]


def market_calendar_snapshot(timestamp_utc: str | None = None, *, instrument_type: str = "US_EQUITY") -> dict[str, Any]:
    """Extensible market-calendar abstraction, initially focused on U.S. equities."""
    dt = _parse_timestamp(timestamp_utc or utc_timestamp())
    date = dt.date().isoformat()
    weekday = dt.weekday()
    holiday = date in _US_MARKET_HOLIDAYS_2026
    early_close = date in _US_EARLY_CLOSES_2026
    if instrument_type.upper() == "CRYPTO":
        return {
            "trading_date": date,
            "instrument_type": instrument_type,
            "is_market_holiday": False,
            "is_early_close": False,
            "current_session": "Continuous",
            "regular_open": "00:00",
            "regular_close": "23:59",
            "timezone": "America/New_York",
            "continuous_market_does_not_authorize_continuous_expensive_offices": True,
        }
    regular_close = "13:00" if early_close else "16:00"
    current_time = dt.time()
    if weekday >= 5 or holiday:
        session = "Closed"
    elif time(4, 0) <= current_time < time(9, 30):
        session = "Pre-Market"
    elif time(9, 30) <= current_time < time.fromisoformat(regular_close):
        session = "Regular"
    elif time.fromisoformat(regular_close) <= current_time < time(20, 0):
        session = "After-Hours"
    else:
        session = "Closed"
    return {
        "trading_date": date,
        "instrument_type": instrument_type,
        "is_market_holiday": holiday,
        "is_early_close": early_close,
        "current_session": session,
        "regular_open": "09:30",
        "regular_close": regular_close,
        "pre_market_open": "04:00",
        "after_hours_close": "20:00",
        "timezone": "America/New_York",
    }


def _default_mission_templates() -> dict[str, MissionTemplate]:
    templates = (
        MissionTemplate(
            "pre_market_readiness",
            "Scheduled",
            "Pre-Market Readiness Mission",
            "Validate enterprise health, open-position risk, calendar status, capital budgets, and Commander attention items.",
            "09:00",
            True,
            "Risk Control",
            "Required",
            ("Runtime Monitoring", "Position Lifecycle", "Risk", "Commander Briefing"),
            "pre_market_readiness",
            600,
            0.25,
            2,
            1,
            "Pre-Market",
            "Exclusive Office Mission",
            3600,
        ),
        MissionTemplate(
            "post_open_discovery",
            "Scheduled",
            "Post-Open Discovery Mission",
            "Discover and evaluate actionable paper-trading opportunities after open volatility stabilizes.",
            "10:05",
            True,
            "Tactical Opportunity Evaluation",
            "Discretionary",
            ("Seeker", "Analyst", "Risk", "Trader"),
            "post_open_discovery",
            900,
            1.0,
            4,
            3,
            "Regular",
            "Prohibited Concurrency",
            3600,
        ),
        MissionTemplate(
            "midday_position_review",
            "Scheduled",
            "Midday Position Review Mission",
            "Review existing positions and material changes without full-market rediscovery.",
            "12:30",
            True,
            "Position Safety",
            "Safety",
            ("Position Monitor", "Risk", "Trader", "Historian"),
            "midday_position_review",
            600,
            0.35,
            2,
            1,
            "Regular",
            "Read-Only Parallel Activity",
            3600,
        ),
        MissionTemplate(
            "pre_close_risk",
            "Scheduled",
            "Pre-Close Risk Mission",
            "Review overnight exposure, outstanding orders, and time-sensitive position lifecycle conditions.",
            "15:30",
            True,
            "Position Safety",
            "Safety",
            ("Position Lifecycle", "Risk", "Trader", "Historian"),
            "pre_close_risk",
            600,
            0.5,
            2,
            1,
            "Regular",
            "Exclusive Office Mission",
            3600,
        ),
        MissionTemplate(
            "end_of_day_reconciliation",
            "Scheduled",
            "End-of-Day Reconciliation Mission",
            "Reconcile orders, fills, positions, cash, performance, costs, and mission outcomes.",
            "16:15",
            True,
            "Broker and Ledger Reconciliation",
            "Required",
            ("Trader Accounting", "Performance Truth Engine", "Historian", "Librarian", "Commander Briefing Generator"),
            "end_of_day_reconciliation",
            900,
            0.4,
            2,
            1,
            "After-Hours",
            "Exclusive Enterprise Mission",
            3600,
        ),
        MissionTemplate(
            "overnight_strategic_research",
            "Scheduled",
            "Overnight Strategic Research Mission",
            "Conduct non-time-critical strategic work outside the main trading mission cycle.",
            "21:00",
            False,
            "Strategic Intelligence",
            "Discretionary",
            ("Strategic Intelligence Command", "Librarian", "Historian"),
            "overnight_strategic_research",
            1800,
            1.25,
            4,
            2,
            "Closed",
            "Read-Only Parallel Activity",
            86400,
        ),
    )
    return {template.template_id: template for template in templates}


def _baseline_offices() -> dict[str, OfficeSchedule]:
    offices: dict[str, OfficeSchedule] = {}
    sequence = 1
    for organization, office_names in ORGANIZATION_OFFICES.items():
        for office in office_names:
            mode = OperatingMode.EVENT_DRIVEN if organization not in {"Infrastructure"} else OperatingMode.BUSINESS_HOURS
            status = "SLEEPING"
            requested_state = "Sleeping"
            if organization == "Infrastructure":
                status = "ACTIVE"
                requested_state = "Monitoring"
            offices[_key(organization, office)] = OfficeSchedule(
                schedule_id=f"SCH-{sequence:06d}",
                organization=organization,
                office=office,
                operating_mode=mode,
                status=status,
                time_zone="America/Cancun",
                business_hours="09:30-16:00",
                scheduled_tasks=("health-monitoring",) if status == "ACTIVE" else (),
                wake_triggers=("Commander", "Enterprise Event", "Critical Alert", "Scheduled Event", "EOS Mission"),
                sleep_triggers=("Workflow Complete", "Commander", "Runtime Limit", "Mission Complete"),
                runtime_limit_minutes=240 if status == "ACTIVE" else 60,
                resource_budget_usd=12.0 if status == "ACTIVE" else 3.0,
                runtime_minutes=15 if status == "ACTIVE" else 0,
                cpu_usage=18 if status == "ACTIVE" else 2,
                memory_usage=24 if status == "ACTIVE" else 4,
                token_consumption=720 if status == "ACTIVE" else 0,
                queue_length=1 if status == "ACTIVE" else 0,
                wake_count=1 if status == "ACTIVE" else 0,
                last_transition_utc=utc_timestamp(),
                requested_state=requested_state,
                remaining_budget_usd=12.0 if status == "ACTIVE" else 3.0,
            )
            sequence += 1
    return offices


def _office_roster(offices: tuple[dict[str, Any], ...], activations: list[OfficeActivationRequest]) -> tuple[dict[str, Any], ...]:
    latest = {activation.office_id: activation for activation in activations}
    roster = []
    for office in offices:
        activation = latest.get(office.get("office", "")) or latest.get(f"{office.get('organization', '')}/{office.get('office', '')}")
        roster.append(
            {
                "office": office.get("office", ""),
                "organization": office.get("organization", ""),
                "currentState": office.get("requested_state") or ("Working" if office.get("status") == "ACTIVE" else "Sleeping"),
                "assignedMission": office.get("assigned_mission") or (activation.mission_id if activation else ""),
                "activationReason": office.get("activation_reason") or (activation.activation_reason if activation else "Sleeping until EOS mission requires work."),
                "runtime": office.get("runtime_minutes", 0),
                "costIncurred": office.get("cost_incurred_usd", 0.0),
                "remainingBudget": office.get("remaining_budget_usd", office.get("resource_budget_usd", 0.0)),
            }
        )
    return tuple(roster)


def _mission_from_dict(item: dict[str, Any]) -> EnterpriseMission:
    fields = EnterpriseMission.__dataclass_fields__
    values = {name: item.get(name) for name in fields}
    for key in ("required_offices", "optional_offices", "prohibited_offices"):
        values[key] = tuple(values.get(key) or ())
    values["cost_summary"] = dict(values.get("cost_summary") or {})
    return EnterpriseMission(**values)


def _override_record(action: str, actor: str, reason: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "override_id": f"EOS-OVR-{utc_timestamp().replace(':', '').replace('-', '')}",
        "timestamp": utc_timestamp(),
        "action": action,
        "actor": actor,
        "reason": reason,
        "metadata": metadata or {},
        "audit_reference": "EOS-MANUAL-CONTROL",
    }


def _enterprise_mode(value: str) -> EnterpriseOperatingMode:
    normalized = value.strip().replace("_", " ").replace("-", " ").title()
    aliases = {
        "Full Paper Trading": EnterpriseOperatingMode.FULL_PAPER_TRADING,
        "Observation Only": EnterpriseOperatingMode.OBSERVATION_ONLY,
        "Position Management Only": EnterpriseOperatingMode.POSITION_MANAGEMENT_ONLY,
        "Capital Preservation": EnterpriseOperatingMode.CAPITAL_PRESERVATION,
        "Strategic Research Only": EnterpriseOperatingMode.STRATEGIC_RESEARCH_ONLY,
        "Maintenance": EnterpriseOperatingMode.MAINTENANCE,
        "Halted": EnterpriseOperatingMode.HALTED,
    }
    if normalized in aliases:
        return aliases[normalized]
    raise ValueError(f"unsupported enterprise operating mode: {value}")


def _key(organization: str, office: str) -> str:
    return f"{organization}::{office}"


def _mode(value: str) -> OperatingMode:
    normalized = value.strip().replace("_", " ").title()
    aliases = {
        "Active": OperatingMode.CONTINUOUS_OPERATION,
        "Paper Trading": OperatingMode.EVENT_DRIVEN,
    }
    if normalized in aliases:
        return aliases[normalized]
    for mode in OperatingMode:
        if mode.value == normalized:
            return mode
    raise ValueError(f"unsupported operating mode: {value}")


def _percentage(value: int, total: int) -> str:
    return f"{round((value / total) * 100, 1) if total else 0}%"


def _estimated_cost(office: OfficeSchedule) -> float:
    return (office.runtime_minutes * 0.0025) + (office.token_consumption / 1000 * 0.0015) + office.cost_incurred_usd


def _scheduling_efficiency(offices: Any) -> str:
    office_tuple = tuple(offices)
    productive = sum(1 for office in office_tuple if office.status == "ACTIVE" and office.queue_length <= 3)
    return _percentage(productive, len(office_tuple))


def _resource_allocation(offices: Any) -> dict[str, int]:
    office_tuple = tuple(offices)
    return {
        "cpuAverage": round(sum(office.cpu_usage for office in office_tuple) / len(office_tuple)),
        "memoryAverage": round(sum(office.memory_usage for office in office_tuple) / len(office_tuple)),
        "budgetAverageUsd": round(sum(office.resource_budget_usd for office in office_tuple) / len(office_tuple)),
    }


def _refresh_detections(office: OfficeSchedule, detections: dict[str, int]) -> None:
    if office.runtime_minutes > office.runtime_limit_minutes:
        detections["runtimeViolations"] += 1
    if office.cpu_usage >= 95 or office.memory_usage >= 95:
        detections["resourceExhaustion"] += 1
    if office.status == "ACTIVE" and office.runtime_minutes > office.runtime_limit_minutes * 2:
        detections["runawayProcesses"] += 1
    if office.status == "ACTIVE" and office.queue_length > 10:
        detections["stalledOffices"] += 1
    if office.operating_mode == OperatingMode.SCHEDULED and not office.scheduled_tasks:
        detections["scheduleConflicts"] += 1


def _scheduled_start(timestamp: str, hhmm: str) -> str:
    dt = _parse_timestamp(timestamp)
    return f"{dt.date().isoformat()}T{hhmm}:00Z"


def _parse_timestamp(value: str) -> datetime:
    if not value:
        return datetime.now(UTC)
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.now(UTC)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _duration_seconds(start: str, end: str) -> int:
    if not start or not end:
        return 0
    return int((_parse_timestamp(end) - _parse_timestamp(start)).total_seconds())


def _priority_rank(priority: str) -> int:
    return PRIORITY_RANK.get(priority, 99)


def _allowed_sessions(requirement: str) -> set[str]:
    if requirement == "Any":
        return {"Pre-Market", "Regular", "After-Hours", "Closed", "Continuous"}
    if requirement == "Market Hours":
        return {"Regular"}
    return {requirement}


def _cost_by_office(activations: list[OfficeActivationRequest]) -> dict[str, float]:
    costs: dict[str, float] = {}
    for activation in activations:
        costs[activation.office_id] = round(costs.get(activation.office_id, 0.0) + float(activation.maximum_api_cost), 4)
    return costs


def _cost_by_mission_type(missions: tuple[EnterpriseMission, ...]) -> dict[str, float]:
    costs: dict[str, float] = {}
    for mission in missions:
        costs[mission.mission_type] = round(costs.get(mission.mission_type, 0.0) + float(mission.cost_summary.get("actual_api_cost_usd", 0.0)), 4)
    return costs


def _average_workflows(missions: tuple[EnterpriseMission, ...]) -> float:
    if not missions:
        return 0.0
    return round(sum(mission.maximum_workflows for mission in missions) / len(missions), 2)


_US_MARKET_HOLIDAYS_2026 = {
    "2026-01-01",
    "2026-01-19",
    "2026-02-16",
    "2026-04-03",
    "2026-05-25",
    "2026-06-19",
    "2026-07-03",
    "2026-09-07",
    "2026-11-26",
    "2026-12-25",
}

_US_EARLY_CLOSES_2026 = {
    "2026-11-27",
    "2026-12-24",
}
