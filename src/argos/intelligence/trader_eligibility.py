"""MO-TR-015 Trader evidence-eligibility and conflict-prohibition doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp
from argos.intelligence.analyst_resolution import AnalystDecisionRecord, AnalystDisposition
from argos.intelligence.broker_reconciliation import BrokerReconciliationDisposition, BrokerReconciliationRecord, TradeRestrictionState
from argos.intelligence.risk_uncertainty import RiskDisposition, RiskUncertaintyAssessmentRecord


MO_TR_015_VERSION = "MO-TR-015/1.0.0"


class TraderDisposition(str, Enum):
    EXECUTION_ELIGIBLE = "EXECUTION_ELIGIBLE"
    REFRESH_REQUIRED = "REFRESH_REQUIRED"
    RETURN_TO_ANALYST = "RETURN_TO_ANALYST"
    RETURN_TO_RISK = "RETURN_TO_RISK"
    BROKER_RECONCILIATION_REQUIRED = "BROKER_RECONCILIATION_REQUIRED"
    EXECUTION_BLOCKED = "EXECUTION_BLOCKED"
    UNKNOWN_EXECUTION_STATE = "UNKNOWN_EXECUTION_STATE"


@dataclass(frozen=True)
class ProposedExecutionPackage:
    execution_package_id: str
    workflow_id: str
    workflow_active: bool
    workflow_execution_token_id: str
    current_token_owner: str
    decision_object_id: str
    decision_object_version_current: bool
    authorized_instrument_id: str
    proposed_instrument_id: str
    authorized_side: str
    proposed_side: str
    proposed_quantity: str
    max_authorized_quantity: str
    proposed_notional: str
    max_authorized_notional: str
    analyst_decision: AnalystDecisionRecord | None
    risk_assessment: RiskUncertaintyAssessmentRecord | None
    broker_reconciliation: BrokerReconciliationRecord | None
    evidence_package_complete: bool
    evidence_fresh: bool
    legal_tradability_established: bool
    market_status_permits_trading: bool
    active_halt: bool
    active_suspension: bool
    broker_restriction_active: bool
    account_identity_verified: bool
    duplicate_order_protection_passed: bool
    human_review_open: bool
    audit_references: tuple[str, ...]
    provenance_references: tuple[str, ...]


@dataclass(frozen=True)
class TraderEligibilityRecord:
    eligibility_id: str
    execution_package_id: str
    workflow_id: str
    decision_object_id: str
    final_disposition: TraderDisposition
    reason_codes: tuple[str, ...]
    analyst_decision_id: str
    risk_assessment_id: str
    broker_reconciliation_id: str
    execution_authorization_id: str
    route_to_office: str
    doctrine_version: str
    created_at: str
    audit_references: tuple[str, ...]
    provenance_references: tuple[str, ...]
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class TraderEligibilityLedger:
    def __init__(self) -> None:
        self._records: dict[str, TraderEligibilityRecord] = {}

    def append(self, record: TraderEligibilityRecord) -> None:
        if record.eligibility_id in self._records:
            raise ValueError("Trader eligibility records are append-only")
        self._records[record.eligibility_id] = record


class TraderEvidenceEligibilityEngine:
    def __init__(self, ledger: TraderEligibilityLedger | None = None) -> None:
        self.ledger = ledger or TraderEligibilityLedger()

    def evaluate(self, package: ProposedExecutionPackage) -> TraderEligibilityRecord:
        reasons = _reason_codes(package)
        disposition = _first_disposition(reasons)
        authorization = _stable_id("EXECAUTH", package.execution_package_id, package.workflow_execution_token_id) if disposition is TraderDisposition.EXECUTION_ELIGIBLE else ""
        route = {
            TraderDisposition.EXECUTION_ELIGIBLE: "ExecutionGateway",
            TraderDisposition.REFRESH_REQUIRED: "Seeker",
            TraderDisposition.RETURN_TO_ANALYST: "Analyst",
            TraderDisposition.RETURN_TO_RISK: "Risk",
            TraderDisposition.BROKER_RECONCILIATION_REQUIRED: "BrokerReconciliation",
            TraderDisposition.EXECUTION_BLOCKED: "Risk",
            TraderDisposition.UNKNOWN_EXECUTION_STATE: "Commander",
        }[disposition]
        record = TraderEligibilityRecord(
            _stable_id("TRADERELIG", package.execution_package_id, tuple(reasons), disposition.value),
            package.execution_package_id,
            package.workflow_id,
            package.decision_object_id,
            disposition,
            tuple(reasons),
            package.analyst_decision.analyst_decision_id if package.analyst_decision else "",
            package.risk_assessment.risk_uncertainty_assessment_id if package.risk_assessment else "",
            package.broker_reconciliation.reconciliation_id if package.broker_reconciliation else "",
            authorization,
            route,
            MO_TR_015_VERSION,
            utc_timestamp(),
            package.audit_references,
            package.provenance_references,
        )
        self.ledger.append(record)
        return record


def _reason_codes(package: ProposedExecutionPackage) -> list[str]:
    reasons: list[str] = []
    if not package.execution_package_id or not package.workflow_id or not package.workflow_execution_token_id:
        reasons.append("UNKNOWN_EXECUTION_STATE:mandatory_identity_missing")
    if not package.workflow_active or package.current_token_owner != "Trader" or not package.decision_object_id or not package.decision_object_version_current:
        reasons.append("EXECUTION_BLOCKED:workflow_or_authority_invalid")
    if package.active_halt or package.active_suspension or not package.legal_tradability_established or not package.market_status_permits_trading:
        reasons.append("EXECUTION_BLOCKED:market_or_legal_status_blocks_execution")
    if package.proposed_instrument_id != package.authorized_instrument_id or package.proposed_side != package.authorized_side or not package.account_identity_verified or not package.duplicate_order_protection_passed or package.human_review_open:
        reasons.append("EXECUTION_BLOCKED:execution_conditions_not_authorized")
    if package.broker_reconciliation is None or package.broker_restriction_active:
        reasons.append("BROKER_RECONCILIATION_REQUIRED:broker_state_missing_or_restricted")
    elif package.broker_reconciliation.disposition not in {BrokerReconciliationDisposition.MATCHED, BrokerReconciliationDisposition.MATCHED_WITH_ALLOWED_DELAY} or package.broker_reconciliation.trade_restriction.scope is not TradeRestrictionState.NO_TRADE_RESTRICTION:
        reasons.append("BROKER_RECONCILIATION_REQUIRED:broker_reconciliation_not_clean")
    if package.analyst_decision is None or package.analyst_decision.final_disposition not in {AnalystDisposition.VERIFIED, AnalystDisposition.VERIFIED_WITH_LIMITATION, AnalystDisposition.PROVISIONALLY_VERIFIED}:
        reasons.append("RETURN_TO_ANALYST:analyst_disposition_missing_or_ineligible")
    if package.risk_assessment is None or package.risk_assessment.risk_disposition not in {RiskDisposition.ELIGIBLE, RiskDisposition.ELIGIBLE_WITH_RESTRICTIONS, RiskDisposition.REDUCED_SIZE, RiskDisposition.HEIGHTENED_MONITORING}:
        reasons.append("RETURN_TO_RISK:risk_disposition_missing_or_ineligible")
    if not package.evidence_package_complete:
        reasons.append("RETURN_TO_ANALYST:evidence_package_incomplete")
    if not package.evidence_fresh:
        reasons.append("REFRESH_REQUIRED:execution_time_evidence_expired")
    try:
        if float(package.proposed_quantity) > float(package.max_authorized_quantity) or float(package.proposed_notional) > float(package.max_authorized_notional):
            reasons.append("RETURN_TO_RISK:proposed_size_exceeds_authorization")
    except ValueError:
        reasons.append("UNKNOWN_EXECUTION_STATE:invalid_numeric_order_terms")
    if not package.audit_references or not package.provenance_references:
        reasons.append("EXECUTION_BLOCKED:audit_or_provenance_missing")
    return reasons


def _first_disposition(reasons: list[str]) -> TraderDisposition:
    precedence = [
        TraderDisposition.UNKNOWN_EXECUTION_STATE,
        TraderDisposition.EXECUTION_BLOCKED,
        TraderDisposition.BROKER_RECONCILIATION_REQUIRED,
        TraderDisposition.RETURN_TO_ANALYST,
        TraderDisposition.RETURN_TO_RISK,
        TraderDisposition.REFRESH_REQUIRED,
    ]
    for disposition in precedence:
        if any(reason.startswith(disposition.value) for reason in reasons):
            return disposition
    return TraderDisposition.EXECUTION_ELIGIBLE


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
