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


def observation_fingerprint(observation: ObservationRecord) -> str:
    payload = {
        "objective_id": observation.objective_id,
        "source_id": observation.source_id,
        "observation_timestamp": observation.observation_timestamp,
        "value_hash": observation.value_hash,
        "mission_assignment_id": observation.mission_assignment_id,
    }
    return _digest(payload)


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
