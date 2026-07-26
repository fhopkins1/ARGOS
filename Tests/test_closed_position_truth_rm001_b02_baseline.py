from __future__ import annotations

import json
from pathlib import Path
import unittest

from Scripts.closed_position_truth_rm001_b02_baseline import OUTPUT_DIR, generate_baseline


class ClosedPositionTruthRM001B02BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        generate_baseline()

    def _load(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_b02_deliverables_exist(self) -> None:
        required = {
            "B02-001_canonical_object_registry.json",
            "B02-001_object_identity_registry.json",
            "B02-001_object_relationship_registry.json",
            "B02-001_constitutional_findings_registry.json",
            "B02-001_completion_report.json",
            "B02-002_ownership_registry.json",
            "B02-002_custody_registry.json",
            "B02-002_creation_authority_registry.json",
            "B02-002_mutation_authority_registry.json",
            "B02-002_correction_authority_registry.json",
            "B02-002_supersession_authority_registry.json",
            "B02-002_archival_authority_registry.json",
            "B02-002_constitutional_transfer_registry.json",
            "B02-002_object_authority_matrix.json",
            "B02-002_unauthorized_authority_registry.json",
            "B02-002_authority_conflict_registry.json",
            "B02-002_completion_report.json",
            "B02-003_lifecycle_registry.json",
            "B02-003_state_transition_registry.json",
            "B02-003_transition_authority_matrix.json",
            "B02-003_prohibited_transition_registry.json",
            "B02-003_duplicate_prevention_doctrine.json",
            "B02-003_idempotency_doctrine.json",
            "B02-003_replay_doctrine.json",
            "B02-003_recovery_doctrine.json",
            "B02-003_correction_lifecycle_doctrine.json",
            "B02-003_supersession_lifecycle_doctrine.json",
            "B02-003_archival_eligibility_doctrine.json",
            "B02-003_completion_report.json",
            "B02-004_historical_integrity_registry.json",
            "B02-004_immutability_registry.json",
            "B02-004_correction_lineage_registry.json",
            "B02-004_supersession_lineage_registry.json",
            "B02-004_version_identity_registry.json",
            "B02-004_provenance_registry.json",
            "B02-004_archival_eligibility_registry.json",
            "B02-004_historical_custody_registry.json",
            "B02-004_historical_retrieval_registry.json",
            "B02-004_historical_audit_registry.json",
            "B02-004_destructive_action_prohibition_registry.json",
            "B02-004_completion_report.json",
            "B02_series_completion_report.json",
            "manifest.json",
            "source_order_registry.json",
        }
        present = {item.name for item in Path(OUTPUT_DIR).iterdir() if item.is_file()}
        self.assertTrue(required.issubset(present))

    def test_series_is_doctrine_only_and_ready_for_b03(self) -> None:
        report = self._load("B02_series_completion_report.json")

        self.assertEqual("COMPLETE", report["status"])
        self.assertTrue(report["constitutional_doctrine_only"])
        self.assertFalse(report["implementation_behavior_modified"])
        self.assertFalse(report["behavioral_verification_executed"])
        self.assertFalse(report["implementation_certification_executed"])
        self.assertFalse(report["implementation_proof_generated"])
        self.assertEqual("CLOSED-POSITION-TRUTH-RM-001-B03", report["ready_for"])
        self.assertTrue(all(report["completion_criteria"].values()))

    def test_canonical_objects_have_identity_owner_creator_relationships_and_retirement(self) -> None:
        objects = self._load("B02-001_canonical_object_registry.json")
        names = {item["canonical_object"] for item in objects}

        self.assertEqual(14, len(objects))
        self.assertIn("Closed Position Record", names)
        self.assertIn("Archival Record", names)
        self.assertTrue(all(item["constitutional_owner"] == "Closed Position Truth Office" for item in objects))
        self.assertTrue(all(item["constitutional_creator"] == "Closed Position Truth Office" for item in objects))
        self.assertTrue(all(item["identity_namespace"] for item in objects))
        self.assertTrue(all(item["relationships"] for item in objects))
        self.assertTrue(all(item["retirement_conditions"] for item in objects))
        self.assertTrue(all(item["replaces_upstream_truth"] is False for item in objects))

    def test_object_authority_matrix_prevents_implicit_transfer_and_finalized_mutation(self) -> None:
        matrix = self._load("B02-002_object_authority_matrix.json")
        conflicts = self._load("B02-002_authority_conflict_registry.json")
        unauthorized = self._load("B02-002_unauthorized_authority_registry.json")

        self.assertEqual(14, len(matrix))
        self.assertTrue(all(item["owner"] == "Closed Position Truth Office" for item in matrix))
        self.assertTrue(all(item["implicit_ownership_transfer_allowed"] is False for item in matrix))
        finalized = {item["canonical_object"]: item for item in matrix}
        self.assertEqual("PROHIBITED_AFTER_FINALIZATION", finalized["Closed Position Record"]["mutation_authority"])
        self.assertEqual("NO_UNRESOLVED_AUTHORITY_CONFLICTS", conflicts["status"])
        self.assertIn("mutation of finalized truth", {item["prohibited_authority"] for item in unauthorized})

    def test_lifecycle_blocks_bypass_reopen_and_exception_truth(self) -> None:
        lifecycle = self._load("B02-003_lifecycle_registry.json")
        transitions = self._load("B02-003_state_transition_registry.json")
        prohibited = self._load("B02-003_prohibited_transition_registry.json")

        states = {item["state"] for item in lifecycle["states"]}
        self.assertIn("Constitutionally Closed", states)
        self.assertIn("Exception", states)
        self.assertIn("Archived", states)
        self.assertTrue(any(item["from_state"] == "Eligible for Closure" and item["to_state"] == "Constitutionally Closed" for item in transitions))
        prohibited_values = {item["transition"] for item in prohibited}
        self.assertIn("Exception -> Constitutionally Closed", prohibited_values)
        self.assertIn("Constitutionally Closed -> open-position state", prohibited_values)
        self.assertIn("Archived -> active lifecycle state", prohibited_values)

    def test_historical_integrity_preserves_lineage_and_auditability(self) -> None:
        integrity = self._load("B02-004_historical_integrity_registry.json")
        versions = self._load("B02-004_version_identity_registry.json")
        retrieval = self._load("B02-004_historical_retrieval_registry.json")
        destructive = self._load("B02-004_destructive_action_prohibition_registry.json")

        self.assertEqual(14, len(integrity))
        self.assertTrue(all(item["immutable_after_finalization"] for item in integrity))
        self.assertTrue(all(item["lineage_required"] for item in integrity))
        self.assertTrue(all(item["audit_reconstruction_required"] for item in integrity))
        self.assertTrue(all(item["parallel_authoritative_versions_allowed"] is False for item in versions))
        self.assertFalse(retrieval["multiple_versions_simultaneously_current"])
        self.assertIn("historical overwrite", {item["prohibited_action"] for item in destructive})
        self.assertIn("reopening of constitutionally closed positions", {item["prohibited_action"] for item in destructive})


if __name__ == "__main__":
    unittest.main()
