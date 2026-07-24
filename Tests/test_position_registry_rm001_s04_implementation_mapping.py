from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S04_IMPLEMENTATION_MAPPING"


class PositionRegistryRM001S04ImplementationMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_s04_implementation_mapping.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_b04_001_inventory_has_identity_classification_and_dependency_evidence(self) -> None:
        inventory = json.loads((EVIDENCE_ROOT / "B04-001_implementation_inventory.json").read_text(encoding="utf-8"))
        deficiencies = json.loads((EVIDENCE_ROOT / "B04-001_remaining_implementation_discovery_deficiency_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(inventory), 10)
        self.assertEqual(len({item["implementation_id"] for item in inventory}), len(inventory))
        self.assertTrue(all(item["implementation_classification"] for item in inventory))
        self.assertTrue(all(item["objective_dependency_evidence"] for item in inventory))
        self.assertEqual(deficiencies, [])

    def test_b04_002_maps_every_requirement_without_gaps(self) -> None:
        requirements = json.loads((REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S03_INTERFACE_EVIDENCE_TRACEABILITY" / "B03-004_canonical_constitutional_requirement_registry.json").read_text(encoding="utf-8"))
        matrix = json.loads((EVIDENCE_ROOT / "B04-002_constitutional_to_implementation_matrix.json").read_text(encoding="utf-8"))
        gaps = json.loads((EVIDENCE_ROOT / "B04-002_implementation_gap_registry.json").read_text(encoding="utf-8"))
        self.assertEqual({item["requirement_id"] for item in requirements}, {item["requirement_id"] for item in matrix})
        self.assertTrue(all(item["implementation_artifacts"] for item in matrix))
        self.assertEqual(gaps, [])

    def test_b04_003_verification_population_is_classified_but_not_executed(self) -> None:
        verifiers = json.loads((EVIDENCE_ROOT / "B04-003_verifier_inventory.json").read_text(encoding="utf-8"))
        modes = json.loads((EVIDENCE_ROOT / "B04-003_verification_mode_registry.json").read_text(encoding="utf-8"))
        integrity = json.loads((EVIDENCE_ROOT / "B04-003_verification_integrity_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(verifiers), 4)
        self.assertEqual(len(verifiers), len(modes))
        self.assertEqual(integrity["orphan_verifiers"], [])
        self.assertEqual(integrity["evidence_producers_lacking_constitutional_authority"], [])

    def test_completion_report_preserves_no_behavior_or_certification_claims(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_correctness_evaluated"])
        self.assertFalse(completion["proof_objects_generated"])
        self.assertFalse(completion["certification_readiness_issued"])


if __name__ == "__main__":
    unittest.main()
