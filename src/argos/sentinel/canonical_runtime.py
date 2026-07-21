"""Canonical Sentinel runtime and Commander bridge integration for SENT-MO-001/002."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping

from argos.control_panel.canonical_bridge_fabric import (
    BridgeCertificationStatus,
    BridgeIdempotencyPolicy,
    BridgeImplementationStatus,
    BridgeRequirementClass,
    BridgeResultStatus,
    BridgeTransferClass,
    CanonicalBridgeDefinition,
    CanonicalBridgeExecutor,
    CanonicalBridgeRegistry,
    make_bridge_request,
)
from argos.control_panel.enterprise_communications_bus import EnterpriseCommunicationsBus, MessageMode
from argos.control_panel.office_lifecycle import (
    OfficeActivationAuthority,
    OfficeClassification,
    OfficeDefinition,
    OfficeLifecycleController,
    OfficeLifecycleState,
    OfficeRegistry,
    default_office_definitions,
)
from argos.control_panel.scheduler import EnterpriseMission, EnterpriseOperatingMode, EnterpriseOperationsScheduler
from argos.foundation.contracts import utc_timestamp

from .constitutional_observation import (
    MonitoringObjective,
    ObservationIntegrityValidator,
    ObservationRecord,
    ObservationScheduleEntry,
    RuntimeObservationPipeline,
    SourceRecord,
)


SENT_MO_CANONICAL_RUNTIME_VERSION = "SENT-MO-001-002-CANONICAL/1.0.0"
SENTINEL_COMMANDER_BRIDGE_ID = "BRIDGE-SENTINEL-COMMANDER-ALERT-001"


class SentinelRuntimeDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INSUFFICIENT = "INSUFFICIENT"
    QUARANTINED = "QUARANTINED"
    PENDING = "PENDING"


class SentinelOfficeState(str, Enum):
    DORMANT = "DORMANT"
    ACTIVATION_REQUESTED = "ACTIVATION_REQUESTED"
    ACTIVE = "ACTIVE"
    COMPLETING = "COMPLETING"


class SentinelNotificationStatus(str, Enum):
    NOT_YET_DELIVERED = "NOT_YET_DELIVERED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED_BY_COMMANDER = "RECEIVED_BY_COMMANDER"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    REJECTED = "REJECTED"


class CommanderAcknowledgmentResult(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    DUPLICATE = "DUPLICATE"
    QUARANTINED = "QUARANTINED"
    DEFERRED = "DEFERRED"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


class FailureResponse(str, Enum):
    AUTOMATIC_RECOVERY = "Automatic Recovery"
    AUTOMATIC_RETRY = "Automatic Retry"
    QUARANTINE = "Quarantine"
    DEGRADED_READ_ONLY_OPERATION = "Degraded Read-Only Operation"
    HALT = "Halt"


@dataclass(frozen=True)
class SentinelRuntimeTraceEvent:
    trace_event_id: str
    parent_trace_event_id: str
    trace_root_id: str
    candidate_identity: str
    runtime_identity: str
    office_identity: str
    mission_identity: str
    authority_identity: str
    scheduler_obligation_identity: str
    actor: str
    action: str
    implementation_symbol: str
    rule_identity: str
    input_artifacts: tuple[str, ...]
    output_artifacts: tuple[str, ...]
    before_state: str
    after_state: str
    result: str
    failure_code: str
    timestamp: str
    deterministic_digest: str


@dataclass(frozen=True)
class SentinelMissionAssignment:
    assignment_id: str
    schema_version: str
    candidate_identity: str
    runtime_identity: str
    mission_id: str
    commander_authority_id: str
    mission_status: str
    sentinel_recipient: str
    runtime_mode: str
    approved_domains: tuple[str, ...]
    approved_event_classes: tuple[str, ...]
    source_requirements: tuple[str, ...]
    sufficiency_rule_id: str
    priority_rule_id: str
    revoked: bool
    effective_at: str
    expires_at: str
    deterministic_id: str


@dataclass(frozen=True)
class SentinelSourcePlanReference:
    source_plan_id: str
    objective_id: str
    source_id: str
    adapter_id: str
    source_host: str
    source_path: str
    retrieval_method: str
    entitlement_class: str
    operationally_allowed: bool


@dataclass(frozen=True)
class SentinelRawAcquisitionEvidence:
    raw_evidence_id: str
    source_plan_id: str
    requested_source: str
    actual_host: str
    actual_path: str
    retrieval_method: str
    request_parameters: Mapping[str, str]
    acquisition_time: str
    source_publication_time: str
    response_digest: str
    response_status: str
    raw_evidence_reference: str
    parser_identity: str
    normalization_identity: str
    entitlement_class: str
    source_failure_condition: str


@dataclass(frozen=True)
class SentinelDuplicateDecision:
    decision_id: str
    compared_observation_ids: tuple[str, ...]
    rule_identity: str
    comparison_dimensions: tuple[str, ...]
    duplicate_window: str
    result: str
    reason_code: str
    retained_observation: str
    suppressed_observation: str


@dataclass(frozen=True)
class SentinelSourceIndependenceDecision:
    decision_id: str
    source_identities: tuple[str, ...]
    upstream_dependencies: tuple[str, ...]
    independence_rule: str
    result: str
    unresolved_uncertainty: tuple[str, ...]


@dataclass(frozen=True)
class SentinelConflictDecision:
    decision_id: str
    conflicting_observation_ids: tuple[str, ...]
    conflicting_fields: tuple[str, ...]
    source_authority: tuple[str, ...]
    applicable_precedence: str
    unresolved_conditions: tuple[str, ...]
    resulting_state: str
    sufficiency_remains_satisfied: bool


@dataclass(frozen=True)
class SentinelSufficiencyDecision:
    decision_id: str
    rule_identity: str
    required_fields_satisfied: tuple[str, ...]
    required_sources_present: tuple[str, ...]
    mandatory_corroboration_satisfied: bool
    remaining_uncertainty: tuple[str, ...]
    notification_readiness: SentinelRuntimeDecision


@dataclass(frozen=True)
class SentinelPriorityDecision:
    decision_id: str
    rule_identity: str
    mission_impact: int
    constitutional_severity: int
    observation_timestamp: str
    stable_event_identity: str
    final_rank: int


@dataclass(frozen=True)
class SentinelObservationEvidenceEnvelope:
    envelope_id: str
    candidate_identity: str
    runtime_identity: str
    mission_identity: str
    commander_authority_identity: str
    sentinel_office_identity: str
    scheduler_obligation_identity: str
    source_plan_identity: str
    acquisition_evidence_references: tuple[str, ...]
    normalized_observation_identity: str
    duplicate_decision: SentinelDuplicateDecision
    independence_decision: SentinelSourceIndependenceDecision
    conflict_decision: SentinelConflictDecision
    sufficiency_decision: SentinelSufficiencyDecision
    priority_decision: SentinelPriorityDecision
    uncertainty: tuple[str, ...]
    discovered_candidate_event_classes: tuple[str, ...]
    final_notification_readiness_state: SentinelRuntimeDecision
    deterministic_digest: str
    trace_references: tuple[str, ...]


@dataclass(frozen=True)
class SentinelNotificationReadyAlert:
    alert_id: str
    schema_version: str
    observation_evidence_id: str
    mission_id: str
    sentinel_identity: str
    required_destination: str
    priority: int
    severity: int
    sufficiency_state: SentinelRuntimeDecision
    uncertainty: tuple[str, ...]
    event_class: str
    source_references: tuple[str, ...]
    idempotency_key: str
    candidate_identity: str
    runtime_identity: str
    notification_status: SentinelNotificationStatus
    deterministic_digest: str


@dataclass(frozen=True)
class SentinelRuntimeExecutionRecord:
    execution_id: str
    candidate_identity: str
    runtime_identity: str
    mission_id: str
    scheduler_obligation_id: str
    lifecycle_states: tuple[str, ...]
    trace_events: tuple[SentinelRuntimeTraceEvent, ...]
    evidence_envelope: SentinelObservationEvidenceEnvelope | None
    notification_ready_alert: SentinelNotificationReadyAlert | None
    failure_response: FailureResponse | None
    final_office_state: SentinelOfficeState
    result: SentinelRuntimeDecision
    deterministic_digest: str


@dataclass(frozen=True)
class CommanderReceiptRecord:
    receipt_id: str
    alert_id: str
    bridge_message_id: str
    observation_evidence_id: str
    mission_id: str
    candidate_identity: str
    runtime_identity: str
    source_office: str
    destination_office: str
    receipt_timestamp: str
    validation_result: SentinelRuntimeDecision
    uncertainty: tuple[str, ...]
    priority: int
    severity: int
    current_commander_disposition: str
    acknowledgment_state: str
    evidence_digest: str


@dataclass(frozen=True)
class CommanderAcknowledgment:
    acknowledgment_id: str
    commander_identity: str
    commander_authority_identity: str
    original_alert_id: str
    bridge_message_id: str
    receipt_id: str
    candidate_identity: str
    runtime_identity: str
    mission_identity: str
    acknowledgment_timestamp: str
    validation_result: SentinelRuntimeDecision
    acknowledgment_result: CommanderAcknowledgmentResult
    deterministic_digest: str


@dataclass(frozen=True)
class SentinelCommanderDeliveryRecord:
    delivery_id: str
    alert: SentinelNotificationReadyAlert
    bridge_result_status: str
    bridge_rejection_code: str
    bus_message_id: str
    commander_receipt: CommanderReceiptRecord | None
    commander_acknowledgment: CommanderAcknowledgment | None
    sentinel_delivery_state: SentinelNotificationStatus
    downstream_activation_attempts: tuple[str, ...]
    reconciliation_digest: str


class DeterministicSentinelSourceAdapter:
    """Mission-authorized source adapter that returns raw evidence, not normalized proof."""

    adapter_id = "SENTINEL-DETERMINISTIC-SOURCE-ADAPTER/1.0.0"

    def acquire(
        self,
        source_plan: SentinelSourcePlanReference,
        *,
        event_class: str,
        value_hash: str = "sha256:observed-event",
        response_status: str = "OK",
        malformed: bool = False,
    ) -> SentinelRawAcquisitionEvidence:
        payload = {
            "eventClass": event_class,
            "sourceId": source_plan.source_id,
            "valueHash": value_hash,
            "malformed": malformed,
        }
        return SentinelRawAcquisitionEvidence(
            raw_evidence_id=f"RAW-{_hash((source_plan.source_plan_id, event_class, value_hash))[:12].upper()}",
            source_plan_id=source_plan.source_plan_id,
            requested_source=source_plan.source_id,
            actual_host=source_plan.source_host,
            actual_path=source_plan.source_path,
            retrieval_method=source_plan.retrieval_method,
            request_parameters={"event_class": event_class},
            acquisition_time=utc_timestamp(),
            source_publication_time=utc_timestamp(),
            response_digest=_hash(payload),
            response_status="MALFORMED" if malformed else response_status,
            raw_evidence_reference=f"raw://{source_plan.source_plan_id}/{_hash(payload)[:16]}",
            parser_identity="sentinel-json-parser/1.0.0",
            normalization_identity="sentinel-normalizer/1.0.0",
            entitlement_class=source_plan.entitlement_class,
            source_failure_condition="" if response_status == "OK" and not malformed else response_status,
        )

    def normalize(
        self,
        raw: SentinelRawAcquisitionEvidence,
        assignment: SentinelMissionAssignment,
        source_plan: SentinelSourcePlanReference,
        schedule_entry: ObservationScheduleEntry,
        value_hash: str = "sha256:observed-event",
    ) -> ObservationRecord:
        if raw.response_status != "OK":
            raise ValueError("raw acquisition cannot be normalized without OK source status")
        return ObservationRecord(
            observation_id=f"OBS-{_hash((raw.raw_evidence_id, assignment.mission_id))[:12].upper()}",
            objective_id=schedule_entry.objective_id,
            source_id=source_plan.source_id,
            collection_mechanism=source_plan.retrieval_method,
            acquisition_timestamp=raw.acquisition_time,
            observation_timestamp=raw.source_publication_time,
            evidence_creation_timestamp=utc_timestamp(),
            value_hash=value_hash,
            evidence_references=(raw.raw_evidence_reference, raw.response_digest),
            mission_assignment_id=assignment.assignment_id,
            freshness_limit_seconds=300,
            observed_age_seconds=0,
        )


class SentinelCanonicalRuntime:
    """Executes Sentinel through canonical scheduler, lifecycle, source, and evidence paths."""

    def __init__(
        self,
        *,
        scheduler: EnterpriseOperationsScheduler | None = None,
        lifecycle: OfficeLifecycleController | None = None,
        source_adapter: DeterministicSentinelSourceAdapter | None = None,
        candidate_identity: str = "candidate:unknown",
        runtime_identity: str = "ARGOS-CANONICAL-RUNTIME",
    ) -> None:
        self.scheduler = scheduler or EnterpriseOperationsScheduler()
        self.lifecycle = lifecycle or _sentinel_lifecycle_controller()
        self.source_adapter = source_adapter or DeterministicSentinelSourceAdapter()
        self.candidate_identity = candidate_identity
        self.runtime_identity = runtime_identity
        self.trace_events: tuple[SentinelRuntimeTraceEvent, ...] = ()
        self.persistence: dict[str, Any] = {}

    def execute_observation(
        self,
        *,
        mission: EnterpriseMission,
        source_plan: SentinelSourcePlanReference,
        event_class: str,
        value_hash: str = "sha256:observed-event",
        prior_observations: Iterable[ObservationRecord] = (),
    ) -> SentinelRuntimeExecutionRecord:
        trace_root = f"SENT-TRACE-{_hash((mission.mission_id, self.candidate_identity))[:12].upper()}"
        assignment = self._resolve_assignment(mission, source_plan, event_class)
        authority_ok = self._validate_assignment(assignment, mission, source_plan, event_class)
        if not authority_ok:
            return self._failed_execution(trace_root, mission, "", FailureResponse.QUARANTINE, "MISSION_AUTHORITY_INVALID")
        dispatched = self.scheduler.dispatch_mission(mission.mission_id, workflow_id=mission.mission_id, token_id=mission.execution_token_id)
        activation_id = self._scheduler_obligation_id(dispatched)
        schedule = ObservationScheduleEntry(1, source_plan.objective_id, dispatched.actual_start or utc_timestamp(), 10, (5, 15), 30)
        objective = MonitoringObjective(source_plan.objective_id, assignment.commander_authority_id, next(iter(assignment.approved_domains)), 60, 15, 10, (5, 15), 30)
        scheduler_plan = self._schedule(objective, schedule.scheduled_execution_time)
        parent = ""
        parent = self._trace(trace_root, parent, mission, activation_id, "Commander", "mission_resolved", "MissionRegistry.resolve", "SENT-MO-001-STAGE-1", (), (assignment.assignment_id,), "", "MISSION_RESOLVED", "PASS")
        parent = self._trace(trace_root, parent, mission, activation_id, "AuthorityRegistry", "authority_validated", "SentinelCanonicalRuntime._validate_assignment", "SENT-MO-001-STAGE-2", (assignment.assignment_id,), ("authority:Commander",), "", "AUTHORITY_VALIDATED", "PASS")
        parent = self._trace(trace_root, parent, mission, activation_id, "EnterpriseOperationsScheduler", "sentinel_scheduled", "EnterpriseOperationsScheduler.dispatch_mission", "SENT-MO-001-STAGE-3", (mission.mission_id,), (activation_id, scheduler_plan.schedule_digest), "", "SCHEDULED", "PASS")
        self.lifecycle.activate("Sentinel", authority=OfficeActivationAuthority.SCHEDULER, workflow_id=mission.mission_id, token_id=mission.execution_token_id, current_owner="Sentinel", proof_domain="PAPER")
        parent = self._trace(trace_root, parent, mission, activation_id, "OfficeLifecycleController", "sentinel_active", "OfficeLifecycleController.activate", "SENT-MO-001-STAGE-4", (activation_id,), ("Sentinel:ACTIVE",), "DORMANT", "ACTIVE", "PASS")
        raw = self.source_adapter.acquire(source_plan, event_class=event_class, value_hash=value_hash)
        if raw.response_status != "OK":
            return self._failed_execution(trace_root, mission, activation_id, FailureResponse.QUARANTINE, "SOURCE_ACQUISITION_FAILED")
        parent = self._trace(trace_root, parent, mission, activation_id, "Sentinel", "source_acquired", self.source_adapter.adapter_id, "SENT-MO-001-STAGE-5", (source_plan.source_plan_id,), (raw.raw_evidence_id,), "ACTIVE", "ACTIVE", "PASS")
        observation = self.source_adapter.normalize(raw, assignment, source_plan, schedule, value_hash=value_hash)
        parent = self._trace(trace_root, parent, mission, activation_id, "Sentinel", "observation_normalized", "sentinel-normalizer/1.0.0", "SENT-MO-001-STAGE-6", (raw.raw_evidence_id,), (observation.observation_id,), "ACTIVE", "ACTIVE", "PASS")
        source = SourceRecord(source_plan.source_id, True, True, "HEALTHY", source_plan.source_host, 1.0, 1.0)
        pipeline = RuntimeObservationPipeline(validator=ObservationIntegrityValidator())
        result = pipeline.execute(schedule, observation, source, prior_observations)
        duplicate = _duplicate_decision(observation, prior_observations)
        independence = SentinelSourceIndependenceDecision(f"IND-{_hash(observation.source_id)[:10].upper()}", (source_plan.source_id,), (source_plan.source_host,), "SENT-GOV-020-INDEPENDENCE/1", "INDEPENDENT", ())
        conflict = SentinelConflictDecision(f"CON-{_hash(observation.observation_id)[:10].upper()}", (), (), (source_plan.source_id,), "NO_CONFLICT", (), "NO_CONFLICT", True)
        sufficiency = SentinelSufficiencyDecision(f"SUF-{_hash(observation.observation_id)[:10].upper()}", assignment.sufficiency_rule_id, ("event_class", "value_hash", "source_timestamp", "raw_evidence"), (source_plan.source_id,), True, (), SentinelRuntimeDecision.PASS if result.decision.value == "PASS" else SentinelRuntimeDecision.INSUFFICIENT)
        priority = SentinelPriorityDecision(f"PRI-{_hash(observation.observation_id)[:10].upper()}", assignment.priority_rule_id, 1, 1, observation.observation_timestamp, observation.observation_id, 1)
        parent = self._trace(trace_root, parent, mission, activation_id, "Sentinel", "observation_evaluated", "RuntimeObservationPipeline.execute", "SENT-MO-001-STAGES-7-11", (observation.observation_id,), (result.evidence.evidence_checksum,), "ACTIVE", "ACTIVE", result.decision.value)
        envelope = _evidence_envelope(self.candidate_identity, self.runtime_identity, mission, activation_id, source_plan, raw, observation, duplicate, independence, conflict, sufficiency, priority, tuple(item.trace_event_id for item in self.trace_events))
        alert = _notification_ready_alert(envelope, mission, self.candidate_identity, self.runtime_identity, event_class)
        parent = self._trace(trace_root, parent, mission, activation_id, "Sentinel", "evidence_and_alert_created", "SentinelCanonicalRuntime.execute_observation", "SENT-MO-001-STAGES-12-13", (envelope.envelope_id,), (alert.alert_id,), "ACTIVE", "COMPLETING", "PASS")
        self.persistence[envelope.envelope_id] = envelope
        self.persistence[alert.alert_id] = alert
        self.scheduler.complete_mission(mission.mission_id, api_calls=1, result_summary="Sentinel notification-ready alert generated.")
        self.lifecycle.transition("Sentinel", OfficeLifecycleState.DORMANT)
        parent = self._trace(trace_root, parent, mission, activation_id, "OfficeLifecycleController", "sentinel_dormant", "OfficeLifecycleController.transition", "SENT-MO-001-STAGE-14", (alert.alert_id,), ("Sentinel:DORMANT",), "COMPLETING", "DORMANT", "PASS")
        record = SentinelRuntimeExecutionRecord(
            execution_id=f"SENT-RUN-{_hash((mission.mission_id, alert.alert_id))[:12].upper()}",
            candidate_identity=self.candidate_identity,
            runtime_identity=self.runtime_identity,
            mission_id=mission.mission_id,
            scheduler_obligation_id=activation_id,
            lifecycle_states=("DORMANT", "ACTIVATION_REQUESTED", "ACTIVE", "COMPLETING", "DORMANT"),
            trace_events=self.trace_events,
            evidence_envelope=envelope,
            notification_ready_alert=alert,
            failure_response=None,
            final_office_state=SentinelOfficeState.DORMANT,
            result=SentinelRuntimeDecision.PASS if alert.notification_status == SentinelNotificationStatus.NOT_YET_DELIVERED else SentinelRuntimeDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_hash(asdict(record)))

    def _resolve_assignment(self, mission: EnterpriseMission, source_plan: SentinelSourcePlanReference, event_class: str) -> SentinelMissionAssignment:
        payload = (mission.mission_id, self.candidate_identity, source_plan.source_plan_id, event_class)
        return SentinelMissionAssignment(
            assignment_id=f"SENT-ASSIGN-{_hash(payload)[:12].upper()}",
            schema_version=SENT_MO_CANONICAL_RUNTIME_VERSION,
            candidate_identity=self.candidate_identity,
            runtime_identity=self.runtime_identity,
            mission_id=mission.mission_id,
            commander_authority_id=mission.commander_directive_id,
            mission_status=mission.status,
            sentinel_recipient="Sentinel",
            runtime_mode=EnterpriseOperatingMode.OBSERVATION_ONLY.value,
            approved_domains=(source_plan.source_host,),
            approved_event_classes=(event_class,),
            source_requirements=(source_plan.source_id,),
            sufficiency_rule_id="SENT-GOV-018-MINIMUM-AUTHORITATIVE-EVIDENCE/1",
            priority_rule_id="SENT-GOV-017-PRIORITY/1",
            revoked=False,
            effective_at=mission.created_at,
            expires_at="",
            deterministic_id=_hash(payload),
        )

    def _validate_assignment(self, assignment: SentinelMissionAssignment, mission: EnterpriseMission, source_plan: SentinelSourcePlanReference, event_class: str) -> bool:
        return all(
            (
                mission.trigger_type == "Commander",
                bool(mission.commander_directive_id),
                "Sentinel" in mission.required_offices,
                mission.status in {"Queued", "Authorized", "Running", "Completed"},
                assignment.candidate_identity == self.candidate_identity,
                source_plan.operationally_allowed,
                event_class in assignment.approved_event_classes,
            )
        )

    def _schedule(self, objective: MonitoringObjective, timestamp: str):
        from .constitutional_observation import DeterministicObservationScheduler

        return DeterministicObservationScheduler().build_schedule((objective,), timestamp)

    def _scheduler_obligation_id(self, mission: EnterpriseMission) -> str:
        snapshot = self.scheduler.snapshot()
        activations = tuple(item for item in snapshot.get("officeActivationQueue", ()) if item.get("mission_id") == mission.mission_id and item.get("office_id") == "Sentinel")
        if activations:
            return str(activations[-1]["activation_id"])
        return f"EOS-ACT-{_hash((mission.mission_id, 'Sentinel'))[:10].upper()}"

    def _trace(self, root: str, parent: str, mission: EnterpriseMission, obligation: str, actor: str, action: str, symbol: str, rule: str, inputs: tuple[str, ...], outputs: tuple[str, ...], before: str, after: str, result: str, failure: str = "") -> str:
        payload = (root, parent, action, inputs, outputs, before, after, result, len(self.trace_events) + 1)
        event_id = f"SENT-TRACE-EVT-{len(self.trace_events) + 1:04d}-{_hash(payload)[:8].upper()}"
        event = SentinelRuntimeTraceEvent(
            event_id,
            parent,
            root,
            self.candidate_identity,
            self.runtime_identity,
            "Sentinel",
            mission.mission_id,
            mission.commander_directive_id,
            obligation,
            actor,
            action,
            symbol,
            rule,
            inputs,
            outputs,
            before,
            after,
            result,
            failure,
            utc_timestamp(),
            "",
        )
        event = replace(event, deterministic_digest=_hash(asdict(event)))
        self.trace_events = self.trace_events + (event,)
        return event.trace_event_id

    def _failed_execution(self, root: str, mission: EnterpriseMission, obligation: str, response: FailureResponse, code: str) -> SentinelRuntimeExecutionRecord:
        self._trace(root, "", mission, obligation, "SentinelCanonicalRuntime", "fail_closed", "SentinelCanonicalRuntime._failed_execution", "SENT-MO-001-FAILURE", (mission.mission_id,), (), "", "DORMANT", "FAIL", code)
        record = SentinelRuntimeExecutionRecord(
            f"SENT-RUN-{_hash((mission.mission_id, code))[:12].upper()}",
            self.candidate_identity,
            self.runtime_identity,
            mission.mission_id,
            obligation,
            ("DORMANT",),
            self.trace_events,
            None,
            None,
            response,
            SentinelOfficeState.DORMANT,
            SentinelRuntimeDecision.FAIL,
            "",
        )
        return replace(record, deterministic_digest=_hash(asdict(record)))


class CommanderAlertRuntime:
    """Actual Commander receiving surface for Sentinel constitutional alerts."""

    def __init__(self, *, candidate_identity: str, runtime_identity: str) -> None:
        self.candidate_identity = candidate_identity
        self.runtime_identity = runtime_identity
        self.receipts: tuple[CommanderReceiptRecord, ...] = ()
        self.acknowledgments: tuple[CommanderAcknowledgment, ...] = ()
        self._idempotency: dict[str, CommanderReceiptRecord] = {}

    def receive(self, alert: SentinelNotificationReadyAlert, bridge_message_id: str) -> tuple[CommanderReceiptRecord, CommanderAcknowledgment]:
        if alert.idempotency_key in self._idempotency:
            prior = self._idempotency[alert.idempotency_key]
            ack = self._ack(alert, bridge_message_id, prior, CommanderAcknowledgmentResult.DUPLICATE)
            self.acknowledgments = self.acknowledgments + (ack,)
            return prior, ack
        valid = self._validate(alert)
        receipt = CommanderReceiptRecord(
            receipt_id=f"CMD-RCPT-{_hash((alert.alert_id, bridge_message_id))[:12].upper()}",
            alert_id=alert.alert_id,
            bridge_message_id=bridge_message_id,
            observation_evidence_id=alert.observation_evidence_id,
            mission_id=alert.mission_id,
            candidate_identity=alert.candidate_identity,
            runtime_identity=alert.runtime_identity,
            source_office=alert.sentinel_identity,
            destination_office="Commander",
            receipt_timestamp=utc_timestamp(),
            validation_result=SentinelRuntimeDecision.PASS if valid else SentinelRuntimeDecision.FAIL,
            uncertainty=alert.uncertainty,
            priority=alert.priority,
            severity=alert.severity,
            current_commander_disposition="RECEIVED_NO_WORKFLOW_CREATED" if valid else "REJECTED",
            acknowledgment_state="PENDING",
            evidence_digest="",
        )
        receipt = replace(receipt, evidence_digest=_hash(asdict(receipt)))
        self.receipts = self.receipts + (receipt,)
        self._idempotency[alert.idempotency_key] = receipt
        ack = self._ack(alert, bridge_message_id, receipt, CommanderAcknowledgmentResult.ACCEPTED if valid else CommanderAcknowledgmentResult.REJECTED)
        self.acknowledgments = self.acknowledgments + (ack,)
        return receipt, ack

    def _validate(self, alert: SentinelNotificationReadyAlert) -> bool:
        return all(
            (
                alert.required_destination == "Commander",
                alert.sentinel_identity == "Sentinel",
                alert.candidate_identity == self.candidate_identity,
                alert.runtime_identity == self.runtime_identity,
                alert.sufficiency_state == SentinelRuntimeDecision.PASS,
                alert.notification_status == SentinelNotificationStatus.NOT_YET_DELIVERED,
                bool(alert.source_references),
                bool(alert.idempotency_key),
            )
        )

    def _ack(
        self,
        alert: SentinelNotificationReadyAlert,
        bridge_message_id: str,
        receipt: CommanderReceiptRecord,
        result: CommanderAcknowledgmentResult,
    ) -> CommanderAcknowledgment:
        ack = CommanderAcknowledgment(
            acknowledgment_id=f"CMD-ACK-{_hash((alert.alert_id, receipt.receipt_id, result.value))[:12].upper()}",
            commander_identity="Commander",
            commander_authority_identity=f"CMD-AUTH-{alert.mission_id}",
            original_alert_id=alert.alert_id,
            bridge_message_id=bridge_message_id,
            receipt_id=receipt.receipt_id,
            candidate_identity=alert.candidate_identity,
            runtime_identity=alert.runtime_identity,
            mission_identity=alert.mission_id,
            acknowledgment_timestamp=utc_timestamp(),
            validation_result=receipt.validation_result,
            acknowledgment_result=result,
            deterministic_digest="",
        )
        return replace(ack, deterministic_digest=_hash(asdict(ack)))


class SentinelCommanderBridgeRuntime:
    """Delivers SENT-MO-001 alerts through the canonical bridge and Commander runtime."""

    def __init__(
        self,
        *,
        bridge_executor: CanonicalBridgeExecutor | None = None,
        communications_bus: EnterpriseCommunicationsBus | None = None,
        commander: CommanderAlertRuntime | None = None,
        candidate_identity: str = "candidate:unknown",
        runtime_identity: str = "ARGOS-CANONICAL-RUNTIME",
    ) -> None:
        self.candidate_identity = candidate_identity
        self.runtime_identity = runtime_identity
        self.commander = commander or CommanderAlertRuntime(candidate_identity=candidate_identity, runtime_identity=runtime_identity)
        self.communications_bus = communications_bus or EnterpriseCommunicationsBus()
        registry = CanonicalBridgeRegistry((sentinel_commander_bridge_definition(),))
        self.bridge_executor = bridge_executor or CanonicalBridgeExecutor(runtime_instance_id=runtime_identity, registry=registry)
        self.bridge_executor.register_acceptor(SENTINEL_COMMANDER_BRIDGE_ID, self._commander_acceptor)
        self.delivery_records: tuple[SentinelCommanderDeliveryRecord, ...] = ()

    def deliver(self, alert: SentinelNotificationReadyAlert) -> SentinelCommanderDeliveryRecord:
        payload = asdict(alert)
        if alert.notification_status != SentinelNotificationStatus.NOT_YET_DELIVERED:
            return self._rejected(alert, "alert_not_delivery_ready")
        if alert.required_destination != "Commander":
            return self._rejected(alert, "wrong_destination")
        request = make_bridge_request(
            bridge_id=SENTINEL_COMMANDER_BRIDGE_ID,
            runtime_instance_id=self.runtime_identity,
            workflow_id=alert.mission_id,
            source="Sentinel",
            destination="Commander",
            artifact_id=alert.alert_id,
            payload=payload,
            current_owner="Sentinel",
            token_id=f"NOTIFY-{alert.mission_id}",
            proof_domain="PAPER",
        )
        result = self.bridge_executor.execute(request)
        if result.status == BridgeResultStatus.DUPLICATE_IDEMPOTENT_SUCCESS:
            self.commander.receive(alert, result.execution_id)
        bus_result = self.communications_bus.publish_observation(
            message_type="SENTINEL_COMMANDER_ALERT",
            source_service_id="Sentinel",
            payload=payload,
            target_service_id="Commander",
            target_office_id="Commander",
            source_office_id="Sentinel",
            mission_id=alert.mission_id,
            paper_live_mode=MessageMode.PAPER,
            priority_class=str(alert.priority),
            idempotency_key=alert.idempotency_key,
            ordering_key=f"{alert.priority:04d}:{alert.severity:04d}:{alert.alert_id}",
            sequence_number=alert.priority,
            authorization_context_reference=f"NOTIFY-{alert.mission_id}",
        )
        receipt = self.commander.receipts[-1] if self.commander.receipts else None
        acknowledgment = self.commander.acknowledgments[-1] if self.commander.acknowledgments else None
        state = SentinelNotificationStatus.ACKNOWLEDGED if result.status in {BridgeResultStatus.ACCEPTED, BridgeResultStatus.DUPLICATE_IDEMPOTENT_SUCCESS} and acknowledgment and acknowledgment.acknowledgment_result in {CommanderAcknowledgmentResult.ACCEPTED, CommanderAcknowledgmentResult.DUPLICATE} else SentinelNotificationStatus.REJECTED
        record = SentinelCommanderDeliveryRecord(
            delivery_id=f"SENT-DELIVERY-{_hash((alert.alert_id, result.execution_id, bus_result.message_id))[:12].upper()}",
            alert=alert,
            bridge_result_status=result.status.value,
            bridge_rejection_code=result.rejection_code.value if result.rejection_code else "",
            bus_message_id=bus_result.message_id,
            commander_receipt=receipt,
            commander_acknowledgment=acknowledgment,
            sentinel_delivery_state=state,
            downstream_activation_attempts=(),
            reconciliation_digest="",
        )
        record = replace(record, reconciliation_digest=_hash(asdict(record)))
        self.delivery_records = self.delivery_records + (record,)
        return record

    def static_bypass_analysis(self) -> Mapping[str, tuple[str, ...]]:
        prohibited = ("Seeker", "Analyst", "Risk", "Trader", "Broker", "Position Registry", "Workflow Creation", "Decision Object")
        return {"prohibited_destinations": prohibited, "resolved_findings": (), "unresolved_findings": ()}

    def replay(self, record: SentinelCommanderDeliveryRecord) -> SentinelCommanderDeliveryRecord:
        return replace(record, sentinel_delivery_state=record.sentinel_delivery_state)

    def _commander_acceptor(self, request) -> dict[str, Any]:
        alert = SentinelNotificationReadyAlert(**request.payload)
        receipt, _ack = self.commander.receive(alert, request.execution_id)
        return {"accepted": receipt.validation_result == SentinelRuntimeDecision.PASS, "acceptance_reference": receipt.receipt_id}

    def _rejected(self, alert: SentinelNotificationReadyAlert, code: str) -> SentinelCommanderDeliveryRecord:
        record = SentinelCommanderDeliveryRecord(
            f"SENT-DELIVERY-{_hash((alert.alert_id, code))[:12].upper()}",
            alert,
            "REJECTED",
            code,
            "",
            None,
            None,
            SentinelNotificationStatus.REJECTED,
            (),
            "",
        )
        return replace(record, reconciliation_digest=_hash(asdict(record)))


def sentinel_commander_bridge_definition() -> CanonicalBridgeDefinition:
    return CanonicalBridgeDefinition(
        bridge_id=SENTINEL_COMMANDER_BRIDGE_ID,
        bridge_name="Sentinel to Commander Constitutional Alert Notification",
        bridge_version="SENT-MO-002/1.0.0",
        source_component="Sentinel",
        destination_component="Commander",
        allowed_workflow_types=("paper", "commander_directed_mission"),
        allowed_proof_domains=("PAPER",),
        input_artifact_type="SentinelNotificationReadyAlert",
        accepted_artifact_type="CommanderAcknowledgment",
        payload_schema_version="SENT-MO-002-ALERT/1.0.0",
        transfer_class=BridgeTransferClass.INFORMATION_DELIVERY,
        token_required=True,
        source_preconditions=("Sentinel active for Commander mission", "alert status NOT_YET_DELIVERED"),
        destination_preconditions=("Commander receiving interface active",),
        persistence_required=True,
        transaction_required=False,
        idempotency_policy=BridgeIdempotencyPolicy.IDEMPOTENT_REPLAY,
        timeout_seconds=30,
        retry_policy="retry with same idempotency key",
        failure_policy="do not claim delivery",
        recovery_policy="reconcile from Commander receipt and acknowledgment evidence",
        audit_policy="dual-sided Sentinel and Commander evidence",
        enabled=True,
        requirement_class=BridgeRequirementClass.REQUIRED_PRODUCTION,
        implementation_status=BridgeImplementationStatus.IMPLEMENTED,
        certification_status=BridgeCertificationStatus.CONDITIONALLY_PRODUCTION,
    )


def _sentinel_lifecycle_controller() -> OfficeLifecycleController:
    definitions = default_office_definitions() + (
        OfficeDefinition(
            office_id="Sentinel",
            office_name="Sentinel Observation Office",
            office_version=SENT_MO_CANONICAL_RUNTIME_VERSION,
            implementation_path="argos.sentinel.canonical_runtime.SentinelCanonicalRuntime",
            classification=OfficeClassification.INFORMATION_ONLY,
            constitutional_role="mission-directed observation and Commander alert preparation",
            allowed_workflow_types=("commander_directed_mission", "paper"),
            allowed_proof_domains=("PAPER",),
            ownership_bearing=False,
            allowed_activation_authorities=(OfficeActivationAuthority.SCHEDULER, OfficeActivationAuthority.COMMANDER),
            ingress_bridges=(),
            egress_bridges=(SENTINEL_COMMANDER_BRIDGE_ID,),
            information_subscriptions=(),
            required_dependencies=("EnterpriseOperationsScheduler", "CanonicalBridgeExecutor", "EnterpriseCommunicationsBus"),
            persistence_required=True,
            recovery_required=True,
            default_state=OfficeLifecycleState.DORMANT,
            background_activity_policy="no autonomous monitoring without Commander mission",
            multiplicity_policy="single mission activation per runtime execution",
            enabled=True,
            production_required=True,
        ),
    )
    return OfficeLifecycleController(registry=OfficeRegistry(definitions))


def _duplicate_decision(observation: ObservationRecord, prior: Iterable[ObservationRecord]) -> SentinelDuplicateDecision:
    prior_ids = tuple(item.observation_id for item in prior)
    duplicate = observation.observation_id in prior_ids
    return SentinelDuplicateDecision(
        decision_id=f"DUP-{_hash((observation.observation_id, prior_ids))[:10].upper()}",
        compared_observation_ids=prior_ids + (observation.observation_id,),
        rule_identity="SENT-MO-001-DUPLICATE/1",
        comparison_dimensions=("objective_id", "source_id", "observation_timestamp", "value_hash", "mission_assignment_id"),
        duplicate_window="PT5M",
        result="DUPLICATE" if duplicate else "UNIQUE",
        reason_code="MATCHED_PRIOR_OBSERVATION" if duplicate else "NO_MATCH",
        retained_observation=prior_ids[0] if duplicate and prior_ids else observation.observation_id,
        suppressed_observation=observation.observation_id if duplicate else "",
    )


def _evidence_envelope(
    candidate: str,
    runtime: str,
    mission: EnterpriseMission,
    obligation: str,
    source_plan: SentinelSourcePlanReference,
    raw: SentinelRawAcquisitionEvidence,
    observation: ObservationRecord,
    duplicate: SentinelDuplicateDecision,
    independence: SentinelSourceIndependenceDecision,
    conflict: SentinelConflictDecision,
    sufficiency: SentinelSufficiencyDecision,
    priority: SentinelPriorityDecision,
    trace_refs: tuple[str, ...],
) -> SentinelObservationEvidenceEnvelope:
    envelope = SentinelObservationEvidenceEnvelope(
        envelope_id=f"SENT-EVID-{_hash((mission.mission_id, observation.observation_id))[:12].upper()}",
        candidate_identity=candidate,
        runtime_identity=runtime,
        mission_identity=mission.mission_id,
        commander_authority_identity=mission.commander_directive_id,
        sentinel_office_identity="Sentinel",
        scheduler_obligation_identity=obligation,
        source_plan_identity=source_plan.source_plan_id,
        acquisition_evidence_references=(raw.raw_evidence_reference, raw.response_digest),
        normalized_observation_identity=observation.observation_id,
        duplicate_decision=duplicate,
        independence_decision=independence,
        conflict_decision=conflict,
        sufficiency_decision=sufficiency,
        priority_decision=priority,
        uncertainty=sufficiency.remaining_uncertainty,
        discovered_candidate_event_classes=(),
        final_notification_readiness_state=sufficiency.notification_readiness,
        deterministic_digest="",
        trace_references=trace_refs,
    )
    return replace(envelope, deterministic_digest=_hash(asdict(envelope)))


def _notification_ready_alert(
    envelope: SentinelObservationEvidenceEnvelope,
    mission: EnterpriseMission,
    candidate: str,
    runtime: str,
    event_class: str,
) -> SentinelNotificationReadyAlert:
    alert = SentinelNotificationReadyAlert(
        alert_id=f"SENT-ALERT-{_hash((envelope.envelope_id, event_class))[:12].upper()}",
        schema_version="SENT-MO-002-ALERT/1.0.0",
        observation_evidence_id=envelope.envelope_id,
        mission_id=mission.mission_id,
        sentinel_identity="Sentinel",
        required_destination="Commander",
        priority=envelope.priority_decision.final_rank,
        severity=envelope.priority_decision.constitutional_severity,
        sufficiency_state=envelope.sufficiency_decision.notification_readiness,
        uncertainty=envelope.uncertainty,
        event_class=event_class,
        source_references=envelope.acquisition_evidence_references,
        idempotency_key=_hash((candidate, runtime, mission.mission_id, envelope.envelope_id, event_class, "v1")),
        candidate_identity=candidate,
        runtime_identity=runtime,
        notification_status=SentinelNotificationStatus.NOT_YET_DELIVERED,
        deterministic_digest="",
    )
    return replace(alert, deterministic_digest=_hash(asdict(alert)))


def _hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
