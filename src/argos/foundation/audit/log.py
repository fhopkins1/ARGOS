"""Append-only audit log."""

from __future__ import annotations

from dataclasses import dataclass, field

from .events import AuditEvent


GENESIS_HASH = "0" * 64


class AuditIntegrityError(ValueError):
    """Raised when audit log integrity checks fail."""


@dataclass
class AppendOnlyAuditLog:
    """In-memory append-only audit log with hash-chain integrity."""

    _events: list[AuditEvent] = field(default_factory=list)

    def append(self, event: AuditEvent) -> AuditEvent:
        """Append an already-created immutable event."""
        expected_sequence = len(self._events) + 1
        if event.sequence != expected_sequence:
            raise AuditIntegrityError("audit event sequence is not append-only")

        expected_previous_hash = self._events[-1].event_hash if self._events else GENESIS_HASH
        if event.previous_event_hash != expected_previous_hash:
            raise AuditIntegrityError("audit event previous hash does not match log tail")
        if event.event_hash != event.compute_hash():
            raise AuditIntegrityError("audit event hash is invalid")

        self._events.append(event)
        return event

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        """Return immutable event ordering."""
        return tuple(self._events)

    def latest_hash(self) -> str:
        """Return the latest event hash or the genesis hash."""
        return self._events[-1].event_hash if self._events else GENESIS_HASH

    def verify_integrity(self) -> bool:
        """Verify ordering and hash-chain integrity."""
        previous_hash = GENESIS_HASH
        for expected_sequence, event in enumerate(self._events, start=1):
            if event.sequence != expected_sequence:
                raise AuditIntegrityError("audit event sequence gap or reorder detected")
            if event.previous_event_hash != previous_hash:
                raise AuditIntegrityError("audit event hash chain is broken")
            if event.event_hash != event.compute_hash():
                raise AuditIntegrityError("audit event hash mismatch")
            previous_hash = event.event_hash
        return True

