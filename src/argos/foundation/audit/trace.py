"""Trace engine for replaying Case Files from audit events."""

from __future__ import annotations

from dataclasses import dataclass

from .events import AuditEvent
from .log import AppendOnlyAuditLog


@dataclass(frozen=True)
class CaseFileReplay:
    """Deterministic replay result for one Case File."""

    case_file_id: str
    events: tuple[AuditEvent, ...]
    document_ids: tuple[str, ...]
    staff_ids: tuple[str, ...]
    trade_cycle_ids: tuple[str, ...]


class TraceEngine:
    """Replay Case File activity from an append-only audit log."""

    def __init__(self, audit_log: AppendOnlyAuditLog) -> None:
        self.audit_log = audit_log

    def replay_case_file(self, case_file_id: str) -> CaseFileReplay:
        """Replay all events for a Case File in append-only order."""
        self.audit_log.verify_integrity()
        events = tuple(event for event in self.audit_log.events if event.case_file_id == case_file_id)
        return CaseFileReplay(
            case_file_id=case_file_id,
            events=events,
            document_ids=_unique_in_order(event.document_id for event in events),
            staff_ids=_unique_in_order(event.staff_id for event in events),
            trade_cycle_ids=_unique_in_order(event.trade_cycle_id for event in events),
        )


def _unique_in_order(values) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)

