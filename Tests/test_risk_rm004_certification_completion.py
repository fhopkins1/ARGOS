from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskOfficeCertificationCompletionSupport  # noqa: E402


class RiskRm004CertificationCompletionTests(unittest.TestCase):
    def test_rm004_foundation_package_covers_candidate_identity_rule_threshold_and_test_registries(self) -> None:
        package = RiskOfficeCertificationCompletionSupport().build_foundation_package()

        self.assertEqual(package.final_foundation_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-004-001",
                "RISK-RM-004-002",
                "RISK-RM-004-003",
                "RISK-RM-004-004",
                "RISK-RM-004-005",
            ),
        )
        self.assertIn("Risk Assessment", package.candidate_class_registry.registry_scope)
        self.assertIn("CC-007 Certification Objects", package.candidate_class_registry.candidate_categories)
        self.assertIn("Applicability", package.candidate_class_registry.schema_sections)
        self.assertIn("certification requirement", package.candidate_class_registry.applicability_declarations)
        self.assertIn("registry identifiers", package.identity_normalization.normalized_identity_scope)
        self.assertEqual(package.identity_normalization.normalization_table["Registered Alias"], "Resolve to canonical identifier")
        self.assertIn("cross-namespace normalization prohibited", package.identity_normalization.namespace_rules)
        self.assertIn("Authority Rules", package.evaluation_rule_registry.rule_categories)
        self.assertEqual(package.evaluation_rule_registry.evaluation_order[0], "Authority Rules")
        self.assertEqual(package.evaluation_rule_registry.permitted_outcomes, ("PASS", "FAIL", "NOT APPLICABLE"))
        self.assertIn("Critical", package.evaluation_rule_registry.severity_levels)
        self.assertEqual(package.certification_thresholds.decision_classes, ("PASS", "CONDITIONAL PASS", "FAIL", "INCOMPLETE"))
        self.assertIn("complete traceability", package.certification_thresholds.pass_thresholds)
        self.assertIn("Certification Package Verification", package.certification_thresholds.evaluation_order)
        self.assertIn("Traceability Failure", package.certification_thresholds.failure_classes)
        self.assertIn("Authority Verification", package.certification_test_registry.test_categories)
        self.assertIn("Constitutional Invariants", package.certification_test_registry.certification_domains)
        self.assertIn("Execution Dependencies", package.certification_test_registry.registry_fields)
        self.assertIn("acyclic dependencies", package.certification_test_registry.dependency_requirements)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm004_foundation_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeCertificationCompletionSupport()

        candidates = support.evaluate_candidate_class_registry(
            duplicate_identifier_findings=("RCC-001 duplicated",),
            multiple_classification_findings=("Risk Assessment classified twice",),
            missing_owner_findings=("registry owner absent",),
            incomplete_applicability_findings=("required evidence classes omitted",),
            dependency_graph_findings=("candidate dependency cycle",),
            invalid_schema_reference_findings=("unknown schema reference",),
            replay_inconsistency_findings=("candidate class changed replay",),
            invariant_violations=("published registry entry mutable",),
        )
        identity = support.evaluate_identity_normalization_tables(
            duplicate_canonical_identity_findings=("two canonical Risk Assessment IDs",),
            ambiguous_alias_findings=("alias resolves to two identities",),
            namespace_reuse_findings=("namespace reused",),
            normalization_drift_findings=("case normalization drifted",),
            equivalence_rule_findings=("semantic similarity accepted",),
            traceability_gaps=("alias lacks trace",),
            audit_gaps=("normalization unaudited",),
        )
        rules = support.evaluate_evaluation_rule_registry(
            duplicate_rule_findings=("RER-001 duplicated",),
            missing_rule_findings=("Replay Rules absent",),
            invalid_outcome_findings=("MAYBE outcome",),
            dependency_cycle_findings=("rule dependency cycle",),
            registry_ambiguity_findings=("two active rule versions",),
            replay_divergence_findings=("rule outcome changed replay",),
            recovery_gaps=("registry not restored",),
            audit_gaps=("rule execution unaudited",),
        )
        thresholds = support.evaluate_certification_thresholds(
            missing_threshold_classes=("Traceability Threshold",),
            invalid_outcome_findings=("MAYBE"),
            weak_mandatory_threshold_findings=("mandatory threshold allowed discretion",),
            blocking_threshold_bypass_findings=("blocking failure continued",),
            traceability_gaps=("threshold lacks doctrine link",),
            audit_gaps=("threshold unaudited",),
        )
        tests = support.evaluate_certification_test_registry(
            duplicate_test_findings=("RCT-001 duplicated",),
            missing_category_findings=("Replay Verification",),
            missing_requirement_coverage=("confidence requirement untested",),
            nondeterministic_execution_findings=("test order changed outcome",),
            missing_evidence_findings=("generated evidence absent",),
            dependency_cycle_findings=("test dependency cycle",),
            replay_divergence_findings=("certification replay diverged",),
            recovery_gaps=("test registry not restored",),
            audit_gaps=("test result unaudited",),
        )

        self.assertEqual(candidates.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("candidate dependency cycle", candidates.dependency_graph_findings)
        self.assertEqual(identity.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("semantic similarity accepted", identity.equivalence_rule_findings)
        self.assertEqual(rules.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Replay Rules absent", rules.missing_rule_findings)
        self.assertEqual(thresholds.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("blocking failure continued", thresholds.blocking_threshold_bypass_findings)
        self.assertEqual(tests.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("confidence requirement untested", tests.missing_requirement_coverage)

    def test_rm004_registry_governance_package_covers_collision_metrics_manifest_identifiers_and_versions(self) -> None:
        package = RiskOfficeCertificationCompletionSupport().build_registry_governance_package()

        self.assertEqual(package.final_registry_governance_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-004-006",
                "RISK-RM-004-007",
                "RISK-RM-004-008",
                "RISK-RM-004-009",
                "RISK-RM-004-010",
            ),
        )
        self.assertIn("IC-004 Ownership Conflict", package.identity_collision_resolution.collision_classes)
        self.assertEqual(package.identity_collision_resolution.resolution_sequence[0], "Verify canonical identity")
        self.assertEqual(package.identity_collision_resolution.resolution_outcomes, ("Resolved", "Rejected"))
        self.assertIn("CM-007 Replay Metrics", package.metrics_registry.metric_categories)
        self.assertIn("Coverage Index", package.metrics_registry.metric_units)
        self.assertIn("Certification Manifests", package.metrics_registry.admissible_sources)
        self.assertIn("Compatibility Declaration", package.certification_manifest_schema.schema_sections)
        self.assertIn("Certification Evidence Package", package.certification_manifest_schema.mandatory_artifacts)
        self.assertEqual(package.certification_manifest_schema.lifecycle_states[0], "Draft")
        self.assertEqual(package.certification_manifest_schema.lifecycle_states[-1], "Archived")
        self.assertIn("Risk Assessment Identifier", package.identifier_registry.namespaces)
        self.assertIn("Manifest Identifier", package.identifier_registry.namespaces)
        self.assertIn("constitutional testing", package.identifier_registry.reserved_ranges)
        self.assertIn("Evidence Package Version", package.version_compatibility_matrix.version_categories)
        self.assertIn("Migration Required", package.version_compatibility_matrix.classifications)
        self.assertIn("unknown compatibility prohibited", package.version_compatibility_matrix.invariants)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm004_registry_governance_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeCertificationCompletionSupport()

        collisions = support.evaluate_identity_collision_resolution(
            duplicate_identifier_findings=("RA-1 duplicated",),
            conflicting_ownership_findings=("same identity owned by Analyst",),
            unresolved_collision_findings=("alias collision unresolved",),
            namespace_allocation_findings=("namespace reused",),
            replay_identity_findings=("replay identity changed",),
            recovery_identity_findings=("recovery restored conflict",),
            traceability_gaps=("collision lacks lineage",),
            audit_gaps=("collision unaudited",),
        )
        metrics = support.evaluate_metrics_registry(
            duplicate_metric_findings=("MET-1 duplicated",),
            missing_metric_class_findings=("Replay Metrics",),
            ownership_findings=("metric owned by runtime",),
            inadmissible_input_findings=("implementation counter admitted",),
            dependency_cycle_findings=("metric dependency cycle",),
            reproducibility_findings=("metric value changed",),
            traceability_gaps=("metric lacks source evidence",),
            audit_gaps=("metric unaudited",),
        )
        manifest = support.evaluate_certification_manifest_schema(
            missing_schema_sections=("Compatibility Declaration",),
            missing_artifact_findings=("Audit Records",),
            evidence_linkage_findings=("evidence inventory broken",),
            compatibility_findings=("registry version incompatible",),
            validation_failures=("manifest validation failed",),
            replay_divergence_findings=("manifest replay changed",),
            recovery_gaps=("manifest not restored",),
            audit_gaps=("manifest approval unaudited",),
        )
        identifiers = support.evaluate_identifier_registry(
            duplicate_namespace_findings=("Risk Assessment Identifier duplicated",),
            missing_namespace_findings=("Manifest Identifier",),
            allocation_findings=("partial allocation committed",),
            uniqueness_findings=("identifier reused",),
            replay_identifier_findings=("replay generated new identifier",),
            recovery_identifier_findings=("recovery inferred allocation",),
            traceability_gaps=("identifier lacks provenance",),
            audit_gaps=("allocation unaudited",),
        )
        versions = support.evaluate_version_compatibility_matrix(
            missing_compatibility_entries=("Manifest->Evidence",),
            unknown_compatibility_findings=("unknown compatibility assumed",),
            incompatible_artifact_findings=("incompatible manifest accepted",),
            supersession_findings=("historical compatibility overwritten",),
            replay_divergence_findings=("compatibility replay changed",),
            recovery_gaps=("matrix not restored",),
            audit_gaps=("compatibility unaudited",),
        )

        self.assertEqual(collisions.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("alias collision unresolved", collisions.unresolved_collision_findings)
        self.assertEqual(metrics.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("implementation counter admitted", metrics.inadmissible_input_findings)
        self.assertEqual(manifest.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Compatibility Declaration", manifest.missing_schema_sections)
        self.assertEqual(identifiers.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("identifier reused", identifiers.uniqueness_findings)
        self.assertEqual(versions.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("unknown compatibility assumed", versions.unknown_compatibility_findings)


if __name__ == "__main__":
    unittest.main()
