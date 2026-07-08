"""Doctrine Management Office."""

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

from .group import LIBRARIAN_GROUP_ID, DoctrineStatus, KnowledgeClassification


DOCTRINE_MANAGEMENT_OFFICE_ID = "LIBRARIAN-OFFICE-002"
DOCTRINE_MANAGEMENT_STAFF_ID = "STF-082"


class DoctrineLifecycleState(str, Enum):
    """Doctrine lifecycle state."""

    PROPOSED = "proposed"
    EVIDENCE_VERIFIED = "evidence_verified"
    APPROVAL_PENDING = "approval_pending"
    AUTHORITATIVE = "authoritative"
    AMENDED = "amended"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class DoctrineReviewCadence(str, Enum):
    """Doctrine review cadence."""

    QUARTERLY = "quarterly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"


@dataclass(frozen=True)
class DoctrineMetadata:
    """Doctrine metadata schema."""

    doctrine_id: str
    title: str
    knowledge_id: str
    classification: KnowledgeClassification
    owner_group_id: str
    evidence_ids: tuple[str, ...]
    approval_ids: tuple[str, ...]
    dependency_ids: tuple[str, ...]
    historical_justification_ids: tuple[str, ...]


@dataclass(frozen=True)
class DoctrineHierarchyNode:
    """Deterministic doctrine hierarchy node."""

    node_id: str
    doctrine_id: str
    parent_doctrine_id: str | None
    path: tuple[str, ...]
    depth: int


@dataclass(frozen=True)
class DoctrineLifecycleRecord:
    """Doctrine lifecycle model record."""

    lifecycle_id: str
    doctrine_id: str
    previous_state: DoctrineLifecycleState
    new_state: DoctrineLifecycleState
    deterministic_reason: str
    timestamp_utc: str


@dataclass(frozen=True)
class DoctrineVersionRecord:
    """Doctrine version control record."""

    version_id: str
    doctrine_id: str
    version: str
    parent_version_id: str | None
    content_hash: str
    immutable: bool
    timestamp_utc: str


@dataclass(frozen=True)
class AmendmentWorkflowRecord:
    """Doctrine amendment workflow."""

    amendment_id: str
    doctrine_id: str
    proposed_version: str
    required_approval_ids: tuple[str, ...]
    received_approval_ids: tuple[str, ...]
    approved: bool


@dataclass(frozen=True)
class DoctrineDependencyGraph:
    """Doctrine dependency graph specification."""

    graph_id: str
    doctrine_id: str
    dependency_ids: tuple[str, ...]
    missing_dependencies: tuple[str, ...]
    dependency_integrity_verified: bool


@dataclass(frozen=True)
class DoctrineConflictRecord:
    """Doctrine conflict resolution framework record."""

    conflict_id: str
    doctrine_id: str
    conflicting_doctrine_ids: tuple[str, ...]
    conflict_detected: bool
    resolution_procedure: str


@dataclass(frozen=True)
class DoctrineReviewSchedule:
    """Doctrine review schedule."""

    schedule_id: str
    doctrine_id: str
    cadence: DoctrineReviewCadence
    next_review_period: str
    formalized: bool


@dataclass(frozen=True)
class DoctrineDeprecationRecord:
    """Doctrine deprecation lifecycle."""

    deprecation_id: str
    doctrine_id: str
    superseded_by_doctrine_id: str | None
    deprecated: bool
    archived: bool


@dataclass(frozen=True)
class DoctrineGovernanceDashboard:
    """Governance dashboard metrics."""

    dashboard_id: str
    authoritative_count: int
    pending_approval_count: int
    conflict_count: int
    dependency_violation_count: int
    deprecated_count: int
    review_due_count: int


@dataclass(frozen=True)
class DoctrineSystemPrompt:
    """Doctrine Management Office prompt."""

    prompt_id: str
    version: str
    prompt_text: str


