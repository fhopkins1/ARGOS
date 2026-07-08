from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.academy import (  # noqa: E402
    CompetencyDomain,
    InstructionOffice,
    InstructionSourceMaterial,
    LearnerLevel,
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


def source() -> InstructionSourceMaterial:
    return InstructionSourceMaterial(
        "ISM-079",
        "Evidence-first position risk lesson",
        CompetencyDomain.EVIDENCE_REASONING,
        ("KNOW-070",),
        ("DOC-072",),
        ("CF-041",),
        ("RES-079",),
        ("EV-079-1", "EV-079-2"),
        ("OUTCOME-079",),
    )


def create(office: InstructionOffice, materials: tuple[InstructionSourceMaterial, ...] = (source(),), level: LearnerLevel = LearnerLevel.NOVICE):
    return office.create_instruction(
        "USER-001",
        level,
        materials,
        "UDM-038",
        "CF-001",
        "TC-001",
        7901,
    )


class InstructionOfficeTests(unittest.TestCase):
    def test_instruction_architecture_lesson_design_and_audit_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = InstructionOffice(config(), persistence, audit, PromptRepository())

        artifacts = create(office)

        architecture = artifacts["instruction_architecture"].machine_payload["instruction_architecture"]
        design = artifacts["lesson_design_standard"].machine_payload["lesson_design_standard"]
        self.assertTrue(architecture["teaches_reasoning_process"])
        self.assertTrue(architecture["avoids_investment_instructions"])
        self.assertIn("evidence_walkthrough", design["progressive_sequence"])
        self.assertTrue(artifacts["lesson_design_standard"].machine_payload["deterministic_instructional_principles_documented"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["instruction_architecture"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_translation_historical_learning_and_decision_reconstruction_are_traceable(self) -> None:
        office = InstructionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = create(office)

        translations = artifacts["educational_translation_framework"].machine_payload["educational_translation_records"]
        historical = artifacts["historical_learning_framework"].machine_payload["historical_learning_records"]
        reconstruction = artifacts["historical_learning_framework"].machine_payload["decision_reconstruction_standard"]
        self.assertEqual(translations[0]["source_id"], "ISM-079")
        self.assertIn("Separate observation", translations[0]["reasoning_steps"][1])
        self.assertEqual(historical[0]["case_file_ids"], ["CF-041"])
        self.assertTrue(historical[0]["uncertainty_preserved"])
        self.assertEqual(reconstruction["decision_model_id"], "UDM-038")
        self.assertEqual(reconstruction["evidence_ids"], ["EV-079-1", "EV-079-2"])

    def test_personalization_validation_dashboard_and_metrics_are_generated(self) -> None:
        office = InstructionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = create(office)

        personalized = artifacts["personalized_instruction_framework"].machine_payload["personalized_instruction_framework"]
        validation = artifacts["personalized_instruction_framework"].machine_payload["lesson_validation_process"]
        dashboard = artifacts["instruction_dashboard"].machine_payload["instruction_dashboard"]
        metrics = artifacts["instruction_dashboard"].machine_payload["instruction_metrics"]
        self.assertEqual(personalized["pacing"], "guided")
        self.assertEqual(personalized["target_competency"], CompetencyDomain.EVIDENCE_REASONING.value)
        self.assertTrue(validation["lesson_valid"])
        self.assertEqual(dashboard["instruction_health"], "healthy")
        self.assertEqual(len(metrics), 4)

    def test_advanced_instruction_uses_independent_sequence(self) -> None:
        office = InstructionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = create(office, level=LearnerLevel.ADVANCED)

        design = artifacts["lesson_design_standard"].machine_payload["lesson_design_standard"]
        personalized = artifacts["personalized_instruction_framework"].machine_payload["personalized_instruction_framework"]
        self.assertIn("argument_map", design["progressive_sequence"])
        self.assertEqual(personalized["pacing"], "independent")

    def test_missing_traceability_blocks_lesson_validation(self) -> None:
        office = InstructionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        incomplete = InstructionSourceMaterial("ISM-BAD", "Incomplete lesson", CompetencyDomain.RISK_DISCIPLINE, (), (), (), (), (), ())

        artifacts = create(office, materials=(incomplete,))

        validation = artifacts["personalized_instruction_framework"].machine_payload["lesson_validation_process"]
        dashboard = artifacts["instruction_dashboard"].machine_payload["instruction_dashboard"]
        self.assertFalse(validation["traceability_complete"])
        self.assertFalse(validation["doctrine_supported"])
        self.assertFalse(validation["historical_context_present"])
        self.assertFalse(validation["lesson_valid"])
        self.assertEqual(dashboard["instruction_health"], "attention")

    def test_instruction_prompt_is_complete(self) -> None:
        office = InstructionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = office.system_prompt()

        self.assertIn("Instruction Office", prompt.prompt_text)
        self.assertIn("Teach users how ARGOS reasons", prompt.prompt_text)


if __name__ == "__main__":
    unittest.main()
