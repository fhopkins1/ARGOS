import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from argos.trader.rm002a016_b05_risk_batch import _build_inventory, _scenarios, execute_b05


class TraderRM002A016B05RiskBatchTests(unittest.TestCase):
    def test_b05_inventory_freezes_b05_002_and_b05_003(self):
        inventory = _build_inventory("candidate")
        self.assertEqual(inventory["completion"], "PASS")
        orders = {item["order"] for item in inventory["items"]}
        self.assertEqual(orders, {"B05-002", "B05-003"})
        self.assertGreater(inventory["summary"]["TRADER_DIRECT"], 0)
        self.assertGreater(inventory["summary"]["TRADER_DEPENDENCY"], 0)

    def test_b05_scenarios_have_proof_and_requirement_mapping(self):
        for scenario in _scenarios("candidate"):
            self.assertTrue(scenario.requirement_id)
            self.assertTrue(scenario.proof_id)
            self.assertNotEqual(scenario.scope_classification, "UNRESOLVED")

    def test_b05_execution_produces_bounded_reconciliation(self):
        with TemporaryDirectory() as temp_dir:
            result = execute_b05(Path(temp_dir))
            self.assertEqual(result["B05-004"]["completion"], "PASS")
            self.assertIn("updated_candidate_verdict", result["B05-004"])
            self.assertEqual(result["B05-004"]["counts"]["ERROR"], 0)


if __name__ == "__main__":
    unittest.main()
