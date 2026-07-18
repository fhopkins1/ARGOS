"""Broker-realistic deterministic paper brokerage for ARGOS OR-003."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from typing import Any

from argos.control_panel.enterprise_communications_bus import EnterpriseCommunicationsBus, MessageMode
from argos.control_panel.market_data_provider import MarketDataProviderAbstractionLayer
from argos.control_panel.performance_truth_engine import PerformanceTruthEngine
from argos.control_panel.position_monitoring_network import PositionMonitoringNetwork
from argos.control_panel.truth_domain import make_paper_operational_truth_envelope, validate_decision_object_for_operational_truth
from argos.control_panel.truth_promotion import PromotionDecisionStatus, TruthPromotionAuthority
from argos.foundation.contracts import utc_timestamp

from .execution_quality import CompletedExecutionRecord, ExecutionQualityOffice
from .order_management import (
    BrokerOrderMessage,
    ExecutionOrderRequest,
    OrderFillRecord,
    OrderLifecycleState,
    OrderManagementOffice,
)


PAPER_BROKERAGE_ID = "BROKER-PAPER-OR003"
SUPPORTED_ORDER_TYPES = ("market", "limit", "stop", "stop_limit")
SUPPORTED_TIME_IN_FORCE = ("day", "gtc", "ioc", "fok")
SUPPORTED_ASSETS = ("stock", "equity", "etf", "retail_bond", "option", "crypto")
TERMINAL_STATUSES = {"filled", "cancelled", "rejected", "expired", "settled"}


class PaperBrokerRejectionCode(str, Enum):
    MISSING_WORKFLOW_OWNERSHIP = "MISSING_WORKFLOW_OWNERSHIP"
    INVALID_WORKFLOW_OWNER = "INVALID_WORKFLOW_OWNER"
    EXPIRED_WORKFLOW_TOKEN = "EXPIRED_WORKFLOW_TOKEN"
    MISSING_DECISION_PROVENANCE = "MISSING_DECISION_PROVENANCE"
    MISSING_RISK_APPROVAL = "MISSING_RISK_APPROVAL"
    MISSING_POLICY_APPROVAL = "MISSING_POLICY_APPROVAL"
    INSUFFICIENT_BUYING_POWER = "INSUFFICIENT_BUYING_POWER"
    UNSUPPORTED_ASSET = "UNSUPPORTED_ASSET"
    MARKET_CLOSED = "MARKET_CLOSED"
    MARKET_DATA_UNAVAILABLE = "MARKET_DATA_UNAVAILABLE"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    INVALID_ORDER_TYPE = "INVALID_ORDER_TYPE"
    INVALID_TIME_IN_FORCE = "INVALID_TIME_IN_FORCE"
    INVALID_SIDE = "INVALID_SIDE"
    INVALID_ACCOUNT = "INVALID_ACCOUNT"
    DUPLICATE_ORDER = "DUPLICATE_ORDER"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"


@dataclass(frozen=True)
class PaperBrokerAccount:
    account_id: str
    cash: float
    reserved_cash: float = 0.0
    settled_cash: float | None = None


@dataclass(frozen=True)
class PaperBrokerOrderTicket:
    order_id: str
    workflow_id: str
    mission_id: str
    decision_object_id: str
    workflow_token: str
    trader_identity: str
    account_id: str
    symbol: str
    asset_type: str
    side: str
    quantity: float
    order_type: str
    time_in_force: str
    limit_price: float = 0.0
    stop_price: float = 0.0
    risk_approval_id: str = ""
    policy_approval_id: str = ""
    strategy_id: str = ""
    execution_plan_id: str = ""
    decision_object: dict[str, Any] | None = None


@dataclass(frozen=True)
class MarketState:
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    session: str
    source: str
    timestamp_utc: str
    replay_identifier: str = ""
    truth_domain: str = "PAPER"


@dataclass(frozen=True)
class BrokerFillRecord:
    fill_id: str
    order_id: str
    execution_id: str
    quantity: float
    price: float
    commission: float
    slippage: float
    timestamp_utc: str
    price_source: str
    remaining_quantity: float


@dataclass(frozen=True)
class BrokerEventRecord:
    event_id: str
    event_type: str
    order_id: str
    status: str
    timestamp_utc: str
    provenance: dict[str, Any]
    payload: dict[str, Any]
    content_hash: str


@dataclass(frozen=True)
class PaperBrokerOrderRecord:
    order_id: str
    ticket: PaperBrokerOrderTicket
    status: str
    lifecycle: tuple[str, ...]
    market_state: MarketState | None
    created_at: str
    updated_at: str
    requested_quantity: float
    filled_quantity: float
    remaining_quantity: float
    average_fill_price: float
    reserved_cash: float
    rejection_code: str = ""
    fills: tuple[BrokerFillRecord, ...] = ()
    events: tuple[BrokerEventRecord, ...] = ()
    settlement_state: str = ""
    settlement_timestamp: str = ""


@dataclass(frozen=True)
class BrokerSubmissionResult:
    accepted: bool
    order: PaperBrokerOrderRecord
    events: tuple[BrokerEventRecord, ...]
    rejection_code: str = ""


class PaperBrokerMarketDataAdapter:
    """Read bid/ask market observations from the existing market-data layer."""

    def __init__(self, provider: MarketDataProviderAbstractionLayer | None = None) -> None:
        self.provider = provider or MarketDataProviderAbstractionLayer()

    def market_state(self, symbol: str, timestamp_utc: str, workflow_id: str, decision_object_id: str) -> MarketState | None:
        quote = self.provider.get_quote(symbol, timestamp_utc, workflow_id=workflow_id, decision_object_id=decision_object_id)
        normalized = quote.get("normalizedObject") or {}
        if not normalized:
            return None
        source = normalized.get("sourceAttribution", {})
        status_response = self.provider.get_market_status(timestamp_utc)
        market_status = (status_response.get("normalizedObject") or {}).get("status", "UNKNOWN")
        try:
            return MarketState(
                symbol=str(normalized["symbol"]).upper(),
                bid=float(normalized["bid"]),
                ask=float(normalized["ask"]),
                last=float(normalized["last"]),
                volume=float(normalized.get("volume", 0.0) or 0.0),
                session=str(market_status),
                source=str(source.get("providerId", "unknown")),
                timestamp_utc=str(source.get("dataTimestamp", timestamp_utc)),
                replay_identifier=str(source.get("rawPayloadReference", "")),
            )
        except (KeyError, TypeError, ValueError):
            return None


class PaperBrokerOrderBook:
    """Append-only in-memory broker order book."""

    def __init__(self) -> None:
        self._orders: dict[str, PaperBrokerOrderRecord] = {}

    def add(self, order: PaperBrokerOrderRecord) -> None:
        if order.order_id in self._orders:
            raise ValueError(f"duplicate broker order: {order.order_id}")
        self._orders[order.order_id] = order

    def replace(self, order: PaperBrokerOrderRecord) -> None:
        if order.order_id not in self._orders:
            raise ValueError(f"unknown broker order: {order.order_id}")
        self._orders[order.order_id] = order

    def get(self, order_id: str) -> PaperBrokerOrderRecord | None:
        return self._orders.get(order_id)

    def snapshot(self) -> dict[str, tuple[dict[str, Any], ...]]:
        groups: dict[str, list[dict[str, Any]]] = {status: [] for status in ("pending", "working", "filled", "cancelled", "expired", "rejected", "settled")}
        for order in self._orders.values():
            key = "pending" if order.status in {"created", "validated", "accepted", "queued"} else order.status
            groups.setdefault(key, []).append(_json_ready(order))
        return {key: tuple(value) for key, value in groups.items()}


class PaperBrokerFillEngine:
    """Sole authority for paper fills, partial fills, average price, and settlement triggers."""

    def evaluate(self, order: PaperBrokerOrderRecord, market: MarketState) -> tuple[PaperBrokerOrderRecord, tuple[BrokerFillRecord, ...], str]:
        ticket = order.ticket
        if ticket.order_type == "limit" and not _limit_executable(ticket, market):
            return order, (), "queued"
        if ticket.order_type == "stop" and not _stop_triggered(ticket, market):
            return order, (), "queued"
        if ticket.order_type == "stop_limit" and (not _stop_triggered(ticket, market) or not _limit_executable(ticket, market)):
            return order, (), "queued"
        reference_price = market.ask if ticket.side == "buy" else market.bid
        if reference_price <= 0:
            return order, (), "rejected"
        available_quantity = max(0.0, min(order.remaining_quantity, market.volume * 0.001 if market.volume else order.remaining_quantity))
        if ticket.time_in_force == "fok" and available_quantity < order.remaining_quantity:
            return order, (), "expired"
        if ticket.time_in_force == "ioc" and available_quantity <= 0:
            return order, (), "expired"
        fill_quantity = round(min(order.remaining_quantity, available_quantity), 4)
        if fill_quantity <= 0:
            return order, (), "queued"
        slippage = _slippage(ticket, market, fill_quantity)
        price = round(reference_price + slippage if ticket.side == "buy" else max(0.0, reference_price - slippage), 4)
        commission = _commission(ticket, fill_quantity, price)
        remaining = round(max(0.0, order.remaining_quantity - fill_quantity), 4)
        fill = BrokerFillRecord(
            fill_id=_stable_id("FILL", order.order_id, str(len(order.fills) + 1), market.timestamp_utc),
            order_id=order.order_id,
            execution_id=_stable_id("EXEC", order.order_id),
            quantity=fill_quantity,
            price=price,
            commission=commission,
            slippage=round(slippage * fill_quantity, 4),
            timestamp_utc=market.timestamp_utc,
            price_source=market.source,
            remaining_quantity=remaining,
        )
        total_quantity = round(order.filled_quantity + fill.quantity, 4)
        average = round(((order.average_fill_price * order.filled_quantity) + (fill.price * fill.quantity)) / max(total_quantity, 0.0001), 4)
        status = "filled" if remaining == 0 else "partially_filled"
        return replace(
            order,
            status=status,
            lifecycle=(*order.lifecycle, "Working", "Filled" if status == "filled" else "Partially Filled"),
            updated_at=market.timestamp_utc,
            filled_quantity=total_quantity,
            remaining_quantity=remaining,
            average_fill_price=average,
            fills=(*order.fills, fill),
        ), (fill,), status


class DeterministicPaperBrokerage:
    """Enterprise paper broker boundary between Trader and Performance Truth."""

    def __init__(
        self,
        *,
        order_management: OrderManagementOffice,
        execution_quality: ExecutionQualityOffice | None = None,
        performance_truth: PerformanceTruthEngine | None = None,
        communications_bus: EnterpriseCommunicationsBus | None = None,
        position_monitoring: PositionMonitoringNetwork | None = None,
        market_data: PaperBrokerMarketDataAdapter | None = None,
        account: PaperBrokerAccount | None = None,
    ) -> None:
        self.order_management = order_management
        self.execution_quality = execution_quality
        self.performance_truth = performance_truth
        self.communications_bus = communications_bus
        self.position_monitoring = position_monitoring
        self.market_data = market_data or PaperBrokerMarketDataAdapter()
        self.account = account or PaperBrokerAccount("ACCT-PAPER-001", 100000.0, 0.0, 100000.0)
        self.order_book = PaperBrokerOrderBook()
        self.fill_engine = PaperBrokerFillEngine()
        self._sequence = 0

    def submit_order(
        self,
        ticket: PaperBrokerOrderTicket,
        *,
        workflow_token: Any,
        case_file_id: str = "CF-003",
        trade_cycle_id: str = "TC-003",
        document_sequence: int = 3000,
    ) -> BrokerSubmissionResult:
        now = utc_timestamp()
        market = self.market_data.market_state(ticket.symbol, now, ticket.workflow_id, ticket.decision_object_id)
        rejection = self._validate(ticket, workflow_token, market)
        if rejection:
            order = self._new_order(ticket, now, market, "rejected", rejection.value)
            event = self._event(order, "Broker Reject", {"rejectionCode": rejection.value})
            order = replace(order, events=(event,))
            self.order_book.add(order)
            self._publish(event)
            self._record_order_management_message(order, event, case_file_id, trade_cycle_id, document_sequence)
            return BrokerSubmissionResult(False, order, (event,), rejection.value)

        order = self._new_order(ticket, now, market, "accepted", "")
        accepted = self._event(order, "Order Accepted", {})
        order = replace(order, lifecycle=("Created", "Validated", "Accepted", "Queued"), events=(accepted,), reserved_cash=self._reserve_cash(ticket, market))
        self.order_book.add(order)
        self._publish(accepted)
        self._record_order_management_message(order, accepted, case_file_id, trade_cycle_id, document_sequence)
        if market and _session_allows_execution(market):
            order, fill_events = self.advance_order(order.order_id, case_file_id=case_file_id, trade_cycle_id=trade_cycle_id, document_sequence=document_sequence + 1)
            return BrokerSubmissionResult(True, order, (accepted, *fill_events))
        working = self._event(order, "Order Working", {"queuedReason": "awaiting_executable_market"})
        order = replace(order, status="queued", events=(*order.events, working))
        self.order_book.replace(order)
        self._publish(working)
        return BrokerSubmissionResult(True, order, (accepted, working))

    def advance_order(self, order_id: str, *, case_file_id: str = "CF-003", trade_cycle_id: str = "TC-003", document_sequence: int = 3000) -> tuple[PaperBrokerOrderRecord, tuple[BrokerEventRecord, ...]]:
        order = self._require_order(order_id)
        if order.status in TERMINAL_STATUSES:
            return order, ()
        market = order.market_state or self.market_data.market_state(order.ticket.symbol, utc_timestamp(), order.ticket.workflow_id, order.ticket.decision_object_id)
        if market is None:
            event = self._event(order, "Broker Reject", {"rejectionCode": PaperBrokerRejectionCode.MARKET_DATA_UNAVAILABLE.value})
            updated = replace(order, status="rejected", rejection_code=PaperBrokerRejectionCode.MARKET_DATA_UNAVAILABLE.value, events=(*order.events, event))
            self.order_book.replace(updated)
            self._publish(event)
            return updated, (event,)
        if not _session_allows_execution(market):
            event = self._event(order, "Order Working", {"queuedReason": "market_session_not_executable"})
            updated = replace(order, status="queued", events=(*order.events, event))
            self.order_book.replace(updated)
            self._publish(event)
            return updated, (event,)
        updated, fills, fill_status = self.fill_engine.evaluate(replace(order, market_state=market), market)
        if fill_status == "expired":
            event = self._event(updated, "Order Expiration", {"reason": f"{order.ticket.time_in_force}_not_fillable"})
            updated = replace(updated, status="expired", lifecycle=(*updated.lifecycle, "Expired"), events=(*updated.events, event))
            self.order_book.replace(updated)
            self._publish(event)
            return updated, (event,)
        if fill_status == "queued":
            event = self._event(updated, "Order Working", {"reason": "order_not_executable"})
            updated = replace(updated, status="working", events=(*updated.events, event))
            self.order_book.replace(updated)
            self._publish(event)
            return updated, (event,)
        events = tuple(self._event(updated, "Partial Fill" if fill.remaining_quantity else "Fill", {"fill": _json_ready(fill)}) for fill in fills)
        updated = replace(updated, events=(*updated.events, *events))
        if updated.status == "filled":
            settlement = self._event(updated, "Settlement", {"settlementState": "settled"})
            updated = replace(updated, lifecycle=(*updated.lifecycle, "Settled"), status="settled", settlement_state="settled", settlement_timestamp=settlement.timestamp_utc, events=(*updated.events, settlement))
            events = (*events, settlement)
        self.order_book.replace(updated)
        for event in events:
            self._publish(event)
            self._record_order_management_message(updated, event, case_file_id, trade_cycle_id, document_sequence)
        self._record_performance_truth(updated)
        self._record_execution_quality(updated, case_file_id, trade_cycle_id, document_sequence + 20)
        self._notify_position_monitoring()
        return updated, events

    def cancel_order(self, order_id: str, reason: str = "trader_request") -> PaperBrokerOrderRecord:
        order = self._require_order(order_id)
        if order.status in TERMINAL_STATUSES:
            return order
        event = self._event(order, "Cancellation", {"reason": reason})
        updated = replace(order, status="cancelled", lifecycle=(*order.lifecycle, "Cancelled"), events=(*order.events, event), updated_at=event.timestamp_utc)
        self.order_book.replace(updated)
        self._publish(event)
        return updated

    def _validate(self, ticket: PaperBrokerOrderTicket, workflow_token: Any, market: MarketState | None) -> PaperBrokerRejectionCode | None:
        if self.order_book.get(ticket.order_id):
            return PaperBrokerRejectionCode.DUPLICATE_ORDER
        if not ticket.workflow_id or not ticket.workflow_token:
            return PaperBrokerRejectionCode.MISSING_WORKFLOW_OWNERSHIP
        if str(getattr(workflow_token, "current_owner", "")) != "Trader":
            return PaperBrokerRejectionCode.INVALID_WORKFLOW_OWNER
        if str(getattr(workflow_token, "workflow_status", "")) not in {"Executing", "Ownership Transferred"}:
            return PaperBrokerRejectionCode.EXPIRED_WORKFLOW_TOKEN
        decision = dict(ticket.decision_object or {})
        decision.setdefault("workflowId", ticket.workflow_id)
        decision.setdefault("missionId", ticket.mission_id)
        decision.setdefault("workflowTokenId", ticket.workflow_token)
        provenance = validate_decision_object_for_operational_truth(decision, execution_environment="paper")
        promotion = TruthPromotionAuthority().promote_decision_object(decision, requested_consumer="Trader")
        if not provenance.valid or promotion.decision != PromotionDecisionStatus.APPROVED:
            return PaperBrokerRejectionCode.MISSING_DECISION_PROVENANCE
        if not ticket.risk_approval_id:
            return PaperBrokerRejectionCode.MISSING_RISK_APPROVAL
        if not ticket.policy_approval_id:
            return PaperBrokerRejectionCode.MISSING_POLICY_APPROVAL
        if ticket.account_id != self.account.account_id:
            return PaperBrokerRejectionCode.INVALID_ACCOUNT
        if ticket.quantity <= 0:
            return PaperBrokerRejectionCode.INVALID_QUANTITY
        if ticket.side.lower() not in {"buy", "sell"}:
            return PaperBrokerRejectionCode.INVALID_SIDE
        if ticket.order_type.lower() not in SUPPORTED_ORDER_TYPES:
            return PaperBrokerRejectionCode.INVALID_ORDER_TYPE
        if ticket.time_in_force.lower() not in SUPPORTED_TIME_IN_FORCE:
            return PaperBrokerRejectionCode.INVALID_TIME_IN_FORCE
        if ticket.asset_type.lower() not in SUPPORTED_ASSETS:
            return PaperBrokerRejectionCode.UNSUPPORTED_ASSET
        if market is None:
            return PaperBrokerRejectionCode.MARKET_DATA_UNAVAILABLE
        if ticket.side.lower() == "buy" and self._reserve_cash(ticket, market) > self.account.cash - self.account.reserved_cash:
            return PaperBrokerRejectionCode.INSUFFICIENT_BUYING_POWER
        if not _session_allows_execution(market) and ticket.order_type == "market":
            return PaperBrokerRejectionCode.MARKET_CLOSED
        return None

    def _new_order(self, ticket: PaperBrokerOrderTicket, timestamp: str, market: MarketState | None, status: str, rejection: str) -> PaperBrokerOrderRecord:
        return PaperBrokerOrderRecord(ticket.order_id, ticket, status, ("Created",), market, timestamp, timestamp, ticket.quantity, 0.0, ticket.quantity, 0.0, 0.0, rejection)

    def _event(self, order: PaperBrokerOrderRecord, event_type: str, payload: dict[str, Any]) -> BrokerEventRecord:
        timestamp = utc_timestamp()
        provenance = {
            "orderId": order.order_id,
            "decisionObjectId": order.ticket.decision_object_id,
            "workflowId": order.ticket.workflow_id,
            "missionId": order.ticket.mission_id,
            "workflowToken": order.ticket.workflow_token,
            "traderIdentity": order.ticket.trader_identity,
            "brokerAdapter": PAPER_BROKERAGE_ID,
            "truthDomain": "PAPER_OPERATIONAL",
            "executionMode": "PAPER",
            "timestamp": timestamp,
            "sourceMarketState": _json_ready(order.market_state) if order.market_state else {},
            "certificationState": "PAPER_OPERATIONAL_CERTIFIED",
            "paperLiveDesignation": "paper",
        }
        content = {"eventType": event_type, "orderId": order.order_id, "status": order.status, "provenance": provenance, "payload": payload}
        return BrokerEventRecord(_stable_id("PBE", order.order_id, event_type, str(len(order.events) + 1)), event_type, order.order_id, order.status, timestamp, provenance, payload, _hash(content))

    def _reserve_cash(self, ticket: PaperBrokerOrderTicket, market: MarketState | None) -> float:
        if ticket.side.lower() != "buy" or market is None:
            return 0.0
        reference = ticket.limit_price if ticket.order_type in {"limit", "stop_limit"} and ticket.limit_price else market.ask
        return round(ticket.quantity * reference, 4)

    def _publish(self, event: BrokerEventRecord) -> None:
        if not self.communications_bus:
            return
        self._sequence += 1
        self.communications_bus.publish_event(
            message_type="ENTERPRISE_ACTIVITY_EVENT",
            source_service_id="Paper Brokerage",
            source_office_id="Trader",
            payload={"summary": event.event_type, "severity": "INFO", "brokerEvent": _json_ready(event)},
            workflow_id=event.provenance["workflowId"],
            mission_id=event.provenance["missionId"],
            decision_object_id=event.provenance["decisionObjectId"],
            order_id=event.order_id,
            paper_live_mode=MessageMode.PAPER,
            ordering_key=event.order_id,
            sequence_number=self._sequence,
            idempotency_key=event.event_id,
        )

    def _record_order_management_message(self, order: PaperBrokerOrderRecord, event: BrokerEventRecord, case_file_id: str, trade_cycle_id: str, document_sequence: int) -> None:
        if not self.order_management.managed_order(order.order_id):
            return
        message = BrokerOrderMessage(event.event_id, order.order_id, event.event_type, order.requested_quantity, order.filled_quantity, order.remaining_quantity, order.average_fill_price, order.status, event.timestamp_utc)
        self.order_management.record_broker_message(order.order_id, message, case_file_id, trade_cycle_id, document_sequence)
        for fill in order.fills:
            self.order_management.record_fill(order.order_id, OrderFillRecord(fill.fill_id, order.order_id, fill.quantity, fill.price, fill.timestamp_utc, event.event_id), case_file_id, trade_cycle_id, document_sequence + 1)

    def _record_performance_truth(self, order: PaperBrokerOrderRecord) -> None:
        if self.performance_truth and hasattr(self.performance_truth, "record_broker_authoritative_order"):
            source_event = order.events[-1].event_id if order.events else order.order_id
            envelope = make_paper_operational_truth_envelope(
                originating_authority="DeterministicPaperBrokerage",
                originating_workflow_id=order.ticket.workflow_id,
                workflow_token_id=order.ticket.workflow_token,
                mission_id=order.ticket.mission_id,
                source_event_id=source_event,
                idempotency_key=order.order_id,
                timestamp_utc=order.updated_at,
                caller="PerformanceTruthEngine",
                source_system=PAPER_BROKERAGE_ID,
            )
            self.performance_truth.record_broker_authoritative_order(_json_ready(order), truth_envelope=envelope)

    def _record_execution_quality(self, order: PaperBrokerOrderRecord, case_file_id: str, trade_cycle_id: str, document_sequence: int) -> None:
        if not self.execution_quality or not order.fills:
            return
        market = order.market_state
        fill = order.fills[-1]
        self.execution_quality.evaluate_execution(
            CompletedExecutionRecord(
                execution_record_id=_stable_id("EXREC", order.order_id),
                executive_decision_id=order.ticket.risk_approval_id if order.ticket.risk_approval_id.startswith("DOC-") else "DOC-001",
                execution_strategy_id=order.ticket.strategy_id or order.ticket.execution_plan_id,
                order_id=order.order_id,
                broker_id=PAPER_BROKERAGE_ID,
                broker_execution_id=fill.execution_id,
                market_condition_id=market.replay_identifier if market else "",
                position_id=f"POS-{order.ticket.symbol}",
                audit_id="DOC-003",
                requested_price=order.ticket.limit_price or (market.ask if market and order.ticket.side == "buy" else market.bid if market else fill.price),
                requested_quantity=order.requested_quantity,
                average_fill_price=order.average_fill_price,
                filled_quantity=order.filled_quantity,
                best_available_market_price=market.ask if market and order.ticket.side == "buy" else market.bid if market else fill.price,
                bid_ask_spread=round((market.ask - market.bid), 4) if market else 0.0,
                fill_latency_ms=0,
                order_completion_time_ms=0,
                commission_cost=sum(item.commission for item in order.fills),
                fees=0.0,
                realized_market_impact=sum(item.slippage for item in order.fills),
                asset_class=order.ticket.asset_type,
                exchange="PAPER",
                liquidity_regime="normal",
                volatility_regime="contained",
                time_of_day=market.session if market else "unknown",
                order_type=order.ticket.order_type,
            ),
            case_file_id,
            trade_cycle_id,
            document_sequence,
        )

    def _notify_position_monitoring(self) -> None:
        if not self.position_monitoring or not self.performance_truth:
            return
        snapshot = self.performance_truth.snapshot(execution_environment="paper")
        provider = self.market_data.provider.snapshot(timestamp_utc=utc_timestamp())
        self.position_monitoring.scan(position_registry=snapshot.get("positionRegistry", {}), market_data_provider=provider, performance_truth=snapshot)

    def _require_order(self, order_id: str) -> PaperBrokerOrderRecord:
        order = self.order_book.get(order_id)
        if order is None:
            raise ValueError(f"unknown broker order: {order_id}")
        return order


def _limit_executable(ticket: PaperBrokerOrderTicket, market: MarketState) -> bool:
    return market.ask <= ticket.limit_price if ticket.side == "buy" else market.bid >= ticket.limit_price


def _stop_triggered(ticket: PaperBrokerOrderTicket, market: MarketState) -> bool:
    return market.last >= ticket.stop_price if ticket.side == "buy" else market.last <= ticket.stop_price


def _session_allows_execution(market: MarketState) -> bool:
    return market.session.upper() in {"PAPER_OPEN", "REPLAY_OPEN", "REGULAR", "OPEN"}


def _slippage(ticket: PaperBrokerOrderTicket, market: MarketState, quantity: float) -> float:
    spread = max(0.0, market.ask - market.bid)
    participation = min(1.0, quantity / max(1.0, market.volume))
    return round((spread / 2) * (0.1 + participation), 4)


def _commission(ticket: PaperBrokerOrderTicket, quantity: float, price: float) -> float:
    if ticket.asset_type.lower() in {"stock", "equity", "etf", "crypto"}:
        return 0.0
    return round(max(0.65, quantity * price * 0.0001), 4)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()[:12].upper()
    return f"{prefix}-{digest}"


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_json_ready(value), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_json_ready(item) for item in value)
    return value
