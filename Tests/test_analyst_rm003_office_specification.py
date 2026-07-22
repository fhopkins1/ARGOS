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


if __name__ == "__main__":
    unittest.main()
