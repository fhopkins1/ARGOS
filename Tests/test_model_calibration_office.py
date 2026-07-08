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
from argos.historian import BiasDirection, ModelCalibrationOffice, ModelStatus, OrganizationalModel, PredictionObservation  # noqa: E402


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


def model() -> OrganizationalModel:
    return OrganizationalModel("MODEL-064", "Analyst Confidence Model", "1.0.0", "Analyst Department", "decision_accuracy", "FEATURES-064", "TRAIN-064", None, "AUD-MODEL-064")


def observations() -> tuple[PredictionObservation, ...]:
    return (
        PredictionObservation("OBS-1", "MODEL-064", "PRED-1", 0.9, 0.7, "2026-07-04T00:00:00Z", "HC-1", "AUD-OBS-1"),
        PredictionObservation("OBS-2", "MODEL-064", "PRED-2", 0.8, 0.6, "2026-07-04T00:00:00Z", "HC-2", "AUD-OBS-2"),
        PredictionObservation("OBS-3", "MODEL-064", "PRED-3", 0.7, 0.5, "2026-07-04T00:00:00Z", "HC-3", "AUD-OBS-3"),
    )


class ModelCalibrationOfficeTests(unittest.TestCase):
    def test_model_registration_is_version_controlled_and_audited(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = ModelCalibrationOffice(config(), persistence, audit, PromptRepository())

        contract = office.register_model(model(), "CF-001", "TC-001", 6401)

        self.assertEqual(contract.contract_type, "MODEL_REGISTRY")
        self.assertEqual(contract.machine_payload["model_registry_record"]["status"], ModelStatus.REGISTERED.value)
        self.assertFalse(contract.machine_payload["historical_model_versions_overwritten"])
        self.assertEqual(len(office.model_registry), 1)
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_calibration_calculates_error_bias_recommendation_and_simulation(self) -> None:
        office = ModelCalibrationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_model(model(), "CF-001", "TC-001", 6410)

        artifacts = office.calibrate_model("MODEL-064", observations(), "1.1.0", "CF-001", "TC-001", 6411)

        report = artifacts["model_calibration_report"].machine_payload
        self.assertEqual(report["prediction_error_dataset"]["mean_absolute_error"], 0.2)
        self.assertEqual(report["bias_assessment"]["bias_direction"], BiasDirection.OVERPREDICTION.value)
        self.assertTrue(report["bias_assessment"]["systematic_bias_detected"])
        self.assertTrue(report["calibration_recommendation"]["evidence_based"])
        self.assertFalse(report["calibration_recommendation"]["directly_updates_model"])
        self.assertTrue(report["calibration_simulation_result"]["simulation_successful"])

    def test_model_generation_comparison_and_evolution_are_generated(self) -> None:
        office = ModelCalibrationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_model(model(), "CF-001", "TC-001", 6420)

        artifacts = office.calibrate_model("MODEL-064", observations(), "1.1.0", "CF-001", "TC-001", 6421)

        comparison = artifacts["calibration_comparison_report"].machine_payload["model_generation_comparison"]
        evolution = artifacts["model_evolution_report"].machine_payload
        self.assertEqual(comparison["baseline_version"], "1.0.0")
        self.assertEqual(comparison["candidate_version"], "1.1.0")
        self.assertTrue(comparison["candidate_preferred"])
        self.assertIn("MVH-MODEL-064-1.1.0", evolution["model_version_history"])
        self.assertTrue(evolution["model_version_archive_immutable"])
        self.assertTrue(evolution["historical_reproducibility_preserved"])

    def test_calibration_history_and_summary_remain_complete(self) -> None:
        office = ModelCalibrationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_model(model(), "CF-001", "TC-001", 6430)

        summary = office.calibrate_model("MODEL-064", observations(), "1.1.0", "CF-001", "TC-001", 6431)["organizational_calibration_summary"].machine_payload

        self.assertTrue(office.calibration_history_archive)
        self.assertTrue(summary["historical_calibration_archive_complete"])
        self.assertEqual(summary["model_registry"][0]["status"], ModelStatus.CALIBRATION_RECOMMENDED.value)
        self.assertTrue(summary["calibration_recommendation_register"][0]["requires_version_increment"])

    def test_invalid_model_inputs_are_rejected(self) -> None:
        office = ModelCalibrationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.register_model(model(), "CF-001", "TC-001", 6440)

        with self.assertRaises(ValueError):
            office.register_model(model(), "CF-001", "TC-001", 6441)
        with self.assertRaises(ValueError):
            office.calibrate_model("MODEL-UNKNOWN", observations(), "1.1.0", "CF-001", "TC-001", 6442)
        with self.assertRaises(ValueError):
            office.calibrate_model("MODEL-064", (), "1.1.0", "CF-001", "TC-001", 6443)
        with self.assertRaises(ValueError):
            office.calibrate_model("MODEL-064", (PredictionObservation("OBS-X", "OTHER", "PRED-X", 0.5, 0.4, "2026-07-04T00:00:00Z", "HC-X", "AUD-X"),), "1.1.0", "CF-001", "TC-001", 6444)

    def test_standards_define_librarian_deliverables(self) -> None:
        standards = ModelCalibrationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository()).standards()

        self.assertEqual(standards.standards_id, "MCS-064")
        self.assertIn("MAE", standards.prediction_error_methodology)
        self.assertIn("Systematic bias", standards.bias_detection_methodology)
        self.assertIn("never overwritten", standards.version_specification)
        self.assertTrue(standards.reproducibility_required)


if __name__ == "__main__":
    unittest.main()
