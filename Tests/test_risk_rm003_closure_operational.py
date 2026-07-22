from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskRm003ClosureOperationalSupport  # noqa: E402


class RiskRm003ClosureOperationalTests(unittest.TestCase):
    def test_closure_operational_package_covers_orders_sixteen_through_twenty_five(self) -> None:
        package = RiskRm003ClosureOperationalSupport().build_operational_package(
            candidate_identifier="RM003-CLOSURE-FRESH-PACKET"
        )

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-003-016",
                "RISK-RM-003-017",
                "RISK-RM-003-018",
                "RISK-RM-003-019",
                "RISK-RM-003-020",
                "RISK-RM-003-021",
                "RISK-RM-003-022",
                "RISK-RM-003-023",
                "RISK-RM-003-024",
                "RISK-RM-003-025",
            ),
        )
        self.assertEqual(len(package.records), 10)
        self.assertEqual(package.records["RISK-RM-003-016"].title, "Risk Validation Framework")
        self.assertEqual(package.records["RISK-RM-003-025"].title, "Independent Risk Office Certification Suite")
        self.assertIn("traceability_to_certification", package.certification_trace)
        self.assertIn("risk_outputs_to_fusion", package.certification_trace)
        self.assertTrue(all(record.result == EnterpriseCertificationDecision.PASS for record in package.records.values()))
        self.assertEqual(package.replay_digest, RiskRm003ClosureOperationalSupport().build_operational_package().replay_digest)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_validation_commit_replay_configuration_and_error_records_fail_closed_on_omissions(self) -> None:
        support = RiskRm003ClosureOperationalSupport()

        validation = support.evaluate_validation_framework(implemented_domains=("validation domains", "validation ordering"))
        commits = support.evaluate_commit_boundaries(implemented_domains=("commit authority", "commit boundaries"))
        replay = support.evaluate_replay_equivalence(implemented_domains=("deterministic replay",))
        configuration = support.evaluate_configuration_object(implemented_domains=("configuration ownership", "canonical identity"))
        errors = support.evaluate_error_taxonomy(implemented_domains=("error classes",), findings=("implementation-defined error class admitted",))

        self.assertEqual(validation.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: evidence integrity", validation.findings)
        self.assertEqual(commits.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: transactional guarantees", commits.findings)
        self.assertEqual(replay.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: semantic equivalence", replay.findings)
        self.assertEqual(configuration.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: immutable schema", configuration.findings)
        self.assertEqual(errors.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("implementation-defined error class admitted", errors.findings)

    def test_traceability_outputs_fusion_and_certification_fail_closed_on_gaps(self) -> None:
        support = RiskRm003ClosureOperationalSupport()

        traceability = support.evaluate_traceability_architecture(implemented_domains=("doctrine-to-implementation traceability",))
        confidence_exposure = support.evaluate_confidence_exposure(implemented_domains=("confidence identity", "exposure identity"))
        mitigation = support.evaluate_mitigation_constitution(implemented_domains=("mitigation representation", "ownership"))
        fusion = support.evaluate_risk_fusion(implemented_domains=("fusion ownership", "fusion inputs"))
        certification = support.evaluate_independent_certification_suite(implemented_domains=("certification test classes", "execution procedures"))

        self.assertEqual(traceability.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: certification traceability", traceability.findings)
        self.assertEqual(confidence_exposure.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: uncertainty representation", confidence_exposure.findings)
        self.assertEqual(mitigation.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: execution readiness", mitigation.findings)
        self.assertEqual(fusion.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: Enterprise Risk determination", fusion.findings)
        self.assertEqual(certification.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: coverage requirements", certification.findings)

    def test_closure_guardrails_preserve_constitutional_authority(self) -> None:
        support = RiskRm003ClosureOperationalSupport()

        replay = support.evaluate_replay_equivalence()
        mitigation = support.evaluate_mitigation_constitution()
        fusion = support.evaluate_risk_fusion()
        certification = support.evaluate_independent_certification_suite()

        self.assertIn("replay never rewrites history", replay.deterministic_guards)
        self.assertIn("Risk Office recommends but never executes", mitigation.deterministic_guards)
        self.assertIn("fusion produces one Enterprise Risk Assessment", fusion.deterministic_guards)
        self.assertIn("complete RM003 coverage is required for RM004 progression", certification.deterministic_guards)


if __name__ == "__main__":
    unittest.main()
