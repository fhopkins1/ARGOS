import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B02_OBJECT_LIFECYCLE"


class ExitDecisionRM001B02ObjectLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/exit_decision_rm001_b02_object_lifecycle.py"],
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

    def test_source_orders_and_canonical_objects_are_complete(self):
        sources = self._read_json("source_order_registry.json")
        objects = self._read_json("canonical_exit_decision_object_registry.json")
        self.assertEqual(len(sources), 4)
        self.assertEqual(len(objects), 18)
        self.assertIn("Exit Decision", {item["object_name"] for item in objects})
        self.assertTrue(all(item["lifecycle_required"] for item in objects))

    def test_ownership_separates_external_truth(self):
        ownership = self._read_json("attribute_ownership_registry.json")
        external = {item["attribute"]: item for item in ownership if item["constitutional_owner"] != "Exit Decision Office"}
        self.assertIn("position_binding", external)
        self.assertIn("authorization_binding", external)
        self.assertTrue(all(item["external_truth_transfer"] == "prohibited" for item in ownership))
        self.assertFalse(external["position_binding"]["exit_decision_may_mutate"])

    def test_lifecycle_and_invalid_transitions_are_governed(self):
        states = self._read_json("lifecycle_state_registry.json")
        transitions = self._read_json("transition_registry.json")
        invalid = self._read_json("invalid_transition_registry.json")
        self.assertIn("created", {item["state"] for item in states})
        self.assertIn("archived", {item["state"] for item in states})
        self.assertTrue(all(item["transition_authority"] for item in transitions))
        self.assertTrue(all(item["disposition"].startswith("fail closed") for item in invalid))

    def test_correction_supersession_expiration_and_history_are_complete(self):
        corrections = self._read_json("correction_authority_registry.json")
        supersession = self._read_json("supersession_lineage_registry.json")
        expiration = self._read_json("expiration_authority_registry.json")
        history = self._read_json("historical_integrity_constitution.json")
        self.assertGreaterEqual(len(corrections), 5)
        self.assertTrue(all(item["predecessor_required"] and item["successor_required"] for item in supersession))
        self.assertTrue(all(item["post_expiration_rule"] for item in expiration))
        self.assertEqual(history["history"], "append_only")

    def test_completion_report_ready_for_b03(self):
        completion = self._read_json("completion_report.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["ready_for"], "EXIT-DECISION-RM-001-B03")
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertTrue(all(completion["completion_checks"].values()))


if __name__ == "__main__":
    unittest.main()
