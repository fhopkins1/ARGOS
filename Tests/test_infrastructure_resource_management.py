from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import InfrastructureResourceManager, create_runtime  # noqa: E402


class InfrastructureResourceManagementTests(unittest.TestCase):
    def test_runtime_state_contains_resource_cost_and_token_metrics(self) -> None:
        runtime = create_runtime()
        runtime.start_paper_self_training()

        state = runtime.state()

        self.assertIn("infrastructure", state)
        self.assertGreaterEqual(state["infrastructure"]["tokenConsumption"]["dailyTokenUsage"], 0)
        self.assertIn("dailyOperatingCostUsd", state["infrastructure"]["operatingCost"])
        self.assertIn("organizationResourceConsumption", state["infrastructure"])
        self.assertTrue(state["infrastructure"]["history"])

    def test_commander_controls_update_budgets_modes_and_limits(self) -> None:
        runtime = create_runtime()

        state = runtime.configure_infrastructure(10, 100, 25, "Cost Saving", "Trader", 12.5)

        controls = state["infrastructure"]["controls"]
        self.assertEqual(controls["daily_budget_usd"], 10)
        self.assertEqual(controls["monthly_budget_usd"], 100)
        self.assertEqual(controls["runtime_limit_minutes"], 25)
        self.assertEqual(controls["resource_mode"], "Cost Saving")
        self.assertEqual(controls["organization_resource_limits"]["Trader"], 12.5)
        self.assertTrue(any(event["office"] == "AI Resource Management" for event in state["eab"]["events"]))

    def test_optimization_action_is_recorded_and_audited(self) -> None:
        runtime = create_runtime()

        state = runtime.record_infrastructure_optimization("Reduce runtime for noncritical offices")

        self.assertEqual(state["infrastructure"]["metrics"]["optimizationActionCount"], 1)
        self.assertTrue(any(event["summary"].startswith("Optimization action recorded") for event in state["eab"]["events"]))

    def test_alerts_are_generated_for_budget_and_resource_thresholds(self) -> None:
        manager = InfrastructureResourceManager()
        manager.configure_controls(
            daily_budget_usd=1,
            monthly_budget_usd=1,
            runtime_limit_minutes=60,
            resource_mode="Balanced",
            timestamp_utc="2026-07-06T00:00:00Z",
        )

        snapshot = manager.snapshot(
            timestamp_utc="2026-07-06T00:00:01Z",
            resources={"cpu": 91, "memory": 41, "storage": 35, "network": 27},
            costs={
                "today_api_credits_usd": 1.0,
                "month_to_date_api_credits_usd": 1.0,
                "other_operating_expenses_usd": 42.75,
                "total_operating_burn_usd": 43.75,
            },
            scheduler={"summary": {"activeOffices": 2}, "offices": ()},
            eab={"health": {"eventThroughput": 4}, "events": ()},
            organizations=({"name": "Executive"}, {"name": "Trader"}),
            audit_event_count=0,
        )

        categories = {alert["category"] for alert in snapshot["alerts"]}
        self.assertIn("Budget Threshold", categories)
        self.assertIn("Resource Exhaustion", categories)
        self.assertEqual(snapshot["current"]["infrastructure_health"], "DEGRADED")

    def test_ui_and_server_expose_infrastructure_controls(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        self.assertIn("Infrastructure & AI Resource Management", html)
        self.assertIn("infra-configure", html)
        self.assertIn("/api/infrastructure/configure", js)
        self.assertIn("/api/infrastructure/optimization", js)
        self.assertIn("/api/infrastructure/state", server)


if __name__ == "__main__":
    unittest.main()
