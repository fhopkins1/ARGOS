from __future__ import annotations

import json
import unittest

from Scripts import historian_ecs003_audit_003 as audit


class HistorianECS003Audit003Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        audit.generate()

    def _load(self, name: str):
        return json.loads((audit.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_final_behavioral_certification_is_issued(self) -> None:
        report = self._load("final_independent_certification_report.json")
        self.assertEqual("ECS-003 CERTIFIED", report["decision"])
        self.assertEqual("behavioral_certification_only", report["certification_scope"])
        self.assertFalse(report["constitutional_architecture_modified"])
        self.assertFalse(report["implementation_modified"])

    def test_all_audit_orders_pass(self) -> None:
        matrix = self._load("ecs003_compliance_matrix.json")
        self.assertEqual(12, len(matrix))
        self.assertTrue(all(row["disposition"] == "PASS" for row in matrix))
        manifest = self._load("audit_manifest.json")
        self.assertEqual(12, manifest["audit_orders_passed"])

    def test_fail_closed_and_reproduction_are_objectively_demonstrated(self) -> None:
        fail_closed = self._load("fail_closed_validation_report.json")
        self.assertGreaterEqual(len(fail_closed), 4)
        self.assertTrue(all(item["detected"] for item in fail_closed))
        self.assertTrue(all(item["evidence_outcome"] == "FAIL_CLOSED" for item in fail_closed))
        reproduction = self._load("independent_reproduction_report.json")
        self.assertTrue(reproduction["equivalent"])
        self.assertEqual("PASS", reproduction["run_a_status"])
        self.assertEqual("PASS", reproduction["run_b_status"])


if __name__ == "__main__":
    unittest.main()
