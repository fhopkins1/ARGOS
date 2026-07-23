from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.trader_ecs003_audit import build_test_inventory, run_test_module  # noqa: E402


class TraderECS003AuditTests(unittest.TestCase):
    def test_inventory_discovers_repository_tests(self) -> None:
        inventory = build_test_inventory(REPOSITORY_ROOT / "Tests")

        self.assertGreater(inventory["total_tests"], 0)
        self.assertTrue(any(record["test_identifier"].startswith("test_trader_requirement_verifier.") for record in inventory["records"]))
        self.assertEqual(inventory["total_tests"], len(inventory["records"]))

    def test_module_runner_assigns_final_dispositions(self) -> None:
        result = run_test_module("Tests.test_trader_requirement_verifier")
        dispositions = {record["disposition"] for record in result["records"]}

        self.assertTrue(result["successful"])
        self.assertEqual(dispositions, {"PASS"})
        self.assertEqual(result["disposition_counts"]["PASS"], len(result["records"]))


if __name__ == "__main__":
    unittest.main()
