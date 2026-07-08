"""Specification Repository Office."""

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

from .group import LIBRARIAN_GROUP_ID


SPECIFICATION_REPOSITORY_OFFICE_ID = "LIBRARIAN-OFFICE-003"
SPECIFICATION_REPOSITORY_STAFF_ID = "STF-083"


class SpecificationType(str, Enum):
    """Authoritative specification type."""

    ENGINEERING_ORDER = "engineering_order"
    STAFF_SPECIFICATION = "staff_specification"
    INTERFACE_SPECIFICATION = "interface_specification"
    DATABASE_SPECIFICATION = "database_specification"
    API_SPECIFICATION = "api_specification"
    TEST_SPECIFICATION = "test_specification"
    PROMPT_SPECIFICATION = "prompt_specification"
    WORKFLOW_SPECIFICATION = "workflow_specification"
    SOFTWARE_MODULE_SPECIFICATION = "software_module_specification"
    ENGINEERING_STANDARD = "engineering_standard"


class SpecificationLifecycleState(str, Enum):
    """Specification lifecycle state."""

    DRAFT = "draft"
    VALIDATED = "validated"
    APPROVAL_PENDING = "approval_pending"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class SpecificationMetadata:
    """Specification metadata standard."""

    specification_id: str
    title: str
    specification_type: SpecificationType
    owner_group_id: str
    version: str
    approval_ids: tuple[str, ...]
    dependency_ids: tuple[str, ...]
    doctrine_ids: tuple[str, ...]
    implementation_reference_ids: tuple[str, ...]
    prompt_ids: tuple[str, ...]
    database_schema_ids: tuple[str, ...]
    api_contract_ids: tuple[str, ...]
    test_specification_ids: tuple[str, ...]


@dataclass(frozen=True)
class SpecificationRepositoryRecord:
    """Repository architecture record."""

    repository_record_id: str
    specification_id: str
    hierarchy_path: tuple[str, ...]
    specification_type: SpecificationType
    authoritative: bool
    immutable_history_preserved: bool


@dataclass(frozen=True)
class RepositoryIdentifierStandard:
    """Repository identifier standard."""

    standard_id: str
    specification_id: str
    required_prefix: str
    identifier_valid: bool
    deterministic_rule: str


@dataclass(frozen=True)
class SpecificationLifecycleRecord:
    """Specification lifecycle model."""

    lifecycle_id: str
    specification_id: str
    previous_state: SpecificationLifecycleState
    new_state: SpecificationLifecycleState
    deterministic_reason: str
    timestamp_utc: str


@dataclass(frozen=True)
class SpecificationVersionRecord:
    """Immutable specification version."""

    version_id: str
    specification_id: str
    version: str
    parent_version_id: str | None
    content_hash: str
    immutable: bool
    timestamp_utc: str


@dataclass(frozen=True)
class SpecificationValidationRecord:
    """Specification validation procedure result."""

    validation_id: str
    specification_id: str
    metadata_complete: bool
    identifier_valid: bool
    dependencies_resolved: bool
    approvals_complete: bool
    duplicate_detected: bool
    conflict_detected: bool
    validation_status: str
    validation_errors: tuple[str, ...]


@dataclass(frozen=True)
class SpecificationTraceabilityRecord:
    """Specification traceability framework record."""

    traceability_id: str
    specification_id: str
    dependency_ids: tuple[str, ...]
    doctrine_ids: tuple[str, ...]
    implementation_reference_ids: tuple[str, ...]
    prompt_ids: tuple[str, ...]
    database_schema_ids: tuple[str, ...]
    api_contract_ids: tuple[str, ...]
    test_specification_ids: tuple[str, ...]
    complete: bool


@dataclass(frozen=True)
class SpecificationSearchIndex:
    """Repository search architecture."""

    search_index_id: str
    normalized_terms: tuple[str, ...]
    specification_ids: tuple[str, ...]


