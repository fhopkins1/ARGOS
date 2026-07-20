"""MO-SP-005 Analyst verification search engine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp
from argos.intelligence import CostClass, RetrievalMethod, SourceAuthorizationGateway, SourceAuthorizationRequest
from argos.seeker import EvidencePackage, EvidenceState, InvestigationClass, SourceRole as SeekerSourceRole


MO_SP_005_VERSION = "MO-SP-005/1.0.0"


class AnalystVerificationError(ValueError):
    """Raised when an Analyst verification request violates doctrine."""


class VerificationQuestionID(str, Enum):
    PRICE_VERIFICATION = "PRICE_VERIFICATION"
    TRADING_VOLUME_VERIFICATION = "TRADING_VOLUME_VERIFICATION"
    EARNINGS_VERIFICATION = "EARNINGS_VERIFICATION"
    GUIDANCE_VERIFICATION = "GUIDANCE_VERIFICATION"
    REGULATORY_STATUS_VERIFICATION = "REGULATORY_STATUS_VERIFICATION"
    CORPORATE_ANNOUNCEMENT_VERIFICATION = "CORPORATE_ANNOUNCEMENT_VERIFICATION"
    CORPORATE_ACTION_VERIFICATION = "CORPORATE_ACTION_VERIFICATION"
    ECONOMIC_STATISTICS_VERIFICATION = "ECONOMIC_STATISTICS_VERIFICATION"
    LEGAL_PROCEEDINGS_VERIFICATION = "LEGAL_PROCEEDINGS_VERIFICATION"
    CREDIT_EVENT_VERIFICATION = "CREDIT_EVENT_VERIFICATION"
    MARKET_HALT_VERIFICATION = "MARKET_HALT_VERIFICATION"
    BROKER_EXECUTION_VERIFICATION = "BROKER_EXECUTION_VERIFICATION"
    POSITION_VERIFICATION = "POSITION_VERIFICATION"
    CAUSAL_CLAIM_VERIFICATION = "CAUSAL_CLAIM_VERIFICATION"


class EvidenceGapStatus(str, Enum):
    COMPLETE = "COMPLETE"
    MISSING = "MISSING"
    CONFLICTED = "CONFLICTED"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class VerificationOutcome(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    CONFLICTED = "CONFLICTED"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    RETURN_TO_SEEKER = "RETURN_TO_SEEKER"
    ESCALATE_TO_RISK = "ESCALATE_TO_RISK"


class CausalComponent(str, Enum):
    OBSERVED_FACT = "Observed Fact"
    SOURCE_INTERPRETATION = "Source Interpretation"
    MARKET_COMMENTARY = "Market Commentary"
    STATISTICAL_CORRELATION = "Statistical Correlation"
    DEMONSTRATED_CAUSATION = "Demonstrated Causation"


@dataclass(frozen=True)
class VerificationQuestion:
    question_id: VerificationQuestionID
    title: str
    required_sources: tuple[str, ...]
    required_fields: tuple[str, ...]
    originator_required: bool
    historical_context_allowed: bool


@dataclass(frozen=True)
class AnalystVerificationRequest:
    verification_request_id: str
    workflow_id: str
    workflow_execution_token_id: str
    decision_object_id: str
    claim_id: str
    verification_question_id: VerificationQuestionID
    evidence_package: EvidencePackage
    material_capital_exposure: bool = False
    historical_context_required: bool = False
    environment: str = "research"


@dataclass(frozen=True)
class VerificationPlan:
    verification_question_id: VerificationQuestionID
    claim_id: str
    investigation_class: InvestigationClass
    required_source_list: tuple[str, ...]
    source_retrieval_order: tuple[str, ...]
    required_evidence_items: tuple[str, ...]
    maximum_search_depth: int
    maximum_search_cost: int
    maximum_search_duration_seconds: int
    termination_rule: str
    historical_context_required: bool
    plan_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_digest", _stable_digest(self))


@dataclass(frozen=True)
class EvidenceGapRecord:
    gap_id: str
    claim_id: str
    source_id: str
    required_item: str
    status: EvidenceGapStatus
    reason: str
    detected_at: str


@dataclass(frozen=True)
class CausalClaimDecomposition:
    claim_id: str
    components: Mapping[CausalComponent, EvidenceGapStatus]
    conclusion: VerificationOutcome


@dataclass(frozen=True)
class VerificationAuditRecord:
    audit_id: str
    workflow_id: str
    decision_object_id: str
    verification_question_id: VerificationQuestionID
    claim_id: str
    requested_source: str
    retrieved_source: str
    query: str
    filters: Mapping[str, str]
    retrieval_timestamp: str
    publication_timestamp: str
    evidence_reference: str
    cache_status: str
    retry_history: tuple[str, ...]
    search_cost: int
    search_duration_seconds: int
    verification_result: VerificationOutcome
    termination_rule: str
    escalation_status: str


@dataclass(frozen=True)
class VerificationReport:
    request_id: str
    plan: VerificationPlan
    outcome: VerificationOutcome
    gap_records: tuple[EvidenceGapRecord, ...]
    causal_decomposition: CausalClaimDecomposition | None
    audit_records: tuple[VerificationAuditRecord, ...]
    independent_source_count: int
    report_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_digest", _stable_digest(self))


class AnalystVerificationPlanner:
    """Creates a frozen plan before Analyst verification execution starts."""

    def plan(self, request: AnalystVerificationRequest) -> VerificationPlan:
        question = verification_question_registry()[request.verification_question_id]
        if request.historical_context_required and not question.historical_context_allowed:
            raise AnalystVerificationError("historical context not authorized for verification question")
        return VerificationPlan(
            request.verification_question_id,
            request.claim_id,
            request.evidence_package.investigation_class,
            question.required_sources,
            question.required_sources,
            question.required_fields,
            len(question.required_sources),
            10,
            120,
            "terminate after all required evidence is present, conflicted, unavailable, stale, or budget bound",
            request.historical_context_required,
        )


class AnalystVerificationEngine:
    """Verifies only registered questions against retained Seeker evidence."""

    def __init__(self, gateway: SourceAuthorizationGateway | None = None) -> None:
        self.gateway = gateway or SourceAuthorizationGateway()
        self.planner = AnalystVerificationPlanner()

    def verify(self, request: AnalystVerificationRequest) -> VerificationReport:
        plan = self.planner.plan(request)
        gaps = _detect_gaps(plan, request)
        decisions = [_authorize(request, source_id, self.gateway) for source_id in plan.source_retrieval_order]
        auth_failures = [decision for decision in decisions if decision[1] != "AUTHORIZED"]
        independent_count = independent_originating_source_count(request.evidence_package)
        causal = _decompose_causal_claim(request, gaps) if request.verification_question_id is VerificationQuestionID.CAUSAL_CLAIM_VERIFICATION else None
        outcome = _outcome(request, gaps, auth_failures, independent_count, causal)
        audit = tuple(_audit(request, plan, source_id, decision_code, outcome) for source_id, decision_code in decisions)
        return VerificationReport(request.verification_request_id, plan, outcome, tuple(gaps), causal, audit, independent_count)


def verification_question_registry() -> Mapping[VerificationQuestionID, VerificationQuestion]:
    return MappingProxyType({
        VerificationQuestionID.PRICE_VERIFICATION: _question(VerificationQuestionID.PRICE_VERIFICATION, ("SRC-LICENSED-SIP-MARKET-DATA",), ("last_trade", "market_timestamp")),
        VerificationQuestionID.TRADING_VOLUME_VERIFICATION: _question(VerificationQuestionID.TRADING_VOLUME_VERIFICATION, ("SRC-LICENSED-SIP-MARKET-DATA",), ("volume", "market_timestamp")),
        VerificationQuestionID.EARNINGS_VERIFICATION: _question(VerificationQuestionID.EARNINGS_VERIFICATION, ("SRC-ISSUER-IR", "SRC-US-SEC-EDGAR"), ("reported_earnings_values", "publication_timestamp")),
        VerificationQuestionID.GUIDANCE_VERIFICATION: _question(VerificationQuestionID.GUIDANCE_VERIFICATION, ("SRC-ISSUER-IR", "SRC-US-SEC-EDGAR"), ("management_guidance", "publication_timestamp")),
        VerificationQuestionID.REGULATORY_STATUS_VERIFICATION: _question(VerificationQuestionID.REGULATORY_STATUS_VERIFICATION, ("SRC-US-SEC-ENFORCEMENT",), ("regulatory_status", "publication_timestamp")),
        VerificationQuestionID.CORPORATE_ANNOUNCEMENT_VERIFICATION: _question(VerificationQuestionID.CORPORATE_ANNOUNCEMENT_VERIFICATION, ("SRC-ISSUER-IR", "SRC-US-SEC-EDGAR"), ("issuer_release", "official_url")),
        VerificationQuestionID.CORPORATE_ACTION_VERIFICATION: _question(VerificationQuestionID.CORPORATE_ACTION_VERIFICATION, ("SRC-ISSUER-IR", "SRC-US-SEC-EDGAR"), ("corporate_action", "effective_date")),
        VerificationQuestionID.ECONOMIC_STATISTICS_VERIFICATION: _question(VerificationQuestionID.ECONOMIC_STATISTICS_VERIFICATION, ("SRC-US-BLS", "SRC-US-FRED-DISTRIBUTION"), ("series_value", "release_timestamp")),
        VerificationQuestionID.LEGAL_PROCEEDINGS_VERIFICATION: _question(VerificationQuestionID.LEGAL_PROCEEDINGS_VERIFICATION, ("SRC-US-SEC-ENFORCEMENT",), ("court_or_regulatory_record", "publication_timestamp")),
        VerificationQuestionID.CREDIT_EVENT_VERIFICATION: _question(VerificationQuestionID.CREDIT_EVENT_VERIFICATION, ("SRC-ISSUER-IR", "SRC-US-SEC-EDGAR"), ("credit_event", "official_document_reference")),
        VerificationQuestionID.MARKET_HALT_VERIFICATION: _question(VerificationQuestionID.MARKET_HALT_VERIFICATION, ("SRC-US-NYSE-MARKET-STATUS",), ("halt_symbol", "status_timestamp")),
        VerificationQuestionID.BROKER_EXECUTION_VERIFICATION: _question(VerificationQuestionID.BROKER_EXECUTION_VERIFICATION, ("SRC-BROKER-OF-RECORD",), ("broker_order_acceptance", "broker_fill")),
        VerificationQuestionID.POSITION_VERIFICATION: _question(VerificationQuestionID.POSITION_VERIFICATION, ("SRC-BROKER-OF-RECORD",), ("position_quantity", "cash_balance")),
        VerificationQuestionID.CAUSAL_CLAIM_VERIFICATION: _question(VerificationQuestionID.CAUSAL_CLAIM_VERIFICATION, ("SRC-US-SEC-EDGAR", "SRC-ISSUER-IR"), ("observed_fact", "source_interpretation", "demonstrated_causation")),
    })


def _question(question_id: VerificationQuestionID, sources: tuple[str, ...], fields: tuple[str, ...]) -> VerificationQuestion:
    return VerificationQuestion(question_id, question_id.value.replace("_", " ").title(), sources, fields, True, question_id in {VerificationQuestionID.EARNINGS_VERIFICATION, VerificationQuestionID.GUIDANCE_VERIFICATION, VerificationQuestionID.CAUSAL_CLAIM_VERIFICATION})


def _detect_gaps(plan: VerificationPlan, request: AnalystVerificationRequest) -> list[EvidenceGapRecord]:
    documents_by_source = {document.source_id: document for document in request.evidence_package.collected_documents}
    structured = tuple(dict(item) for item in request.evidence_package.collected_structured_data)
    gaps: list[EvidenceGapRecord] = []
    for source_id in plan.required_source_list:
        if source_id not in documents_by_source:
            gaps.append(_gap(request.claim_id, source_id, "originating_source", EvidenceGapStatus.MISSING, "mandatory originating source absent from Seeker package"))
    for item in plan.required_evidence_items:
        if not any(item in row or any(item in str(value) for value in row.values()) for row in structured):
            gaps.append(_gap(request.claim_id, "PACKAGE", item, EvidenceGapStatus.MISSING, "required evidence item absent from retained evidence"))
    for missing in request.evidence_package.unavailable_searches:
        if missing.source_id in plan.required_source_list:
            status = EvidenceGapStatus.UNAVAILABLE if missing.state in {EvidenceState.UNAVAILABLE, EvidenceState.SOURCE_DOWN, EvidenceState.AUTHORIZATION_FAILED} else EvidenceGapStatus.MISSING
            gaps.append(_gap(request.claim_id, missing.source_id, "source_availability", status, missing.reason))
    if request.evidence_package.evidence_completeness_status == "CONFLICTED":
        gaps.append(_gap(request.claim_id, "PACKAGE", "conflict_state", EvidenceGapStatus.CONFLICTED, "Seeker package contains unresolved conflict"))
    return gaps


def independent_originating_source_count(package: EvidencePackage) -> int:
    originators = {
        document.source_id
        for document in package.collected_documents
        if document.source_role in {SeekerSourceRole.PRIMARY, SeekerSourceRole.MANDATORY_CORROBORATING, SeekerSourceRole.CONTRARY}
        and document.source_id not in {"SRC-SEARCH-ENGINE-DISCOVERY", "SRC-SOCIAL-EARLY-WARNING"}
    }
    return len(originators)


def _decompose_causal_claim(request: AnalystVerificationRequest, gaps: list[EvidenceGapRecord]) -> CausalClaimDecomposition:
    gap_items = {gap.required_item for gap in gaps}
    components = {
        CausalComponent.OBSERVED_FACT: EvidenceGapStatus.MISSING if "observed_fact" in gap_items else EvidenceGapStatus.COMPLETE,
        CausalComponent.SOURCE_INTERPRETATION: EvidenceGapStatus.MISSING if "source_interpretation" in gap_items else EvidenceGapStatus.COMPLETE,
        CausalComponent.MARKET_COMMENTARY: EvidenceGapStatus.COMPLETE,
        CausalComponent.STATISTICAL_CORRELATION: EvidenceGapStatus.UNAVAILABLE,
        CausalComponent.DEMONSTRATED_CAUSATION: EvidenceGapStatus.MISSING if "demonstrated_causation" in gap_items else EvidenceGapStatus.COMPLETE,
    }
    conclusion = VerificationOutcome.VERIFIED if all(status is EvidenceGapStatus.COMPLETE for status in components.values()) else VerificationOutcome.UNKNOWN
    return CausalClaimDecomposition(request.claim_id, MappingProxyType(components), conclusion)


def _outcome(
    request: AnalystVerificationRequest,
    gaps: list[EvidenceGapRecord],
    auth_failures: list[tuple[str, str]],
    independent_count: int,
    causal: CausalClaimDecomposition | None,
) -> VerificationOutcome:
    if any(gap.status is EvidenceGapStatus.CONFLICTED for gap in gaps):
        return VerificationOutcome.CONFLICTED
    if auth_failures:
        return VerificationOutcome.RETURN_TO_SEEKER
    if any(gap.status in {EvidenceGapStatus.MISSING, EvidenceGapStatus.UNAVAILABLE} for gap in gaps):
        if request.material_capital_exposure:
            return VerificationOutcome.ESCALATE_TO_RISK
        return VerificationOutcome.RETURN_TO_SEEKER
    if causal and causal.conclusion is not VerificationOutcome.VERIFIED:
        return VerificationOutcome.UNKNOWN
    if independent_count == 1 and len(request.evidence_package.collected_documents) > 1:
        return VerificationOutcome.PARTIALLY_VERIFIED
    return VerificationOutcome.VERIFIED


def _authorize(request: AnalystVerificationRequest, source_id: str, gateway: SourceAuthorizationGateway) -> tuple[str, str]:
    surface_method = {
        "SRC-US-SEC-EDGAR": ("SURF-US-SEC-SUBMISSIONS", RetrievalMethod.OFFICIAL_API, CostClass.ZERO_MARGINAL_PUBLIC, "official_filing_retrieval"),
        "SRC-US-SEC-ENFORCEMENT": ("SURF-US-SEC-ENFORCEMENT-WEB", RetrievalMethod.OFFICIAL_WEB_PAGE, CostClass.ZERO_MARGINAL_PUBLIC, "adversarial_review"),
        "SRC-ISSUER-IR": ("SURF-ISSUER-IR-WEB", RetrievalMethod.OFFICIAL_WEB_PAGE, CostClass.ZERO_MARGINAL_PUBLIC, "official_issuer_release_retrieval"),
        "SRC-US-BLS": ("SURF-US-BLS-API", RetrievalMethod.OFFICIAL_API, CostClass.ZERO_MARGINAL_PUBLIC, "official_economic_release_retrieval"),
        "SRC-US-FRED-DISTRIBUTION": ("SURF-US-FRED-API", RetrievalMethod.APPROVED_SECONDARY_API, CostClass.ZERO_MARGINAL_PUBLIC, "corroboration"),
        "SRC-US-NYSE-MARKET-STATUS": ("SURF-US-NYSE-STATUS-WEB", RetrievalMethod.OFFICIAL_WEB_PAGE, CostClass.ZERO_MARGINAL_PUBLIC, "halt_detection"),
        "SRC-BROKER-OF-RECORD": ("SURF-BROKER-PAPER-API", RetrievalMethod.BROKER_API, CostClass.BROKER_INCLUDED, "account_reconciliation"),
        "SRC-LICENSED-SIP-MARKET-DATA": ("SURF-LICENSED-SIP-API", RetrievalMethod.LICENSED_PROVIDER_API, CostClass.LICENSED_METERED, "market_data_observation"),
    }[source_id]
    surface, method, cost, purpose = surface_method
    fact_types, fields = _registry_fact_fields(source_id, request.verification_question_id)
    auth = SourceAuthorizationRequest(
        _stable_id("AVREQ", request.verification_request_id, source_id),
        request.workflow_id,
        request.workflow_execution_token_id,
        "Analyst",
        "AnalystVerificationEngine",
        purpose,
        source_id,
        surface,
        fact_types,
        fields,
        request.evidence_package.asset.asset_class,
        (request.evidence_package.asset.ticker, request.evidence_package.asset.cusip, request.evidence_package.asset.cik),
        request.evidence_package.asset.jurisdiction,
        request.environment,
        method,
        cost,
        request.decision_object_id,
        utc_timestamp(),
        _url(surface),
    )
    decision = gateway.authorize(auth)
    return source_id, decision.decision_code


def _registry_fact_fields(source_id: str, question_id: VerificationQuestionID) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if source_id == "SRC-LICENSED-SIP-MARKET-DATA":
        return ("subscribed market prices",), ("last_trade", "market_timestamp", "delay_status")
    if source_id == "SRC-US-SEC-EDGAR":
        return ("regulatory_filing", "filing_metadata"), ("accession_number", "filing_form", "issuer_identity", "acceptance_timestamp", "filing_url")
    if source_id == "SRC-US-SEC-ENFORCEMENT":
        return ("sec_enforcement_action",), ("release_number", "action_date", "respondent", "official_url", "publication_timestamp")
    if source_id == "SRC-ISSUER-IR":
        if question_id is VerificationQuestionID.CORPORATE_ACTION_VERIFICATION:
            return ("corporate_action_notice",), ("corporate_action_notice", "publication_timestamp", "official_url")
        if question_id is VerificationQuestionID.EARNINGS_VERIFICATION:
            return ("earnings_release",), ("earnings_release", "publication_timestamp", "official_url")
        return ("issuer_release",), ("issuer_release", "publication_timestamp", "official_url")
    if source_id == "SRC-US-BLS":
        return ("economic_indicator",), ("series_value", "release_timestamp", "series_metadata", "source_agency")
    if source_id == "SRC-US-FRED-DISTRIBUTION":
        return ("economic_indicator_distribution",), ("series_value", "source_agency", "retrieval_timestamp", "distribution_series_id")
    if source_id == "SRC-US-NYSE-MARKET-STATUS":
        return ("trading_halt_status",), ("halt_symbol", "status_timestamp", "market_session")
    if source_id == "SRC-BROKER-OF-RECORD":
        return ("accepted orders", "fills", "positions"), ("broker_order_acceptance", "broker_fill", "position_quantity")
    return (question_id.value.lower(),), verification_question_registry()[question_id].required_fields


def _url(surface: str) -> str:
    return {
        "SURF-US-SEC-SUBMISSIONS": "https://data.sec.gov/submissions/CIK0000320193.json",
        "SURF-US-SEC-ENFORCEMENT-WEB": "https://www.sec.gov/enforcement/search/aapl",
        "SURF-ISSUER-IR-WEB": "https://investors.example-issuer-authority.invalid/AAPL",
        "SURF-US-BLS-API": "https://api.bls.gov/publicAPI/v2/timeseries/data/CPI",
        "SURF-US-FRED-API": "https://api.stlouisfed.org/fred/series?series_id=CPI",
        "SURF-US-NYSE-STATUS-WEB": "https://www.nyse.com/trade-halt/AAPL",
        "SURF-BROKER-PAPER-API": "https://broker.account-api/accounts/AAPL",
        "SURF-LICENSED-SIP-API": "https://sip.market-data/v1/quotes/AAPL",
    }[surface]


def _gap(claim_id: str, source_id: str, item: str, status: EvidenceGapStatus, reason: str) -> EvidenceGapRecord:
    return EvidenceGapRecord(_stable_id("AVGAP", claim_id, source_id, item, status.value), claim_id, source_id, item, status, reason, utc_timestamp())


def _audit(request: AnalystVerificationRequest, plan: VerificationPlan, source_id: str, decision_code: str, outcome: VerificationOutcome) -> VerificationAuditRecord:
    return VerificationAuditRecord(
        _stable_id("AVAUD", request.verification_request_id, source_id, outcome.value),
        request.workflow_id,
        request.decision_object_id,
        request.verification_question_id,
        request.claim_id,
        source_id,
        source_id if decision_code == "AUTHORIZED" else "",
        f"{request.claim_id}:{request.verification_question_id.value}",
        MappingProxyType({"sequence": ",".join(plan.source_retrieval_order)}),
        utc_timestamp(),
        "UNKNOWN",
        request.evidence_package.evidence_hash,
        "NO_CACHE",
        (),
        1,
        0,
        outcome,
        plan.termination_rule,
        "ESCALATED" if outcome is VerificationOutcome.ESCALATE_TO_RISK else "NONE",
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
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name not in {"plan_digest", "report_digest"}}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
