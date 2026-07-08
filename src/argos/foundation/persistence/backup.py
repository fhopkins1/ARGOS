"""Backup and restore interfaces for persistence repositories."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .records import ObjectType, PersistentRecord
from .repository import InMemoryPersistenceRepository


@dataclass(frozen=True)
class BackupBundle:
    """Deterministic repository backup bundle."""

    records: tuple[dict, ...]
    backup_hash: str


@dataclass
class BackupService:
    """Create and restore deterministic persistence backups."""

    repository: InMemoryPersistenceRepository

    def create_backup(self) -> BackupBundle:
        """Create a deterministic backup bundle."""
        records = tuple(record.to_dict() for record in self.repository.all_records())
        encoded = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return BackupBundle(records=records, backup_hash=hashlib.sha256(encoded).hexdigest())

    def restore(self, backup: BackupBundle) -> None:
        """Restore records from a backup bundle."""
        encoded = json.dumps(backup.records, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if hashlib.sha256(encoded).hexdigest() != backup.backup_hash:
            raise ValueError("backup hash mismatch")
        records = tuple(_record_from_dict(record) for record in backup.records)
        self.repository.replace_records(records)


def _record_from_dict(data: dict) -> PersistentRecord:
    record = PersistentRecord(
        object_type=ObjectType(data["object_type"]),
        object_id=data["object_id"],
        version=int(data["version"]),
        schema_version=data["schema_version"],
        payload=data["payload"],
        created_timestamp_utc=data["created_timestamp_utc"],
        previous_record_hash=data["previous_record_hash"],
    )
    if record.record_hash != data["record_hash"]:
        raise ValueError("record hash mismatch during restore")
    return record

