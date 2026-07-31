from __future__ import annotations

import json
import unittest

from Scripts.performance_truth_ecs003_audit_004 import OUTPUT_DIR, generate_audit


class PerformanceTruthEcs003Audit004Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = generate_audit()

    def _read(self, name):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_audit_004_deliverables_exist(self):
        required = [
            "independent_audit_environment_record.json",
            "candidate_integrity_report.json",
            "entrypoint_verification_report.json",
            "run_a_complete_execution_package.json",
            "run_b_complete_execution_package.json",
            "deterministic_equivalence_report.json",
            "runtime_behavioral_verification_report.json",
            "replay_verification_report.json",
            "fail_closed_verification_report.json",
            "mutation_verification_report.json",
            "stress_verification_report.json",
            "cross_office_boundary_verification_report.json",
            "submitted_evidence_comparison_report.json",
            "audit_harness_integrity_report.json",
            "certification_findings_register.json",
            "final_ecs003_certification_decision.json",
            "completion_report.json",
        ]
        for name in required:
            self.assertTrue((OUTPUT_DIR / name).is_file(), name)

    def test_two_clean_room_runs_completed_from_entrypoint(self):
        run_a = self._read("run_a_complete_execution_package.json")
        run_b = self._read("run_b_complete_execution_package.json")
        self.assertEqual(run_a["exit_code"], 0)
        self.assertEqual(run_b["exit_code"], 0)
        self.assertNotEqual(run_a["output_dir"], run_b["output_dir"])
        self.assertGreater(run_a["generated_artifact_count"], 10)
        self.assertGreater(run_b["generated_artifact_count"], 10)

    def test_final_decision_is_exactly_pass_or_fail(self):
        decision = self._read("final_ecs003_certification_decision.json")
        completion = self._read("completion_report.json")
        self.assertIn(decision["decision"], {"PASS", "FAIL"})
        self.assertEqual(decision["decision"], completion["decision"])
        self.assertEqual(completion["status"], "COMPLETE")

    def test_findings_are_consistent_with_decision(self):
        findings = self._read("certification_findings_register.json")
        decision = self._read("final_ecs003_certification_decision.json")
        if decision["decision"] == "PASS":
            self.assertEqual(findings, [])
        else:
            self.assertGreater(len(findings), 0)
            self.assertTrue(all(row["blocking"] for row in findings))

    def test_submitted_evidence_is_compared_only_after_runs(self):
        comparison = self._read("submitted_evidence_comparison_report.json")
        self.assertGreater(comparison["submitted_file_count"], 0)
        self.assertIn("execution_summary.json", comparison["independent_top_level_json_outputs"])
        self.assertEqual(comparison["disposition"], "PASS")


if __name__ == "__main__":
    unittest.main()
