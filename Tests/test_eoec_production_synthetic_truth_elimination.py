from __future__ import annotations

import unittest

from argos.control_panel.production_synthetic_truth_elimination import EO_EC_VERSION, execute_eoec_certification


class EOECProductionSyntheticTruthEliminationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = execute_eoec_certification("TEST-COMMIT")

    def test_preserves_exact_three_major_baseline_findings(self) -> None:
        baseline = self.payload["synthetic_truth_baseline"]
        closures = self.payload["major_finding_closure"]

        self.assertEqual(baseline["priorMajorFindingCount"], 3)
        self.assertEqual({row["finding_id"] for row in closures}, {"SYN-MARKET-002", "SYN-DASHBOARD-001", "SYN-RECOVERY-001"})
        self.assertTrue(all(row["prior_status"] == "UNRESOLVED" for row in closures))

    def test_major_findings_are_structurally_closed_without_decision_reachability(self) -> None:
        closures = self.payload["major_finding_closure"]
        proof = self.payload["negative_reachability_proof"]

        self.assertTrue(all(row["closure_status"] == "STRUCTURALLY_CLOSED_INTERNAL" for row in closures))
        self.assertFalse(any(row["production_decision_reachable"] for row in closures))
        self.assertTrue(proof["internalSyntheticTruthPathsClosed"])
        self.assertFalse(proof["paperRuntimeMayClaimUnavailableExternalTruth"])

    def test_dynamic_attacks_remain_rejected(self) -> None:
        attacks = self.payload["dynamic_attack_results"]

        self.assertEqual(attacks["attackTotal"], 8)
        self.assertEqual(attacks["attackRejected"], 8)
        self.assertTrue(all(row["rejected"] and not row["authoritative_mutation"] for row in attacks["attacks"]))

    def test_market_provider_boundary_has_no_synthetic_fallback(self) -> None:
        boundary = self.payload["market_data_boundary_validation"]
        provider = self.payload["provider_factory_validation"]

        self.assertEqual(boundary["productionReachableSyntheticSources"], ())
        self.assertFalse(provider["mockFallbackEnabled"])
        self.assertFalse(provider["syntheticFallbackEnabled"])
        self.assertFalse(provider["syntheticDefaultProviderConfigured"])

    def test_bridge_and_certification_truth_are_not_runtime_truth(self) -> None:
        bridge = self.payload["bridge_truth_validation"]
        certification = self.payload["certification_truth_validation"]

        self.assertGreater(bridge["canonicalRuntimeExecuted"], 0)
        self.assertTrue(bridge["bridgesRequireDestinationAcceptance"])
        self.assertTrue(certification["certificationCannotCreateRuntimeTruth"])

    def test_verdict_is_incomplete_not_pass_until_external_provider_certified(self) -> None:
        certification = self.payload["certification"]

        self.assertEqual(certification["schemaVersion"], EO_EC_VERSION)
        self.assertEqual(certification["verdict"], "INCOMPLETE")
        self.assertTrue(certification["internalSyntheticTruthPathsClosed"])
        self.assertFalse(certification["externalAuthoritativeProviderCertified"])
        self.assertEqual(certification["failReasons"], ())


if __name__ == "__main__":
    unittest.main()
