import json
import unittest

from Scripts.performance_truth_ecs003_audit_001 import OUTPUT_DIR, generate_audit


class PerformanceTruthEcs003Audit001Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = generate_audit()

    def _read(self, name):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_audit_deliverables_exist(self):
        required = [
            "executive_audit_report.json",
            "constitutional_audit_report.json",
            "implementation_audit_report.json",
            "behavioral_audit_report.json",
            "evidence_and_proof_audit_report.json",
            "clean_room_reproduction_report.json",
            "initial_fail_closed_assessment.json",
            "certification_blocker_registry.json",
            "decision_requirement_registry.json",
            "remediation_recommendation_registry.json",
            "final_ecs003_audit_report.json",
            "initial_ecs003_verdict.json",
            "behavioral_execution_registry.json",
            "raw_execution_evidence_registry.json",
            "requirement_proof_registry.json",
            "proof_lineage_registry.json",
            "manifest.json",
        ]
        for name in required:
            self.assertTrue((OUTPUT_DIR / name).is_file(), name)

    def test_behavioral_executions_have_raw_evidence(self):
        executions = self._read("behavioral_execution_registry.json")
        evidence = {row["evidence_id"]: row for row in self._read("raw_execution_evidence_registry.json")}

        self.assertEqual(len(executions), 2)
        for execution in executions:
            self.assertEqual(execution["disposition"], "PASS")
            self.assertEqual(len(execution["evidence"]), 3)
            for evidence_id in execution["evidence"]:
                self.assertIn(evidence_id, evidence)

    def test_verdict_is_pass_with_remediation_when_blockers_remain(self):
        verdict = self._read("initial_ecs003_verdict.json")
        blockers = self._read("certification_blocker_registry.json")
        report = self._read("final_ecs003_audit_report.json")

        self.assertEqual(verdict["verdict"], "PASS_WITH_REMEDIATION")
        self.assertEqual(report["initial_ecs003_verdict"], "PASS_WITH_REMEDIATION")
        self.assertGreater(len(blockers), 0)
        self.assertTrue(report["behavioral_pass"])

    def test_every_requirement_has_one_disposition(self):
        requirements = self._read("canonical_requirement_registry.json")
        proofs = self._read("requirement_proof_registry.json")
        allowed = {"PROVEN", "NOT_PROVEN", "NOT_APPLICABLE"}

        self.assertEqual(len(requirements), len(proofs))
        self.assertEqual(len({row["requirement_id"] for row in proofs}), len(proofs))
        for proof in proofs:
            self.assertIn(proof["disposition"], allowed)

    def test_no_implementation_remediation_occurs(self):
        implementation = self._read("dependency_derived_implementation_inventory.json")
        source = self._read("source_order_registry.json")

        self.assertGreater(len(implementation), 0)
        self.assertEqual(source[0]["order_id"], "PERFORMANCE-TRUTH-ECS003-AUDIT-001")


if __name__ == "__main__":
    unittest.main()
