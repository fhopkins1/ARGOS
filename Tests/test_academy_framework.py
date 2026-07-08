from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.academy import (  # noqa: E402
    AcademyFramework,
    CompetencyDomain,
    LearnerLevel,
    academy_office_templates,
)
from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402


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


def establish(academy: AcademyFramework, *, knowledge: tuple[str, ...] = ("KNOW-070", "DOC-072"), evidence: tuple[str, ...] = ("EV-078-1", "EV-078-2")):
    return academy.establish_academy(
        "USER-001",
        LearnerLevel.NOVICE,
        LearnerLevel.COMPETENT,
        knowledge,
        evidence,
        "LEAR-077",
        "CF-001",
        "TC-001",
        7801,
    )


class AcademyFrameworkTests(unittest.TestCase):
    def test_academy_architecture_mission_structure_and_audit_are_established(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        academy = AcademyFramework(config(), persistence, audit, PromptRepository())

        artifacts = establish(academy)

        architecture = artifacts["academy_architecture"].machine_payload["academy_architecture"]
        self.assertIn("complete accumulated knowledge of ARGOS", architecture["mission"])
        self.assertTrue(architecture["user_facing"])
        self.assertTrue(architecture["librarian_certification_required"])
        self.assertEqual(len(architecture["office_templates"]), 6)
        self.assertEqual(tuple(template.name for template in academy_office_templates())[0], "Instruction Office")
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["academy_architecture"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_educational_philosophy_and_system_prompt_are_complete(self) -> None:
        academy = AcademyFramework(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = academy.system_prompt()
        artifacts = establish(academy)

        philosophy = artifacts["educational_philosophy_framework"].machine_payload["educational_philosophy_framework"]
        self.assertIn("Academy of ARGOS", prompt.prompt_text)
        self.assertIn("deterministic, evidence-based financial education", prompt.prompt_text)
        self.assertTrue(philosophy["evidence_based"])
        self.assertTrue(philosophy["deterministic"])
        self.assertTrue(philosophy["doctrine_traceable"])
        self.assertTrue(artifacts["educational_philosophy_framework"].machine_payload["deterministic_educational_principles_established"])

    def test_financial_competency_and_personalized_learning_frameworks_are_generated(self) -> None:
        academy = AcademyFramework(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = establish(academy)

        competencies = artifacts["financial_competency_framework"].machine_payload["financial_competency_records"]
        personalized = artifacts["personalized_learning_framework"].machine_payload["personalized_learning_framework"]
        self.assertEqual(len(competencies), len(tuple(CompetencyDomain)))
        self.assertEqual(competencies[0]["learner_level"], LearnerLevel.NOVICE.value)
        self.assertEqual(personalized["learner_id"], "USER-001")
        self.assertEqual(personalized["current_level"], LearnerLevel.NOVICE.value)
        self.assertEqual(personalized["target_level"], LearnerLevel.COMPETENT.value)
        self.assertEqual(len(personalized["recommended_competency_ids"]), len(competencies))

    def test_pipeline_governance_dashboard_and_metrics_are_available(self) -> None:
        academy = AcademyFramework(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = establish(academy)

        pipeline = artifacts["educational_pipeline_model"].machine_payload["educational_pipeline_model"]
        governance = artifacts["educational_pipeline_model"].machine_payload["academy_governance_framework"]
        dashboard = artifacts["educational_dashboard"].machine_payload["educational_dashboard"]
        metrics = artifacts["educational_dashboard"].machine_payload["educational_success_metrics"]
        self.assertTrue(pipeline["pipeline_operational"])
        self.assertEqual(len(pipeline["stages"]), 5)
        self.assertTrue(all(stage["traceability_required"] for stage in pipeline["stages"]))
        self.assertEqual(governance["librarian_certification_id"], "LEAR-077")
        self.assertTrue(governance["prohibited_unvalidated_content"])
        self.assertEqual(dashboard["educational_health"], "healthy")
        self.assertEqual(len(metrics), 4)

    def test_dashboard_flags_missing_traceability_inputs(self) -> None:
        academy = AcademyFramework(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = establish(academy, knowledge=(), evidence=())

        pipeline = artifacts["educational_pipeline_model"].machine_payload["educational_pipeline_model"]
        dashboard = artifacts["educational_dashboard"].machine_payload["educational_dashboard"]
        self.assertFalse(pipeline["pipeline_operational"])
        self.assertEqual(dashboard["traceability_coverage"], 0.0)
        self.assertEqual(dashboard["educational_health"], "attention")


if __name__ == "__main__":
    unittest.main()
