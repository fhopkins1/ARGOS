from __future__ import annotations

import json
import unittest

from Scripts import enterprise_learning_ecs004_final_certification as final


class EnterpriseLearningECS004FinalCertificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        final.run()

    def _load(self, name: str):
        return json.loads((final.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_machine_report_has_single_pass_disposition(self) -> None:
        report = self._load("machine_readable_certification_report.json")
        self.assertEqual("PASS", report["overall_status"])
        self.assertEqual("PASS", report["overall_certification_disposition"])
        self.assertEqual([], report["constitutional_failures"])

    def test_repository_independence_has_no_developer_paths(self) -> None:
        report = self._load("repository_independence_verification_report.json")
        self.assertEqual("PASS", report["disposition"])
        self.assertFalse(report["git_metadata_required"])
        self.assertEqual([], report["absolute_developer_paths_detected"])

    def test_repository_provenance_is_repository_contained(self) -> None:
        report = self._load("repository_provenance_verification_report.json")
        self.assertEqual("PASS", report["disposition"])
        self.assertEqual([], report["missing_source_order_directories"])
        self.assertEqual([], report["developer_local_reference_findings"])

    def test_complete_mutation_campaign_fails_closed(self) -> None:
        report = self._load("complete_mutation_verification_report.json")
        self.assertEqual("PASS", report["disposition"])
        self.assertEqual([], report["unexpected_results"])
        self.assertEqual(16, report["mutation_count"])
        gate = report["inventory_reconciliation_gate"]
        self.assertEqual(16, gate["authoritative_inventory_size"])
        self.assertEqual(16, gate["implementation_count"])
        self.assertEqual(16, gate["discovery_count"])
        self.assertEqual(16, gate["execution_count"])
        self.assertEqual(16, gate["expected_failure_count"])
        self.assertEqual(0, gate["unexpected_pass_count"])
        self.assertEqual(0, gate["error_count"])
        self.assertEqual(0, gate["missing_evidence_count"])

    def test_human_report_and_runbook_are_generated(self) -> None:
        self.assertTrue((final.OUTPUT_DIR / "human_readable_certification_report.md").exists())
        runbook = (final.OUTPUT_DIR / "updated_auditor_execution_runbook.md").read_text(encoding="utf-8")
        self.assertIn("enterprise_learning_ecs004_final_certification.py", runbook)


if __name__ == "__main__":
    unittest.main()
