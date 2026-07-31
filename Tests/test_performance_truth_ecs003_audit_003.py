from __future__ import annotations

import json
import unittest

from Scripts.performance_truth_ecs003_audit_003 import OUTPUT_DIR, generate_audit


class PerformanceTruthEcs003Audit003Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = generate_audit()

    def _read(self, name):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_operational_deliverables_exist(self):
        required = [
            "independent_environment_construction_report.json",
            "independent_build_verification_report.json",
            "runtime_execution_report.json",
            "behavioral_validation_report.json",
            "runtime_interface_verification_report.json",
            "deterministic_replay_report.json",
            "runtime_mutation_validation_report.json",
            "stress_validation_report.json",
            "runtime_evidence_regeneration_report.json",
            "certification_findings_register.json",
            "final_ecs003_operational_certification_decision.json",
            "completion_report.json",
        ]
        for name in required:
            self.assertTrue((OUTPUT_DIR / name).is_file(), name)

    def test_runtime_execution_is_direct_and_successful(self):
        runtime = self._read("runtime_execution_report.json")
        evidence = self._read("runtime_audit_log/runtime_execution_evidence.json")
        self.assertEqual(runtime["disposition"], "PASS")
        self.assertEqual(evidence["startup"]["engineName"], "Performance Truth Engine")
        self.assertGreaterEqual(len(evidence["final_snapshot"]["orderLedger"]), 3)
        self.assertTrue(evidence["final_snapshot"]["integrity"]["hashesValid"])
        self.assertEqual(len(evidence["live_snapshot"]["orderLedger"]), 0)

    def test_behavior_interfaces_stress_and_evidence_pass(self):
        behavior = self._read("behavioral_validation_report.json")
        interfaces = self._read("runtime_interface_verification_report.json")
        stress = self._read("stress_validation_report.json")
        regenerated = self._read("runtime_evidence_regeneration_report.json")
        self.assertTrue(all(row["disposition"] == "PASS" for row in behavior))
        self.assertTrue(all(row["disposition"] == "PASS" for row in interfaces))
        self.assertEqual(stress["disposition"], "PASS")
        self.assertEqual(stress["ledger_count"], 25)
        self.assertEqual(regenerated["disposition"], "PASS")

    def test_replay_and_runtime_mutations_are_validated(self):
        replay = self._read("deterministic_replay_report.json")
        mutations = self._read("runtime_mutation_validation_report.json")
        self.assertEqual(replay["disposition"], "PASS")
        self.assertTrue(replay["deterministic"])
        self.assertTrue(all(row["detected"] for row in mutations))
        self.assertTrue(all(row["terminal_behavior"] == "FAIL_CLOSED" for row in mutations))

    def test_final_operational_decision_is_pass_with_no_findings(self):
        findings = self._read("certification_findings_register.json")
        decision = self._read("final_ecs003_operational_certification_decision.json")
        completion = self._read("completion_report.json")
        self.assertEqual(findings, [])
        self.assertEqual(decision["decision"], "PASS")
        self.assertEqual(completion["decision"], "PASS")
        self.assertEqual(completion["status"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
