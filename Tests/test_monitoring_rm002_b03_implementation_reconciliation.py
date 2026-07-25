import json
import unittest

from Scripts import monitoring_rm002_b03_implementation_reconciliation as b03


class MonitoringRM002B03ImplementationReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completion = b03.generate()
        cls.output_dir = b03.OUTPUT_DIR

    def _load(self, name):
        return json.loads((self.output_dir / name).read_text(encoding="utf-8"))

    def test_defect_inventory_contains_no_verified_implementation_defects(self):
        defects = self._load("B03-001_verified_implementation_defect_registry.json")
        classifications = self._load("B03-001_defect_classification_registry.json")
        validation = self._load("B03-001_defect_validation_report.json")

        self.assertEqual(defects, [])
        self.assertGreater(len(classifications), 0)
        self.assertTrue(all(not item["may_produce_implementation_modification"] for item in classifications))
        self.assertEqual(validation["status"], "PASS")
        self.assertEqual(validation["implementation_defects"], 0)
        self.assertFalse(validation["classification_ambiguity"])

    def test_remediation_records_no_code_change_required(self):
        remediation = self._load("B03-002_implementation_remediation_registry.json")
        modifications = self._load("B03-002_implementation_modification_registry.json")
        candidate = self._load("B03-002_updated_implementation_candidate_registry.json")
        report = self._load("B03-002_implementation_modification_reconciliation_report.json")

        self.assertEqual(remediation, [])
        self.assertEqual(modifications, [])
        self.assertFalse(candidate["implementation_modified_during_b03"])
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["no_code_change_required"])
        self.assertEqual(report["unauthorized_modifications"], 0)

    def test_targeted_regression_passed_for_unchanged_candidate(self):
        regression = self._load("B03-003_regression_verification_registry.json")
        introduced = self._load("B03-003_introduced_regression_registry.json")
        unresolved = self._load("B03-003_unresolved_regression_registry.json")
        disposition = self._load("B03-003_defect_disposition_registry.json")

        self.assertEqual(len(regression), 2)
        self.assertTrue(all(item["terminal_disposition"] == "PASS" for item in regression))
        self.assertEqual(introduced, [])
        self.assertEqual(unresolved, [])
        self.assertEqual(disposition[0]["final_disposition"], "NON_IMPLEMENTATION_FINDING")

    def test_candidate_reconciliation_ready_for_b04(self):
        integrity = self._load("B03-004_implementation_integrity_verification_report.json")
        readiness = self._load("B03-004_implementation_readiness_assessment.json")
        unresolved = self._load("B03-004_unresolved_finding_registry.json")
        evidence = self._load("B03-004_implementation_evidence_registry.json")

        self.assertEqual(integrity["status"], "PASS")
        self.assertTrue(integrity["regression_evidence_complete"])
        self.assertEqual(readiness["status"], "READY")
        self.assertEqual(readiness["ready_for"], "MONITORING-RM-002-B04")
        self.assertEqual(unresolved, [])
        self.assertTrue(all(item["admissible"] for item in evidence))

    def test_completion_report_preserves_constraints(self):
        completion = self._load("completion_report.json")
        series = self._load("series_completion_report.json")
        baseline = self._load("monitoring_rm002_b03_authoritative_implementation_candidate.json")

        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(series["status"], "COMPLETE")
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["implementation_proof_generated"])
        self.assertFalse(completion["certification_activity_executed"])
        self.assertEqual(completion["baseline_digest"], baseline["digest"])


if __name__ == "__main__":
    unittest.main()
