"""MO-TR-002 observation identity, comparability, and independence doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_002_VERSION = "MO-TR-002/1.0.0"


class ObservationRelationshipClassification(str, Enum):
    SAME_OBSERVATION = "SAME_OBSERVATION"
    SAME_ORIGIN = "SAME_ORIGIN"
    DERIVATIVE_COPY = "DERIVATIVE_COPY"
    PARTIALLY_INDEPENDENT = "PARTIALLY_INDEPENDENT"
    INDEPENDENT = "INDEPENDENT"
    NONCOMPARABLE = "NONCOMPARABLE"
    WRONG_ENTITY = "WRONG_ENTITY"
    WRONG_INSTRUMENT = "WRONG_INSTRUMENT"
    WRONG_TIME_WINDOW = "WRONG_TIME_WINDOW"
    WRONG_UNIT = "WRONG_UNIT"
    WRONG_VERSION = "WRONG_VERSION"
    UNKNOWN_RELATIONSHIP = "UNKNOWN_RELATIONSHIP"


class LineageRelationshipType(str, Enum):
    DIRECT_COPY = "DIRECT_COPY"
    REPUBLISHED_FROM = "REPUBLISHED_FROM"
    SYNDICATED_FROM = "SYNDICATED_FROM"
    SUMMARIZED_FROM = "SUMMARIZED_FROM"
    CITES = "CITES"
    CALCULATED_FROM = "CALCULATED_FROM"
    TRANSLATED_FROM = "TRANSLATED_FROM"
    DISPLAYED_FROM_VENDOR = "DISPLAYED_FROM_VENDOR"
    DISTRIBUTED_BY = "DISTRIBUTED_BY"
    HOSTED_MIRROR = "HOSTED_MIRROR"
    SAME_INSTITUTIONAL_RECORD = "SAME_INSTITUTIONAL_RECORD"
    COMMON_DATASET = "COMMON_DATASET"
    COMMON_WITNESS = "COMMON_WITNESS"
    COMMON_FILING = "COMMON_FILING"
    COMMON_BROKER_RECORD = "COMMON_BROKER_RECORD"
    UNKNOWN_LINEAGE = "UNKNOWN_LINEAGE"


@dataclass(frozen=True)
class ObservationRecord:
    observation_id: str
    workflow_id: str
    collection_event_id: str
    source_record_id: str
    source_institution_id: str
    source_publication_id: str
    source_channel_id: str
    source_url_or_locator: str
    source_document_id: str
    upstream_origin_id: str
    upstream_vendor_id: str
    raw_evidence_reference: str
    content_hash: str
    semantic_payload_hash: str
    retrieval_timestamp: str
    publication_timestamp: str
    observation_timestamp: str
    effective_timestamp: str
    revision_timestamp: str
    entity_identifiers: Mapping[str, str]
    instrument_identifiers: Mapping[str, str]
    account_identifiers: Mapping[str, str]
    event_identifiers: Mapping[str, str]
    document_identifiers: Mapping[str, str]
    fact_domain: str
    claim_scope: str
    value_type: str
    raw_value: str
    normalized_value: str
    unit: str
    currency: str
    scale: str
    adjustment_basis: str
    reporting_basis: str
    version_identifier: str
    version_state: str
    session_identifier: str
    market_venue: str
    reporting_period: str
    provenance_status: str
    lineage_status: str
    created_at: str
    created_by_office: str
    record_version: str


@dataclass(frozen=True)
class SourceLineageEdge:
    lineage_edge_id: str
    upstream_node_id: str
    downstream_node_id: str
    relationship_type: LineageRelationshipType
    claim_scope: str
    evidence_reference: str
    confidence_method: str
    proof_status: str
    observed_at: str
    recorded_at: str
    rule_version: str


@dataclass(frozen=True)
class ObservationRelationshipEvaluation:
    relationship_evaluation_id: str
    workflow_id: str
    left_observation_id: str
    right_observation_id: str
    claim_identifier: str
    requested_relationship_purpose: str
    classification: ObservationRelationshipClassification
    comparability_status: str
    independence_status: str
    entity_match_status: str
    instrument_match_status: str
    account_match_status: str
    event_match_status: str
    document_match_status: str
    time_alignment_status: str
    unit_alignment_status: str
    currency_alignment_status: str
    adjustment_alignment_status: str
    reporting_basis_alignment_status: str
    version_alignment_status: str
    origin_relationship_status: str
    common_origin_ids: tuple[str, ...]
    upstream_parent_observation_ids: tuple[str, ...]
    lineage_path_evidence: tuple[str, ...]
    normalization_actions: tuple[str, ...]
    rules_evaluated: tuple[str, ...]
    failed_rules: tuple[str, ...]
    unresolved_requirements: tuple[str, ...]
    supporting_evidence_references: tuple[str, ...]
    contrary_evidence_references: tuple[str, ...]
    evaluation_timestamp: str
    doctrine_rule_version: str
    evaluating_office: str
    evaluating_component: str
    resolution_state: str
    supersedes_evaluation_id: str
    human_review_status: str
    audit_record_id: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


@dataclass(frozen=True)
class ObservationGroup:
    observation_group_id: str
    workflow_id: str
    claim_identifier: str
    fact_domain: str
    candidate_entity_id: str
    candidate_instrument_id: str
    candidate_event_id: str
    candidate_time_window: str
    member_observation_ids: tuple[str, ...]
    relationship_evaluation_ids: tuple[str, ...]
    distinct_origin_count: int
    confirmed_independent_count: int
    partially_independent_count: int
    same_origin_count: int
    derivative_copy_count: int
    unknown_relationship_count: int
    noncomparable_count: int
    group_disposition: str
    created_at: str
    updated_at: str
    rule_version: str


class ObservationRelationshipEngine:
    """Evaluates identity, comparability, and independence before corroboration."""

    def evaluate(
        self,
        left: ObservationRecord,
        right: ObservationRecord,
        *,
        claim_identifier: str,
        requested_relationship_purpose: str = "corroboration_check",
        lineage_edges: tuple[SourceLineageEdge, ...] = (),
        evaluating_office: str = "Intelligence",
    ) -> ObservationRelationshipEvaluation:
        classification, failed, unresolved = _classify(left, right, lineage_edges)
        common = tuple(sorted({left.upstream_origin_id} & {right.upstream_origin_id} - {""}))
        parent_ids = tuple(edge.upstream_node_id for edge in lineage_edges if edge.downstream_node_id in {left.observation_id, right.observation_id})
        comparable = "COMPARABLE" if classification in {ObservationRelationshipClassification.SAME_OBSERVATION, ObservationRelationshipClassification.SAME_ORIGIN, ObservationRelationshipClassification.DERIVATIVE_COPY, ObservationRelationshipClassification.PARTIALLY_INDEPENDENT, ObservationRelationshipClassification.INDEPENDENT} else "NOT_COMPARABLE"
        independence = "INDEPENDENT" if classification is ObservationRelationshipClassification.INDEPENDENT else "NOT_INDEPENDENT" if classification in {ObservationRelationshipClassification.SAME_OBSERVATION, ObservationRelationshipClassification.SAME_ORIGIN, ObservationRelationshipClassification.DERIVATIVE_COPY} else "UNKNOWN_OR_PARTIAL"
        return ObservationRelationshipEvaluation(
            _stable_id("OREL", left.observation_id, right.observation_id, classification.value),
            left.workflow_id,
            left.observation_id,
            right.observation_id,
            claim_identifier,
            requested_relationship_purpose,
            classification,
            comparable,
            independence,
            "MATCH" if left.entity_identifiers == right.entity_identifiers else "MISMATCH",
            "MATCH" if left.instrument_identifiers == right.instrument_identifiers else "MISMATCH",
            "MATCH" if left.account_identifiers == right.account_identifiers else "MISMATCH",
            "MATCH" if left.event_identifiers == right.event_identifiers else "MISMATCH",
            "MATCH" if left.document_identifiers == right.document_identifiers else "MISMATCH",
            "MATCH" if _time_key(left) == _time_key(right) else "MISMATCH",
            "MATCH" if left.unit == right.unit else "MISMATCH",
            "MATCH" if left.currency == right.currency else "MISMATCH",
            "MATCH" if left.adjustment_basis == right.adjustment_basis else "MISMATCH",
            "MATCH" if left.reporting_basis == right.reporting_basis else "MISMATCH",
            "MATCH" if left.version_identifier == right.version_identifier and left.version_state == right.version_state else "MISMATCH",
            classification.value,
            common,
            parent_ids,
            tuple(edge.lineage_edge_id for edge in lineage_edges),
            (),
            ("identity", "entity", "instrument", "time", "unit", "version", "lineage", "independence"),
            failed,
            unresolved,
            tuple(item for item in (left.raw_evidence_reference, right.raw_evidence_reference) if item),
            (),
            utc_timestamp(),
            MO_TR_002_VERSION,
            evaluating_office,
            "ObservationRelationshipEngine",
            "CURRENT",
            "",
            "NOT_REQUIRED" if classification is not ObservationRelationshipClassification.UNKNOWN_RELATIONSHIP else "REQUIRED",
            _stable_id("AUD-OREL", left.observation_id, right.observation_id, classification.value),
        )

    def build_group(self, workflow_id: str, claim_identifier: str, fact_domain: str, observations: tuple[ObservationRecord, ...], evaluations: tuple[ObservationRelationshipEvaluation, ...]) -> ObservationGroup:
        counts = {classification: 0 for classification in ObservationRelationshipClassification}
        for evaluation in evaluations:
            counts[evaluation.classification] += 1
        origins = {obs.upstream_origin_id or obs.source_record_id for obs in observations}
        disposition = "INDEPENDENT_SUPPORT_PRESENT" if counts[ObservationRelationshipClassification.INDEPENDENT] else "UNKNOWN_OR_DEPENDENT_SUPPORT"
        now = utc_timestamp()
        return ObservationGroup(_stable_id("OGRP", workflow_id, claim_identifier, tuple(obs.observation_id for obs in observations)), workflow_id, claim_identifier, fact_domain, _first_value(observations, "entity_identifiers"), _first_value(observations, "instrument_identifiers"), _first_value(observations, "event_identifiers"), _first_value(observations, "reporting_period"), tuple(obs.observation_id for obs in observations), tuple(ev.relationship_evaluation_id for ev in evaluations), len(origins), counts[ObservationRelationshipClassification.INDEPENDENT], counts[ObservationRelationshipClassification.PARTIALLY_INDEPENDENT], counts[ObservationRelationshipClassification.SAME_ORIGIN], counts[ObservationRelationshipClassification.DERIVATIVE_COPY], counts[ObservationRelationshipClassification.UNKNOWN_RELATIONSHIP], counts[ObservationRelationshipClassification.NONCOMPARABLE], disposition, now, now, MO_TR_002_VERSION)


def _classify(left: ObservationRecord, right: ObservationRecord, edges: tuple[SourceLineageEdge, ...]) -> tuple[ObservationRelationshipClassification, tuple[str, ...], tuple[str, ...]]:
    if (
        left.content_hash
        and left.content_hash == right.content_hash
        and left.source_record_id == right.source_record_id
        and _time_key(left) == _time_key(right)
        and left.normalized_value == right.normalized_value
        and left.unit == right.unit
        and left.currency == right.currency
        and left.version_identifier == right.version_identifier
        and left.entity_identifiers == right.entity_identifiers
        and left.instrument_identifiers == right.instrument_identifiers
        and left.account_identifiers == right.account_identifiers
        and left.event_identifiers == right.event_identifiers
    ):
        return ObservationRelationshipClassification.SAME_OBSERVATION, (), ()
    if left.entity_identifiers != right.entity_identifiers:
        return ObservationRelationshipClassification.WRONG_ENTITY, ("entity_match",), ()
    if left.instrument_identifiers != right.instrument_identifiers:
        return ObservationRelationshipClassification.WRONG_INSTRUMENT, ("instrument_match",), ()
    if _time_key(left) != _time_key(right):
        return ObservationRelationshipClassification.WRONG_TIME_WINDOW, ("time_alignment",), ()
    if left.unit != right.unit or left.currency != right.currency or left.scale != right.scale:
        return ObservationRelationshipClassification.WRONG_UNIT, ("unit_alignment",), ()
    if left.version_identifier != right.version_identifier or left.version_state != right.version_state or left.adjustment_basis != right.adjustment_basis:
        return ObservationRelationshipClassification.WRONG_VERSION, ("version_alignment",), ()
    if left.claim_scope != right.claim_scope or left.value_type != right.value_type:
        return ObservationRelationshipClassification.NONCOMPARABLE, ("claim_scope",), ()
    if left.upstream_origin_id and left.upstream_origin_id == right.upstream_origin_id:
        return ObservationRelationshipClassification.SAME_ORIGIN, (), ()
    edge_types = {edge.relationship_type for edge in edges}
    if edge_types & {LineageRelationshipType.DIRECT_COPY, LineageRelationshipType.REPUBLISHED_FROM, LineageRelationshipType.SYNDICATED_FROM, LineageRelationshipType.SUMMARIZED_FROM, LineageRelationshipType.TRANSLATED_FROM, LineageRelationshipType.DISPLAYED_FROM_VENDOR, LineageRelationshipType.HOSTED_MIRROR}:
        return ObservationRelationshipClassification.DERIVATIVE_COPY, (), ()
    if edge_types & {LineageRelationshipType.CITES, LineageRelationshipType.CALCULATED_FROM} and left.upstream_origin_id != right.upstream_origin_id:
        return ObservationRelationshipClassification.PARTIALLY_INDEPENDENT, (), ()
    if left.lineage_status == "CERTIFIED" and right.lineage_status == "CERTIFIED" and left.upstream_origin_id and right.upstream_origin_id and left.upstream_origin_id != right.upstream_origin_id:
        return ObservationRelationshipClassification.INDEPENDENT, (), ()
    return ObservationRelationshipClassification.UNKNOWN_RELATIONSHIP, (), ("source_lineage", "independence_proof")


def _time_key(obs: ObservationRecord) -> tuple[str, str, str]:
    return obs.reporting_period, obs.session_identifier, obs.effective_timestamp or obs.observation_timestamp


def _first_value(observations: tuple[ObservationRecord, ...], attr: str) -> str:
    if not observations:
        return ""
    value = getattr(observations[0], attr)
    if isinstance(value, Mapping):
        return next(iter(value.values()), "")
    return str(value)


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
