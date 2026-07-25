import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_ECS003_AUDIT_001"


class ExitDecisionECS003AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/exit_decision_ecs003_audit.py"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=240,
        )
        cls.returncode = completed.returncode
        cls.stderr = completed.stderr

    def _read_json(self, filename: str):
        return json.loads((OUTPUT_DIR / filename).read_text(encoding="utf-8"))

    def test_audit_runner_completes(self):
        self.assertEqual(self.returncode, 0, self.stderr)

    def test_completion_report_fails_closed(self):
        completion = self._read_json("completion_report.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["final_ecs003_verdict"], "FAIL")
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertGreater(completion["blocking_findings"], 0)

    def test_behavioral_execution_registry_contains_terminal_evidence(self):
        executions = self._read_json("behavioral_execution_registry.json")
        self.assertEqual(len(executions), 7)
        self.assertTrue(all(record["disposition"] in {"PASS", "FAIL"} for record in executions))
        self.assertTrue(all((REPOSITORY_ROOT / record["stderr"]).exists() for record in executions))

    def test_requirements_and_proofs_are_one_to_one(self):
        requirements = self._read_json("canonical_constitutional_requirement_registry.json")
        proofs = self._read_json("requirement_proof_registry.json")
        self.assertEqual(len(requirements), 14)
        self.assertEqual(len(requirements), len(proofs))
        self.assertTrue(any(record["final_disposition"] == "PROVEN" for record in requirements))
        self.assertTrue(any(record["final_disposition"] != "PROVEN" for record in requirements))

    def test_required_reports_are_present(self):
        expected = (
            "executive_audit_report.json",
            "constitutional_audit_report.json",
            "dependency_derived_implementation_inventory.json",
            "requirement_to_implementation_matrix.json",
            "evidence_sufficiency_report.json",
            "proof_coverage_matrix.json",
            "execution_derived_traceability_graph.json",
            "certification_blocker_registry.json",
            "final_ecs003_verdict.json",
        )
        for filename in expected:
            self.assertTrue((OUTPUT_DIR / filename).exists(), filename)


if __name__ == "__main__":
    unittest.main()
