from __future__ import annotations

import unittest

from argos.control_panel.deterministic_persistence_recovery_closure import EO_ED_VERSION, execute_eoed_certification


class EOEDDeterministicPersistenceRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = execute_eoed_certification("TEST-COMMIT")

    def test_bounded_restart_is_deterministic(self) -> None:
        repeated = self.payload["repeated_restart_results"]
        certification = self.payload["certification"]

        self.assertEqual(repeated["firstDigest"], repeated["secondDigest"])
        self.assertEqual(repeated["deterministicRestartVerdict"], "PASS")
        self.assertEqual(certification["deterministicRestartVerdict"], "PASS")

    def test_recovery_restores_durable_runtime_without_fabrication(self) -> None:
        baseline = self.payload["persistence_baseline"]
        static = self.payload["static_assurance"]

        self.assertGreater(baseline["persistentRecordCount"], 0)
        self.assertIn("runtime", baseline["restoredEntities"])
        self.assertFalse(static["fabricatedTruthDetected"])
        self.assertFalse(static["duplicatePersistentIdentities"])

    def test_financial_recovery_preserves_uncertainty(self) -> None:
        self.assertFalse(self.payload["fill_recovery"]["fillsInferred"])
        self.assertFalse(self.payload["fill_recovery"]["fillsDuplicated"])
        self.assertTrue(self.payload["position_recovery"]["positionsRequireAcceptedFills"])
        self.assertTrue(self.payload["closure_recovery"]["closingFillRequired"])
        self.assertTrue(self.payload["performance_recovery"]["closedPositionTruthRequired"])

    def test_authority_and_bridge_completion_are_not_reconstructed(self) -> None:
        authority = self.payload["authority_recovery"]
        bridge = self.payload["bridge_recovery"]

        self.assertFalse(authority["authorityRecreated"])
        self.assertFalse(authority["delegationReconstructed"])
        self.assertFalse(bridge["bridgeCompletionInferred"])
        self.assertFalse(bridge["destinationAcceptanceInferred"])

    def test_startup_gate_and_audit_chain_pass_for_bounded_state(self) -> None:
        startup = self.payload["startup_gate_validation"]
        audit = self.payload["audit_chain_validation"]

        self.assertTrue(startup["startupRecoveryGatePassesForBoundedDurableState"])
        self.assertFalse(startup["startupBypassAllowed"])
        self.assertTrue(audit["hashChainVerified"])

    def test_verdict_is_incomplete_until_external_reconciliation_is_certified(self) -> None:
        certification = self.payload["certification"]

        self.assertEqual(certification["schemaVersion"], EO_ED_VERSION)
        self.assertEqual(certification["verdict"], "INCOMPLETE")
        self.assertFalse(certification["externalProviderOrBrokerReconciliationCertified"])
        self.assertEqual(certification["failReasons"], ())


if __name__ == "__main__":
    unittest.main()
