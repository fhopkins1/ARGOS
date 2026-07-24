from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_B01002A_S03_ENTERPRISE_GOVERNANCE_BOUNDARIES"


class PositionRegistryB01002AS03EnterpriseGovernanceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_b01002a_s03_enterprise_governance_boundaries.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_historian_boundary_answers_required_questions(self) -> None:
        boundary = json.loads((EVIDENCE_ROOT / "B01-002A-S03-002_historian_boundary_registry.json").read_text(encoding="utf-8"))
        report = json.loads((EVIDENCE_ROOT / "B01-002A-S03-002_completion_report.json").read_text(encoding="utf-8"))
        self.assertFalse(report["historian_owns_position_registry_truth"])
        self.assertFalse(report["historian_mutates_historical_records"])
        self.assertTrue(report["position_registry_transfers_historical_custody"])
        self.assertTrue(report["replay_consumes_historian_evidence"])
        self.assertIn("correction lineage", boundary["constitutional_authority"])
        self.assertIn("restores immutable evidence", report["authority_during_restoration"])

    def test_final_enterprise_governance_baseline_has_all_counterparties(self) -> None:
        baseline = json.loads((EVIDENCE_ROOT / "B01-002A-S03-004_enterprise_governance_constitutional_baseline.json").read_text(encoding="utf-8"))
        offices = {item["counterparty_office"] for item in baseline["boundaries"]}
        self.assertEqual(offices, {"Commander", "Historian", "Infrastructure", "Sentinel"})
        self.assertTrue(all(not item["custody_implies_ownership"] for item in baseline["historical_custody"]))

    def test_infrastructure_and_sentinel_do_not_own_or_mutate_position_truth(self) -> None:
        infrastructure = json.loads((EVIDENCE_ROOT / "B01-002A-S03-003_infrastructure_boundary_registry.json").read_text(encoding="utf-8"))
        sentinel = json.loads((EVIDENCE_ROOT / "B01-002A-S03-003_sentinel_boundary_registry.json").read_text(encoding="utf-8"))
        self.assertIn("not Position Registry business truth", infrastructure["ownership_boundary"])
        self.assertIn("does not mutate", infrastructure["mutation_authority"])
        self.assertIn("never Position Registry state", sentinel["ownership_boundary"])
        self.assertIn("no mutation authority", sentinel["mutation_authority"])

    def test_series_is_doctrine_only_and_unambiguous(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        verification = json.loads((EVIDENCE_ROOT / "B01-002A-S03-004_deterministic_governance_verification_report.json").read_text(encoding="utf-8"))
        self.assertFalse(completion["implementation_evaluated"])
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["certification_activity_executed"])
        self.assertFalse(verification["governance_ambiguity_remaining"])
        self.assertFalse(verification["historical_custody_ambiguity_remaining"])
        self.assertFalse(verification["enterprise_observation_ambiguity_remaining"])


if __name__ == "__main__":
    unittest.main()
