from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.academy import (  # noqa: E402
    CaseStudyOffice,
    CompetencyDomain,
    HistoricalEvidencePacket,
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


def evidence() -> tuple[HistoricalEvidencePacket, ...]:
    return (
        HistoricalEvidencePacket("EV-001", "market_data", "2026-01-10T14:00:00Z", "Pre-decision price volatility increased.", False),
        HistoricalEvidencePacket("EV-002", "risk_report", "2026-01-10T14:30:00Z", "Liquidity conditions were weakening.", False),
        HistoricalEvidencePacket("EV-003", "historian_outcome", "2026-01-12T14:30:00Z", "The position ultimately failed.", True),
    )


def create(
    office: CaseStudyOffice,
    *,
    packets: tuple[HistoricalEvidencePacket, ...] = evidence(),
    scores: tuple[float, float, float, float] = (0.82, 0.78, 0.80, 0.84),
):
    return office.create_case_study(
        "CASE-082",
        "USER-001",
        LearnerLevel.DEVELOPING,
        "Historical Volatility Shock",
        "2026-01-10T15:00:00Z",
        packets,
        (CompetencyDomain.EVIDENCE_REASONING, CompetencyDomain.RISK_DISCIPLINE),
        scores,
        "CF-001",
        "TC-001",
        8201,
    )


class CaseStudyOfficeTests(unittest.TestCase):
    def test_architecture_reconstruction_dashboard_and_audit_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = CaseStudyOffice(config(), persistence, audit, PromptRepository())

        artifacts = create(office)

        architecture = artifacts["case_study_architecture"].machine_payload["case_study_architecture"]
        reconstruction = artifacts["historical_reconstruction_framework"].machine_payload["historical_reconstruction_framework"]
        dashboard = artifacts["case_study_dashboard"].machine_payload["case_study_dashboard"]
        self.assertTrue(architecture["immersive"])
        self.assertTrue(architecture["pre_outcome_reconstruction_required"])
        self.assertEqual(reconstruction["case_study_id"], "CASE-082")
        self.assertEqual(dashboard["case_study_health"], "healthy")
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["case_study_dashboard"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_historical_reconstruction_excludes_outcome_revealing_evidence(self) -> None:
        office = CaseStudyOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = create(office)

        reconstruction = artifacts["historical_reconstruction_framework"].machine_payload["historical_reconstruction_framework"]
        available_packets = artifacts["historical_reconstruction_framework"].machine_payload["available_evidence_packets"]
        self.assertEqual(reconstruction["available_evidence_ids"], ["EV-001", "EV-002"])
        self.assertEqual(reconstruction["excluded_outcome_evidence_ids"], ["EV-003"])
        self.assertNotIn("EV-003", [packet["evidence_id"] for packet in available_packets])

    def test_decision_simulation_and_alternative_history_are_created(self) -> None:
        office = CaseStudyOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = create(office)

        simulation = artifacts["decision_simulation_framework"].machine_payload["decision_simulation_framework"]
        alternatives = artifacts["decision_simulation_framework"].machine_payload["alternative_history_scenarios"]
        self.assertTrue(simulation["outcome_hidden_until_submission"])
        self.assertIn(CompetencyDomain.RISK_DISCIPLINE.value, simulation["assessed_competencies"])
        self.assertEqual(len(alternatives), 2)
        self.assertIn("Liquidity conditions deteriorate", alternatives[0]["changed_assumption"])

    def test_multi_perspective_analysis_and_personalized_selection_are_balanced(self) -> None:
        office = CaseStudyOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = create(office)

        perspectives = artifacts["multi_perspective_analysis_standard"].machine_payload["multi_perspective_analysis_standard"]
        selection = artifacts["personalized_case_selection_engine"].machine_payload["personalized_case_selection"]
        self.assertTrue(perspectives["balanced"])
        self.assertGreaterEqual(len(perspectives["perspectives"]), 3)
        self.assertEqual(selection["selected_case_study_ids"], ["CASE-082"])
        self.assertIn("learner_level=developing", selection["selection_basis"])

    def test_validation_flags_missing_pre_outcome_evidence(self) -> None:
        office = CaseStudyOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        bad_packets = (
            HistoricalEvidencePacket("EV-LATE", "outcome", "2026-01-12T15:00:00Z", "Outcome was known later.", True),
        )

        artifacts = create(office, packets=bad_packets, scores=(0.50, 0.52, 0.48, 0.51))

        validation = artifacts["case_study_dashboard"].machine_payload["case_validation_standard"]
        dashboard = artifacts["case_study_dashboard"].machine_payload["case_study_dashboard"]
        self.assertFalse(validation["valid"])
        self.assertIn("missing_pre_outcome_evidence", validation["validation_errors"])
        self.assertEqual(dashboard["case_study_health"], "attention")

    def test_system_prompt_documents_outcome_reveal_boundary(self) -> None:
        office = CaseStudyOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = office.system_prompt()

        self.assertIn("Case Study Office", prompt.prompt_text)
        self.assertIn("only the information available at the time", prompt.prompt_text)
        self.assertIn("before historical outcomes are revealed", prompt.prompt_text)


if __name__ == "__main__":
    unittest.main()
