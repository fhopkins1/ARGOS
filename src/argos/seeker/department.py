"""Seeker Department orchestration."""

from __future__ import annotations

from argos.foundation.audit import AuditService
from argos.foundation.communication import CourierService, IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.persistence import InMemoryPersistenceRepository
from argos.foundation.prompts import PromptRepository

from .offices import (
    CandidateOpportunityReportGenerator,
    OfficeRegistry,
    SeekerOffice,
    seeker_office_templates,
)


class SeekerDepartment:
    """Deterministic collection of Seeker intelligence offices."""

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
        self.registry = OfficeRegistry()
        self.offices: dict[str, SeekerOffice] = {}
        self.cor_generator = CandidateOpportunityReportGenerator()
        for template in seeker_office_templates():
            record = self.registry.register(template)
            self.offices[template.office_id] = SeekerOffice(record)

    def generate_cor(
        self,
        office_id: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ):
        """Generate a COR from a registered office."""
        self.configuration_service.validate_startup()
        office = self._office(office_id)
        return self.cor_generator.generate(
            office,
            case_file_id,
            trade_cycle_id,
            document_sequence,
            self.prompt_repository,
            prompt_id,
            self.persistence_repository,
        )

    def route_cor(self, office_id: str, cor, target_inbox: IncomingMailbox):
        """Route a COR through Courier Framework."""
        office = self._office(office_id)
        result = CourierService(self.audit_service).deliver(office.record.outbox, target_inbox, cor)
        if result.delivered:
            office.routed_reports += 1
        return result

    def instrument_panels(self):
        """Return instrument panels for every office."""
        return tuple(self.offices[key].instrument_panel() for key in sorted(self.offices))

    def _office(self, office_id: str) -> SeekerOffice:
        if office_id not in self.offices:
            raise ValueError(f"unknown Seeker office: {office_id}")
        return self.offices[office_id]

