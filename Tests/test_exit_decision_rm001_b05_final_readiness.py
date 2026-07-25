import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B05_FINAL_READINESS"


class ExitDecisionRM001B05FinalReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/exit_decision_rm001_b05_final_readiness.py"],
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

    def test_source_orders_and_baselines_are_complete(self):
        sources = self._read_json("source_order_registry.json")
        baselines = self._read_json("baseline_input_registry.json")
        self.assertEqual(len(sources), 4)
        self.assertEqual(len(baselines), 4)
        self.assertTrue(all(item["status"] == "COMPLETE" for item in baselines))

    def test_requirements_are_atomic_owned_and_classified(self):
        requirements = self._read_json("canonical_requirement_identity_registry.json")
        classes = {item["classification"] for item in requirements}
        self.assertGreater(len(requirements), 80)
        self.assertIn("governance", classes)
        self.assertIn("traceability", classes)
        self.assertTrue(all(item["atomic"] and item["owner"] for item in requirements))

    def test_dependencies_and_traceability_are_clean(self):
        dependencies = self._read_json("constitutional_dependency_registry.json")
        integrity = self._read_json("traceability_integrity_registry.json")
        graph = self._read_json("constitutional_participation_graph.json")
        self.assertFalse(any(item["circular_dependency"] or item["missing_dependency"] for item in dependencies))
        self.assertEqual(integrity["broken_traceability"], [])
        self.assertTrue(graph["nodes"])
        self.assertTrue(graph["edges"])

    def test_final_audit_and_verdict_are_constitutionally_ready(self):
        audit = self._read_json("final_constitutional_audit_report.json")
        verdict = self._read_json("final_ecs003_constitutional_verdict.json")
        self.assertTrue(all(item["status"] == "PASS" for item in audit["audit_domains"]))
        self.assertEqual(verdict["verdict"], "UNCONDITIONAL_PASS")
        self.assertEqual(verdict["scope"], "constitutional_readiness")
        self.assertFalse(verdict["implementation_behavior_evaluated"])

    def test_completion_report_ready_for_rm002(self):
        completion = self._read_json("completion_report.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["ready_for"], "EXIT-DECISION-RM-002")
        self.assertEqual(completion["final_constitutional_ecs003_verdict"], "UNCONDITIONAL_PASS")
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertTrue(all(completion["completion_checks"].values()))


if __name__ == "__main__":
    unittest.main()
