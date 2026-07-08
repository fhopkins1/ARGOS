from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import CommanderNotificationAlertCenter, create_runtime  # noqa: E402


class CommanderNotificationAlertCenterTests(unittest.TestCase):
    def test_cnac_classifies_event_priority_and_delivery_channels(self) -> None:
        cnac = CommanderNotificationAlertCenter()
        cnac.ingest((
            _event("EAB-000001", 1, "Trader", "Trade Execution", "CRITICAL", "Live gate denied", "TRADING"),
        ))

        snapshot = cnac.snapshot()
        notification = snapshot["notifications"][0]

        self.assertEqual(notification["notification_type"], "Critical Event")
        self.assertEqual(notification["priority"], "Critical")
        self.assertIn("SMS", notification["delivery_channels"])
        self.assertEqual(notification["status"], "UNRESOLVED")
        self.assertEqual(notification["confidence_level"], "HIGH")

    def test_cnac_does_not_duplicate_refresh_ingestion(self) -> None:
        cnac = CommanderNotificationAlertCenter()
        event = _event("EAB-000001", 1, "Risk", "Portfolio", "WARNING", "Risk watch", "RISK")

        cnac.ingest((event,))
        cnac.ingest((event,))

        snapshot = cnac.snapshot()
        self.assertEqual(snapshot["metrics"]["notificationVolume"], 1)
        self.assertEqual(snapshot["detections"]["duplicateNotifications"], 0)

    def test_cnac_filters_acknowledges_escalates_and_generates_briefings(self) -> None:
        cnac = CommanderNotificationAlertCenter()
        cnac.ingest((
            _event("EAB-000001", 1, "Risk", "Portfolio", "WARNING", "Risk watch", "RISK", portfolio="Paper Portfolio"),
            _event("EAB-000002", 2, "Academy", "Instruction", "INFO", "Lesson refreshed", "EDUCATION"),
        ))

        filtered = cnac.snapshot({"organization": "Risk", "priority": "Warning", "portfolio": "Paper Portfolio"})
        acknowledged = cnac.acknowledge(filtered["notifications"][0]["notification_id"])
        cnac.escalate_unresolved()
        briefing = cnac.generate_briefing("Daily Enterprise Report")

        self.assertEqual(len(filtered["notifications"]), 1)
        self.assertEqual(acknowledged.status, "ACKNOWLEDGED")
        self.assertEqual(briefing.briefing_type, "Daily Enterprise Report")
        self.assertEqual(cnac.snapshot()["metrics"]["acknowledged"], 1)

    def test_runtime_generates_cnac_notifications_from_eab_events(self) -> None:
        runtime = create_runtime()

        state = runtime.request_real_world_trading()

        self.assertIn("cnac", state)
        self.assertTrue(any(note["priority"] == "Critical" for note in state["cnac"]["notifications"]))
        self.assertGreaterEqual(state["cnac"]["metrics"]["notificationVolume"], 1)

    def test_runtime_cnac_acknowledge_escalate_and_briefing_paths(self) -> None:
        runtime = create_runtime()
        state = runtime.request_real_world_trading()
        critical = next(note for note in state["cnac"]["notifications"] if note["priority"] == "Critical")

        acknowledged = runtime.acknowledge_notification(critical["notification_id"])
        escalated = runtime.escalate_notifications()
        briefing = runtime.generate_commander_briefing("Market Close Summary")

        self.assertGreaterEqual(acknowledged["cnac"]["metrics"]["acknowledged"], 1)
        self.assertIn("cnac", escalated)
        self.assertEqual(briefing["commanderBriefing"]["briefing_type"], "Market Close Summary")

    def test_ui_exposes_cnac_controls_and_endpoints(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("Commander Notification & Alert Center", html)
        self.assertIn("cnac-filter-priority", html)
        self.assertIn("/api/cnac/notifications", js)
        self.assertIn("/api/cnac/acknowledge", js)
        self.assertIn("/api/cnac/briefing", js)


def _event(
    event_id: str,
    sequence: int,
    organization: str,
    office: str,
    severity: str,
    summary: str,
    category: str,
    portfolio: str = "",
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "sequence": sequence,
        "timestamp_utc": "2026-07-06T12:00:00Z",
        "organization": organization,
        "office": office,
        "workflow": f"{office} Workflow",
        "task_identifier": f"TASK-{sequence:03d}",
        "event_category": category,
        "severity": severity,
        "summary": summary,
        "detailed_description": summary,
        "supporting_evidence": ("DOC-001",),
        "correlation_identifier": f"CORR-{sequence:03d}",
        "audit_identifier": f"AE-{sequence:06d}",
        "asset": "SPY",
        "portfolio": portfolio,
        "case_file_id": f"CF-{9900 + sequence}",
        "status": "RECORDED",
    }


if __name__ == "__main__":
    unittest.main()
