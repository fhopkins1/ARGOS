from __future__ import annotations

import json
from pathlib import Path
import unittest

from Scripts.closed_position_truth_rm001a_b01_requirement_architecture import CATEGORIES, OUTPUT_DIR, generate_requirement_architecture


class ClosedPositionTruthRM001AB01RequirementArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        generate_requirement_architecture()

    def _load(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_deliverables_exist(self) -> None:
        required = {
            "constitutional_obligation_inventory.json",
            "discovery_report.json",
            "canonical_requirement_registry.json",
            "requirement_validation_report.json",
            "requirement_identity_registry.json",
            "identifier_validation_registry.json",
            "requirement_classification_registry.json",
            "requirement_coverage_report.json",
            "constitutional_traceability_graph.json",
            "requirement_integrity_report.json",
            "requirement_findings_registry.json",
            "completion_report.json",
            "manifest.json",
            "source_order_registry.json",
            "accepted_baseline_registry.json",
        }
        present = {item.name for item in Path(OUTPUT_DIR).iterdir() if item.is_file()}
        self.assertTrue(required.issubset(present))

    def test_every_obligation_maps_to_exactly_one_atomic_requirement(self) -> None:
        obligations = self._load("constitutional_obligation_inventory.json")
        requirements = self._load("canonical_requirement_registry.json")

        self.assertEqual(len(obligations), len(requirements))
        self.assertEqual(
            {item["obligation_id"] for item in obligations},
            {item["originating_obligation"] for item in requirements},
        )
        self.assertTrue(all(item["atomic"] for item in requirements))
        self.assertTrue(all(item["independently_testable"] for item in requirements))
        self.assertTrue(all(item["deterministic"] for item in requirements))
        self.assertTrue(all(item["uniquely_owned"] for item in requirements))
        self.assertTrue(all(item["non_overlapping"] for item in requirements))

    def test_identifier_and_classification_coverage_are_complete(self) -> None:
        identifiers = self._load("identifier_validation_registry.json")
        coverage = self._load("requirement_coverage_report.json")
        classifications = self._load("requirement_classification_registry.json")

        self.assertEqual("PASS", identifiers["validation_status"])
        self.assertEqual(identifiers["total_identifiers"], identifiers["unique_identifiers"])
        self.assertEqual([], identifiers["duplicate_identifiers"])
        self.assertTrue(coverage["complete_category_coverage"])
        self.assertEqual(set(CATEGORIES), set(coverage["categories"]))
        self.assertTrue(all(value > 0 for value in coverage["categories"].values()))
        self.assertEqual(coverage["total_requirements"], len(classifications))

    def test_traceability_preserves_required_lineage_fields(self) -> None:
        traceability = self._load("constitutional_traceability_graph.json")

        self.assertTrue(all(item["forward_traceability_complete"] for item in traceability))
        self.assertTrue(all(item["backward_traceability_complete"] for item in traceability))
        self.assertTrue(all(item["originating_doctrine"] for item in traceability))
        self.assertTrue(all(item["governing_object"] for item in traceability))
        self.assertTrue(all(item["governing_lifecycle"] for item in traceability))
        self.assertTrue(all(item["governing_evidence_obligation"] for item in traceability))
        self.assertTrue(all(item["certification_disposition"] == "MANDATORY_BLOCKING" for item in traceability))

    def test_integrity_disposition_is_complete_and_constitutional_only(self) -> None:
        integrity = self._load("requirement_integrity_report.json")
        completion = self._load("completion_report.json")
        findings = self._load("requirement_findings_registry.json")

        self.assertEqual("COMPLETE", integrity["disposition"])
        self.assertEqual("COMPLETE", completion["status"])
        self.assertEqual([], findings)
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["constitutional_authority_changed"])
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["behavioral_verification_occurred"])
        self.assertFalse(completion["implementation_certification_occurred"])
        self.assertTrue(all(completion["completion_criteria"].values()))


if __name__ == "__main__":
    unittest.main()
