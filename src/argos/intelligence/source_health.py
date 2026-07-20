"""MO-TR-017 source reliability, health, and quarantine doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_017_VERSION = "MO-TR-017/1.0.0"


class SourceHealthState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    UNRELIABLE = "UNRELIABLE"
    QUARANTINED = "QUARANTINED"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"
    UNKNOWN_HEALTH = "UNKNOWN_HEALTH"


class SourceOperationalRole(str, Enum):
    PRIMARY_AUTHORITY = "PRIMARY_AUTHORITY"
    ACCOUNT_SPECIFIC_AUTHORITY = "ACCOUNT_SPECIFIC_AUTHORITY"
    CORROBORATING_AUTHORITY = "CORROBORATING_AUTHORITY"
    PROVISIONAL_SOURCE = "PROVISIONAL_SOURCE"
    DISCOVERY_ONLY_SOURCE = "DISCOVERY_ONLY_SOURCE"
    FORENSIC_ONLY_SOURCE = "FORENSIC_ONLY_SOURCE"
    HISTORICAL_REPLAY_SOURCE = "HISTORICAL_REPLAY_SOURCE"
    PROHIBITED_SOURCE = "PROHIBITED_SOURCE"


@dataclass(frozen=True)
class SourceHealthPolicy:
    policy_id: str
    source_class: str
    fact_domain: str
    source_role: SourceOperationalRole
    evaluation_window: int
    minimum_observation_count: int
    successful_response_threshold: float
    transport_error_threshold: float
    authentication_failure_threshold: float
    stale_response_threshold: float
    schema_error_threshold: float
    conflict_frequency_threshold: float
    suspected_corruption_threshold: int
    suspected_manipulation_threshold: int
    consecutive_success_restore_requirement: int
    role_restrictions_by_health_state: Mapping[SourceHealthState, tuple[SourceOperationalRole, ...]]
    replacement_source_rules: Mapping[str, str]
    human_review_required_for_quarantine: bool
    escalation_destination: str
    policy_version: str = MO_TR_017_VERSION


@dataclass(frozen=True)
class SourceTelemetryRecord:
    telemetry_id: str
    source_id: str
    workflow_id: str
    fact_domain: str
    request_timestamp: str
    response_timestamp: str
    source_observation_timestamp: str
    transport_success: bool
    authentication_success: bool
    authorization_success: bool
    timeout: bool
    rate_limited: bool
    schema_valid: bool
    required_fields_present: bool
    identifiers_valid: bool
    timestamps_valid: bool
    fresh: bool
    duplicate_response: bool
    frozen_data: bool
    correction: bool
    revision: bool
    authority_conflict: bool
    numerical_conflict: bool
    suspected_corruption: bool
    suspected_manipulation: bool
    downstream_rejected: bool
    observation_id: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class SourceHealthEvaluationRecord:
    health_evaluation_id: str
    source_id: str
    policy_id: str
    policy_version: str
    evaluated_fact_domain: str
    evaluated_source_role: SourceOperationalRole
    evaluation_window: int
    telemetry_references: tuple[str, ...]
    metric_values: Mapping[str, float]
    thresholds_applied: Mapping[str, float]
    immediate_failure_rules_triggered: tuple[str, ...]
    prior_health_state: SourceHealthState
    new_health_state: SourceHealthState
    eligibility_changes: tuple[SourceOperationalRole, ...]
    quarantine_status: str
    replacement_source_action: str
    dependent_evidence_consequence: str
    dependent_workflow_consequence: str
    trade_consequence: str
    escalation_destination: str
    human_review_required: bool
    reason_codes: tuple[str, ...]
    evaluation_timestamp: str
    state_transition_timestamp: str
    evidence_references: tuple[str, ...]
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class SourceHealthLedger:
    def __init__(self) -> None:
        self._records: dict[str, SourceHealthEvaluationRecord] = {}

    def append(self, record: SourceHealthEvaluationRecord) -> None:
        if record.health_evaluation_id in self._records:
            raise ValueError("source health evaluations are append-only")
        self._records[record.health_evaluation_id] = record


class SourceHealthEvaluationEngine:
    def __init__(self, ledger: SourceHealthLedger | None = None) -> None:
        self.ledger = ledger or SourceHealthLedger()

    def evaluate(self, source_id: str, prior_state: SourceHealthState, policy: SourceHealthPolicy, telemetry: tuple[SourceTelemetryRecord, ...]) -> SourceHealthEvaluationRecord:
        metrics = _metrics(telemetry)
        reasons: list[str] = []
        if len(telemetry) < policy.minimum_observation_count:
            state = SourceHealthState.UNKNOWN_HEALTH
            reasons.append("minimum_observation_window_not_satisfied")
        elif any(item.suspected_corruption for item in telemetry) or metrics["suspected_corruption_count"] >= policy.suspected_corruption_threshold:
            state = SourceHealthState.QUARANTINED
            reasons.append("suspected_corruption")
        elif any(item.suspected_manipulation for item in telemetry) or metrics["suspected_manipulation_count"] >= policy.suspected_manipulation_threshold:
            state = SourceHealthState.QUARANTINED
            reasons.append("suspected_manipulation")
        elif metrics["authentication_failure_rate"] > policy.authentication_failure_threshold:
            state = SourceHealthState.SUSPENDED
            reasons.append("authentication_failure_threshold_exceeded")
        elif metrics["stale_response_rate"] > policy.stale_response_threshold or metrics["frozen_feed_rate"] > 0:
            state = SourceHealthState.STALE
            reasons.append("stale_or_frozen_data")
        elif metrics["transport_error_rate"] > policy.transport_error_threshold or metrics["schema_error_rate"] > policy.schema_error_threshold or metrics["conflict_rate"] > policy.conflict_frequency_threshold:
            state = SourceHealthState.UNRELIABLE
            reasons.append("error_or_conflict_threshold_exceeded")
        elif metrics["successful_response_rate"] < policy.successful_response_threshold:
            state = SourceHealthState.DEGRADED
            reasons.append("success_rate_below_healthy_threshold")
        else:
            state = SourceHealthState.HEALTHY
            reasons.append("all_mandatory_metrics_within_thresholds")
        roles = policy.role_restrictions_by_health_state.get(state, (SourceOperationalRole.PROHIBITED_SOURCE,))
        record = SourceHealthEvaluationRecord(
            _stable_id("SRCHEALTH", source_id, tuple(item.telemetry_id for item in telemetry), state.value),
            source_id,
            policy.policy_id,
            policy.policy_version,
            policy.fact_domain,
            policy.source_role,
            policy.evaluation_window,
            tuple(item.telemetry_id for item in telemetry),
            MappingProxyType(metrics),
            MappingProxyType({
                "successful_response_threshold": policy.successful_response_threshold,
                "transport_error_threshold": policy.transport_error_threshold,
                "authentication_failure_threshold": policy.authentication_failure_threshold,
                "stale_response_threshold": policy.stale_response_threshold,
                "schema_error_threshold": policy.schema_error_threshold,
                "conflict_frequency_threshold": policy.conflict_frequency_threshold,
            }),
            tuple(reason for reason in reasons if "suspected" in reason or "authentication" in reason),
            prior_state,
            state,
            roles,
            "QUARANTINE_ACTIVE" if state is SourceHealthState.QUARANTINED else "NO_ACTIVE_QUARANTINE",
            policy.replacement_source_rules.get(policy.fact_domain, "NO_PREAPPROVED_REPLACEMENT"),
            "recertify_dependent_facts" if state is not SourceHealthState.HEALTHY else "no_dependent_evidence_action",
            "restrict_dependent_workflows" if state in {SourceHealthState.QUARANTINED, SourceHealthState.SUSPENDED, SourceHealthState.UNKNOWN_HEALTH} else "monitor_dependent_workflows",
            "block_execution_sensitive_use" if state is not SourceHealthState.HEALTHY else "no_trade_consequence",
            policy.escalation_destination,
            policy.human_review_required_for_quarantine and state is SourceHealthState.QUARANTINED,
            tuple(reasons),
            utc_timestamp(),
            utc_timestamp(),
            tuple(ref for item in telemetry for ref in item.evidence_references),
        )
        self.ledger.append(record)
        return record


def default_source_health_policy(source_class: str = "PRIMARY", fact_domain: str = "market_data", role: SourceOperationalRole = SourceOperationalRole.PRIMARY_AUTHORITY) -> SourceHealthPolicy:
    restrictions = MappingProxyType({
        SourceHealthState.HEALTHY: (role,),
        SourceHealthState.DEGRADED: (SourceOperationalRole.CORROBORATING_AUTHORITY, SourceOperationalRole.DISCOVERY_ONLY_SOURCE),
        SourceHealthState.STALE: (SourceOperationalRole.HISTORICAL_REPLAY_SOURCE, SourceOperationalRole.DISCOVERY_ONLY_SOURCE),
        SourceHealthState.UNRELIABLE: (SourceOperationalRole.DISCOVERY_ONLY_SOURCE,),
        SourceHealthState.QUARANTINED: (SourceOperationalRole.FORENSIC_ONLY_SOURCE, SourceOperationalRole.HISTORICAL_REPLAY_SOURCE),
        SourceHealthState.SUSPENDED: (SourceOperationalRole.PROHIBITED_SOURCE,),
        SourceHealthState.RETIRED: (SourceOperationalRole.HISTORICAL_REPLAY_SOURCE,),
        SourceHealthState.UNKNOWN_HEALTH: (SourceOperationalRole.PROHIBITED_SOURCE,),
    })
    return SourceHealthPolicy("SHP-DEFAULT", source_class, fact_domain, role, 10, 3, 0.95, 0.10, 0.0, 0.0, 0.05, 0.10, 1, 1, 3, restrictions, MappingProxyType({}), True, "Risk")


def _metrics(telemetry: tuple[SourceTelemetryRecord, ...]) -> dict[str, float]:
    total = max(1, len(telemetry))
    return {
        "successful_response_rate": sum(1 for item in telemetry if item.transport_success and item.authentication_success and item.authorization_success) / total,
        "transport_error_rate": sum(1 for item in telemetry if not item.transport_success) / total,
        "authentication_failure_rate": sum(1 for item in telemetry if not item.authentication_success) / total,
        "schema_error_rate": sum(1 for item in telemetry if not item.schema_valid or not item.required_fields_present) / total,
        "stale_response_rate": sum(1 for item in telemetry if not item.fresh) / total,
        "frozen_feed_rate": sum(1 for item in telemetry if item.frozen_data) / total,
        "conflict_rate": sum(1 for item in telemetry if item.authority_conflict or item.numerical_conflict) / total,
        "suspected_corruption_count": float(sum(1 for item in telemetry if item.suspected_corruption)),
        "suspected_manipulation_count": float(sum(1 for item in telemetry if item.suspected_manipulation)),
    }


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
