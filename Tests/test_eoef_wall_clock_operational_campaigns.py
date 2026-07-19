from __future__ import annotations

from pathlib import Path
import unittest

from argos.control_panel.wall_clock_operational_campaigns import EOEFCampaignStatus, execute_eoef_certification


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class EOEFWallClockOperationalCampaignsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = execute_eoef_certification("TEST-COMMIT", repo_root=REPOSITORY_ROOT)

    def test_preflight_blocks_campaign_launch_when_eoee_fails(self) -> None:
        preflight = self.payload["preflight"]
        gates = {item["gateId"]: item for item in preflight["gates"]}

        self.assertFalse(preflight["preflightPassed"])
        self.assertEqual(gates["EO-EE"]["status"], "BLOCKED")
        self.assertEqual(gates["BOUNDED_INTERNAL_SUITE"]["status"], "BLOCKED")

    def test_level2_and_level3_are_not_fabricated(self) -> None:
        self.assertEqual(self.payload["level2_campaign_a"]["status"], EOEFCampaignStatus.PREFLIGHT_BLOCKED.value)
        self.assertEqual(self.payload["level2_campaign_a"]["realElapsedSeconds"], 0)
        self.assertEqual(self.payload["level2_campaign_b"]["status"], EOEFCampaignStatus.PREFLIGHT_BLOCKED.value)
        self.assertEqual(self.payload["level3"]["status"], EOEFCampaignStatus.PREFLIGHT_BLOCKED.value)

    def test_accelerated_evidence_is_not_labeled_as_level2_or_level3(self) -> None:
        static = self.payload["static_assurance"]

        self.assertFalse(static["acceleratedEvidenceLabeledAsLevel2Or3"])
        self.assertTrue(static["elapsedDurationMayNotBeInferred"])

    def test_certification_is_fail_until_preflight_gate_is_green(self) -> None:
        certification = self.payload["certification"]

        self.assertEqual(certification["verdict"], "FAIL")
        self.assertFalse(certification["preflightPassed"])
        self.assertEqual(certification["level2CampaignsPassed"], 0)
        self.assertEqual(certification["level3CampaignsPassed"], 0)


if __name__ == "__main__":
    unittest.main()
