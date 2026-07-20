"""MO-TR-016 Historian conflict preservation and historical truth doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_016_VERSION = "MO-TR-016/1.0.0"


class HistoricalLayer(str, Enum):
    OBSERVED_REALITY = "OBSERVED_REALITY"
    HISTORICAL_KNOWLEDGE = "HISTORICAL_KNOWLEDGE"
    HISTORICAL_DECISION = "HISTORICAL_DECISION"
    CURRENT_BEST_SUPPORTED_TRUTH = "CURRENT_BEST_SUPPORTED_TRUTH"


class HistorianReplayMode(str, Enum):
    HISTORICAL_KNOWLEDGE = "HISTORICAL_KNOWLEDGE"
    CURRENT_SUPPORTED_TRUTH = "CURRENT_SUPPORTED_TRUTH"
    DECISION_REPLAY = "DECISION_REPLAY"
    WORKFLOW_REPLAY = "WORKFLOW_REPLAY"
    CONFLICT_REPLAY = "CONFLICT_REPLAY"
    AUDIT_REPLAY = "AUDIT_REPLAY"
    FULL_SYSTEM_REPLAY = "FULL_SYSTEM_REPLAY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class HistoricalRecord:
    historical_record_id: str
    workflow_id: str
    claim_identity: str
    fact_domain: str
    observation_ids: tuple[str, ...]
    evidence_package_id: str
    conflict_ids: tuple[str, ...]
    decision_ids: tuple[str, ...]
    uncertainty_ids: tuple[str, ...]
    revision_ids: tuple[str, ...]
    office_identity: str
    doctrine_version: str
    historical_layer: HistoricalLayer
    valid_from: str
    system_recorded_time: str
    evidence_references: tuple[str, ...]
    successor_record_id: str = ""
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


@dataclass(frozen=True)
class HistoricalReplayRequest:
    replay_id: str
    workflow_id: str
    requested_timestamp: str
    requested_rule_version: str
    requested_fact_domain: str
    requested_claim: str
    requested_security: str
    requested_position: str
    requested_portfolio: str
    requested_account: str
    replay_mode: HistorianReplayMode
    initiating_office: str
    system_timestamp: str


@dataclass(frozen=True)
class HistoricalReplayResult:
    replay_id: str
    replay_mode: HistorianReplayMode
    requested_timestamp: str
    included_record_ids: tuple[str, ...]
    excluded_later_record_ids: tuple[str, ...]
    known_observations: tuple[str, ...]
    known_conflicts: tuple[str, ...]
    known_decisions: tuple[str, ...]
    known_uncertainty: tuple[str, ...]
    current_supported_records: tuple[str, ...]
    rule_version: str
    result_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "result_digest", _stable_digest(self))


@dataclass(frozen=True)
class RetroactiveReviewRecord:
    review_id: str
    original_record_id: str
    new_record_id: str
    would_alter_decision: bool
    reason_for_change: str
    affected_workflows: tuple[str, ...]
    affected_positions: tuple[str, ...]
    affected_risk: tuple[str, ...]
    affected_performance: tuple[str, ...]
    doctrine_version: str
    created_at: str


class HistorianTruthArchive:
    def __init__(self) -> None:
        self._records: dict[str, HistoricalRecord] = {}
        self._reviews: dict[str, RetroactiveReviewRecord] = {}

    def append_record(self, record: HistoricalRecord) -> None:
        if record.historical_record_id in self._records:
            raise ValueError("historical records are append-only")
        self._records[record.historical_record_id] = record

    def append_retroactive_review(self, review: RetroactiveReviewRecord) -> None:
        if review.review_id in self._reviews:
            raise ValueError("retroactive reviews are append-only")
        self._reviews[review.review_id] = review

    def replay(self, request: HistoricalReplayRequest) -> HistoricalReplayResult:
        eligible = [
            record
            for record in self._records.values()
            if record.system_recorded_time <= request.requested_timestamp
            and (not request.workflow_id or record.workflow_id == request.workflow_id)
            and (not request.requested_claim or record.claim_identity == request.requested_claim)
            and (not request.requested_fact_domain or record.fact_domain == request.requested_fact_domain)
        ]
        later = [record for record in self._records.values() if record.system_recorded_time > request.requested_timestamp]
        if request.replay_mode is HistorianReplayMode.CURRENT_SUPPORTED_TRUTH:
            current = [record for record in eligible if record.historical_layer is HistoricalLayer.CURRENT_BEST_SUPPORTED_TRUTH and not record.successor_record_id]
        else:
            current = []
        return HistoricalReplayResult(
            request.replay_id,
            request.replay_mode,
            request.requested_timestamp,
            tuple(sorted(record.historical_record_id for record in eligible)),
            tuple(sorted(record.historical_record_id for record in later)),
            tuple(obs for record in eligible for obs in record.observation_ids),
            tuple(conflict for record in eligible for conflict in record.conflict_ids),
            tuple(decision for record in eligible for decision in record.decision_ids),
            tuple(uncertainty for record in eligible for uncertainty in record.uncertainty_ids),
            tuple(sorted(record.historical_record_id for record in current)),
            request.requested_rule_version or MO_TR_016_VERSION,
        )

    def retroactive_review(self, original: HistoricalRecord, new: HistoricalRecord, reason: str) -> RetroactiveReviewRecord:
        review = RetroactiveReviewRecord(_stable_id("HISTREV", original.historical_record_id, new.historical_record_id, reason), original.historical_record_id, new.historical_record_id, original.record_digest != new.record_digest, reason, (original.workflow_id,), (), tuple(new.uncertainty_ids), (), MO_TR_016_VERSION, utc_timestamp())
        self.append_retroactive_review(review)
        return review


def historical_record(workflow_id: str, claim_identity: str, fact_domain: str, layer: HistoricalLayer, *, observation_ids: tuple[str, ...] = (), evidence_package_id: str = "", conflict_ids: tuple[str, ...] = (), decision_ids: tuple[str, ...] = (), uncertainty_ids: tuple[str, ...] = (), revision_ids: tuple[str, ...] = (), recorded_at: str = "", successor_record_id: str = "") -> HistoricalRecord:
    return HistoricalRecord(_stable_id("HIST", workflow_id, claim_identity, fact_domain, layer.value, recorded_at or utc_timestamp()), workflow_id, claim_identity, fact_domain, observation_ids, evidence_package_id, conflict_ids, decision_ids, uncertainty_ids, revision_ids, "Historian", MO_TR_016_VERSION, layer, recorded_at or utc_timestamp(), recorded_at or utc_timestamp(), (), successor_record_id)


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
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name not in {"record_digest", "result_digest"}}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
