from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_B01002A_S06_CONSTITUTIONAL_BOUNDARY_BASELINE"


class PositionRegistryB01002AS06ConstitutionalBoundaryBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_b01002a_s06_constitutional_boundary_baseline.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_input_registry_preserves_available_series_and_documents_s04_gap(self) -> None:
        registry = json.loads((EVIDENCE_ROOT / "B01-002A-S06-001_constitutional_input_registry.json").read_text(encoding="utf-8"))
        statuses = {item["series_id"]: item["input_status"] for item in registry}
        self.assertEqual(statuses["S01"], "AVAILABLE")
        self.assertEqual(statuses["S02"], "AVAILABLE")
        self.assertEqual(statuses["S03"], "AVAILABLE")
        self.assertEqual(statuses["S05"], "AVAILABLE")
        self.assertEqual(statuses["S04"], "NOT_AVAILABLE_NOT_FABRICATED")

    def test_s06_002_reconciles_unique_ownership_identity_truth_and_dependency(self) -> None:
        ownership = json.loads((EVIDENCE_ROOT / "B01-002A-S06-002_constitutional_ownership_baseline.json").read_text(encoding="utf-8"))
        identities = json.loads((EVIDENCE_ROOT / "B01-002A-S06-002_constitutional_identity_baseline.json").read_text(encoding="utf-8"))
        truths = json.loads((EVIDENCE_ROOT / "B01-002A-S06-002_constitutional_truth_ownership_baseline.json").read_text(encoding="utf-8"))
        dependencies = json.loads((EVIDENCE_ROOT / "B01-002A-S06-002_constitutional_dependency_baseline.json").read_text(encoding="utf-8"))

        self.assertTrue(all(not item["split_ownership"] for item in ownership))
        self.assertTrue(all(not item["duplicate_authority"] for item in ownership))
        self.assertEqual(
            [item["identity_authority"] for item in identities if item["canonical_identity"] == "position_identity"],
            ["Position Registry"],
        )
        self.assertEqual(len({item["truth_class"] for item in truths}), len(truths))
        self.assertTrue(all(not item["conflicting_truth_ownership"] for item in truths))
        self.assertTrue(dependencies["deterministic_dependency_direction"])
        self.assertTrue(dependencies["deterministic_dependency_precedence"])
        self.assertEqual(dependencies["unauthorized_circular_dependencies"], [])

    def test_s06_003_integrity_report_has_no_unresolved_conflicts(self) -> None:
        integrity = json.loads((EVIDENCE_ROOT / "B01-002A-S06-003_constitutional_integrity_report.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B01-002A-S06-003_unresolved_constitutional_findings_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(integrity["every_interaction_has_one_governing_authority"])
        self.assertTrue(integrity["every_truth_ownership_relationship_is_deterministic"])
        self.assertEqual(integrity["duplicate_authority"], [])
        self.assertEqual(integrity["split_ownership"], [])
        self.assertEqual(integrity["conflicting_truth_ownership"], [])
        self.assertEqual(integrity["circular_dependency"], [])
        self.assertEqual(unresolved, [])

    def test_s06_004_publication_is_doctrine_only_and_digest_matches(self) -> None:
        baseline_path = EVIDENCE_ROOT / "B01-002A-S06-004_authoritative_constitutional_boundary_baseline.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        manifest = json.loads((EVIDENCE_ROOT / "B01-002A-S06-004_publication_manifest.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))

        self.assertEqual(baseline["status"], "PUBLISHED_AUTHORITATIVE_BASELINE")
        self.assertEqual(baseline["competing_normative_baselines"], [])
        self.assertEqual(manifest["published_baseline"], baseline_path.name)
        self.assertEqual(manifest["baseline_digest"], completion["baseline_digest"])
        self.assertFalse(completion["implementation_evaluated"])
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_proof_generated"])
        self.assertFalse(completion["certification_activity_executed"])


if __name__ == "__main__":
    unittest.main()
