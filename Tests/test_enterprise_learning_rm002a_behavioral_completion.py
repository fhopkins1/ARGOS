from __future__ import annotations

import json
import unittest

from Scripts import enterprise_learning_rm002a_behavioral_completion as rm002a


class EnterpriseLearningRM002ABehavioralCompletionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rm002a.generate()

    def _load(self, name: str):
        return json.loads((rm002a.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_repository_independence_is_portable(self) -> None:
        report = self._load("repository_independence_report.json")
        self.assertEqual("PASS", report["disposition"])
        self.assertFalse(report["network_required"])
        self.assertFalse(report["local_cache_required"])
        self.assertEqual([], report["missing_artifacts"])

    def test_regeneration_is_deterministically_equivalent(self) -> None:
        report = self._load("deterministic_regeneration_report.json")
        self.assertEqual("PASS", report["disposition"])
        self.assertTrue(report["normalized_outputs_equivalent"])
        self.assertEqual([], report["mismatches"])

    def test_baseline_equivalence_has_no_failures(self) -> None:
        report = self._load("baseline_equivalence_report.json")
        self.assertEqual("PASS", report["disposition"])
        self.assertEqual([], report["failures"])

    def test_evidence_validation_checks_schema_and_digest(self) -> None:
        report = self._load("evidence_validation_report.json")
        self.assertEqual("PASS", report["disposition"])
        self.assertEqual("PASS", report["schema_validation"])
        self.assertEqual([], report["invalid_evidence"])

    def test_mutations_fail_closed(self) -> None:
        report = self._load("mutation_verification_report.json")
        self.assertEqual("PASS", report["disposition"])
        self.assertEqual([], report["unexpected_passes"])
        self.assertTrue(all(item["observed_failure"] == item["expected_failure"] for item in report["results"]))

    def test_completion_review_is_ready_without_certification_claim(self) -> None:
        report = self._load("completion_report.json")
        self.assertEqual("PASS", report["disposition"])
        self.assertEqual(10, report["orders_passed"])
        self.assertFalse(report["certification_claim_made"])
        self.assertEqual("READY_FOR_INDEPENDENT_ECS004_CERTIFICATION", report["readiness_determination"])


if __name__ == "__main__":
    unittest.main()
