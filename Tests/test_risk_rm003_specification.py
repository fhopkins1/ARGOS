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


if __name__ == "__main__":
    unittest.main()
