import json
from pathlib import Path
import unittest


S02_PATH = Path("Documentation/BROKER_RM001_S02_OWNERSHIP_CUSTODY/broker_rm001_s02_ownership_baseline.json")
S03_PATH = Path("Documentation/BROKER_RM001_S03_LIFECYCLE/broker_rm001_s03_lifecycle_baseline.json")
S04_PATH = Path("Documentation/BROKER_RM001_S04_INTERFACES/broker_rm001_s04_interface_baseline.json")


class BrokerRM001S04InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.s02 = json.loads(S02_PATH.read_text(encoding="utf-8"))
        cls.s03 = json.loads(S03_PATH.read_text(encoding="utf-8"))
        cls.s04 = json.loads(S04_PATH.read_text(encoding="utf-8"))

    def test_every_interface_has_owner_authority_and_dependencies(self) -> None:
        interfaces = self.s04["b04_001_broker_interface_registry"]

        self.assertEqual(len(interfaces), 14)
        for interface in interfaces:
            self.assertTrue(interface["interface_id"].startswith("BROKER-IFACE-"))
            self.assertTrue(interface["owner"])
            self.assertTrue(interface["provider"])
            self.assertTrue(interface["consumer"])
            self.assertTrue(interface["governing_authority"])
            self.assertTrue(interface["classification"])
            self.assertTrue(interface["sync_classification"])
            self.assertTrue(interface["dependencies"])
            self.assertTrue(interface["governing_objects"])
            self.assertTrue(interface["governing_lifecycles"])

    def test_interface_traceability_targets_existing_objects_and_lifecycles(self) -> None:
        s02_objects = {item["object_id"] for item in self.s02["b02_001_object_inventory"]}
        s03_lifecycles = {item["lifecycle_id"] for item in self.s03["b03_001_broker_lifecycle_registry"]}

        for item in self.s04["interface_traceability_registry"]:
            self.assertTrue(set(item["objects"]).issubset(s02_objects))
            self.assertTrue(set(item["lifecycles"]).issubset(s03_lifecycles))

    def test_every_interface_has_authority_contract_validation_and_acceptance(self) -> None:
        interface_ids = {item["interface_id"] for item in self.s04["b04_001_broker_interface_registry"]}
        matrix_ids = {item["interface_id"] for item in self.s04["b04_002_interface_authority_matrix"]}
        contract_ids = {item["interface_id"] for item in self.s04["b04_002_authority_contract_registry"]}
        validation_ids = {item["interface_id"] for item in self.s04["b04_002_validation_registry"]}
        acceptance_ids = {item["interface_id"] for item in self.s04["b04_002_acceptance_registry"]}

        self.assertEqual(interface_ids, matrix_ids)
        self.assertEqual(interface_ids, contract_ids)
        self.assertEqual(interface_ids, validation_ids)
        self.assertEqual(interface_ids, acceptance_ids)

        for contract in self.s04["b04_002_authority_contract_registry"]:
            self.assertTrue(contract["authorization_prerequisites"])
            self.assertTrue(contract["mandatory_inputs"])
            self.assertTrue(contract["mandatory_outputs"])
            self.assertTrue(contract["required_acknowledgments"])
            self.assertTrue(contract["required_evidence"])
            self.assertTrue(contract["immutable_contract_obligations"])

    def test_every_interface_has_dependency_failure_recovery_and_compatibility_governance(self) -> None:
        interface_ids = {item["interface_id"] for item in self.s04["b04_001_broker_interface_registry"]}

        for registry_name in (
            "b04_003_dependency_registry",
            "b04_003_compatibility_registry",
            "b04_003_interface_failure_registry",
            "b04_003_interface_recovery_registry",
            "b04_003_escalation_registry",
        ):
            registry_ids = {item["interface_id"] for item in self.s04[registry_name]}
            self.assertEqual(interface_ids, registry_ids)

    def test_reconciliation_closes_interface_deficiencies_without_runtime_execution(self) -> None:
        report = self.s04["b04_004_interface_reconciliation_report"]
        completion = self.s04["series_completion_report"]

        self.assertEqual(report["interfaces_inventoried"], 14)
        self.assertEqual(report["interfaces_with_one_owner"], 14)
        self.assertEqual(report["duplicate_interface_count"], 0)
        self.assertEqual(report["implied_interface_count"], 0)
        self.assertEqual(report["ambiguous_authority_contract_count"], 0)
        self.assertEqual(report["unresolved_interface_authority_count"], 0)
        self.assertFalse(report["runtime_behavior_modified"])
        self.assertFalse(report["repository_wide_verification_executed"])

        for order_id in ("B04-001", "B04-002", "B04-003", "B04-004"):
            self.assertEqual(completion[order_id], "COMPLETE")
        self.assertTrue(completion["ready_for_series_5"])
        self.assertFalse(completion["implied_interface_behavior_remaining"])
        self.assertFalse(completion["unresolved_interface_authority_remaining"])


if __name__ == "__main__":
    unittest.main()
