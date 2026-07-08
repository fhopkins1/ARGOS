from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.academy import (  # noqa: E402
    AcademyCertificationOutcome,
    AcademyEducationalStressTestEngine,
    AcademyOperationalReadinessVerifier,
    AcademyReadinessReportGenerator,
)
from argos.foundation.testing import TestExecutionResult, foundation_test_registry  # noqa: E402


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


class AcademyReadinessTests(unittest.TestCase):
    def test_academy_readiness_certifies_complete_academy(self) -> None:
        result = AcademyOperationalReadinessVerifier().verify(passing_results())

        self.assertTrue(result.certified)
        self.assertEqual(result.outcome, AcademyCertificationOutcome.CERTIFIED)
        self.assertEqual(len(result.checks), 8)
        self.assertTrue(all(check.passed for check in result.checks))
        self.assertEqual(len(result.stress_results), 6)
        self.assertTrue(all(item.passed for item in result.stress_results))

    def test_academy_readiness_blocks_failed_tests(self) -> None:
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

        result = AcademyOperationalReadinessVerifier().verify(tuple(results))

        self.assertFalse(result.certified)
        self.assertEqual(result.outcome, AcademyCertificationOutcome.NOT_CERTIFIED)
        self.assertTrue(result.deficiencies)

    def test_academy_reports_dashboard_corrective_actions_and_approval_are_generated(self) -> None:
        result = AcademyOperationalReadinessVerifier().verify(passing_results())
        generator = AcademyReadinessReportGenerator(result)

        self.assertIn("Certification Outcome: CERTIFIED", generator.academy_operational_readiness_framework())
        self.assertIn("Academy Status: CERTIFIED", generator.certification_report_template())
        self.assertEqual(generator.corrective_action_framework(), {"framework_id": "ACAF-085", "open_actions": (), "status": "clear"})
        standard = generator.educational_certification_standard()
        dashboard = generator.academy_readiness_dashboard()
        approval = generator.executive_approval_record()
        self.assertEqual(standard["standard_id"], "ECS-085")
        self.assertTrue(dashboard["argos_initial_architecture_complete"])
        self.assertTrue(approval["argos_initial_architecture_complete"])

    def test_readiness_verifies_lifecycle_traceability_personalization_and_quality(self) -> None:
        result = AcademyOperationalReadinessVerifier().verify(passing_results())
        checks = {check.check_id: check for check in result.checks}

        self.assertTrue(checks["AORR-CHECK-003"].passed)
        self.assertIn("integrated", checks["AORR-CHECK-003"].detail)
        self.assertTrue(checks["AORR-CHECK-004"].passed)
        self.assertIn("educational evidence", checks["AORR-CHECK-004"].detail)
        self.assertTrue(checks["AORR-CHECK-005"].passed)
        self.assertIn("Personalized interventions", checks["AORR-CHECK-005"].detail)
        self.assertTrue(checks["AORR-CHECK-008"].passed)
        self.assertIn("audit integrity", checks["AORR-CHECK-008"].detail)

    def test_educational_stress_tests_preserve_required_properties(self) -> None:
        results = AcademyEducationalStressTestEngine().execute()

        names = tuple(result.name for result in results)
        self.assertIn("Instruction Without Evidence Traceability", names)
        self.assertIn("Case Study Outcome Leakage", names)
        self.assertTrue(all(result.preserved_traceability for result in results))
        self.assertTrue(all(result.preserved_personalization for result in results))
        self.assertTrue(all(result.preserved_educational_quality for result in results))


if __name__ == "__main__":
    unittest.main()
