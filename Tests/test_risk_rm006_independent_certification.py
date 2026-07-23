from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskRm006IndependentCertificationSupport  # noqa: E402


class RiskRm006IndependentCertificationTests(unittest.TestCase):
    def test_independent_certification_package_covers_all_rm006_orders(self) -> None:
        package = RiskRm006IndependentCertificationSupport().build_independent_certification_package(REPOSITORY_ROOT)

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-006-001",
                "RISK-RM-006-002",
                "RISK-RM-006-003",
                "RISK-RM-006-004",
                "RISK-RM-006-005",
            ),
        )
        self.assertTrue(package.candidate_acceptance.accepted)
        self.assertEqual(package.certification_execution.result, EnterpriseCertificationDecision.PASS)
        self.assertEqual(package.finding_adjudications[0].classification, "NO_FINDING")
        self.assertEqual(package.certification_determination.determination, EnterpriseCertificationDecision.PASS)
        self.assertTrue(package.constitutional_closure.closed)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_unversioned_temp_candidate_is_rejected_before_independent_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src" / "argos" / "risk").mkdir(parents=True)
            (root / "Tests").mkdir()
            (root / "Documentation").mkdir()
            (root / "src" / "argos" / "risk" / "candidate_surface.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "Tests" / "test_risk_candidate_operational.py").write_text("def test_surface():\n    assert True\n", encoding="utf-8")
            (root / "Documentation" / "RISK-RM-006-EVIDENCE.md").write_text("evidence\n", encoding="utf-8")
            package = RiskRm006IndependentCertificationSupport().build_independent_certification_package(root)

        self.assertEqual(package.candidate_acceptance.result, EnterpriseCertificationDecision.FAIL)
        self.assertFalse(package.candidate_acceptance.accepted)
        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.FAIL)
        self.assertIn("candidate immutable revision is unavailable", package.candidate_acceptance.findings)

    def test_candidate_acceptance_fails_closed_on_forced_rejection(self) -> None:
        support = RiskRm006IndependentCertificationSupport()
        package = support.build_independent_certification_package(REPOSITORY_ROOT)
        acceptance = support.accept_candidate(
            package.operational_completion_package,
            force_rejection=("independent evidence mismatch",),
        )

        self.assertEqual(acceptance.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("independent evidence mismatch", acceptance.findings)

    def test_execution_findings_are_adjudicated_as_blocking(self) -> None:
        support = RiskRm006IndependentCertificationSupport()
        package = support.build_independent_certification_package(REPOSITORY_ROOT)
        execution = support.execute_independent_certification(
            package.operational_completion_package,
            package.candidate_acceptance,
            injected_findings=("metric threshold evidence mismatch",),
        )
        adjudications = support.adjudicate_findings(execution)
        determination = support.issue_certification_determination(
            package.operational_completion_package,
            package.candidate_acceptance,
            execution,
            adjudications,
        )

        self.assertEqual(execution.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(adjudications[0].classification, "CONSTITUTIONAL_BLOCKER")
        self.assertEqual(determination.determination, EnterpriseCertificationDecision.FAIL)
        self.assertIn("blocking adjudicated findings prohibit certification", determination.findings)

    def test_closure_fails_when_determination_does_not_pass(self) -> None:
        support = RiskRm006IndependentCertificationSupport()
        package = support.build_independent_certification_package(REPOSITORY_ROOT)
        execution = support.execute_independent_certification(
            package.operational_completion_package,
            package.candidate_acceptance,
            injected_findings=("replay variance",),
        )
        adjudications = support.adjudicate_findings(execution)
        determination = support.issue_certification_determination(
            package.operational_completion_package,
            package.candidate_acceptance,
            execution,
            adjudications,
        )
        closure = support.close_constitutional_certification(
            package.operational_completion_package,
            package.candidate_acceptance,
            execution,
            adjudications,
            determination,
        )

        self.assertEqual(closure.result, EnterpriseCertificationDecision.FAIL)
        self.assertFalse(closure.closed)
        self.assertIn("closure precondition failed: execution_completed", closure.findings)
        self.assertIn("closure precondition failed: determination_passed", closure.findings)


if __name__ == "__main__":
    unittest.main()
