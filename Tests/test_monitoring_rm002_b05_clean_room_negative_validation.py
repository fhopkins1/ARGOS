import json
import unittest

from Scripts import monitoring_rm002_b05_clean_room_negative_validation as b05


class MonitoringRM002B05CleanRoomNegativeValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completion = b05.generate()
        cls.output_dir = b05.OUTPUT_DIR

    def _load(self, name):
        return json.loads((self.output_dir / name).read_text(encoding="utf-8"))

    def test_clean_room_excludes_prior_state_and_git_history(self):
        identity = self._load("clean_room_baseline_identity_registry.json")
        isolation = self._load("prior_generated_artifact_isolation_report.json")

        self.assertFalse(identity["git_history_present"])
        self.assertFalse(identity["prior_generated_monitoring_certification_state_present"])
        self.assertEqual(isolation["status"], "PASS")
        self.assertFalse(isolation["prior_generated_state_present"])
        self.assertTrue(isolation["submitted_artifacts_comparison_only"])

    def test_baseline_reproduction_passes_from_current_execution(self):
        report = self._load("independent_reproduction_report.json")
        executions = self._load("complete_behavioral_execution_registry.json")
        proof = self._load("independent_proof_baseline.json")

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["baseline_verdict"], "UNCONDITIONAL_PASS")
        self.assertFalse(report["prior_artifacts_reused"])
        self.assertTrue(all(item["terminal_disposition"] == "PASS" for item in executions))
        self.assertTrue(all(item["derived_from_current_execution"] for item in proof))

    def test_negative_mutations_fail_closed(self):
        plan = self._load("negative_mutation_plan.json")
        registry = self._load("negative_mutation_registry.json")
        fail_closed = self._load("fail_closed_validation_registry.json")
        report = self._load("negative_certification_validation_report.json")

        self.assertEqual(len(plan), len(b05.NEGATIVE_MUTATIONS))
        self.assertEqual(len(registry), len(b05.NEGATIVE_MUTATIONS))
        self.assertTrue(all(item["status"] == "PASS" for item in fail_closed))
        self.assertTrue(all(item["unconditional_pass_denied"] for item in fail_closed))
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["fail_closed"])

    def test_false_positive_controls_and_certification_system_are_clean(self):
        controls = self._load("false_positive_control_registry.json")
        defects = self._load("certification_system_defect_registry.json")
        remediation = self._load("minimum_bounded_remediation_registry.json")

        self.assertTrue(all(item["baseline_restored"] for item in controls))
        self.assertEqual(defects, [])
        self.assertEqual(remediation, [])

    def test_final_verdict_and_confidence_are_authorized(self):
        verdict = self._load("independent_ecs003_verdict.json")
        confidence = self._load("confidence_determination.json")
        completion = self._load("completion_report.json")
        baseline = self._load("monitoring_rm002_b05_clean_room_negative_validation_baseline.json")

        self.assertEqual(verdict["verdict"], "UNCONDITIONAL_PASS")
        self.assertTrue(verdict["defective_candidates_denied_unconditional_pass"])
        self.assertEqual(confidence["confidence"], "VERY_HIGH_CONFIDENCE")
        self.assertEqual(completion["independent_verdict"], "UNCONDITIONAL_PASS")
        self.assertEqual(completion["confidence"], "VERY_HIGH_CONFIDENCE")
        self.assertEqual(baseline["confidence"], "VERY_HIGH_CONFIDENCE")


if __name__ == "__main__":
    unittest.main()
