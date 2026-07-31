from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_MO003_ARCHITECTURE_HARDENING"


class PerformanceTruthMO003ArchitectureHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "performance_truth_mo003_architecture_hardening.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_received_source_orders_are_preserved_and_limitations_recorded(self) -> None:
        sources = json.loads((EVIDENCE_ROOT / "source_order_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(sources), 12)
        self.assertEqual(sum(1 for row in sources if row["source_available"]), 9)
        self.assertEqual(
            {row["order_id"] for row in sources if not row["source_available"]},
            {
                "PERFORMANCE-TRUTH-MO-003-008",
                "PERFORMANCE-TRUTH-MO-003-009",
                "PERFORMANCE-TRUTH-MO-003-010",
            },
        )

    def test_responsibilities_have_single_classification_and_disposition(self) -> None:
        responsibilities = json.loads((EVIDENCE_ROOT / "complete_responsibility_register.json").read_text(encoding="utf-8"))
        self.assertTrue(responsibilities)
        self.assertTrue(all(row["classification"] for row in responsibilities))
        self.assertTrue(all(row["final_disposition"] for row in responsibilities))
        self.assertFalse(json.loads((EVIDENCE_ROOT / "duplicated_responsibility_register.json").read_text(encoding="utf-8")))
        self.assertFalse(json.loads((EVIDENCE_ROOT / "missing_responsibility_register.json").read_text(encoding="utf-8")))

    def test_ownership_interface_and_dependency_closure_are_singular(self) -> None:
        objects = json.loads((EVIDENCE_ROOT / "final_canonical_object_ownership_register.json").read_text(encoding="utf-8"))
        interfaces = json.loads((EVIDENCE_ROOT / "final_interface_inventory.json").read_text(encoding="utf-8"))
        graph = json.loads((EVIDENCE_ROOT / "final_dependency_graph.json").read_text(encoding="utf-8"))
        self.assertTrue(all(row["ownership"] == "SINGULAR" for row in objects))
        self.assertTrue(all(row["minimality_disposition"] == "RETAIN_MINIMAL" for row in interfaces))
        self.assertFalse(graph["circular_responsibility_detected"])
        self.assertFalse(graph["bridge_overreach_detected"])

    def test_closure_findings_are_non_blocking(self) -> None:
        findings = json.loads((EVIDENCE_ROOT / "closure_findings_register.json").read_text(encoding="utf-8"))
        risks = json.loads((EVIDENCE_ROOT / "residual_architectural_risk_register.json").read_text(encoding="utf-8"))
        self.assertTrue(findings)
        self.assertTrue(all(not row["blocking"] for row in findings))
        self.assertTrue(all(row["accepted"] for row in risks))

    def test_completion_establishes_hardened_baseline(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        baseline = json.loads((EVIDENCE_ROOT / "hardened_baseline_record.json").read_text(encoding="utf-8"))
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["completion_decision"], "PASS")
        self.assertEqual(baseline["closure_determination"], "PASS")
        self.assertEqual(completion["hardened_baseline_id"], baseline["baseline_id"])


if __name__ == "__main__":
    unittest.main()
