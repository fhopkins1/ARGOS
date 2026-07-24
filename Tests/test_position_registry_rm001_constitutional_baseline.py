from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_CONSTITUTIONAL_BASELINE"


class PositionRegistryRM001ConstitutionalBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_constitutional_baseline.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_governance_baseline_has_no_unresolved_findings(self) -> None:
        baseline = json.loads((EVIDENCE_ROOT / "B01-004_position_registry_constitutional_governance_baseline.json").read_text(encoding="utf-8"))
        self.assertEqual(baseline["unresolved_constitutional_findings"], [])
        self.assertFalse(baseline["certification_statement"].startswith("Publication is implementation"))

    def test_object_lifecycle_baseline_is_authoritative_and_reconciled(self) -> None:
        object_baseline = json.loads((EVIDENCE_ROOT / "B02-004_constitutional_object_and_lifecycle_baseline.json").read_text(encoding="utf-8"))
        self.assertTrue(object_baseline["objects"])
        self.assertTrue(object_baseline["fields"])
        self.assertTrue(object_baseline["lifecycle"])
        self.assertTrue(object_baseline["transitions"])
        self.assertTrue(object_baseline["digest"])

    def test_completion_reports_preserve_no_implementation_certification(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_certification_issued"])

    def test_required_order_deliverables_exist(self) -> None:
        required = (
            "B01-001_constitutional_authority_registry.json",
            "B01-003_mutation_authority_registry.json",
            "B01-004_certification_authority_registry.json",
            "B02-001_position_registry_constitutional_object_registry.json",
            "B02-002_field_authority_matrix.json",
            "B02-003_state_transition_matrix.json",
            "B02-004_authoritative_reconciliation_report.json",
            "S02_series_completion_report.json",
        )
        for name in required:
            with self.subTest(name=name):
                self.assertTrue((EVIDENCE_ROOT / name).exists())


if __name__ == "__main__":
    unittest.main()
