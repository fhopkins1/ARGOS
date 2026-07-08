from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.readiness import FoundationReadinessVerifier, FoundationReportGenerator  # noqa: E402
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


class FoundationReadinessTests(unittest.TestCase):
    def test_readiness_authorizes_when_all_checks_and_tests_pass(self) -> None:
        result = FoundationReadinessVerifier().verify(passing_results())

        self.assertTrue(result.authorized)
        self.assertEqual(len(result.checks), 5)
        self.assertTrue(all(check.passed for check in result.checks))

    def test_readiness_blocks_when_any_test_fails(self) -> None:
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

        result = FoundationReadinessVerifier().verify(tuple(results))

        self.assertFalse(result.authorized)
        self.assertFalse(result.checks[0].passed)

    def test_operational_readiness_report_contains_check_statuses(self) -> None:
        result = FoundationReadinessVerifier().verify(passing_results())
        report = FoundationReportGenerator(result).operational_readiness_report()

        self.assertIn("# ORR-001 Operational Readiness Report", report)
        self.assertIn("Status: PASS", report)
        self.assertIn("ORR-CHECK-005: PASS", report)

    def test_foundation_completion_report_and_authorization_are_generated(self) -> None:
        result = FoundationReadinessVerifier().verify(passing_results())
        generator = FoundationReportGenerator(result)

        self.assertIn("Foundation Status: COMPLETE", generator.foundation_completion_report())
        self.assertIn("Decision: AUTHORIZED", generator.authorization_to_proceed())


if __name__ == "__main__":
    unittest.main()

