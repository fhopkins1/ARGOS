from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskOfficeCompletionSupport  # noqa: E402


class RiskRm002CompletionTests(unittest.TestCase):
    def test_rm002_completion_package_covers_objects_inputs_outputs_lifecycle_and_evaluation(self) -> None:
        package = RiskOfficeCompletionSupport().build_completion_package()

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-002-001",
                "RISK-RM-002-002",
                "RISK-RM-002-003",
                "RISK-RM-002-004",
                "RISK-RM-002-005",
            ),
        )
        self.assertEqual(len(package.object_completion.canonical_objects), 15)
        self.assertEqual(package.object_completion.canonical_objects["RO-012"], "Risk Decision")
        self.assertIn("Object Identifier", package.object_completion.identity_attributes)
        self.assertEqual(len(package.input_completion.canonical_inputs), 10)
        self.assertEqual(package.input_completion.canonical_inputs["RI-004"][1], "Sentinel Office")
        self.assertIn("freshness validation", package.input_completion.validation_requirements)
        self.assertEqual(len(package.output_completion.authorized_outputs), 10)
        self.assertIn("Risk Decision Record", package.output_completion.authorized_outputs)
        self.assertEqual(package.output_completion.state_machine, ("Created", "Validated", "Completed", "Persisted", "Released", "Superseded", "Archived"))
        self.assertIn("Under Evaluation", package.lifecycle_completion.canonical_lifecycle)
        self.assertIn("Invalidated", package.lifecycle_completion.terminal_states)
        self.assertIn("Risk Fusion Evaluation", package.evaluation_architecture.required_evaluation_classes)
        self.assertIn("Tail Scenario Registry", package.evaluation_architecture.required_registries)
        self.assertIn("Deterministic Execution", package.evaluation_architecture.expected_pass_domains)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm002_completion_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeCompletionSupport()

        objects = support.evaluate_canonical_objects(
            inventory_findings=("RO-016 implementation-defined object",),
            ownership_findings=("Risk Evidence Package co-owned",),
            invariant_violations=("object bypassed lifecycle rules",),
        )
        inputs = support.evaluate_inputs(
            input_findings=("implicit input admitted",),
            freshness_findings=("stale input accepted",),
            provenance_gaps=("originating workflow absent",),
        )
        outputs = support.evaluate_outputs(
            output_findings=("unsupported output released",),
            completion_findings=("incomplete output released",),
            traceability_gaps=("final decision missing provenance",),
        )
        lifecycle = support.evaluate_lifecycle(
            transition_findings=("backward transition allowed",),
            supersession_findings=("two active versions",),
            replay_recovery_findings=("replay changed terminal state",),
        )
        evaluation = support.evaluate_evaluation_architecture(
            scope_findings=("evaluation scope mutable after start",),
            domain_findings=("required liquidity domain skipped",),
            sufficiency_findings=("missing mandatory component passed",),
            invariant_violations=("hidden evaluation affected conclusion",),
        )

        self.assertEqual(objects.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Risk Evidence Package co-owned", objects.ownership_findings)
        self.assertEqual(inputs.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("stale input accepted", inputs.freshness_findings)
        self.assertEqual(outputs.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("incomplete output released", outputs.completion_findings)
        self.assertEqual(lifecycle.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("two active versions", lifecycle.supersession_findings)
        self.assertEqual(evaluation.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("hidden evaluation affected conclusion", evaluation.invariant_violations)

    def test_rm002_decision_validation_package_covers_confidence_mitigation_decisions_and_validation(self) -> None:
        package = RiskOfficeCompletionSupport().build_decision_validation_package()

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-002-006",
                "RISK-RM-002-007",
                "RISK-RM-002-008",
                "RISK-RM-002-009",
            ),
        )
        self.assertIn("unresolved uncertainty", package.confidence_exposure.confidence_factors)
        self.assertIn("systemic exposure", package.confidence_exposure.exposure_factors)
        self.assertIn("one Confidence Assessment per Risk Assessment", package.confidence_exposure.invariants)
        self.assertEqual(len(package.mitigation_recovery.planning_objects), 7)
        self.assertEqual(package.mitigation_recovery.planning_objects["RM-005"], "Escalation Recommendation")
        self.assertIn("CI-003", package.mitigation_recovery.invariants)
        self.assertIn("residual risk exceeds tolerance", package.mitigation_recovery.escalation_triggers)
        self.assertEqual(len(package.deterministic_decisions.decision_inventory), 12)
        self.assertEqual(package.deterministic_decisions.decision_inventory["Final Risk Decision"], ("ACCEPTABLE", "ACCEPTABLE WITH MITIGATION", "UNACCEPTABLE"))
        self.assertEqual(package.deterministic_decisions.evaluation_sequence[0], "Input Admission")
        self.assertEqual(package.deterministic_decisions.evaluation_sequence[-1], "Final Risk Decision")
        self.assertEqual(len(package.validation_completion.validation_pipeline), 17)
        self.assertEqual(package.validation_completion.validation_pipeline[0], "Identity Validation")
        self.assertEqual(package.validation_completion.validation_pipeline[-1], "Validation Completion")
        self.assertIn("Traceability Validation", package.validation_completion.validation_pipeline)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm002_decision_validation_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeCompletionSupport()

        confidence = support.evaluate_confidence_exposure(
            confidence_findings=("confidence adjusted by implementation preference",),
            uncertainty_findings=("unknown uncertainty hidden",),
            inheritance_findings=("implicit exposure inheritance",),
        )
        mitigation = support.evaluate_mitigation_recovery(
            planning_findings=("actionable risk lacks mitigation",),
            alternative_findings=("admissible alternative discarded",),
            escalation_findings=("limit breach did not escalate",),
        )
        decisions = support.evaluate_decisions(
            precondition_findings=("decision executed before validation",),
            sequence_findings=("Final Risk Decision issued before Recovery Requirement",),
            traceability_gaps=("decision lacks originating input provenance",),
        )
        validation = support.evaluate_validation_completion(
            sequence_findings=("validation order varied",),
            failure_findings=("schema failure allowed evaluation",),
            audit_gaps=("validation failure unaudited",),
        )

        self.assertEqual(confidence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("unknown uncertainty hidden", confidence.uncertainty_findings)
        self.assertEqual(mitigation.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("admissible alternative discarded", mitigation.alternative_findings)
        self.assertEqual(decisions.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Final Risk Decision issued before Recovery Requirement", decisions.sequence_findings)
        self.assertEqual(validation.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("schema failure allowed evaluation", validation.failure_findings)

    def test_rm002_replay_recovery_review_package_covers_final_completion_tranche(self) -> None:
        package = RiskOfficeCompletionSupport().build_replay_recovery_review_package()

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(package.independent_review_result, "CONSTITUTIONALLY_COMPLETE_FOR_RISK_RM_003")
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-002-011",
                "RISK-RM-002-012",
                "RISK-RM-002-013",
                "RISK-RM-002-014",
                "RISK-RM-002-015",
            ),
        )
        self.assertIn("Risk Decisions", package.replay_completion.replay_scope)
        self.assertIn("constitutional decisions", package.replay_completion.semantic_equivalence_requirements)
        self.assertEqual(package.replay_completion.acceptable_differences, ("replay execution timestamp", "replay session identifier", "replay operator identifier", "replay infrastructure identifier"))
        self.assertEqual(len(package.recovery_completion.recovery_objects), 6)
        self.assertIn("Recovery Certification", package.recovery_completion.recovery_sequence)
        self.assertIn("Evaluation Configuration", package.configuration_completion.configuration_objects)
        self.assertEqual(package.configuration_completion.state_machine, ("Draft", "Validated", "Approved", "Persisted", "Active", "Superseded", "Archived"))
        self.assertEqual(package.traceability_completion.provenance_graph[0], "Input Evidence")
        self.assertEqual(package.traceability_completion.provenance_graph[-1], "Historical Archive")
        self.assertEqual(len(package.independent_completion_review.mandatory_work_orders), 15)
        self.assertIn("RISK-RM-002-010", package.independent_completion_review.mandatory_work_orders)
        self.assertIn("CONSTITUTIONALLY_COMPLETE_FOR_RISK_RM_003", package.independent_completion_review.review_states)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm002_replay_recovery_review_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeCompletionSupport()

        replay = support.evaluate_replay_completion(
            precondition_findings=("transient artifact consumed",),
            equivalence_findings=("decision equivalence failed",),
            evidence_gaps=("replay completion status missing",),
        )
        recovery = support.evaluate_recovery_completion(
            checkpoint_findings=("invalid checkpoint admitted",),
            idempotency_findings=("duplicate decision generated",),
            provenance_gaps=("originating checkpoint absent",),
        )
        configuration = support.evaluate_configuration_completion(
            ownership_findings=("shared configuration owner",),
            activation_findings=("partial activation accepted",),
            replay_recovery_findings=("replay substituted configuration",),
        )
        traceability = support.evaluate_traceability_completion(
            graph_findings=("Decision provenance omitted",),
            relationship_findings=("relationship identifier missing",),
            audit_gaps=("certification provenance unauditable",),
        )
        review = support.evaluate_independent_completion_review(
            missing_work_order_findings=("RISK-RM-002-010 absent",),
            discretion_findings=("reasonable implementation fallback remains",),
            evidence_gaps=("completion package missing",),
        )

        self.assertEqual(replay.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("decision equivalence failed", replay.equivalence_findings)
        self.assertEqual(recovery.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("duplicate decision generated", recovery.idempotency_findings)
        self.assertEqual(configuration.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("partial activation accepted", configuration.activation_findings)
        self.assertEqual(traceability.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("relationship identifier missing", traceability.relationship_findings)
        self.assertEqual(review.result, "NOT_CONSTITUTIONALLY_COMPLETE_FOR_RISK_RM_003")
        self.assertIn("RISK-RM-002-010 absent", review.missing_work_order_findings)


if __name__ == "__main__":
    unittest.main()
