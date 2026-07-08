"""Analyst Department orchestration."""

from __future__ import annotations

from argos.foundation.audit import AuditService
from argos.foundation.communication import CourierService, IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract
from argos.foundation.persistence import InMemoryPersistenceRepository
from argos.foundation.prompts import PromptRepository

from .offices import (
    AnalyticalAssessmentReportGenerator,
    AnalystOffice,
    AnalystOfficeRegistry,
    analyst_office_templates,
)


class AnalystDepartment:
    """Deterministic collection of Analyst reasoning offices."""

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
        self.registry = AnalystOfficeRegistry()
        self.offices: dict[str, AnalystOffice] = {}
        self.aar_generator = AnalyticalAssessmentReportGenerator()
        for template in analyst_office_templates():
            record = self.registry.register(template)
            self.offices[template.office_id] = AnalystOffice(record)

    def generate_aar(
        self,
        office_id: str,
        source_reports: tuple[OperationalContract, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        """Generate an AAR from existing evidence."""
        self.configuration_service.validate_startup()
        office = self._office(office_id)
        return self.aar_generator.generate(
            office,
            source_reports,
            case_file_id,
            trade_cycle_id,
            document_sequence,
            self.prompt_repository,
            prompt_id,
            self.persistence_repository,
        )

    def route_aar(self, office_id: str, aar: OperationalContract, target_inbox: IncomingMailbox):
        """Route an AAR through Courier Framework."""
        office = self._office(office_id)
        result = CourierService(self.audit_service).deliver(office.record.outbox, target_inbox, aar)
        if result.delivered:
            office.routed_reports += 1
        return result

    def instrument_panels(self):
        """Return instrument panels for every Analyst office."""
        return tuple(self.offices[key].instrument_panel() for key in sorted(self.offices))

    def _office(self, office_id: str) -> AnalystOffice:
        if office_id not in self.offices:
            raise ValueError(f"unknown Analyst office: {office_id}")
        return self.offices[office_id]
