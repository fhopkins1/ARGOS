"""EO-INT-001 through EO-INT-009 constitutional Intelligence doctrine.

The Intelligence Office is the only ARGOS gateway for externally acquired
facts. This module implements acquisition contracts, authority resolution,
observation/provenance records, normalization, scheduling, routing, integrity
certification, and audit reconstruction primitives without analysis, risk,
strategy, trading, estimation, or synthetic truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Iterable, Mapping


UNKNOWN = "UNKNOWN"
CONSTITUTIONAL_VERSION = "EO-INT-001..009/1.0.0"


class ConstitutionalViolation(ValueError):
    """Raised when an Intelligence Office boundary is violated."""


class TruthDomain(str, Enum):
    MARKET_PRICES = "MARKET_PRICES"
    TRADE_EXECUTIONS = "TRADE_EXECUTIONS"
    REGULATORY_FILINGS = "REGULATORY_FILINGS"
    CORPORATE_ANNOUNCEMENTS = "CORPORATE_ANNOUNCEMENTS"
    EARNINGS = "EARNINGS"
    ECONOMIC_DATA = "ECONOMIC_DATA"
    MONETARY_POLICY = "MONETARY_POLICY"
    EXCHANGE_CALENDAR = "EXCHANGE_CALENDAR"
    TRADING_HALTS = "TRADING_HALTS"
    CORPORATE_ACTIONS = "CORPORATE_ACTIONS"
    OPTIONS_INFORMATION = "OPTIONS_INFORMATION"
    PORTFOLIO_RECORDS = "PORTFOLIO_RECORDS"
    ACCOUNT_BALANCES = "ACCOUNT_BALANCES"
    CASH_TRANSACTIONS = "CASH_TRANSACTIONS"
    POSITION_COST_BASIS = "POSITION_COST_BASIS"
    NEWS = "NEWS"
    SENTIMENT = "SENTIMENT"
    ANALYST_OPINIONS = "ANALYST_OPINIONS"
    ESG = "ESG"


class AuthorityClass(str, Enum):
    CLASS_I = "CLASS_I_PRIMARY_AUTHORITY"
    CLASS_II = "CLASS_II_OFFICIAL_SECONDARY"
    CLASS_III = "CLASS_III_LICENSED_VENDOR"
    CLASS_IV = "CLASS_IV_INTERNAL_RECORD"
    CLASS_V = "CLASS_V_UNTRUSTED_CONTEXT"


class ObservationState(str, Enum):
    COLLECTING = "COLLECTING"
    COLLECTED = "COLLECTED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"
    QUARANTINED = "QUARANTINED"
    REPLACED = "REPLACED"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"
    CERTIFIED = "CERTIFIED"


class ProvenanceState(str, Enum):
    VALID = "VALID"
    PARTIAL = "PARTIAL"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"
    UNVERIFIED = "UNVERIFIED"
    INVALID = "INVALID"
    CORRUPTED = "CORRUPTED"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"
    QUARANTINED = "QUARANTINED"
    REVOKED = "REVOKED"
    ARCHIVED = "ARCHIVED"


class TriggerClass(str, Enum):
    STARTUP = "STARTUP"
    RECOVERY = "RECOVERY"
    PERIODIC = "PERIODIC"
    EVENT_DRIVEN = "EVENT_DRIVEN"
    WORKFLOW_DRIVEN = "WORKFLOW_DRIVEN"
    VERIFICATION = "VERIFICATION"


class FreshnessStatus(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class RoutingClass(str, Enum):
    CLASS_A = "CLASS_A_IMMEDIATE_MARKET_EVENTS"
    CLASS_B = "CLASS_B_CORPORATE_ACTIONS"
    CLASS_C = "CLASS_C_REGULATORY_EVENTS"
    CLASS_D = "CLASS_D_BROKER_STATE"
    CLASS_E = "CLASS_E_SCHEDULED_INTELLIGENCE"
    CLASS_F = "CLASS_F_OFFICIAL_NEWS"
    CLASS_G = "CLASS_G_REFERENCE_DATA"
    CLASS_H = "CLASS_H_HISTORICAL_DATA"
    CLASS_I = "CLASS_I_DIAGNOSTICS"


class IntegrityState(str, Enum):
    VERIFIED = "VERIFIED"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    MALFORMED = "MALFORMED"
    INCOMPLETE = "INCOMPLETE"
    CORRUPTED = "CORRUPTED"
    DUPLICATE = "DUPLICATE"
    REPLAYED = "REPLAYED"
    UNKNOWN = "UNKNOWN"


class AuditStatus(str, Enum):
    PENDING = "PENDING"
    COLLECTED = "COLLECTED"
    VALIDATED = "VALIDATED"
    NORMALIZED = "NORMALIZED"
    CERTIFIED = "CERTIFIED"
    ARCHIVED = "ARCHIVED"
    REPLAY_VERIFIED = "REPLAY_VERIFIED"
    PARTIALLY_RECONSTRUCTABLE = "PARTIALLY_RECONSTRUCTABLE"
    RECONSTRUCTION_FAILED = "RECONSTRUCTION_FAILED"
    PROVENANCE_FAILED = "PROVENANCE_FAILED"
    ROUTING_FAILED = "ROUTING_FAILED"
    INTEGRITY_FAILED = "INTEGRITY_FAILED"
    QUARANTINED = "QUARANTINED"
    UNKNOWN = "UNKNOWN"


PROHIBITED_AUTHORITIES = frozenset(
    {
        "analysis",
        "indicator",
        "forecast",
        "strategy",
        "risk",
        "order",
        "trade",
        "execution",
        "position",
        "sentiment_interpretation",
        "ranking",
        "learning",
        "self_modification",
        "policy_change",
        "constitution_change",
        "interpolation",
        "estimation",
        "repair",
        "synthetic_observation",
    }
)

OUTPUT_CONTRACTS = (
    "Validated Observation",
    "Canonical Fact",
    "Provenance Record",
    "Integrity Report",
    "Retrieval Evidence",
    "Collection Log",
    "Routing Record",
    "Quarantine Record",
    "Observation Failure",
    "Audit Evidence",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    def convert(item: Any) -> Any:
        if isinstance(item, Enum):
            return item.value
        if isinstance(item, MappingProxyType):
            return dict(item)
        if is_dataclass(item):
            return {field_info.name: convert(getattr(item, field_info.name)) for field_info in fields(item)}
        if isinstance(item, tuple):
            return [convert(part) for part in item]
        if isinstance(item, Mapping):
            return {str(key): convert(val) for key, val in sorted(item.items(), key=lambda kv: str(kv[0]))}
        return item

    return json.dumps(convert(value), sort_keys=True, separators=(",", ":"), default=str)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _identity(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{_digest(parts)[:32]}"


def _immutable_mapping(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(mapping))


def _require_not_unknown(name: str, value: Any) -> None:
    if value in (None, "", UNKNOWN):
        raise ConstitutionalViolation(f"{name} is mandatory and cannot be UNKNOWN")


@dataclass(frozen=True)
class IntelligenceCharter:
    mission: str
    permitted_authority: tuple[str, ...]
    prohibited_authority: tuple[str, ...]
    allowed_inputs: tuple[str, ...]
    output_contracts: tuple[str, ...]
    mandatory_workflow: tuple[str, ...]
    unknown_doctrine: str
    version: str = CONSTITUTIONAL_VERSION


def build_constitutional_charter() -> IntelligenceCharter:
    return IntelligenceCharter(
        mission="External acquisition, validation, normalization, provenance, routing, quarantine, audit, and replay only.",
        permitted_authority=(
            "external_observation",
            "external_retrieval",
            "authority_validation",
            "normalization_without_meaning_change",
            "provenance_assignment",
            "deterministic_routing",
            "quarantine",
            "audit_logging",
            "audit_replay",
        ),
        prohibited_authority=tuple(sorted(PROHIBITED_AUTHORITIES)),
        allowed_inputs=(
            "authorized_collection_request",
            "scheduled_collection_event",
            "approved_trigger",
            "replay_audit_reconstruction",
        ),
        output_contracts=OUTPUT_CONTRACTS,
        mandatory_workflow=(
            "authorize",
            "select_approved_authority",
            "retrieve",
            "verify_authority",
            "validate_completeness_integrity_freshness",
            "normalize",
            "assign_ids_and_provenance",
            "audit",
            "route",
            "archive",
            "deliver",
        ),
        unknown_doctrine="UNKNOWN is mandatory whenever truth cannot be proven; fabrication, inference, estimation, and placeholders are violations.",
    )


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    institution: str
    truth_domains: tuple[TruthDomain, ...]
    authority_class: AuthorityClass
    approval_status: str
    certification_date: str
    review_interval_days: int
    revoked: bool
    api_identifier: str
    api_version: str
    auth_method: str
    licensing: str
    documentation_uri: str
    availability: str
    reliability: str
    retrieval_methods: tuple[str, ...]
    role: str = "PRIMARY"
    registry_version: str = "EO-INT-002/1.0.0"
    caching_permitted: bool = False

    def validate(self) -> None:
        for name in (
            "source_id",
            "institution",
            "approval_status",
            "certification_date",
            "api_identifier",
            "api_version",
            "auth_method",
            "licensing",
            "documentation_uri",
            "availability",
            "reliability",
            "role",
        ):
            _require_not_unknown(name, getattr(self, name))
        if not self.truth_domains or not self.retrieval_methods:
            raise ConstitutionalViolation("source truth domains and retrieval methods are mandatory")
        if self.revoked or self.approval_status != "APPROVED":
            raise ConstitutionalViolation(f"source {self.source_id} is not approved")
        if self.authority_class is AuthorityClass.CLASS_V:
            raise ConstitutionalViolation("Class V sources cannot be constitutional authorities")


@dataclass(frozen=True)
class AuthorityRegistry:
    registry_id: str
    version: str
    sources: tuple[SourceRecord, ...]

    def __post_init__(self) -> None:
        for source in self.sources:
            source.validate()
        primary_by_domain: dict[TruthDomain, str] = {}
        for source in self.sources:
            if source.role != "PRIMARY":
                continue
            for domain in source.truth_domains:
                if domain in primary_by_domain:
                    raise ConstitutionalViolation(f"duplicate primary authority for {domain.value}")
                primary_by_domain[domain] = source.source_id
        missing = set(TruthDomain) - set(primary_by_domain)
        if missing:
            names = ", ".join(sorted(domain.value for domain in missing))
            raise ConstitutionalViolation(f"missing primary authority for {names}")

    def resolve(self, domain: TruthDomain, source_id: str | None = None) -> SourceRecord:
        candidates = [source for source in self.sources if domain in source.truth_domains]
        if source_id is not None:
            candidates = [source for source in candidates if source.source_id == source_id]
        candidates.sort(key=lambda source: (source.authority_class.value, source.role != "PRIMARY", source.source_id))
        if not candidates:
            raise ConstitutionalViolation(f"unknown authority for {domain.value}")
        resolved = candidates[0]
        resolved.validate()
        if source_id is None and resolved.role != "PRIMARY":
            raise ConstitutionalViolation(f"no approved primary authority for {domain.value}")
        return resolved


def default_authority_registry() -> AuthorityRegistry:
    sources = (
        SourceRecord("AUTH-NASDAQ-CTA-PRICE", "NASDAQ UTP / CTA SIP", (TruthDomain.MARKET_PRICES,), AuthorityClass.CLASS_I, "APPROVED", "2026-07-20", 90, False, "sip.market-data", "1", "contracted_api_key", "licensed_market_data", "https://www.nasdaqtrader.com", "market_hours", "authoritative", ("api",), "PRIMARY"),
        SourceRecord("AUTH-BROKER-EXECUTION", "Broker of Record", (TruthDomain.TRADE_EXECUTIONS, TruthDomain.PORTFOLIO_RECORDS, TruthDomain.ACCOUNT_BALANCES, TruthDomain.CASH_TRANSACTIONS, TruthDomain.POSITION_COST_BASIS), AuthorityClass.CLASS_I, "APPROVED", "2026-07-20", 30, False, "broker.account-api", "1", "oauth2", "account_owner", "broker_contract", "continuous", "authoritative_account_record", ("api", "statement"), "PRIMARY"),
        SourceRecord("AUTH-SEC-EDGAR", "U.S. Securities and Exchange Commission EDGAR", (TruthDomain.REGULATORY_FILINGS,), AuthorityClass.CLASS_I, "APPROVED", "2026-07-20", 180, False, "sec.edgar", "1", "public_endpoint", "public_regulatory", "https://www.sec.gov/edgar", "continuous", "authoritative", ("api", "download"), "PRIMARY"),
        SourceRecord("AUTH-CORPORATE-IR", "Issuer Investor Relations", (TruthDomain.CORPORATE_ANNOUNCEMENTS, TruthDomain.EARNINGS, TruthDomain.CORPORATE_ACTIONS, TruthDomain.NEWS), AuthorityClass.CLASS_I, "APPROVED", "2026-07-20", 90, False, "issuer.ir-feed", "1", "public_or_contract", "issuer_publication", "issuer_publication_endpoint", "publication_based", "authoritative_issuer_record", ("api", "web", "rss"), "PRIMARY"),
        SourceRecord("AUTH-BLS-BEA-FRED", "U.S. Economic Data Authorities", (TruthDomain.ECONOMIC_DATA,), AuthorityClass.CLASS_I, "APPROVED", "2026-07-20", 180, False, "economic.authority-feed", "1", "public_endpoint", "public_government", "https://www.bls.gov", "scheduled", "authoritative_government_record", ("api", "download"), "PRIMARY"),
        SourceRecord("AUTH-FEDERAL-RESERVE", "Federal Reserve", (TruthDomain.MONETARY_POLICY,), AuthorityClass.CLASS_I, "APPROVED", "2026-07-20", 180, False, "federalreserve.publications", "1", "public_endpoint", "public_government", "https://www.federalreserve.gov", "scheduled", "authoritative", ("api", "web"), "PRIMARY"),
        SourceRecord("AUTH-NYSE-CALENDAR", "NYSE Market Status and Calendar", (TruthDomain.EXCHANGE_CALENDAR, TruthDomain.TRADING_HALTS), AuthorityClass.CLASS_I, "APPROVED", "2026-07-20", 90, False, "nyse.market-status", "1", "public_or_contract", "exchange_publication", "https://www.nyse.com/markets/hours-calendars", "market_hours", "authoritative_exchange_record", ("api", "web"), "PRIMARY"),
        SourceRecord("AUTH-OCC-OPTIONS", "Options Clearing Corporation", (TruthDomain.OPTIONS_INFORMATION,), AuthorityClass.CLASS_I, "APPROVED", "2026-07-20", 90, False, "occ.options", "1", "contracted_api_key", "licensed_options_data", "https://www.theocc.com", "market_hours", "authoritative_options_record", ("api", "download"), "PRIMARY"),
        SourceRecord("AUTH-NEWSWIRE-OFFICIAL", "Licensed Official Newswire", (TruthDomain.SENTIMENT, TruthDomain.ANALYST_OPINIONS, TruthDomain.ESG), AuthorityClass.CLASS_III, "APPROVED", "2026-07-20", 90, False, "licensed.newswire", "1", "contracted_api_key", "licensed_news", "vendor_contract", "continuous", "licensed_external_record", ("api",), "PRIMARY"),
    )
    return AuthorityRegistry("AIR-EO-INT-002", "EO-INT-002/1.0.0", sources)


@dataclass(frozen=True)
class CollectionRequest:
    request_id: str
    truth_domain: TruthDomain
    trigger: TriggerClass
    workflow_id: str
    source_id: str | None = None
    authorized: bool = True


@dataclass(frozen=True)
class RetrievalEvidence:
    retrieval_session_id: str
    method: str
    endpoint: str
    request_identifier: str
    response_identifier: str
    collection_started_at: str
    retrieval_completed_at: str
    publication_time: str
    effective_time: str
    authority_time: str
    receipt_time: str
    storage_time: str
    transport_status: str
    authentication_status: str
    integrity_status: str
    raw_payload: Mapping[str, Any]
    signature_reference: str = UNKNOWN
    sequence_identifier: str = UNKNOWN

    @property
    def raw_payload_digest(self) -> str:
        return _digest(self.raw_payload)

    @property
    def payload_length(self) -> int:
        return len(_canonical_json(self.raw_payload).encode("utf-8"))


@dataclass(frozen=True)
class ObservationMetadata:
    observation_id: str
    observation_type: str
    authority_domain: TruthDomain
    approved_source_id: str
    retrieval_session_id: str
    collection_method: str
    collection_started_at: str
    retrieval_completed_at: str
    publication_time: str
    effective_time: str
    authority_time: str
    receipt_time: str
    storage_time: str
    observed_object_id: str
    object_classification: str
    raw_payload_digest: str
    canonical_payload_digest: str
    payload_length: int
    transport_status: str
    authentication_status: str
    integrity_status: str
    observation_state: ObservationState
    observation_version: str
    schema_version: str
    workflow_id: str
    certification_eligible: bool
    retention_classification: str


@dataclass(frozen=True)
class Observation:
    metadata: ObservationMetadata
    canonical_payload: Mapping[str, Any]
    lifecycle: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ObservationFailure:
    failure_id: str
    request_id: str
    truth_domain: TruthDomain
    source_id: str
    reason: str
    timestamp_utc: str
    evidence_digest: str
    workflow_id: str


def _contains_forbidden_payload(value: Any) -> bool:
    lowered = _canonical_json(value).lower()
    forbidden = ("placeholder", "dummy", "sample", "demo", "lorem ipsum", "synthetic", "mock", "1970-01-01", "0000-00-00")
    return any(token in lowered for token in forbidden)


def create_observation(request: CollectionRequest, retrieval: RetrievalEvidence, registry: AuthorityRegistry | None = None) -> Observation | ObservationFailure:
    registry = registry or default_authority_registry()
    if not request.authorized:
        return ObservationFailure(_identity("OF", request.request_id, "unauthorized"), request.request_id, request.truth_domain, request.source_id or UNKNOWN, "unauthorized_collection_request", _utc_now(), _digest(retrieval), request.workflow_id)
    try:
        source = registry.resolve(request.truth_domain, request.source_id)
        if request.trigger not in set(TriggerClass):
            raise ConstitutionalViolation("undefined trigger class")
        for name in ("retrieval_session_id", "method", "endpoint", "request_identifier", "collection_started_at", "retrieval_completed_at"):
            _require_not_unknown(name, getattr(retrieval, name))
        if retrieval.transport_status != "PASS" or retrieval.authentication_status != "PASS" or retrieval.integrity_status != "PASS":
            raise ConstitutionalViolation("retrieval transport/authentication/integrity did not pass")
        if _contains_forbidden_payload(retrieval.raw_payload):
            raise ConstitutionalViolation("synthetic or placeholder payload rejected")
        observed_object_id = str(retrieval.raw_payload.get("security_id") or retrieval.raw_payload.get("cusip") or retrieval.raw_payload.get("isin") or retrieval.raw_payload.get("figi") or UNKNOWN)
        _require_not_unknown("observed_object_id", observed_object_id)
        observation_id = _identity(
            "OID",
            source.source_id,
            observed_object_id,
            retrieval.retrieval_session_id,
            retrieval.publication_time,
            request.truth_domain.value,
            retrieval.raw_payload_digest,
        )
        canonical_payload = _immutable_mapping(dict(retrieval.raw_payload))
        metadata = ObservationMetadata(
            observation_id=observation_id,
            observation_type=request.truth_domain.value,
            authority_domain=request.truth_domain,
            approved_source_id=source.source_id,
            retrieval_session_id=retrieval.retrieval_session_id,
            collection_method=retrieval.method,
            collection_started_at=retrieval.collection_started_at,
            retrieval_completed_at=retrieval.retrieval_completed_at,
            publication_time=retrieval.publication_time or UNKNOWN,
            effective_time=retrieval.effective_time or UNKNOWN,
            authority_time=retrieval.authority_time or UNKNOWN,
            receipt_time=retrieval.receipt_time or UNKNOWN,
            storage_time=retrieval.storage_time or UNKNOWN,
            observed_object_id=observed_object_id,
            object_classification=str(retrieval.raw_payload.get("security_type", UNKNOWN)),
            raw_payload_digest=retrieval.raw_payload_digest,
            canonical_payload_digest=_digest(canonical_payload),
            payload_length=retrieval.payload_length,
            transport_status=retrieval.transport_status,
            authentication_status=retrieval.authentication_status,
            integrity_status=retrieval.integrity_status,
            observation_state=ObservationState.COLLECTED,
            observation_version="EO-INT-003/1.0.0",
            schema_version="EO-INT-003/observation/1.0.0",
            workflow_id=request.workflow_id,
            certification_eligible=True,
            retention_classification="CERTIFICATION_EVIDENCE",
        )
        return Observation(metadata, canonical_payload, ({"state": ObservationState.COLLECTED.value, "timestamp": _utc_now(), "reason": "external_authority_collection"},))
    except ConstitutionalViolation as exc:
        return ObservationFailure(_identity("OF", request.request_id, str(exc)), request.request_id, request.truth_domain, request.source_id or UNKNOWN, str(exc), _utc_now(), retrieval.raw_payload_digest, request.workflow_id)


@dataclass(frozen=True)
class CustodyEvent:
    event_id: str
    responsible_office: str
    workflow_token: str
    timestamp_utc: str
    artifact_hashes: tuple[str, ...]
    previous_hash: str
    new_hash: str
    authorization: str
    reason: str


@dataclass(frozen=True)
class ProvenanceRecord:
    provenance_id: str
    observation_id: str
    source_id: str
    authority_domain: TruthDomain
    retrieval_session_id: str
    retrieval_method: str
    retrieval_parameters_digest: str
    temporal_provenance: Mapping[str, str]
    raw_retrieval_evidence_digest: str
    signature_reference: str
    custody_events: tuple[CustodyEvent, ...]
    state: ProvenanceState
    registry_version: str


def build_provenance_record(observation: Observation, retrieval: RetrievalEvidence, registry: AuthorityRegistry | None = None) -> ProvenanceRecord:
    registry = registry or default_authority_registry()
    source = registry.resolve(observation.metadata.authority_domain, observation.metadata.approved_source_id)
    state = ProvenanceState.VALID
    if retrieval.signature_reference == UNKNOWN:
        state = ProvenanceState.UNVERIFIED
    if observation.metadata.raw_payload_digest != retrieval.raw_payload_digest:
        state = ProvenanceState.CORRUPTED
    custody = CustodyEvent(
        _identity("CUST", observation.metadata.observation_id, retrieval.retrieval_session_id),
        "Intelligence Office",
        observation.metadata.workflow_id,
        _utc_now(),
        (observation.metadata.raw_payload_digest, observation.metadata.canonical_payload_digest),
        UNKNOWN,
        _digest((observation.metadata.observation_id, retrieval.raw_payload_digest)),
        "authorized_collection_request",
        "initial_external_retrieval",
    )
    return ProvenanceRecord(
        _identity("PROV", observation.metadata.observation_id, source.source_id, retrieval.retrieval_session_id),
        observation.metadata.observation_id,
        source.source_id,
        observation.metadata.authority_domain,
        retrieval.retrieval_session_id,
        retrieval.method,
        _digest({"endpoint": retrieval.endpoint, "request": retrieval.request_identifier}),
        _immutable_mapping(
            {
                "collection_started_at": retrieval.collection_started_at,
                "retrieval_completed_at": retrieval.retrieval_completed_at,
                "publication_time": retrieval.publication_time or UNKNOWN,
                "effective_time": retrieval.effective_time or UNKNOWN,
                "receipt_time": retrieval.receipt_time or UNKNOWN,
            }
        ),
        retrieval.raw_payload_digest,
        retrieval.signature_reference,
        (custody,),
        state,
        registry.version,
    )


def append_custody_event(provenance: ProvenanceRecord, event: CustodyEvent) -> ProvenanceRecord:
    return ProvenanceRecord(
        provenance.provenance_id,
        provenance.observation_id,
        provenance.source_id,
        provenance.authority_domain,
        provenance.retrieval_session_id,
        provenance.retrieval_method,
        provenance.retrieval_parameters_digest,
        provenance.temporal_provenance,
        provenance.raw_retrieval_evidence_digest,
        provenance.signature_reference,
        provenance.custody_events + (event,),
        provenance.state,
        provenance.registry_version,
    )


@dataclass(frozen=True)
class FactSchema:
    schema_id: str
    version: str
    effective_date: str
    retirement_date: str
    compatibility_rules: tuple[str, ...]
    migration_rules: tuple[str, ...]
    required_fields: tuple[str, ...]


def default_schema_registry() -> Mapping[str, FactSchema]:
    schema_names = (
        "Market Price",
        "Trade Execution",
        "Quote",
        "Corporate Action",
        "Dividend",
        "Split",
        "Exchange Status",
        "Trading Halt",
        "Regulatory Filing",
        "Economic Indicator",
        "Broker Position",
        "Portfolio Balance",
        "Order Status",
        "Options Chain",
        "News Publication",
        "Sentiment Observation",
    )
    return _immutable_mapping(
        {
            name: FactSchema(
                _identity("SCHEMA", name),
                "1.0.0",
                "2026-07-20",
                UNKNOWN,
                ("historical_facts_remain_on_original_schema",),
                ("migration_replay_only_no_history_rewrite",),
                ("security_id", "publication_time", "effective_time"),
            )
            for name in schema_names
        }
    )


EXCHANGE_ALIASES = MappingProxyType({"NYSE": "XNYS", "NASDAQ": "XNAS", "CBOE": "XCBO", "CME": "XCME", "ICE": "IFUS", "OTC": "OOTC"})
CURRENCY_CODES = frozenset({"USD", "EUR", "JPY", "GBP", "CHF", "CAD"})
UNIT_CODES = frozenset({"shares", "contracts", "percent", "basis_points", "USD", "USD/share", "milliseconds", "seconds"})


@dataclass(frozen=True)
class CanonicalFact:
    fact_id: str
    observation_id: str
    source_observation_id: str
    source_authority: str
    authority_domain: TruthDomain
    canonical_security_identifier: str
    security_type: str
    exchange: str
    market_identifier: str
    ticker: str
    primary_listing: str
    observation_time: str
    publication_time: str
    effective_time: str
    retrieval_time: str
    price: Any
    currency: str
    quantity: Any
    unit: str
    precision: str
    provenance_record: str
    retrieval_record: str
    authority_record: str
    normalization_record: str
    validation_status: str
    completeness_status: str
    duplicate_status: str
    conflict_status: str
    schema_id: str
    schema_version: str


def normalize_observation(observation: Observation, provenance: ProvenanceRecord, schemas: Mapping[str, FactSchema] | None = None) -> CanonicalFact:
    if observation.metadata.observation_state not in (ObservationState.COLLECTED, ObservationState.CERTIFIED):
        raise ConstitutionalViolation("only collected observations can be normalized")
    if provenance.state not in (ProvenanceState.VALID, ProvenanceState.UNVERIFIED):
        raise ConstitutionalViolation("invalid provenance cannot be normalized")
    payload = dict(observation.canonical_payload)
    identifier = payload.get("cusip") or payload.get("isin") or payload.get("figi") or payload.get("sedol") or payload.get("exchange_symbol") or payload.get("ticker") or UNKNOWN
    if identifier == UNKNOWN:
        raise ConstitutionalViolation("canonical security identifier cannot be determined")
    exchange_original = str(payload.get("exchange", UNKNOWN)).upper()
    exchange = EXCHANGE_ALIASES.get(exchange_original, exchange_original if exchange_original != "UNKNOWN" else UNKNOWN)
    currency = str(payload.get("currency", UNKNOWN)).upper()
    if currency != UNKNOWN and currency not in CURRENCY_CODES:
        raise ConstitutionalViolation("invalid currency code")
    unit = str(payload.get("unit", UNKNOWN))
    if unit != UNKNOWN and unit not in UNIT_CODES:
        raise ConstitutionalViolation("invalid unit code")
    schema_name = str(payload.get("schema", "Market Price"))
    schema = (schemas or default_schema_registry()).get(schema_name)
    if schema is None:
        raise ConstitutionalViolation("missing canonical schema")
    conflict_status = "PASS"
    if payload.get("ticker_conflict") or payload.get("identifier_conflict"):
        conflict_status = "CONFLICT"
        identifier = "UNKNOWN_SECURITY"
    completeness_status = "PASS" if all(payload.get(field, UNKNOWN) != UNKNOWN for field in schema.required_fields) else "INVALID"
    fact_id = _identity("FACT", observation.metadata.observation_id, identifier, schema.schema_id, provenance.provenance_id)
    return CanonicalFact(
        fact_id,
        observation.metadata.observation_id,
        observation.metadata.observation_id,
        observation.metadata.approved_source_id,
        observation.metadata.authority_domain,
        str(identifier),
        str(payload.get("security_type", UNKNOWN)),
        exchange,
        str(payload.get("market_identifier", exchange)),
        str(payload.get("ticker", UNKNOWN)).upper() if payload.get("ticker") else UNKNOWN,
        str(payload.get("primary_listing", UNKNOWN)),
        observation.metadata.receipt_time,
        observation.metadata.publication_time,
        observation.metadata.effective_time,
        observation.metadata.retrieval_completed_at,
        payload.get("price", UNKNOWN),
        currency,
        payload.get("quantity", UNKNOWN),
        unit,
        str(payload.get("precision", UNKNOWN)),
        provenance.provenance_id,
        observation.metadata.retrieval_session_id,
        observation.metadata.approved_source_id,
        _identity("NORM", observation.metadata.observation_id, schema.schema_id),
        "PASS" if completeness_status == "PASS" and conflict_status == "PASS" else "FAIL",
        completeness_status,
        "UNIQUE",
        conflict_status,
        schema.schema_id,
        schema.version,
    )


@dataclass(frozen=True)
class ScheduleRule:
    rule_id: str
    authority_domain: TruthDomain
    source_id: str
    trigger_type: TriggerClass
    polling_interval_seconds: int
    preferred_freshness_seconds: int
    maximum_freshness_seconds: int
    expiration_threshold_seconds: int
    retry_policy: tuple[int, ...]
    escalation_policy: str
    market_session_applicability: tuple[str, ...]
    cost_tier: int
    workflow_authorization_required: bool
    rule_version: str
    evidence_reference: str


@dataclass(frozen=True)
class ScheduleRecord:
    schedule_id: str
    trigger: TriggerClass
    authority_domain: TruthDomain
    source_id: str
    reason: str
    collection_time: str
    expected_freshness: FreshnessStatus
    observed_freshness: FreshnessStatus
    result: str
    workflow_id: str
    evidence_reference: str
    retry_count: int
    cost_tier: int
    market_session: str
    rule_version: str
    outcome: str


def evaluate_schedule(rule: ScheduleRule, *, trigger: TriggerClass, workflow_id: str, market_session: str, retry_count: int = 0, now_utc: str | None = None) -> ScheduleRecord:
    if trigger is not rule.trigger_type:
        raise ConstitutionalViolation("schedule trigger does not match rule")
    if market_session not in rule.market_session_applicability:
        outcome = "SUPPRESSED_MARKET_SESSION"
    elif retry_count > len(rule.retry_policy):
        outcome = "FAILED_MAX_RETRIES"
    else:
        outcome = "COLLECT"
    return ScheduleRecord(
        _identity("SCHED", rule.rule_id, trigger.value, workflow_id, retry_count, now_utc or _utc_now()),
        trigger,
        rule.authority_domain,
        rule.source_id,
        "deterministic_rule_evaluation",
        now_utc or _utc_now(),
        FreshnessStatus.CURRENT,
        FreshnessStatus.UNKNOWN,
        "AUTHORIZED" if outcome == "COLLECT" else "NOT_COLLECTED",
        workflow_id,
        rule.evidence_reference,
        retry_count,
        rule.cost_tier,
        market_session,
        rule.rule_version,
        outcome,
    )


ROUTING_BY_DOMAIN = MappingProxyType(
    {
        TruthDomain.MARKET_PRICES: RoutingClass.CLASS_A,
        TruthDomain.TRADE_EXECUTIONS: RoutingClass.CLASS_A,
        TruthDomain.EXCHANGE_CALENDAR: RoutingClass.CLASS_A,
        TruthDomain.TRADING_HALTS: RoutingClass.CLASS_A,
        TruthDomain.CORPORATE_ACTIONS: RoutingClass.CLASS_B,
        TruthDomain.REGULATORY_FILINGS: RoutingClass.CLASS_C,
        TruthDomain.PORTFOLIO_RECORDS: RoutingClass.CLASS_D,
        TruthDomain.ACCOUNT_BALANCES: RoutingClass.CLASS_D,
        TruthDomain.CASH_TRANSACTIONS: RoutingClass.CLASS_D,
        TruthDomain.POSITION_COST_BASIS: RoutingClass.CLASS_D,
        TruthDomain.EARNINGS: RoutingClass.CLASS_E,
        TruthDomain.ECONOMIC_DATA: RoutingClass.CLASS_E,
        TruthDomain.MONETARY_POLICY: RoutingClass.CLASS_E,
        TruthDomain.CORPORATE_ANNOUNCEMENTS: RoutingClass.CLASS_F,
        TruthDomain.NEWS: RoutingClass.CLASS_F,
        TruthDomain.OPTIONS_INFORMATION: RoutingClass.CLASS_H,
        TruthDomain.SENTIMENT: RoutingClass.CLASS_G,
        TruthDomain.ANALYST_OPINIONS: RoutingClass.CLASS_G,
        TruthDomain.ESG: RoutingClass.CLASS_G,
    }
)


@dataclass(frozen=True)
class RoutingRecord:
    routing_record_id: str
    observation_id: str
    destination: str
    routing_timestamp: str
    routing_version: str
    delivery_priority: int
    workflow_trigger_decision: str
    sentinel_wake_decision: str
    archive_decision: str
    notification_decision: str
    retry_policy: tuple[int, ...]
    delivery_evidence: str
    routing_certification: str
    routing_class: RoutingClass


def route_fact(fact: CanonicalFact, integrity_state: IntegrityState, provenance: ProvenanceRecord, *, policy_version: str = "EO-INT-007/1.0.0") -> RoutingRecord:
    if integrity_state not in (IntegrityState.VERIFIED, IntegrityState.DEGRADED):
        raise ConstitutionalViolation("routing denied until integrity passes")
    if provenance.state not in (ProvenanceState.VALID, ProvenanceState.UNVERIFIED):
        raise ConstitutionalViolation("routing denied until provenance passes")
    routing_class = ROUTING_BY_DOMAIN[fact.authority_domain]
    archive_classes = {RoutingClass.CLASS_G, RoutingClass.CLASS_H, RoutingClass.CLASS_I}
    destination = "Archive" if routing_class in archive_classes else "Sentinel"
    sentinel_wake = "WAKE" if destination == "Sentinel" else "DO_NOT_WAKE"
    priority = {
        RoutingClass.CLASS_A: 1,
        RoutingClass.CLASS_D: 1,
        RoutingClass.CLASS_B: 2,
        RoutingClass.CLASS_C: 2,
        RoutingClass.CLASS_E: 2,
        RoutingClass.CLASS_F: 2,
        RoutingClass.CLASS_G: 3,
        RoutingClass.CLASS_H: 4,
        RoutingClass.CLASS_I: 5,
    }[routing_class]
    return RoutingRecord(
        _identity("ROUTE", fact.observation_id, destination, policy_version),
        fact.observation_id,
        destination,
        _utc_now(),
        policy_version,
        priority,
        "CREATE_WORKFLOW" if destination == "Sentinel" else "NO_WORKFLOW",
        sentinel_wake,
        "ARCHIVE_COPY_REQUIRED",
        "NOTIFY" if destination == "Sentinel" else "NO_NOTIFICATION",
        (5, 15, 45),
        _identity("DELIVERY", fact.observation_id, destination),
        "CERTIFIED",
        routing_class,
    )


@dataclass(frozen=True)
class QuarantineRecord:
    quarantine_id: str
    observation_id: str
    reason: str
    validator: str
    rule_version: str
    timestamp_utc: str
    payload_hash: str
    workflow_id: str
    authority: str
    provenance: str
    retrieval_evidence: str
    constitutional_violation: str
    validator_version: str


def evaluate_integrity(
    observation: Observation,
    provenance: ProvenanceRecord,
    *,
    known_observation_ids: Iterable[str] = (),
    known_payload_hashes: Iterable[str] = (),
    freshness: FreshnessStatus = FreshnessStatus.CURRENT,
) -> tuple[IntegrityState, tuple[Mapping[str, Any], ...], QuarantineRecord | None]:
    stages: list[Mapping[str, Any]] = []
    state = IntegrityState.VERIFIED
    reason = ""
    checks = (
        ("Transport Integrity Verification", observation.metadata.transport_status == "PASS", IntegrityState.CORRUPTED),
        ("Payload Completeness Verification", observation.metadata.payload_length > 0, IntegrityState.INCOMPLETE),
        ("Schema Validation", observation.metadata.schema_version != UNKNOWN, IntegrityState.MALFORMED),
        ("Authority Validation", observation.metadata.approved_source_id != UNKNOWN, IntegrityState.UNKNOWN),
        ("Provenance Validation", provenance.state in (ProvenanceState.VALID, ProvenanceState.UNVERIFIED), IntegrityState.UNKNOWN),
        ("Timestamp Validation", observation.metadata.retrieval_completed_at != UNKNOWN, IntegrityState.MALFORMED),
        ("Identifier Validation", observation.metadata.observed_object_id != UNKNOWN, IntegrityState.MALFORMED),
        ("Normalization Validation", observation.metadata.canonical_payload_digest != UNKNOWN, IntegrityState.MALFORMED),
        ("Freshness Validation", freshness is not FreshnessStatus.EXPIRED, IntegrityState.STALE),
        ("Duplicate Detection", observation.metadata.observation_id not in set(known_observation_ids), IntegrityState.DUPLICATE),
        ("Replay Detection", observation.metadata.raw_payload_digest not in set(known_payload_hashes), IntegrityState.REPLAYED),
        ("Synthetic Truth Detection", not _contains_forbidden_payload(observation.canonical_payload), IntegrityState.MALFORMED),
        ("Placeholder Detection", not _contains_forbidden_payload(observation.canonical_payload), IntegrityState.MALFORMED),
        ("Integrity Certification", True, IntegrityState.UNKNOWN),
    )
    for stage, passed, failure_state in checks:
        stages.append(_immutable_mapping({"stage": stage, "result": "PASS" if passed else "FAIL", "rule_version": "EO-INT-008/1.0.0"}))
        if not passed:
            state = failure_state
            reason = stage
            break
    if state is IntegrityState.VERIFIED:
        return state, tuple(stages), None
    quarantine = QuarantineRecord(
        _identity("QUAR", observation.metadata.observation_id, state.value, reason),
        observation.metadata.observation_id,
        reason,
        "INT-008 Integrity Engine",
        "EO-INT-008/1.0.0",
        _utc_now(),
        observation.metadata.raw_payload_digest,
        observation.metadata.workflow_id,
        observation.metadata.approved_source_id,
        provenance.provenance_id,
        observation.metadata.retrieval_session_id,
        state.value,
        "EO-INT-008/1.0.0",
    )
    return state, tuple(stages), quarantine


@dataclass(frozen=True)
class AuditRecord:
    audit_record_id: str
    observation_id: str
    provenance_id: str
    routing_id: str
    workflow_id: str
    collection_session_id: str
    authority_domain: TruthDomain
    authority_registry_id: str
    source_identifier: str
    source_class: AuthorityClass
    authority_approval_version: str
    collection_timestamp: str
    publication_timestamp: str
    effective_timestamp: str
    retrieval_completion_timestamp: str
    retrieval_method: str
    collector_identity: str
    endpoint_or_retrieval_location: str
    request_identifier: str
    response_identifier: str
    integrity_status: IntegrityState
    validation_result: str
    schema_validation_result: str
    signature_validation_result: str
    hash_verification_result: str
    duplicate_detection_result: str
    replay_detection_result: str
    original_payload_digest: str
    canonical_payload_digest: str
    canonical_schema_version: str
    normalization_version: str
    destination_office: str
    routing_decision: str
    routing_rule_version: str
    trigger_classification: str
    wake_condition_identifier: str
    certification_status: AuditStatus
    certification_time: str
    certification_workflow: str
    certification_rule_version: str
    evidence_manifest: Mapping[str, Any]
    archived_payload_references: tuple[str, ...]
    hashes: tuple[str, ...]
    signature_references: tuple[str, ...]
    external_references: tuple[str, ...]
    lineage: tuple[Mapping[str, Any], ...]


def build_audit_record(
    observation: Observation,
    provenance: ProvenanceRecord,
    fact: CanonicalFact,
    routing: RoutingRecord,
    integrity_state: IntegrityState,
    retrieval: RetrievalEvidence,
    registry: AuthorityRegistry | None = None,
) -> AuditRecord:
    registry = registry or default_authority_registry()
    source = registry.resolve(observation.metadata.authority_domain, observation.metadata.approved_source_id)
    if integrity_state not in (IntegrityState.VERIFIED, IntegrityState.DEGRADED):
        raise ConstitutionalViolation("certification evidence requires passing integrity")
    if routing.destination == UNKNOWN:
        raise ConstitutionalViolation("certification evidence requires verified routing")
    lineage_names = (
        "External Authority",
        "Collection",
        "Raw Observation",
        "Validation",
        "Normalization",
        "Integrity Verification",
        "Routing Decision",
        "Sentinel" if routing.destination == "Sentinel" else "Archive",
        "Certification",
        "Historical Archive",
    )
    lineage = tuple(
        _immutable_mapping(
            {
                "node": name,
                "timestamp": _utc_now(),
                "workflow": observation.metadata.workflow_id,
                "authority": source.source_id,
                "rule_version": CONSTITUTIONAL_VERSION,
                "evidence_reference": _identity("EDGE", observation.metadata.observation_id, name),
            }
        )
        for name in lineage_names
    )
    manifest = _immutable_mapping(
        {
            "observation_id": observation.metadata.observation_id,
            "provenance_id": provenance.provenance_id,
            "fact_id": fact.fact_id,
            "routing_id": routing.routing_record_id,
            "registry_version": registry.version,
            "schema_version": fact.schema_version,
        }
    )
    return AuditRecord(
        _identity("AUDIT", observation.metadata.observation_id, provenance.provenance_id, routing.routing_record_id),
        observation.metadata.observation_id,
        provenance.provenance_id,
        routing.routing_record_id,
        observation.metadata.workflow_id,
        retrieval.retrieval_session_id,
        observation.metadata.authority_domain,
        registry.registry_id,
        source.source_id,
        source.authority_class,
        source.registry_version,
        retrieval.collection_started_at,
        retrieval.publication_time or UNKNOWN,
        retrieval.effective_time or UNKNOWN,
        retrieval.retrieval_completed_at,
        retrieval.method,
        "Intelligence Office",
        retrieval.endpoint,
        retrieval.request_identifier,
        retrieval.response_identifier,
        integrity_state,
        "PASS",
        "PASS",
        "UNKNOWN" if retrieval.signature_reference == UNKNOWN else "PASS",
        "PASS",
        "UNIQUE",
        "NOT_REPLAYED",
        observation.metadata.raw_payload_digest,
        fact.fact_id,
        fact.schema_version,
        "EO-INT-005/1.0.0",
        routing.destination,
        routing.routing_class.value,
        routing.routing_version,
        retrieval.sequence_identifier,
        routing.sentinel_wake_decision,
        AuditStatus.CERTIFIED,
        _utc_now(),
        observation.metadata.workflow_id,
        CONSTITUTIONAL_VERSION,
        manifest,
        (observation.metadata.raw_payload_digest, fact.fact_id),
        (observation.metadata.raw_payload_digest, observation.metadata.canonical_payload_digest, fact.fact_id),
        (retrieval.signature_reference,),
        (retrieval.endpoint,),
        lineage,
    )


def export_audit_package(records: Iterable[AuditRecord]) -> Mapping[str, Any]:
    material = tuple(records)
    payload = {
        "package_type": "ARGOS_INTELLIGENCE_AUDIT_EXPORT",
        "constitutional_version": CONSTITUTIONAL_VERSION,
        "audit_records": material,
        "replay_instructions": (
            "metadata_replay",
            "evidence_replay",
            "full_constitutional_replay",
            "rule_migration_replay_no_history_rewrite",
        ),
    }
    return _immutable_mapping({**payload, "package_digest": _digest(payload)})
