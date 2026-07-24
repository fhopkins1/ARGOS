import unittest

from argos.trader_rm002a016_b03_runner import (
    BATCH_ID,
    DECLARED_PRIOR_MISSING_JSON_POPULATION,
    MODULE_SPECS,
    affected_module_inventory,
)


class TraderRM002A016B03RunnerTests(unittest.TestCase):
    def test_inventory_is_limited_to_b03_module_population(self) -> None:
        inventory = affected_module_inventory()
        modules = {row["immutable_module_identifier"] for row in inventory["records"]}

        self.assertEqual("TRADER-RM-002A-016-B03", BATCH_ID)
        self.assertEqual(len(MODULE_SPECS), inventory["total_modules"])
        self.assertIn("Tests.test_cic02_recovery_foundation", modules)
        self.assertIn("Tests.test_cr6_cr7_certification_artifacts", modules)
        self.assertIn("Tests.test_css_continuous_certification", modules)
        self.assertIn("Tests.test_trader_ecs003_audit", modules)
        self.assertFalse(any("authorization" in module.lower() for module in modules))
        self.assertFalse(any("risk" in module.lower() for module in modules))
        self.assertFalse(any("dashboard" in module.lower() for module in modules))

    def test_inventory_records_prior_missing_json_without_fabricating_raw_records(self) -> None:
        inventory = affected_module_inventory()

        self.assertEqual(44, DECLARED_PRIOR_MISSING_JSON_POPULATION)
        self.assertGreater(inventory["total_tests"], 0)
        self.assertTrue(
            all(row["prior_error_message"] == "module runner did not produce a JSON execution record" for row in inventory["records"])
        )
        self.assertTrue(all(row["timeout"] > 0 for row in inventory["records"]))
        self.assertTrue(all(row["contained_test_identifiers"] for row in inventory["records"]))


if __name__ == "__main__":
    unittest.main()
