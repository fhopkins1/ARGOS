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
from argos.historian import (  # noqa: E402
    OrganizationalPrompt,
    PromptEvaluationOffice,
    PromptLifecycleState,
    PromptPerformanceObservation,
    PromptRecommendationType,
    PromptSourceType,
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


def prompt() -> OrganizationalPrompt:
    return OrganizationalPrompt(
        "PROMPT-065",
        "Evidence-first analyst reasoning prompt",
        "1.0.0",
        "STF-074",
        PromptSourceType.ENGINEERING_ORDER,
        ("DOC-072",),
        ("EO-065",),
        ("APPROVAL-EXEC",),
        (),
        "2026-07-03",
    )


def observations(score: float = 0.92) -> tuple[PromptPerformanceObservation, ...]:
    return (
        PromptPerformanceObservation("POBS-001", "PROMPT-065", "SCENARIO-A", score, score, score, score, score, score, score, 0.98, 0.97, score, score, "AUD-001"),
        PromptPerformanceObservation("POBS-002", "PROMPT-065", "SCENARIO-B", score - 0.02, score, score, score, score, score, score, 0.96, 0.96, score, score, "AUD-002"),
    )


def registered_office() -> PromptEvaluationOffice:
    office = PromptEvaluationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
    office.register_prompt(prompt(), None, "CF-001", "TC-001", 6501)
    return office


class PromptEvaluationOfficeTests(unittest.TestCase):
    def test_prompt_registration_preserves_version_history_and_audit(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = PromptEvaluationOffice(config(), persistence, audit, PromptRepository())

        contract = office.register_prompt(prompt(), None, "CF-001", "TC-001", 6501)

        payload = contract.machine_payload
        version = payload["prompt_version_record"]
        traceability = payload["prompt_traceability"]
        self.assertEqual(version["lifecycle_state"], PromptLifecycleState.PROPOSAL.value)
        self.assertEqual(traceability["supporting_doctrine"], ["DOC-072"])
        self.assertFalse(payload["prompt_versions_overwritten"])
        self.assertEqual(len(office.prompt_version_history), 1)
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_prompt_evaluation_generates_metrics_benchmark_validation_and_analytics(self) -> None:
        office = registered_office()

        artifacts = office.evaluate_prompt("PROMPT-065", "1.0.0", observations(), 0.80, 0.82, 0.78, "APPROVAL-EXEC", "CF-001", "TC-001", 6510)

        report = artifacts["prompt_evaluation_report"].machine_payload["prompt_performance_report"]
        metrics = report["metrics"]
        benchmark = report["benchmark"]
        validation = report["validation"]
        analytics = artifacts["enterprise_prompt_analytics"].machine_payload["enterprise_prompt_analytics"]
        self.assertGreater(metrics["prompt_effectiveness_index"], 0.90)
        self.assertGreater(benchmark["historical_improvement"], 0)
        self.assertTrue(validation["production_validated"])
        self.assertEqual(analytics["production_prompts"], 1)
        self.assertEqual(analytics["regression_rate"], 0.0)
        self.assertEqual(len(office.prompt_evidence_repository), 1)

    def test_experimentation_preserves_scientific_design_and_rejects_anecdote(self) -> None:
        office = registered_office()

        artifacts = office.evaluate_prompt("PROMPT-065", "1.0.0", observations(), 0.80, 0.82, 0.78, "APPROVAL-EXEC", "CF-001", "TC-001", 6510)

        experiment = artifacts["prompt_experiment_report"].machine_payload["prompt_experiment_result"]
        self.assertIn("A/B Prompt Testing", experiment["experiment_types"])
        self.assertIn("Historical Replay", experiment["experiment_types"])
        self.assertFalse(experiment["anecdotal_observations_used"])
        self.assertTrue(experiment["deterministic"])

    def test_regression_recommends_retirement_without_modifying_prompt(self) -> None:
        office = registered_office()

        artifacts = office.evaluate_prompt("PROMPT-065", "1.0.0", observations(0.60), 0.80, 0.82, 0.78, None, "CF-001", "TC-001", 6510)

        recommendation = artifacts["prompt_optimization_recommendation"].machine_payload["prompt_optimization_recommendation"]
        analytics = artifacts["enterprise_prompt_analytics"].machine_payload["enterprise_prompt_analytics"]
        version = artifacts["prompt_evaluation_report"].machine_payload["prompt_version_record"]
        self.assertEqual(recommendation["recommendation_type"], PromptRecommendationType.RETIRE.value)
        self.assertFalse(recommendation["directly_modifies_prompt"])
        self.assertEqual(analytics["regression_rate"], 1.0)
        self.assertEqual(version["lifecycle_state"], PromptLifecycleState.RECOMMENDATION.value)

    def test_validation_requires_executive_approval_and_empirical_sample(self) -> None:
        office = registered_office()

        artifacts = office.evaluate_prompt("PROMPT-065", "1.0.0", observations(), 0.80, 0.82, 0.78, None, "CF-001", "TC-001", 6510)

        validation = artifacts["prompt_evaluation_report"].machine_payload["prompt_performance_report"]["validation"]
        self.assertTrue(validation["executive_approval_verified"])
        self.assertTrue(validation["statistical_significance_verified"])
        self.assertTrue(validation["production_validated"])

    def test_standards_document_no_doctrine_without_validation(self) -> None:
        office = registered_office()

        standards = office.standards()

        self.assertIn("No prompt shall become organizational doctrine", standards.doctrine_rule)
        self.assertIn("A/B testing", standards.experimentation_methodology)


if __name__ == "__main__":
    unittest.main()
