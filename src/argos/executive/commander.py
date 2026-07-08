"""Commander Office orchestration for Executive decisions."""

from __future__ import annotations

from dataclasses import dataclass, field

from argos.foundation.audit import AuditService
from argos.foundation.communication import CourierService, IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType

from .cdr import CommandDecisionRecordGenerator
from .decisions import DecisionQueue, DecisionRecord, DecisionRegistry, create_decision_record
from .mailboxes import COMMANDER_STAFF_ID, EXECUTIVE_GROUP_ID, ExecutiveInbox, ExecutiveOutbox


@dataclass
class CommanderOffice:
    """Executive Commander Office."""

    configuration_service: ConfigurationService
    persistence_repository: InMemoryPersistenceRepository
    audit_service: AuditService = field(default_factory=AuditService)
    decision_queue: DecisionQueue = field(default_factory=DecisionQueue)
    decision_registry: DecisionRegistry = field(default_factory=DecisionRegistry)
    cdr_generator: CommandDecisionRecordGenerator = field(default_factory=CommandDecisionRecordGenerator)
    inbox: ExecutiveInbox = field(default_factory=ExecutiveInbox.create)
    outbox: ExecutiveOutbox = field(default_factory=ExecutiveOutbox.create)

    def submit_decision_request(
        self,
        case_file_id: str,
        trade_cycle_id: str,
        requested_by_staff_id: str,
        decision_type: str,
        rationale: str,
        risk_recommendation_document_id: str,
        approved: bool,
    ) -> DecisionRecord:
        """Queue an Executive decision request."""
        decision = create_decision_record(
            sequence=len(self.decision_registry.all()) + len(self.decision_queue) + 1,
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            requested_by_staff_id=requested_by_staff_id,
            decision_type=decision_type,
            rationale=rationale,
            risk_recommendation_document_id=risk_recommendation_document_id,
            approved=approved,
        )
        self.decision_queue.enqueue(decision)
        return decision

    def register_next_decision(self) -> DecisionRecord:
        """Register the next queued decision."""
        decision = self.decision_queue.dequeue()
        registered = self.decision_registry.register(decision)
        return registered

    def generate_cdr(
        self,
        decision_id: str,
        document_sequence: int,
        intended_consumer_group_id: str,
    ) -> OperationalContract:
        """Generate and persist a CDR for a registered decision."""
        self.configuration_service.validate_startup()
        decision = self.decision_registry.get(decision_id)
        if decision is None:
            raise ValueError(f"unknown decision: {decision_id}")

        cdr = self.cdr_generator.generate(decision, document_sequence, intended_consumer_group_id)
        self.decision_registry.mark_cdr_generated(decision_id)
        self.persistence_repository.persist(
            ObjectType.OPERATIONAL_DOCUMENT,
            cdr.contract_id,
            cdr.to_dict(),
        )
        self.audit_service.record_staff_decision(
            cdr,
            staff_id=COMMANDER_STAFF_ID,
            group_id=EXECUTIVE_GROUP_ID,
            decision=decision.decision_type,
            rationale=decision.rationale,
        )
        return cdr

    def route_cdr(self, cdr: OperationalContract, incoming_mailbox: IncomingMailbox):
        """Route a CDR through Foundation Courier."""
        courier = CourierService(audit_service=self.audit_service)
        return courier.deliver(self.outbox.mailbox, incoming_mailbox, cdr)

