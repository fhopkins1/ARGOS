import json
import unittest

from Scripts import monitoring_rm002_b04_final_certification as b04


class MonitoringRM002B04FinalCertificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completion = b04.generate()
        cls.output_dir = b04.OUTPUT_DIR

    def _load(self, name):
        return json.loads((self.output_dir / name).read_text(encoding="utf-8"))

    def test_authoritative_proof_baseline_covers_requirements(self):
        proofs = self._load("B04-001_authoritative_proof_baseline.json")
        identities = self._load("B04-001_proof_identity_registry.json")
        validation = self._load("B04-001_proof_validation_report.json")

        self.assertGreater(len(proofs), 0)
        self.assertEqual(len(proofs), len(identities))
        self.assertEqual(validation["status"], "PASS")
        self.assertEqual(validation["missing_proof"], 0)
        self.assertEqual(validation["duplicate_proof"], 0)
        self.assertTrue(all(item["derived_exclusively_from_executed_behavioral_evidence"] for item in proofs))

    def test_certification_candidate_has_no_blockers(self):
        candidate = self._load("B04-002_certification_candidate_registry.json")
        readiness = self._load("B04-002_certification_readiness_assessment.json")
        blockers = self._load("B04-002_certification_blocker_registry.json")
        report = self._load("B04-002_certification_reconciliation_report.json")

        self.assertTrue(candidate["candidate_frozen"])
        self.assertEqual(readiness["status"], "READY")
        self.assertEqual(blockers, [])
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["unresolved_findings"], 0)

    def test_reproducibility_runs_are_deterministic_and_independent(self):
        repro = self._load("B04-003_certification_reproducibility_report.json")
        runs = self._load("B04-003_behavioral_execution_reproduction_registry.json")
        comparison = self._load("B04-003_repeated_execution_comparison_matrix.json")
        git_independence = self._load("B04-003_git_independence_verification_report.json")
        workstation = self._load("B04-003_workstation_independence_verification_report.json")

        self.assertEqual(repro["status"], "PASS")
        self.assertTrue(all(item["terminal_disposition"] == "PASS" for item in runs))
        self.assertTrue(all(item["constitutionally_equivalent"] for item in comparison))
        self.assertEqual(git_independence["status"], "PASS")
        self.assertEqual(workstation["status"], "PASS")

    def test_final_ecs003_verdict_is_unconditional_pass(self):
        verdict = self._load("B04-004_final_ecs003_certification_verdict.json")
        blockers = self._load("B04-004_certification_blocker_registry.json")
        integrity = self._load("B04-004_certification_integrity_verification_report.json")
        completion = self._load("B04-004_certification_completion_report.json")

        self.assertEqual(verdict["verdict"], "UNCONDITIONAL_PASS")
        self.assertTrue(verdict["authorized"])
        self.assertEqual(blockers, [])
        self.assertEqual(integrity["status"], "PASS")
        self.assertEqual(completion["verdict"], "UNCONDITIONAL_PASS")

    def test_completion_report_preserves_constraints(self):
        completion = self._load("completion_report.json")
        series = self._load("series_completion_report.json")
        baseline = self._load("monitoring_rm002_b04_authoritative_certification_baseline.json")

        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["final_verdict"], "UNCONDITIONAL_PASS")
        self.assertEqual(series["final_verdict"], "UNCONDITIONAL_PASS")
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertEqual(completion["baseline_digest"], baseline["digest"])


if __name__ == "__main__":
    unittest.main()
