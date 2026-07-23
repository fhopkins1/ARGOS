from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskRm005aOperationalSupport  # noqa: E402


class RiskRm005aOperationalTests(unittest.TestCase):
    def test_005a_package_covers_orders_and_is_ready_for_rm006(self) -> None:
        package = RiskRm005aOperationalSupport().build_operational_package(REPOSITORY_ROOT)

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-005A-001",
                "RISK-RM-005A-002",
                "RISK-RM-005A-003",
                "RISK-RM-005A-004",
                "RISK-RM-005A-005",
            ),
        )
        self.assertGreater(len(package.constitutional_rule_registry), len(package.closure_package.registry_package.execution_package.rule_evaluations))
        self.assertEqual(package.candidate_governance.result, EnterpriseCertificationDecision.PASS)
        self.assertEqual(package.authority_separation.independent_certification_decision, "RESERVED_FOR_RISK_RM_006")
        self.assertEqual(package.conditional_pass_governance.disposition_code, "CP-001")
        self.assertTrue(package.evidence_completion_review.readiness_for_rm006)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_temp_candidate_materializes_operational_rule_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src" / "argos" / "risk").mkdir(parents=True)
            (root / "Tests").mkdir()
            (root / "Documentation").mkdir()
            (root / "src" / "argos" / "risk" / "candidate_surface.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "Tests" / "test_risk_candidate_operational.py").write_text("def test_surface():\n    assert True\n", encoding="utf-8")
            (root / "Documentation" / "RISK-RM-005A-EVIDENCE.md").write_text("evidence\n", encoding="utf-8")
            package = RiskRm005aOperationalSupport().build_operational_package(root)

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(package.candidate_governance.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("candidate admissibility requirement failed: immutable_commit", package.candidate_governance.findings)
        self.assertTrue(package.constitutional_rule_registry)

    def test_rule_registry_fails_closed_when_requirement_rule_is_missing(self) -> None:
        support = RiskRm005aOperationalSupport()
        package = support.build_operational_package(REPOSITORY_ROOT)
        rules = support.materialize_constitutional_rule_registry(
            package.closure_package,
            omit_requirements=("RISK-RM-005A-004",),
        )

        self.assertTrue(any(record.result == EnterpriseCertificationDecision.FAIL for record in rules))
        self.assertIn("RISK-RM-005A-004", rules[-1].findings[0])

    def test_candidate_governance_fails_closed_on_forced_mutability(self) -> None:
        support = RiskRm005aOperationalSupport()
        package = support.build_operational_package(REPOSITORY_ROOT)
        governance = support.govern_certification_candidate(
            package.closure_package,
            REPOSITORY_ROOT,
            force_mutable_candidate=True,
        )

        self.assertEqual(governance.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("candidate admissibility requirement failed: not_forced_mutable", governance.findings)

    def test_authority_separation_and_review_fail_when_operational_authority_self_certifies(self) -> None:
        support = RiskRm005aOperationalSupport()
        package = support.build_operational_package(REPOSITORY_ROOT)
        authority = support.separate_certification_authority(
            package.closure_package,
            operational_issues_independent_certification=True,
        )
        conditional = support.evaluate_conditional_pass_governance(package.closure_package, authority)
        review = support.review_operational_evidence_completion(
            package.closure_package,
            package.constitutional_rule_registry,
            package.candidate_governance,
            authority,
            conditional,
        )

        self.assertEqual(authority.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(conditional.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(review.result, EnterpriseCertificationDecision.FAIL)
        self.assertFalse(review.readiness_for_rm006)

    def test_conditional_pass_is_restricted_and_not_independent_certification(self) -> None:
        support = RiskRm005aOperationalSupport()
        package = support.build_operational_package(REPOSITORY_ROOT)
        conditional = support.evaluate_conditional_pass_governance(
            package.closure_package,
            package.authority_separation,
            unresolved_deficiencies=("documentation correction pending",),
        )

        self.assertEqual(conditional.disposition_code, "CP-002")
        self.assertEqual(conditional.disposition_label, "CONDITIONAL PASS")
        self.assertTrue(conditional.remediation_required)
        self.assertFalse(conditional.independent_certification_eligible)
        self.assertIn("operational disposition is not independent certification", conditional.restrictions)


if __name__ == "__main__":
    unittest.main()
