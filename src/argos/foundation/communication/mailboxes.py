"""Deterministic mailboxes for ARGOS staff communication."""

from __future__ import annotations

from dataclasses import dataclass, field

from argos.foundation.contracts import BaseContract
from argos.foundation.identity import IdentifierKind, validate_identifier


class MailboxDeliveryError(ValueError):
    """Raised when mailbox ownership or delivery rules are violated."""


class DirectCommunicationRejected(MailboxDeliveryError):
    """Raised when code attempts staff-to-staff communication without courier."""


@dataclass
class OutgoingMailbox:
    """Outgoing mailbox owned by one staff member."""

    owner_staff_id: str
    owner_group_id: str
    queued_contracts: dict[str, BaseContract] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_staff_and_group(self.owner_staff_id, self.owner_group_id)

    def enqueue(self, contract: BaseContract) -> None:
        """Queue a contract for courier pickup."""
        if contract.produced_by_staff_id != self.owner_staff_id:
            raise MailboxDeliveryError("contract producer staff must match outgoing mailbox owner")
        if contract.produced_by_group_id != self.owner_group_id:
            raise MailboxDeliveryError("contract producer group must match outgoing mailbox owner group")
        self.queued_contracts[contract.contract_id] = contract

    def remove(self, contract_id: str) -> BaseContract:
        """Remove and return a queued contract after courier delivery."""
        return self.queued_contracts.pop(contract_id)

    def get(self, contract_id: str) -> BaseContract | None:
        """Return a queued contract by ID."""
        return self.queued_contracts.get(contract_id)


@dataclass
class IncomingMailbox:
    """Incoming mailbox owned by one staff member."""

    owner_staff_id: str
    owner_group_id: str
    received_contracts: dict[str, BaseContract] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_staff_and_group(self.owner_staff_id, self.owner_group_id)

    def receive_direct(self, contract: BaseContract) -> None:
        """Reject direct delivery attempts that bypass the Courier Service."""
        raise DirectCommunicationRejected(
            f"direct delivery of {contract.contract_id} to {self.owner_staff_id} is prohibited"
        )

    def _receive_from_courier(self, contract: BaseContract) -> None:
        """Accept a courier-validated contract."""
        if contract.intended_consumer_group_id != self.owner_group_id:
            raise MailboxDeliveryError("contract consumer group must match incoming mailbox owner group")
        self.received_contracts[contract.contract_id] = contract

    def get(self, contract_id: str) -> BaseContract | None:
        """Return a received contract by ID."""
        return self.received_contracts.get(contract_id)


def _validate_staff_and_group(staff_id: str, group_id: str) -> None:
    staff_result = validate_identifier(staff_id)
    if not staff_result.is_valid or staff_result.kind != IdentifierKind.STAFF:
        raise MailboxDeliveryError(f"invalid staff identifier: {staff_id}")

    group_result = validate_identifier(group_id)
    if not group_result.is_valid or group_result.kind != IdentifierKind.DEPARTMENT:
        raise MailboxDeliveryError(f"invalid group identifier: {group_id}")

