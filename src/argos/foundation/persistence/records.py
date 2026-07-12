"""Immutable persistent records for canonical ARGOS objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping


class ObjectType(str, Enum):
    """Canonical persisted object types required by EO-007."""

    CASE_FILE = "case_file"
    OPERATIONAL_DOCUMENT = "operational_document"
    AUDIT_EVENT = "audit_event"
    CONFIGURATION_SNAPSHOT = "configuration_snapshot"
    PROMPT_SNAPSHOT = "prompt_snapshot"
    MODEL_SNAPSHOT = "model_snapshot"
    STAFF_REGISTRY = "staff_registry"
    DEPARTMENT_REGISTRY = "department_registry"
    ENTERPRISE_RUNTIME_STATE = "enterprise_runtime_state"
    ENTERPRISE_RUNTIME_CHECKPOINT = "enterprise_runtime_checkpoint"
    ENTERPRISE_MISSION_STATE = "enterprise_mission_state"
    ENTERPRISE_WORKFLOW_STATE = "enterprise_workflow_state"
    ENTERPRISE_BROKER_STATE = "enterprise_broker_state"
    ENTERPRISE_POSITION_STATE = "enterprise_position_state"
    ENTERPRISE_PERFORMANCE_TRUTH = "enterprise_performance_truth"
    ENTERPRISE_POLICY_STATE = "enterprise_policy_state"
    ENTERPRISE_RECOVERY_AUDIT = "enterprise_recovery_audit"
    ENTERPRISE_TRANSACTION = "enterprise_transaction"


@dataclass(frozen=True)
class PersistentRecord:
    """Append-only versioned persistence record."""

    object_type: ObjectType
    object_id: str
    version: int
    schema_version: str
    payload: Mapping[str, Any]
    created_timestamp_utc: str
    previous_record_hash: str
    record_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.object_type, ObjectType):
            object.__setattr__(self, "object_type", ObjectType(self.object_type))
        object.__setattr__(self, "payload", MappingProxyType(_freeze_mapping(dict(self.payload))))
        object.__setattr__(self, "record_hash", self.compute_hash())

    def compute_hash(self) -> str:
        """Compute the deterministic record hash."""
        canonical = {
            "created_timestamp_utc": self.created_timestamp_utc,
            "object_id": self.object_id,
            "object_type": self.object_type.value,
            "payload": _json_ready(dict(self.payload)),
            "previous_record_hash": self.previous_record_hash,
            "schema_version": self.schema_version,
            "version": self.version,
        }
        encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialize this record to a JSON-compatible dictionary."""
        return {
            "created_timestamp_utc": self.created_timestamp_utc,
            "object_id": self.object_id,
            "object_type": self.object_type.value,
            "payload": _json_ready(dict(self.payload)),
            "previous_record_hash": self.previous_record_hash,
            "record_hash": self.record_hash,
            "schema_version": self.schema_version,
            "version": self.version,
        }


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

