import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B01_CONSTITUTIONAL_BASELINE"


class ExitDecisionRM001B01ConstitutionalBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/exit_decision_rm001_b01_constitutional_baseline.py"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=120,
        )
        cls.returncode = completed.returncode
        cls.stderr = completed.stderr

    def _read_json(self, filename: str):
        return json.loads((OUTPUT_DIR / filename).read_text(encoding="utf-8"))

    def test_generator_completes(self):
        self.assertEqual(self.returncode, 0, self.stderr)

    def test_all_source_orders_are_preserved(self):
        source_registry = self._read_json("source_order_registry.json")
        self.assertEqual(len(source_registry), 4)
        self.assertTrue(all(record["disposition"] == "PRESERVED" for record in source_registry))
        self.assertTrue(all((REPOSITORY_ROOT / record["committed_copy"]).exists() for record in source_registry))

    def test_exit_decision_authority_excludes_execution_and_truth_mutation(self):
        prohibited = self._read_json("prohibited_authority_registry.json")
        separation = self._read_json("authority_separation_registry.json")
        prohibited_text = " ".join(item["prohibited_authority"] for item in prohibited)
        self.assertIn("execute trades", prohibited_text)
        self.assertIn("modify Position Registry truth", prohibited_text)
        for item in separation:
            if item["authority_stage"] in {"authorization", "execution_request", "broker_submission", "position_mutation", "historical_custody"}:
                self.assertFalse(item["exit_decision_may_perform"])

    def test_enterprise_boundaries_cover_required_offices(self):
        boundaries = self._read_json("enterprise_boundary_registry.json")
        offices = {item["office"] for item in boundaries}
        self.assertIn("Commander", offices)
        self.assertIn("Trader", offices)
        self.assertIn("Broker", offices)
        self.assertIn("Position Registry", offices)
        self.assertIn("Historian", offices)

    def test_conflict_governance_and_precedence_are_complete(self):
        conflicts = self._read_json("conflict_resolution_registry.json")
        precedence = self._read_json("precedence_matrix.json")
        self.assertGreaterEqual(len(conflicts), 6)
        self.assertEqual(precedence[0]["authority"], "Commander")
        self.assertTrue(all("fail closed" in item["required_disposition"] or "escalate" in item["required_disposition"] or "preserve" in item["required_disposition"] for item in conflicts))

    def test_completion_report_ready_for_b02(self):
        completion = self._read_json("completion_report.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["ready_for"], "EXIT-DECISION-RM-001-B02")
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertTrue(all(completion["completion_checks"].values()))


if __name__ == "__main__":
    unittest.main()
