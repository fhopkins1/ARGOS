"""MO-TR-018 human escalation and exceptional-authority doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_018_VERSION = "MO-TR-018/1.0.0"


class HumanReviewClass(str, Enum):
    NOVEL_INSTRUMENT_REVIEW = "NOVEL_INSTRUMENT_REVIEW"
    NOVEL_JURISDICTION_REVIEW = "NOVEL_JURISDICTION_REVIEW"
    LEGAL_CONFLICT_REVIEW = "LEGAL_CONFLICT_REVIEW"
    BROKER_ACCOUNT_DISCREPANCY_REVIEW = "BROKER_ACCOUNT_DISCREPANCY_REVIEW"
    SOURCE_MANIPULATION_REVIEW = "SOURCE_MANIPULATION_REVIEW"
    MARKET_MANIPULATION_REVIEW = "MARKET_MANIPULATION_REVIEW"
    CATASTROPHIC_EVENT_REVIEW = "CATASTROPHIC_EVENT_REVIEW"
    CONFLICTING_PRIMARY_AUTHORITY_REVIEW = "CONFLICTING_PRIMARY_AUTHORITY_REVIEW"
    UNSUPPORTED_SYSTEM_CONDITION_REVIEW = "UNSUPPORTED_SYSTEM_CONDITION_REVIEW"
    CONSTITUTIONAL_AMBIGUITY_REVIEW = "CONSTITUTIONAL_AMBIGUITY_REVIEW"
    IDENTITY_CONFLICT_REVIEW = "IDENTITY_CONFLICT_REVIEW"
    TRADING_STATUS_REVIEW = "TRADING_STATUS_REVIEW"
    MATERIAL_CORPORATE_EVENT_REVIEW = "MATERIAL_CORPORATE_EVENT_REVIEW"
    SOURCE_QUARANTINE_REVIEW = "SOURCE_QUARANTINE_REVIEW"
    DATA_CORRUPTION_REVIEW = "DATA_CORRUPTION_REVIEW"
    MODEL_FAILURE_REVIEW = "MODEL_FAILURE_REVIEW"
    PORTFOLIO_EMERGENCY_REVIEW = "PORTFOLIO_EMERGENCY_REVIEW"
    SETTLEMENT_FAILURE_REVIEW = "SETTLEMENT_FAILURE_REVIEW"
    CYBERSECURITY_INCIDENT_REVIEW = "CYBERSECURITY_INCIDENT_REVIEW"
    OTHER_AUTHORIZED_EXCEPTION_REVIEW = "OTHER_AUTHORIZED_EXCEPTION_REVIEW"
    UNKNOWN_REVIEW_CLASS = "UNKNOWN_REVIEW_CLASS"


class HumanReviewState(str, Enum):
    REVIEW_REQUESTED = "REVIEW_REQUESTED"
    REVIEW_QUEUED = "REVIEW_QUEUED"
    REVIEW_ASSIGNED = "REVIEW_ASSIGNED"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    REVIEW_IN_PROGRESS = "REVIEW_IN_PROGRESS"
    ADDITIONAL_EVIDENCE_REQUIRED = "ADDITIONAL_EVIDENCE_REQUIRED"
    SECOND_REVIEW_REQUIRED = "SECOND_REVIEW_REQUIRED"
    COMPLIANCE_REVIEW_REQUIRED = "COMPLIANCE_REVIEW_REQUIRED"
    RISK_REVIEW_REQUIRED = "RISK_REVIEW_REQUIRED"
    LEGAL_REVIEW_REQUIRED = "LEGAL_REVIEW_REQUIRED"
    COMMAND_REVIEW_REQUIRED = "COMMAND_REVIEW_REQUIRED"
    DECISION_PENDING = "DECISION_PENDING"
    DECISION_ISSUED = "DECISION_ISSUED"
    DECISION_REJECTED = "DECISION_REJECTED"
    DECISION_EXPIRED = "DECISION_EXPIRED"
    DECISION_REVOKED = "DECISION_REVOKED"
    DECISION_SUPERSEDED = "DECISION_SUPERSEDED"
    REVIEW_CLOSED_UNRESOLVED = "REVIEW_CLOSED_UNRESOLVED"
    REVIEW_CANCELLED = "REVIEW_CANCELLED"
    UNKNOWN_REVIEW_STATE = "UNKNOWN_REVIEW_STATE"


class HumanReviewOutcome(str, Enum):
    NO_EXCEPTION_GRANTED = "NO_EXCEPTION_GRANTED"
    OPERATIONAL_ACTION_PERMITTED = "OPERATIONAL_ACTION_PERMITTED"
    OPERATIONAL_ACTION_PERMITTED_WITH_RESTRICTIONS = "OPERATIONAL_ACTION_PERMITTED_WITH_RESTRICTIONS"
    TEMPORARY_EXCEPTION_GRANTED = "TEMPORARY_EXCEPTION_GRANTED"
    TEMPORARY_EXCEPTION_DENIED = "TEMPORARY_EXCEPTION_DENIED"
    ADDITIONAL_EVIDENCE_REQUIRED = "ADDITIONAL_EVIDENCE_REQUIRED"
    AUTOMATED_PROCESS_MAY_RESUME = "AUTOMATED_PROCESS_MAY_RESUME"
    AUTOMATED_PROCESS_REMAINS_BLOCKED = "AUTOMATED_PROCESS_REMAINS_BLOCKED"
    TRADE_PROHIBITED = "TRADE_PROHIBITED"
    NEW_TRADING_PROHIBITED = "NEW_TRADING_PROHIBITED"
    CLOSING_ACTION_ONLY = "CLOSING_ACTION_ONLY"
    POSITION_REDUCTION_REQUIRED = "POSITION_REDUCTION_REQUIRED"
    SOURCE_QUARANTINE_REQUIRED = "SOURCE_QUARANTINE_REQUIRED"
    SOURCE_USE_RESTRICTED = "SOURCE_USE_RESTRICTED"
    ACCOUNT_RECONCILIATION_REQUIRED = "ACCOUNT_RECONCILIATION_REQUIRED"
    LEGAL_DETERMINATION_REQUIRED = "LEGAL_DETERMINATION_REQUIRED"
    BROKER_CONFIRMATION_REQUIRED = "BROKER_CONFIRMATION_REQUIRED"
    RISK_RECERTIFICATION_REQUIRED = "RISK_RECERTIFICATION_REQUIRED"
    ANALYST_RECERTIFICATION_REQUIRED = "ANALYST_RECERTIFICATION_REQUIRED"
    CONSTITUTIONAL_RULING_REQUIRED = "CONSTITUTIONAL_RULING_REQUIRED"
    SYSTEM_HALT_FOR_AFFECTED_SCOPE = "SYSTEM_HALT_FOR_AFFECTED_SCOPE"
    CASE_CLOSED_UNRESOLVED = "CASE_CLOSED_UNRESOLVED"
    UNKNOWN_REVIEW_OUTCOME = "UNKNOWN_REVIEW_OUTCOME"


class ReviewAuthorityRole(str, Enum):
    AUTHORIZED_RISK_REVIEWER = "AUTHORIZED_RISK_REVIEWER"
    AUTHORIZED_COMPLIANCE_REVIEWER = "AUTHORIZED_COMPLIANCE_REVIEWER"
    AUTHORIZED_LEGAL_REVIEWER = "AUTHORIZED_LEGAL_REVIEWER"
    AUTHORIZED_BROKERAGE_OPERATIONS_REVIEWER = "AUTHORIZED_BROKERAGE_OPERATIONS_REVIEWER"
    AUTHORIZED_MARKET_DATA_REVIEWER = "AUTHORIZED_MARKET_DATA_REVIEWER"
    AUTHORIZED_TRADING_OPERATIONS_REVIEWER = "AUTHORIZED_TRADING_OPERATIONS_REVIEWER"
    AUTHORIZED_PORTFOLIO_REVIEWER = "AUTHORIZED_PORTFOLIO_REVIEWER"
    AUTHORIZED_INFORMATION_SECURITY_REVIEWER = "AUTHORIZED_INFORMATION_SECURITY_REVIEWER"
    AUTHORIZED_INTERNAL_AUDIT_REVIEWER = "AUTHORIZED_INTERNAL_AUDIT_REVIEWER"
    AUTHORIZED_COMMAND_REVIEWER = "AUTHORIZED_COMMAND_REVIEWER"
    AUTHORIZED_CONSTITUTIONAL_REVIEWER = "AUTHORIZED_CONSTITUTIONAL_REVIEWER"
    AUTHORIZED_DUAL_CONTROL_APPROVER = "AUTHORIZED_DUAL_CONTROL_APPROVER"
    UNKNOWN_REVIEW_AUTHORITY = "UNKNOWN_REVIEW_AUTHORITY"


@dataclass(frozen=True)
class HumanAuthorityRule:
    authority_rule_id: str
    review_class: HumanReviewClass
    permitted_reviewer_role: ReviewAuthorityRole
    required_secondary_role: ReviewAuthorityRole | None
    required_office: str
    permitted_decisions: tuple[HumanReviewOutcome, ...]
    prohibited_decisions: tuple[HumanReviewOutcome, ...]
    maximum_scope: str
    maximum_duration: str
    evidence_requirements: tuple[str, ...]
    dual_control_required: bool
    risk_concurrence_required: bool
    compliance_concurrence_required: bool
    legal_concurrence_required: bool
    command_concurrence_required: bool
    expiration_rule: str
    revocation_rule: str
    rule_version: str = MO_TR_018_VERSION


@dataclass(frozen=True)
class EscalationCaseRecord:
    escalation_case_id: str
    workflow_id: str
    decision_object_id: str
    account_id: str
    instrument_id: str
    issuer_id: str
    source_id: str
    review_class: HumanReviewClass
    triggering_record_ids: tuple[str, ...]
    triggering_conflict_ids: tuple[str, ...]
    triggering_uncertainty_ids: tuple[str, ...]
    triggering_restriction_ids: tuple[str, ...]
    case_summary: str
    constitutional_question: str
    operational_question: str
    current_fact_state: str
    current_conflict_state: str
    current_risk_state: str
    current_trade_restriction: str
    affected_scope: str
    materiality: str
    urgency: str
    requested_by_office: str
    requested_by_actor: str
    workflow_execution_token_id: str
    requested_at: str
    assigned_reviewer_ids: tuple[str, ...]
    required_reviewer_roles: tuple[ReviewAuthorityRole, ...]
    review_state: HumanReviewState
    evidence_package_id: str
    decision_id: str
    expiration_timestamp: str
    closed_at: str
    audit_record_id: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


@dataclass(frozen=True)
class HumanReviewDecisionRecord:
    decision_id: str
    escalation_case_id: str
    reviewer_id: str
    reviewer_role: ReviewAuthorityRole
    outcomes: tuple[HumanReviewOutcome, ...]
    authority_rule_id: str
    decision_state: HumanReviewState
    expiration_timestamp: str
    reason_codes: tuple[str, ...]
    evidence_references: tuple[str, ...]
    created_at: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class HumanEscalationLedger:
    def __init__(self) -> None:
        self._cases: dict[str, EscalationCaseRecord] = {}
        self._decisions: dict[str, HumanReviewDecisionRecord] = {}

    def append_case(self, case: EscalationCaseRecord) -> None:
        if case.escalation_case_id in self._cases:
            raise ValueError("escalation cases are append-only")
        self._cases[case.escalation_case_id] = case

    def append_decision(self, decision: HumanReviewDecisionRecord) -> None:
        if decision.decision_id in self._decisions:
            raise ValueError("human review decisions are append-only")
        self._decisions[decision.decision_id] = decision


class HumanEscalationEngine:
    def __init__(self, rules: Mapping[HumanReviewClass, HumanAuthorityRule] | None = None, ledger: HumanEscalationLedger | None = None) -> None:
        self.rules = MappingProxyType(dict(rules or default_human_authority_rules()))
        self.ledger = ledger or HumanEscalationLedger()

    def create_case(self, review_class: HumanReviewClass, workflow_id: str, decision_object_id: str, triggering_record_ids: tuple[str, ...], *, evidence_package_id: str = "", requested_by_office: str = "Risk") -> EscalationCaseRecord:
        system_evidence_classes = {HumanReviewClass.UNSUPPORTED_SYSTEM_CONDITION_REVIEW, HumanReviewClass.CONSTITUTIONAL_AMBIGUITY_REVIEW, HumanReviewClass.CYBERSECURITY_INCIDENT_REVIEW}
        if not triggering_record_ids and review_class not in system_evidence_classes:
            raise ValueError("escalation case requires linked triggering records")
        rule = self.rules.get(review_class, self.rules[HumanReviewClass.CONSTITUTIONAL_AMBIGUITY_REVIEW])
        case = EscalationCaseRecord(_stable_id("ESCALATE", review_class.value, workflow_id, decision_object_id, triggering_record_ids), workflow_id, decision_object_id, "", "", "", "", review_class, triggering_record_ids, (), (), (), review_class.value, "", "determine_authorized_operational_consequence", "UNKNOWN", "PRESERVED", "BLOCKED_PENDING_REVIEW", "ACTIVE", rule.maximum_scope, "MATERIAL", "NORMAL", requested_by_office, requested_by_office, "", utc_timestamp(), (), (rule.permitted_reviewer_role,) + ((rule.required_secondary_role,) if rule.required_secondary_role else ()), HumanReviewState.REVIEW_REQUESTED, evidence_package_id, "", "", "", _stable_id("ESCAUDIT", review_class.value, workflow_id))
        self.ledger.append_case(case)
        return case

    def issue_decision(self, case: EscalationCaseRecord, reviewer_id: str, reviewer_role: ReviewAuthorityRole, outcomes: tuple[HumanReviewOutcome, ...], evidence_references: tuple[str, ...]) -> HumanReviewDecisionRecord:
        rule = self.rules.get(case.review_class, self.rules[HumanReviewClass.CONSTITUTIONAL_AMBIGUITY_REVIEW])
        reasons: list[str] = []
        state = HumanReviewState.DECISION_ISSUED
        if reviewer_role is not rule.permitted_reviewer_role:
            reasons.append("reviewer_role_not_authorized")
            state = HumanReviewState.DECISION_REJECTED
        if any(outcome not in rule.permitted_decisions for outcome in outcomes):
            reasons.append("outcome_not_permitted_by_authority_rule")
            state = HumanReviewState.DECISION_REJECTED
        if any(outcome in rule.prohibited_decisions for outcome in outcomes):
            reasons.append("outcome_explicitly_prohibited")
            state = HumanReviewState.DECISION_REJECTED
        if _contradictory(outcomes):
            reasons.append("contradictory_outcomes")
            state = HumanReviewState.DECISION_REJECTED
        if not evidence_references:
            reasons.append("review_evidence_missing")
            state = HumanReviewState.EVIDENCE_INCOMPLETE
        decision = HumanReviewDecisionRecord(_stable_id("HUMDEC", case.escalation_case_id, reviewer_id, outcomes, state.value), case.escalation_case_id, reviewer_id, reviewer_role, outcomes, rule.authority_rule_id, state, rule.maximum_duration, tuple(reasons or ("authorized_operational_consequence_only",)), evidence_references, utc_timestamp())
        self.ledger.append_decision(decision)
        return decision


def default_human_authority_rules() -> Mapping[HumanReviewClass, HumanAuthorityRule]:
    trade_block = (HumanReviewOutcome.TRADE_PROHIBITED, HumanReviewOutcome.AUTOMATED_PROCESS_REMAINS_BLOCKED, HumanReviewOutcome.ADDITIONAL_EVIDENCE_REQUIRED, HumanReviewOutcome.CASE_CLOSED_UNRESOLVED)
    return MappingProxyType({
        HumanReviewClass.LEGAL_CONFLICT_REVIEW: HumanAuthorityRule("HAR-LEGAL", HumanReviewClass.LEGAL_CONFLICT_REVIEW, ReviewAuthorityRole.AUTHORIZED_LEGAL_REVIEWER, None, "Legal", trade_block + (HumanReviewOutcome.LEGAL_DETERMINATION_REQUIRED,), (HumanReviewOutcome.AUTOMATED_PROCESS_MAY_RESUME,), "affected_instrument_or_account", "24h", ("legal_record", "conflict_record"), False, False, False, True, False, "expires_at_timestamp", "successor_decision"),
        HumanReviewClass.BROKER_ACCOUNT_DISCREPANCY_REVIEW: HumanAuthorityRule("HAR-BROKER", HumanReviewClass.BROKER_ACCOUNT_DISCREPANCY_REVIEW, ReviewAuthorityRole.AUTHORIZED_BROKERAGE_OPERATIONS_REVIEWER, None, "BrokerageOperations", (HumanReviewOutcome.ACCOUNT_RECONCILIATION_REQUIRED, HumanReviewOutcome.BROKER_CONFIRMATION_REQUIRED, HumanReviewOutcome.NEW_TRADING_PROHIBITED, HumanReviewOutcome.CLOSING_ACTION_ONLY), (HumanReviewOutcome.OPERATIONAL_ACTION_PERMITTED,), "affected_account", "4h", ("broker_record", "account_snapshot"), False, True, False, False, False, "expires_at_timestamp", "successor_decision"),
        HumanReviewClass.CONSTITUTIONAL_AMBIGUITY_REVIEW: HumanAuthorityRule("HAR-CONST", HumanReviewClass.CONSTITUTIONAL_AMBIGUITY_REVIEW, ReviewAuthorityRole.AUTHORIZED_CONSTITUTIONAL_REVIEWER, ReviewAuthorityRole.AUTHORIZED_COMMAND_REVIEWER, "Commander", (HumanReviewOutcome.CONSTITUTIONAL_RULING_REQUIRED, HumanReviewOutcome.SYSTEM_HALT_FOR_AFFECTED_SCOPE, HumanReviewOutcome.CASE_CLOSED_UNRESOLVED), (HumanReviewOutcome.OPERATIONAL_ACTION_PERMITTED,), "affected_workflow", "until_ruling", ("doctrine_records",), True, False, True, False, True, "requires_successor_ruling", "constitutional_revocation"),
    })


def _contradictory(outcomes: tuple[HumanReviewOutcome, ...]) -> bool:
    outcome_set = set(outcomes)
    return bool(
        {HumanReviewOutcome.AUTOMATED_PROCESS_MAY_RESUME, HumanReviewOutcome.AUTOMATED_PROCESS_REMAINS_BLOCKED} <= outcome_set
        or {HumanReviewOutcome.TRADE_PROHIBITED, HumanReviewOutcome.OPERATIONAL_ACTION_PERMITTED} <= outcome_set
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
