import json
from pathlib import Path
import unittest


BASELINE_PATH = Path("Documentation/BROKER_RM002A_S02_BEHAVIORAL_VERIFICATION/broker_rm002a_s02_behavioral_verification_baseline.json")
RAW_LOG_PATH = Path("Documentation/BROKER_RM002A_S02_BEHAVIORAL_VERIFICATION/raw_execution_evidence/bounded_broker_behavioral_unittest.log")


class BrokerRM002AS02BehavioralVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    def test_raw_bounded_execution_evidence_exists_and_passed(self) -> None:
        self.assertTrue(RAW_LOG_PATH.exists())
        raw_log = RAW_LOG_PATH.read_text(encoding="utf-8")
        self.assertIn("Ran 8 tests", raw_log)
        self.assertIn("OK", raw_log)
        self.assertEqual(self.baseline["raw_execution_evidence"][0]["tests_run"], 8)
        self.assertEqual(self.baseline["raw_execution_evidence"][0]["result"], "PASS")

    def test_every_behavioral_obligation_has_terminal_disposition(self) -> None:
        submission = self.baseline["b02_002_submission_execution_registry"]
        lifecycle = self.baseline["b02_003_lifecycle_execution_registry"]
        terminal_dispositions = set(self.baseline["behavioral_verification_integrity_registry"]["disposition_model"])

        self.assertEqual(len(submission), len(self.baseline["b02_001_behavioral_obligation_registry"]["B02-002"]))
        self.assertEqual(len(lifecycle), len(self.baseline["b02_001_behavioral_obligation_registry"]["B02-003"]))
        for item in (*submission, *lifecycle):
            self.assertIn(item["disposition"], terminal_dispositions)

    def test_passed_obligations_have_verifier_and_evidence(self) -> None:
        for item in (
            *self.baseline["b02_002_submission_execution_registry"],
            *self.baseline["b02_003_lifecycle_execution_registry"],
        ):
            if item["disposition"] == "VERIFIED_PASS":
                self.assertTrue(item["verifier"])
                self.assertTrue(item["evidence"])

    def test_reconciliation_is_honest_about_gaps_and_avoids_proof_claims(self) -> None:
        reconciliation = self.baseline["b02_004_behavioral_coverage_and_reconciliation"]

        self.assertGreater(reconciliation["verified_pass"], 0)
        self.assertGreater(reconciliation["not_executed"], 0)
        self.assertGreater(reconciliation["blocked_by_dependency_gap"], 0)
        self.assertGreater(reconciliation["blocked_by_implementation_gap"], 0)
        self.assertFalse(reconciliation["proof_objects_generated"])
        self.assertFalse(reconciliation["certification_readiness_activity_executed"])
        self.assertFalse(self.baseline["repository_wide_behavioral_verification_executed"])

    def test_completion_report_keeps_behavioral_scope_bounded(self) -> None:
        report = self.baseline["completion_report"]

        self.assertEqual(report["B02-001"], "COMPLETE")
        self.assertEqual(report["B02-002"], "COMPLETE_WITH_FINDINGS")
        self.assertEqual(report["B02-003"], "COMPLETE_WITH_FINDINGS")
        self.assertEqual(report["B02-004"], "COMPLETE")
        self.assertTrue(report["bounded_population_executed"])
        self.assertTrue(report["every_obligation_has_terminal_disposition"])
        self.assertTrue(report["behavioral_correctness_claim_limited_to_executed_pass_items"])


if __name__ == "__main__":
    unittest.main()
