import json
from pathlib import Path
import unittest


S02_PATH = Path("Documentation/BROKER_RM001_S02_OWNERSHIP_CUSTODY/broker_rm001_s02_ownership_baseline.json")
S03_PATH = Path("Documentation/BROKER_RM001_S03_LIFECYCLE/broker_rm001_s03_lifecycle_baseline.json")


class BrokerRM001S03LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.s02 = json.loads(S02_PATH.read_text(encoding="utf-8"))
        cls.s03 = json.loads(S03_PATH.read_text(encoding="utf-8"))

    def test_every_s02_object_maps_to_a_lifecycle(self) -> None:
        s02_objects = {item["object_id"] for item in self.s02["b02_001_object_inventory"]}
        mapped_objects = {item["object_id"] for item in self.s03["object_to_lifecycle_map"]}
        lifecycle_ids = {item["lifecycle_id"] for item in self.s03["b03_001_broker_lifecycle_registry"]}

        self.assertEqual(s02_objects, mapped_objects)
        self.assertTrue(all(item["lifecycle_id"] in lifecycle_ids for item in self.s03["object_to_lifecycle_map"]))

    def test_every_lifecycle_has_owner_trigger_inputs_outputs_and_authority(self) -> None:
        for lifecycle in self.s03["b03_001_broker_lifecycle_registry"]:
            self.assertTrue(lifecycle["owner"])
            self.assertTrue(lifecycle["trigger"])
            self.assertTrue(lifecycle["inputs"])
            self.assertTrue(lifecycle["outputs"])
            self.assertTrue(lifecycle["governing_objects"])
            self.assertTrue(lifecycle["constitutional_authority"])

    def test_state_model_defines_required_state_classes(self) -> None:
        state_model = self.s03["b03_002_lifecycle_state_registry"][0]

        for key in (
            "initial_state",
            "intermediate_states",
            "waiting_states",
            "active_states",
            "suspended_states",
            "retry_states",
            "failed_states",
            "cancelled_states",
            "terminal_states",
        ):
            self.assertTrue(state_model[key])

    def test_transitions_have_authority_and_evidence(self) -> None:
        transitions = self.s03["b03_002_transition_authority_matrix"]
        prohibited = self.s03["b03_002_prohibited_transition_registry"]

        self.assertGreater(len(transitions), 0)
        self.assertGreater(len(prohibited), 0)
        for transition in transitions:
            self.assertTrue(transition["entry_authority"])
            self.assertTrue(transition["exit_authority"])
            self.assertTrue(transition["required_evidence"])

    def test_exception_recovery_termination_and_history_are_governed(self) -> None:
        self.assertGreater(len(self.s03["b03_003_exception_registry"]), 0)
        self.assertGreater(len(self.s03["b03_003_recovery_registry"]), 0)
        self.assertGreater(len(self.s03["b03_003_termination_registry"]), 0)
        history = self.s03["b03_003_immutable_lifecycle_history_specification"]
        self.assertEqual(history["state_history"], "append-only")
        self.assertEqual(history["correction_history"], "supersession only")

    def test_reconciliation_closes_lifecycle_deficiencies(self) -> None:
        report = self.s03["b03_004_lifecycle_reconciliation_report"]
        completion = self.s03["series_completion_report"]

        self.assertEqual(report["object_count_from_s02"], report["objects_mapped_to_lifecycle"])
        self.assertEqual(report["undefined_state_count"], 0)
        self.assertEqual(report["ambiguous_transition_count"], 0)
        self.assertEqual(report["unresolved_lifecycle_authority_count"], 0)
        self.assertFalse(report["runtime_behavior_modified"])
        self.assertFalse(report["repository_wide_verification_executed"])
        self.assertEqual(completion["B03-001"], "COMPLETE")
        self.assertEqual(completion["B03-002"], "COMPLETE")
        self.assertEqual(completion["B03-003"], "COMPLETE")
        self.assertEqual(completion["B03-004"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
