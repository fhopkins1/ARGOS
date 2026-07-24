from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "BROKER_RM002A_006_BEHAVIORAL_COMPLETION"


class BrokerRm002a006BehavioralCompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "broker_rm002a_006_behavioral_completion.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_every_new_behavior_has_passing_verification(self) -> None:
        verification = json.loads((EVIDENCE_ROOT / "behavioral_verification_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(verification), 18)
        self.assertTrue(all(item["disposition"] == "VERIFIED_PASS" for item in verification))
        self.assertEqual(len({item["originating_finding_id"] for item in verification}), 18)

    def test_completion_has_no_remaining_findings_or_forbidden_certification_work(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "behavioral_completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["remaining_findings"], 0)
        self.assertFalse(completion["authoritative_proof_baseline_regenerated"])
        self.assertFalse(completion["repository_wide_certification_executed"])
        self.assertFalse(completion["certification_readiness_executed"])
        self.assertFalse(completion["ecs_003_verdict_issued"])

    def test_required_deliverables_exist(self) -> None:
        required = (
            "behavioral_implementation_registry.json",
            "behavioral_capability_completion_registry.json",
            "implementation_modification_registry.json",
            "implementation_to_finding_traceability_matrix.json",
            "behavioral_verification_registry.json",
            "behavioral_regression_registry.json",
            "implementation_regression_registry.json",
            "remaining_finding_registry.json",
            "behavioral_completion_report.json",
        )
        for name in required:
            with self.subTest(name=name):
                self.assertTrue((EVIDENCE_ROOT / name).exists())


if __name__ == "__main__":
    unittest.main()
