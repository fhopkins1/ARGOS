from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_MO001_CONSTITUTIONAL_HARDENING"


class PerformanceTruthMO001ConstitutionalHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "performance_truth_mo001_constitutional_hardening.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=900,
        )

    def test_all_modification_orders_are_preserved(self) -> None:
        sources = json.loads((EVIDENCE_ROOT / "source_order_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(sources), 15)
        self.assertTrue(all(row["source_available"] for row in sources))

    def test_assumptions_and_hidden_responsibilities_are_resolved(self) -> None:
        assumptions = json.loads((EVIDENCE_ROOT / "constitutional_assumption_registry.json").read_text(encoding="utf-8"))
        hidden = json.loads((EVIDENCE_ROOT / "hidden_responsibility_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(assumptions), 15)
        self.assertTrue(all(row["resolution_status"] == "CONSTITUTIONALLY_RESOLVED" for row in assumptions))
        self.assertTrue(all(not row["performance_truth_owner"] for row in hidden))

    def test_math_truth_bridge_and_adversarial_registries_exist(self) -> None:
        math_rows = json.loads((EVIDENCE_ROOT / "mathematical_governance_inventory.json").read_text(encoding="utf-8"))
        truth_rows = json.loads((EVIDENCE_ROOT / "truth_integrity_audit_registry.json").read_text(encoding="utf-8"))
        bridge_rows = json.loads((EVIDENCE_ROOT / "enterprise_bridge_dependency_registry.json").read_text(encoding="utf-8"))
        adversarial = json.loads((EVIDENCE_ROOT / "adversarial_failure_analysis_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(math_rows)
        self.assertTrue(all(row["deterministic"] for row in math_rows))
        self.assertTrue(all(not row["fabrication_allowed"] for row in truth_rows))
        self.assertTrue(all(not row["hidden_dependency_detected"] for row in bridge_rows))
        self.assertTrue(all(row["expected_response"] == "FAIL_CLOSED" for row in adversarial))

    def test_regression_preservation_passes(self) -> None:
        regressions = json.loads((EVIDENCE_ROOT / "regression_preservation_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(regressions), 5)
        self.assertTrue(all(row["disposition"] == "PASS" for row in regressions))
        for row in regressions:
            self.assertTrue((REPOSITORY_ROOT / row["stderr"]).exists())

    def test_closure_establishes_hardened_baseline(self) -> None:
        closure = json.loads((EVIDENCE_ROOT / "constitutional_hardening_closure.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(closure["hardened_baseline_status"], "ESTABLISHED")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["hardened_baseline_status"], "ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
