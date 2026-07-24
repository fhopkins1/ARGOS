from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM002A_FINAL_CLOSURE"


class PositionRegistryRM002AFinalClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm002a_final_closure.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_s05_005_regenerates_requirement_dispositions_without_behavioral_execution(self) -> None:
        disposition = json.loads((EVIDENCE_ROOT / "S05-005_regenerated_requirement_disposition_registry.json").read_text(encoding="utf-8"))
        report = json.loads((EVIDENCE_ROOT / "S05-005_completion_report.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(disposition), 5)
        self.assertTrue(all(item["requirement_id"] for item in disposition))
        self.assertTrue(all(item["proof_object"] for item in disposition))
        self.assertFalse(report["implementation_modified"])
        self.assertFalse(report["behavioral_verification_executed"])

    def test_s06_001_clean_execution_and_single_verdict_are_present(self) -> None:
        clean = json.loads((EVIDENCE_ROOT / "S06-001_clean_environment_execution_report.json").read_text(encoding="utf-8"))
        verdict = json.loads((EVIDENCE_ROOT / "S06-001_final_certification_verdict.json").read_text(encoding="utf-8"))
        self.assertTrue(clean["executions"])
        self.assertTrue(all(item["terminal_disposition"] == "PASS" for item in clean["executions"]))
        self.assertTrue(verdict["issued_exactly_one_verdict"])
        self.assertIn(verdict["verdict"], verdict["allowed_verdicts"])

    def test_traceability_and_proof_are_complete_for_affected_requirements(self) -> None:
        proof = json.loads((EVIDENCE_ROOT / "S06-001_regenerated_certification_proof.json").read_text(encoding="utf-8"))
        traceability = json.loads((EVIDENCE_ROOT / "S06-001_regenerated_certification_traceability.json").read_text(encoding="utf-8"))
        self.assertEqual(len(proof), len(traceability))
        self.assertTrue(all(item["proof_disposition"] == "PASS" for item in proof))
        self.assertTrue(all(item["forward_status"] == "COMPLETE" and item["reverse_status"] == "COMPLETE" for item in traceability))

    def test_completion_reports_unconditional_pass_without_doctrine_change(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(completion["final_verdict"], "UNCONDITIONAL_PASS")
        self.assertTrue(completion["implementation_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["repository_wide_verification_executed"])


if __name__ == "__main__":
    unittest.main()
