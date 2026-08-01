from __future__ import annotations

import json
import unittest

from Scripts import enterprise_learning_rm001_constitutional_baseline as baseline


class EnterpriseLearningRM001ConstitutionalBaselineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        baseline.generate()

    def _load(self, name: str):
        return json.loads((baseline.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_all_orders_pass_and_mo001_is_ready(self) -> None:
        report = self._load("completion_report.json")
        self.assertEqual(10, report["orders_total"])
        self.assertEqual(10, report["orders_passed"])
        self.assertEqual(0, report["orders_failed"])
        self.assertEqual("READY FOR ENTERPRISE-LEARNING-MO-001", report["readiness_determination"])

    def test_ownership_and_boundaries_remain_separated(self) -> None:
        ownership = self._load("constitutional_ownership_matrix.json")
        self.assertTrue(all(not item["shared_ownership"] for item in ownership["owned_objects"]))
        boundary = self._load("constitutional_boundary_verification_report.json")
        self.assertTrue(all(not item["enterprise_learning_authorized"] for item in boundary["verified_boundaries"]))

    def test_product_publication_requires_evidence_explainability_and_reproducibility(self) -> None:
        products = self._load("learning_product_architecture_assessment.json")
        required = set(products["required_learning_product_record"])
        self.assertIn("uncertainty", required)
        self.assertIn("explainability artifact", required)
        self.assertIn("reproducibility status", required)
        explainability = self._load("explainability_assessment.json")
        self.assertTrue(explainability["publication_blocked_when_incomplete"])

    def test_evidence_lineage_is_distinct_from_historical_provenance(self) -> None:
        evidence = self._load("evidence_and_provenance_boundary_assessment.json")
        self.assertEqual("Enterprise Learning Office", evidence["learning_lineage_owner"])
        self.assertEqual("Historian", evidence["historical_provenance_owner"])
        self.assertIn("enterprise_learning_lineage_graph", evidence["graph_domains"])


if __name__ == "__main__":
    unittest.main()
