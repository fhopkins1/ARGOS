from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_B01002A_S01_TRADING_BOUNDARIES"


class PositionRegistryB01002AS01TradingBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_b01002a_s01_trading_boundaries.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_broker_boundary_answers_required_ownership_questions(self) -> None:
        broker = json.loads((EVIDENCE_ROOT / "B01-002A-S01-002_broker_boundary_registry.json").read_text(encoding="utf-8"))
        report = json.loads((EVIDENCE_ROOT / "B01-002A-S01-002_completion_report.json").read_text(encoding="utf-8"))
        self.assertFalse(report["broker_mutates_positions"])
        self.assertTrue(report["broker_owns_broker_execution_truth"])
        self.assertTrue(report["position_registry_owns_canonical_position_state"])
        self.assertEqual(broker["broker_truth_ownership"], "Broker")
        self.assertEqual(broker["position_truth_ownership"], "Position Registry")

    def test_final_baseline_has_unique_ownership_and_no_conflicts(self) -> None:
        baseline = json.loads((EVIDENCE_ROOT / "B01-002A-S01-004_trading_authority_constitutional_baseline.json").read_text(encoding="utf-8"))
        findings = json.loads((EVIDENCE_ROOT / "B01-002A-S01-004_unresolved_constitutional_findings_registry.json").read_text(encoding="utf-8"))
        ownership = baseline["ownership"]
        self.assertEqual(findings, [])
        self.assertTrue(all(not item["shared_ownership"] for item in ownership))
        self.assertEqual({item["constitutional_owner"] for item in ownership}, {"Position Registry", "Broker", "Trader", "Authorizations", "Risk"})

    def test_series_is_doctrine_only(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertFalse(completion["implementation_evaluated"])
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["certification_activity_executed"])

    def test_dependency_and_interface_registries_are_complete(self) -> None:
        matrix = json.loads((EVIDENCE_ROOT / "B01-002A-S01-004_trading_authority_interaction_matrix.json").read_text(encoding="utf-8"))
        interfaces = json.loads((EVIDENCE_ROOT / "B01-002A-S01-004_interface_authority_reconciliation_registry.json").read_text(encoding="utf-8"))
        self.assertEqual({item["counterparty_office"] for item in matrix}, {"Trader", "Broker", "Authorizations", "Risk"})
        self.assertGreaterEqual(len(interfaces), 5)
        self.assertTrue(all(item["acknowledgement_authority"] for item in interfaces))


if __name__ == "__main__":
    unittest.main()
