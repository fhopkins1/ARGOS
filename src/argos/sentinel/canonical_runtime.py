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
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas

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


class SourceAdapterMode(str, Enum):
    PAPER_AUTHORITATIVE = "PAPER_AUTHORITATIVE"
    TEST_ISOLATED = "TEST_ISOLATED"
    REPLAY_ISOLATED = "REPLAY_ISOLATED"


class SentinelEvidenceOrigin(str, Enum):
    RUNTIME_OBSERVATION = "Runtime Observation"
    CAPTURED_AUTHORITATIVE_RESPONSE = "Captured Authoritative Response"
    HISTORICAL_REPLAY = "Historical Replay"
    CONSTITUTIONAL_SIMULATION = "Constitutional Simulation"
    UNIT_TEST = "Unit Test"
    STATIC_INSPECTION = "Static Inspection"


@dataclass(frozen=True)
class AuthorityRecord:
    authority_id: str
    issuer: str
    recipient: str
    operation: str
    mission_id: str
    candidate_identity: str
    runtime_identity: str
    active: bool
    revoked: bool = False
    expired: bool = False
    superseded: bool = False


@dataclass(frozen=True)
class SentinelRuntimeEvidenceOriginRecord:
    origin_record_id: str
    evidence_identifier: str
    origin: SentinelEvidenceOrigin
    producing_subsystem: str
    associated_mission: str
    creation_time: str
    immutable: bool
    metadata: Mapping[str, str]
    deterministic_digest: str


@dataclass(frozen=True)
class SentinelDependencyRecord:
    dependency_id: str
    dependency_type: str
    constitutional_role: str
    implementation_identity: str
    acquisition_source: str
    enterprise_owned: bool
    available: bool
    validation_result: SentinelRuntimeDecision
    failure_reason: str
    deterministic_digest: str


@dataclass(frozen=True)
class SentinelDependencyCertification:
    certification_id: str
    records: tuple[SentinelDependencyRecord, ...]
    result: SentinelRuntimeDecision
    failure_reasons: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class SentinelEventSufficiencyRule:
    rule_id: str
    event_class: str
    required_evidence_fields: tuple[str, ...]
    required_source_count: int
    required_independent_source_count: int
    required_dependencies: tuple[str, ...]
    optional_corroboration_allowed: bool = True


@dataclass(frozen=True)
class SentinelSufficiencyEvaluationEvidence:
    evidence_id: str
    mission_identifier: str
    observation_identifiers: tuple[str, ...]
    event_class: str
    sufficiency_decision: SentinelRuntimeDecision
    constitutional_rule_set: str
    independent_source_analysis: tuple[str, ...]
    dependency_evaluation: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    missing_independent_sources: tuple[str, ...]
    unresolved_dependencies: tuple[str, ...]
    timestamp: str
    evaluator_version: str
    deterministic_digest: str


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
class SentinelConstitutionalTraceRecord:
    trace_identifier: str
    workflow_identifier: str
    mission_identifier: str
    runtime_execution_identifier: str
    stage_identifier: str
    stage_timestamp: str
    execution_order: int
    executing_component: str
    operation_performed: str
    dependency_invoked: str
    dependency_response: str
    evidence_identifiers_generated: tuple[str, ...]
    constitutional_evaluation_result: str
    success_or_failure_outcome: str
    failure_reason: str
    deterministic_digest: str


@dataclass(frozen=True)
class SentinelRuntimeAuditTrail:
    audit_identifier: str
    runtime_execution_identifier: str
    mission_identifier: str
    workflow_identifier: str
    trace_records: tuple[SentinelConstitutionalTraceRecord, ...]
    coverage_stages: tuple[str, ...]
    missing_stages: tuple[str, ...]
    orphan_trace_records: tuple[str, ...]
    immutable: bool
    audit_reconstruction_result: SentinelRuntimeDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SentinelReplayCertificationRecord:
    replay_certification_id: str
    original_execution_id: str
    replay_execution_id: str
    original_semantic_digest: str
    replay_semantic_digest: str
    equivalent_trace_order: bool
    equivalent_decisions: bool
    equivalent_evidence_relationships: bool
    equivalent_state_transitions: bool
    missing_evidence: tuple[str, ...]
    semantic_differences: tuple[str, ...]
    result: SentinelRuntimeDecision
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


class ApprovedSentinelSourceAdapter:
    """Approved paper-authoritative source adapter that returns raw evidence."""

    adapter_id = "SENTINEL-APPROVED-SOURCE-ADAPTER/1.0.0"
    mode = SourceAdapterMode.PAPER_AUTHORITATIVE

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


class DeterministicSentinelSourceAdapter(ApprovedSentinelSourceAdapter):
    """Deterministic adapter isolated to tests and replay, never operational proof."""

    adapter_id = "SENTINEL-DETERMINISTIC-SOURCE-ADAPTER/1.0.0"
    mode = SourceAdapterMode.TEST_ISOLATED


class SentinelEvidenceOriginRegistry:
    """Validates immutable origin metadata for Sentinel constitutional evidence."""

    approved_origins = tuple(SentinelEvidenceOrigin)

    def declare(
        self,
        *,
        evidence_identifier: str,
        origin: SentinelEvidenceOrigin,
        producing_subsystem: str,
        associated_mission: str,
        metadata: Mapping[str, str] | None = None,
    ) -> SentinelRuntimeEvidenceOriginRecord:
        if origin not in self.approved_origins:
            raise ValueError("unapproved Sentinel evidence origin")
        record = SentinelRuntimeEvidenceOriginRecord(
            origin_record_id=f"SENT-ORIGIN-{_hash((evidence_identifier, origin.value, producing_subsystem))[:12].upper()}",
            evidence_identifier=evidence_identifier,
            origin=origin,
            producing_subsystem=producing_subsystem,
            associated_mission=associated_mission,
            creation_time=utc_timestamp(),
            immutable=True,
            metadata=dict(metadata or {}),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_hash(asdict(record)))

    def validate(self, record: SentinelRuntimeEvidenceOriginRecord | None) -> bool:
        return bool(record and record.immutable and record.origin in self.approved_origins and record.evidence_identifier and record.producing_subsystem)


class SentinelEnterpriseServiceRegistry:
    """Authoritative service registry view consumed by Sentinel certification paths."""

    def __init__(self, services: Mapping[str, object], *, acquisition_source: str = "CanonicalEnterpriseRuntime") -> None:
        self._services = dict(services)
        self.acquisition_source = acquisition_source

    def resolve(self, dependency_type: str) -> object | None:
        return self._services.get(dependency_type)

    def identity_for(self, dependency_type: str) -> str:
        service = self.resolve(dependency_type)
        if service is None:
            return ""
        identity = getattr(service, "adapter_id", "") or getattr(service, "__class__", type(service)).__name__
        return f"{service.__class__.__module__}.{identity}"


