from __future__ import annotations

import json
from pathlib import Path
import unittest

from Scripts.closed_position_truth_rm001_b05_certification import OUTPUT_DIR, generate_certification


class ClosedPositionTruthRM001B05CertificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        generate_certification()

    def _load(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_b05_deliverables_exist(self) -> None:
        required = {
            "B05-001_constitutional_completeness_registry.json",
            "B05-001_constitutional_findings_registry.json",
            "B05-001_missing_constitutional_domain_registry.json",
            "B05-001_duplicate_constitutional_domain_registry.json",
            "B05-001_unresolved_constitutional_decision_registry.json",
            "B05-001_completeness_reconciliation_completion_report.json",
            "B05-002_constitutional_consistency_registry.json",
            "B05-002_authority_consistency_registry.json",
            "B05-002_boundary_consistency_registry.json",
            "B05-002_ownership_consistency_registry.json",
            "B05-002_custody_consistency_registry.json",
            "B05-002_object_consistency_registry.json",
            "B05-002_lifecycle_consistency_registry.json",
            "B05-002_closure_doctrine_consistency_registry.json",
            "B05-002_settlement_doctrine_consistency_registry.json",
            "B05-002_residual_quantity_consistency_registry.json",
            "B05-002_reconciliation_consistency_registry.json",
            "B05-002_realized_outcome_consistency_registry.json",
            "B05-002_temporal_consistency_registry.json",
            "B05-002_evidence_consistency_registry.json",
            "B05-002_historical_integrity_consistency_registry.json",
            "B05-002_requirement_consistency_registry.json",
            "B05-002_terminology_consistency_registry.json",
            "B05-002_conflict_registry.json",
            "B05-002_conflict_resolution_registry.json",
            "B05-002_constitutional_findings_registry.json",
            "B05-002_completion_report.json",
            "B05-003_requirement_audit_registry.json",
            "B05-003_traceability_audit_registry.json",
            "B05-003_canonical_requirement_population.json",
            "B05-003_requirement_identity_registry.json",
            "B05-003_requirement_classification_registry.json",
            "B05-003_duplicate_requirement_registry.json",
            "B05-003_aggregate_requirement_registry.json",
            "B05-003_orphan_requirement_registry.json",
            "B05-003_conflict_registry.json",
            "B05-003_constitutional_traceability_graph.json",
            "B05-003_constitutional_blocker_registry.json",
            "B05-003_completion_report.json",
            "B05-004_constitutional_certification_registry.json",
            "B05-004_constitutional_completeness_assessment.json",
            "B05-004_constitutional_consistency_assessment.json",
            "B05-004_constitutional_findings_registry.json",
            "B05-004_constitutional_blocker_registry.json",
            "B05-004_constitutional_freeze_authorization_or_denial.json",
            "B05-004_final_ecs003_constitutional_audit_report.json",
            "B05-004_final_constitutional_verdict.json",
            "B05-004_constitutional_completion_report.json",
            "B05_series_completion_report.json",
            "manifest.json",
            "source_order_registry.json",
        }
        present = {item.name for item in Path(OUTPUT_DIR).iterdir() if item.is_file()}
        self.assertTrue(required.issubset(present))

    def test_b05_is_constitutional_only_and_does_not_execute_implementation_work(self) -> None:
        completion = self._load("B05_series_completion_report.json")

        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["implementation_discovery_performed"])
        self.assertFalse(completion["behavioral_verification_performed"])
        self.assertFalse(completion["implementation_proof_generated"])
        self.assertFalse(completion["implementation_certification_activity_performed"])
        self.assertTrue(all(completion["completion_criteria"].values()))

    def test_b04_requirement_traceability_gap_is_reported_as_blocking_not_concealed(self) -> None:
        domains = self._load("B05-001_constitutional_completeness_registry.json")
        missing = self._load("B05-001_missing_constitutional_domain_registry.json")
        findings = self._load("B05-001_constitutional_findings_registry.json")

        b04_domains = [item for item in domains if item["required_series"].endswith("B04")]
        self.assertEqual(2, len(b04_domains))
        self.assertTrue(all(item["completeness_status"] == "MISSING" for item in b04_domains))
        self.assertEqual({item["domain"] for item in b04_domains}, {item["domain"] for item in missing})
        self.assertTrue(all(item["severity"] == "BLOCKER" for item in findings))
        self.assertTrue(all(item["disposition"] == "OPEN_REPORTED" for item in findings))

    def test_requirement_and_traceability_audit_has_terminal_dispositions(self) -> None:
        requirements = self._load("B05-003_requirement_audit_registry.json")
        traceability = self._load("B05-003_traceability_audit_registry.json")
        blockers = self._load("B05-003_constitutional_blocker_registry.json")

        self.assertEqual(len(requirements), len(traceability))
        self.assertTrue(all(item["atomic"] for item in requirements))
        self.assertTrue(all(item["requirement_id"].startswith("CPT-REQ-") for item in requirements))
        self.assertTrue(all(item["disposition"] in {"TRACEABLE", "BLOCKED_MISSING_SOURCE"} for item in traceability))
        self.assertGreaterEqual(len(blockers), 1)
        self.assertTrue(all(item["constitutional_freeze_effect"] == "DENY_FREEZE" for item in blockers))

    def test_final_verdict_denies_freeze_until_reported_blockers_are_remediated(self) -> None:
        verdict = self._load("B05-004_final_constitutional_verdict.json")
        freeze = self._load("B05-004_constitutional_freeze_authorization_or_denial.json")
        certification = self._load("B05-004_constitutional_certification_registry.json")

        self.assertEqual("CONSTITUTIONALLY_INCOMPLETE", verdict["verdict"])
        self.assertFalse(freeze["authorized"])
        self.assertFalse(certification["constitutional_freeze_authorized"])
        self.assertFalse(certification["progression_to_rm002_authorized"])
        self.assertGreater(certification["blocker_count"], 0)


if __name__ == "__main__":
    unittest.main()
