import json
from pathlib import Path
import unittest

from Scripts.closed_position_truth_rm002_b07_004_mutation_accuracy import OUTPUT_DIR, generate_mutation_accuracy


class ClosedPositionTruthRm002B07004MutationAccuracyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completion = generate_mutation_accuracy()

    def _read(self, name):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_mutation_deliverables_exist(self):
        required = [
            "mutation_plan.json",
            "mutation_registry.json",
            "requirement_to_mutation_registry.json",
            "constitutional_coverage_matrix.json",
            "mutation_classification_registry.json",
            "mutation_justification_registry.json",
            "mutation_candidate_registry.json",
            "mutation_application_registry.json",
            "mutation_diff_registry.json",
            "mutation_execution_registry.json",
            "mutation_attempt_registry.json",
            "mutation_evidence_registry.json",
            "mutation_regenerated_evidence_registry.json",
            "mutation_regenerated_proof_registry.json",
            "mutation_regenerated_traceability_registry.json",
            "mutation_blocker_findings_registry.json",
            "mutation_certification_outcome_registry.json",
            "fail_closed_validation_registry.json",
            "blocker_generation_registry.json",
            "accuracy_registry.json",
            "false_positive_registry.json",
            "false_negative_registry.json",
            "true_positive_registry.json",
            "true_negative_registry.json",
            "accuracy_assessment_report.json",
            "completion_report.json",
            "manifest.json",
        ]
        for name in required:
            self.assertTrue((OUTPUT_DIR / name).is_file(), name)

    def test_every_mutation_executed_and_fail_closed(self):
        mutations = self._read("mutation_registry.json")
        executions = self._read("mutation_execution_registry.json")
        fail_closed = self._read("fail_closed_validation_registry.json")
        blockers = self._read("blocker_generation_registry.json")

        self.assertEqual(len(mutations), len(executions))
        self.assertEqual(len(mutations), len(fail_closed))
        self.assertEqual(len(mutations), len(blockers))
        self.assertGreater(len(mutations), 0)
        for row in executions:
            self.assertEqual(row["execution_outcome"], "EXECUTION_COMPLETED")
        for row in fail_closed:
            self.assertEqual(row["fail_closed_disposition"], "FAIL_CLOSED_CONFIRMED")
            self.assertEqual(row["certification_outcome"], "REJECTED")
            self.assertTrue(row["blocker_identities"])

    def test_accuracy_metrics_have_no_false_positive_or_false_negative(self):
        report = self._read("accuracy_assessment_report.json")
        false_positive = self._read("false_positive_registry.json")
        false_negative = self._read("false_negative_registry.json")
        true_positive = self._read("true_positive_registry.json")
        accuracy = self._read("accuracy_registry.json")

        self.assertEqual(report["false_positive_count"], 0)
        self.assertEqual(report["false_negative_count"], 0)
        self.assertEqual(false_positive, [])
        self.assertEqual(false_negative, [])
        self.assertEqual(len(true_positive), report["total_mutations_executed"])
        self.assertEqual(len(accuracy), report["total_mutations_executed"])
        self.assertEqual(report["blocker_precision"], 1.0)
        self.assertEqual(report["blocker_recall"], 1.0)

    def test_mutation_evidence_files_exist_and_are_hashed(self):
        evidence = self._read("mutation_evidence_registry.json")
        self.assertGreater(len(evidence), 0)
        for row in evidence:
            path = OUTPUT_DIR.parents[1] / row["storage_location"]
            self.assertTrue(path.is_file(), path)
            self.assertRegex(row["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(row["integrity_status"], "VALID")

    def test_completion_is_non_certifying_and_non_remediating(self):
        completion = self._read("completion_report.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["implementation_remediation_occurred"])
        self.assertFalse(completion["certification_verdict_issued"])
        self.assertTrue(all(completion["completion_criteria"].values()))


if __name__ == "__main__":
    unittest.main()
