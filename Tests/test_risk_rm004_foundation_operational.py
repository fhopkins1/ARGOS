from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskRm004FoundationOperationalSupport  # noqa: E402


class RiskRm004FoundationOperationalTests(unittest.TestCase):
    def test_foundation_package_covers_orders_one_through_ten(self) -> None:
        package = RiskRm004FoundationOperationalSupport().build_operational_package(
            candidate_identifier="RM004-FOUNDATION-FRESH-PACKET"
        )

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-004-001",
                "RISK-RM-004-002",
                "RISK-RM-004-003",
                "RISK-RM-004-004",
                "RISK-RM-004-005",
                "RISK-RM-004-006",
                "RISK-RM-004-007",
                "RISK-RM-004-008",
                "RISK-RM-004-009",
                "RISK-RM-004-010",
            ),
        )
        self.assertEqual(len(package.records), 10)
        self.assertEqual(package.records["RISK-RM-004-001"].title, "Candidate Class Registry")
        self.assertEqual(package.records["RISK-RM-004-010"].title, "Version Compatibility Matrix")
        self.assertIn("rules_to_thresholds_to_tests", package.registry_trace)
        self.assertIn("identifiers_to_versions", package.registry_trace)
        self.assertTrue(all(record.result == EnterpriseCertificationDecision.PASS for record in package.records.values()))
        self.assertEqual(package.replay_digest, RiskRm004FoundationOperationalSupport().build_operational_package().replay_digest)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_candidate_identity_rules_threshold_and_tests_fail_closed_on_missing_domains(self) -> None:
        support = RiskRm004FoundationOperationalSupport()

        candidates = support.evaluate_candidate_class_registry(implemented_domains=("candidate classes", "candidate identity"))
        identity = support.evaluate_identity_normalization_tables(implemented_domains=("canonical identity",))
        rules = support.evaluate_evaluation_rule_registry(implemented_domains=("evaluation rules", "deterministic procedures"))
        thresholds = support.evaluate_certification_threshold_doctrine(implemented_domains=("threshold ownership", "pass criteria"))
        tests = support.evaluate_certification_test_registry(implemented_domains=("certification tests", "expected behavior"), findings=("unregistered test executed",))

        self.assertEqual(candidates.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: required evidence", candidates.findings)
        self.assertEqual(identity.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: alias resolution", identity.findings)
        self.assertEqual(rules.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: rule dependencies", rules.findings)
        self.assertEqual(thresholds.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: failure criteria", thresholds.findings)
        self.assertEqual(tests.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("unregistered test executed", tests.findings)

    def test_collision_metrics_manifest_identifier_and_versions_fail_closed_on_gaps(self) -> None:
        support = RiskRm004FoundationOperationalSupport()

        collisions = support.evaluate_identity_collision_resolution(implemented_domains=("collision classes",))
        metrics = support.evaluate_metrics_registry(implemented_domains=("metric identity", "metric ownership"))
        manifest = support.evaluate_certification_manifest_schema(implemented_domains=("manifest identity", "artifact inventory"))
        identifiers = support.evaluate_identifier_registry(implemented_domains=("identifier ownership", "namespaces"))
        versions = support.evaluate_version_compatibility_matrix(implemented_domains=("compatibility rules", "deterministic evaluation"))

        self.assertEqual(collisions.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: identity integrity", collisions.findings)
        self.assertEqual(metrics.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: provenance", metrics.findings)
        self.assertEqual(manifest.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: evidence linkage", manifest.findings)
        self.assertEqual(identifiers.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: uniqueness requirements", identifiers.findings)
        self.assertEqual(versions.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: replay compatibility", versions.findings)

    def test_foundation_guardrails_prevent_unregistered_certification_behavior(self) -> None:
        support = RiskRm004FoundationOperationalSupport()

        candidates = support.evaluate_candidate_class_registry()
        rules = support.evaluate_evaluation_rule_registry()
        tests = support.evaluate_certification_test_registry()
        versions = support.evaluate_version_compatibility_matrix()

        self.assertIn("unregistered candidates are inadmissible", candidates.deterministic_guards)
        self.assertIn("only registered rules can certify", rules.deterministic_guards)
        self.assertIn("no test exists outside registry", tests.deterministic_guards)
        self.assertIn("no implementation-defined compatibility", versions.deterministic_guards)


if __name__ == "__main__":
    unittest.main()
