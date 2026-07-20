"""MO-SP-010 Historian search retention and reconstruction doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp
from argos.intelligence.search_operations import SearchEvidenceRecord


MO_SP_010_VERSION = "MO-SP-010/1.0.0"


class TemporalEvidenceClassification(str, Enum):
    KNOWN_AT_DECISION_TIME = "KNOWN_AT_DECISION_TIME"
    AVAILABLE_NOT_COLLECTED = "AVAILABLE_NOT_COLLECTED"
    PUBLISHED_AFTER_DECISION = "PUBLISHED_AFTER_DECISION"
    LATER_CORRECTION = "LATER_CORRECTION"
    LATER_REVISION = "LATER_REVISION"
    RETROSPECTIVE_INTERPRETATION = "RETROSPECTIVE_INTERPRETATION"


class SkippedSearchReason(str, Enum):
    NOT_APPLICABLE_BY_PLAN = "NOT_APPLICABLE_BY_PLAN"
    AUTHORITY_DENIED = "AUTHORITY_DENIED"
    BUDGET_BLOCKED = "BUDGET_BLOCKED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    WORKFLOW_CANCELLED = "WORKFLOW_CANCELLED"
    PREREQUISITE_FAILED = "PREREQUISITE_FAILED"
    SUPERSEDED_BY_NEW_PLAN_VERSION = "SUPERSEDED_BY_NEW_PLAN_VERSION"


@dataclass(frozen=True)
class HistoricalSearchRecord:
    search_record_id: str
    search_plan_id: str
    search_plan_version: str
    workflow_id: str
    workflow_execution_token_id: str
    requesting_office: str
    executing_office: str
    requesting_authority: str
    authorized_purpose: str
    decision_object_id: str
    position_identifier: str
    order_identifier: str
    investigation_identifier: str
    source_identifier: str
    source_registry_version: str
    source_authority_classification: str
    retrieval_surface_identifier: str
    retrieval_method: str
    canonical_query_text: str
    structured_request_parameters: Mapping[str, str]
    filters: Mapping[str, str]
    entity_identifiers: Mapping[str, str]
    security_identifiers: tuple[str, ...]
    date_range_requested: tuple[str, str]
    source_sequence_position: int
    search_depth_authorized: int
    search_depth_reached: int
    request_timestamp: str
    source_publication_timestamp: str
    source_effective_timestamp: str
    source_revision_timestamp: str
    retrieval_completion_timestamp: str
    ingestion_timestamp: str
    original_response_status: str
    normalized_outcome_status: str
    raw_evidence_reference: str
    raw_response_digest: str
    extracted_fact_references: tuple[str, ...]
    cache_status: str
    cache_key: str
    cache_creation_timestamp: str
    cache_age_seconds: int
    retry_count: int
    retry_history_reference: str
    fallback_status: str
    fallback_source_identifier: str
    zero_result_status: bool
    failure_classification: str
    failure_details: str
    stop_rule_identifier: str
    stop_rule_outcome: str
    escalation_outcome: str
    monetary_cost: int
    retention_class: str
    legal_hold_status: str
    integrity_status: str
    created_at: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


@dataclass(frozen=True)
class EvidenceUseRecord:
    use_record_id: str
    consuming_office: str
    consuming_artifact: str
    evidence_reference: str
    disposition: str
    disposition_reason: str
    evaluation_timestamp: str
    information_cutoff: str


@dataclass(frozen=True)
class HistoricalInformationCutoff:
    cutoff_id: str
    workflow_id: str
    decision_object_id: str
    cutoff_timestamp: str
    cutoff_rationale: str
    establishing_office: str
    workflow_execution_token_id: str
    included_search_record_ids: tuple[str, ...]
    included_evidence_ids: tuple[str, ...]
    unresolved_conflicts: tuple[str, ...]
    failed_mandatory_searches: tuple[str, ...]
    skipped_mandatory_searches: tuple[str, ...]
    source_outages: tuple[str, ...]
    stale_evidence: tuple[str, ...]
    cutoff_certification_status: str
    cutoff_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "cutoff_digest", _stable_digest(self))


@dataclass(frozen=True)
class EvidenceTemporalRelationship:
    relationship_id: str
    evidence_reference: str
    classification: TemporalEvidenceClassification
    cutoff_id: str
    support_reason: str
    publication_timestamp: str
    retrieval_timestamp: str


@dataclass(frozen=True)
class CorrectionRevisionLink:
    link_id: str
    original_artifact_identifier: str
    later_artifact_identifier: str
    relationship_type: TemporalEvidenceClassification
    issuing_authority: str
    correction_publication_timestamp: str
    correction_retrieval_timestamp: str
    affected_fields: tuple[str, ...]
    original_values: Mapping[str, Any]
    corrected_or_revised_values: Mapping[str, Any]
    materiality_classification: str
    discovery_method: str


@dataclass(frozen=True)
class RetrospectiveSearchAuthorization:
    authorization_id: str
    authorizing_office_or_human_authority: str
    authorized_purpose: str
    target_workflow_or_decision: str
    allowed_source_classes: tuple[str, ...]
    allowed_date_range: tuple[str, str]
    maximum_search_depth: int
    maximum_cost: int
    created_at: str


@dataclass(frozen=True)
class HistoricalReconstruction:
    reconstruction_id: str
    workflow_id: str
    decision_object_id: str
    cutoff_id: str
    known_at_decision_time: tuple[str, ...]
    available_not_collected: tuple[str, ...]
    published_after_decision: tuple[str, ...]
    later_corrections: tuple[str, ...]
    later_revisions: tuple[str, ...]
    retrospective_interpretations: tuple[str, ...]
    failed_searches: tuple[str, ...]
    skipped_searches: tuple[str, ...]
    conflicts_known_at_cutoff: tuple[str, ...]
    reconstructed_at: str
    reconstruction_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "reconstruction_digest", _stable_digest(self))


class HistorianSearchArchive:
    """Append-only in-memory archive for decision-time reconstruction."""

    def __init__(self) -> None:
        self._searches: dict[str, HistoricalSearchRecord] = {}
        self._temporal: list[EvidenceTemporalRelationship] = []
        self._cutoffs: dict[str, HistoricalInformationCutoff] = {}
        self._corrections: list[CorrectionRevisionLink] = []

    def append_search_record(self, record: HistoricalSearchRecord) -> None:
        if record.search_record_id in self._searches:
            raise ValueError("historical search records are append-only by identifier")
        self._searches[record.search_record_id] = record

    def append_temporal_relationship(self, relationship: EvidenceTemporalRelationship) -> None:
        self._temporal.append(relationship)

    def freeze_cutoff(self, cutoff: HistoricalInformationCutoff) -> None:
        if cutoff.cutoff_id in self._cutoffs:
            raise ValueError("information cutoffs are immutable")
        self._cutoffs[cutoff.cutoff_id] = cutoff

    def append_correction(self, link: CorrectionRevisionLink) -> None:
        self._corrections.append(link)

    def reconstruct(self, cutoff_id: str) -> HistoricalReconstruction:
        cutoff = self._cutoffs[cutoff_id]
        buckets = {classification: [] for classification in TemporalEvidenceClassification}
        for relationship in self._temporal:
            if relationship.cutoff_id == cutoff_id:
                buckets[relationship.classification].append(relationship.evidence_reference)
        return HistoricalReconstruction(
            _stable_id("HREC", cutoff.workflow_id, cutoff.decision_object_id, cutoff.cutoff_digest),
            cutoff.workflow_id,
            cutoff.decision_object_id,
            cutoff.cutoff_id,
            tuple(buckets[TemporalEvidenceClassification.KNOWN_AT_DECISION_TIME]),
            tuple(buckets[TemporalEvidenceClassification.AVAILABLE_NOT_COLLECTED]),
            tuple(buckets[TemporalEvidenceClassification.PUBLISHED_AFTER_DECISION]),
            tuple(buckets[TemporalEvidenceClassification.LATER_CORRECTION]),
            tuple(buckets[TemporalEvidenceClassification.LATER_REVISION]),
            tuple(buckets[TemporalEvidenceClassification.RETROSPECTIVE_INTERPRETATION]),
            cutoff.failed_mandatory_searches,
            cutoff.skipped_mandatory_searches,
            cutoff.unresolved_conflicts,
            utc_timestamp(),
        )


def historical_record_from_search_evidence(record: SearchEvidenceRecord) -> HistoricalSearchRecord:
    return HistoricalSearchRecord(
        _stable_id("HSR", record.search_evidence_id),
        record.search_plan_id,
        record.search_plan_version,
        record.workflow_id,
        record.workflow_execution_token_id,
        record.requesting_office,
        record.executing_office,
        record.authorizing_artifact_identifier,
        record.authorized_purpose,
        record.decision_object_id,
        "",
        "",
        record.investigation_id,
        record.canonical_source_identifier,
        record.source_registry_version,
        record.source_classification,
        record.retrieval_surface_identifier,
        record.retrieval_method,
        record.exact_query_text,
        record.structured_parameters,
        MappingProxyType({}),
        record.entity_identifiers,
        tuple(record.entity_identifiers.values()),
        record.requested_time_range,
        1,
        record.authorized_search_depth_limit,
        record.attempt_number,
        record.created_at,
        record.source_publication_timestamp,
        "",
        "",
        record.retrieval_completion_timestamp,
        record.finalized_at,
        record.source_response_status,
        record.stop_rule_outcome,
        record.raw_evidence_reference,
        record.response_digest,
        (record.normalized_evidence_reference,),
        record.cache_status.value,
        record.cache_key,
        "",
        record.cache_age_seconds,
        record.total_attempt_count - 1,
        record.retry_policy_identifier,
        "USED" if record.fallback_source_identifier else "NOT_USED",
        record.fallback_source_identifier,
        record.zero_result_status,
        record.failure_classification.value if record.failure_classification else "",
        record.authorization_rejection_code,
        record.stop_rule_identifier,
        record.stop_rule_outcome,
        record.escalation_outcome,
        record.monetary_cost_units,
        record.retention_class,
        record.legal_hold_status,
        record.integrity_status,
        utc_timestamp(),
    )


def classify_temporal_evidence(evidence_reference: str, cutoff: HistoricalInformationCutoff, publication_timestamp: str, retrieval_timestamp: str, *, correction: bool = False, revision: bool = False, interpretation: bool = False, available_not_collected: bool = False) -> EvidenceTemporalRelationship:
    if correction:
        classification = TemporalEvidenceClassification.LATER_CORRECTION
    elif revision:
        classification = TemporalEvidenceClassification.LATER_REVISION
    elif interpretation:
        classification = TemporalEvidenceClassification.RETROSPECTIVE_INTERPRETATION
    elif available_not_collected:
        classification = TemporalEvidenceClassification.AVAILABLE_NOT_COLLECTED
    elif publication_timestamp > cutoff.cutoff_timestamp:
        classification = TemporalEvidenceClassification.PUBLISHED_AFTER_DECISION
    else:
        classification = TemporalEvidenceClassification.KNOWN_AT_DECISION_TIME if evidence_reference in cutoff.included_evidence_ids else TemporalEvidenceClassification.AVAILABLE_NOT_COLLECTED
    return EvidenceTemporalRelationship(_stable_id("HTR", evidence_reference, cutoff.cutoff_id, classification.value), evidence_reference, classification, cutoff.cutoff_id, "MO-SP-010 temporal classification", publication_timestamp, retrieval_timestamp)


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
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name not in {"record_digest", "cutoff_digest", "reconstruction_digest"}}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
