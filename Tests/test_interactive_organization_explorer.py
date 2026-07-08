from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import InteractiveOrganizationExplorer, create_runtime  # noqa: E402


class InteractiveOrganizationExplorerTests(unittest.TestCase):
    def test_ioe_constructs_traceable_enterprise_hierarchy(self) -> None:
        runtime = create_runtime()

        state = runtime.state()

        self.assertIn("ioe", state)
        self.assertGreater(state["ioe"]["summary"]["totalNodes"], 300)
        self.assertTrue(any(node["node_type"] == "Enterprise" for node in state["ioe"]["nodes"]))
        self.assertTrue(any(node["node_type"] == "Audit Trail" for node in state["ioe"]["nodes"]))
        self.assertEqual(state["ioe"]["detections"]["orphanedObjects"], 0)

    def test_ioe_syncs_with_eab_cnac_and_filters_nodes(self) -> None:
        runtime = create_runtime()
        runtime.request_real_world_trading()

        filtered = runtime.ioe_explorer({"organization": "Trader", "node_type": "Historical Event"})

        self.assertTrue(filtered["ioe"]["nodes"])
        self.assertTrue(all(node["organization"] == "Trader" for node in filtered["ioe"]["nodes"]))
        self.assertTrue(all(node["node_type"] == "Historical Event" for node in filtered["ioe"]["nodes"]))

    def test_ioe_actions_bookmark_follow_monitor_and_publish_events(self) -> None:
        runtime = create_runtime()

        bookmarked = runtime.ioe_action("bookmark", "ENT-ARGOS")
        followed = runtime.ioe_action("follow", "ENT-ARGOS")
        monitored = runtime.ioe_action("monitor", "ENT-ARGOS")

        self.assertIn("ENT-ARGOS", bookmarked["ioe"]["bookmarks"])
        self.assertIn("ENT-ARGOS", followed["ioe"]["following"])
        self.assertIn("ENT-ARGOS", monitored["ioe"]["monitored"])
        self.assertTrue(any(event["event_category"] == "NAVIGATION" for event in monitored["eab"]["events"]))

    def test_ioe_filter_query_searches_labels_and_status(self) -> None:
        runtime = create_runtime()

        searched = runtime.ioe_explorer({"q": "Trader", "status": "NOMINAL"})

        self.assertTrue(searched["ioe"]["nodes"])
        self.assertTrue(any("Trader" in node["label"] or "Trader" in node["current_activity"] for node in searched["ioe"]["nodes"]))

    def test_ui_exposes_ioe_controls_and_endpoints(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("Interactive Organization Explorer", html)
        self.assertIn("ioe-filter-org", html)
        self.assertIn("ioe-bookmark", html)
        self.assertIn("/api/ioe/explorer", js)
        self.assertIn("/api/ioe/action", js)


if __name__ == "__main__":
    unittest.main()
