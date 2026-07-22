from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import AnalystOfficeSpecificationSupport  # noqa: E402
from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402


class AnalystRm003OfficeSpecificationTests(unittest.TestCase):
    def test_rm003_analytical_mission_specification_covers_root_authority_object(self) -> None:
        package = AnalystOfficeSpecificationSupport().build_package()

        mission = package.analytical_mission
        self.assertEqual(package.final_specification_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(package.specification_order_coverage, ("ANALYST-RM-003-001",))
        self.assertIn("Identity", mission.schema_sections)
        self.assertIn("Mission Identifier", mission.schema_sections["Identity"])
        self.assertIn("Mission Authority Token", mission.schema_sections["Authority"])
        self.assertIn("Completion Contract", mission.schema_sections["Mission Definition"])
        self.assertIn("Workflow Execution Token Identifier", mission.identity_fields)
        self.assertIn("perform deterministic reasoning", mission.permitted_authorities)
        self.assertIn("trade execution", mission.prohibited_authorities)
        self.assertIn("Analysis Plan", mission.subordinate_relationships)
        self.assertIn("Recovering", mission.lifecycle_states)
        self.assertIn("identifier uniqueness", mission.validation_requirements)
        self.assertIn("mission identity", mission.persistent_elements)
        self.assertIn("Mission Identifier", mission.replay_restoration_fields)
        self.assertIn("mission version", mission.recovery_restoration_fields)
        self.assertIn("authorization", mission.audit_events)
        self.assertIn("mission identity is immutable", mission.invariant_registry)
        self.assertTrue(mission.fail_closed)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm003_analytical_mission_specification_fails_closed_on_defects(self) -> None:
        mission = AnalystOfficeSpecificationSupport().evaluate_analytical_mission_specification(
            missing_schema_fields=("Mission Authority Token", "Completion Contract"),
            duplicate_identity_findings=("AN-MISSION-1 reused",),
            authority_violations=("trade execution granted",),
            lifecycle_violations=("Created->Active",),
            validation_failures=("configuration compatibility failed",),
            persistence_gaps=("audit metadata",),
            replay_divergence_findings=("mission identity regenerated",),
            recovery_inference_findings=("scope inferred from output",),
            traceability_gaps=("reasoning graph missing parent mission",),
            fail_closed=False,
        )

        self.assertEqual(mission.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Mission Authority Token", mission.missing_schema_fields)
        self.assertIn("Completion Contract", mission.missing_schema_fields)
        self.assertIn("AN-MISSION-1 reused", mission.duplicate_identity_findings)
        self.assertIn("trade execution granted", mission.authority_violations)
        self.assertIn("Created->Active", mission.lifecycle_violations)
        self.assertIn("configuration compatibility failed", mission.validation_failures)
        self.assertIn("mission identity regenerated", mission.replay_divergence_findings)
        self.assertIn("scope inferred from output", mission.recovery_inference_findings)
        self.assertFalse(mission.fail_closed)

    def test_rm003_mission_doctrine_package_covers_lifecycle_sufficiency_equivalence_freshness_and_obs(self) -> None:
        package = AnalystOfficeSpecificationSupport().build_mission_doctrine_package()

        self.assertEqual(package.final_mission_doctrine_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.specification_order_coverage,
            (
                "ANALYST-RM-003-006",
                "ANALYST-RM-003-007",
                "ANALYST-RM-003-008",
                "ANALYST-RM-003-009",
                "ANALYST-RM-003-010",
            ),
        )
        self.assertEqual(package.mission_lifecycle.authority_acquisition_transition, "Ready->Executing")
        self.assertIn("Completed", package.mission_lifecycle.authority_relinquishment_states)
        self.assertIn("Evidence Sufficiency", package.analytical_sufficiency.sufficiency_categories)
        self.assertIn("Constitutionally Complete", package.analytical_sufficiency.completion_outcomes)
        self.assertIn("Semantic Equivalence", package.analytical_equivalence.equivalence_domains)
        self.assertIn("canonical reference ordering", package.analytical_equivalence.normalization_steps)
        self.assertIn("Replay Admissible", package.analytical_freshness.freshness_states)
        self.assertIn("freshness duration", package.analytical_freshness.window_fields)
        self.assertIn("Belief Representation", package.organizational_belief_state.schema_sections)
        self.assertIn("Current Accepted Conclusion", package.organizational_belief_state.schema_sections["Belief Representation"])
        self.assertIn("hypotheses preserved", package.organizational_belief_state.invariants)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm003_mission_doctrine_records_fail_closed_on_defects(self) -> None:
        support = AnalystOfficeSpecificationSupport()

        lifecycle = support.evaluate_mission_lifecycle_specification(
            illegal_transition_findings=("Completed->Executing",),
            duplicate_transition_findings=("Executing->Suspended repeated",),
            missing_authority_findings=("Ready->Executing missing authority",),
            invalid_checkpoint_findings=("checkpoint corrupt",),
            persistence_failures=("transition not committed",),
            provenance_gaps=("predecessor transition missing",),
            replay_divergence_findings=("state ordering changed",),
            recovery_boundary_findings=("recovered from uncommitted state",),
        )
        sufficiency = support.evaluate_sufficiency_specification(
            missing_categories=("Traceability Sufficiency",),
            invalid_completion_outcomes=("Maybe Complete",),
            sequencing_violations=("confidence before reasoning",),
            evidence_deficiencies=("required evidence missing",),
            reasoning_deficiencies=("inference chain open",),
            validation_deficiencies=("invariant validation missing",),
            confidence_deficiencies=("confidence undefined",),
            traceability_deficiencies=("audit chain broken",),
        )
        equivalence = support.evaluate_equivalence_specification(
            missing_scope=("Organizational Belief States",),
            normalization_failures=("timestamps not canonicalized",),
            semantic_comparison_failures=("meaning changed",),
            duplicate_resolution_findings=("duplicate silently discarded",),
            supersession_trace_gaps=("predecessor missing",),
            replay_divergence_findings=("duplicate classification changed",),
            recovery_state_findings=("comparison repeated inconsistently",),
        )
        freshness = support.evaluate_freshness_specification(
            missing_scope=("Validation Records",),
            invalid_state_findings=("Stale",),
            implicit_window_findings=("expiration inferred",),
            temporal_nondeterminism_findings=("local machine time used",),
            inheritance_violations=("derived object fresher than source",),
            replay_admissibility_findings=("operational freshness changed replay",),
            recovery_admissibility_findings=("expired mission resumed",),
            audit_gaps=("freshness transition unaudited",),
        )
        obs = support.evaluate_organizational_belief_state_specification(
            missing_schema_fields=("Current Accepted Conclusion",),
            ownership_violations=("Risk modified belief",),
            unsupported_conclusion_findings=("conclusion lacks evidence",),
            implicit_assumption_findings=("assumption hidden",),
            hypothesis_preservation_findings=("rejected hypothesis removed",),
            contradiction_preservation_findings=("contradiction discarded",),
            supersession_violations=("previous belief overwritten",),
            replay_divergence_findings=("accepted conclusion changed"),
            recovery_mutation_findings=("belief state mutated"),
        )

        self.assertEqual(lifecycle.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Completed->Executing", lifecycle.illegal_transition_findings)
        self.assertEqual(sufficiency.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Traceability Sufficiency", sufficiency.missing_categories)
        self.assertIn("Maybe Complete", sufficiency.invalid_completion_outcomes)
        self.assertEqual(equivalence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Organizational Belief States", equivalence.missing_scope)
        self.assertIn("duplicate silently discarded", equivalence.duplicate_resolution_findings)
        self.assertEqual(freshness.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Stale", freshness.invalid_state_findings)
        self.assertIn("local machine time used", freshness.temporal_nondeterminism_findings)
        self.assertEqual(obs.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Current Accepted Conclusion", obs.missing_schema_fields)
        self.assertIn("Risk modified belief", obs.ownership_violations)

    def test_rm003_constitutional_architecture_package_covers_rejection_evidence_provenance_state_and_persistence(self) -> None:
        package = AnalystOfficeSpecificationSupport().build_constitutional_architecture_package()

        self.assertEqual(package.final_architecture_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.specification_order_coverage,
            (
                "ANALYST-RM-003-011",
                "ANALYST-RM-003-012",
                "ANALYST-RM-003-013",
                "ANALYST-RM-003-014",
                "ANALYST-RM-003-015",
            ),
        )
        self.assertIn("AR-015 Constitutional Invariant Rejection", package.rejection_taxonomy.rejection_classes)
        self.assertIn("Rejection Class", package.rejection_taxonomy.rejection_record_fields)
        self.assertIn("Constitutional Identity", package.evidence_constitution.schema_sections)
        self.assertIn("Evidence Identifier", package.evidence_constitution.schema_sections["Constitutional Identity"])
        self.assertIn("provenance completeness", package.evidence_constitution.admissibility_rules)
        self.assertIn("Reasoning Graphs", package.provenance_architecture.governed_object_scope)
        self.assertIn("Final Conclusion", package.provenance_architecture.required_chain)
        self.assertIn("Terminated", package.office_state_machine.execution_states)
        self.assertIn("Created->Executing", package.office_state_machine.prohibited_transitions)
        self.assertIn("Mission State", package.persistent_state.persistent_inventory)
        self.assertIn("Runtime Execution Context", package.persistent_state.transient_inventory)
        self.assertEqual(package.persistent_state.classification_rules["Runtime Memory"], "Transient")
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm003_constitutional_architecture_records_fail_closed_on_defects(self) -> None:
        support = AnalystOfficeSpecificationSupport()

        rejection = support.evaluate_rejection_taxonomy_specification(
            missing_classes=("AR-014 Replay Rejection",),
            ambiguous_authority_findings=("external office assigned rejection",),
            mutation_findings=("rejection class edited",),
            lifecycle_violations=("Rejected->Under Evaluation",),
            missing_audit_evidence=("triggering evidence absent",),
            replay_inconsistencies=("AR-005 replayed as AR-006",),
            recovery_inconsistencies=("recovery re-adjudicated object",),
            traceability_gaps=("rule evaluation missing",),
        )
        evidence = support.evaluate_evidence_constitution_specification(
            missing_schema_fields=("Evidence Identifier",),
            unapproved_class_findings=("Opinion Evidence",),
            admissibility_failures=("provenance incomplete",),
            normalization_failures=("timestamp not canonicalized",),
            orphaned_relationship_findings=("final conclusion reference missing",),
            persistence_gaps=("validation state omitted",),
            replay_divergence_findings=("evidence identity regenerated",),
            recovery_mutation_findings=("accepted evidence modified",),
        )
        provenance = support.evaluate_provenance_architecture_specification(
            missing_scope=("Recommendations",),
            undocumented_source_findings=("manual spreadsheet input",),
            graph_cycle_findings=("confidence depends on itself",),
            missing_chain_stages=("Certification Evidence",),
            validation_failures=("dependency integrity failed",),
            persistence_gaps=("edge metadata omitted",),
            replay_divergence_findings=("lineage changed",),
            recovery_gaps=("node relationship lost",),
        )
        state_machine = support.evaluate_office_state_machine_specification(
            missing_states=("Output Validation",),
            illegal_transition_findings=("Created->Executing",),
            unauthorized_transition_findings=("Commander modified Analyst state",),
            validation_failures=("configuration integrity failed",),
            persistence_failures=("Completion not committed",),
            replay_divergence_findings=("state sequence changed",),
            recovery_violations=("Recovery->Created",),
            audit_gaps=("transition timestamp missing",),
        )
        persistent = support.evaluate_persistent_state_specification(
            missing_persistent_categories=("Belief State",),
            missing_transient_categories=("Temporary Validation Workspace",),
            dual_classification_findings=("scheduler allocation persisted",),
            implicit_persistence_findings=("cache acquired constitutional meaning",),
            atomic_commit_failures=("partial evidence commit",),
            durability_failures=("state lost after restart",),
            replay_divergence_findings=("reasoning relationship changed",),
            recovery_divergence_findings=("audit history not restored",),
            audit_gaps=("commit boundary unaudited",),
        )

        self.assertEqual(rejection.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("AR-014 Replay Rejection", rejection.missing_classes)
        self.assertIn("rejection class edited", rejection.mutation_findings)
        self.assertEqual(evidence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Evidence Identifier", evidence.missing_schema_fields)
        self.assertIn("Opinion Evidence", evidence.unapproved_class_findings)
        self.assertEqual(provenance.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Recommendations", provenance.missing_scope)
        self.assertIn("Certification Evidence", provenance.missing_chain_stages)
        self.assertEqual(state_machine.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Output Validation", state_machine.missing_states)
        self.assertIn("Created->Executing", state_machine.illegal_transition_findings)
        self.assertEqual(persistent.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Belief State", persistent.missing_persistent_categories)
        self.assertIn("Temporary Validation Workspace", persistent.missing_transient_categories)

    def test_rm003_execution_governance_package_covers_validation_commits_replay_configuration_and_errors(self) -> None:
        package = AnalystOfficeSpecificationSupport().build_execution_governance_package()

        self.assertEqual(package.final_execution_governance_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.specification_order_coverage,
            (
                "ANALYST-RM-003-016",
                "ANALYST-RM-003-017",
                "ANALYST-RM-003-018",
                "ANALYST-RM-003-019",
                "ANALYST-RM-003-020",
            ),
        )
        self.assertIn("AV-015 Certification Validation", package.validation_framework.validation_stages)
        self.assertIn("Validation Identifier", package.validation_framework.validation_record_fields)
        self.assertIn("CB-012 Recovery Completion", package.commit_boundaries.commit_boundaries)
        self.assertIn("Mission Acceptance", package.commit_boundaries.commit_ordering)
        self.assertIn("Recommendations", package.replay_semantic_equivalence.replay_scope)
        self.assertIn("Conclusion Semantics", package.replay_semantic_equivalence.semantic_criteria)
        self.assertIn("Runtime Configuration", package.configuration_object.configuration_classes)
        self.assertIn("Configuration Header", package.configuration_object.schema_sections)
        self.assertIn("Class L Certification Errors", package.error_taxonomy.error_classes)
        self.assertIn("Fatal", package.error_taxonomy.severity_levels)
        self.assertIn("Permanently Failed", package.error_taxonomy.lifecycle_effects)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm003_execution_governance_records_fail_closed_on_defects(self) -> None:
        support = AnalystOfficeSpecificationSupport()

        validation = support.evaluate_validation_framework_specification(
            missing_stages=("AV-013 Replay Validation",),
            illegal_ordering_findings=("confidence before hypotheses",),
            duplicate_record_findings=("AV-001 duplicated",),
            invalid_authority_findings=("external validator authority",),
            inconsistent_outcome_findings=("same input produced pass and fail",),
            provenance_gaps=("validation evidence missing mission",),
            replay_inconsistencies=("validation order changed",),
            recovery_gaps=("pending stage lost",),
            invariant_violations=("invalid object used after failed validation",),
        )
        commits = support.evaluate_commit_boundary_specification(
            missing_boundaries=("CB-007 Validation Completion",),
            partial_commit_findings=("evidence committed without provenance",),
            ordering_violations=("Output before Conclusion",),
            ownership_violations=("Infrastructure redefined commit",),
            precondition_failures=("schema validity not checked",),
            postcondition_failures=("audit not immutable",),
            rollback_violations=("committed state discarded",),
            replay_divergence_findings=("commit sequence changed",),
            recovery_boundary_findings=("resumed from partial commit",),
        )
        replay = support.evaluate_replay_semantic_equivalence_specification(
            missing_scope=("Organizational Belief States",),
            missing_preconditions=("complete provenance",),
            substituted_input_findings=("replacement evidence object used",),
            environment_drift_findings=("configuration version drift",),
            semantic_divergence_findings=("confidence changed",),
            validation_failures=("semantic equivalence failed"),
            persistence_gaps=("replay audit not persisted",),
            audit_gaps=("replay purpose missing",),
        )
        configuration = support.evaluate_configuration_object_specification(
            missing_identity_fields=("Integrity Identifier",),
            unapproved_class_findings=("Experimental Configuration",),
            missing_schema_sections=("Compatibility Rules",),
            activation_failures=("certification approval missing",),
            compatibility_gaps=("Replay Engine absent",),
            runtime_mutation_findings=("parameter changed during execution",),
            replay_substitution_findings=("alternate config used in replay",),
            recovery_substitution_findings=("upgraded config during recovery",),
            audit_gaps=("supersession unaudited",),
        )
        errors = support.evaluate_error_taxonomy_specification(
            missing_error_classes=("Class K Traceability Errors",),
            invalid_severity_findings=("Mutable severity",),
            invalid_recovery_findings=("implementation decided recovery",),
            unclassified_failure_findings=("dependency failure unclassified",),
            mutation_findings=("error record edited",),
            retry_violations=("committed work retried",),
            replay_divergence_findings=("error suppressed during replay",),
            recovery_history_violations=("historical severity downgraded",),
            audit_gaps=("failure cause omitted",),
        )

        self.assertEqual(validation.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("AV-013 Replay Validation", validation.missing_stages)
        self.assertIn("external validator authority", validation.invalid_authority_findings)
        self.assertEqual(commits.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("CB-007 Validation Completion", commits.missing_boundaries)
        self.assertIn("evidence committed without provenance", commits.partial_commit_findings)
        self.assertEqual(replay.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Organizational Belief States", replay.missing_scope)
        self.assertIn("replacement evidence object used", replay.substituted_input_findings)
        self.assertEqual(configuration.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Integrity Identifier", configuration.missing_identity_fields)
        self.assertIn("Compatibility Rules", configuration.missing_schema_sections)
        self.assertEqual(errors.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Class K Traceability Errors", errors.missing_error_classes)
        self.assertIn("error record edited", errors.mutation_findings)

    def test_rm003_certification_closure_package_covers_traceability_confidence_hypotheses_consensus_and_suite(self) -> None:
        package = AnalystOfficeSpecificationSupport().build_certification_closure_package()

        self.assertEqual(package.final_certification_closure_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.specification_order_coverage,
            (
                "ANALYST-RM-003-021",
                "ANALYST-RM-003-022",
                "ANALYST-RM-003-023",
                "ANALYST-RM-003-024",
                "ANALYST-RM-003-025",
            ),
        )
        self.assertIn("CT-010 Audits", package.traceability_architecture.relationship_types)
        self.assertIn("Audit Archive", package.traceability_architecture.traceability_chain)
        self.assertIn("High Confidence", package.confidence_probability.confidence_classifications)
        self.assertIn("Uncertainty Representation", package.confidence_probability.schema_sections["Confidence Representation"])
        self.assertIn("Competing Hypothesis", package.competing_hypotheses.hypothesis_classes)
        self.assertIn("contradiction analysis", package.competing_hypotheses.evaluation_sequence)
        self.assertIn("Policy Contradiction", package.consensus_contradiction.contradiction_classes)
        self.assertIn("Certification Blocking", package.consensus_contradiction.resolution_states)
        self.assertIn("Layer E Office Certification", package.independent_certification_suite.architecture_layers)
        self.assertIn("100% Work Order coverage", package.independent_certification_suite.coverage_requirements)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm003_certification_closure_records_fail_closed_on_defects(self) -> None:
        support = AnalystOfficeSpecificationSupport()

        traceability = support.evaluate_constitutional_traceability_specification(
            missing_relationships=("CT-007 Replays",),
            orphaned_artifact_findings=("runtime object lacks mission lineage",),
            duplicate_relationship_findings=("duplicate CT-003 edge",),
            illegal_relationship_findings=("audit governs doctrine",),
            version_chain_findings=("configuration version omitted",),
            replay_inconsistencies=("trace graph regenerated differently",),
            recovery_gaps=("relationship graph not restored",),
            audit_gaps=("relationship event unaudited",),
        )
        confidence = support.evaluate_confidence_probability_specification(
            missing_schema_fields=("Uncertainty Representation",),
            invalid_classification_findings=("Very Sure",),
            hidden_uncertainty_findings=("model limitation omitted",),
            unsupported_confidence_findings=("confidence lacks evidence",),
            orphaned_relationship_findings=("conclusion reference absent",),
            replay_divergence_findings=("confidence class changed",),
            recovery_recalculation_findings=("accepted confidence recalculated",),
            audit_gaps=("publication unaudited",),
        )
        hypotheses = support.evaluate_competing_hypothesis_specification(
            missing_classes=("Contradictory Hypothesis",),
            missing_identity_fields=("Integrity Metadata",),
            admissibility_failures=("supporting evidence unverified",),
            discarded_hypothesis_findings=("lower ranked hypothesis removed",),
            contradiction_preservation_findings=("contradiction omitted",),
            ranking_nondeterminism_findings=("runtime timing affected rank",),
            replay_divergence_findings=("hypothesis inventory changed",),
            recovery_gaps=("relationship graph lost",),
            audit_gaps=("confidence change unaudited",),
        )
        consensus = support.evaluate_consensus_contradiction_specification(
            missing_contradiction_classes=("Policy Contradiction",),
            invalid_severity_findings=("Catastrophic",),
            invalid_resolution_findings=("Silently Ignored",),
            suppressed_contradiction_findings=("conflicting evidence hidden",),
            undocumented_reconciliation_findings=("heuristic reconciliation used",),
            validation_failures=("consensus accepted before validation"),
            replay_divergence_findings=("resolution state changed",),
            recovery_duplication_findings=("contradiction evaluated twice",),
            audit_gaps=("reconciliation action missing",),
        )
        certification = support.evaluate_independent_certification_suite_specification(
            missing_categories=("Traceability Certification",),
            missing_coverage=("100% recovery coverage",),
            nondeterministic_execution_findings=("test order changed outcome",),
            suppressed_failure_findings=("failed invariant hidden",),
            missing_evidence_findings=("coverage report absent",),
            replay_divergence_findings=("cert replay changed result",),
            recovery_gaps=("completed test result not restored",),
            audit_gaps=("failure classification omitted",),
        )

        self.assertEqual(traceability.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("CT-007 Replays", traceability.missing_relationships)
        self.assertIn("runtime object lacks mission lineage", traceability.orphaned_artifact_findings)
        self.assertEqual(confidence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Uncertainty Representation", confidence.missing_schema_fields)
        self.assertIn("confidence lacks evidence", confidence.unsupported_confidence_findings)
        self.assertEqual(hypotheses.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Contradictory Hypothesis", hypotheses.missing_classes)
        self.assertIn("lower ranked hypothesis removed", hypotheses.discarded_hypothesis_findings)
        self.assertEqual(consensus.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Policy Contradiction", consensus.missing_contradiction_classes)
        self.assertIn("Catastrophic", consensus.invalid_severity_findings)
        self.assertEqual(certification.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Traceability Certification", certification.missing_categories)
        self.assertIn("100% recovery coverage", certification.missing_coverage)


if __name__ == "__main__":
    unittest.main()
