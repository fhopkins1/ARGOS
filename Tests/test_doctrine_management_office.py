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
    DoctrineLifecycleState,
    DoctrineManagementOffice,
    DoctrineMetadata,
    DoctrineReviewCadence,
    KnowledgeClassification,
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


def metadata(dependencies: tuple[str, ...] = ("DOC-ROOT",)) -> DoctrineMetadata:
    return DoctrineMetadata(
        "DOC-072",
        "Evidence-first decision discipline",
        "KNOW-072",
        KnowledgeClassification.DOCTRINE,
        "DEP-002",
        ("EV-1", "EV-2"),
        ("APPROVAL-EXEC", "APPROVAL-LIB"),
        dependencies,
        ("HIST-1",),
    )


def govern(office: DoctrineManagementOffice, *, conflicts: tuple[str, ...] = (), approvals: tuple[str, ...] = ("APPROVAL-EXEC", "APPROVAL-LIB"), dependencies: tuple[str, ...] = ("DOC-ROOT",), superseded_by: str | None = None):
    return office.govern_doctrine(
        metadata(dependencies),
        "DOC-ROOT",
        "HASH-072",
        "1.0.0",
        ("APPROVAL-EXEC", "APPROVAL-LIB"),
        approvals,
        ("DOC-ROOT",),
        conflicts,
        DoctrineReviewCadence.ANNUAL,
        "2027-Q3",
        superseded_by,
        "CF-001",
        "TC-001",
        7201,
    )


class DoctrineManagementOfficeTests(unittest.TestCase):
    def test_doctrine_hierarchy_lifecycle_and_versioning_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = DoctrineManagementOffice(config(), persistence, audit, PromptRepository())

        artifacts = govern(office)

        hierarchy = artifacts["doctrine_hierarchy_specification"].machine_payload["doctrine_hierarchy"]
        lifecycle = artifacts["doctrine_lifecycle_model"].machine_payload["doctrine_lifecycle_record"]
        version = artifacts["version_control_standard"].machine_payload["doctrine_version_record"]
        self.assertEqual(hierarchy["parent_doctrine_id"], "DOC-ROOT")
        self.assertEqual(lifecycle["new_state"], DoctrineLifecycleState.AUTHORITATIVE.value)
        self.assertTrue(version["immutable"])
        self.assertEqual(len(office.version_history), 1)
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["doctrine_hierarchy_specification"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_approval_requirements_are_codified_and_block_incomplete_approval(self) -> None:
        office = DoctrineManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = govern(office, approvals=("APPROVAL-EXEC",))

        amendment = artifacts["amendment_workflow"].machine_payload["amendment_workflow_record"]
        lifecycle = artifacts["doctrine_lifecycle_model"].machine_payload["doctrine_lifecycle_record"]
        dashboard = artifacts["governance_dashboard_definition"].machine_payload["doctrine_governance_dashboard"]
        self.assertFalse(amendment["approved"])
        self.assertEqual(lifecycle["new_state"], DoctrineLifecycleState.APPROVAL_PENDING.value)
        self.assertEqual(dashboard["pending_approval_count"], 1)

    def test_dependency_graph_and_conflict_resolution_are_established(self) -> None:
        office = DoctrineManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = govern(office, conflicts=("DOC-CONFLICT",), dependencies=("DOC-MISSING",))

        dependency = artifacts["dependency_graph_specification"].machine_payload["doctrine_dependency_graph"]
        conflict = artifacts["dependency_graph_specification"].machine_payload["conflict_resolution_framework"]
        dashboard = artifacts["governance_dashboard_definition"].machine_payload["doctrine_governance_dashboard"]
        self.assertFalse(dependency["dependency_integrity_verified"])
        self.assertEqual(dependency["missing_dependencies"], ["DOC-MISSING"])
        self.assertTrue(conflict["conflict_detected"])
        self.assertIn("Suspend promotion", conflict["resolution_procedure"])
        self.assertEqual(dashboard["conflict_count"], 1)
        self.assertEqual(dashboard["dependency_violation_count"], 1)

    def test_review_scheduling_and_deprecation_lifecycle_are_implemented(self) -> None:
        office = DoctrineManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = govern(office, superseded_by="DOC-073")

        review = artifacts["governance_dashboard_definition"].machine_payload["review_scheduling_framework"]
        deprecation = artifacts["doctrine_lifecycle_model"].machine_payload["doctrine_deprecation_standard"]
        dashboard = artifacts["governance_dashboard_definition"].machine_payload["doctrine_governance_dashboard"]
        self.assertEqual(review["cadence"], DoctrineReviewCadence.ANNUAL.value)
        self.assertTrue(review["formalized"])
        self.assertTrue(deprecation["deprecated"])
        self.assertTrue(deprecation["archived"])
        self.assertEqual(dashboard["deprecated_count"], 1)

    def test_system_prompt_and_governance_principles_are_complete(self) -> None:
        office = DoctrineManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = office.system_prompt()
        artifacts = govern(office)

        self.assertIn("Doctrine Management Office", prompt.prompt_text)
        self.assertIn("verifying evidence, approvals, dependencies", prompt.prompt_text)
        self.assertTrue(artifacts["governance_dashboard_definition"].machine_payload["deterministic_governance_principles_documented"])


if __name__ == "__main__":
    unittest.main()
