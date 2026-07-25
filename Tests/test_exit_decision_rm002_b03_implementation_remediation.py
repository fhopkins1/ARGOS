import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B03_IMPLEMENTATION_REMEDIATION"


class ExitDecisionRM002B03ImplementationRemediationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/exit_decision_rm002_b03_implementation_remediation.py"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=120,
        )
        cls.returncode = completed.returncode
        cls.stderr = completed.stderr

    def _read_json(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_generator_completes(self):
        self.assertEqual(self.returncode, 0, self.stderr)

    def test_no_unjustified_modifications_occurred(self):
        remediation = self._read_json("implementation_remediation_registry.json")
        modifications = self._read_json("implementation_modification_registry.json")
        self.assertEqual(remediation, [])
        self.assertEqual(modifications, [])

    def test_regression_lineage_preserves_b02_evidence(self):
        regression = self._read_json("regression_execution_registry.json")
        self.assertGreaterEqual(len(regression), 15)
        self.assertTrue(all(item["execution_reused_from"] == "EXIT-DECISION-RM-002-B02" for item in regression))
        self.assertTrue(all(not item["rerun_required"] for item in regression))

    def test_candidate_is_ready_for_proof_generation(self):
        candidate = self._read_json("final_implementation_candidate_registry.json")
        readiness = self._read_json("implementation_readiness_assessment.json")
        self.assertEqual(candidate["disposition"], "READY_FOR_PROOF_GENERATION")
        self.assertEqual(readiness["disposition"], "READY_FOR_PROOF_GENERATION")
        self.assertEqual(readiness["ready_for"], "EXIT-DECISION-RM-002-B04")

    def test_completion_report(self):
        completion = self._read_json("completion_report.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["implementation_defects"], 0)
        self.assertEqual(completion["implementation_modifications"], 0)
        self.assertEqual(completion["ready_for"], "EXIT-DECISION-RM-002-B04")
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertTrue(all(completion["completion_checks"].values()))


if __name__ == "__main__":
    unittest.main()
