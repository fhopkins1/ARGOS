from __future__ import annotations

import json
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
B08_DIR = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM002_B08_CLEAN_ROOM_REPRODUCIBILITY"
B09_DIR = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM002_B09_FAIL_CLOSED_CERTIFICATION"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class MonitoringRm002B08B09EvidenceTests(unittest.TestCase):
    def test_b08_clean_room_reproducibility_is_ready(self) -> None:
        completion = read_json(B08_DIR / "completion_report.json")
        blockers = read_json(B08_DIR / "B08-004_reproducibility_blocker_registry.json")
        comparison = read_json(B08_DIR / "B08-004_repeated_execution_comparison_registry.json")

        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["reproducibility_readiness"], "READY_FOR_FAIL_CLOSED_CERTIFICATION_VALIDATION")
        self.assertTrue(completion["all_regeneration_executions_passed"])
        self.assertTrue(completion["repeated_clean_room_semantic_equivalence"])
        self.assertTrue(completion["clean_extraction_without_prior_monitoring_rm002_artifacts"])
        self.assertEqual(blockers, [])
        self.assertTrue(comparison["semantic_equivalence"])

    def test_b09_fail_closed_campaign_is_ready(self) -> None:
        completion = read_json(B09_DIR / "completion_report.json")
        blockers = read_json(B09_DIR / "B09-004_certification_system_blocker_registry.json")
        fail_closed = read_json(B09_DIR / "B09-002_fail_closed_validation_report.json")

        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["certification_system_readiness"], "READY_FOR_FINAL_INDEPENDENT_ECS003_CERTIFICATION")
        self.assertEqual(completion["confidence"], "VERY_HIGH_CONFIDENCE")
        self.assertTrue(completion["all_mutations_fail_closed"])
        self.assertTrue(completion["all_restorations_passed"])
        self.assertTrue(completion["repeated_mutation_determinism"])
        self.assertEqual(completion["false_positive_certifications"], 0)
        self.assertEqual(completion["false_negative_certifications"], 0)
        self.assertEqual(blockers, [])
        self.assertEqual(fail_closed["status"], "PASS")

    def test_b09_every_mutation_denies_unconditional_pass_and_restores(self) -> None:
        verdicts = read_json(B09_DIR / "B09-004_certification_verdict_registry.json")
        controls = read_json(B09_DIR / "B09-004_false_negative_validation_registry.json")

        self.assertEqual(len(verdicts), 6)
        self.assertEqual(len(controls), 6)
        for verdict in verdicts:
            self.assertEqual(verdict["verdict"], "FAIL")
        for control in controls:
            self.assertTrue(control["baseline_restored"])
            self.assertEqual(control["control_disposition"], "PASS")


if __name__ == "__main__":
    unittest.main()
