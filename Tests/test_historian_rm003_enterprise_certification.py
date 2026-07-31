from __future__ import annotations

import json
import unittest

from Scripts import historian_rm003_enterprise_certification as rm003


class HistorianRM003EnterpriseCertificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rm003.generate()

    def _load(self, name: str):
        return json.loads((rm003.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_all_enterprise_certification_orders_are_dispositioned(self) -> None:
        registry = self._load("enterprise_certification_order_registry.json")
        self.assertEqual(12, len(registry))
        self.assertTrue(all(row["disposition"] == "BLOCKED_PRECONDITION" for row in registry))

    def test_precondition_gate_blocks_freeze_and_audit002(self) -> None:
        gate = self._load("rm003_precondition_gate_report.json")
        self.assertEqual("FAILED", gate["precondition_gate"])
        self.assertFalse(gate["enterprise_certification_execution_authorized"])
        self.assertFalse(gate["constitutional_freeze_authorized"])
        self.assertFalse(gate["hist_ecs003_audit_002_authorized"])
        self.assertEqual("FAIL_CLOSED", gate["observed_rm002_final_disposition"])

    def test_completion_report_is_honest_and_non_mutating(self) -> None:
        report = self._load("completion_report.json")
        self.assertEqual("NOT_CERTIFIED_PRECONDITION_FAILED", report["final_certification"])
        self.assertFalse(report["constitutional_architecture_modified"])
        self.assertFalse(report["implementation_modified"])
        self.assertFalse(report["new_behavior_introduced"])
        self.assertFalse(report["operational_authorization"])


if __name__ == "__main__":
    unittest.main()
