from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM001_B01_CONSTITUTIONAL_BASELINE"


class MonitoringRM001B01ConstitutionalBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "monitoring_rm001_b01_constitutional_baseline.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_b01_001_purpose_authority_deliverables_are_complete(self) -> None:
        required = [
            "B01-001_monitoring_constitutional_purpose_statement.json",
            "B01-001_constitutional_mission_statement.json",
            "B01-001_constitutional_authority_registry.json",
            "B01-001_authorized_responsibility_registry.json",
            "B01-001_constitutional_limitation_registry.json",
            "B01-001_constitutional_ownership_declaration.json",
            "B01-001_governance_validation_report.json",
        ]
        for filename in required:
            self.assertTrue((EVIDENCE_ROOT / filename).exists(), filename)
        validation = json.loads((EVIDENCE_ROOT / "B01-001_governance_validation_report.json").read_text(encoding="utf-8"))
        self.assertTrue(validation["observation_isolated_from_decision_authority"])
        self.assertEqual(validation["unresolved_governance_conflicts"], [])

    def test_b01_002_enterprise_boundaries_cover_all_required_offices(self) -> None:
        boundaries = json.loads((EVIDENCE_ROOT / "B01-002_enterprise_boundary_registry.json").read_text(encoding="utf-8"))
        offices = {item["interacting_office"] for item in boundaries}
        expected = {
            "Commander",
            "Sentinel",
            "Seeker",
            "Analyst",
            "Risk",
            "Trader",
            "Broker",
            "Position Registry",
            "Authorizations",
            "Exit Decision",
            "Closed Position Truth",
            "Performance Truth",
            "Historian",
            "Infrastructure",
        }
        self.assertEqual(offices, expected)
        self.assertTrue(all(item["prohibited_mutation"] for item in boundaries))
        self.assertEqual(json.loads((EVIDENCE_ROOT / "B01-002_boundary_conflict_registry.json").read_text(encoding="utf-8")), [])

    def test_b01_003_sentinel_separation_is_non_overlapping(self) -> None:
        separation = json.loads((EVIDENCE_ROOT / "B01-003_monitoring_sentinel_boundary_constitution.json").read_text(encoding="utf-8"))
        self.assertTrue(separation["mission_overlap_prohibited"])
        self.assertEqual(separation["unknown_event_owner"], "Sentinel until constitutional governance transitions the event class.")
        self.assertTrue(separation["no_circular_dependency"])

    def test_b01_004_escalation_never_authorizes_action(self) -> None:
        governance = json.loads((EVIDENCE_ROOT / "B01-004_constitutional_governance_verification_report.json").read_text(encoding="utf-8"))
        prohibited = json.loads((EVIDENCE_ROOT / "B01-004_prohibited_action_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(governance["every_escalation_authority_has_one_owner"])
        self.assertFalse(governance["notification_transfers_authority"])
        actions = {item["prohibited_action"] for item in prohibited}
        self.assertIn("authorize trades", actions)
        self.assertIn("modify enterprise state", actions)

    def test_series_completion_preserves_no_implementation_or_certification_activity(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        series = json.loads((EVIDENCE_ROOT / "series_completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["behavioral_verification_performed"])
        self.assertFalse(completion["certification_activity_executed"])
        self.assertEqual(series["unresolved_governance_conflicts"], [])
        self.assertTrue(series["baseline_digest"])


if __name__ == "__main__":
    unittest.main()
