from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S02_OBJECT_LIFECYCLE"


class PositionRegistryRM001S02ObjectLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_s02_object_lifecycle.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_b02_001_objects_are_complete(self) -> None:
        objects = json.loads((EVIDENCE_ROOT / "B02-001_canonical_object_registry.json").read_text(encoding="utf-8"))
        conflicts = json.loads((EVIDENCE_ROOT / "B02-001_object_conflict_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(objects), 18)
        self.assertTrue(all(item["object_id"] for item in objects))
        self.assertEqual(conflicts, [])

    def test_b02_002_quantity_cost_and_temporal_rules_exist(self) -> None:
        quantity = json.loads((EVIDENCE_ROOT / "B02-002_quantity_doctrine_registry.json").read_text(encoding="utf-8"))
        cost = json.loads((EVIDENCE_ROOT / "B02-002_cost_basis_doctrine_registry.json").read_text(encoding="utf-8"))
        temporal = json.loads((EVIDENCE_ROOT / "B02-002_temporal_doctrine_registry.json").read_text(encoding="utf-8"))
        ambiguity = json.loads((EVIDENCE_ROOT / "B02-002_lifecycle_ambiguity_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(quantity)
        self.assertTrue(cost)
        self.assertTrue(temporal)
        self.assertEqual(ambiguity, [])

    def test_b02_003_historical_integrity_prohibits_fabrication(self) -> None:
        replay = json.loads((EVIDENCE_ROOT / "B02-003_replay_constitution.json").read_text(encoding="utf-8"))
        supersession = json.loads((EVIDENCE_ROOT / "B02-003_supersession_constitution.json").read_text(encoding="utf-8"))
        self.assertTrue(replay["identity_preservation"])
        self.assertTrue(replay["fabrication_prohibited"])
        self.assertTrue(supersession["superseded_object_preserved"])

    def test_b02_004_baseline_has_no_unresolved_findings_or_certification(self) -> None:
        baseline = json.loads((EVIDENCE_ROOT / "B02-004_authoritative_position_registry_object_and_lifecycle_baseline.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(baseline["unresolved_constitutional_finding_registry"], [])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_certification_issued"])


if __name__ == "__main__":
    unittest.main()
