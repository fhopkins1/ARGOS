from __future__ import annotations

import json
import unittest

from Scripts import historian_rm002_implementation_certification as cert


class HistorianRM002ImplementationCertificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cert.generate()

    def _load(self, name: str):
        return json.loads((cert.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_inventory_and_all_required_orders_are_present(self) -> None:
        manifest = self._load("campaign_manifest.json")
        self.assertGreaterEqual(manifest["artifact_count"], 10)
        self.assertGreaterEqual(manifest["verification_order_count"], 12)
        matrix = self._load("historian_rm002_certification_matrix.json")
        order_ids = {row["order_id"] for row in matrix}
        for suffix in range(1, 13):
            self.assertIn(f"HISTORIAN-RM-002-B{suffix:02d}", order_ids)

    def test_certification_fails_closed_when_blockers_exist(self) -> None:
        report = self._load("implementation_completeness_report.json")
        self.assertEqual("FAIL_CLOSED", report["final_disposition"])
        self.assertFalse(report["rm003_authorized"])
        self.assertFalse(report["constitutional_architecture_modified"])
        self.assertFalse(report["runtime_behavior_modified"])
        self.assertTrue(report["blocking_findings"])

    def test_findings_have_objective_evidence_and_remediation_objectives(self) -> None:
        findings = self._load("certification_findings_registry.json")
        self.assertGreaterEqual(len(findings), 10)
        for finding in findings:
            self.assertTrue(finding["objective_evidence"], finding["finding_id"])
            self.assertTrue(finding["recommended_remediation_objective"], finding["finding_id"])
            self.assertIn(finding["severity"], {"MAJOR", "BLOCKING"})


if __name__ == "__main__":
    unittest.main()
