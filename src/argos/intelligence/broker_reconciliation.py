"""MO-TR-010 broker, order, execution, position, and account reconciliation."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from decimal import Decimal
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_010_VERSION = "MO-TR-010/1.0.0"


class OrderLifecycleState(str, Enum):
    INTENT_CREATED = "INTENT_CREATED"
    INTERNALLY_AUTHORIZED = "INTERNALLY_AUTHORIZED"
    SUBMISSION_PENDING = "SUBMISSION_PENDING"
    SUBMISSION_ATTEMPTED = "SUBMISSION_ATTEMPTED"
    SUBMISSION_FAILED = "SUBMISSION_FAILED"
    TRANSMITTED = "TRANSMITTED"
    BROKER_RECEIVED = "BROKER_RECEIVED"
    BROKER_PENDING = "BROKER_PENDING"
    BROKER_ACCEPTED = "BROKER_ACCEPTED"
    BROKER_REJECTED = "BROKER_REJECTED"
    BROKER_HELD = "BROKER_HELD"
    BROKER_ROUTED = "BROKER_ROUTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCEL_PENDING = "CANCEL_PENDING"
    CANCELLED = "CANCELLED"
    CANCEL_REJECTED = "CANCEL_REJECTED"
    REPLACE_REQUESTED = "REPLACE_REQUESTED"
    REPLACE_PENDING = "REPLACE_PENDING"
    REPLACED = "REPLACED"
    REPLACE_REJECTED = "REPLACE_REJECTED"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    STOPPED = "STOPPED"
    TRIGGERED = "TRIGGERED"
    CORRECTED = "CORRECTED"
    BUSTED = "BUSTED"
    UNKNOWN_ORDER_STATE = "UNKNOWN_ORDER_STATE"


class ExecutionState(str, Enum):
    NO_EXECUTION = "NO_EXECUTION"
    EXECUTION_PENDING = "EXECUTION_PENDING"
    PARTIAL_EXECUTION = "PARTIAL_EXECUTION"
    COMPLETE_EXECUTION = "COMPLETE_EXECUTION"
    EXECUTION_CORRECTED = "EXECUTION_CORRECTED"
    EXECUTION_BUSTED = "EXECUTION_BUSTED"
    EXECUTION_REVERSED = "EXECUTION_REVERSED"
    EXECUTION_UNCONFIRMED = "EXECUTION_UNCONFIRMED"
    EXECUTION_CONFLICTED = "EXECUTION_CONFLICTED"
    UNKNOWN_EXECUTION_STATE = "UNKNOWN_EXECUTION_STATE"


class SettlementState(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNSETTLED = "UNSETTLED"
    PARTIALLY_SETTLED = "PARTIALLY_SETTLED"
    SETTLED = "SETTLED"
    SETTLEMENT_DELAYED = "SETTLEMENT_DELAYED"
    SETTLEMENT_FAILED = "SETTLEMENT_FAILED"
    SETTLEMENT_ADJUSTED = "SETTLEMENT_ADJUSTED"
    UNKNOWN_SETTLEMENT_STATE = "UNKNOWN_SETTLEMENT_STATE"


class BrokerReconciliationDisposition(str, Enum):
    MATCHED = "MATCHED"
    MATCHED_WITH_ALLOWED_DELAY = "MATCHED_WITH_ALLOWED_DELAY"
    MATCHED_AFTER_REFRESH = "MATCHED_AFTER_REFRESH"
    MATCHED_AFTER_CORRECTION = "MATCHED_AFTER_CORRECTION"
    EXPECTED_TRANSITION_PENDING = "EXPECTED_TRANSITION_PENDING"
    INTERNAL_RECORD_MISSING = "INTERNAL_RECORD_MISSING"
    BROKER_RECORD_MISSING = "BROKER_RECORD_MISSING"
    STATUS_MISMATCH = "STATUS_MISMATCH"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    PRICE_MISMATCH = "PRICE_MISMATCH"
    FEE_MISMATCH = "FEE_MISMATCH"
    POSITION_MISMATCH = "POSITION_MISMATCH"
    CASH_MISMATCH = "CASH_MISMATCH"
    BUYING_POWER_MISMATCH = "BUYING_POWER_MISMATCH"
    MARGIN_MISMATCH = "MARGIN_MISMATCH"
    SETTLEMENT_MISMATCH = "SETTLEMENT_MISMATCH"
    CORPORATE_ACTION_MISMATCH = "CORPORATE_ACTION_MISMATCH"
    ASSIGNMENT_MISMATCH = "ASSIGNMENT_MISMATCH"
    EXERCISE_MISMATCH = "EXERCISE_MISMATCH"
    UNEXPECTED_BROKER_ACTIVITY = "UNEXPECTED_BROKER_ACTIVITY"
    DUPLICATE_BROKER_EVENT = "DUPLICATE_BROKER_EVENT"
    OUT_OF_ORDER_EVENT = "OUT_OF_ORDER_EVENT"
    STALE_BROKER_STATE = "STALE_BROKER_STATE"
    BROKER_SOURCE_UNAVAILABLE = "BROKER_SOURCE_UNAVAILABLE"
    INTERNAL_STATE_CORRUPTION = "INTERNAL_STATE_CORRUPTION"
    BROKER_STATE_CONFLICT = "BROKER_STATE_CONFLICT"
    UNRESOLVED_RECONCILIATION = "UNRESOLVED_RECONCILIATION"
    UNKNOWN_RECONCILIATION_STATE = "UNKNOWN_RECONCILIATION_STATE"


class TradeRestrictionState(str, Enum):
    NO_TRADE_RESTRICTION = "NO_TRADE_RESTRICTION"
    REFRESH_REQUIRED = "REFRESH_REQUIRED"
    AFFECTED_ORDER_BLOCKED = "AFFECTED_ORDER_BLOCKED"
    AFFECTED_INSTRUMENT_NEW_ORDERS_BLOCKED = "AFFECTED_INSTRUMENT_NEW_ORDERS_BLOCKED"
    AFFECTED_INSTRUMENT_POSITION_INCREASE_BLOCKED = "AFFECTED_INSTRUMENT_POSITION_INCREASE_BLOCKED"
    AFFECTED_ACCOUNT_NEW_ORDERS_BLOCKED = "AFFECTED_ACCOUNT_NEW_ORDERS_BLOCKED"
    CLOSING_ORDERS_ONLY = "CLOSING_ORDERS_ONLY"
    ALL_NEW_TRADING_BLOCKED = "ALL_NEW_TRADING_BLOCKED"
    ALL_TRADING_BLOCKED = "ALL_TRADING_BLOCKED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    UNKNOWN_TRADE_RESTRICTION = "UNKNOWN_TRADE_RESTRICTION"


class SnapshotSourceType(str, Enum):
    BROKER_REPORTED = "BROKER_REPORTED"
    INTERNAL_EXPECTED = "INTERNAL_EXPECTED"
    RECONCILED_CERTIFIED = "RECONCILED_CERTIFIED"


@dataclass(frozen=True)
class OrderIntentRecord:
    order_intent_id: str
    workflow_id: str
    decision_object_id: str
    risk_authorization_id: str
    account_id: str
    strategy_id: str
    instrument_id: str
    side: str
    position_effect: str
    order_type: str
    time_in_force: str
    requested_quantity: Decimal
    limit_price: Decimal | None
    currency: str
    client_order_id: str
    idempotency_key: str
    authorized_at: str
    workflow_execution_token_id: str
    intent_status: OrderLifecycleState
    created_at: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class BrokerOrderRecord:
    broker_order_record_id: str
    broker_id: str
    broker_account_id: str
    broker_order_id: str
    client_order_id: str
    order_intent_id: str
    instrument_id: str
    side: str
    original_quantity: Decimal
    remaining_quantity: Decimal
    filled_quantity: Decimal
    average_fill_price: Decimal | None
    broker_status: OrderLifecycleState
    broker_status_reason: str
    broker_received_at: str
    last_updated_at: str
    raw_broker_evidence: str
    broker_event_sequence: int
    recorded_at: str


@dataclass(frozen=True)
class ExecutionRecord:
    execution_record_id: str
    broker_execution_id: str
    broker_order_id: str
    order_intent_id: str
    account_id: str
    instrument_id: str
    execution_quantity: Decimal
    execution_price: Decimal
    currency: str
    execution_timestamp: str
    commission: Decimal
    regulatory_fees: Decimal
    exchange_fees: Decimal
    other_fees: Decimal
    execution_status: ExecutionState
    raw_evidence_reference: str
    created_at: str


@dataclass(frozen=True)
class PositionSnapshot:
    position_snapshot_id: str
    source_type: SnapshotSourceType
    broker_id: str
    account_id: str
    instrument_id: str
    snapshot_timestamp: str
    broker_position_quantity: Decimal
    settled_quantity: Decimal
    unsettled_quantity: Decimal
    average_cost: Decimal | None
    currency: str
    raw_evidence_reference: str
    recorded_at: str


@dataclass(frozen=True)
class TradeRestrictionRecord:
    restriction_id: str
    scope: TradeRestrictionState
    affected_account_id: str
    affected_instrument_ids: tuple[str, ...]
    affected_order_ids: tuple[str, ...]
    effective_timestamp: str
    reason_code: str
    source_reconciliation_ids: tuple[str, ...]
    issuing_office: str
    authority_token: str
    expiration_rule: str
    release_conditions: tuple[str, ...]
    status: str
    audit_record_id: str


@dataclass(frozen=True)
class BrokerReconciliationRecord:
    reconciliation_id: str
    workflow_id: str
    order_intent_id: str
    broker_order_id: str
    execution_ids: tuple[str, ...]
    internal_state: OrderLifecycleState
    broker_state: OrderLifecycleState
    execution_state: ExecutionState
    settlement_state: SettlementState
    disposition: BrokerReconciliationDisposition
    trade_restriction: TradeRestrictionRecord
    source_record_hashes: tuple[str, ...]
    required_action: str
    doctrine_version: str
    created_at: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class BrokerReconciliationLedger:
    def __init__(self) -> None:
        self._records: dict[str, BrokerReconciliationRecord] = {}

    def append(self, record: BrokerReconciliationRecord) -> None:
        if record.reconciliation_id in self._records:
            raise ValueError("broker reconciliations are append-only")
        self._records[record.reconciliation_id] = record

    def all_records(self) -> tuple[BrokerReconciliationRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))


class BrokerReconciliationEngine:
    def __init__(self, ledger: BrokerReconciliationLedger | None = None) -> None:
        self.ledger = ledger or BrokerReconciliationLedger()

    def reconcile_order(self, intent: OrderIntentRecord | None, broker_order: BrokerOrderRecord | None, executions: tuple[ExecutionRecord, ...] = ()) -> BrokerReconciliationRecord:
        if intent is None and broker_order is None:
            return self._record(None, None, (), OrderLifecycleState.UNKNOWN_ORDER_STATE, OrderLifecycleState.UNKNOWN_ORDER_STATE, ExecutionState.UNKNOWN_EXECUTION_STATE, BrokerReconciliationDisposition.UNKNOWN_RECONCILIATION_STATE, TradeRestrictionState.ALL_NEW_TRADING_BLOCKED, "missing_internal_and_broker_records")
        if intent is None:
            return self._record(None, broker_order, executions, OrderLifecycleState.UNKNOWN_ORDER_STATE, broker_order.broker_status, _execution_state(broker_order, executions), BrokerReconciliationDisposition.INTERNAL_RECORD_MISSING, TradeRestrictionState.AFFECTED_ACCOUNT_NEW_ORDERS_BLOCKED, "preserve_unexpected_broker_activity")
        if broker_order is None:
            return self._record(intent, None, executions, intent.intent_status, OrderLifecycleState.UNKNOWN_ORDER_STATE, ExecutionState.EXECUTION_UNCONFIRMED, BrokerReconciliationDisposition.BROKER_RECORD_MISSING, TradeRestrictionState.AFFECTED_ORDER_BLOCKED, "refresh_broker_order_before_progression")
        if intent.order_intent_id != broker_order.order_intent_id or intent.client_order_id != broker_order.client_order_id:
            return self._record(intent, broker_order, executions, intent.intent_status, broker_order.broker_status, _execution_state(broker_order, executions), BrokerReconciliationDisposition.STATUS_MISMATCH, TradeRestrictionState.AFFECTED_ORDER_BLOCKED, "preserve_identity_mismatch")
        execution_state = _execution_state(broker_order, executions)
        executed = sum((execution.execution_quantity for execution in executions), Decimal("0"))
        if executed != broker_order.filled_quantity:
            return self._record(intent, broker_order, executions, intent.intent_status, broker_order.broker_status, ExecutionState.EXECUTION_CONFLICTED, BrokerReconciliationDisposition.QUANTITY_MISMATCH, TradeRestrictionState.AFFECTED_INSTRUMENT_NEW_ORDERS_BLOCKED, "reconcile_broker_fill_quantity")
        expected_terminal = {
            OrderLifecycleState.BROKER_ACCEPTED,
            OrderLifecycleState.BROKER_RECEIVED,
            OrderLifecycleState.BROKER_PENDING,
            OrderLifecycleState.TRANSMITTED,
            OrderLifecycleState.SUBMISSION_ATTEMPTED,
        }
        if intent.intent_status in expected_terminal and broker_order.broker_status in expected_terminal:
            disposition = BrokerReconciliationDisposition.MATCHED_WITH_ALLOWED_DELAY
        elif broker_order.broker_status in {OrderLifecycleState.BROKER_REJECTED, OrderLifecycleState.CANCEL_REJECTED, OrderLifecycleState.BUSTED}:
            disposition = BrokerReconciliationDisposition.STATUS_MISMATCH
        else:
            disposition = BrokerReconciliationDisposition.MATCHED
        restriction = TradeRestrictionState.NO_TRADE_RESTRICTION if disposition in {BrokerReconciliationDisposition.MATCHED, BrokerReconciliationDisposition.MATCHED_WITH_ALLOWED_DELAY} else TradeRestrictionState.AFFECTED_ORDER_BLOCKED
        return self._record(intent, broker_order, executions, intent.intent_status, broker_order.broker_status, execution_state, disposition, restriction, "certify_reconciled_state_without_mutating_sources")

    def reconcile_position(self, internal: PositionSnapshot, broker: PositionSnapshot) -> BrokerReconciliationDisposition:
        if internal.source_type is not SnapshotSourceType.INTERNAL_EXPECTED or broker.source_type is not SnapshotSourceType.BROKER_REPORTED:
            return BrokerReconciliationDisposition.UNKNOWN_RECONCILIATION_STATE
        if internal.instrument_id != broker.instrument_id or internal.account_id != broker.account_id:
            return BrokerReconciliationDisposition.POSITION_MISMATCH
        return BrokerReconciliationDisposition.MATCHED if internal.broker_position_quantity == broker.broker_position_quantity else BrokerReconciliationDisposition.POSITION_MISMATCH

    def _record(self, intent: OrderIntentRecord | None, broker_order: BrokerOrderRecord | None, executions: tuple[ExecutionRecord, ...], internal_state: OrderLifecycleState, broker_state: OrderLifecycleState, execution_state: ExecutionState, disposition: BrokerReconciliationDisposition, restriction_state: TradeRestrictionState, action: str) -> BrokerReconciliationRecord:
        recon_id = _stable_id("BROKERREC", intent.order_intent_id if intent else "", broker_order.broker_order_id if broker_order else "", tuple(execution.execution_record_id for execution in executions), disposition.value)
        restriction = TradeRestrictionRecord(_stable_id("TRADERSTR", recon_id, restriction_state.value), restriction_state, intent.account_id if intent else broker_order.broker_account_id if broker_order else "", (intent.instrument_id if intent else broker_order.instrument_id if broker_order else "",), (intent.order_intent_id if intent else broker_order.broker_order_id if broker_order else "",), utc_timestamp(), disposition.value, (recon_id,), "Risk", "MO-TR-010", "until_successor_reconciliation_releases", ("fresh_broker_authoritative_record",), "ACTIVE" if restriction_state is not TradeRestrictionState.NO_TRADE_RESTRICTION else "NOT_REQUIRED", _stable_id("BRAUDIT", recon_id))
        record = BrokerReconciliationRecord(recon_id, intent.workflow_id if intent else "", intent.order_intent_id if intent else "", broker_order.broker_order_id if broker_order else "", tuple(execution.execution_record_id for execution in executions), internal_state, broker_state, execution_state, SettlementState.UNSETTLED if execution_state in {ExecutionState.PARTIAL_EXECUTION, ExecutionState.COMPLETE_EXECUTION} else SettlementState.NOT_APPLICABLE, disposition, restriction, tuple(_stable_digest(item) for item in (tuple(x for x in (intent, broker_order) if x is not None) + executions)), action, MO_TR_010_VERSION, utc_timestamp())
        self.ledger.append(record)
        return record


def _execution_state(broker_order: BrokerOrderRecord | None, executions: tuple[ExecutionRecord, ...]) -> ExecutionState:
    if any(execution.execution_status is ExecutionState.EXECUTION_BUSTED for execution in executions):
        return ExecutionState.EXECUTION_BUSTED
    if broker_order is None:
        return ExecutionState.EXECUTION_UNCONFIRMED
    if broker_order.filled_quantity == 0:
        return ExecutionState.NO_EXECUTION
    if broker_order.filled_quantity < broker_order.original_quantity:
        return ExecutionState.PARTIAL_EXECUTION
    return ExecutionState.COMPLETE_EXECUTION


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
