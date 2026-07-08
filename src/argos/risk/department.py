"""Risk Office orchestration."""

from __future__ import annotations

from argos.analyst import OrganizationalBeliefState
from argos.foundation.audit import AuditService
from argos.foundation.communication import CourierService, IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract
from argos.foundation.persistence import InMemoryPersistenceRepository
from argos.foundation.prompts import PromptRepository

from .offices import (
    RiskAssessmentReportGenerator,
    RiskOffice,
    RiskOfficeRegistry,
    risk_office_templates,
)


class RiskDepartment:
    """Deterministic collection of Risk safeguard offices."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.configuration_service = configuration_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self.prompt_repository = prompt_repository
        self.registry = RiskOfficeRegistry()
        self.offices: dict[str, RiskOffice] = {}
        self.rar_generator = RiskAssessmentReportGenerator()
        for template in risk_office_templates():
            record = self.registry.register(template)
            self.offices[template.office_id] = RiskOffice(record)

    def generate_rar(
        self,
        office_id: str,
        belief_state: OrganizationalBeliefState,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        """Generate a Risk Assessment Report from an Organizational Belief State."""
        self.configuration_service.validate_startup()
        office = self._office(office_id)
        report = self.rar_generator.generate(
            office,
            belief_state,
            case_file_id,
            trade_cycle_id,
            document_sequence,
            self.prompt_repository,
            prompt_id,
            self.persistence_repository,
        )
        self.audit_service.record_document_creation(report)
        return report

    def route_rar(self, office_id: str, rar: OperationalContract, target_inbox: IncomingMailbox):
        """Route a RAR through Courier Framework."""
        office = self._office(office_id)
        result = CourierService(self.audit_service).deliver(office.record.outbox, target_inbox, rar)
        if result.delivered:
            office.routed_reports += 1
        return result

    def instrument_panels(self):
        """Return instrument panels for every Risk office."""
        return tuple(self.offices[key].instrument_panel() for key in sorted(self.offices))

    def _office(self, office_id: str) -> RiskOffice:
        if office_id not in self.offices:
            raise ValueError(f"unknown Risk office: {office_id}")
        return self.offices[office_id]
