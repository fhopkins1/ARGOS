from __future__ import annotations

from pathlib import Path
import unittest

from argos.control_panel.full_suite_failure_error_closure import EOEJRootCause, execute_eoej_certification


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class EOEJFullSuiteFailureErrorClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = execute_eoej_certification("TEST-COMMIT", repo_root=REPOSITORY_ROOT)

    def test_denominator_is_current_unittest_collection(self) -> None:
        denominator = self.payload["authoritative_test_denominator"]

        self.assertGreaterEqual(denominator["collected"], 1280)
        self.assertEqual(denominator["collected"], denominator["requiredBoundedInternal"])
        self.assertTrue(self.payload["collection_results"]["collectionComplete"])

    def test_closed_adverse_results_have_known_root_causes(self) -> None:
        closed = tuple(item for item in self.payload["failure_closure_matrix"] if item["final_status"] == "CLOSED")

        self.assertGreaterEqual(len(closed), 2)
        self.assertTrue(all(item["primary_root_cause"] in {cause.value for cause in EOEJRootCause} for item in closed))
        self.assertTrue(all(item["targeted_rerun_result"] == "PASS" for item in closed))

    def test_open_dashboard_adverse_results_block_pass(self) -> None:
        certification = self.payload["certification"]
        open_items = tuple(item for item in self.payload["failure_closure_matrix"] if item["final_status"] == "OPEN")

        self.assertEqual(certification["verdict"], "FAIL")
        self.assertGreaterEqual(len(open_items), 3)
        self.assertEqual(certification["openAdverseResults"], len(open_items))

    def test_no_unknown_root_cause_is_reported(self) -> None:
        causes = {item["primary_root_cause"] for item in self.payload["failure_closure_matrix"]}

        self.assertNotIn("UNKNOWN_ROOT_CAUSE", causes)

    def test_complete_verification_cannot_be_inferred_from_segments(self) -> None:
        verification = self.payload["complete_verification_run"]
        static = self.payload["static_assurance"]

        self.assertFalse(verification["complete"])
        self.assertTrue(static["currentAdverseEvidenceBlocksPass"])


if __name__ == "__main__":
    unittest.main()
