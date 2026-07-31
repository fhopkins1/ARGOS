from __future__ import annotations

import json
import unittest

from Scripts import historian_rm002a_behavioral_completion as completion


class HistorianRM002ABehavioralCompletionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completion.generate()

    def _load(self, name: str):
        return json.loads((completion.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_all_rm002a_orders_pass_behavioral_completion(self) -> None:
        report = self._load("behavioral_completion_report.json")
        self.assertEqual(12, report["orders_total"])
        self.assertEqual(12, report["orders_passed"])
        self.assertEqual(0, report["orders_failed"])
        self.assertEqual("PASS", report["behavioral_completion_status"])
        self.assertTrue(report["ready_for_rm002_recertification"])

    def test_reference_execution_proves_replay_learning_and_evidence(self) -> None:
        reference = self._load("reference_runtime_execution.json")
        self.assertTrue(reference["replay"]["equivalent"])
        self.assertFalse(reference["learning_projection"]["historian_performed_learning"])
        self.assertEqual("PASS", reference["certification_report"]["certification_status"])
        self.assertGreaterEqual(len(reference["journey"]["evidence"]), 10)

    def test_behavioral_order_registry_has_terminal_dispositions(self) -> None:
        registry = self._load("behavioral_order_registry.json")
        self.assertEqual(12, len(registry))
        self.assertTrue(all(item["disposition"] == "PASS" for item in registry))
        self.assertEqual({item["evidence_reference"] for item in registry}, {"reference_runtime_execution.json"})


if __name__ == "__main__":
    unittest.main()
