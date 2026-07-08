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
    LearningIntegrationOffice,
    LearningSourceType,
    PropagationTargetType,
    ValidatedLearningSource,
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


def sources() -> tuple[ValidatedLearningSource, ...]:
    return (
        ValidatedLearningSource(
            "LEARN-075-A",
            LearningSourceType.HISTORIAN_VALIDATION,
            "Improve evidence freshness checks",
            ("EV-075-A",),
            ("HIST-075-A",),
            ("FOUNDATION", "LIBRARIAN"),
            ("MISTAKE-001",),
            0.18,
            0.92,
        ),
        ValidatedLearningSource(
            "LEARN-075-B",
            LearningSourceType.DECISION_EVALUATION,
            "Reduce stale executive packets",
            ("EV-075-B",),
            ("HIST-075-B",),
            ("EXECUTIVE",),
            (),
            0.08,
            0.80,
        ),
    )


def targets() -> dict[str, tuple[tuple[PropagationTargetType, str], ...]]:
    return {
        "LEARN-075-A": (
            (PropagationTargetType.DOCTRINE, "DOC-EVIDENCE-FRESHNESS"),
            (PropagationTargetType.SPECIFICATION, "EO-FUTURE-EVIDENCE-FRESHNESS"),
            (PropagationTargetType.ACADEMY_CURRICULUM, "ACADEMY-EVIDENCE-LESSON"),
        ),
        "LEARN-075-B": (
            (PropagationTargetType.WORKFLOW, "EXECUTIVE-PACKET-WORKFLOW"),
            (PropagationTargetType.PROMPT, "PROMPT-CHIEF-OF-STAFF"),
        ),
    }


def integrate(
    office: LearningIntegrationOffice,
    *,
    baseline: dict[str, float] | None = None,
    observed: dict[str, float] | None = None,
):
    return office.integrate_learning(
        sources(),
        targets(),
        baseline or {"LEARN-075-A": 0.70, "LEARN-075-B": 0.81},
        observed or {"LEARN-075-A": 0.82, "LEARN-075-B": 0.84},
        "2026-Q4",
        "CF-001",
        "TC-001",
        7501,
    )


class LearningIntegrationOfficeTests(unittest.TestCase):
    def test_learning_pipeline_propagation_and_audit_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = LearningIntegrationOffice(config(), persistence, audit, PromptRepository())

        artifacts = integrate(office)

        pipeline = artifacts["enterprise_learning_pipeline"].machine_payload["enterprise_learning_pipeline"]
        propagation = artifacts["knowledge_propagation_framework"].machine_payload["knowledge_propagation_records"]
        self.assertEqual(pipeline["validated_source_count"], 2)
        self.assertEqual(pipeline["propagation_target_count"], 5)
        self.assertEqual(len(propagation), 5)
        self.assertIn("Doctrine Management Office", propagation[0]["governance_gate"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["enterprise_learning_pipeline"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_prioritization_and_improvement_framework_are_deterministic(self) -> None:
        office = LearningIntegrationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = integrate(office)

        prioritization = artifacts["organizational_improvement_framework"].machine_payload["learning_prioritization_standard"]
        improvements = artifacts["organizational_improvement_framework"].machine_payload["organizational_improvement_records"]
        self.assertEqual(prioritization["ranked_learning_ids"], ["LEARN-075-A", "LEARN-075-B"])
        self.assertGreater(prioritization["score_by_learning_id"]["LEARN-075-A"], prioritization["score_by_learning_id"]["LEARN-075-B"])
        self.assertEqual(improvements[0]["status"], "propagation_ready")

    def test_integration_validation_feedback_and_maturity_model_are_generated(self) -> None:
        office = LearningIntegrationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = integrate(office)

        validations = artifacts["continuous_improvement_engine"].machine_payload["integration_validation_records"]
        continuous = artifacts["continuous_improvement_engine"].machine_payload["continuous_improvement_records"]
        feedback = artifacts["feedback_loop_architecture"].machine_payload["feedback_loop_records"]
        maturity = artifacts["feedback_loop_architecture"].machine_payload["enterprise_maturity_model"]
        self.assertTrue(all(item["performance_gain_verified"] for item in validations))
        self.assertTrue(continuous[0]["repeated_mistake_eliminated"])
        self.assertTrue(feedback[0]["historian_feedback_required"])
        self.assertEqual(maturity["maturity_level"], "optimizing")

    def test_stagnation_is_detected_when_observable_gain_is_absent(self) -> None:
        office = LearningIntegrationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = integrate(office, observed={"LEARN-075-A": 0.69, "LEARN-075-B": 0.81})

        continuous = artifacts["continuous_improvement_engine"].machine_payload["continuous_improvement_records"]
        dashboard = artifacts["organizational_learning_dashboard"].machine_payload["organizational_learning_dashboard"]
        self.assertTrue(continuous[0]["stagnation_detected"])
        self.assertEqual(dashboard["stagnation_count"], 2)
        self.assertEqual(dashboard["learning_health"], "attention")

    def test_system_prompt_and_learning_sources_are_available(self) -> None:
        office = LearningIntegrationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = office.system_prompt()
        integrate(office)

        self.assertIn("Learning Integration Office", prompt.prompt_text)
        self.assertIn("observable performance gains", prompt.prompt_text)
        self.assertEqual(tuple(source.learning_id for source in office.learning_sources), ("LEARN-075-A", "LEARN-075-B"))


if __name__ == "__main__":
    unittest.main()
