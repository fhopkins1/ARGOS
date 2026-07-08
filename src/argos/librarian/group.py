"""Librarian Group institutional knowledge framework."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository


LIBRARIAN_GROUP_ID = "DEP-008"
LIBRARIAN_CHIEF_OFFICE_ID = "LIBRARIAN-OFFICE-001"
LIBRARIAN_CHIEF_STAFF_ID = "STF-080"


class KnowledgeClassification(str, Enum):
    """Institutional knowledge classification."""

    VALIDATED_LESSON = "validated_lesson"
    ORGANIZATIONAL_STANDARD = "organizational_standard"
    DOCTRINE = "doctrine"
    REFERENCE = "reference"


class DoctrineStatus(str, Enum):
    """Doctrine status."""

    CANDIDATE = "candidate"
    AUTHORITATIVE = "authoritative"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class LibrarianOfficeTemplate:
    """Librarian office template."""

    office_id: str
    name: str
    mission: str


@dataclass(frozen=True)
class InstitutionalKnowledgeArtifact:
    """Validated institutional knowledge artifact."""

    knowledge_id: str
    title: str
    classification: KnowledgeClassification
    source_historian_package_id: str
    doctrine_candidate: bool
    content_hash: str
    provenance_ids: tuple[str, ...]
    reference_ids: tuple[str, ...]


@dataclass(frozen=True)
class KnowledgeRepositoryRecord:
    """Institutional repository record."""

    repository_id: str
    knowledge: InstitutionalKnowledgeArtifact
    current_version_id: str
    doctrine_status: DoctrineStatus
    created_timestamp_utc: str


@dataclass(frozen=True)
class DoctrineRegistryRecord:
    """Doctrine registry record."""

    doctrine_id: str
    knowledge_id: str
    status: DoctrineStatus
    classification: KnowledgeClassification
    authoritative_version_id: str
    promoted_timestamp_utc: str


@dataclass(frozen=True)
class KnowledgeVersionRecord:
    """Immutable knowledge version record."""

    version_id: str
    knowledge_id: str
    version: str
    parent_version_id: str | None
    content_hash: str
    provenance_ids: tuple[str, ...]
    timestamp_utc: str


@dataclass(frozen=True)
class KnowledgePromotionRecord:
    """Deterministic promotion record."""

    promotion_id: str
    knowledge_id: str
    promoted: bool
    promotion_reason: str
    historian_certification_package_id: str
    doctrine_revision_id: str | None


@dataclass(frozen=True)
class ReferenceGraph:
    """Reference graph for knowledge artifacts."""

    graph_id: str
    knowledge_id: str
    reference_ids: tuple[str, ...]
    provenance_ids: tuple[str, ...]
    broken_references: tuple[str, ...]
    reference_integrity_verified: bool


@dataclass(frozen=True)
class RepositoryIntegrityReport:
    """Repository integrity report."""

    integrity_id: str
    repository_ids: tuple[str, ...]
    reference_graph_ids: tuple[str, ...]
    historical_doctrine_immutable: bool
    repository_integrity_operational: bool


@dataclass(frozen=True)
class KnowledgeDistributionRecord:
    """Knowledge distribution record."""

    distribution_id: str
    knowledge_id: str
    target_consumers: tuple[str, ...]
    distributed: bool
    distribution_timestamp_utc: str


@dataclass(frozen=True)
class OrganizationalKnowledgeSummary:
    """Organizational knowledge summary."""

    summary_id: str
    knowledge_count: int
    doctrine_count: int
    candidate_count: int
    repository_health: str
    distributed_knowledge_ids: tuple[str, ...]


class LibrarianGroup:
    """Permanent institutional memory authority."""

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
        self._repository: dict[str, KnowledgeRepositoryRecord] = {}
        self._doctrine: dict[str, DoctrineRegistryRecord] = {}
        self._version_archive: list[KnowledgeVersionRecord] = []
        self._promotion_register: list[KnowledgePromotionRecord] = []

    @property
    def institutional_repository(self) -> tuple[KnowledgeRepositoryRecord, ...]:
        """Return institutional repository."""
        return tuple(self._repository[key] for key in sorted(self._repository))

    @property
    def doctrine_registry(self) -> tuple[DoctrineRegistryRecord, ...]:
        """Return doctrine registry."""
        return tuple(self._doctrine[key] for key in sorted(self._doctrine))

    @property
    def knowledge_version_archive(self) -> tuple[KnowledgeVersionRecord, ...]:
        """Return immutable knowledge version archive."""
        return tuple(self._version_archive)

    def promote_knowledge(
        self,
        knowledge: InstitutionalKnowledgeArtifact,
        historian_certification_package_id: str,
        validated_knowledge_transfer_authorized: bool,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Promote validated knowledge into Librarian repositories."""
        self.configuration_service.validate_startup()
        if knowledge.knowledge_id in self._repository:
            raise ValueError(f"knowledge already exists: {knowledge.knowledge_id}")
        version = KnowledgeVersionRecord(
            f"KVR-{document_sequence:06d}",
            knowledge.knowledge_id,
            "1.0.0",
            None,
            knowledge.content_hash,
            knowledge.provenance_ids,
            utc_timestamp(),
        )
        status = DoctrineStatus.AUTHORITATIVE if validated_knowledge_transfer_authorized and knowledge.doctrine_candidate else DoctrineStatus.CANDIDATE
        repository = KnowledgeRepositoryRecord(
            f"IKR-{hashlib.sha256(knowledge.knowledge_id.encode('utf-8')).hexdigest()[:8].upper()}",
            knowledge,
            version.version_id,
            status,
            version.timestamp_utc,
        )
        doctrine = DoctrineRegistryRecord(
            f"DR-{hashlib.sha256(f'{knowledge.knowledge_id}:{version.version_id}'.encode('utf-8')).hexdigest()[:8].upper()}",
            knowledge.knowledge_id,
            status,
            knowledge.classification if status == DoctrineStatus.AUTHORITATIVE else KnowledgeClassification.VALIDATED_LESSON,
            version.version_id,
            version.timestamp_utc,
        )
        promotion = KnowledgePromotionRecord(
            f"KPR-{hashlib.sha256(f'{knowledge.knowledge_id}:{historian_certification_package_id}'.encode('utf-8')).hexdigest()[:8].upper()}",
            knowledge.knowledge_id,
            status == DoctrineStatus.AUTHORITATIVE,
            "validated_historian_transfer_authorized" if status == DoctrineStatus.AUTHORITATIVE else "stored_as_candidate_pending_authorization",
            historian_certification_package_id,
            doctrine.doctrine_id if status == DoctrineStatus.AUTHORITATIVE else None,
        )
        graph = _reference_graph(knowledge)
        distribution = KnowledgeDistributionRecord(
            f"KDR-{document_sequence:06d}",
            knowledge.knowledge_id,
            ("Executive Group", "Seeker Department", "Analyst Department", "Risk Office", "Trader Group", "Historian Group", "Academy"),
            True,
            utc_timestamp(),
        )
        self._repository[knowledge.knowledge_id] = repository
        self._doctrine[doctrine.doctrine_id] = doctrine
        self._version_archive.append(version)
        self._promotion_register.append(promotion)
        integrity = RepositoryIntegrityReport(
            f"RIR-{document_sequence:06d}",
            tuple(record.repository_id for record in self.institutional_repository),
            (graph.graph_id,),
            True,
            graph.reference_integrity_verified,
        )
        summary = OrganizationalKnowledgeSummary(
            f"OKS-{document_sequence:06d}",
            len(self._repository),
            sum(1 for item in self._doctrine.values() if item.status == DoctrineStatus.AUTHORITATIVE),
            sum(1 for item in self._repository.values() if item.doctrine_status == DoctrineStatus.CANDIDATE),
            "healthy" if integrity.repository_integrity_operational else "attention",
            (knowledge.knowledge_id,) if distribution.distributed else (),
        )
        return {
            "institutional_knowledge_report": self._persist_contract(
                "LIBRARIAN_INSTITUTIONAL_KNOWLEDGE_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Institutional Knowledge Report.",
                {
                    "office_id": LIBRARIAN_CHIEF_OFFICE_ID,
                    "office_name": "Librarian Group",
                    "institutional_knowledge_repository": self.institutional_repository,
                    "knowledge_version_archive": self.knowledge_version_archive,
                    "knowledge_provenance_record": knowledge.provenance_ids,
                    "deterministic_knowledge_trace": graph,
                },
            ),
            "doctrine_status_report": self._persist_contract(
                "DOCTRINE_STATUS_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Doctrine Status Report.",
                {
                    "doctrine_registry": self.doctrine_registry,
                    "knowledge_promotion_register": tuple(self._promotion_register),
                    "historical_doctrine_immutable": True,
                },
            ),
            "repository_integrity_report": self._persist_contract(
                "REPOSITORY_INTEGRITY_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Repository Integrity Report.",
                {
                    "repository_integrity_report": integrity,
                    "reference_graph": graph,
                    "repository_health_database": {"status": summary.repository_health},
                },
            ),
            "organizational_knowledge_summary": self._persist_contract(
                "ORGANIZATIONAL_KNOWLEDGE_SUMMARY",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Organizational Knowledge Summary.",
                {
                    "organizational_knowledge_summary": summary,
                    "knowledge_distribution_record": distribution,
                    "organizational_standards_archive": tuple(item.knowledge.knowledge_id for item in self.institutional_repository),
                },
            ),
        }

    def _persist_contract(
        self,
        contract_type: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        human_summary: str,
        payload: dict[str, Any],
    ) -> OperationalContract:
        contract = _contract(contract_type, case_file_id, trade_cycle_id, document_sequence, human_summary, payload)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        return contract


