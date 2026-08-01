from __future__ import annotations

import json
import unittest

from Scripts import historian_ecs004_audit_001 as audit


class HistorianECS004Audit001Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        audit.generate()

    def _load(self, name: str):
        return json.loads((audit.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_final_independent_reproducibility_certification_is_issued(self) -> None:
        report = self._load("final_independent_reproducibility_certification_report.json")
        self.assertEqual("ECS-004 CERTIFIED", report["decision"])
        self.assertTrue(report["certification_derived_from_reproduced_execution"])
        self.assertFalse(report["developer_generated_artifacts_authoritative"])

    def test_all_twelve_audit_orders_pass(self) -> None:
        registry = self._load("audit_order_registry.json")
        self.assertEqual(12, len(registry))
        self.assertTrue(all(item["disposition"] == "PASS" for item in registry))

    def test_compliance_matrix_and_mutations_are_complete(self) -> None:
        compliance = self._load("ecs004_compliance_matrix.json")
        self.assertTrue(all(item["disposition"] == "PASS" for item in compliance))
        mutation = self._load("mutation_detection_assessment.json")
        self.assertTrue(mutation["all_mutations_detected"])
        self.assertTrue(mutation["fail_closed_behavior_verified"])

    def test_independent_reproduction_uses_multiple_runs(self) -> None:
        reproduction = self._load("independent_reproduction_report.json")
        self.assertEqual(3, len(reproduction["reproductions"]))
        self.assertEqual("PASS", reproduction["independent_reproduction_status"])
        self.assertTrue(reproduction["constitutional_equivalence"])


if __name__ == "__main__":
    unittest.main()
