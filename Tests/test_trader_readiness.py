from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.testing import TestExecutionResult, foundation_test_registry  # noqa: E402
from argos.trader import (  # noqa: E402
    TraderCertificationOutcome,
    TraderOperationalReadinessVerifier,
    TraderReadinessReportGenerator,
    TraderStressTestEngine,
    trader_readiness_case_file,
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


class TraderReadinessTests(unittest.TestCase):
    def test_trader_readiness_certifies_complete_group(self) -> None:
        result = TraderOperationalReadinessVerifier().verify(passing_results())

        self.assertTrue(result.certified)
        self.assertEqual(result.outcome, TraderCertificationOutcome.CERTIFIED)
        self.assertEqual(len(result.checks), 8)
        self.assertTrue(all(check.passed for check in result.checks))
        self.assertEqual(len(result.stress_results), 12)
        self.assertTrue(all(stress.passed for stress in result.stress_results))

    def test_trader_readiness_blocks_failed_tests(self) -> None:
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

        result = TraderOperationalReadinessVerifier().verify(tuple(results))

        self.assertFalse(result.certified)
        self.assertEqual(result.outcome, TraderCertificationOutcome.NOT_CERTIFIED)
        self.assertTrue(result.deficiencies)
        case_file = trader_readiness_case_file(result)
        self.assertEqual(case_file.case_file_id, "TRCF-060")
        self.assertTrue(case_file.evidence_preserved)

    def test_trader_certification_reports_and_archive_are_generated(self) -> None:
        result = TraderOperationalReadinessVerifier().verify(passing_results())
        generator = TraderReadinessReportGenerator(result)

        self.assertIn("Certification Outcome: CERTIFIED", generator.trader_operational_readiness_report())
        self.assertIn("Trader Group Status: CERTIFIED", generator.trader_certification_report())
        self.assertEqual(generator.corrective_action_register(), {"register_id": "CAR-060", "open_actions": (), "status": "clear"})
        archive = generator.trader_certification_archive()
        self.assertEqual(archive["archive_id"], "TCA-060")
        self.assertEqual(archive["certification_status"], "CERTIFIED")
        self.assertTrue(archive["evidence_preserved"])

    def test_readiness_verifies_lifecycle_stress_traceability_and_prompt(self) -> None:
        verifier = TraderOperationalReadinessVerifier()
        result = verifier.verify(passing_results())
        checks = {check.check_id: check for check in result.checks}

        self.assertTrue(checks["TORR-CHECK-003"].passed)
        self.assertIn("historian_recording", checks["TORR-CHECK-003"].detail)
        self.assertTrue(checks["TORR-CHECK-006"].passed)
        self.assertTrue(checks["TORR-CHECK-007"].passed)
        prompt = verifier.system_prompt()
        self.assertIn("Trader Operational Readiness Review Board", prompt.prompt_text)
        self.assertIn("Every detected deficiency shall generate a Trader Readiness Case File", prompt.prompt_text)
        self.assertIn("Never overwrite readiness evidence", prompt.prompt_text)

    def test_stress_scenarios_preserve_required_properties(self) -> None:
        results = TraderStressTestEngine().execute()

        names = tuple(result.name for result in results)
        self.assertIn("Broker Failure", names)
        self.assertIn("Infrastructure Failure", names)
        self.assertTrue(all(result.preserved_execution_integrity for result in results))
        self.assertTrue(all(result.preserved_auditability for result in results))
        self.assertTrue(all(result.maintained_determinism for result in results))
        self.assertTrue(all(result.generated_operational_records for result in results))


if __name__ == "__main__":
    unittest.main()
