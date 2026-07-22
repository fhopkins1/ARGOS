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

    def test_rm004_governance_registry_package_covers_rules_schemas_cross_references_evidence_and_decisions(self) -> None:
        package = RiskOfficeCertificationCompletionSupport().build_governance_registry_package()

        self.assertEqual(package.final_governance_registry_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-004-011",
                "RISK-RM-004-012",
                "RISK-RM-004-013",
                "RISK-RM-004-014",
                "RISK-RM-004-015",
            ),
        )
        self.assertIn("CR-006 Certification Rules", package.constitutional_rule_registry.rule_categories)
        self.assertEqual(package.constitutional_rule_registry.evaluation_outcomes, ("Pass", "Fail", "Not Evaluated"))
        self.assertIn("CS-008 Audit Schemas", package.schema_registry.schema_categories)
        self.assertIn("Relationship Definitions", package.schema_registry.schema_record_fields)
        self.assertIn("Decision Registry", package.registry_cross_reference_matrix.registry_inventory)
        self.assertIn("TRACES", package.registry_cross_reference_matrix.relationship_types)
        self.assertIn("Compatibility Matrix->Every Registry", package.registry_cross_reference_matrix.canonical_matrix)
        self.assertIn("Replay Evidence", package.certification_evidence_registry.evidence_classes)
        self.assertIn("Certification Package Evidence", package.certification_evidence_registry.evidence_classes)
        self.assertEqual(package.certification_evidence_registry.lifecycle_states[0], "Draft")
        self.assertIn("Certification Approval Decision", package.decision_registry.decision_categories)
        self.assertIn("Independent Certification Auditor", package.decision_registry.decision_authorities)
        self.assertIn("Compatible", package.decision_registry.decision_results)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm004_governance_registry_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeCertificationCompletionSupport()

        rules = support.evaluate_constitutional_rule_registry(
            duplicate_rule_findings=("CR-1 duplicated",),
            ambiguous_ownership_findings=("rule owned by runtime",),
            missing_dependency_findings=("evidence registry absent",),
            invalid_applicability_findings=("candidate class unknown",),
            traceability_gaps=("rule trace absent",),
            replay_recovery_findings=("rule replay diverged",),
            audit_gaps=("rule unaudited",),
            invariant_violations=("published rule mutable",),
        )
        schemas = support.evaluate_schema_registry(
            duplicate_schema_findings=("schema duplicated",),
            missing_schema_class_findings=("Audit Schemas",),
            ownership_findings=("schema owner ambiguous",),
            compatibility_gaps=("schema compatibility undefined",),
            relationship_cycle_findings=("schema relationship cycle",),
            validation_failures=("schema validation failed",),
            replay_recovery_gaps=("schema recovery changed version",),
            audit_gaps=("schema approval unaudited",),
        )
        cross_refs = support.evaluate_registry_cross_reference_matrix(
            duplicate_registry_findings=("Decision Registry duplicated",),
            missing_registry_findings=("Evidence Registry",),
            illegal_relationship_findings=("RELATES_TO used",),
            broken_reference_findings=("manifest references missing registry",),
            dependency_cycle_findings=("registry dependency cycle",),
            compatibility_gaps=("version compatibility absent",),
            replay_recovery_gaps=("cross reference replay changed",),
            audit_gaps=("matrix unaudited",),
        )
        evidence = support.evaluate_certification_evidence_registry(
            duplicate_evidence_findings=("EV-1 duplicated",),
            missing_class_findings=("Replay Evidence",),
            ownership_findings=("evidence owner runtime",),
            inadmissible_evidence_findings=("unverifiable evidence admitted",),
            integrity_failures=("hash mismatch",),
            provenance_gaps=("provenance missing",),
            traceability_gaps=("evidence orphaned",),
            replay_recovery_gaps=("evidence replay changed",),
            audit_gaps=("evidence unaudited",),
        )
        decisions = support.evaluate_decision_registry(
            duplicate_decision_findings=("DEC-1 duplicated",),
            missing_category_findings=("Certification Closure Decision",),
            invalid_outcome_findings=("MAYBE result",),
            authority_findings=("self-certification authority used",),
            evidence_gaps=("decision evidence absent",),
            dependency_cycle_findings=("decision dependency cycle",),
            traceability_gaps=("decision orphaned",),
            replay_recovery_gaps=("decision replay changed",),
            audit_gaps=("decision unaudited",),
        )

        self.assertEqual(rules.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("evidence registry absent", rules.missing_dependency_findings)
        self.assertEqual(schemas.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("schema relationship cycle", schemas.relationship_cycle_findings)
        self.assertEqual(cross_refs.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("RELATES_TO used", cross_refs.illegal_relationship_findings)
        self.assertEqual(evidence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("unverifiable evidence admitted", evidence.inadmissible_evidence_findings)
        self.assertEqual(decisions.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("self-certification authority used", decisions.authority_findings)

    def test_rm004_certification_closure_package_covers_schema_traceability_procedure_exceptions_and_closure(self) -> None:
        package = RiskOfficeCertificationCompletionSupport().build_certification_closure_package()

        self.assertEqual(package.final_certification_closure_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-004-016",
                "RISK-RM-004-017",
                "RISK-RM-004-018",
                "RISK-RM-004-019",
                "RISK-RM-004-020",
            ),
        )
        self.assertIn("Section J - Integrity Package", package.certification_package_schema.package_sections)
        self.assertIn("Certification Decision Record", package.certification_package_schema.mandatory_artifacts)
        self.assertIn("Certification Procedure Version", package.certification_package_schema.manifest_dependencies)
        self.assertEqual(package.certification_traceability_matrix.traceability_chain[0], "Constitutional Doctrine")
        self.assertEqual(package.certification_traceability_matrix.traceability_chain[-1], "Certification Result")
        self.assertIn("CT-010 Certification Decision Traceability", package.certification_traceability_matrix.traceability_domains)
        self.assertIn("Remediates", package.certification_traceability_matrix.relationship_types)
        self.assertEqual(package.certification_procedure.rule_outcomes, ("PASS", "FAIL", "NOT APPLICABLE"))
        self.assertEqual(package.certification_procedure.decision_outcomes, ("PASS", "CONDITIONAL PASS", "FAIL"))
        self.assertIn("Evidence Preservation", package.certification_procedure.procedure_stages)
        self.assertIn("Certification Evidence Packaging Exception", package.certification_exception_registry.authorized_exception_classes)
        self.assertIn("Constitutional Rule Waiver", package.certification_exception_registry.prohibited_exception_classes)
        self.assertEqual(package.certification_exception_registry.lifecycle_states[0], "Draft")
        self.assertEqual(
            package.independent_certification_closure.permitted_outcomes,
            (
                "Unconditional Independent Risk Office Certification PASS",
                "Independent Risk Office Certification FAIL",
            ),
        )
        self.assertIn("certification package", package.independent_certification_closure.archival_artifacts)
        self.assertIn("revocation requires authority", package.independent_certification_closure.invariants)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm004_certification_closure_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeCertificationCompletionSupport()

        package_schema = support.evaluate_certification_package_schema(
            missing_section_findings=("Section J omitted",),
            missing_artifact_findings=("Integrity Package absent",),
            unsupported_claim_findings=("claim lacks evidence",),
            undeclared_dependency_findings=("Test Suite Version implicit",),
            integrity_failures=("package hash mismatch",),
            replay_recovery_gaps=("package replay changed ordering",),
            audit_gaps=("submission unaudited",),
            invariant_violations=("published package mutable",),
        )
        traceability = support.evaluate_certification_traceability_matrix(
            orphan_artifact_findings=("evidence artifact orphaned",),
            missing_domain_findings=("CT-009 absent",),
            illegal_relationship_findings=("RELATES_TO used",),
            cycle_findings=("traceability cycle",),
            mixed_version_findings=("mixed schema version unauthorized",),
            replay_recovery_gaps=("trace graph replay diverged",),
            audit_gaps=("trace edge unaudited",),
        )
        procedure = support.evaluate_certification_procedure(
            incomplete_submission_findings=("manifest missing",),
            invalid_evidence_findings=("inadmissible evidence evaluated",),
            registry_failure_findings=("Decision Registry invalid",),
            dependency_failure_findings=("schema dependency unresolved",),
            traceability_failure_findings=("broken doctrine chain",),
            rule_execution_findings=("rule executed twice",),
            closure_gaps=("evidence not archived",),
            audit_gaps=("decision unaudited",),
        )
        exceptions = support.evaluate_certification_exception_registry(
            unauthorized_class_findings=("Constitutional Rule Waiver admitted",),
            missing_documentation_findings=("exception rationale absent",),
            approval_authority_findings=("runtime approved exception",),
            inadmissible_exception_findings=("determinism affected",),
            lifecycle_findings=("backward transition",),
            replay_recovery_gaps=("exception replay generated new state",),
            traceability_gaps=("exception orphaned",),
            audit_gaps=("exception approval unaudited",),
        )
        closure = support.evaluate_independent_certification_closure(
            unmet_precondition_findings=("replay verification absent",),
            invalid_outcome_findings=("CONDITIONAL PASS used",),
            archival_gap_findings=("registry snapshot omitted",),
            integrity_failure_findings=("manifest integrity failed",),
            revocation_authority_findings=("revocation without authority",),
            replay_recovery_gaps=("closure replay diverged",),
            traceability_gaps=("closure lacks doctrine link",),
            audit_gaps=("closure unaudited",),
        )

        self.assertEqual(package_schema.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Integrity Package absent", package_schema.missing_artifact_findings)
        self.assertEqual(traceability.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("traceability cycle", traceability.cycle_findings)
        self.assertEqual(procedure.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("rule executed twice", procedure.rule_execution_findings)
        self.assertEqual(exceptions.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("runtime approved exception", exceptions.approval_authority_findings)
        self.assertEqual(closure.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("CONDITIONAL PASS used", closure.invalid_outcome_findings)


if __name__ == "__main__":
    unittest.main()
