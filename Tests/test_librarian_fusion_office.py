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
    KnowledgeCapabilityAssessment,
    KnowledgeCapabilityType,
    KnowledgeRiskLevel,
    LibrarianFusionOffice,
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


def assessments() -> tuple[KnowledgeCapabilityAssessment, ...]:
    return (
        KnowledgeCapabilityAssessment("CAP-IK", KnowledgeCapabilityType.INSTITUTIONAL_KNOWLEDGE, 0.91, 0.88, 0.86, 0.92, True, (), (), ("EV-IK",)),
        KnowledgeCapabilityAssessment("CAP-DOC", KnowledgeCapabilityType.DOCTRINE_MANAGEMENT, 0.89, 0.82, 0.81, 0.90, True, (), (), ("EV-DOC",)),
        KnowledgeCapabilityAssessment("CAP-SPEC", KnowledgeCapabilityType.SPECIFICATION_REPOSITORY, 0.78, 0.70, 0.74, 0.85, True, ("DEF-SPEC-CONSISTENCY",), ("RISK-SPEC-ACCESS",), ("EV-SPEC",)),
        KnowledgeCapabilityAssessment("CAP-GRAPH", KnowledgeCapabilityType.KNOWLEDGE_GRAPH, 0.84, 0.79, 0.76, 0.88, True, (), (), ("EV-GRAPH",)),
        KnowledgeCapabilityAssessment("CAP-LEARN", KnowledgeCapabilityType.LEARNING_INTEGRATION, 0.86, 0.83, 0.80, 0.91, True, (), (), ("EV-LEARN",)),
    )


def fuse(office: LibrarianFusionOffice, capability_assessments: tuple[KnowledgeCapabilityAssessment, ...] = assessments()):
    return office.fuse_knowledge_capabilities(capability_assessments, "CF-001", "TC-001", 7601)


class LibrarianFusionOfficeTests(unittest.TestCase):
    def test_integration_architecture_and_audit_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = LibrarianFusionOffice(config(), persistence, audit, PromptRepository())

        artifacts = fuse(office)

        architecture = artifacts["enterprise_knowledge_integration_architecture"].machine_payload["integration_architecture"]
        self.assertEqual(architecture["capability_count"], 5)
        self.assertIn("learning_integration", architecture["integrated_capability_types"])
        self.assertTrue(architecture["traceability_preserved"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["enterprise_knowledge_integration_architecture"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_consistency_quality_and_governance_find_deficiencies(self) -> None:
        office = LibrarianFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = fuse(office)

        governance = artifacts["knowledge_governance_framework"].machine_payload["knowledge_governance_framework"]
        consistency = artifacts["enterprise_consistency_analysis_framework"].machine_payload["enterprise_consistency_analysis"]
        quality = artifacts["enterprise_consistency_analysis_framework"].machine_payload["knowledge_quality_assurance_standard"]
        self.assertEqual(governance["governance_deficiency_ids"], ["DEF-SPEC-CONSISTENCY"])
        self.assertTrue(governance["escalation_required"])
        self.assertEqual(consistency["inconsistent_capability_ids"], ["CAP-SPEC"])
        self.assertEqual(consistency["consistency_status"], "attention_required")
        self.assertTrue(quality["quality_assurance_passed"])

    def test_strategic_planning_risk_and_executive_reporting_are_generated(self) -> None:
        office = LibrarianFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = fuse(office)

        planning = artifacts["strategic_knowledge_planning_framework"].machine_payload["strategic_knowledge_planning_framework"]
        risk = artifacts["strategic_knowledge_planning_framework"].machine_payload["knowledge_risk_assessment_framework"]
        executive = artifacts["executive_knowledge_reporting_standard"].machine_payload["executive_knowledge_reporting_standard"]
        self.assertIn("Improve deterministic knowledge retrieval", planning["future_capability_requirements"][0])
        self.assertEqual(risk["risk_level"], KnowledgeRiskLevel.MODERATE.value)
        self.assertEqual(risk["knowledge_risk_ids"], ["RISK-SPEC-ACCESS"])
        self.assertIn("Authorize corrective governance review", executive["recommended_executive_actions"][0])
        self.assertIn("EV-SPEC", executive["traceability_ids"])

    def test_dashboard_and_institutional_intelligence_are_calculated(self) -> None:
        office = LibrarianFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = fuse(office)

        dashboard = artifacts["enterprise_knowledge_dashboard"].machine_payload["enterprise_knowledge_dashboard"]
        intelligence = artifacts["enterprise_knowledge_dashboard"].machine_payload["institutional_intelligence_assessment_framework"]
        self.assertEqual(dashboard["capability_count"], 5)
        self.assertEqual(dashboard["risk_level"], KnowledgeRiskLevel.MODERATE.value)
        self.assertEqual(dashboard["knowledge_health"], "attention")
        self.assertTrue(intelligence["continuously_improving"])
        self.assertEqual(intelligence["strategic_asset_status"], "strategic_asset")

    def test_prompt_and_clean_capability_set_produce_healthy_governance(self) -> None:
        office = LibrarianFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        clean = tuple(
            KnowledgeCapabilityAssessment(f"CAP-CLEAN-{index}", capability, 0.91, 0.90, 0.89, 0.92, True, (), (), (f"EV-{index}",))
            for index, capability in enumerate(KnowledgeCapabilityType, start=1)
        )

        prompt = office.system_prompt()
        artifacts = fuse(office, clean)

        dashboard = artifacts["enterprise_knowledge_dashboard"].machine_payload["enterprise_knowledge_dashboard"]
        executive = artifacts["executive_knowledge_reporting_standard"].machine_payload["executive_knowledge_reporting_standard"]
        self.assertIn("Librarian Fusion Office", prompt.prompt_text)
        self.assertIn("unified enterprise intelligence system", prompt.prompt_text)
        self.assertEqual(dashboard["knowledge_health"], "healthy")
        self.assertEqual(executive["recommended_executive_actions"], ["Maintain current Librarian governance cadence."])


if __name__ == "__main__":
    unittest.main()
