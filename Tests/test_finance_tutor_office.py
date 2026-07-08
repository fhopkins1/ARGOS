from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.academy import (  # noqa: E402
    CompetencyDomain,
    ExplanationDepth,
    FinanceTutorOffice,
    LearnerLevel,
    StudentLearningContext,
    TutorInteractionMode,
    TutorKnowledgeReference,
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


def context(
    *,
    level: LearnerLevel = LearnerLevel.DEVELOPING,
    misconceptions: tuple[str, ...] = ("price action proves value",),
) -> StudentLearningContext:
    return StudentLearningContext(
        "USER-001",
        level,
        (CompetencyDomain.EVIDENCE_REASONING,),
        misconceptions,
        ("improve risk reasoning", "understand evidence quality"),
        ("ASSESS-081", "CASE-082"),
    )


def references() -> tuple[TutorKnowledgeReference, ...]:
    return (
        TutorKnowledgeReference("REF-001", "case_study", "Volatility Shock Case", ("EV-001", "EV-002"), ("DOC-RISK-001",), ("CASE-082",)),
        TutorKnowledgeReference("REF-002", "doctrine", "Evidence Before Doctrine", ("EV-003",), ("DOC-FOUNDATION-001",), ()),
    )


def tutor(
    office: FinanceTutorOffice,
    *,
    learner_context: StudentLearningContext = context(),
    knowledge_references: tuple[TutorKnowledgeReference, ...] = references(),
):
    return office.create_tutoring_session(
        "TUTOR-083",
        learner_context,
        knowledge_references,
        "Should I trust a strong price move?",
        "CF-001",
        "TC-001",
        8301,
    )


class FinanceTutorOfficeTests(unittest.TestCase):
    def test_tutoring_framework_dashboard_persistence_and_audit_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = FinanceTutorOffice(config(), persistence, audit, PromptRepository())

        artifacts = tutor(office)

        framework = artifacts["personalized_tutoring_framework"].machine_payload["personalized_tutoring_framework"]
        dashboard = artifacts["tutor_analytics_dashboard"].machine_payload["tutor_analytics_dashboard"]
        self.assertTrue(framework["evidence_based"])
        self.assertTrue(framework["prohibits_investment_advice"])
        self.assertTrue(dashboard["traceability_complete"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["tutor_analytics_dashboard"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_adaptive_guidance_uses_misconception_repair_when_needed(self) -> None:
        office = FinanceTutorOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = tutor(office)

        guidance = artifacts["adaptive_guidance_architecture"].machine_payload["adaptive_guidance_architecture"]
        misconceptions = artifacts["educational_conversation_model"].machine_payload["misconception_detection_framework"]
        self.assertEqual(guidance["guidance_mode"], TutorInteractionMode.MISCONCEPTION_REPAIR.value)
        self.assertIn("Repair misconception: price action proves value", guidance["next_guidance_actions"])
        self.assertEqual(misconceptions["detected_misconceptions"], ["price action proves value"])
        self.assertEqual(misconceptions["confidence"], 1.0)

    def test_socratic_reasoning_and_explanation_depth_are_deterministic(self) -> None:
        office = FinanceTutorOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        learner_context = context(misconceptions=())

        artifacts = tutor(office, learner_context=learner_context)

        guidance = artifacts["adaptive_guidance_architecture"].machine_payload["adaptive_guidance_architecture"]
        socratic = artifacts["socratic_reasoning_framework"].machine_payload["socratic_reasoning_framework"]
        explanation = artifacts["explanation_depth_standard"].machine_payload["explanation_depth_standard"]
        self.assertEqual(guidance["guidance_mode"], TutorInteractionMode.SOCRATIC.value)
        self.assertFalse(socratic["immediate_conclusion_preferred"])
        self.assertIn("What evidence would you need", socratic["question_sequence"][0])
        self.assertEqual(explanation["selected_depth"], ExplanationDepth.APPLIED.value)

    def test_decision_coaching_remains_educational_and_traceable(self) -> None:
        office = FinanceTutorOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = tutor(office)

        coaching = artifacts["decision_coaching_framework"].machine_payload["decision_coaching_framework"]
        self.assertTrue(coaching["coaching_not_advice"])
        self.assertEqual(coaching["evidence_reference_ids"], ["EV-001", "EV-002", "EV-003"])
        self.assertIn("Separate evidence from assumptions.", coaching["required_reasoning_steps"])

    def test_missing_references_flag_attention_health(self) -> None:
        office = FinanceTutorOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = tutor(office, knowledge_references=())

        dashboard = artifacts["tutor_analytics_dashboard"].machine_payload["tutor_analytics_dashboard"]
        self.assertFalse(dashboard["traceability_complete"])
        self.assertEqual(dashboard["tutor_health"], "attention")
        self.assertEqual(dashboard["reference_count"], 0)

    def test_system_prompt_documents_guided_questioning_and_traceability(self) -> None:
        office = FinanceTutorOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = office.system_prompt()

        self.assertIn("Finance Tutor Office", prompt.prompt_text)
        self.assertIn("Prefer guided questioning", prompt.prompt_text)
        self.assertIn("complete traceability", prompt.prompt_text)


if __name__ == "__main__":
    unittest.main()
