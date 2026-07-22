from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskOfficeSpecificationSupport  # noqa: E402


class RiskRm003SpecificationProgramTests(unittest.TestCase):
    def test_rm003_program_manifest_covers_all_required_specification_work_orders(self) -> None:
        record = RiskOfficeSpecificationSupport().build_specification_program_record()

        self.assertEqual(record.result, EnterpriseCertificationDecision.PASS)
        self.assertEqual(record.program_identifier, "RISK-RM-003")
        self.assertEqual(len(record.work_orders), 25)
        self.assertEqual(record.work_orders[0].work_order_identifier, "RISK-RM-003-001")
        self.assertEqual(record.work_orders[-1].work_order_identifier, "RISK-RM-003-025")
        self.assertIn("Risk Fusion Doctrine", {order.title for order in record.work_orders})
        self.assertIn("ownership", record.complete_specification_fields)
        self.assertIn("auditability", record.complete_specification_fields)
        self.assertIn("complete independent certification test suite", record.deliverables)
        self.assertIn("every Constitutional Specification Work Order complete", record.completion_criteria)
        self.assertIn("Bridge Certification", record.excluded_certification_domains)
        self.assertNotEqual(record.deterministic_digest, "")

    def test_rm003_program_manifest_fails_closed_on_missing_scope_or_evidence(self) -> None:
        record = RiskOfficeSpecificationSupport().build_specification_program_record(
            missing_work_order_findings=("RISK-RM-003-017 absent",),
            ownership_boundary_findings=("Bridge behavior redefined",),
            guarantee_regression_findings=("RM002 validation weakened",),
            interpretation_findings=("implementation chooses freshness rule",),
            deliverable_gaps=("certification test suite absent",),
            evidence_gaps=("traceability evidence missing",),
        )

        self.assertEqual(record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("RISK-RM-003-017 absent", record.missing_work_order_findings)
        self.assertIn("Bridge behavior redefined", record.ownership_boundary_findings)
        self.assertIn("implementation chooses freshness rule", record.interpretation_findings)
        self.assertIn("traceability evidence missing", record.evidence_gaps)

    def test_rm003_object_foundation_package_covers_first_five_specifications(self) -> None:
        package = RiskOfficeSpecificationSupport().build_object_foundation_specification_package()

        self.assertEqual(package.final_specification_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-003-001",
                "RISK-RM-003-002",
                "RISK-RM-003-003",
                "RISK-RM-003-004",
                "RISK-RM-003-005",
            ),
        )
        self.assertIn("Risk Assessment Identifier", package.risk_assessment_object.identity_attributes)
        self.assertIn("Risk Results", package.risk_assessment_object.schema_sections)
        self.assertEqual(package.risk_assessment_object.lifecycle_states[0], "Created")
        self.assertEqual(package.evaluation_plan.execution_sequence[0], "Mission Authorization")
        self.assertEqual(package.evaluation_plan.execution_sequence[-1], "Completion Verification")
        self.assertIn("Evaluation Dependency Graph", package.evaluation_plan.plan_sections)
        self.assertIn("Workflow Execution Token", package.evaluation_package.identity_attributes)
        self.assertEqual(package.evaluation_package.lifecycle_states, ("Created", "Normalized", "Validated", "Accepted", "Evaluation Active", "Evaluation Complete", "Archived"))
        self.assertIn("Risk Assessment Node", package.evaluation_graph.node_classes)
        self.assertIn("produces", package.evaluation_graph.edge_relationships)
        self.assertIn("cycles prohibited", package.evaluation_graph.invariants)
        self.assertIn("CREATION_REQUESTED", package.object_lifecycle.universal_states)
        self.assertIn("TERMINATED", package.object_lifecycle.terminal_states)
        self.assertIn("Risk Certification Evidence Object", package.object_lifecycle.covered_objects)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm003_object_foundation_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeSpecificationSupport()

        assessment = support.evaluate_risk_assessment_object_specification(
            schema_findings=("mandatory Confidence section omitted",),
            relationship_findings=("Risk Decision relationship implicit",),
            invariant_violations=("published assessment mutable",),
        )
        plan = support.evaluate_evaluation_plan_specification(
            sequence_findings=("dynamic evaluation ordering allowed",),
            completion_findings=("partial completion accepted",),
            audit_gaps=("dependency graph hash absent",),
        )
        package_record = support.evaluate_evaluation_package_specification(
            admissibility_findings=("package accepted with missing dependency",),
            validation_findings=("integrity validation skipped",),
            replay_recovery_findings=("replay inferred missing package data",),
        )
        graph = support.evaluate_evaluation_graph_specification(
            node_findings=("unsupported node class registered",),
            cycle_findings=("cycle detection absent",),
            provenance_gaps=("orphan node admitted",),
        )
        lifecycle = support.evaluate_object_lifecycle_specification(
            state_findings=("object occupied two authoritative states",),
            creation_findings=("unregistered trigger created object",),
            invariant_violations=("history overwritten",),
        )

        self.assertEqual(assessment.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("published assessment mutable", assessment.invariant_violations)
        self.assertEqual(plan.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("partial completion accepted", plan.completion_findings)
        self.assertEqual(package_record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("integrity validation skipped", package_record.validation_findings)
        self.assertEqual(graph.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("cycle detection absent", graph.cycle_findings)
        self.assertEqual(lifecycle.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("history overwritten", lifecycle.invariant_violations)

    def test_rm003_state_doctrine_package_covers_orders_six_through_ten(self) -> None:
        package = RiskOfficeSpecificationSupport().build_state_doctrine_specification_package()

        self.assertEqual(package.final_specification_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-003-006",
                "RISK-RM-003-007",
                "RISK-RM-003-008",
                "RISK-RM-003-009",
                "RISK-RM-003-010",
            ),
        )
        self.assertEqual(package.mission_lifecycle.lifecycle_states[0], "Authorized")
        self.assertEqual(package.mission_lifecycle.lifecycle_states[-1], "Archived")
        self.assertIn(("Validation Complete", "Authority Relinquished"), package.mission_lifecycle.legal_transitions)
        self.assertIn("Authority Relinquished", package.mission_lifecycle.lifecycle_states)
        self.assertIn("Input Sufficiency", package.sufficiency_doctrine.sufficiency_components)
        self.assertEqual(package.sufficiency_doctrine.sufficiency_states, ("SUFFICIENT", "INSUFFICIENT", "REJECTED", "TERMINATED"))
        self.assertIn("Risk Fusion", package.sufficiency_doctrine.mandatory_evaluations)
        self.assertEqual(package.equivalence_doctrine.evaluation_sequence[0], "Object Admission")
        self.assertEqual(package.equivalence_doctrine.evaluation_sequence[-1], "Consolidation Decision")
        self.assertIn("Semantically Equivalent", package.equivalence_doctrine.equivalence_classes)
        self.assertEqual(package.equivalence_doctrine.consolidation_rules["Superseding Revision"], "Preserve prior version, register new revision")
        self.assertEqual(package.freshness_doctrine.freshness_states, ("Fresh", "Aging", "Expired", "Historical", "Superseded", "Indeterminate"))
        self.assertIn("Immutable Reference", package.freshness_doctrine.freshness_categories)
        self.assertIn("freshness promotion prohibited", package.freshness_doctrine.inheritance_rules)
        self.assertIn("state-family identity", package.enterprise_risk_state.identity_fields)
        self.assertIn("Source Manifest", package.enterprise_risk_state.required_state_fields)
        self.assertIn("STATE_CURRENT", package.enterprise_risk_state.lifecycle_states)
        self.assertIn("Enterprise Risk State Current-Version Registry", package.enterprise_risk_state.required_registries)
        self.assertIn("No Averaging Away Blocking Risk", package.enterprise_risk_state.invariants)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm003_state_doctrine_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeSpecificationSupport()

        mission = support.evaluate_mission_lifecycle_specification(
            authority_findings=("mission authority delegated",),
            lifecycle_findings=("state skipped",),
            invariant_violations=("closed mission reopened",),
        )
        sufficiency = support.evaluate_sufficiency_doctrine_specification(
            component_findings=("evidence sufficiency omitted",),
            failure_classification_findings=("missing evidence unclassified",),
            traceability_gaps=("Risk Decision provenance broken",),
        )
        equivalence = support.evaluate_equivalence_doctrine_specification(
            normalization_findings=("raw objects compared directly",),
            consolidation_findings=("manual consolidation allowed",),
            provenance_gaps=("superseded revision erased",),
        )
        freshness = support.evaluate_freshness_doctrine_specification(
            state_findings=("custom stale state introduced",),
            expiration_findings=("expired evidence admitted live",),
            invariant_violations=("freshness inferred from runtime behavior",),
        )
        state = support.evaluate_enterprise_risk_state_specification(
            scope_findings=("ambiguous scope accepted",),
            atomicity_findings=("predecessor supersession non-atomic",),
            invariant_violations=("two current states for identical scope",),
        )

        self.assertEqual(mission.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("mission authority delegated", mission.authority_findings)
        self.assertEqual(sufficiency.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("missing evidence unclassified", sufficiency.failure_classification_findings)
        self.assertEqual(equivalence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("raw objects compared directly", equivalence.normalization_findings)
        self.assertEqual(freshness.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("expired evidence admitted live", freshness.expiration_findings)
        self.assertEqual(state.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("two current states for identical scope", state.invariant_violations)

    def test_rm003_execution_state_package_covers_orders_eleven_through_fifteen(self) -> None:
        package = RiskOfficeSpecificationSupport().build_execution_state_specification_package()

        self.assertEqual(package.final_specification_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-003-011",
                "RISK-RM-003-012",
                "RISK-RM-003-013",
                "RISK-RM-003-014",
                "RISK-RM-003-015",
            ),
        )
        self.assertIn("RJ-010 Invariant Rejection", package.rejection_taxonomy.rejection_classes)
        self.assertEqual(package.rejection_taxonomy.recovery_statuses, ("Recoverable", "Non-Recoverable"))
        self.assertIn("Validator Version", package.rejection_taxonomy.audit_fields)
        self.assertIn("Evidence Identifier", package.evidence_constitution.identity_fields)
        self.assertIn("Traceability References", package.evidence_constitution.schema_sections)
        self.assertIn("Configuration Evidence", package.evidence_constitution.evidence_classes)
        self.assertEqual(package.evidence_constitution.lifecycle_states, ("Created", "Normalized", "Validated", "Accepted", "Referenced", "Archived", "Retired"))
        self.assertIn("DERIVED_FROM", package.provenance_architecture.relationship_types)
        self.assertIn("Enterprise Risk State", package.provenance_architecture.graph_structure)
        self.assertIn("Final Risk Assessment", package.provenance_architecture.lineage_requirements)
        self.assertEqual(package.office_state_machine.execution_states[0], "Dormant")
        self.assertEqual(package.office_state_machine.execution_states[-1], "Completed")
        self.assertIn(("Authority Relinquishment", "Completed"), package.office_state_machine.legal_transitions)
        self.assertIn(("Any Active State", "Interrupted"), package.office_state_machine.failure_transitions)
        self.assertIn("Risk Evaluation Graphs", package.persistent_state.persistent_inventory)
        self.assertIn("temporary graph traversal state", package.persistent_state.transient_inventory)
        self.assertIn("Checkpoint Identifier", package.persistent_state.schema_fields)
        self.assertIn("software replacement", package.persistent_state.durability_requirements)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm003_execution_state_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeSpecificationSupport()

        rejection = support.evaluate_rejection_taxonomy_specification(
            class_findings=("unregistered rejection class admitted",),
            terminal_behavior_findings=("rejected object advanced",),
            invariant_violations=("rejection history mutable",),
        )
        evidence = support.evaluate_evidence_constitution_specification(
            schema_findings=("classification section omitted",),
            admissibility_findings=("evidence used before admissibility",),
            provenance_gaps=("Risk Decision unsupported by evidence",),
        )
        provenance = support.evaluate_provenance_architecture_specification(
            relationship_findings=("implementation-defined relation added",),
            graph_findings=("cycle allowed",),
            lineage_gaps=("confidence object lacks evidence lineage",),
        )
        state_machine = support.evaluate_office_state_machine_specification(
            state_findings=("custom execution state added",),
            transition_findings=("Publication bypassed Output Validation",),
            recovery_findings=("recovery inferred progress",),
        )
        persistence = support.evaluate_persistent_state_specification(
            inventory_findings=("unregistered persistent state exists",),
            commit_findings=("commit allowed before validation",),
            replay_recovery_findings=("partial state restored",),
        )

        self.assertEqual(rejection.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("unregistered rejection class admitted", rejection.class_findings)
        self.assertEqual(evidence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("evidence used before admissibility", evidence.admissibility_findings)
        self.assertEqual(provenance.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("implementation-defined relation added", provenance.relationship_findings)
        self.assertEqual(state_machine.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Publication bypassed Output Validation", state_machine.transition_findings)
        self.assertEqual(persistence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("partial state restored", persistence.replay_recovery_findings)

    def test_rm003_validation_commit_package_covers_orders_sixteen_through_twenty(self) -> None:
        package = RiskOfficeSpecificationSupport().build_validation_commit_specification_package()

        self.assertEqual(package.final_specification_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-003-016",
                "RISK-RM-003-017",
                "RISK-RM-003-018",
                "RISK-RM-003-019",
                "RISK-RM-003-020",
            ),
        )
        self.assertEqual(package.validation_framework.validation_sequence[0], "Identity Validation")
        self.assertEqual(package.validation_framework.validation_sequence[-1], "Invariant Validation")
        self.assertEqual(package.validation_framework.outcomes, ("Valid", "Invalid", "Incomplete"))
        self.assertIn("VF-010 Invariant Validation", package.validation_framework.validation_categories)
        self.assertIn("CB-012 Completion Commit", package.commit_boundaries.commit_boundaries)
        self.assertEqual(package.commit_boundaries.commit_order[0], "Mission Initialization")
        self.assertEqual(package.commit_boundaries.commit_order[-1], "Mission Completion")
        self.assertIn("Persistence Failure", package.commit_boundaries.failure_classes)
        self.assertIn("Original Workflow Execution Token", package.replay_semantic_equivalence.canonical_inputs)
        self.assertIn("Class II Semantically Equivalent Replay", package.replay_semantic_equivalence.classifications)
        self.assertIn("processor scheduling", package.replay_semantic_equivalence.acceptable_runtime_differences)
        self.assertIn("constitutional decisions", package.replay_semantic_equivalence.prohibited_differences)
        self.assertIn("Rule Registry References", package.configuration_object.schema_sections)
        self.assertIn("Audit Configuration", package.configuration_object.parameter_categories)
        self.assertIn("Digital Integrity Hash", package.configuration_object.version_fields)
        self.assertIn("Critical Constitutional Failure", package.error_taxonomy.severities)
        self.assertIn("Traceability Error", package.error_taxonomy.error_classes)
        self.assertEqual(package.error_taxonomy.lifecycle_states[0], "Detected")
        self.assertEqual(package.error_taxonomy.lifecycle_states[-1], "Archived")
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm003_validation_commit_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeSpecificationSupport()

        validation = support.evaluate_validation_framework_specification(
            category_findings=("custom validation category admitted",),
            sequence_findings=("ownership validation skipped",),
            invariant_violations=("validation modified object",),
        )
        commits = support.evaluate_commit_boundary_specification(
            boundary_findings=("state transition outside commit boundary",),
            atomicity_findings=("partial commit persisted",),
            rollback_findings=("rollback modified committed state",),
        )
        replay = support.evaluate_replay_semantic_equivalence_specification(
            input_findings=("substitute replay input admitted",),
            equivalence_findings=("confidence divergence accepted",),
            classification_findings=("custom replay classification added",),
        )
        configuration = support.evaluate_configuration_object_specification(
            schema_findings=("mandatory audit parameters omitted",),
            activation_findings=("partial activation accepted",),
            replay_recovery_findings=("newer config substituted during replay",),
        )
        errors = support.evaluate_error_taxonomy_specification(
            class_findings=("unclassified constitutional violation",),
            severity_findings=("multiple severities assigned",),
            escalation_findings=("operator discretion used",),
        )

        self.assertEqual(validation.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("ownership validation skipped", validation.sequence_findings)
        self.assertEqual(commits.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("partial commit persisted", commits.atomicity_findings)
        self.assertEqual(replay.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("confidence divergence accepted", replay.equivalence_findings)
        self.assertEqual(configuration.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("partial activation accepted", configuration.activation_findings)
        self.assertEqual(errors.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("unclassified constitutional violation", errors.class_findings)

    def test_rm003_certification_closure_package_covers_orders_twenty_one_through_twenty_five(self) -> None:
        package = RiskOfficeSpecificationSupport().build_certification_closure_specification_package()

        self.assertEqual(package.final_specification_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-003-021",
                "RISK-RM-003-022",
                "RISK-RM-003-023",
                "RISK-RM-003-024",
                "RISK-RM-003-025",
            ),
        )
        self.assertEqual(len(package.complete_rm003_order_coverage), 25)
        self.assertEqual(package.complete_rm003_order_coverage[0], "RISK-RM-003-001")
        self.assertEqual(package.complete_rm003_order_coverage[-1], "RISK-RM-003-025")
        self.assertIn("Certification", package.traceability_architecture.schema_sections)
        self.assertIn("cycles prohibited", package.traceability_architecture.graph_requirements)
        self.assertIn("CE-005 Exposure Aggregation Record", package.confidence_exposure.canonical_objects)
        self.assertIn("Enterprise Aggregate Exposure", package.confidence_exposure.exposure_categories)
        self.assertIn("Indeterminate", package.confidence_exposure.confidence_categories)
        self.assertEqual(package.mitigation_constitution.readiness_classifications, ("READY", "READY WITH DEPENDENCIES", "DEFERRED", "NOT RECOMMENDED"))
        self.assertEqual(package.mitigation_constitution.evaluation_sequence[0], "Risk Assessment Complete")
        self.assertEqual(package.mitigation_constitution.evaluation_sequence[-1], "Mitigation Plan Finalized")
        self.assertIn("Risk Fusion", package.certification_suite.certification_domains)
        self.assertIn("Conflict Resolution", package.fusion_doctrine.fusion_sequence)
        self.assertIn("Enterprise Risk Assessment", package.fusion_doctrine.persistence_requirements)
        self.assertIn("Invariant Test", package.certification_suite.certification_categories)
        self.assertEqual(package.certification_suite.execution_order[0], "Environment Verification")
        self.assertEqual(package.certification_suite.execution_order[-1], "Certification Summary")
        self.assertIn("every mandatory certification test passes", package.certification_suite.pass_decision_requirements)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm003_certification_closure_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeSpecificationSupport()

        traceability = support.evaluate_traceability_architecture_specification(
            relationship_findings=("implicit dependency admitted",),
            graph_findings=("cycle allowed",),
            invariant_violations=("certification artifact lacks doctrine link",),
        )
        confidence_exposure = support.evaluate_confidence_exposure_constitution_specification(
            category_findings=("custom exposure category added",),
            uncertainty_findings=("implicit uncertainty accepted",),
            propagation_aggregation_findings=("confidence propagation nondeterministic",),
        )
        mitigation = support.evaluate_mitigation_constitution_specification(
            strategy_findings=("implementation-defined strategy category",),
            readiness_findings=("custom readiness state added",),
            preservation_findings=("alternative strategy discarded",),
        )
        fusion = support.evaluate_fusion_doctrine_specification(
            input_findings=("incomplete Risk object fused",),
            conflict_findings=("manual conflict resolution allowed",),
            invariant_violations=("fusion modified source evidence",),
        )
        certification = support.evaluate_independent_certification_suite_specification(
            coverage_findings=("constitutional requirement lacks test",),
            evidence_findings=("certification result lacks evidence",),
            replay_recovery_findings=("certification replay diverged",),
        )

        self.assertEqual(traceability.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("implicit dependency admitted", traceability.relationship_findings)
        self.assertEqual(confidence_exposure.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("implicit uncertainty accepted", confidence_exposure.uncertainty_findings)
        self.assertEqual(mitigation.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("custom readiness state added", mitigation.readiness_findings)
        self.assertEqual(fusion.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("manual conflict resolution allowed", fusion.conflict_findings)
        self.assertEqual(certification.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("constitutional requirement lacks test", certification.coverage_findings)


if __name__ == "__main__":
    unittest.main()
