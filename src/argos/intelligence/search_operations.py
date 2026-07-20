"""MO-SP-011/012/013 search resource, failure, and evidence governance."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp
from argos.intelligence.source_registry import SourceAuthorizationGateway, SourceAuthorizationRequest


MO_SP_011_VERSION = "MO-SP-011/1.0.0"
MO_SP_012_VERSION = "MO-SP-012/1.0.0"
MO_SP_013_VERSION = "MO-SP-013/1.0.0"


class SearchPriority(str, Enum):
    P0_PORTFOLIO_EXECUTION_SAFETY = "P0"
    P1_HALTS_RESTRICTIONS = "P1"
    P2_TIME_SENSITIVE_EVENTS = "P2"
    P3_ACTIVE_TRADE_INVESTIGATIONS = "P3"
    P4_SCHEDULED_EVENTS = "P4"
    P5_BROAD_MARKET_MONITORING = "P5"
    P6_BACKGROUND_RESEARCH = "P6"
    P7_HISTORICAL_ENRICHMENT = "P7"


class SearchCostClass(str, Enum):
    C0_ZERO_MARGINAL = "C0"
    C1_NEGLIGIBLE_METERED = "C1"
    C2_STANDARD_METERED = "C2"
    C3_ELEVATED = "C3"
    C4_EXCEPTIONAL = "C4"
    C5_HUMAN_APPROVAL = "C5"
    UNKNOWN = "UNKNOWN"


class BudgetOutcome(str, Enum):
    AUTHORIZED_CACHE_HIT = "AUTHORIZED_CACHE_HIT"
    AUTHORIZED_EXTERNAL_RETRIEVAL = "AUTHORIZED_EXTERNAL_RETRIEVAL"
    AUTHORIZED_BATCHED_RETRIEVAL = "AUTHORIZED_BATCHED_RETRIEVAL"
    AUTHORIZED_SAFETY_OVERRIDE = "AUTHORIZED_SAFETY_OVERRIDE"
    DEFERRED_PRIORITY = "DEFERRED_PRIORITY"
    DEFERRED_BUDGET = "DEFERRED_BUDGET"
    BLOCKED_OFFICE_BUDGET = "BLOCKED_OFFICE_BUDGET"
    BLOCKED_WORKFLOW_BUDGET = "BLOCKED_WORKFLOW_BUDGET"
    BLOCKED_DAILY_BUDGET = "BLOCKED_DAILY_BUDGET"
    BLOCKED_MONTHLY_BUDGET = "BLOCKED_MONTHLY_BUDGET"
    BLOCKED_PROVIDER_QUOTA = "BLOCKED_PROVIDER_QUOTA"
    BLOCKED_COST_CLASS = "BLOCKED_COST_CLASS"
    ESCALATED_HUMAN_APPROVAL = "ESCALATED_HUMAN_APPROVAL"
    ESCALATED_SAFETY_RESERVE = "ESCALATED_SAFETY_RESERVE"
    TRADE_BLOCKING_RESOURCE_FAILURE = "TRADE_BLOCKING_RESOURCE_FAILURE"
    REJECTED_UNCLASSIFIED_COST = "REJECTED_UNCLASSIFIED_COST"
    REJECTED_UNAUTHORIZED_PRIORITY = "REJECTED_UNAUTHORIZED_PRIORITY"
    REJECTED_UNAUTHORIZED_SOURCE = "REJECTED_UNAUTHORIZED_SOURCE"
    REJECTED_UNAUTHORIZED_SEARCH_PLAN = "REJECTED_UNAUTHORIZED_SEARCH_PLAN"


class CacheStatus(str, Enum):
    NOT_USED = "NOT_USED"
    HIT = "HIT"
    MISS = "MISS"
    REFRESHED = "REFRESHED"
    STALE_USED = "STALE_USED"
    STALE_REJECTED = "STALE_REJECTED"
    CORRUPT = "CORRUPT"


class FailureSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WorkflowFailureState(str, Enum):
    NORMAL = "Normal"
    WAITING = "Waiting"
    RETRYING = "Retrying"
    DEFERRED = "Deferred"
    PAUSED = "Paused"
    SOURCE_UNAVAILABLE = "SourceUnavailable"
    PROVIDER_UNAVAILABLE = "ProviderUnavailable"
    EVIDENCE_INCOMPLETE = "EvidenceIncomplete"
    EVIDENCE_CONFLICTED = "EvidenceConflicted"
    CACHE_AUTHORIZED = "CacheAuthorized"
    CACHE_EXPIRED = "CacheExpired"
    ESCALATED = "Escalated"
    HUMAN_REVIEW_REQUIRED = "HumanReviewRequired"
    TRADE_BLOCKED = "TradeBlocked"
    RECOVERED = "Recovered"
    CANCELLED = "Cancelled"
    ABORTED = "Aborted"
    COMPLETED_WITH_EXCEPTIONS = "CompletedWithExceptions"


class SearchFailureClass(str, Enum):
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    DNS_FAILURE = "DNS_FAILURE"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    CONNECTION_REFUSED = "CONNECTION_REFUSED"
    TLS_FAILURE = "TLS_FAILURE"
    AUTHENTICATION_FAILURE = "AUTHENTICATION_FAILURE"
    AUTHORIZATION_FAILURE = "AUTHORIZATION_FAILURE"
    EXPIRED_CREDENTIALS = "EXPIRED_CREDENTIALS"
    SUBSCRIPTION_FAILURE = "SUBSCRIPTION_FAILURE"
    LICENSE_EXPIRATION = "LICENSE_EXPIRATION"
    API_QUOTA_EXCEEDED = "API_QUOTA_EXCEEDED"
    RATE_LIMITING = "RATE_LIMITING"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    CORRUPTED_PAYLOAD = "CORRUPTED_PAYLOAD"
    CHECKSUM_FAILURE = "CHECKSUM_FAILURE"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    FIELD_MISSING = "FIELD_MISSING"
    REQUIRED_FIELD_NULL = "REQUIRED_FIELD_NULL"
    INCOMPLETE_RESPONSE = "INCOMPLETE_RESPONSE"
    PARTIAL_DATASET = "PARTIAL_DATASET"
    UNEXPECTED_TRUNCATION = "UNEXPECTED_TRUNCATION"
    DUPLICATE_RESPONSE = "DUPLICATE_RESPONSE"
    DELAYED_PUBLICATION = "DELAYED_PUBLICATION"
    STALE_RESPONSE = "STALE_RESPONSE"
    PUBLICATION_WITHDRAWN = "PUBLICATION_WITHDRAWN"
    DOCUMENT_REMOVED = "DOCUMENT_REMOVED"
    CHANGED_URL = "CHANGED_URL"
    CHANGED_API_SCHEMA = "CHANGED_API_SCHEMA"
    BROKEN_PARSER = "BROKEN_PARSER"
    UNSUPPORTED_ENDPOINT = "UNSUPPORTED_ENDPOINT"
    UNSUPPORTED_ASSET = "UNSUPPORTED_ASSET"
    UNSUPPORTED_EXCHANGE = "UNSUPPORTED_EXCHANGE"
    UNSUPPORTED_JURISDICTION = "UNSUPPORTED_JURISDICTION"
    CONFLICTING_IDENTIFIERS = "CONFLICTING_IDENTIFIERS"
    BROKER_OUTAGE = "BROKER_OUTAGE"
    EXCHANGE_OUTAGE = "EXCHANGE_OUTAGE"
    MARKET_DATA_PROVIDER_OUTAGE = "MARKET_DATA_PROVIDER_OUTAGE"
    GOVERNMENT_SOURCE_OUTAGE = "GOVERNMENT_SOURCE_OUTAGE"
    LOSS_OF_INTERNET_CONNECTIVITY = "LOSS_OF_INTERNET_CONNECTIVITY"
    CACHE_CORRUPTION = "CACHE_CORRUPTION"
    EVIDENCE_STORAGE_FAILURE = "EVIDENCE_STORAGE_FAILURE"
    PROVENANCE_RECORDING_FAILURE = "PROVENANCE_RECORDING_FAILURE"
    MULTI_SOURCE_SYSTEMIC_FAILURE = "MULTI_SOURCE_SYSTEMIC_FAILURE"


class SearchEvidenceCertificationStatus(str, Enum):
    CERTIFIED = "CERTIFIED"
    INVALID = "INVALID"
    AUTHORIZATION_REJECTED = "AUTHORIZATION_REJECTED"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"


@dataclass(frozen=True)
class GovernedSearchRequest:
    request_id: str
    search_plan_id: str
    source_id: str
    provider_id: str
    requesting_office: str
    workflow_id: str
    decision_object_id: str
    workflow_execution_token_id: str
    environment: str
    asset_class: str
    identifiers: Mapping[str, str]
    fact_type: str
    retrieval_purpose: str
    query_fingerprint: str
    parameters: Mapping[str, str]
    requested_time_range: tuple[str, str]
    requested_freshness_seconds: int
    priority_class: SearchPriority
    cost_class: SearchCostClass
    estimated_cost_units: int
    cache_policy_id: str
    cache_isolation_scope: str
    deduplication_policy_id: str
    batch_eligible: bool
    fallback_eligible: bool
    safety_critical: bool
    created_at: str
    expires_at: str
    evidence_retention_classification: str


@dataclass(frozen=True)
class CacheEntry:
    cache_entry_id: str
    source_id: str
    provider_id: str
    search_plan_id: str
    canonical_query_fingerprint: str
    normalized_request_parameters: Mapping[str, str]
    fact_type: str
    entity_identifiers: Mapping[str, str]
    requested_time_range: tuple[str, str]
    retrieval_timestamp: str
    freshness_deadline: str
    hard_expiration_timestamp: str
    invalidation_tags: tuple[str, ...]
    environment: str
    cache_isolation_scope: str
    provenance_reference: str
    raw_evidence_reference: str
    response_digest: str
    stale_status: CacheStatus
    cost_avoided_units: int


@dataclass
class SearchBudgetLedger:
    workflow_limit: int = 100
    office_limit: int = 500
    daily_limit: int = 2000
    monthly_limit: int = 10000
    provider_quota: int = 1000
    safety_reserve: int = 200
    workflow_used: dict[str, int] = field(default_factory=dict)
    office_used: dict[str, int] = field(default_factory=dict)
    daily_used: int = 0
    monthly_used: int = 0
    provider_used: dict[str, int] = field(default_factory=dict)
    safety_used: int = 0

    def reserve(self, request: GovernedSearchRequest) -> BudgetOutcome:
        cost = request.estimated_cost_units
        if request.cost_class is SearchCostClass.UNKNOWN:
            return BudgetOutcome.REJECTED_UNCLASSIFIED_COST
        if request.cost_class is SearchCostClass.C5_HUMAN_APPROVAL:
            return BudgetOutcome.ESCALATED_HUMAN_APPROVAL
        if request.cost_class is SearchCostClass.C4_EXCEPTIONAL and not request.safety_critical:
            return BudgetOutcome.BLOCKED_COST_CLASS
        if self.workflow_used.get(request.workflow_id, 0) + cost > self.workflow_limit:
            return BudgetOutcome.BLOCKED_WORKFLOW_BUDGET
        if self.office_used.get(request.requesting_office, 0) + cost > self.office_limit:
            return BudgetOutcome.BLOCKED_OFFICE_BUDGET
        if self.provider_used.get(request.provider_id, 0) + cost > self.provider_quota:
            return BudgetOutcome.BLOCKED_PROVIDER_QUOTA
        if self.daily_used + cost > self.daily_limit:
            if request.priority_class in {SearchPriority.P0_PORTFOLIO_EXECUTION_SAFETY, SearchPriority.P1_HALTS_RESTRICTIONS} and self.safety_used + cost <= self.safety_reserve:
                self.safety_used += cost
                return BudgetOutcome.AUTHORIZED_SAFETY_OVERRIDE
            return BudgetOutcome.BLOCKED_DAILY_BUDGET
        if self.monthly_used + cost > self.monthly_limit:
            return BudgetOutcome.BLOCKED_MONTHLY_BUDGET
        self.workflow_used[request.workflow_id] = self.workflow_used.get(request.workflow_id, 0) + cost
        self.office_used[request.requesting_office] = self.office_used.get(request.requesting_office, 0) + cost
        self.provider_used[request.provider_id] = self.provider_used.get(request.provider_id, 0) + cost
        self.daily_used += cost
        self.monthly_used += cost
        return BudgetOutcome.AUTHORIZED_EXTERNAL_RETRIEVAL


@dataclass(frozen=True)
class ResourceGovernanceDecision:
    decision_id: str
    request_id: str
    outcome: BudgetOutcome
    cache_status: CacheStatus
    priority_class: SearchPriority
    reserved_cost_units: int
    evidence_required: bool
    decision_reason: str
    created_at: str


class SearchResourceGovernor:
    """Mandatory pre-retrieval resource governance boundary."""

    def __init__(self, ledger: SearchBudgetLedger | None = None, gateway: SourceAuthorizationGateway | None = None) -> None:
        self.ledger = ledger or SearchBudgetLedger()
        self.gateway = gateway or SourceAuthorizationGateway()

    def authorize(
        self,
        request: GovernedSearchRequest,
        source_request: SourceAuthorizationRequest | None = None,
        cache_entry: CacheEntry | None = None,
    ) -> ResourceGovernanceDecision:
        if request.priority_class in {SearchPriority.P6_BACKGROUND_RESEARCH, SearchPriority.P7_HISTORICAL_ENRICHMENT} and request.safety_critical:
            return _decision(request, BudgetOutcome.REJECTED_UNAUTHORIZED_PRIORITY, CacheStatus.NOT_USED, 0, "background work cannot claim safety-critical priority")
        if source_request is not None and not self.gateway.authorize(source_request).authorized:
            return _decision(request, BudgetOutcome.REJECTED_UNAUTHORIZED_SOURCE, CacheStatus.NOT_USED, 0, "source authorization failed")
        if cache_entry is not None:
            if cache_entry.raw_evidence_reference and cache_entry.provenance_reference and cache_entry.environment == request.environment and cache_entry.cache_isolation_scope == request.cache_isolation_scope and cache_entry.stale_status is CacheStatus.HIT:
                return _decision(request, BudgetOutcome.AUTHORIZED_CACHE_HIT, CacheStatus.HIT, 0, "valid governed cache hit")
            if cache_entry.stale_status in {CacheStatus.STALE_REJECTED, CacheStatus.CORRUPT}:
                return _decision(request, BudgetOutcome.TRADE_BLOCKING_RESOURCE_FAILURE, cache_entry.stale_status, 0, "cache not eligible for authoritative use")
        outcome = self.ledger.reserve(request)
        reserved = request.estimated_cost_units if outcome in {BudgetOutcome.AUTHORIZED_EXTERNAL_RETRIEVAL, BudgetOutcome.AUTHORIZED_SAFETY_OVERRIDE} else 0
        return _decision(request, outcome, CacheStatus.MISS, reserved, outcome.value)


@dataclass(frozen=True)
class FailureDoctrineRule:
    failure_class: SearchFailureClass
    category: str
    severity: FailureSeverity
    detection_method: str
    detection_timeout_seconds: int
    required_retry_count: int
    retry_schedule_seconds: tuple[int, ...]
    fallback_eligibility: str
    cache_authorization: str
    office_responsible: str
    workflow_state: WorkflowFailureState
    escalation_destination: str
    commander_notification_required: bool
    trade_eligible: bool
    final_workflow_disposition: str


class FailureDoctrineRegistry:
    def __init__(self, rules: Mapping[SearchFailureClass, FailureDoctrineRule] | None = None) -> None:
        self._rules = MappingProxyType(dict(rules or {failure: _failure_rule(failure) for failure in SearchFailureClass}))

    def classify(self, failure: SearchFailureClass) -> FailureDoctrineRule:
        return self._rules[failure]


@dataclass(frozen=True)
class SearchEvidenceRecord:
    search_evidence_id: str
    search_execution_id: str
    search_plan_id: str
    search_plan_version: str
    source_registry_version: str
    requesting_office: str
    executing_office: str
    workflow_id: str
    workflow_execution_token_id: str
    decision_object_id: str
    investigation_id: str
    parent_search_execution_id: str
    correlation_id: str
    created_at: str
    finalized_at: str
    authorized_purpose: str
    search_authorization_status: str
    authorizing_artifact_type: str
    authorizing_artifact_identifier: str
    requesting_office_authority_result: str
    executing_office_authority_result: str
    workflow_authority_validation_result: str
    approved_source_authorization_result: str
    approved_retrieval_surface_authorization_result: str
    authorized_search_depth_limit: int
    authorized_cost_limit: int
    authorized_freshness_requirement_seconds: int
    authorization_rejection_code: str
    canonical_source_identifier: str
    source_name: str
    owning_institution: str
    source_classification: str
    retrieval_surface_identifier: str
    retrieval_location_reference: str
    retrieval_method: str
    source_role_classification: str
    source_jurisdiction: str
    exact_query_text: str
    normalized_query_text: str
    structured_parameters: Mapping[str, str]
    entity_identifiers: Mapping[str, str]
    requested_time_range: tuple[str, str]
    query_template_identifier: str
    retrieval_start_timestamp: str
    retrieval_completion_timestamp: str
    source_response_timestamp: str
    source_publication_timestamp: str
    timezone: str
    cache_status: CacheStatus
    cache_key: str
    cache_record_identifier: str
    cache_age_seconds: int
    attempt_number: int
    total_attempt_count: int
    retry_policy_identifier: str
    fallback_source_identifier: str
    transport_status: str
    protocol_status: str
    source_response_status: str
    content_type: str
    response_size_bytes: int
    record_count: int
    result_count: int
    zero_result_status: bool
    partial_response_status: bool
    malformed_response_status: bool
    response_digest: str
    canonicalized_response_digest: str
    raw_evidence_reference: str
    normalized_evidence_reference: str
    extraction_manifest_reference: str
    evidence_storage_integrity_result: str
    failure_classification: SearchFailureClass | None
    stop_rule_identifier: str
    stop_rule_outcome: str
    escalation_outcome: str
    monetary_cost_units: int
    retention_class: str
    legal_hold_status: str
    integrity_status: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class SearchEvidenceCertifier:
    REQUIRED = (
        "search_evidence_id", "search_execution_id", "search_plan_id", "search_plan_version",
        "source_registry_version", "requesting_office", "executing_office", "workflow_id",
        "workflow_execution_token_id", "authorized_purpose", "canonical_source_identifier",
        "retrieval_surface_identifier", "retrieval_method", "created_at", "finalized_at",
        "record_digest",
    )

    def certify(self, record: SearchEvidenceRecord) -> SearchEvidenceCertificationStatus:
        if any(getattr(record, name) in ("", None) for name in self.REQUIRED):
            return SearchEvidenceCertificationStatus.INVALID
        if record.search_authorization_status != "AUTHORIZED":
            return SearchEvidenceCertificationStatus.AUTHORIZATION_REJECTED
        if not record.raw_evidence_reference and record.failure_classification is None and not record.zero_result_status:
            return SearchEvidenceCertificationStatus.EVIDENCE_INCOMPLETE
        if record.integrity_status != "VERIFIED":
            return SearchEvidenceCertificationStatus.INVALID
        return SearchEvidenceCertificationStatus.CERTIFIED


class SearchEvidenceRepository:
    def __init__(self) -> None:
        self._records: dict[str, SearchEvidenceRecord] = {}

    def append(self, record: SearchEvidenceRecord) -> None:
        if record.search_evidence_id in self._records:
            raise ValueError("search evidence records are immutable and append-only by identifier")
        self._records[record.search_evidence_id] = record

    def get(self, search_evidence_id: str) -> SearchEvidenceRecord:
        return self._records[search_evidence_id]

    def all_records(self) -> tuple[SearchEvidenceRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))


def _decision(request: GovernedSearchRequest, outcome: BudgetOutcome, cache_status: CacheStatus, reserved: int, reason: str) -> ResourceGovernanceDecision:
    return ResourceGovernanceDecision(_stable_id("SGD", request.request_id, outcome.value, cache_status.value), request.request_id, outcome, cache_status, request.priority_class, reserved, True, reason, utc_timestamp())


def _failure_rule(failure: SearchFailureClass) -> FailureDoctrineRule:
    critical = {
        SearchFailureClass.AUTHENTICATION_FAILURE,
        SearchFailureClass.AUTHORIZATION_FAILURE,
        SearchFailureClass.BROKER_OUTAGE,
        SearchFailureClass.EXCHANGE_OUTAGE,
        SearchFailureClass.EVIDENCE_STORAGE_FAILURE,
        SearchFailureClass.PROVENANCE_RECORDING_FAILURE,
        SearchFailureClass.MULTI_SOURCE_SYSTEMIC_FAILURE,
    }
    outage = "OUTAGE" in failure.value or failure in {SearchFailureClass.SOURCE_UNAVAILABLE, SearchFailureClass.LOSS_OF_INTERNET_CONNECTIVITY}
    severity = FailureSeverity.CRITICAL if failure in critical else FailureSeverity.HIGH if outage else FailureSeverity.MEDIUM
    return FailureDoctrineRule(
        failure,
        "outage" if outage else "retrieval_failure",
        severity,
        "provider_status_or_response_validation",
        30,
        0 if failure in {SearchFailureClass.AUTHORIZATION_FAILURE, SearchFailureClass.UNSUPPORTED_ASSET, SearchFailureClass.UNSUPPORTED_JURISDICTION} else 2,
        () if failure in {SearchFailureClass.AUTHORIZATION_FAILURE, SearchFailureClass.UNSUPPORTED_ASSET, SearchFailureClass.UNSUPPORTED_JURISDICTION} else (2, 5),
        "prohibited unless approved fallback source exists",
        "cache allowed only if policy permits and explicitly labeled",
        "Intelligence",
        WorkflowFailureState.TRADE_BLOCKED if severity is FailureSeverity.CRITICAL else WorkflowFailureState.EVIDENCE_INCOMPLETE,
        "Commander" if severity is FailureSeverity.CRITICAL else "RequestingOffice",
        severity is FailureSeverity.CRITICAL,
        False,
        "block_or_escalate_until explicit evidence state is resolved",
    )


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
