"""ARGOS Control Panel operational controls."""

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

from .override import HumanAuthority, HumanOverrideService, OverrideAction


CONTROL_PANEL_STAFF_ID = "STF-094"
CONTROL_PANEL_GROUP_ID = "DEP-002"


class ControlAction(str, Enum):
    """User-facing ARGOS control action."""

    INITIATE_PAPER_TRADING = "initiate_paper_trading"
    HALT_PAPER_TRADING = "halt_paper_trading"
    DEPOSIT_USER_FUNDS = "deposit_user_funds"
    HALT_USER_FUNDS = "halt_user_funds"
    INITIATE_REAL_WORLD_TRADING = "initiate_real_world_trading"
    HALT_REAL_WORLD_TRADING = "halt_real_world_trading"


class ControlActionStatus(str, Enum):
    """Control action status."""

    APPLIED = "applied"
    DENIED = "denied"


@dataclass(frozen=True)
class TreasuryTransaction:
    """Active treasury transaction record."""

    transaction_id: str
    user_id: str
    amount_usd: float
    halted: bool
    reason: str
    timestamp_utc: str


@dataclass(frozen=True)
class RealWorldTradingGate:
    """Explicit gate requirements for real-world trading."""

    user_approval: bool
    broker_controls_verified: bool
    risk_certification_verified: bool
    treasury_funded: bool
    human_override_clear: bool
    live_trading_configuration_authorized: bool

    @property
    def satisfied(self) -> bool:
        """Return whether all live-trading gates are satisfied."""
        return all(
            (
                self.user_approval,
                self.broker_controls_verified,
                self.risk_certification_verified,
                self.treasury_funded,
                self.human_override_clear,
                self.live_trading_configuration_authorized,
            )
        )

    def missing(self) -> tuple[str, ...]:
        """Return missing gate labels."""
        labels = (
            ("user_approval", self.user_approval),
            ("broker_controls_verified", self.broker_controls_verified),
            ("risk_certification_verified", self.risk_certification_verified),
            ("treasury_funded", self.treasury_funded),
            ("human_override_clear", self.human_override_clear),
            ("live_trading_configuration_authorized", self.live_trading_configuration_authorized),
        )
        return tuple(name for name, passed in labels if not passed)


@dataclass(frozen=True)
class ControlPanelActionRecord:
    """Immutable control panel action record."""

    action_id: str
    action: ControlAction
    status: ControlActionStatus
    authorized_by: str
    reason: str
    timestamp_utc: str
    resulting_state: dict[str, object]
    denial_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class ControlPanelSnapshot:
    """Immediately visible ARGOS control panel snapshot."""

    snapshot_id: str
    paper_trading_active: bool
    active_treasury_balance_usd: float
    user_funds_halted: bool
    real_world_trading_active: bool
    real_world_trading_blocked: bool
    latest_action_id: str | None
    visible_to_user: bool


