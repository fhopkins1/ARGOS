"""MO-TR-009 news, event, rumor, and narrative reconciliation doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_009_VERSION = "MO-TR-009/1.0.0"


class NewsSourceClass(str, Enum):
    ORIGINATING_AUTHORITY = "ORIGINATING_AUTHORITY"
    PRIMARY_WITNESS = "PRIMARY_WITNESS"
    OFFICIAL_STATEMENT = "OFFICIAL_STATEMENT"
    OFFICIAL_RECORD = "OFFICIAL_RECORD"
    RECOGNIZED_NEWSWIRE = "RECOGNIZED_NEWSWIRE"
    ESTABLISHED_SECONDARY_PUBLICATION = "ESTABLISHED_SECONDARY_PUBLICATION"
    SPECIALIST_PUBLICATION = "SPECIALIST_PUBLICATION"
    ANALYST_COMMENTARY = "ANALYST_COMMENTARY"
    UNATTRIBUTED_REPORT = "UNATTRIBUTED_REPORT"
    ANONYMOUS_SOURCE_REPORT = "ANONYMOUS_SOURCE_REPORT"
    SOCIAL_MEDIA_OFFICIAL_ACCOUNT = "SOCIAL_MEDIA_OFFICIAL_ACCOUNT"
    SOCIAL_MEDIA_IDENTIFIED_PERSON = "SOCIAL_MEDIA_IDENTIFIED_PERSON"
    SOCIAL_MEDIA_UNVERIFIED_ACCOUNT = "SOCIAL_MEDIA_UNVERIFIED_ACCOUNT"
    PUBLIC_FORUM = "PUBLIC_FORUM"
    RUMOR = "RUMOR"
    AGGREGATOR = "AGGREGATOR"
    SYNDICATED_COPY = "SYNDICATED_COPY"
    DERIVATIVE_SUMMARY = "DERIVATIVE_SUMMARY"
    MODEL_GENERATED_SUMMARY = "MODEL_GENERATED_SUMMARY"
    UNKNOWN_ORIGIN = "UNKNOWN_ORIGIN"


class NewsClaimState(str, Enum):
    REPORT_DETECTED = "REPORT_DETECTED"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    INVESTIGATION_REQUIRED = "INVESTIGATION_REQUIRED"
    UNCONFIRMED = "UNCONFIRMED"
    PARTIALLY_CORROBORATED = "PARTIALLY_CORROBORATED"
    INDEPENDENTLY_CORROBORATED = "INDEPENDENTLY_CORROBORATED"
    OFFICIALLY_ACKNOWLEDGED = "OFFICIALLY_ACKNOWLEDGED"
    OFFICIALLY_CONFIRMED = "OFFICIALLY_CONFIRMED"
    CONFIRMED_WITH_LIMITATION = "CONFIRMED_WITH_LIMITATION"
    DISPUTED = "DISPUTED"
    OFFICIALLY_DENIED = "OFFICIALLY_DENIED"
    CORRECTED = "CORRECTED"
    PARTIALLY_RETRACTED = "PARTIALLY_RETRACTED"
    FULLY_RETRACTED = "FULLY_RETRACTED"
    EXPIRED_UNCONFIRMED = "EXPIRED_UNCONFIRMED"
    STALE_REPORT = "STALE_REPORT"
    NONCOMPARABLE_REPORTS = "NONCOMPARABLE_REPORTS"
    WRONG_ENTITY = "WRONG_ENTITY"
    WRONG_EVENT = "WRONG_EVENT"
    POSSIBLE_FABRICATION = "POSSIBLE_FABRICATION"
    POSSIBLE_ACCOUNT_COMPROMISE = "POSSIBLE_ACCOUNT_COMPROMISE"
    UNRESOLVED = "UNRESOLVED"
    UNKNOWN_CLAIM_STATE = "UNKNOWN_CLAIM_STATE"


class NewsEventClass(str, Enum):
    MERGER_OR_ACQUISITION = "MERGER_OR_ACQUISITION"
    BANKRUPTCY_OR_INSOLVENCY = "BANKRUPTCY_OR_INSOLVENCY"
    EXECUTIVE_DEPARTURE = "EXECUTIVE_DEPARTURE"
    EXECUTIVE_APPOINTMENT = "EXECUTIVE_APPOINTMENT"
    REGULATORY_INVESTIGATION = "REGULATORY_INVESTIGATION"
    REGULATORY_ACTION = "REGULATORY_ACTION"
    LITIGATION = "LITIGATION"
    COURT_DECISION = "COURT_DECISION"
    PRODUCT_RECALL = "PRODUCT_RECALL"
    CYBERSECURITY_INCIDENT = "CYBERSECURITY_INCIDENT"
    DATA_BREACH = "DATA_BREACH"
    GEOPOLITICAL_EVENT = "GEOPOLITICAL_EVENT"
    MILITARY_EVENT = "MILITARY_EVENT"
    NATURAL_DISASTER = "NATURAL_DISASTER"
    OPERATIONAL_SHUTDOWN = "OPERATIONAL_SHUTDOWN"
    SUPPLY_DISRUPTION = "SUPPLY_DISRUPTION"
    UNSCHEDULED_CORPORATE_ANNOUNCEMENT = "UNSCHEDULED_CORPORATE_ANNOUNCEMENT"
    EARNINGS_PREANNOUNCEMENT = "EARNINGS_PREANNOUNCEMENT"
    GUIDANCE_CHANGE = "GUIDANCE_CHANGE"
    FINANCING_EVENT = "FINANCING_EVENT"
    CREDIT_EVENT = "CREDIT_EVENT"
    SANCTIONS_EVENT = "SANCTIONS_EVENT"
    TRADING_HALT_REPORT = "TRADING_HALT_REPORT"
    DELISTING_REPORT = "DELISTING_REPORT"
    FRAUD_ALLEGATION = "FRAUD_ALLEGATION"
    MARKET_MANIPULATION_ALLEGATION = "MARKET_MANIPULATION_ALLEGATION"
    LABOR_DISRUPTION = "LABOR_DISRUPTION"
    MANAGEMENT_CONDUCT_EVENT = "MANAGEMENT_CONDUCT_EVENT"
    UNKNOWN_EVENT_CLASS = "UNKNOWN_EVENT_CLASS"


class OriginRelationship(str, Enum):
    SAME_ORIGIN = "SAME_ORIGIN"
    SYNDICATED_COPY = "SYNDICATED_COPY"
    COPIED_CONTENT = "COPIED_CONTENT"
    COMMON_OWNER = "COMMON_OWNER"
    COMMON_DATA_PROVIDER = "COMMON_DATA_PROVIDER"
    INDEPENDENT_ORIGIN = "INDEPENDENT_ORIGIN"
    UNKNOWN_ORIGIN = "UNKNOWN_ORIGIN"


class OfficialConfirmationStatus(str, Enum):
    OFFICIAL_ACKNOWLEDGMENT = "OFFICIAL_ACKNOWLEDGMENT"
    OFFICIAL_CONFIRMATION = "OFFICIAL_CONFIRMATION"
    OFFICIAL_DENIAL = "OFFICIAL_DENIAL"
    OFFICIAL_NONCOMMENT = "OFFICIAL_NONCOMMENT"
    OFFICIAL_INVESTIGATION = "OFFICIAL_INVESTIGATION"
    OFFICIAL_PRELIMINARY_STATEMENT = "OFFICIAL_PRELIMINARY_STATEMENT"
    OFFICIAL_FINAL_DETERMINATION = "OFFICIAL_FINAL_DETERMINATION"
    OFFICIAL_CORRECTION = "OFFICIAL_CORRECTION"
    OFFICIAL_RETRACTION = "OFFICIAL_RETRACTION"
    OFFICIAL_SILENCE = "OFFICIAL_SILENCE"
    NO_OFFICIAL_AUTHORITY_PRESENT = "NO_OFFICIAL_AUTHORITY_PRESENT"


@dataclass(frozen=True)
class NewsSourceRecord:
    source_id: str
    organization_id: str
    publication_name: str
    source_surface: str
    source_class: NewsSourceClass
    ownership_group: str
    parent_organization: str
    syndication_relationships: tuple[str, ...]
    known_content_suppliers: tuple[str, ...]
    jurisdiction: str
    authentication_method: str
    official_account_status: str
    identity_verification_status: str
    correction_mechanism: str
    retraction_mechanism: str
    provenance_capabilities: tuple[str, ...]
    permitted_discovery_uses: tuple[str, ...]
    permitted_provisional_uses: tuple[str, ...]
    permitted_corroboration_uses: tuple[str, ...]
    prohibited_uses: tuple[str, ...]
    configuration_version: str = MO_TR_009_VERSION
    effective_timestamp: str = "2026-07-20T00:00:00Z"
    retirement_timestamp: str = ""


@dataclass(frozen=True)
class NewsClaim:
    claim_id: str
    subject_entity: str
    affected_instrument: str
    event_class: NewsEventClass
    asserted_action: str
    asserted_actor: str
    asserted_target: str
    asserted_status: str
    asserted_jurisdiction: str
    asserted_event_time: str
    asserted_effective_time: str
    asserted_publication_time: str
    claim_scope: str
    source_language: str
    normalized_claim: str
    qualifying_language: str
    uncertainty_language: str
    denial_language: str
    conditional_language: str
    future_tense_language: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class NewsReport:
    report_id: str
    workflow_id: str
    claim: NewsClaim
    source: NewsSourceRecord
    origin_evidence_id: str
    cited_report_ids: tuple[str, ...]
    cited_evidence_retrievable: bool
    publication_time: str
    retrieval_time: str
    correction_time: str
    retraction_time: str
    expiration_time: str
    named_source_present: bool
    anonymous_source_present: bool
    official_confirmation_status: OfficialConfirmationStatus
    report_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_digest", _stable_digest(self))


@dataclass(frozen=True)
class NewsReconciliationRecord:
    reconciliation_id: str
    workflow_id: str
    claim_id: str
    event_class: NewsEventClass
    report_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    source_classes: tuple[NewsSourceClass, ...]
    report_origins: tuple[str, ...]
    independence_determinations: tuple[OriginRelationship, ...]
    official_confirmation_status: OfficialConfirmationStatus
    current_claim_state: NewsClaimState
    conflict_state: str
    sentinel_consequence: str
    seeker_consequence: str
    analyst_consequence: str
    risk_consequence: str
    trader_consequence: str
    escalation_destination: str
    evidence_references: tuple[str, ...]
    doctrine_version: str
    determination_timestamp: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class NewsReconciliationLedger:
    def __init__(self) -> None:
        self._records: dict[str, NewsReconciliationRecord] = {}

    def append(self, record: NewsReconciliationRecord) -> None:
        if record.reconciliation_id in self._records:
            raise ValueError("news reconciliations are append-only")
        self._records[record.reconciliation_id] = record

    def all_records(self) -> tuple[NewsReconciliationRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))


class NewsClaimReconciliationEngine:
    def __init__(self, ledger: NewsReconciliationLedger | None = None) -> None:
        self.ledger = ledger or NewsReconciliationLedger()

    def reconcile(self, reports: tuple[NewsReport, ...]) -> NewsReconciliationRecord:
        if not reports:
            return self._record((), NewsClaimState.UNKNOWN_CLAIM_STATE, OfficialConfirmationStatus.NO_OFFICIAL_AUTHORITY_PRESENT, (), "missing_reports", "Seeker", "collect_reports")
        first = reports[0]
        if any(report.claim.subject_entity != first.claim.subject_entity for report in reports):
            return self._record(reports, NewsClaimState.WRONG_ENTITY, OfficialConfirmationStatus.NO_OFFICIAL_AUTHORITY_PRESENT, (), "entity_mismatch", "Seeker", "preserve_noncomparable_reports")
        if any(report.claim.event_class is not first.claim.event_class for report in reports):
            return self._record(reports, NewsClaimState.WRONG_EVENT, OfficialConfirmationStatus.NO_OFFICIAL_AUTHORITY_PRESENT, (), "event_mismatch", "Seeker", "preserve_noncomparable_reports")
        relationships = _origin_relationships(reports)
        official = _official_status(reports)
        if official is OfficialConfirmationStatus.OFFICIAL_DENIAL:
            return self._record(reports, NewsClaimState.OFFICIALLY_DENIED, official, relationships, "official_denial_preserved", "Analyst", "route_denial_for_review")
        if any(report.retraction_time for report in reports):
            return self._record(reports, NewsClaimState.FULLY_RETRACTED, official, relationships, "retraction_successor_record", "Historian", "recertify_consumers")
        if official in {OfficialConfirmationStatus.OFFICIAL_CONFIRMATION, OfficialConfirmationStatus.OFFICIAL_FINAL_DETERMINATION}:
            return self._record(reports, NewsClaimState.OFFICIALLY_CONFIRMED, official, relationships, "official_authority_confirmed", "Analyst", "analyst_review_permitted")
        independent = sum(1 for relation in relationships if relation is OriginRelationship.INDEPENDENT_ORIGIN)
        if independent >= 1 and all(report.source.source_class not in {NewsSourceClass.RUMOR, NewsSourceClass.PUBLIC_FORUM, NewsSourceClass.MODEL_GENERATED_SUMMARY} for report in reports):
            return self._record(reports, NewsClaimState.INDEPENDENTLY_CORROBORATED, official, relationships, "independent_origins_without_official_confirmation", "Analyst", "analyst_review_with_limitations")
        if any(report.source.source_class in {NewsSourceClass.RUMOR, NewsSourceClass.PUBLIC_FORUM, NewsSourceClass.SOCIAL_MEDIA_UNVERIFIED_ACCOUNT, NewsSourceClass.ANONYMOUS_SOURCE_REPORT} for report in reports):
            return self._record(reports, NewsClaimState.UNCONFIRMED, official, relationships, "rumor_or_anonymous_source", "Seeker", "investigate_without_truth_promotion")
        return self._record(reports, NewsClaimState.INVESTIGATION_REQUIRED, official, relationships, "reported_claim_requires_evidence_collection", "Seeker", "collect_originating_evidence")

    def _record(self, reports: tuple[NewsReport, ...], state: NewsClaimState, official: OfficialConfirmationStatus, relationships: tuple[OriginRelationship, ...], reason: str, escalation: str, action: str) -> NewsReconciliationRecord:
        first = reports[0] if reports else None
        trader = "EXECUTION_PROHIBITED" if state in {NewsClaimState.UNCONFIRMED, NewsClaimState.WRONG_ENTITY, NewsClaimState.WRONG_EVENT, NewsClaimState.POSSIBLE_FABRICATION} else "NO_TRADER_AUTHORITY"
        risk = "CONSTRAIN_CAPITAL" if state in {NewsClaimState.UNCONFIRMED, NewsClaimState.DISPUTED, NewsClaimState.OFFICIALLY_DENIED} else "PRESERVE_FOR_RISK_REVIEW"
        record = NewsReconciliationRecord(
            _stable_id("NEWSREC", tuple(report.report_id for report in reports), state.value, reason),
            first.workflow_id if first else "",
            first.claim.claim_id if first else "",
            first.claim.event_class if first else NewsEventClass.UNKNOWN_EVENT_CLASS,
            tuple(report.report_id for report in reports),
            tuple(report.source.source_id for report in reports),
            tuple(report.source.source_class for report in reports),
            tuple(report.origin_evidence_id for report in reports),
            relationships,
            official,
            state,
            "PRESERVED_UNRESOLVED" if state in {NewsClaimState.UNCONFIRMED, NewsClaimState.DISPUTED, NewsClaimState.WRONG_ENTITY, NewsClaimState.WRONG_EVENT} else "NO_CONFLICT_RESOLVED",
            "INVESTIGATE" if state in {NewsClaimState.UNCONFIRMED, NewsClaimState.INVESTIGATION_REQUIRED} else "WATCH",
            action,
            "NO_TRUTH_SELECTED_BY_NEWS_ENGINE",
            risk,
            trader,
            escalation,
            tuple(ref for report in reports for ref in report.claim.evidence_references),
            MO_TR_009_VERSION,
            utc_timestamp(),
        )
        self.ledger.append(record)
        return record


def _origin_relationships(reports: tuple[NewsReport, ...]) -> tuple[OriginRelationship, ...]:
    relationships = []
    seen_origins: set[str] = set()
    for report in reports:
        if report.origin_evidence_id in seen_origins:
            relationships.append(OriginRelationship.SAME_ORIGIN)
        elif report.source.source_class in {NewsSourceClass.SYNDICATED_COPY, NewsSourceClass.AGGREGATOR, NewsSourceClass.DERIVATIVE_SUMMARY, NewsSourceClass.MODEL_GENERATED_SUMMARY}:
            relationships.append(OriginRelationship.SYNDICATED_COPY)
        else:
            relationships.append(OriginRelationship.INDEPENDENT_ORIGIN if seen_origins else OriginRelationship.UNKNOWN_ORIGIN)
        seen_origins.add(report.origin_evidence_id)
    return tuple(relationships)


def _official_status(reports: tuple[NewsReport, ...]) -> OfficialConfirmationStatus:
    priority = [
        OfficialConfirmationStatus.OFFICIAL_DENIAL,
        OfficialConfirmationStatus.OFFICIAL_RETRACTION,
        OfficialConfirmationStatus.OFFICIAL_CORRECTION,
        OfficialConfirmationStatus.OFFICIAL_FINAL_DETERMINATION,
        OfficialConfirmationStatus.OFFICIAL_CONFIRMATION,
        OfficialConfirmationStatus.OFFICIAL_ACKNOWLEDGMENT,
        OfficialConfirmationStatus.OFFICIAL_NONCOMMENT,
        OfficialConfirmationStatus.OFFICIAL_SILENCE,
    ]
    statuses = {report.official_confirmation_status for report in reports}
    for status in priority:
        if status in statuses:
            return status
    return OfficialConfirmationStatus.NO_OFFICIAL_AUTHORITY_PRESENT


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
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name not in {"record_digest", "report_digest"}}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
