import json
from pathlib import Path
import unittest


S01_PATH = Path("Documentation/BROKER_RM002A_S01_IMPLEMENTATION_INVENTORY/broker_rm002a_s01_implementation_inventory.json")
S03_PATH = Path("Documentation/BROKER_RM001_S03_LIFECYCLE/broker_rm001_s03_lifecycle_baseline.json")
S04_PATH = Path("Documentation/BROKER_RM001_S04_INTERFACES/broker_rm001_s04_interface_baseline.json")
S05_PATH = Path("Documentation/BROKER_RM001_S05_EVIDENCE_CERTIFICATION/broker_rm001_s05_evidence_baseline.json")
S02_PATH = Path("Documentation/BROKER_RM002A_S02_STRUCTURAL_VERIFICATION/broker_rm002a_s02_structural_verification_baseline.json")


class BrokerRM002AS02StructuralVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.s01 = json.loads(S01_PATH.read_text(encoding="utf-8"))
        cls.s03 = json.loads(S03_PATH.read_text(encoding="utf-8"))
        cls.s04 = json.loads(S04_PATH.read_text(encoding="utf-8"))
        cls.s05 = json.loads(S05_PATH.read_text(encoding="utf-8"))
        cls.s02 = json.loads(S02_PATH.read_text(encoding="utf-8"))

    def test_s01_inventory_is_dependency_derived_and_frozen_for_s02(self) -> None:
        inventory = self.s01["canonical_implementation_inventory"]

        self.assertEqual(len(inventory), 12)
        self.assertTrue(self.s01["implementation_inventory_reconciliation"]["canonical_implementation_baseline_published"])
        self.assertFalse(self.s01["implementation_inventory_reconciliation"]["filename_only_participation_allowed"])
        self.assertFalse(self.s01["implementation_inventory_reconciliation"]["manual_participation_allowed"])
        for artifact in inventory:
            self.assertEqual(artifact["participation_status"], "PARTICIPATING")
            self.assertTrue(artifact["objective_dependency_evidence"])

    def test_every_inventory_artifact_is_structurally_verified_once(self) -> None:
        inventory_ids = {item["artifact_id"] for item in self.s01["canonical_implementation_inventory"]}
        verified_ids = {item["artifact_id"] for item in self.s02["structural_verification_registry"]}

        self.assertEqual(inventory_ids, verified_ids)
        for item in self.s02["structural_verification_registry"]:
            self.assertEqual(item["structural_status"], "VERIFIED")

    def test_interface_lifecycle_and_evidence_coverage_matches_constitutional_baselines(self) -> None:
        interface_ids = {item["interface_id"] for item in self.s04["b04_001_broker_interface_registry"]}
        verified_interface_ids = {item["interface_id"] for item in self.s02["interface_verification_registry"]}
        lifecycle_ids = {item["lifecycle_id"] for item in self.s03["b03_001_broker_lifecycle_registry"]}
        covered_lifecycle_ids = {item["lifecycle_id"] for item in self.s02["lifecycle_implementation_registry"]}
        evidence_ids = {item["evidence_id"] for item in self.s05["b05_001_broker_evidence_registry"]}
        capability_evidence_ids = {item["evidence_id"] for item in self.s02["evidence_production_capability_registry"]}

        self.assertEqual(interface_ids, verified_interface_ids)
        self.assertEqual(lifecycle_ids, covered_lifecycle_ids)
        self.assertEqual(evidence_ids, capability_evidence_ids)

    def test_structural_verification_does_not_claim_behavioral_or_certification_proof(self) -> None:
        self.assertFalse(self.s02["behavioral_correctness_evaluated"])
        self.assertFalse(self.s02["runtime_behavior_modified"])
        self.assertFalse(self.s02["constitutional_doctrine_modified"])
        self.assertFalse(self.s02["repository_wide_behavioral_verification_executed"])
        self.assertFalse(self.s02["certification_readiness_activity_executed"])
        self.assertFalse(self.s02["final_proof_objects_generated"])

    def test_structural_reconciliation_closes_ambiguity(self) -> None:
        reconciliation = self.s02["structural_reconciliation_registry"]
        completion = self.s02["series_completion_report"]

        self.assertEqual(reconciliation["participating_artifacts_verified"], 12)
        self.assertEqual(reconciliation["unresolved_structural_findings"], 0)
        self.assertEqual(reconciliation["unresolved_structural_contradictions"], 0)
        self.assertEqual(reconciliation["unresolved_structural_ambiguity"], 0)
        self.assertTrue(completion["every_participating_artifact_structurally_verified"])
        self.assertTrue(completion["ready_for_subsequent_broker_implementation_verification"])


if __name__ == "__main__":
    unittest.main()
