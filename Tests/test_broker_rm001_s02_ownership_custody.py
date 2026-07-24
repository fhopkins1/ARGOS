import json
from pathlib import Path
import unittest


BASELINE_PATH = Path("Documentation/BROKER_RM001_S02_OWNERSHIP_CUSTODY/broker_rm001_s02_ownership_baseline.json")


class BrokerRM001S02OwnershipCustodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    def test_every_object_has_exactly_one_owner(self) -> None:
        objects = self.baseline["b02_001_object_inventory"]

        self.assertGreater(len(objects), 0)
        for item in objects:
            self.assertTrue(item["object_id"])
            self.assertTrue(item["canonical_name"])
            self.assertIsInstance(item["constitutional_owner"], str)
            self.assertNotIn("/", item["constitutional_owner"])
            self.assertFalse(item["shared_ownership_candidate"])

    def test_custody_covers_every_object(self) -> None:
        object_ids = {item["object_id"] for item in self.baseline["b02_001_object_inventory"]}
        custody_ids = {
            object_id
            for custody in self.baseline["b02_002_custody_registry"]
            for object_id in custody["objects"]
        }

        self.assertEqual(object_ids, custody_ids)

    def test_transfer_rules_prohibit_implied_ownership_transfer(self) -> None:
        transfer_rules = " ".join(item["rule"] for item in self.baseline["b02_003_ownership_transfer_registry"])

        self.assertIn("shall not imply ownership transfer", transfer_rules)
        self.assertTrue(self.baseline["b02_004_final_constitutional_ownership_baseline"]["ready_for_series_3"])

    def test_integrity_report_closes_duplicates_and_orphans(self) -> None:
        report = self.baseline["b02_004_ownership_reconciliation_report"]

        self.assertEqual(report["duplicate_ownership_count"], 0)
        self.assertEqual(report["orphaned_object_count"], 0)
        self.assertEqual(report["shared_ownership_candidates_remaining"], 0)
        self.assertFalse(report["runtime_behavior_modified"])
        self.assertFalse(report["repository_wide_verification_executed"])

    def test_all_b02_orders_are_complete(self) -> None:
        report = self.baseline["series_completion_report"]

        self.assertEqual(report["B02-001"], "COMPLETE")
        self.assertEqual(report["B02-002"], "COMPLETE")
        self.assertEqual(report["B02-003"], "COMPLETE")
        self.assertEqual(report["B02-004"], "COMPLETE")
        self.assertEqual(report["unresolved_ownership_or_custody_decisions"], 0)


if __name__ == "__main__":
    unittest.main()
