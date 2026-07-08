"""Position Management Office."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository

from .offices import TRADER_GROUP_ID


POSITION_MANAGEMENT_OFFICE_ID = "TRADER-OFFICE-005"
POSITION_MANAGEMENT_STAFF_ID = "STF-065"


class PositionLifecycleState(str, Enum):
    """Authoritative position lifecycle states."""

    CREATED = "created"
    ACCUMULATING = "accumulating"
    OPEN = "open"
    ADJUSTED = "adjusted"
    REDUCING = "reducing"
    CLOSED = "closed"
    ARCHIVED = "archived"


class PositionDirection(str, Enum):
    """Supported position directions."""

    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True)
class PositionExecutionEvent:
    """Execution event consumed by PMO."""

    execution_event_id: str
    order_id: str
    position_id: str
    asset_identifier: str
    portfolio_id: str
    strategy_id: str
    executive_decision_id: str
    quantity: float
    price: float
    side: str
    timestamp_utc: str
    audit_id: str
    asset_class: str = "equity"


@dataclass(frozen=True)
class BrokerPositionRecord:
    """Broker-side position record used for reconciliation."""

    broker_id: str
    position_id: str
    quantity: float
    average_cost_basis: float
    market_value: float
    timestamp_utc: str


@dataclass(frozen=True)
class PositionStateTransition:
    """Immutable position transition."""

    transition_id: str
    position_id: str
    from_state: PositionLifecycleState
    to_state: PositionLifecycleState
    triggering_event: str
    timestamp_utc: str
    audit_id: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class PositionRecord:
    """Authoritative enterprise position record."""

    position_id: str
    asset_identifier: str
    portfolio_id: str
    strategy_id: str
    executive_decision_id: str
    average_cost_basis: float
    quantity: float
    market_value: float
    realized_pnl: float
    unrealized_pnl: float
    exposure: float
    position_status: PositionLifecycleState
    creation_timestamp_utc: str
    last_update_timestamp_utc: str
    audit_identifier: str
    direction: PositionDirection
    asset_class: str
    history: tuple[PositionStateTransition, ...]

    def to_payload(self) -> dict[str, object]:
        return _json_ready(self)


@dataclass(frozen=True)
class PortfolioState:
    """Current portfolio state publication."""

    portfolio_id: str
    positions: tuple[PositionRecord, ...]
    total_market_value: float
    total_exposure: float
    total_realized_pnl: float
    total_unrealized_pnl: float


@dataclass(frozen=True)
class PositionManagementAnomaly:
    """PMO anomaly."""

    anomaly_id: str
    classification: str
    severity: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class PositionManagementCaseFile:
    """Case file for PMO anomalies."""

    case_file_id: str
    position_id: str
    anomalies: tuple[PositionManagementAnomaly, ...]
    reconstructable: bool


@dataclass(frozen=True)
class PositionManagementSystemPrompt:
    """PMO governing prompt artifact."""

    prompt_id: str
    version: str
    prompt_text: str


class PositionLifecycleEngine:
    """Apply deterministic position lifecycle transitions."""

    def transition(self, position: PositionRecord, to_state: PositionLifecycleState, event_id: str, audit_id: str) -> PositionRecord:
        to_state = PositionLifecycleState(to_state)
        transition = PositionStateTransition(
            f"PST-{len(position.history) + 1:06d}",
            position.position_id,
            position.position_status,
            to_state,
            event_id,
            utc_timestamp(),
            audit_id,
            {"responsible_office": POSITION_MANAGEMENT_OFFICE_ID},
        )
        return PositionRecord(
            position.position_id,
            position.asset_identifier,
            position.portfolio_id,
            position.strategy_id,
            position.executive_decision_id,
            position.average_cost_basis,
            position.quantity,
            position.market_value,
            position.realized_pnl,
            position.unrealized_pnl,
            position.exposure,
            to_state,
            position.creation_timestamp_utc,
            transition.timestamp_utc,
            position.audit_identifier,
            position.direction,
            position.asset_class,
            (*position.history, transition),
        )


class PositionAccountingEngine:
    """Apply execution events to position accounting."""

    def apply(self, position: PositionRecord | None, event: PositionExecutionEvent, market_price: float) -> PositionRecord:
        direction = PositionDirection.LONG if event.side in {"buy", "cover"} else PositionDirection.SHORT
        signed_quantity = event.quantity if event.side in {"buy", "cover"} else -event.quantity
        created = utc_timestamp()
        if position is None:
            quantity = signed_quantity
            avg_cost = event.price
            realized = 0.0
            creation_time = created
            history: tuple[PositionStateTransition, ...] = ()
        else:
            quantity, avg_cost, realized = self._apply_existing(position, signed_quantity, event.price)
            realized = round(position.realized_pnl + realized, 4)
            creation_time = position.creation_timestamp_utc
            history = position.history
            direction = position.direction
        market_value = round(quantity * market_price, 4)
        unrealized = round((market_price - avg_cost) * quantity, 4)
        exposure = round(abs(market_value), 4)
        state = _state_for_quantity(position, quantity, signed_quantity)
        record = PositionRecord(
            event.position_id,
            event.asset_identifier,
            event.portfolio_id,
            event.strategy_id,
            event.executive_decision_id,
            round(avg_cost, 4),
            round(quantity, 4),
            market_value,
            realized,
            unrealized,
            exposure,
            state,
            creation_time,
            created,
            event.audit_id,
            direction,
            event.asset_class,
            history,
        )
        return PositionLifecycleEngine().transition(record, state, event.execution_event_id, event.audit_id)

    def _apply_existing(self, position: PositionRecord, signed_quantity: float, price: float) -> tuple[float, float, float]:
        old_quantity = position.quantity
        new_quantity = old_quantity + signed_quantity
        if old_quantity == 0 or (old_quantity > 0 and signed_quantity > 0) or (old_quantity < 0 and signed_quantity < 0):
            total_cost = abs(old_quantity) * position.average_cost_basis + abs(signed_quantity) * price
            total_quantity = abs(old_quantity) + abs(signed_quantity)
            return new_quantity, total_cost / total_quantity if total_quantity else 0.0, 0.0
        closing_quantity = min(abs(old_quantity), abs(signed_quantity))
        realized = (price - position.average_cost_basis) * closing_quantity * (1 if old_quantity > 0 else -1)
        avg_cost = position.average_cost_basis if new_quantity != 0 else 0.0
        return new_quantity, avg_cost, realized


def _state_for_quantity(position: PositionRecord | None, quantity: float, signed_quantity: float) -> PositionLifecycleState:
    if quantity == 0:
        return PositionLifecycleState.CLOSED
    if position is None:
        return PositionLifecycleState.CREATED
    if abs(quantity) > abs(position.quantity):
        return PositionLifecycleState.ACCUMULATING
    if abs(quantity) < abs(position.quantity):
        return PositionLifecycleState.REDUCING
    return PositionLifecycleState.ADJUSTED


class PositionReconciliationEngine:
    """Reconcile ARGOS positions with broker records."""

    def reconcile(self, position: PositionRecord, broker: BrokerPositionRecord) -> tuple[PositionManagementAnomaly, ...]:
        anomalies = []
        if broker.position_id != position.position_id:
            anomalies.append(_anomaly("broker_disagreement", "high", f"broker_position:{broker.position_id}"))
        if round(broker.quantity, 4) != round(position.quantity, 4):
            anomalies.append(_anomaly("quantity_error", "high", f"{broker.quantity}!={position.quantity}"))
        if abs(broker.average_cost_basis - position.average_cost_basis) > 0.01:
            anomalies.append(_anomaly("cost_basis_error", "medium", f"{broker.average_cost_basis}!={position.average_cost_basis}"))
        if abs(broker.market_value - position.market_value) > 1.0:
            anomalies.append(_anomaly("position_mismatch", "high", f"{broker.market_value}!={position.market_value}"))
        return tuple(anomalies)


class PositionMonitor:
    """Monitor position integrity and limits."""

    def inspect(self, position: PositionRecord, portfolio_exposure: float, seen_position_ids: tuple[str, ...]) -> tuple[PositionManagementAnomaly, ...]:
        anomalies = []
        if position.position_id in seen_position_ids:
            anomalies.append(_anomaly("duplicate_position", "high", position.position_id))
        if position.quantity != 0 and position.average_cost_basis <= 0:
            anomalies.append(_anomaly("cost_basis_error", "high", "non_positive_cost_basis"))
        if abs(position.exposure) > 1_000_000:
            anomalies.append(_anomaly("unexpected_exposure", "high", f"exposure:{position.exposure}"))
        if abs(position.quantity * position.average_cost_basis - position.market_value) > max(10.0, abs(position.market_value) * 0.5):
            anomalies.append(_anomaly("position_drift", "medium", "market_value_deviates_from_cost_reference"))
        if portfolio_exposure > 5_000_000:
            anomalies.append(_anomaly("concentration_limit_breach", "high", f"portfolio_exposure:{portfolio_exposure}"))
        return tuple(anomalies)


class PositionManagementOffice:
    """Authoritative enterprise source of truth for positions."""

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
        self.accounting = PositionAccountingEngine()
        self.reconciliation = PositionReconciliationEngine()
        self.monitor = PositionMonitor()
        self._positions: dict[str, PositionRecord] = {}

    def apply_execution_event(
        self,
        event: PositionExecutionEvent,
        market_price: float,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Apply an execution event to a position and emit PMO records."""
        self.configuration_service.validate_startup()
        existing = self._positions.get(event.position_id)
        updated = self.accounting.apply(existing, event, market_price)
        seen = tuple(position_id for position_id in self._positions if position_id != event.position_id)
        self._positions[event.position_id] = updated
        portfolio = self.publish_portfolio_state(updated.portfolio_id)
        anomalies = self.monitor.inspect(updated, portfolio.total_exposure, seen)
        artifacts = {
            "position_record": self._position_contract(updated, portfolio, case_file_id, trade_cycle_id, document_sequence),
            "portfolio_state": self._portfolio_contract(portfolio, case_file_id, trade_cycle_id, document_sequence + 1),
        }
        if anomalies:
            artifacts["position_management_case_file"] = self.generate_case_file(updated.position_id, anomalies, case_file_id, trade_cycle_id, document_sequence + 2)
        return artifacts

    def reconcile_with_broker(
        self,
        position_id: str,
        broker_record: BrokerPositionRecord,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Reconcile one ARGOS position with a broker record."""
        if position_id not in self._positions:
            return self.generate_case_file(position_id, (_anomaly("missing_execution", "high", position_id),), case_file_id, trade_cycle_id, document_sequence)
        anomalies = self.reconciliation.reconcile(self._positions[position_id], broker_record)
        if anomalies:
            return self.generate_case_file(position_id, anomalies, case_file_id, trade_cycle_id, document_sequence)
        payload = {
            "office_id": POSITION_MANAGEMENT_OFFICE_ID,
            "office_name": "Position Management Office",
            "reconciliation_status": "reconciled",
            "position": self._positions[position_id],
            "broker_record": broker_record,
        }
        return self._persist_contract("POSITION_RECONCILIATION", case_file_id, trade_cycle_id, document_sequence, (self._positions[position_id].audit_identifier,), "Position reconciliation record.", payload)

    def close_position(
        self,
        position_id: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Close and archive a zero-quantity position."""
        if position_id not in self._positions:
            raise ValueError(f"unknown position: {position_id}")
        position = self._positions[position_id]
        if position.quantity != 0:
            raise ValueError("only zero-quantity positions can be closed")
        archived = PositionLifecycleEngine().transition(position, PositionLifecycleState.ARCHIVED, "position_archive", position.audit_identifier)
        self._positions[position_id] = archived
        return self._position_contract(archived, self.publish_portfolio_state(archived.portfolio_id), case_file_id, trade_cycle_id, document_sequence)

    def publish_portfolio_state(self, portfolio_id: str) -> PortfolioState:
        """Publish current portfolio state."""
        positions = tuple(position for position in self._positions.values() if position.portfolio_id == portfolio_id)
        return PortfolioState(
            portfolio_id,
            positions,
            round(sum(position.market_value for position in positions), 4),
            round(sum(position.exposure for position in positions), 4),
            round(sum(position.realized_pnl for position in positions), 4),
            round(sum(position.unrealized_pnl for position in positions), 4),
        )

    def position(self, position_id: str) -> PositionRecord | None:
        """Return authoritative position record."""
        return self._positions.get(position_id)

    def generate_case_file(
        self,
        position_id: str,
        anomalies: tuple[PositionManagementAnomaly, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Generate a Position Management Case File."""
        payload = {
            "office_id": POSITION_MANAGEMENT_OFFICE_ID,
            "office_name": "Position Management Office",
            "case_file": PositionManagementCaseFile(f"PMCF-{document_sequence:06d}", position_id, anomalies, True),
            "synchronization_sources": ("Executions", "Orders", "Positions", "Portfolios", "Risk Office", "Trader Group", "Historian Group", "Audit Records"),
            "history_overwritten": False,
            "state_transition_loss_detected": False,
        }
        return self._persist_contract("POSITION_CASE_FILE", case_file_id, trade_cycle_id, document_sequence, (), "Position Management Case File.", payload)

    def system_prompt(self) -> PositionManagementSystemPrompt:
        """Return PMO governing prompt."""
        return PositionManagementSystemPrompt(
            "PROMPT-PMO-057",
            "1.0.0",
            (
                "You are the Position Management Office (PMO) of ARGOS. Maintain the authoritative record of every "
                "financial position throughout its lifecycle. Do not determine what should be traded, execute trades, "
                "or perform investment analysis. Construct, maintain, reconcile, monitor, and archive every enterprise "
                "position while preserving complete history, deterministic synchronization, and permanent traceability."
            ),
        )

    def _position_contract(self, position: PositionRecord, portfolio: PortfolioState, case_file_id: str, trade_cycle_id: str, document_sequence: int) -> OperationalContract:
        payload = {
            "office_id": POSITION_MANAGEMENT_OFFICE_ID,
            "office_name": "Position Management Office",
            "position_management_system_prompt": self.system_prompt(),
            "position": position,
            "portfolio_state": portfolio,
            "history_overwritten": False,
            "position_reconstructable": True,
        }
        return self._persist_contract("POSITION_RECORD", case_file_id, trade_cycle_id, document_sequence, (position.audit_identifier,), "Authoritative position record.", payload)

    def _portfolio_contract(self, portfolio: PortfolioState, case_file_id: str, trade_cycle_id: str, document_sequence: int) -> OperationalContract:
        payload = {
            "office_id": POSITION_MANAGEMENT_OFFICE_ID,
            "office_name": "Position Management Office",
            "portfolio_state": portfolio,
        }
        return self._persist_contract("PORTFOLIO_STATE", case_file_id, trade_cycle_id, document_sequence, (), "Current portfolio state.", payload)

    def _persist_contract(
        self,
        contract_type: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        parent_contract_ids: tuple[str, ...],
        human_summary: str,
        payload: dict[str, Any],
    ) -> OperationalContract:
        contract = _contract(contract_type, case_file_id, trade_cycle_id, document_sequence, parent_contract_ids, human_summary, payload)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        return contract


def _anomaly(classification: str, severity: str, evidence: str) -> PositionManagementAnomaly:
    return PositionManagementAnomaly(
        f"PMA-{hashlib.sha256(f'{classification}:{evidence}'.encode('utf-8')).hexdigest()[:8].upper()}",
        classification,
        severity,
        (evidence,),
    )


def _contract(
    contract_type: str,
    case_file_id: str,
    trade_cycle_id: str,
    document_sequence: int,
    parent_contract_ids: tuple[str, ...],
    human_summary: str,
    payload: dict[str, Any],
) -> OperationalContract:
    created = utc_timestamp()
    normalized_payload = _json_ready(payload)
    signature_hash = hashlib.sha256(json.dumps(normalized_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id=generate_document_id(document_sequence),
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=case_file_id,
        trade_cycle_id=trade_cycle_id,
        parent_contract_ids=parent_contract_ids,
        produced_by_staff_id=POSITION_MANAGEMENT_STAFF_ID,
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
