from __future__ import annotations

import json
from pathlib import Path
import unittest

from Scripts.closed_position_truth_ecs003_audit import OUTPUT_DIR, generate_audit


class ClosedPositionTruthECS003AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        generate_audit()

    def _load(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_audit_deliverables_are_produced(self) -> None:
        required = {
            "executive_audit_report.json",
            "constitutional_audit_report.json",
            "canonical_requirement_registry.json",
            "ownership_assessment.json",
            "object_model_assessment.json",
            "lifecycle_assessment.json",
            "reconciliation_assessment.json",
            "evidence_assessment.json",
            "dependency_derived_implementation_inventory.json",
            "verifier_inventory.json",
            "behavioral_execution_registry.json",
            "evidence_registry.json",
            "proof_registry.json",
            "traceability_graph.json",
            "certification_blocker_registry.json",
            "clean_room_reproduction_report.json",
            "final_ecs003_audit_report.json",
            "final_verdict.json",
            "completion_report.json",
            "manifest.json",
            "source_order.txt",
        }
        present = {item.name for item in Path(OUTPUT_DIR).iterdir() if item.is_file()}
        self.assertTrue(required.issubset(present))

    def test_audit_is_bounded_and_does_not_claim_remediation(self) -> None:
        completion = self._load("completion_report.json")
        executive = self._load("executive_audit_report.json")

        self.assertTrue(completion["status"], "COMPLETE")
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["remediation_performed"])
        self.assertFalse(completion["repository_wide_verification_executed"])
        self.assertFalse(executive["implementation_modified"])
        self.assertFalse(executive["constitutional_doctrine_modified"])

    def test_fail_closed_verdict_has_blocking_evidence(self) -> None:
        verdict = self._load("final_verdict.json")
        blockers = self._load("certification_blocker_registry.json")
        final_report = self._load("final_ecs003_audit_report.json")

        self.assertIn(verdict["verdict"], {"UNCONDITIONAL_PASS", "FAIL"})
        if verdict["verdict"] == "FAIL":
            self.assertTrue(verdict["fail_closed"])
            self.assertGreater(blockers["blocker_count"], 0)
            self.assertFalse(final_report["unconditional_pass_criteria_met"])

    def test_behavioral_executions_are_terminal_and_mapped_to_evidence(self) -> None:
        executions = self._load("behavioral_execution_registry.json")
        allowed = {"PASS", "FAIL", "ERROR", "TIMEOUT", "INVALID_EVIDENCE", "CONSTITUTIONAL_CONFLICT", "NOT_APPLICABLE"}

        self.assertGreaterEqual(len(executions), 1)
        for execution in executions:
            self.assertIn(execution["terminal_disposition"], allowed)
            self.assertIn("raw_stdout", execution)
            self.assertIn("raw_stderr", execution)
            self.assertTrue((OUTPUT_DIR.parent.parent / execution["raw_stdout"]).exists())
            self.assertTrue((OUTPUT_DIR.parent.parent / execution["raw_stderr"]).exists())

    def test_dependency_discovery_is_not_filename_only(self) -> None:
        inventory = self._load("dependency_derived_implementation_inventory.json")
        direct = [item for item in inventory if item["classification"] == "CLOSED_POSITION_DIRECT"]
        self.assertEqual(1, len(direct))
        self.assertTrue(direct[0]["dependency_evidence"]["marker_hits"])
        self.assertIn("classification_basis", direct[0]["dependency_evidence"])


if __name__ == "__main__":
    unittest.main()
