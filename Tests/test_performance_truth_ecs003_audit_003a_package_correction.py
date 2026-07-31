from __future__ import annotations

import json
import unittest

from Scripts.performance_truth_ecs003_audit_003a_package_correction import OUTPUT_DIR, generate_evidence


class PerformanceTruthAudit003APackageCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = generate_evidence()

    def _read(self, name):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_canonical_auditor_entrypoint_and_guide_exist(self):
        command = self._read("execution_command_reference.json")
        self.assertEqual(command["canonical_command"], "python audit_reproduce.py --candidate <repository-package.zip> --output <empty-output-directory>")

    def test_active_auditor_path_has_no_authorizations_references(self):
        scan = self._read("active_auditor_path_scan.json")
        for record in scan.values():
            self.assertFalse(any(record.values()))

    def test_self_validation_entrypoint_completed(self):
        log = self._read("self_validation_execution_log.json")
        manifest = self._read("self_validation_output_manifest.json")
        self.assertEqual(log["exit_code"], 0)
        self.assertGreater(manifest["file_count"], 10)
        self.assertIn("execution_summary.json", manifest["files"])

    def test_evidence_package_is_not_used_as_proof_and_no_business_logic_changed(self):
        historical = self._read("historical_artifact_classification_record.json")
        changes = self._read("implementation_change_manifest.json")
        self.assertFalse(historical["evidence_package_used_as_proof"])
        self.assertTrue(all(not row["business_logic_modified"] for row in changes))

    def test_completion_result_is_complete_not_certification(self):
        completion = self._read("completion_report.json")
        self.assertEqual(completion["completion_result"], "COMPLETE")
        self.assertFalse(completion["entrypoint_issues_certification"])
        self.assertEqual(completion["status"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
