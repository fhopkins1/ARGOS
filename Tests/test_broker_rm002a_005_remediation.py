from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "BROKER_RM002A_005_REMEDIATION"


class BrokerRm002a005RemediationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "broker_rm002a_005_remediation.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_every_originating_finding_has_one_traceable_disposition(self) -> None:
        matrix = json.loads((EVIDENCE_ROOT / "finding_to_remediation_matrix.json").read_text(encoding="utf-8"))
        finding_ids = [item["originating_finding_id"] for item in matrix]
        remediation_ids = [item["remediation_id"] for item in matrix]
        self.assertEqual(len(finding_ids), 19)
        self.assertEqual(len(finding_ids), len(set(finding_ids)))
        self.assertEqual(len(remediation_ids), len(set(remediation_ids)))
        self.assertTrue(all(item["traceability_preserved"] for item in matrix))

    def test_duplicate_defect_and_verifier_fixture_gaps_are_remediated(self) -> None:
        implementation = json.loads((EVIDENCE_ROOT / "implementation_remediation_registry.json").read_text(encoding="utf-8"))
        verifier = json.loads((EVIDENCE_ROOT / "verifier_remediation_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(implementation), 1)
        self.assertEqual(implementation[0]["originating_finding_id"], "BROKER-RM002A-004-FINDING-003")
        self.assertEqual(implementation[0]["regression_disposition"], "REGRESSION_PASS")
        self.assertEqual(len(verifier), 4)
        self.assertTrue(all(item["regression_disposition"] == "REGRESSION_PASS" for item in verifier))

    def test_completion_does_not_regenerate_proof_or_certification_readiness(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "remediation_completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(completion["status"], "COMPLETE_WITH_FORMAL_DISPOSITIONS")
        self.assertFalse(completion["authoritative_proof_baseline_regenerated"])
        self.assertFalse(completion["repository_wide_certification_executed"])
        self.assertFalse(completion["certification_readiness_executed"])
        self.assertEqual(completion["formal_dispositions"], 14)


if __name__ == "__main__":
    unittest.main()
