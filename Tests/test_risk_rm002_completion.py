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


if __name__ == "__main__":
    unittest.main()
