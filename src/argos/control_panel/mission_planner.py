"""Enterprise Mission Planner for ARGOS EO-CD."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp


class MissionTriggerType(str, Enum):
    VALIDATED_EVENT = "validated_event"
    EVENT_GROUP = "event_group"
    SCHEDULED_OBLIGATION = "scheduled_obligation"
    COMMANDER_DIRECTIVE = "commander_directive"
    DUTY_OFFICER_RECOMMENDATION = "duty_officer_recommendation"
    ENTERPRISE_RECOVERY = "enterprise_recovery"
    MANUAL_REQUEST = "manual_request"
    POLICY_REQUIREMENT = "policy_requirement"


class MissionPlanStatus(str, Enum):
    INTAKE = "intake"
    EVALUATING = "evaluating"
    NOT_REQUIRED = "not_required"
    DRAFT = "draft"
    VALIDATING = "validating"
    READY_FOR_SUBMISSION = "ready_for_submission"
    SUBMITTED = "submitted"
    RETURNED_FOR_REVISION = "returned_for_revision"
    SCHEDULER_DEFERRED = "scheduler_deferred"
    SCHEDULER_REJECTED = "scheduler_rejected"
    SCHEDULER_AUTHORIZED = "scheduler_authorized"
    SUPERSEDED = "superseded"
    MERGED = "merged"
    EXPIRED = "expired"
    CANCELED = "canceled"
    FAILED = "failed"


class MissionType(str, Enum):
    POSITION_SAFETY_REVIEW = "position_safety_review"
    EMERGENCY_RISK_REVIEW = "emergency_risk_review"
    ORDER_LIFECYCLE_REVIEW = "order_lifecycle_review"
    BROKER_RECONCILIATION = "broker_reconciliation"
    LEDGER_RECONCILIATION = "ledger_reconciliation"
    PORTFOLIO_RISK_REVIEW = "portfolio_risk_review"
    EARNINGS_REASSESSMENT = "earnings_reassessment"
    FILING_REVIEW = "filing_review"
    INFORMATION_REFRESH = "information_refresh"
    OPPORTUNITY_SCAN = "opportunity_scan"
    CANDIDATE_EVALUATION = "candidate_evaluation"
    TRADE_ENTRY_REVIEW = "trade_entry_review"
    TRADE_EXIT_REVIEW = "trade_exit_review"
    END_OF_DAY_RECONCILIATION = "end_of_day_reconciliation"
    COMMANDER_BRIEFING = "commander_briefing"
    STRATEGIC_RESEARCH = "strategic_research"
    ENTERPRISE_RECOVERY = "enterprise_recovery"
    SYSTEM_INTEGRITY_REVIEW = "system_integrity_review"
    COST_REVIEW = "cost_review"
    REPLAY_ANALYSIS = "replay_analysis"
    CAPABILITY_DEVELOPMENT = "capability_development"


class MissionPriorityClass(str, Enum):
    EMERGENCY_RECOVERY = "emergency_recovery"
    POSITION_SAFETY = "position_safety"
    BROKER_LEDGER_INTEGRITY = "broker_ledger_integrity"
    RISK_CONTROL = "risk_control"
    REQUIRED_LIFECYCLE_ACTION = "required_lifecycle_action"
    COMMANDER_DIRECTED = "commander_directed"
    TACTICAL_EVALUATION = "tactical_evaluation"
    STRATEGIC_INTELLIGENCE = "strategic_intelligence"
    HISTORICAL_REVIEW = "historical_review"
    CAPABILITY_DEVELOPMENT = "capability_development"


@dataclass(frozen=True)
class MissionTrigger:
    trigger_id: str
    trigger_type: MissionTriggerType
    source_event_id: str
    source_event_group_id: str
    source_schedule_id: str
    source_directive_id: str
    source_duty_officer_id: str
    title: str
    summary: str
    subject_type: str
    subject_id: str
    ticker: str
    position_id: str
    order_id: str
    workflow_id: str
    severity: str
    urgency: str
    materiality: str
    confidence: float
    requested_mission_type: str
    recommended_offices: tuple[str, ...]
    earliest_start_at: str
    deadline_at: str
    expires_at: str
    provenance: dict[str, Any]
    metadata: dict[str, Any]
    received_at: str


@dataclass(frozen=True)
class MissionObjective:
    objective_id: str
    primary_objective: str
    decision_question: str
    subject_type: str
    subject_id: str
    scope_inclusions: tuple[str, ...]
    scope_exclusions: tuple[str, ...]
    required_decisions: tuple[str, ...]
    required_outputs: tuple[str, ...]
    success_definition: str
    failure_definition: str
    deadline_at: str


@dataclass(frozen=True)
class MissionOfficeAssignment:
    office_id: str
    participation_type: str
    sequence_index: int
    responsibility: str
    required_inputs: tuple[str, ...]
    required_outputs: tuple[str, ...]
    upstream_dependencies: tuple[str, ...]
    downstream_recipients: tuple[str, ...]
    max_runtime_seconds: int
    max_api_calls: int
    max_input_tokens: int | None
    max_output_tokens: int | None
    allowed_model_classes: tuple[str, ...]
    paid_data_allowed: bool
    optional: bool
    omission_condition: str
    skip_condition: str
    completion_condition: str
    failure_behavior: str
    inclusion_reason: str


@dataclass(frozen=True)
class MissionDependency:
    dependency_id: str
    upstream_node_id: str
    downstream_node_id: str
    dependency_type: str
    required: bool
    satisfaction_condition: str
    failure_behavior: str
    timeout_seconds: int | None


@dataclass(frozen=True)
class MissionInputRequirement:
    input_id: str
    name: str
    description: str
    source_type: str
    authoritative_source: str
    required: bool
    freshness_requirement_seconds: int | None
    existing_reference_id: str
    retrieval_required: bool
    validation_rule: str
    fallback_source: str
    unavailable_behavior: str


@dataclass(frozen=True)
class MissionOutputContract:
    output_id: str
    name: str
    description: str
    required: bool
    expected_schema: tuple[str, ...]
    validation_rule: str
    consumer: str
    completion_signal: str


@dataclass(frozen=True)
class MissionResourceEnvelope:
    runtime_ceiling_seconds: int
    wall_clock_deadline_seconds: int
    api_call_ceiling: int
    token_ceiling: int
    paid_data_call_ceiling: int
    estimated_cost_usd: float
    cost_class: str
    estimate_confidence: float
    estimate_basis: tuple[str, ...]


@dataclass(frozen=True)
class MissionCompletionPolicy:
    completion_criteria: tuple[str, ...]
    failure_criteria: tuple[str, ...]
    retry_limit: int
    fallback_behavior: str
    deferment_behavior: str
    cancellation_behavior: str
    escalation_conditions: tuple[str, ...]
    cleanup_requirements: tuple[str, ...]


@dataclass(frozen=True)
class MissionTemplateRecord:
    template_id: str
    version: str
    mission_type: MissionType
    supported_triggers: tuple[MissionTriggerType, ...]
    mandatory_offices: tuple[str, ...]
    conditional_offices: tuple[str, ...]
    prohibited_offices: tuple[str, ...]
    default_sequence: tuple[str, ...]
    cost_class: str
    runtime_ceiling_seconds: int
    api_call_ceiling: int
    completion_criteria: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class MissionPlanRecord:
    mission_plan_id: str
    plan_version: int
    status: MissionPlanStatus
    plan_title: str
    mission_type: MissionType
    priority_class: MissionPriorityClass
    source_trigger_ids: tuple[str, ...]
    template_id: str
    template_version: str
    created_at: str
    updated_at: str
    objective: MissionObjective
    office_assignments: tuple[MissionOfficeAssignment, ...]
    prohibited_offices: tuple[str, ...]
    excluded_offices: tuple[dict[str, str], ...]
    dependencies: tuple[MissionDependency, ...]
    input_requirements: tuple[MissionInputRequirement, ...]
    output_contracts: tuple[MissionOutputContract, ...]
    resource_envelope: MissionResourceEnvelope
    completion_policy: MissionCompletionPolicy
    necessity_decision: str
    reuse_decision: dict[str, Any]
    delta_decision: dict[str, Any]
    planning_explanation: tuple[str, ...]
    validation_results: tuple[dict[str, Any], ...]
    scheduler_disposition: dict[str, Any]
    lineage: dict[str, Any]
    audit_history: tuple[dict[str, Any], ...]
    content_hash: str


class EnterpriseMissionPlanner:
    """Deterministic mission planning layer between triggers and EOS."""

    def __init__(self) -> None:
        self._templates = _default_templates()
        self._capabilities = _default_capabilities()
        self._triggers: dict[str, MissionTrigger] = {}
        self._plans: dict[str, MissionPlanRecord] = {}
        self._trigger_to_plan: dict[str, str] = {}
        self._audit: list[dict[str, Any]] = []
        self._dead_letters: list[dict[str, Any]] = []
        self._merge_records: list[dict[str, Any]] = []
        self._supersession_records: list[dict[str, Any]] = []
        self.enabled = True

    def snapshot(self) -> dict[str, Any]:
        plans = tuple(self._plans.values())
        active = tuple(item for item in plans if item.status not in {MissionPlanStatus.NOT_REQUIRED, MissionPlanStatus.SUBMITTED, MissionPlanStatus.SUPERSEDED, MissionPlanStatus.CANCELED})
        submitted = tuple(item for item in plans if item.status == MissionPlanStatus.SUBMITTED)
        return {
            "plannerName": "Enterprise Mission Planner",
            "engineeringOrder": "EO-CD",
            "enabled": self.enabled,
            "status": "HEALTHY" if self.enabled else "DISABLED_SAFE",
            "triggerQueue": tuple(_snapshot_dataclass(item) for item in self._triggers.values()),
            "draftMissionPlans": tuple(_snapshot_dataclass(item) for item in active),
            "submittedMissionPlans": tuple(_snapshot_dataclass(item) for item in submitted),
            "allMissionPlans": tuple(_snapshot_dataclass(item) for item in plans),
            "missionTemplates": tuple(_snapshot_dataclass(item) for item in self._templates.values()),
            "officeCapabilityRegistry": tuple(_json_safe(value | {"office_id": key}) for key, value in sorted(self._capabilities.items())),
            "planningDecisions": tuple(_snapshot_dataclass(item) for item in plans),
            "minimumWorkforceView": tuple(_minimum_workforce_view(item) for item in active[-8:]),
            "dependencyGraphs": tuple(_dependency_graph_view(item) for item in active[-8:]),
            "resourceEnvelopes": tuple({"mission_plan_id": item.mission_plan_id, **_snapshot_dataclass(item.resource_envelope)} for item in active[-8:]),
            "reuseAndDelta": tuple({"mission_plan_id": item.mission_plan_id, "reuse": _json_safe(item.reuse_decision), "delta": _json_safe(item.delta_decision)} for item in active[-8:]),
            "completionAndFailure": tuple({"mission_plan_id": item.mission_plan_id, **_snapshot_dataclass(item.completion_policy)} for item in active[-8:]),
            "auditHistory": tuple(self._audit[-50:]),
            "deadLetters": tuple(self._dead_letters[-20:]),
            "mergeRecords": tuple(self._merge_records[-20:]),
            "supersessionRecords": tuple(self._supersession_records[-20:]),
            "metrics": self._metrics(),
            "lawCD": {
                "planningIsAuthorization": False,
                "officeActivations": 0,
                "workflowStarts": 0,
                "routineAiInvocations": 0,
                "brokerOrdersSubmitted": 0,
                "positionMutations": 0,
                "ledgerMutations": 0,
                "creditsReserved": 0,
                "selfAuthorizedPlans": 0,
            },
            "replay": {"available": True, "productionMutation": False},
        }

    def plan_from_event(self, event: dict[str, Any], *, submit_to_scheduler: bool = False, eos: Any = None) -> dict[str, Any]:
        trigger = _trigger_from_event(event)
        plan = self.plan_trigger(trigger)
        if submit_to_scheduler and plan.status == MissionPlanStatus.READY_FOR_SUBMISSION:
            self.submit_plan(plan.mission_plan_id, eos=eos)
        return self.snapshot()

    def plan_commander_request(self, request: dict[str, Any], *, submit_to_scheduler: bool = False, eos: Any = None) -> dict[str, Any]:
        trigger = _trigger_from_commander_request(request)
        plan = self.plan_trigger(trigger)
        if submit_to_scheduler and plan.status == MissionPlanStatus.READY_FOR_SUBMISSION:
            self.submit_plan(plan.mission_plan_id, eos=eos)
        return self.snapshot()

    def plan_duty_officer_recommendation(self, decision: dict[str, Any], *, submit_to_scheduler: bool = False, eos: Any = None) -> dict[str, Any]:
        trigger = _trigger_from_duty_decision(decision)
        plan = self.plan_trigger(trigger)
        if submit_to_scheduler and plan.status == MissionPlanStatus.READY_FOR_SUBMISSION:
            self.submit_plan(plan.mission_plan_id, eos=eos)
        return self.snapshot()

    def plan_scheduled_obligation(self, obligation: dict[str, Any], *, submit_to_scheduler: bool = False, eos: Any = None) -> dict[str, Any]:
        trigger = _trigger_from_schedule(obligation)
        plan = self.plan_trigger(trigger)
        if submit_to_scheduler and plan.status == MissionPlanStatus.READY_FOR_SUBMISSION:
            self.submit_plan(plan.mission_plan_id, eos=eos)
        return self.snapshot()

    def plan_trigger(self, trigger: MissionTrigger | dict[str, Any]) -> MissionPlanRecord:
        if isinstance(trigger, dict):
            trigger = _trigger_from_dict(trigger)
        if trigger.trigger_id in self._trigger_to_plan:
            plan = self._plans[self._trigger_to_plan[trigger.trigger_id]]
            self._audit_record("duplicate_trigger_suppressed", trigger.trigger_id, plan.mission_plan_id, "Existing unresolved plan satisfies trigger.")
            return plan
        self._triggers[trigger.trigger_id] = trigger
        self._audit_record("trigger_received", trigger.trigger_id, "", "Mission trigger accepted for deterministic planning.")

        necessary, reuse = self._necessity(trigger)
        if not necessary:
            plan = self._not_required_plan(trigger, reuse)
            self._plans[plan.mission_plan_id] = plan
            self._trigger_to_plan[trigger.trigger_id] = plan.mission_plan_id
            return plan

        template = self._select_template(trigger)
        merge = self._merge_candidate(trigger, template)
        if merge:
            merged = self._merge_plan(merge, trigger)
            self._trigger_to_plan[trigger.trigger_id] = merged.mission_plan_id
            return merged
        superseded = self._supersession_candidate(trigger, template)
        objective = _objective_for(trigger, template)
        delta = _delta_decision(trigger)
        assignments, excluded = self._select_workforce(trigger, template, delta)
        dependencies = _dependencies_for(assignments)
        inputs = _inputs_for(trigger, template, delta)
        outputs = _outputs_for(template)
        envelope = _resource_envelope(template, assignments, delta)
        completion = _completion_policy(template)
        validation = _validate_plan(trigger, template, assignments, dependencies, inputs, outputs, envelope)
        status = MissionPlanStatus.READY_FOR_SUBMISSION if all(item["valid"] for item in validation) else MissionPlanStatus.RETURNED_FOR_REVISION
        plan_id = f"EMP-PLAN-{len(self._plans) + 1:06d}"
        lineage = {"supersedes": superseded.mission_plan_id if superseded else "", "superseded_by": "", "merged_from": ()}
        explanation = _planning_explanation(trigger, template, assignments, excluded, reuse, delta)
        plan = MissionPlanRecord(
            mission_plan_id=plan_id,
            plan_version=1,
            status=status,
            plan_title=f"{template.mission_type.value.replace('_', ' ').title()} for {trigger.subject_id or trigger.ticker or trigger.trigger_id}",
            mission_type=template.mission_type,
            priority_class=_priority_for(trigger, template),
            source_trigger_ids=(trigger.trigger_id,),
            template_id=template.template_id,
            template_version=template.version,
            created_at=utc_timestamp(),
            updated_at=utc_timestamp(),
            objective=objective,
            office_assignments=assignments,
            prohibited_offices=template.prohibited_offices,
            excluded_offices=excluded,
            dependencies=dependencies,
            input_requirements=inputs,
            output_contracts=outputs,
            resource_envelope=envelope,
            completion_policy=completion,
            necessity_decision="NEW_MISSION_REQUIRED",
            reuse_decision=reuse,
            delta_decision=delta,
            planning_explanation=explanation,
            validation_results=tuple(validation),
            scheduler_disposition={},
            lineage=lineage,
            audit_history=(self._audit_record("plan_created", trigger.trigger_id, plan_id, "Mission plan created and validated.", emit=False),),
            content_hash="",
        )
        plan = replace(plan, content_hash=_plan_hash(plan))
        self._plans[plan.mission_plan_id] = plan
        self._trigger_to_plan[trigger.trigger_id] = plan.mission_plan_id
        if superseded:
            self._plans[superseded.mission_plan_id] = replace(superseded, status=MissionPlanStatus.SUPERSEDED, lineage=superseded.lineage | {"superseded_by": plan.mission_plan_id})
            self._supersession_records.append({"timestamp": utc_timestamp(), "old_plan_id": superseded.mission_plan_id, "new_plan_id": plan.mission_plan_id, "reason": "Severity escalation requires revised plan."})
        self._audit_record("plan_ready_for_submission", trigger.trigger_id, plan.mission_plan_id, "Plan is ready for EOS review." if status == MissionPlanStatus.READY_FOR_SUBMISSION else "Plan requires revision before EOS submission.")
        return plan

    def submit_plan(self, mission_plan_id: str, *, eos: Any) -> MissionPlanRecord:
        plan = self._plans[mission_plan_id]
        if plan.status != MissionPlanStatus.READY_FOR_SUBMISSION:
            self._dead_letters.append({"timestamp": utc_timestamp(), "mission_plan_id": mission_plan_id, "reason": "Plan is not ready for submission."})
            return plan
        if eos is None:
            self._dead_letters.append({"timestamp": utc_timestamp(), "mission_plan_id": mission_plan_id, "reason": "Scheduler unavailable."})
            return replace(plan, status=MissionPlanStatus.SCHEDULER_DEFERRED)
        if plan.scheduler_disposition.get("scheduler_mission_id"):
            return plan
        mandatory = tuple(item.office_id for item in plan.office_assignments if not item.optional and item.participation_type != "deterministic_service")
        mission = eos.create_commander_directed_mission(
            mission_name=plan.plan_title,
            required_offices=mandatory,
            directive_id=plan.mission_plan_id,
            priority=_eos_priority(plan.priority_class),
            maximum_api_cost=plan.resource_envelope.estimated_cost_usd,
            maximum_api_calls=plan.resource_envelope.api_call_ceiling,
            maximum_runtime_seconds=plan.resource_envelope.runtime_ceiling_seconds,
            workflow_type=plan.mission_type.value,
        )
        disposition = {
            "scheduler_mission_id": mission.mission_id,
            "scheduler_status": mission.status,
            "submitted_at": utc_timestamp(),
            "authority": "Enterprise Operations Scheduler",
            "authorization_performed": False,
        }
        submitted = replace(plan, status=MissionPlanStatus.SUBMITTED, updated_at=utc_timestamp(), scheduler_disposition=disposition)
        submitted = replace(submitted, content_hash=_plan_hash(submitted))
        self._plans[mission_plan_id] = submitted
        self._audit_record("plan_submitted_to_scheduler", "", mission_plan_id, f"Plan submitted to EOS as {mission.mission_id}; authorization remains with EOS.")
        return submitted

    def replay(self, triggers: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        engine = EnterpriseMissionPlanner()
        for trigger in triggers:
            engine.plan_trigger(trigger)
        result = engine.snapshot()
        result["replayMode"] = True
        result["productionMutation"] = False
        return result

    def recover_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        for item in snapshot.get("triggerQueue", ()):
            trigger = _trigger_from_dict(item)
            self._triggers[trigger.trigger_id] = trigger
        for item in snapshot.get("allMissionPlans", ()):
            plan = _plan_from_dict(item)
            self._plans[plan.mission_plan_id] = plan
            for trigger_id in plan.source_trigger_ids:
                self._trigger_to_plan[trigger_id] = plan.mission_plan_id
        self._audit.append({"timestamp": utc_timestamp(), "action": "restart_recovery", "reason": "Mission Planner restored from snapshot."})

    def cancel_plan(self, mission_plan_id: str, *, reason: str = "Commander canceled draft mission plan.") -> MissionPlanRecord:
        plan = self._plans[mission_plan_id]
        canceled = replace(plan, status=MissionPlanStatus.CANCELED, updated_at=utc_timestamp())
        self._plans[mission_plan_id] = canceled
        self._audit_record("plan_canceled", "", mission_plan_id, reason)
        return canceled

    def _necessity(self, trigger: MissionTrigger) -> tuple[bool, dict[str, Any]]:
        metadata = trigger.metadata or {}
        if metadata.get("suppressed"):
            return False, {"decision": "SUPPRESSED_TRIGGER_REJECTED", "reason": "Suppressed EO-CC candidates cannot create mission plans.", "work_avoided_estimate": 0.0}
        if metadata.get("cache_current") or metadata.get("cache_available") or metadata.get("local_resolution_available"):
            return False, {"decision": "USE_CACHED_OR_LOCAL_RESULT", "cache_reference": str(metadata.get("cache_reference", "LOCAL-RESULT")), "reason": "Existing local or cached product satisfies the request.", "work_avoided_estimate": 0.0}
        return True, {"decision": "MISSION_REQUIRED", "reason": "No fresh cached, local, or deterministic result fully satisfies the trigger.", "work_avoided_estimate": 0.0}

    def _select_template(self, trigger: MissionTrigger) -> MissionTemplateRecord:
        requested = _mission_type(trigger.requested_mission_type)
        if requested and requested in {template.mission_type for template in self._templates.values()}:
            return next(template for template in self._templates.values() if template.mission_type == requested)
        event_type = (trigger.metadata.get("event_type") or trigger.requested_mission_type or trigger.title or "").lower()
        if trigger.position_id or "stop" in event_type or "position" in event_type:
            return self._templates["position_safety_review_v1"]
        if trigger.order_id or "broker" in event_type or "order" in event_type:
            return self._templates["broker_reconciliation_v1"]
        if "ledger" in event_type or "reconciliation" in event_type or "end_of_day" in event_type:
            return self._templates["end_of_day_reconciliation_v1"]
        if "briefing" in event_type or "report" in event_type:
            return self._templates["commander_briefing_v1"]
        if "earnings" in event_type or "guidance" in event_type:
            return self._templates["earnings_reassessment_v1"]
        if trigger.trigger_type == MissionTriggerType.ENTERPRISE_RECOVERY or "health" in event_type or "recovery" in event_type:
            return self._templates["enterprise_recovery_v1"]
        if "cost" in event_type or "credit" in event_type:
            return self._templates["cost_review_v1"]
        if trigger.trigger_type == MissionTriggerType.SCHEDULED_OBLIGATION:
            return self._templates["opportunity_scan_v1"]
        return self._templates["strategic_research_v1"] if trigger.trigger_type == MissionTriggerType.COMMANDER_DIRECTIVE else self._templates["information_refresh_v1"]

    def _select_workforce(self, trigger: MissionTrigger, template: MissionTemplateRecord, delta: dict[str, Any]) -> tuple[tuple[MissionOfficeAssignment, ...], tuple[dict[str, str], ...]]:
        included: list[MissionOfficeAssignment] = []
        excluded: list[dict[str, str]] = []
        recommended = tuple(item for item in trigger.recommended_offices if item in self._capabilities)
        roster = list(template.mandatory_offices)
        for office in recommended:
            if office not in roster and office not in template.prohibited_offices and office in template.conditional_offices:
                roster.append(office)
        if delta.get("delta_mission") and "Seeker" in roster:
            roster.remove("Seeker")
            excluded.append({"office_id": "Seeker", "reason": "Delta mission reuses discovery and avoids full market scan."})
        for office in roster:
            included.append(_assignment_for(office, len(included) + 1, trigger, template, self._capabilities[office]))
        known = set(self._capabilities)
        for office in sorted(known - set(roster)):
            reason = "Prohibited by template." if office in template.prohibited_offices else "Not required for minimum workforce."
            if office in {"Performance Truth", "Position Lifecycle"} and office not in template.mandatory_offices:
                reason = "Deterministic service not required by this mission type."
            excluded.append({"office_id": office, "reason": reason})
        return tuple(included), tuple(excluded)

    def _merge_candidate(self, trigger: MissionTrigger, template: MissionTemplateRecord) -> MissionPlanRecord | None:
        merge_key = f"{template.mission_type.value}:{trigger.subject_id or trigger.order_id or trigger.position_id}"
        if trigger.severity in {"critical", "emergency"}:
            return None
        for plan in self._plans.values():
            if plan.status == MissionPlanStatus.READY_FOR_SUBMISSION and f"{plan.mission_type.value}:{plan.objective.subject_id}" == merge_key:
                return plan
        return None

    def _merge_plan(self, plan: MissionPlanRecord, trigger: MissionTrigger) -> MissionPlanRecord:
        merged_ids = tuple(dict.fromkeys((*plan.source_trigger_ids, trigger.trigger_id)))
        lineage = plan.lineage | {"merged_from": merged_ids}
        merged = replace(plan, source_trigger_ids=merged_ids, updated_at=utc_timestamp(), lineage=lineage, plan_version=plan.plan_version + 1)
        merged = replace(merged, content_hash=_plan_hash(merged))
        self._plans[plan.mission_plan_id] = merged
        self._merge_records.append({"timestamp": utc_timestamp(), "mission_plan_id": plan.mission_plan_id, "trigger_id": trigger.trigger_id, "reason": "Related trigger merged into existing unresolved plan."})
        self._audit_record("trigger_merged", trigger.trigger_id, plan.mission_plan_id, "Related trigger merged into one mission plan.")
        return merged

    def _supersession_candidate(self, trigger: MissionTrigger, template: MissionTemplateRecord) -> MissionPlanRecord | None:
        if trigger.severity not in {"critical", "emergency"}:
            return None
        subject = trigger.subject_id or trigger.position_id or trigger.order_id
        for plan in self._plans.values():
            if plan.status == MissionPlanStatus.READY_FOR_SUBMISSION and plan.mission_type == template.mission_type and plan.objective.subject_id == subject:
                return plan
        return None

    def _not_required_plan(self, trigger: MissionTrigger, reuse: dict[str, Any]) -> MissionPlanRecord:
        template = self._templates["information_refresh_v1"]
        objective = _objective_for(trigger, template)
        envelope = MissionResourceEnvelope(1, 60, 0, 0, 0, 0.0, "local", 1.0, ("cache_or_local_resolution",))
        completion = MissionCompletionPolicy(("Return cached/local answer reference.",), ("Cache/local answer unavailable.",), 0, "Escalate to planner re-evaluation.", "Queue if source stale.", "Cancel no-work plan.", ("Freshness failure",), ("Preserve no-action evidence.",))
        plan = MissionPlanRecord(
            mission_plan_id=f"EMP-PLAN-{len(self._plans) + 1:06d}",
            plan_version=1,
            status=MissionPlanStatus.NOT_REQUIRED,
            plan_title=f"No Mission Required for {trigger.subject_id or trigger.trigger_id}",
            mission_type=template.mission_type,
            priority_class=MissionPriorityClass.TACTICAL_EVALUATION,
            source_trigger_ids=(trigger.trigger_id,),
            template_id=template.template_id,
            template_version=template.version,
            created_at=utc_timestamp(),
            updated_at=utc_timestamp(),
            objective=objective,
            office_assignments=(),
            prohibited_offices=template.prohibited_offices,
            excluded_offices=tuple({"office_id": office, "reason": "Mission not required; prior/local result satisfies trigger."} for office in sorted(self._capabilities)),
            dependencies=(),
            input_requirements=(),
            output_contracts=(),
            resource_envelope=envelope,
            completion_policy=completion,
            necessity_decision=reuse["decision"],
            reuse_decision=reuse,
            delta_decision={"delta_mission": False, "reason": "No mission created."},
            planning_explanation=("Mission suppressed because reuse or local resolution satisfies the trigger.",),
            validation_results=({"rule": "no_authorization", "valid": True, "reason": "No scheduler submission required."},),
            scheduler_disposition={},
            lineage={"supersedes": "", "superseded_by": "", "merged_from": ()},
            audit_history=(self._audit_record("mission_not_required", trigger.trigger_id, "", reuse["reason"], emit=False),),
            content_hash="",
        )
        return replace(plan, content_hash=_plan_hash(plan))

    def _audit_record(self, action: str, trigger_id: str, plan_id: str, reason: str, *, emit: bool = True) -> dict[str, Any]:
        record = {
            "audit_id": f"EMP-AUD-{len(self._audit) + 1:06d}",
            "actor_type": "system",
            "actor_id": "EnterpriseMissionPlanner",
            "action": action,
            "timestamp": utc_timestamp(),
            "trigger_ids": (trigger_id,) if trigger_id else (),
            "mission_plan_id": plan_id,
            "plan_version": self._plans.get(plan_id, MissionPlanRecord).__name__ if False else "",
            "reason": reason,
            "correlation_id": plan_id or trigger_id,
        }
        record["content_hash"] = sha256(json.dumps(record, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        if emit:
            self._audit.append(record)
        return record

    def _metrics(self) -> dict[str, Any]:
        plans = tuple(self._plans.values())
        active_plans = tuple(item for item in plans if item.status != MissionPlanStatus.NOT_REQUIRED)
        assignment_counts = [len(item.office_assignments) for item in active_plans]
        return {
            "triggersReceived": len(self._triggers),
            "invalidTriggers": len(self._dead_letters),
            "noActionDecisions": sum(1 for item in plans if item.status == MissionPlanStatus.NOT_REQUIRED),
            "localResolutions": sum(1 for item in plans if item.necessity_decision == "USE_CACHED_OR_LOCAL_RESULT"),
            "cacheResolutions": sum(1 for item in plans if item.reuse_decision.get("cache_reference")),
            "newPlansCreated": len(active_plans),
            "deltaPlansCreated": sum(1 for item in plans if item.delta_decision.get("delta_mission")),
            "plansMerged": len(self._merge_records),
            "plansSuperseded": len(self._supersession_records),
            "plansDeferred": sum(1 for item in plans if item.status == MissionPlanStatus.SCHEDULER_DEFERRED),
            "plansRejected": sum(1 for item in plans if item.status == MissionPlanStatus.SCHEDULER_REJECTED),
            "plansAuthorized": sum(1 for item in plans if item.status == MissionPlanStatus.SCHEDULER_AUTHORIZED),
            "averageOfficesPerPlan": round(sum(assignment_counts) / max(1, len(assignment_counts)), 2),
            "fullEnterprisePlansCreated": sum(1 for count in assignment_counts if count >= 6),
            "fullEnterprisePlansPrevented": sum(len(item.excluded_offices) > 2 for item in plans),
            "estimatedCostPerPlan": round(sum(item.resource_envelope.estimated_cost_usd for item in active_plans) / max(1, len(active_plans)), 4),
            "estimatedApiCallsPerPlan": round(sum(item.resource_envelope.api_call_ceiling for item in active_plans) / max(1, len(active_plans)), 2),
            "duplicateMissionSuppression": len(self._merge_records),
        }


def _default_templates() -> dict[str, MissionTemplateRecord]:
    return {
        "position_safety_review_v1": MissionTemplateRecord("position_safety_review_v1", "1.0", MissionType.POSITION_SAFETY_REVIEW, (MissionTriggerType.VALIDATED_EVENT, MissionTriggerType.DUTY_OFFICER_RECOMMENDATION), ("Position Lifecycle", "Risk"), ("Trader", "Historian"), ("Seeker", "Academy", "Strategic Intelligence"), ("Position Lifecycle", "Risk", "Trader", "Historian"), "safety", 420, 2, ("Produce hold, reduce, exit, or monitor recommendation.", "Record supporting surveillance and risk evidence."), "Review an open position after a safety-relevant event."),
        "broker_reconciliation_v1": MissionTemplateRecord("broker_reconciliation_v1", "1.0", MissionType.BROKER_RECONCILIATION, (MissionTriggerType.VALIDATED_EVENT, MissionTriggerType.DUTY_OFFICER_RECOMMENDATION), ("Trader", "Performance Truth", "Risk"), ("Historian",), ("Seeker", "Academy", "Strategic Intelligence"), ("Trader", "Performance Truth", "Risk", "Historian"), "integrity", 360, 1, ("Reconcile broker/order status against internal records.", "Escalate mismatches."), "Resolve order or broker truth mismatches."),
        "end_of_day_reconciliation_v1": MissionTemplateRecord("end_of_day_reconciliation_v1", "1.0", MissionType.END_OF_DAY_RECONCILIATION, (MissionTriggerType.SCHEDULED_OBLIGATION, MissionTriggerType.POLICY_REQUIREMENT), ("Trader", "Performance Truth", "Risk", "Historian"), (), ("Seeker", "Analyst", "Academy", "Strategic Intelligence"), ("Trader", "Performance Truth", "Risk", "Historian"), "routine", 600, 2, ("Validate ledgers and daily truth records.", "Carry unresolved items forward."), "Daily ledger and trading truth reconciliation."),
        "commander_briefing_v1": MissionTemplateRecord("commander_briefing_v1", "1.0", MissionType.COMMANDER_BRIEFING, (MissionTriggerType.SCHEDULED_OBLIGATION, MissionTriggerType.COMMANDER_DIRECTIVE), ("Executive",), ("Historian", "Risk"), ("Seeker", "Trader", "Academy"), ("Executive", "Historian", "Risk"), "briefing", 240, 1, ("Produce deterministic Commander briefing record.",), "Create a bounded Commander briefing from authoritative records."),
        "earnings_reassessment_v1": MissionTemplateRecord("earnings_reassessment_v1", "1.0", MissionType.EARNINGS_REASSESSMENT, (MissionTriggerType.VALIDATED_EVENT, MissionTriggerType.COMMANDER_DIRECTIVE), ("Librarian", "Analyst"), ("Risk",), ("Seeker", "Academy", "Strategic Intelligence"), ("Librarian", "Analyst", "Risk"), "delta", 900, 3, ("Update valuation and risk sections affected by new guidance.",), "Perform a delta reassessment after earnings or guidance change."),
        "opportunity_scan_v1": MissionTemplateRecord("opportunity_scan_v1", "1.0", MissionType.OPPORTUNITY_SCAN, (MissionTriggerType.SCHEDULED_OBLIGATION,), ("Seeker",), ("Analyst",), ("Trader", "Academy"), ("Seeker", "Analyst"), "research", 900, 3, ("Produce bounded candidate list or no-op result.",), "Run a bounded scheduled opportunity scan."),
        "strategic_research_v1": MissionTemplateRecord("strategic_research_v1", "1.0", MissionType.STRATEGIC_RESEARCH, (MissionTriggerType.COMMANDER_DIRECTIVE, MissionTriggerType.MANUAL_REQUEST), ("Strategic Intelligence",), ("Librarian", "Analyst"), ("Trader", "Academy"), ("Strategic Intelligence", "Librarian", "Analyst"), "research", 1200, 3, ("Produce strategic assessment with evidence references.",), "Bounded strategic research request."),
        "information_refresh_v1": MissionTemplateRecord("information_refresh_v1", "1.0", MissionType.INFORMATION_REFRESH, (MissionTriggerType.VALIDATED_EVENT, MissionTriggerType.MANUAL_REQUEST), ("Librarian",), ("Analyst",), ("Trader", "Academy"), ("Librarian", "Analyst"), "local", 300, 1, ("Refresh required information artifact.",), "Refresh stale information with minimum office participation."),
        "enterprise_recovery_v1": MissionTemplateRecord("enterprise_recovery_v1", "1.0", MissionType.ENTERPRISE_RECOVERY, (MissionTriggerType.ENTERPRISE_RECOVERY, MissionTriggerType.VALIDATED_EVENT), ("Executive", "Infrastructure"), ("Risk",), ("Seeker", "Academy"), ("Executive", "Infrastructure", "Risk"), "recovery", 600, 1, ("Contain failure and create recovery evidence.",), "Plan enterprise recovery or system integrity response."),
        "cost_review_v1": MissionTemplateRecord("cost_review_v1", "1.0", MissionType.COST_REVIEW, (MissionTriggerType.COMMANDER_DIRECTIVE, MissionTriggerType.VALIDATED_EVENT), ("Infrastructure", "Executive"), (), ("Trader", "Seeker", "Academy"), ("Infrastructure", "Executive"), "local", 240, 0, ("Report credit and runtime posture.",), "Review enterprise credit and runtime cost state."),
    }


def _default_capabilities() -> dict[str, dict[str, Any]]:
    return {
        "Executive": {"mission": "enterprise coordination", "local": False},
        "Seeker": {"mission": "candidate discovery", "local": False},
        "Analyst": {"mission": "decision analysis", "local": False},
        "Risk": {"mission": "risk control", "local": False},
        "Trader": {"mission": "order and execution lifecycle", "local": False},
        "Historian": {"mission": "truth learning and records", "local": False},
        "Librarian": {"mission": "knowledge retrieval", "local": False},
        "Academy": {"mission": "capability development", "local": False},
        "Strategic Intelligence": {"mission": "strategic intelligence", "local": False},
        "Infrastructure": {"mission": "runtime and system integrity", "local": False},
        "Performance Truth": {"mission": "deterministic ledger truth service", "local": True},
        "Position Lifecycle": {"mission": "deterministic position lifecycle service", "local": True},
    }


def _trigger_from_event(event: dict[str, Any]) -> MissionTrigger:
    event_type = str(event.get("event_type", event.get("eventType", "")))
    trigger_id = f"EMP-TRG-EVT-{event.get('event_id', event.get('eventId', len(event_type)))}"
    return MissionTrigger(
        trigger_id=trigger_id,
        trigger_type=MissionTriggerType.VALIDATED_EVENT,
        source_event_id=str(event.get("event_id", event.get("eventId", ""))),
        source_event_group_id=str(event.get("event_group_id", "")),
        source_schedule_id="",
        source_directive_id="",
        source_duty_officer_id="",
        title=str(event.get("title", event_type or "Validated Event")),
        summary=str(event.get("summary", "")),
        subject_type=str(event.get("subject_type", "record")),
        subject_id=str(event.get("subject_id", event.get("ticker", event.get("position_id", "")))),
        ticker=str(event.get("ticker", "")),
        position_id=str(event.get("position_id", "")),
        order_id=str(event.get("order_id", "")),
        workflow_id=str(event.get("workflow_id", "")),
        severity=str(event.get("severity", "")),
        urgency=str(event.get("urgency", "")),
        materiality=str(event.get("materiality", "")),
        confidence=float(event.get("confidence", 0.95) or 0.95),
        requested_mission_type=str(event.get("recommended_mission_type", event_type)),
        recommended_offices=tuple(event.get("recommended_offices", ()) or ()),
        earliest_start_at=utc_timestamp(),
        deadline_at=str(event.get("expires_at", "")),
        expires_at=str(event.get("expires_at", "")),
        provenance=dict(event.get("provenance", {})),
        metadata=dict(event.get("metadata", {})) | {"event_type": event_type},
        received_at=utc_timestamp(),
    )


def _trigger_from_commander_request(request: dict[str, Any]) -> MissionTrigger:
    directive = str(request.get("directiveId", request.get("directive_id", f"CMD-{sha256(json.dumps(request, sort_keys=True, default=str).encode('utf-8')).hexdigest()[:8]}")))
    summary = str(request.get("summary", request.get("objective", request.get("task", "Commander requested bounded mission planning."))))
    return MissionTrigger(
        trigger_id=f"EMP-TRG-CMD-{directive}",
        trigger_type=MissionTriggerType.COMMANDER_DIRECTIVE,
        source_event_id="",
        source_event_group_id="",
        source_schedule_id="",
        source_directive_id=directive,
        source_duty_officer_id="",
        title=str(request.get("title", "Commander Directive")),
        summary=summary,
        subject_type=str(request.get("subjectType", request.get("subject_type", "directive"))),
        subject_id=str(request.get("subjectId", request.get("subject_id", directive))),
        ticker=str(request.get("ticker", "")),
        position_id=str(request.get("positionId", request.get("position_id", ""))),
        order_id=str(request.get("orderId", request.get("order_id", ""))),
        workflow_id="",
        severity=str(request.get("severity", "moderate")),
        urgency=str(request.get("urgency", "prompt")),
        materiality=str(request.get("materiality", "material")),
        confidence=1.0,
        requested_mission_type=str(request.get("missionType", request.get("mission_type", ""))),
        recommended_offices=tuple(request.get("recommendedOffices", request.get("recommended_offices", ())) or ()),
        earliest_start_at=utc_timestamp(),
        deadline_at=str(request.get("deadline", "")),
        expires_at=str(request.get("expiresAt", "")),
        provenance={"source": "Commander"},
        metadata=dict(request.get("metadata", {})) | {"event_type": summary},
        received_at=utc_timestamp(),
    )


def _trigger_from_duty_decision(decision: dict[str, Any]) -> MissionTrigger:
    request = decision.get("request", {})
    decision_id = str(decision.get("decision_id", decision.get("decisionId", "ODO-DECISION")))
    return MissionTrigger(
        trigger_id=f"EMP-TRG-ODO-{decision_id}",
        trigger_type=MissionTriggerType.DUTY_OFFICER_RECOMMENDATION,
        source_event_id=str(decision.get("event_reference", request.get("eventReference", ""))),
        source_event_group_id="",
        source_schedule_id="",
        source_directive_id=str(decision.get("commander_directive_id", "")),
        source_duty_officer_id=decision_id,
        title="Duty Officer Recommendation",
        summary=str(decision.get("explanation", "Duty Officer recommended scheduler review.")),
        subject_type="office_request",
        subject_id=str(decision.get("office_id", decision.get("officeId", ""))),
        ticker="",
        position_id=str(decision.get("position_id", "")),
        order_id=str(decision.get("order_id", "")),
        workflow_id=str(decision.get("workflow_id", "")),
        severity="high" if decision.get("wake_recommendation") else "moderate",
        urgency="immediate" if decision.get("wake_recommendation") else "prompt",
        materiality="material",
        confidence=float(decision.get("confidence", 0.8) or 0.8),
        requested_mission_type=str(decision.get("request_type", "commander_directed")),
        recommended_offices=(str(decision.get("office_id", "")),) if decision.get("office_id") else (),
        earliest_start_at=utc_timestamp(),
        deadline_at="",
        expires_at="",
        provenance={"source": "OfficeDutyOfficer"},
        metadata={"event_type": str(decision.get("reason_code", ""))},
        received_at=utc_timestamp(),
    )


def _trigger_from_schedule(obligation: dict[str, Any]) -> MissionTrigger:
    schedule_id = str(obligation.get("mission_id", obligation.get("template_id", obligation.get("scheduleId", "scheduled"))))
    mission_type = str(obligation.get("mission_type", obligation.get("template_id", "")))
    return MissionTrigger(
        trigger_id=f"EMP-TRG-SCH-{schedule_id}",
        trigger_type=MissionTriggerType.SCHEDULED_OBLIGATION,
        source_event_id="",
        source_event_group_id="",
        source_schedule_id=schedule_id,
        source_directive_id="",
        source_duty_officer_id="",
        title=str(obligation.get("mission_name", obligation.get("title", "Scheduled Obligation"))),
        summary=str(obligation.get("description", "Scheduled obligation requires bounded mission planning.")),
        subject_type="schedule",
        subject_id=schedule_id,
        ticker="",
        position_id="",
        order_id="",
        workflow_id="",
        severity=str(obligation.get("severity", "informational")),
        urgency=str(obligation.get("urgency", "routine")),
        materiality=str(obligation.get("materiality", "minor")),
        confidence=1.0,
        requested_mission_type=mission_type,
        recommended_offices=tuple(obligation.get("required_offices", ()) or ()),
        earliest_start_at=str(obligation.get("scheduled_start", utc_timestamp())),
        deadline_at="",
        expires_at="",
        provenance={"source": "EnterpriseOperationsScheduler"},
        metadata={"event_type": mission_type},
        received_at=utc_timestamp(),
    )


def _trigger_from_dict(item: dict[str, Any]) -> MissionTrigger:
    data = dict(item)
    data["trigger_type"] = MissionTriggerType(data["trigger_type"])
    data["recommended_offices"] = tuple(data.get("recommended_offices", ()))
    return MissionTrigger(**{key: data.get(key) for key in MissionTrigger.__dataclass_fields__})


def _plan_from_dict(item: dict[str, Any]) -> MissionPlanRecord:
    data = dict(item)
    data["status"] = MissionPlanStatus(data["status"])
    data["mission_type"] = MissionType(data["mission_type"])
    data["priority_class"] = MissionPriorityClass(data["priority_class"])
    data["source_trigger_ids"] = tuple(data.get("source_trigger_ids", ()))
    data["objective"] = MissionObjective(**data["objective"])
    data["office_assignments"] = tuple(MissionOfficeAssignment(**assignment) for assignment in data.get("office_assignments", ()))
    data["prohibited_offices"] = tuple(data.get("prohibited_offices", ()))
    data["excluded_offices"] = tuple(data.get("excluded_offices", ()))
    data["dependencies"] = tuple(MissionDependency(**dep) for dep in data.get("dependencies", ()))
    data["input_requirements"] = tuple(MissionInputRequirement(**inp) for inp in data.get("input_requirements", ()))
    data["output_contracts"] = tuple(MissionOutputContract(**out) for out in data.get("output_contracts", ()))
    data["resource_envelope"] = MissionResourceEnvelope(**data["resource_envelope"])
    data["completion_policy"] = MissionCompletionPolicy(**data["completion_policy"])
    data["planning_explanation"] = tuple(data.get("planning_explanation", ()))
    data["validation_results"] = tuple(data.get("validation_results", ()))
    data["audit_history"] = tuple(data.get("audit_history", ()))
    return MissionPlanRecord(**{key: data.get(key) for key in MissionPlanRecord.__dataclass_fields__})


def _mission_type(value: str) -> MissionType | None:
    normalized = str(value or "").replace("-", "_").lower()
    for item in MissionType:
        if item.value == normalized:
            return item
    return None


def _objective_for(trigger: MissionTrigger, template: MissionTemplateRecord) -> MissionObjective:
    subject = trigger.subject_id or trigger.position_id or trigger.order_id or trigger.ticker or trigger.trigger_id
    action = template.mission_type.value.replace("_", " ")
    decision = "Determine the bounded recommendation or no-action result required by the trigger."
    if template.mission_type == MissionType.POSITION_SAFETY_REVIEW:
        decision = "Should ARGOS hold, reduce, exit, or continue monitoring this position?"
    elif template.mission_type == MissionType.BROKER_RECONCILIATION:
        decision = "Does broker/order truth match internal ARGOS truth, and what escalation is required?"
    return MissionObjective(
        objective_id=f"EMP-OBJ-{sha256((trigger.trigger_id + template.template_id).encode('utf-8')).hexdigest()[:8].upper()}",
        primary_objective=f"Complete {action} for {subject} using only the scope required by the trigger.",
        decision_question=decision,
        subject_type=trigger.subject_type,
        subject_id=subject,
        scope_inclusions=("source trigger", "authoritative current records", "affected outputs only"),
        scope_exclusions=("unrelated offices", "open-ended market analysis", "broker execution", "ledger mutation"),
        required_decisions=("mission outcome", "escalation need"),
        required_outputs=template.completion_criteria,
        success_definition="All required output contracts are produced or a documented no-action result is returned.",
        failure_definition="Required inputs unavailable, dependency fails, or output contract cannot be satisfied inside limits.",
        deadline_at=trigger.deadline_at,
    )


def _delta_decision(trigger: MissionTrigger) -> dict[str, Any]:
    changed = tuple(trigger.metadata.get("changed_fields", ()) or trigger.metadata.get("changedFields", ()) or ())
    if changed:
        return {"delta_mission": True, "changed_fields": changed, "full_reassessment_required": False, "reason": "Only listed fields changed; preliminary dependency impact prefers delta work."}
    if any(word in (trigger.summary + trigger.title).lower() for word in ("guidance", "earnings", "price", "volatility")):
        return {"delta_mission": True, "changed_fields": ("price_or_information_delta",), "full_reassessment_required": False, "reason": "Trigger indicates a bounded state change."}
    return {"delta_mission": False, "changed_fields": (), "full_reassessment_required": False, "reason": "No bounded delta signal was supplied."}


def _assignment_for(office: str, index: int, trigger: MissionTrigger, template: MissionTemplateRecord, capability: dict[str, Any]) -> MissionOfficeAssignment:
    local = bool(capability.get("local"))
    return MissionOfficeAssignment(
        office_id=office,
        participation_type="deterministic_service" if local else "mandatory",
        sequence_index=index,
        responsibility=f"{office} provides {capability.get('mission', 'assigned mission work')} for {template.mission_type.value}.",
        required_inputs=("mission_plan", "source_trigger", "authoritative_records"),
        required_outputs=("mission_output", "audit_evidence") if not local else ("deterministic_truth_reference",),
        upstream_dependencies=() if index == 1 else (f"node_{index - 1}",),
        downstream_recipients=(f"node_{index + 1}",),
        max_runtime_seconds=max(30, template.runtime_ceiling_seconds // max(1, len(template.default_sequence))),
        max_api_calls=0 if local else max(0, template.api_call_ceiling // max(1, len(template.default_sequence))),
        max_input_tokens=None if local else 6000,
        max_output_tokens=None if local else 1200,
        allowed_model_classes=() if local else ("deterministic", "authorized_low_cost"),
        paid_data_allowed=False,
        optional=False,
        omission_condition="May be omitted only by new plan version.",
        skip_condition="Skip only if required input is already satisfied by validated deterministic record.",
        completion_condition="Produce required output contract and audit evidence.",
        failure_behavior="Return mission to Scheduler for revision or escalation.",
        inclusion_reason=f"Included because {template.template_id} requires {office} for {trigger.trigger_type.value}.",
    )


def _dependencies_for(assignments: tuple[MissionOfficeAssignment, ...]) -> tuple[MissionDependency, ...]:
    dependencies = []
    for index, assignment in enumerate(assignments[1:], start=2):
        dependencies.append(
            MissionDependency(
                dependency_id=f"EMP-DEP-{index - 1:03d}",
                upstream_node_id=assignments[index - 2].office_id,
                downstream_node_id=assignment.office_id,
                dependency_type="sequence",
                required=True,
                satisfaction_condition="Upstream office or deterministic service produces required output.",
                failure_behavior="Stop mission and preserve audit evidence.",
                timeout_seconds=assignment.max_runtime_seconds,
            )
        )
    return tuple(dependencies)


def _inputs_for(trigger: MissionTrigger, template: MissionTemplateRecord, delta: dict[str, Any]) -> tuple[MissionInputRequirement, ...]:
    return (
        MissionInputRequirement("EMP-IN-001", "Source Trigger", "Validated trigger that justified planning.", "trigger", "Enterprise Mission Planner", True, None, trigger.trigger_id, False, "trigger_must_be_valid", "", "return_for_revision"),
        MissionInputRequirement("EMP-IN-002", "Authoritative Runtime State", "Current ARGOS runtime state relevant to the mission.", "runtime_snapshot", "ARGOS Control Panel Runtime", True, 300, "", True, "freshness_or_degraded_state_required", "last_validated_snapshot", "defer_or_escalate"),
        MissionInputRequirement("EMP-IN-003", "Prior Product Review", "Existing products, cache, or deterministic truth that may reduce work.", "cache_or_truth", "Future EO-CG / existing truth records", False, 3600, "", not delta.get("delta_mission"), "reuse_review_required", "", "continue_with_new_work"),
    )


def _outputs_for(template: MissionTemplateRecord) -> tuple[MissionOutputContract, ...]:
    return tuple(
        MissionOutputContract(
            output_id=f"EMP-OUT-{index:03d}",
            name=f"Output {index}",
            description=criterion,
            required=True,
            expected_schema=("summary", "supporting_evidence", "audit_reference"),
            validation_rule="structured_output_contains_required_fields",
            consumer="Enterprise Operations Scheduler",
            completion_signal="output_contract_satisfied",
        )
        for index, criterion in enumerate(template.completion_criteria, start=1)
    )


def _resource_envelope(template: MissionTemplateRecord, assignments: tuple[MissionOfficeAssignment, ...], delta: dict[str, Any]) -> MissionResourceEnvelope:
    multiplier = 0.65 if delta.get("delta_mission") else 1.0
    api_calls = max(0, int(round(template.api_call_ceiling * multiplier)))
    runtime = max(60, int(template.runtime_ceiling_seconds * multiplier))
    cost = round(api_calls * 0.01, 4)
    return MissionResourceEnvelope(runtime, template.runtime_ceiling_seconds + 300, api_calls, api_calls * 4000, 0, cost, template.cost_class, 0.82, ("template_version", template.version, "office_count", str(len(assignments)), "delta_multiplier", str(multiplier)))


def _completion_policy(template: MissionTemplateRecord) -> MissionCompletionPolicy:
    return MissionCompletionPolicy(template.completion_criteria, ("Required input unavailable.", "Output contract invalid.", "Dependency timeout.", "Resource ceiling exceeded."), 0 if template.cost_class in {"safety", "integrity"} else 1, "Return to Scheduler with bounded fallback recommendation.", "Defer when source freshness or market condition blocks safe work.", "Cancel draft or queued plan without mutating source records.", ("critical dependency failure", "impossible deadline", "source truth conflict"), ("preserve audit trail", "return offices to sleep after EOS execution"))


def _validate_plan(trigger: MissionTrigger, template: MissionTemplateRecord, assignments: tuple[MissionOfficeAssignment, ...], dependencies: tuple[MissionDependency, ...], inputs: tuple[MissionInputRequirement, ...], outputs: tuple[MissionOutputContract, ...], envelope: MissionResourceEnvelope) -> list[dict[str, Any]]:
    assigned = {item.office_id for item in assignments}
    deps = [(item.upstream_node_id, item.downstream_node_id) for item in dependencies]
    return [
        {"rule": "specific_objective", "valid": bool(trigger.subject_id or trigger.position_id or trigger.order_id or trigger.ticker or trigger.source_directive_id or trigger.source_schedule_id), "reason": "Plan has a bounded subject."},
        {"rule": "minimum_workforce", "valid": bool(assignments), "reason": "Plan includes at least one authorized participant."},
        {"rule": "prohibited_offices_excluded", "valid": not (assigned & set(template.prohibited_offices)), "reason": "No prohibited offices are assigned."},
        {"rule": "registered_offices", "valid": all(item.office_id in _default_capabilities() for item in assignments), "reason": "All assignments are registered."},
        {"rule": "acyclic_dependencies", "valid": len(deps) == len(set(deps)), "reason": "Dependency graph has no duplicate edge cycle."},
        {"rule": "required_inputs", "valid": any(item.required for item in inputs), "reason": "Required inputs are declared."},
        {"rule": "output_contracts", "valid": bool(outputs), "reason": "Required outputs are declared."},
        {"rule": "bounded_resources", "valid": envelope.runtime_ceiling_seconds > 0 and envelope.api_call_ceiling >= 0 and envelope.estimated_cost_usd >= 0, "reason": "Runtime, API, and cost ceilings are bounded."},
    ]


def _priority_for(trigger: MissionTrigger, template: MissionTemplateRecord) -> MissionPriorityClass:
    if trigger.severity in {"emergency"} or template.mission_type == MissionType.ENTERPRISE_RECOVERY:
        return MissionPriorityClass.EMERGENCY_RECOVERY
    if template.mission_type == MissionType.POSITION_SAFETY_REVIEW:
        return MissionPriorityClass.POSITION_SAFETY
    if template.mission_type in {MissionType.BROKER_RECONCILIATION, MissionType.LEDGER_RECONCILIATION, MissionType.END_OF_DAY_RECONCILIATION}:
        return MissionPriorityClass.BROKER_LEDGER_INTEGRITY
    if template.mission_type in {MissionType.PORTFOLIO_RISK_REVIEW, MissionType.EMERGENCY_RISK_REVIEW}:
        return MissionPriorityClass.RISK_CONTROL
    if trigger.trigger_type == MissionTriggerType.COMMANDER_DIRECTIVE:
        return MissionPriorityClass.COMMANDER_DIRECTED
    if template.mission_type == MissionType.STRATEGIC_RESEARCH:
        return MissionPriorityClass.STRATEGIC_INTELLIGENCE
    return MissionPriorityClass.TACTICAL_EVALUATION


def _planning_explanation(trigger: MissionTrigger, template: MissionTemplateRecord, assignments: tuple[MissionOfficeAssignment, ...], excluded: tuple[dict[str, str], ...], reuse: dict[str, Any], delta: dict[str, Any]) -> tuple[str, ...]:
    return (
        f"Trigger {trigger.trigger_id} requires planning because {reuse.get('reason')}.",
        f"Template {template.template_id} v{template.version} was selected for {template.mission_type.value}.",
        f"Minimum workforce contains {', '.join(item.office_id for item in assignments)}.",
        f"{len(excluded)} offices or services were excluded to prevent unnecessary activation.",
        f"Delta policy: {delta.get('reason')}.",
        "Planner submits only to EOS review and does not authorize execution.",
    )


def _plan_hash(plan: MissionPlanRecord) -> str:
    data = _snapshot_dataclass(replace(plan, content_hash=""))
    return sha256(json.dumps(data, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _eos_priority(priority: MissionPriorityClass) -> str:
    mapping = {
        MissionPriorityClass.EMERGENCY_RECOVERY: "Emergency",
        MissionPriorityClass.POSITION_SAFETY: "Position Safety",
        MissionPriorityClass.BROKER_LEDGER_INTEGRITY: "Broker Ledger Integrity",
        MissionPriorityClass.RISK_CONTROL: "Risk Control",
        MissionPriorityClass.COMMANDER_DIRECTED: "Commander-Directed",
        MissionPriorityClass.STRATEGIC_INTELLIGENCE: "Strategic Intelligence",
    }
    return mapping.get(priority, "Tactical Opportunity Evaluation")


def _minimum_workforce_view(plan: MissionPlanRecord) -> dict[str, Any]:
    return {
        "mission_plan_id": plan.mission_plan_id,
        "included_offices": tuple({"office_id": item.office_id, "reason": item.inclusion_reason, "type": item.participation_type} for item in plan.office_assignments),
        "excluded_offices": plan.excluded_offices,
        "prohibited_offices": plan.prohibited_offices,
        "cache_replaced_offices": tuple(item["office_id"] for item in plan.excluded_offices if "cache" in item["reason"].lower()),
        "deterministic_service_replacements": tuple(item.office_id for item in plan.office_assignments if item.participation_type == "deterministic_service"),
    }


def _dependency_graph_view(plan: MissionPlanRecord) -> dict[str, Any]:
    return {
        "mission_plan_id": plan.mission_plan_id,
        "nodes": tuple(item.office_id for item in plan.office_assignments),
        "edges": tuple({"from": item.upstream_node_id, "to": item.downstream_node_id, "type": item.dependency_type} for item in plan.dependencies),
        "workflow_token_path": tuple(item.office_id for item in sorted(plan.office_assignments, key=lambda entry: entry.sequence_index)),
    }


def _snapshot_dataclass(item: Any) -> dict[str, Any]:
    return _json_safe(asdict(item))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, tuple):
        return tuple(_json_safe(item) for item in value)
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value
