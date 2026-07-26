from __future__ import annotations

import json
from pathlib import Path
import unittest

from Scripts.closed_position_truth_rm002_b07_clean_room_audit import OUTPUT_DIR, generate_clean_room_audit


class ClosedPositionTruthRM002B07CleanRoomAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        generate_clean_room_audit()

    def _load(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_b07_deliverables_exist(self) -> None:
        required = {
            "clean_room_repository_manifest.json",
            "repository_identity_registry.json",
            "repository_completeness_report.json",
            "environment_identity_registry.json",
            "reproduced_implementation_inventory.json",
            "reproduced_verifier_registry.json",
            "reproduced_fixture_registry.json",
            "reproduced_behavioral_execution_registry.json",
            "reproduced_evidence_registry.json",
            "reproduced_proof_registry.json",
            "reproduced_implementation_traceability_graph.json",
            "independent_mutation_plan.json",
            "mutation_registry.json",
            "false_positive_false_negative_report.json",
            "fail_closed_validation_report.json",
            "reproduction_comparison_registry.json",
            "variance_registry.json",
            "certification_blocker_registry.json",
            "independent_clean_room_reproduction_report.json",
            "final_ecs003_certification_report.json",
            "final_reproduction_disposition.json",
            "final_certification_verdict.json",
            "completion_report.json",
            "manifest.json",
        }
        present = {item.name for item in Path(OUTPUT_DIR).iterdir() if item.is_file()}
        self.assertTrue(required.issubset(present))

    def test_clean_room_identity_and_package_only_execution_are_recorded(self) -> None:
        repository = self._load("repository_identity_registry.json")
        readiness = self._load("clean_room_readiness_assessment.json")
        environment = self._load("environment_identity_registry.json")

        self.assertTrue(repository["repository_hash"])
        self.assertGreater(repository["content_file_count"], 0)
        self.assertTrue(readiness["ready"])
        self.assertFalse(readiness["hidden_state_required"])
        self.assertFalse(environment["git_metadata_required"])
        self.assertFalse(environment["prior_generated_evidence_reused"])

    def test_behavioral_and_mutation_campaigns_pass_without_false_results(self) -> None:
        behavioral = self._load("reproduced_behavioral_execution_registry.json")
        mutations = self._load("mutation_registry.json")
        false_report = self._load("false_positive_false_negative_report.json")

        self.assertEqual(10, len(behavioral))
        self.assertTrue(all(item["disposition"] == "PASS" for item in behavioral))
        self.assertEqual(20, len(mutations))
        self.assertTrue(all(item["true_positive"] for item in mutations))
        self.assertEqual([], false_report["false_positives"])
        self.assertEqual([], false_report["false_negatives"])

    def test_requirement_proof_and_traceability_are_regenerated(self) -> None:
        proof = self._load("reproduced_proof_registry.json")
        lineage = self._load("reproduced_proof_lineage_registry.json")
        forward = self._load("forward_traceability_matrix.json")
        backward = self._load("backward_traceability_matrix.json")

        self.assertEqual(34, len(proof))
        self.assertEqual(34, len(lineage))
        self.assertTrue(all(item["disposition"] == "PROVEN" for item in proof))
        self.assertTrue(all(item["complete"] for item in forward))
        self.assertTrue(all(item["complete"] for item in backward))
        self.assertTrue(all(item["prior_proof_reused"] is False for item in proof))

    def test_final_reproduction_and_certification_are_clean(self) -> None:
        completion = self._load("completion_report.json")
        reproduction = self._load("final_reproduction_disposition.json")
        verdict = self._load("final_certification_verdict.json")
        blockers = self._load("certification_blocker_registry.json")

        self.assertEqual("REPRODUCIBLE", reproduction["disposition"])
        self.assertEqual("ECS003_IMPLEMENTATION_CERTIFIED", verdict["verdict"])
        self.assertEqual([], blockers)
        self.assertEqual(0, completion["certification_blocker_count"])
        self.assertEqual(0, completion["false_positive_count"])
        self.assertEqual(0, completion["false_negative_count"])
        self.assertEqual(34, completion["proven_requirement_count"])
        self.assertEqual(0, completion["not_proven_requirement_count"])


if __name__ == "__main__":
    unittest.main()
