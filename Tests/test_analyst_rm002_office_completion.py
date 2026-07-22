from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import AnalystOfficeCompletionSupport  # noqa: E402
from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402


class AnalystRm002OfficeCompletionTests(unittest.TestCase):
    def test_rm002_package_covers_objects_inputs_outputs_lifecycle_and_reasoning(self) -> None:
        package = AnalystOfficeCompletionSupport().build_package()

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.remediation_order_coverage,
            (
                "ANALYST-RM-002-001",
                "ANALYST-RM-002-002",
                "ANALYST-RM-002-003",
                "ANALYST-RM-002-004",
                "ANALYST-RM-002-005",
            ),
        )
        self.assertEqual(len(package.canonical_objects.canonical_objects), 12)
        self.assertIn("AO-004 Analytical Reasoning Graph", package.canonical_objects.immutable_relationship_chain)
        self.assertIn("Certification Metadata", package.canonical_objects.required_attributes)
        self.assertIn("Candidate Package", package.analytical_inputs.input_classes)
        self.assertIn("freshness status", package.analytical_inputs.contract_fields)
        self.assertIn("Decision Recommendation", package.analytical_outputs.output_classes)
        self.assertIn("exactly-once constitutional publication", package.analytical_outputs.publication_requirements)
        self.assertIn("Restored", package.analytical_lifecycle.lifecycle_states)
        self.assertEqual(package.analytical_lifecycle.illegal_transitions, ())
        self.assertEqual(package.reasoning_architecture.reasoning_stages[-1], "Reasoning Validation")
        self.assertIn("contradiction registry", package.reasoning_architecture.persistent_reasoning_state)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm002_records_fail_closed_on_completion_defects(self) -> None:
        support = AnalystOfficeCompletionSupport()

        objects = support.evaluate_canonical_object_completion(
            undefined_objects=("Analytical Scenario",),
            missing_attributes=("Certification Metadata",),
            ambiguous_ownership=("AO-007 Confidence Assessment"),
            relationship_violations=("AO-004 bypassed"),
            invariant_violations=("provenance missing"),
            replay_supported=False,
            recovery_supported=False,
        )
        inputs = support.evaluate_input_completion(
            unauthorized_inputs=("Direct Operator Note",),
            missing_contract_fields=("freshness status",),
            ownership_transfer_violations=("shared ownership during transfer"),
            normalization_failures=("semantic mutation"),
            validation_failures=("missing provenance"),
            circular_dependencies=("Replay Inputs->Recovery Inputs->Replay Inputs"),
        )
        outputs = support.evaluate_output_completion(
            unauthorized_outputs=("Trade Instruction"),
            missing_identity_fields=("integrity metadata",),
            unmet_completion_requirements=("reasoning completion",),
            validation_failures=("confidence invalid"),
            duplicate_publication_findings=("AN-OUT-1 twice"),
            replay_divergence_findings=("conclusion changed"),
            recovery_integrity_findings=("duplicate ownership transfer"),
        )
        lifecycle = support.evaluate_lifecycle_completion(
            observed_transition_sequence=("Created", "Active", "Terminal"),
            revision_violations=("revision overwrote original"),
            archival_violations=("archived object mutable"),
            replay_lifecycle_violations=("state sequence changed"),
            recovery_lifecycle_violations=("transition repeated"),
        )
        reasoning = support.evaluate_reasoning_architecture_completion(
            observed_stages=("Evidence Acquisition", "Reasoning Validation"),
            undocumented_assumptions=("market regime inferred"),
            hidden_inferences=("confidence shortcut"),
            circular_dependencies=("Inference A->Inference B->Inference A"),
            contradiction_suppression_findings=("contradictory evidence removed"),
            replay_reasoning_violations=("finding changed"),
            recovery_reasoning_violations=("dependency graph rebuilt differently"),
            fail_closed_on_incomplete_reasoning=False,
        )

        self.assertEqual(objects.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Certification Metadata", objects.missing_attributes)
        self.assertFalse(objects.replay_supported)
        self.assertEqual(inputs.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("freshness status", inputs.missing_contract_fields)
        self.assertIn("Direct Operator Note", inputs.unauthorized_inputs)
        self.assertEqual(outputs.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("reasoning completion", outputs.unmet_completion_requirements)
        self.assertIn("conclusion changed", outputs.replay_divergence_findings)
        self.assertEqual(lifecycle.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Created->Active", lifecycle.illegal_transitions)
        self.assertIn("Under Validation", lifecycle.missing_states)
        self.assertEqual(reasoning.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Evidence Classification", reasoning.missing_stages)
        self.assertFalse(reasoning.fail_closed_on_incomplete_reasoning)


if __name__ == "__main__":
    unittest.main()
