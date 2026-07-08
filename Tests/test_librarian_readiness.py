from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.testing import TestExecutionResult, foundation_test_registry  # noqa: E402
from argos.librarian import (  # noqa: E402
    LibrarianCertificationOutcome,
    LibrarianKnowledgeStressTestEngine,
    LibrarianOperationalReadinessVerifier,
    LibrarianReadinessReportGenerator,
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


class LibrarianReadinessTests(unittest.TestCase):
    def test_librarian_readiness_certifies_complete_group(self) -> None:
        result = LibrarianOperationalReadinessVerifier().verify(passing_results())

        self.assertTrue(result.certified)
        self.assertEqual(result.outcome, LibrarianCertificationOutcome.CERTIFIED)
        self.assertEqual(len(result.checks), 8)
        self.assertTrue(all(check.passed for check in result.checks))
        self.assertEqual(len(result.stress_results), 6)
        self.assertTrue(all(item.passed for item in result.stress_results))

    def test_librarian_readiness_blocks_failed_tests(self) -> None:
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

        result = LibrarianOperationalReadinessVerifier().verify(tuple(results))

        self.assertFalse(result.certified)
        self.assertEqual(result.outcome, LibrarianCertificationOutcome.NOT_CERTIFIED)
        self.assertTrue(result.deficiencies)

    def test_librarian_reports_dashboard_corrective_actions_and_approval_are_generated(self) -> None:
        result = LibrarianOperationalReadinessVerifier().verify(passing_results())
        generator = LibrarianReadinessReportGenerator(result)

        self.assertIn("Certification Outcome: CERTIFIED", generator.librarian_operational_readiness_framework())
        self.assertIn("Librarian Group Status: CERTIFIED", generator.certification_report_template())
        self.assertEqual(generator.corrective_action_framework(), {"framework_id": "LCAF-077", "open_actions": (), "status": "clear"})
        standard = generator.enterprise_knowledge_certification_standard()
        dashboard = generator.readiness_dashboard()
        approval = generator.executive_approval_record()
        self.assertEqual(standard["standard_id"], "EKCS-077")
        self.assertTrue(dashboard["academy_authorization_ready"])
        self.assertTrue(approval["academy_group_authorized"])

    def test_readiness_verifies_lifecycle_governance_traceability_quality_and_dashboard(self) -> None:
        result = LibrarianOperationalReadinessVerifier().verify(passing_results())
        checks = {check.check_id: check for check in result.checks}

        self.assertTrue(checks["LORR-CHECK-003"].passed)
        self.assertIn("integrated", checks["LORR-CHECK-003"].detail)
        self.assertTrue(checks["LORR-CHECK-004"].passed)
        self.assertIn("Governance standards", checks["LORR-CHECK-004"].detail)
        self.assertTrue(checks["LORR-CHECK-005"].passed)
        self.assertIn("executive traceability", checks["LORR-CHECK-005"].detail)
        self.assertTrue(checks["LORR-CHECK-008"].passed)
        self.assertIn("Healthy dashboard", checks["LORR-CHECK-008"].detail)

    def test_stress_tests_preserve_required_properties(self) -> None:
        results = LibrarianKnowledgeStressTestEngine().execute()

        names = tuple(result.name for result in results)
        self.assertIn("Missing Institutional Provenance", names)
        self.assertIn("Academy Handoff Without Certification", names)
        self.assertTrue(all(result.preserved_traceability for result in results))
        self.assertTrue(all(result.preserved_governance for result in results))
        self.assertTrue(all(result.preserved_auditability for result in results))


if __name__ == "__main__":
    unittest.main()
