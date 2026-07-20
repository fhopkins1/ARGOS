"""MO-SP-004 Seeker evidence acquisition engine.

The Seeker acquires source-attributed evidence only. It does not interpret,
rank truth, reconcile conflicts, score evidence, recommend trades, or perform
risk analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping, Protocol

from argos.foundation.contracts import utc_timestamp
from argos.intelligence import (
    CostClass,
    RetrievalMethod,
    SourceAuthorizationDecision,
    SourceAuthorizationGateway,
    SourceAuthorizationRequest,
)


MO_SP_004_VERSION = "MO-SP-004/1.0.0"
UNKNOWN = "UNKNOWN"


class SeekerEvidenceError(ValueError):
    """Raised when Seeker evidence acquisition authority is invalid."""


class InvestigationClass(str, Enum):
    UNUSUAL_PRICE_MOVEMENT = "unusual_price_movement"
    UNUSUAL_VOLUME = "unusual_volume"
    UNUSUAL_OPTIONS_ACTIVITY = "unusual_options_activity"
    EARNINGS_ANNOUNCEMENT = "earnings_announcement"
    EARNINGS_SURPRISE = "earnings_surprise"
    GUIDANCE_REVISION = "guidance_revision"
    SEC_FILING = "sec_filing"
    MERGER = "merger"
    ACQUISITION = "acquisition"
    SECURITIES_OFFERING = "securities_offering"
    DIVIDEND = "dividend"
    SPLIT = "split"
    BANKRUPTCY = "bankruptcy"
    EXECUTIVE_CHANGE = "executive_change"
    LITIGATION = "litigation"
    REGULATORY_INVESTIGATION = "regulatory_investigation"
    CREDIT_RATING_ACTION = "credit_rating_action"
    ANALYST_RATING_EVENT = "analyst_rating_event"
    MACROECONOMIC_RELEASE = "macroeconomic_release"
    FEDERAL_RESERVE_EVENT = "federal_reserve_event"
    GEOPOLITICAL_EVENT = "geopolitical_event"
    COMMODITY_DISRUPTION = "commodity_disruption"
    CYBERSECURITY_INCIDENT = "cybersecurity_incident"
    PRODUCT_RECALL = "product_recall"
    TRADING_HALT = "trading_halt"
    BROKER_DISCREPANCY = "broker_discrepancy"
    PORTFOLIO_DISCREPANCY = "portfolio_discrepancy"


class EvidenceState(str, Enum):
    COLLECTED = "COLLECTED"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_FOUND = "NOT_FOUND"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SOURCE_DOWN = "SOURCE_DOWN"
    TIMEOUT = "TIMEOUT"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    STALE = "STALE"
    CONFLICTED = "CONFLICTED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"


class SourceRole(str, Enum):
    PRIMARY = "PRIMARY"
    MANDATORY_CORROBORATING = "MANDATORY_CORROBORATING"
    CONTRARY = "CONTRARY"
    NEGATIVE = "NEGATIVE"
    FALLBACK = "FALLBACK"
    DISCOVERY = "DISCOVERY"


class TerminationReason(str, Enum):
    MANDATORY_SOURCES_COMPLETE = "mandatory_sources_complete"
    EVIDENCE_PACKAGE_COMPLETE = "evidence_package_complete"
    BUDGET_EXHAUSTED = "budget_exhausted"
    TIME_LIMIT_REACHED = "time_limit_reached"
    EVENT_IMMATERIAL = "event_immaterial"
    REQUIRED_SOURCE_UNAVAILABLE = "required_source_unavailable"
    ANALYST_REVIEW_REQUIRED = "analyst_review_required"
    HUMAN_ESCALATION_REQUIRED = "human_escalation_required"
    AUTHORITY_REJECTED = "authority_rejected"


@dataclass(frozen=True)
class InvestigationAuthorization:
    investigation_authorization_id: str
    authorized: bool
    authorized_by: str
    authorized_at: str


@dataclass(frozen=True)
class AssetIdentity:
    issuer_name: str
    ticker: str
    cusip: str = UNKNOWN
    cik: str = UNKNOWN
    exchange: str = UNKNOWN
    asset_class: str = "equity"
    security_type: str = "common_stock"
    industry: str = UNKNOWN
    sector: str = UNKNOWN
    jurisdiction: str = "US"
    aliases: tuple[str, ...] = ()
    former_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class SeekerInvestigationRequest:
    investigation_id: str
    workflow_id: str
    workflow_execution_token_id: str
    investigation_authorization: InvestigationAuthorization
    requesting_office: str
    decision_object_id: str
    asset: AssetIdentity
    investigation_class: InvestigationClass
    date_range: tuple[str, str]
    environment: str = "research"
    budget_api_cost: int = 25
    budget_query_count: int = 12
    budget_documents: int = 8
    budget_pages: int = 10
    budget_runtime_seconds: int = 300


@dataclass(frozen=True)
class EntityResolution:
    issuer: str
    ticker: str
    company_name: str
    exchange: str
    security_identifier: str
    industry: str
    sector: str
    aliases: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class SearchQuery:
    query_id: str
    source_role: SourceRole
    source_id: str
    surface_id: str
    retrieval_method: RetrievalMethod
    purpose: str
    fact_types: tuple[str, ...]
    fields: tuple[str, ...]
    query_terms: tuple[str, ...]
    negative_keywords: tuple[str, ...]
    date_range: tuple[str, str]
    final_url: str
    cost_class: CostClass
    required: bool


@dataclass(frozen=True)
class SearchStep:
    role: SourceRole
    source_id: str
    surface_id: str
    retrieval_method: RetrievalMethod
    purpose: str
    fact_types: tuple[str, ...]
    fields: tuple[str, ...]
    final_url_template: str
    required: bool = True


@dataclass(frozen=True)
class InvestigationSearchPlan:
    investigation_class: InvestigationClass
    primary_sources: tuple[SearchStep, ...]
    mandatory_corroborating_sources: tuple[SearchStep, ...]
    contrary_evidence_sources: tuple[SearchStep, ...]
    negative_search_sources: tuple[SearchStep, ...]
    fallback_sources: tuple[SearchStep, ...]
    discovery_sources: tuple[SearchStep, ...]
    lookback_windows: Mapping[str, str]

    @property
    def ordered_steps(self) -> tuple[SearchStep, ...]:
        return (
            self.primary_sources
            + self.mandatory_corroborating_sources
            + self.contrary_evidence_sources
            + self.negative_search_sources
            + self.fallback_sources
            + self.discovery_sources
        )


@dataclass(frozen=True)
class RetrievalResult:
    state: EvidenceState
    payload: Mapping[str, Any]
    publication_time: str
    document_identifier: str
    location: str
    raw_evidence_reference: str
    failure_reference: str = ""
    cache_indicator: str = "NO_CACHE"
    cost_units: int = 1


class EvidenceRetriever(Protocol):
    def retrieve(self, query: SearchQuery, request: SeekerInvestigationRequest) -> RetrievalResult:
        ...


@dataclass(frozen=True)
class EvidenceDocument:
    document_id: str
    source_id: str
    surface_id: str
    source_role: SourceRole
    publication_time: str
    retrieval_time: str
    document_identifier: str
    location: str
    payload_hash: str
    raw_evidence_reference: str


@dataclass(frozen=True)
class MissingEvidenceRecord:
    missing_id: str
    source_id: str
    surface_id: str
    source_role: SourceRole
    state: EvidenceState
    reason: str
    searched_at: str


@dataclass(frozen=True)
class SourceProvenance:
    provenance_id: str
    source_id: str
    retrieval_method: RetrievalMethod
    query_id: str
    retrieval_timestamp: str
    publication_timestamp: str
    document_reference: str
    evidence_hash: str
    authorization_decision_id: str


@dataclass(frozen=True)
class SearchAuditEvent:
    event_id: str
    event_type: str
    investigation_id: str
    query_id: str
    source_id: str
    timestamp: str
    detail: Mapping[str, Any]


@dataclass(frozen=True)
class BudgetState:
    api_cost: int = 0
    query_count: int = 0
    documents_retrieved: int = 0
    pages_retrieved: int = 0
    runtime_seconds: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


@dataclass(frozen=True)
class EvidencePackage:
    investigation_id: str
    workflow_id: str
    decision_object_id: str
    investigation_class: InvestigationClass
    asset: AssetIdentity
    entity_resolution: EntityResolution
    executed_search_plan: InvestigationSearchPlan
    executed_queries: tuple[SearchQuery, ...]
    executed_sources: tuple[str, ...]
    collected_documents: tuple[EvidenceDocument, ...]
    collected_structured_data: tuple[Mapping[str, Any], ...]
    collected_events: tuple[Mapping[str, Any], ...]
    negative_searches: tuple[MissingEvidenceRecord, ...]
    unavailable_searches: tuple[MissingEvidenceRecord, ...]
    contrary_evidence: tuple[EvidenceDocument, ...]
    source_provenance: tuple[SourceProvenance, ...]
    retrieval_metadata: tuple[Mapping[str, Any], ...]
    search_timing: Mapping[str, str]
    evidence_completeness_status: str
    search_cost: BudgetState
    termination_reason: TerminationReason
    audit_events: tuple[SearchAuditEvent, ...]
    evidence_hash: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_hash", stable_digest(self))


class StaticEvidenceRetriever:
    """Deterministic retriever for tests and offline certification inputs."""

    def __init__(self, results: Mapping[str, RetrievalResult]) -> None:
        self.results = dict(results)

    def retrieve(self, query: SearchQuery, request: SeekerInvestigationRequest) -> RetrievalResult:
        key = query.query_id
        if key in self.results:
            return self.results[key]
        role_key = f"{query.source_id}:{query.purpose}:{query.source_role.value}"
        if role_key in self.results:
            return self.results[role_key]
        if query.source_role is SourceRole.NEGATIVE:
            return RetrievalResult(EvidenceState.NOT_FOUND, MappingProxyType({}), UNKNOWN, "", "", "", failure_reference="negative_search_not_found")
        source_key = f"{query.source_id}:{query.purpose}"
        if source_key in self.results:
            return self.results[source_key]
        return RetrievalResult(EvidenceState.NOT_FOUND, MappingProxyType({}), UNKNOWN, "", "", "", failure_reference="not_found")


class SeekerEvidenceAcquisitionEngine:
    """Deterministic Seeker evidence acquisition engine."""

    def __init__(self, gateway: SourceAuthorizationGateway | None = None, retriever: EvidenceRetriever | None = None) -> None:
        self.gateway = gateway or SourceAuthorizationGateway()
        self.retriever = retriever or StaticEvidenceRetriever({})

    def acquire(self, request: SeekerInvestigationRequest) -> EvidencePackage:
        self._validate_authority(request)
        entity = resolve_entity(request.asset)
        if entity.status != "RESOLVED":
            return self._authority_failure_package(request, entity, TerminationReason.HUMAN_ESCALATION_REQUIRED, EvidenceState.UNKNOWN)
        plan = investigation_plan(request.investigation_class)
        queries = build_queries(request, entity, plan)
        audit: list[SearchAuditEvent] = []
        documents: list[EvidenceDocument] = []
        structured: list[Mapping[str, Any]] = []
        events: list[Mapping[str, Any]] = []
        negative: list[MissingEvidenceRecord] = []
        unavailable: list[MissingEvidenceRecord] = []
        contrary: list[EvidenceDocument] = []
        provenance: list[SourceProvenance] = []
        metadata: list[Mapping[str, Any]] = []
        budget = BudgetState()
        termination = TerminationReason.MANDATORY_SOURCES_COMPLETE
        started = utc_timestamp()

        for query in queries:
            if _budget_exceeded(request, budget):
                termination = TerminationReason.BUDGET_EXHAUSTED
                audit.append(_audit("budget_event", request, query, {"state": EvidenceState.BUDGET_EXHAUSTED.value}))
                break
            decision = self.gateway.authorize(_authorization_request(request, query))
            audit.append(_audit("authorization_decision", request, query, {"decision": decision.decision.value, "decision_code": decision.decision_code}))
            if not decision.authorized:
                record = _missing(query, EvidenceState.AUTHORIZATION_FAILED, decision.decision_code)
                unavailable.append(record)
                self.gateway.record_source_use(_authorization_request(request, query), decision, result_status=EvidenceState.AUTHORIZATION_FAILED.value, failure_reference=decision.decision_code)
                if query.source_role in {SourceRole.PRIMARY, SourceRole.MANDATORY_CORROBORATING}:
                    termination = TerminationReason.AUTHORITY_REJECTED
                continue
            result = self.retriever.retrieve(query, request)
            use = self.gateway.record_source_use(_authorization_request(request, query), decision, result_status=result.state.value, raw_evidence_reference=result.raw_evidence_reference, failure_reference=result.failure_reference, cache_indicator=result.cache_indicator, response_payload=result.payload)
            audit.append(_audit("source_retrieval", request, query, {"state": result.state.value, "use_evidence_id": use.use_evidence_id}))
            budget = _add_budget(budget, result, document=bool(result.payload))
            metadata.append(MappingProxyType({"query_id": query.query_id, "source_id": query.source_id, "state": result.state.value, "cache": result.cache_indicator, "cost_units": result.cost_units}))
            if result.state is EvidenceState.COLLECTED:
                document = _document(query, result)
                documents.append(document)
                structured.append(MappingProxyType(dict(result.payload)))
                events.append(MappingProxyType({"source_id": query.source_id, "document_id": document.document_id, "state": result.state.value}))
                if query.source_role is SourceRole.CONTRARY:
                    contrary.append(document)
                provenance.append(_provenance(query, result, decision))
                continue
            missing = _missing(query, result.state, result.failure_reference or result.state.value)
            if query.source_role is SourceRole.NEGATIVE:
                negative.append(missing)
            else:
                unavailable.append(missing)
            if query.required and query.source_role in {SourceRole.PRIMARY, SourceRole.MANDATORY_CORROBORATING}:
                termination = TerminationReason.REQUIRED_SOURCE_UNAVAILABLE

        completeness = _completeness(plan, documents, negative, unavailable, termination)
        finished = utc_timestamp()
        return EvidencePackage(
            request.investigation_id,
            request.workflow_id,
            request.decision_object_id,
            request.investigation_class,
            request.asset,
            entity,
            plan,
            tuple(queries[: budget.query_count + len([event for event in audit if event.event_type == "authorization_decision" and event.detail.get("decision") != "AUTHORIZED"])] or queries),
            tuple(dict.fromkeys(query.source_id for query in queries)),
            tuple(documents),
            tuple(structured),
            tuple(events),
            tuple(negative),
            tuple(unavailable),
            tuple(contrary),
            tuple(provenance),
            tuple(metadata),
            MappingProxyType({"started": started, "finished": finished}),
            completeness,
            budget,
            termination,
            tuple(audit + [_audit("evidence_package_generation", request, queries[0], {"completeness": completeness, "termination": termination.value})]),
        )

    def _validate_authority(self, request: SeekerInvestigationRequest) -> None:
        missing = []
        if not request.workflow_execution_token_id:
            missing.append("workflow_execution_token_id")
        if not request.investigation_authorization.authorized:
            missing.append("investigation_authorization")
        if not request.investigation_id:
            missing.append("investigation_id")
        if not request.requesting_office:
            missing.append("requesting_office")
        if not request.decision_object_id:
            missing.append("decision_object_id")
        if missing:
            raise SeekerEvidenceError(f"missing constitutional authority: {', '.join(missing)}")

    def _authority_failure_package(self, request: SeekerInvestigationRequest, entity: EntityResolution, reason: TerminationReason, state: EvidenceState) -> EvidencePackage:
        plan = investigation_plan(request.investigation_class)
        missing = MissingEvidenceRecord(stable_id("MISS", request.investigation_id, state.value), "", "", SourceRole.PRIMARY, state, "entity_resolution_failed", utc_timestamp())
        return EvidencePackage(request.investigation_id, request.workflow_id, request.decision_object_id, request.investigation_class, request.asset, entity, plan, (), (), (), (), (), (), (missing,), (), (), (), MappingProxyType({}), "INCOMPLETE", BudgetState(), reason, ())


def resolve_entity(asset: AssetIdentity) -> EntityResolution:
    security_identifier = asset.cusip if asset.cusip != UNKNOWN else asset.cik if asset.cik != UNKNOWN else UNKNOWN
    required = (asset.issuer_name, asset.ticker, asset.exchange, security_identifier)
    status = "RESOLVED" if all(item not in ("", UNKNOWN, None) for item in required) else "UNKNOWN_ENTITY"
    return EntityResolution(asset.issuer_name or UNKNOWN, asset.ticker.upper() if asset.ticker else UNKNOWN, asset.issuer_name or UNKNOWN, asset.exchange or UNKNOWN, security_identifier, asset.industry or UNKNOWN, asset.sector or UNKNOWN, tuple(dict.fromkeys(asset.aliases + asset.former_names)), status)


def investigation_plan(investigation_class: InvestigationClass) -> InvestigationSearchPlan:
    if investigation_class in {
        InvestigationClass.SEC_FILING,
        InvestigationClass.SECURITIES_OFFERING,
        InvestigationClass.BANKRUPTCY,
        InvestigationClass.REGULATORY_INVESTIGATION,
        InvestigationClass.LITIGATION,
    }:
        primary = (_sec_step(SourceRole.PRIMARY, "official_filing_retrieval"),)
        corroborating = (_issuer_step(SourceRole.MANDATORY_CORROBORATING, "official_issuer_release_retrieval"),)
        contrary = (_sec_enforcement_step(SourceRole.CONTRARY, "adversarial_review"),)
        negative = (_sec_step(SourceRole.NEGATIVE, "official_filing_retrieval"),)
    elif investigation_class in {
        InvestigationClass.EARNINGS_ANNOUNCEMENT,
        InvestigationClass.EARNINGS_SURPRISE,
        InvestigationClass.GUIDANCE_REVISION,
        InvestigationClass.MERGER,
        InvestigationClass.ACQUISITION,
        InvestigationClass.DIVIDEND,
        InvestigationClass.SPLIT,
        InvestigationClass.EXECUTIVE_CHANGE,
        InvestigationClass.PRODUCT_RECALL,
        InvestigationClass.CYBERSECURITY_INCIDENT,
    }:
        primary = (_issuer_step(SourceRole.PRIMARY, "official_issuer_release_retrieval"),)
        corroborating = (_sec_step(SourceRole.MANDATORY_CORROBORATING, "official_filing_retrieval"),)
        contrary = (_sec_enforcement_step(SourceRole.CONTRARY, "adversarial_review"),)
        negative = (_issuer_step(SourceRole.NEGATIVE, "official_issuer_release_retrieval"),)
    elif investigation_class in {InvestigationClass.TRADING_HALT, InvestigationClass.UNUSUAL_PRICE_MOVEMENT, InvestigationClass.UNUSUAL_VOLUME, InvestigationClass.UNUSUAL_OPTIONS_ACTIVITY}:
        primary = (_nyse_step(SourceRole.PRIMARY),)
        corroborating = (_sec_step(SourceRole.MANDATORY_CORROBORATING, "official_filing_retrieval"),)
        contrary = (_search_step(SourceRole.CONTRARY),)
        negative = (_nyse_step(SourceRole.NEGATIVE),)
    elif investigation_class in {InvestigationClass.MACROECONOMIC_RELEASE, InvestigationClass.FEDERAL_RESERVE_EVENT, InvestigationClass.GEOPOLITICAL_EVENT, InvestigationClass.COMMODITY_DISRUPTION}:
        primary = (_bls_step(SourceRole.PRIMARY),)
        corroborating = (_fred_step(SourceRole.MANDATORY_CORROBORATING),)
        contrary = (_search_step(SourceRole.CONTRARY),)
        negative = (_bls_step(SourceRole.NEGATIVE),)
    elif investigation_class in {InvestigationClass.BROKER_DISCREPANCY, InvestigationClass.PORTFOLIO_DISCREPANCY}:
        primary = (_broker_step(SourceRole.PRIMARY),)
        corroborating = ()
        contrary = (_broker_step(SourceRole.CONTRARY),)
        negative = (_broker_step(SourceRole.NEGATIVE),)
    elif investigation_class is InvestigationClass.CREDIT_RATING_ACTION:
        primary = (_issuer_step(SourceRole.PRIMARY, "official_issuer_release_retrieval"),)
        corroborating = (_sec_step(SourceRole.MANDATORY_CORROBORATING, "official_filing_retrieval"),)
        contrary = (_search_step(SourceRole.CONTRARY),)
        negative = (_search_step(SourceRole.NEGATIVE),)
    else:
        primary = (_search_step(SourceRole.PRIMARY),)
        corroborating = (_issuer_step(SourceRole.MANDATORY_CORROBORATING, "official_issuer_release_retrieval"),)
        contrary = (_search_step(SourceRole.CONTRARY),)
        negative = (_search_step(SourceRole.NEGATIVE),)
    return InvestigationSearchPlan(investigation_class, primary, corroborating, contrary, negative, (), (_search_step(SourceRole.DISCOVERY),), MappingProxyType({"event_window": "7d", "filing_window": "30d", "news_window": "7d", "market_window": "20 sessions", "economic_window": "30d"}))


def build_queries(request: SeekerInvestigationRequest, entity: EntityResolution, plan: InvestigationSearchPlan) -> tuple[SearchQuery, ...]:
    queries: list[SearchQuery] = []
    seen: set[str] = set()
    terms = _query_terms(request, entity)
    for index, step in enumerate(plan.ordered_steps, start=1):
        final_url = step.final_url_template.format(cik=request.asset.cik, ticker=request.asset.ticker.upper(), query="+".join(terms), issuer=request.asset.issuer_name.replace(" ", "+"))
        query = SearchQuery(
            stable_id("SEQ", request.investigation_id, step.source_id, step.role.value, tuple(terms)),
            step.role,
            step.source_id,
            step.surface_id,
            step.retrieval_method,
            step.purpose,
            step.fact_types,
            step.fields,
            terms,
            ("rumor", "unverified", "message-board"),
            request.date_range,
            final_url,
            _cost_for(step.source_id),
            step.required,
        )
        if query.query_id not in seen:
            seen.add(query.query_id)
            queries.append(query)
    return tuple(queries)


def stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{stable_digest(parts)[:24].upper()}"


def stable_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return {key: _jsonable(item) for key, item in value.items()}
    if is_dataclass(value):
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name != "evidence_hash"}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _query_terms(request: SeekerInvestigationRequest, entity: EntityResolution) -> tuple[str, ...]:
    terms = (
        entity.issuer,
        entity.ticker,
        request.investigation_class.value,
        request.asset.cik,
        request.asset.exchange,
        request.asset.asset_class,
        request.asset.security_type,
        request.asset.industry,
        request.asset.sector,
        request.asset.jurisdiction,
    ) + entity.aliases
    return tuple(dict.fromkeys(str(term).upper() for term in terms if term and term != UNKNOWN))


def _authorization_request(request: SeekerInvestigationRequest, query: SearchQuery) -> SourceAuthorizationRequest:
    return SourceAuthorizationRequest(
        stable_id("SPREQ", request.investigation_id, query.query_id),
        request.workflow_id,
        request.workflow_execution_token_id,
        "Seeker",
        "SeekerEvidenceAcquisitionEngine",
        query.purpose,
        query.source_id,
        query.surface_id,
        query.fact_types,
        query.fields,
        request.asset.asset_class,
        tuple(item for item in (request.asset.ticker, request.asset.cusip, request.asset.cik) if item and item != UNKNOWN),
        request.asset.jurisdiction,
        request.environment,
        query.retrieval_method,
        query.cost_class,
        request.decision_object_id,
        utc_timestamp(),
        query.final_url,
    )


def _document(query: SearchQuery, result: RetrievalResult) -> EvidenceDocument:
    payload_hash = stable_digest(result.payload)
    return EvidenceDocument(stable_id("DOC", query.query_id, payload_hash), query.source_id, query.surface_id, query.source_role, result.publication_time or UNKNOWN, utc_timestamp(), result.document_identifier, result.location, payload_hash, result.raw_evidence_reference)


def _missing(query: SearchQuery, state: EvidenceState, reason: str) -> MissingEvidenceRecord:
    return MissingEvidenceRecord(stable_id("MISS", query.query_id, state.value, reason), query.source_id, query.surface_id, query.source_role, state, reason, utc_timestamp())


def _provenance(query: SearchQuery, result: RetrievalResult, decision: SourceAuthorizationDecision) -> SourceProvenance:
    return SourceProvenance(stable_id("PROV", query.query_id, result.raw_evidence_reference), query.source_id, query.retrieval_method, query.query_id, utc_timestamp(), result.publication_time or UNKNOWN, result.document_identifier, stable_digest(result.payload), decision.authorization_decision_id)


def _audit(event_type: str, request: SeekerInvestigationRequest, query: SearchQuery, detail: Mapping[str, Any]) -> SearchAuditEvent:
    return SearchAuditEvent(stable_id("AUD", request.investigation_id, query.query_id, event_type, detail), event_type, request.investigation_id, query.query_id, query.source_id, utc_timestamp(), MappingProxyType(dict(detail)))


def _add_budget(budget: BudgetState, result: RetrievalResult, *, document: bool) -> BudgetState:
    return BudgetState(budget.api_cost + result.cost_units, budget.query_count + 1, budget.documents_retrieved + (1 if document else 0), budget.pages_retrieved + (0 if result.cache_indicator == "CACHE_HIT" else 1), budget.runtime_seconds, budget.cache_hits + (1 if result.cache_indicator == "CACHE_HIT" else 0), budget.cache_misses + (1 if result.cache_indicator != "CACHE_HIT" else 0))


def _budget_exceeded(request: SeekerInvestigationRequest, budget: BudgetState) -> bool:
    return (
        budget.api_cost >= request.budget_api_cost
        or budget.query_count >= request.budget_query_count
        or budget.documents_retrieved >= request.budget_documents
        or budget.pages_retrieved >= request.budget_pages
        or budget.runtime_seconds >= request.budget_runtime_seconds
    )


def _completeness(plan: InvestigationSearchPlan, documents: list[EvidenceDocument], negative: list[MissingEvidenceRecord], unavailable: list[MissingEvidenceRecord], termination: TerminationReason) -> str:
    if termination in {TerminationReason.AUTHORITY_REJECTED, TerminationReason.REQUIRED_SOURCE_UNAVAILABLE, TerminationReason.BUDGET_EXHAUSTED}:
        return "INCOMPLETE"
    required_roles = {step.role for step in plan.ordered_steps if step.required and step.role in {SourceRole.PRIMARY, SourceRole.MANDATORY_CORROBORATING, SourceRole.CONTRARY, SourceRole.NEGATIVE}}
    satisfied_roles = {doc.source_role for doc in documents} | {item.source_role for item in negative}
    required_unavailable = [item for item in unavailable if item.source_role in required_roles]
    return "COMPLETE" if required_roles.issubset(satisfied_roles) and not required_unavailable else "INCOMPLETE"


def _cost_for(source_id: str) -> CostClass:
    if source_id == "SRC-BROKER-OF-RECORD":
        return CostClass.BROKER_INCLUDED
    if source_id in {"SRC-SEARCH-ENGINE-DISCOVERY", "SRC-SOCIAL-EARLY-WARNING"}:
        return CostClass.LOW_MARGINAL_PUBLIC
    return CostClass.ZERO_MARGINAL_PUBLIC


def _sec_step(role: SourceRole, purpose: str) -> SearchStep:
    return SearchStep(role, "SRC-US-SEC-EDGAR", "SURF-US-SEC-SUBMISSIONS", RetrievalMethod.OFFICIAL_API, purpose, ("regulatory_filing",), ("accession_number", "filing_form", "issuer_identity", "acceptance_timestamp", "filing_url"), "https://data.sec.gov/submissions/CIK{cik}.json")


def _sec_enforcement_step(role: SourceRole, purpose: str) -> SearchStep:
    return SearchStep(role, "SRC-US-SEC-ENFORCEMENT", "SURF-US-SEC-ENFORCEMENT-WEB", RetrievalMethod.OFFICIAL_WEB_PAGE, purpose, ("sec_enforcement_action",), ("release_number", "action_date", "respondent", "order_text", "official_url", "publication_timestamp"), "https://www.sec.gov/enforcement/search/{query}")


def _issuer_step(role: SourceRole, purpose: str) -> SearchStep:
    return SearchStep(role, "SRC-ISSUER-IR", "SURF-ISSUER-IR-WEB", RetrievalMethod.OFFICIAL_WEB_PAGE, purpose, ("issuer_release",), ("issuer_release", "publication_timestamp", "official_url"), "https://investors.example-issuer-authority.invalid/{ticker}")


def _nyse_step(role: SourceRole) -> SearchStep:
    return SearchStep(role, "SRC-US-NYSE-MARKET-STATUS", "SURF-US-NYSE-STATUS-WEB", RetrievalMethod.OFFICIAL_WEB_PAGE, "halt_detection", ("trading_halt_status",), ("halt_symbol", "halt_reason", "status_timestamp", "market_session"), "https://www.nyse.com/trade-halt/{ticker}")


def _bls_step(role: SourceRole) -> SearchStep:
    return SearchStep(role, "SRC-US-BLS", "SURF-US-BLS-API", RetrievalMethod.OFFICIAL_API, "official_economic_release_retrieval", ("economic_indicator",), ("series_value", "release_timestamp", "series_metadata", "source_agency"), "https://api.bls.gov/publicAPI/v2/timeseries/data/{query}")


def _fred_step(role: SourceRole) -> SearchStep:
    return SearchStep(role, "SRC-US-FRED-DISTRIBUTION", "SURF-US-FRED-API", RetrievalMethod.APPROVED_SECONDARY_API, "corroboration", ("economic_indicator_distribution",), ("series_value", "source_agency", "retrieval_timestamp", "distribution_series_id"), "https://api.stlouisfed.org/fred/series?search_text={query}")


def _broker_step(role: SourceRole) -> SearchStep:
    return SearchStep(role, "SRC-BROKER-OF-RECORD", "SURF-BROKER-PAPER-API", RetrievalMethod.BROKER_API, "account_reconciliation", ("positions",), ("position_quantity", "cash_balance", "account_buying_power"), "https://broker.account-api/accounts/{ticker}")


def _search_step(role: SourceRole) -> SearchStep:
    return SearchStep(role, "SRC-SEARCH-ENGINE-DISCOVERY", "SURF-SEARCH-DISCOVERY", RetrievalMethod.SEARCH_ENGINE_DISCOVERY, "discovery", ("all",), ("discovery_result_url", "query", "ranking", "retrieval_timestamp", "engine_identity"), "https://search.example-authority.invalid/search?q={query}", required=role is not SourceRole.DISCOVERY)
