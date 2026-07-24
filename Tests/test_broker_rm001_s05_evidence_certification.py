import json
from pathlib import Path
import unittest


S02_PATH = Path("Documentation/BROKER_RM001_S02_OWNERSHIP_CUSTODY/broker_rm001_s02_ownership_baseline.json")
S03_PATH = Path("Documentation/BROKER_RM001_S03_LIFECYCLE/broker_rm001_s03_lifecycle_baseline.json")
S04_PATH = Path("Documentation/BROKER_RM001_S04_INTERFACES/broker_rm001_s04_interface_baseline.json")
S05_PATH = Path("Documentation/BROKER_RM001_S05_EVIDENCE_CERTIFICATION/broker_rm001_s05_evidence_baseline.json")


class BrokerRM001S05EvidenceCertificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.s02 = json.loads(S02_PATH.read_text(encoding="utf-8"))
        cls.s03 = json.loads(S03_PATH.read_text(encoding="utf-8"))
        cls.s04 = json.loads(S04_PATH.read_text(encoding="utf-8"))
        cls.s05 = json.loads(S05_PATH.read_text(encoding="utf-8"))

    def test_every_evidence_artifact_has_owner_producer_custodian_and_authority(self) -> None:
        evidence = self.s05["b05_001_broker_evidence_registry"]

        self.assertEqual(len(evidence), 12)
        for item in evidence:
            self.assertTrue(item["evidence_id"].startswith("BROKER-EVID-"))
            self.assertTrue(item["owner"])
            self.assertTrue(item["producer"])
            self.assertTrue(item["consumers"])
            self.assertTrue(item["custodian"])
            self.assertTrue(item["governing_authority"])
            self.assertTrue(item["relationships"])

    def test_evidence_traceability_targets_existing_baselines(self) -> None:
        s02_objects = {item["object_id"] for item in self.s02["b02_001_object_inventory"]}
        s03_lifecycles = {item["lifecycle_id"] for item in self.s03["b03_001_broker_lifecycle_registry"]}
        s04_interfaces = {item["interface_id"] for item in self.s04["b04_001_broker_interface_registry"]}

        for item in self.s05["b05_001_broker_evidence_registry"]:
            self.assertTrue(set(item["governing_objects"]).issubset(s02_objects))
            self.assertTrue(set(item["governing_lifecycles"]).issubset(s03_lifecycles))
            self.assertTrue(set(item["governing_interfaces"]).issubset(s04_interfaces))

    def test_validation_and_traceability_cover_every_evidence_artifact(self) -> None:
        evidence_ids = {item["evidence_id"] for item in self.s05["b05_001_broker_evidence_registry"]}
        ownership_ids = {item["evidence_id"] for item in self.s05["b05_001_evidence_ownership_registry"]}
        validation_ids = {item["evidence_id"] for item in self.s05["b05_002_evidence_validation_registry"]}
        traceability_ids = {item["evidence_id"] for item in self.s05["b05_002_traceability_registry"]}

        self.assertEqual(evidence_ids, ownership_ids)
        self.assertEqual(evidence_ids, validation_ids)
        self.assertEqual(evidence_ids, traceability_ids)

        for validation in self.s05["b05_002_evidence_validation_registry"]:
            self.assertTrue(validation["validation_authority"])
            self.assertTrue(validation["acceptance_authority"])
            self.assertTrue(validation["rejection_authority"])
            self.assertTrue(validation["validation_requirements"])

    def test_certification_audit_reconciliation_and_exception_governance_is_complete(self) -> None:
        self.assertEqual(len(self.s05["b05_003_certification_registry"]), 2)
        self.assertEqual(len(self.s05["b05_003_audit_registry"]), 2)
        self.assertEqual(len(self.s05["b05_003_reconciliation_registry"]), 2)
        self.assertEqual(len(self.s05["b05_003_evidence_exception_registry"]), 5)

        for certification in self.s05["b05_003_certification_registry"]:
            self.assertEqual(certification["certification_authority"], "Enterprise Certification Authority")
            self.assertTrue(certification["certification_prerequisites"])
            self.assertTrue(certification["certification_evidence"])
            self.assertTrue(certification["terminal_certification_disposition"])

    def test_reconciliation_closes_evidence_deficiencies_without_runtime_execution(self) -> None:
        report = self.s05["b05_004_evidence_reconciliation_registry"]
        completion = self.s05["series_completion_report"]
        immutable = self.s05["b05_002_immutable_evidence_specification"]

        self.assertEqual(report["evidence_artifacts_inventoried"], 12)
        self.assertEqual(report["evidence_artifacts_with_one_owner"], 12)
        self.assertEqual(report["traceability_complete"], 12)
        self.assertFalse(report["implied_evidence_obligations_remaining"])
        self.assertFalse(report["conflicting_certification_definitions_remaining"])
        self.assertFalse(report["runtime_behavior_modified"])
        self.assertFalse(report["repository_wide_verification_executed"])
        self.assertEqual(immutable["history_model"], "append-only")
        self.assertEqual(immutable["correction_model"], "supersession only")

        for order_id in ("B05-001", "B05-002", "B05-003", "B05-004"):
            self.assertEqual(completion[order_id], "COMPLETE")
        self.assertTrue(completion["ready_for_series_6"])


if __name__ == "__main__":
    unittest.main()
