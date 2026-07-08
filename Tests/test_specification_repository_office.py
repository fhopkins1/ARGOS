from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402
from argos.librarian import (  # noqa: E402
    SpecificationLifecycleState,
    SpecificationMetadata,
    SpecificationRepositoryOffice,
    SpecificationType,
)


def config() -> ConfigurationService:
    return ConfigurationService.load(
        {
            "environment": "development",
            "config_version": "1.0.0",
            "schema_version": "1.0.0",
            "log_level": "INFO",
            "live_trading_enabled": False,
            "feature_flags": {},
            "secret_references": [],
        },
        {},
    )


def specification(specification_id: str = "EO-073", title: str = "Specification Repository Office") -> SpecificationMetadata:
    return SpecificationMetadata(
        specification_id,
        title,
        SpecificationType.ENGINEERING_ORDER,
        "LIBRARIAN-GROUP",
        "1.0.0",
        ("APPROVAL-LIB", "APPROVAL-EXEC"),
        ("EO-072",),
        ("DOC-072",),
        ("src/argos/librarian/specification_repository.py",),
        ("PROMPT-SRO-073",),
        ("DB-SPEC-FOUNDATION",),
        ("API-SPEC-FOUNDATION",),
        ("TS-073",),
    )


def register(
    office: SpecificationRepositoryOffice,
    *,
    metadata: SpecificationMetadata | None = None,
    approvals: tuple[str, ...] = ("APPROVAL-LIB", "APPROVAL-EXEC"),
    known: tuple[str, ...] = ("EO-072",),
    conflicts: tuple[str, ...] = (),
    sequence: int = 7301,
):
    return office.register_specification(
        metadata or specification(),
        "EO-072",
        "HASH-073",
        ("APPROVAL-LIB", "APPROVAL-EXEC"),
        approvals,
        known,
        conflicts,
        "CF-001",
        "TC-001",
        sequence,
    )


class SpecificationRepositoryOfficeTests(unittest.TestCase):
    def test_repository_architecture_metadata_lifecycle_and_audit_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = SpecificationRepositoryOffice(config(), persistence, audit, PromptRepository())

        artifacts = register(office)

        repository = artifacts["specification_repository_architecture"].machine_payload["repository_record"]
        identifier = artifacts["specification_metadata_standard"].machine_payload["identifier_standard"]
        lifecycle = artifacts["specification_lifecycle_model"].machine_payload["lifecycle_record"]
        version = artifacts["specification_lifecycle_model"].machine_payload["version_record"]
        self.assertEqual(repository["specification_id"], "EO-073")
        self.assertEqual(repository["hierarchy_path"], ["EO-072", "EO-073"])
        self.assertTrue(identifier["identifier_valid"])
        self.assertEqual(lifecycle["new_state"], SpecificationLifecycleState.APPROVED.value)
        self.assertTrue(version["immutable"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["specification_repository_architecture"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_validation_detects_invalid_identifier_missing_dependency_and_incomplete_approval(self) -> None:
        office = SpecificationRepositoryOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        bad = specification("BAD-073")

        artifacts = register(office, metadata=bad, approvals=("APPROVAL-LIB",), known=())

        validation = artifacts["specification_metadata_standard"].machine_payload["validation_record"]
        traceability = artifacts["traceability_framework"].machine_payload["traceability_record"]
        dashboard = artifacts["repository_health_dashboard"].machine_payload["repository_health_dashboard"]
        lifecycle = artifacts["specification_lifecycle_model"].machine_payload["lifecycle_record"]
        self.assertIn("invalid_identifier", validation["validation_errors"])
        self.assertIn("missing_dependencies", validation["validation_errors"])
        self.assertIn("incomplete_approvals", validation["validation_errors"])
        self.assertFalse(traceability["complete"])
        self.assertEqual(lifecycle["new_state"], SpecificationLifecycleState.APPROVAL_PENDING.value)
        self.assertEqual(dashboard["dependency_violation_count"], 1)

    def test_duplicate_and_conflict_detection_are_reported_without_overwriting_history(self) -> None:
        office = SpecificationRepositoryOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        register(office)

        artifacts = register(office, metadata=specification("EO-074"), conflicts=("EO-073",), sequence=7310)

        validation = artifacts["specification_metadata_standard"].machine_payload["validation_record"]
        dashboard = artifacts["repository_health_dashboard"].machine_payload["repository_health_dashboard"]
        self.assertTrue(validation["duplicate_detected"])
        self.assertTrue(validation["conflict_detected"])
        self.assertEqual(dashboard["duplicate_count"], 1)
        self.assertEqual(dashboard["conflict_count"], 1)
        self.assertEqual(len(office.version_history), 2)

    def test_search_architecture_and_query_return_deterministic_results(self) -> None:
        office = SpecificationRepositoryOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = register(office)
        matches = office.search("repository office")

        search_index = artifacts["repository_search_architecture"].machine_payload["search_index"]
        self.assertIn("repository", search_index["normalized_terms"])
        self.assertEqual(tuple(item.specification_id for item in matches), ("EO-073",))

    def test_governance_framework_and_system_prompt_are_complete(self) -> None:
        office = SpecificationRepositoryOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = office.system_prompt()
        artifacts = register(office)

        governance = artifacts["repository_health_dashboard"].machine_payload["specification_governance_framework"]
        self.assertIn("Specification Repository Office", prompt.prompt_text)
        self.assertIn("version controlled", prompt.prompt_text)
        self.assertTrue(governance["repository_metrics_specified"])
        self.assertTrue(governance["validation_procedures_established"])
        self.assertTrue(governance["change_management_documented"])
        self.assertTrue(governance["codex_prompt_complete"])


if __name__ == "__main__":
    unittest.main()
