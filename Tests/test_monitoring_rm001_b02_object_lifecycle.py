from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM001_B02_OBJECT_LIFECYCLE"


class MonitoringRM001B02ObjectLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "monitoring_rm001_b02_object_lifecycle.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_b02_001_canonical_objects_are_unique_and_owned(self) -> None:
        objects = json.loads((EVIDENCE_ROOT / "B02-001_canonical_monitoring_object_registry.json").read_text(encoding="utf-8"))
        validation = json.loads((EVIDENCE_ROOT / "B02-001_constitutional_validation_report.json").read_text(encoding="utf-8"))
        names = [item["object_name"] for item in objects]
        identities = [item["canonical_identity_structure"] for item in objects]
        self.assertGreaterEqual(len(objects), 20)
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(identities), len(set(identities)))
        self.assertTrue(all(item["constitutional_owner"] == "Monitoring Office" for item in objects))
        self.assertEqual(validation["ambiguities"], [])

    def test_b02_002_pipeline_is_immutable_and_separated(self) -> None:
        pipeline = json.loads((EVIDENCE_ROOT / "B02-002_constitutional_processing_pipeline.json").read_text(encoding="utf-8"))
        separation = json.loads((EVIDENCE_ROOT / "B02-002_pipeline_separation_verification_report.json").read_text(encoding="utf-8"))
        self.assertEqual([item["from_stage"] for item in pipeline], ["Raw Observation", "Normalized Observation", "Evaluation", "Finding", "Alert"])
        self.assertEqual(pipeline[-1]["to_stage"], "Escalation")
        self.assertTrue(all(item["immutable_sequence"] for item in pipeline))
        self.assertFalse(separation["stage_bypass_exists"])
        self.assertTrue(separation["escalations_never_authorize_enterprise_action"])

    def test_b02_003_lifecycle_threshold_replay_and_recovery_are_defined(self) -> None:
        states = json.loads((EVIDENCE_ROOT / "B02-003_lifecycle_state_registry.json").read_text(encoding="utf-8"))
        transitions = json.loads((EVIDENCE_ROOT / "B02-003_state_transition_registry.json").read_text(encoding="utf-8"))
        replay = json.loads((EVIDENCE_ROOT / "B02-003_replay_constitution.json").read_text(encoding="utf-8"))
        recovery = json.loads((EVIDENCE_ROOT / "B02-003_recovery_constitution.json").read_text(encoding="utf-8"))
        prohibited = json.loads((EVIDENCE_ROOT / "B02-003_prohibited_transition_registry.json").read_text(encoding="utf-8"))
        self.assertIn("Archived", {item["state"] for item in states})
        self.assertTrue(transitions)
        self.assertTrue(replay["deterministic"])
        self.assertTrue(recovery["preserves_lifecycle_integrity"])
        self.assertTrue(prohibited)

    def test_b02_004_historical_integrity_preserves_lineage(self) -> None:
        historical = json.loads((EVIDENCE_ROOT / "B02-004_historical_integrity_constitution.json").read_text(encoding="utf-8"))
        correction = json.loads((EVIDENCE_ROOT / "B02-004_correction_registry.json").read_text(encoding="utf-8"))
        supersession = json.loads((EVIDENCE_ROOT / "B02-004_supersession_registry.json").read_text(encoding="utf-8"))
        verification = json.loads((EVIDENCE_ROOT / "B02-004_historical_integrity_verification_report.json").read_text(encoding="utf-8"))
        self.assertEqual(len(historical), len(correction))
        self.assertEqual(len(correction), len(supersession))
        self.assertTrue(all(item["lineage_preservation"] for item in supersession))
        self.assertTrue(verification["lineage_chain_complete"])
        self.assertEqual(verification["ambiguities"], [])

    def test_series_completion_preserves_constitutional_only_scope(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        series = json.loads((EVIDENCE_ROOT / "series_completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_proof_generated"])
        self.assertFalse(completion["certification_activity_executed"])
        self.assertEqual(series["depends_on"], "MONITORING-RM-001-B01")
        self.assertTrue(series["baseline_digest"])


if __name__ == "__main__":
    unittest.main()
