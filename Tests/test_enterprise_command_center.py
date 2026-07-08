from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import create_runtime  # noqa: E402


class EnterpriseCommandCenterTests(unittest.TestCase):
    def test_ecc_state_contains_every_enterprise_entity_and_drilldown(self) -> None:
        runtime = create_runtime()

        state = runtime.state()

        self.assertIn("ecc", state)
        self.assertEqual(
            {org["name"] for org in state["ecc"]["organizations"]},
            {"Executive", "Seeker", "Analyst", "Risk", "Trader", "Historian", "Librarian", "Academy", "Infrastructure"},
        )
        executive = state["ecc"]["drilldown"]["Executive"]
        self.assertEqual(executive["organization"], "Executive")
        self.assertTrue(executive["offices"])
        first_workflow = executive["offices"][0]["workflows"][0]
        self.assertTrue(first_workflow["tasks"][0]["supporting_evidence_ids"])
        self.assertTrue(first_workflow["tasks"][0]["audit_log_ids"])

    def test_commander_actions_update_state_and_generate_audit_records(self) -> None:
        runtime = create_runtime()

        paused = runtime.commander_action("pause_organization", "Risk")
        resumed = runtime.commander_action("resume_organization", "Risk")

        risk_after_pause = next(org for org in paused["ecc"]["organizations"] if org["name"] == "Risk")
        risk_after_resume = next(org for org in resumed["ecc"]["organizations"] if org["name"] == "Risk")
        self.assertEqual(risk_after_pause["current_status"], "PAUSED")
        self.assertEqual(risk_after_resume["current_status"], "NOMINAL")
        self.assertEqual(resumed["auditEventCount"], 22)
        self.assertEqual(len(resumed["ecc"]["commanderActions"]), 2)

    def test_mode_schedule_review_history_and_export_are_audited(self) -> None:
        runtime = create_runtime()

        runtime.commander_action("change_operating_mode", "Trader", "PAPER_TRADING")
        runtime.commander_action("configure_schedule", "Trader", "continuous monitoring")
        runtime.commander_action("review_evidence", "Trader")
        runtime.commander_action("inspect_workflows", "Trader")
        runtime.commander_action("view_historical_activity", "Trader")
        exported = runtime.export_ecc_report()

        trader = next(org for org in exported["ecc"]["organizations"] if org["name"] == "Trader")
        self.assertEqual(trader["operating_mode"], "PAPER_TRADING")
        self.assertIn("eccReport", exported)
        self.assertGreaterEqual(exported["auditEventCount"], 25)

    def test_paper_self_training_is_visible_to_ecc(self) -> None:
        runtime = create_runtime()

        state = runtime.start_paper_self_training()

        trader = next(org for org in state["ecc"]["organizations"] if org["name"] == "Trader")
        self.assertEqual(state["ecc"]["tradingStatus"], "PAPER ACTIVE")
        self.assertEqual(state["ecc"]["paperPortfolioStatus"], "ACTIVE")
        self.assertEqual(trader["current_workflow"], "Paper Trading Workflow")

    def test_ui_exposes_ecc_controls_and_endpoints(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("Enterprise Command Center", html)
        self.assertIn("ecc-org-select", html)
        self.assertIn("Export ECC Report", html)
        self.assertIn("/api/ecc/action", js)
        self.assertIn("/api/ecc/export", js)


if __name__ == "__main__":
    unittest.main()
