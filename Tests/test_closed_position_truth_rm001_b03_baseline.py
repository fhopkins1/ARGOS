from __future__ import annotations

import json
from pathlib import Path
import unittest

from Scripts.closed_position_truth_rm001_b03_baseline import OUTPUT_DIR, generate_baseline


class ClosedPositionTruthRM001B03BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        generate_baseline()

    def _load(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_b03_deliverables_exist(self) -> None:
        required = {
            "B03-001_constitutional_closure_registry.json",
            "B03-001_closure_admissibility_registry.json",
            "B03-001_closure_authority_registry.json",
            "B03-001_prohibited_closure_registry.json",
            "B03-001_constitutional_findings_registry.json",
            "B03-001_completion_report.json",
            "B03-002_settlement_constitution.json",
            "B03-002_settlement_registry.json",
            "B03-002_settlement_ownership_registry.json",
            "B03-002_settlement_authority_registry.json",
            "B03-002_settlement_state_registry.json",
            "B03-002_settlement_verification_registry.json",
            "B03-002_settlement_evidence_registry.json",
            "B03-002_settlement_exemption_registry.json",
            "B03-002_settlement_failure_registry.json",
            "B03-002_settlement_reconciliation_registry.json",
            "B03-002_settlement_correction_registry.json",
            "B03-002_settlement_supersession_registry.json",
            "B03-002_settlement_temporal_registry.json",
            "B03-002_prohibited_settlement_authority_registry.json",
            "B03-002_settlement_conflict_registry.json",
            "B03-002_settlement_authority_matrix.json",
            "B03-002_completion_report.json",
            "B03-003_residual_quantity_registry.json",
            "B03-003_quantity_verification_registry.json",
            "B03-003_quantity_reconciliation_registry.json",
            "B03-003_residual_quantity_ownership_matrix.json",
            "B03-003_quantity_source_precedence_matrix.json",
            "B03-003_duplicate_execution_registry.json",
            "B03-003_quantity_exception_registry.json",
            "B03-003_completion_report.json",
            "B03-004_reconciliation_registry.json",
            "B03-004_reconciliation_authority_registry.json",
            "B03-004_reconciliation_evidence_registry.json",
            "B03-004_source_precedence_registry.json",
            "B03-004_reconciliation_success_criteria_registry.json",
            "B03-004_reconciliation_failure_registry.json",
            "B03-004_exception_registry.json",
            "B03-004_correction_lineage_registry.json",
            "B03-004_supersession_lineage_registry.json",
            "B03-004_reconciliation_participation_matrix.json",
            "B03-004_completion_report.json",
            "B03_series_completion_report.json",
            "manifest.json",
            "source_order_registry.json",
        }
        present = {item.name for item in Path(OUTPUT_DIR).iterdir() if item.is_file()}
        self.assertTrue(required.issubset(present))

    def test_series_is_doctrine_only_for_issued_orders(self) -> None:
        report = self._load("B03_series_completion_report.json")

        self.assertEqual("COMPLETE_FOR_ISSUED_ORDERS", report["status"])
        self.assertTrue(report["constitutional_doctrine_only"])
        self.assertFalse(report["implementation_behavior_modified"])
        self.assertFalse(report["behavioral_verification_executed"])
        self.assertFalse(report["implementation_certification_executed"])
        self.assertFalse(report["implementation_proof_generated"])
        self.assertTrue(all(report["completion_criteria"].values()))

    def test_closure_requires_all_mandatory_criteria_and_only_closed_outcome_authorizes_truth(self) -> None:
        registry = self._load("B03-001_constitutional_closure_registry.json")
        determination = self._load("B03-001_closure_determination_doctrine.json")
        prohibited = self._load("B03-001_prohibited_closure_registry.json")

        self.assertEqual(12, len(registry))
        self.assertTrue(all(item["waiver_allowed"] is False for item in registry))
        self.assertEqual("CONSTITUTIONALLY_CLOSED", determination["only_authorizing_outcome"])
        self.assertFalse(determination["degraded_authoritative_truth_allowed"])
        prohibited_conditions = {item["condition"] for item in prohibited}
        self.assertIn("residual quantity greater than zero", prohibited_conditions)
        self.assertIn("settlement neither verified nor constitutionally exempt", prohibited_conditions)
        self.assertIn("analytical degradation used as substitute evidence", prohibited_conditions)

    def test_settlement_is_bounded_verified_or_exempt_and_never_sufficient_alone(self) -> None:
        constitution = self._load("B03-002_settlement_constitution.json")
        states = self._load("B03-002_settlement_state_registry.json")
        prohibited = self._load("B03-002_prohibited_settlement_authority_registry.json")

        self.assertFalse(constitution["independently_creates_closed_position_truth"])
        self.assertEqual(["Verified", "Constitutionally Exempt"], constitution["admissible_dispositions"])
        satisfying = {item["state"] for item in states if item["satisfies_closure_participation"]}
        self.assertEqual({"Verified", "Constitutionally Exempt"}, satisfying)
        self.assertIn("settlement overriding reconciliation failure", {item["prohibition"] for item in prohibited})
        self.assertIn("settlement overriding nonzero residual quantity", {item["prohibition"] for item in prohibited})

    def test_residual_quantity_zero_is_required_but_not_sufficient(self) -> None:
        residual = self._load("B03-003_residual_quantity_registry.json")
        verification = self._load("B03-003_quantity_verification_registry.json")
        exceptions = self._load("B03-003_quantity_exception_registry.json")

        self.assertTrue(residual["zero_required_for_closure"])
        self.assertFalse(residual["zero_independently_establishes_closure"])
        outcomes = {item["outcome"]: item["may_satisfy_closure_quantity_condition"] for item in verification}
        self.assertTrue(outcomes["ZERO_VERIFIED"])
        self.assertFalse(outcomes["NONZERO_CONFIRMED"])
        self.assertFalse(outcomes["INCONSISTENT"])
        self.assertFalse(outcomes["INSUFFICIENT_EVIDENCE"])
        self.assertIn("positive residual quantity", {item["exception"] for item in exceptions})
        self.assertIn("negative residual quantity", {item["exception"] for item in exceptions})

    def test_reconciliation_requires_success_and_preserves_source_ownership(self) -> None:
        reconciliation = self._load("B03-004_reconciliation_registry.json")
        success = self._load("B03-004_reconciliation_success_criteria_registry.json")
        failure = self._load("B03-004_reconciliation_failure_registry.json")
        participation = self._load("B03-004_reconciliation_participation_matrix.json")
        precedence = self._load("B03-004_source_precedence_registry.json")

        self.assertTrue(reconciliation["mandatory_failure_prohibits_closure"])
        self.assertGreaterEqual(len(success), 8)
        self.assertTrue(all(item["required"] for item in success))
        self.assertTrue(all(item["closure_effect"] == "PROHIBITS_CLOSED_POSITION_TRUTH" for item in failure))
        self.assertTrue(all(item["closed_position_truth_may_modify_owned_truth"] is False for item in participation))
        self.assertEqual(list(range(1, len(precedence) + 1)), [item["rank"] for item in precedence])


if __name__ == "__main__":
    unittest.main()
