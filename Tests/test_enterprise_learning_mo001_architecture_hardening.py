from __future__ import annotations

import json
import unittest

from Scripts import enterprise_learning_mo001_architecture_hardening as hardening


class EnterpriseLearningMO001ArchitectureHardeningTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        hardening.generate()

    def _load(self, name: str):
        return json.loads((hardening.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_hardening_certifies_progression_to_rm002(self) -> None:
        report = self._load("completion_report.json")
        self.assertEqual(10, report["orders_total"])
        self.assertEqual(10, report["orders_passed"])
        self.assertEqual(0, report["orders_failed"])
        self.assertEqual("Proceed to ENTERPRISE-LEARNING-RM-002", report["certification_decision"])

    def test_findings_are_nonblocking_clarifications(self) -> None:
        findings = self._load("constitutional_findings_register.json")
        self.assertGreaterEqual(len(findings), 1)
        self.assertTrue(all(not finding["blocks_rm002"] for finding in findings))
        self.assertEqual(0, self._load("completion_report.json")["blocking_findings"])

    def test_product_taxonomy_is_simplified_without_authority_expansion(self) -> None:
        products = self._load("learning_product_architecture_challenge_report.json")
        self.assertIn("model evaluation artifact", products["reclassified_as_attributes_or_evidence"])
        self.assertEqual([], products["hidden_authority_findings"])
        self.assertIn("learning-derived recommendation", products["recommended_taxonomy"])

    def test_coupling_is_minimal_and_directional(self) -> None:
        coupling = self._load("constitutional_coupling_and_cohesion_review.json")
        self.assertEqual("HIGH", coupling["internal_cohesion"])
        self.assertFalse(coupling["circular_dependencies_detected"])
        self.assertTrue(all(item["coupling_level"] == "minimal" for item in coupling["enterprise_dependency_matrix"]))


if __name__ == "__main__":
    unittest.main()
