import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B04_INTERFACE_TRACEABILITY"


class ExitDecisionRM001B04InterfaceTraceabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/exit_decision_rm001_b04_interface_traceability.py"],
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

    def test_sources_and_prior_baselines_are_preserved(self):
        sources = self._read_json("source_order_registry.json")
        baselines = self._read_json("baseline_input_registry.json")
        self.assertEqual(len(sources), 4)
        self.assertEqual(len(baselines), 3)
        self.assertTrue(all(item["status"] == "COMPLETE" for item in baselines))

    def test_interfaces_and_contracts_are_complete(self):
        inbound = self._read_json("inbound_interface_registry.json")
        outbound = self._read_json("outbound_interface_registry.json")
        contracts = self._read_json("interface_contract_registry.json")
        self.assertIn("Monitoring", {item["producer"] for item in inbound})
        self.assertIn("Trader", {item["consumer"] for item in outbound})
        self.assertTrue(all(item["failure_behavior"].startswith("fail closed") for item in contracts))

    def test_dependencies_and_temporal_conflicts_fail_closed(self):
        dependencies = self._read_json("dependency_direction_matrix.json")
        conflicts = self._read_json("temporal_conflict_resolution_registry.json")
        self.assertFalse(any(item["circular_dependency"] for item in dependencies))
        self.assertTrue(all("fail closed" in item["disposition"] for item in conflicts))

    def test_evidence_integrity_and_prohibitions_are_explicit(self):
        evidence = self._read_json("evidence_object_registry.json")
        prohibited = self._read_json("prohibited_evidence_registry.json")
        integrity = self._read_json("evidence_integrity_constitution.json")
        self.assertGreaterEqual(len(evidence), 15)
        self.assertTrue(all(item["immutable"] for item in evidence))
        self.assertTrue(all(item["disposition"] == "not proof eligible" for item in prohibited))
        self.assertIn("append-only", integrity["integrity"])

    def test_requirement_traceability_is_bidirectional(self):
        requirements = self._read_json("requirement_identity_registry.json")
        graph = self._read_json("bidirectional_traceability_graph.json")
        self.assertEqual(len(requirements), 8)
        self.assertTrue(all(item["forward_trace"] and item["reverse_trace"] for item in requirements))
        self.assertTrue(graph["nodes"])
        self.assertTrue(graph["edges"])

    def test_completion_report_ready_for_b05(self):
        completion = self._read_json("completion_report.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["ready_for"], "EXIT-DECISION-RM-001-B05")
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertTrue(all(completion["completion_checks"].values()))


if __name__ == "__main__":
    unittest.main()
