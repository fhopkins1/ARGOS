import json
from pathlib import Path
import unittest


S02_PATH = Path("Documentation/BROKER_RM001_S02_OWNERSHIP_CUSTODY/broker_rm001_s02_ownership_baseline.json")
S03_PATH = Path("Documentation/BROKER_RM001_S03_LIFECYCLE/broker_rm001_s03_lifecycle_baseline.json")
S04_PATH = Path("Documentation/BROKER_RM001_S04_INTERFACES/broker_rm001_s04_interface_baseline.json")
S05_PATH = Path("Documentation/BROKER_RM001_S05_EVIDENCE_CERTIFICATION/broker_rm001_s05_evidence_baseline.json")
S06_PATH = Path("Documentation/BROKER_RM001_S06_TRACEABILITY_READINESS/broker_rm001_s06_traceability_readiness_baseline.json")


class BrokerRM001S06TraceabilityReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.s02 = json.loads(S02_PATH.read_text(encoding="utf-8"))
        cls.s03 = json.loads(S03_PATH.read_text(encoding="utf-8"))
        cls.s04 = json.loads(S04_PATH.read_text(encoding="utf-8"))
        cls.s05 = json.loads(S05_PATH.read_text(encoding="utf-8"))
        cls.s06 = json.loads(S06_PATH.read_text(encoding="utf-8"))

    def test_traceability_covers_existing_broker_populations(self) -> None:
        s02_objects = {item["object_id"] for item in self.s02["b02_001_object_inventory"]}
        s03_lifecycles = {item["lifecycle_id"] for item in self.s03["b03_001_broker_lifecycle_registry"]}
        s04_interfaces = {item["interface_id"] for item in self.s04["b04_001_broker_interface_registry"]}
        s05_evidence = {item["evidence_id"] for item in self.s05["b05_001_broker_evidence_registry"]}

        object_ids = set(self.s06["b06_001_constitutional_object_traceability_registry"][0]["object_ids"])
        lifecycle_ids = set(self.s06["b06_001_lifecycle_traceability_registry"][0]["lifecycle_ids"])
        interface_ids = set(self.s06["b06_001_interface_traceability_registry"][0]["interface_ids"])
        evidence_ids = set(self.s06["b06_001_evidence_traceability_registry"][0]["evidence_ids"])

        self.assertEqual(s02_objects, object_ids)
        self.assertEqual(s03_lifecycles, lifecycle_ids)
        self.assertEqual(s04_interfaces, interface_ids)
        self.assertEqual(s05_evidence, evidence_ids)

    def test_every_requirement_has_source_rule_and_readiness_status(self) -> None:
        requirement_ids = {item["requirement_id"] for item in self.s06["b06_001_constitutional_requirement_registry"]}
        rule_requirement_ids = {item["requirement_id"] for item in self.s06["b06_001_executable_rule_traceability_registry"]}
        readiness_requirement_ids = {item["requirement_id"] for item in self.s06["b06_004_constitutional_readiness_registry"]}

        self.assertEqual(len(requirement_ids), 8)
        self.assertEqual(requirement_ids, rule_requirement_ids)
        self.assertEqual(requirement_ids, readiness_requirement_ids)

    def test_participation_exclusions_and_findings_are_governed(self) -> None:
        self.assertGreaterEqual(len(self.s06["b06_002_dependency_derived_participation_registry"]), 5)
        self.assertEqual(len(self.s06["b06_002_exclusion_validation_registry"]), 2)
        self.assertEqual(len(self.s06["b06_003_constitutional_finding_registry"]), 3)

        for finding in self.s06["b06_003_constitutional_finding_registry"]:
            self.assertTrue(finding["finding_id"])
            self.assertTrue(finding["governing_requirement"])
            self.assertTrue(finding["owner"])
            self.assertEqual(finding["disposition"], "CLOSED_BY_BASELINE")

    def test_s06_readiness_is_complete_without_certification_pass_claim(self) -> None:
        readiness = self.s06["b06_004_final_constitutional_readiness_baseline"]
        traceability = self.s06["b06_001_bidirectional_traceability_matrix"]
        completion = self.s06["series_completion_report"]

        self.assertTrue(traceability["forward_traceability_complete"])
        self.assertTrue(traceability["reverse_traceability_complete"])
        self.assertEqual(traceability["orphaned_requirement_count"], 0)
        self.assertEqual(traceability["orphaned_artifact_count"], 0)
        self.assertEqual(readiness["certification_readiness_status"], "READY_FOR_INDEPENDENT_ECS003_REAUDIT")
        self.assertEqual(readiness["certification_verdict"], "NOT_CERTIFICATION_PASS")

        for order_id in ("B06-001", "B06-002", "B06-003", "B06-004"):
            self.assertEqual(completion[order_id], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
