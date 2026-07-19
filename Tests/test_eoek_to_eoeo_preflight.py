from __future__ import annotations

from pathlib import Path
import unittest

from argos.control_panel.final_remediation_preflight import (
    FINAL_REMEDIATION_ORDERS,
    execute_eoek_preflight,
    execute_eoel_preflight,
    execute_eoem_preflight,
    execute_eoen_preflight,
    execute_eoeo_preflight,
    execute_final_remediation_preflight,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class FinalRemediationPreflightTests(unittest.TestCase):
    def test_eoek_is_blocked_by_eoej_fail(self) -> None:
        payload = execute_eoek_preflight("TEST-COMMIT", repo_root=REPOSITORY_ROOT)

        self.assertEqual(payload["certification"]["verdict"], "FAIL")
        self.assertFalse(payload["certification"]["entryGatePassed"])
        self.assertFalse(payload["certification"]["campaignStarted"])
        self.assertIn("EO-EJ", {item["orderId"] for item in payload["entry_gate"]["blockers"]})

    def test_wall_clock_campaign_orders_do_not_fabricate_duration(self) -> None:
        for executor in (execute_eoel_preflight, execute_eoem_preflight, execute_eoen_preflight):
            with self.subTest(executor=executor.__name__):
                payload = executor("TEST-COMMIT", repo_root=REPOSITORY_ROOT)

                self.assertEqual(payload["certification"]["verdict"], "FAIL")
                self.assertEqual(payload["certification"]["observedDurationSeconds"], 0)
                self.assertTrue(payload["certification"]["noDurationFabricated"])
                self.assertFalse(payload["certification"]["campaignStarted"])

    def test_eoeo_reports_controlled_remediation_not_paper_certified(self) -> None:
        payload = execute_eoeo_preflight("TEST-COMMIT", repo_root=REPOSITORY_ROOT)

        self.assertEqual(payload["certification"]["verdict"], "FAIL")
        self.assertEqual(payload["certification"]["readinessClassification"], "CONTROLLED REMEDIATION")
        self.assertTrue(payload["certification"]["noHistoricalEvidencePromoted"])

    def test_every_declared_artifact_has_payload(self) -> None:
        for order_id, order in FINAL_REMEDIATION_ORDERS.items():
            with self.subTest(order_id=order_id):
                payload = execute_final_remediation_preflight(order_id, "TEST-COMMIT", repo_root=REPOSITORY_ROOT)
                keys = {artifact.rsplit(".", 1)[0] for artifact in order.artifact_names}

                self.assertLessEqual(keys, set(payload))
                self.assertIn("certification", payload)


if __name__ == "__main__":
    unittest.main()
