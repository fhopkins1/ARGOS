from __future__ import annotations

import unittest

from argos.control_panel.trace_closure_final import (
    SyntheticTruthTaxonomy,
    TCRejectionCode,
    execute_tc005_certification,
    execute_tc006_certification,
    execute_tc007_certification,
    execute_tc008_certification,
)


class TC005ResidualSyntheticTruthClosureTests(unittest.TestCase):
    def test_tc005_taxonomy_and_rejection_codes_are_complete(self) -> None:
        payload = execute_tc005_certification("TEST-COMMIT")

        taxonomy = set(payload["truth_taxonomy"]["taxonomy"])
        codes = set(payload["static_assurance"]["rejectionCodesPresent"])

        self.assertIn(SyntheticTruthTaxonomy.PROOF_DOMAIN_CONTAMINATION.value, taxonomy)
        self.assertIn(TCRejectionCode.TRACE_FABRICATION_REJECTED.value, codes)
        self.assertIn(TCRejectionCode.NO_OP_PRODUCTION_SUCCESS_REJECTED.value, codes)

    def test_tc005_closes_residual_paths_without_promoting_external_absence(self) -> None:
        payload = execute_tc005_certification("TEST-COMMIT")

        self.assertEqual(payload["certification"]["verdict"], "INCOMPLETE")
        self.assertEqual(payload["residual_finding_closure"]["openMajorFindings"], 0)
        self.assertEqual(payload["unsafe_fallback_inventory"]["openUnsafeFallbacks"], 0)
        self.assertEqual(payload["proof_domain_attack_results"]["acceptedAttackCount"], 0)
        self.assertIn("External provider", payload["certification"]["blockingReasons"][0])


class TC006FullSuiteDeterminismTests(unittest.TestCase):
    def test_tc006_consumes_adverse_full_suite_evidence(self) -> None:
        payload = execute_tc006_certification("TEST-COMMIT")

        self.assertEqual(payload["certification"]["verdict"], "FAIL")
        self.assertEqual(payload["full_suite_results"]["status"], "FAIL")
        self.assertTrue(payload["full_suite_results"]["adverseEvidenceConsumed"])
        self.assertFalse(payload["full_suite_results"]["terminalOutcomeForEveryRequiredTest"])

    def test_tc006_does_not_reclassify_wall_clock_as_internal_suite(self) -> None:
        payload = execute_tc006_certification("TEST-COMMIT")

        self.assertTrue(payload["test_classification"]["wallClockEnduranceDeferredToTC007"])
        self.assertFalse(payload["dependency_inventory"]["externalDependenciesRequiredForInternalSuite"])


class TC007WallClockEnduranceTests(unittest.TestCase):
    def test_tc007_does_not_promote_accelerated_endurance_to_wall_clock(self) -> None:
        payload = execute_tc007_certification("TEST-COMMIT")

        self.assertEqual(payload["certification"]["verdict"], "INCOMPLETE")
        self.assertTrue(payload["certification"]["acceleratedEnduranceCompleted"])
        self.assertFalse(payload["certification"]["wallClockExtendedRunCompleted"])
        self.assertFalse(payload["wall_clock_proof"]["actualWallClockDurationProven"])
        self.assertFalse(payload["wall_clock_proof"]["acceleratedEventTimeSubstitutedForWallClock"])

    def test_tc007_reports_missing_required_campaigns(self) -> None:
        payload = execute_tc007_certification("TEST-COMMIT")

        self.assertEqual(payload["campaign_inventory"]["qualifyingWallClockLevel2Campaigns"], 0)
        self.assertEqual(payload["campaign_inventory"]["qualifyingWallClockLevel3Campaigns"], 0)
        self.assertFalse(payload["restart_campaign"]["requiredRestartCampaignCompleted"])
        self.assertFalse(payload["failure_injection_campaign"]["requiredFailureInjectionsCompleted"])


class TC008IndependentTraceClosureTests(unittest.TestCase):
    def test_tc008_inherits_prior_trace_blockers(self) -> None:
        payload = execute_tc008_certification("TEST-COMMIT")

        self.assertEqual(payload["certification"]["verdict"], "FAIL")
        self.assertGreater(payload["certification"]["blockerCount"], 0)
        self.assertTrue(payload["contradiction_report"]["adverseEvidencePrecedenceApplied"])
        self.assertEqual(payload["certification_matrix"]["TC-006"]["verdict"], "FAIL")

    def test_tc008_does_not_overstate_readiness(self) -> None:
        payload = execute_tc008_certification("TEST-COMMIT")

        self.assertEqual(payload["readiness_classification"]["classification"], "Not Certified")
        self.assertFalse(payload["market_data_review"]["externalProviderCertified"])
        self.assertFalse(payload["financial_lifecycle_review"]["externalBrokerCertified"])
        self.assertFalse(payload["endurance_review"]["level3Completed"])


if __name__ == "__main__":
    unittest.main()
