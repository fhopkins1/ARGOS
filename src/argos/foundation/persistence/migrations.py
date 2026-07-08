"""Schema definitions and deterministic migration management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .records import ObjectType


@dataclass(frozen=True)
class SchemaDefinition:
    """Canonical schema definition for a persisted object family."""

    object_type: ObjectType
    schema_version: str
    required_fields: tuple[str, ...]


@dataclass(frozen=True)
class Migration:
    """Deterministic schema migration descriptor."""

    migration_id: str
    object_type: ObjectType
    from_version: str
    to_version: str
    transform: Callable[[dict], dict]


class MigrationManager:
    """Register and apply deterministic schema migrations."""

    def __init__(self) -> None:
        self._migrations: dict[tuple[ObjectType, str, str], Migration] = {}

    def register(self, migration: Migration) -> None:
        """Register a migration once."""
        key = (migration.object_type, migration.from_version, migration.to_version)
        if key in self._migrations:
            raise ValueError(f"migration already registered: {migration.migration_id}")
        self._migrations[key] = migration

    def migrate(
        self,
        object_type: ObjectType,
        payload: dict,
        from_version: str,
        to_version: str,
    ) -> dict:
        """Apply a registered migration or return an unchanged copy for same-version moves."""
        if from_version == to_version:
            return dict(payload)
        key = (object_type, from_version, to_version)
        if key not in self._migrations:
            raise ValueError(f"missing migration for {object_type.value}: {from_version} -> {to_version}")
        return self._migrations[key].transform(dict(payload))


def canonical_schemas() -> tuple[SchemaDefinition, ...]:
    """Return canonical EO-007 schema definitions."""
    return (
        SchemaDefinition(ObjectType.CASE_FILE, "1.0.0", ("case_file_id", "trade_cycle_id")),
        SchemaDefinition(ObjectType.OPERATIONAL_DOCUMENT, "1.0.0", ("contract_id", "case_file_id")),
        SchemaDefinition(ObjectType.AUDIT_EVENT, "1.0.0", ("event_id", "case_file_id", "document_id")),
        SchemaDefinition(
            ObjectType.CONFIGURATION_SNAPSHOT,
            "1.0.0",
            ("case_file_id", "trade_cycle_id", "config_hash"),
        ),
        SchemaDefinition(
            ObjectType.PROMPT_SNAPSHOT,
            "1.0.0",
            ("prompt_snapshot_id", "case_file_id", "prompt_id", "prompt_version"),
        ),
        SchemaDefinition(ObjectType.MODEL_SNAPSHOT, "1.0.0", ("model_snapshot_id", "case_file_id")),
        SchemaDefinition(ObjectType.STAFF_REGISTRY, "1.0.0", ("staff_id", "group_id")),
        SchemaDefinition(ObjectType.DEPARTMENT_REGISTRY, "1.0.0", ("department_id", "name")),
    )
