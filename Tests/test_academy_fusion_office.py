from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.academy import (  # noqa: E402
    ACADEMY_FUSION_OFFICE_ID,
    AcademyFusionOffice,
    AcademyOfficeSignal,
    AcademyOfficeSignalType,
    CompetencyDomain,
    LearnerLevel,
    LearningInterventionPriority,
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


def signal(
    signal_id: str,
    signal_type: AcademyOfficeSignalType,
    office_id: str,
    domain: CompetencyDomain,
    score: float,
    knowledge_gap: bool,
    action: str,
    evidence_ids: tuple[str, ...] = ("EV-001",),
) -> AcademyOfficeSignal:
    return AcademyOfficeSignal(signal_id, signal_type, office_id, "USER-001", domain, score, knowledge_gap, evidence_ids, action)


def signals() -> tuple[AcademyOfficeSignal, ...]:
    return (
        signal("SIG-001", AcademyOfficeSignalType.INSTRUCTION, "ACADEMY-OFFICE-001", CompetencyDomain.EVIDENCE_REASONING, 0.86, False, "Advance evidence reasoning practice."),
        signal("SIG-002", AcademyOfficeSignalType.CURRICULUM, "ACADEMY-OFFICE-002", CompetencyDomain.RISK_DISCIPLINE, 0.62, True, "Reorder curriculum toward risk discipline."),
        signal("SIG-003", AcademyOfficeSignalType.ASSESSMENT, "ACADEMY-OFFICE-003", CompetencyDomain.RISK_DISCIPLINE, 0.58, True, "Assign risk recognition assessment."),
        signal("SIG-004", AcademyOfficeSignalType.CASE_STUDY, "ACADEMY-OFFICE-004", CompetencyDomain.PORTFOLIO_JUDGMENT, 0.72, False, "Assign portfolio case study."),
        signal("SIG-005", AcademyOfficeSignalType.TUTORING, "ACADEMY-OFFICE-005", CompetencyDomain.RISK_DISCIPLINE, 0.66, True, "Tutor misconception about risk."),
    )


def integrate(
    office: AcademyFusionOffice,
    *,
    office_signals: tuple[AcademyOfficeSignal, ...] = signals(),
):
    return office.integrate_learning_system(
        "USER-001",
        LearnerLevel.DEVELOPING,
        office_signals,
        "CF-001",
        "TC-001",
        8401,
    )


class AcademyFusionOfficeTests(unittest.TestCase):
    def test_integration_architecture_dashboard_persistence_and_audit_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = AcademyFusionOffice(config(), persistence, audit, PromptRepository())

        artifacts = integrate(office)

        architecture = artifacts["educational_integration_architecture"].machine_payload["educational_integration_architecture"]
        dashboard = artifacts["academy_intelligence_dashboard"].machine_payload["academy_intelligence_dashboard"]
        self.assertTrue(architecture["evidence_based"])
        self.assertIn(AcademyOfficeSignalType.ASSESSMENT.value, architecture["integrated_office_types"])
        self.assertEqual(dashboard["integrated_office_count"], 5)
        self.assertEqual(dashboard["academy_learning_health"], "healthy")
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["academy_intelligence_dashboard"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_student_model_fuses_scores_and_detects_knowledge_gaps(self) -> None:
        office = AcademyFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = integrate(office)

        model = artifacts["student_educational_model"].machine_payload["student_educational_model"]
        self.assertIn(CompetencyDomain.RISK_DISCIPLINE.value, model["knowledge_gap_domains"])
        self.assertIn(CompetencyDomain.EVIDENCE_REASONING.value, model["mastery_domains"])
        self.assertIn("EV-001", model["traceability_reference_ids"])

    def test_orchestration_prioritizes_gap_interventions(self) -> None:
        office = AcademyFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = integrate(office)

        orchestration = artifacts["personalized_learning_orchestration_framework"].machine_payload["personalized_learning_orchestration_framework"]
        self.assertEqual(orchestration["intervention_priority"], LearningInterventionPriority.HIGH.value)
        self.assertEqual(
            orchestration["prioritized_interventions"],
            ["Assign risk recognition assessment.", "Reorder curriculum toward risk discipline.", "Tutor misconception about risk."],
        )
        self.assertIn(AcademyOfficeSignalType.TUTORING.value, orchestration["optimized_sequence"])

    def test_coordination_optimization_and_feedback_are_documented(self) -> None:
        office = AcademyFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = integrate(office)

        coordination = artifacts["cross_office_coordination_framework"].machine_payload["cross_office_coordination_framework"]
        optimization = artifacts["educational_optimization_framework"].machine_payload["educational_optimization_framework"]
        feedback = artifacts["learning_feedback_architecture"].machine_payload["learning_feedback_architecture"]
        self.assertTrue(coordination["consistent"])
        self.assertEqual(len(coordination["coordinated_office_ids"]), 5)
        self.assertIn("gap=risk_discipline", optimization["optimization_basis"])
        self.assertTrue(feedback["feedback_loop_documented"])
        self.assertIn(AcademyOfficeSignalType.TUTORING.value, feedback["feedback_sources"])

    def test_quality_assurance_flags_missing_evidence(self) -> None:
        office = AcademyFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        bad_signals = (
            signal("SIG-BAD", AcademyOfficeSignalType.ASSESSMENT, "ACADEMY-OFFICE-003", CompetencyDomain.RISK_DISCIPLINE, 0.44, True, "Repair missing evidence.", ()),
        )

        artifacts = integrate(office, office_signals=bad_signals)

        qa = artifacts["learning_feedback_architecture"].machine_payload["educational_quality_assurance_framework"]
        dashboard = artifacts["academy_intelligence_dashboard"].machine_payload["academy_intelligence_dashboard"]
        orchestration = artifacts["personalized_learning_orchestration_framework"].machine_payload["personalized_learning_orchestration_framework"]
        self.assertFalse(qa["valid"])
        self.assertIn("signal_missing_evidence", qa["validation_errors"])
        self.assertEqual(orchestration["intervention_priority"], LearningInterventionPriority.URGENT.value)
        self.assertEqual(dashboard["academy_learning_health"], "attention")

    def test_system_prompt_documents_unified_learning_system(self) -> None:
        office = AcademyFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = office.system_prompt()

        self.assertIn("Academy Fusion Office", prompt.prompt_text)
        self.assertIn("unified, personalized learning system", prompt.prompt_text)
        self.assertIn("educational analytics", prompt.prompt_text)
        self.assertEqual(ACADEMY_FUSION_OFFICE_ID, "ACADEMY-OFFICE-006")


if __name__ == "__main__":
    unittest.main()
