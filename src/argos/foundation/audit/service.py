"""Audit service for creating and searching immutable events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from argos.foundation.contracts import BaseContract, utc_timestamp
from argos.foundation.identity import validate_identifier

from .events import AuditEvent, AuditEventType
from .log import AppendOnlyAuditLog


@dataclass
class AuditService:
    """Create immutable audit events and provide deterministic searches."""

    audit_log: AppendOnlyAuditLog = field(default_factory=AppendOnlyAuditLog)

    def record_event(
        self,
        event_type: AuditEventType,
        contract: BaseContract,
        staff_id: str,
        group_id: str,
        payload: dict[str, Any],
    ) -> AuditEvent:
        """Create and append an immutable audit event for a contract action."""
        self._validate_event_identity(contract, staff_id, group_id)
        event = AuditEvent(
            event_id=f"AE-{len(self.audit_log.events) + 1:06d}",
            sequence=len(self.audit_log.events) + 1,
            event_type=event_type,
            timestamp_utc=utc_timestamp(),
            case_file_id=contract.case_file_id,
            trade_cycle_id=contract.trade_cycle_id,
            staff_id=staff_id,
            group_id=group_id,
            document_id=contract.contract_id,
            payload=dict(payload),
            previous_event_hash=self.audit_log.latest_hash(),
        )
        return self.audit_log.append(event)

    def record_document_creation(self, contract: BaseContract) -> AuditEvent:
        """Record document creation."""
        return self.record_event(
            AuditEventType.DOCUMENT_CREATED,
            contract,
            contract.produced_by_staff_id,
            contract.produced_by_group_id,
            {"contract_type": contract.contract_type, "contract_version": contract.contract_version},
        )

    def record_mailbox_deposit(
        self,
        contract: BaseContract,
        staff_id: str,
        group_id: str,
        mailbox: str,
    ) -> AuditEvent:
        """Record a mailbox deposit."""
        return self.record_event(
            AuditEventType.MAILBOX_DEPOSITED,
            contract,
            staff_id,
            group_id,
            {"mailbox": mailbox},
        )

    def record_courier_transfer(
        self,
        contract: BaseContract,
        staff_id: str,
        group_id: str,
        status: str,
        attempt: int,
        reason: str | None = None,
    ) -> AuditEvent:
        """Record a courier transfer attempt."""
        return self.record_event(
            AuditEventType.COURIER_TRANSFER,
            contract,
            staff_id,
            group_id,
            {"status": status, "attempt": attempt, "reason": reason},
        )

    def record_validation_result(
        self,
        contract: BaseContract,
        staff_id: str,
        group_id: str,
        passed: bool,
        errors: list[str],
    ) -> AuditEvent:
        """Record a validation result."""
        return self.record_event(
            AuditEventType.VALIDATION_RESULT,
            contract,
            staff_id,
            group_id,
            {"passed": passed, "errors": list(errors)},
        )

    def record_document_receipt(
        self,
        contract: BaseContract,
        staff_id: str,
        group_id: str,
        mailbox: str,
    ) -> AuditEvent:
        """Record document receipt."""
        return self.record_event(
            AuditEventType.DOCUMENT_RECEIVED,
            contract,
            staff_id,
            group_id,
            {"mailbox": mailbox},
        )

    def record_staff_decision(
        self,
        contract: BaseContract,
        staff_id: str,
        group_id: str,
        decision: str,
        rationale: str,
    ) -> AuditEvent:
        """Record a staff decision."""
        return self.record_event(
            AuditEventType.STAFF_DECISION,
            contract,
            staff_id,
            group_id,
            {"decision": decision, "rationale": rationale},
        )

    def search_by_case_file_id(self, case_file_id: str) -> tuple[AuditEvent, ...]:
        """Return events for a Case File ID."""
        return self._search("case_file_id", case_file_id)

    def search_by_trade_cycle_id(self, trade_cycle_id: str) -> tuple[AuditEvent, ...]:
        """Return events for a Trade Cycle ID."""
        return self._search("trade_cycle_id", trade_cycle_id)

    def search_by_staff_id(self, staff_id: str) -> tuple[AuditEvent, ...]:
        """Return events for a Staff ID."""
        return self._search("staff_id", staff_id)

    def search_by_document_id(self, document_id: str) -> tuple[AuditEvent, ...]:
        """Return events for a Document ID."""
        return self._search("document_id", document_id)

    def _search(self, field_name: str, identifier: str) -> tuple[AuditEvent, ...]:
        return tuple(
            event for event in self.audit_log.events if getattr(event, field_name) == identifier
        )

    def _validate_event_identity(self, contract: BaseContract, staff_id: str, group_id: str) -> None:
        contract_errors = contract.validate()
        if contract_errors:
            raise ValueError("; ".join(contract_errors))

        staff_result = validate_identifier(staff_id)
        if not staff_result.is_valid:
            raise ValueError(staff_result.reason or "invalid staff_id")

        group_result = validate_identifier(group_id)
        if not group_result.is_valid:
            raise ValueError(group_result.reason or "invalid group_id")

