from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from argos.broker_ecs003_audit import build_repository_inventory, run_broker_ecs003_audit, run_broker_tests


class BrokerECS003AuditTests(unittest.TestCase):
    def test_inventory_derives_broker_participation(self) -> None:
        inventory = build_repository_inventory()
        paths = {item["path"] for item in inventory["artifacts"]}

        self.assertIn("src/argos/trader/broker_integration.py", paths)
        self.assertIn("Tests/test_broker_integration_office.py", paths)
        self.assertGreater(inventory["participating_artifact_count"], 0)

    def test_focused_broker_tests_execute(self) -> None:
        result = run_broker_tests()

        self.assertGreaterEqual(result["tests_run"], 8)
        self.assertFalse(result["repository_wide_execution_performed"])
        self.assertEqual(result["status"], "PASS")

    def test_audit_package_reports_final_verdict(self) -> None:
        with TemporaryDirectory() as temp_dir:
            result = run_broker_ecs003_audit(Path(temp_dir))

            self.assertEqual(result["phase_i_verdict"], "FAIL")
            self.assertEqual(result["final_verdict"], "FAIL")
            self.assertEqual(result["constitutional_freeze_decision"], "NOT_ELIGIBLE")
            self.assertGreater(result["finding_count"], 0)


if __name__ == "__main__":
    unittest.main()
