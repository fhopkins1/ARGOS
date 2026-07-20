"""MO-TR-003 conflict classification doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp
from argos.intelligence.observation_relationships import ObservationRecord, ObservationRelationshipClassification, ObservationRelationshipEvaluation


MO_TR_003_VERSION = "MO-TR-003/1.0.0"


class ConflictClass(str, Enum):
    NO_CONFLICT = "NO_CONFLICT"
    FORMAT_DIFFERENCE = "FORMAT_DIFFERENCE"
    ROUNDING_DIFFERENCE = "ROUNDING_DIFFERENCE"
    TIMING_DIFFERENCE = "TIMING_DIFFERENCE"
    MARKET_VENUE_DIFFERENCE = "MARKET_VENUE_DIFFERENCE"
    PRELIMINARY_VERSUS_FINAL = "PRELIMINARY_VERSUS_FINAL"
    REVISED_VALUE = "REVISED_VALUE"
    SOURCE_LAG = "SOURCE_LAG"
    STALE_SOURCE = "STALE_SOURCE"
    PARTIAL_DATA = "PARTIAL_DATA"
    MISSING_DATA = "MISSING_DATA"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    UNIT_CONFLICT = "UNIT_CONFLICT"
    DEFINITION_CONFLICT = "DEFINITION_CONFLICT"
    INTERPRETATION_CONFLICT = "INTERPRETATION_CONFLICT"
    AUTHORITY_CONFLICT = "AUTHORITY_CONFLICT"
    MATERIAL_NUMERICAL_CONFLICT = "MATERIAL_NUMERICAL_CONFLICT"
    MATERIAL_EVENT_CONFLICT = "MATERIAL_EVENT_CONFLICT"
    POSSIBLE_CORRUPTION = "POSSIBLE_CORRUPTION"
    POSSIBLE_MANIPULATION = "POSSIBLE_MANIPULATION"
    UNRESOLVED_CONFLICT = "UNRESOLVED_CONFLICT"
    UNKNOWN = "UNKNOWN"


class ConflictResolutionState(str, Enum):
    OPEN = "OPEN"
    ROUTED = "ROUTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    BLOCKED = "BLOCKED"
    ESCALATED = "ESCALATED"
    UNKNOWN = "UNKNOWN"


class ConflictEventType(str, Enum):
    ConflictCreated = "ConflictCreated"
    ConflictClassified = "ConflictClassified"
    ConflictEscalated = "ConflictEscalated"
    ConflictResolved = "ConflictResolved"
    ConflictReplayed = "ConflictReplayed"
    ConflictAudited = "ConflictAudited"
    ConflictBlocked = "ConflictBlocked"


@dataclass(frozen=True)
class ConflictClassificationInput:
    observation_a: ObservationRecord | None
    observation_b: ObservationRecord | None
    fact_domain: str
    identity_record: ObservationRelationshipEvaluation | None
    normalization_record: str
    authority_record: str
    timestamp_record: str
    workflow_id: str
    decision_object_id: str
    office_identifier: str
    doctrine_version: str = MO_TR_003_VERSION


@dataclass(frozen=True)
class ConflictRecord:
    conflict_id: str
    workflow_id: str
    decision_object_id: str
    observation_ids: tuple[str, ...]
    observation_hashes: tuple[str, ...]
    fact_domain: str
    conflict_class: ConflictClass
    rule_id: str
    doctrine_version: str
    authority_domains: tuple[str, ...]
    source_ids: tuple[str, ...]
    source_independence: str
    observation_time: tuple[str, ...]
    publication_time: tuple[str, ...]
    effective_time: tuple[str, ...]
    retrieval_time: tuple[str, ...]
    normalization_version: str
    materiality: str
    required_action: str
    resolution_state: ConflictResolutionState
    office_responsible: str
    creation_timestamp: str
    replay_reference: str
    audit_reference: str
    metadata: Mapping[str, str]
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


@dataclass(frozen=True)
class ConflictClassificationResult:
    conflict_identifier: str
    conflict_class: ConflictClass
    conflict_metadata: Mapping[str, str]
    affected_domain: str
    affected_offices: tuple[str, ...]
    materiality: str
    required_next_action: str
    resolution_state: ConflictResolutionState
    replay_identifier: str
    audit_identifier: str


class ConflictRecordRepository:
    def __init__(self) -> None:
        self._records: dict[str, ConflictRecord] = {}

    def append(self, record: ConflictRecord) -> None:
        if record.conflict_id in self._records:
            raise ValueError("conflict records are immutable")
        self._records[record.conflict_id] = record

    def get(self, conflict_id: str) -> ConflictRecord:
        return self._records[conflict_id]


class ConflictClassificationEngine:
    """The sole service for MO-TR-003 conflict classification."""

    def __init__(self, repository: ConflictRecordRepository | None = None) -> None:
        self.repository = repository or ConflictRecordRepository()

    def classify(self, request: ConflictClassificationInput) -> ConflictClassificationResult:
        conflict_class, rule_id = _classify(request)
        record = _record(request, conflict_class, rule_id)
        self.repository.append(record)
        return ConflictClassificationResult(record.conflict_id, record.conflict_class, record.metadata, record.fact_domain, ("Seeker", "Analyst", "Risk", "Trader", "Historian"), record.materiality, record.required_action, record.resolution_state, record.replay_reference, record.audit_reference)

    def replay(self, record: ConflictRecord, left: ObservationRecord | None, right: ObservationRecord | None, identity: ObservationRelationshipEvaluation | None) -> ConflictClass:
        return _classify(ConflictClassificationInput(left, right, record.fact_domain, identity, record.normalization_version, ",".join(record.authority_domains), ",".join(record.effective_time), record.workflow_id, record.decision_object_id, record.office_responsible, record.doctrine_version))[0]


def _classify(request: ConflictClassificationInput) -> tuple[ConflictClass, str]:
    left = request.observation_a
    right = request.observation_b
    if left is None or right is None or not request.fact_domain or request.identity_record is None or not request.workflow_id or not request.decision_object_id:
        return ConflictClass.UNKNOWN, "INPUT_INCOMPLETE"
    rel = request.identity_record.classification
    if rel in {ObservationRelationshipClassification.WRONG_ENTITY, ObservationRelationshipClassification.WRONG_INSTRUMENT}:
        return ConflictClass.IDENTITY_CONFLICT, "IDENTITY"
    if rel is ObservationRelationshipClassification.WRONG_TIME_WINDOW:
        return ConflictClass.TIMING_DIFFERENCE, "COMPARABILITY_TIME"
    if rel is ObservationRelationshipClassification.WRONG_UNIT:
        return ConflictClass.UNIT_CONFLICT, "UNITS"
    if left.value_type != right.value_type or left.reporting_basis != right.reporting_basis:
        return ConflictClass.DEFINITION_CONFLICT, "DEFINITIONS"
    if request.authority_record == "CONFLICTED_PRIMARY_AUTHORITY":
        return ConflictClass.AUTHORITY_CONFLICT, "AUTHORITY"
    if left.observation_timestamp != right.observation_timestamp or left.publication_timestamp != right.publication_timestamp:
        return ConflictClass.TIMING_DIFFERENCE, "TIMING"
    if left.version_state != right.version_state:
        return ConflictClass.PRELIMINARY_VERSUS_FINAL if {left.version_state, right.version_state} & {"PRELIMINARY", "FINAL"} else ConflictClass.REVISED_VALUE, "REVISION"
    if _numeric(left.normalized_value) is not None and _numeric(right.normalized_value) is not None:
        diff = abs(_numeric(left.normalized_value) - _numeric(right.normalized_value))
        if diff == 0:
            return ConflictClass.NO_CONFLICT, "NUMERICAL_EQUAL"
        if diff <= 0.01:
            return ConflictClass.ROUNDING_DIFFERENCE, "NUMERICAL_ROUNDING"
        return ConflictClass.MATERIAL_NUMERICAL_CONFLICT, "NUMERICAL_DIFFERENCE"
    if left.normalized_value == right.normalized_value:
        return ConflictClass.NO_CONFLICT, "VALUE_EQUAL"
    if left.value_type == "event":
        return ConflictClass.MATERIAL_EVENT_CONFLICT, "EVENT_DIFFERENCE"
    if left.lineage_status == "SUSPICIOUS" or right.lineage_status == "SUSPICIOUS":
        return ConflictClass.POSSIBLE_MANIPULATION, "INTEGRITY"
    return ConflictClass.UNRESOLVED_CONFLICT, "UNKNOWN"


def _record(request: ConflictClassificationInput, conflict_class: ConflictClass, rule_id: str) -> ConflictRecord:
    left = request.observation_a
    right = request.observation_b
    observations = tuple(obs for obs in (left, right) if obs is not None)
    material = "NONE" if conflict_class in {ConflictClass.NO_CONFLICT, ConflictClass.FORMAT_DIFFERENCE, ConflictClass.ROUNDING_DIFFERENCE} else "MATERIAL"
    state = ConflictResolutionState.RESOLVED if conflict_class in {ConflictClass.NO_CONFLICT, ConflictClass.FORMAT_DIFFERENCE, ConflictClass.ROUNDING_DIFFERENCE} else ConflictResolutionState.BLOCKED if conflict_class in {ConflictClass.AUTHORITY_CONFLICT, ConflictClass.MATERIAL_NUMERICAL_CONFLICT, ConflictClass.MATERIAL_EVENT_CONFLICT, ConflictClass.UNKNOWN} else ConflictResolutionState.ROUTED
    action = "NONE" if state is ConflictResolutionState.RESOLVED else "ROUTE_TO_RISK_AND_ANALYST" if state is ConflictResolutionState.BLOCKED else "ROUTE_TO_ANALYST"
    metadata = MappingProxyType({
        "primary_authority": request.authority_record,
        "secondary_authority": "UNKNOWN",
        "normalization_status": request.normalization_record,
        "comparison_result": conflict_class.value,
        "timestamp_comparison": request.timestamp_record,
        "affected_thesis": "UNKNOWN",
        "affected_trade": "BLOCKED" if state is ConflictResolutionState.BLOCKED else "NONE",
        "affected_workflow": request.workflow_id,
        "required_resolution_rule": rule_id,
        "procedural_consequence": action,
    })
    return ConflictRecord(_stable_id("CONF", request.workflow_id, tuple(obs.observation_id for obs in observations), conflict_class.value, rule_id), request.workflow_id, request.decision_object_id, tuple(obs.observation_id for obs in observations), tuple(obs.semantic_payload_hash for obs in observations), request.fact_domain, conflict_class, rule_id, request.doctrine_version, (request.authority_record,), tuple(obs.source_record_id for obs in observations), request.identity_record.independence_status if request.identity_record else "UNKNOWN", tuple(obs.observation_timestamp for obs in observations), tuple(obs.publication_timestamp for obs in observations), tuple(obs.effective_timestamp for obs in observations), tuple(obs.retrieval_timestamp for obs in observations), request.normalization_record, material, action, state, "ConflictClassificationEngine", utc_timestamp(), _stable_id("REPLAY-CONF", request.workflow_id, rule_id), _stable_id("AUD-CONF", request.workflow_id, rule_id), metadata)


def _numeric(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name != "record_digest"}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
