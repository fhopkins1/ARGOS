from __future__ import annotations

from pathlib import Path
import unittest

from argos.control_panel.full_suite_failure_timeout_elimination import EOEEOutcome, execute_eoee_certification


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class EOEEFullSuiteFailureTimeoutEliminationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = execute_eoee_certification(
            "TEST-COMMIT",
            repo_root=REPOSITORY_ROOT,
            campaign_results=(
                {
                    "campaignIndex": 1,
                    "complete": False,
                    "terminalOutcome": EOEEOutcome.TIMEOUT.value,
                    "visibleFailures": "F",
                    "visibleErrors": "E",
                    "summary": "bounded baseline exceeded audit window",
                },
            ),
        )

    def test_denominator_discovers_required_internal_tests(self) -> None:
        collection = self.payload["collection_results"]

        self.assertGreaterEqual(collection["discoveredTestCount"], 1200)
        self.assertEqual(collection["discoveredTestCount"], collection["requiredInternalCount"])

    def test_focused_synthetic_truth_failure_is_closed_by_current_boundary(self) -> None:
        focused = self.payload["focused_failure_analysis"]

        self.assertEqual(focused["currentOutcome"], EOEEOutcome.PASS.value)
        self.assertIn("NonProductionMarketDataProvider", focused["rootCause"])

    def test_timeout_and_visible_failures_block_certification_pass(self) -> None:
        certification = self.payload["certification"]
        timeout = self.payload["timeout_root_cause_report"]

        self.assertEqual(certification["verdict"], "FAIL")
        self.assertTrue(timeout["timeoutCampaigns"])
        self.assertIn("full-suite campaign adverse outcomes remain", certification["failReasons"])

    def test_result_accounting_refuses_partial_campaign_completion(self) -> None:
        accounting = self.payload["result_accounting"]

        self.assertFalse(accounting["accountingReconciled"])
        self.assertEqual(accounting["completeCampaigns"], 0)

    def test_adverse_evidence_blocks_pass_gate(self) -> None:
        matrix = self.payload["test_certification_matrix"]

        self.assertEqual(matrix["boundedSuiteGate"], "BLOCKED")
        self.assertEqual(matrix["adverseCampaignCount"], 1)

    def test_wall_clock_endurance_is_not_counted_as_bounded_internal_pass(self) -> None:
        report = self.payload["randomness_and_clock_report"]

        self.assertTrue(report["wallClockEnduranceAssignedToEOEF"])


if __name__ == "__main__":
    unittest.main()
