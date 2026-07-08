"""Persistence replay and search services."""

from __future__ import annotations

from dataclasses import dataclass

from .records import ObjectType, PersistentRecord
from .repository import InMemoryPersistenceRepository


@dataclass
class PersistenceSearchService:
    """Search persisted canonical objects."""

    repository: InMemoryPersistenceRepository

    def search_by_case_file_id(self, case_file_id: str) -> tuple[PersistentRecord, ...]:
        """Search records by Case File ID in payload or object ID."""
        return self._search("case_file_id", case_file_id)

    def search_by_trade_cycle_id(self, trade_cycle_id: str) -> tuple[PersistentRecord, ...]:
        """Search records by Trade Cycle ID."""
        return self._search("trade_cycle_id", trade_cycle_id)

    def search_by_staff_id(self, staff_id: str) -> tuple[PersistentRecord, ...]:
        """Search records by Staff ID."""
        return tuple(
            record
            for record in self.repository.all_records()
            if record.payload.get("staff_id") == staff_id
            or record.payload.get("produced_by_staff_id") == staff_id
        )

    def search_by_document_id(self, document_id: str) -> tuple[PersistentRecord, ...]:
        """Search records by Document ID or contract ID."""
        return tuple(
            record
            for record in self.repository.all_records()
            if record.object_id == document_id
            or record.payload.get("document_id") == document_id
            or record.payload.get("contract_id") == document_id
        )

    def _search(self, field_name: str, value: str) -> tuple[PersistentRecord, ...]:
        return tuple(
            record
            for record in self.repository.all_records()
            if record.object_id == value or record.payload.get(field_name) == value
        )


@dataclass(frozen=True)
class PersistedCaseFileReplay:
    """Replay result from persisted records."""

    case_file_id: str
    records: tuple[PersistentRecord, ...]
    document_ids: tuple[str, ...]
    audit_event_ids: tuple[str, ...]


@dataclass
class PersistenceReplayService:
    """Reconstruct Case Files from persisted canonical records."""

    repository: InMemoryPersistenceRepository

    def replay_case_file(self, case_file_id: str) -> PersistedCaseFileReplay:
        """Replay persisted records for one Case File."""
        self.repository.validate_integrity()
        search = PersistenceSearchService(self.repository)
        records = search.search_by_case_file_id(case_file_id)
        return PersistedCaseFileReplay(
            case_file_id=case_file_id,
            records=records,
            document_ids=_unique(
                record.object_id
                for record in records
                if record.object_type == ObjectType.OPERATIONAL_DOCUMENT
            ),
            audit_event_ids=_unique(
                str(record.payload.get("event_id"))
                for record in records
                if record.object_type == ObjectType.AUDIT_EVENT
            ),
        )


def _unique(values) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)

