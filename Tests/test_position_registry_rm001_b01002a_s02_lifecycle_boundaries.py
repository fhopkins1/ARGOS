from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_B01002A_S02_LIFECYCLE_BOUNDARIES"


class PositionRegistryB01002AS02LifecycleBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_b01002a_s02_lifecycle_boundaries.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_exit_decision_boundary_answers_required_questions(self) -> None:
        boundary = json.loads((EVIDENCE_ROOT / "B01-002A-S02-002_exit_decision_boundary_registry.json").read_text(encoding="utf-8"))
        lifecycle = json.loads((EVIDENCE_ROOT / "B01-002A-S02-002_lifecycle_authority_registry.json").read_text(encoding="utf-8"))
        report = json.loads((EVIDENCE_ROOT / "B01-002A-S02-002_completion_report.json").read_text(encoding="utf-8"))
        self.assertFalse(report["exit_decision_owns_positions"])
        self.assertFalse(report["exit_decision_mutates_positions"])
        self.assertTrue(report["exit_decision_authorizes_closure"])
        self.assertTrue(report["position_registry_executes_authorized_lifecycle_transitions"])
        self.assertEqual(lifecycle["canonical_lifecycle_execution"], "Position Registry")
        self.assertIn("Position Registry", boundary["lifecycle_authority"])

    def test_final_lifecycle_baseline_has_all_counterparties(self) -> None:
        baseline = json.loads((EVIDENCE_ROOT / "B01-002A-S02-004_position_lifecycle_constitutional_baseline.json").read_text(encoding="utf-8"))
        offices = {item["counterparty_office"] for item in baseline["boundaries"]}
        self.assertEqual(offices, {"Monitoring", "Exit Decision", "Closed Position Truth", "Performance Truth"})
        self.assertEqual(baseline["historical_transfer"]["receiving_owner"], "Closed Position Truth")

    def test_truth_ownership_is_unique_and_complete(self) -> None:
        truth = json.loads((EVIDENCE_ROOT / "B01-002A-S02-004_truth_ownership_reconciliation_registry.json").read_text(encoding="utf-8"))
        classes = {item["truth_class"] for item in truth}
        self.assertIn("canonical_active_position_truth", classes)
        self.assertIn("exit_authorization_truth", classes)
        self.assertIn("immutable_closed_position_truth", classes)
        self.assertIn("historical_performance_truth", classes)
        self.assertTrue(all(item["constitutional_owner"] for item in truth))

    def test_series_is_doctrine_only_and_unambiguous(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        verification = json.loads((EVIDENCE_ROOT / "B01-002A-S02-004_deterministic_boundary_verification_report.json").read_text(encoding="utf-8"))
        self.assertFalse(completion["implementation_evaluated"])
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["certification_activity_executed"])
        self.assertFalse(verification["ownership_ambiguity_remaining"])
        self.assertFalse(verification["lifecycle_ambiguity_remaining"])
        self.assertFalse(verification["truth_ownership_ambiguity_remaining"])


if __name__ == "__main__":
    unittest.main()
