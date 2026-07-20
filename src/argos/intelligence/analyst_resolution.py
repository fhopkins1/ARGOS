"""MO-TR-013 Analyst evidentiary resolution doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp
from argos.intelligence.seeker_evidence import EvidencePackage, EvidenceSufficiencyState


MO_TR_013_VERSION = "MO-TR-013/1.0.0"


class AnalystClaimClass(str, Enum):
    MARKET_PRICE_CLAIM = "MARKET_PRICE_CLAIM"
    MARKET_STATUS_CLAIM = "MARKET_STATUS_CLAIM"
    SECURITY_IDENTITY_CLAIM = "SECURITY_IDENTITY_CLAIM"
    CORPORATE_FILING_CLAIM = "CORPORATE_FILING_CLAIM"
    CORPORATE_EVENT_CLAIM = "CORPORATE_EVENT_CLAIM"
    EARNINGS_CLAIM = "EARNINGS_CLAIM"
    GUIDANCE_CLAIM = "GUIDANCE_CLAIM"
    MERGER_CLAIM = "MERGER_CLAIM"
    BANKRUPTCY_CLAIM = "BANKRUPTCY_CLAIM"
    EXECUTIVE_CHANGE_CLAIM = "EXECUTIVE_CHANGE_CLAIM"
    REGULATORY_CLAIM = "REGULATORY_CLAIM"
    LEGAL_CLAIM = "LEGAL_CLAIM"
    TRADING_STATUS_CLAIM = "TRADING_STATUS_CLAIM"
    MACROECONOMIC_CLAIM = "MACROECONOMIC_CLAIM"
    CENTRAL_BANK_CLAIM = "CENTRAL_BANK_CLAIM"
    NEWS_EVENT_CLAIM = "NEWS_EVENT_CLAIM"
    BROKER_ORDER_CLAIM = "BROKER_ORDER_CLAIM"
    BROKER_EXECUTION_CLAIM = "BROKER_EXECUTION_CLAIM"
    POSITION_STATE_CLAIM = "POSITION_STATE_CLAIM"
    CASH_STATE_CLAIM = "CASH_STATE_CLAIM"
    BUYING_POWER_CLAIM = "BUYING_POWER_CLAIM"
    PORTFOLIO_VALUE_CLAIM = "PORTFOLIO_VALUE_CLAIM"
    PERFORMANCE_CLAIM = "PERFORMANCE_CLAIM"
    CAUSAL_MARKET_CLAIM = "CAUSAL_MARKET_CLAIM"
    FORECAST_CLAIM = "FORECAST_CLAIM"
    MODEL_OUTPUT_CLAIM = "MODEL_OUTPUT_CLAIM"
    UNKNOWN_CLAIM_CLASS = "UNKNOWN_CLAIM_CLASS"


class AnalystDisposition(str, Enum):
    VERIFIED = "VERIFIED"
    VERIFIED_WITH_LIMITATION = "VERIFIED_WITH_LIMITATION"
    PROVISIONALLY_VERIFIED = "PROVISIONALLY_VERIFIED"
    DISPROVEN = "DISPROVEN"
    CONFLICTED = "CONFLICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    STALE = "STALE"
    NONCOMPARABLE = "NONCOMPARABLE"
    WRONG_ENTITY = "WRONG_ENTITY"
    UNKNOWN = "UNKNOWN"


class AnalystPackageState(str, Enum):
    PACKAGE_COMPLETE = "PACKAGE_COMPLETE"
    PACKAGE_COMPLETE_WITH_CONFLICT = "PACKAGE_COMPLETE_WITH_CONFLICT"
    PACKAGE_INCOMPLETE = "PACKAGE_INCOMPLETE"
    PACKAGE_PRIMARY_SOURCE_MISSING = "PACKAGE_PRIMARY_SOURCE_MISSING"
    PACKAGE_INDEPENDENCE_UNPROVEN = "PACKAGE_INDEPENDENCE_UNPROVEN"
    PACKAGE_STALE = "PACKAGE_STALE"
    PACKAGE_WRONG_ENTITY = "PACKAGE_WRONG_ENTITY"
    PACKAGE_WRONG_INSTRUMENT = "PACKAGE_WRONG_INSTRUMENT"
    PACKAGE_WRONG_TIME_WINDOW = "PACKAGE_WRONG_TIME_WINDOW"
    PACKAGE_WRONG_VERSION = "PACKAGE_WRONG_VERSION"
    PACKAGE_CORRUPTED = "PACKAGE_CORRUPTED"
    PACKAGE_UNKNOWN = "PACKAGE_UNKNOWN"


class CausalState(str, Enum):
    CONFIRMED_OCCURRENCE = "CONFIRMED_OCCURRENCE"
    TEMPORAL_ASSOCIATION = "TEMPORAL_ASSOCIATION"
    PLAUSIBLE_EXPLANATION = "PLAUSIBLE_EXPLANATION"
    SUPPORTED_CAUSAL_MECHANISM = "SUPPORTED_CAUSAL_MECHANISM"
    UNPROVEN_NARRATIVE = "UNPROVEN_NARRATIVE"
    CONTRADICTED_CAUSAL_CLAIM = "CONTRADICTED_CAUSAL_CLAIM"
    INSUFFICIENT_CAUSAL_EVIDENCE = "INSUFFICIENT_CAUSAL_EVIDENCE"
    UNKNOWN_CAUSAL_STATE = "UNKNOWN_CAUSAL_STATE"


@dataclass(frozen=True)
class AnalystClaim:
    claim_id: str
    claim_class: AnalystClaimClass
    subject_entity: str
    affected_instrument: str
    affected_account: str
    asserted_predicate: str
    asserted_value: str
    asserted_status: str
    unit: str
    currency: str
    asserted_time: str
    effective_time: str
    jurisdiction: str
    venue: str
    document_or_event_version: str
    claim_scope: str
    originating_workflow: str
    strategy_dependency: str
    materiality_reference: str
    current_claim_version: str


@dataclass(frozen=True)
class AnalystClaimPolicy:
    claim_class: AnalystClaimClass
    required_package_states: tuple[AnalystPackageState, ...]
    minimum_independent_origins: int
    official_confirmation_required: bool
    provisional_allowed: bool
    conflict_blocks_verification: bool
    stale_blocks_verification: bool
    required_limitation_codes: tuple[str, ...]
    risk_notification_rule: str
    thesis_blocking_rule: str
    human_review_rule: str
    rule_version: str = MO_TR_013_VERSION


@dataclass(frozen=True)
class AnalystDecisionRecord:
    analyst_decision_id: str
    workflow_id: str
    claim_id: str
    claim_version: str
    claim_class: AnalystClaimClass
    evidence_package_id: str
    evidence_ids: tuple[str, ...]
    conflict_records: tuple[str, ...]
    package_state: AnalystPackageState
    policy_version: str
    threshold_evaluation: str
    causal_state: CausalState
    final_disposition: AnalystDisposition
    limitations: tuple[str, ...]
    required_next_action: str
    seeker_return_required: bool
    risk_consequence: str
    thesis_consequence: str
    trade_consequence: str
    escalation_destination: str
    office_identity: str
    workflow_execution_token_id: str
    decision_timestamp: str
    evidence_references: tuple[str, ...]
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class AnalystDecisionLedger:
    def __init__(self) -> None:
        self._records: dict[str, AnalystDecisionRecord] = {}

    def append(self, record: AnalystDecisionRecord) -> None:
        if record.analyst_decision_id in self._records:
            raise ValueError("Analyst decisions are append-only")
        self._records[record.analyst_decision_id] = record


class AnalystResolutionEngine:
    def __init__(self, ledger: AnalystDecisionLedger | None = None) -> None:
        self.ledger = ledger or AnalystDecisionLedger()

    def resolve(self, claim: AnalystClaim, package: EvidencePackage, *, workflow_execution_token_id: str = "") -> AnalystDecisionRecord:
        package_state = _map_package_state(package.sufficiency_state)
        policy = _policy_for(claim.claim_class)
        limitations: list[str] = []
        if package_state is AnalystPackageState.PACKAGE_WRONG_ENTITY:
            disposition = AnalystDisposition.WRONG_ENTITY
            action = "return_to_seeker"
        elif package_state is AnalystPackageState.PACKAGE_STALE:
            disposition = AnalystDisposition.STALE
            action = "return_to_seeker_for_refresh"
            limitations.append("evidence_stale")
        elif package_state in {AnalystPackageState.PACKAGE_INCOMPLETE, AnalystPackageState.PACKAGE_PRIMARY_SOURCE_MISSING, AnalystPackageState.PACKAGE_INDEPENDENCE_UNPROVEN}:
            disposition = AnalystDisposition.INSUFFICIENT_EVIDENCE
            action = "return_to_seeker"
            limitations.append(package_state.value.lower())
        elif package.conflict_records and policy.conflict_blocks_verification:
            disposition = AnalystDisposition.CONFLICTED
            action = "notify_risk_and_return_if_required"
            limitations.append("contrary_or_conflicting_evidence_preserved")
        elif claim.claim_class is AnalystClaimClass.CAUSAL_MARKET_CLAIM:
            disposition = AnalystDisposition.INSUFFICIENT_EVIDENCE
            action = "causal_mechanism_required"
            limitations.append("causal_mechanism_unproven")
        elif package_state is AnalystPackageState.PACKAGE_COMPLETE_WITH_CONFLICT:
            disposition = AnalystDisposition.VERIFIED_WITH_LIMITATION
            action = "notify_risk"
            limitations.append("verified_with_preserved_conflict")
        else:
            disposition = AnalystDisposition.VERIFIED
            action = "risk_review"
        limitations.extend(policy.required_limitation_codes)
        record = AnalystDecisionRecord(
            _stable_id("ANDEC", claim.claim_id, package.package_id, disposition.value),
            claim.originating_workflow or package.workflow_id,
            claim.claim_id,
            claim.current_claim_version,
            claim.claim_class,
            package.package_id,
            tuple(item.evidence_id for item in package.evidence_records),
            tuple(item.conflict_id for item in package.conflict_records),
            package_state,
            policy.rule_version,
            "categorical_policy_threshold_applied",
            CausalState.INSUFFICIENT_CAUSAL_EVIDENCE if claim.claim_class is AnalystClaimClass.CAUSAL_MARKET_CLAIM else CausalState.CONFIRMED_OCCURRENCE,
            disposition,
            tuple(dict.fromkeys(limitations)),
            action,
            action.startswith("return_to_seeker"),
            policy.risk_notification_rule,
            policy.thesis_blocking_rule if disposition not in {AnalystDisposition.VERIFIED, AnalystDisposition.VERIFIED_WITH_LIMITATION} else "THESIS_MAY_PROCEED_TO_RISK",
            "NO_TRADE_AUTHORITY_GRANTED_BY_ANALYST",
            "Risk" if disposition in {AnalystDisposition.VERIFIED, AnalystDisposition.VERIFIED_WITH_LIMITATION} else "Seeker",
            "Analyst",
            workflow_execution_token_id,
            utc_timestamp(),
            tuple(item.raw_evidence_reference for item in package.evidence_records),
        )
        self.ledger.append(record)
        return record


def _map_package_state(state: EvidenceSufficiencyState) -> AnalystPackageState:
    return {
        EvidenceSufficiencyState.COMPLETE: AnalystPackageState.PACKAGE_COMPLETE,
        EvidenceSufficiencyState.COMPLETE_WITH_CONFLICT: AnalystPackageState.PACKAGE_COMPLETE_WITH_CONFLICT,
        EvidenceSufficiencyState.INCOMPLETE: AnalystPackageState.PACKAGE_INCOMPLETE,
        EvidenceSufficiencyState.PRIMARY_SOURCE_MISSING: AnalystPackageState.PACKAGE_PRIMARY_SOURCE_MISSING,
        EvidenceSufficiencyState.INDEPENDENCE_UNPROVEN: AnalystPackageState.PACKAGE_INDEPENDENCE_UNPROVEN,
        EvidenceSufficiencyState.STALE_EVIDENCE: AnalystPackageState.PACKAGE_STALE,
        EvidenceSufficiencyState.WRONG_ENTITY: AnalystPackageState.PACKAGE_WRONG_ENTITY,
        EvidenceSufficiencyState.WRONG_INSTRUMENT: AnalystPackageState.PACKAGE_WRONG_INSTRUMENT,
        EvidenceSufficiencyState.WRONG_TIME_WINDOW: AnalystPackageState.PACKAGE_WRONG_TIME_WINDOW,
        EvidenceSufficiencyState.UNKNOWN: AnalystPackageState.PACKAGE_UNKNOWN,
        EvidenceSufficiencyState.SOURCE_UNAVAILABLE: AnalystPackageState.PACKAGE_INCOMPLETE,
    }[state]


def _policy_for(claim_class: AnalystClaimClass) -> AnalystClaimPolicy:
    return AnalystClaimPolicy(claim_class, (AnalystPackageState.PACKAGE_COMPLETE, AnalystPackageState.PACKAGE_COMPLETE_WITH_CONFLICT), 1, claim_class in {AnalystClaimClass.LEGAL_CLAIM, AnalystClaimClass.TRADING_STATUS_CLAIM}, True, True, True, (), "RISK_MUST_CONSUME_DISPOSITION", "BLOCK_IF_NOT_VERIFIED", "HUMAN_REVIEW_IF_POLICY_UNKNOWN")


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
