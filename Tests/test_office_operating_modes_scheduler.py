from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import OfficeScheduler, OperatingMode, create_runtime  # noqa: E402


class OfficeOperatingModesSchedulerTests(unittest.TestCase):
    def test_scheduler_initializes_every_office_in_exactly_one_mode(self) -> None:
        scheduler = OfficeScheduler()

        snapshot = scheduler.snapshot()

        self.assertGreater(snapshot["summary"]["totalOffices"], 60)
        self.assertGreater(snapshot["summary"]["activeOffices"], 0)
        self.assertTrue(
            all(office["operating_mode"] in {mode.value for mode in OperatingMode} for office in snapshot["offices"])
        )

    def test_configure_activate_suspend_office_are_deterministic(self) -> None:
        scheduler = OfficeScheduler()

        configured = scheduler.configure(
            organization="Risk",
            office="Position",
            operating_mode="Scheduled",
            time_zone="America/New_York",
            business_hours="08:00-17:00",
            scheduled_tasks=("risk-refresh",),
            wake_triggers=("Commander", "Scheduled Event"),
            sleep_triggers=("Workflow Complete", "Runtime Limit"),
            runtime_limit_minutes=90,
            resource_budget_usd=7.5,
        )
        activated = scheduler.activate("Risk", "Position", "Scheduled Event")
        suspended = scheduler.suspend("Risk", "Position", "Workflow Complete")

        self.assertEqual(configured.operating_mode, OperatingMode.SCHEDULED)
        self.assertEqual(activated.wake_count, 1)
        self.assertEqual(suspended.status, "SLEEPING")

    def test_runtime_scheduler_configuration_publishes_eab_event(self) -> None:
        runtime = create_runtime()

        state = runtime.configure_office_schedule("Trader", "Execution", "Business Hours", 11.25, 120)

        execution = next(
            office for office in state["scheduler"]["offices"]
            if office["organization"] == "Trader" and office["office"] == "Execution"
        )
        self.assertEqual(execution["operating_mode"], "Business Hours")
        self.assertTrue(any(event["event_category"] == "SCHEDULING" for event in state["eab"]["events"]))

    def test_runtime_activation_suspension_and_tick_update_analytics(self) -> None:
        runtime = create_runtime()

        activated = runtime.activate_office("Academy", "Finance Tutor")
        runtime.start_paper_self_training()
        suspended = runtime.suspend_office("Academy", "Finance Tutor")

        active_office = next(
            office for office in activated["scheduler"]["offices"]
            if office["organization"] == "Academy" and office["office"] == "Finance Tutor"
        )
        sleeping_office = next(
            office for office in suspended["scheduler"]["offices"]
            if office["organization"] == "Academy" and office["office"] == "Finance Tutor"
        )
        self.assertEqual(active_office["status"], "ACTIVE")
        self.assertEqual(sleeping_office["status"], "SLEEPING")
        self.assertIn("estimatedComputeCostUsd", suspended["scheduler"]["summary"])

    def test_commander_mode_action_configures_all_target_organization_offices(self) -> None:
        runtime = create_runtime()

        state = runtime.commander_action("change_operating_mode", "Seeker", "Dormant")

        seeker_offices = [office for office in state["scheduler"]["offices"] if office["organization"] == "Seeker"]
        self.assertTrue(seeker_offices)
        self.assertTrue(all(office["operating_mode"] == "Dormant" for office in seeker_offices))

    def test_ui_exposes_scheduler_controls_and_endpoints(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("Office Operating Modes & Scheduling", html)
        self.assertIn("scheduler-mode", html)
        self.assertIn("/api/scheduler/configure", js)
        self.assertIn("/api/scheduler/activate", js)
        self.assertIn("/api/scheduler/suspend", js)


if __name__ == "__main__":
    unittest.main()
