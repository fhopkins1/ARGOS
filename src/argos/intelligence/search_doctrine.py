"""MO-SP-007 canonical market, corporate, regulatory, legal, and macro search doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp

from .source_registry import RetrievalMethod, SourceAuthorizationGateway, SourceAuthorizationRequest, CostClass


MO_SP_007_VERSION = "MO-SP-007/1.0.0"


class CanonicalSearchError(ValueError):
    """Raised when canonical search doctrine cannot resolve a valid plan."""


class FactDomain(str, Enum):
    MARKET_DATA = "MARKET_DATA"
    CORPORATE_INFORMATION = "CORPORATE_INFORMATION"
    REGULATORY_LEGAL = "REGULATORY_LEGAL"
    MACROECONOMIC = "MACROECONOMIC"


class SourceRole(str, Enum):
    PRIMARY_AUTHORITY = "PRIMARY_AUTHORITY"
    SECONDARY_CONFIRMATION = "SECONDARY_CONFIRMATION"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    FALLBACK_AUTHORITY = "FALLBACK_AUTHORITY"
    CONTRARY_EVIDENCE = "CONTRARY_EVIDENCE"
    PROHIBITED = "PROHIBITED"


class CanonicalSearchStatus(str, Enum):
    CERTIFIED = "CERTIFIED"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    INCOMPLETE = "INCOMPLETE"
    STALE = "STALE"
    CONFLICTED = "CONFLICTED"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID_IDENTIFIER = "INVALID_IDENTIFIER"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    AUTHORITY_DENIED = "AUTHORITY_DENIED"
    EVIDENCE_NOT_RETAINED = "EVIDENCE_NOT_RETAINED"
    TRADE_BLOCKING = "TRADE_BLOCKING"
    HUMAN_ESCALATION_REQUIRED = "HUMAN_ESCALATION_REQUIRED"


@dataclass(frozen=True)
class CanonicalFactType:
    fact_type_id: str
    domain: FactDomain
    display_name: str
    required_identifiers: tuple[str, ...]
    required_fields: tuple[str, ...]


@dataclass(frozen=True)
class SourceStep:
    role: SourceRole
    source_id: str
    surface_id: str
    retrieval_method: RetrievalMethod
    required: bool = True


@dataclass(frozen=True)
class CanonicalSearchPlan:
    search_plan_id: str
    search_plan_version: str
    fact_type_id: str
    governed_domain: FactDomain
    effective_status: str
    governing_order_id: str
    schema_version: str
    authorized_offices: tuple[str, ...]
    authorized_purpose: str
    source_sequence: tuple[SourceStep, ...]
    required_identifiers: tuple[str, ...]
    required_fields: tuple[str, ...]
    prohibited_query_parameters: tuple[str, ...]
    maximum_records: int
    maximum_pages: int
    maximum_lookback: str
    maximum_forward_window: str
    freshness_limit_seconds: int
    stop_conditions: tuple[str, ...]
    failure_outcomes: tuple[CanonicalSearchStatus, ...]
    evidence_retention: tuple[str, ...]
    plan_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_digest", _stable_digest(self))


@dataclass(frozen=True)
class CanonicalSearchRequest:
    request_id: str
    workflow_id: str
    workflow_execution_token_id: str
    decision_object_id: str
    requesting_office: str
    fact_type_id: str
    environment: str
    identifiers: Mapping[str, str]
    query_parameters: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalSearchAuditRecord:
    audit_id: str
    request_id: str
    plan_id: str
    fact_type_id: str
    source_sequence: tuple[str, ...]
    authorization_decisions: tuple[str, ...]
    terminal_status: CanonicalSearchStatus
    stop_condition: str
    retained_evidence_required: bool
    created_at: str


@dataclass(frozen=True)
class CanonicalSearchCertification:
    request_id: str
    plan: CanonicalSearchPlan
    terminal_status: CanonicalSearchStatus
    failure_reason: str
    audit_record: CanonicalSearchAuditRecord


class CanonicalSearchPlanRegistry:
    """Immutable registry: one active canonical algorithm for each fact type."""

    def __init__(self, plans: Mapping[str, CanonicalSearchPlan] | None = None) -> None:
        self._plans = MappingProxyType(dict(plans or default_canonical_search_plans()))
        self._validate()

    def resolve(self, fact_type_id: str) -> CanonicalSearchPlan:
        plan = self._plans.get(fact_type_id)
        if plan is None:
            raise CanonicalSearchError(f"PLAN_NOT_FOUND: {fact_type_id}")
        return plan

    def all_plans(self) -> tuple[CanonicalSearchPlan, ...]:
        return tuple(self._plans[key] for key in sorted(self._plans))

    def _validate(self) -> None:
        seen: set[str] = set()
        for key, plan in self._plans.items():
            if key != plan.fact_type_id:
                raise CanonicalSearchError(f"PLAN_INVALID: key mismatch for {key}")
            if plan.fact_type_id in seen:
                raise CanonicalSearchError(f"PLAN_INVALID: duplicate {plan.fact_type_id}")
            seen.add(plan.fact_type_id)
            required = (
                plan.search_plan_id,
                plan.search_plan_version,
                plan.fact_type_id,
                plan.effective_status,
                plan.governing_order_id,
                plan.schema_version,
                plan.authorized_purpose,
            )
            if any(not item for item in required):
                raise CanonicalSearchError(f"PLAN_INVALID: missing required identity for {plan.fact_type_id}")
            if not plan.source_sequence or not any(step.role is SourceRole.PRIMARY_AUTHORITY for step in plan.source_sequence):
                raise CanonicalSearchError(f"PLAN_INVALID: primary authority missing for {plan.fact_type_id}")
            if SourceRole.PROHIBITED in {step.role for step in plan.source_sequence}:
                raise CanonicalSearchError(f"PLAN_INVALID: prohibited source in sequence for {plan.fact_type_id}")


class CanonicalSearchEngine:
    """Builds authorized search requests; it never performs general browsing."""

    def __init__(self, registry: CanonicalSearchPlanRegistry | None = None, gateway: SourceAuthorizationGateway | None = None) -> None:
        self.registry = registry or CanonicalSearchPlanRegistry()
        self.gateway = gateway or SourceAuthorizationGateway()

    def certify_request(self, request: CanonicalSearchRequest) -> CanonicalSearchCertification:
        plan = self.registry.resolve(request.fact_type_id)
        missing = [identifier for identifier in plan.required_identifiers if not request.identifiers.get(identifier)]
        if missing:
            return _certification(request, plan, CanonicalSearchStatus.INVALID_IDENTIFIER, f"missing identifiers: {', '.join(missing)}", ())
        prohibited = [key for key in request.query_parameters if key in plan.prohibited_query_parameters]
        if prohibited:
            return _certification(request, plan, CanonicalSearchStatus.AUTHORITY_DENIED, f"prohibited query parameters: {', '.join(prohibited)}", ())
        if request.requesting_office not in plan.authorized_offices:
            return _certification(request, plan, CanonicalSearchStatus.AUTHORITY_DENIED, "requesting office not authorized", ())

        decisions: list[str] = []
        for step in plan.source_sequence:
            decision = self.gateway.authorize(_authorization_request(request, plan, step))
            decisions.append(decision.decision_code)
            if step.required and not decision.authorized:
                return _certification(request, plan, CanonicalSearchStatus.AUTHORITY_DENIED, decision.decision_code, tuple(decisions))
        return _certification(request, plan, CanonicalSearchStatus.CERTIFIED, "", tuple(decisions))


def default_fact_types() -> Mapping[str, CanonicalFactType]:
    market = (
        "latest_price", "official_closing_price", "current_bid", "current_ask", "last_reported_trade",
        "current_session_volume", "historical_price_bars", "current_trading_status", "primary_listing_venue",
        "exchange_session_status", "options_chain", "implied_volatility_information",
        "historical_volatility_information", "trading_halt_status", "market_calendar_status",
        "security_identifier_resolution", "quote_timestamp", "trade_timestamp",
        "corporate_action_adjusted_price_status",
    )
    corporate = (
        "issuer_identity", "legal_issuer_name", "ticker_to_issuer_resolution", "primary_security_identifier",
        "sec_filing_existence", "sec_filing_metadata", "sec_filing_document", "earnings_release",
        "reported_earnings_values", "earnings_publication_time", "management_guidance", "guidance_revision",
        "investor_presentation", "corporate_action", "dividend_declaration", "dividend_terms",
        "stock_split", "reverse_split", "merger_announcement", "acquisition_announcement",
        "securities_offering", "dilution_event", "management_appointment", "management_departure",
        "official_company_announcement", "investor_relations_publication", "bankruptcy_disclosure",
        "credit_related_company_disclosure",
    )
    regulatory = (
        "enforcement_action", "regulatory_investigation", "regulatory_order", "rule_proposal",
        "final_rule", "rule_effective_date", "exchange_rule_notice", "court_proceeding", "court_filing",
        "court_judgment", "bankruptcy_petition", "bankruptcy_docket_event", "sanctions_status",
        "sanctions_action", "trading_restriction", "security_suspension", "exchange_halt_notice",
        "regulator_warning", "issuer_eligibility_restriction", "jurisdictional_legal_status",
    )
    macro = (
        "economic_calendar_event", "official_release_schedule", "published_economic_value",
        "prior_published_value", "revised_prior_value", "release_timestamp", "central_bank_decision",
        "central_bank_target_rate", "central_bank_policy_statement", "central_bank_meeting_calendar",
        "treasury_auction_information", "treasury_yield_or_rate_information", "treasury_fiscal_release",
        "labor_market_statistic", "unemployment_statistic", "payroll_statistic", "inflation_statistic",
        "consumer_price_statistic", "producer_price_statistic", "gross_domestic_product_statistic",
        "gdp_revision", "national_accounts_statistic", "industrial_production_statistic",
        "retail_sales_statistic", "housing_statistic", "manufacturing_statistic",
        "commodity_related_official_statistic", "other_registered_market_moving_economic_indicator",
    )
    items: dict[str, CanonicalFactType] = {}
    for name in market:
        items[name] = CanonicalFactType(name, FactDomain.MARKET_DATA, name.replace("_", " "), ("security_id", "venue"), _fields_for(name))
    for name in corporate:
        items[name] = CanonicalFactType(name, FactDomain.CORPORATE_INFORMATION, name.replace("_", " "), ("issuer_id",), _fields_for(name))
    for name in regulatory:
        items[name] = CanonicalFactType(name, FactDomain.REGULATORY_LEGAL, name.replace("_", " "), ("jurisdiction", "entity_id"), _fields_for(name))
    for name in macro:
        items[name] = CanonicalFactType(name, FactDomain.MACROECONOMIC, name.replace("_", " "), ("series_id", "release_date"), _fields_for(name))
    return MappingProxyType(items)


def default_canonical_search_plans() -> Mapping[str, CanonicalSearchPlan]:
    plans: dict[str, CanonicalSearchPlan] = {}
    for fact in default_fact_types().values():
        plans[fact.fact_type_id] = _plan_for(fact)
    return MappingProxyType(plans)


def _plan_for(fact: CanonicalFactType) -> CanonicalSearchPlan:
    if fact.domain is FactDomain.MARKET_DATA:
        sequence = (_step(SourceRole.PRIMARY_AUTHORITY, "SRC-LICENSED-SIP-MARKET-DATA", "SURF-LICENSED-SIP-API", RetrievalMethod.LICENSED_PROVIDER_API),)
        purpose = "market_data_observation"
        freshness = 15 if fact.fact_type_id in {"latest_price", "current_bid", "current_ask", "last_reported_trade"} else 86400
    elif fact.domain is FactDomain.CORPORATE_INFORMATION:
        sequence = (
            _step(SourceRole.PRIMARY_AUTHORITY, "SRC-US-SEC-EDGAR", "SURF-US-SEC-SUBMISSIONS", RetrievalMethod.OFFICIAL_API),
            _step(SourceRole.SECONDARY_CONFIRMATION, "SRC-ISSUER-IR", "SURF-ISSUER-IR-WEB", RetrievalMethod.OFFICIAL_WEB_PAGE, required=False),
        )
        purpose = "official_filing_retrieval"
        freshness = 86400
    elif fact.domain is FactDomain.REGULATORY_LEGAL:
        sequence = (_step(SourceRole.PRIMARY_AUTHORITY, "SRC-US-SEC-ENFORCEMENT", "SURF-US-SEC-ENFORCEMENT-WEB", RetrievalMethod.OFFICIAL_WEB_PAGE),)
        purpose = "adversarial_review"
        freshness = 86400
    else:
        primary = "SRC-US-BLS" if "labor" in fact.fact_type_id or "unemployment" in fact.fact_type_id or "payroll" in fact.fact_type_id or "price" in fact.fact_type_id else "SRC-US-FRED-DISTRIBUTION"
        surface = "SURF-US-BLS-API" if primary == "SRC-US-BLS" else "SURF-US-FRED-API"
        method = RetrievalMethod.OFFICIAL_API if primary == "SRC-US-BLS" else RetrievalMethod.APPROVED_SECONDARY_API
        sequence = (_step(SourceRole.PRIMARY_AUTHORITY, primary, surface, method),)
        purpose = "official_economic_release_retrieval" if primary == "SRC-US-BLS" else "corroboration"
        freshness = 86400
    return CanonicalSearchPlan(
        f"CSP-{fact.fact_type_id.upper()}",
        "1.0.0",
        fact.fact_type_id,
        fact.domain,
        "ACTIVE",
        "MO-SP-007",
        "1.0.0",
        ("Intelligence", "Sentinel", "Seeker", "Analyst", "Risk", "Trader", "Historian"),
        purpose,
        sequence,
        fact.required_identifiers,
        fact.required_fields,
        ("snippet", "generated_summary", "model_memory", "sample_payload", "unregistered_url"),
        100,
        10,
        "domain_policy_window",
        "domain_policy_window",
        freshness,
        ("authoritative_primary_fact_obtained", "mandatory_fields_obtained", "source_conflict_detected", "source_unavailable", "stale_only_evidence", "search_budget_exhausted"),
        tuple(status for status in CanonicalSearchStatus if status is not CanonicalSearchStatus.CERTIFIED),
        ("request_parameters", "raw_response_reference", "response_digest", "publication_timestamp", "retrieval_timestamp", "source_sequence_followed", "stop_rule_result"),
    )


def _fields_for(fact_type_id: str) -> tuple[str, ...]:
    if fact_type_id in {"current_bid", "current_ask"}:
        return (fact_type_id, "observation_timestamp", "venue", "delay_status", "raw_evidence_reference")
    if "price" in fact_type_id or "trade" in fact_type_id:
        return ("value", "observation_timestamp", "venue", "currency", "delay_status", "raw_evidence_reference")
    if "filing" in fact_type_id:
        return ("accession_number", "form_type", "filed_timestamp", "issuer_identity", "raw_evidence_reference")
    if "guidance" in fact_type_id or "earnings" in fact_type_id:
        return ("metric", "period", "publication_timestamp", "official_document_reference", "raw_evidence_reference")
    return ("value", "publication_timestamp", "source_identifier", "raw_evidence_reference")


def _step(role: SourceRole, source_id: str, surface_id: str, method: RetrievalMethod, required: bool = True) -> SourceStep:
    return SourceStep(role, source_id, surface_id, method, required)


def _authorization_request(request: CanonicalSearchRequest, plan: CanonicalSearchPlan, step: SourceStep) -> SourceAuthorizationRequest:
    fact_types, fields = _registry_fact_fields(plan, step)
    return SourceAuthorizationRequest(
        _stable_id("SPREQ", request.request_id, step.source_id, plan.fact_type_id),
        request.workflow_id,
        request.workflow_execution_token_id,
        request.requesting_office,
        "CanonicalSearchEngine",
        plan.authorized_purpose,
        step.source_id,
        step.surface_id,
        fact_types,
        fields,
        request.identifiers.get("asset_class", "equity"),
        tuple(value for value in request.identifiers.values() if value),
        request.identifiers.get("jurisdiction", "US"),
        request.environment,
        step.retrieval_method,
        CostClass.LICENSED_METERED if step.source_id == "SRC-LICENSED-SIP-MARKET-DATA" else CostClass.ZERO_MARGINAL_PUBLIC,
        request.decision_object_id,
        utc_timestamp(),
        _url_for(step, request),
    )


def _url_for(step: SourceStep, request: CanonicalSearchRequest) -> str:
    if step.surface_id == "SURF-US-SEC-SUBMISSIONS":
        return f"https://data.sec.gov/submissions/CIK{request.identifiers.get('issuer_id', 'UNKNOWN')}.json"
    if step.surface_id == "SURF-US-SEC-ENFORCEMENT-WEB":
        return "https://www.sec.gov/enforcement/search/issuer"
    if step.surface_id == "SURF-US-BLS-API":
        return "https://api.bls.gov/publicAPI/v2/timeseries/data/series"
    if step.surface_id == "SURF-US-FRED-API":
        return "https://api.stlouisfed.org/fred/series?series_id=SERIES"
    if step.surface_id == "SURF-LICENSED-SIP-API":
        return "https://sip.market-data/v1/quotes/security"
    return "https://investors.example-issuer-authority.invalid/"


def _registry_fact_fields(plan: CanonicalSearchPlan, step: SourceStep) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if step.source_id == "SRC-LICENSED-SIP-MARKET-DATA":
        return ("subscribed market prices",), ("last_trade", "market_timestamp", "delay_status")
    if step.source_id == "SRC-US-SEC-EDGAR":
        return ("regulatory_filing", "filing_metadata"), ("accession_number", "filing_form", "issuer_identity", "acceptance_timestamp", "filing_url")
    if step.source_id == "SRC-ISSUER-IR":
        return ("issuer_release",), ("issuer_release", "publication_timestamp", "official_url")
    if step.source_id == "SRC-US-SEC-ENFORCEMENT":
        return ("sec_enforcement_action",), ("release_number", "action_date", "respondent", "official_url", "publication_timestamp")
    if step.source_id == "SRC-US-BLS":
        return ("economic_indicator",), ("series_value", "release_timestamp", "series_metadata", "source_agency")
    if step.source_id == "SRC-US-FRED-DISTRIBUTION":
        return ("economic_indicator_distribution",), ("series_value", "source_agency", "retrieval_timestamp", "distribution_series_id")
    return (plan.fact_type_id,), plan.required_fields


def _certification(request: CanonicalSearchRequest, plan: CanonicalSearchPlan, status: CanonicalSearchStatus, reason: str, decisions: tuple[str, ...]) -> CanonicalSearchCertification:
    audit = CanonicalSearchAuditRecord(
        _stable_id("CSAUD", request.request_id, plan.search_plan_id, status.value, decisions),
        request.request_id,
        plan.search_plan_id,
        plan.fact_type_id,
        tuple(step.source_id for step in plan.source_sequence),
        decisions,
        status,
        reason or "canonical_request_certified",
        True,
        utc_timestamp(),
    )
    return CanonicalSearchCertification(request.request_id, plan, status, reason, audit)


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
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name != "plan_digest"}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
