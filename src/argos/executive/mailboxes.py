"""Executive inbox and outbox wrappers."""

from __future__ import annotations

from dataclasses import dataclass

from argos.foundation.communication import IncomingMailbox, OutgoingMailbox


EXECUTIVE_GROUP_ID = "DEP-002"
COMMANDER_STAFF_ID = "STF-002"


@dataclass
class ExecutiveInbox:
    """Executive Incoming Mailbox."""

    mailbox: IncomingMailbox

    @classmethod
    def create(cls, staff_id: str = COMMANDER_STAFF_ID) -> "ExecutiveInbox":
        """Create a deterministic Executive inbox."""
        return cls(IncomingMailbox(staff_id, EXECUTIVE_GROUP_ID))


@dataclass
class ExecutiveOutbox:
    """Executive Outgoing Mailbox."""

    mailbox: OutgoingMailbox

    @classmethod
    def create(cls, staff_id: str = COMMANDER_STAFF_ID) -> "ExecutiveOutbox":
        """Create a deterministic Executive outbox."""
        return cls(OutgoingMailbox(staff_id, EXECUTIVE_GROUP_ID))

