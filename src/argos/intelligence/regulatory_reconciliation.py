"""MO-TR-007 regulatory, legal, exchange, and trading-status reconciliation."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_007_VERSION = "MO-TR-007/1.0.0"


class RegulatoryDomain(str, Enum):
    SEC_FILINGS = "SEC_FILINGS"
    SEC_ENFORCEMENT_ACTIONS = "SEC_ENFORCEMENT_ACTIONS"
    EXCHANGE_NOTICES = "EXCHANGE_NOTICES"
    FINRA_NOTICES = "FINRA_NOTICES"
    COURT_ORDERS = "COURT_ORDERS"
    COURT_DOCKETS = "COURT_DOCKETS"
    BANKRUPTCY_PROCEEDINGS = "BANKRUPTCY_PROCEEDINGS"
    TRADING_HALTS = "TRADING_HALTS"
    LISTING_SUSPENSIONS = "LISTING_SUSPENSIONS"
    DELISTING_NOTICES = "DELISTING_NOTICES"
    SHORT_SALE_RESTRICTIONS = "SHORT_SALE_RESTRICTIONS"
    BROKER_TRADING_RESTRICTIONS = "BROKER_TRADING_RESTRICTIONS"
    SANCTIONS_LISTS = "SANCTIONS_LISTS"
    JURISDICTION_RESTRICTIONS = "JURISDICTION_RESTRICTIONS"
    SETTLEMENT_RESTRICTIONS = "SETTLEMENT_RESTRICTIONS"
    CORPORATE_LEGAL_ACTIONS = "CORPORATE_LEGAL_ACTIONS"
    UNKNOWN_REGULATORY_DOMAIN = "UNKNOWN_REGULATORY_DOMAIN"


class RegulatoryAuthorityClass(str, Enum):
    EXCHANGE = "EXCHANGE"
    SEC = "SEC"
    FINRA = "FINRA"
    COURT = "COURT"
    BANKRUPTCY_COURT = "BANKRUPTCY_COURT"
    BROKER = "BROKER"
    SANCTIONS_AUTHORITY = "SANCTIONS_AUTHORITY"
    SETTLEMENT_AUTHORITY = "SETTLEMENT_AUTHORITY"
    ISSUER = "ISSUER"
    NEWS = "NEWS"
    UNKNOWN_AUTHORITY = "UNKNOWN_AUTHORITY"


class RegulatoryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    HALTED = "HALTED"
    SUSPENDED = "SUSPENDED"
    DELISTED = "DELISTED"
    BANKRUPTCY_PENDING = "BANKRUPTCY_PENDING"
    BANKRUPTCY_ACTIVE = "BANKRUPTCY_ACTIVE"
    SANCTIONED = "SANCTIONED"
    RESTRICTED = "RESTRICTED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    LEGAL_UNCERTAINTY = "LEGAL_UNCERTAINTY"
    REGULATORY_CONFLICT = "REGULATORY_CONFLICT"
    UNKNOWN_STATUS = "UNKNOWN_STATUS"


class TradeEligibility(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    PROHIBITED = "PROHIBITED"
    RESTRICTED = "RESTRICTED"
    DEFERRED = "DEFERRED"
    UNKNOWN_FAIL_CLOSED = "UNKNOWN_FAIL_CLOSED"


@dataclass(frozen=True)
class RegulatoryObservation:
    observation_id: str
    workflow_id: str
    decision_object_id: str
    instrument_id: str
    issuer_id: str
    authority_domain: RegulatoryDomain
    authority_class: RegulatoryAuthorityClass
    source_id: str
    status: RegulatoryStatus
    previous_status: RegulatoryStatus
    publication_time: str
    effective_time: str
    retrieval_time: str
    jurisdiction: str
    rule_identifier: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class RegulatoryReconciliationRecord:
    reconciliation_id: str
    workflow_id: str
    decision_object_id: str
    instrument_id: str
    issuer_id: str
    authority_domain: RegulatoryDomain
    primary_authority: RegulatoryAuthorityClass
    secondary_authority: RegulatoryAuthorityClass
    observation_ids: tuple[str, ...]
    observation_hashes: tuple[str, ...]
    publication_time: str
    effective_time: str
    retrieval_time: str
    jurisdiction: str
    current_status: RegulatoryStatus
    previous_status: RegulatoryStatus
    rule_identifier: str
    doctrine_version: str
    resolution_result: str
    required_action: str
    trade_eligibility: TradeEligibility
    affected_offices: tuple[str, ...]
    replay_identifier: str
    audit_identifier: str
    evidence_references: tuple[str, ...]
    created_at: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class RegulatoryReconciliationLedger:
    def __init__(self) -> None:
        self._records: dict[str, RegulatoryReconciliationRecord] = {}

    def append(self, record: RegulatoryReconciliationRecord) -> None:
        if record.reconciliation_id in self._records:
            raise ValueError("regulatory reconciliations are append-only")
        self._records[record.reconciliation_id] = record

    def all_records(self) -> tuple[RegulatoryReconciliationRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))


class RegulatoryReconciliationEngine:
    def __init__(self, ledger: RegulatoryReconciliationLedger | None = None) -> None:
        self.ledger = ledger or RegulatoryReconciliationLedger()

    def reconcile(self, observations: tuple[RegulatoryObservation, ...]) -> RegulatoryReconciliationRecord:
        if not observations:
            return self._record((), RegulatoryDomain.UNKNOWN_REGULATORY_DOMAIN, RegulatoryStatus.UNKNOWN_STATUS, RegulatoryStatus.UNKNOWN_STATUS, RegulatoryAuthorityClass.UNKNOWN_AUTHORITY, RegulatoryAuthorityClass.UNKNOWN_AUTHORITY, "no_observations", "collect_official_legal_status", TradeEligibility.UNKNOWN_FAIL_CLOSED)
        first = observations[0]
        if any(obs.instrument_id != first.instrument_id or obs.issuer_id != first.issuer_id for obs in observations):
            return self._record(observations, first.authority_domain, RegulatoryStatus.UNKNOWN_STATUS, first.previous_status, RegulatoryAuthorityClass.UNKNOWN_AUTHORITY, RegulatoryAuthorityClass.UNKNOWN_AUTHORITY, "instrument_or_issuer_mismatch", "block_until_identity_resolved", TradeEligibility.PROHIBITED)

        primary_class = _primary_for_domain(first.authority_domain)
        primaries = [obs for obs in observations if obs.authority_class is primary_class and obs.authority_domain is first.authority_domain]
        if not primaries:
            discovery_only = [obs for obs in observations if obs.authority_class in {RegulatoryAuthorityClass.ISSUER, RegulatoryAuthorityClass.NEWS}]
            reason = "issuer_or_news_cannot_override_official_authority" if discovery_only else "primary_authority_missing"
            return self._record(observations, first.authority_domain, RegulatoryStatus.UNKNOWN_STATUS, first.previous_status, primary_class, observations[0].authority_class, reason, "collect_primary_authority_and_block", TradeEligibility.UNKNOWN_FAIL_CLOSED)

        latest_effective = sorted(primaries, key=lambda obs: (obs.effective_time, obs.publication_time, obs.observation_id))
        current = latest_effective[-1]
        same_time_primaries = [obs for obs in primaries if obs.effective_time == current.effective_time]
        if len({obs.status for obs in same_time_primaries}) > 1:
            return self._record(observations, first.authority_domain, RegulatoryStatus.REGULATORY_CONFLICT, current.previous_status, primary_class, primary_class, "conflicting_primary_authorities", "route_conflict_and_block_trading", TradeEligibility.PROHIBITED)

        eligibility = _eligibility_for_status(current.status)
        action = "permit_read_only_status_consumption" if eligibility is TradeEligibility.ELIGIBLE else "emit_trade_block"
        return self._record(observations, first.authority_domain, current.status, current.previous_status, primary_class, _secondary_authority(observations, primary_class), "latest_effective_official_status", action, eligibility)

    def _record(self, observations: tuple[RegulatoryObservation, ...], domain: RegulatoryDomain, current: RegulatoryStatus, previous: RegulatoryStatus, primary: RegulatoryAuthorityClass, secondary: RegulatoryAuthorityClass, result: str, action: str, eligibility: TradeEligibility) -> RegulatoryReconciliationRecord:
        first = observations[0] if observations else None
        record = RegulatoryReconciliationRecord(
            _stable_id("REGREC", tuple(obs.observation_id for obs in observations), current.value, result),
            first.workflow_id if first else "",
            first.decision_object_id if first else "",
            first.instrument_id if first else "",
            first.issuer_id if first else "",
            domain,
            primary,
            secondary,
            tuple(obs.observation_id for obs in observations),
            tuple(_stable_digest(obs) for obs in observations),
            max((obs.publication_time for obs in observations), default=""),
            max((obs.effective_time for obs in observations), default=""),
            max((obs.retrieval_time for obs in observations), default=""),
            first.jurisdiction if first else "",
            current,
            previous,
            first.rule_identifier if first else MO_TR_007_VERSION,
            MO_TR_007_VERSION,
            result,
            action,
            eligibility,
            ("RegulatoryReconciliation", "Risk", "Trader", "Historian"),
            _stable_id("REGREPLAY", tuple(obs.observation_id for obs in observations), current.value),
            _stable_id("REGAUDIT", tuple(obs.evidence_references for obs in observations), result),
            tuple(ref for obs in observations for ref in obs.evidence_references),
            utc_timestamp(),
        )
        self.ledger.append(record)
        return record


def _primary_for_domain(domain: RegulatoryDomain) -> RegulatoryAuthorityClass:
    if domain in {RegulatoryDomain.EXCHANGE_NOTICES, RegulatoryDomain.TRADING_HALTS, RegulatoryDomain.LISTING_SUSPENSIONS, RegulatoryDomain.DELISTING_NOTICES, RegulatoryDomain.SHORT_SALE_RESTRICTIONS}:
        return RegulatoryAuthorityClass.EXCHANGE
    if domain in {RegulatoryDomain.SEC_FILINGS, RegulatoryDomain.SEC_ENFORCEMENT_ACTIONS}:
        return RegulatoryAuthorityClass.SEC
    if domain is RegulatoryDomain.FINRA_NOTICES:
        return RegulatoryAuthorityClass.FINRA
    if domain in {RegulatoryDomain.COURT_ORDERS, RegulatoryDomain.COURT_DOCKETS, RegulatoryDomain.CORPORATE_LEGAL_ACTIONS}:
        return RegulatoryAuthorityClass.COURT
    if domain is RegulatoryDomain.BANKRUPTCY_PROCEEDINGS:
        return RegulatoryAuthorityClass.BANKRUPTCY_COURT
    if domain is RegulatoryDomain.BROKER_TRADING_RESTRICTIONS:
        return RegulatoryAuthorityClass.BROKER
    if domain in {RegulatoryDomain.SANCTIONS_LISTS, RegulatoryDomain.JURISDICTION_RESTRICTIONS}:
        return RegulatoryAuthorityClass.SANCTIONS_AUTHORITY
    if domain is RegulatoryDomain.SETTLEMENT_RESTRICTIONS:
        return RegulatoryAuthorityClass.SETTLEMENT_AUTHORITY
    return RegulatoryAuthorityClass.UNKNOWN_AUTHORITY


def _eligibility_for_status(status: RegulatoryStatus) -> TradeEligibility:
    if status is RegulatoryStatus.ACTIVE:
        return TradeEligibility.ELIGIBLE
    if status in {RegulatoryStatus.RESTRICTED, RegulatoryStatus.UNDER_INVESTIGATION}:
        return TradeEligibility.RESTRICTED
    if status in {RegulatoryStatus.LEGAL_UNCERTAINTY, RegulatoryStatus.UNKNOWN_STATUS}:
        return TradeEligibility.UNKNOWN_FAIL_CLOSED
    return TradeEligibility.PROHIBITED


def _secondary_authority(observations: tuple[RegulatoryObservation, ...], primary: RegulatoryAuthorityClass) -> RegulatoryAuthorityClass:
    for obs in observations:
        if obs.authority_class is not primary:
            return obs.authority_class
    return RegulatoryAuthorityClass.UNKNOWN_AUTHORITY


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
