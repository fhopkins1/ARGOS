"""Deterministic in-memory persistence repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .migrations import SchemaDefinition
from .records import ObjectType, PersistentRecord


GENESIS_HASH = "0" * 64


class PersistenceError(ValueError):
    """Raised when persistence rules are violated."""


@dataclass
class InMemoryPersistenceRepository:
    """Append-only persistence repository for canonical ARGOS objects."""

    schemas: tuple[SchemaDefinition, ...]
    _records: dict[tuple[ObjectType, str], list[PersistentRecord]] = field(default_factory=dict)

    def persist(
        self,
        object_type: ObjectType,
        object_id: str,
        payload: dict[str, Any],
        schema_version: str = "1.0.0",
    ) -> PersistentRecord:
        """Append a new version for an object."""
        schema = self._schema_for(object_type, schema_version)
        missing = [field_name for field_name in schema.required_fields if field_name not in payload]
        if missing:
            raise PersistenceError(f"missing required persisted fields: {', '.join(missing)}")

        key = (object_type, object_id)
        history = self._records.setdefault(key, [])
        previous_hash = history[-1].record_hash if history else GENESIS_HASH
        record = PersistentRecord(
            object_type=object_type,
            object_id=object_id,
            version=len(history) + 1,
            schema_version=schema_version,
            payload=payload,
            created_timestamp_utc=utc_timestamp(),
            previous_record_hash=previous_hash,
        )
        history.append(record)
        return record

    def history(self, object_type: ObjectType, object_id: str) -> tuple[PersistentRecord, ...]:
        """Return full version history for an object."""
        return tuple(self._records.get((object_type, object_id), ()))

    def latest(self, object_type: ObjectType, object_id: str) -> PersistentRecord | None:
        """Return latest version for an object."""
        history = self.history(object_type, object_id)
        return history[-1] if history else None

    def all_records(self) -> tuple[PersistentRecord, ...]:
        """Return all persisted records sorted by creation order."""
        records: list[PersistentRecord] = []
        for history in self._records.values():
            records.extend(history)
        return tuple(sorted(records, key=lambda record: (record.created_timestamp_utc, record.record_hash)))

    def replace_records(self, records: tuple[PersistentRecord, ...]) -> None:
        """Replace repository contents during restore after integrity validation."""
        restored: dict[tuple[ObjectType, str], list[PersistentRecord]] = {}
        for record in sorted(records, key=lambda item: (item.object_type.value, item.object_id, item.version)):
            key = (record.object_type, record.object_id)
            restored.setdefault(key, []).append(record)
        self._records = restored
        self.validate_integrity()

    def validate_integrity(self) -> bool:
        """Validate version continuity and hash chains."""
        for history in self._records.values():
            previous_hash = GENESIS_HASH
            for expected_version, record in enumerate(history, start=1):
                if record.version != expected_version:
                    raise PersistenceError("record version sequence is broken")
                if record.previous_record_hash != previous_hash:
                    raise PersistenceError("record hash chain is broken")
                if record.record_hash != record.compute_hash():
                    raise PersistenceError("record hash mismatch")
                previous_hash = record.record_hash
        return True

    def _schema_for(self, object_type: ObjectType, schema_version: str) -> SchemaDefinition:
        for schema in self.schemas:
            if schema.object_type == object_type and schema.schema_version == schema_version:
                return schema
        raise PersistenceError(f"unknown schema: {object_type.value} {schema_version}")

