from __future__ import annotations

import json
import unittest

from Scripts.performance_truth_ecs003_audit_002 import OUTPUT_DIR, REQUIRED_REPORTS, generate_audit


class PerformanceTruthEcs003Audit002Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = generate_audit()

    def _read(self, name):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_all_required_deliverables_exist(self):
        filenames = {
            "Independent Repository Discovery Report": "independent_repository_discovery_report.json",
            "Independent Constitutional Verification Report": "independent_constitutional_verification_report.json",
            "Independent Behavioral Verification Report": "independent_behavioral_verification_report.json",
            "Independent Evidence Regeneration Report": "independent_evidence_regeneration_report.json",
            "Mutation Validation Report": "mutation_validation_report.json",
            "Fail-Closed Validation Report": "fail_closed_validation_report.json",
            "Deterministic Replay Report": "deterministic_replay_report.json",
            "Cross-Office Verification Report": "cross_office_verification_report.json",
            "Certification Findings Register": "certification_findings_register.json",
            "Final ECS-003 Certification Decision": "final_ecs003_certification_decision.json",
        }
        self.assertEqual(set(REQUIRED_REPORTS), set(filenames))
        for filename in filenames.values():
            self.assertTrue((OUTPUT_DIR / filename).is_file(), filename)

    def test_repository_discovery_is_package_only_and_complete(self):
        report = self._read("independent_repository_discovery_report.json")
        self.assertEqual(report["disposition"], "PASS")
        self.assertGreater(len(report["implementation_inventory"]), 0)
        self.assertGreater(len(report["verifier_inventory"]), 0)
        self.assertTrue(all(row["available"] for row in report["submitted_package_inventory"]))
        self.assertFalse(report["package_only_probe"]["external_state_required"])

    def test_independent_behavioral_execution_passes_with_raw_evidence(self):
        executions = self._read("independent_behavioral_verification_report.json")
        self.assertEqual(len(executions), 5)
        self.assertTrue(all(row["disposition"] == "PASS" for row in executions))
        for row in executions:
            self.assertTrue(row["stdout_sha256"])
            self.assertTrue(row["stderr_sha256"])

    def test_mutation_fail_closed_and_replay_validation_pass(self):
        mutations = self._read("mutation_validation_report.json")
        fail_closed = self._read("fail_closed_validation_report.json")
        replay = self._read("deterministic_replay_report.json")
        self.assertTrue(all(row["detected"] and row["disposition"] == "PASS" for row in mutations))
        self.assertTrue(all(row["terminal_disposition"] == "FAIL_CLOSED" for row in fail_closed))
        self.assertEqual(replay["disposition"], "PASS")

    def test_final_decision_is_single_pass_with_no_findings(self):
        findings = self._read("certification_findings_register.json")
        decision = self._read("final_ecs003_certification_decision.json")
        completion = self._read("completion_report.json")
        self.assertEqual(findings, [])
        self.assertEqual(decision["decision"], "PASS")
        self.assertEqual(completion["decision"], "PASS")
        self.assertEqual(completion["status"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
