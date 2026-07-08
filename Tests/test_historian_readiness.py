from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.testing import TestExecutionResult, foundation_test_registry  # noqa: E402
from argos.historian import (  # noqa: E402
    HistorianAdversarialTestEngine,
    HistorianCertificationOutcome,
    HistorianOperationalReadinessVerifier,
    HistorianReadinessReportGenerator,
)


def passing_results() -> tuple[TestExecutionResult, ...]:
    return tuple(
        TestExecutionResult(
            suite_id=registration.suite_id,
            module_name=registration.module_name,
            tests_run=1,
            failures=0,
            errors=0,
            skipped=0,
            successful=True,
        )
        for registration in foundation_test_registry()
    )


class HistorianReadinessTests(unittest.TestCase):
    def test_historian_readiness_certifies_complete_group(self) -> None:
        result = HistorianOperationalReadinessVerifier().verify(passing_results())

        self.assertTrue(result.certified)
        self.assertEqual(result.outcome, HistorianCertificationOutcome.CERTIFIED)
        self.assertEqual(len(result.checks), 8)
        self.assertTrue(all(check.passed for check in result.checks))
        self.assertEqual(len(result.adversarial_results), 6)
        self.assertTrue(all(item.passed for item in result.adversarial_results))

    def test_historian_readiness_blocks_failed_tests(self) -> None:
        results = list(passing_results())
        results[0] = TestExecutionResult(
            suite_id=results[0].suite_id,
            module_name=results[0].module_name,
            tests_run=1,
            failures=1,
            errors=0,
            skipped=0,
            successful=False,
        )

        result = HistorianOperationalReadinessVerifier().verify(tuple(results))

        self.assertFalse(result.certified)
        self.assertEqual(result.outcome, HistorianCertificationOutcome.NOT_CERTIFIED)
        self.assertTrue(result.deficiencies)

    def test_historian_certification_reports_archive_and_package_are_generated(self) -> None:
        result = HistorianOperationalReadinessVerifier().verify(passing_results())
        generator = HistorianReadinessReportGenerator(result)

        self.assertIn("Certification Outcome: CERTIFIED", generator.historian_operational_readiness_report())
        self.assertIn("Historian Group Status: CERTIFIED", generator.historian_certification_report())
        self.assertEqual(generator.corrective_action_register(), {"register_id": "CAR-069", "open_actions": (), "status": "clear"})
        archive = generator.historian_certification_archive()
        package = generator.historian_certification_package()
        self.assertEqual(archive["archive_id"], "HCA-069")
        self.assertTrue(archive["validated_knowledge_transfer_authorized"])
        self.assertTrue(package["historian_certified"])
        self.assertTrue(package["validated_knowledge_transfer_authorization"])

    def test_readiness_verifies_traceability_librarian_and_knowledge_control(self) -> None:
        result = HistorianOperationalReadinessVerifier().verify(passing_results())
        checks = {check.check_id: check for check in result.checks}

        self.assertTrue(checks["HORR-CHECK-004"].passed)
        self.assertIn("Reproduced learning assessment", checks["HORR-CHECK-004"].detail)
        self.assertTrue(checks["HORR-CHECK-006"].passed)
        self.assertIn("conflicted learning is blocked", checks["HORR-CHECK-006"].detail)
        self.assertTrue(checks["HORR-CHECK-008"].passed)
        self.assertIn("Validated knowledge package", checks["HORR-CHECK-008"].detail)

    def test_adversarial_scenarios_preserve_required_properties(self) -> None:
        results = HistorianAdversarialTestEngine().execute()

        names = tuple(result.name for result in results)
        self.assertIn("Missing Historian Office Finding", names)
        self.assertIn("Librarian Handoff Without Validation", names)
        self.assertTrue(all(result.deterministic_failure for result in results))
        self.assertTrue(all(result.preserved_auditability for result in results))
        self.assertTrue(all(result.preserved_empirical_integrity for result in results))


if __name__ == "__main__":
    unittest.main()
