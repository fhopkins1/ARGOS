import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B02_BEHAVIORAL_VERIFICATION"


class ExitDecisionRM002B02BehavioralVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/exit_decision_rm002_b02_behavioral_verification.py"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=240,
        )
        cls.returncode = completed.returncode
        cls.stderr = completed.stderr

    def _read_json(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_generator_completes(self):
        self.assertEqual(self.returncode, 0, self.stderr)

    def test_behavioral_executions_are_terminal(self):
        executions = self._read_json("behavioral_execution_registry.json")
        self.assertGreaterEqual(len(executions), 10)
        self.assertTrue(all(item["disposition"] in {"PASS", "FAIL", "TIMEOUT"} for item in executions))
        self.assertTrue(all(item["stdout"] and item["stderr"] for item in executions))

    def test_core_domain_registries_exist(self):
        self.assertTrue(self._read_json("admissibility_execution_registry.json"))
        self.assertTrue(self._read_json("evaluation_execution_registry.json"))
        self.assertTrue(self._read_json("decision_execution_registry.json"))
        self.assertTrue(self._read_json("interface_execution_registry.json"))
        self.assertTrue(self._read_json("lifecycle_execution_registry.json"))

    def test_every_requirement_has_behavioral_disposition(self):
        dispositions = self._read_json("requirement_behavioral_disposition_registry.json")
        self.assertEqual(len(dispositions), 94)
        self.assertTrue(all(item["behavioral_disposition"] for item in dispositions))

    def test_findings_are_classified_and_readiness_points_to_b03(self):
        findings = self._read_json("behavioral_findings_registry.json")
        readiness = self._read_json("behavioral_readiness_assessment.json")
        self.assertTrue(all(item["classification"] for item in findings))
        self.assertEqual(readiness["ready_for"], "EXIT-DECISION-RM-002-B03")

    def test_completion_report(self):
        completion = self._read_json("completion_report.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["ready_for"], "EXIT-DECISION-RM-002-B03")
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertTrue(all(completion["completion_checks"].values()))


if __name__ == "__main__":
    unittest.main()
