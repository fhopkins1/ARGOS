import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from argos.trader.rm002a016_b04_authorization_batch import execute_b04, _build_inventory, _scenarios


class TraderRM002A016B04AuthorizationBatchTests(unittest.TestCase):
    def test_inventory_freezes_only_resolved_classifications(self):
        inventory = _build_inventory("candidate")
        self.assertEqual(inventory["completion"], "PASS")
        self.assertEqual(inventory["summary"]["UNRESOLVED"], 0)
        self.assertTrue(any(item["group"] == "GROUP-A" for item in inventory["items"]))
        self.assertTrue(any(item["group"] == "GROUP-E" for item in inventory["items"]))

    def test_execution_scope_excludes_group_f_and_g(self):
        with TemporaryDirectory() as temp_dir:
            result = execute_b04(Path(temp_dir))
            executed_groups = set(result["B04-002"]) | set(result["B04-003"])
            self.assertEqual(executed_groups, {"GROUP-A", "GROUP-B", "GROUP-C", "GROUP-D", "GROUP-E"})
            self.assertNotIn("INTERRUPTED", result["B04-004"]["participating_executions"])
            self.assertNotIn("UNKNOWN", result["B04-004"]["participating_executions"])

    def test_all_execution_scenarios_have_requirement_and_proof_mapping(self):
        executed = [item for item in _scenarios("candidate") if item.group in {"GROUP-A", "GROUP-B", "GROUP-C", "GROUP-D", "GROUP-E"}]
        self.assertGreater(len(executed), 0)
        for scenario in executed:
            self.assertTrue(scenario.requirement_id)
            self.assertTrue(scenario.proof_id)
            self.assertNotEqual(scenario.scope_classification, "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
