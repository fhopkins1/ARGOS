import json
from pathlib import Path
import unittest


S06_PATH = Path("Documentation/BROKER_RM001_S06_TRACEABILITY_READINESS/broker_rm001_s06_traceability_readiness_baseline.json")
S07_PATH = Path("Documentation/BROKER_RM001_S07_GOVERNANCE_CLOSURE/broker_rm001_s07_governance_closure_baseline.json")


class BrokerRM001S07GovernanceClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.s06 = json.loads(S06_PATH.read_text(encoding="utf-8"))
        cls.s07 = json.loads(S07_PATH.read_text(encoding="utf-8"))

    def test_candidate_includes_prior_governance_artifacts(self) -> None:
        candidate = self.s07["b07_001_constitutional_candidate_registry"]
        included = set(candidate["included_artifacts"])

        self.assertTrue({"BROKER-ART-S02", "BROKER-ART-S03", "BROKER-ART-S04", "BROKER-ART-S05", "BROKER-ART-S06", "BROKER-ART-S07"}.issubset(included))
        self.assertEqual(candidate["candidate_status"], "READY_FOR_INDEPENDENT_ECS003_REAUDIT")
        self.assertEqual(candidate["unresolved_constitutional_inconsistencies"], 0)

    def test_s07_preserves_certification_independence(self) -> None:
        self.assertEqual(self.s07["certification_verdict"], "NOT_CERTIFICATION_PASS")
        acceptance = self.s07["b07_003_constitutional_acceptance_registry"]

        self.assertIn("Enterprise Certification Authority", acceptance["acceptance_authority"])
        self.assertEqual(acceptance["rejection_authority"], "Enterprise Certification Authority")
        self.assertFalse(self.s07["runtime_behavior_modified"])
        self.assertFalse(self.s07["repository_wide_verification_executed"])

    def test_readiness_has_no_blockers_waivers_or_exceptions(self) -> None:
        self.assertEqual(self.s07["b07_002_certification_blocker_registry"]["open_blocker_count"], 0)
        self.assertFalse(self.s07["b07_003_constitutional_waiver_registry"]["waivers_present"])
        self.assertFalse(self.s07["b07_003_constitutional_exception_registry"]["exceptions_present"])

    def test_final_publication_is_ready_for_independent_reaudit(self) -> None:
        baseline = self.s07["b07_004_final_constitutional_certification_baseline"]
        completion = self.s07["series_completion_report"]

        self.assertEqual(baseline["readiness_status"], self.s06["b06_004_final_constitutional_readiness_baseline"]["certification_readiness_status"])
        self.assertEqual(baseline["certification_verdict"], "NOT_CERTIFICATION_PASS")
        self.assertEqual(completion["unresolved_governance_deficiencies"], 0)
        self.assertTrue(completion["ready_for_independent_ecs003_reaudit"])

        for order_id in ("B07-001", "B07-002", "B07-003", "B07-004"):
            self.assertEqual(completion[order_id], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
