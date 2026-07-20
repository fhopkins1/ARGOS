"""MO-SP-008 broker, account, order, and execution search doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_SP_008_VERSION = "MO-SP-008/1.0.0"


class BrokerDoctrineError(ValueError):
    """Raised when broker retrieval doctrine is incomplete or unauthorized."""


class BrokerInformationState(str, Enum):
    OBSERVED_CURRENT = "OBSERVED_CURRENT"
    OBSERVED_STALE = "OBSERVED_STALE"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    INCOMPLETE = "INCOMPLETE"
    CONFLICTED = "CONFLICTED"
    PENDING_BROKER_CONFIRMATION = "PENDING_BROKER_CONFIRMATION"
    DELAYED = "DELAYED"
    UNSUPPORTED = "UNSUPPORTED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    BROKER_OUTAGE = "BROKER_OUTAGE"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    RECONCILIATION_FAILED = "RECONCILIATION_FAILED"


class BrokerEnvironment(str, Enum):
    PAPER = "paper"
    LIVE = "live"


class BrokerRetrievalOperation(str, Enum):
    ACCOUNT_STATUS = "retrieve_account_status"
    ACCOUNT_RESTRICTIONS = "retrieve_account_restrictions"
    ACCOUNT_BALANCES = "retrieve_account_balances"
    BUYING_POWER = "retrieve_buying_power"
    MARGIN_STATE = "retrieve_margin_state"
    CURRENT_POSITIONS = "retrieve_current_positions"
    SPECIFIC_POSITION = "retrieve_specific_position"
    OPEN_ORDERS = "retrieve_open_orders"
    SPECIFIC_ORDER = "retrieve_specific_order"
    COMPLETED_ORDERS = "retrieve_recent_completed_orders"
    FILLS_EXECUTIONS = "retrieve_fills_or_executions"
    REJECTED_ORDERS = "retrieve_rejected_orders"
    CANCELLED_ORDERS = "retrieve_cancelled_orders"
    ASSIGNMENT_EXERCISE = "retrieve_assignment_and_exercise_events"
    CORPORATE_ACTION_ADJUSTMENTS = "retrieve_corporate_action_adjustments"
    CLOSED_POSITIONS = "retrieve_closed_position_records"
    BROKER_HEALTH = "retrieve_broker_service_or_account_health"


class ReconciliationSeverity(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class BrokerIdentity:
    broker_id: str
    configured_name: str
    adapter_identifier: str
    adapter_version: str
    supported_environment_types: tuple[BrokerEnvironment, ...]
    supported_retrieval_capabilities: tuple[BrokerRetrievalOperation, ...]
    supported_event_notification_capabilities: tuple[str, ...]
    supported_asset_classes: tuple[str, ...]
    supported_account_types: tuple[str, ...]
    status: str
    approval_state: str
    activation_timestamp: str
    suspension_timestamp: str = ""


@dataclass(frozen=True)
class BrokerageAccountReference:
    broker_id: str
    account_pseudonym: str
    environment: BrokerEnvironment
    account_type: str
    base_currency: str
    margin_enabled: bool
    options_enabled: bool
    supported_asset_classes: tuple[str, ...]
    account_status: str
    last_verified_timestamp: str
    credential_scope_identifier: str
    account_authority_state: str


@dataclass(frozen=True)
class BrokerRetrievalPlan:
    retrieval_plan_id: str
    version: str
    fact_domain: str
    authorized_requesting_offices: tuple[str, ...]
    broker_capability_required: BrokerRetrievalOperation
    adapter_operation: BrokerRetrievalOperation
    retrieval_trigger: tuple[str, ...]
    normal_polling_interval_seconds: int
    heightened_polling_interval_seconds: int
    dormant_polling_interval_seconds: int
    event_driven_notification_eligible: bool
    freshness_limit_seconds: int
    cache_eligibility: str
    maximum_cache_age_seconds: int
    timeout_seconds: int
    retry_count: int
    retry_interval_seconds: int
    backoff_schedule: tuple[int, ...]
    rate_limit_behavior: str
    fallback_rule: str
    evidence_retention_rule: str
    cost_class: str
    stop_condition: str
    escalation_route: str
    trade_blocking_classification: str
    plan_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_digest", _stable_digest(self))


@dataclass(frozen=True)
class BrokerRetrievalRequest:
    request_id: str
    retrieval_plan_id: str
    workflow_id: str
    workflow_execution_token_id: str
    decision_object_id: str
    requesting_office: str
    broker: BrokerIdentity
    account: BrokerageAccountReference
    parameters: Mapping[str, str]


@dataclass(frozen=True)
class BrokerObservationEnvelope:
    observation_id: str
    retrieval_plan_id: str
    retrieval_plan_version: str
    workflow_id: str
    workflow_execution_token_id: str
    decision_object_id: str
    position_object_id: str
    internal_order_id: str
    broker_order_id: str
    broker_execution_id: str
    requesting_office: str
    executing_service: str
    broker_id: str
    account_pseudonym: str
    environment: BrokerEnvironment
    adapter_version: str
    retrieval_operation: BrokerRetrievalOperation
    retrieval_request_parameters: Mapping[str, str]
    request_timestamp: str
    response_timestamp: str
    broker_reported_timestamp: str
    source_timezone: str
    normalized_utc_timestamp: str
    response_status: BrokerInformationState
    transport_status: str
    broker_error_code: str
    raw_evidence_reference: str
    response_digest: str
    normalization_version: str
    cache_status: str
    retry_history: tuple[str, ...]
    latency_ms: int
    cost_classification: str
    freshness_classification: BrokerInformationState
    extracted_facts: Mapping[str, Any]
    warnings: tuple[str, ...]
    failure_state: BrokerInformationState
    escalation_state: str


@dataclass(frozen=True)
class BrokerReconciliationRecord:
    reconciliation_id: str
    reconciliation_type: str
    trigger: str
    environment: BrokerEnvironment
    broker_id: str
    account_pseudonym: str
    scope: str
    internal_observation_set: tuple[str, ...]
    broker_observation_set: tuple[str, ...]
    comparison_timestamp: str
    comparison_algorithm_version: str
    matched_items: tuple[str, ...]
    broker_only_items: tuple[str, ...]
    internal_only_items: tuple[str, ...]
    field_level_mismatches: Mapping[str, str]
    severity: ReconciliationSeverity
    resolution_status: str
    owning_office: str
    required_action: str
    trade_eligibility_effect: str
    evidence_references: tuple[str, ...]
    audit_references: tuple[str, ...]


class BrokerRetrievalPlanRegistry:
    """Single controlled list of allowed broker fact retrieval plans."""

    def __init__(self, plans: tuple[BrokerRetrievalPlan, ...] | None = None) -> None:
        self._plans = {plan.retrieval_plan_id: plan for plan in plans or default_broker_retrieval_plans()}
        self._validate()

    def resolve(self, retrieval_plan_id: str) -> BrokerRetrievalPlan:
        try:
            return self._plans[retrieval_plan_id]
        except KeyError as exc:
            raise BrokerDoctrineError(f"BROKER_PLAN_NOT_FOUND: {retrieval_plan_id}") from exc

    def all_plans(self) -> tuple[BrokerRetrievalPlan, ...]:
        return tuple(self._plans[key] for key in sorted(self._plans))

    def _validate(self) -> None:
        if len(self._plans) < len(BrokerRetrievalOperation):
            raise BrokerDoctrineError("not every broker retrieval operation has a plan")
        for plan in self._plans.values():
            if not plan.authorized_requesting_offices or not plan.evidence_retention_rule:
                raise BrokerDoctrineError(f"incomplete broker retrieval plan: {plan.retrieval_plan_id}")


class BrokerInformationGateway:
    """Authorizes broker observations without making broker data universal truth."""

    def __init__(self, registry: BrokerRetrievalPlanRegistry | None = None) -> None:
        self.registry = registry or BrokerRetrievalPlanRegistry()

    def observe(self, request: BrokerRetrievalRequest, payload: Mapping[str, Any] | None, *, raw_evidence_reference: str = "") -> BrokerObservationEnvelope:
        plan = self.registry.resolve(request.retrieval_plan_id)
        if request.requesting_office not in plan.authorized_requesting_offices:
            return _envelope(request, plan, BrokerInformationState.UNKNOWN, {}, raw_evidence_reference, "authorization_failed")
        if request.account.environment not in request.broker.supported_environment_types:
            return _envelope(request, plan, BrokerInformationState.UNAVAILABLE, {}, raw_evidence_reference, "environment_not_supported")
        if request.account.environment is BrokerEnvironment.LIVE and request.broker.broker_id.endswith("PAPER"):
            return _envelope(request, plan, BrokerInformationState.CONFLICTED, {}, raw_evidence_reference, "paper_broker_cannot_satisfy_live_query")
        if plan.broker_capability_required not in request.broker.supported_retrieval_capabilities:
            return _envelope(request, plan, BrokerInformationState.UNSUPPORTED, {}, raw_evidence_reference, "capability_unsupported")
        if not payload:
            return _envelope(request, plan, BrokerInformationState.UNAVAILABLE, {}, raw_evidence_reference, "broker_fact_unavailable")
        if not raw_evidence_reference:
            return _envelope(request, plan, BrokerInformationState.INCOMPLETE, dict(payload), raw_evidence_reference, "raw_evidence_required")
        return _envelope(request, plan, BrokerInformationState.OBSERVED_CURRENT, dict(payload), raw_evidence_reference, "")


def reconcile_broker_truth(
    *,
    environment: BrokerEnvironment,
    broker_id: str,
    account_pseudonym: str,
    internal_facts: Mapping[str, Any],
    broker_facts: Mapping[str, Any],
    evidence_references: tuple[str, ...],
) -> BrokerReconciliationRecord:
    mismatches = {key: f"internal={internal_facts.get(key)!r}; broker={broker_facts.get(key)!r}" for key in sorted(set(internal_facts) | set(broker_facts)) if internal_facts.get(key) != broker_facts.get(key)}
    severity = ReconciliationSeverity.NONE if not mismatches else ReconciliationSeverity.HIGH
    return BrokerReconciliationRecord(
        _stable_id("BREC", broker_id, account_pseudonym, internal_facts, broker_facts),
        "broker_internal_state_comparison",
        "explicit_reconciliation_request",
        environment,
        broker_id,
        account_pseudonym,
        "account_order_position_execution",
        tuple(sorted(internal_facts)),
        tuple(sorted(broker_facts)),
        utc_timestamp(),
        MO_SP_008_VERSION,
        tuple(sorted(set(internal_facts) & set(broker_facts))),
        tuple(sorted(set(broker_facts) - set(internal_facts))),
        tuple(sorted(set(internal_facts) - set(broker_facts))),
        MappingProxyType(mismatches),
        severity,
        "RECONCILIATION_REQUIRED" if mismatches else "RECONCILED",
        "Risk",
        "investigate_mismatch" if mismatches else "none",
        "BLOCK_NEW_ORDER" if mismatches else "NO_BLOCK",
        evidence_references,
        (_stable_id("BRAUD", broker_id, account_pseudonym, mismatches),),
    )


def default_broker_identity() -> BrokerIdentity:
    return BrokerIdentity(
        "BROKER-PAPER",
        "Configured Paper Broker",
        "DeterministicPaperBrokerAdapter",
        "1.0.0",
        (BrokerEnvironment.PAPER,),
        tuple(BrokerRetrievalOperation),
        ("order_events", "account_events"),
        ("equity", "option", "cash"),
        ("paper_margin", "paper_cash"),
        "ACTIVE",
        "APPROVED_PAPER_ONLY",
        "2026-07-20T00:00:00Z",
    )


def default_account_reference() -> BrokerageAccountReference:
    return BrokerageAccountReference(
        "BROKER-PAPER",
        "ACCT-PSEUDONYM-001",
        BrokerEnvironment.PAPER,
        "paper_margin",
        "USD",
        True,
        True,
        ("equity", "option", "cash"),
        "ACTIVE",
        "2026-07-20T00:00:00Z",
        "account_execution_state",
        "BROKER_AUTHORIZED_PAPER",
    )


def default_broker_retrieval_plans() -> tuple[BrokerRetrievalPlan, ...]:
    return tuple(_plan(operation) for operation in BrokerRetrievalOperation)


def _plan(operation: BrokerRetrievalOperation) -> BrokerRetrievalPlan:
    freshness = 15 if operation is BrokerRetrievalOperation.BUYING_POWER else 30 if operation in {BrokerRetrievalOperation.CURRENT_POSITIONS, BrokerRetrievalOperation.SPECIFIC_POSITION} else 60
    offices = {
        BrokerRetrievalOperation.ACCOUNT_STATUS: ("Intelligence", "Trader", "Risk", "Historian"),
        BrokerRetrievalOperation.ACCOUNT_RESTRICTIONS: ("Intelligence", "Trader", "Risk", "Historian"),
        BrokerRetrievalOperation.ACCOUNT_BALANCES: ("Intelligence", "Risk", "Historian"),
        BrokerRetrievalOperation.BUYING_POWER: ("Intelligence", "Trader", "Risk", "Historian"),
        BrokerRetrievalOperation.MARGIN_STATE: ("Intelligence", "Risk", "Historian"),
        BrokerRetrievalOperation.CURRENT_POSITIONS: ("Intelligence", "Trader", "Risk", "Historian"),
        BrokerRetrievalOperation.SPECIFIC_POSITION: ("Intelligence", "Trader", "Risk", "Historian"),
        BrokerRetrievalOperation.OPEN_ORDERS: ("Intelligence", "Trader", "Risk", "Historian"),
        BrokerRetrievalOperation.SPECIFIC_ORDER: ("Intelligence", "Trader", "Risk", "Historian"),
        BrokerRetrievalOperation.COMPLETED_ORDERS: ("Intelligence", "Trader", "Historian"),
        BrokerRetrievalOperation.FILLS_EXECUTIONS: ("Intelligence", "Trader", "Risk", "Historian"),
        BrokerRetrievalOperation.REJECTED_ORDERS: ("Intelligence", "Trader", "Historian"),
        BrokerRetrievalOperation.CANCELLED_ORDERS: ("Intelligence", "Trader", "Historian"),
        BrokerRetrievalOperation.ASSIGNMENT_EXERCISE: ("Intelligence", "Trader", "Risk", "Historian"),
        BrokerRetrievalOperation.CORPORATE_ACTION_ADJUSTMENTS: ("Intelligence", "Trader", "Risk", "Historian"),
        BrokerRetrievalOperation.CLOSED_POSITIONS: ("Intelligence", "Historian", "Risk"),
        BrokerRetrievalOperation.BROKER_HEALTH: ("Intelligence", "Trader", "Risk", "Historian", "Commander"),
    }[operation]
    return BrokerRetrievalPlan(
        f"BRP-{operation.value.upper()}",
        "1.0.0",
        operation.value,
        offices,
        operation,
        operation,
        ("startup", "pre_order", "polling", "event", "reconciliation", "shutdown"),
        300 if operation is BrokerRetrievalOperation.ACCOUNT_STATUS else 5,
        2 if operation in {BrokerRetrievalOperation.SPECIFIC_ORDER, BrokerRetrievalOperation.FILLS_EXECUTIONS} else 30,
        900,
        operation in {BrokerRetrievalOperation.SPECIFIC_ORDER, BrokerRetrievalOperation.FILLS_EXECUTIONS, BrokerRetrievalOperation.BROKER_HEALTH},
        freshness,
        "cache_permitted_only_with_freshness_state",
        freshness,
        10,
        1,
        2,
        (2, 5, 10),
        "return RATE_LIMITED explicit state",
        "no substitute broker source",
        "raw broker payload or durable reference required",
        "BROKER_INCLUDED",
        "terminal broker state or explicit unavailable/outage/unsupported state",
        "Risk" if operation in {BrokerRetrievalOperation.BUYING_POWER, BrokerRetrievalOperation.CURRENT_POSITIONS, BrokerRetrievalOperation.MARGIN_STATE} else "Trader",
        "TRADE_BLOCKING" if operation in {BrokerRetrievalOperation.BUYING_POWER, BrokerRetrievalOperation.CURRENT_POSITIONS, BrokerRetrievalOperation.SPECIFIC_ORDER} else "NON_BLOCKING_UNLESS_CONFLICTED",
    )


def _envelope(
    request: BrokerRetrievalRequest,
    plan: BrokerRetrievalPlan,
    state: BrokerInformationState,
    facts: Mapping[str, Any],
    raw_evidence_reference: str,
    failure: str,
) -> BrokerObservationEnvelope:
    now = utc_timestamp()
    return BrokerObservationEnvelope(
        _stable_id("BOBS", request.request_id, plan.retrieval_plan_id, state.value, raw_evidence_reference),
        plan.retrieval_plan_id,
        plan.version,
        request.workflow_id,
        request.workflow_execution_token_id,
        request.decision_object_id,
        request.parameters.get("position_object_id", ""),
        request.parameters.get("internal_order_id", ""),
        request.parameters.get("broker_order_id", ""),
        request.parameters.get("broker_execution_id", ""),
        request.requesting_office,
        "BrokerInformationGateway",
        request.broker.broker_id,
        request.account.account_pseudonym,
        request.account.environment,
        request.broker.adapter_version,
        plan.adapter_operation,
        MappingProxyType(dict(request.parameters)),
        now,
        now,
        str(facts.get("broker_timestamp", "UNKNOWN")),
        str(facts.get("source_timezone", "UTC")),
        now,
        state,
        "OK" if state is BrokerInformationState.OBSERVED_CURRENT else "NO_ACCEPTED_FACT",
        str(facts.get("broker_error_code", "")),
        raw_evidence_reference,
        _stable_digest(facts) if facts else "",
        MO_SP_008_VERSION,
        "NO_CACHE",
        (),
        int(facts.get("latency_ms", 0)) if facts else 0,
        plan.cost_class,
        state,
        MappingProxyType(dict(facts)),
        tuple(() if not failure else (failure,)),
        BrokerInformationState.UNKNOWN if state is BrokerInformationState.OBSERVED_CURRENT else state,
        "NONE" if state is BrokerInformationState.OBSERVED_CURRENT else plan.escalation_route,
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
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name != "plan_digest"}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
