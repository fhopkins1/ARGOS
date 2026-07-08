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
from argos.historian import GroupPerformanceDataset, PerformanceMeasurementOffice, PerformanceTrendDirection  # noqa: E402


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


def datasets(period_id: str = "2026-Q3") -> tuple[GroupPerformanceDataset, ...]:
    return (
        GroupPerformanceDataset("DS-EXEC", "Executive Group", period_id, 10, 8, 20, 18, 3, 3, 12, 1, ("AUD-EX-1",), ("HC-1",)),
        GroupPerformanceDataset("DS-SEEK", "Seeker Department", period_id, 12, 9, 30, 24, 4, 5, 15, 2, ("AUD-SK-1",), ("HC-2",)),
        GroupPerformanceDataset("DS-ANALYST", "Analyst Department", period_id, 11, 8, 28, 25, 4, 4, 16, 1, ("AUD-AN-1",), ("HC-3",)),
        GroupPerformanceDataset("DS-RISK", "Risk Office", period_id, 9, 7, 18, 17, 6, 5, 13, 1, ("AUD-RK-1",), ("HC-4",)),
        GroupPerformanceDataset("DS-TRADER", "Trader Group", period_id, 14, 13, 22, 21, 2, 2, 20, 1, ("AUD-TR-1",), ("HC-5",)),
    )


def baseline_scorecard() -> object:
    office = PerformanceMeasurementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
    artifacts = office.generate_reports(
        (
            GroupPerformanceDataset("DS-EXEC-B", "Executive Group", "2026-Q2", 10, 7, 20, 16, 4, 3, 11, 2, ("AUD-EX-B",), ("HC-B1",)),
            GroupPerformanceDataset("DS-TRADER-B", "Trader Group", "2026-Q2", 14, 10, 22, 18, 3, 3, 17, 3, ("AUD-TR-B",), ("HC-B2",)),
        ),
        (),
        "CF-001",
        "TC-001",
        6201,
    )
    payload = artifacts["organizational_scorecard"].machine_payload["organizational_scorecard"]
    return office.historical_performance_archive[0]


class PerformanceMeasurementOfficeTests(unittest.TestCase):
    def test_organizational_performance_reports_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = PerformanceMeasurementOffice(config(), persistence, audit, PromptRepository())

        artifacts = office.generate_reports(datasets(), (), "CF-001", "TC-001", 6210)

        self.assertIn("organizational_performance_report", artifacts)
        self.assertIn("executive_performance_report", artifacts)
        self.assertIn("organizational_scorecard", artifacts)
        self.assertIn("performance_trend_report", artifacts)
        report = artifacts["organizational_performance_report"]
        self.assertEqual(report.contract_type, "ORGANIZATIONAL_PERFORMANCE_REPORT")
        self.assertFalse(report.machine_payload["active_operations_influenced"])
        self.assertFalse(report.machine_payload["historical_performance_overwritten"])
        self.assertEqual(len(report.machine_payload["performance_metrics"]), 5)
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_scorecard_rankings_are_deterministic_and_traceable(self) -> None:
        office = PerformanceMeasurementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        first = office.generate_reports(datasets(), (), "CF-001", "TC-001", 6220)["organizational_scorecard"].machine_payload["organizational_scorecard"]
        second_office = PerformanceMeasurementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        second = second_office.generate_reports(datasets(), (), "CF-001", "TC-001", 6220)["organizational_scorecard"].machine_payload["organizational_scorecard"]

        self.assertEqual(first["deterministic_rankings"], second["deterministic_rankings"])
        self.assertEqual(first["generated_from_dataset_ids"], ["DS-EXEC", "DS-SEEK", "DS-ANALYST", "DS-RISK", "DS-TRADER"])
        self.assertTrue(first["evaluations"][0]["trace_ids"])

    def test_historical_comparisons_and_trends_function(self) -> None:
        baseline = baseline_scorecard()
        office = PerformanceMeasurementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        trend_report = office.generate_reports(datasets(), (baseline,), "CF-001", "TC-001", 6230)["performance_trend_report"].machine_payload

        trends = trend_report["performance_trends"]
        directions = tuple(item["direction"] for item in trends)
        self.assertIn(PerformanceTrendDirection.IMPROVING.value, directions)
        self.assertTrue(trend_report["performance_trend_archive_immutable"])
        self.assertEqual(trend_report["historical_comparison_record"]["baseline_period_id"], "2026-Q2")

    def test_duplicate_datasets_are_rejected_to_preserve_history(self) -> None:
        office = PerformanceMeasurementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.generate_reports(datasets(), (), "CF-001", "TC-001", 6240)

        with self.assertRaises(ValueError):
            office.generate_reports(datasets(), (), "CF-001", "TC-001", 6245)

    def test_standards_define_librarian_deliverables(self) -> None:
        office = PerformanceMeasurementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        standards = office.standards()

        self.assertEqual(standards.standards_id, "PMS-062")
        self.assertIn("decision_accuracy", standards.metric_definitions)
        self.assertIn("Historical", "Historical Performance Methodology")
        self.assertTrue(standards.reproducibility_required)


if __name__ == "__main__":
    unittest.main()
