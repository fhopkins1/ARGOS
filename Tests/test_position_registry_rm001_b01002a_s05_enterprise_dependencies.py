from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_B01002A_S05_ENTERPRISE_DEPENDENCIES"


class PositionRegistryB01002AS05EnterpriseDependencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_b01002a_s05_enterprise_dependencies.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_dependency_population_covers_all_required_offices(self) -> None:
        registry = json.loads((EVIDENCE_ROOT / "B01-002A-S05-001_dependency_registry.json").read_text(encoding="utf-8"))
        offices = {item["counterparty_office"] for item in registry}
        self.assertEqual(
            offices,
            {
                "Trader",
                "Broker",
                "Authorizations",
                "Risk",
                "Monitoring",
                "Exit Decision",
                "Closed Position Truth",
                "Performance Truth",
                "Commander",
                "Historian",
                "Infrastructure",
                "Sentinel",
            },
        )
        self.assertEqual(len({item["dependency_id"] for item in registry}), len(registry))

    def test_s05_002_authority_direction_and_sequence_are_deterministic(self) -> None:
        authority = json.loads((EVIDENCE_ROOT / "B01-002A-S05-002_dependency_authority_registry.json").read_text(encoding="utf-8"))
        sequence = json.loads((EVIDENCE_ROOT / "B01-002A-S05-002_dependency_sequencing_registry.json").read_text(encoding="utf-8"))
        circular = json.loads((EVIDENCE_ROOT / "B01-002A-S05-002_circular_dependency_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(circular, [])
        self.assertTrue(all(item["dependency_initiation_authority"] for item in authority))
        self.assertTrue(all(item["dependency_acceptance_authority"] for item in authority))
        self.assertEqual([item["dependency_ordering"] for item in sequence], sorted(item["dependency_ordering"] for item in sequence))

    def test_failure_replay_recovery_are_defined_for_every_dependency(self) -> None:
        registry = json.loads((EVIDENCE_ROOT / "B01-002A-S05-001_dependency_registry.json").read_text(encoding="utf-8"))
        continuity = json.loads((EVIDENCE_ROOT / "B01-002A-S05-003_dependency_recovery_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(registry), len(continuity))
        self.assertTrue(all(item["failure_disposition"] == "FAIL_CLOSED_AND_RECORD_EVIDENCE" for item in continuity))
        self.assertTrue(all(item["replay_preserves_authority"] for item in continuity))
        self.assertTrue(all(item["recovery_preserves_dependency_identity"] for item in continuity))

    def test_final_baseline_is_doctrine_only_and_unambiguous(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        consistency = json.loads((EVIDENCE_ROOT / "B01-002A-S05-004_constitutional_consistency_registry.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B01-002A-S05-004_unresolved_constitutional_findings_registry.json").read_text(encoding="utf-8"))
        self.assertFalse(completion["implementation_evaluated"])
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["certification_activity_executed"])
        self.assertEqual(unresolved, [])
        self.assertEqual(consistency["circular_dependencies"], [])
        self.assertEqual(consistency["unresolved_dependency_ambiguity"], [])


if __name__ == "__main__":
    unittest.main()
