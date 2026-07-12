from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import (  # noqa: E402
    ApiExecutionRequest,
    CanonicalEnterpriseRuntime,
    CanonicalRuntimeError,
    CanonicalRuntimeMode,
)


class OR005CanonicalRuntimeTests(unittest.TestCase):
    def test_paper_startup_is_idle_and_duplicate_start_does_not_create_second_loop(self) -> None:
        runtime = CanonicalEnterpriseRuntime()

        first = runtime.start()
        second = runtime.start()

        self.assertEqual(first["mode"], CanonicalRuntimeMode.PAPER_IDLE.value)
        self.assertEqual(second["startCount"], 1)
        self.assertTrue(second["loopStarted"])
        self.assertFalse(second["liveTradingEnabled"])
        self.assertEqual(runtime.stateful_authority_duplicates(), ())

    def test_live_startup_fails_closed(self) -> None:
        runtime = CanonicalEnterpriseRuntime(live_trading_enabled=True)

        with self.assertRaises(CanonicalRuntimeError) as raised:
            runtime.start()

        self.assertEqual(raised.exception.failure.code, "LIVE_TRADING_DISABLED")
        self.assertEqual(runtime.mode, CanonicalRuntimeMode.LIVE_DISABLED)

    def test_scheduled_obligation_uses_series_c_admission_without_creating_financial_truth(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        runtime.start()
        before = runtime.read_only_snapshot()

        admission = runtime.admit_scheduled_obligation("pre_market_readiness", now="2026-07-13T08:15:00Z")
        after = runtime.read_only_snapshot()

        self.assertEqual(admission.status, "ADMITTED")
        self.assertTrue(admission.scheduler_mission_id)
        self.assertTrue(admission.mission_plan_id)
        self.assertTrue(admission.workflow_token_id)
        self.assertTrue(admission.duty_decisions)
        self.assertEqual(after["paperBrokerOrderCount"], before["paperBrokerOrderCount"])
        self.assertEqual(after["positionCount"], before["positionCount"])

    def test_seeker_requires_strategic_mandate(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        runtime.start()

        rejected = runtime.request_seeker_work(mandate_id="missing")
        mandate = runtime.create_strategic_mandate(subject="AI infrastructure", decision="allow")
        accepted = runtime.request_seeker_work(mandate_id=mandate["mandate_id"])

        self.assertFalse(rejected["accepted"])
        self.assertEqual(rejected["failure"]["code"], "MISSING_STRATEGIC_MANDATE")
        self.assertTrue(accepted["accepted"])
        self.assertFalse(accepted["mandate"]["runtime_authored"])

    def test_unreserved_api_request_is_blocked_before_gateway_execution(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        runtime.start()
        response = runtime.execute_api_request(
            ApiExecutionRequest(
                workflow_id="WF",
                workflow_token_id="TOKEN",
                requesting_office="Analyst",
                workflow_stage="Analyst",
                task_type="analysis",
                model="dry-run-model",
                prompt_template_id="template",
                prompt_payload={},
                expected_output_schema=("summary",),
                max_runtime_seconds=5,
                max_cost_usd=0.01,
                max_input_tokens=100,
                max_output_tokens=50,
                audit_identifier="OR005-API-001",
            )
        )

        self.assertFalse(response["allowed"])
        self.assertTrue(response["blocked"])
        self.assertEqual(response["failure"]["code"], "COST_RESERVATION_REQUIRED")

    def test_read_only_snapshot_is_stable(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        runtime.start()

        first = runtime.read_only_digest()
        second = runtime.read_only_digest()

        self.assertEqual(first, second)

    def test_series_c_inventory_resolves_ci_cm_and_co(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        ids = {item.eo_id: item for item in runtime.series_c_inventory()}

        self.assertIn("EO-CI", ids)
        self.assertIn("EO-CM", ids)
        self.assertIn("EO-CO", ids)
        self.assertIn("found_under", ids["EO-CI"].status)
        self.assertIn("gap", ids["EO-CM"].status)
        self.assertEqual(ids["EO-CO"].runtime_attribute, "doctrine_policy")


if __name__ == "__main__":
    unittest.main()
