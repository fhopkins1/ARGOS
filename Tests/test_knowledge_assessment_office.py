from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.academy import (  # noqa: E402
    AssessmentItem,
    AssessmentItemDifficulty,
    AssessmentMeasure,
    AssessmentResponse,
    CompetencyDomain,
    KnowledgeAssessmentOffice,
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


def item(item_id: str, domain: CompetencyDomain, difficulty: AssessmentItemDifficulty = AssessmentItemDifficulty.APPLIED) -> AssessmentItem:
    suffix = domain.value.upper()
    return AssessmentItem(
        item_id,
        domain,
        difficulty,
        f"SCENARIO-{suffix}",
        (f"EV-{suffix}-1", f"EV-{suffix}-2"),
        tuple(AssessmentMeasure),
    )


def items() -> tuple[AssessmentItem, ...]:
    return (
        item("ITEM-001", CompetencyDomain.EVIDENCE_REASONING),
        item("ITEM-002", CompetencyDomain.RISK_DISCIPLINE),
        item("ITEM-003", CompetencyDomain.PORTFOLIO_JUDGMENT, AssessmentItemDifficulty.ADVANCED),
    )


def response(
    response_id: str,
    item_id: str,
    domain: CompetencyDomain,
    score: float,
    cited: tuple[str, ...],
) -> AssessmentResponse:
    return AssessmentResponse(response_id, item_id, domain, score, score, score, score, score, cited)


def responses() -> tuple[AssessmentResponse, ...]:
    return (
        response(
            "RESP-001",
            "ITEM-001",
            CompetencyDomain.EVIDENCE_REASONING,
            0.90,
            ("EV-EVIDENCE_REASONING-1", "EV-EVIDENCE_REASONING-2"),
        ),
        response(
            "RESP-002",
            "ITEM-002",
            CompetencyDomain.RISK_DISCIPLINE,
            0.60,
            ("EV-RISK_DISCIPLINE-1",),
        ),
        response(
            "RESP-003",
            "ITEM-003",
            CompetencyDomain.PORTFOLIO_JUDGMENT,
            0.74,
            ("EV-PORTFOLIO_JUDGMENT-1", "EV-PORTFOLIO_JUDGMENT-2"),
        ),
    )


def evaluate(
    office: KnowledgeAssessmentOffice,
    *,
    assessment_items: tuple[AssessmentItem, ...] = items(),
    assessment_responses: tuple[AssessmentResponse, ...] = responses(),
    prior_scores: tuple[float, ...] = (0.58, 0.64),
):
    return office.evaluate_assessment(
        "ASSESS-081",
        "USER-001",
        assessment_items,
        assessment_responses,
        prior_scores,
        "CF-001",
        "TC-001",
        8101,
    )


class KnowledgeAssessmentOfficeTests(unittest.TestCase):
    def test_framework_profile_dashboard_and_audit_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = KnowledgeAssessmentOffice(config(), persistence, audit, PromptRepository())

        artifacts = evaluate(office)

        framework = artifacts["competency_assessment_framework"].machine_payload["competency_assessment_framework"]
        profile = artifacts["student_competency_profile_standard"].machine_payload["student_competency_profile"]
        dashboard = artifacts["assessment_dashboard"].machine_payload["assessment_dashboard"]
        self.assertTrue(framework["decision_based"])
        self.assertFalse(framework["memorization_primary"])
        self.assertEqual(profile["learner_id"], "USER-001")
        self.assertEqual(dashboard["assessed_competency_count"], 3)
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["assessment_dashboard"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_competency_scores_detect_strengths_and_knowledge_gaps(self) -> None:
        office = KnowledgeAssessmentOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = evaluate(office)

        profile = artifacts["student_competency_profile_standard"].machine_payload["student_competency_profile"]
        feedback = artifacts["educational_feedback_framework"].machine_payload["educational_feedback_record"]
        self.assertIn(CompetencyDomain.EVIDENCE_REASONING.value, profile["demonstrated_competencies"])
        self.assertIn(CompetencyDomain.RISK_DISCIPLINE.value, profile["knowledge_gap_domains"])
        self.assertIn(CompetencyDomain.EVIDENCE_REASONING.value, feedback["strengths"])
        self.assertIn("Assign reinforced curriculum module for risk discipline", feedback["recommended_curriculum_actions"])

    def test_adaptive_architecture_selects_gap_items_deterministically(self) -> None:
        office = KnowledgeAssessmentOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = evaluate(office)

        adaptive = artifacts["adaptive_assessment_architecture"].machine_payload["adaptive_assessment_architecture"]
        self.assertEqual(adaptive["next_item_ids"], ["ITEM-002"])
        self.assertIn("knowledge_gap=risk_discipline", adaptive["adaptation_basis"])
        self.assertTrue(adaptive["deterministic"])

    def test_longitudinal_learning_analytics_measure_growth(self) -> None:
        office = KnowledgeAssessmentOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = evaluate(office)

        analytics = artifacts["longitudinal_learning_analytics"].machine_payload["longitudinal_learning_analytics"]
        self.assertEqual(analytics["prior_assessment_ids"], ["ASSESS-PRIOR-001", "ASSESS-PRIOR-002"])
        self.assertGreater(analytics["current_average_score"], 0.70)
        self.assertGreater(analytics["competency_growth"], 0.0)
        self.assertTrue(analytics["longitudinal_process_documented"])

    def test_validation_flags_unknown_item_and_missing_required_evidence(self) -> None:
        office = KnowledgeAssessmentOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        bad_items = (
            AssessmentItem("ITEM-001", CompetencyDomain.EVIDENCE_REASONING, AssessmentItemDifficulty.FOUNDATION, "SCENARIO-BAD", (), tuple(AssessmentMeasure)),
        )
        bad_responses = (
            response("RESP-UNKNOWN", "ITEM-999", CompetencyDomain.EVIDENCE_REASONING, 0.90, ("EV-1",)),
        )

        artifacts = evaluate(office, assessment_items=bad_items, assessment_responses=bad_responses)

        validation = artifacts["assessment_dashboard"].machine_payload["assessment_validation_record"]
        dashboard = artifacts["assessment_dashboard"].machine_payload["assessment_dashboard"]
        self.assertFalse(validation["valid"])
        self.assertIn("response_for_unknown_item", validation["validation_errors"])
        self.assertIn("item_missing_required_evidence", validation["validation_errors"])
        self.assertEqual(dashboard["assessment_health"], "attention")

    def test_system_prompt_documents_assessment_boundaries(self) -> None:
        office = KnowledgeAssessmentOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = office.system_prompt()

        self.assertIn("Knowledge Assessment Office", prompt.prompt_text)
        self.assertIn("rather than memorization", prompt.prompt_text)
        self.assertIn("competency", prompt.prompt_text.lower())


if __name__ == "__main__":
    unittest.main()
