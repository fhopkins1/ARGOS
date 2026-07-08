"""Institutional Knowledge Office."""

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

from .group import LIBRARIAN_GROUP_ID, InstitutionalKnowledgeArtifact, KnowledgeClassification


INSTITUTIONAL_KNOWLEDGE_OFFICE_ID = "LIBRARIAN-OFFICE-001"
INSTITUTIONAL_KNOWLEDGE_STAFF_ID = "STF-081"


class KnowledgeRelationType(str, Enum):
    """Knowledge relationship type."""

    SUPPORTS = "supports"
    REFINES = "refines"
    SUPERSEDES = "supersedes"
    REFERENCES = "references"


@dataclass(frozen=True)
class KnowledgeClassificationRecord:
    """Classification registry record."""

    classification_id: str
    knowledge_id: str
    classification: KnowledgeClassification
    deterministic_reason: str


@dataclass(frozen=True)
class KnowledgeHierarchyNode:
    """Knowledge hierarchy node."""

    node_id: str
    knowledge_id: str
    parent_knowledge_id: str | None
    path: tuple[str, ...]
    depth: int


@dataclass(frozen=True)
class KnowledgeRelationship:
    """Knowledge relationship edge."""

    relationship_id: str
    source_knowledge_id: str
    target_knowledge_id: str
    relation_type: KnowledgeRelationType
    provenance_id: str


@dataclass(frozen=True)
class ProvenanceRecord:
    """Complete provenance record."""

    provenance_record_id: str
    knowledge_id: str
    source_historian_package_id: str
    provenance_ids: tuple[str, ...]
    complete: bool


@dataclass(frozen=True)
class RetrievalIndexRecord:
    """Deterministic retrieval index record."""

    index_id: str
    normalized_terms: tuple[str, ...]
    knowledge_ids: tuple[str, ...]


@dataclass(frozen=True)
class KnowledgeConsolidationRecord:
    """Knowledge consolidation record."""

    consolidation_id: str
    knowledge_id: str
    duplicate_of: str | None
    consolidated: bool
    deterministic_reason: str


@dataclass(frozen=True)
class InstitutionalArchiveRecord:
    """Institutional archive record."""

    archive_id: str
    knowledge_id: str
    version_id: str
    immutable: bool
    archived_timestamp_utc: str


@dataclass(frozen=True)
class KnowledgeIntegrityRecord:
    """Knowledge integrity record."""

    integrity_id: str
    knowledge_id: str
    provenance_complete: bool
    relationships_consistent: bool
    duplicate_detected: bool
    repository_integrity_verified: bool


@dataclass(frozen=True)
class InstitutionalRepositorySummary:
    """Institutional repository summary."""

    summary_id: str
    knowledge_count: int
    hierarchy_node_count: int
    relationship_count: int
    archive_count: int
    repository_health: str


@dataclass(frozen=True)
class InstitutionalLearningPackage:
    """Academy deliverable."""

    package_id: str
    validated_reference_ids: tuple[str, ...]
    best_practice_ids: tuple[str, ...]
    retrieval_index_ids: tuple[str, ...]


