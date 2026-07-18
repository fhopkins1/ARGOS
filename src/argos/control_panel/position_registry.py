"""Position Object and Registry for ARGOS EO-XA."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from typing import Any

from argos.foundation.contracts import utc_timestamp


class PositionLifecycleStatus(str, Enum):
    """Supported constitutional Position Object lifecycle states."""

    CREATED = "created"
    PENDING_OPENING = "pending_opening"
    OPENING = "opening"
    SUBMITTED = "submitted"
    PENDING_FILL = "pending_fill"
    PARTIALLY_FILLED = "partially_filled"
    OPEN = "open"
    INCREASING = "increasing"
    REDUCING = "reducing"
    MONITORING = "monitoring"
    RISK_REVIEW = "risk_review"
    EXIT_RECOMMENDED = "exit_recommended"
    EXIT_PENDING = "exit_pending"
    CLOSING = "closing"
    CLOSED = "closed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


VALID_POSITION_TRANSITIONS: dict[PositionLifecycleStatus, tuple[PositionLifecycleStatus, ...]] = {
    PositionLifecycleStatus.CREATED: (
        PositionLifecycleStatus.PENDING_OPENING,
        PositionLifecycleStatus.OPENING,
        PositionLifecycleStatus.SUBMITTED,
        PositionLifecycleStatus.PENDING_FILL,
        PositionLifecycleStatus.PARTIALLY_FILLED,
        PositionLifecycleStatus.OPEN,
        PositionLifecycleStatus.REJECTED,
        PositionLifecycleStatus.CANCELLED,
    ),
    PositionLifecycleStatus.PENDING_OPENING: (
        PositionLifecycleStatus.OPENING,
        PositionLifecycleStatus.PARTIALLY_FILLED,
        PositionLifecycleStatus.OPEN,
        PositionLifecycleStatus.REJECTED,
        PositionLifecycleStatus.CANCELLED,
    ),
    PositionLifecycleStatus.OPENING: (
        PositionLifecycleStatus.PARTIALLY_FILLED,
        PositionLifecycleStatus.OPEN,
        PositionLifecycleStatus.REJECTED,
        PositionLifecycleStatus.CANCELLED,
    ),
    PositionLifecycleStatus.SUBMITTED: (
        PositionLifecycleStatus.PENDING_FILL,
        PositionLifecycleStatus.PARTIALLY_FILLED,
        PositionLifecycleStatus.OPEN,
        PositionLifecycleStatus.REJECTED,
        PositionLifecycleStatus.CANCELLED,
    ),
    PositionLifecycleStatus.PENDING_FILL: (
        PositionLifecycleStatus.PARTIALLY_FILLED,
        PositionLifecycleStatus.OPEN,
        PositionLifecycleStatus.REJECTED,
        PositionLifecycleStatus.CANCELLED,
    ),
    PositionLifecycleStatus.PARTIALLY_FILLED: (
        PositionLifecycleStatus.OPEN,
        PositionLifecycleStatus.INCREASING,
        PositionLifecycleStatus.REDUCING,
        PositionLifecycleStatus.EXIT_RECOMMENDED,
        PositionLifecycleStatus.EXIT_PENDING,
        PositionLifecycleStatus.CLOSING,
        PositionLifecycleStatus.CLOSED,
        PositionLifecycleStatus.CANCELLED,
    ),
    PositionLifecycleStatus.OPEN: (
        PositionLifecycleStatus.INCREASING,
        PositionLifecycleStatus.REDUCING,
        PositionLifecycleStatus.MONITORING,
        PositionLifecycleStatus.RISK_REVIEW,
        PositionLifecycleStatus.EXIT_RECOMMENDED,
        PositionLifecycleStatus.EXIT_PENDING,
        PositionLifecycleStatus.CLOSING,
        PositionLifecycleStatus.CLOSED,
    ),
    PositionLifecycleStatus.INCREASING: (
        PositionLifecycleStatus.OPEN,
        PositionLifecycleStatus.MONITORING,
        PositionLifecycleStatus.EXIT_RECOMMENDED,
        PositionLifecycleStatus.CLOSING,
    ),
    PositionLifecycleStatus.REDUCING: (
        PositionLifecycleStatus.OPEN,
        PositionLifecycleStatus.MONITORING,
        PositionLifecycleStatus.EXIT_RECOMMENDED,
        PositionLifecycleStatus.EXIT_PENDING,
        PositionLifecycleStatus.CLOSING,
        PositionLifecycleStatus.CLOSED,
    ),
    PositionLifecycleStatus.MONITORING: (
        PositionLifecycleStatus.RISK_REVIEW,
        PositionLifecycleStatus.EXIT_RECOMMENDED,
        PositionLifecycleStatus.EXIT_PENDING,
        PositionLifecycleStatus.CLOSING,
        PositionLifecycleStatus.CLOSED,
    ),
    PositionLifecycleStatus.RISK_REVIEW: (
        PositionLifecycleStatus.MONITORING,
        PositionLifecycleStatus.EXIT_RECOMMENDED,
        PositionLifecycleStatus.EXIT_PENDING,
        PositionLifecycleStatus.CLOSING,
    ),
    PositionLifecycleStatus.EXIT_RECOMMENDED: (
        PositionLifecycleStatus.EXIT_PENDING,
        PositionLifecycleStatus.CLOSING,
        PositionLifecycleStatus.MONITORING,
        PositionLifecycleStatus.CLOSED,
    ),
    PositionLifecycleStatus.EXIT_PENDING: (
        PositionLifecycleStatus.CLOSING,
        PositionLifecycleStatus.PARTIALLY_FILLED,
        PositionLifecycleStatus.REDUCING,
        PositionLifecycleStatus.CLOSED,
        PositionLifecycleStatus.CANCELLED,
    ),
    PositionLifecycleStatus.CLOSING: (
        PositionLifecycleStatus.EXIT_PENDING,
        PositionLifecycleStatus.PARTIALLY_FILLED,
        PositionLifecycleStatus.CLOSED,
        PositionLifecycleStatus.CANCELLED,
    ),
    PositionLifecycleStatus.CLOSED: (PositionLifecycleStatus.ARCHIVED,),
    PositionLifecycleStatus.REJECTED: (PositionLifecycleStatus.ARCHIVED,),
    PositionLifecycleStatus.CANCELLED: (PositionLifecycleStatus.ARCHIVED,),
    PositionLifecycleStatus.ARCHIVED: (),
}


@dataclass(frozen=True)
class PositionHistoryRecord:
    """Immutable position mutation history entry."""

    position_id: str
    timestamp: str
    previous_status: str
    new_status: str
    changed_fields: tuple[str, ...]
    reason: str
    source: str
    workflow_id: str


@dataclass(frozen=True)
class PositionValidationResult:
    """Deterministic position validation result."""

    valid: bool
    errors: tuple[str, ...]


@dataclass(frozen=True)
class PositionObject:
    """Mutable-in-the-registry constitutional representation of capital at risk."""

    position_id: str
    workflow_id: str
    decision_object_id: str
    symbol: str
    asset_type: str
    side: str
    lifecycle_status: str
    entry_thesis: str
    entry_time: str
    entry_price: float
    quantity: float
    average_cost: float
    current_price: float
    current_value: float
    unrealized_pnl: float
    realized_pnl: float
    stop_loss: float
    profit_target: float
    trailing_stop: float
    time_in_trade: str
    current_risk: float
    current_confidence: float
    market_context: dict[str, Any]
    monitoring_history: tuple[PositionHistoryRecord, ...]
    exit_conditions: tuple[str, ...]
    exit_recommendation: str
    created_at: str
    updated_at: str
    owner: str = "Enterprise"
    broker_order_ids: tuple[str, ...] = ()
    fill_ids: tuple[str, ...] = ()
    workflow_token_lineage: tuple[str, ...] = ()
    mission_id: str = ""
    trader_identity: str = ""
    account_id: str = ""
    truth_domain: str = "PAPER_OPERATIONAL"
    execution_mode: str = "PAPER"
    certification_state: str = "PAPER_OPERATIONAL_CERTIFIED"
    pending_close_quantity: float = 0.0
    available_quantity: float = 0.0
    realized_pnl_from_fills: float = 0.0
    last_valuation_provenance: dict[str, Any] | None = None


class PositionRegistry:
    """Authoritative mutation gateway for Position Objects."""

    def __init__(self) -> None:
        self._positions: dict[str, PositionObject] = {}
        self._history: list[PositionHistoryRecord] = []
        self._audit_events: list[dict[str, Any]] = []

    def create_from_execution(self, order: dict[str, Any], decision: dict[str, Any] | None = None) -> PositionObject:
        """Create or update a Position Object from a filled BUY execution."""
        decision = decision or {}
        if str(order.get("side", "")).upper() != "BUY":
            raise ValueError("create_from_execution requires BUY order")
        position_id = self._position_id(order)
        existing = self._positions.get(position_id)
        filled = float(order.get("filled_quantity", 0.0) or 0.0)
        fill_ids = _fill_ids(order)
        if filled > 0 and not fill_ids:
            self._audit("position_create_rejected", position_id, ("missing authoritative fill id",), str(order.get("workflow_id", "")))
            raise ValueError("authoritative fill id required for position mutation")
        if existing and fill_ids and set(fill_ids).issubset(set(existing.fill_ids)):
            self._audit("duplicate_fill_rejected", position_id, fill_ids, str(order.get("workflow_id", "")))
            return existing
        average_fill = float(order.get("average_fill_price", 0.0) or order.get("ask_price", 0.0) or 0.0)
        status = PositionLifecycleStatus.PARTIALLY_FILLED if str(order.get("status")) == "PARTIALLY_FILLED" else PositionLifecycleStatus.OPEN
        now = str(order.get("timestamp") or utc_timestamp())
        if existing:
            quantity = round(existing.quantity + filled, 4)
            total_cost = existing.average_cost * existing.quantity + average_fill * filled
            average_cost = round(total_cost / max(1.0, quantity), 4)
            updated = replace(
                existing,
                lifecycle_status=status.value,
                quantity=quantity,
                average_cost=average_cost,
                current_price=float(order.get("mid_price", average_fill) or average_fill),
                current_value=round(quantity * float(order.get("mid_price", average_fill) or average_fill), 4),
                unrealized_pnl=round((float(order.get("mid_price", average_fill) or average_fill) - average_cost) * quantity, 4),
                current_risk=float(decision.get("riskScore", existing.current_risk) or existing.current_risk),
                current_confidence=float(decision.get("confidence", existing.current_confidence) or existing.current_confidence),
                updated_at=now,
                broker_order_ids=tuple(dict.fromkeys((*existing.broker_order_ids, str(order.get("order_id", ""))))),
                fill_ids=tuple(dict.fromkeys((*existing.fill_ids, *fill_ids))),
                workflow_token_lineage=tuple(dict.fromkeys((*existing.workflow_token_lineage, str(order.get("token_id", ""))))),
                available_quantity=quantity,
                last_valuation_provenance={"source": "broker_buy_fill", "order_id": str(order.get("order_id", "")), "timestamp": now},
            )
            return self._store_update(existing, updated, "buy execution updated position", "PaperBrokerExecution")
        current_price = float(order.get("mid_price", average_fill) or average_fill)
        position = PositionObject(
            position_id=position_id,
            workflow_id=str(order.get("workflow_id", "")),
            decision_object_id=str(order.get("decision_object_id", "")),
            symbol=str(order.get("symbol", "")),
            asset_type=str(order.get("asset_type", "")),
            side="LONG",
            lifecycle_status=status.value,
            entry_thesis=str(decision.get("recommendation") or order.get("intended_order", {}).get("sourceRecommendation", "")),
            entry_time=now,
            entry_price=average_fill,
            quantity=filled,
            average_cost=average_fill,
            current_price=current_price,
            current_value=round(filled * current_price, 4),
            unrealized_pnl=round((current_price - average_fill) * filled, 4),
            realized_pnl=0.0,
            stop_loss=float(decision.get("stopLoss") or 0.0),
            profit_target=float(decision.get("targetPrice") or 0.0),
            trailing_stop=0.0,
            time_in_trade="0m",
            current_risk=float(decision.get("riskScore", 0.0) or 0.0),
            current_confidence=float(decision.get("confidence", 0.0) or 0.0),
            market_context=dict(decision.get("marketContext", {})) if isinstance(decision.get("marketContext"), dict) else {},
            monitoring_history=(),
            exit_conditions=tuple(item for item in ("profit_target", "stop_loss") if decision.get("targetPrice" if item == "profit_target" else "stopLoss") is not None),
            exit_recommendation="",
            created_at=now,
            updated_at=now,
            broker_order_ids=(str(order.get("order_id", "")),),
            fill_ids=fill_ids,
            workflow_token_lineage=(str(order.get("token_id", "")),),
            mission_id=str(order.get("mission_id", order.get("intended_order", {}).get("missionId", ""))),
            trader_identity=str(order.get("trader_identity", order.get("intended_order", {}).get("traderIdentity", ""))),
            account_id=str(order.get("account_id", "")),
            truth_domain=str(order.get("truth_domain", "PAPER_OPERATIONAL")),
            execution_mode=str(order.get("execution_environment", "paper")).upper(),
            certification_state=str(order.get("certification_state", "PAPER_OPERATIONAL_CERTIFIED")),
            available_quantity=filled,
            last_valuation_provenance={"source": "broker_buy_fill", "order_id": str(order.get("order_id", "")), "timestamp": now},
        )
        result = self.validate(position)
        if not result.valid:
            self._audit("position_create_rejected", position_id, result.errors, order.get("workflow_id", ""))
            raise ValueError("; ".join(result.errors))
        return self._store_create(position, "buy execution created position", "PaperBrokerExecution")

    def apply_sell_execution(self, order: dict[str, Any]) -> PositionObject:
        """Reduce or close an existing Position Object from a SELL execution."""
        position_id = self._position_id(order)
        existing = self._positions.get(position_id)
        if not existing:
            self._audit("position_sell_rejected", position_id, ("unknown position",), str(order.get("workflow_id", "")))
            raise ValueError(f"unknown position: {position_id}")
        sold = float(order.get("filled_quantity", 0.0) or 0.0)
        fill_ids = _fill_ids(order)
        if sold > 0 and not fill_ids:
            self._audit("position_sell_rejected", position_id, ("missing authoritative fill id",), str(order.get("workflow_id", "")))
            raise ValueError("authoritative fill id required for position mutation")
        if fill_ids and set(fill_ids).issubset(set(existing.fill_ids)):
            self._audit("duplicate_fill_rejected", position_id, fill_ids, str(order.get("workflow_id", "")))
            return existing
        average_fill = float(order.get("average_fill_price", 0.0) or order.get("bid_price", 0.0) or 0.0)
        quantity = round(max(0.0, existing.quantity - sold), 4)
        realized = round(existing.realized_pnl + (average_fill - existing.average_cost) * sold - float(order.get("slippage", 0.0) or 0.0), 4)
        status = PositionLifecycleStatus.CLOSED if quantity == 0 else PositionLifecycleStatus.CLOSING
        now = str(order.get("timestamp") or utc_timestamp())
        current_value = round(quantity * float(order.get("mid_price", average_fill) or average_fill), 4)
        updated = replace(
            existing,
            lifecycle_status=status.value,
            quantity=quantity,
            current_price=float(order.get("mid_price", average_fill) or average_fill),
            current_value=current_value,
            unrealized_pnl=round((float(order.get("mid_price", average_fill) or average_fill) - existing.average_cost) * quantity, 4),
            realized_pnl=realized,
            realized_pnl_from_fills=realized,
            exit_recommendation="SELL_EXECUTED",
            updated_at=now,
            broker_order_ids=tuple(dict.fromkeys((*existing.broker_order_ids, str(order.get("order_id", ""))))),
            fill_ids=tuple(dict.fromkeys((*existing.fill_ids, *fill_ids))),
            workflow_token_lineage=tuple(dict.fromkeys((*existing.workflow_token_lineage, str(order.get("token_id", ""))))),
            pending_close_quantity=round(max(0.0, existing.pending_close_quantity - sold), 4),
            available_quantity=quantity,
            last_valuation_provenance={"source": "broker_sell_fill", "order_id": str(order.get("order_id", "")), "timestamp": now},
        )
        return self._store_update(existing, updated, "sell execution reduced position", "PaperBrokerExecution")

    def update_market_price(self, position_id: str, current_price: float, *, reason: str = "mark to market", source: str = "PositionRegistry") -> PositionObject:
        position = self.position(position_id)
        value = round(position.quantity * float(current_price), 4)
        updated = replace(
            position,
            current_price=round(float(current_price), 4),
            current_value=value,
            unrealized_pnl=round((float(current_price) - position.average_cost) * position.quantity, 4),
            updated_at=utc_timestamp(),
            available_quantity=position.quantity,
            last_valuation_provenance={"source": source, "reason": reason, "timestamp": utc_timestamp()},
        )
        return self._store_update(position, updated, reason, source)

    def reserve_close_quantity(self, position_id: str, quantity: float, *, reason: str = "exit authorization", source: str = "PositionRegistry") -> PositionObject:
        """Reserve open quantity for an authorized closing order without reducing position quantity."""
        position = self.position(position_id)
        requested = round(max(0.0, float(quantity)), 4)
        available = round(max(0.0, position.quantity - position.pending_close_quantity), 4)
        if requested <= 0:
            raise ValueError("reserved close quantity must be positive")
        if requested > available:
            self._audit("close_quantity_exceeds_position", position_id, (f"{requested}>{available}",), position.workflow_id)
            raise ValueError("closing quantity exceeds available position quantity")
        updated = replace(
            position,
            lifecycle_status=PositionLifecycleStatus.EXIT_PENDING.value,
            pending_close_quantity=round(position.pending_close_quantity + requested, 4),
            available_quantity=round(available - requested, 4),
            updated_at=utc_timestamp(),
        )
        return self._store_update(position, updated, reason, source)

    def update_surveillance_state(
        self,
        position_id: str,
        *,
        current_price: float,
        time_in_trade: str,
        current_risk: float,
        current_confidence: float,
        reason: str = "surveillance state refresh",
        source: str = "PositionRegistry",
    ) -> PositionObject:
        """Update mutable surveillance fields through the registry gateway."""
        position = self.position(position_id)
        price = round(float(current_price), 4)
        value = round(position.quantity * price, 4)
        updated = replace(
            position,
            lifecycle_status=PositionLifecycleStatus.MONITORING.value if position.lifecycle_status == PositionLifecycleStatus.OPEN.value else position.lifecycle_status,
            current_price=price,
            current_value=value,
            unrealized_pnl=round((price - position.average_cost) * position.quantity, 4),
            time_in_trade=str(time_in_trade),
            current_risk=round(max(0.0, min(1.0, float(current_risk))), 4),
            current_confidence=round(max(0.0, min(1.0, float(current_confidence))), 4),
            updated_at=utc_timestamp(),
        )
        return self._store_update(position, updated, reason, source)

    def recommend_exit(self, position_id: str, exit_recommendation: str, *, reason: str = "exit decision recommended", source: str = "PositionRegistry") -> PositionObject:
        """Record an exit recommendation through the Position Registry gateway."""
        position = self.position(position_id)
        updated = replace(
            position,
            lifecycle_status=PositionLifecycleStatus.EXIT_RECOMMENDED.value,
            exit_recommendation=str(exit_recommendation),
            updated_at=utc_timestamp(),
        )
        return self._store_update(position, updated, reason, source)

    def close_position(self, position_id: str, *, reason: str = "position closed", source: str = "PositionRegistry") -> PositionObject:
        position = self.position(position_id)
        updated = replace(position, lifecycle_status=PositionLifecycleStatus.CLOSED.value, quantity=0.0, current_value=0.0, unrealized_pnl=0.0, updated_at=utc_timestamp())
        return self._store_update(position, updated, reason, source)

    def archive_position(self, position_id: str, *, reason: str = "position archived", source: str = "PositionRegistry") -> PositionObject:
        position = self.position(position_id)
        updated = replace(position, lifecycle_status=PositionLifecycleStatus.ARCHIVED.value, updated_at=utc_timestamp())
        return self._store_update(position, updated, reason, source)

    def position(self, position_id: str) -> PositionObject:
        if position_id not in self._positions:
            raise ValueError(f"unknown position: {position_id}")
        return self._positions[position_id]

    def active_positions(self) -> tuple[PositionObject, ...]:
        return tuple(position for position in self._positions.values() if position.lifecycle_status not in {PositionLifecycleStatus.CLOSED.value, PositionLifecycleStatus.ARCHIVED.value, PositionLifecycleStatus.REJECTED.value, PositionLifecycleStatus.CANCELLED.value})

    def positions_by_workflow(self, workflow_id: str) -> tuple[PositionObject, ...]:
        return tuple(position for position in self._positions.values() if position.workflow_id == workflow_id)

    def positions_by_decision_object(self, decision_object_id: str) -> tuple[PositionObject, ...]:
        return tuple(position for position in self._positions.values() if position.decision_object_id == decision_object_id)

    def command_bridge_positions(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            {
                "positionId": position.position_id,
                "workflowId": position.workflow_id,
                "decisionObjectId": position.decision_object_id,
                "symbol": position.symbol,
                "quantity": position.quantity,
                "averageCost": position.average_cost,
                "currentPrice": position.current_price,
                "unrealizedPnl": position.unrealized_pnl,
                "lifecycleStatus": position.lifecycle_status,
                "target": position.profit_target,
                "stop": position.stop_loss,
                "timeInTrade": position.time_in_trade,
                "currentRisk": position.current_risk,
                "currentConfidence": position.current_confidence,
            }
            for position in self.active_positions()
        )

    def validate(self, position: PositionObject) -> PositionValidationResult:
        errors: list[str] = []
        if not position.position_id:
            errors.append("position_id required")
        if not position.symbol:
            errors.append("symbol required")
        if not position.asset_type:
            errors.append("asset_type required")
        if position.quantity < 0:
            errors.append("quantity cannot be negative")
        if position.average_cost < 0:
            errors.append("average_cost cannot be negative")
        if abs(position.current_value - position.quantity * position.current_price) > 0.01:
            errors.append("current_value must equal quantity times current_price")
        if position.lifecycle_status == PositionLifecycleStatus.CLOSED.value and position.quantity > 0:
            errors.append("closed positions cannot retain positive quantity")
        if position.lifecycle_status in {PositionLifecycleStatus.OPEN.value, PositionLifecycleStatus.MONITORING.value} and position.quantity <= 0:
            errors.append("open positions require positive quantity")
        if not position.decision_object_id:
            errors.append("decision_object_id required for ARGOS-created position")
        return PositionValidationResult(not errors, tuple(errors))

    def snapshot(self) -> dict[str, Any]:
        return {
            "registryName": "Position Registry",
            "engineeringOrder": "EO-XA",
            "constitutionalOwnership": {
                "Analyst": "Decision Objects",
                "Trader": "Position Objects",
                "Performance Truth": "Completed outcome records",
                "Historian": "Institutional memory",
            },
            "activePositions": tuple(asdict(position) for position in self.active_positions()),
            "allPositions": tuple(asdict(position) for position in self._positions.values()),
            "positionHistory": tuple(asdict(item) for item in self._history),
            "auditEvents": tuple(self._audit_events),
            "commandBridgePositions": self.command_bridge_positions(),
            "metrics": {
                "activePositionCount": len(self.active_positions()),
                "totalPositionCount": len(self._positions),
                "historyRecordCount": len(self._history),
                "auditEventCount": len(self._audit_events),
            },
        }

    def _store_create(self, position: PositionObject, reason: str, source: str) -> PositionObject:
        history = self._history_record(position, "", position.lifecycle_status, tuple(asdict(position).keys()), reason, source)
        position = replace(position, monitoring_history=(history,))
        self._positions[position.position_id] = position
        self._history.append(history)
        return position

    def _store_update(self, previous: PositionObject, updated: PositionObject, reason: str, source: str) -> PositionObject:
        self._validate_transition(previous.lifecycle_status, updated.lifecycle_status, previous.position_id, previous.workflow_id)
        result = self.validate(updated)
        if not result.valid:
            self._audit("position_update_rejected", previous.position_id, result.errors, previous.workflow_id)
            raise ValueError("; ".join(result.errors))
        changed = tuple(key for key, value in asdict(previous).items() if key != "monitoring_history" and asdict(updated).get(key) != value)
        history = self._history_record(updated, previous.lifecycle_status, updated.lifecycle_status, changed, reason, source)
        updated = replace(updated, monitoring_history=(*previous.monitoring_history, history))
        self._positions[updated.position_id] = updated
        self._history.append(history)
        return updated

    def _validate_transition(self, previous: str, new: str, position_id: str, workflow_id: str) -> None:
        previous_status = PositionLifecycleStatus(previous)
        new_status = PositionLifecycleStatus(new)
        if previous_status == new_status:
            return
        if new_status not in VALID_POSITION_TRANSITIONS[previous_status]:
            self._audit("invalid_lifecycle_transition", position_id, (f"{previous}->{new}",), workflow_id)
            raise ValueError(f"invalid lifecycle transition: {previous}->{new}")

    def _history_record(self, position: PositionObject, previous_status: str, new_status: str, changed_fields: tuple[str, ...], reason: str, source: str) -> PositionHistoryRecord:
        return PositionHistoryRecord(position.position_id, utc_timestamp(), previous_status, new_status, tuple(sorted(changed_fields)), reason, source, position.workflow_id)

    def _audit(self, event_type: str, position_id: str, errors: tuple[str, ...], workflow_id: str) -> None:
        self._audit_events.append({"eventType": event_type, "positionId": position_id, "errors": errors, "workflowId": workflow_id, "timestamp": utc_timestamp()})

    def _position_id(self, order: dict[str, Any]) -> str:
        symbol = str(order.get("symbol", "UNKNOWN")).upper()
        decision_id = str(order.get("decision_object_id", "MANUAL"))
        return f"POS-{symbol}-{decision_id}"


def _fill_ids(order: dict[str, Any]) -> tuple[str, ...]:
    fills = order.get("fills", ()) or order.get("fill_ids", ()) or ()
    if isinstance(fills, (tuple, list)):
        values = []
        for item in fills:
            if isinstance(item, dict):
                values.append(str(item.get("fill_id", item.get("fillId", ""))))
            else:
                values.append(str(item))
        return tuple(item for item in values if item)
    return ()
