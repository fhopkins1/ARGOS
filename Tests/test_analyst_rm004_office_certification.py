from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import AnalystOfficeCertificationSupport  # noqa: E402
from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402


class AnalystRm004OfficeCertificationTests(unittest.TestCase):
    def test_rm004_foundation_package_covers_candidate_identity_rule_threshold_and_test_registries(self) -> None:
        package = AnalystOfficeCertificationSupport().build_foundation_package()

        self.assertEqual(package.final_foundation_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "ANALYST-RM-004-001",
                "ANALYST-RM-004-002",
                "ANALYST-RM-004-003",
                "ANALYST-RM-004-004",
                "ANALYST-RM-004-005",
            ),
        )
        self.assertEqual(len(package.candidate_class_registry.entries), 15)
        self.assertIn("ACC-001", {entry.candidate_class_identifier for entry in package.candidate_class_registry.entries})
        self.assertIn("Mission Namespace", package.identity_normalization.namespaces)
        self.assertIn("alias resolution", package.identity_normalization.normalization_rules)
        self.assertEqual(len(package.evaluation_rule_registry.entries), 15)
        self.assertIn("Certification Closure", package.evaluation_rule_registry.evaluation_ordering)
        self.assertIn("Certification Blocking Threshold", package.certification_thresholds.threshold_classes)
        self.assertIn("every mandatory threshold passes", package.certification_thresholds.acceptance_standards)
        self.assertEqual(len(package.certification_test_registry.entries), 12)
        self.assertIn("Category L Traceability Certification", package.certification_test_registry.canonical_categories)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm004_foundation_records_fail_closed_on_defects(self) -> None:
        support = AnalystOfficeCertificationSupport()

        candidates = support.evaluate_candidate_class_registry(
            duplicate_identifier_findings=("ACC-001 duplicated",),
            multiple_classification_findings=("mission classified twice",),
            missing_owner_findings=("ACC-005 missing owner",),
            incomplete_applicability_findings=("replay requirement undefined",),
            dependency_graph_findings=("circular candidate dependency",),
            invalid_schema_reference_findings=("unknown schema",),
            replay_inconsistency_findings=("candidate class changed replay",),
            invariant_violations=("CCR-001 violated",),
        )
        identity = support.evaluate_identity_normalization(
            duplicate_canonical_identity_findings=("two canonical mission identifiers",),
            ambiguous_alias_findings=("alias maps to two objects",),
            namespace_reuse_findings=("identity reused cross namespace",),
            normalization_drift_findings=("case normalization changed",),
            equivalence_rule_findings=("object class ignored",),
            traceability_gaps=("canonical assignment lacks trace",),
            audit_gaps=("alias registration unaudited",),
        )
        rules = support.evaluate_evaluation_rule_registry(
            duplicate_rule_findings=("AER-001 duplicated",),
            missing_rule_findings=("Replay rule absent",),
            invalid_outcome_findings=("Maybe outcome",),
            dependency_cycle_findings=("rule dependency cycle",),
            registry_ambiguity_findings=("two active rule versions",),
            replay_divergence_findings=("rule outcome changed replay",),
            recovery_gaps=("registry version not restored",),
            audit_gaps=("rule execution unaudited",),
        )
        thresholds = support.evaluate_certification_thresholds(
            missing_threshold_classes=("Traceability Threshold",),
            invalid_outcome_findings=("Maybe"),
            weak_mandatory_threshold_findings=("mandatory threshold allowed discretion",),
            blocking_threshold_bypass_findings=("blocking failure continued",),
            traceability_gaps=("threshold lacks doctrine link",),
            audit_gaps=("threshold outcome unaudited",),
        )
        tests = support.evaluate_certification_test_registry(
            duplicate_test_findings=("ACT-001 duplicated",),
            missing_category_findings=("Category I Replay Certification",),
            missing_requirement_coverage=("confidence requirement untested",),
            nondeterministic_execution_findings=("test order changed outcome",),
            missing_evidence_findings=("audit evidence absent",),
            dependency_cycle_findings=("test dependency cycle",),
            replay_divergence_findings=("certification replay changed result",),
            recovery_gaps=("test state not restored",),
            audit_gaps=("failure classification unaudited",),
        )

        self.assertEqual(candidates.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("ACC-001 duplicated", candidates.duplicate_identifier_findings)
        self.assertIn("circular candidate dependency", candidates.dependency_graph_findings)
        self.assertEqual(identity.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("alias maps to two objects", identity.ambiguous_alias_findings)
        self.assertIn("object class ignored", identity.equivalence_rule_findings)
        self.assertEqual(rules.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Replay rule absent", rules.missing_rule_findings)
        self.assertIn("two active rule versions", rules.registry_ambiguity_findings)
        self.assertEqual(thresholds.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Traceability Threshold", thresholds.missing_threshold_classes)
        self.assertIn("blocking failure continued", thresholds.blocking_threshold_bypass_findings)
        self.assertEqual(tests.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Category I Replay Certification", tests.missing_category_findings)
        self.assertIn("confidence requirement untested", tests.missing_requirement_coverage)


if __name__ == "__main__":
    unittest.main()
