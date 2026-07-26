from __future__ import annotations

import json
from pathlib import Path
import unittest

from Scripts.closed_position_truth_rm001_b01_baseline import OUTPUT_DIR, generate_baseline


class ClosedPositionTruthRM001B01BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        generate_baseline()

    def _load(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_all_order_deliverables_are_materialized(self) -> None:
        required = {
            "B01-001_constitutional_charter.json",
            "B01-001_constitutional_authority_registry.json",
            "B01-001_constitutional_responsibility_registry.json",
            "B01-001_constitutional_limitation_registry.json",
            "B01-001_success_failure_registry.json",
            "B01-001_completion_report.json",
            "B01-002_office_boundary_registry.json",
            "B01-002_enterprise_boundary_matrix.json",
            "B01-002_responsibility_allocation_matrix.json",
            "B01-002_authority_allocation_matrix.json",
            "B01-002_information_exchange_registry.json",
            "B01-002_dependency_boundary_registry.json",
            "B01-002_authority_transfer_registry.json",
            "B01-002_boundary_conflict_registry.json",
            "B01-002_completion_report.json",
            "B01-003_truth_ownership_registry.json",
            "B01-003_authority_matrix.json",
            "B01-003_custody_matrix.json",
            "B01-003_ownership_conflict_assessment.json",
            "B01-003_authority_conflict_assessment.json",
            "B01-003_completion_report.json",
            "B01-004_dependency_registry.json",
            "B01-004_truth_source_registry.json",
            "B01-004_upstream_dependency_registry.json",
            "B01-004_downstream_consumer_registry.json",
            "B01-004_source_precedence_matrix.json",
            "B01-004_dependency_direction_matrix.json",
            "B01-004_dependency_ownership_matrix.json",
            "B01-004_dependency_interaction_matrix.json",
            "B01-004_dependency_failure_registry.json",
            "B01-004_truth_derivation_registry.json",
            "B01-004_completion_report.json",
            "constitutional_findings_registry.json",
            "B01_series_completion_report.json",
            "manifest.json",
            "source_order_registry.json",
        }
        present = {path.name for path in Path(OUTPUT_DIR).iterdir() if path.is_file()}
        self.assertTrue(required.issubset(present))

    def test_series_is_doctrine_only_and_ready_for_b02(self) -> None:
        report = self._load("B01_series_completion_report.json")

        self.assertEqual("COMPLETE", report["status"])
        self.assertTrue(report["constitutional_doctrine_only"])
        self.assertFalse(report["implementation_behavior_modified"])
        self.assertFalse(report["behavioral_verification_executed"])
        self.assertFalse(report["implementation_certification_executed"])
        self.assertFalse(report["implementation_proof_generated"])
        self.assertEqual("CLOSED-POSITION-TRUTH-RM-001-B02", report["ready_for"])
        self.assertTrue(all(report["completion_criteria"].values()))

    def test_every_authority_and_responsibility_has_single_owner(self) -> None:
        authority = self._load("B01-001_constitutional_authority_registry.json")
        responsibilities = self._load("B01-001_constitutional_responsibility_registry.json")

        self.assertGreaterEqual(len(authority), 7)
        self.assertGreaterEqual(len(responsibilities), 10)
        self.assertTrue(all(item["constitutional_owner"] == "Closed Position Truth Office" for item in authority))
        self.assertTrue(all(item["constitutional_owner"] == "Closed Position Truth Office" for item in responsibilities))
        self.assertTrue(all(item["shared_owner"] is False for item in responsibilities))

    def test_boundaries_preserve_authority_and_prevent_shared_responsibility(self) -> None:
        boundaries = self._load("B01-002_office_boundary_registry.json")
        exchanges = self._load("B01-002_information_exchange_registry.json")
        conflicts = self._load("B01-002_boundary_conflict_registry.json")

        offices = {item["counterparty_office"] for item in boundaries}
        self.assertEqual(
            {"Trader", "Broker", "Position Registry", "Exit Decision", "Risk", "Performance Truth", "Historian", "Monitoring", "Analyst", "Infrastructure", "Commander"},
            offices,
        )
        self.assertTrue(all(item["information_exchange_transfers_authority"] is False for item in boundaries))
        self.assertTrue(all(item["authority_transfer"] == "PROHIBITED_UNLESS_EXPLICIT" for item in exchanges))
        self.assertFalse(conflicts["shared_responsibility_detected"])
        self.assertFalse(conflicts["authority_overlap_detected"])
        self.assertEqual([], conflicts["unresolved_boundary_conflicts"])

    def test_truth_ownership_and_dependency_precedence_are_deterministic(self) -> None:
        truth = self._load("B01-003_truth_ownership_registry.json")
        dependencies = self._load("B01-004_dependency_registry.json")
        precedence = self._load("B01-004_source_precedence_matrix.json")
        derivation = self._load("B01-004_truth_derivation_registry.json")

        self.assertEqual(9, len(truth))
        self.assertTrue(all(item["owner"] == "Closed Position Truth Office" for item in truth))
        self.assertTrue(all(item["ordinary_mutation_authority"] == "NONE_AFTER_AUTHORITATIVE_CREATION" for item in truth))
        self.assertGreaterEqual(len(dependencies), 10)
        self.assertEqual(list(range(1, len(precedence) + 1)), [item["precedence_rank"] for item in precedence])
        self.assertFalse(derivation["stage_skip_permitted"])
        self.assertTrue(derivation["requires_successful_prior_stage"])


if __name__ == "__main__":
    unittest.main()
