"""Human Override and Kill Switch framework."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json

from argos.foundation.audit import AuditService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id, validate_identifier, IdentifierKind
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType


class OverrideLevel(int, Enum):
    """Human override levels 0-6."""

    LEVEL_0_NORMAL = 0
    LEVEL_1_EXECUTIVE_PAUSE = 1
    LEVEL_2_TRADING_PAUSE = 2
    LEVEL_3_READ_ONLY_MODE = 3
    LEVEL_4_REPLAY_MODE = 4
    LEVEL_5_ORGANIZATION_LOCKDOWN = 5
    LEVEL_6_EMERGENCY_LIQUIDATION = 6


class OverrideAction(str, Enum):
    """Supported override actions."""

    EXECUTIVE_PAUSE = "executive_pause"
    TRADING_PAUSE = "trading_pause"
    ORGANIZATION_LOCKDOWN = "organization_lockdown"
    EMERGENCY_LIQUIDATION = "emergency_liquidation"
    REPLAY_MODE = "replay_mode"
    READ_ONLY_MODE = "read_only_mode"
    RESUME = "resume"


@dataclass(frozen=True)
class HumanAuthority:
    """Authorized human override authority."""

    authority_id: str
    staff_id: str
    max_level: OverrideLevel

    def __post_init__(self) -> None:
        result = validate_identifier(self.staff_id)
        if not result.is_valid or result.kind != IdentifierKind.STAFF:
            raise ValueError("human authority staff_id must be a valid Staff ID")
        if not isinstance(self.max_level, OverrideLevel):
            object.__setattr__(self, "max_level", OverrideLevel(self.max_level))


@dataclass(frozen=True)
class HumanOverrideRecord:
    """Immutable human override record."""

    override_id: str
    action: OverrideAction
    level: OverrideLevel
    authorized_by: HumanAuthority
    reason: str
    created_timestamp_utc: str
    active: bool

    def __post_init__(self) -> None:
        if not isinstance(self.action, OverrideAction):
            object.__setattr__(self, "action", OverrideAction(self.action))
        if not isinstance(self.level, OverrideLevel):
            object.__setattr__(self, "level", OverrideLevel(self.level))
        if not self.reason.strip():
            raise ValueError("override reason is required")

    def to_payload(self) -> dict[str, object]:
        """Serialize for persistence/audit."""
        return {
            "override_id": self.override_id,
            "action": self.action.value,
            "level": self.level.value,
            "authorized_by": self.authorized_by.authority_id,
            "authorized_staff_id": self.authorized_by.staff_id,
            "reason": self.reason,
            "created_timestamp_utc": self.created_timestamp_utc,
            "active": self.active,
        }


class HumanOverrideService:
    """Authorized human override and kill switch service."""

    def __init__(
        self,
        audit_service: AuditService,
        persistence_repository: InMemoryPersistenceRepository,
    ) -> None:
        self.audit_service = audit_service
        self.persistence_repository = persistence_repository
        self._records: list[HumanOverrideRecord] = []
        self.current_level = OverrideLevel.LEVEL_0_NORMAL
        self.read_only_mode = False
        self.replay_mode = False
        self.executive_paused = False
        self.trading_paused = False
        self.organization_locked = False
        self.emergency_liquidation_active = False

    @property
    def records(self) -> tuple[HumanOverrideRecord, ...]:
        """Return immutable override history."""
        return tuple(self._records)

    def apply_override(
        self,
        action: OverrideAction,
        authority: HumanAuthority,
        reason: str,
    ) -> HumanOverrideRecord:
        """Apply an authorized override and append an immutable record."""
        level = _level_for_action(action)
        self._authorize(authority, level)
        record = HumanOverrideRecord(
            override_id=f"OVR-{len(self._records) + 1:06d}",
            action=action,
            level=level,
            authorized_by=authority,
            reason=reason,
            created_timestamp_utc=utc_timestamp(),
            active=action != OverrideAction.RESUME,
        )
        self._records.append(record)
        self._apply_state(record)
        self._persist_and_audit(record)
        return record

    def resume(self, authority: HumanAuthority, reason: str) -> HumanOverrideRecord:
        """Resume normal operation after an override."""
        self._authorize(authority, self.current_level)
        return self.apply_override(OverrideAction.RESUME, authority, reason)

    def assert_commander_allowed(self) -> None:
        """Raise if Commander actions are blocked."""
        if self.executive_paused or self.organization_locked or self.read_only_mode:
            raise PermissionError("Commander actions blocked by human override")

    def assert_courier_allowed(self) -> None:
        """Raise if Courier routing is blocked."""
        if self.organization_locked or self.read_only_mode:
            raise PermissionError("Courier routing blocked by human override")

    def assert_persistence_write_allowed(self) -> None:
        """Raise if writes are blocked."""
        if self.read_only_mode or self.replay_mode:
            raise PermissionError("Persistence writes blocked by human override")

    def _authorize(self, authority: HumanAuthority, level: OverrideLevel) -> None:
        if authority.max_level.value < level.value:
            raise PermissionError("human authority is not authorized for requested override level")

    def _apply_state(self, record: HumanOverrideRecord) -> None:
        if record.action == OverrideAction.RESUME:
            self.current_level = OverrideLevel.LEVEL_0_NORMAL
            self.read_only_mode = False
            self.replay_mode = False
            self.executive_paused = False
            self.trading_paused = False
            self.organization_locked = False
            self.emergency_liquidation_active = False
            return
        self.current_level = record.level
        self.executive_paused = record.action == OverrideAction.EXECUTIVE_PAUSE
        self.trading_paused = record.action == OverrideAction.TRADING_PAUSE
        self.organization_locked = record.action == OverrideAction.ORGANIZATION_LOCKDOWN
        self.emergency_liquidation_active = record.action == OverrideAction.EMERGENCY_LIQUIDATION
        self.replay_mode = record.action == OverrideAction.REPLAY_MODE
        self.read_only_mode = record.action == OverrideAction.READ_ONLY_MODE

    def _persist_and_audit(self, record: HumanOverrideRecord) -> None:
        payload = record.to_payload()
        self.persistence_repository.persist(
            ObjectType.OPERATIONAL_DOCUMENT,
            record.override_id.replace("OVR", "DOC"),
            {
                "contract_id": record.override_id.replace("OVR", "DOC"),
                "case_file_id": "CF-001",
                "trade_cycle_id": "TC-001",
                "override_id": record.override_id,
                "payload": payload,
            },
        )
        contract = _override_contract(record)
        self.audit_service.record_staff_decision(
            contract,
            staff_id=record.authorized_by.staff_id,
            group_id="DEP-002",
            decision=record.action.value,
            rationale=record.reason,
        )


class HumanAuthorityPanel:
    """Human-facing authority panel facade."""

    def __init__(self, override_service: HumanOverrideService, authority: HumanAuthority) -> None:
        self.override_service = override_service
        self.authority = authority

    def trigger(self, action: OverrideAction, reason: str) -> HumanOverrideRecord:
        """Trigger an override from the authority panel."""
        return self.override_service.apply_override(action, self.authority, reason)

    def resume(self, reason: str) -> HumanOverrideRecord:
        """Resume normal operation from the authority panel."""
        return self.override_service.resume(self.authority, reason)


def _level_for_action(action: OverrideAction) -> OverrideLevel:
    return {
        OverrideAction.RESUME: OverrideLevel.LEVEL_0_NORMAL,
        OverrideAction.EXECUTIVE_PAUSE: OverrideLevel.LEVEL_1_EXECUTIVE_PAUSE,
        OverrideAction.TRADING_PAUSE: OverrideLevel.LEVEL_2_TRADING_PAUSE,
        OverrideAction.READ_ONLY_MODE: OverrideLevel.LEVEL_3_READ_ONLY_MODE,
        OverrideAction.REPLAY_MODE: OverrideLevel.LEVEL_4_REPLAY_MODE,
        OverrideAction.ORGANIZATION_LOCKDOWN: OverrideLevel.LEVEL_5_ORGANIZATION_LOCKDOWN,
        OverrideAction.EMERGENCY_LIQUIDATION: OverrideLevel.LEVEL_6_EMERGENCY_LIQUIDATION,
    }[OverrideAction(action)]


def _override_contract(record: HumanOverrideRecord) -> OperationalContract:
    created = utc_timestamp()
    payload = record.to_payload()
    signature_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    sequence = int(record.override_id.split("-")[1])
    return OperationalContract(
        contract_id=generate_document_id(950 + sequence),
        contract_type="HUMAN_OVERRIDE",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id=record.authorized_by.staff_id,
        produced_by_group_id="DEP-002",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=f"Human override {record.override_id}: {record.action.value}.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )

