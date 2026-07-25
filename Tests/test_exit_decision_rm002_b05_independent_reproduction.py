import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B05_INDEPENDENT_REPRODUCTION"


class ExitDecisionRM002B05IndependentReproductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/exit_decision_rm002_b05_independent_reproduction.py"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=300,
        )
        cls.returncode = completed.returncode
        cls.stderr = completed.stderr

    def _read_json(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_generator_completes(self):
        self.assertEqual(self.returncode, 0, self.stderr)

    def test_repository_and_environment_are_reproduced_without_git_dependency(self):
        repo = self._read_json("repository_reproduction_registry.json")
        env = self._read_json("environment_reproduction_registry.json")
        self.assertTrue(repo["critical_files_present"])
        self.assertFalse(env["uses_git_history_for_reproduction"])
        self.assertFalse(env["uses_external_services"])

    def test_discovery_behavior_and_proof_match_authoritative_candidate(self):
        discovery = self._read_json("discovery_comparison_report.json")
        proof = self._read_json("proof_comparison_report.json")
        self.assertEqual(discovery["implementation"]["mismatches"], [])
        self.assertEqual(discovery["verifiers"]["mismatches"], [])
        self.assertEqual(discovery["fixtures"]["mismatches"], [])
        self.assertEqual(proof["mismatches"], [])

    def test_behavioral_reproduction_executes_and_passes(self):
        executions = self._read_json("reproduced_behavioral_execution_registry.json")
        self.assertGreaterEqual(len(executions), 15)
        self.assertTrue(all(item["disposition"] == "PASS" for item in executions))

    def test_final_reproduction_assessment(self):
        assessment = self._read_json("final_reproduction_assessment.json")
        self.assertEqual(assessment["assessment"], "REPRODUCIBLE")
        self.assertTrue(assessment["authorizes_final_ecs003_verdict"])

    def test_completion_report(self):
        completion = self._read_json("completion_report.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["assessment"], "REPRODUCIBLE")
        self.assertEqual(completion["certification_blockers"], 0)
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertTrue(all(completion["completion_checks"].values()))


if __name__ == "__main__":
    unittest.main()
