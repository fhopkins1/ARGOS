import json
import unittest

from Scripts import monitoring_rm002_b02_behavioral_verification as b02


class MonitoringRM002B02BehavioralVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completion = b02.generate()
        cls.output_dir = b02.OUTPUT_DIR

    def _load(self, name):
        return json.loads((self.output_dir / name).read_text(encoding="utf-8"))

    def test_bounded_unittest_execution_passed(self):
        record = self._load("bounded_unittest_execution_record.json")

        self.assertEqual(record["module"], b02.MONITORING_VERIFIER)
        self.assertEqual(record["returncode"], 0)
        self.assertEqual(record["disposition"], "PASS")

    def test_observation_evaluation_and_finding_campaign_complete(self):
        validation = self._load("B02-001_behavioral_validation_report.json")
        executions = self._load("B02-001_behavioral_execution_evidence_registry.json")
        deficiencies = self._load("B02-001_outstanding_behavioral_deficiency_registry.json")

        self.assertEqual(validation["status"], "PASS")
        self.assertGreaterEqual(validation["executions"], 9)
        self.assertEqual(validation["failures"], 0)
        self.assertEqual(deficiencies, [])
        self.assertTrue(all(item["terminal_disposition"] == "PASS" for item in executions))

    def test_response_and_resilience_campaigns_have_terminal_evidence(self):
        response = self._load("B02-002_behavioral_execution_registry.json")
        recovery = self._load("B02-003_behavioral_execution_evidence_registry.json")
        response_report = self._load("B02-002_behavioral_coverage_report.json")
        recovery_report = self._load("B02-003_verification_ambiguity_resolution_report.json")

        self.assertGreaterEqual(len(response), 7)
        self.assertGreaterEqual(len(recovery), 9)
        self.assertTrue(all(item["terminal_disposition"] == "PASS" for item in response + recovery))
        self.assertEqual(response_report["status"], "PASS")
        self.assertEqual(recovery_report["status"], "PASS")
        self.assertFalse(recovery_report["replay_ambiguity"])

    def test_behavioral_reconciliation_is_ready_for_b03(self):
        coverage = self._load("B02-004_behavioral_coverage_registry.json")
        evidence = self._load("B02-004_behavioral_evidence_registry.json")
        traceability = self._load("B02-004_behavioral_traceability_registry.json")
        readiness = self._load("B02-004_behavioral_readiness_assessment.json")
        report = self._load("B02-004_behavioral_reconciliation_report.json")

        self.assertEqual(len(coverage), len(evidence))
        self.assertEqual(len(traceability), len(evidence))
        self.assertTrue(all(item["traceability_complete"] for item in coverage))
        self.assertTrue(all(item["admissible"] and item["origin"] == "executable verification" for item in evidence))
        self.assertEqual(readiness["status"], "READY")
        self.assertEqual(readiness["ready_for"], "MONITORING-RM-002-B03")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["failures"], 0)

    def test_completion_report_preserves_order_constraints(self):
        completion = self._load("completion_report.json")
        series = self._load("series_completion_report.json")
        baseline = self._load("monitoring_rm002_b02_authoritative_behavioral_baseline.json")

        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(series["status"], "COMPLETE")
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["implementation_proof_generated"])
        self.assertFalse(completion["certification_activity_executed"])
        self.assertEqual(completion["baseline_digest"], baseline["digest"])


if __name__ == "__main__":
    unittest.main()
