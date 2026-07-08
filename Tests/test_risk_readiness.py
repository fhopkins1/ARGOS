from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.testing import TestExecutionResult, foundation_test_registry  # noqa: E402
from argos.risk import RiskReadinessReportGenerator, RiskReadinessVerifier  # noqa: E402


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


class RiskReadinessTests(unittest.TestCase):
    def test_risk_readiness_certifies_when_checks_pass(self) -> None:
        result = RiskReadinessVerifier().verify(passing_results())

        self.assertTrue(result.certified)
        self.assertEqual(len(result.checks), 8)
        self.assertTrue(all(check.passed for check in result.checks))

    def test_risk_readiness_blocks_failed_tests(self) -> None:
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

        result = RiskReadinessVerifier().verify(tuple(results))

        self.assertFalse(result.certified)
        self.assertFalse(result.checks[0].passed)

    def test_risk_certification_reports_and_authorization_are_generated(self) -> None:
        result = RiskReadinessVerifier().verify(passing_results())
        generator = RiskReadinessReportGenerator(result)

        self.assertIn("Status: PASS", generator.risk_operational_readiness_report())
        self.assertIn("Risk Office Status: CERTIFIED", generator.risk_certification_report())
        self.assertIn("Decision: AUTHORIZED", generator.authorization_to_proceed())
        self.assertIn("Trader Group", generator.authorization_to_proceed())
        self.assertEqual(generator.corrective_action_register(), {"register_id": "CAR-051", "open_actions": (), "status": "clear"})

    def test_readiness_verifies_adversarial_traceability_and_handoff(self) -> None:
        result = RiskReadinessVerifier().verify(passing_results())
        checks = {check.check_id: check for check in result.checks}

        self.assertTrue(checks["RORR-CHECK-004"].passed)
        self.assertIn("Traceable sources", checks["RORR-CHECK-004"].detail)
        self.assertTrue(checks["RORR-CHECK-005"].passed)
        self.assertIn("rejected", checks["RORR-CHECK-005"].detail)
        self.assertTrue(checks["RORR-CHECK-007"].passed)
        self.assertIn("Trader", checks["RORR-CHECK-007"].detail)


if __name__ == "__main__":
    unittest.main()
