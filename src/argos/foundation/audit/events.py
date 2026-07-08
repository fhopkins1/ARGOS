"""Immutable audit event records."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping


class AuditEventType(str, Enum):
    """Audit event types required by EO-005."""

    DOCUMENT_CREATED = "document_created"
    MAILBOX_DEPOSITED = "mailbox_deposited"
    COURIER_TRANSFER = "courier_transfer"
    VALIDATION_RESULT = "validation_result"
    DOCUMENT_RECEIVED = "document_received"
    STAFF_DECISION = "staff_decision"


@dataclass(frozen=True)
class AuditEvent:
    """Append-only immutable audit event."""

    event_id: str
    sequence: int
    event_type: AuditEventType
    timestamp_utc: str
    case_file_id: str
    trade_cycle_id: str
    staff_id: str
    group_id: str
    document_id: str
    payload: Mapping[str, Any]
    previous_event_hash: str
    event_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, AuditEventType):
            object.__setattr__(self, "event_type", AuditEventType(self.event_type))
        object.__setattr__(self, "payload", MappingProxyType(_freeze_mapping(dict(self.payload))))
        object.__setattr__(self, "event_hash", self.compute_hash())

    def compute_hash(self) -> str:
        """Compute the deterministic hash for this event."""
        canonical = {
            "case_file_id": self.case_file_id,
            "document_id": self.document_id,
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "group_id": self.group_id,
            "payload": _json_ready(dict(self.payload)),
            "previous_event_hash": self.previous_event_hash,
            "sequence": self.sequence,
            "staff_id": self.staff_id,
            "timestamp_utc": self.timestamp_utc,
            "trade_cycle_id": self.trade_cycle_id,
        }
        encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["payload"] = _json_ready(dict(self.payload))
        return data


def _freeze_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    frozen: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            frozen[key] = MappingProxyType(_freeze_mapping(value))
        elif isinstance(value, list):
            frozen[key] = tuple(value)
        else:
            frozen[key] = value
    return frozen


def _json_ready(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value

