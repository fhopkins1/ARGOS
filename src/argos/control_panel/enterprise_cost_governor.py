"""Enterprise Cost Governor for ARGOS EO-CE."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp


MONEY = Decimal("0.0001")


class BudgetScope(str, Enum):
    ENTERPRISE = "enterprise"
    PERIOD = "period"
    RESERVE = "reserve"
    OPERATING_MODE = "operating_mode"
    MISSION_TYPE = "mission_type"
    MISSION = "mission"
    WORKFLOW = "workflow"
    OFFICE = "office"
    PROVIDER = "provider"
    MODEL = "model"
    DATA_SOURCE = "data_source"
    STRATEGY = "strategy"
    COMMANDER_DIRECTIVE = "commander_directive"


class BudgetCategory(str, Enum):
    POSITION_SAFETY = "position_safety"
    BROKER_RECONCILIATION = "broker_reconciliation"
    LEDGER_INTEGRITY = "ledger_integrity"
    RISK_CONTROL = "risk_control"
    REQUIRED_LIFECYCLE = "required_lifecycle"
    EMERGENCY_RECOVERY = "emergency_recovery"
    COMMANDER_RESERVE = "commander_reserve"
    TACTICAL_OPERATIONS = "tactical_operations"
    OPPORTUNITY_DISCOVERY = "opportunity_discovery"
    STRATEGIC_RESEARCH = "strategic_research"
    HISTORICAL_ANALYSIS = "historical_analysis"
    CAPABILITY_DEVELOPMENT = "capability_development"
    ENTERPRISE_OVERHEAD = "enterprise_overhead"


class BudgetPeriodType(str, Enum):
    MISSION = "mission"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class BudgetState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    WARNING = "warning"
    RESTRICTED = "restricted"
    EXHAUSTED = "exhausted"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    RECONCILING = "reconciling"
    FAULTED = "faulted"


class ReservationState(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REDUCED = "reduced"
    DEFERRED = "deferred"
    REJECTED = "rejected"
    ACTIVE = "active"
    PARTIALLY_CONSUMED = "partially_consumed"
    CONSUMED = "consumed"
    RELEASED = "released"
    EXPIRED = "expired"
    CANCELED = "canceled"
    SETTLING = "settling"
    SETTLED = "settled"
    FAULTED = "faulted"


class CostAuthorizationDecision(str, Enum):
    APPROVE = "approve"
    APPROVE_REDUCED = "approve_reduced"
    DEFER = "defer"
    REJECT = "reject"
    REQUIRE_COMMANDER_OVERRIDE = "require_commander_override"
    SAFETY_RESERVE_ONLY = "safety_reserve_only"
    LOCAL_ONLY = "local_only"


class CostType(str, Enum):
    MODEL_INPUT = "model_input"
    MODEL_OUTPUT = "model_output"
    MODEL_CACHED_INPUT = "model_cached_input"
    MODEL_REASONING = "model_reasoning"
    API_REQUEST = "api_request"
    PAID_DATA = "paid_data"
    BROKER_DATA = "broker_data"
    EMBEDDING = "embedding"
    IMAGE = "image"
    STORAGE = "storage"
    LOCAL_COMPUTE = "local_compute"
    RUNTIME = "runtime"
    RETRY = "retry"
    OTHER = "other"


@dataclass(frozen=True)
class EnterpriseBudgetPolicy:
    policy_id: str
    version: int
    name: str
    description: str
    state: BudgetState
    currency: str
    daily_limit: Decimal
    weekly_limit: Decimal
    monthly_limit: Decimal
    warning_threshold_percent: Decimal
    restriction_threshold_percent: Decimal
    hard_stop_threshold_percent: Decimal
    category_allocations: dict[BudgetCategory, Decimal]
    protected_reserve_allocations: dict[BudgetCategory, Decimal]
    office_limits: dict[str, Decimal]
    mission_type_limits: dict[str, Decimal]
    model_limits: dict[str, Decimal]
    provider_limits: dict[str, Decimal]
    data_source_limits: dict[str, Decimal]
    allowed_models: tuple[str, ...]
    prohibited_models: tuple[str, ...]
    allowed_providers: tuple[str, ...]
    prohibited_providers: tuple[str, ...]
    max_api_calls_per_mission: int
    max_api_calls_per_office: int
    max_tokens_per_mission: int | None
    max_tokens_per_office: int | None
    emergency_override_limit: Decimal
    commander_override_limit: Decimal
    effective_at: str
    expires_at: str
    created_by: str
    created_at: str
    reason: str
    content_hash: str


@dataclass(frozen=True)
class BudgetAccount:
    budget_account_id: str
    scope: BudgetScope
    scope_id: str
    category: BudgetCategory
    period_type: BudgetPeriodType
    period_start: str
    period_end: str
    currency: str
    allocated_amount: Decimal
    protected_amount: Decimal
    reserved_amount: Decimal
    committed_amount: Decimal
    incurred_amount: Decimal
    settled_amount: Decimal
    released_amount: Decimal
    available_amount: Decimal
    warning_threshold: Decimal
    restriction_threshold: Decimal
    hard_limit: Decimal
    state: BudgetState
    policy_id: str
    policy_version: int
    updated_at: str
    content_hash: str


@dataclass(frozen=True)
class CostReservationRequest:
    reservation_request_id: str
    mission_plan_id: str
    mission_plan_version: int
    mission_id: str
    workflow_id: str
    mission_type: str
    priority_class: str
    budget_category: BudgetCategory
    requesting_office_id: str
    requested_by: str
    estimated_minimum_cost: Decimal
    estimated_expected_cost: Decimal
    estimated_maximum_cost: Decimal
    requested_reservation_amount: Decimal
    requested_api_calls: int
    requested_paid_data_calls: int
    requested_input_tokens: int | None
    requested_output_tokens: int | None
    requested_models: tuple[str, ...]
    requested_providers: tuple[str, ...]
    requested_data_sources: tuple[str, ...]
    estimated_runtime_seconds: int
    deadline_at: str
    safety_critical: bool
    open_position_related: bool
    active_order_related: bool
    estimate_basis: dict[str, Any]
    estimate_confidence: float
    submitted_at: str


@dataclass(frozen=True)
class CostReservation:
    reservation_id: str
    reservation_request_id: str
    state: ReservationState
    decision: CostAuthorizationDecision
    budget_account_ids: tuple[str, ...]
    mission_plan_id: str
    mission_plan_version: int
    mission_id: str
    workflow_id: str
    office_id: str
    budget_category: BudgetCategory
    requested_amount: Decimal
    approved_amount: Decimal
    consumed_amount: Decimal
    released_amount: Decimal
    approved_api_calls: int
    consumed_api_calls: int
    approved_input_tokens: int | None
    consumed_input_tokens: int
    approved_output_tokens: int | None
    consumed_output_tokens: int
    allowed_models: tuple[str, ...]
    allowed_providers: tuple[str, ...]
    allowed_data_sources: tuple[str, ...]
    approved_runtime_seconds: int
    consumed_runtime_seconds: int
    safety_reserve_used: bool
    override_id: str
    approval_reason: str
    restriction_reason: str
    approved_at: str
    activated_at: str
    expires_at: str
    released_at: str
    settled_at: str
    content_hash: str


@dataclass(frozen=True)
class CostAuthorizationRequest:
    authorization_request_id: str
    reservation_id: str
    mission_id: str
    workflow_id: str
    office_id: str
    provider: str
    model: str
    operation_type: CostType
    estimated_cost: Decimal
    input_tokens: int
    output_tokens: int
    paid_data_calls: int
    purpose: str
    correlation_id: str
    requested_at: str


@dataclass(frozen=True)
class CostAuthorizationRecord:
    authorization_id: str
    request: CostAuthorizationRequest
    allowed: bool
    decision: CostAuthorizationDecision
    reason: str
    reservation_state: ReservationState
    created_at: str
    content_hash: str


@dataclass(frozen=True)
class CostUsageRecord:
    usage_id: str
    idempotency_key: str
    authorization_id: str
    reservation_id: str
    mission_id: str
    mission_plan_id: str
    workflow_id: str
    office_id: str
    provider: str
    model: str
    cost_type: CostType
    estimated_cost: Decimal
    actual_cost: Decimal
    input_tokens: int
    output_tokens: int
    api_calls: int
    runtime_seconds: int
    provider_reported_cost: Decimal
    variance: Decimal
    recorded_at: str
    settled: bool
    content_hash: str


@dataclass(frozen=True)
class CostLedgerEntry:
    ledger_entry_id: str
    entry_type: str
    reservation_id: str
    usage_id: str
    budget_account_id: str
    amount: Decimal
    estimated: Decimal
    reserved: Decimal
    incurred: Decimal
    settled: Decimal
    released: Decimal
    timestamp: str
    reason: str
    content_hash: str


@dataclass(frozen=True)
class CircuitBreakerRecord:
    circuit_breaker_id: str
    scope: str
    severity: str
    current_state: str
    trigger_value: Decimal
    threshold: Decimal
    blocked_activity: str
    allowed_safety_activity: str
    created_at: str
    resolved_at: str


@dataclass(frozen=True)
class CostOverrideRecord:
    override_id: str
    scope: str
    amount: Decimal
    expires_at: str
    actor: str
    reason: str
    approval_source: str
    permitted_models: tuple[str, ...]
    permitted_providers: tuple[str, ...]
    single_use: bool
    used: bool
    audit_record: str


class EnterpriseCostGovernor:
    """Authoritative computational-capital governor."""

    def __init__(self) -> None:
        self._policy_versions: list[EnterpriseBudgetPolicy] = [_hash_policy(_default_policy())]
        self._accounts: dict[str, BudgetAccount] = _default_accounts(self.policy)
        self._reservation_requests: dict[str, CostReservationRequest] = {}
        self._reservations: dict[str, CostReservation] = {}
        self._authorizations: list[CostAuthorizationRecord] = []
        self._usage: dict[str, CostUsageRecord] = {}
        self._ledger: list[CostLedgerEntry] = []
        self._overrides: list[CostOverrideRecord] = []
        self._circuit_breakers: list[CircuitBreakerRecord] = []
        self._alerts: list[dict[str, Any]] = []
        self._dead_letters: list[dict[str, Any]] = []

    @property
    def policy(self) -> EnterpriseBudgetPolicy:
        return self._policy_versions[-1]

    def snapshot(self) -> dict[str, Any]:
        accounts = tuple(self._accounts.values())
        reservations = tuple(self._reservations.values())
        usage = tuple(self._usage.values())
        return {
            "governorName": "Enterprise Cost Governor",
            "engineeringOrder": "EO-CE",
            "status": "HEALTHY" if not any(item.current_state == "blocked" for item in self._circuit_breakers) else "RESTRICTED",
            "activePolicy": _snapshot_dataclass(self.policy),
            "policyVersions": tuple(_snapshot_dataclass(item) for item in self._policy_versions),
            "budgetAccounts": tuple(_snapshot_dataclass(item) for item in accounts),
            "budgetAllocation": _budget_allocation(accounts),
            "protectedReserves": tuple(_snapshot_dataclass(item) for item in accounts if item.scope == BudgetScope.RESERVE),
            "missionReservations": tuple(_snapshot_dataclass(item) for item in reservations),
            "authorizationStream": tuple(_snapshot_dataclass(item) for item in self._authorizations[-40:]),
            "usageRecords": tuple(_snapshot_dataclass(item) for item in usage),
            "costLedger": tuple(_snapshot_dataclass(item) for item in self._ledger[-80:]),
            "officeCostTable": _office_cost_table(usage, self.policy),
            "providerModelUsage": _provider_model_usage(usage),
            "circuitBreakers": tuple(_snapshot_dataclass(item) for item in self._circuit_breakers),
            "alerts": tuple(self._alerts[-30:]),
            "overrides": tuple(_snapshot_dataclass(item) for item in self._overrides[-20:]),
            "forecast": self._forecast(),
            "metrics": self._metrics(),
            "lawCE": {
                "unattributedSpendBlocked": True,
                "reservationBeforeExpenditure": True,
                "protectedReservesEnforced": True,
                "costAuthorityCreatesMissions": False,
                "officeWakeAuthority": False,
                "investmentDecisionAuthority": False,
                "directProviderBypassAllowed": False,
                "uiCanBypassBackendPolicy": False,
            },
            "gatewayIntegration": {
                "mandatory": True,
                "perCallAuthorizationRequired": True,
                "usageReportedAfterExecution": True,
                "unreservedCallsBlocked": True,
            },
            "replay": {"available": True, "productionMutation": False},
        }

    def create_policy_version(self, updates: dict[str, Any], *, actor: str = "Commander", reason: str = "Commander policy update.") -> EnterpriseBudgetPolicy:
        current = self.policy
        new_policy = replace(
            current,
            version=current.version + 1,
            daily_limit=_money(updates.get("daily_limit", updates.get("dailyLimit", current.daily_limit))),
            weekly_limit=_money(updates.get("weekly_limit", updates.get("weeklyLimit", current.weekly_limit))),
            monthly_limit=_money(updates.get("monthly_limit", updates.get("monthlyLimit", current.monthly_limit))),
            created_by=actor,
            created_at=utc_timestamp(),
            reason=reason,
            content_hash="",
        )
        new_policy = _hash_policy(new_policy)
        self._policy_versions.append(new_policy)
        self._audit_ledger("policy_version", "", "", "ENTERPRISE-DAILY", Decimal("0"), f"Policy updated by {actor}: {reason}")
        return new_policy

    def request_reservation_from_plan(self, plan: dict[str, Any], *, mission_id: str = "", workflow_id: str = "", office_id: str = "") -> CostReservation:
        envelope = plan.get("resource_envelope", {}) or {}
        request = CostReservationRequest(
            reservation_request_id=f"ECG-REQ-{len(self._reservation_requests) + 1:06d}",
            mission_plan_id=str(plan.get("mission_plan_id", "")),
            mission_plan_version=int(plan.get("plan_version", 1) or 1),
            mission_id=mission_id,
            workflow_id=workflow_id,
            mission_type=str(plan.get("mission_type", "")),
            priority_class=str(plan.get("priority_class", "")),
            budget_category=_category_for(str(plan.get("mission_type", "")), str(plan.get("priority_class", ""))),
            requesting_office_id=office_id,
            requested_by="EnterpriseMissionPlanner",
            estimated_minimum_cost=_money(envelope.get("estimated_cost_usd", 0)),
            estimated_expected_cost=_money(envelope.get("estimated_cost_usd", 0)),
            estimated_maximum_cost=_money(envelope.get("estimated_cost_usd", 0)),
            requested_reservation_amount=_money(envelope.get("estimated_cost_usd", 0)),
            requested_api_calls=int(envelope.get("api_call_ceiling", 0) or 0),
            requested_paid_data_calls=int(envelope.get("paid_data_call_ceiling", 0) or 0),
            requested_input_tokens=int(envelope.get("token_ceiling", 0) or 0),
            requested_output_tokens=int(envelope.get("token_ceiling", 0) or 0),
            requested_models=("deterministic", "dry-run-model", "gpt-4.1-mini"),
            requested_providers=("none", "openai"),
            requested_data_sources=(),
            estimated_runtime_seconds=int(envelope.get("runtime_ceiling_seconds", 0) or 0),
            deadline_at="",
            safety_critical=_is_safety_category(_category_for(str(plan.get("mission_type", "")), str(plan.get("priority_class", ""))),
            ),
            open_position_related=str(plan.get("mission_type", "")).startswith("position"),
            active_order_related="broker" in str(plan.get("mission_type", "")) or "order" in str(plan.get("mission_type", "")),
            estimate_basis=dict(envelope.get("estimate_basis", {})) if isinstance(envelope.get("estimate_basis"), dict) else {"basis": envelope.get("estimate_basis", ())},
            estimate_confidence=float(envelope.get("estimate_confidence", 0.8) or 0.8),
            submitted_at=utc_timestamp(),
        )
        return self.request_reservation(request)

    def request_reservation(self, request: CostReservationRequest | dict[str, Any]) -> CostReservation:
        if isinstance(request, dict):
            request = _reservation_request_from_dict(request)
        self._reservation_requests[request.reservation_request_id] = request
        missing = _missing_attribution(request)
        if missing:
            return self._reservation_from_request(request, CostAuthorizationDecision.REJECT, ReservationState.REJECTED, Decimal("0"), f"Missing attribution: {', '.join(missing)}")
        account = self._account_for(request.budget_category)
        if not account:
            return self._reservation_from_request(request, CostAuthorizationDecision.DEFER, ReservationState.DEFERRED, Decimal("0"), "No budget account exists for category.")
        policy = self.policy
        if any(model in policy.prohibited_models for model in request.requested_models):
            return self._reservation_from_request(request, CostAuthorizationDecision.REJECT, ReservationState.REJECTED, Decimal("0"), "Requested model is prohibited.")
        if any(provider in policy.prohibited_providers for provider in request.requested_providers):
            return self._reservation_from_request(request, CostAuthorizationDecision.REJECT, ReservationState.REJECTED, Decimal("0"), "Requested provider is prohibited.")
        if request.requested_api_calls > policy.max_api_calls_per_mission:
            approved_calls = policy.max_api_calls_per_mission
            reduced = min(account.available_amount, request.requested_reservation_amount, _money("0.01") * Decimal(approved_calls))
            return self._reservation_from_request(request, CostAuthorizationDecision.APPROVE_REDUCED, ReservationState.REDUCED, reduced, "API-call ceiling reduced reservation.", approved_api_calls=approved_calls)
        if request.requested_reservation_amount <= Decimal("0") or request.requested_api_calls == 0:
            return self._reservation_from_request(request, CostAuthorizationDecision.LOCAL_ONLY, ReservationState.APPROVED, Decimal("0"), "Local or deterministic work requires no paid reservation.", approved_api_calls=0)
        if request.requested_reservation_amount > account.available_amount:
            if _is_safety_category(request.budget_category):
                reserve = self._reserve_account_for(request.budget_category)
                if reserve and request.requested_reservation_amount <= reserve.available_amount:
                    return self._reservation_from_request(request, CostAuthorizationDecision.SAFETY_RESERVE_ONLY, ReservationState.APPROVED, request.requested_reservation_amount, "Approved from protected safety reserve.", reserve=True)
            decision = CostAuthorizationDecision.DEFER if account.available_amount > Decimal("0") else CostAuthorizationDecision.REJECT
            state = ReservationState.DEFERRED if decision == CostAuthorizationDecision.DEFER else ReservationState.REJECTED
            return self._reservation_from_request(request, decision, state, Decimal("0"), "Insufficient discretionary budget; protected reserves remain untouched.")
        return self._reservation_from_request(request, CostAuthorizationDecision.APPROVE, ReservationState.APPROVED, request.requested_reservation_amount, "Reservation approved inside policy limits.")

    def activate_reservation(self, reservation_id: str, *, mission_id: str = "", workflow_id: str = "") -> CostReservation:
        reservation = self._reservations[reservation_id]
        if reservation.state not in {ReservationState.APPROVED, ReservationState.REDUCED}:
            return reservation
        active = replace(reservation, state=ReservationState.ACTIVE, mission_id=mission_id or reservation.mission_id, workflow_id=workflow_id or reservation.workflow_id, activated_at=utc_timestamp())
        active = _hash_reservation(active)
        self._reservations[reservation_id] = active
        return active

    def authorize_gateway_request(self, request: Any) -> dict[str, Any]:
        reservation_id = str(getattr(request, "cost_reservation_id", "") or getattr(request, "reservation_id", ""))
        estimated_cost = _money(getattr(request, "max_cost_usd", 0))
        provider = str(getattr(request, "provider", "none"))
        model = str(getattr(request, "model", ""))
        office = str(getattr(request, "requesting_office", "") or getattr(request, "office_id", ""))
        mission_id = str(getattr(request, "mission_id", ""))
        workflow_id = str(getattr(request, "workflow_id", ""))
        correlation = str(getattr(request, "audit_identifier", "") or f"ECG-AUTH-{len(self._authorizations) + 1:06d}")
        if not reservation_id:
            if str(getattr(request, "execution_mode", "")) == "real_api_pilot":
                reservation = self._gateway_reservation_for_real_api_pilot(request, estimated_cost, provider, model, office, mission_id, workflow_id)
                if reservation.state not in {ReservationState.ACTIVE, ReservationState.APPROVED, ReservationState.REDUCED}:
                    record = self._authorization_record(
                        None,
                        reservation.reservation_id,
                        mission_id or reservation.mission_id,
                        workflow_id or reservation.workflow_id,
                        office or reservation.office_id,
                        provider,
                        model,
                        estimated_cost,
                        False,
                        reservation.decision,
                        reservation.decision_reason,
                    )
                    return {
                        "allowed": False,
                        "code": "COST_GOVERNOR_RESERVATION_REJECTED",
                        "reason": record.reason,
                        "authorizationId": record.authorization_id,
                        "reservationId": reservation.reservation_id,
                    }
                reservation_id = reservation.reservation_id
            else:
                record = self._authorization_record(None, reservation_id, mission_id, workflow_id, office, provider, model, estimated_cost, False, CostAuthorizationDecision.REJECT, "Missing active cost reservation.")
                return {"allowed": False, "code": "COST_GOVERNOR_UNRESERVED_CALL", "reason": record.reason, "authorizationId": record.authorization_id}
        reservation = self._reservations.get(reservation_id)
        if not reservation:
            record = self._authorization_record(None, reservation_id, mission_id, workflow_id, office, provider, model, estimated_cost, False, CostAuthorizationDecision.REJECT, "Unknown cost reservation.")
            return {"allowed": False, "code": "COST_GOVERNOR_UNKNOWN_RESERVATION", "reason": record.reason, "authorizationId": record.authorization_id}
        auth_request = CostAuthorizationRequest(
            authorization_request_id=f"ECG-AUTH-REQ-{len(self._authorizations) + 1:06d}",
            reservation_id=reservation_id,
            mission_id=mission_id or reservation.mission_id,
            workflow_id=workflow_id or reservation.workflow_id,
            office_id=office or reservation.office_id,
            provider=provider,
            model=model,
            operation_type=CostType.API_REQUEST,
            estimated_cost=estimated_cost,
            input_tokens=int(getattr(request, "max_input_tokens", 0) or 0),
            output_tokens=int(getattr(request, "max_output_tokens", 0) or 0),
            paid_data_calls=0,
            purpose=str(getattr(request, "task_type", "")),
            correlation_id=correlation,
            requested_at=utc_timestamp(),
        )
        allowed, code, reason, decision = self._authorize(auth_request, reservation)
        record = self._authorization_record(auth_request, reservation_id, auth_request.mission_id, auth_request.workflow_id, auth_request.office_id, provider, model, estimated_cost, allowed, decision, reason)
        return {"allowed": allowed, "code": code, "reason": reason, "authorizationId": record.authorization_id, "reservationId": reservation_id}

    def _gateway_reservation_for_real_api_pilot(
        self,
        request: Any,
        estimated_cost: Decimal,
        provider: str,
        model: str,
        office: str,
        mission_id: str,
        workflow_id: str,
    ) -> CostReservation:
        correlation = str(getattr(request, "audit_identifier", "") or f"GWY-{len(self._reservation_requests) + 1:06d}")
        category = BudgetCategory.RISK_CONTROL if office.lower() in {"risk", "trader"} else BudgetCategory.TACTICAL_OPERATIONS
        reservation_request = CostReservationRequest(
            reservation_request_id=f"ECG-REQ-GWY-{len(self._reservation_requests) + 1:06d}",
            mission_plan_id=f"GATEWAY-REAL-API-PILOT-{correlation}",
            mission_plan_version=1,
            mission_id=mission_id or f"REAL-API-PILOT-{workflow_id or correlation}",
            workflow_id=workflow_id or f"WORKFLOW-{correlation}",
            mission_type="real_api_pilot_gateway_execution",
            priority_class="tactical_evaluation",
            budget_category=category,
            requesting_office_id=office or "Unknown",
            requested_by="ApiExecutionGateway",
            estimated_minimum_cost=estimated_cost,
            estimated_expected_cost=estimated_cost,
            estimated_maximum_cost=estimated_cost,
            requested_reservation_amount=estimated_cost,
            requested_api_calls=1,
            requested_paid_data_calls=0,
            requested_input_tokens=int(getattr(request, "max_input_tokens", 0) or 0),
            requested_output_tokens=int(getattr(request, "max_output_tokens", 0) or 0),
            requested_models=(model,),
            requested_providers=(provider,),
            requested_data_sources=(),
            estimated_runtime_seconds=int(getattr(request, "max_runtime_seconds", 0) or 0),
            deadline_at="",
            safety_critical=category == BudgetCategory.RISK_CONTROL,
            open_position_related=office.lower() == "trader",
            active_order_related=False,
            estimate_basis={"basis": "API Execution Gateway real_api_pilot reservation", "correlation_id": correlation},
            estimate_confidence=0.90,
            submitted_at=utc_timestamp(),
        )
        reservation = self.request_reservation(reservation_request)
        if reservation.state in {ReservationState.APPROVED, ReservationState.REDUCED}:
            return self.activate_reservation(reservation.reservation_id, mission_id=reservation_request.mission_id, workflow_id=reservation_request.workflow_id)
        return reservation

    def record_gateway_usage(self, request: Any, response: Any, authorization: dict[str, Any]) -> dict[str, Any]:
        reservation_id = str(authorization.get("reservationId", "") or getattr(request, "cost_reservation_id", ""))
        if not reservation_id or reservation_id not in self._reservations:
            return {"recorded": False, "reason": "No reservation for usage record."}
        idempotency = f"{reservation_id}:{getattr(request, 'audit_identifier', '')}:{getattr(response, 'execution_status', '')}"
        if idempotency in self._usage:
            self._alerts.append({"alertType": "duplicate_usage_report", "severity": "INFO", "reservationId": reservation_id, "timestamp": utc_timestamp()})
            return {"recorded": False, "duplicate": True, "usageId": self._usage[idempotency].usage_id}
        reservation = self._reservations[reservation_id]
        actual = _money(getattr(response, "actual_cost_usd", 0))
        usage = CostUsageRecord(
            usage_id=f"ECG-USG-{len(self._usage) + 1:06d}",
            idempotency_key=idempotency,
            authorization_id=str(authorization.get("authorizationId", "")),
            reservation_id=reservation_id,
            mission_id=reservation.mission_id,
            mission_plan_id=reservation.mission_plan_id,
            workflow_id=reservation.workflow_id or str(getattr(request, "workflow_id", "")),
            office_id=reservation.office_id or str(getattr(request, "requesting_office", "")),
            provider=str(getattr(response, "provider", getattr(request, "provider", "none"))),
            model=str(getattr(response, "model", getattr(request, "model", ""))),
            cost_type=CostType.API_REQUEST,
            estimated_cost=_money(getattr(response, "estimated_cost_usd", 0)),
            actual_cost=actual,
            input_tokens=int(getattr(response, "input_tokens", 0) or 0),
            output_tokens=int(getattr(response, "output_tokens", 0) or 0),
            api_calls=1 if actual > 0 else 0,
            runtime_seconds=max(0, int(getattr(request, "max_runtime_seconds", 0) or 0)),
            provider_reported_cost=actual,
            variance=Decimal("0"),
            recorded_at=utc_timestamp(),
            settled=False,
            content_hash="",
        )
        usage = _hash_usage(usage)
        self._usage[idempotency] = usage
        consumed = reservation.consumed_amount + actual
        state = ReservationState.CONSUMED if consumed >= reservation.approved_amount and reservation.approved_amount > 0 else ReservationState.PARTIALLY_CONSUMED
        updated = replace(
            reservation,
            consumed_amount=_money(consumed),
            consumed_api_calls=reservation.consumed_api_calls + usage.api_calls,
            consumed_input_tokens=reservation.consumed_input_tokens + usage.input_tokens,
            consumed_output_tokens=reservation.consumed_output_tokens + usage.output_tokens,
            consumed_runtime_seconds=reservation.consumed_runtime_seconds + usage.runtime_seconds,
            state=state,
        )
        updated = _hash_reservation(updated)
        self._reservations[reservation_id] = updated
        self._apply_incurred(updated.budget_account_ids, actual, usage.usage_id)
        self._check_thresholds()
        return {"recorded": True, "usageId": usage.usage_id}

    def settle_reservation(self, reservation_id: str) -> CostReservation:
        reservation = self._reservations[reservation_id]
        release = max(Decimal("0"), reservation.approved_amount - reservation.consumed_amount - reservation.released_amount)
        settled = replace(reservation, state=ReservationState.SETTLED, released_amount=_money(reservation.released_amount + release), settled_at=utc_timestamp())
        settled = _hash_reservation(settled)
        self._reservations[reservation_id] = settled
        for account_id in reservation.budget_account_ids:
            account = self._accounts[account_id]
            updated = replace(
                account,
                reserved_amount=_money(max(Decimal("0"), account.reserved_amount - release)),
                settled_amount=_money(account.settled_amount + reservation.consumed_amount),
                released_amount=_money(account.released_amount + release),
                updated_at=utc_timestamp(),
            )
            self._accounts[account_id] = _hash_account(_recalculate_account(updated))
            self._audit_ledger("settlement", reservation_id, "", account_id, reservation.consumed_amount, "Reservation settled; unused funds released.")
        return settled

    def release_reservation(self, reservation_id: str, *, reason: str = "Unused reservation released.") -> CostReservation:
        reservation = self._reservations[reservation_id]
        release = max(Decimal("0"), reservation.approved_amount - reservation.consumed_amount - reservation.released_amount)
        released = replace(reservation, state=ReservationState.RELEASED, released_amount=_money(reservation.released_amount + release), released_at=utc_timestamp())
        released = _hash_reservation(released)
        self._reservations[reservation_id] = released
        for account_id in reservation.budget_account_ids:
            account = self._accounts[account_id]
            updated = replace(account, reserved_amount=_money(max(Decimal("0"), account.reserved_amount - release)), released_amount=_money(account.released_amount + release), updated_at=utc_timestamp())
            self._accounts[account_id] = _hash_account(_recalculate_account(updated))
            self._audit_ledger("release", reservation_id, "", account_id, release, reason)
        return released

    def recover_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._policy_versions = tuple(_policy_from_dict(item) for item in snapshot.get("policyVersions", ())) or self._policy_versions
        self._policy_versions = list(self._policy_versions)
        self._accounts = {item["budget_account_id"]: _account_from_dict(item) for item in snapshot.get("budgetAccounts", ())}
        self._reservations = {item["reservation_id"]: _reservation_from_dict(item) for item in snapshot.get("missionReservations", ())}
        self._usage = {item["idempotency_key"]: _usage_from_dict(item) for item in snapshot.get("usageRecords", ())}
        self._ledger = [_ledger_from_dict(item) for item in snapshot.get("costLedger", ())]
        self._circuit_breakers = [CircuitBreakerRecord(**item) for item in snapshot.get("circuitBreakers", ())]

    def _reservation_from_request(self, request: CostReservationRequest, decision: CostAuthorizationDecision, state: ReservationState, amount: Decimal, reason: str, *, approved_api_calls: int | None = None, reserve: bool = False) -> CostReservation:
        account = self._reserve_account_for(request.budget_category) if reserve else self._account_for(request.budget_category)
        account_ids = (account.budget_account_id,) if account and amount >= Decimal("0") else ()
        reservation = CostReservation(
            reservation_id=f"ECG-RES-{len(self._reservations) + 1:06d}",
            reservation_request_id=request.reservation_request_id,
            state=state,
            decision=decision,
            budget_account_ids=account_ids,
            mission_plan_id=request.mission_plan_id,
            mission_plan_version=request.mission_plan_version,
            mission_id=request.mission_id,
            workflow_id=request.workflow_id,
            office_id=request.requesting_office_id,
            budget_category=request.budget_category,
            requested_amount=request.requested_reservation_amount,
            approved_amount=_money(amount),
            consumed_amount=Decimal("0"),
            released_amount=Decimal("0"),
            approved_api_calls=approved_api_calls if approved_api_calls is not None else request.requested_api_calls,
            consumed_api_calls=0,
            approved_input_tokens=request.requested_input_tokens,
            consumed_input_tokens=0,
            approved_output_tokens=request.requested_output_tokens,
            consumed_output_tokens=0,
            allowed_models=request.requested_models or self.policy.allowed_models,
            allowed_providers=request.requested_providers or self.policy.allowed_providers,
            allowed_data_sources=request.requested_data_sources,
            approved_runtime_seconds=request.estimated_runtime_seconds,
            consumed_runtime_seconds=0,
            safety_reserve_used=reserve,
            override_id="",
            approval_reason=reason,
            restriction_reason="" if state in {ReservationState.APPROVED, ReservationState.REDUCED} else reason,
            approved_at=utc_timestamp() if state in {ReservationState.APPROVED, ReservationState.REDUCED} else "",
            activated_at="",
            expires_at=(_now_dt() + timedelta(hours=4)).isoformat().replace("+00:00", "Z"),
            released_at="",
            settled_at="",
            content_hash="",
        )
        reservation = _hash_reservation(reservation)
        self._reservations[reservation.reservation_id] = reservation
        if account and amount > Decimal("0") and state in {ReservationState.APPROVED, ReservationState.REDUCED}:
            updated = replace(account, reserved_amount=_money(account.reserved_amount + amount), updated_at=utc_timestamp())
            self._accounts[account.budget_account_id] = _hash_account(_recalculate_account(updated))
            self._audit_ledger("reservation", reservation.reservation_id, "", account.budget_account_id, amount, reason)
        return reservation

    def _authorize(self, request: CostAuthorizationRequest, reservation: CostReservation) -> tuple[bool, str, str, CostAuthorizationDecision]:
        if reservation.state not in {ReservationState.ACTIVE, ReservationState.APPROVED, ReservationState.REDUCED, ReservationState.PARTIALLY_CONSUMED}:
            return False, "COST_GOVERNOR_RESERVATION_INACTIVE", "Reservation is not active.", CostAuthorizationDecision.REJECT
        if request.provider in self.policy.prohibited_providers or (self.policy.allowed_providers and request.provider not in self.policy.allowed_providers):
            return False, "COST_GOVERNOR_PROVIDER_BLOCKED", "Provider is not allowed by policy.", CostAuthorizationDecision.REJECT
        if request.model in self.policy.prohibited_models or (self.policy.allowed_models and request.model not in reservation.allowed_models and request.model not in {"deterministic", ""}):
            return False, "COST_GOVERNOR_MODEL_BLOCKED", "Model is not allowed by reservation.", CostAuthorizationDecision.REJECT
        if reservation.consumed_api_calls + 1 > reservation.approved_api_calls:
            return False, "COST_GOVERNOR_API_CALL_LIMIT", "Reservation API-call ceiling would be exceeded.", CostAuthorizationDecision.REJECT
        if reservation.approved_input_tokens is not None and reservation.consumed_input_tokens + request.input_tokens > reservation.approved_input_tokens:
            return False, "COST_GOVERNOR_INPUT_TOKEN_LIMIT", "Input token ceiling would be exceeded.", CostAuthorizationDecision.REJECT
        if reservation.approved_output_tokens is not None and reservation.consumed_output_tokens + request.output_tokens > reservation.approved_output_tokens:
            return False, "COST_GOVERNOR_OUTPUT_TOKEN_LIMIT", "Output token ceiling would be exceeded.", CostAuthorizationDecision.REJECT
        if reservation.consumed_amount + request.estimated_cost > reservation.approved_amount:
            return False, "COST_GOVERNOR_RESERVATION_EXCEEDED", "Requested call would exceed reservation amount.", CostAuthorizationDecision.REJECT
        if any(item.current_state == "blocked" and not reservation.safety_reserve_used for item in self._circuit_breakers):
            return False, "COST_GOVERNOR_CIRCUIT_BREAKER", "Circuit breaker blocks discretionary spending.", CostAuthorizationDecision.REJECT
        return True, "", "Cost Governor authorized bounded gateway call.", CostAuthorizationDecision.APPROVE

    def _authorization_record(self, request: CostAuthorizationRequest | None, reservation_id: str, mission_id: str, workflow_id: str, office: str, provider: str, model: str, estimated_cost: Decimal, allowed: bool, decision: CostAuthorizationDecision, reason: str) -> CostAuthorizationRecord:
        auth_request = request or CostAuthorizationRequest(f"ECG-AUTH-REQ-{len(self._authorizations) + 1:06d}", reservation_id, mission_id, workflow_id, office, provider, model, CostType.API_REQUEST, estimated_cost, 0, 0, 0, "", f"ECG-AUTH-{len(self._authorizations) + 1:06d}", utc_timestamp())
        record = CostAuthorizationRecord(
            authorization_id=f"ECG-AUTH-{len(self._authorizations) + 1:06d}",
            request=auth_request,
            allowed=allowed,
            decision=decision,
            reason=reason,
            reservation_state=self._reservations[reservation_id].state if reservation_id in self._reservations else ReservationState.REJECTED,
            created_at=utc_timestamp(),
            content_hash="",
        )
        record = replace(record, content_hash=sha256(json.dumps(_snapshot_dataclass(record) | {"content_hash": ""}, sort_keys=True, default=str).encode("utf-8")).hexdigest())
        self._authorizations.append(record)
        return record

    def _apply_incurred(self, account_ids: tuple[str, ...], amount: Decimal, usage_id: str) -> None:
        for account_id in account_ids:
            account = self._accounts[account_id]
            updated = replace(account, incurred_amount=_money(account.incurred_amount + amount), committed_amount=_money(account.committed_amount + amount), updated_at=utc_timestamp())
            self._accounts[account_id] = _hash_account(_recalculate_account(updated))
            self._audit_ledger("usage", "", usage_id, account_id, amount, "Usage incurred through API Execution Gateway.")

    def _check_thresholds(self) -> None:
        for account in self._accounts.values():
            if account.allocated_amount <= 0:
                continue
            used = account.incurred_amount + account.reserved_amount
            ratio = used / account.allocated_amount
            if ratio >= self.policy.hard_stop_threshold_percent:
                self._circuit_breakers.append(CircuitBreakerRecord(f"ECG-CB-{len(self._circuit_breakers) + 1:06d}", account.scope_id, "CRITICAL", "blocked", _money(ratio), self.policy.hard_stop_threshold_percent, "new discretionary reservations", "safety cleanup and protected reserves", utc_timestamp(), ""))
            elif ratio >= self.policy.warning_threshold_percent:
                self._alerts.append({"alertType": "budget_threshold", "scope": account.scope_id, "severity": "WARNING", "triggerValue": float(ratio), "threshold": float(self.policy.warning_threshold_percent), "timestamp": utc_timestamp()})

    def _account_for(self, category: BudgetCategory) -> BudgetAccount | None:
        for account in self._accounts.values():
            if account.category == category and account.scope != BudgetScope.RESERVE:
                return account
        return self._accounts.get("ENTERPRISE-DAILY")

    def _reserve_account_for(self, category: BudgetCategory) -> BudgetAccount | None:
        for account in self._accounts.values():
            if account.category == category and account.scope == BudgetScope.RESERVE:
                return account
        return None

    def _forecast(self) -> dict[str, Any]:
        today = sum((account.incurred_amount for account in self._accounts.values() if account.period_type == BudgetPeriodType.DAILY), Decimal("0"))
        utilization = today / self.policy.daily_limit if self.policy.daily_limit else Decimal("1")
        return {
            "endOfDayForecast": float(_money(today)),
            "endOfWeekForecast": float(_money(today * Decimal("5"))),
            "endOfMonthForecast": float(_money(today * Decimal("21"))),
            "estimatedExhaustionTime": "not_forecast" if utilization < Decimal("0.75") else "within_current_period",
            "remainingMissionCapacity": int(max(0, (self.policy.daily_limit - today) / Decimal("0.01"))) if self.policy.daily_limit > today else 0,
            "forecastConfidence": 0.72,
            "assumptions": ("linear intraday spend", "known reservations only", "safety reserves excluded from discretionary forecast"),
        }

    def _metrics(self) -> dict[str, Any]:
        usage = tuple(self._usage.values())
        reservations = tuple(self._reservations.values())
        spend_today = sum((item.actual_cost for item in usage), Decimal("0"))
        reserve_accounts = tuple(account for account in self._accounts.values() if account.scope == BudgetScope.RESERVE)
        reserve_allocated = sum((account.allocated_amount for account in reserve_accounts), Decimal("0"))
        reserve_available = sum((account.available_amount for account in reserve_accounts), Decimal("0"))
        return {
            "spendToday": float(_money(spend_today)),
            "spendThisWeek": float(_money(spend_today)),
            "spendThisMonth": float(_money(spend_today)),
            "budgetUtilization": float(_money(spend_today / self.policy.daily_limit if self.policy.daily_limit else Decimal("0"))),
            "protectedReserveUtilization": float(_money((reserve_allocated - reserve_available) / reserve_allocated if reserve_allocated else Decimal("0"))),
            "activeReservations": sum(1 for item in reservations if item.state in {ReservationState.APPROVED, ReservationState.REDUCED, ReservationState.ACTIVE, ReservationState.PARTIALLY_CONSUMED}),
            "unsettledAmount": float(_money(sum((item.actual_cost for item in usage if not item.settled), Decimal("0")))),
            "costPerMission": _cost_by(usage, lambda item: item.mission_id or "unassigned"),
            "costPerWorkflow": _cost_by(usage, lambda item: item.workflow_id or "unassigned"),
            "costPerOffice": _cost_by(usage, lambda item: item.office_id or "unassigned"),
            "costPerModel": _cost_by(usage, lambda item: item.model or "none"),
            "costPerProvider": _cost_by(usage, lambda item: item.provider or "none"),
            "rejectedReservationCount": sum(1 for item in reservations if item.state == ReservationState.REJECTED),
            "deferredReservationCount": sum(1 for item in reservations if item.state == ReservationState.DEFERRED),
            "reservationReductionRate": round(sum(1 for item in reservations if item.state == ReservationState.REDUCED) / max(1, len(reservations)), 4),
            "duplicateCallPrevention": sum(1 for item in self._alerts if item.get("alertType") == "duplicate_usage_report"),
            "safetyReserveRemaining": float(_money(reserve_available)),
            "safetyMissionsFunded": sum(1 for item in reservations if item.safety_reserve_used),
            "safetyMissionsBlocked": sum(1 for item in reservations if _is_safety_category(item.budget_category) and item.state == ReservationState.REJECTED),
        }

    def _audit_ledger(self, entry_type: str, reservation_id: str, usage_id: str, account_id: str, amount: Decimal, reason: str) -> None:
        entry = CostLedgerEntry(f"ECG-LED-{len(self._ledger) + 1:06d}", entry_type, reservation_id, usage_id, account_id, _money(amount), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), utc_timestamp(), reason, "")
        entry = replace(entry, content_hash=sha256(json.dumps(_snapshot_dataclass(entry) | {"content_hash": ""}, sort_keys=True, default=str).encode("utf-8")).hexdigest())
        self._ledger.append(entry)


def _default_policy() -> EnterpriseBudgetPolicy:
    allocations = {
        BudgetCategory.TACTICAL_OPERATIONS: Decimal("5.00"),
        BudgetCategory.OPPORTUNITY_DISCOVERY: Decimal("3.00"),
        BudgetCategory.STRATEGIC_RESEARCH: Decimal("4.00"),
        BudgetCategory.ENTERPRISE_OVERHEAD: Decimal("2.00"),
        BudgetCategory.COMMANDER_RESERVE: Decimal("2.00"),
        BudgetCategory.POSITION_SAFETY: Decimal("4.00"),
        BudgetCategory.BROKER_RECONCILIATION: Decimal("2.00"),
        BudgetCategory.LEDGER_INTEGRITY: Decimal("2.00"),
        BudgetCategory.RISK_CONTROL: Decimal("3.00"),
        BudgetCategory.EMERGENCY_RECOVERY: Decimal("3.00"),
    }
    reserves = {
        BudgetCategory.POSITION_SAFETY: Decimal("2.00"),
        BudgetCategory.BROKER_RECONCILIATION: Decimal("1.00"),
        BudgetCategory.LEDGER_INTEGRITY: Decimal("1.00"),
        BudgetCategory.RISK_CONTROL: Decimal("1.50"),
        BudgetCategory.EMERGENCY_RECOVERY: Decimal("1.50"),
        BudgetCategory.COMMANDER_RESERVE: Decimal("1.00"),
    }
    return EnterpriseBudgetPolicy(
        "ECG-POLICY-001",
        1,
        "Default Enterprise Cost Policy",
        "Bounded paper-mode computational-capital policy.",
        BudgetState.ACTIVE,
        "USD",
        Decimal("25.00"),
        Decimal("100.00"),
        Decimal("250.00"),
        Decimal("0.50"),
        Decimal("0.75"),
        Decimal("1.00"),
        allocations,
        reserves,
        {"Analyst": Decimal("5.00"), "Risk": Decimal("5.00"), "Trader": Decimal("5.00"), "Executive": Decimal("5.00")},
        {"position_safety_review": Decimal("2.00"), "opportunity_scan": Decimal("1.00"), "strategic_research": Decimal("2.00")},
        {"gpt-4.1-mini": Decimal("5.00"), "deterministic": Decimal("0.00"), "dry-run-model": Decimal("0.00")},
        {"openai": Decimal("10.00"), "none": Decimal("0.00")},
        {},
        ("deterministic", "dry-run-model", "gpt-4.1-mini"),
        ("gpt-5-thinking-unbounded",),
        ("none", "openai"),
        ("unknown-paid-provider",),
        5,
        5,
        20000,
        20000,
        Decimal("5.00"),
        Decimal("5.00"),
        utc_timestamp(),
        "",
        "System",
        utc_timestamp(),
        "Initial EO-CE policy.",
        "",
    )


def _default_accounts(policy: EnterpriseBudgetPolicy) -> dict[str, BudgetAccount]:
    start = utc_timestamp()
    end = (_now_dt() + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    accounts = {
        "ENTERPRISE-DAILY": _hash_account(_account("ENTERPRISE-DAILY", BudgetScope.ENTERPRISE, "enterprise", BudgetCategory.ENTERPRISE_OVERHEAD, BudgetPeriodType.DAILY, policy.daily_limit, Decimal("0"), start, end, policy)),
    }
    for category, amount in policy.category_allocations.items():
        account_id = f"CAT-{category.value.upper()}"
        accounts[account_id] = _hash_account(_account(account_id, BudgetScope.PERIOD, category.value, category, BudgetPeriodType.DAILY, amount, Decimal("0"), start, end, policy))
    for category, amount in policy.protected_reserve_allocations.items():
        account_id = f"RES-{category.value.upper()}"
        accounts[account_id] = _hash_account(_account(account_id, BudgetScope.RESERVE, category.value, category, BudgetPeriodType.DAILY, amount, amount, start, end, policy))
    return accounts


def _account(account_id: str, scope: BudgetScope, scope_id: str, category: BudgetCategory, period: BudgetPeriodType, allocated: Decimal, protected: Decimal, start: str, end: str, policy: EnterpriseBudgetPolicy) -> BudgetAccount:
    account = BudgetAccount(account_id, scope, scope_id, category, period, start, end, "USD", _money(allocated), _money(protected), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), _money(allocated), _money(allocated * policy.warning_threshold_percent), _money(allocated * policy.restriction_threshold_percent), _money(allocated * policy.hard_stop_threshold_percent), BudgetState.ACTIVE, policy.policy_id, policy.version, utc_timestamp(), "")
    return _recalculate_account(account)


def _recalculate_account(account: BudgetAccount) -> BudgetAccount:
    available = _money(max(Decimal("0"), account.allocated_amount - account.reserved_amount - account.incurred_amount + account.released_amount))
    used = account.reserved_amount + account.incurred_amount
    state = BudgetState.ACTIVE
    if used >= account.hard_limit and account.hard_limit > 0:
        state = BudgetState.EXHAUSTED
    elif used >= account.restriction_threshold and account.restriction_threshold > 0:
        state = BudgetState.RESTRICTED
    elif used >= account.warning_threshold and account.warning_threshold > 0:
        state = BudgetState.WARNING
    return replace(account, available_amount=available, state=state)


def _hash_policy(policy: EnterpriseBudgetPolicy) -> EnterpriseBudgetPolicy:
    return replace(policy, content_hash=sha256(json.dumps(_snapshot_dataclass(replace(policy, content_hash="")), sort_keys=True, default=str).encode("utf-8")).hexdigest())


def _hash_account(account: BudgetAccount) -> BudgetAccount:
    return replace(account, content_hash=sha256(json.dumps(_snapshot_dataclass(replace(account, content_hash="")), sort_keys=True, default=str).encode("utf-8")).hexdigest())


def _hash_reservation(reservation: CostReservation) -> CostReservation:
    return replace(reservation, content_hash=sha256(json.dumps(_snapshot_dataclass(replace(reservation, content_hash="")), sort_keys=True, default=str).encode("utf-8")).hexdigest())


def _hash_usage(usage: CostUsageRecord) -> CostUsageRecord:
    return replace(usage, content_hash=sha256(json.dumps(_snapshot_dataclass(replace(usage, content_hash="")), sort_keys=True, default=str).encode("utf-8")).hexdigest())


def _reservation_request_from_dict(item: dict[str, Any]) -> CostReservationRequest:
    data = dict(item)
    data["budget_category"] = BudgetCategory(data.get("budget_category", BudgetCategory.TACTICAL_OPERATIONS.value))
    for key in ("estimated_minimum_cost", "estimated_expected_cost", "estimated_maximum_cost", "requested_reservation_amount"):
        data[key] = _money(data.get(key, 0))
    for key in ("requested_models", "requested_providers", "requested_data_sources"):
        data[key] = tuple(data.get(key, ()) or ())
    return CostReservationRequest(**{key: data.get(key) for key in CostReservationRequest.__dataclass_fields__})


def _missing_attribution(request: CostReservationRequest) -> tuple[str, ...]:
    missing = []
    for field in ("mission_plan_id", "mission_type", "priority_class", "requested_by"):
        if not getattr(request, field):
            missing.append(field)
    return tuple(missing)


def _category_for(mission_type: str, priority_class: str) -> BudgetCategory:
    text = f"{mission_type} {priority_class}".lower()
    if "position" in text:
        return BudgetCategory.POSITION_SAFETY
    if "broker" in text or "order" in text:
        return BudgetCategory.BROKER_RECONCILIATION
    if "ledger" in text or "reconciliation" in text:
        return BudgetCategory.LEDGER_INTEGRITY
    if "risk" in text:
        return BudgetCategory.RISK_CONTROL
    if "recovery" in text or "emergency" in text:
        return BudgetCategory.EMERGENCY_RECOVERY
    if "strategic" in text:
        return BudgetCategory.STRATEGIC_RESEARCH
    if "opportunity" in text or "discovery" in text:
        return BudgetCategory.OPPORTUNITY_DISCOVERY
    if "capability" in text or "academy" in text:
        return BudgetCategory.CAPABILITY_DEVELOPMENT
    return BudgetCategory.TACTICAL_OPERATIONS


def _is_safety_category(category: BudgetCategory) -> bool:
    return category in {BudgetCategory.POSITION_SAFETY, BudgetCategory.BROKER_RECONCILIATION, BudgetCategory.LEDGER_INTEGRITY, BudgetCategory.RISK_CONTROL, BudgetCategory.REQUIRED_LIFECYCLE, BudgetCategory.EMERGENCY_RECOVERY}


def _budget_allocation(accounts: tuple[BudgetAccount, ...]) -> dict[str, Any]:
    return {
        "allocated": float(_money(sum((item.allocated_amount for item in accounts), Decimal("0")))),
        "reserved": float(_money(sum((item.reserved_amount for item in accounts), Decimal("0")))),
        "incurred": float(_money(sum((item.incurred_amount for item in accounts), Decimal("0")))),
        "settled": float(_money(sum((item.settled_amount for item in accounts), Decimal("0")))),
        "released": float(_money(sum((item.released_amount for item in accounts), Decimal("0")))),
        "available": float(_money(sum((item.available_amount for item in accounts), Decimal("0")))),
    }


def _office_cost_table(usage: tuple[CostUsageRecord, ...], policy: EnterpriseBudgetPolicy) -> tuple[dict[str, Any], ...]:
    offices = sorted(set(policy.office_limits) | {item.office_id for item in usage if item.office_id})
    rows = []
    for office in offices:
        items = tuple(item for item in usage if item.office_id == office)
        rows.append({"office": office, "costToday": float(_money(sum((item.actual_cost for item in items), Decimal("0")))), "apiCalls": sum(item.api_calls for item in items), "tokens": sum(item.input_tokens + item.output_tokens for item in items), "ceiling": float(policy.office_limits.get(office, Decimal("0"))), "state": "active"})
    return tuple(rows)


def _provider_model_usage(usage: tuple[CostUsageRecord, ...]) -> tuple[dict[str, Any], ...]:
    grouped: dict[tuple[str, str], list[CostUsageRecord]] = {}
    for item in usage:
        grouped.setdefault((item.provider, item.model), []).append(item)
    return tuple({"provider": provider, "model": model, "calls": sum(item.api_calls for item in items), "inputTokens": sum(item.input_tokens for item in items), "outputTokens": sum(item.output_tokens for item in items), "calculatedCost": float(_money(sum((item.actual_cost for item in items), Decimal("0")))), "providerReportedCost": float(_money(sum((item.provider_reported_cost for item in items), Decimal("0")))), "variance": float(_money(sum((item.variance for item in items), Decimal("0"))))} for (provider, model), items in sorted(grouped.items()))


def _cost_by(usage: tuple[CostUsageRecord, ...], key_fn: Any) -> dict[str, float]:
    out: dict[str, Decimal] = {}
    for item in usage:
        key = str(key_fn(item))
        out[key] = out.get(key, Decimal("0")) + item.actual_cost
    return {key: float(_money(value)) for key, value in out.items()}


def _money(value: Any) -> Decimal:
    try:
        return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.0000")


def _now_dt() -> datetime:
    return datetime.now(UTC)


def _snapshot_dataclass(item: Any) -> dict[str, Any]:
    return _json_safe(asdict(item))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, tuple):
        return tuple(_json_safe(item) for item in value)
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(_json_safe(key)): _json_safe(item) for key, item in value.items()}
    return value


def _policy_from_dict(item: dict[str, Any]) -> EnterpriseBudgetPolicy:
    data = dict(item)
    data["state"] = BudgetState(data["state"])
    for key in ("daily_limit", "weekly_limit", "monthly_limit", "warning_threshold_percent", "restriction_threshold_percent", "hard_stop_threshold_percent", "emergency_override_limit", "commander_override_limit"):
        data[key] = _money(data.get(key, 0))
    for key in ("category_allocations", "protected_reserve_allocations"):
        data[key] = {BudgetCategory(k): _money(v) for k, v in data.get(key, {}).items()}
    for key in ("office_limits", "mission_type_limits", "model_limits", "provider_limits", "data_source_limits"):
        data[key] = {str(k): _money(v) for k, v in data.get(key, {}).items()}
    for key in ("allowed_models", "prohibited_models", "allowed_providers", "prohibited_providers"):
        data[key] = tuple(data.get(key, ()) or ())
    return EnterpriseBudgetPolicy(**{key: data.get(key) for key in EnterpriseBudgetPolicy.__dataclass_fields__})


def _account_from_dict(item: dict[str, Any]) -> BudgetAccount:
    data = dict(item)
    data["scope"] = BudgetScope(data["scope"])
    data["category"] = BudgetCategory(data["category"])
    data["period_type"] = BudgetPeriodType(data["period_type"])
    data["state"] = BudgetState(data["state"])
    for key in ("allocated_amount", "protected_amount", "reserved_amount", "committed_amount", "incurred_amount", "settled_amount", "released_amount", "available_amount", "warning_threshold", "restriction_threshold", "hard_limit"):
        data[key] = _money(data.get(key, 0))
    return BudgetAccount(**{key: data.get(key) for key in BudgetAccount.__dataclass_fields__})


def _reservation_from_dict(item: dict[str, Any]) -> CostReservation:
    data = dict(item)
    data["state"] = ReservationState(data["state"])
    data["decision"] = CostAuthorizationDecision(data["decision"])
    data["budget_category"] = BudgetCategory(data["budget_category"])
    for key in ("budget_account_ids", "allowed_models", "allowed_providers", "allowed_data_sources"):
        data[key] = tuple(data.get(key, ()) or ())
    for key in ("requested_amount", "approved_amount", "consumed_amount", "released_amount"):
        data[key] = _money(data.get(key, 0))
    return CostReservation(**{key: data.get(key) for key in CostReservation.__dataclass_fields__})


def _usage_from_dict(item: dict[str, Any]) -> CostUsageRecord:
    data = dict(item)
    data["cost_type"] = CostType(data["cost_type"])
    for key in ("estimated_cost", "actual_cost", "provider_reported_cost", "variance"):
        data[key] = _money(data.get(key, 0))
    return CostUsageRecord(**{key: data.get(key) for key in CostUsageRecord.__dataclass_fields__})


def _ledger_from_dict(item: dict[str, Any]) -> CostLedgerEntry:
    data = dict(item)
    for key in ("amount", "estimated", "reserved", "incurred", "settled", "released"):
        data[key] = _money(data.get(key, 0))
    return CostLedgerEntry(**{key: data.get(key) for key in CostLedgerEntry.__dataclass_fields__})
