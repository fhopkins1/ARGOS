from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "BROKER_RM002A_007_FINAL_CERTIFICATION"


class BrokerRm002a007FinalCertificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "broker_rm002a_007_final_certification.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_final_verdict_is_unconditional_pass_without_blockers(self) -> None:
        verdict = json.loads((EVIDENCE_ROOT / "final_ecs003_verdict.json").read_text(encoding="utf-8"))
        blockers = json.loads((EVIDENCE_ROOT / "certification_blocker_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(verdict["verdict"], "UNCONDITIONAL_PASS")
        self.assertEqual(blockers, [])

    def test_every_requirement_proof_is_proven_and_reproducible(self) -> None:
        proofs = json.loads((EVIDENCE_ROOT / "regenerated_authoritative_requirement_proof_registry.json").read_text(encoding="utf-8"))
        dispositions = json.loads((EVIDENCE_ROOT / "requirement_proof_disposition_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(proofs)
        self.assertTrue(all(item["disposition"] == "PROVEN" for item in proofs))
        self.assertTrue(all(item["reproducible"] for item in proofs))
        self.assertTrue(all(item["disposition"] == "PROVEN" for item in dispositions))

    def test_required_completion_artifacts_exist(self) -> None:
        required = (
            "regenerated_authoritative_evidence_registry.json",
            "regenerated_authoritative_requirement_proof_registry.json",
            "regenerated_implementation_proof_registry.json",
            "regenerated_verifier_proof_registry.json",
            "regenerated_execution_derived_traceability_graph.json",
            "proof_supersession_registry.json",
            "final_candidate_manifest.json",
            "candidate_reconciliation_registry.json",
            "certification_readiness_report.json",
            "independent_audit_execution_registry.json",
            "final_ecs003_certification_report.json",
            "final_ecs003_verdict.json",
            "completion_report.json",
        )
        for name in required:
            with self.subTest(name=name):
                self.assertTrue((EVIDENCE_ROOT / name).exists())


if __name__ == "__main__":
    unittest.main()
