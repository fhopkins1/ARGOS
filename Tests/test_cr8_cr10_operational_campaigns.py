from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.cr_audit_closure import (  # noqa: E402
    execute_cr10_level3_paper_candidate_audit,
    execute_cr8_level2_campaign_a_audit,
)


def cr7_payload() -> dict:
    return {
        "repositoryCommit": "TEST-COMMIT",
        "verdict": "INCOMPLETE",
        "predecessorResults": {
            "cr1": {"orderId": "CR-1", "verdict": "FAIL", "commit": "TEST-COMMIT"},
            "cr2": {"orderId": "CR-2", "verdict": "INCOMPLETE", "commit": "TEST-COMMIT"},
            "cr3": {"orderId": "CR-3", "verdict": "INCOMPLETE", "commit": "TEST-COMMIT"},
            "cr4": {"orderId": "CR-4", "verdict": "INCOMPLETE", "commit": "TEST-COMMIT"},
            "cr5": {"orderId": "CR-5", "verdict": "INCOMPLETE", "commit": "TEST-COMMIT"},
            "cr6": {"orderId": "CR-6", "verdict": "INCOMPLETE", "commit": "TEST-COMMIT"},
        },
    }


class CR8CR10OperationalCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cr8 = execute_cr8_level2_campaign_a_audit(REPOSITORY_ROOT, commit="TEST-COMMIT", cr7_payload=cr7_payload())
        cls.cr10 = execute_cr10_level3_paper_candidate_audit(REPOSITORY_ROOT, commit="TEST-COMMIT", cr8_payload=cls.cr8)

    def test_cr8_defines_level2_campaign_a_without_launching_when_blocked(self) -> None:
        payload = self.cr8

        self.assertEqual("CR-8", payload["orderId"])
        self.assertEqual("INCOMPLETE", payload["verdict"])
        self.assertEqual(7200, payload["campaignConfiguration"]["required_duration_seconds"])
        self.assertEqual("WALL_CLOCK_MONOTONIC", payload["campaignConfiguration"]["duration_mode"])
        self.assertEqual("PREFLIGHT_BLOCKED", payload["campaignAttempts"][0]["status"])
        self.assertEqual(0, payload["campaignAttempts"][0]["qualifyingDurationSeconds"])

    def test_cr8_records_activity_monitoring_and_reconciliation_requirements(self) -> None:
        payload = self.cr8

        self.assertIn("scheduler stability", payload["monitoringPlan"]["domains"])
        self.assertIn("minimums", payload["activityFloor"])
        self.assertIn("workflowEquation", payload["reconciliationPlan"])
        self.assertFalse(payload["baselineState"]["captured"])
        self.assertFalse(payload["runtimeReadiness"]["ready"])

    def test_cr10_blocks_without_cr9_and_does_not_claim_paper_candidate(self) -> None:
        payload = self.cr10

        self.assertEqual("CR-10", payload["orderId"])
        self.assertEqual("INCOMPLETE", payload["verdict"])
        self.assertEqual(28800, payload["campaignConfiguration"]["required_duration_seconds"])
        self.assertEqual("CR-9", payload["predecessorResults"]["cr9"]["orderId"])
        self.assertEqual("INCOMPLETE", payload["predecessorResults"]["cr9"]["verdict"])
        self.assertFalse(payload["paperCandidateQualification"]["qualified"])

    def test_cr10_contains_required_overnight_phase_and_morning_reconciliation_models(self) -> None:
        payload = self.cr10
        phases = {item["phase"] for item in payload["overnightPhases"]}

        self.assertEqual(6, len(payload["overnightPhases"]))
        self.assertIn("Morning Reconciliation", phases)
        self.assertIn("Controlled Shutdown", phases)
        self.assertIn("created = completed", payload["morningReconciliationPlan"]["requiredEquation"])
        self.assertIn("opening cash", payload["financialReconciliationPlan"]["equation"])


if __name__ == "__main__":
    unittest.main()
