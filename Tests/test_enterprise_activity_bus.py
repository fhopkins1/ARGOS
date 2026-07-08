from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import EnterpriseActivityBus, create_runtime  # noqa: E402
from argos.foundation.audit import AuditService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, canonical_schemas  # noqa: E402


class EnterpriseActivityBusTests(unittest.TestCase):
    def test_bus_normalizes_archives_audits_and_delivers_events(self) -> None:
        audit = AuditService()
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        bus = EnterpriseActivityBus(audit, persistence)

        event = bus.publish(
            organization="Trader",
            office="Order Management",
            workflow="Order Lifecycle",
            task_identifier="TASK-001",
            event_category="EXECUTION",
            severity="NOTICE",
            summary="Order queued",
            detailed_description="Validated paper order was queued for broker simulation.",
            supporting_evidence=("DOC-001",),
            correlation_identifier="CORR-001",
            asset="SPY",
            portfolio="Paper Portfolio",
            status="QUEUED",
        )
        snapshot = bus.snapshot()

        self.assertEqual(event.event_id, "EAB-000001")
        self.assertEqual(event.severity, "NOTICE")
        self.assertEqual(event.audit_identifier, "AE-000001")
        self.assertEqual(snapshot["health"]["eventOrdering"], "CHRONOLOGICAL")
        self.assertGreaterEqual(len(snapshot["deliveries"]), 2)
        self.assertEqual(snapshot["detections"]["lostEvents"], 0)

    def test_bus_filters_by_commander_supported_fields(self) -> None:
        bus = EnterpriseActivityBus(AuditService(), InMemoryPersistenceRepository(canonical_schemas()))
        bus.publish(
            organization="Risk",
            office="Portfolio",
            workflow="Risk Fusion",
            task_identifier="TASK-RISK",
            event_category="RISK",
            severity="WARNING",
            summary="Risk alert",
            detailed_description="Portfolio risk watch detected.",
            correlation_identifier="CORR-RISK",
            asset="QQQ",
            portfolio="Paper Portfolio",
            status="OPEN",
        )
        bus.publish(
            organization="Academy",
            office="Instruction",
            workflow="Lesson Update",
            task_identifier="TASK-EDU",
            event_category="EDUCATION",
            severity="INFO",
            summary="Lesson refreshed",
            detailed_description="Validated lesson package was refreshed.",
            correlation_identifier="CORR-EDU",
            status="PUBLISHED",
        )

        risk_events = bus.snapshot({"organization": "Risk", "severity": "WARNING", "status": "OPEN"})["events"]

        self.assertEqual(len(risk_events), 1)
        self.assertEqual(risk_events[0]["organization"], "Risk")

    def test_bus_detects_duplicates_and_missing_correlation(self) -> None:
        bus = EnterpriseActivityBus(AuditService(), InMemoryPersistenceRepository(canonical_schemas()))
        kwargs = {
            "organization": "Executive",
            "office": "Commander",
            "workflow": "Decision",
            "task_identifier": "TASK-DUP",
            "event_category": "COMMAND",
            "severity": "NOTICE",
            "summary": "Duplicate candidate",
            "detailed_description": "Same command submitted twice.",
            "correlation_identifier": "CORR-DUP",
        }
        bus.publish(**kwargs)
        bus.publish(**kwargs)
        bus.publish(
            organization="Infrastructure",
            office="Runtime",
            workflow="Health",
            task_identifier="TASK-NOCORR",
            event_category="INFRASTRUCTURE",
            severity="INFO",
            summary="No correlation supplied",
            detailed_description="Bus supplied deterministic fallback correlation.",
        )

        snapshot = bus.snapshot()

        self.assertEqual(snapshot["detections"]["duplicateEvents"], 1)
        self.assertEqual(snapshot["detections"]["brokenCorrelations"], 1)

    def test_runtime_publishes_control_actions_to_eab(self) -> None:
        runtime = create_runtime()

        state = runtime.start_paper_self_training()

        self.assertIn("eab", state)
        self.assertGreaterEqual(len(state["eab"]["events"]), 9)
        self.assertTrue(any(event["summary"] == "Paper self-training started" for event in state["eab"]["events"]))
        self.assertTrue(any(event["subscriber"] == "Commander" for event in state["eab"]["deliveries"]))

    def test_ui_exposes_eab_controls_and_filter_endpoint(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("Enterprise Activity Bus", html)
        self.assertIn("eab-filter-org", html)
        self.assertIn("Canonical Event Stream", html)
        self.assertIn("/api/eab/events", js)


if __name__ == "__main__":
    unittest.main()
