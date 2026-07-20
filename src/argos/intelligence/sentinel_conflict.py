"""MO-TR-011 Sentinel conflict-handling doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_011_VERSION = "MO-TR-011/1.0.0"


class SentinelSignalType(str, Enum):
    MARKET_ALERT = "MARKET_ALERT"
    NEWS_ALERT = "NEWS_ALERT"
    CORPORATE_EVENT = "CORPORATE_EVENT"
    EXCHANGE_NOTICE = "EXCHANGE_NOTICE"
    ECONOMIC_RELEASE = "ECONOMIC_RELEASE"
    BROKER_NOTIFICATION = "BROKER_NOTIFICATION"
    TRADING_HALT = "TRADING_HALT"
    CORPORATE_ACTION = "CORPORATE_ACTION"
    REGULATORY_ACTION = "REGULATORY_ACTION"
    LEGAL_EVENT = "LEGAL_EVENT"
    MACROECONOMIC_EVENT = "MACROECONOMIC_EVENT"
    OPERATIONAL_FAILURE = "OPERATIONAL_FAILURE"
    SOURCE_OUTAGE = "SOURCE_OUTAGE"
    SOURCE_CORRUPTION = "SOURCE_CORRUPTION"
    SYSTEM_HEALTH_ALERT = "SYSTEM_HEALTH_ALERT"
    RISK_TRIGGERING_OBSERVATION = "RISK_TRIGGERING_OBSERVATION"


class SentinelAlertState(str, Enum):
    NO_ACTION = "NO_ACTION"
    WATCH = "WATCH"
    INVESTIGATE = "INVESTIGATE"
    URGENT_INVESTIGATION = "URGENT_INVESTIGATION"
    SOURCE_HEALTH_ALERT = "SOURCE_HEALTH_ALERT"
    MARKET_SAFETY_ALERT = "MARKET_SAFETY_ALERT"
    UNKNOWN_ALERT_STATE = "UNKNOWN_ALERT_STATE"


class SentinelIndependence(str, Enum):
    INDEPENDENT = "INDEPENDENT"
    SAME_ORIGIN = "SAME_ORIGIN"
    DERIVATIVE = "DERIVATIVE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SentinelSignal:
    signal_id: str
    workflow_id: str
    decision_object_id: str
    observation_id: str
    instrument_id: str
    issuer_id: str
    event_type: str
    authority_domain: str
    source_id: str
    source_origin_id: str
    content_hash: str
    semantic_identity_id: str
    signal_type: SentinelSignalType
    materiality: str
    source_available: bool
    source_schema_valid: bool
    source_authenticated: bool
    conflicting_observation_ids: tuple[str, ...]
    observation_time: str
    publication_time: str
    effective_time: str
    expiration_time: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class SentinelAlertRecord:
    alert_id: str
    workflow_id: str
    decision_object_id: str
    observation_ids: tuple[str, ...]
    observation_hashes: tuple[str, ...]
    alert_state: SentinelAlertState
    signal_type: SentinelSignalType
    instrument_id: str
    issuer_id: str
    authority_domain: str
    source_id: str
    source_independence: SentinelIndependence
    observation_time: str
    publication_time: str
    effective_time: str
    expiration_time: str
    replay_identifier: str
    audit_identifier: str
    doctrine_version: str
    rule_identifier: str
    triggered_office: str
    escalation_target: str
    required_action: str
    evidence_references: tuple[str, ...]
    created_at: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class AlertRepository:
    def __init__(self) -> None:
        self._records: dict[str, SentinelAlertRecord] = {}

    def append(self, record: SentinelAlertRecord) -> None:
        if record.alert_id in self._records:
            raise ValueError("sentinel alerts are append-only")
        self._records[record.alert_id] = record

    def all_records(self) -> tuple[SentinelAlertRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def active_records(self) -> tuple[SentinelAlertRecord, ...]:
        return tuple(record for record in self.all_records() if record.alert_state is not SentinelAlertState.NO_ACTION and (not record.expiration_time or record.expiration_time > utc_timestamp()))


class DuplicateDetectionEngine:
    def is_duplicate(self, signal: SentinelSignal, active_records: tuple[SentinelAlertRecord, ...]) -> bool:
        key = (signal.instrument_id, signal.issuer_id, signal.event_type, signal.authority_domain, signal.publication_time, signal.effective_time, signal.source_id, signal.semantic_identity_id)
        for record in active_records:
            record_key = (record.instrument_id, record.issuer_id, record.rule_identifier.split("|")[0], record.authority_domain, record.publication_time, record.effective_time, record.source_id, record.rule_identifier.split("|")[2])
            if key == record_key:
                return True
        return False


class SourceIndependenceEvaluator:
    def evaluate(self, signal: SentinelSignal, active_records: tuple[SentinelAlertRecord, ...]) -> SentinelIndependence:
        if not signal.source_origin_id:
            return SentinelIndependence.UNKNOWN
        for record in active_records:
            if signal.source_origin_id in record.rule_identifier:
                return SentinelIndependence.SAME_ORIGIN
        return SentinelIndependence.INDEPENDENT


class SentinelConflictEngine:
    def __init__(self, repository: AlertRepository | None = None) -> None:
        self.repository = repository or AlertRepository()
        self.duplicates = DuplicateDetectionEngine()
        self.independence = SourceIndependenceEvaluator()

    def evaluate(self, signal: SentinelSignal) -> SentinelAlertRecord:
        if not signal.signal_id or not signal.observation_id or not signal.source_id:
            return self._record(signal, SentinelAlertState.UNKNOWN_ALERT_STATE, SentinelIndependence.UNKNOWN, "mandatory_input_missing", "Sentinel", "preserve_and_request_required_metadata")
        active = self.repository.active_records()
        independence = self.independence.evaluate(signal, active)
        if self.duplicates.is_duplicate(signal, active):
            return self._record(signal, SentinelAlertState.NO_ACTION, independence, "duplicate_suppressed", "Sentinel", "record_duplicate_suppression")
        if signal.expiration_time and signal.expiration_time <= utc_timestamp():
            return self._record(signal, SentinelAlertState.NO_ACTION, independence, "expired_signal", "Sentinel", "record_expired_signal")
        if not signal.source_available or not signal.source_schema_valid or not signal.source_authenticated:
            return self._record(signal, SentinelAlertState.SOURCE_HEALTH_ALERT, independence, "source_health_failure", "Seeker", "request_source_health_investigation")
        if signal.signal_type in {SentinelSignalType.SOURCE_OUTAGE, SentinelSignalType.SOURCE_CORRUPTION, SentinelSignalType.SYSTEM_HEALTH_ALERT}:
            return self._record(signal, SentinelAlertState.SOURCE_HEALTH_ALERT, independence, "source_or_system_health_signal", "Seeker", "open_source_health_case")
        if signal.signal_type in {SentinelSignalType.TRADING_HALT, SentinelSignalType.EXCHANGE_NOTICE}:
            return self._record(signal, SentinelAlertState.MARKET_SAFETY_ALERT, independence, "market_safety_signal", "Risk", "escalate_market_safety")
        if signal.signal_type in {SentinelSignalType.BROKER_NOTIFICATION, SentinelSignalType.REGULATORY_ACTION, SentinelSignalType.LEGAL_EVENT} or signal.materiality == "HIGH":
            return self._record(signal, SentinelAlertState.URGENT_INVESTIGATION, independence, "urgent_material_signal", "Seeker", "request_urgent_investigation")
        if signal.conflicting_observation_ids:
            return self._record(signal, SentinelAlertState.INVESTIGATE, independence, "conflicting_signal_preserved", "Seeker", "request_evidence_collection")
        return self._record(signal, SentinelAlertState.WATCH if signal.materiality == "LOW" else SentinelAlertState.INVESTIGATE, independence, "deterministic_alert_classification", "Seeker", "monitor_or_collect_evidence")

    def replay(self, record: SentinelAlertRecord, signal: SentinelSignal) -> SentinelAlertState:
        clone = SentinelConflictEngine(AlertRepository())
        replayed = clone.evaluate(signal)
        return replayed.alert_state if replayed.rule_identifier == record.rule_identifier else SentinelAlertState.UNKNOWN_ALERT_STATE

    def _record(self, signal: SentinelSignal, state: SentinelAlertState, independence: SentinelIndependence, rule: str, office: str, action: str) -> SentinelAlertRecord:
        record = SentinelAlertRecord(
            _stable_id("SENTALERT", signal.signal_id, state.value, rule),
            signal.workflow_id,
            signal.decision_object_id,
            (signal.observation_id,) + signal.conflicting_observation_ids,
            (_stable_digest(signal),),
            state,
            signal.signal_type,
            signal.instrument_id,
            signal.issuer_id,
            signal.authority_domain,
            signal.source_id,
            independence,
            signal.observation_time,
            signal.publication_time,
            signal.effective_time,
            signal.expiration_time,
            _stable_id("SENTREPLAY", signal.signal_id, rule),
            _stable_id("SENTAUDIT", signal.signal_id, state.value),
            MO_TR_011_VERSION,
            f"{signal.event_type}|{signal.source_origin_id}|{signal.semantic_identity_id}|{rule}",
            office,
            office,
            action,
            signal.evidence_references,
            utc_timestamp(),
        )
        self.repository.append(record)
        return record


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
