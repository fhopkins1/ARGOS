from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S05_BEHAVIORAL_VERIFICATION"


class PositionRegistryRM001S05BehavioralVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_s05_behavioral_verification.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_b05_001_population_is_frozen_and_bounded(self) -> None:
        obligations = json.loads((EVIDENCE_ROOT / "B05-001_behavioral_obligation_registry.json").read_text(encoding="utf-8"))
        gaps = json.loads((EVIDENCE_ROOT / "B05-001_verification_gap_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(obligations), 30)
        self.assertEqual({item["bounded_execution_group"] for item in obligations}, {"B05-002", "B05-003"})
        self.assertEqual(gaps, [])

    def test_b05_002_executes_lifecycle_quantity_and_cost_basis_population(self) -> None:
        evidence = json.loads((EVIDENCE_ROOT / "B05-002_execution_evidence_registry.json").read_text(encoding="utf-8"))
        report = json.loads((EVIDENCE_ROOT / "B05-002_completion_report.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(evidence), 8)
        self.assertTrue(all(item["disposition"] in {"PASS", "FAIL", "ERROR"} for item in evidence))
        self.assertEqual(report["executions"], len(evidence))

    def test_b05_003_executes_persistence_replay_recovery_and_reconciliation_population(self) -> None:
        evidence = json.loads((EVIDENCE_ROOT / "B05-003_execution_evidence_registry.json").read_text(encoding="utf-8"))
        findings = json.loads((EVIDENCE_ROOT / "B05-003_behavioral_findings_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(evidence), 3)
        self.assertTrue(all(item["evidence_digest"] for item in evidence))
        self.assertTrue(any("replay" in item["finding"].lower() or "correction" in item["finding"].lower() for item in findings))

    def test_completion_report_is_honest_and_non_certifying(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertTrue(completion["bounded_population_executed"])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["repository_wide_verification_executed"])
        self.assertFalse(completion["certification_conclusion_issued"])
        self.assertGreaterEqual(completion["executions"], completion["pass"])


if __name__ == "__main__":
    unittest.main()
