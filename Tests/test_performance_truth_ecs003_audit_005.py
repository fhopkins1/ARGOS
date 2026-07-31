from __future__ import annotations

import json
import unittest

from Scripts.performance_truth_ecs003_audit_005 import OUTPUT_DIR, generate_audit


class PerformanceTruthAudit005Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decision = generate_audit()

    def _read(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_deliverables_exist(self):
        required = [
            "candidate_integrity_report.json",
            "clean_room_environment_report.json",
            "audit_harness_verification_report.json",
            "run_a_runtime_package.json",
            "run_b_runtime_package.json",
            "runtime_test_verification_report.json",
            "audit_004_finding_verification_report.json",
            "behavioral_verification_report.json",
            "replay_verification_report.json",
            "fail_closed_verification_report.json",
            "mutation_verification_report.json",
            "stress_verification_report.json",
            "evidence_comparison_report.json",
            "audit_harness_integrity_report.json",
            "certification_findings_register.json",
            "final_ecs003_certification_decision.json",
            "completion_report.json",
        ]
        for name in required:
            self.assertTrue((OUTPUT_DIR / name).is_file(), name)

    def test_two_clean_room_runs_executed(self):
        run_a = self._read("run_a_runtime_package.json")
        run_b = self._read("run_b_runtime_package.json")
        self.assertEqual(run_a["exit_code"], 0)
        self.assertEqual(run_b["exit_code"], 0)
        self.assertNotEqual(run_a["clean_room_root"], run_b["clean_room_root"])
        self.assertGreater(run_a["test_results"]["total_executed"], 0)
        self.assertGreater(run_b["test_results"]["total_executed"], 0)

    def test_decision_is_exactly_pass_or_fail_and_matches_findings(self):
        decision = self._read("final_ecs003_certification_decision.json")
        findings = self._read("certification_findings_register.json")
        self.assertIn(decision["decision"], {"PASS", "FAIL"})
        if findings:
            self.assertEqual(decision["decision"], "FAIL")
        else:
            self.assertEqual(decision["decision"], "PASS")

    def test_mutation_specific_hardcoded_detection_is_blocking(self):
        mutation = self._read("mutation_verification_report.json")
        findings = self._read("certification_findings_register.json")
        self.assertEqual(mutation["disposition"], "FAIL")
        self.assertTrue(mutation["hardcoded_detection_findings"])
        self.assertTrue(any("Mutation" in item["title"] for item in findings))


if __name__ == "__main__":
    unittest.main()
