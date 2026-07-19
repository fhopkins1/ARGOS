from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.constitutional_certification_series import CSVerdict, run_all_cs_certifications  # noqa: E402


class ConstitutionalCertificationSeriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results = run_all_cs_certifications()

    def test_all_orders_emit_certification_artifacts(self) -> None:
        self.assertEqual(set(self.results), {"CS-001", "CS-002", "CS-003", "CS-004", "CS-005", "CS-006", "CS-007", "CS-008", "CS-009"})
        for order_id, payload in self.results.items():
            self.assertIn("certification", payload)
            self.assertEqual(payload["certification"]["order_id"], order_id)
            self.assertTrue(payload["certification"]["evidence_hash"])

    def test_market_data_certification_preserves_external_provider_incomplete(self) -> None:
        certification = self.results["CS-001"]["certification"]

        self.assertEqual(certification["verdict"], CSVerdict.INCOMPLETE.value)
        self.assertEqual(certification["metrics"]["productionSyntheticPaths"], 0)
        self.assertFalse(certification["metrics"]["externalProviderDeploymentVerified"])

    def test_bridge_office_and_recovery_certify_from_runtime_evidence(self) -> None:
        self.assertEqual(self.results["CS-002"]["certification"]["verdict"], CSVerdict.PASS.value)
        self.assertEqual(self.results["CS-003"]["certification"]["verdict"], CSVerdict.PASS.value)
        self.assertEqual(self.results["CS-005"]["certification"]["verdict"], CSVerdict.PASS.value)
        self.assertEqual(self.results["CS-006"]["certification"]["verdict"], CSVerdict.PASS.value)
        self.assertEqual(self.results["CS-007"]["certification"]["verdict"], CSVerdict.PASS.value)

    def test_financial_lifecycle_is_conditionally_operational_without_external_broker_certification(self) -> None:
        certification = self.results["CS-004"]["certification"]

        self.assertEqual(certification["verdict"], CSVerdict.INCOMPLETE.value)
        self.assertEqual(certification["metrics"]["closedTruthCount"], 1)
        self.assertEqual(certification["metrics"]["openQuantityAfterClose"], 0.0)
        self.assertFalse(certification["metrics"]["externalBrokerCertified"])

    def test_endurance_and_enterprise_readiness_preserve_remaining_blockers(self) -> None:
        endurance = self.results["CS-008"]["certification"]
        enterprise = self.results["CS-009"]["certification"]

        self.assertEqual(endurance["verdict"], CSVerdict.INCOMPLETE.value)
        self.assertFalse(endurance["metrics"]["wallClockExtendedRunCompleted"])
        self.assertEqual(enterprise["verdict"], CSVerdict.INCOMPLETE.value)
        self.assertEqual(enterprise["readiness"], "Conditionally Operational")


if __name__ == "__main__":
    unittest.main()
