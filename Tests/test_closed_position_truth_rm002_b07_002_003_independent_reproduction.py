import json
from pathlib import Path
import unittest

from Scripts.closed_position_truth_rm002_b07_002_003_independent_reproduction import (
    OUTPUT_DIR,
    generate_reproduction,
)


class ClosedPositionTruthRm002B07002003IndependentReproductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completion = generate_reproduction()

    def _read(self, name):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_b07_002_deliverables_exist(self):
        required = [
            "implementation_inventory.json",
            "runtime_participation_registry.json",
            "dependency_discovery_registry.json",
            "artifact_classification_registry.json",
            "verifier_registry.json",
            "fixture_registry.json",
            "verifier_to_fixture_binding_registry.json",
            "behavioral_execution_registry.json",
            "raw_behavioral_evidence_registry.json",
            "behavioral_findings_registry.json",
            "behavioral_coverage_matrix.json",
            "behavioral_reconciliation_registry.json",
            "behavioral_coverage_findings_registry.json",
            "coverage_completeness_report.json",
        ]
        for name in required:
            self.assertTrue((OUTPUT_DIR / name).is_file(), name)

    def test_required_b07_003_deliverables_exist(self):
        required = [
            "evidence_registry.json",
            "evidence_identity_registry.json",
            "evidence_provenance_registry.json",
            "evidence_integrity_registry.json",
            "evidence_admissibility_registry.json",
            "proof_registry.json",
            "requirement_proof_registry.json",
            "proof_lineage_registry.json",
            "lineage_validation_report.json",
            "traceability_registry.json",
            "forward_traceability_matrix.json",
            "backward_traceability_matrix.json",
            "traceability_integrity_report.json",
            "completion_report.json",
            "manifest.json",
        ]
        for name in required:
            self.assertTrue((OUTPUT_DIR / name).is_file(), name)

    def test_behavioral_execution_preserves_raw_evidence(self):
        executions = self._read("behavioral_execution_registry.json")
        evidence = self._read("raw_behavioral_evidence_registry.json")
        evidence_by_id = {row["evidence_id"]: row for row in evidence}

        self.assertGreater(len(executions), 0)
        for execution in executions:
            self.assertIn(execution["primary_disposition"], {"PASS", "FAIL", "NOT_APPLICABLE", "BLOCKED", "EXECUTION_ERROR", "NOT_EXECUTED"})
            self.assertGreater(len(execution["raw_evidence_references"]), 0)
            for evidence_id in execution["raw_evidence_references"]:
                self.assertIn(evidence_id, evidence_by_id)
                path = OUTPUT_DIR.parents[1] / evidence_by_id[evidence_id]["storage_location"]
                self.assertTrue(path.is_file(), path)

    def test_completion_is_honest_and_non_certifying(self):
        completion = self._read("completion_report.json")
        self.assertIn(completion["status"], {"COMPLETE", "COMPLETE_WITH_FINDINGS"})
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["mutation_campaign_occurred"])
        self.assertFalse(completion["certification_verdict_issued"])
        self.assertTrue(completion["completion_criteria"]["no_certification_verdict_issued"])
        self.assertTrue(completion["completion_criteria"]["no_implementation_modification"])

    def test_requirement_proof_population_reconciles_to_requirements(self):
        report = self._read("proof_population_reconciliation_report.json")
        proofs = self._read("proof_registry.json")
        dispositions = {"PROVEN", "NOT_PROVEN", "NOT_APPLICABLE"}

        self.assertTrue(report["identity_holds"])
        self.assertEqual(len(proofs), report["total_canonical_requirements"])
        for proof in proofs:
            self.assertIn(proof["proof_disposition"], dispositions)
            self.assertTrue(proof["proof_id"])
            self.assertTrue(proof["canonical_requirement_identifier"])


if __name__ == "__main__":
    unittest.main()
