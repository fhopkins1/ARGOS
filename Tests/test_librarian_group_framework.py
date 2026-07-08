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
    DoctrineStatus,
    InstitutionalKnowledgeArtifact,
    KnowledgeClassification,
    LibrarianGroup,
    librarian_office_templates,
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


def knowledge(doctrine_candidate: bool = True, references: tuple[str, ...] = ("DOC-6801", "DOC-6901")) -> InstitutionalKnowledgeArtifact:
    return InstitutionalKnowledgeArtifact(
        "KNOW-070",
        "Evidence-first decision discipline",
        KnowledgeClassification.DOCTRINE,
        "HCP-069",
        doctrine_candidate,
        "HASH-070",
        ("EV-PERF-1", "EV-HYP-1", "DOC-6801"),
        references,
    )


class LibrarianGroupFrameworkTests(unittest.TestCase):
    def test_librarian_office_templates_exist(self) -> None:
        templates = librarian_office_templates()

        self.assertEqual(len(templates), 6)
        self.assertIn("Doctrine Management Office", tuple(item.name for item in templates))

    def test_validated_knowledge_is_promoted_to_authoritative_doctrine(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        librarian = LibrarianGroup(config(), persistence, audit, PromptRepository())

        artifacts = librarian.promote_knowledge(knowledge(), "HCP-069", True, "CF-001", "TC-001", 7001)

        self.assertIn("institutional_knowledge_report", artifacts)
        self.assertIn("doctrine_status_report", artifacts)
        report = artifacts["institutional_knowledge_report"]
        doctrine = artifacts["doctrine_status_report"].machine_payload["doctrine_registry"][0]
        self.assertEqual(report.contract_type, "LIBRARIAN_INSTITUTIONAL_KNOWLEDGE_REPORT")
        self.assertEqual(doctrine["status"], DoctrineStatus.AUTHORITATIVE.value)
        self.assertEqual(len(librarian.knowledge_version_archive), 1)
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_candidate_knowledge_is_not_authoritative_without_authorization(self) -> None:
        librarian = LibrarianGroup(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = librarian.promote_knowledge(knowledge(), "HCP-069", False, "CF-001", "TC-001", 7010)

        doctrine = artifacts["doctrine_status_report"].machine_payload["doctrine_registry"][0]
        promotion = artifacts["doctrine_status_report"].machine_payload["knowledge_promotion_register"][0]
        self.assertEqual(doctrine["status"], DoctrineStatus.CANDIDATE.value)
        self.assertFalse(promotion["promoted"])
        self.assertIsNone(promotion["doctrine_revision_id"])

    def test_reference_integrity_and_distribution_are_reported(self) -> None:
        librarian = LibrarianGroup(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = librarian.promote_knowledge(knowledge(references=("DOC-6801", "DOC-6901")), "HCP-069", True, "CF-001", "TC-001", 7020)

        integrity = artifacts["repository_integrity_report"].machine_payload["repository_integrity_report"]
        graph = artifacts["repository_integrity_report"].machine_payload["reference_graph"]
        summary = artifacts["organizational_knowledge_summary"].machine_payload["organizational_knowledge_summary"]
        distribution = artifacts["organizational_knowledge_summary"].machine_payload["knowledge_distribution_record"]
        self.assertTrue(integrity["repository_integrity_operational"])
        self.assertTrue(graph["reference_integrity_verified"])
        self.assertEqual(summary["repository_health"], "healthy")
        self.assertTrue(distribution["distributed"])
        self.assertIn("Academy", distribution["target_consumers"])

    def test_broken_reference_marks_repository_attention(self) -> None:
        librarian = LibrarianGroup(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = librarian.promote_knowledge(knowledge(references=("DOC-6801", "")), "HCP-069", True, "CF-001", "TC-001", 7030)

        graph = artifacts["repository_integrity_report"].machine_payload["reference_graph"]
        summary = artifacts["organizational_knowledge_summary"].machine_payload["organizational_knowledge_summary"]
        self.assertFalse(graph["reference_integrity_verified"])
        self.assertEqual(summary["repository_health"], "attention")

    def test_duplicate_knowledge_is_rejected_to_preserve_versions(self) -> None:
        librarian = LibrarianGroup(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        librarian.promote_knowledge(knowledge(), "HCP-069", True, "CF-001", "TC-001", 7040)

        with self.assertRaises(ValueError):
            librarian.promote_knowledge(knowledge(), "HCP-069", True, "CF-001", "TC-001", 7045)


if __name__ == "__main__":
    unittest.main()