@dataclass(frozen=True)
class SpecificationChangeManagementRecord:
    """Specification governance change management."""

    change_record_id: str
    specification_id: str
    proposed_version: str
    approved: bool
    required_approval_ids: tuple[str, ...]
    received_approval_ids: tuple[str, ...]
    preserved_previous_version: bool


@dataclass(frozen=True)
class RepositoryHealthDashboard:
    """Repository health dashboard metrics."""

    dashboard_id: str
    specification_count: int
    approved_count: int
    pending_count: int
    duplicate_count: int
    conflict_count: int
    dependency_violation_count: int
    missing_metadata_count: int


@dataclass(frozen=True)
class SpecificationGovernanceFramework:
    """Specification governance framework artifact."""

    governance_id: str
    repository_metrics_specified: bool
    validation_procedures_established: bool
    change_management_documented: bool
    traceability_model_complete: bool
    codex_prompt_complete: bool


@dataclass(frozen=True)
class SpecificationSystemPrompt:
    """Specification Repository Office prompt."""

    prompt_id: str
    version: str
    prompt_text: str


class SpecificationRepositoryOffice:
    """Authoritative repository for ARGOS engineering specifications."""

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
        self._specifications: dict[str, SpecificationMetadata] = {}
        self._versions: list[SpecificationVersionRecord] = []
        self._search_indexes: dict[str, SpecificationSearchIndex] = {}

    @property
    def version_history(self) -> tuple[SpecificationVersionRecord, ...]:
        """Return immutable specification version history."""
        return tuple(self._versions)

    def system_prompt(self) -> SpecificationSystemPrompt:
        """Return governing Specification Repository prompt."""
        return SpecificationSystemPrompt(
            "PROMPT-SRO-073",
            "1.0.0",
            (
                "You are the Specification Repository Office of ARGOS.\n\n"
                "Maintain the authoritative repository for every engineering specification used throughout the "
                "enterprise. Ensure every specification is version controlled, uniquely identified, fully traceable, "
                "dependency-aware, and approved before implementation. Detect conflicts, missing specifications, "
                "dependency violations, duplicate definitions, and repository inconsistencies. Preserve complete "
                "historical versions while providing deterministic engineering references for every organization, "
                "software module, AI office, workflow, prompt, database, API, and engineering standard within ARGOS."
            ),
        )

    def register_specification(
        self,
        metadata: SpecificationMetadata,
        parent_specification_id: str | None,
        content_hash: str,
        required_approval_ids: tuple[str, ...],
        received_approval_ids: tuple[str, ...],
        known_specification_ids: tuple[str, ...],
        conflicting_specification_ids: tuple[str, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Register and govern a specification through deterministic repository controls."""
        self.configuration_service.validate_startup()
        identifier = _identifier_standard(metadata)
        duplicate_detected = any(item.specification_id != metadata.specification_id and item.title == metadata.title for item in self._specifications.values())
        missing_dependencies = tuple(item for item in metadata.dependency_ids if item not in known_specification_ids and item not in self._specifications)
        approvals_complete = set(required_approval_ids).issubset(set(received_approval_ids))
        validation = _validation(metadata, identifier.identifier_valid, missing_dependencies, approvals_complete, duplicate_detected, conflicting_specification_ids)
        approved = validation.validation_status == "valid"
        lifecycle_state = SpecificationLifecycleState.APPROVED if approved else SpecificationLifecycleState.APPROVAL_PENDING
        repository_record = SpecificationRepositoryRecord(
            f"SRR-{document_sequence:06d}",
            metadata.specification_id,
            _hierarchy_path(metadata, parent_specification_id),
            metadata.specification_type,
            approved,
            True,
        )
        version = SpecificationVersionRecord(
            f"SVR-{document_sequence:06d}",
            metadata.specification_id,
            metadata.version,
            _parent_version_id(metadata.specification_id, self._versions),
            content_hash,
            True,
            utc_timestamp(),
        )
        lifecycle = SpecificationLifecycleRecord(
            f"SLC-{document_sequence:06d}",
            metadata.specification_id,
            SpecificationLifecycleState.DRAFT,
            lifecycle_state,
            "Metadata, identifier, approvals, dependencies, duplicates, and conflicts evaluated deterministically.",
            version.timestamp_utc,
        )
        traceability = SpecificationTraceabilityRecord(
            f"STR-{document_sequence:06d}",
            metadata.specification_id,
            metadata.dependency_ids,
            metadata.doctrine_ids,
            metadata.implementation_reference_ids,
            metadata.prompt_ids,
            metadata.database_schema_ids,
            metadata.api_contract_ids,
            metadata.test_specification_ids,
            not missing_dependencies and bool(metadata.doctrine_ids or metadata.implementation_reference_ids),
        )
        change = SpecificationChangeManagementRecord(
            f"SCM-{document_sequence:06d}",
            metadata.specification_id,
            metadata.version,
            approvals_complete,
            required_approval_ids,
            received_approval_ids,
            _parent_version_id(metadata.specification_id, self._versions) is not None or metadata.specification_id not in self._specifications,
        )
        if not duplicate_detected:
            self._specifications[metadata.specification_id] = metadata
        self._versions.append(version)
        search = _search_index(metadata, tuple(sorted(self._specifications)))
        self._search_indexes[search.search_index_id] = search
        dashboard = RepositoryHealthDashboard(
            f"RHD-{document_sequence:06d}",
            len(self._specifications),
            1 if approved else 0,
            0 if approved else 1,
            1 if duplicate_detected else 0,
            1 if conflicting_specification_ids else 0,
            len(missing_dependencies),
            0 if validation.metadata_complete else 1,
        )
        governance = SpecificationGovernanceFramework(
            f"SGF-{document_sequence:06d}",
            True,
            True,
            True,
            traceability.complete,
            True,
        )
        return {
            "specification_repository_architecture": self._persist_contract(
                "SPECIFICATION_REPOSITORY_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Specification Repository Architecture.",
                {"repository_record": repository_record, "specification_hierarchy": repository_record.hierarchy_path, "system_prompt": self.system_prompt()},
            ),
            "specification_metadata_standard": self._persist_contract(
                "SPECIFICATION_METADATA_STANDARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Specification Metadata Standard.",
                {"specification_metadata": metadata, "identifier_standard": identifier, "validation_record": validation},
            ),
            "specification_lifecycle_model": self._persist_contract(
                "SPECIFICATION_LIFECYCLE_MODEL",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Specification Lifecycle Model.",
                {"lifecycle_record": lifecycle, "version_record": version, "change_management_record": change, "complete_version_history": self.version_history},
            ),
            "traceability_framework": self._persist_contract(
                "SPECIFICATION_TRACEABILITY_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Traceability Framework.",
                {"traceability_record": traceability, "missing_dependencies": missing_dependencies, "conflicting_specification_ids": conflicting_specification_ids},
            ),
            "repository_search_architecture": self._persist_contract(
                "SPECIFICATION_REPOSITORY_SEARCH_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Repository Search Architecture.",
                {"search_index": search, "search_indexes": tuple(self._search_indexes.values())},
            ),
            "repository_health_dashboard": self._persist_contract(
                "SPECIFICATION_REPOSITORY_HEALTH_DASHBOARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 5,
                "Repository Health Dashboard.",
                {"repository_health_dashboard": dashboard, "specification_governance_framework": governance},
            ),
        }

    def search(self, query: str) -> tuple[SpecificationMetadata, ...]:
        """Search specifications deterministically by normalized terms."""
        terms = tuple(_normalize_terms(query))
        matches = []
        for specification in self._specifications.values():
            haystack = set(_normalize_terms(_search_text(specification)))
            if all(term in haystack for term in terms):
                matches.append(specification)
        return tuple(sorted(matches, key=lambda item: item.specification_id))

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


def _identifier_standard(metadata: SpecificationMetadata) -> RepositoryIdentifierStandard:
    required_prefix = {
        SpecificationType.ENGINEERING_ORDER: "EO-",
        SpecificationType.STAFF_SPECIFICATION: "SP-",
        SpecificationType.INTERFACE_SPECIFICATION: "IF-",
        SpecificationType.DATABASE_SPECIFICATION: "DB-",
        SpecificationType.API_SPECIFICATION: "API-",
        SpecificationType.TEST_SPECIFICATION: "TS-",
        SpecificationType.PROMPT_SPECIFICATION: "PROMPT-",
        SpecificationType.WORKFLOW_SPECIFICATION: "WF-",
        SpecificationType.SOFTWARE_MODULE_SPECIFICATION: "MOD-",
        SpecificationType.ENGINEERING_STANDARD: "STD-",
    }[metadata.specification_type]
    return RepositoryIdentifierStandard(
        f"RIS-{hashlib.sha256(metadata.specification_id.encode('utf-8')).hexdigest()[:8].upper()}",
        metadata.specification_id,
        required_prefix,
        metadata.specification_id.startswith(required_prefix),
        f"{metadata.specification_type.value} identifiers shall begin with {required_prefix}.",
    )


def _validation(
    metadata: SpecificationMetadata,
    identifier_valid: bool,
    missing_dependencies: tuple[str, ...],
    approvals_complete: bool,
    duplicate_detected: bool,
    conflicting_specification_ids: tuple[str, ...],
) -> SpecificationValidationRecord:
    metadata_complete = all(
        (
            metadata.specification_id,
            metadata.title,
            metadata.owner_group_id,
            metadata.version,
            metadata.approval_ids,
        )
    )
    errors: list[str] = []
    if not metadata_complete:
        errors.append("missing_metadata")
    if not identifier_valid:
        errors.append("invalid_identifier")
    if missing_dependencies:
        errors.append("missing_dependencies")
    if not approvals_complete:
        errors.append("incomplete_approvals")
    if duplicate_detected:
        errors.append("duplicate_definition")
    if conflicting_specification_ids:
        errors.append("conflicting_specifications")
    return SpecificationValidationRecord(
        f"SVL-{hashlib.sha256(metadata.specification_id.encode('utf-8')).hexdigest()[:8].upper()}",
        metadata.specification_id,
        metadata_complete,
        identifier_valid,
        not missing_dependencies,
        approvals_complete,
        duplicate_detected,
        bool(conflicting_specification_ids),
        "valid" if not errors else "attention_required",
        tuple(errors),
    )


def _hierarchy_path(metadata: SpecificationMetadata, parent_specification_id: str | None) -> tuple[str, ...]:
    return (parent_specification_id, metadata.specification_id) if parent_specification_id else (metadata.specification_type.value, metadata.specification_id)


def _parent_version_id(specification_id: str, versions: list[SpecificationVersionRecord]) -> str | None:
    for version in reversed(versions):
        if version.specification_id == specification_id:
            return version.version_id
    return None


def _search_index(metadata: SpecificationMetadata, specification_ids: tuple[str, ...]) -> SpecificationSearchIndex:
    terms = tuple(_normalize_terms(_search_text(metadata)))
    return SpecificationSearchIndex(
        f"SSI-{hashlib.sha256(':'.join(terms).encode('utf-8')).hexdigest()[:8].upper()}",
        terms,
        specification_ids,
    )


def _search_text(metadata: SpecificationMetadata) -> str:
    return " ".join(
        (
            metadata.specification_id,
            metadata.title,
            metadata.specification_type.value,
            metadata.owner_group_id,
            metadata.version,
            " ".join(metadata.dependency_ids),
            " ".join(metadata.doctrine_ids),
            " ".join(metadata.implementation_reference_ids),
            " ".join(metadata.prompt_ids),
            " ".join(metadata.database_schema_ids),
            " ".join(metadata.api_contract_ids),
            " ".join(metadata.test_specification_ids),
        )
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
        produced_by_staff_id=SPECIFICATION_REPOSITORY_STAFF_ID,
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
