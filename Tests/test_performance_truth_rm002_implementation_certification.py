from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_RM002_IMPLEMENTATION_CERTIFICATION"


class PerformanceTruthRM002ImplementationCertificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        subprocess.run(
            [
                sys.executable,
                str(REPOSITORY_ROOT / "Scripts" / "performance_truth_rm002_implementation_certification.py"),
            ],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )

    def test_b01_repository_inventory_and_dependencies_exist(self) -> None:
        inventory = json.loads((EVIDENCE_ROOT / "repository_inventory.json").read_text(encoding="utf-8"))
        dependencies = json.loads((EVIDENCE_ROOT / "dependency_inventory.json").read_text(encoding="utf-8"))
        paths = {row["path"] for row in inventory}
        self.assertIn("src/argos/control_panel/performance_truth_engine.py", paths)
        self.assertIn("src/argos/historian/performance.py", paths)
        self.assertTrue(dependencies)

    def test_b02_canonical_object_verification_is_terminal(self) -> None:
        objects = json.loads((EVIDENCE_ROOT / "canonical_object_verification_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(objects), 12)
        self.assertTrue(all(row["implementation_status"] in {"PASS", "FAIL"} for row in objects))
        self.assertTrue(any(row["implementation_status"] == "PASS" for row in objects))

    def test_b03_behavioral_execution_has_raw_evidence(self) -> None:
        executions = json.loads((EVIDENCE_ROOT / "behavioral_execution_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(executions), 4)
        self.assertTrue(all(row["disposition"] in {"PASS", "FAIL", "TIMEOUT"} for row in executions))
        for row in executions:
            evidence = row.get("stdout") or row.get("evidence")
            self.assertTrue(evidence, row["execution_id"])
            self.assertTrue((REPOSITORY_ROOT / evidence).exists(), evidence)

    def test_b05_traceability_and_proof_are_generated(self) -> None:
        evidence = json.loads((EVIDENCE_ROOT / "evidence_registry.json").read_text(encoding="utf-8"))
        traceability = json.loads((EVIDENCE_ROOT / "traceability_registry.json").read_text(encoding="utf-8"))
        proof = json.loads((EVIDENCE_ROOT / "proof_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(evidence)
        self.assertTrue(traceability)
        self.assertGreater(len(proof), len(evidence))

    def test_b09_final_report_and_verdict_are_reproducible(self) -> None:
        final = json.loads((EVIDENCE_ROOT / "final_independent_implementation_certification_report.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertIn(final["verdict"], {"UNCONDITIONAL_PASS", "CONDITIONAL_FAIL"})
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["repository_wide_certification_executed"])


if __name__ == "__main__":
    unittest.main()
