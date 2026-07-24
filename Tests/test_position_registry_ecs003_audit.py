from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_ECS003_AUDIT_001"


class PositionRegistryECS003AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_ecs003_audit.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_audit_fails_closed_with_blockers(self) -> None:
        verdict = json.loads((EVIDENCE_ROOT / "final_ecs003_verdict.json").read_text(encoding="utf-8"))
        blockers = json.loads((EVIDENCE_ROOT / "certification_blocker_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(verdict["verdict"], "FAIL")
        self.assertTrue(blockers)

    def test_clean_environment_runner_executes(self) -> None:
        clean = json.loads((EVIDENCE_ROOT / "clean_environment_reproduction_report.json").read_text(encoding="utf-8"))
        self.assertTrue(clean["succeeded"])
        self.assertFalse(clean["clean_root_git_metadata_present"])

    def test_required_deliverables_exist(self) -> None:
        required = (
            "executive_audit_report.json",
            "constitutional_audit_report.json",
            "constitutional_finding_registry.json",
            "canonical_constitutional_requirement_registry.json",
            "dependency_derived_implementation_inventory.json",
            "requirement_to_implementation_matrix.json",
            "behavioral_execution_registry.json",
            "requirement_proof_registry.json",
            "proof_reproducibility_report.json",
            "execution_derived_traceability_graph.json",
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
