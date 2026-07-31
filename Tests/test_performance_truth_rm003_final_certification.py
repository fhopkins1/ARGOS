from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_RM003_FINAL_CERTIFICATION"


class PerformanceTruthRM003FinalCertificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "performance_truth_rm003_final_certification.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=600,
        )

    def test_constitutional_compliance_passes_from_rm001(self) -> None:
        compliance = json.loads((EVIDENCE_ROOT / "constitutional_compliance_verification.json").read_text(encoding="utf-8"))
        self.assertEqual(compliance["disposition"], "PASS")
        self.assertEqual(compliance["rm001_status"], "COMPLETE")
        self.assertFalse(compliance["blocking_findings"])

    def test_enterprise_integration_covers_required_offices(self) -> None:
        integrations = json.loads((EVIDENCE_ROOT / "enterprise_integration_registry.json").read_text(encoding="utf-8"))
        offices = {row["office"] for row in integrations}
        self.assertEqual(len(offices), 12)
        self.assertTrue(all(row["disposition"] == "PASS" for row in integrations))

    def test_regression_executions_have_terminal_evidence(self) -> None:
        report = json.loads((EVIDENCE_ROOT / "enterprise_regression_certification_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["disposition"], "PASS")
        for row in report["executions"]:
            self.assertEqual(row["disposition"], "PASS")
            self.assertTrue((REPOSITORY_ROOT / row["stderr"]).exists())

    def test_evidence_finalization_includes_rm001_and_rm002(self) -> None:
        finalization = json.loads((EVIDENCE_ROOT / "certification_evidence_finalization_report.json").read_text(encoding="utf-8"))
        self.assertEqual(finalization["disposition"], "PASS")
        self.assertTrue(finalization["rm001_evidence_present"])
        self.assertTrue(finalization["rm002_evidence_present"])
        self.assertTrue(finalization["all_evidence_hashed"])

    def test_freeze_and_operational_transition_are_authorized(self) -> None:
        freeze = json.loads((EVIDENCE_ROOT / "constitutional_freeze_baseline.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(freeze["freeze_status"], "FROZEN")
        self.assertEqual(freeze["operational_authorization"], "AUTHORIZED")
        self.assertEqual(completion["final_verdict"], "CERTIFIED_AND_FROZEN")


if __name__ == "__main__":
    unittest.main()
