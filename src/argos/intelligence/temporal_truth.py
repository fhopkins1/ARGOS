"""MO-TR-004 timestamp, effective-time, and revision doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_004_VERSION = "MO-TR-004/1.0.0"


class TimestampPrecision(str, Enum):
    NANOSECOND = "NANOSECOND"
    MICROSECOND = "MICROSECOND"
    MILLISECOND = "MILLISECOND"
    SECOND = "SECOND"
    MINUTE = "MINUTE"
    HOUR = "HOUR"
    DAY = "DAY"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"
    RANGE = "RANGE"
    UNKNOWN = "UNKNOWN"


class ClockBasis(str, Enum):
    SOURCE_REPORTED = "SOURCE_REPORTED"
    EXCHANGE_REPORTED = "EXCHANGE_REPORTED"
    BROKER_REPORTED = "BROKER_REPORTED"
    REGULATOR_REPORTED = "REGULATOR_REPORTED"
    ISSUER_REPORTED = "ISSUER_REPORTED"
    GOVERNMENT_REPORTED = "GOVERNMENT_REPORTED"
    ARGOS_RETRIEVAL_CLOCK = "ARGOS_RETRIEVAL_CLOCK"
    ARGOS_PERSISTENCE_CLOCK = "ARGOS_PERSISTENCE_CLOCK"
    FILE_METADATA = "FILE_METADATA"
    TRANSPORT_METADATA = "TRANSPORT_METADATA"
    DERIVED = "DERIVED"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"


class TemporalNormalizationStatus(str, Enum):
    RAW = "RAW"
    PARSED = "PARSED"
    NORMALIZED = "NORMALIZED"
    PARTIALLY_NORMALIZED = "PARTIALLY_NORMALIZED"
    AMBIGUOUS_TIMEZONE = "AMBIGUOUS_TIMEZONE"
    AMBIGUOUS_DATE = "AMBIGUOUS_DATE"
    INVALID_FORMAT = "INVALID_FORMAT"
    CLOCK_CONFLICT = "CLOCK_CONFLICT"
    MISSING = "MISSING"
    UNRESOLVED = "UNRESOLVED"


class VersionStatus(str, Enum):
    ORIGINAL = "ORIGINAL"
    PRELIMINARY = "PRELIMINARY"
    ESTIMATE = "ESTIMATE"
    INITIAL = "INITIAL"
    FINAL = "FINAL"
    CORRECTED = "CORRECTED"
    REVISED = "REVISED"
    AMENDED = "AMENDED"
    RESTATED = "RESTATED"
    CANCELLED = "CANCELLED"
    VOIDED = "VOIDED"
    SUPERSEDED = "SUPERSEDED"
    RETRACTED = "RETRACTED"
    REINSTATED = "REINSTATED"
    REPLACEMENT = "REPLACEMENT"
    UNKNOWN_VERSION = "UNKNOWN_VERSION"


class RevisionRelationshipType(str, Enum):
    CORRECTS = "CORRECTS"
    REVISES = "REVISES"
    AMENDS = "AMENDS"
    RESTATES = "RESTATES"
    CANCELS = "CANCELS"
    VOIDS = "VOIDS"
    SUPERSEDES = "SUPERSEDES"
    RETRACTS = "RETRACTS"
    REPLACES = "REPLACES"
    REINSTATES = "REINSTATES"
    CLARIFIES = "CLARIFIES"
    RELATED_VERSION = "RELATED_VERSION"
    UNKNOWN_RELATIONSHIP = "UNKNOWN_RELATIONSHIP"


@dataclass(frozen=True)
class TimestampValue:
    value: str
    timezone: str
    precision: TimestampPrecision
    source: str
    source_field: str
    confidence_state: str
    is_estimated: bool
    is_approximate: bool
    lower_bound: str
    upper_bound: str
    clock_basis: ClockBasis
    normalization_status: TemporalNormalizationStatus
    original_text: str

    @property
    def usable_for_promotion(self) -> bool:
        return self.normalization_status is TemporalNormalizationStatus.NORMALIZED and self.value not in {"", "UNKNOWN"} and self.timezone not in {"", "UNKNOWN"}


@dataclass(frozen=True)
class TemporalEnvelope:
    event_time: TimestampValue
    market_time: TimestampValue
    publication_time: TimestampValue
    filing_time: TimestampValue
    retrieval_time: TimestampValue
    effective_time: TimestampValue
    correction_time: TimestampValue
    revision_time: TimestampValue
    settlement_time: TimestampValue
    execution_time: TimestampValue
    system_recorded_time: TimestampValue


@dataclass(frozen=True)
class TemporalObservation:
    observation_id: str
    fact_identity: str
    entity_id: str
    instrument_id: str
    account_id: str
    fact_domain: str
    value: str
    temporal_envelope: TemporalEnvelope
    version_status: VersionStatus
    source_id: str
    evidence_reference: str
    recorded_at: str
    observation_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "observation_digest", _stable_digest(self))


@dataclass(frozen=True)
class RevisionRelationship:
    relationship_id: str
    earlier_observation_id: str
    later_observation_id: str
    relationship_type: RevisionRelationshipType
    source_declared_relationship: str
    relationship_basis: str
    effective_time: TimestampValue
    publication_or_revision_time: TimestampValue
    recorded_time: TimestampValue
    rule_version: str
    created_by_office: str
    evidence_references: tuple[str, ...]
    validation_state: str


@dataclass(frozen=True)
class TemporalResolutionResult:
    selector_id: str
    operation: str
    fact_identity: str
    selected_observation_id: str
    excluded_observation_ids: tuple[str, ...]
    cutoff: str
    reason: str
    result_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "result_digest", _stable_digest(self))


class TemporalTruthArchive:
    """Append-only observation and revision archive."""

    def __init__(self) -> None:
        self._observations: dict[str, TemporalObservation] = {}
        self._relationships: list[RevisionRelationship] = []

    def append_observation(self, observation: TemporalObservation) -> None:
        if observation.observation_id in self._observations:
            raise ValueError("temporal observations are append-only")
        self._observations[observation.observation_id] = observation

    def append_revision_relationship(self, relationship: RevisionRelationship) -> None:
        self._relationships.append(relationship)

    def resolve_current_fact(self, fact_identity: str, evaluation_cutoff: str) -> TemporalResolutionResult:
        candidates = [obs for obs in self._observations.values() if obs.fact_identity == fact_identity and obs.recorded_at <= evaluation_cutoff]
        selected = _select_best_current(candidates, self._relationships, evaluation_cutoff)
        excluded = tuple(obs.observation_id for obs in candidates if selected is None or obs.observation_id != selected.observation_id)
        return TemporalResolutionResult(_stable_id("TSEL", "current", fact_identity, evaluation_cutoff), "resolve_current_fact", fact_identity, selected.observation_id if selected else "", excluded, evaluation_cutoff, "latest valid supersession chain applied")

    def resolve_fact_as_known_at(self, fact_identity: str, knowledge_cutoff: str) -> TemporalResolutionResult:
        candidates = [obs for obs in self._observations.values() if obs.fact_identity == fact_identity and obs.recorded_at <= knowledge_cutoff and obs.temporal_envelope.publication_time.value <= knowledge_cutoff and obs.temporal_envelope.retrieval_time.value <= knowledge_cutoff]
        selected = _select_best_current(candidates, [rel for rel in self._relationships if rel.recorded_time.value <= knowledge_cutoff], knowledge_cutoff)
        excluded = tuple(obs.observation_id for obs in self._observations.values() if obs.fact_identity == fact_identity and (selected is None or obs.observation_id != selected.observation_id))
        return TemporalResolutionResult(_stable_id("TSEL", "known", fact_identity, knowledge_cutoff), "resolve_fact_as_known_at", fact_identity, selected.observation_id if selected else "", excluded, knowledge_cutoff, "post-cutoff publications and retrievals excluded")

    def resolve_effective_state(self, fact_identity: str, effective_cutoff: str, knowledge_cutoff: str) -> TemporalResolutionResult:
        candidates = [obs for obs in self._observations.values() if obs.fact_identity == fact_identity and obs.temporal_envelope.effective_time.value <= effective_cutoff and obs.recorded_at <= knowledge_cutoff]
        selected = _select_best_current(candidates, [rel for rel in self._relationships if rel.recorded_time.value <= knowledge_cutoff], knowledge_cutoff)
        excluded = tuple(obs.observation_id for obs in self._observations.values() if obs.fact_identity == fact_identity and (selected is None or obs.observation_id != selected.observation_id))
        return TemporalResolutionResult(_stable_id("TSEL", "effective", fact_identity, effective_cutoff, knowledge_cutoff), "resolve_effective_state", fact_identity, selected.observation_id if selected else "", excluded, f"{effective_cutoff}|{knowledge_cutoff}", "effective-time and knowledge cutoffs both applied")


def timestamp(value: str = "UNKNOWN", *, timezone: str = "UTC", precision: TimestampPrecision = TimestampPrecision.SECOND, source: str = "ARGOS", source_field: str = "", clock_basis: ClockBasis = ClockBasis.SOURCE_REPORTED, status: TemporalNormalizationStatus = TemporalNormalizationStatus.NORMALIZED, original_text: str = "") -> TimestampValue:
    if value == "UNKNOWN":
        return TimestampValue("UNKNOWN", "UNKNOWN", TimestampPrecision.UNKNOWN, source, source_field, "UNKNOWN", False, False, "", "", ClockBasis.UNKNOWN, TemporalNormalizationStatus.MISSING, original_text)
    if not timezone or timezone == "UNKNOWN":
        return TimestampValue(value, "UNKNOWN", precision, source, source_field, "LOW", False, False, "", "", clock_basis, TemporalNormalizationStatus.AMBIGUOUS_TIMEZONE, original_text or value)
    return TimestampValue(value, timezone, precision, source, source_field, "HIGH", False, False, "", "", clock_basis, status, original_text or value)


def empty_temporal_envelope() -> TemporalEnvelope:
    missing = timestamp()
    return TemporalEnvelope(missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing)


def make_temporal_envelope(**values: TimestampValue) -> TemporalEnvelope:
    base = empty_temporal_envelope()
    data = {field_info.name: getattr(base, field_info.name) for field_info in fields(base)}
    data.update(values)
    return TemporalEnvelope(**data)


def make_revision_relationship(earlier: TemporalObservation, later: TemporalObservation, relationship_type: RevisionRelationshipType, evidence_references: tuple[str, ...]) -> RevisionRelationship:
    return RevisionRelationship(_stable_id("TREL", earlier.observation_id, later.observation_id, relationship_type.value), earlier.observation_id, later.observation_id, relationship_type, relationship_type.value, "source_declared_or_policy_validated", later.temporal_envelope.effective_time, later.temporal_envelope.revision_time if later.temporal_envelope.revision_time.value != "UNKNOWN" else later.temporal_envelope.publication_time, timestamp(utc_timestamp(), clock_basis=ClockBasis.ARGOS_PERSISTENCE_CLOCK, source_field="system_recorded_time"), MO_TR_004_VERSION, "Intelligence", evidence_references, "VALIDATED")


def validate_temporal_envelope(envelope: TemporalEnvelope, required: tuple[str, ...]) -> tuple[str, ...]:
    failures = []
    for name in required:
        value = getattr(envelope, name)
        if not value.usable_for_promotion:
            failures.append(name)
    return tuple(failures)


def _select_best_current(candidates: list[TemporalObservation], relationships: list[RevisionRelationship], cutoff: str) -> TemporalObservation | None:
    if not candidates:
        return None
    by_id = {obs.observation_id: obs for obs in candidates}
    superseded = {rel.earlier_observation_id for rel in relationships if rel.later_observation_id in by_id and rel.relationship_type in {RevisionRelationshipType.CORRECTS, RevisionRelationshipType.REVISES, RevisionRelationshipType.AMENDS, RevisionRelationshipType.RESTATES, RevisionRelationshipType.SUPERSEDES, RevisionRelationshipType.REPLACES}}
    remaining = [obs for obs in candidates if obs.observation_id not in superseded and obs.version_status not in {VersionStatus.CANCELLED, VersionStatus.VOIDED, VersionStatus.RETRACTED, VersionStatus.SUPERSEDED}]
    if not remaining:
        return None
    priority = {
        VersionStatus.CORRECTED: 1,
        VersionStatus.REVISED: 2,
        VersionStatus.AMENDED: 3,
        VersionStatus.RESTATED: 4,
        VersionStatus.FINAL: 5,
        VersionStatus.ORIGINAL: 6,
        VersionStatus.INITIAL: 7,
        VersionStatus.PRELIMINARY: 8,
        VersionStatus.ESTIMATE: 9,
        VersionStatus.UNKNOWN_VERSION: 99,
    }
    return sorted(remaining, key=lambda obs: (priority.get(obs.version_status, 50), obs.temporal_envelope.effective_time.value, obs.recorded_at, obs.observation_id))[0]


def _stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{_stable_digest(parts)[:24].upper()}"


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return dict(value)
    if is_dataclass(value):
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name not in {"observation_digest", "result_digest"}}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