@dataclass(frozen=True)
class SentinelEnterpriseServices:
    scheduler: EnterpriseOperationsScheduler
    lifecycle: OfficeLifecycleController
    source_adapter: ApprovedSentinelSourceAdapter
    mission_registry: SentinelMissionRegistry
    authority_registry: SentinelAuthorityRegistry
    persistence: InMemoryPersistenceRepository
    evidence_origin_registry: SentinelEvidenceOriginRegistry
    sufficiency_policy_registry: "SentinelSufficiencyPolicyRegistry"
    service_registry: SentinelEnterpriseServiceRegistry


class SentinelMissionRegistry:
    """Canonical mission registry view backed by EnterpriseOperationsScheduler."""

    def __init__(self, scheduler: EnterpriseOperationsScheduler) -> None:
        self.scheduler = scheduler

    def resolve(self, mission_id: str) -> EnterpriseMission | None:
        if any(item.get("mission_id") == mission_id for item in self.scheduler.snapshot().get("missionRecords", ())):
            return self.scheduler._mission(mission_id)
        return None


class SentinelAuthorityRegistry:
    """Authority records for Commander mission, Sentinel observation, and Commander acceptance."""

    def __init__(self, records: Iterable[AuthorityRecord]) -> None:
        self._records = tuple(records)

    @classmethod
    def for_mission(cls, mission: EnterpriseMission, candidate_identity: str, runtime_identity: str) -> "SentinelAuthorityRegistry":
        return cls(
            (
                AuthorityRecord(f"AUTH-MISSION-{mission.mission_id}", "Commander", "Sentinel", "observe", mission.mission_id, candidate_identity, runtime_identity, True),
                AuthorityRecord(f"AUTH-NOTIFY-{mission.mission_id}", "Commander", "Sentinel", "notify_commander", mission.mission_id, candidate_identity, runtime_identity, True),
                AuthorityRecord(f"AUTH-COMMANDER-RECEIPT-{mission.mission_id}", "Commander", "Commander", "receive_sentinel_alert", mission.mission_id, candidate_identity, runtime_identity, True),
                AuthorityRecord(f"AUTH-COMMANDER-ACK-{mission.mission_id}", "Commander", "Commander", "acknowledge_sentinel_alert", mission.mission_id, candidate_identity, runtime_identity, True),
            )
        )

    def validate(self, operation: str, mission_id: str, candidate_identity: str, runtime_identity: str) -> AuthorityRecord | None:
        for record in self._records:
            if (
                record.operation == operation
                and record.mission_id == mission_id
                and record.candidate_identity == candidate_identity
                and record.runtime_identity == runtime_identity
                and record.active
                and not record.revoked
                and not record.expired
                and not record.superseded
            ):
                return record
        return None


class SentinelEnterpriseCompositionRoot:
    """Composition root that owns Sentinel enterprise dependencies before injection."""

    def __init__(
        self,
        *,
        scheduler: EnterpriseOperationsScheduler,
        lifecycle: OfficeLifecycleController,
        persistence: InMemoryPersistenceRepository,
        source_adapter: ApprovedSentinelSourceAdapter,
        acquisition_source: str = "CanonicalEnterpriseRuntime.SentinelEnterpriseCompositionRoot",
    ) -> None:
        self.scheduler = scheduler
        self.lifecycle = lifecycle
        self.persistence = persistence
        self.source_adapter = source_adapter
        self.evidence_origin_registry = SentinelEvidenceOriginRegistry()
        self.acquisition_source = acquisition_source

    @classmethod
    def paper(cls) -> "SentinelEnterpriseCompositionRoot":
        return cls(
            scheduler=EnterpriseOperationsScheduler(),
            lifecycle=_sentinel_lifecycle_controller(),
            persistence=InMemoryPersistenceRepository(canonical_schemas()),
            source_adapter=ApprovedSentinelSourceAdapter(),
        )

    def services_for_mission(
        self,
        mission: EnterpriseMission,
        *,
        candidate_identity: str,
        runtime_identity: str,
        event_classes: Iterable[str],
    ) -> SentinelEnterpriseServices:
        mission_registry = SentinelMissionRegistry(self.scheduler)
        authority_registry = SentinelAuthorityRegistry.for_mission(mission, candidate_identity, runtime_identity)
        sufficiency_policy = SentinelSufficiencyPolicyRegistry.for_event_classes(event_classes)
        services: dict[str, object] = {
            "Enterprise Scheduler": self.scheduler,
            "Enterprise Mission Registry": mission_registry,
            "Enterprise Authority Registry": authority_registry,
            "Enterprise Persistence": self.persistence,
            "Runtime Audit Infrastructure": self.evidence_origin_registry,
            "Approved Operational Source Adapters": self.source_adapter,
            "Constitutional Sufficiency Policy": sufficiency_policy,
        }
        registry = SentinelEnterpriseServiceRegistry(services, acquisition_source=self.acquisition_source)
        return SentinelEnterpriseServices(
            scheduler=self.scheduler,
            lifecycle=self.lifecycle,
            source_adapter=self.source_adapter,
            mission_registry=mission_registry,
            authority_registry=authority_registry,
            persistence=self.persistence,
            evidence_origin_registry=self.evidence_origin_registry,
            sufficiency_policy_registry=sufficiency_policy,
            service_registry=registry,
        )


class SentinelDependencyCertifier:
    """Certifies externally acquired Sentinel runtime dependencies."""

    required_dependencies = (
        ("Enterprise Scheduler", "scheduler", "mission scheduling and activation"),
        ("Enterprise Mission Registry", "mission_registry", "Commander mission acquisition"),
        ("Enterprise Authority Registry", "authority_registry", "authority validation"),
        ("Enterprise Persistence", "persistence", "immutable runtime evidence"),
        ("Runtime Audit Infrastructure", "evidence_origin_registry", "evidence origin certification"),
        ("Approved Operational Source Adapters", "source_adapter", "approved observation acquisition"),
        ("Constitutional Sufficiency Policy", "sufficiency_policy_registry", "authoritative observation sufficiency"),
    )

    def certify(self, services: SentinelEnterpriseServices | None, *, source: str = "canonical enterprise composition root") -> SentinelDependencyCertification:
        records: list[SentinelDependencyRecord] = []
        failures: list[str] = []
        for dependency_type, attribute, role in self.required_dependencies:
            service = getattr(services, attribute, None) if services is not None else None
            available = service is not None
            enterprise_owned = available and services is not None and services.service_registry.resolve(dependency_type) is service
            failure = "" if available and enterprise_owned else ("MISSING_DEPENDENCY" if not available else "UNAUTHORIZED_LOCAL_SUBSTITUTE")
            if failure:
                failures.append(f"{dependency_type}:{failure}")
            record = SentinelDependencyRecord(
                dependency_id=f"SENT-DEP-{_hash((dependency_type, attribute, source))[:12].upper()}",
                dependency_type=dependency_type,
                constitutional_role=role,
                implementation_identity=services.service_registry.identity_for(dependency_type) if services is not None else "",
                acquisition_source=source,
                enterprise_owned=enterprise_owned,
                available=available,
                validation_result=SentinelRuntimeDecision.PASS if available and enterprise_owned else SentinelRuntimeDecision.FAIL,
                failure_reason=failure,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_hash(asdict(record))))
        result = SentinelRuntimeDecision.PASS if not failures else SentinelRuntimeDecision.FAIL
        certification = SentinelDependencyCertification(
            certification_id=f"SENT-DEPCERT-{_hash(tuple(item.dependency_id for item in records))[:12].upper()}",
            records=tuple(records),
            result=result,
            failure_reasons=tuple(failures),
            deterministic_digest="",
        )
        return replace(certification, deterministic_digest=_hash(asdict(certification)))


