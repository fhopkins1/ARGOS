"""MO-SP-001 approved source registry and search-surface doctrine.

This module is the pre-retrieval authority for external information access.
It validates source, surface, office, purpose, environment, fact type, fields,
method, URL, license, credential scope, fallback, and workflow token context
before any external retrieval may begin.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import ipaddress
import json
import re
from types import MappingProxyType
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse


MO_SP_001_VERSION = "MO-SP-001/1.0.0"
UNKNOWN = "UNKNOWN"


class SourceRegistryError(ValueError):
    """Raised when a source registry violates MO-SP-001."""


class SourceAuthorityClass(str, Enum):
    PRIMARY_AUTHORITY = "PRIMARY_AUTHORITY"
    LICENSED_MARKET_AUTHORITY = "LICENSED_MARKET_AUTHORITY"
    CORROBORATING_AUTHORITY = "CORROBORATING_AUTHORITY"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    EARLY_WARNING_ONLY = "EARLY_WARNING_ONLY"
    ADVERSARIAL_EVIDENCE = "ADVERSARIAL_EVIDENCE"
    FALLBACK_ONLY = "FALLBACK_ONLY"
    PROHIBITED = "PROHIBITED"


class RetrievalMethod(str, Enum):
    OFFICIAL_API = "OFFICIAL_API"
    OFFICIAL_STREAM = "OFFICIAL_STREAM"
    OFFICIAL_MACHINE_READABLE_FILE = "OFFICIAL_MACHINE_READABLE_FILE"
    OFFICIAL_RSS_OR_EVENT_FEED = "OFFICIAL_RSS_OR_EVENT_FEED"
    OFFICIAL_DOCUMENT_REPOSITORY = "OFFICIAL_DOCUMENT_REPOSITORY"
    OFFICIAL_WEB_PAGE = "OFFICIAL_WEB_PAGE"
    LICENSED_PROVIDER_API = "LICENSED_PROVIDER_API"
    LICENSED_PROVIDER_STREAM = "LICENSED_PROVIDER_STREAM"
    APPROVED_SECONDARY_API = "APPROVED_SECONDARY_API"
    APPROVED_SECONDARY_WEB_PAGE = "APPROVED_SECONDARY_WEB_PAGE"
    BROKER_API = "BROKER_API"
    BROKER_STREAM = "BROKER_STREAM"
    BROKER_STATEMENT_OR_REPORT = "BROKER_STATEMENT_OR_REPORT"
    COURT_RECORD_PORTAL = "COURT_RECORD_PORTAL"
    SEARCH_ENGINE_DISCOVERY = "SEARCH_ENGINE_DISCOVERY"
    BROWSER_DISCOVERY = "BROWSER_DISCOVERY"
    MANUAL_HUMAN_SUBMISSION = "MANUAL_HUMAN_SUBMISSION"


class SourceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE_PENDING_APPROVAL = "INACTIVE_PENDING_APPROVAL"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"
    PROHIBITED = "PROHIBITED"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    PAPER_ONLY = "PAPER_ONLY"


class SurfaceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE_PENDING_APPROVAL = "INACTIVE_PENDING_APPROVAL"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"
    PROHIBITED = "PROHIBITED"


class RegistryVersionStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    CERTIFIED = "CERTIFIED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"


class SourceAuthorizationDecisionCode(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    DENIED = "DENIED"
    SOURCE_SUSPENDED = "SOURCE_SUSPENDED"
    SOURCE_RETIRED = "SOURCE_RETIRED"
    SURFACE_UNAPPROVED = "SURFACE_UNAPPROVED"
    OFFICE_UNAUTHORIZED = "OFFICE_UNAUTHORIZED"
    PURPOSE_UNAUTHORIZED = "PURPOSE_UNAUTHORIZED"
    ENVIRONMENT_UNAUTHORIZED = "ENVIRONMENT_UNAUTHORIZED"
    FACT_TYPE_UNAUTHORIZED = "FACT_TYPE_UNAUTHORIZED"
    FIELD_UNAUTHORIZED = "FIELD_UNAUTHORIZED"
    METHOD_UNAUTHORIZED = "METHOD_UNAUTHORIZED"
    LICENSE_REQUIRED = "LICENSE_REQUIRED"
    CREDENTIAL_SCOPE_INVALID = "CREDENTIAL_SCOPE_INVALID"
    FALLBACK_NOT_AUTHORIZED = "FALLBACK_NOT_AUTHORIZED"
    REGISTRY_VERSION_INVALID = "REGISTRY_VERSION_INVALID"
    TOKEN_INVALID = "TOKEN_INVALID"
    CONFIGURATION_INVALID = "CONFIGURATION_INVALID"


class SP001RejectionCode(str, Enum):
    SOURCE_NOT_REGISTERED = "SP001_SOURCE_NOT_REGISTERED"
    SURFACE_NOT_REGISTERED = "SP001_SURFACE_NOT_REGISTERED"
    SOURCE_NOT_ACTIVE = "SP001_SOURCE_NOT_ACTIVE"
    SOURCE_SUSPENDED = "SP001_SOURCE_SUSPENDED"
    SOURCE_RETIRED = "SP001_SOURCE_RETIRED"
    SOURCE_PROHIBITED = "SP001_SOURCE_PROHIBITED"
    OFFICE_NOT_AUTHORIZED = "SP001_OFFICE_NOT_AUTHORIZED"
    PURPOSE_NOT_AUTHORIZED = "SP001_PURPOSE_NOT_AUTHORIZED"
    ENVIRONMENT_NOT_AUTHORIZED = "SP001_ENVIRONMENT_NOT_AUTHORIZED"
    FACT_TYPE_NOT_AUTHORIZED = "SP001_FACT_TYPE_NOT_AUTHORIZED"
    FIELD_NOT_AUTHORIZED = "SP001_FIELD_NOT_AUTHORIZED"
    METHOD_NOT_AUTHORIZED = "SP001_METHOD_NOT_AUTHORIZED"
    HOST_NOT_AUTHORIZED = "SP001_HOST_NOT_AUTHORIZED"
    PATH_NOT_AUTHORIZED = "SP001_PATH_NOT_AUTHORIZED"
    REDIRECT_NOT_AUTHORIZED = "SP001_REDIRECT_NOT_AUTHORIZED"
    LICENSE_NOT_ACTIVE = "SP001_LICENSE_NOT_ACTIVE"
    CREDENTIAL_SCOPE_INVALID = "SP001_CREDENTIAL_SCOPE_INVALID"
    COST_CLASS_UNDEFINED = "SP001_COST_CLASS_UNDEFINED"
    FRESHNESS_CLASS_UNDEFINED = "SP001_FRESHNESS_CLASS_UNDEFINED"
    EVIDENCE_POLICY_UNDEFINED = "SP001_EVIDENCE_POLICY_UNDEFINED"
    FALLBACK_NOT_AUTHORIZED = "SP001_FALLBACK_NOT_AUTHORIZED"
    FALLBACK_CHAIN_INVALID = "SP001_FALLBACK_CHAIN_INVALID"
    REGISTRY_VERSION_NOT_ACTIVE = "SP001_REGISTRY_VERSION_NOT_ACTIVE"
    REGISTRY_DIGEST_INVALID = "SP001_REGISTRY_DIGEST_INVALID"
    WORKFLOW_TOKEN_INVALID = "SP001_WORKFLOW_TOKEN_INVALID"
    DECISION_OBJECT_CONTEXT_INVALID = "SP001_DECISION_OBJECT_CONTEXT_INVALID"
    DISCOVERY_RESULT_NOT_EVIDENCE = "SP001_DISCOVERY_RESULT_NOT_EVIDENCE"
    EARLY_WARNING_NOT_TRADE_ELIGIBLE = "SP001_EARLY_WARNING_NOT_TRADE_ELIGIBLE"
    TEST_SOURCE_OPERATIONALLY_BLOCKED = "SP001_TEST_SOURCE_OPERATIONALLY_BLOCKED"
    ARBITRARY_URL_BLOCKED = "SP001_ARBITRARY_URL_BLOCKED"
    SEARCH_ENGINE_SNIPPET_BLOCKED = "SP001_SEARCH_ENGINE_SNIPPET_BLOCKED"
    SYNTHETIC_SUBSTITUTION_BLOCKED = "SP001_SYNTHETIC_SUBSTITUTION_BLOCKED"


class EvidenceRetentionClass(str, Enum):
    FULL_RAW_RESPONSE = "FULL_RAW_RESPONSE"
    FULL_DOCUMENT = "FULL_DOCUMENT"
    STRUCTURED_RESPONSE_AND_DIGEST = "STRUCTURED_RESPONSE_AND_DIGEST"
    OFFICIAL_DOCUMENT_REFERENCE_AND_DIGEST = "OFFICIAL_DOCUMENT_REFERENCE_AND_DIGEST"
    EVENT_MESSAGE_AND_METADATA = "EVENT_MESSAGE_AND_METADATA"
    BROKER_RESPONSE_AND_RECONCILIATION_REFERENCE = "BROKER_RESPONSE_AND_RECONCILIATION_REFERENCE"
    DISCOVERY_RESULT_METADATA_ONLY = "DISCOVERY_RESULT_METADATA_ONLY"
    EARLY_WARNING_CONTENT_AND_CONTEXT = "EARLY_WARNING_CONTENT_AND_CONTEXT"
    RETENTION_PROHIBITED_ESCALATION_REQUIRED = "RETENTION_PROHIBITED_ESCALATION_REQUIRED"


class CostClass(str, Enum):
    ZERO_MARGINAL_PUBLIC = "ZERO_MARGINAL_PUBLIC"
    LOW_MARGINAL_PUBLIC = "LOW_MARGINAL_PUBLIC"
    METERED_API = "METERED_API"
    LICENSED_FIXED_COST = "LICENSED_FIXED_COST"
    LICENSED_METERED = "LICENSED_METERED"
    BROKER_INCLUDED = "BROKER_INCLUDED"
    BROKER_METERED = "BROKER_METERED"
    HUMAN_REVIEW_COST = "HUMAN_REVIEW_COST"
    UNKNOWN_COST_PROHIBITED = "UNKNOWN_COST_PROHIBITED"


class FreshnessClass(str, Enum):
    REAL_TIME = "REAL_TIME"
    NEAR_REAL_TIME = "NEAR_REAL_TIME"
    DELAYED_DECLARED = "DELAYED_DECLARED"
    EVENT_DRIVEN = "EVENT_DRIVEN"
    INTRADAY = "INTRADAY"
    DAILY = "DAILY"
    PUBLICATION_SCHEDULED = "PUBLICATION_SCHEDULED"
    PERIODIC = "PERIODIC"
    HISTORICAL = "HISTORICAL"
    STATIC_REFERENCE = "STATIC_REFERENCE"
    UNDEFINED_PROHIBITED = "UNDEFINED_PROHIBITED"


class LicensingClass(str, Enum):
    PUBLIC = "PUBLIC"
    LICENSED_ACTIVE = "LICENSED_ACTIVE"
    LICENSED_PENDING_APPROVAL = "LICENSED_PENDING_APPROVAL"
    BROKER_ACCOUNT_AUTHORIZED = "BROKER_ACCOUNT_AUTHORIZED"
    PROHIBITED = "PROHIBITED"


class CredentialRequirement(str, Enum):
    NONE = "NONE"
    API_KEY = "API_KEY"
    OAUTH = "OAUTH"
    BROKER_SESSION = "BROKER_SESSION"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    PROHIBITED = "PROHIBITED"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return {key: _jsonable(item) for key, item in value.items()}
    if is_dataclass(value):
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name not in {"record_digest", "decision_digest", "content_digest"}}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list, frozenset, set)):
        return [_jsonable(item) for item in value]
    return value


def stable_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{stable_digest(parts)[:32].upper()}"


@dataclass(frozen=True)
class ApprovedSourceRecord:
    source_id: str
    canonical_name: str
    owning_institution: str
    source_family: str
    authority_domain: tuple[str, ...]
    authority_class: SourceAuthorityClass
    institution_type: str
    jurisdiction: tuple[str, ...]
    asset_classes: tuple[str, ...]
    fact_types: tuple[str, ...]
    permitted_information_fields: tuple[str, ...]
    prohibited_information_fields: tuple[str, ...]
    prohibited_conclusions: tuple[str, ...]
    authorized_offices: tuple[str, ...]
    authorized_request_purposes: tuple[str, ...]
    authorized_environments: tuple[str, ...]
    approved_retrieval_surface_ids: tuple[str, ...]
    normal_retrieval_frequency_class: str
    freshness_expectation_class: FreshnessClass
    evidence_retention_class: EvidenceRetentionClass
    cost_class: CostClass
    licensing_class: LicensingClass
    credential_requirement: CredentialRequirement
    fallback_source_ids: tuple[str, ...]
    outage_disposition: str
    suspension_conditions: tuple[str, ...]
    replacement_conditions: tuple[str, ...]
    source_status: SourceStatus
    effective_from: str
    effective_until: str
    registry_version: str
    approving_authority: str
    approval_record_id: str
    created_at: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", stable_digest(self))

    def validate(self) -> None:
        required_text = (
            "source_id",
            "canonical_name",
            "owning_institution",
            "source_family",
            "normal_retrieval_frequency_class",
            "outage_disposition",
            "effective_from",
            "registry_version",
            "approving_authority",
            "approval_record_id",
            "created_at",
        )
        for name in required_text:
            if getattr(self, name) in ("", UNKNOWN, None):
                raise SourceRegistryError(f"{self.source_id}: missing {name}")
        required_tuples = (
            "authority_domain",
            "jurisdiction",
            "asset_classes",
            "fact_types",
            "permitted_information_fields",
            "prohibited_information_fields",
            "prohibited_conclusions",
            "authorized_offices",
            "authorized_request_purposes",
            "authorized_environments",
            "approved_retrieval_surface_ids",
            "suspension_conditions",
            "replacement_conditions",
        )
        for name in required_tuples:
            if not getattr(self, name):
                raise SourceRegistryError(f"{self.source_id}: missing {name}")
        if self.cost_class is CostClass.UNKNOWN_COST_PROHIBITED and self.source_status is SourceStatus.ACTIVE:
            raise SourceRegistryError(f"{self.source_id}: active source has unknown prohibited cost")
        if self.freshness_expectation_class is FreshnessClass.UNDEFINED_PROHIBITED and self.source_status is SourceStatus.ACTIVE:
            raise SourceRegistryError(f"{self.source_id}: active source has undefined freshness")
        if self.evidence_retention_class is EvidenceRetentionClass.RETENTION_PROHIBITED_ESCALATION_REQUIRED and self.source_status is SourceStatus.ACTIVE:
            raise SourceRegistryError(f"{self.source_id}: active source has unresolved evidence retention")
        if self.authority_class is SourceAuthorityClass.PROHIBITED and self.source_status is not SourceStatus.PROHIBITED:
            raise SourceRegistryError(f"{self.source_id}: prohibited authority class must have prohibited status")
        if self.authority_class in {SourceAuthorityClass.DISCOVERY_ONLY, SourceAuthorityClass.EARLY_WARNING_ONLY} and "execution_eligibility" in self.authorized_request_purposes:
            raise SourceRegistryError(f"{self.source_id}: low-authority source cannot be execution eligible")
        if "live" in self.authorized_environments and self.source_id.lower().startswith(("test", "fixture", "demo")):
            raise SourceRegistryError(f"{self.source_id}: test/demo source cannot be live eligible")
        if self.source_status is SourceStatus.ACTIVE and self.licensing_class is LicensingClass.LICENSED_PENDING_APPROVAL:
            raise SourceRegistryError(f"{self.source_id}: active source lacks active license")


@dataclass(frozen=True)
class ApprovedRetrievalSurfaceRecord:
    retrieval_surface_id: str
    source_id: str
    surface_name: str
    surface_type: str
    canonical_host: str
    approved_path_pattern: str
    approved_protocol: str
    retrieval_method: RetrievalMethod
    machine_readable: bool
    structured_data_preference_rank: int
    authentication_type: str
    credential_scope: str
    rate_limit_class: str
    licensed_access_required: bool
    allowed_query_parameter_classes: tuple[str, ...]
    allowed_response_content_types: tuple[str, ...]
    prohibited_redirect_behavior: tuple[str, ...]
    prohibited_host_variants: tuple[str, ...]
    browser_access_allowed: bool
    search_engine_discovery_allowed: bool
    direct_retrieval_required: bool
    environment_permissions: tuple[str, ...]
    surface_status: SurfaceStatus
    effective_from: str
    effective_until: str
    registry_version: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", stable_digest(self))

    def validate(self) -> None:
        if not self.retrieval_surface_id or not self.source_id or not self.canonical_host:
            raise SourceRegistryError("surface identity, source, and host are mandatory")
        if self.surface_status is SurfaceStatus.ACTIVE and self.retrieval_method in {RetrievalMethod.SEARCH_ENGINE_DISCOVERY, RetrievalMethod.BROWSER_DISCOVERY} and not self.search_engine_discovery_allowed and not self.browser_access_allowed:
            raise SourceRegistryError(f"{self.retrieval_surface_id}: discovery method requires discovery permission")
        if self.licensed_access_required and self.authentication_type == "none":
            raise SourceRegistryError(f"{self.retrieval_surface_id}: licensed surface requires authentication")
        if not self.environment_permissions:
            raise SourceRegistryError(f"{self.retrieval_surface_id}: environment permissions required")


@dataclass(frozen=True)
class SourceRegistryVersion:
    registry_version: str
    status: RegistryVersionStatus
    effective_from: str
    effective_until: str
    source_record_count: int
    retrieval_surface_count: int
    content_digest: str
    predecessor_version: str
    change_record_ids: tuple[str, ...]
    approving_authority: str
    certified_at: str


@dataclass(frozen=True)
class SourceRegistryChangeRecord:
    change_record_id: str
    prior_value: Mapping[str, Any]
    new_value: Mapping[str, Any]
    change_type: str
    reason: str
    evidence: str
    approving_authority: str
    effective_time: str
    affected_environments: tuple[str, ...]
    affected_source_ids: tuple[str, ...]
    affected_retrieval_surfaces: tuple[str, ...]
    compatibility_impact: str
    required_migration_action: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", stable_digest(self))


@dataclass(frozen=True)
class SourceAuthorizationRequest:
    authorization_request_id: str
    workflow_id: str
    workflow_execution_token_id: str
    requesting_office: str
    requesting_component: str
    request_purpose_code: str
    requested_source_id: str
    requested_retrieval_surface_id: str
    requested_fact_types: tuple[str, ...]
    requested_fields: tuple[str, ...]
    asset_class: str
    instrument_identifiers: tuple[str, ...]
    jurisdiction: str
    environment: str
    proposed_retrieval_method: RetrievalMethod
    proposed_cost_class: CostClass
    decision_object_id: str
    requested_at: str
    final_resolved_url: str = ""
    redirect_chain: tuple[str, ...] = ()
    fallback_for_source_id: str = ""


@dataclass(frozen=True)
class SourceAuthorizationDecision:
    authorization_decision_id: str
    authorization_request_id: str
    decision: SourceAuthorizationDecisionCode
    decision_code: str
    registry_version: str
    source_status: str
    surface_status: str
    office_authorized: bool
    purpose_authorized: bool
    environment_authorized: bool
    fact_types_authorized: bool
    fields_authorized: bool
    retrieval_method_authorized: bool
    licensing_authorized: bool
    credential_scope_authorized: bool
    cost_class_authorized: bool
    fallback_status: str
    evaluated_at: str
    authorizing_component: str
    decision_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_digest", stable_digest(self))

    @property
    def authorized(self) -> bool:
        return self.decision is SourceAuthorizationDecisionCode.AUTHORIZED


@dataclass(frozen=True)
class SourceUseEvidenceRecord:
    use_evidence_id: str
    authorization_request_reference: str
    authorization_decision_reference: str
    source_id: str
    retrieval_surface_id: str
    registry_version: str
    requesting_office: str
    request_purpose: str
    workflow_id: str
    decision_object_id: str
    retrieval_timestamp: str
    result_status: str
    raw_evidence_reference: str
    failure_reference: str
    cache_indicator: str
    cost_classification: CostClass
    response_digest: str


@dataclass(frozen=True)
class SourceRegistrySnapshot:
    version: SourceRegistryVersion
    sources: tuple[ApprovedSourceRecord, ...]
    surfaces: tuple[ApprovedRetrievalSurfaceRecord, ...]
    changes: tuple[SourceRegistryChangeRecord, ...]


class ApprovedSourceRegistry:
    """Certified registry state plus deterministic validation."""

    def __init__(self, snapshot: SourceRegistrySnapshot) -> None:
        self.snapshot = snapshot
        self._sources = {source.source_id: source for source in snapshot.sources}
        self._surfaces = {surface.retrieval_surface_id: surface for surface in snapshot.surfaces}
        self.validate()

    @property
    def version(self) -> SourceRegistryVersion:
        return self.snapshot.version

    def source(self, source_id: str) -> ApprovedSourceRecord | None:
        return self._sources.get(source_id)

    def surface(self, surface_id: str) -> ApprovedRetrievalSurfaceRecord | None:
        return self._surfaces.get(surface_id)

    def list_operator_view(self) -> tuple[Mapping[str, Any], ...]:
        rows = []
        for source in sorted(self.snapshot.sources, key=lambda item: item.source_id):
            rows.append(
                MappingProxyType(
                    {
                        "active_registry_version": self.version.registry_version,
                        "source_id": source.source_id,
                        "canonical_source_name": source.canonical_name,
                        "owning_institution": source.owning_institution,
                        "authority_class": source.authority_class.value,
                        "authority_domain": source.authority_domain,
                        "source_status": source.source_status.value,
                        "authorized_offices": source.authorized_offices,
                        "authorized_environments": source.authorized_environments,
                        "approved_retrieval_surfaces": source.approved_retrieval_surface_ids,
                        "licensing_state": source.licensing_class.value,
                        "credential_state": source.credential_requirement.value,
                        "cost_class": source.cost_class.value,
                        "freshness_class": source.freshness_expectation_class.value,
                        "fallback_relationships": source.fallback_source_ids,
                        "last_validation_result": "PASS",
                        "suspension_reason": "" if source.source_status is not SourceStatus.SUSPENDED else source.outage_disposition,
                        "effective_from": source.effective_from,
                        "effective_until": source.effective_until,
                        "registry_change_history": tuple(change.change_record_id for change in self.snapshot.changes if source.source_id in change.affected_source_ids),
                    }
                )
            )
        return tuple(rows)

    def validate(self) -> None:
        if self.version.status is not RegistryVersionStatus.ACTIVE:
            raise SourceRegistryError(SP001RejectionCode.REGISTRY_VERSION_NOT_ACTIVE.value)
        if len(self._sources) != len(self.snapshot.sources):
            raise SourceRegistryError("duplicate source IDs fail")
        if len(self._surfaces) != len(self.snapshot.surfaces):
            raise SourceRegistryError("duplicate surface IDs fail")
        for source in self.snapshot.sources:
            source.validate()
            for surface_id in source.approved_retrieval_surface_ids:
                surface = self._surfaces.get(surface_id)
                if surface is None or surface.source_id != source.source_id:
                    raise SourceRegistryError(f"{source.source_id}: registered surface missing or assigned to another source")
        for surface in self.snapshot.surfaces:
            surface.validate()
            if surface.source_id not in self._sources:
                raise SourceRegistryError(f"{surface.retrieval_surface_id}: source not registered")
        self._validate_fallback_graph()
        expected_digest = self.compute_content_digest()
        if self.version.content_digest != expected_digest:
            raise SourceRegistryError(SP001RejectionCode.REGISTRY_DIGEST_INVALID.value)

    def compute_content_digest(self) -> str:
        return stable_digest(
            {
                "sources": tuple(sorted(self.snapshot.sources, key=lambda item: item.source_id)),
                "surfaces": tuple(sorted(self.snapshot.surfaces, key=lambda item: item.retrieval_surface_id)),
                "changes": tuple(sorted(self.snapshot.changes, key=lambda item: item.change_record_id)),
            }
        )

    def _validate_fallback_graph(self) -> None:
        for source in self.snapshot.sources:
            for fallback_id in source.fallback_source_ids:
                fallback = self._sources.get(fallback_id)
                if fallback is None:
                    raise SourceRegistryError(SP001RejectionCode.FALLBACK_NOT_AUTHORIZED.value)
                if fallback.source_status is SourceStatus.PROHIBITED or fallback.authority_class is SourceAuthorityClass.PROHIBITED:
                    raise SourceRegistryError(SP001RejectionCode.FALLBACK_CHAIN_INVALID.value)
        for source in self.snapshot.sources:
            seen: set[str] = set()
            current = source
            while current.fallback_source_ids:
                next_id = current.fallback_source_ids[0]
                if next_id in seen or next_id == source.source_id:
                    raise SourceRegistryError(SP001RejectionCode.FALLBACK_CHAIN_INVALID.value)
                seen.add(next_id)
                current = self._sources[next_id]


class SourceAuthorizationGateway:
    """Machine-enforced pre-retrieval authorization gateway."""

    def __init__(self, registry: ApprovedSourceRegistry | None = None) -> None:
        self.registry = registry or canonical_source_registry()
        self.decisions: list[SourceAuthorizationDecision] = []
        self.use_evidence: list[SourceUseEvidenceRecord] = []

    def authorize(self, request: SourceAuthorizationRequest) -> SourceAuthorizationDecision:
        source = self.registry.source(request.requested_source_id)
        surface = self.registry.surface(request.requested_retrieval_surface_id)
        if self.registry.version.status is not RegistryVersionStatus.ACTIVE:
            return self._deny(request, SourceAuthorizationDecisionCode.REGISTRY_VERSION_INVALID, SP001RejectionCode.REGISTRY_VERSION_NOT_ACTIVE, source, surface)
        if not request.workflow_execution_token_id:
            return self._deny(request, SourceAuthorizationDecisionCode.TOKEN_INVALID, SP001RejectionCode.WORKFLOW_TOKEN_INVALID, source, surface)
        if source is None:
            return self._deny(request, SourceAuthorizationDecisionCode.DENIED, SP001RejectionCode.SOURCE_NOT_REGISTERED, source, surface)
        if surface is None:
            return self._deny(request, SourceAuthorizationDecisionCode.SURFACE_UNAPPROVED, SP001RejectionCode.SURFACE_NOT_REGISTERED, source, surface)
        if surface.source_id != source.source_id or surface.retrieval_surface_id not in source.approved_retrieval_surface_ids:
            return self._deny(request, SourceAuthorizationDecisionCode.SURFACE_UNAPPROVED, SP001RejectionCode.SURFACE_NOT_REGISTERED, source, surface)
        status_denial = self._status_denial(request, source, surface)
        if status_denial:
            decision_code, rejection_code = status_denial
            return self._deny(request, decision_code, rejection_code, source, surface)
        checks: tuple[tuple[bool, SourceAuthorizationDecisionCode, SP001RejectionCode], ...] = (
            (request.requesting_office in source.authorized_offices, SourceAuthorizationDecisionCode.OFFICE_UNAUTHORIZED, SP001RejectionCode.OFFICE_NOT_AUTHORIZED),
            (request.request_purpose_code in source.authorized_request_purposes, SourceAuthorizationDecisionCode.PURPOSE_UNAUTHORIZED, SP001RejectionCode.PURPOSE_NOT_AUTHORIZED),
            (request.environment in source.authorized_environments and request.environment in surface.environment_permissions, SourceAuthorizationDecisionCode.ENVIRONMENT_UNAUTHORIZED, SP001RejectionCode.ENVIRONMENT_NOT_AUTHORIZED),
            (set(request.requested_fact_types).issubset(set(source.fact_types)), SourceAuthorizationDecisionCode.FACT_TYPE_UNAUTHORIZED, SP001RejectionCode.FACT_TYPE_NOT_AUTHORIZED),
            (self._fields_authorized(request, source), SourceAuthorizationDecisionCode.FIELD_UNAUTHORIZED, SP001RejectionCode.FIELD_NOT_AUTHORIZED),
            (request.proposed_retrieval_method is surface.retrieval_method, SourceAuthorizationDecisionCode.METHOD_UNAUTHORIZED, SP001RejectionCode.METHOD_NOT_AUTHORIZED),
            (self._license_authorized(source), SourceAuthorizationDecisionCode.LICENSE_REQUIRED, SP001RejectionCode.LICENSE_NOT_ACTIVE),
            (self._credential_authorized(source, surface), SourceAuthorizationDecisionCode.CREDENTIAL_SCOPE_INVALID, SP001RejectionCode.CREDENTIAL_SCOPE_INVALID),
            (request.proposed_cost_class is source.cost_class and source.cost_class is not CostClass.UNKNOWN_COST_PROHIBITED, SourceAuthorizationDecisionCode.CONFIGURATION_INVALID, SP001RejectionCode.COST_CLASS_UNDEFINED),
            (source.freshness_expectation_class is not FreshnessClass.UNDEFINED_PROHIBITED, SourceAuthorizationDecisionCode.CONFIGURATION_INVALID, SP001RejectionCode.FRESHNESS_CLASS_UNDEFINED),
        )
        for passed, decision_code, rejection_code in checks:
            if not passed:
                return self._deny(request, decision_code, rejection_code, source, surface)
        url_code = validate_resolved_destination(surface, request.final_resolved_url, request.redirect_chain)
        if url_code is not None:
            return self._deny(request, SourceAuthorizationDecisionCode.SURFACE_UNAPPROVED, url_code, source, surface)
        if request.fallback_for_source_id and request.requested_source_id not in (self.registry.source(request.fallback_for_source_id) or source).fallback_source_ids:
            return self._deny(request, SourceAuthorizationDecisionCode.FALLBACK_NOT_AUTHORIZED, SP001RejectionCode.FALLBACK_NOT_AUTHORIZED, source, surface)
        if source.authority_class is SourceAuthorityClass.DISCOVERY_ONLY and "snippet" in request.requested_fields:
            return self._deny(request, SourceAuthorizationDecisionCode.FIELD_UNAUTHORIZED, SP001RejectionCode.SEARCH_ENGINE_SNIPPET_BLOCKED, source, surface)
        if source.authority_class is SourceAuthorityClass.EARLY_WARNING_ONLY and request.request_purpose_code == "execution_eligibility":
            return self._deny(request, SourceAuthorizationDecisionCode.PURPOSE_UNAUTHORIZED, SP001RejectionCode.EARLY_WARNING_NOT_TRADE_ELIGIBLE, source, surface)
        return self._decision(request, SourceAuthorizationDecisionCode.AUTHORIZED, SourceAuthorizationDecisionCode.AUTHORIZED.value, source, surface)

    def record_source_use(self, request: SourceAuthorizationRequest, decision: SourceAuthorizationDecision, *, result_status: str, raw_evidence_reference: str = "", failure_reference: str = "", cache_indicator: str = "NO_CACHE", response_payload: Any = None) -> SourceUseEvidenceRecord:
        source = self.registry.source(request.requested_source_id)
        record = SourceUseEvidenceRecord(
            stable_id("SPUSE", request.authorization_request_id, decision.authorization_decision_id, result_status),
            request.authorization_request_id,
            decision.authorization_decision_id,
            request.requested_source_id,
            request.requested_retrieval_surface_id,
            self.registry.version.registry_version,
            request.requesting_office,
            request.request_purpose_code,
            request.workflow_id,
            request.decision_object_id,
            _utc_now(),
            result_status,
            raw_evidence_reference,
            failure_reference,
            cache_indicator,
            source.cost_class if source else CostClass.UNKNOWN_COST_PROHIBITED,
            stable_digest(response_payload) if response_payload is not None else "",
        )
        self.use_evidence.append(record)
        return record

    def _status_denial(self, request: SourceAuthorizationRequest, source: ApprovedSourceRecord, surface: ApprovedRetrievalSurfaceRecord) -> tuple[SourceAuthorizationDecisionCode, SP001RejectionCode] | None:
        if source.source_status is SourceStatus.SUSPENDED:
            return SourceAuthorizationDecisionCode.SOURCE_SUSPENDED, SP001RejectionCode.SOURCE_SUSPENDED
        if source.source_status is SourceStatus.RETIRED:
            return SourceAuthorizationDecisionCode.SOURCE_RETIRED, SP001RejectionCode.SOURCE_RETIRED
        if source.source_status is SourceStatus.PROHIBITED or source.authority_class is SourceAuthorityClass.PROHIBITED:
            return SourceAuthorizationDecisionCode.DENIED, SP001RejectionCode.SOURCE_PROHIBITED
        if source.source_status is SourceStatus.INACTIVE_PENDING_APPROVAL:
            return SourceAuthorizationDecisionCode.DENIED, SP001RejectionCode.SOURCE_NOT_ACTIVE
        if source.source_status is SourceStatus.PAPER_ONLY and request.environment != "paper":
            return SourceAuthorizationDecisionCode.ENVIRONMENT_UNAUTHORIZED, SP001RejectionCode.ENVIRONMENT_NOT_AUTHORIZED
        if source.source_status is SourceStatus.RESEARCH_ONLY and request.environment != "research":
            return SourceAuthorizationDecisionCode.ENVIRONMENT_UNAUTHORIZED, SP001RejectionCode.ENVIRONMENT_NOT_AUTHORIZED
        if surface.surface_status is not SurfaceStatus.ACTIVE:
            return SourceAuthorizationDecisionCode.SURFACE_UNAPPROVED, SP001RejectionCode.SURFACE_NOT_REGISTERED
        return None

    def _fields_authorized(self, request: SourceAuthorizationRequest, source: ApprovedSourceRecord) -> bool:
        requested = set(request.requested_fields)
        return bool(requested) and requested.issubset(set(source.permitted_information_fields)) and not requested.intersection(set(source.prohibited_information_fields))

    def _license_authorized(self, source: ApprovedSourceRecord) -> bool:
        if source.licensing_class in {LicensingClass.PUBLIC, LicensingClass.LICENSED_ACTIVE, LicensingClass.BROKER_ACCOUNT_AUTHORIZED}:
            return True
        return False

    def _credential_authorized(self, source: ApprovedSourceRecord, surface: ApprovedRetrievalSurfaceRecord) -> bool:
        if source.credential_requirement is CredentialRequirement.PROHIBITED:
            return False
        if surface.licensed_access_required and source.credential_requirement is CredentialRequirement.NONE:
            return False
        return True

    def _deny(self, request: SourceAuthorizationRequest, decision: SourceAuthorizationDecisionCode, rejection: SP001RejectionCode, source: ApprovedSourceRecord | None, surface: ApprovedRetrievalSurfaceRecord | None) -> SourceAuthorizationDecision:
        return self._decision(request, decision, rejection.value, source, surface)

    def _decision(self, request: SourceAuthorizationRequest, decision: SourceAuthorizationDecisionCode, decision_code: str, source: ApprovedSourceRecord | None, surface: ApprovedRetrievalSurfaceRecord | None) -> SourceAuthorizationDecision:
        source_status = source.source_status.value if source else UNKNOWN
        surface_status = surface.surface_status.value if surface else UNKNOWN
        decided = SourceAuthorizationDecision(
            stable_id("SPDEC", request.authorization_request_id, decision.value, decision_code),
            request.authorization_request_id,
            decision,
            decision_code,
            self.registry.version.registry_version,
            source_status,
            surface_status,
            bool(source and request.requesting_office in source.authorized_offices),
            bool(source and request.request_purpose_code in source.authorized_request_purposes),
            bool(source and surface and request.environment in source.authorized_environments and request.environment in surface.environment_permissions),
            bool(source and set(request.requested_fact_types).issubset(set(source.fact_types))),
            bool(source and self._fields_authorized(request, source)),
            bool(surface and request.proposed_retrieval_method is surface.retrieval_method),
            bool(source and self._license_authorized(source)),
            bool(source and surface and self._credential_authorized(source, surface)),
            bool(source and request.proposed_cost_class is source.cost_class and source.cost_class is not CostClass.UNKNOWN_COST_PROHIBITED),
            "NOT_REQUESTED" if not request.fallback_for_source_id else "REQUESTED",
            _utc_now(),
            "MO-SP-001 SourceAuthorizationGateway",
        )
        self.decisions.append(decided)
        return decided


def validate_resolved_destination(surface: ApprovedRetrievalSurfaceRecord, final_resolved_url: str, redirect_chain: tuple[str, ...] = ()) -> SP001RejectionCode | None:
    if not final_resolved_url:
        return None
    urls = redirect_chain + (final_resolved_url,)
    if len(urls) > 1 and "all_redirects" in surface.prohibited_redirect_behavior:
        return SP001RejectionCode.REDIRECT_NOT_AUTHORIZED
    for index, url in enumerate(urls):
        parsed = urlparse(url)
        if parsed.username or parsed.password:
            return SP001RejectionCode.ARBITRARY_URL_BLOCKED
        if parsed.scheme != surface.approved_protocol:
            return SP001RejectionCode.ARBITRARY_URL_BLOCKED
        host = (parsed.hostname or "").lower().rstrip(".")
        if _is_private_or_local(host):
            return SP001RejectionCode.ARBITRARY_URL_BLOCKED
        if host != surface.canonical_host.lower() or host in {item.lower() for item in surface.prohibited_host_variants}:
            return SP001RejectionCode.REDIRECT_NOT_AUTHORIZED if index < len(urls) - 1 else SP001RejectionCode.HOST_NOT_AUTHORIZED
        if not re.fullmatch(surface.approved_path_pattern, parsed.path or "/"):
            return SP001RejectionCode.PATH_NOT_AUTHORIZED
    return None


def _is_private_or_local(host: str) -> bool:
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local


def canonical_source_registry() -> ApprovedSourceRegistry:
    sources = canonical_source_records()
    surfaces = canonical_surface_records()
    changes = (
        SourceRegistryChangeRecord(
            "SPCHG-INITIAL-CANONICAL-SEED",
            MappingProxyType({}),
            MappingProxyType({"source_count": len(sources), "surface_count": len(surfaces)}),
            "INITIAL_CERTIFIED_SEED",
            "MO-SP-001 canonical source registry seed",
            "MO-SP-001 implementation order",
            "Constitutional Control Panel",
            "2026-07-20T00:00:00Z",
            ("development", "test", "paper", "research", "live"),
            tuple(source.source_id for source in sources),
            tuple(surface.retrieval_surface_id for surface in surfaces),
            "new pre-retrieval source authorization gateway",
            "route external retrieval through SourceAuthorizationGateway",
        ),
    )
    digest = stable_digest({"sources": tuple(sorted(sources, key=lambda item: item.source_id)), "surfaces": tuple(sorted(surfaces, key=lambda item: item.retrieval_surface_id)), "changes": changes})
    version = SourceRegistryVersion("SPREG-2026-07-20-001", RegistryVersionStatus.ACTIVE, "2026-07-20T00:00:00Z", UNKNOWN, len(sources), len(surfaces), digest, UNKNOWN, tuple(change.change_record_id for change in changes), "Constitutional Control Panel", "2026-07-20T00:00:00Z")
    return ApprovedSourceRegistry(SourceRegistrySnapshot(version, sources, surfaces, changes))


def _source(
    source_id: str,
    canonical_name: str,
    owning_institution: str,
    source_family: str,
    authority_domain: tuple[str, ...],
    authority_class: SourceAuthorityClass,
    institution_type: str,
    jurisdiction: tuple[str, ...],
    asset_classes: tuple[str, ...],
    fact_types: tuple[str, ...],
    permitted_fields: tuple[str, ...],
    prohibited_fields: tuple[str, ...],
    prohibited_conclusions: tuple[str, ...],
    offices: tuple[str, ...],
    purposes: tuple[str, ...],
    environments: tuple[str, ...],
    surfaces: tuple[str, ...],
    freshness: FreshnessClass,
    evidence: EvidenceRetentionClass,
    cost: CostClass,
    licensing: LicensingClass,
    credential: CredentialRequirement,
    status: SourceStatus,
    fallback_source_ids: tuple[str, ...] = (),
) -> ApprovedSourceRecord:
    return ApprovedSourceRecord(
        source_id,
        canonical_name,
        owning_institution,
        source_family,
        authority_domain,
        authority_class,
        institution_type,
        jurisdiction,
        asset_classes,
        fact_types,
        permitted_fields,
        prohibited_fields,
        prohibited_conclusions,
        offices,
        purposes,
        environments,
        surfaces,
        "MO-SP-002 owns detailed timing",
        freshness,
        evidence,
        cost,
        licensing,
        credential,
        fallback_source_ids,
        "SOURCE_UNAVAILABLE_FAIL_CLOSED",
        ("authority_revoked", "credential_expired", "license_expired", "integrity_failure", "legal_prohibition"),
        ("authority_replaced", "surface_retired", "license_unavailable", "jurisdiction_changed"),
        status,
        "2026-07-20T00:00:00Z",
        UNKNOWN,
        "SPREG-2026-07-20-001",
        "Constitutional Control Panel",
        f"SPAPP-{source_id}",
        "2026-07-20T00:00:00Z",
    )


def canonical_source_records() -> tuple[ApprovedSourceRecord, ...]:
    return (
        _source(
            "SRC-US-SEC-EDGAR",
            "SEC EDGAR",
            "United States Securities and Exchange Commission",
            "regulatory_filing",
            ("SEC-filed issuer disclosures", "filing metadata", "official filing acceptance times"),
            SourceAuthorityClass.PRIMARY_AUTHORITY,
            "regulator",
            ("US",),
            ("equity", "fund", "issuer"),
            ("regulatory_filing", "filing_metadata"),
            ("accession_number", "filing_form", "issuer_identity", "cik", "filing_date", "acceptance_timestamp", "reporting_period", "filed_documents", "filing_exhibits", "structured_filing_facts", "amendment_status", "filing_url"),
            ("live_bid", "live_ask", "live_last", "management_statement_truth", "legal_innocence"),
            ("issuer_statement_accuracy", "absence_of_enforcement_action", "current_when_superseded"),
            ("Intelligence", "Sentinel", "Seeker", "Analyst", "Risk", "Historian"),
            ("official_filing_retrieval", "new_filing_detection", "historical_reconstruction"),
            ("development", "test", "paper", "research", "live"),
            ("SURF-US-SEC-SUBMISSIONS", "SURF-US-SEC-ARCHIVES", "SURF-US-SEC-WEB-DISCOVERY"),
            FreshnessClass.EVENT_DRIVEN,
            EvidenceRetentionClass.FULL_DOCUMENT,
            CostClass.ZERO_MARGINAL_PUBLIC,
            LicensingClass.PUBLIC,
            CredentialRequirement.NONE,
            SourceStatus.ACTIVE,
        ),
        _source(
            "SRC-US-SEC-ENFORCEMENT",
            "SEC Enforcement and Administrative Proceedings",
            "United States Securities and Exchange Commission",
            "regulatory_enforcement",
            ("SEC enforcement actions", "litigation releases", "administrative proceedings", "orders"),
            SourceAuthorityClass.PRIMARY_AUTHORITY,
            "regulator",
            ("US",),
            ("equity", "issuer", "regulated_entity"),
            ("sec_enforcement_action", "sec_litigation_release", "sec_order"),
            ("release_number", "action_date", "respondent", "order_text", "official_url", "publication_timestamp"),
            ("criminal_guilt", "civil_liability_beyond_order", "market_price"),
            ("legal_guilt", "investment_merit", "causation"),
            ("Intelligence", "Sentinel", "Seeker", "Analyst", "Risk", "Historian"),
            ("official_enforcement_retrieval", "adversarial_review", "historical_reconstruction"),
            ("development", "test", "paper", "research", "live"),
            ("SURF-US-SEC-ENFORCEMENT-WEB",),
            FreshnessClass.EVENT_DRIVEN,
            EvidenceRetentionClass.FULL_DOCUMENT,
            CostClass.ZERO_MARGINAL_PUBLIC,
            LicensingClass.PUBLIC,
            CredentialRequirement.NONE,
            SourceStatus.ACTIVE,
        ),
        _source(
            "SRC-US-NYSE-MARKET-STATUS",
            "NYSE Market Status and Notices",
            "New York Stock Exchange",
            "exchange_status",
            ("exchange calendar", "trading halts", "market status notices"),
            SourceAuthorityClass.PRIMARY_AUTHORITY,
            "exchange",
            ("US",),
            ("equity", "etf"),
            ("exchange_calendar", "trading_halt_status", "market_session_status"),
            ("halt_symbol", "halt_reason", "status_timestamp", "resume_time", "market_session"),
            ("broker_order_acceptance", "issuer_intent", "portfolio_state"),
            ("broker_order_status", "issuer_guidance_truth"),
            ("Intelligence", "Sentinel", "Seeker", "Analyst", "Risk", "Historian"),
            ("market_status_monitoring", "halt_detection", "historical_reconstruction"),
            ("development", "test", "paper", "research", "live"),
            ("SURF-US-NYSE-STATUS-WEB",),
            FreshnessClass.NEAR_REAL_TIME,
            EvidenceRetentionClass.OFFICIAL_DOCUMENT_REFERENCE_AND_DIGEST,
            CostClass.ZERO_MARGINAL_PUBLIC,
            LicensingClass.PUBLIC,
            CredentialRequirement.NONE,
            SourceStatus.ACTIVE,
        ),
        _source(
            "SRC-US-BLS",
            "U.S. Bureau of Labor Statistics",
            "U.S. Bureau of Labor Statistics",
            "economic_data",
            ("BLS statistical releases", "official series metadata"),
            SourceAuthorityClass.PRIMARY_AUTHORITY,
            "government_statistical_agency",
            ("US",),
            ("macro",),
            ("economic_indicator",),
            ("series_value", "release_timestamp", "series_metadata", "source_agency"),
            ("issuer_guidance", "market_price", "broker_state"),
            ("future_economic_outcome", "causation", "investment_recommendation"),
            ("Intelligence", "Sentinel", "Seeker", "Analyst", "Risk", "Historian"),
            ("official_economic_release_retrieval", "scheduled_publication_monitoring", "historical_reconstruction"),
            ("development", "test", "paper", "research", "live"),
            ("SURF-US-BLS-API",),
            FreshnessClass.PUBLICATION_SCHEDULED,
            EvidenceRetentionClass.STRUCTURED_RESPONSE_AND_DIGEST,
            CostClass.ZERO_MARGINAL_PUBLIC,
            LicensingClass.PUBLIC,
            CredentialRequirement.NONE,
            SourceStatus.ACTIVE,
        ),
        _source(
            "SRC-US-FRED-DISTRIBUTION",
            "Federal Reserve Economic Data Distribution",
            "Federal Reserve Bank of St. Louis",
            "economic_data_distribution",
            ("redistributed public economic series with source attribution",),
            SourceAuthorityClass.CORROBORATING_AUTHORITY,
            "government_data_distributor",
            ("US",),
            ("macro",),
            ("economic_indicator_distribution",),
            ("series_value", "source_agency", "retrieval_timestamp", "distribution_series_id"),
            ("originating_agency_identity_replacement", "market_price", "broker_state"),
            ("primary_agency_replacement", "future_economic_outcome"),
            ("Intelligence", "Seeker", "Analyst", "Risk", "Historian"),
            ("corroboration", "research", "historical_reconstruction"),
            ("development", "test", "paper", "research"),
            ("SURF-US-FRED-API",),
            FreshnessClass.DAILY,
            EvidenceRetentionClass.STRUCTURED_RESPONSE_AND_DIGEST,
            CostClass.ZERO_MARGINAL_PUBLIC,
            LicensingClass.PUBLIC,
            CredentialRequirement.NONE,
            SourceStatus.ACTIVE,
        ),
        _source(
            "SRC-ISSUER-IR",
            "Issuer Investor Relations Publication Surface",
            "Public Issuer",
            "issuer_publication",
            ("issuer corporate announcements", "earnings releases", "dividend declarations"),
            SourceAuthorityClass.PRIMARY_AUTHORITY,
            "issuer",
            ("GLOBAL",),
            ("equity", "issuer"),
            ("issuer_release", "declared_dividend", "earnings_release", "corporate_action_notice"),
            ("issuer_release", "declared_dividend", "earnings_release", "corporate_action_notice", "publication_timestamp", "official_url"),
            ("live_price", "independently_verified_future_cash_flow", "broker_state"),
            ("management_accuracy", "investment_merit", "cash_flow_verification"),
            ("Intelligence", "Sentinel", "Seeker", "Analyst", "Risk", "Historian"),
            ("official_issuer_release_retrieval", "corporate_action_monitoring", "historical_reconstruction"),
            ("development", "test", "paper", "research", "live"),
            ("SURF-ISSUER-IR-WEB",),
            FreshnessClass.EVENT_DRIVEN,
            EvidenceRetentionClass.FULL_DOCUMENT,
            CostClass.ZERO_MARGINAL_PUBLIC,
            LicensingClass.PUBLIC,
            CredentialRequirement.NONE,
            SourceStatus.ACTIVE,
        ),
        _source(
            "SRC-BROKER-OF-RECORD",
            "Broker of Record Operational Account APIs",
            "Configured Broker of Record",
            "broker_account",
            ("accepted orders", "fills", "positions", "account restrictions", "cash", "buying power"),
            SourceAuthorityClass.PRIMARY_AUTHORITY,
            "broker",
            ("US",),
            ("equity", "option", "cash"),
            ("accepted orders", "fills", "positions", "account restrictions", "cash", "buying power"),
            ("broker_order_acceptance", "broker_fill", "account_buying_power", "cash_balance", "position_quantity", "margin_requirement"),
            ("issuer_guidance", "market_news", "live_bid", "legal_liability"),
            ("issuer_intent", "market_price_truth", "investment_merit"),
            ("Intelligence", "Sentinel", "Trader", "Historian", "Risk"),
            ("broker_execution_state", "account_reconciliation", "execution_critical_service"),
            ("development", "test", "paper"),
            ("SURF-BROKER-PAPER-API",),
            FreshnessClass.REAL_TIME,
            EvidenceRetentionClass.BROKER_RESPONSE_AND_RECONCILIATION_REFERENCE,
            CostClass.BROKER_INCLUDED,
            LicensingClass.BROKER_ACCOUNT_AUTHORIZED,
            CredentialRequirement.BROKER_SESSION,
            SourceStatus.PAPER_ONLY,
        ),
        _source(
            "SRC-LICENSED-SIP-MARKET-DATA",
            "Licensed SIP Market Data Provider",
            "Licensed Market Data Provider",
            "market_data_provider",
            ("subscribed market prices", "quotes", "trades", "NBBO"),
            SourceAuthorityClass.LICENSED_MARKET_AUTHORITY,
            "licensed_vendor",
            ("US",),
            ("equity", "option"),
            ("subscribed market prices", "quotes", "trades", "NBBO"),
            ("last_trade", "bid_price", "ask_price", "nbbo", "venue", "delay_status", "market_timestamp"),
            ("issuer_intent", "legal_liability", "broker_state", "unsubscribed_field"),
            ("issuer_intent", "regulatory_disposition", "broker_account_state"),
            ("Intelligence", "Sentinel", "Seeker", "Analyst", "Risk", "Historian"),
            ("market_data_observation", "market_status_monitoring"),
            ("development", "test", "paper"),
            ("SURF-LICENSED-SIP-API",),
            FreshnessClass.REAL_TIME,
            EvidenceRetentionClass.STRUCTURED_RESPONSE_AND_DIGEST,
            CostClass.LICENSED_METERED,
            LicensingClass.LICENSED_PENDING_APPROVAL,
            CredentialRequirement.API_KEY,
            SourceStatus.INACTIVE_PENDING_APPROVAL,
        ),
        _source(
            "SRC-SEARCH-ENGINE-DISCOVERY",
            "Approved Search Engine Discovery Surface",
            "Search Provider",
            "discovery",
            ("discovery of originating evidence only",),
            SourceAuthorityClass.DISCOVERY_ONLY,
            "search_provider",
            ("GLOBAL",),
            ("all",),
            ("all",),
            ("discovery_result_url", "query", "ranking", "retrieval_timestamp", "engine_identity"),
            ("snippet", "generated_summary", "authoritative_fact", "trade_eligible_fact"),
            ("truth_from_snippet", "primary_source_replacement", "absence_as_proof"),
            ("Intelligence", "Seeker", "Analyst", "Risk", "Historian"),
            ("discovery", "corroboration_lead"),
            ("development", "test", "research"),
            ("SURF-SEARCH-DISCOVERY",),
            FreshnessClass.EVENT_DRIVEN,
            EvidenceRetentionClass.DISCOVERY_RESULT_METADATA_ONLY,
            CostClass.LOW_MARGINAL_PUBLIC,
            LicensingClass.PUBLIC,
            CredentialRequirement.NONE,
            SourceStatus.RESEARCH_ONLY,
        ),
        _source(
            "SRC-SOCIAL-EARLY-WARNING",
            "Low-Authority Social Early Warning Surface",
            "Public Social Platform",
            "early_warning",
            ("early warning leads only",),
            SourceAuthorityClass.EARLY_WARNING_ONLY,
            "social_platform",
            ("GLOBAL",),
            ("all",),
            ("all",),
            ("early_warning_lead", "post_url", "author_handle", "retrieval_timestamp"),
            ("confirmed_event", "causation", "trade_eligible_fact", "legal_liability"),
            ("truth", "causation", "execution_eligibility"),
            ("Intelligence", "Sentinel", "Seeker", "Risk"),
            ("early_warning", "adversarial_review"),
            ("development", "test", "research"),
            ("SURF-SOCIAL-EARLY-WARNING-WEB",),
            FreshnessClass.EVENT_DRIVEN,
            EvidenceRetentionClass.EARLY_WARNING_CONTENT_AND_CONTEXT,
            CostClass.LOW_MARGINAL_PUBLIC,
            LicensingClass.PUBLIC,
            CredentialRequirement.NONE,
            SourceStatus.RESEARCH_ONLY,
        ),
        _source(
            "SRC-PROHIBITED-MODEL-MEMORY",
            "Model Memory and Generated Summary",
            "ARGOS Language Model Runtime",
            "prohibited_synthetic",
            ("none",),
            SourceAuthorityClass.PROHIBITED,
            "model",
            ("GLOBAL",),
            ("none",),
            ("none",),
            ("none",),
            ("all_fields", "snippet", "generated_summary", "default_price", "default_quantity"),
            ("evidence", "truth", "source_substitution", "execution_eligibility"),
            ("NONE",),
            ("none",),
            ("development", "test", "paper", "research", "live"),
            ("SURF-PROHIBITED-MODEL-MEMORY",),
            FreshnessClass.UNDEFINED_PROHIBITED,
            EvidenceRetentionClass.RETENTION_PROHIBITED_ESCALATION_REQUIRED,
            CostClass.UNKNOWN_COST_PROHIBITED,
            LicensingClass.PROHIBITED,
            CredentialRequirement.PROHIBITED,
            SourceStatus.PROHIBITED,
        ),
    )


def canonical_surface_records() -> tuple[ApprovedRetrievalSurfaceRecord, ...]:
    return (
        _surface("SURF-US-SEC-SUBMISSIONS", "SRC-US-SEC-EDGAR", "SEC company submissions API", "data.sec.gov", r"/submissions/.*", RetrievalMethod.OFFICIAL_API, True, ("json",)),
        _surface("SURF-US-SEC-ARCHIVES", "SRC-US-SEC-EDGAR", "SEC EDGAR filing archive", "www.sec.gov", r"/Archives/edgar/.*", RetrievalMethod.OFFICIAL_DOCUMENT_REPOSITORY, True, ("html", "xml", "txt", "xbrl")),
        _surface("SURF-US-SEC-WEB-DISCOVERY", "SRC-US-SEC-EDGAR", "SEC company search page", "www.sec.gov", r"/edgar/.*", RetrievalMethod.OFFICIAL_WEB_PAGE, False, ("html",), browser=True),
        _surface("SURF-US-SEC-ENFORCEMENT-WEB", "SRC-US-SEC-ENFORCEMENT", "SEC enforcement releases", "www.sec.gov", r"/enforcement/.*|/litigation/.*", RetrievalMethod.OFFICIAL_WEB_PAGE, False, ("html", "pdf"), browser=True),
        _surface("SURF-US-NYSE-STATUS-WEB", "SRC-US-NYSE-MARKET-STATUS", "NYSE market status", "www.nyse.com", r"/markets/.*|/trade-halt.*", RetrievalMethod.OFFICIAL_WEB_PAGE, False, ("html",), browser=True),
        _surface("SURF-US-BLS-API", "SRC-US-BLS", "BLS public API", "api.bls.gov", r"/publicAPI/.*", RetrievalMethod.OFFICIAL_API, True, ("json",)),
        _surface("SURF-US-FRED-API", "SRC-US-FRED-DISTRIBUTION", "FRED public API", "api.stlouisfed.org", r"/fred/.*", RetrievalMethod.APPROVED_SECONDARY_API, True, ("json", "xml")),
        _surface("SURF-ISSUER-IR-WEB", "SRC-ISSUER-IR", "Issuer investor relations official page", "investors.example-issuer-authority.invalid", r"/.*", RetrievalMethod.OFFICIAL_WEB_PAGE, False, ("html", "pdf"), browser=True),
        _surface("SURF-BROKER-PAPER-API", "SRC-BROKER-OF-RECORD", "Configured paper broker API", "broker.account-api", r"/.*", RetrievalMethod.BROKER_API, True, ("json",), environments=("development", "test", "paper"), licensed=True, auth="broker_session", credential_scope="account_execution_state"),
        _surface("SURF-LICENSED-SIP-API", "SRC-LICENSED-SIP-MARKET-DATA", "Licensed market data API", "sip.market-data", r"/.*", RetrievalMethod.LICENSED_PROVIDER_API, True, ("json",), environments=("development", "test", "paper"), licensed=True, auth="api_key", credential_scope="market_data_entitlement"),
        _surface("SURF-SEARCH-DISCOVERY", "SRC-SEARCH-ENGINE-DISCOVERY", "Search engine discovery", "search.example-authority.invalid", r"/search.*", RetrievalMethod.SEARCH_ENGINE_DISCOVERY, True, ("json", "html"), environments=("development", "test", "research"), browser=True, search=True),
        _surface("SURF-SOCIAL-EARLY-WARNING-WEB", "SRC-SOCIAL-EARLY-WARNING", "Social early warning page", "social.example-authority.invalid", r"/.*", RetrievalMethod.BROWSER_DISCOVERY, False, ("html",), environments=("development", "test", "research"), browser=True),
        _surface("SURF-PROHIBITED-MODEL-MEMORY", "SRC-PROHIBITED-MODEL-MEMORY", "Prohibited model-generated evidence", "model-memory.invalid", r"/.*", RetrievalMethod.MANUAL_HUMAN_SUBMISSION, False, ("text",), environments=("development", "test", "paper", "research", "live"), status=SurfaceStatus.PROHIBITED),
    )


def _surface(
    retrieval_surface_id: str,
    source_id: str,
    name: str,
    host: str,
    path_pattern: str,
    method: RetrievalMethod,
    machine_readable: bool,
    content_types: tuple[str, ...],
    *,
    environments: tuple[str, ...] = ("development", "test", "paper", "research", "live"),
    licensed: bool = False,
    auth: str = "none",
    credential_scope: str = "none",
    browser: bool = False,
    search: bool = False,
    status: SurfaceStatus = SurfaceStatus.ACTIVE,
) -> ApprovedRetrievalSurfaceRecord:
    return ApprovedRetrievalSurfaceRecord(
        retrieval_surface_id,
        source_id,
        name,
        "external_retrieval_surface",
        host,
        path_pattern,
        "https",
        method,
        machine_readable,
        1 if machine_readable else 2,
        auth,
        credential_scope,
        "MO-SP-002_DEFINED",
        licensed,
        ("issuer", "cik", "accession", "symbol", "series_id", "date_range", "query"),
        content_types,
        ("all_redirects_to_unapproved_hosts",),
        ("localhost", "127.0.0.1", "::1"),
        browser,
        search,
        not browser and not search,
        environments,
        status,
        "2026-07-20T00:00:00Z",
        UNKNOWN,
        "SPREG-2026-07-20-001",
    )


def migration_inventory() -> tuple[Mapping[str, str], ...]:
    return (
        MappingProxyType({"original_component": "src/argos/control_panel/market_data_provider.py", "original_behavior": "EO-DJ market-data ingress with provider registry and fail-closed default", "new_registry_source_id": "SRC-LICENSED-SIP-MARKET-DATA", "new_retrieval_surface_id": "SURF-LICENSED-SIP-API", "new_authorization_path": "SourceAuthorizationGateway.authorize before provider.observe", "environment_restrictions": "development/test/paper until entitlement is certified", "migration_disposition": "inactive source candidate pending license/credential approval"}),
        MappingProxyType({"original_component": "src/argos/trader/broker_integration.py", "original_behavior": "paper broker adapter and broker-specific response isolation", "new_registry_source_id": "SRC-BROKER-OF-RECORD", "new_retrieval_surface_id": "SURF-BROKER-PAPER-API", "new_authorization_path": "SourceAuthorizationGateway for broker execution/account-state requests", "environment_restrictions": "paper only; live requires separate certified source", "migration_disposition": "registered paper-only broker authority"}),
        MappingProxyType({"original_component": "src/argos/control_panel/production_read_surface_registry.py", "original_behavior": "read-only production surface certification", "new_registry_source_id": "internal read surfaces", "new_retrieval_surface_id": "not external retrieval", "new_authorization_path": "unchanged read-only guard; MO-SP-001 governs only external retrieval", "environment_restrictions": "paper proof-domain separation", "migration_disposition": "reused as conformance reference"}),
        MappingProxyType({"original_component": "Codex/browser/web-search utilities", "original_behavior": "operator/tool-level browsing outside ARGOS runtime", "new_registry_source_id": "SRC-SEARCH-ENGINE-DISCOVERY", "new_retrieval_surface_id": "SURF-SEARCH-DISCOVERY", "new_authorization_path": "blocked unless research/discovery purpose and snippet fields excluded", "environment_restrictions": "development/test/research only", "migration_disposition": "quarantined from operational evidence"}),
        MappingProxyType({"original_component": "tests and fixtures containing mock/demo/sample values", "original_behavior": "isolated test fixtures", "new_registry_source_id": "SRC-PROHIBITED-MODEL-MEMORY for generated evidence; no live source", "new_retrieval_surface_id": "SURF-PROHIBITED-MODEL-MEMORY", "new_authorization_path": "operational authorization denied", "environment_restrictions": "test-only fixtures remain outside paper/live", "migration_disposition": "not grandfathered as external authority"}),
    )


def inactive_source_candidates() -> tuple[str, ...]:
    return tuple(source.source_id for source in canonical_source_records() if source.source_status is SourceStatus.INACTIVE_PENDING_APPROVAL)


def prohibited_or_quarantined_legacy_paths() -> tuple[str, ...]:
    return (
        "Model recollection or generated summaries as source evidence",
        "Search-engine snippets as evidence",
        "Unregistered URL destinations",
        "Demo/sample/mock providers outside isolated tests",
        "Paper broker records in live operation",
        "Unlicensed live market-data redistribution",
    )


def registry_conformance_report() -> Mapping[str, Any]:
    registry = canonical_source_registry()
    active = tuple(source.source_id for source in registry.snapshot.sources if source.source_status is SourceStatus.ACTIVE)
    return MappingProxyType(
        {
            "implementation": "MO-SP-001 Approved Source Registry and Search-Surface Doctrine",
            "registry_version": registry.version.registry_version,
            "source_count": len(registry.snapshot.sources),
            "surface_count": len(registry.snapshot.surfaces),
            "active_sources": active,
            "inactive_source_candidates": inactive_source_candidates(),
            "prohibited_or_quarantined_legacy_paths": prohibited_or_quarantined_legacy_paths(),
            "migration_inventory": migration_inventory(),
            "operator_view_available": True,
            "unresolved_dependencies": (
                "MO-SP-002 scheduling details",
                "MO-SP-013 expanded source-use evidence schema",
                "Live broker and market-data credentials/entitlements are not present in repository",
            ),
        }
    )


def snapshot_to_payload(snapshot: SourceRegistrySnapshot) -> dict[str, Any]:
    return _jsonable(snapshot)


def persist_registry_snapshot(repository: Any, snapshot: SourceRegistrySnapshot | None = None) -> Any:
    """Persist the certified registry through the existing append-only repository."""
    from argos.foundation.persistence import ObjectType

    material = snapshot or canonical_source_registry().snapshot
    payload = {
        "contract_id": material.version.registry_version,
        "case_file_id": "MO-SP-001",
        "source_registry_snapshot": snapshot_to_payload(material),
        "registry_version": material.version.registry_version,
        "content_digest": material.version.content_digest,
    }
    return repository.persist(ObjectType.OPERATIONAL_DOCUMENT, material.version.registry_version, payload)


def recover_registry_snapshot(record: Any) -> ApprovedSourceRegistry:
    """Recover a registry from persisted payload and verify its digest."""
    persisted_payload = dict(record.payload)
    payload = persisted_payload["source_registry_snapshot"]
    version_payload = payload["version"]
    version = SourceRegistryVersion(
        registry_version=version_payload["registry_version"],
        status=RegistryVersionStatus(version_payload["status"]),
        effective_from=version_payload["effective_from"],
        effective_until=version_payload["effective_until"],
        source_record_count=int(version_payload["source_record_count"]),
        retrieval_surface_count=int(version_payload["retrieval_surface_count"]),
        content_digest=version_payload.get("content_digest", persisted_payload.get("content_digest", "")),
        predecessor_version=version_payload["predecessor_version"],
        change_record_ids=tuple(version_payload["change_record_ids"]),
        approving_authority=version_payload["approving_authority"],
        certified_at=version_payload["certified_at"],
    )
    sources = tuple(_source_from_payload(item) for item in payload["sources"])
    surfaces = tuple(_surface_from_payload(item) for item in payload["surfaces"])
    changes = tuple(_change_from_payload(item) for item in payload["changes"])
    return ApprovedSourceRegistry(SourceRegistrySnapshot(version, sources, surfaces, changes))


def _source_from_payload(item: Mapping[str, Any]) -> ApprovedSourceRecord:
    data = dict(item)
    data["authority_class"] = SourceAuthorityClass(data["authority_class"])
    data["freshness_expectation_class"] = FreshnessClass(data["freshness_expectation_class"])
    data["evidence_retention_class"] = EvidenceRetentionClass(data["evidence_retention_class"])
    data["cost_class"] = CostClass(data["cost_class"])
    data["licensing_class"] = LicensingClass(data["licensing_class"])
    data["credential_requirement"] = CredentialRequirement(data["credential_requirement"])
    data["source_status"] = SourceStatus(data["source_status"])
    for key in (
        "authority_domain",
        "jurisdiction",
        "asset_classes",
        "fact_types",
        "permitted_information_fields",
        "prohibited_information_fields",
        "prohibited_conclusions",
        "authorized_offices",
        "authorized_request_purposes",
        "authorized_environments",
        "approved_retrieval_surface_ids",
        "fallback_source_ids",
        "suspension_conditions",
        "replacement_conditions",
    ):
        data[key] = tuple(data[key])
    data.pop("record_digest", None)
    return ApprovedSourceRecord(**data)


def _surface_from_payload(item: Mapping[str, Any]) -> ApprovedRetrievalSurfaceRecord:
    data = dict(item)
    data["retrieval_method"] = RetrievalMethod(data["retrieval_method"])
    data["environment_permissions"] = tuple(data["environment_permissions"])
    data["allowed_query_parameter_classes"] = tuple(data["allowed_query_parameter_classes"])
    data["allowed_response_content_types"] = tuple(data["allowed_response_content_types"])
    data["prohibited_redirect_behavior"] = tuple(data["prohibited_redirect_behavior"])
    data["prohibited_host_variants"] = tuple(data["prohibited_host_variants"])
    data["surface_status"] = SurfaceStatus(data["surface_status"])
    data.pop("record_digest", None)
    return ApprovedRetrievalSurfaceRecord(**data)


def _change_from_payload(item: Mapping[str, Any]) -> SourceRegistryChangeRecord:
    data = dict(item)
    data["prior_value"] = MappingProxyType(dict(data["prior_value"]))
    data["new_value"] = MappingProxyType(dict(data["new_value"]))
    data["affected_environments"] = tuple(data["affected_environments"])
    data["affected_source_ids"] = tuple(data["affected_source_ids"])
    data["affected_retrieval_surfaces"] = tuple(data["affected_retrieval_surfaces"])
    data.pop("record_digest", None)
    return SourceRegistryChangeRecord(**data)
