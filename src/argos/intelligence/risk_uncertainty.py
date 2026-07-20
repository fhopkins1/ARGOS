"""MO-TR-014 Risk uncertainty, materiality, and trade-eligibility doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp
from argos.intelligence.analyst_resolution import AnalystDecisionRecord, AnalystDisposition


MO_TR_014_VERSION = "MO-TR-014/1.0.0"


class RiskDisposition(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    ELIGIBLE_WITH_RESTRICTIONS = "ELIGIBLE_WITH_RESTRICTIONS"
    REDUCED_SIZE = "REDUCED_SIZE"
    HEIGHTENED_MONITORING = "HEIGHTENED_MONITORING"
    DEFERRED = "DEFERRED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    INELIGIBLE = "INELIGIBLE"
    UNKNOWN_RISK_STATE = "UNKNOWN_RISK_STATE"


class UncertaintyState(str, Enum):
    NO_MATERIAL_UNCERTAINTY = "NO_MATERIAL_UNCERTAINTY"
    EVIDENCE_LIMITATION = "EVIDENCE_LIMITATION"
    PARTIAL_EVIDENCE = "PARTIAL_EVIDENCE"
    MISSING_MANDATORY_EVIDENCE = "MISSING_MANDATORY_EVIDENCE"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    CONFLICTED_EVIDENCE = "CONFLICTED_EVIDENCE"
    UNRESOLVED_AUTHORITY = "UNRESOLVED_AUTHORITY"
    UNRESOLVED_IDENTITY = "UNRESOLVED_IDENTITY"
    UNRESOLVED_INSTRUMENT = "UNRESOLVED_INSTRUMENT"
    UNRESOLVED_TIME = "UNRESOLVED_TIME"
    UNRESOLVED_VERSION = "UNRESOLVED_VERSION"
    UNRESOLVED_UNIT = "UNRESOLVED_UNIT"
    UNRESOLVED_NUMERICAL_VALUE = "UNRESOLVED_NUMERICAL_VALUE"
    UNRESOLVED_EVENT = "UNRESOLVED_EVENT"
    UNRESOLVED_LEGAL_STATUS = "UNRESOLVED_LEGAL_STATUS"
    UNRESOLVED_TRADING_STATUS = "UNRESOLVED_TRADING_STATUS"
    UNRESOLVED_BROKER_STATE = "UNRESOLVED_BROKER_STATE"
    UNRESOLVED_ORDER_STATE = "UNRESOLVED_ORDER_STATE"
    UNRESOLVED_POSITION_STATE = "UNRESOLVED_POSITION_STATE"
    UNRESOLVED_CASH_STATE = "UNRESOLVED_CASH_STATE"
    UNRESOLVED_BUYING_POWER = "UNRESOLVED_BUYING_POWER"
    UNRESOLVED_MARGIN_STATE = "UNRESOLVED_MARGIN_STATE"
    UNRESOLVED_LIQUIDITY = "UNRESOLVED_LIQUIDITY"
    UNRESOLVED_CORPORATE_ACTION = "UNRESOLVED_CORPORATE_ACTION"
    UNRESOLVED_BANKRUPTCY = "UNRESOLVED_BANKRUPTCY"
    UNRESOLVED_MERGER_TERMS = "UNRESOLVED_MERGER_TERMS"
    UNRESOLVED_EARNINGS_STATUS = "UNRESOLVED_EARNINGS_STATUS"
    UNRESOLVED_SOURCE_INDEPENDENCE = "UNRESOLVED_SOURCE_INDEPENDENCE"
    SUSPECTED_SOURCE_CORRUPTION = "SUSPECTED_SOURCE_CORRUPTION"
    SUSPECTED_SOURCE_MANIPULATION = "SUSPECTED_SOURCE_MANIPULATION"
    SUSPECTED_MARKET_MANIPULATION = "SUSPECTED_MARKET_MANIPULATION"
    NOVEL_UNSUPPORTED_CONDITION = "NOVEL_UNSUPPORTED_CONDITION"
    CONSTITUTIONAL_AMBIGUITY = "CONSTITUTIONAL_AMBIGUITY"
    UNKNOWN_UNCERTAINTY = "UNKNOWN_UNCERTAINTY"


class ImpactSeverity(str, Enum):
    NO_IMPACT = "NO_IMPACT"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"
    CATASTROPHIC = "CATASTROPHIC"
    UNKNOWN_IMPACT = "UNKNOWN_IMPACT"


class LikelihoodState(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    REMOTE = "REMOTE"
    POSSIBLE = "POSSIBLE"
    PLAUSIBLE = "PLAUSIBLE"
    LIKELY = "LIKELY"
    OBSERVED = "OBSERVED"
    UNKNOWN_LIKELIHOOD = "UNKNOWN_LIKELIHOOD"


class DownsideAsymmetry(str, Enum):
    SYMMETRIC = "SYMMETRIC"
    MILD_DOWNSIDE_ASYMMETRY = "MILD_DOWNSIDE_ASYMMETRY"
    MATERIAL_DOWNSIDE_ASYMMETRY = "MATERIAL_DOWNSIDE_ASYMMETRY"
    SEVERE_DOWNSIDE_ASYMMETRY = "SEVERE_DOWNSIDE_ASYMMETRY"
    UNBOUNDED_OR_UNQUANTIFIED_DOWNSIDE = "UNBOUNDED_OR_UNQUANTIFIED_DOWNSIDE"
    UNKNOWN_ASYMMETRY = "UNKNOWN_ASYMMETRY"


class GovernedRiskSubject(str, Enum):
    LEGAL_TRADABILITY = "LEGAL_TRADABILITY"
    MARKET_STATUS = "MARKET_STATUS"
    BROKER_ACCOUNT_STATUS = "BROKER_ACCOUNT_STATUS"
    BUYING_POWER = "BUYING_POWER"
    CASH_BALANCE = "CASH_BALANCE"
    MARGIN_STATE = "MARGIN_STATE"
    ORDER_STATUS = "ORDER_STATUS"
    EXECUTION_STATUS = "EXECUTION_STATUS"
    POSITION_STATE = "POSITION_STATE"
    LIQUIDITY = "LIQUIDITY"
    BANKRUPTCY = "BANKRUPTCY"
    MERGER = "MERGER"
    REGULATORY_ACTION = "REGULATORY_ACTION"
    LEGAL_PROCEEDING = "LEGAL_PROCEEDING"
    SANCTIONS_STATUS = "SANCTIONS_STATUS"
    DATA_SOURCE_HEALTH = "DATA_SOURCE_HEALTH"
    OTHER_REQUIRED_FACT = "OTHER_REQUIRED_FACT"


@dataclass(frozen=True)
class RiskUncertaintyInput:
    workflow_id: str
    decision_object_id: str
    analyst_decision: AnalystDecisionRecord | None
    evidence_package_id: str
    account_id: str
    instrument_id: str
    issuer_id: str
    strategy_id: str
    portfolio_id: str
    position_id: str
    claim_ids: tuple[str, ...]
    fact_domains: tuple[str, ...]
    governed_subjects: tuple[GovernedRiskSubject, ...]
    uncertainty_states: tuple[UncertaintyState, ...]
    impact_severity: ImpactSeverity
    likelihood_state: LikelihoodState
    downside_asymmetry: DownsideAsymmetry
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class RiskUncertaintyAssessmentRecord:
    risk_uncertainty_assessment_id: str
    workflow_id: str
    decision_object_id: str
    analyst_conclusion_id: str
    evidence_package_id: str
    account_id: str
    instrument_id: str
    issuer_id: str
    strategy_id: str
    portfolio_id: str
    position_id: str
    claim_ids: tuple[str, ...]
    fact_domains: tuple[str, ...]
    uncertainty_states: tuple[UncertaintyState, ...]
    impact_severity: ImpactSeverity
    likelihood_state: LikelihoodState
    downside_asymmetry: DownsideAsymmetry
    risk_disposition: RiskDisposition
    restrictions: tuple[str, ...]
    release_conditions: tuple[str, ...]
    monitoring_requirements: tuple[str, ...]
    human_review_required: bool
    rule_version: str
    created_at: str
    evidence_references: tuple[str, ...]
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class RiskUncertaintyLedger:
    def __init__(self) -> None:
        self._records: dict[str, RiskUncertaintyAssessmentRecord] = {}

    def append(self, record: RiskUncertaintyAssessmentRecord) -> None:
        if record.risk_uncertainty_assessment_id in self._records:
            raise ValueError("Risk uncertainty records are append-only")
        self._records[record.risk_uncertainty_assessment_id] = record


class RiskUncertaintyEngine:
    def __init__(self, ledger: RiskUncertaintyLedger | None = None) -> None:
        self.ledger = ledger or RiskUncertaintyLedger()

    def assess(self, risk_input: RiskUncertaintyInput) -> RiskUncertaintyAssessmentRecord:
        uncertainties = set(risk_input.uncertainty_states)
        restrictions: list[str] = []
        release: list[str] = []
        if risk_input.analyst_decision is None:
            uncertainties.add(UncertaintyState.UNKNOWN_UNCERTAINTY)
            restrictions.append("analyst_disposition_required")
        elif risk_input.analyst_decision.final_disposition in {AnalystDisposition.CONFLICTED, AnalystDisposition.INSUFFICIENT_EVIDENCE, AnalystDisposition.UNKNOWN, AnalystDisposition.WRONG_ENTITY, AnalystDisposition.NONCOMPARABLE}:
            uncertainties.add(UncertaintyState.CONFLICTED_EVIDENCE if risk_input.analyst_decision.final_disposition is AnalystDisposition.CONFLICTED else UncertaintyState.MISSING_MANDATORY_EVIDENCE)
            restrictions.append("upstream_truth_not_trade_eligible")
        if uncertainties & {UncertaintyState.UNRESOLVED_LEGAL_STATUS, UncertaintyState.UNRESOLVED_TRADING_STATUS, UncertaintyState.UNRESOLVED_BROKER_STATE, UncertaintyState.UNRESOLVED_IDENTITY}:
            disposition = RiskDisposition.INELIGIBLE
            restrictions.append("constitutional_trade_block")
        elif risk_input.impact_severity in {ImpactSeverity.CATASTROPHIC, ImpactSeverity.CRITICAL} or risk_input.downside_asymmetry in {DownsideAsymmetry.SEVERE_DOWNSIDE_ASYMMETRY, DownsideAsymmetry.UNBOUNDED_OR_UNQUANTIFIED_DOWNSIDE}:
            disposition = RiskDisposition.INELIGIBLE
            restrictions.append("severe_asymmetric_downside")
        elif uncertainties - {UncertaintyState.NO_MATERIAL_UNCERTAINTY}:
            disposition = RiskDisposition.DEFERRED if UncertaintyState.STALE_EVIDENCE in uncertainties else RiskDisposition.ELIGIBLE_WITH_RESTRICTIONS
            restrictions.append("restricted_until_uncertainty_resolved")
        else:
            disposition = RiskDisposition.ELIGIBLE
        release.extend(f"resolve:{item.value}" for item in sorted(uncertainties, key=lambda item: item.value) if item is not UncertaintyState.NO_MATERIAL_UNCERTAINTY)
        record = RiskUncertaintyAssessmentRecord(
            _stable_id("RISKUNC", risk_input.workflow_id, risk_input.decision_object_id, tuple(item.value for item in sorted(uncertainties, key=lambda item: item.value)), disposition.value),
            risk_input.workflow_id,
            risk_input.decision_object_id,
            risk_input.analyst_decision.analyst_decision_id if risk_input.analyst_decision else "",
            risk_input.evidence_package_id,
            risk_input.account_id,
            risk_input.instrument_id,
            risk_input.issuer_id,
            risk_input.strategy_id,
            risk_input.portfolio_id,
            risk_input.position_id,
            risk_input.claim_ids,
            risk_input.fact_domains,
            tuple(sorted(uncertainties, key=lambda item: item.value)),
            risk_input.impact_severity,
            risk_input.likelihood_state,
            risk_input.downside_asymmetry,
            disposition,
            tuple(dict.fromkeys(restrictions)),
            tuple(dict.fromkeys(release)),
            ("heightened_monitoring_required",) if disposition in {RiskDisposition.ELIGIBLE_WITH_RESTRICTIONS, RiskDisposition.DEFERRED} else (),
            disposition is RiskDisposition.HUMAN_REVIEW_REQUIRED,
            MO_TR_014_VERSION,
            utc_timestamp(),
            risk_input.evidence_references,
        )
        self.ledger.append(record)
        return record


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
    if isinstance(value, (tuple, list, set)):
        return [_jsonable(item) for item in value]
    return value
