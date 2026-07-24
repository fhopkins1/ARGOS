from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S06_FINAL_CERTIFICATION"


class PositionRegistryRM001S06FinalCertificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_s06_final_certification.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_b06_001_proofs_are_derived_from_s05_execution_evidence(self) -> None:
        evidence = json.loads((EVIDENCE_ROOT / "B06-001_evidence_inventory.json").read_text(encoding="utf-8"))
        proofs = json.loads((EVIDENCE_ROOT / "B06-001_requirement_proof_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(evidence), 10)
        self.assertGreaterEqual(len(proofs), 30)
        self.assertTrue(all(item["provenance"]["originating_execution"] for item in evidence))
        self.assertTrue(all(item["execution_identity"] for item in proofs))

    def test_b06_002_traceability_and_coverage_are_present(self) -> None:
        traceability = json.loads((EVIDENCE_ROOT / "B06-002_execution_derived_traceability_graph.json").read_text(encoding="utf-8"))
        coverage = json.loads((EVIDENCE_ROOT / "B06-002_proof_coverage_matrix.json").read_text(encoding="utf-8"))
        orphans = json.loads((EVIDENCE_ROOT / "B06-002_orphan_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(traceability)
        self.assertIn("requirements", coverage)
        self.assertEqual(orphans["orphan_requirements"], [])

    def test_b06_003_readiness_is_blocked_by_open_findings(self) -> None:
        readiness = json.loads((EVIDENCE_ROOT / "B06-003_certification_readiness_report.json").read_text(encoding="utf-8"))
        blockers = json.loads((EVIDENCE_ROOT / "B06-003_certification_blocker_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(readiness["readiness"], "NOT_READY_BLOCKED")
        self.assertGreater(len(blockers), 0)
        self.assertFalse(readiness["certification_verdict_issued"])

    def test_b06_004_issues_single_fail_verdict(self) -> None:
        verdict = json.loads((EVIDENCE_ROOT / "B06-004_final_ecs003_verdict.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(verdict["verdict"], "FAIL")
        self.assertFalse(verdict["conditional_pass_authorized"])
        self.assertEqual(completion["final_verdict"], "FAIL")
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])


if __name__ == "__main__":
    unittest.main()