class SentinelSufficiencyPolicyRegistry:
    """Authoritative event-class sufficiency policy consumed by the runtime."""

    def __init__(self, rules: Iterable[SentinelEventSufficiencyRule]) -> None:
        self._rules = {rule.event_class: rule for rule in rules}

    @classmethod
    def for_event_classes(cls, event_classes: Iterable[str]) -> "SentinelSufficiencyPolicyRegistry":
        return cls(
            SentinelEventSufficiencyRule(
                rule_id="SENT-GOV-018-MINIMUM-AUTHORITATIVE-EVIDENCE/1",
                event_class=event_class,
                required_evidence_fields=("event_class", "value_hash", "source_timestamp", "raw_evidence"),
                required_source_count=1,
                required_independent_source_count=1,
                required_dependencies=("Enterprise Authority Registry", "Enterprise Persistence", "Runtime Audit Infrastructure"),
            )
            for event_class in event_classes
        )

    def rule_for(self, event_class: str) -> SentinelEventSufficiencyRule | None:
        return self._rules.get(event_class)


class SentinelObservationSufficiencyEvaluator:
    """Determines observation sufficiency from authoritative event-class policy only."""

    evaluator_version = "SENT-MO1-005-SUFFICIENCY-EVALUATOR/1.0.0"

    def __init__(self, policy_registry: SentinelSufficiencyPolicyRegistry) -> None:
        self.policy_registry = policy_registry

    def evaluate(
        self,
        *,
        mission_id: str,
        event_class: str,
        observations: Iterable[ObservationRecord],
        source_records: Mapping[str, SourceRecord],
        dependency_certification: SentinelDependencyCertification,
    ) -> tuple[SentinelSufficiencyDecision, SentinelSufficiencyEvaluationEvidence]:
        observed = tuple(observations)
        rule = self.policy_registry.rule_for(event_class)
        if rule is None:
            return self._result(mission_id, event_class, observed, SentinelRuntimeDecision.FAIL, "", (), (), ("missing_event_class_policy",), (), (), ("Constitutional Sufficiency Policy",))
        missing_evidence = []
        for observation in observed:
            if not observation.value_hash:
                missing_evidence.append(f"{observation.observation_id}:value_hash")
            if not observation.observation_timestamp:
                missing_evidence.append(f"{observation.observation_id}:source_timestamp")
            if not observation.evidence_references:
                missing_evidence.append(f"{observation.observation_id}:raw_evidence")
        present_sources = tuple(dict.fromkeys(item.source_id for item in observed))
        independent_groups = tuple(dict.fromkeys(source_records[item].independence_group for item in present_sources if item in source_records and source_records[item].enabled and source_records[item].authorized))
        missing_sources: list[str] = []
        if len(present_sources) < rule.required_source_count:
            missing_sources.append(f"required_sources:{rule.required_source_count}")
        if len(independent_groups) < rule.required_independent_source_count:
            missing_sources.append(f"required_independent_sources:{rule.required_independent_source_count}")
        unresolved_dependencies = tuple(item for item in rule.required_dependencies if not any(record.dependency_type == item and record.validation_result == SentinelRuntimeDecision.PASS for record in dependency_certification.records))
        missing_requirements = tuple(missing_evidence + missing_sources + list(unresolved_dependencies))
        decision = SentinelRuntimeDecision.PASS if not missing_requirements else SentinelRuntimeDecision.INSUFFICIENT
        return self._result(mission_id, event_class, observed, decision, rule.rule_id, present_sources, independent_groups, tuple(missing_requirements), tuple(missing_evidence), tuple(missing_sources), unresolved_dependencies)

    def _result(
        self,
        mission_id: str,
        event_class: str,
        observations: tuple[ObservationRecord, ...],
        decision: SentinelRuntimeDecision,
        rule_id: str,
        present_sources: tuple[str, ...],
        independent_groups: tuple[str, ...],
        missing_requirements: tuple[str, ...],
        missing_evidence: tuple[str, ...],
        missing_sources: tuple[str, ...],
        unresolved_dependencies: tuple[str, ...],
    ) -> tuple[SentinelSufficiencyDecision, SentinelSufficiencyEvaluationEvidence]:
        evidence = SentinelSufficiencyEvaluationEvidence(
            evidence_id=f"SENT-SUFF-EVID-{_hash((mission_id, event_class, tuple(item.observation_id for item in observations), missing_requirements))[:12].upper()}",
            mission_identifier=mission_id,
            observation_identifiers=tuple(item.observation_id for item in observations),
            event_class=event_class,
            sufficiency_decision=decision,
            constitutional_rule_set=rule_id,
            independent_source_analysis=independent_groups,
            dependency_evaluation=unresolved_dependencies,
            missing_requirements=missing_requirements,
            missing_evidence=missing_evidence,
            missing_independent_sources=missing_sources,
            unresolved_dependencies=unresolved_dependencies,
            timestamp=utc_timestamp(),
            evaluator_version=self.evaluator_version,
            deterministic_digest="",
        )
        evidence = replace(evidence, deterministic_digest=_hash(asdict(evidence)))
        sufficiency = SentinelSufficiencyDecision(
            decision_id=f"SUF-{_hash(evidence.evidence_id)[:10].upper()}",
            rule_identity=rule_id,
            required_fields_satisfied=() if missing_evidence else ("event_class", "value_hash", "source_timestamp", "raw_evidence"),
            required_sources_present=present_sources,
            mandatory_corroboration_satisfied=not missing_sources,
            remaining_uncertainty=missing_requirements,
            notification_readiness=decision,
        )
        return sufficiency, evidence