def librarian_office_templates() -> tuple[LibrarianOfficeTemplate, ...]:
    """Return Librarian office templates."""
    return (
        LibrarianOfficeTemplate("LIBRARIAN-OFFICE-001", "Institutional Knowledge Office", "Maintain validated institutional knowledge repositories."),
        LibrarianOfficeTemplate("LIBRARIAN-OFFICE-002", "Doctrine Management Office", "Govern doctrine status, versioning, and historical doctrine preservation."),
        LibrarianOfficeTemplate("LIBRARIAN-OFFICE-003", "Specification Repository Office", "Preserve specifications and organizational standards."),
        LibrarianOfficeTemplate("LIBRARIAN-OFFICE-004", "Knowledge Graph Office", "Maintain reference integrity and knowledge provenance graphs."),
        LibrarianOfficeTemplate("LIBRARIAN-OFFICE-005", "Learning Integration Office", "Integrate validated Historian learning into institutional memory."),
        LibrarianOfficeTemplate("LIBRARIAN-OFFICE-006", "Librarian Fusion Office", "Synthesize knowledge repository status for enterprise distribution."),
    )


def _reference_graph(knowledge: InstitutionalKnowledgeArtifact) -> ReferenceGraph:
    broken = tuple(reference for reference in knowledge.reference_ids if not reference)
    return ReferenceGraph(
        f"RG-{hashlib.sha256(knowledge.knowledge_id.encode('utf-8')).hexdigest()[:8].upper()}",
        knowledge.knowledge_id,
        knowledge.reference_ids,
        knowledge.provenance_ids,
        broken,
        not broken,
    )


def _contract(
    contract_type: str,
    case_file_id: str,
    trade_cycle_id: str,
    document_sequence: int,
    human_summary: str,
    payload: dict[str, Any],
) -> OperationalContract:
    created = utc_timestamp()
    normalized_payload = _json_ready(payload)
    signature_hash = hashlib.sha256(json.dumps(normalized_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id=generate_document_id(document_sequence),
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=case_file_id,
        trade_cycle_id=trade_cycle_id,
        parent_contract_ids=(),
        produced_by_staff_id=LIBRARIAN_CHIEF_STAFF_ID,
        produced_by_group_id=LIBRARIAN_GROUP_ID,
        intended_consumer_group_id=LIBRARIAN_GROUP_ID,
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=human_summary,
        machine_payload=normalized_payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
