from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "BROKER_RM002A_008_REPRODUCIBILITY"


class BrokerRm002a008ReproducibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "broker_rm002a_008_reproducibility.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_clean_environment_reproduces_without_git_metadata(self) -> None:
        report = json.loads((EVIDENCE_ROOT / "clean_environment_execution_report.json").read_text(encoding="utf-8"))
        self.assertTrue(report["succeeded"])
        self.assertFalse(report["clean_root_git_metadata_present"])
        self.assertTrue(report["portable_repository_digest"])

    def test_canonical_proofs_have_no_blockers(self) -> None:
        verdict = json.loads((EVIDENCE_ROOT / "final_ecs003_verdict.json").read_text(encoding="utf-8"))
        blockers = json.loads((EVIDENCE_ROOT / "certification_blocker_registry.json").read_text(encoding="utf-8"))
        proofs = json.loads((EVIDENCE_ROOT / "regenerated_authoritative_proof_baseline.json").read_text(encoding="utf-8"))["proofs"]
        self.assertEqual(verdict["verdict"], "UNCONDITIONAL_PASS")
        self.assertEqual(blockers, [])
        self.assertEqual(len(proofs), 6)
        self.assertTrue(all(item["disposition"] == "PROVEN" for item in proofs))
        self.assertTrue(all(item["proof_reproducible"] for item in proofs))

    def test_requirement_identity_is_canonical_not_remediation_authoritative(self) -> None:
        requirements = json.loads((EVIDENCE_ROOT / "canonical_constitutional_requirement_registry.json").read_text(encoding="utf-8"))
        mapping = json.loads((EVIDENCE_ROOT / "remediation_to_constitutional_mapping_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(all(item["requirement_id"].startswith("BROKER-CONST-REQ-") for item in requirements))
        self.assertTrue(all(not item["remediation_identity_authoritative"] for item in mapping))

    def test_required_deliverables_exist(self) -> None:
        required = (
            "certification_reproducibility_report.json",
            "clean_environment_execution_report.json",
            "canonical_constitutional_requirement_registry.json",
            "constitutional_requirement_identity_registry.json",
            "implementation_obligation_registry.json",
            "remediation_to_constitutional_mapping_registry.json",
            "regenerated_authoritative_proof_baseline.json",
            "regenerated_proof_traceability_graph.json",
            "repository_wide_verifier_inventory.json",
            "repository_wide_execution_registry.json",
            "repository_wide_coverage_report.json",
            "proof_reproducibility_report.json",
            "certification_blocker_registry.json",
            "final_reconciliation_registry.json",
            "final_ecs003_certification_report.json",
            "final_ecs003_verdict.json",
            "completion_report.json",
            "REPRODUCE.md",
        )
        for name in required:
            with self.subTest(name=name):
                self.assertTrue((EVIDENCE_ROOT / name).exists())


if __name__ == "__main__":
    unittest.main()
