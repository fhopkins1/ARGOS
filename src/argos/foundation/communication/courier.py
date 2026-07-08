"""Courier Service for deterministic ARGOS contract transfer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from argos.foundation.contracts import BaseContract, utc_timestamp
from argos.foundation.audit import AuditService

from .mailboxes import IncomingMailbox, MailboxDeliveryError, OutgoingMailbox


class DeliveryStatus(str, Enum):
    """Courier transfer status."""

    ACCEPTED = "accepted"
    DELIVERED = "delivered"
    REJECTED = "rejected"


@dataclass(frozen=True)
class TransferLogEntry:
    """Immutable courier transfer audit record."""

    sequence: int
    status: DeliveryStatus
    contract_id: str
    outgoing_owner_staff_id: str
    outgoing_owner_group_id: str
    incoming_owner_staff_id: str
    incoming_owner_group_id: str
    timestamp_utc: str
    attempt: int
    reason: str | None = None


@dataclass(frozen=True)
class CourierDeliveryResult:
    """Structured result returned by Courier Service transfer attempts."""

    delivered: bool
    contract_id: str
    attempt: int
    log_entry: TransferLogEntry


@dataclass
class CourierService:
    """Deterministic courier that validates contracts before delivery."""

    audit_service: AuditService = field(default_factory=AuditService)
    transfer_log: list[TransferLogEntry] = field(default_factory=list)
    _attempts_by_contract_id: dict[str, int] = field(default_factory=dict)

    def deliver(
        self,
        outgoing_mailbox: OutgoingMailbox,
        incoming_mailbox: IncomingMailbox,
        contract: BaseContract,
    ) -> CourierDeliveryResult:
        """Move a contract through Outgoing Mailbox -> Courier -> Incoming Mailbox."""
        attempt = self._next_attempt(contract.contract_id)

        try:
            self.audit_service.record_document_creation(contract)
            validation_errors = self._transfer_validation_errors(
                outgoing_mailbox, incoming_mailbox, contract
            )
            self.audit_service.record_validation_result(
                contract=contract,
                staff_id=outgoing_mailbox.owner_staff_id,
                group_id=outgoing_mailbox.owner_group_id,
                passed=not validation_errors,
                errors=validation_errors,
            )
            if validation_errors:
                raise MailboxDeliveryError("; ".join(validation_errors))
            outgoing_mailbox.enqueue(contract)
            self.audit_service.record_mailbox_deposit(
                contract=contract,
                staff_id=outgoing_mailbox.owner_staff_id,
                group_id=outgoing_mailbox.owner_group_id,
                mailbox="outgoing",
            )
            incoming_mailbox._receive_from_courier(contract)
            outgoing_mailbox.remove(contract.contract_id)
        except Exception as exc:
            self.audit_service.record_courier_transfer(
                contract=contract,
                staff_id=outgoing_mailbox.owner_staff_id,
                group_id=outgoing_mailbox.owner_group_id,
                status=DeliveryStatus.REJECTED.value,
                attempt=attempt,
                reason=str(exc),
            )
            log_entry = self._log(
                status=DeliveryStatus.REJECTED,
                contract=contract,
                outgoing_mailbox=outgoing_mailbox,
                incoming_mailbox=incoming_mailbox,
                attempt=attempt,
                reason=str(exc),
            )
            return CourierDeliveryResult(False, contract.contract_id, attempt, log_entry)

        self.audit_service.record_courier_transfer(
            contract=contract,
            staff_id=outgoing_mailbox.owner_staff_id,
            group_id=outgoing_mailbox.owner_group_id,
            status=DeliveryStatus.DELIVERED.value,
            attempt=attempt,
        )
        self.audit_service.record_document_receipt(
            contract=contract,
            staff_id=incoming_mailbox.owner_staff_id,
            group_id=incoming_mailbox.owner_group_id,
            mailbox="incoming",
        )
        log_entry = self._log(
            status=DeliveryStatus.DELIVERED,
            contract=contract,
            outgoing_mailbox=outgoing_mailbox,
            incoming_mailbox=incoming_mailbox,
            attempt=attempt,
        )
        return CourierDeliveryResult(True, contract.contract_id, attempt, log_entry)

    def retry(
        self,
        outgoing_mailbox: OutgoingMailbox,
        incoming_mailbox: IncomingMailbox,
        contract: BaseContract,
    ) -> CourierDeliveryResult:
        """Retry a courier delivery using the same deterministic path."""
        return self.deliver(outgoing_mailbox, incoming_mailbox, contract)

    def reject_direct_communication(
        self,
        sender_staff_id: str,
        recipient_staff_id: str,
        contract: BaseContract,
    ) -> None:
        """Explicitly reject staff-to-staff communication that bypasses mailboxes."""
        raise MailboxDeliveryError(
            "direct staff-to-staff communication is prohibited; use mailboxes and Courier Service"
        )

    def _validate_transfer(
        self,
        outgoing_mailbox: OutgoingMailbox,
        incoming_mailbox: IncomingMailbox,
        contract: BaseContract,
    ) -> None:
        contract_errors = contract.validate()
        if contract_errors:
            raise MailboxDeliveryError("; ".join(contract_errors))
        if contract.produced_by_staff_id != outgoing_mailbox.owner_staff_id:
            raise MailboxDeliveryError("outgoing mailbox staff does not match contract producer")
        if contract.produced_by_group_id != outgoing_mailbox.owner_group_id:
            raise MailboxDeliveryError("outgoing mailbox group does not match contract producer group")
        if contract.intended_consumer_group_id != incoming_mailbox.owner_group_id:
            raise MailboxDeliveryError("incoming mailbox group does not match intended consumer group")

    def _transfer_validation_errors(
        self,
        outgoing_mailbox: OutgoingMailbox,
        incoming_mailbox: IncomingMailbox,
        contract: BaseContract,
    ) -> list[str]:
        errors = contract.validate()
        if contract.produced_by_staff_id != outgoing_mailbox.owner_staff_id:
            errors.append("outgoing mailbox staff does not match contract producer")
        if contract.produced_by_group_id != outgoing_mailbox.owner_group_id:
            errors.append("outgoing mailbox group does not match contract producer group")
        if contract.intended_consumer_group_id != incoming_mailbox.owner_group_id:
            errors.append("incoming mailbox group does not match intended consumer group")
        return errors

    def _next_attempt(self, contract_id: str) -> int:
        attempt = self._attempts_by_contract_id.get(contract_id, 0) + 1
        self._attempts_by_contract_id[contract_id] = attempt
        return attempt

    def _log(
        self,
        status: DeliveryStatus,
        contract: BaseContract,
        outgoing_mailbox: OutgoingMailbox,
        incoming_mailbox: IncomingMailbox,
        attempt: int,
        reason: str | None = None,
    ) -> TransferLogEntry:
        log_entry = TransferLogEntry(
            sequence=len(self.transfer_log) + 1,
            status=status,
            contract_id=contract.contract_id,
            outgoing_owner_staff_id=outgoing_mailbox.owner_staff_id,
            outgoing_owner_group_id=outgoing_mailbox.owner_group_id,
            incoming_owner_staff_id=incoming_mailbox.owner_staff_id,
            incoming_owner_group_id=incoming_mailbox.owner_group_id,
            timestamp_utc=utc_timestamp(),
            attempt=attempt,
            reason=reason,
        )
        self.transfer_log.append(log_entry)
        return log_entry
