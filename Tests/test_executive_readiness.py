from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.executive.readiness import (  # noqa: E402
    ExecutiveReadinessReportGenerator,
    ExecutiveReadinessVerifier,
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


class ExecutiveReadinessTests(unittest.TestCase):
    def test_executive_readiness_certifies_when_checks_pass(self) -> None:
        result = ExecutiveReadinessVerifier().verify(passing_results())

        self.assertTrue(result.certified)
        self.assertEqual(len(result.checks), 6)
        self.assertTrue(all(check.passed for check in result.checks))

    def test_executive_readiness_blocks_failed_tests(self) -> None:
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

        result = ExecutiveReadinessVerifier().verify(tuple(results))

        self.assertFalse(result.certified)
        self.assertFalse(result.checks[0].passed)

    def test_eorr_ecr_and_authorization_reports_are_generated(self) -> None:
        result = ExecutiveReadinessVerifier().verify(passing_results())
        generator = ExecutiveReadinessReportGenerator(result)

        self.assertIn("Status: PASS", generator.executive_orr())
        self.assertIn("Executive Status: COMPLETE", generator.executive_completion_report())
        self.assertIn("Decision: AUTHORIZED", generator.authorization_to_proceed())


if __name__ == "__main__":
    unittest.main()

