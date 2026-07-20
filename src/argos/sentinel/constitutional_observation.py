"""SENT-MO-001 through SENT-MO-005 Sentinel constitutional observation controls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Iterable, Mapping


SENT_MO_VERSION = "SENT-MO-001-005/1.0.0"


class SentinelDecision(str, Enum):
    PASS = "PASS"
    FAIL_CLOSED = "FAIL_CLOSED"
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    DUPLICATE = "DUPLICATE"
    CONFLICT = "CONFLICT"
    NOTIFIED_COMMANDER = "NOTIFIED_COMMANDER"


class SentinelFailure(str, Enum):
    NON_DETERMINISTIC_SCHEDULE = "non_deterministic_schedule"
    UNAUTHORIZED_OBJECTIVE = "unauthorized_objective"
    MISSING_PROVENANCE = "missing_provenance"
    SOURCE_UNHEALTHY = "source_unhealthy"
    SOURCE_UNAUTHORIZED = "source_unauthorized"
    STALE_OBSERVATION = "stale_observation"
    DUPLICATE_OBSERVATION = "duplicate_observation"
    SOURCE_NOT_INDEPENDENT = "source_not_independent"
    CONFLICTING_OBSERVATION = "conflicting_observation"
    INCOMPLETE_EVIDENCE = "incomplete_evidence"
    PLACEHOLDER_OBSERVATION = "placeholder_observation"
    SYNTHETIC_OBSERVATION = "synthetic_observation"
    AUTHORITY_UNVERIFIED = "authority_unverified"
    BRIDGE_UNVERIFIED = "bridge_unverified"
    TOKEN_DISCONTINUITY = "token_discontinuity"
    COMMANDER_NOT_FIRST = "commander_not_first"
    DUPLICATE_NOTIFICATION = "duplicate_notification"
    WORKFLOW_CREATION_ATTEMPT = "workflow_creation_attempt"
    TRACEABILITY_GAP = "traceability_gap"
    MISSING_CERTIFICATION_EVIDENCE = "missing_certification_evidence"
    REPLAY_DIVERGENCE = "replay_divergence"
    MISSING_RUNTIME_TRACE = "missing_runtime_trace"
    MISSING_BRIDGE_EVIDENCE = "missing_bridge_evidence"
    MUTABLE_CERTIFICATION_ARTIFACT = "mutable_certification_artifact"


@dataclass(frozen=True)
class MonitoringObjective:
    objective_id: str
    commander_authorization_id: str
    monitoring_domain: str
    interval_seconds: int
    polling_cadence_seconds: int
    priority: int
    retry_policy: tuple[int, ...]
    timeout_seconds: int
    active: bool = True


@dataclass(frozen=True)
class ObservationScheduleEntry:
    sequence_number: int
    objective_id: str
    scheduled_execution_time: str
    priority: int
    retry_policy: tuple[int, ...]
    timeout_seconds: int


@dataclass(frozen=True)
class ObservationSchedulePlan:
    decision: SentinelDecision
    failures: tuple[SentinelFailure, ...]
    entries: tuple[ObservationScheduleEntry, ...]
    schedule_digest: str


class DeterministicObservationScheduler:
    """SENT-MO-001 deterministic Commander-directed observation scheduling."""

    def build_schedule(self, objectives: Iterable[MonitoringObjective], base_time_utc: str) -> ObservationSchedulePlan:
        failures: list[SentinelFailure] = []
        active = tuple(item for item in objectives if item.active)
        for objective in active:
            if not objective.commander_authorization_id:
                failures.append(SentinelFailure.UNAUTHORIZED_OBJECTIVE)
            if objective.interval_seconds <= 0 or objective.polling_cadence_seconds <= 0 or objective.timeout_seconds <= 0:
                failures.append(SentinelFailure.NON_DETERMINISTIC_SCHEDULE)
        ordered = sorted(active, key=lambda item: (-item.priority, item.objective_id, item.monitoring_domain))
        entries = tuple(
            ObservationScheduleEntry(
                sequence_number=index + 1,
                objective_id=objective.objective_id,
                scheduled_execution_time=f"{base_time_utc}+{index * objective.polling_cadence_seconds}s",
                priority=objective.priority,
                retry_policy=objective.retry_policy,
                timeout_seconds=objective.timeout_seconds,
            )
            for index, objective in enumerate(ordered)
        )
        unique = tuple(dict.fromkeys(failures))
        return ObservationSchedulePlan(
            decision=SentinelDecision.PASS if not unique else SentinelDecision.FAIL_CLOSED,
            failures=unique,
            entries=entries,
            schedule_digest=_digest(asdict(entry) for entry in entries),
        )


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    enabled: bool
    authorized: bool
    health_state: str
    independence_group: str
    availability_score: float
    response_success_rate: float


@dataclass(frozen=True)
class ObservationRecord:
    observation_id: str
    objective_id: str
    source_id: str
    collection_mechanism: str
    acquisition_timestamp: str
    observation_timestamp: str
    evidence_creation_timestamp: str
    value_hash: str
    evidence_references: tuple[str, ...]
    mission_assignment_id: str
    freshness_limit_seconds: int
    observed_age_seconds: int
    placeholder: bool = False
    synthetic_indicator: bool = False


@dataclass(frozen=True)
class ObservationValidationDecision:
    decision: SentinelDecision
    failures: tuple[SentinelFailure, ...]
    fingerprint: str
    admissible: bool
    provenance: Mapping[str, str]


class ObservationIntegrityValidator:
    """SENT-MO-002 observation integrity, source validation, freshness, and conflict checks."""

    def validate(
        self,
        observation: ObservationRecord,
        source: SourceRecord | None,
        prior_observations: Iterable[ObservationRecord] = (),
        corroborating_sources: Iterable[SourceRecord] = (),
        require_independent_corroboration: bool = False,
    ) -> ObservationValidationDecision:
        failures: list[SentinelFailure] = []
        required = (
            observation.observation_id,
            observation.objective_id,
            observation.source_id,
            observation.collection_mechanism,
            observation.acquisition_timestamp,
            observation.observation_timestamp,
            observation.evidence_creation_timestamp,
            observation.mission_assignment_id,
        )
        if any(_blank(value) for value in required):
            failures.append(SentinelFailure.MISSING_PROVENANCE)
        if source is None or not source.enabled or not source.authorized:
            failures.append(SentinelFailure.SOURCE_UNAUTHORIZED)
        elif source.health_state != "HEALTHY" or source.availability_score <= 0 or source.response_success_rate <= 0:
            failures.append(SentinelFailure.SOURCE_UNHEALTHY)
        if observation.observed_age_seconds > observation.freshness_limit_seconds:
            failures.append(SentinelFailure.STALE_OBSERVATION)
        if not observation.evidence_references:
            failures.append(SentinelFailure.INCOMPLETE_EVIDENCE)
        if observation.placeholder:
            failures.append(SentinelFailure.PLACEHOLDER_OBSERVATION)
        if observation.synthetic_indicator:
            failures.append(SentinelFailure.SYNTHETIC_OBSERVATION)

        fingerprint = observation_fingerprint(observation)
        prior = tuple(prior_observations)
        if any(observation_fingerprint(item) == fingerprint for item in prior):
            failures.append(SentinelFailure.DUPLICATE_OBSERVATION)
        if any(item.objective_id == observation.objective_id and item.value_hash != observation.value_hash for item in prior):
            failures.append(SentinelFailure.CONFLICTING_OBSERVATION)
        if require_independent_corroboration:
            independent = {item.independence_group for item in corroborating_sources if item.source_id != observation.source_id}
            if source is None or source.independence_group in independent or not independent:
                failures.append(SentinelFailure.SOURCE_NOT_INDEPENDENT)

        unique = tuple(dict.fromkeys(failures))
        if SentinelFailure.CONFLICTING_OBSERVATION in unique:
            decision = SentinelDecision.CONFLICT
        elif SentinelFailure.DUPLICATE_OBSERVATION in unique:
            decision = SentinelDecision.DUPLICATE
        elif unique:
            decision = SentinelDecision.REJECTED
        else:
            decision = SentinelDecision.ADMITTED
        return ObservationValidationDecision(
            decision=decision,
            failures=unique,
            fingerprint=fingerprint,
            admissible=decision == SentinelDecision.ADMITTED,
            provenance={
                "source_id": observation.source_id,
                "collection_mechanism": observation.collection_mechanism,
                "acquisition_timestamp": observation.acquisition_timestamp,
                "mission_assignment_id": observation.mission_assignment_id,
            },
        )


@dataclass(frozen=True)
class CommanderNotificationRequest:
    notification_id: str
    observation_id: str
    event_id: str
    commander_recipient: str
    runtime_bridge_id: str
    workflow_token_id: str
    authority_verified: bool
    bridge_verified: bool
    token_continuous: bool
    downstream_recipients: tuple[str, ...] = ()
    workflow_creation_attempted: bool = False


@dataclass(frozen=True)
class CommanderNotificationTrace:
    decision: SentinelDecision
    failures: tuple[SentinelFailure, ...]
    notification_order: tuple[str, ...]
    runtime_trace_id: str
    audit_identifier: str


class CommanderNotificationRuntime:
    """SENT-MO-003 Commander-first runtime notification with no workflow authority."""

    def __init__(self) -> None:
        self._delivered: set[str] = set()

    def notify(self, request: CommanderNotificationRequest) -> CommanderNotificationTrace:
        failures: list[SentinelFailure] = []
        if request.notification_id in self._delivered:
            failures.append(SentinelFailure.DUPLICATE_NOTIFICATION)
        if request.commander_recipient != "Commander":
            failures.append(SentinelFailure.COMMANDER_NOT_FIRST)
        if request.downstream_recipients and request.downstream_recipients[0] != "Commander":
            failures.append(SentinelFailure.COMMANDER_NOT_FIRST)
        if not request.authority_verified:
            failures.append(SentinelFailure.AUTHORITY_UNVERIFIED)
        if not request.bridge_verified:
            failures.append(SentinelFailure.BRIDGE_UNVERIFIED)
        if not request.token_continuous:
            failures.append(SentinelFailure.TOKEN_DISCONTINUITY)
        if request.workflow_creation_attempted:
            failures.append(SentinelFailure.WORKFLOW_CREATION_ATTEMPT)
        unique = tuple(dict.fromkeys(failures))
        if not unique:
            self._delivered.add(request.notification_id)
        order = ("Commander",) + tuple(item for item in request.downstream_recipients if item != "Commander")
        return CommanderNotificationTrace(
            decision=SentinelDecision.NOTIFIED_COMMANDER if not unique else SentinelDecision.FAIL_CLOSED,
            failures=unique,
            notification_order=order,
            runtime_trace_id=_digest(asdict(request)),
            audit_identifier=f"AUDIT-{request.notification_id}",
        )


class SyntheticObservationEliminationEngine:
    """SENT-MO-004 rejects unsupported, stale, duplicate, placeholder, and synthetic observations."""

    def __init__(self, validator: ObservationIntegrityValidator | None = None) -> None:
        self.validator = validator or ObservationIntegrityValidator()

    def evaluate(
        self,
        observation: ObservationRecord,
        source: SourceRecord | None,
        prior_observations: Iterable[ObservationRecord] = (),
    ) -> ObservationValidationDecision:
        return self.validator.validate(observation, source, prior_observations)


@dataclass(frozen=True)
class ObservationRuntimeTrace:
    mission_id: str
    observation_id: str
    scheduler_trace: str
    observation_execution_trace: str
    evidence_generation_trace: str
    duplicate_evaluation_trace: str
    independence_evaluation_trace: str
    conflict_evaluation_trace: str
    archival_trace: str
    commander_notification_trace: str
    trace_digest: str


@dataclass(frozen=True)
class ObservationEvidenceRecord:
    observation_id: str
    mission_id: str
    commander_assignment_id: str
    observation_timestamp: str
    monitored_domain: str
    observation_result_hash: str
    duplicate_status: SentinelDecision
    source_independence_result: SentinelDecision
    conflict_evaluation: SentinelDecision
    execution_trace_digest: str
    evidence_checksum: str


@dataclass(frozen=True)
class ObservationPipelineResult:
    decision: SentinelDecision
    failures: tuple[SentinelFailure, ...]
    validation: ObservationValidationDecision
    evidence: ObservationEvidenceRecord
    runtime_trace: ObservationRuntimeTrace
    notification_trace: CommanderNotificationTrace | None


class RuntimeObservationPipeline:
    """SENT-MO-001 deterministic observation execution pipeline."""

    def __init__(
        self,
        validator: ObservationIntegrityValidator | None = None,
        notifier: CommanderNotificationRuntime | None = None,
    ) -> None:
        self.validator = validator or ObservationIntegrityValidator()
        self.notifier = notifier or CommanderNotificationRuntime()
        self._archive: tuple[ObservationEvidenceRecord, ...] = ()
        self._traces: tuple[ObservationRuntimeTrace, ...] = ()

    @property
    def archive(self) -> tuple[ObservationEvidenceRecord, ...]:
        return self._archive

    @property
    def traces(self) -> tuple[ObservationRuntimeTrace, ...]:
        return self._traces

    def execute(
        self,
        schedule_entry: ObservationScheduleEntry,
        observation: ObservationRecord,
        source: SourceRecord,
        prior_observations: Iterable[ObservationRecord] = (),
        require_independent_corroboration: bool = False,
        corroborating_sources: Iterable[SourceRecord] = (),
    ) -> ObservationPipelineResult:
        validation = self.validator.validate(
            observation,
            source,
            prior_observations,
            corroborating_sources,
            require_independent_corroboration,
        )
        duplicate_status = SentinelDecision.DUPLICATE if SentinelFailure.DUPLICATE_OBSERVATION in validation.failures else SentinelDecision.PASS
        independence_status = SentinelDecision.FAIL_CLOSED if SentinelFailure.SOURCE_NOT_INDEPENDENT in validation.failures else SentinelDecision.PASS
        conflict_status = SentinelDecision.CONFLICT if SentinelFailure.CONFLICTING_OBSERVATION in validation.failures else SentinelDecision.PASS
        trace = _runtime_trace(schedule_entry, observation, validation, "")
        evidence = ObservationEvidenceRecord(
            observation_id=observation.observation_id,
            mission_id=observation.mission_assignment_id,
            commander_assignment_id=observation.mission_assignment_id,
            observation_timestamp=observation.observation_timestamp,
            monitored_domain=schedule_entry.objective_id,
            observation_result_hash=observation.value_hash,
            duplicate_status=duplicate_status,
            source_independence_result=independence_status,
            conflict_evaluation=conflict_status,
            execution_trace_digest=trace.trace_digest,
            evidence_checksum=_digest({"observation": asdict(observation), "validation": asdict(validation)}),
        )
        notification_trace = None
        failures = list(validation.failures)
        if validation.admissible:
            notification_trace = self.notifier.notify(
                CommanderNotificationRequest(
                    notification_id=f"NOTIFY-{observation.observation_id}",
                    observation_id=observation.observation_id,
                    event_id=f"EVENT-{observation.observation_id}",
                    commander_recipient="Commander",
                    runtime_bridge_id="SENTINEL-COMMANDER-BRIDGE",
                    workflow_token_id=observation.mission_assignment_id,
                    authority_verified=True,
                    bridge_verified=True,
                    token_continuous=True,
                    downstream_recipients=("Commander",),
                )
            )
            failures.extend(notification_trace.failures)
            trace = _runtime_trace(schedule_entry, observation, validation, notification_trace.runtime_trace_id)
            evidence = ObservationEvidenceRecord(
                observation_id=evidence.observation_id,
                mission_id=evidence.mission_id,
                commander_assignment_id=evidence.commander_assignment_id,
                observation_timestamp=evidence.observation_timestamp,
                monitored_domain=evidence.monitored_domain,
                observation_result_hash=evidence.observation_result_hash,
                duplicate_status=evidence.duplicate_status,
                source_independence_result=evidence.source_independence_result,
                conflict_evaluation=evidence.conflict_evaluation,
                execution_trace_digest=trace.trace_digest,
                evidence_checksum=_digest({"observation": asdict(observation), "trace": asdict(trace)}),
            )
        unique = tuple(dict.fromkeys(failures))
        self._archive = self._archive + (evidence,)
        self._traces = self._traces + (trace,)
        return ObservationPipelineResult(
            decision=SentinelDecision.PASS if not unique else SentinelDecision.FAIL_CLOSED,
            failures=unique,
            validation=validation,
            evidence=evidence,
            runtime_trace=trace,
            notification_trace=notification_trace,
        )


@dataclass(frozen=True)
class ObservationReplayResult:
    decision: SentinelDecision
    failures: tuple[SentinelFailure, ...]
    replay_digest: str


class ObservationReplayEngine:
    """Replays runtime traces and evidence without creating new observation truth."""

    def replay(self, traces: Iterable[ObservationRuntimeTrace], evidence: Iterable[ObservationEvidenceRecord]) -> ObservationReplayResult:
        trace_items = tuple(traces)
        evidence_items = tuple(evidence)
        failures: list[SentinelFailure] = []
        if len(trace_items) != len(evidence_items):
            failures.append(SentinelFailure.REPLAY_DIVERGENCE)
        for trace, record in zip(trace_items, evidence_items):
            if trace.trace_digest != record.execution_trace_digest:
                failures.append(SentinelFailure.REPLAY_DIVERGENCE)
        digest = _digest({"traces": tuple(asdict(item) for item in trace_items), "evidence": tuple(asdict(item) for item in evidence_items)})
        unique = tuple(dict.fromkeys(failures))
        return ObservationReplayResult(SentinelDecision.PASS if not unique else SentinelDecision.FAIL_CLOSED, unique, digest)


@dataclass(frozen=True)
class CommanderBridgeDiagnostic:
    bridge_id: str
    throughput_count: int
    rejected_count: int
    authority_failures: int
    token_continuity_failures: int
    replay_consistent: bool
    evidence_generated: bool


class CommanderBridgeCertification:
    """SENT-MO-002 bridge diagnostics and replay consistency certification."""

    def certify(self, traces: Iterable[CommanderNotificationTrace], diagnostic: CommanderBridgeDiagnostic) -> SentinelCertificationDecision:
        trace_items = tuple(traces)
        failures: list[SentinelFailure] = []
        if not diagnostic.evidence_generated or any(not item.audit_identifier for item in trace_items):
            failures.append(SentinelFailure.MISSING_BRIDGE_EVIDENCE)
        if diagnostic.authority_failures:
            failures.append(SentinelFailure.AUTHORITY_UNVERIFIED)
        if diagnostic.token_continuity_failures:
            failures.append(SentinelFailure.TOKEN_DISCONTINUITY)
        if not diagnostic.replay_consistent:
            failures.append(SentinelFailure.REPLAY_DIVERGENCE)
        unique = tuple(dict.fromkeys(failures))
        return SentinelCertificationDecision(
            decision=SentinelDecision.PASS if not unique else SentinelDecision.FAIL_CLOSED,
            failures=unique,
            package_hash=_digest({"traces": tuple(asdict(item) for item in trace_items), "diagnostic": asdict(diagnostic)}),
            certified=not unique,
        )


@dataclass(frozen=True)
class SentinelTraceabilityRecord:
    requirement_id: str
    governing_doctrine: str
    implementation_component: str
    verification_procedure: str
    evidence_artifact: str
    certification_result: SentinelDecision


@dataclass(frozen=True)
class SentinelCertificationInput:
    verification_results: Mapping[str, bool]
    traceability: tuple[SentinelTraceabilityRecord, ...]
    immutable_package_hash: str
    independent_audit_result: SentinelDecision


@dataclass(frozen=True)
class SentinelCertificationDecision:
    decision: SentinelDecision
    failures: tuple[SentinelFailure, ...]
    package_hash: str
    certified: bool


class SentinelCertificationFramework:
    """SENT-MO-005 evidence-based Sentinel constitutional certification."""

    required_categories = (
        "observation",
        "source",
        "authority",
        "runtime",
        "constitutional_boundary",
        "synthetic_truth",
        "governance",
        "audit",
    )

    def certify(self, certification_input: SentinelCertificationInput) -> SentinelCertificationDecision:
        failures: list[SentinelFailure] = []
        for category in self.required_categories:
            if not certification_input.verification_results.get(category, False):
                failures.append(SentinelFailure.MISSING_CERTIFICATION_EVIDENCE)
        if not certification_input.traceability or any(not _trace_complete(item) for item in certification_input.traceability):
            failures.append(SentinelFailure.TRACEABILITY_GAP)
        if _blank(certification_input.immutable_package_hash):
            failures.append(SentinelFailure.MISSING_CERTIFICATION_EVIDENCE)
        if certification_input.independent_audit_result != SentinelDecision.PASS:
            failures.append(SentinelFailure.MISSING_CERTIFICATION_EVIDENCE)
        unique = tuple(dict.fromkeys(failures))
        return SentinelCertificationDecision(
            decision=SentinelDecision.PASS if not unique else SentinelDecision.FAIL_CLOSED,
            failures=unique,
            package_hash=certification_input.immutable_package_hash,
            certified=not unique,
        )


@dataclass(frozen=True)
class SentinelAuditPackage:
    repository_revision: str
    verification_summary: Mapping[str, bool]
    constitutional_requirements_tested: tuple[str, ...]
    runtime_evidence_hash: str
    observation_evidence_hash: str
    authority_evidence_hash: str
    bridge_evidence_hash: str
    trace_evidence_hash: str
    constitutional_deficiencies: tuple[str, ...]
    pass_fail_determination: SentinelDecision
    package_digest: str


class SentinelConstitutionalAuditPackageGenerator:
    """SENT-MO-003 immutable Sentinel constitutional audit package generator."""

    def generate(
        self,
        repository_revision: str,
        certification_input: SentinelCertificationInput,
        runtime_traces: Iterable[ObservationRuntimeTrace],
        observation_evidence: Iterable[ObservationEvidenceRecord],
        bridge_traces: Iterable[CommanderNotificationTrace],
    ) -> SentinelAuditPackage:
        framework_decision = SentinelCertificationFramework().certify(certification_input)
        deficiencies = tuple(failure.value for failure in framework_decision.failures)
        runtime_items = tuple(runtime_traces)
        evidence_items = tuple(observation_evidence)
        bridge_items = tuple(bridge_traces)
        missing = []
        if not runtime_items:
            missing.append(SentinelFailure.MISSING_RUNTIME_TRACE.value)
        if not evidence_items:
            missing.append(SentinelFailure.INCOMPLETE_EVIDENCE.value)
        if not bridge_items:
            missing.append(SentinelFailure.MISSING_BRIDGE_EVIDENCE.value)
        deficiencies = tuple(dict.fromkeys(deficiencies + tuple(missing)))
        decision = SentinelDecision.PASS if framework_decision.certified and not deficiencies else SentinelDecision.FAIL_CLOSED
        payload = {
            "repository_revision": repository_revision,
            "verification_summary": dict(certification_input.verification_results),
            "traceability": tuple(asdict(item) for item in certification_input.traceability),
            "runtime_traces": tuple(asdict(item) for item in runtime_items),
            "observation_evidence": tuple(asdict(item) for item in evidence_items),
            "bridge_traces": tuple(asdict(item) for item in bridge_items),
            "deficiencies": deficiencies,
            "decision": decision.value,
        }
        return SentinelAuditPackage(
            repository_revision=repository_revision,
            verification_summary=certification_input.verification_results,
            constitutional_requirements_tested=tuple(sorted(certification_input.verification_results)),
            runtime_evidence_hash=_digest(tuple(asdict(item) for item in runtime_items)),
            observation_evidence_hash=_digest(tuple(asdict(item) for item in evidence_items)),
            authority_evidence_hash=_digest(tuple(item.evidence_artifact for item in certification_input.traceability if "authority" in item.requirement_id.lower())),
            bridge_evidence_hash=_digest(tuple(asdict(item) for item in bridge_items)),
            trace_evidence_hash=_digest(tuple(item.evidence_artifact for item in certification_input.traceability)),
            constitutional_deficiencies=deficiencies,
            pass_fail_determination=decision,
            package_digest=_digest(payload),
        )


def observation_fingerprint(observation: ObservationRecord) -> str:
    payload = {
        "objective_id": observation.objective_id,
        "source_id": observation.source_id,
        "observation_timestamp": observation.observation_timestamp,
        "value_hash": observation.value_hash,
        "mission_assignment_id": observation.mission_assignment_id,
    }
    return _digest(payload)


def _runtime_trace(
    schedule_entry: ObservationScheduleEntry,
    observation: ObservationRecord,
    validation: ObservationValidationDecision,
    commander_notification_trace: str,
) -> ObservationRuntimeTrace:
    trace_payload = {
        "schedule": asdict(schedule_entry),
        "observation": observation.observation_id,
        "validation": validation.decision.value,
        "notification": commander_notification_trace,
    }
    digest = _digest(trace_payload)
    return ObservationRuntimeTrace(
        mission_id=observation.mission_assignment_id,
        observation_id=observation.observation_id,
        scheduler_trace=_digest(asdict(schedule_entry)),
        observation_execution_trace=_digest(asdict(observation)),
        evidence_generation_trace=_digest({"evidence": observation.evidence_references}),
        duplicate_evaluation_trace=_digest({"duplicate": SentinelFailure.DUPLICATE_OBSERVATION in validation.failures}),
        independence_evaluation_trace=_digest({"independent": SentinelFailure.SOURCE_NOT_INDEPENDENT not in validation.failures}),
        conflict_evaluation_trace=_digest({"conflict": SentinelFailure.CONFLICTING_OBSERVATION in validation.failures}),
        archival_trace=_digest({"archive": observation.observation_id}),
        commander_notification_trace=commander_notification_trace,
        trace_digest=digest,
    )


def _trace_complete(item: SentinelTraceabilityRecord) -> bool:
    return all(
        (
            item.requirement_id,
            item.governing_doctrine,
            item.implementation_component,
            item.verification_procedure,
            item.evidence_artifact,
            item.certification_result == SentinelDecision.PASS,
        )
    )


def _blank(value: str) -> bool:
    return str(value).strip().lower() in {"", "unknown", "placeholder", "synthetic", "none", "null"}


def _digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
