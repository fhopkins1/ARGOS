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
    DecisionEvaluationInput,
    DecisionEvaluationOffice,
    DecisionQualityBand,
    DecisionStatus,
    OrganizationalDecision,
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


def decision() -> OrganizationalDecision:
    return OrganizationalDecision(
        "DEC-066",
        "commander_approval",
        "Executive Group",
        "RATIONALE-066",
        ("EV-1", "EV-2", "EV-3"),
        ("ALT-1", "ALT-2"),
        ("GATE-1", "GATE-2"),
        "2026-07-04T00:00:00Z",
        "AUD-DEC-066",
    )


def strong_input() -> DecisionEvaluationInput:
    return DecisionEvaluationInput("DEI-066", "DEC-066", 10, 9, 3, 3, 2, 2, 2, 2, 2, 2, ("evidence_first", "alternatives_considered"), ("AUD-IN-1", "AUD-IN-2"))


def weak_input() -> DecisionEvaluationInput:
    return DecisionEvaluationInput("DEI-066-W", "DEC-066", 10, 4, 5, 2, 3, 1, 3, 2, 3, 1, ("evidence_gap", "alternatives_missing"), ("AUD-W-1",))


def historical_inputs() -> tuple[DecisionEvaluationInput, ...]:
    return (
        DecisionEvaluationInput("DEI-H1", "DEC-H1", 8, 5, 4, 2, 2, 1, 2, 2, 2, 1, ("evidence_gap",), ("AUD-H1",)),
        DecisionEvaluationInput("DEI-H2", "DEC-H2", 7, 5, 3, 3, 2, 1, 2, 1, 1, 1, ("alternatives_missing",), ("AUD-H2",)),
    )


class DecisionEvaluationOfficeTests(unittest.TestCase):
    def test_decision_registration_is_persisted_and_audited(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = DecisionEvaluationOffice(config(), persistence, audit, PromptRepository())

        contract = office.register_decision(decision(), "CF-001", "TC-001", 6601)

        self.assertEqual(contract.contract_type, "DECISION_REGISTRY")
        self.assertEqual(contract.machine_payload["decision_registry_record"]["status"], DecisionStatus.REGISTERED.value)
        self.assertTrue(contract.machine_payload["historical_decision_archive_immutable"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_decision_quality_is_evaluated_without_profitability(self) -> None:
        office = DecisionEvaluationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_decision(decision(), "CF-001", "TC-001", 6610)

        artifacts = office.evaluate_decision("DEC-066", strong_input(), historical_inputs(), "CF-001", "TC-001", 6611)

        report = artifacts["decision_evaluation_report"].machine_payload
        quality = report["decision_quality_evaluation"]
        self.assertEqual(report["decision_registry_record"]["status"], DecisionStatus.EVALUATED.value)
        self.assertEqual(quality["quality_band"], DecisionQualityBand.EXEMPLARY.value)
        self.assertFalse(quality["profitability_considered"])
        self.assertEqual(report["evidence_sufficiency_assessment"]["evidence_sufficiency_score"], 1.0)
        self.assertEqual(report["alternative_analysis_assessment"]["alternative_analysis_score"], 1.0)

    def test_weak_decision_generates_evidence_based_recommendation(self) -> None:
        office = DecisionEvaluationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_decision(decision(), "CF-001", "TC-001", 6620)

        artifacts = office.evaluate_decision("DEC-066", weak_input(), historical_inputs(), "CF-001", "TC-001", 6621)

        summary = artifacts["organizational_decision_summary"].machine_payload
        recommendation = summary["organizational_recommendation_register"][0]
        quality = artifacts["decision_evaluation_report"].machine_payload["decision_quality_evaluation"]
        self.assertIn(quality["quality_band"], (DecisionQualityBand.NEEDS_IMPROVEMENT.value, DecisionQualityBand.DEFICIENT.value))
        self.assertTrue(recommendation["evidence_based"])
        self.assertFalse(recommendation["directly_modifies_behavior"])
        self.assertIn("evidence", recommendation["recommendation"].lower())

    def test_recurring_decision_patterns_are_identified(self) -> None:
        office = DecisionEvaluationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_decision(decision(), "CF-001", "TC-001", 6630)

        pattern_report = office.evaluate_decision("DEC-066", weak_input(), historical_inputs(), "CF-001", "TC-001", 6631)["decision_pattern_report"].machine_payload

        patterns = {item["pattern_tag"]: item for item in pattern_report["decision_pattern_register"]}
        self.assertTrue(patterns["evidence_gap"]["recurring"])
        self.assertTrue(patterns["alternatives_missing"]["recurring"])

    def test_decision_discipline_and_archive_are_preserved(self) -> None:
        office = DecisionEvaluationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_decision(decision(), "CF-001", "TC-001", 6640)

        discipline_report = office.evaluate_decision("DEC-066", strong_input(), (), "CF-001", "TC-001", 6641)["decision_discipline_report"].machine_payload

        self.assertEqual(discipline_report["decision_discipline_metrics"]["governance_compliance_score"], 1.0)
        self.assertTrue(discipline_report["governance_compliance_archive"]["historical_archive_immutable"])
        self.assertTrue(office.historical_decision_archive)

    def test_invalid_inputs_are_rejected(self) -> None:
        office = DecisionEvaluationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_decision(decision(), "CF-001", "TC-001", 6650)

        with self.assertRaises(ValueError):
            office.register_decision(decision(), "CF-001", "TC-001", 6651)
        with self.assertRaises(ValueError):
            office.evaluate_decision("DEC-UNKNOWN", strong_input(), (), "CF-001", "TC-001", 6652)
        with self.assertRaises(ValueError):
            office.evaluate_decision("DEC-066", DecisionEvaluationInput("BAD", "OTHER", 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, (), ("AUD",)), (), "CF-001", "TC-001", 6653)

    def test_standards_define_librarian_deliverables(self) -> None:
        standards = DecisionEvaluationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository()).standards()

        self.assertEqual(standards.standards_id, "DES-066")
        self.assertIn("Reasoning quality", standards.reasoning_methodology)
        self.assertIn("Evidence sufficiency", standards.evidence_methodology)
        self.assertIn("governance", standards.governance_methodology.lower())
        self.assertIn("profitability shall not be used", standards.outcome_independence_rule)


if __name__ == "__main__":
    unittest.main()
