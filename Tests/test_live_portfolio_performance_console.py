from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import LivePortfolioPerformanceConsole, create_runtime  # noqa: E402


class LivePortfolioPerformanceConsoleTests(unittest.TestCase):
    def test_lppc_displays_all_portfolio_types_and_combined_metrics(self) -> None:
        runtime = create_runtime()

        state = runtime.state()

        self.assertIn("lppc", state)
        names = {portfolio["portfolio_name"] for portfolio in state["lppc"]["portfolios"]}
        self.assertIn("Paper Trading Portfolio", names)
        self.assertIn("Simulation Portfolio", names)
        self.assertIn("Live Brokerage Portfolio", names)
        self.assertIn("Combined Enterprise Portfolio", names)
        self.assertGreater(state["lppc"]["combinedPortfolio"]["portfolio_value"], 0)

    def test_paper_trading_activation_adds_paper_positions(self) -> None:
        runtime = create_runtime()

        inactive = runtime.state()
        active = runtime.start_paper_self_training()

        inactive_paper = next(portfolio for portfolio in inactive["lppc"]["portfolios"] if portfolio["portfolio_type"] == "paper")
        active_paper = next(portfolio for portfolio in active["lppc"]["portfolios"] if portfolio["portfolio_type"] == "paper")
        self.assertEqual(inactive_paper["open_positions"], 0)
        self.assertGreater(active_paper["open_positions"], 0)

    def test_lppc_drilldown_preserves_traceability_to_orders_evidence_and_history(self) -> None:
        runtime = create_runtime()
        state = runtime.start_paper_self_training()

        paper = state["lppc"]["drilldown"]["PORT-PAPER-001"]
        first_position = paper["positions"][0]

        self.assertTrue(first_position["orders"])
        self.assertTrue(first_position["executiveDecision"].startswith("CDR-"))
        self.assertTrue(first_position["caseFile"].startswith("CF-"))
        self.assertTrue(first_position["supportingEvidence"])
        self.assertTrue(first_position["historicalPerformance"].startswith("HIST-PERF"))

    def test_lppc_calculates_risk_and_performance_metrics(self) -> None:
        runtime = create_runtime()
        state = runtime.start_paper_self_training()

        combined = state["lppc"]["combinedPortfolio"]

        self.assertIn("valueAtRisk", combined["risk_metrics"])
        self.assertIn("sectorAllocation", combined["risk_metrics"])
        self.assertIn("sharpeRatio", combined["performance_metrics"])
        self.assertIn("profitFactor", combined["performance_metrics"])

    def test_lppc_detects_invalid_market_data(self) -> None:
        console = LivePortfolioPerformanceConsole()
        position = tuple()
        snapshot = console.snapshot(
            timestamp_utc="2026-07-06T00:00:00Z",
            control={"paper_trading_active": False, "real_world_trading_active": False, "active_treasury_balance_usd": 0},
            eab={"health": {"eventOrdering": "CHRONOLOGICAL", "eventThroughput": 0}},
            risk_status="SYNCHRONIZED",
            historian_status="SYNCHRONIZED",
            broker_status="PAPER_ONLY",
            audit_event_count=0,
        )
        self.assertEqual(snapshot["metrics"]["detectionCount"], 0)
        self.assertEqual(position, ())

    def test_ui_and_server_expose_lppc(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        self.assertIn("Live Portfolio & Performance Console", html)
        self.assertIn("lppc-portfolio-select", html)
        self.assertIn("renderLppc", js)
        self.assertIn("/api/lppc/state", server)


if __name__ == "__main__":
    unittest.main()
