"""MO-TR-006 corporate, filing, and issuer-information reconciliation doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from decimal import Decimal
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_006_VERSION = "MO-TR-006/1.0.0"


class CorporateFactDomain(str, Enum):
    REVENUE = "REVENUE"
    NET_REVENUE = "NET_REVENUE"
    GROSS_PROFIT = "GROSS_PROFIT"
    OPERATING_INCOME = "OPERATING_INCOME"
    NET_INCOME = "NET_INCOME"
    EARNINGS_PER_SHARE = "EARNINGS_PER_SHARE"
    DILUTED_EARNINGS_PER_SHARE = "DILUTED_EARNINGS_PER_SHARE"
    BASIC_EARNINGS_PER_SHARE = "BASIC_EARNINGS_PER_SHARE"
    ADJUSTED_EARNINGS = "ADJUSTED_EARNINGS"
    EBITDA = "EBITDA"
    ADJUSTED_EBITDA = "ADJUSTED_EBITDA"
    FREE_CASH_FLOW = "FREE_CASH_FLOW"
    OPERATING_CASH_FLOW = "OPERATING_CASH_FLOW"
    CAPITAL_EXPENDITURES = "CAPITAL_EXPENDITURES"
    TOTAL_ASSETS = "TOTAL_ASSETS"
    TOTAL_LIABILITIES = "TOTAL_LIABILITIES"
    SHAREHOLDERS_EQUITY = "SHAREHOLDERS_EQUITY"
    CASH_AND_EQUIVALENTS = "CASH_AND_EQUIVALENTS"
    DEBT = "DEBT"
    NET_DEBT = "NET_DEBT"
    SHARE_COUNT = "SHARE_COUNT"
    DILUTED_SHARE_COUNT = "DILUTED_SHARE_COUNT"
    SEGMENT_REVENUE = "SEGMENT_REVENUE"
    SEGMENT_PROFIT = "SEGMENT_PROFIT"
    GEOGRAPHIC_REVENUE = "GEOGRAPHIC_REVENUE"
    GUIDANCE = "GUIDANCE"
    GUIDANCE_RANGE = "GUIDANCE_RANGE"
    GUIDANCE_ASSUMPTION = "GUIDANCE_ASSUMPTION"
    DIVIDEND = "DIVIDEND"
    STOCK_SPLIT = "STOCK_SPLIT"
    SHARE_REPURCHASE = "SHARE_REPURCHASE"
    SECURITIES_OFFERING = "SECURITIES_OFFERING"
    MERGER = "MERGER"
    ACQUISITION = "ACQUISITION"
    DIVESTITURE = "DIVESTITURE"
    BANKRUPTCY = "BANKRUPTCY"
    RESTRUCTURING = "RESTRUCTURING"
    MANAGEMENT_CHANGE = "MANAGEMENT_CHANGE"
    BOARD_CHANGE = "BOARD_CHANGE"
    AUDITOR_CHANGE = "AUDITOR_CHANGE"
    ACCOUNTING_POLICY_CHANGE = "ACCOUNTING_POLICY_CHANGE"
    RESTATEMENT = "RESTATEMENT"
    GOING_CONCERN = "GOING_CONCERN"
    MATERIAL_WEAKNESS = "MATERIAL_WEAKNESS"
    INTERNAL_CONTROL_DEFICIENCY = "INTERNAL_CONTROL_DEFICIENCY"
    RISK_DISCLOSURE = "RISK_DISCLOSURE"
    LEGAL_CONTINGENCY = "LEGAL_CONTINGENCY"
    REGULATORY_DISCLOSURE = "REGULATORY_DISCLOSURE"
    RELATED_PARTY_TRANSACTION = "RELATED_PARTY_TRANSACTION"
    INSIDER_TRANSACTION = "INSIDER_TRANSACTION"
    OWNERSHIP_DISCLOSURE = "OWNERSHIP_DISCLOSURE"
    DEBT_COVENANT = "DEBT_COVENANT"
    CREDIT_FACILITY = "CREDIT_FACILITY"
    LIQUIDITY_DISCLOSURE = "LIQUIDITY_DISCLOSURE"
    BACKLOG = "BACKLOG"
    BOOKINGS = "BOOKINGS"
    ORDER_INTAKE = "ORDER_INTAKE"
    SUBSCRIBER_METRIC = "SUBSCRIBER_METRIC"
    UNIT_ECONOMIC = "UNIT_ECONOMIC"
    OPERATIONAL_KPI = "OPERATIONAL_KPI"
    OTHER_CORPORATE_FACT = "OTHER_CORPORATE_FACT"


class CorporateSourceClass(str, Enum):
    FILED_REGULATORY_DOCUMENT = "FILED_REGULATORY_DOCUMENT"
    AMENDED_REGULATORY_DOCUMENT = "AMENDED_REGULATORY_DOCUMENT"
    FINAL_REGULATORY_ORDER = "FINAL_REGULATORY_ORDER"
    ISSUER_EARNINGS_RELEASE = "ISSUER_EARNINGS_RELEASE"
    ISSUER_PRESS_RELEASE = "ISSUER_PRESS_RELEASE"
    ISSUER_INVESTOR_PRESENTATION = "ISSUER_INVESTOR_PRESENTATION"
    ISSUER_PREPARED_REMARKS = "ISSUER_PREPARED_REMARKS"
    ISSUER_CALL_TRANSCRIPT = "ISSUER_CALL_TRANSCRIPT"
    ISSUER_MANAGEMENT_INTERVIEW = "ISSUER_MANAGEMENT_INTERVIEW"
    OFFICIAL_EXCHANGE_NOTICE = "OFFICIAL_EXCHANGE_NOTICE"
    OFFICIAL_BANKRUPTCY_RECORD = "OFFICIAL_BANKRUPTCY_RECORD"
    OFFICIAL_COURT_RECORD = "OFFICIAL_COURT_RECORD"
    RECOGNIZED_NEWSWIRE = "RECOGNIZED_NEWSWIRE"
    ESTABLISHED_SECONDARY_PUBLICATION = "ESTABLISHED_SECONDARY_PUBLICATION"
    ANALYST_RESEARCH = "ANALYST_RESEARCH"
    CONSENSUS_DATASET = "CONSENSUS_DATASET"
    MARKET_DATA_VENDOR = "MARKET_DATA_VENDOR"
    SOCIAL_MEDIA_CLAIM = "SOCIAL_MEDIA_CLAIM"
    PUBLIC_FORUM_CLAIM = "PUBLIC_FORUM_CLAIM"
    UNKNOWN_SOURCE_CLASS = "UNKNOWN_SOURCE_CLASS"


class AccountingBasis(str, Enum):
    GAAP = "GAAP"
    IFRS = "IFRS"
    NON_GAAP = "NON_GAAP"
    ISSUER_DEFINED_ADJUSTED = "ISSUER_DEFINED_ADJUSTED"
    CONSENSUS_ESTIMATE = "CONSENSUS_ESTIMATE"
    ANALYST_ESTIMATE = "ANALYST_ESTIMATE"
    UNKNOWN = "UNKNOWN"


class CorporateVersionState(str, Enum):
    ORIGINAL = "ORIGINAL"
    AMENDED = "AMENDED"
    CORRECTED = "CORRECTED"
    RESTATED = "RESTATED"
    PROVISIONAL = "PROVISIONAL"
    SUPERSEDED = "SUPERSEDED"
    UNKNOWN_VERSION = "UNKNOWN_VERSION"


class CorporateReconciliationState(str, Enum):
    RECONCILED_AUTHORITATIVE = "RECONCILED_AUTHORITATIVE"
    PROVISIONAL_AUTHORITATIVE = "PROVISIONAL_AUTHORITATIVE"
    DIFFERENT_DEFINITION = "DIFFERENT_DEFINITION"
    DIFFERENT_PERIOD = "DIFFERENT_PERIOD"
    DIFFERENT_ISSUER_OR_SECURITY = "DIFFERENT_ISSUER_OR_SECURITY"
    SUPERSEDED_BY_AMENDMENT = "SUPERSEDED_BY_AMENDMENT"
    CONFLICTED_AUTHORITATIVE_FACT = "CONFLICTED_AUTHORITATIVE_FACT"
    ESTIMATE_ONLY = "ESTIMATE_ONLY"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    ESCALATE_ANALYST = "ESCALATE_ANALYST"
    ESCALATE_RISK = "ESCALATE_RISK"
    TRADE_BLOCKED = "TRADE_BLOCKED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CorporateObservation:
    corporate_observation_id: str
    workflow_id: str
    issuer_id: str
    security_id: str
    fact_domain: CorporateFactDomain
    reporting_period: str
    period_start: str
    period_end: str
    accounting_basis: AccountingBasis
    metric_definition: str
    value: str
    unit: str
    currency: str
    source_class: CorporateSourceClass
    document_id: str
    document_version: CorporateVersionState
    filing_status: str
    publication_time: str
    effective_time: str
    amended_sections: tuple[str, ...]
    supersedes_document_id: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class CorporateReconciliationRecord:
    reconciliation_id: str
    workflow_id: str
    issuer_id: str
    security_id: str
    fact_domain: CorporateFactDomain
    observation_ids: tuple[str, ...]
    observation_hashes: tuple[str, ...]
    selected_observation_id: str
    state: CorporateReconciliationState
    authority_rule: str
    required_action: str
    affected_offices: tuple[str, ...]
    doctrine_version: str
    evidence_references: tuple[str, ...]
    created_at: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class CorporateReconciliationLedger:
    def __init__(self) -> None:
        self._records: dict[str, CorporateReconciliationRecord] = {}

    def append(self, record: CorporateReconciliationRecord) -> None:
        if record.reconciliation_id in self._records:
            raise ValueError("corporate reconciliations are append-only")
        self._records[record.reconciliation_id] = record

    def all_records(self) -> tuple[CorporateReconciliationRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))


class CorporateReconciliationEngine:
    def __init__(self, ledger: CorporateReconciliationLedger | None = None) -> None:
        self.ledger = ledger or CorporateReconciliationLedger()

    def reconcile(self, observations: tuple[CorporateObservation, ...]) -> CorporateReconciliationRecord:
        if not observations:
            return self._record((), "", CorporateFactDomain.OTHER_CORPORATE_FACT, CorporateReconciliationState.UNKNOWN, "no_observations", "return_to_seeker", ("Seeker",))
        first = observations[0]
        if any(obs.issuer_id != first.issuer_id or obs.security_id != first.security_id for obs in observations):
            return self._record(observations, "", first.fact_domain, CorporateReconciliationState.DIFFERENT_ISSUER_OR_SECURITY, "issuer_security_identity_mismatch", "return_to_seeker", ("Seeker", "Analyst"))
        if any(obs.reporting_period != first.reporting_period for obs in observations):
            return self._record(observations, "", first.fact_domain, CorporateReconciliationState.DIFFERENT_PERIOD, "reporting_period_mismatch", "preserve_separately", ("Analyst",))
        if any(obs.fact_domain != first.fact_domain or obs.accounting_basis != first.accounting_basis or obs.metric_definition != first.metric_definition for obs in observations):
            return self._record(observations, "", first.fact_domain, CorporateReconciliationState.DIFFERENT_DEFINITION, "definition_or_accounting_basis_mismatch", "do_not_merge_gaap_non_gaap", ("Analyst",))

        amended = [obs for obs in observations if obs.source_class is CorporateSourceClass.AMENDED_REGULATORY_DOCUMENT]
        if amended:
            selected = sorted(amended, key=lambda obs: (obs.publication_time, obs.corporate_observation_id))[-1]
            return self._record(observations, selected.corporate_observation_id, first.fact_domain, CorporateReconciliationState.SUPERSEDED_BY_AMENDMENT, "amended_filing_supersedes_only_amended_facts", "preserve_original_and_reconcile_affected_sections", ("Analyst", "Historian"))

        authoritative = [obs for obs in observations if _authority_rank(obs.source_class) == 1]
        if authoritative:
            values = {obs.value for obs in authoritative}
            if len(values) > 1:
                return self._record(observations, "", first.fact_domain, CorporateReconciliationState.CONFLICTED_AUTHORITATIVE_FACT, "conflicting_primary_documents", "escalate_without_selection", ("Analyst", "Risk"))
            selected = sorted(authoritative, key=lambda obs: (obs.publication_time, obs.corporate_observation_id))[-1]
            return self._record(observations, selected.corporate_observation_id, first.fact_domain, CorporateReconciliationState.RECONCILED_AUTHORITATIVE, "filed_regulatory_or_final_official_record_prevails", "promote_with_evidence", ("Analyst", "Historian"))

        issuer = [obs for obs in observations if obs.source_class in {CorporateSourceClass.ISSUER_EARNINGS_RELEASE, CorporateSourceClass.ISSUER_PRESS_RELEASE}]
        if issuer and first.fact_domain in {CorporateFactDomain.GUIDANCE, CorporateFactDomain.GUIDANCE_RANGE, CorporateFactDomain.GUIDANCE_ASSUMPTION}:
            selected = sorted(issuer, key=lambda obs: (obs.publication_time, obs.corporate_observation_id))[-1]
            return self._record(observations, selected.corporate_observation_id, first.fact_domain, CorporateReconciliationState.PROVISIONAL_AUTHORITATIVE, "issuer_guidance_authoritative_within_declared_scope", "label_provisional_until_filed_or_updated", ("Analyst", "Risk"))

        estimates = [obs for obs in observations if obs.accounting_basis in {AccountingBasis.CONSENSUS_ESTIMATE, AccountingBasis.ANALYST_ESTIMATE}]
        if estimates:
            return self._record(observations, "", first.fact_domain, CorporateReconciliationState.ESTIMATE_ONLY, "estimate_dataset_not_reported_actual", "do_not_substitute_for_reported_result", ("Analyst",))

        return self._record(observations, "", first.fact_domain, CorporateReconciliationState.DISCOVERY_ONLY, "no_primary_corporate_authority", "collect_authoritative_document", ("Seeker", "Analyst"))

    def _record(self, observations: tuple[CorporateObservation, ...], selected: str, domain: CorporateFactDomain, state: CorporateReconciliationState, rule: str, action: str, offices: tuple[str, ...]) -> CorporateReconciliationRecord:
        workflow = observations[0].workflow_id if observations else ""
        issuer = observations[0].issuer_id if observations else ""
        security = observations[0].security_id if observations else ""
        record = CorporateReconciliationRecord(_stable_id("CORPREC", tuple(obs.corporate_observation_id for obs in observations), selected, state.value), workflow, issuer, security, domain, tuple(obs.corporate_observation_id for obs in observations), tuple(_stable_digest(obs) for obs in observations), selected, state, rule, action, offices, MO_TR_006_VERSION, tuple(ref for obs in observations for ref in obs.evidence_references), utc_timestamp())
        self.ledger.append(record)
        return record


def _authority_rank(source_class: CorporateSourceClass) -> int:
    if source_class in {CorporateSourceClass.FILED_REGULATORY_DOCUMENT, CorporateSourceClass.FINAL_REGULATORY_ORDER, CorporateSourceClass.OFFICIAL_BANKRUPTCY_RECORD, CorporateSourceClass.OFFICIAL_COURT_RECORD, CorporateSourceClass.OFFICIAL_EXCHANGE_NOTICE}:
        return 1
    if source_class in {CorporateSourceClass.ISSUER_EARNINGS_RELEASE, CorporateSourceClass.ISSUER_PRESS_RELEASE}:
        return 2
    if source_class in {CorporateSourceClass.RECOGNIZED_NEWSWIRE, CorporateSourceClass.ESTABLISHED_SECONDARY_PUBLICATION}:
        return 3
    return 9


def _stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{_stable_digest(parts)[:24].upper()}"


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
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