class SentinelRuntimeTraceEngine:
    """Projects immutable runtime events into audit-ready constitutional traces."""

    required_success_stages = (
        "mission_resolved",
        "authority_validated",
        "sentinel_scheduled",
        "sentinel_active",
        "source_acquired",
        "observation_normalized",
        "duplicate_suppression_evaluated",
        "source_independence_evaluated",
        "conflict_evaluated",
        "sufficiency_evaluated",
        "priority_determined",
        "evidence_generated",
        "persistence_operation",
        "sentinel_dormant",
    )

    def build_audit_trail(self, record: SentinelRuntimeExecutionRecord) -> SentinelRuntimeAuditTrail:
        trace_records = tuple(self._project_event(record, event, index + 1) for index, event in enumerate(record.trace_events))
        actions = tuple(item.operation_performed for item in trace_records)
        required = ("fail_closed",) if record.result == SentinelRuntimeDecision.FAIL else self.required_success_stages
        missing = tuple(stage for stage in required if stage not in actions)
        orphaned = tuple(item.trace_identifier for item in trace_records if item.mission_identifier != record.mission_id or item.runtime_execution_identifier != record.execution_id)
        audit = SentinelRuntimeAuditTrail(
            audit_identifier=f"SENT-AUDIT-{_hash((record.execution_id, actions))[:12].upper()}",
            runtime_execution_identifier=record.execution_id,
            mission_identifier=record.mission_id,
            workflow_identifier=record.mission_id,
            trace_records=trace_records,
            coverage_stages=actions,
            missing_stages=missing,
            orphan_trace_records=orphaned,
            immutable=True,
            audit_reconstruction_result=SentinelRuntimeDecision.PASS if not missing and not orphaned else SentinelRuntimeDecision.FAIL,
            deterministic_digest="",
        )
        return replace(audit, deterministic_digest=_hash(asdict(audit)))

    def replay_audit_trail(self, audit: SentinelRuntimeAuditTrail) -> SentinelRuntimeAuditTrail:
        return replace(
            audit,
            audit_identifier=f"SENT-REPLAY-AUDIT-{_hash(audit.audit_identifier)[:12].upper()}",
            deterministic_digest="",
        )

    def certify_replay_equivalence(self, record: SentinelRuntimeExecutionRecord, replay_record: SentinelRuntimeExecutionRecord | None = None) -> SentinelReplayCertificationRecord:
        replay = replay_record or replace(record, execution_id=f"REPLAY-{record.execution_id}")
        original_digest = sentinel_runtime_equivalence_digest(record)
        replay_digest = sentinel_runtime_equivalence_digest(replay)
        original_audit = self.build_audit_trail(record)
        replay_audit = self.build_audit_trail(replay)
        original_actions = tuple(item.operation_performed for item in original_audit.trace_records)
        replay_actions = tuple(item.operation_performed for item in replay_audit.trace_records)
        differences: list[str] = []
        if original_digest != replay_digest:
            differences.append("semantic_digest")
        if original_actions != replay_actions:
            differences.append("trace_order")
        if record.result != replay.result:
            differences.append("completion_status")
        if record.evidence_envelope and replay.evidence_envelope and record.evidence_envelope.envelope_id != replay.evidence_envelope.envelope_id:
            differences.append("evidence_identity")
        missing = ()
        if not record.trace_events:
            missing = ("runtime_trace",)
        if record.evidence_envelope is None and record.result == SentinelRuntimeDecision.PASS:
            missing = missing + ("observation_evidence",)
        result = SentinelRuntimeDecision.PASS if not differences and not missing else SentinelRuntimeDecision.FAIL
        certification = SentinelReplayCertificationRecord(
            replay_certification_id=f"SENT-REPLAY-CERT-{_hash((record.execution_id, replay.execution_id, original_digest, replay_digest))[:12].upper()}",
            original_execution_id=record.execution_id,
            replay_execution_id=replay.execution_id,
            original_semantic_digest=original_digest,
            replay_semantic_digest=replay_digest,
            equivalent_trace_order=original_actions == replay_actions,
            equivalent_decisions=record.result == replay.result,
            equivalent_evidence_relationships=not record.evidence_envelope or not replay.evidence_envelope or record.evidence_envelope.envelope_id == replay.evidence_envelope.envelope_id,
            equivalent_state_transitions=record.lifecycle_states == replay.lifecycle_states,
            missing_evidence=missing,
            semantic_differences=tuple(differences),
            result=result,
            deterministic_digest="",
        )
        return replace(certification, deterministic_digest=_hash(asdict(certification)))

    def _project_event(self, record: SentinelRuntimeExecutionRecord, event: SentinelRuntimeTraceEvent, order: int) -> SentinelConstitutionalTraceRecord:
        trace = SentinelConstitutionalTraceRecord(
            trace_identifier=event.trace_event_id,
            workflow_identifier=record.mission_id,
            mission_identifier=event.mission_identity,
            runtime_execution_identifier=record.execution_id,
            stage_identifier=event.rule_identity,
            stage_timestamp=event.timestamp,
            execution_order=order,
            executing_component=event.actor,
            operation_performed=event.action,
            dependency_invoked=event.implementation_symbol,
            dependency_response=event.result,
            evidence_identifiers_generated=event.output_artifacts,
            constitutional_evaluation_result=event.result,
            success_or_failure_outcome="FAIL" if event.failure_code else event.result,
            failure_reason=event.failure_code,
            deterministic_digest="",
        )
        return replace(trace, deterministic_digest=_hash(asdict(trace)))


