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
    InstitutionalKnowledgeArtifact,
    InstitutionalKnowledgeOffice,
    KnowledgeClassification,
    KnowledgeRelationType,
    KnowledgeRelationship,
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


def knowledge(knowledge_id: str = "KNOW-071", content_hash: str = "HASH-071", classification: KnowledgeClassification = KnowledgeClassification.DOCTRINE) -> InstitutionalKnowledgeArtifact:
    return InstitutionalKnowledgeArtifact(
        knowledge_id,
        "Evidence-first decision discipline",
        classification,
        "HCP-069",
        True,
        content_hash,
        ("EV-PERF-1", "EV-HYP-1", "DOC-6801"),
        ("DOC-6801", "DOC-6901"),
    )


class InstitutionalKnowledgeOfficeTests(unittest.TestCase):
    def test_validated_knowledge_is_received_persisted_and_audited(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = InstitutionalKnowledgeOffice(config(), persistence, audit, PromptRepository())

        artifacts = office.receive_validated_knowledge(knowledge(), None, (), "CF-001", "TC-001", 7101)

        report = artifacts["institutional_knowledge_report"]
        self.assertEqual(report.contract_type, "INSTITUTIONAL_KNOWLEDGE_REPORT")
        self.assertEqual(report.machine_payload["institutional_knowledge_repository"][0]["knowledge_id"], "KNOW-071")
        self.assertEqual(report.machine_payload["knowledge_classification_registry"][0]["classification"], KnowledgeClassification.DOCTRINE.value)
        self.assertTrue(report.machine_payload["provenance_archive"][0]["complete"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_hierarchy_relationships_and_retrieval_are_operational(self) -> None:
        office = InstitutionalKnowledgeOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.receive_validated_knowledge(knowledge("ROOT-071", "HASH-ROOT", KnowledgeClassification.ORGANIZATIONAL_STANDARD), None, (), "CF-001", "TC-001", 7110)
        relation = KnowledgeRelationship("REL-071", "KNOW-071", "ROOT-071", KnowledgeRelationType.REFINES, "PROV-071")

        artifacts = office.receive_validated_knowledge(knowledge(), "ROOT-071", (relation,), "CF-001", "TC-001", 7115)

        relationship_report = artifacts["knowledge_relationship_report"].machine_payload
        hierarchy = relationship_report["knowledge_hierarchy_database"]
        self.assertEqual(hierarchy[1]["parent_knowledge_id"], "ROOT-071")
        self.assertEqual(relationship_report["knowledge_relationship_graph"][0]["relation_type"], KnowledgeRelationType.REFINES.value)
        retrieved = office.retrieve("evidence decision discipline")
        self.assertEqual(tuple(item.knowledge_id for item in retrieved), ("KNOW-071", "ROOT-071"))

    def test_duplicate_detection_consolidates_without_overwriting_archive(self) -> None:
        office = InstitutionalKnowledgeOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.receive_validated_knowledge(knowledge("KNOW-A", "HASH-DUP"), None, (), "CF-001", "TC-001", 7120)

        artifacts = office.receive_validated_knowledge(knowledge("KNOW-B", "HASH-DUP"), None, (), "CF-001", "TC-001", 7125)

        report = artifacts["institutional_knowledge_report"].machine_payload
        consolidation = report["knowledge_consolidation_record"]
        self.assertTrue(report["duplicate_knowledge_detected"])
        self.assertEqual(consolidation["duplicate_of"], "KNOW-A")
        self.assertEqual(len(office.institutional_archive), 1)

    def test_integrity_summary_and_academy_deliverables_are_generated(self) -> None:
        office = InstitutionalKnowledgeOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = office.receive_validated_knowledge(knowledge(), None, (), "CF-001", "TC-001", 7130)

        integrity = artifacts["knowledge_integrity_report"].machine_payload["knowledge_integrity_record"]
        summary = artifacts["institutional_repository_summary"].machine_payload["institutional_repository_summary"]
        academy = artifacts["institutional_repository_summary"].machine_payload["institutional_learning_package"]
        self.assertTrue(integrity["provenance_complete"])
        self.assertTrue(integrity["repository_integrity_verified"])
        self.assertEqual(summary["repository_health"], "healthy")
        self.assertIn("KNOW-071", academy["validated_reference_ids"])
        self.assertIn("KNOW-071", academy["best_practice_ids"])

    def test_inconsistent_relationship_marks_integrity_attention(self) -> None:
        office = InstitutionalKnowledgeOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        bad_relation = KnowledgeRelationship("REL-BAD", "KNOW-071", "MISSING", KnowledgeRelationType.SUPPORTS, "PROV-BAD")

        artifacts = office.receive_validated_knowledge(knowledge(), None, (bad_relation,), "CF-001", "TC-001", 7140)

        integrity = artifacts["knowledge_integrity_report"].machine_payload["knowledge_integrity_record"]
        summary = artifacts["institutional_repository_summary"].machine_payload["institutional_repository_summary"]
        self.assertFalse(integrity["relationships_consistent"])
        self.assertEqual(summary["repository_health"], "attention")


if __name__ == "__main__":
    unittest.main()