class InstitutionalKnowledgeOffice:
    """Permanent repository of validated organizational knowledge."""

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
        self._knowledge: dict[str, InstitutionalKnowledgeArtifact] = {}
        self._classification: dict[str, KnowledgeClassificationRecord] = {}
        self._hierarchy: dict[str, KnowledgeHierarchyNode] = {}
        self._relationships: list[KnowledgeRelationship] = []
        self._archive: list[InstitutionalArchiveRecord] = []
        self._retrieval: dict[str, RetrievalIndexRecord] = {}

    @property
    def institutional_archive(self) -> tuple[InstitutionalArchiveRecord, ...]:
        """Return immutable institutional archive."""
        return tuple(self._archive)

    def receive_validated_knowledge(
        self,
        knowledge: InstitutionalKnowledgeArtifact,
        parent_knowledge_id: str | None,
        relationships: tuple[KnowledgeRelationship, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Receive validated knowledge from Historian/Librarian transfer."""
        self.configuration_service.validate_startup()
        duplicate = _duplicate_of(knowledge, self._knowledge)
        if duplicate:
            consolidation = KnowledgeConsolidationRecord(
                f"KCR-{document_sequence:06d}",
                knowledge.knowledge_id,
                duplicate,
                True,
                "Duplicate content hash detected; preserve original artifact and record consolidation.",
            )
            integrity = KnowledgeIntegrityRecord(f"KIR-{document_sequence:06d}", knowledge.knowledge_id, bool(knowledge.provenance_ids), True, True, True)
            return {
                "institutional_knowledge_report": self._persist_contract(
                    "INSTITUTIONAL_KNOWLEDGE_REPORT",
                    case_file_id,
                    trade_cycle_id,
                    document_sequence,
                    "Institutional Knowledge Report.",
                    {"knowledge_consolidation_record": consolidation, "knowledge_integrity_record": integrity, "duplicate_knowledge_detected": True},
                )
            }
        self._knowledge[knowledge.knowledge_id] = knowledge
        classification = KnowledgeClassificationRecord(
            f"KCL-{hashlib.sha256(knowledge.knowledge_id.encode('utf-8')).hexdigest()[:8].upper()}",
            knowledge.knowledge_id,
            knowledge.classification,
            "Classification derived from validated knowledge artifact metadata.",
        )
        node = _hierarchy_node(knowledge, parent_knowledge_id, self._hierarchy)
        provenance = ProvenanceRecord(
            f"KPRV-{hashlib.sha256(knowledge.knowledge_id.encode('utf-8')).hexdigest()[:8].upper()}",
            knowledge.knowledge_id,
            knowledge.source_historian_package_id,
            knowledge.provenance_ids,
            bool(knowledge.provenance_ids) and bool(knowledge.source_historian_package_id),
        )
        relationship_graph = tuple(relationships)
        integrity = KnowledgeIntegrityRecord(
            f"KIR-{document_sequence:06d}",
            knowledge.knowledge_id,
            provenance.complete,
            _relationships_consistent(relationship_graph, self._knowledge),
            False,
            provenance.complete and _relationships_consistent(relationship_graph, self._knowledge),
        )
        archive = InstitutionalArchiveRecord(
            f"IAR-{document_sequence:06d}",
            knowledge.knowledge_id,
            f"IKV-{document_sequence:06d}",
            True,
            utc_timestamp(),
        )
        retrieval = _retrieval_record(knowledge, tuple(self._knowledge))
        consolidation = KnowledgeConsolidationRecord(
            f"KCR-{document_sequence:06d}",
            knowledge.knowledge_id,
            None,
            True,
            "No duplicate content hash detected; knowledge added to institutional repository.",
        )
        self._classification[knowledge.knowledge_id] = classification
        self._hierarchy[knowledge.knowledge_id] = node
        self._relationships.extend(relationship_graph)
        self._archive.append(archive)
        self._retrieval[retrieval.index_id] = retrieval
        summary = InstitutionalRepositorySummary(
            f"IRS-{document_sequence:06d}",
            len(self._knowledge),
            len(self._hierarchy),
            len(self._relationships),
            len(self._archive),
            "healthy" if integrity.repository_integrity_verified else "attention",
        )
        academy = InstitutionalLearningPackage(
            f"ILP-{document_sequence:06d}",
            tuple(sorted(self._knowledge)),
            tuple(item.knowledge_id for item in self._knowledge.values() if item.classification in {KnowledgeClassification.DOCTRINE, KnowledgeClassification.ORGANIZATIONAL_STANDARD}),
            tuple(sorted(self._retrieval)),
        )
        return {
            "institutional_knowledge_report": self._persist_contract(
                "INSTITUTIONAL_KNOWLEDGE_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Institutional Knowledge Report.",
                {
                    "office_id": INSTITUTIONAL_KNOWLEDGE_OFFICE_ID,
                    "office_name": "Institutional Knowledge Office",
                    "institutional_knowledge_repository": tuple(self._knowledge.values()),
                    "knowledge_classification_registry": tuple(self._classification.values()),
                    "provenance_archive": (provenance,),
                    "knowledge_consolidation_register": (consolidation,),
                },
            ),
            "knowledge_relationship_report": self._persist_contract(
                "KNOWLEDGE_RELATIONSHIP_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Knowledge Relationship Report.",
                {
                    "knowledge_hierarchy_database": tuple(self._hierarchy.values()),
                    "knowledge_relationship_graph": tuple(self._relationships),
                    "retrieval_index": retrieval,
                },
            ),
            "knowledge_integrity_report": self._persist_contract(
                "KNOWLEDGE_INTEGRITY_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Knowledge Integrity Report.",
                {
                    "knowledge_integrity_record": integrity,
                    "provenance_verification_archive": (provenance,),
                    "repository_history_archive": self.institutional_archive,
                },
            ),
            "institutional_repository_summary": self._persist_contract(
                "INSTITUTIONAL_REPOSITORY_SUMMARY",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Institutional Repository Summary.",
                {
                    "institutional_repository_summary": summary,
                    "institutional_learning_package": academy,
                    "validated_reference_library": academy.validated_reference_ids,
                    "organizational_best_practices_repository": academy.best_practice_ids,
                },
            ),
        }

    def retrieve(self, query: str) -> tuple[InstitutionalKnowledgeArtifact, ...]:
        """Retrieve knowledge deterministically by normalized terms."""
        terms = tuple(_normalize_terms(query))
        matches = []
        for knowledge in self._knowledge.values():
            haystack = set(_normalize_terms(f"{knowledge.title} {knowledge.classification.value} {' '.join(knowledge.provenance_ids)}"))
            if all(term in haystack for term in terms):
                matches.append(knowledge)
        return tuple(sorted(matches, key=lambda item: item.knowledge_id))

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


def _duplicate_of(knowledge: InstitutionalKnowledgeArtifact, existing: dict[str, InstitutionalKnowledgeArtifact]) -> str | None:
    for item in existing.values():
        if item.content_hash == knowledge.content_hash:
            return item.knowledge_id
    return None


def _hierarchy_node(
    knowledge: InstitutionalKnowledgeArtifact,
    parent_knowledge_id: str | None,
    existing: dict[str, KnowledgeHierarchyNode],
) -> KnowledgeHierarchyNode:
    if parent_knowledge_id and parent_knowledge_id in existing:
        parent_path = existing[parent_knowledge_id].path
    elif parent_knowledge_id:
        parent_path = (parent_knowledge_id,)
    else:
        parent_path = ()
    path = (*parent_path, knowledge.knowledge_id)
    return KnowledgeHierarchyNode(
        f"KHN-{hashlib.sha256(':'.join(path).encode('utf-8')).hexdigest()[:8].upper()}",
        knowledge.knowledge_id,
        parent_knowledge_id,
        path,
        len(path) - 1,
    )


def _relationships_consistent(relationships: tuple[KnowledgeRelationship, ...], knowledge: dict[str, InstitutionalKnowledgeArtifact]) -> bool:
    return all(edge.source_knowledge_id in knowledge and (edge.target_knowledge_id in knowledge or edge.target_knowledge_id.startswith("EXT-")) for edge in relationships)


def _retrieval_record(knowledge: InstitutionalKnowledgeArtifact, knowledge_ids: tuple[str, ...]) -> RetrievalIndexRecord:
    terms = tuple(_normalize_terms(f"{knowledge.title} {knowledge.classification.value} {' '.join(knowledge.provenance_ids)}"))
    return RetrievalIndexRecord(
        f"KRI-{hashlib.sha256(':'.join(terms).encode('utf-8')).hexdigest()[:8].upper()}",
        terms,
        tuple(sorted(knowledge_ids)),
    )


def _normalize_terms(value: str) -> tuple[str, ...]:
    return tuple(term for term in "".join(char.lower() if char.isalnum() else " " for char in value).split() if term)


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
        produced_by_staff_id=INSTITUTIONAL_KNOWLEDGE_STAFF_ID,
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
