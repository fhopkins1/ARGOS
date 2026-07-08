from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import CommandConsole, create_runtime  # noqa: E402


class CommandConsoleTests(unittest.TestCase):
    def test_command_console_validates_executes_and_archives_paper_command(self) -> None:
        runtime = create_runtime()

        state = runtime.command_console_execute("start_paper_self_training", category="trading", target="Trader")

        latest = state["commandConsole"]["lastResponse"]
        self.assertEqual(latest["command_name"], "start_paper_self_training")
        self.assertEqual(latest["status"], "COMPLETED")
        self.assertEqual(tuple(latest["lifecycle"][-2:]), ("Historical Archive", "Audit Record"))
        self.assertTrue(state["control"]["paper_trading_active"])
        self.assertTrue(any(event["office"] == "Command Console" for event in state["eab"]["events"]))

    def test_live_trading_initiation_is_rejected_by_safety_validation(self) -> None:
        runtime = create_runtime()

        state = runtime.command_console_execute("request_real_world_trading", category="trading", target="Trader")

        latest = state["commandConsole"]["lastResponse"]
        self.assertEqual(latest["status"], "REJECTED")
        self.assertEqual(latest["execution_status"], "NOT_EXECUTED")
        self.assertIn("blocked", latest["detailed_results"].lower())
        self.assertFalse(state["control"]["real_world_trading_active"])

    def test_macro_expands_reusable_commander_commands(self) -> None:
        runtime = create_runtime()

        state = runtime.command_console_macro("Emergency Shutdown")

        history = state["commandConsole"]["commands"]
        names = {record["command_name"] for record in history}
        self.assertIn("halt_real_world_trading", names)
        self.assertIn("halt_paper_self_training", names)
        self.assertIn("halt_user_funds", names)
        self.assertTrue(any(event["summary"] == "Commander macro executed: Emergency Shutdown" for event in state["eab"]["events"]))

    def test_history_search_filters_by_status_and_text(self) -> None:
        runtime = create_runtime()
        runtime.command_console_execute("start_paper_self_training", target="Trader")
        runtime.command_console_execute("request_real_world_trading", target="Trader")

        rejected = runtime.command_console_history({"status": "REJECTED", "q": "real-world"})

        self.assertEqual(len(rejected["commandConsole"]["commands"]), 1)
        self.assertEqual(rejected["commandConsole"]["commands"][0]["command_name"], "request_real_world_trading")

    def test_low_authority_console_rejects_unauthorized_commands(self) -> None:
        console = CommandConsole()

        record = console.issue(
            command_name="halt_real_world_trading",
            category="trading",
            target="Trader",
            detail="unit test",
            amount_usd=0,
            authority_level=1,
            context={
                "system_status": "NOMINAL",
                "organizations": ("Trader",),
                "live_trading_enabled": False,
                "risk_certified": False,
                "budget_status": "GREEN",
                "user_funds_halted": False,
            },
            timestamp_utc="2026-07-06T00:00:00Z",
        )

        self.assertEqual(record.status, "REJECTED")
        self.assertEqual(record.validation.commander_authorization, "DENIED")
        self.assertEqual(console.snapshot()["metrics"]["unauthorizedCommands"], 1)

    def test_ui_exposes_command_console_controls_and_endpoints(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        self.assertIn("Command Console", html)
        self.assertIn("cc-execute", html)
        self.assertIn("cc-macro", js)
        self.assertIn("/api/command/execute", js)
        self.assertIn("/api/command/macro", server)


if __name__ == "__main__":
    unittest.main()
