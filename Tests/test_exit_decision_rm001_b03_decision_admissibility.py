import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B03_DECISION_ADMISSIBILITY"


class ExitDecisionRM001B03DecisionAdmissibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/exit_decision_rm001_b03_decision_admissibility.py"],
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

    def test_sources_and_admissibility_gates_are_complete(self):
        sources = self._read_json("source_order_registry.json")
        gates = self._read_json("decision_admissibility_constitution.json")
        self.assertEqual(len(sources), 4)
        self.assertGreaterEqual(len(gates), 10)
        self.assertTrue(all(item["evidence_required"] for item in gates))
        self.assertTrue(all(item["synthetic_completion_prohibited"] for item in gates))

    def test_mandatory_rejections_cover_core_failures(self):
        rejections = self._read_json("mandatory_rejection_registry.json")
        text = " ".join(item["condition"] for item in rejections)
        self.assertIn("missing position truth", text)
        self.assertIn("expired authorization", text)
        self.assertIn("revoked authorization", text)
        self.assertTrue(all(item["disposition"] == "REJECT_OR_FAIL_CLOSED" for item in rejections))

    def test_recommendations_do_not_execute(self):
        outputs = self._read_json("recommendation_constitution.json")
        self.assertTrue(all(item["execution_authority"] == "NONE" for item in outputs))
        actionable = [item for item in outputs if item["requires_authorization_before_execution"]]
        self.assertTrue(actionable)

    def test_authorization_and_execution_boundaries_are_explicit(self):
        boundaries = self._read_json("authority_boundary_registry.json")
        prohibited = self._read_json("prohibited_execution_registry.json")
        offices = {item["office"] for item in boundaries}
        self.assertIn("Authorizations", offices)
        self.assertIn("Trader", offices)
        self.assertIn("Broker", offices)
        self.assertTrue(any("submit broker orders" in item["prohibited_behavior"] for item in prohibited))

    def test_emergency_and_exception_governance_is_limited_and_fail_closed(self):
        emergency = self._read_json("emergency_condition_registry.json")
        exceptions = self._read_json("exception_governance_registry.json")
        self.assertTrue(all("never transfers" in item["override_limit"] for item in emergency))
        self.assertTrue(all("fail closed" in item["disposition"] for item in exceptions))

    def test_completion_report_ready_for_b04(self):
        completion = self._read_json("completion_report.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["ready_for"], "EXIT-DECISION-RM-001-B04")
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertTrue(all(completion["completion_checks"].values()))


if __name__ == "__main__":
    unittest.main()
