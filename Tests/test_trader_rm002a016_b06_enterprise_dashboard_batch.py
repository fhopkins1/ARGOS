import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from argos.trader.rm002a016_b06_enterprise_dashboard_batch import _inventory, _scenarios, execute_b06


class TraderRM002A016B06EnterpriseDashboardBatchTests(unittest.TestCase):
    def test_inventory_freezes_all_b06_populations(self):
        inventory = _inventory("candidate")
        self.assertEqual(inventory["completion"], "PASS")
        self.assertEqual({item["order"] for item in inventory["items"]}, {"B06-002", "B06-003"})
        self.assertGreater(inventory["summary"]["ENTERPRISE_PRECONDITION"], 0)

    def test_all_items_are_mapped(self):
        for scenario in _scenarios("candidate"):
            self.assertTrue(scenario.requirement_id)
            self.assertTrue(scenario.proof_id)
            self.assertNotEqual(scenario.scope_classification, "UNRESOLVED")

    def test_b06_execution_reintegrates_bounded_population(self):
        with TemporaryDirectory() as temp_dir:
            result = execute_b06(Path(temp_dir))
            self.assertEqual(result["B06-004"]["completion"], "PASS")
            self.assertEqual(result["B06-002"]["ERROR"], 0)
            self.assertIn("updated_candidate_verdict", result["B06-004"])


if __name__ == "__main__":
    unittest.main()