class DoctrineManagementOffice:
    """Constitutional governance layer for ARGOS doctrine."""

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
        self._versions: list[DoctrineVersionRecord] = []
        self._lifecycles: list[DoctrineLifecycleRecord] = []

    @property
    def version_history(self) -> tuple[DoctrineVersionRecord, ...]:
        """Return immutable doctrine version history."""
        return tuple(self._versions)

    def system_prompt(self) -> DoctrineSystemPrompt:
        """Return governing Doctrine Management prompt."""
        return DoctrineSystemPrompt(
            "PROMPT-DMO-072",
            "1.0.0",
            (
                "You are the Doctrine Management Office of ARGOS.\n\n"
                "Your responsibility is to govern the organization's permanent operational doctrine. Convert "
                "validated institutional knowledge into authoritative doctrine only after verifying evidence, "
                "approvals, dependencies, and historical justification.\n\n"
                "Maintain complete version history, preserve superseded doctrine, detect conflicts and dependency "
                "violations, enforce deterministic governance standards, and ensure every organizational rule "
                "remains fully auditable, reproducible, and traceable throughout its lifecycle."
            ),
        )

    def govern_doctrine(
        self,
        metadata: DoctrineMetadata,
        parent_doctrine_id: str | None,
        content_hash: str,
        proposed_version: str,
        required_approval_ids: tuple[str, ...],
        received_approval_ids: tuple[str, ...],
        known_doctrine_ids: tuple[str, ...],
        conflicting_doctrine_ids: tuple[str, ...],
        review_cadence: DoctrineReviewCadence,
        next_review_period: str,
        superseded_by_doctrine_id: str | None,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Govern a doctrine candidate through deterministic doctrine controls."""
        self.configuration_service.validate_startup()
        evidence_verified = bool(metadata.evidence_ids and metadata.historical_justification_ids)
        approvals_met = set(required_approval_ids).issubset(set(received_approval_ids))
        dependency_graph = _dependency_graph(metadata, known_doctrine_ids)
        conflict = _conflict(metadata.doctrine_id, conflicting_doctrine_ids)
        approved = evidence_verified and approvals_met and dependency_graph.dependency_integrity_verified and not conflict.conflict_detected
        state = DoctrineLifecycleState.AUTHORITATIVE if approved else DoctrineLifecycleState.APPROVAL_PENDING
        hierarchy = _hierarchy(metadata.doctrine_id, parent_doctrine_id)
        version = DoctrineVersionRecord(
            f"DV-{document_sequence:06d}",
            metadata.doctrine_id,
            proposed_version,
            self._versions[-1].version_id if self._versions else None,
            content_hash,
            True,
            utc_timestamp(),
        )
        lifecycle = DoctrineLifecycleRecord(
            f"DLR-{document_sequence:06d}",
            metadata.doctrine_id,
            DoctrineLifecycleState.PROPOSED,
            state,
            "Evidence, approvals, dependencies, and conflicts evaluated deterministically.",
            version.timestamp_utc,
        )
        amendment = AmendmentWorkflowRecord(
            f"AWR-{document_sequence:06d}",
            metadata.doctrine_id,
            proposed_version,
            required_approval_ids,
            received_approval_ids,
            approvals_met,
        )
        review = DoctrineReviewSchedule(
            f"DRS-{document_sequence:06d}",
            metadata.doctrine_id,
            review_cadence,
            next_review_period,
            True,
        )
        deprecation = DoctrineDeprecationRecord(
            f"DDR-{document_sequence:06d}",
            metadata.doctrine_id,
            superseded_by_doctrine_id,
            superseded_by_doctrine_id is not None,
            superseded_by_doctrine_id is not None,
        )
        dashboard = DoctrineGovernanceDashboard(
            f"DGD-{document_sequence:06d}",
            1 if approved else 0,
            0 if approvals_met else 1,
            1 if conflict.conflict_detected else 0,
            len(dependency_graph.missing_dependencies),
            1 if deprecation.deprecated else 0,
            0,
        )
        self._versions.append(version)
        self._lifecycles.append(lifecycle)
        return {
            "doctrine_hierarchy_specification": self._persist_contract(
                "DOCTRINE_HIERARCHY_SPECIFICATION",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Doctrine Hierarchy Specification.",
                {"doctrine_hierarchy": hierarchy, "doctrine_metadata_schema": metadata, "doctrine_system_prompt": self.system_prompt()},
            ),
            "doctrine_lifecycle_model": self._persist_contract(
                "DOCTRINE_LIFECYCLE_MODEL",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Doctrine Lifecycle Model.",
                {"doctrine_lifecycle_record": lifecycle, "doctrine_deprecation_standard": deprecation},
            ),
            "version_control_standard": self._persist_contract(
                "DOCTRINE_VERSION_CONTROL_STANDARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Version Control Standard.",
                {"doctrine_version_record": version, "complete_version_history": self.version_history, "superseded_doctrine_preserved": True},
            ),
            "amendment_workflow": self._persist_contract(
                "DOCTRINE_AMENDMENT_WORKFLOW",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Amendment Workflow.",
                {"amendment_workflow_record": amendment, "approval_requirements_codified": True},
            ),
            "dependency_graph_specification": self._persist_contract(
                "DOCTRINE_DEPENDENCY_GRAPH_SPECIFICATION",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Dependency Graph Specification.",
                {"doctrine_dependency_graph": dependency_graph, "conflict_resolution_framework": conflict},
            ),
            "governance_dashboard_definition": self._persist_contract(
                "DOCTRINE_GOVERNANCE_DASHBOARD_DEFINITION",
                case_file_id,
                trade_cycle_id,
                document_sequence + 5,
                "Governance Dashboard Definition.",
                {"doctrine_governance_dashboard": dashboard, "review_scheduling_framework": review, "deterministic_governance_principles_documented": True},
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


def _hierarchy(doctrine_id: str, parent_doctrine_id: str | None) -> DoctrineHierarchyNode:
    path = (parent_doctrine_id, doctrine_id) if parent_doctrine_id else (doctrine_id,)
    return DoctrineHierarchyNode(
        f"DHN-{hashlib.sha256(':'.join(path).encode('utf-8')).hexdigest()[:8].upper()}",
        doctrine_id,
        parent_doctrine_id,
        path,
        len(path) - 1,
    )


def _dependency_graph(metadata: DoctrineMetadata, known_doctrine_ids: tuple[str, ...]) -> DoctrineDependencyGraph:
    missing = tuple(item for item in metadata.dependency_ids if item not in known_doctrine_ids)
    return DoctrineDependencyGraph(
        f"DDG-{hashlib.sha256(metadata.doctrine_id.encode('utf-8')).hexdigest()[:8].upper()}",
        metadata.doctrine_id,
        metadata.dependency_ids,
        missing,
        not missing,
    )


def _conflict(doctrine_id: str, conflicting_doctrine_ids: tuple[str, ...]) -> DoctrineConflictRecord:
    return DoctrineConflictRecord(
        f"DCR-{hashlib.sha256(f'{doctrine_id}:{conflicting_doctrine_ids}'.encode('utf-8')).hexdigest()[:8].upper()}",
        doctrine_id,
        conflicting_doctrine_ids,
        bool(conflicting_doctrine_ids),
        "Suspend promotion, preserve conflict, require Executive and Librarian review." if conflicting_doctrine_ids else "No conflict resolution required.",
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
        produced_by_staff_id=DOCTRINE_MANAGEMENT_STAFF_ID,
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
