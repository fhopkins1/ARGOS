"""Order Management Office."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.communication import CourierService, IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository

from .offices import TRADER_GROUP_ID


ORDER_MANAGEMENT_OFFICE_ID = "TRADER-OFFICE-002"
ORDER_MANAGEMENT_STAFF_ID = "STF-062"


class OrderLifecycleState(str, Enum):
    """Authoritative Order Management lifecycle states."""

    CREATED = "created"
    VALIDATED = "validated"
    QUEUED = "queued"
    AWAITING_SUBMISSION = "awaiting_submission"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    WORKING = "working"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    PENDING_CANCELLATION = "pending_cancellation"
    CANCELLED = "cancelled"
    PENDING_MODIFICATION = "pending_modification"
    MODIFIED = "modified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    FAILED = "failed"
    ARCHIVED = "archived"


APPROVED_TRANSITIONS: dict[OrderLifecycleState, tuple[OrderLifecycleState, ...]] = {
    OrderLifecycleState.CREATED: (OrderLifecycleState.VALIDATED, OrderLifecycleState.REJECTED),
    OrderLifecycleState.VALIDATED: (OrderLifecycleState.QUEUED, OrderLifecycleState.AWAITING_SUBMISSION, OrderLifecycleState.REJECTED),
    OrderLifecycleState.QUEUED: (OrderLifecycleState.SUBMITTED, OrderLifecycleState.CANCELLED, OrderLifecycleState.FAILED),
    OrderLifecycleState.AWAITING_SUBMISSION: (OrderLifecycleState.SUBMITTED, OrderLifecycleState.CANCELLED, OrderLifecycleState.FAILED),
    OrderLifecycleState.SUBMITTED: (OrderLifecycleState.ACKNOWLEDGED, OrderLifecycleState.REJECTED, OrderLifecycleState.FAILED),
    OrderLifecycleState.ACKNOWLEDGED: (OrderLifecycleState.WORKING, OrderLifecycleState.REJECTED, OrderLifecycleState.EXPIRED),
    OrderLifecycleState.WORKING: (
        OrderLifecycleState.PARTIALLY_FILLED,
        OrderLifecycleState.FILLED,
        OrderLifecycleState.PENDING_CANCELLATION,
        OrderLifecycleState.PENDING_MODIFICATION,
        OrderLifecycleState.EXPIRED,
        OrderLifecycleState.FAILED,
    ),
    OrderLifecycleState.PARTIALLY_FILLED: (
        OrderLifecycleState.FILLED,
        OrderLifecycleState.PENDING_CANCELLATION,
        OrderLifecycleState.PENDING_MODIFICATION,
        OrderLifecycleState.EXPIRED,
        OrderLifecycleState.FAILED,
    ),
    OrderLifecycleState.PENDING_CANCELLATION: (OrderLifecycleState.CANCELLED, OrderLifecycleState.REJECTED, OrderLifecycleState.FAILED),
    OrderLifecycleState.PENDING_MODIFICATION: (OrderLifecycleState.MODIFIED, OrderLifecycleState.REJECTED, OrderLifecycleState.FAILED),
    OrderLifecycleState.MODIFIED: (OrderLifecycleState.WORKING, OrderLifecycleState.PENDING_CANCELLATION),
    OrderLifecycleState.FILLED: (OrderLifecycleState.ARCHIVED,),
    OrderLifecycleState.CANCELLED: (OrderLifecycleState.ARCHIVED,),
    OrderLifecycleState.REJECTED: (OrderLifecycleState.ARCHIVED,),
    OrderLifecycleState.EXPIRED: (OrderLifecycleState.ARCHIVED,),
    OrderLifecycleState.FAILED: (OrderLifecycleState.ARCHIVED,),
    OrderLifecycleState.ARCHIVED: (),
}


@dataclass(frozen=True)
class ExecutionOrderRequest:
    """Execution request received from the Trade Execution Office."""

    execution_plan_id: str
    instrument_id: str
    quantity: float
    direction: str
    execution_method: str
    venue: str
    account_id: str
    strategy_id: str
    executive_authorization_id: str
    risk_reference_id: str
    position_id: str
    order_priority: int
    broker_destination: str
    exchange_destination: str
    execution_constraints: tuple[str, ...] = ()
    parent_order_id: str | None = None
    child_order_index: int | None = None


@dataclass(frozen=True)
class BrokerOrderMessage:
    """Broker or exchange message consumed by OMO."""

    message_id: str
    order_id: str
    message_type: str
    acknowledged_quantity: float
    filled_quantity: float
    remaining_quantity: float
    price: float
    status: str
    timestamp_utc: str


@dataclass(frozen=True)
class OrderFillRecord:
    """Order fill record received through Broker Integration."""

    fill_id: str
    order_id: str
    quantity: float
    price: float
    timestamp_utc: str
    broker_message_id: str


@dataclass(frozen=True)
class OrderManagementSystemPrompt:
    """OMO governing system prompt artifact."""

    prompt_id: str
    version: str
    prompt_text: str


@dataclass(frozen=True)
class OrderManagementInconsistency:
    """Detected order management inconsistency."""

    inconsistency_id: str
    classification: str
    severity: str
    order_id: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class OrderManagementCaseFile:
    """Case file generated for OMO inconsistencies."""

    case_file_id: str
    order_id: str
    inconsistencies: tuple[OrderManagementInconsistency, ...]
    synchronization_sources: tuple[str, ...]
    reconstructable: bool


@dataclass(frozen=True)
class OrderIdentifierSet:
    """Immutable organizational order identifiers."""

    order_id: str
    parent_order_id: str | None
    child_order_id: str | None
    strategy_id: str
    executive_decision_id: str
    position_id: str
    audit_record_id: str


@dataclass(frozen=True)
class OrderStateTransition:
    """Permanent order state transition."""

    transition_id: str
    order_id: str
    originating_component: str
    triggering_event: str
    organizational_justification: str
    from_state: OrderLifecycleState
    to_state: OrderLifecycleState
    timestamp_utc: str
    position_id: str = ""
    audit_record_id: str = ""
    supporting_metadata: dict[str, object] | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "transition_id": self.transition_id,
            "order_id": self.order_id,
            "originating_component": self.originating_component,
            "triggering_event": self.triggering_event,
            "organizational_justification": self.organizational_justification,
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "timestamp_utc": self.timestamp_utc,
            "position_id": self.position_id,
            "audit_record_id": self.audit_record_id,
            "supporting_metadata": self.supporting_metadata or {},
        }


@dataclass(frozen=True)
class ManagedOrderRecord:
    """Single authoritative order record."""

    identifiers: OrderIdentifierSet
    request: ExecutionOrderRequest
    current_state: OrderLifecycleState
    state_history: tuple[OrderStateTransition, ...]
    routing: dict[str, object]
    synchronization_targets: tuple[str, ...]
    broker_messages: tuple[BrokerOrderMessage, ...] = ()
    fills: tuple[OrderFillRecord, ...] = ()

    def to_payload(self) -> dict[str, object]:
        return {
            "identifiers": self.identifiers.__dict__,
            "request": self.request.__dict__,
            "current_state": self.current_state.value,
            "state_history": [transition.to_payload() for transition in self.state_history],
            "routing": self.routing,
            "synchronization_targets": self.synchronization_targets,
            "broker_messages": [message.__dict__ for message in self.broker_messages],
            "fills": [fill.__dict__ for fill in self.fills],
        }


class OrderIntakeEngine:
    """Receive and validate execution request completeness."""

    required_fields = (
        "execution_plan_id",
        "instrument_id",
        "quantity",
        "direction",
        "execution_method",
        "venue",
        "account_id",
        "strategy_id",
        "executive_authorization_id",
        "risk_reference_id",
        "position_id",
        "broker_destination",
        "exchange_destination",
    )

    def verify(self, request: ExecutionOrderRequest) -> tuple[str, ...]:
        errors = []
        for field_name in self.required_fields:
            value = getattr(request, field_name)
            if value is None or value == "":
                errors.append(f"missing required field: {field_name}")
        if request.quantity <= 0:
            errors.append("order quantity must be positive")
        if request.order_priority < 0:
            errors.append("order priority must be non-negative")
        return tuple(errors)


class OrderConstructionValidationEngine:
    """Validate constructed order semantics."""

    def validate(self, request: ExecutionOrderRequest) -> tuple[str, ...]:
        errors = []
        if request.direction not in {"buy", "sell", "sell_short", "cover"}:
            errors.append("order direction is unsupported")
        if request.execution_method not in {"market", "limit", "stop", "stop_limit", "algorithmic"}:
            errors.append("execution method is unsupported")
        if not request.executive_authorization_id.startswith("DOC-"):
            errors.append("Executive authorization reference must be a Document ID")
        if not request.risk_reference_id.startswith("DOC-"):
            errors.append("Risk reference must be a Document ID")
        if request.child_order_index is not None and not request.parent_order_id:
            errors.append("child orders require a parent order ID")
        return tuple(errors)


class OrderIdentifierEngine:
    """Assign immutable organizational order identifiers."""

    def assign(self, request: ExecutionOrderRequest, sequence: int) -> OrderIdentifierSet:
        order_id = f"ORD-{sequence:06d}"
        child_order_id = f"{request.parent_order_id}-CHILD-{request.child_order_index:03d}" if request.child_order_index is not None else None
        return OrderIdentifierSet(
            order_id,
            request.parent_order_id,
            child_order_id,
            request.strategy_id,
            request.executive_authorization_id,
            request.position_id,
            f"AUD-ORD-{sequence:06d}",
        )


class OrderStateEngine:
    """Maintain authoritative order lifecycle state."""

    def transition(
        self,
        order: ManagedOrderRecord,
        to_state: OrderLifecycleState,
        originating_component: str,
        triggering_event: str,
        justification: str,
    ) -> ManagedOrderRecord:
        to_state = OrderLifecycleState(to_state)
        if to_state not in APPROVED_TRANSITIONS[order.current_state]:
            raise ValueError(f"unauthorized order transition: {order.current_state.value} -> {to_state.value}")
        transition = OrderStateTransition(
            f"OST-{len(order.state_history) + 1:06d}",
            order.identifiers.order_id,
            originating_component,
            triggering_event,
            justification,
            order.current_state,
            to_state,
            utc_timestamp(),
            order.identifiers.position_id,
            order.identifiers.audit_record_id,
            {"responsible_office": ORDER_MANAGEMENT_OFFICE_ID},
        )
        return ManagedOrderRecord(
            order.identifiers,
            order.request,
            to_state,
            (*order.state_history, transition),
            order.routing,
            order.synchronization_targets,
            order.broker_messages,
            order.fills,
        )


class ParentChildOrderEngine:
    """Validate parent-child order relationships."""

    def link_payload(self, order: ManagedOrderRecord) -> dict[str, object]:
        return {
            "order_id": order.identifiers.order_id,
            "parent_order_id": order.identifiers.parent_order_id,
            "child_order_id": order.identifiers.child_order_id,
            "strategy_id": order.identifiers.strategy_id,
            "executive_decision_id": order.identifiers.executive_decision_id,
            "position_id": order.identifiers.position_id,
        }


class OrderRoutingEngine:
    """Prepare validated orders for transmission without optimizing strategy."""

    def route(self, request: ExecutionOrderRequest, identifiers: OrderIdentifierSet) -> dict[str, object]:
        return {
            "order_id": identifiers.order_id,
            "broker_destination": request.broker_destination,
            "exchange_destination": request.exchange_destination,
            "routing_priority": request.order_priority,
            "routing_constraints": request.execution_constraints,
            "transmission_sequence": (identifiers.order_id,),
            "strategy_modified": False,
        }


class SynchronizationEngine:
    """Maintain deterministic synchronization targets."""

    targets = (
        "Trade Execution Office",
        "Broker Integration Office",
        "Position Management Office",
        "Trade Monitoring Office",
        "Executive Dashboard",
        "Audit Repository",
    )

    def verify(self, order: ManagedOrderRecord) -> tuple[str, ...]:
        missing = tuple(target for target in self.targets if target not in order.synchronization_targets)
        if missing:
            raise ValueError(f"order synchronization missing targets: {', '.join(missing)}")
        return self.targets


class OrderConsistencyMonitor:
    """Detect deterministic OMO inconsistencies."""

    def inspect(
        self,
        order: ManagedOrderRecord,
        stale_after_transitions: int = 5,
    ) -> tuple[OrderManagementInconsistency, ...]:
        inconsistencies: list[OrderManagementInconsistency] = []
        seen_messages = set()
        for message in order.broker_messages:
            if message.message_id in seen_messages:
                inconsistencies.append(_inconsistency("duplicate_broker_message", order.identifiers.order_id, message.message_id))
            seen_messages.add(message.message_id)
            if message.order_id != order.identifiers.order_id:
                inconsistencies.append(_inconsistency("unexpected_broker_response", order.identifiers.order_id, message.message_id))
            if message.filled_quantity + message.remaining_quantity > order.request.quantity:
                inconsistencies.append(_inconsistency("quantity_mismatch", order.identifiers.order_id, message.message_id))
            if message.price <= 0:
                inconsistencies.append(_inconsistency("price_inconsistency", order.identifiers.order_id, message.message_id))

        seen_fills = set()
        total_fill_quantity = 0.0
        for fill in order.fills:
            if fill.fill_id in seen_fills:
                inconsistencies.append(_inconsistency("duplicate_fill", order.identifiers.order_id, fill.fill_id))
            seen_fills.add(fill.fill_id)
            total_fill_quantity += fill.quantity
            if fill.order_id != order.identifiers.order_id:
                inconsistencies.append(_inconsistency("unexpected_fill_order", order.identifiers.order_id, fill.fill_id))
            if fill.price <= 0:
                inconsistencies.append(_inconsistency("price_inconsistency", order.identifiers.order_id, fill.fill_id))
        if total_fill_quantity > order.request.quantity:
            inconsistencies.append(_inconsistency("quantity_mismatch", order.identifiers.order_id, "fill_quantity_exceeds_order_quantity"))

        if order.current_state in {OrderLifecycleState.SUBMITTED, OrderLifecycleState.WORKING} and not order.broker_messages:
            inconsistencies.append(_inconsistency("missing_acknowledgement", order.identifiers.order_id, order.current_state.value))
        if len(order.state_history) >= stale_after_transitions and order.current_state in {OrderLifecycleState.SUBMITTED, OrderLifecycleState.ACKNOWLEDGED, OrderLifecycleState.WORKING}:
            inconsistencies.append(_inconsistency("stale_order", order.identifiers.order_id, order.current_state.value))
        missing_targets = tuple(target for target in SynchronizationEngine.targets if target not in order.synchronization_targets)
        if missing_targets:
            inconsistencies.append(_inconsistency("position_synchronization_failure", order.identifiers.order_id, ",".join(missing_targets)))
        return tuple(inconsistencies)


def _inconsistency(classification: str, order_id: str, evidence: str) -> OrderManagementInconsistency:
    return OrderManagementInconsistency(
        f"OMIC-{hashlib.sha256(f'{classification}:{order_id}:{evidence}'.encode('utf-8')).hexdigest()[:8].upper()}",
        classification,
        "high" if classification in {"quantity_mismatch", "position_synchronization_failure"} else "medium",
        order_id,
        (evidence,),
    )


class OrderPersistenceEngine:
    """Persist immutable order history."""

    def persist(self, repository: InMemoryPersistenceRepository, order: ManagedOrderRecord) -> None:
        repository.persist(
            ObjectType.OPERATIONAL_DOCUMENT,
            order.identifiers.order_id.replace("ORD", "DOC"),
            {
                "contract_id": order.identifiers.order_id.replace("ORD", "DOC"),
                "case_file_id": "CF-001",
                "order_id": order.identifiers.order_id,
                "payload": order.to_payload(),
            },
        )


class OrderManagementOffice:
    """Deterministic Order Management Office."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.configuration_service = configuration_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self.prompt_repository = prompt_repository
        self.intake = OrderIntakeEngine()
        self.construction = OrderConstructionValidationEngine()
        self.identifiers = OrderIdentifierEngine()
        self.state = OrderStateEngine()
        self.parent_child = ParentChildOrderEngine()
        self.routing = OrderRoutingEngine()
        self.synchronization = SynchronizationEngine()
        self.consistency = OrderConsistencyMonitor()
        self.persistence = OrderPersistenceEngine()
        self._orders: dict[str, ManagedOrderRecord] = {}

    def create_order(
        self,
        request: ExecutionOrderRequest,
        case_file_id: str,
        trade_cycle_id: str,
        order_sequence: int,
        document_sequence: int,
    ) -> OperationalContract:
        """Create, validate, route, persist, and audit one managed order."""
        self.configuration_service.validate_startup()
        errors = (*self.intake.verify(request), *self.construction.validate(request))
        if errors:
            return self._exception_contract(case_file_id, trade_cycle_id, document_sequence, errors)
        identifiers = self.identifiers.assign(request, order_sequence)
        if identifiers.order_id in self._orders:
            return self._exception_contract(case_file_id, trade_cycle_id, document_sequence, (f"duplicate order: {identifiers.order_id}",))
        routing = self.routing.route(request, identifiers)
        created = ManagedOrderRecord(
            identifiers,
            request,
            OrderLifecycleState.CREATED,
            (),
            routing,
            self.synchronization.targets,
        )
        managed = self.state.transition(created, OrderLifecycleState.VALIDATED, "Order Construction Validation Engine", "construction_validated", "Order contains required construction metadata.")
        managed = self.state.transition(managed, OrderLifecycleState.QUEUED, "Order Routing Engine", "routing_prepared", "Validated order is queued for broker transmission.")
        self.synchronization.verify(managed)
        self.persistence.persist(self.persistence_repository, managed)
        self._orders[identifiers.order_id] = managed
        contract = self._order_contract(managed, case_file_id, trade_cycle_id, document_sequence)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        self.audit_service.record_staff_decision(
            contract,
            ORDER_MANAGEMENT_STAFF_ID,
            TRADER_GROUP_ID,
            "order_created_and_awaiting_submission",
            "Order Management Office validated construction, assigned identifiers, and queued deterministic routing.",
        )
        return contract

    def transition_order(
        self,
        order_id: str,
        to_state: OrderLifecycleState,
        triggering_event: str,
        justification: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Advance one order through an approved lifecycle transition."""
        if order_id not in self._orders:
            raise ValueError(f"unknown order: {order_id}")
        managed = self.state.transition(self._orders[order_id], to_state, "Order State Engine", triggering_event, justification)
        self.synchronization.verify(managed)
        self.persistence.persist(self.persistence_repository, managed)
        self._orders[order_id] = managed
        contract = self._order_contract(managed, case_file_id, trade_cycle_id, document_sequence)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        return contract

    def record_broker_message(
        self,
        order_id: str,
        message: BrokerOrderMessage,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Record a Broker Integration message and inspect consistency."""
        if order_id not in self._orders:
            raise ValueError(f"unknown order: {order_id}")
        order = self._orders[order_id]
        updated = ManagedOrderRecord(
            order.identifiers,
            order.request,
            order.current_state,
            order.state_history,
            order.routing,
            order.synchronization_targets,
            (*order.broker_messages, message),
            order.fills,
        )
        self._orders[order_id] = updated
        inconsistencies = self.consistency.inspect(updated)
        if inconsistencies:
            return self.generate_case_file(order_id, inconsistencies, case_file_id, trade_cycle_id, document_sequence)
        return self._order_contract(updated, case_file_id, trade_cycle_id, document_sequence)

    def record_fill(
        self,
        order_id: str,
        fill: OrderFillRecord,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Record a fill and inspect consistency."""
        if order_id not in self._orders:
            raise ValueError(f"unknown order: {order_id}")
        order = self._orders[order_id]
        updated = ManagedOrderRecord(
            order.identifiers,
            order.request,
            order.current_state,
            order.state_history,
            order.routing,
            order.synchronization_targets,
            order.broker_messages,
            (*order.fills, fill),
        )
        self._orders[order_id] = updated
        inconsistencies = self.consistency.inspect(updated)
        if inconsistencies:
            return self.generate_case_file(order_id, inconsistencies, case_file_id, trade_cycle_id, document_sequence)
        return self._order_contract(updated, case_file_id, trade_cycle_id, document_sequence)

    def generate_case_file(
        self,
        order_id: str,
        inconsistencies: tuple[OrderManagementInconsistency, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Generate an Order Management Case File for downstream review."""
        if order_id not in self._orders:
            raise ValueError(f"unknown order: {order_id}")
        order = self._orders[order_id]
        case_file = OrderManagementCaseFile(
            f"OMCF-{document_sequence:06d}",
            order_id,
            inconsistencies,
            (
                "Executive Decisions",
                "Execution Requests",
                "Broker Messages",
                "Position Records",
                "Audit Logs",
                "Historian Records",
            ),
            True,
        )
        payload = {
            "office_id": ORDER_MANAGEMENT_OFFICE_ID,
            "office_name": "Order Management Office",
            "order_management_status": "case_file_generated",
            "case_file": case_file.__dict__,
            "authoritative_order": order.to_payload(),
            "history_overwritten": False,
            "event_loss_detected": False,
        }
        contract = _contract(document_sequence, "ORDER_CASE_FILE", case_file_id, trade_cycle_id, (order.request.executive_authorization_id, order.request.risk_reference_id), "Order Management Case File.", payload)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        return contract

    def system_prompt(self) -> OrderManagementSystemPrompt:
        """Return OMO governing system prompt."""
        return OrderManagementSystemPrompt(
            "PROMPT-OMO-054",
            "1.0.0",
            (
                "You are the Order Management Office (OMO) of ARGOS. Manage the complete deterministic lifecycle "
                "of every order executed by the Trader Group. Serve as the authoritative state manager from "
                "creation through archival while maintaining complete auditability, traceability, and enterprise "
                "synchronization. Do not determine what should be traded, perform market analysis, or modify "
                "Executive intent. Manage execution state only. Every order progresses only through authorized "
                "lifecycle states, every transition is permanently recorded, and every inconsistency generates an "
                "Order Management Case File for downstream review."
            ),
        )

    def managed_order(self, order_id: str) -> ManagedOrderRecord | None:
        """Return the authoritative order record."""
        return self._orders.get(order_id)

    def order_history(self, order_id: str) -> tuple[OrderStateTransition, ...]:
        """Return permanent order transition history."""
        order = self.managed_order(order_id)
        return () if order is None else order.state_history

    def route_order_record(self, order_contract: OperationalContract, target_inbox: IncomingMailbox):
        """Route an order record through Courier."""
        from argos.foundation.communication import OutgoingMailbox

        return CourierService(self.audit_service).deliver(
            OutgoingMailbox(ORDER_MANAGEMENT_STAFF_ID, TRADER_GROUP_ID),
            target_inbox,
            order_contract,
        )

    def _order_contract(
        self,
        order: ManagedOrderRecord,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        payload = {
            "office_id": ORDER_MANAGEMENT_OFFICE_ID,
            "office_name": "Order Management Office",
            "order_management_status": "authoritative_order_record",
            "managed_order": order.to_payload(),
            "parent_child_linkage": self.parent_child.link_payload(order),
            "order_management_system_prompt": self.system_prompt().__dict__,
            "duplicate_order_prevented": True,
            "execution_strategy_modified": False,
            "executive_intent_modified": False,
            "ambiguous_order_status": False,
        }
        return _contract(
            document_sequence,
            "ORDER_RECORD",
            case_file_id,
            trade_cycle_id,
            (order.request.executive_authorization_id, order.request.risk_reference_id),
            "Order Management Office authoritative order record.",
            payload,
        )

    def _exception_contract(
        self,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        errors: tuple[str, ...],
    ) -> OperationalContract:
        payload = {
            "office_id": ORDER_MANAGEMENT_OFFICE_ID,
            "office_name": "Order Management Office",
            "order_management_status": "order_rejected",
            "validation_errors": errors,
        }
        contract = _contract(document_sequence, "ORDER_EXCEPTION", case_file_id, trade_cycle_id, (), "Order Management Office exception report.", payload)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        return contract


def _contract(
    document_sequence: int,
    contract_type: str,
    case_file_id: str,
    trade_cycle_id: str,
    parent_contract_ids: tuple[str, ...],
    human_summary: str,
    payload: dict[str, Any],
) -> OperationalContract:
    created = utc_timestamp()
    normalized_payload = _json_ready(payload)
    signature_hash = hashlib.sha256(
        json.dumps(normalized_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return OperationalContract(
        contract_id=generate_document_id(document_sequence),
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=case_file_id,
        trade_cycle_id=trade_cycle_id,
        parent_contract_ids=parent_contract_ids,
        produced_by_staff_id=ORDER_MANAGEMENT_STAFF_ID,
        produced_by_group_id=TRADER_GROUP_ID,
        intended_consumer_group_id=TRADER_GROUP_ID,
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=human_summary,
        machine_payload=normalized_payload,
        signature_hash=signature_hash,
        source_reference_ids=parent_contract_ids,
    )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
