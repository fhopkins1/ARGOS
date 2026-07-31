from __future__ import annotations

import json
import unittest

from Scripts import historian_mo001_information_journey_hardening as campaign


class HistorianMO001InformationJourneyHardeningTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        campaign.generate()

    def _load(self, name: str):
        return json.loads((campaign.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_all_fifteen_modification_orders_are_completed(self) -> None:
        manifest = self._load("campaign_manifest.json")
        self.assertEqual(15, manifest["modification_orders_completed"])
        results = self._load("modification_order_results.json")
        self.assertEqual(15, len(results))
        self.assertTrue(all(result["status"] == "COMPLETE" for result in results))

    def test_baseline_preserves_custody_only_historian(self) -> None:
        baseline = self._load("enterprise_information_journey_baseline.json")
        self.assertEqual("Historian Office", baseline["constitutional_owner"])
        for prohibited in ("learn", "infer", "summarize", "optimize", "recommend", "rank", "predict", "authorize", "modify_historical_records"):
            self.assertIn(prohibited, baseline["historian_prohibitions"])
        self.assertIn("Journey Graph Edge", baseline["canonical_record_families"])
        self.assertIn("UNKNOWN_CAUSE", baseline["missing_information_states"])

    def test_closure_report_does_not_modify_implementation_or_authorize_learning(self) -> None:
        report = self._load("enterprise_information_journey_constitutional_hardening_report.json")
        self.assertFalse(report["implementation_evaluated"])
        self.assertFalse(report["implementation_modified"])
        self.assertFalse(report["constitutional_authority_weakened"])
        self.assertFalse(report["learning_or_recommendation_authorized"])
        self.assertEqual(
            "PERMANENT_CONSTITUTIONAL_BASELINE_ESTABLISHED_FOR_ENTERPRISE_HISTORY",
            report["final_status"],
        )


if __name__ == "__main__":
    unittest.main()
