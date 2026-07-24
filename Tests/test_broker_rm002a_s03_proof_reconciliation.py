import json
from pathlib import Path
import unittest


S02_PATH = Path("Documentation/BROKER_RM002A_S02_BEHAVIORAL_VERIFICATION/broker_rm002a_s02_behavioral_verification_baseline.json")
S03_PATH = Path("Documentation/BROKER_RM002A_S03_PROOF_RECONCILIATION/broker_rm002a_s03_proof_baseline.json")


class BrokerRM002AS03ProofReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.s02 = json.loads(S02_PATH.read_text(encoding="utf-8"))
        cls.s03 = json.loads(S03_PATH.read_text(encoding="utf-8"))

    def test_no_new_behavioral_execution_or_certification_claims(self) -> None:
        self.assertFalse(self.s03["new_behavioral_verification_executed"])
        self.assertFalse(self.s03["implementation_modified"])
        self.assertFalse(self.s03["runtime_behavior_modified"])
        self.assertFalse(self.s03["certification_conclusion_issued"])
        self.assertFalse(self.s03["certification_readiness_conclusion_issued"])

    def test_evidence_population_is_execution_derived_and_non_synthetic(self) -> None:
        for evidence in self.s03["b03_001_evidence_population_inventory"]:
            self.assertTrue(evidence["evidence_id"].startswith("BROKER-S03-EVID-"))
            self.assertTrue(evidence["owner"])
            self.assertTrue(evidence["producer"])
            self.assertTrue(evidence["custodian"])
            self.assertFalse(evidence["synthetic"])

    def test_requirement_proofs_preserve_required_identity_chain(self) -> None:
        for proof in self.s03["b03_002_requirement_proof_registry"]:
            self.assertTrue(proof["requirement_id"])
            self.assertTrue(proof["participating_implementation_artifacts"])
            self.assertIn("proof_completeness", proof)
            self.assertIn("proof_sufficiency", proof)
            self.assertNotEqual(proof["proof_sufficiency"], "SUFFICIENT_FOR_CERTIFICATION_PASS")

    def test_series_two_count_mismatch_is_recorded_not_silently_rewritten(self) -> None:
        execution_items = (
            self.s02["b02_002_submission_execution_registry"]
            + self.s02["b02_003_lifecycle_execution_registry"]
        )
        actual_passes = sum(1 for item in execution_items if item["disposition"] == "VERIFIED_PASS")
        summary_passes = self.s02["b02_004_behavioral_coverage_and_reconciliation"]["verified_pass"]

        self.assertEqual(actual_passes, 30)
        self.assertEqual(summary_passes, 31)
        self.assertEqual(self.s03["b03_001_evidence_deficiency_registry"][0]["classification"], "summary-count inconsistency")

    def test_proof_reconciliation_blocks_unsupported_pass(self) -> None:
        reconciliation = self.s03["b03_004_proof_integrity_and_sufficiency_reconciliation"]
        completion = self.s03["completion_report"]

        self.assertEqual(reconciliation["unsupported_pass_dispositions"], 0)
        self.assertEqual(reconciliation["proof_objects_sufficient_for_certification_pass"], 0)
        self.assertGreater(reconciliation["proof_objects_incomplete_or_unsupported"], 0)
        self.assertTrue(completion["proof_uses_only_validated_execution_evidence"])
        self.assertTrue(completion["synthetic_evidence_substitution_prohibited"])


if __name__ == "__main__":
    unittest.main()
