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
    EvidenceRelationship,
    HypothesisEvidence,
    HypothesisStatus,
    HypothesisValidationOffice,
    OrganizationalHypothesis,
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


def hypothesis() -> OrganizationalHypothesis:
    return OrganizationalHypothesis(
        "HYP-063",
        "High evidence diversity improves decision quality",
        "Analyst Department",
        "Independent evidence diversity increases organizational decision accuracy.",
        0.55,
        True,
        "HC-063",
        "AUD-HYP-063",
    )


def supporting_evidence() -> tuple[HypothesisEvidence, ...]:
    return (
        HypothesisEvidence("EV-S1", "HC-1", EvidenceRelationship.SUPPORTS, 0.8, "decision_accuracy", 0.82, "AUD-EV-1"),
        HypothesisEvidence("EV-S2", "HC-2", EvidenceRelationship.SUPPORTS, 0.7, "evidence_quality", 0.9, "AUD-EV-2"),
        HypothesisEvidence("EV-N1", "HC-3", EvidenceRelationship.NEUTRAL, 0.1, "process_reliability", 0.7, "AUD-EV-3"),
    )


def contradicting_evidence() -> tuple[HypothesisEvidence, ...]:
    return (
        HypothesisEvidence("EV-C1", "HC-4", EvidenceRelationship.CONTRADICTS, 0.9, "decision_accuracy", 0.3, "AUD-EV-4"),
        HypothesisEvidence("EV-C2", "HC-5", EvidenceRelationship.CONTRADICTS, 0.8, "evidence_quality", 0.2, "AUD-EV-5"),
        HypothesisEvidence("EV-S3", "HC-6", EvidenceRelationship.SUPPORTS, 0.1, "process_reliability", 0.6, "AUD-EV-6"),
    )


class HypothesisValidationOfficeTests(unittest.TestCase):
    def test_hypothesis_registration_is_persisted_and_audited(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = HypothesisValidationOffice(config(), persistence, audit, PromptRepository())

        contract = office.register_hypothesis(hypothesis(), "CF-001", "TC-001", 6301)

        self.assertEqual(contract.contract_type, "HYPOTHESIS_REGISTRY")
        self.assertEqual(contract.machine_payload["hypothesis_registry_record"]["current_status"], HypothesisStatus.REGISTERED.value)
        self.assertEqual(len(office.hypothesis_registry), 1)
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_supporting_evidence_validates_hypothesis_and_gates_doctrine(self) -> None:
        office = HypothesisValidationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_hypothesis(hypothesis(), "CF-001", "TC-001", 6310)

        artifacts = office.validate_hypothesis("HYP-063", supporting_evidence(), ("CAL-1",), 0.55, "CF-001", "TC-001", 6311)

        report = artifacts["hypothesis_validation_report"].machine_payload
        summary = artifacts["organizational_hypothesis_summary"].machine_payload
        self.assertEqual(report["hypothesis_registry_record"]["current_status"], HypothesisStatus.VALIDATED.value)
        self.assertGreater(report["evidence_correlation_record"]["support_score"], report["evidence_correlation_record"]["contradiction_score"])
        self.assertFalse(report["falsification_record"]["contradicted"])
        self.assertTrue(report["organizational_learning_recommendation"]["eligible_for_doctrine"])
        self.assertTrue(summary["only_validated_hypotheses_progress_to_doctrine"])

    def test_contradicting_evidence_rejects_hypothesis(self) -> None:
        office = HypothesisValidationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_hypothesis(hypothesis(), "CF-001", "TC-001", 6320)

        artifacts = office.validate_hypothesis("HYP-063", contradicting_evidence(), ("CAL-2",), 0.55, "CF-001", "TC-001", 6321)

        report = artifacts["hypothesis_validation_report"].machine_payload
        self.assertEqual(report["hypothesis_registry_record"]["current_status"], HypothesisStatus.REJECTED.value)
        self.assertTrue(report["falsification_record"]["contradicted"])
        self.assertFalse(report["organizational_learning_recommendation"]["eligible_for_doctrine"])

    def test_confidence_calibration_and_drift_are_reported(self) -> None:
        office = HypothesisValidationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_hypothesis(hypothesis(), "CF-001", "TC-001", 6330)

        artifacts = office.validate_hypothesis("HYP-063", supporting_evidence(), ("CAL-3",), 0.1, "CF-001", "TC-001", 6331)

        calibration = artifacts["confidence_calibration_report"].machine_payload["confidence_calibration_record"]
        drift = artifacts["hypothesis_drift_report"].machine_payload["hypothesis_drift_record"]
        self.assertGreater(calibration["calibrated_confidence"], calibration["prior_confidence"])
        self.assertTrue(drift["drift_detected"])
        self.assertTrue(office.validation_history_archive)

    def test_validation_rejects_unknown_duplicate_and_unsupported_inputs(self) -> None:
        office = HypothesisValidationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_hypothesis(hypothesis(), "CF-001", "TC-001", 6340)

        with self.assertRaises(ValueError):
            office.register_hypothesis(hypothesis(), "CF-001", "TC-001", 6341)
        with self.assertRaises(ValueError):
            office.validate_hypothesis("HYP-UNKNOWN", supporting_evidence(), ("CAL-4",), 0.55, "CF-001", "TC-001", 6342)
        with self.assertRaises(ValueError):
            office.validate_hypothesis("HYP-063", (), ("CAL-4",), 0.55, "CF-001", "TC-001", 6343)

    def test_standards_define_librarian_deliverables(self) -> None:
        standards = HypothesisValidationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository()).standards()

        self.assertEqual(standards.standards_id, "HVS-063")
        self.assertIn("falsify", standards.validation_methodology)
        self.assertIn("calibrated_confidence", standards.confidence_calibration_methodology)
        self.assertIn("Only validated hypotheses", standards.doctrine_gate)


if __name__ == "__main__":
    unittest.main()