class ARGOSControlPanel:
    """User-facing operational control panel."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        override_service: HumanOverrideService,
    ) -> None:
        self.configuration_service = configuration_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self.override_service = override_service
        self.paper_trading_active = False
        self.user_funds_halted = False
        self.real_world_trading_active = False
        self.active_treasury_balance_usd = 0.0
        self._actions: list[ControlPanelActionRecord] = []
        self._treasury_transactions: list[TreasuryTransaction] = []

    @property
    def actions(self) -> tuple[ControlPanelActionRecord, ...]:
        """Return immutable control action history."""
        return tuple(self._actions)

    @property
    def treasury_transactions(self) -> tuple[TreasuryTransaction, ...]:
        """Return immutable treasury transaction history."""
        return tuple(self._treasury_transactions)

    def initiate_paper_trading_self_training(self, authority: HumanAuthority, reason: str) -> ControlPanelActionRecord:
        """Initiate paper trading for ARGOS self-training."""
        if self.override_service.trading_paused:
            self.override_service.resume(authority, "Resume trading pause for paper self-training.")
        self.configuration_service.switch_environment("paper_trading")
        self.paper_trading_active = True
        return self._record(ControlAction.INITIATE_PAPER_TRADING, ControlActionStatus.APPLIED, authority, reason, ())

    def halt_paper_trading_self_training(self, authority: HumanAuthority, reason: str) -> ControlPanelActionRecord:
        """Halt paper trading for ARGOS self-training."""
        self.paper_trading_active = False
        self.override_service.apply_override(OverrideAction.TRADING_PAUSE, authority, reason)
        return self._record(ControlAction.HALT_PAPER_TRADING, ControlActionStatus.APPLIED, authority, reason, ())

    def deposit_user_funds_to_active_treasury(
        self,
        authority: HumanAuthority,
        user_id: str,
        amount_usd: float,
        reason: str,
    ) -> ControlPanelActionRecord:
        """Deposit user funds into active treasury."""
        denial = []
        if self.user_funds_halted:
            denial.append("user_funds_deposits_halted")
        if amount_usd <= 0:
            denial.append("amount_must_be_positive")
        if denial:
            return self._record(ControlAction.DEPOSIT_USER_FUNDS, ControlActionStatus.DENIED, authority, reason, tuple(denial))
        transaction = TreasuryTransaction(
            f"TTX-{len(self._treasury_transactions) + 1:06d}",
            user_id,
            round(float(amount_usd), 2),
            False,
            reason,
            utc_timestamp(),
        )
        self._treasury_transactions.append(transaction)
        self.active_treasury_balance_usd = round(self.active_treasury_balance_usd + transaction.amount_usd, 2)
        return self._record(ControlAction.DEPOSIT_USER_FUNDS, ControlActionStatus.APPLIED, authority, reason, ())

    def halt_user_funds_into_active_treasury(self, authority: HumanAuthority, reason: str) -> ControlPanelActionRecord:
        """Halt user fund deposits into active treasury."""
        self.user_funds_halted = True
        transaction = TreasuryTransaction(
            f"TTX-{len(self._treasury_transactions) + 1:06d}",
            authority.authority_id,
            0.0,
            True,
            reason,
            utc_timestamp(),
        )
        self._treasury_transactions.append(transaction)
        return self._record(ControlAction.HALT_USER_FUNDS, ControlActionStatus.APPLIED, authority, reason, ())

    def initiate_real_world_trading_from_active_treasury(
        self,
        authority: HumanAuthority,
        gates: RealWorldTradingGate,
        reason: str,
    ) -> ControlPanelActionRecord:
        """Request real-world trading activation from active treasury."""
        denial = list(gates.missing())
        if self.override_service.trading_paused or self.override_service.organization_locked or self.override_service.read_only_mode:
            denial.append("human_override_blocks_trading")
        if self.configuration_service.configuration.live_trading_enabled is False:
            denial.append("configuration_live_trading_disabled")
        if denial:
            self.real_world_trading_active = False
            return self._record(ControlAction.INITIATE_REAL_WORLD_TRADING, ControlActionStatus.DENIED, authority, reason, tuple(sorted(set(denial))))
        self.real_world_trading_active = True
        return self._record(ControlAction.INITIATE_REAL_WORLD_TRADING, ControlActionStatus.APPLIED, authority, reason, ())

    def halt_real_world_trading(self, authority: HumanAuthority, reason: str) -> ControlPanelActionRecord:
        """Halt real-world trading."""
        self.real_world_trading_active = False
        self.override_service.apply_override(OverrideAction.TRADING_PAUSE, authority, reason)
        return self._record(ControlAction.HALT_REAL_WORLD_TRADING, ControlActionStatus.APPLIED, authority, reason, ())

    def visible_snapshot(self) -> ControlPanelSnapshot:
        """Return immediately visible dashboard state."""
        latest = self._actions[-1].action_id if self._actions else None
        return ControlPanelSnapshot(
            f"CPS-{len(self._actions):06d}",
            self.paper_trading_active,
            self.active_treasury_balance_usd,
            self.user_funds_halted,
            self.real_world_trading_active,
            not self.real_world_trading_active,
            latest,
            True,
        )

    def _record(
        self,
        action: ControlAction,
        status: ControlActionStatus,
        authority: HumanAuthority,
        reason: str,
        denial_reasons: tuple[str, ...],
    ) -> ControlPanelActionRecord:
        record = ControlPanelActionRecord(
            f"CPA-{len(self._actions) + 1:06d}",
            action,
            status,
            authority.authority_id,
            reason,
            utc_timestamp(),
            _json_ready(self.visible_snapshot()),
            denial_reasons,
        )
        self._actions.append(record)
        self._persist_and_audit(record)
        return record

    def _persist_and_audit(self, record: ControlPanelActionRecord) -> None:
        contract = _control_contract(record)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_staff_decision(
            contract,
            staff_id=CONTROL_PANEL_STAFF_ID,
            group_id=CONTROL_PANEL_GROUP_ID,
            decision=record.action.value,
            rationale=record.reason,
        )


def _control_contract(record: ControlPanelActionRecord) -> OperationalContract:
    created = utc_timestamp()
    payload = _json_ready(record)
    signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    sequence = int(record.action_id.split("-")[1])
    return OperationalContract(
        contract_id=generate_document_id(8700 + sequence),
        contract_type="ARGOS_CONTROL_PANEL_ACTION",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id=CONTROL_PANEL_STAFF_ID,
        produced_by_group_id=CONTROL_PANEL_GROUP_ID,
        intended_consumer_group_id=CONTROL_PANEL_GROUP_ID,
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=f"ARGOS control panel action {record.action_id}: {record.action.value}.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {_json_ready(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
