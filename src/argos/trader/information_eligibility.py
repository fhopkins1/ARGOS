"""MO-SP-009 Trader search prohibition and information eligibility doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_SP_009_VERSION = "MO-SP-009/1.0.0"


class TraderEligibilityDecision(str, Enum):
    EXECUTE = "Execute"
    DELAY = "Delay"
    REJECT = "Reject"
    RETURN_TO_ANALYST = "Return to Analyst"
    RETURN_TO_RISK = "Return to Risk"
    RETURN_TO_INTELLIGENCE = "Return to Intelligence"
    ESCALATE_COMMANDER = "Escalate Commander"
    HUMAN_REVIEW = "Human Review"
    ABORT_WORKFLOW = "Abort Workflow"


class TraderValidationFailure(str, Enum):
    EXPIRED_EVIDENCE = "expired_evidence"
    STALE_EVIDENCE = "stale_evidence"
    CONFLICTED_EVIDENCE = "conflicted_evidence"
    MISSING_EVIDENCE = "missing_evidence"
    MISSING_APPROVAL = "missing_approval"
    EXPIRED_RISK_REVIEW = "expired_risk_review"
    EXPIRED_ANALYST_REVIEW = "expired_analyst_review"
    BROKER_INCONSISTENCY = "broker_inconsistency"
    MARKET_HALT = "market_halt"
    CORPORATE_ACTION = "corporate_action"
    PRICE_OUTSIDE_LIMITS = "price_outside_limits"
    PORTFOLIO_MISMATCH = "portfolio_mismatch"
    BUYING_POWER_MISMATCH = "buying_power_mismatch"
    EXECUTION_TIMEOUT = "execution_timeout"
    ORDER_REJECTION = "order_rejection"
    UNKNOWN_MARKET_STATE = "unknown_market_state"
    UNKNOWN_BROKER_STATE = "unknown_broker_state"
    INTEGRITY_FAILURE = "integrity_failure"
    PROHIBITED_TRADER_SEARCH = "prohibited_trader_search"


class TraderInformationObject(str, Enum):
    DECISION_OBJECT = "Decision Object"
    EXECUTION_AUTHORIZATION = "Execution Authorization"
    RISK_APPROVAL = "Risk Approval"
    ANALYST_APPROVAL = "Analyst Approval"
    PORTFOLIO_ALLOCATION = "Portfolio Allocation"
    POSITION_SIZE = "Position Size"
    EXECUTION_CONSTRAINTS = "Execution Constraints"
    PRICE_CONSTRAINTS = "Price Constraints"
    ORDER_TYPE = "Order Type"
    TIME_IN_FORCE = "Time-in-Force"
    BROKER_AUTHORIZATION = "Broker Authorization"
    POSITION_IDENTIFIER = "Position Identifier"
    SECURITY_IDENTIFIER = "Security Identifier"
    ACCOUNT_IDENTIFIER = "Account Identifier"
    WORKFLOW_IDENTIFIER = "Workflow Identifier"
    EVIDENCE_PACKAGE_IDENTIFIER = "Evidence Package Identifier"
    VERSION_IDENTIFIER = "Version Identifier"
    APPROVAL_TIMESTAMP = "Approval Timestamp"
    EVIDENCE_FRESHNESS_TIMESTAMP = "Evidence Freshness Timestamp"
    SOURCE_CERTIFICATION = "Source Certification"
    DIGITAL_INTEGRITY_VERIFICATION = "Digital Integrity Verification"
    EVIDENCE_COMPLETENESS_STATUS = "Evidence Completeness Status"
    REQUIRED_SIGNATURES = "Required Signatures"
    PACKAGE_EXPIRATION = "Package Expiration"
    PACKAGE_IMMUTABILITY = "Package Immutability"


PROHIBITED_TRADER_ACTIVITIES = MappingProxyType({
    "news_search": "Trader is not an investigative office; return to Seeker or Intelligence.",
    "issuer_research": "Trader may not improve an evidence package.",
    "sec_filing_review": "Trader may not perform Analyst verification.",
    "economic_research": "Trader may not refresh thesis evidence.",
    "market_commentary": "Trader may not consume commentary as execution authority.",
    "social_media": "Trader may not use low-authority external information.",
    "internet_browsing": "Trader has no general browsing authority.",
    "general_web_search": "Trader has no discovery authority.",
    "manual_source_substitution": "Source substitution must occur upstream under approved doctrine.",
    "ai_generated_evidence": "Generated text is not institutional evidence.",
    "memory_based_evidence": "Model memory is not evidence.",
    "secondary_evidence_substitution": "Secondary evidence cannot replace required primary evidence.",
    "evidence_reinterpretation": "Trader cannot reinterpret upstream conclusions.",
    "thesis_modification": "Trader cannot change the Decision Object thesis.",
    "price_forecasting": "Trader cannot forecast prices.",
    "risk_reassessment": "Trader must return to Risk for risk changes.",
    "fundamental_analysis": "Trader cannot perform analysis.",
    "technical_analysis": "Trader cannot perform analysis.",
    "manual_calculation": "Trader cannot manufacture missing facts by calculation.",
    "synthetic_interpolation": "Trader cannot fill missing execution facts.",
    "synthetic_continuity": "Trader cannot continue through unknown states.",
})


FRESHNESS_LIMIT_SECONDS = MappingProxyType({
    "market_session": 60,
    "broker_account_state": 60,
    "buying_power": 15,
    "cash": 60,
    "open_orders": 30,
    "current_positions": 30,
    "execution_restrictions": 60,
    "market_status": 30,
    "halt_status": 30,
    "bid": 15,
    "ask": 15,
    "last_trade": 15,
    "nbbo": 15,
    "exchange_status": 60,
    "portfolio_synchronization": 60,
    "account_synchronization": 60,
    "risk_approval": 300,
    "analyst_approval": 300,
    "intelligence_certification": 300,
    "decision_object": 300,
})


RETURN_TO_UPSTREAM = MappingProxyType({
    TraderValidationFailure.EXPIRED_EVIDENCE: TraderEligibilityDecision.RETURN_TO_INTELLIGENCE,
    TraderValidationFailure.STALE_EVIDENCE: TraderEligibilityDecision.RETURN_TO_INTELLIGENCE,
    TraderValidationFailure.CONFLICTED_EVIDENCE: TraderEligibilityDecision.RETURN_TO_ANALYST,
    TraderValidationFailure.MISSING_EVIDENCE: TraderEligibilityDecision.RETURN_TO_INTELLIGENCE,
    TraderValidationFailure.MISSING_APPROVAL: TraderEligibilityDecision.REJECT,
    TraderValidationFailure.EXPIRED_RISK_REVIEW: TraderEligibilityDecision.RETURN_TO_RISK,
    TraderValidationFailure.EXPIRED_ANALYST_REVIEW: TraderEligibilityDecision.RETURN_TO_ANALYST,
    TraderValidationFailure.BROKER_INCONSISTENCY: TraderEligibilityDecision.RETURN_TO_RISK,
    TraderValidationFailure.MARKET_HALT: TraderEligibilityDecision.ESCALATE_COMMANDER,
    TraderValidationFailure.CORPORATE_ACTION: TraderEligibilityDecision.RETURN_TO_RISK,
    TraderValidationFailure.PRICE_OUTSIDE_LIMITS: TraderEligibilityDecision.REJECT,
    TraderValidationFailure.PORTFOLIO_MISMATCH: TraderEligibilityDecision.RETURN_TO_RISK,
    TraderValidationFailure.BUYING_POWER_MISMATCH: TraderEligibilityDecision.RETURN_TO_RISK,
    TraderValidationFailure.EXECUTION_TIMEOUT: TraderEligibilityDecision.DELAY,
    TraderValidationFailure.ORDER_REJECTION: TraderEligibilityDecision.RETURN_TO_RISK,
    TraderValidationFailure.UNKNOWN_MARKET_STATE: TraderEligibilityDecision.RETURN_TO_INTELLIGENCE,
    TraderValidationFailure.UNKNOWN_BROKER_STATE: TraderEligibilityDecision.RETURN_TO_RISK,
    TraderValidationFailure.INTEGRITY_FAILURE: TraderEligibilityDecision.ABORT_WORKFLOW,
    TraderValidationFailure.PROHIBITED_TRADER_SEARCH: TraderEligibilityDecision.ABORT_WORKFLOW,
})


@dataclass(frozen=True)
class TraderExecutionPackage:
    package_id: str
    workflow_id: str
    workflow_execution_token_id: str
    decision_object_id: str
    execution_authorization_id: str
    risk_approval_id: str
    analyst_approval_id: str
    portfolio_allocation_id: str
    position_size: str
    execution_constraints: Mapping[str, Any]
    price_constraints: Mapping[str, Any]
    order_type: str
    time_in_force: str
    broker_authorization_id: str
    position_identifier: str
    security_identifier: str
    account_identifier: str
    evidence_package_id: str
    version_identifier: str
    approval_timestamp: str
    evidence_freshness: Mapping[str, int]
    source_certification_id: str
    digital_integrity_verified: bool
    evidence_completeness_status: str
    required_signatures: tuple[str, ...]
    package_expiration: str
    immutable: bool
    broker_validations: Mapping[str, str]
    market_validations: Mapping[str, str]
    integrity_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "integrity_digest", _stable_digest(self))


@dataclass(frozen=True)
class TraderEligibilityReport:
    package_id: str
    decision: TraderEligibilityDecision
    failures: tuple[TraderValidationFailure, ...]
    upstream_destination: str
    audit_requirements: tuple[str, ...]
    trade_eligible: bool
    report_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_digest", _stable_digest(self))


class TraderInformationEligibilityEngine:
    """Validates execution prerequisites without granting search authority."""

    def evaluate(self, package: TraderExecutionPackage) -> TraderEligibilityReport:
        failures: list[TraderValidationFailure] = []
        missing = [field.value for field in TraderInformationObject if _package_value_missing(package, field)]
        if missing:
            failures.append(TraderValidationFailure.MISSING_EVIDENCE)
        if not package.digital_integrity_verified or not package.immutable or not package.required_signatures:
            failures.append(TraderValidationFailure.INTEGRITY_FAILURE)
        if package.evidence_completeness_status != "COMPLETE":
            failures.append(TraderValidationFailure.CONFLICTED_EVIDENCE if package.evidence_completeness_status == "CONFLICTED" else TraderValidationFailure.MISSING_EVIDENCE)
        for field_name, max_age in FRESHNESS_LIMIT_SECONDS.items():
            age = package.evidence_freshness.get(field_name)
            if age is None:
                failures.append(TraderValidationFailure.MISSING_EVIDENCE)
            elif age > max_age:
                failures.append(TraderValidationFailure.STALE_EVIDENCE)
        if package.broker_validations.get("account_active") != "PASS" or package.broker_validations.get("buying_power_sufficient") != "PASS":
            failures.append(TraderValidationFailure.UNKNOWN_BROKER_STATE)
        if package.market_validations.get("halt_status") == "HALTED":
            failures.append(TraderValidationFailure.MARKET_HALT)
        unique_failures = tuple(dict.fromkeys(failures))
        decision = TraderEligibilityDecision.EXECUTE if not unique_failures else RETURN_TO_UPSTREAM[unique_failures[0]]
        return TraderEligibilityReport(
            package.package_id,
            decision,
            unique_failures,
            _destination(decision),
            ("record_eligibility_matrix_result", "retain_package_digest", "record_upstream_return") if unique_failures else ("record_execution_eligibility",),
            decision is TraderEligibilityDecision.EXECUTE,
        )

    def prohibit_activity(self, activity: str) -> TraderEligibilityReport:
        if activity not in PROHIBITED_TRADER_ACTIVITIES:
            return TraderEligibilityReport("TRADER-ACTIVITY", TraderEligibilityDecision.HUMAN_REVIEW, (), "Commander", ("record_unknown_trader_activity",), False)
        return TraderEligibilityReport(
            "TRADER-ACTIVITY",
            TraderEligibilityDecision.ABORT_WORKFLOW,
            (TraderValidationFailure.PROHIBITED_TRADER_SEARCH,),
            "Commander",
            ("record_prohibited_activity", "preserve_attempt_context", "block_execution"),
            False,
        )


def _package_value_missing(package: TraderExecutionPackage, field_name: TraderInformationObject) -> bool:
    aliases = {
        TraderInformationObject.EVIDENCE_PACKAGE_IDENTIFIER: "evidence_package_id",
        TraderInformationObject.SOURCE_CERTIFICATION: "source_certification_id",
        TraderInformationObject.PACKAGE_IMMUTABILITY: "immutable",
        TraderInformationObject.EVIDENCE_FRESHNESS_TIMESTAMP: "evidence_freshness",
        TraderInformationObject.DECISION_OBJECT: "decision_object_id",
        TraderInformationObject.EXECUTION_AUTHORIZATION: "execution_authorization_id",
        TraderInformationObject.RISK_APPROVAL: "risk_approval_id",
        TraderInformationObject.ANALYST_APPROVAL: "analyst_approval_id",
        TraderInformationObject.PORTFOLIO_ALLOCATION: "portfolio_allocation_id",
        TraderInformationObject.BROKER_AUTHORIZATION: "broker_authorization_id",
        TraderInformationObject.WORKFLOW_IDENTIFIER: "workflow_id",
        TraderInformationObject.DIGITAL_INTEGRITY_VERIFICATION: "digital_integrity_verified",
    }
    attr = aliases.get(field_name, field_name.name.lower())
    value = getattr(package, attr, None)
    return value in ("", None, (), {})


def _destination(decision: TraderEligibilityDecision) -> str:
    if decision is TraderEligibilityDecision.RETURN_TO_ANALYST:
        return "Analyst"
    if decision is TraderEligibilityDecision.RETURN_TO_RISK:
        return "Risk"
    if decision is TraderEligibilityDecision.RETURN_TO_INTELLIGENCE:
        return "Intelligence"
    if decision in {TraderEligibilityDecision.ESCALATE_COMMANDER, TraderEligibilityDecision.ABORT_WORKFLOW, TraderEligibilityDecision.HUMAN_REVIEW}:
        return "Commander"
    return "Trader"


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return dict(value)
    if is_dataclass(value):
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name not in {"integrity_digest", "report_digest"}}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
