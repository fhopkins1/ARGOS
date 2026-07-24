from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "BROKER_RM002A_004_GAP_CLOSURE"
RAW_EVIDENCE = EVIDENCE_ROOT / "raw_execution_evidence" / "broker_gap_closure_execution.json"
ALLOWED_DISPOSITIONS = {
    "VERIFIED_PASS",
    "VERIFIED_FAIL",
    "VERIFIER_ERROR",
    "FIXTURE_ERROR",
    "ENVIRONMENT_ERROR",
    "BLOCKED_BY_IMPLEMENTATION",
    "BLOCKED_BY_EXTERNAL_DEPENDENCY",
    "NOT_APPLICABLE",
    "UNRESOLVED_CONTRADICTION",
}


class BrokerRm002a004GapClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPOSITORY_ROOT / "src")
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "broker_rm002a_004_gap_closure.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_every_gap_has_allowed_terminal_disposition(self) -> None:
        payload = json.loads(RAW_EVIDENCE.read_text(encoding="utf-8"))
        results = payload["results"]
        self.assertEqual(payload["candidate"], "BROKER-RM-002A-004")
        self.assertEqual(len(results), payload["summary"]["total"])
        self.assertTrue(results)
        self.assertTrue(all(item["disposition"] in ALLOWED_DISPOSITIONS for item in results))
        self.assertNotIn("INTERRUPTED", {item["disposition"] for item in results})
        self.assertNotIn("UNKNOWN", {item["disposition"] for item in results})
        self.assertNotIn("NOT EXECUTED", {item["disposition"] for item in results})

    def test_required_deliverables_are_materialized(self) -> None:
        required = (
            "execution_registry.json",
            "execution_to_requirement_map.json",
            "execution_to_proof_object_map.json",
            "behavioral_findings_registry.json",
            "dependency_status_registry.json",
            "checkpoint_registry.json",
            "completion_report.json",
            "gap_closure_report.json",
            "README.md",
        )
        for name in required:
            with self.subTest(name=name):
                self.assertTrue((EVIDENCE_ROOT / name).exists())

    def test_no_proof_recalculation_or_certification_readiness(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertFalse(completion["proof_objects_recalculated"])
        self.assertFalse(completion["certification_readiness_executed"])
        self.assertFalse(completion["repository_wide_verification_executed"])
        self.assertEqual(completion["status"], "COMPLETE_WITH_FINDINGS")


if __name__ == "__main__":
    unittest.main()