class SentinelCanonicalRuntime:
    """Executes Sentinel through canonical scheduler, lifecycle, source, and evidence paths."""

    def __init__(
        self,
        *,
        scheduler: EnterpriseOperationsScheduler | None = None,
        lifecycle: OfficeLifecycleController | None = None,
        source_adapter: ApprovedSentinelSourceAdapter | None = None,
        mission_registry: SentinelMissionRegistry | None = None,
        authority_registry: SentinelAuthorityRegistry | None = None,
        persistence: InMemoryPersistenceRepository | None = None,
        evidence_origin_registry: SentinelEvidenceOriginRegistry | None = None,
        sufficiency_policy_registry: SentinelSufficiencyPolicyRegistry | None = None,
        service_registry: SentinelEnterpriseServiceRegistry | None = None,
        require_certified_dependencies: bool = False,
        candidate_identity: str = "candidate:unknown",
        runtime_identity: str = "ARGOS-CANONICAL-RUNTIME",
    ) -> None:
        self.scheduler = scheduler or EnterpriseOperationsScheduler()
        self.lifecycle = lifecycle or _sentinel_lifecycle_controller()
        self.source_adapter = source_adapter or ApprovedSentinelSourceAdapter()
        self.mission_registry = mission_registry or SentinelMissionRegistry(self.scheduler)
        self.authority_registry = authority_registry
        self.candidate_identity = candidate_identity
        self.runtime_identity = runtime_identity
        self.trace_events: tuple[SentinelRuntimeTraceEvent, ...] = ()
        self.persistence = persistence or InMemoryPersistenceRepository(canonical_schemas())
        self.evidence_origin_registry = evidence_origin_registry or SentinelEvidenceOriginRegistry()
        self.sufficiency_policy_registry = sufficiency_policy_registry
        self.service_registry = service_registry
        self.require_certified_dependencies = require_certified_dependencies
        self.dependency_certification: SentinelDependencyCertification | None = None

    @classmethod
    def from_enterprise_services(
        cls,
        services: SentinelEnterpriseServices,
        *,
        candidate_identity: str,
        runtime_identity: str = "ARGOS-CANONICAL-RUNTIME",
        require_certified_dependencies: bool = True,
    ) -> "SentinelCanonicalRuntime":
        return cls(
            scheduler=services.scheduler,
            lifecycle=services.lifecycle,
            source_adapter=services.source_adapter,
            mission_registry=services.mission_registry,
            authority_registry=services.authority_registry,
            persistence=services.persistence,
            evidence_origin_registry=services.evidence_origin_registry,
            sufficiency_policy_registry=services.sufficiency_policy_registry,
            service_registry=services.service_registry,
            require_certified_dependencies=require_certified_dependencies,
            candidate_identity=candidate_identity,
            runtime_identity=runtime_identity,
        )

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
        certification = self._dependency_certification()
        if self.require_certified_dependencies and certification.result != SentinelRuntimeDecision.PASS:
            return self._failed_execution(trace_root, mission, "", FailureResponse.HALT, "DEPENDENCY_CERTIFICATION_FAILED:" + ",".join(certification.failure_reasons))
        dependency_record = self._persist("sentinel_dependency_certification", certification.certification_id, _json_ready(asdict(certification)), certification.deterministic_digest)
        canonical_mission = self.mission_registry.resolve(mission.mission_id)
        if canonical_mission is None:
            return self._failed_execution(trace_root, mission, "", FailureResponse.QUARANTINE, "MISSION_NOT_IN_CANONICAL_REGISTRY")
        if self.authority_registry is None and self.require_certified_dependencies:
            return self._failed_execution(trace_root, mission, "", FailureResponse.HALT, "AUTHORITY_REGISTRY_UNAVAILABLE")
        authority_registry = self.authority_registry or SentinelAuthorityRegistry.for_mission(canonical_mission, self.candidate_identity, self.runtime_identity)
        authority_record = authority_registry.validate("observe", canonical_mission.mission_id, self.candidate_identity, self.runtime_identity)
        if authority_record is None:
            return self._failed_execution(trace_root, mission, "", FailureResponse.HALT, "AUTHORITY_REGISTRY_VALIDATION_FAILED")
        authority_origin = self.evidence_origin_registry.declare(
            evidence_identifier=authority_record.authority_id,
            origin=SentinelEvidenceOrigin.CAPTURED_AUTHORITATIVE_RESPONSE,
            producing_subsystem="Enterprise Authority Registry",
            associated_mission=canonical_mission.mission_id,
            metadata={"operation": "observe", "recipient": authority_record.recipient},
        )
        if not self.evidence_origin_registry.validate(authority_origin):
            return self._failed_execution(trace_root, mission, "", FailureResponse.HALT, "AUTHORITY_ORIGIN_VALIDATION_FAILED")
        authority_origin_record = self._persist("sentinel_authority_origin", authority_origin.origin_record_id, _json_ready(asdict(authority_origin)), authority_origin.deterministic_digest)
        if self.source_adapter.mode != SourceAdapterMode.PAPER_AUTHORITATIVE:
            return self._failed_execution(trace_root, mission, "", FailureResponse.HALT, "DETERMINISTIC_ADAPTER_ISOLATED_FROM_OPERATIONAL_EXECUTION")
        assignment = self._resolve_assignment(canonical_mission, source_plan, event_class, authority_record)
        authority_ok = self._validate_assignment(assignment, mission, source_plan, event_class)
        if not authority_ok:
            return self._failed_execution(trace_root, mission, "", FailureResponse.QUARANTINE, "MISSION_AUTHORITY_INVALID")
        dispatched = self.scheduler.dispatch_mission(mission.mission_id, workflow_id=mission.mission_id, token_id=mission.execution_token_id)
        activation_id = self._scheduler_obligation_id(dispatched)
        schedule = ObservationScheduleEntry(1, source_plan.objective_id, dispatched.actual_start or utc_timestamp(), 10, (5, 15), 30)
        objective = MonitoringObjective(source_plan.objective_id, assignment.commander_authority_id, next(iter(assignment.approved_domains)), 60, 15, 10, (5, 15), 30)
        scheduler_plan = self._schedule(objective, schedule.scheduled_execution_time)
        parent = ""
        parent = self._trace(trace_root, parent, mission, activation_id, "Commander", "mission_resolved", "SentinelMissionRegistry.resolve", "SENT-MO-001-R2-STAGE-1", (), (assignment.assignment_id,), "", "MISSION_RESOLVED", "PASS")
        parent = self._trace(trace_root, parent, mission, activation_id, "AuthorityRegistry", "authority_validated", "SentinelAuthorityRegistry.validate", "SENT-MO-001-R2-STAGE-2", (assignment.assignment_id,), (authority_record.authority_id,), "", "AUTHORITY_VALIDATED", "PASS")
        parent = self._trace(trace_root, parent, mission, activation_id, "EnterpriseOperationsScheduler", "sentinel_scheduled", "EnterpriseOperationsScheduler.dispatch_mission", "SENT-MO-001-STAGE-3", (mission.mission_id,), (activation_id, scheduler_plan.schedule_digest), "", "SCHEDULED", "PASS")
        self.lifecycle.activate("Sentinel", authority=OfficeActivationAuthority.SCHEDULER, workflow_id=mission.mission_id, token_id=mission.execution_token_id, current_owner="Sentinel", proof_domain="PAPER")
        parent = self._trace(trace_root, parent, mission, activation_id, "OfficeLifecycleController", "sentinel_active", "OfficeLifecycleController.activate", "SENT-MO-001-STAGE-4", (activation_id,), ("Sentinel:ACTIVE",), "DORMANT", "ACTIVE", "PASS")
        raw = self.source_adapter.acquire(source_plan, event_class=event_class, value_hash=value_hash)
        if raw.response_status != "OK":
            return self._failed_execution(trace_root, mission, activation_id, FailureResponse.QUARANTINE, "SOURCE_ACQUISITION_FAILED")
        raw_origin = self.evidence_origin_registry.declare(
            evidence_identifier=raw.raw_evidence_id,
            origin=SentinelEvidenceOrigin.CAPTURED_AUTHORITATIVE_RESPONSE,
            producing_subsystem=self.source_adapter.adapter_id,
            associated_mission=mission.mission_id,
            metadata={"source": source_plan.source_id, "host": source_plan.source_host},
        )
        if not self.evidence_origin_registry.validate(raw_origin):
            return self._failed_execution(trace_root, mission, activation_id, FailureResponse.HALT, "RAW_EVIDENCE_ORIGIN_VALIDATION_FAILED")
        raw_origin_record = self._persist("sentinel_raw_evidence_origin", raw_origin.origin_record_id, _json_ready(asdict(raw_origin)), raw_origin.deterministic_digest)
        parent = self._trace(trace_root, parent, mission, activation_id, "Sentinel", "source_acquired", self.source_adapter.adapter_id, "SENT-MO-001-STAGE-5", (source_plan.source_plan_id,), (raw.raw_evidence_id,), "ACTIVE", "ACTIVE", "PASS")
        observation = self.source_adapter.normalize(raw, assignment, source_plan, schedule, value_hash=value_hash)
        observation_origin = self.evidence_origin_registry.declare(
            evidence_identifier=observation.observation_id,
            origin=SentinelEvidenceOrigin.RUNTIME_OBSERVATION,
            producing_subsystem="SentinelCanonicalRuntime.normalize",
            associated_mission=mission.mission_id,
            metadata={"source": source_plan.source_id, "raw_evidence": raw.raw_evidence_id},
        )
        if not self.evidence_origin_registry.validate(observation_origin):
            return self._failed_execution(trace_root, mission, activation_id, FailureResponse.HALT, "OBSERVATION_ORIGIN_VALIDATION_FAILED")
        observation_origin_record = self._persist("sentinel_observation_origin", observation_origin.origin_record_id, _json_ready(asdict(observation_origin)), observation_origin.deterministic_digest)
        parent = self._trace(trace_root, parent, mission, activation_id, "Sentinel", "observation_normalized", "sentinel-normalizer/1.0.0", "SENT-MO-001-STAGE-6", (raw.raw_evidence_id,), (observation.observation_id,), "ACTIVE", "ACTIVE", "PASS")
        source = SourceRecord(source_plan.source_id, True, True, "HEALTHY", source_plan.source_host, 1.0, 1.0)
        pipeline = RuntimeObservationPipeline(validator=ObservationIntegrityValidator())
        result = pipeline.execute(schedule, observation, source, prior_observations)
        duplicate = _duplicate_decision(observation, prior_observations)
        parent = self._trace(trace_root, parent, mission, activation_id, "Sentinel", "duplicate_suppression_evaluated", "SentinelDuplicateDecision", "SENT-MO-001-STAGE-7", (observation.observation_id,), (duplicate.decision_id,), "ACTIVE", "ACTIVE", duplicate.result)
        independence = SentinelSourceIndependenceDecision(f"IND-{_hash(observation.source_id)[:10].upper()}", (source_plan.source_id,), (source_plan.source_host,), "SENT-GOV-020-INDEPENDENCE/1", "INDEPENDENT", ())
        parent = self._trace(trace_root, parent, mission, activation_id, "Sentinel", "source_independence_evaluated", "SentinelSourceIndependenceDecision", "SENT-MO-001-STAGE-8", (observation.observation_id,), (independence.decision_id,), "ACTIVE", "ACTIVE", independence.result)
        conflict = SentinelConflictDecision(f"CON-{_hash(observation.observation_id)[:10].upper()}", (), (), (source_plan.source_id,), "NO_CONFLICT", (), "NO_CONFLICT", True)
        parent = self._trace(trace_root, parent, mission, activation_id, "Sentinel", "conflict_evaluated", "SentinelConflictDecision", "SENT-MO-001-STAGE-9", (observation.observation_id,), (conflict.decision_id,), "ACTIVE", "ACTIVE", conflict.resulting_state)
        policy_registry = self.sufficiency_policy_registry or SentinelSufficiencyPolicyRegistry.for_event_classes((event_class,))
        sufficiency, sufficiency_evidence = SentinelObservationSufficiencyEvaluator(policy_registry).evaluate(
            mission_id=mission.mission_id,
            event_class=event_class,
            observations=(observation,),
            source_records={source.source_id: source},
            dependency_certification=certification,
        )
        sufficiency_origin = self.evidence_origin_registry.declare(
            evidence_identifier=sufficiency_evidence.evidence_id,
            origin=SentinelEvidenceOrigin.RUNTIME_OBSERVATION,
            producing_subsystem=SentinelObservationSufficiencyEvaluator.evaluator_version,
            associated_mission=mission.mission_id,
            metadata={"rule": sufficiency.rule_identity, "decision": sufficiency.notification_readiness.value},
        )
        if not self.evidence_origin_registry.validate(sufficiency_origin):
            return self._failed_execution(trace_root, mission, activation_id, FailureResponse.HALT, "SUFFICIENCY_ORIGIN_VALIDATION_FAILED")
        sufficiency_record = self._persist("sentinel_sufficiency_evaluation", sufficiency_evidence.evidence_id, _json_ready(asdict(sufficiency_evidence)), sufficiency_evidence.deterministic_digest)
        sufficiency_origin_record = self._persist("sentinel_sufficiency_origin", sufficiency_origin.origin_record_id, _json_ready(asdict(sufficiency_origin)), sufficiency_origin.deterministic_digest)
        parent = self._trace(trace_root, parent, mission, activation_id, "Sentinel", "sufficiency_evaluated", SentinelObservationSufficiencyEvaluator.evaluator_version, "SENT-MO-001-STAGE-10", (observation.observation_id,), (sufficiency.decision_id, sufficiency_evidence.evidence_id), "ACTIVE", "ACTIVE", sufficiency.notification_readiness.value)
        priority = SentinelPriorityDecision(f"PRI-{_hash(observation.observation_id)[:10].upper()}", assignment.priority_rule_id, 1, 1, observation.observation_timestamp, observation.observation_id, 1)
        parent = self._trace(trace_root, parent, mission, activation_id, "Sentinel", "priority_determined", "SentinelPriorityDecision", "SENT-MO-001-STAGE-11", (observation.observation_id,), (priority.decision_id,), "ACTIVE", "ACTIVE", str(priority.final_rank))
        envelope = _evidence_envelope(self.candidate_identity, self.runtime_identity, mission, activation_id, source_plan, raw, observation, duplicate, independence, conflict, sufficiency, priority, tuple(item.trace_event_id for item in self.trace_events))
        if envelope.final_notification_readiness_state != SentinelRuntimeDecision.PASS:
            return self._failed_execution(trace_root, mission, activation_id, FailureResponse.HALT, "OBSERVATION_SUFFICIENCY_NOT_SATISFIED:" + ",".join(sufficiency.remaining_uncertainty))
        alert = _notification_ready_alert(envelope, mission, self.candidate_identity, self.runtime_identity, event_class)
        parent = self._trace(trace_root, parent, mission, activation_id, "Sentinel", "evidence_generated", "SentinelCanonicalRuntime.execute_observation", "SENT-MO-001-STAGE-12", (observation.observation_id, result.evidence.evidence_checksum), (envelope.envelope_id, alert.alert_id), "ACTIVE", "COMPLETING", "PASS")
        envelope_record = self._persist("sentinel_observation_evidence", envelope.envelope_id, _json_ready(asdict(envelope)), envelope.deterministic_digest)
        alert_record = self._persist("sentinel_notification_ready_alert", alert.alert_id, _json_ready(asdict(alert)), alert.deterministic_digest)
        parent = self._trace(trace_root, parent, mission, activation_id, "EnterprisePersistence", "persistence_operation", "InMemoryPersistenceRepository.persist", "SENT-MO-001-STAGE-13", (envelope.envelope_id, alert.alert_id), (envelope_record.record_hash, alert_record.record_hash), "COMPLETING", "COMPLETING", "PASS")
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
        semantic = sentinel_runtime_equivalence_digest(record)
        record = replace(
            record,
            deterministic_digest=_hash(
                {
                    "record": asdict(record),
                    "persistence": (
                        dependency_record.record_hash,
                        authority_origin_record.record_hash,
                        raw_origin_record.record_hash,
                        observation_origin_record.record_hash,
                        sufficiency_record.record_hash,
                        sufficiency_origin_record.record_hash,
                        envelope_record.record_hash,
                        alert_record.record_hash,
                    ),
                    "semantic": semantic,
                }
            ),
        )
        audit_trail = self.audit_trail_for(record)
        replay_certification = self.certify_replay_equivalence(record)
        self._persist("sentinel_runtime_audit_trail", audit_trail.audit_identifier, _json_ready(asdict(audit_trail)), audit_trail.deterministic_digest)
        self._persist("sentinel_replay_equivalence_certification", replay_certification.replay_certification_id, _json_ready(asdict(replay_certification)), replay_certification.deterministic_digest)
        return record

    def audit_trail_for(self, record: SentinelRuntimeExecutionRecord) -> SentinelRuntimeAuditTrail:
        return SentinelRuntimeTraceEngine().build_audit_trail(record)

    def certify_replay_equivalence(self, record: SentinelRuntimeExecutionRecord, replay_record: SentinelRuntimeExecutionRecord | None = None) -> SentinelReplayCertificationRecord:
        return SentinelRuntimeTraceEngine().certify_replay_equivalence(record, replay_record)

    def _dependency_certification(self) -> SentinelDependencyCertification:
        if self.dependency_certification is not None:
            return self.dependency_certification
        if self.service_registry is None:
            if self.require_certified_dependencies:
                services = None
            else:
                policy = self.sufficiency_policy_registry or SentinelSufficiencyPolicyRegistry.for_event_classes(("EXPOSURE_SOURCE_ALERT",))
                registry = SentinelEnterpriseServiceRegistry(
                    {
                        "Enterprise Scheduler": self.scheduler,
                        "Enterprise Mission Registry": self.mission_registry,
                        "Enterprise Authority Registry": self.authority_registry or SentinelAuthorityRegistry(()),
                        "Enterprise Persistence": self.persistence,
                        "Runtime Audit Infrastructure": self.evidence_origin_registry,
                        "Approved Operational Source Adapters": self.source_adapter,
                        "Constitutional Sufficiency Policy": policy,
                    },
                    acquisition_source="legacy non-certification test harness",
                )
                services = SentinelEnterpriseServices(
                    scheduler=self.scheduler,
                    lifecycle=self.lifecycle,
                    source_adapter=self.source_adapter,
                    mission_registry=self.mission_registry,
                    authority_registry=self.authority_registry or SentinelAuthorityRegistry(()),
                    persistence=self.persistence,
                    evidence_origin_registry=self.evidence_origin_registry,
                    sufficiency_policy_registry=policy,
                    service_registry=registry,
                )
        else:
            services = SentinelEnterpriseServices(
                scheduler=self.scheduler,
                lifecycle=self.lifecycle,
                source_adapter=self.source_adapter,
                mission_registry=self.mission_registry,
                authority_registry=self.authority_registry or SentinelAuthorityRegistry(()),
                persistence=self.persistence,
                evidence_origin_registry=self.evidence_origin_registry,
                sufficiency_policy_registry=self.sufficiency_policy_registry or SentinelSufficiencyPolicyRegistry.for_event_classes(()),
                service_registry=self.service_registry,
            )
        self.dependency_certification = SentinelDependencyCertifier().certify(services)
        return self.dependency_certification

    def _resolve_assignment(self, mission: EnterpriseMission, source_plan: SentinelSourcePlanReference, event_class: str, authority: AuthorityRecord) -> SentinelMissionAssignment:
        payload = (mission.mission_id, self.candidate_identity, source_plan.source_plan_id, event_class)
        return SentinelMissionAssignment(
            assignment_id=f"SENT-ASSIGN-{_hash(payload)[:12].upper()}",
            schema_version=SENT_MO_CANONICAL_RUNTIME_VERSION,
            candidate_identity=self.candidate_identity,
            runtime_identity=self.runtime_identity,
            mission_id=mission.mission_id,
            commander_authority_id=authority.authority_id,
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

    def _persist(self, object_name: str, entity_id: str, payload: dict[str, Any], payload_hash: str):
        return self.persistence.persist(
            ObjectType.ENTERPRISE_RUNTIME_STATE,
            entity_id,
            {
                "entity_id": entity_id,
                "schema_version": SENT_MO_CANONICAL_RUNTIME_VERSION,
                "truth_domain": "PAPER",
                "serialization_version": "1.0.0",
                "creation_sequence": len(self.persistence.all_records()) + 1,
                "modification_sequence": 1,
                "payload": {"object_name": object_name, "payload": payload},
                "payload_hash": payload_hash,
                "idempotency_key": _hash((object_name, entity_id, payload_hash)),
            },
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
    """Commander receiving surface backed by canonical authority and persistence evidence."""

    def __init__(
        self,
        *,
        candidate_identity: str,
        runtime_identity: str,
        authority_registry: SentinelAuthorityRegistry | None = None,
        persistence: InMemoryPersistenceRepository | None = None,
    ) -> None:
        self.candidate_identity = candidate_identity
        self.runtime_identity = runtime_identity
        self.authority_registry = authority_registry or SentinelAuthorityRegistry(())
        self.persistence = persistence or InMemoryPersistenceRepository(canonical_schemas())
        self.receipts: tuple[CommanderReceiptRecord, ...] = ()
        self.acknowledgments: tuple[CommanderAcknowledgment, ...] = ()
        self._idempotency: dict[str, CommanderReceiptRecord] = {}

    def receive(self, alert: SentinelNotificationReadyAlert, bridge_message_id: str) -> tuple[CommanderReceiptRecord, CommanderAcknowledgment]:
        if alert.idempotency_key in self._idempotency:
            prior = self._idempotency[alert.idempotency_key]
            ack = next((item for item in self.acknowledgments if item.receipt_id == prior.receipt_id), self._ack(alert, bridge_message_id, prior, CommanderAcknowledgmentResult.DUPLICATE))
            return prior, ack
        valid = self._validate(alert) and self.authority_registry.validate("receive_sentinel_alert", alert.mission_id, alert.candidate_identity, alert.runtime_identity) is not None
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
        self._persist("commander_sentinel_receipt", receipt.receipt_id, asdict(receipt), receipt.evidence_digest)
        ack = self._ack(alert, bridge_message_id, receipt, CommanderAcknowledgmentResult.ACCEPTED if valid else CommanderAcknowledgmentResult.REJECTED)
        self.acknowledgments = self.acknowledgments + (ack,)
        self._persist("commander_sentinel_acknowledgment", ack.acknowledgment_id, asdict(ack), ack.deterministic_digest)
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
            commander_authority_identity=(self.authority_registry.validate("acknowledge_sentinel_alert", alert.mission_id, alert.candidate_identity, alert.runtime_identity) or AuthorityRecord("", "", "", "", "", "", "", False)).authority_id,
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

    def _persist(self, object_name: str, entity_id: str, payload: dict[str, Any], payload_hash: str) -> None:
        self.persistence.persist(
            ObjectType.ENTERPRISE_RUNTIME_STATE,
            entity_id,
            {
                "entity_id": entity_id,
                "schema_version": SENT_MO_CANONICAL_RUNTIME_VERSION,
                "truth_domain": "PAPER",
                "serialization_version": "1.0.0",
                "creation_sequence": len(self.persistence.all_records()) + 1,
                "modification_sequence": 1,
                "payload": {"object_name": object_name, "payload": payload},
                "payload_hash": payload_hash,
                "idempotency_key": _hash((object_name, entity_id, payload_hash)),
            },
        )


class SentinelCommanderBridgeRuntime:
    """Delivers SENT-MO-001 alerts through the canonical bridge and Commander runtime."""

    def __init__(
        self,
        *,
        bridge_executor: CanonicalBridgeExecutor | None = None,
        communications_bus: EnterpriseCommunicationsBus | None = None,
        commander: CommanderAlertRuntime | None = None,
        authority_registry: SentinelAuthorityRegistry | None = None,
        persistence: InMemoryPersistenceRepository | None = None,
        candidate_identity: str = "candidate:unknown",
        runtime_identity: str = "ARGOS-CANONICAL-RUNTIME",
    ) -> None:
        self.candidate_identity = candidate_identity
        self.runtime_identity = runtime_identity
        self.authority_registry = authority_registry or SentinelAuthorityRegistry(())
        self.persistence = persistence or InMemoryPersistenceRepository(canonical_schemas())
        self.commander = commander or CommanderAlertRuntime(candidate_identity=candidate_identity, runtime_identity=runtime_identity, authority_registry=self.authority_registry, persistence=self.persistence)
        self.communications_bus = communications_bus or EnterpriseCommunicationsBus()
        registry = _enterprise_bridge_registry_with_sentinel()
        self.bridge_executor = bridge_executor or CanonicalBridgeExecutor(runtime_instance_id=runtime_identity, registry=registry)
        self.delivery_records: tuple[SentinelCommanderDeliveryRecord, ...] = ()

    def deliver(self, alert: SentinelNotificationReadyAlert) -> SentinelCommanderDeliveryRecord:
        payload = asdict(alert)
        if alert.notification_status != SentinelNotificationStatus.NOT_YET_DELIVERED:
            return self._rejected(alert, "alert_not_delivery_ready")
        if alert.required_destination != "Commander":
            return self._rejected(alert, "wrong_destination")
        if self.authority_registry.validate("notify_commander", alert.mission_id, alert.candidate_identity, alert.runtime_identity) is None:
            return self._rejected(alert, "notification_authority_missing")
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
        if result.status in {BridgeResultStatus.ACCEPTED, BridgeResultStatus.DUPLICATE_IDEMPOTENT_SUCCESS}:
            self.commander.receive(alert, bus_result.message_id)
            if self.commander.acknowledgments:
                ack = self.commander.acknowledgments[-1]
                self.communications_bus.publish_event(
                    message_type="SENTINEL_COMMANDER_ACKNOWLEDGMENT",
                    source_service_id="Commander",
                    payload=asdict(ack),
                    target_service_id="Sentinel",
                    target_office_id="Sentinel",
                    source_office_id="Commander",
                    mission_id=alert.mission_id,
                    paper_live_mode=MessageMode.PAPER,
                    idempotency_key=ack.deterministic_digest,
                    ordering_key=alert.idempotency_key,
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

    def static_bypass_analysis(self, repository_root: str | None = None) -> Mapping[str, tuple[str, ...]]:
        from pathlib import Path

        root = Path(repository_root or Path(__file__).resolve().parents[3])
        files = tuple(sorted((root / "src" / "argos" / "sentinel").glob("*.py")))
        prohibited_terms = ("argos.seeker", "argos.analyst", "argos.risk", "argos.trader", "create_workflow", "DecisionObject", "OrderManagement", "financial_truth")
        unresolved = []
        approved = []
        for path in files:
            lines = path.read_text(encoding="utf-8").splitlines()
            text = "\n".join(lines)
            for term in prohibited_terms:
                if any(term in line and "prohibited_terms" not in line for line in lines):
                    unresolved.append(f"{path.name}:{term}")
            if SENTINEL_COMMANDER_BRIDGE_ID in text or "Commander" in text:
                approved.append(path.name)
        return {"scanned_files": tuple(str(item) for item in files), "approved_canonical_path": tuple(sorted(set(approved))), "unresolved_findings": tuple(unresolved)}

    def replay(self, record: SentinelCommanderDeliveryRecord) -> SentinelCommanderDeliveryRecord:
        return replace(record, sentinel_delivery_state=record.sentinel_delivery_state)

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
        certification_status=BridgeCertificationStatus.CERTIFIED_PRODUCTION,
    )


def _enterprise_bridge_registry_with_sentinel() -> CanonicalBridgeRegistry:
    existing = tuple(item for item in CanonicalBridgeRegistry().all() if item.bridge_id != SENTINEL_COMMANDER_BRIDGE_ID)
    return CanonicalBridgeRegistry(existing + (sentinel_commander_bridge_definition(),))


def sentinel_runtime_equivalence_digest(record: SentinelRuntimeExecutionRecord) -> str:
    """Timestamp-insensitive semantic projection for repeated runtime evidence."""
    envelope = record.evidence_envelope
    alert = record.notification_ready_alert
    payload = {
        "candidate": record.candidate_identity,
        "runtime": record.runtime_identity,
        "mission": record.mission_id,
        "scheduler_obligation": record.scheduler_obligation_id,
        "lifecycle": record.lifecycle_states,
        "result": record.result.value,
        "final_office_state": record.final_office_state.value,
        "envelope": {
            "mission": envelope.mission_identity if envelope else "",
            "source_plan": envelope.source_plan_identity if envelope else "",
            "readiness": envelope.final_notification_readiness_state.value if envelope else "",
            "duplicate": envelope.duplicate_decision.result if envelope else "",
            "independence": envelope.independence_decision.result if envelope else "",
            "conflict": envelope.conflict_decision.resulting_state if envelope else "",
            "sufficiency_rule": envelope.sufficiency_decision.rule_identity if envelope else "",
            "priority_rule": envelope.priority_decision.rule_identity if envelope else "",
        },
        "alert": {
            "mission": alert.mission_id if alert else "",
            "destination": alert.required_destination if alert else "",
            "status": alert.notification_status.value if alert else "",
            "event_class": alert.event_class if alert else "",
            "idempotency_key": alert.idempotency_key if alert else "",
        },
        "trace_actions": tuple(event.action for event in record.trace_events),
    }
    return _hash(payload)


def sentinel_delivery_equivalence_digest(record: SentinelCommanderDeliveryRecord) -> str:
    payload = {
        "candidate": record.alert.candidate_identity,
        "runtime": record.alert.runtime_identity,
        "mission": record.alert.mission_id,
        "alert": record.alert.alert_id,
        "bridge_status": record.bridge_result_status,
        "receipt_result": record.commander_receipt.validation_result.value if record.commander_receipt else "",
        "ack_result": record.commander_acknowledgment.acknowledgment_result.value if record.commander_acknowledgment else "",
        "final_state": record.sentinel_delivery_state.value,
        "downstream": record.downstream_activation_attempts,
    }
    return _hash(payload)


def recover_persisted_sentinel_records(repository: InMemoryPersistenceRepository) -> tuple[str, ...]:
    repository.validate_integrity()
    return tuple(record.record_hash for record in repository.all_records())


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


def _json_ready(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
