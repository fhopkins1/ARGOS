"""Seeker office framework and COR generation."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json

from argos.foundation.audit import AuditService
from argos.foundation.communication import IncomingMailbox, OutgoingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository, PromptSnapshotService


SEEKER_GROUP_ID = "DEP-003"


@dataclass(frozen=True)
class OfficeConfiguration:
    """Seeker office configuration."""

    office_id: str
    name: str
    staff_id: str
    enabled: bool = True


@dataclass(frozen=True)
class OfficeRecord:
    """Registered Seeker office record."""

    configuration: OfficeConfiguration
    inbox: IncomingMailbox
    outbox: OutgoingMailbox


class OfficeRegistry:
    """Deterministic Seeker office registry."""

    def __init__(self) -> None:
        self._offices: dict[str, OfficeRecord] = {}

    def register(self, configuration: OfficeConfiguration) -> OfficeRecord:
        """Register one office."""
        if configuration.office_id in self._offices:
            raise ValueError(f"office already registered: {configuration.office_id}")
        record = OfficeRecord(
            configuration=configuration,
            inbox=IncomingMailbox(configuration.staff_id, SEEKER_GROUP_ID),
            outbox=OutgoingMailbox(configuration.staff_id, SEEKER_GROUP_ID),
        )
        self._offices[configuration.office_id] = record
        return record

    def get(self, office_id: str) -> OfficeRecord | None:
        """Return an office by ID."""
        return self._offices.get(office_id)

    def all(self) -> tuple[OfficeRecord, ...]:
        """Return all offices in deterministic order."""
        return tuple(self._offices[key] for key in sorted(self._offices))


class OfficeQueue:
    """Office work queue."""

    def __init__(self) -> None:
        self._items: list[str] = []

    def enqueue(self, item_id: str) -> None:
        self._items.append(item_id)

    def dequeue(self) -> str:
        if not self._items:
            raise IndexError("office queue is empty")
        return self._items.pop(0)

    def __len__(self) -> int:
        return len(self._items)


@dataclass(frozen=True)
class OfficeMetrics:
    """Seeker office metrics."""

    queue_depth: int
    reports_generated: int
    routed_reports: int


@dataclass(frozen=True)
class OfficeHealth:
    """Seeker office health."""

    status: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class OfficeInstrumentPanel:
    """Traceable office instrument panel."""

    office_id: str
    metrics: OfficeMetrics
    health: OfficeHealth
    source: str


@dataclass
class SeekerOffice:
    """Seeker intelligence office scaffold."""

    record: OfficeRecord
    queue: OfficeQueue = field(default_factory=OfficeQueue)
    reports_generated: int = 0
    routed_reports: int = 0

    def metrics(self) -> OfficeMetrics:
        return OfficeMetrics(len(self.queue), self.reports_generated, self.routed_reports)

    def health(self) -> OfficeHealth:
        reasons = []
        if not self.record.configuration.enabled:
            reasons.append("office_disabled")
        if len(self.queue) > 10:
            reasons.append("queue_depth_high")
        return OfficeHealth("healthy" if not reasons else "attention", tuple(reasons))

    def instrument_panel(self) -> OfficeInstrumentPanel:
        return OfficeInstrumentPanel(
            self.record.configuration.office_id,
            self.metrics(),
            self.health(),
            f"office:{self.record.configuration.office_id}",
        )


class CandidateOpportunityReportGenerator:
    """Generate Candidate Opportunity Reports without performing analysis."""

    def generate(
        self,
        office: SeekerOffice,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_repository: PromptRepository,
        prompt_id: str,
        persistence_repository: InMemoryPersistenceRepository,
    ) -> OperationalContract:
        """Generate and persist a COR."""
        snapshot = PromptSnapshotService(prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        created = utc_timestamp()
        payload = {
            "office_id": office.record.configuration.office_id,
            "office_name": office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "candidate_status": "unanalysed_candidate",
        }
        signature_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        cor = OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type="COR",
            contract_version="1.0.0",
            schema_version="1.0.0",
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            parent_contract_ids=(),
            produced_by_staff_id=office.record.configuration.staff_id,
            produced_by_group_id=SEEKER_GROUP_ID,
            intended_consumer_group_id="DEP-002",
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary=f"Candidate Opportunity Report from {office.record.configuration.name}.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=(),
        )
        persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, cor.contract_id, cor.to_dict())
        office.reports_generated += 1
        return cor


def seeker_office_templates() -> tuple[OfficeConfiguration, ...]:
    """Return EO-018 office templates."""
    names = (
        "Technical Analysis Office",
        "Fundamental Research Office",
        "Macroeconomic Office",
        "News & Sentiment Office",
        "Options Flow Office",
        "Cryptocurrency Office",
        "Event Intelligence Office",
        "Alternative Data Office",
    )
    return tuple(
        OfficeConfiguration(f"SEEKER-OFFICE-{index:03d}", name, f"STF-{20 + index:03d}")
        for index, name in enumerate(names, start=1)
    )

