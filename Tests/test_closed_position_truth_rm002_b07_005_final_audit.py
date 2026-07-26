import json
import unittest

from Scripts.closed_position_truth_rm002_b07_005_final_audit import OUTPUT_DIR, generate_final_audit


class ClosedPositionTruthRm002B07005FinalAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completion = generate_final_audit()

    def _read(self, name):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_final_audit_deliverables_exist(self):
        required = [
            "certification_reproduction_registry.json",
            "independent_execution_registry.json",
            "certification_comparison_registry.json",
            "variance_registry.json",
            "certification_sufficiency_registry.json",
            "certification_findings_registry.json",
            "final_certification_registry.json",
            "final_certification_findings_registry.json",
            "ecs003_certification_report.json",
            "certification_baseline_registry.json",
            "certification_freeze_authorization.json",
            "enterprise_eligibility_registry.json",
            "certification_closure_report.json",
            "final_independent_clean_room_audit_report.json",
            "final_ecs003_implementation_certification_verdict.json",
            "series_completion_report.json",
            "manifest.json",
        ]
        for name in required:
            self.assertTrue((OUTPUT_DIR / name).is_file(), name)

    def test_final_verdict_follows_certification_conditions(self):
        sufficiency = self._read("certification_sufficiency_registry.json")
        final = self._read("final_certification_registry.json")
        verdict = self._read("final_ecs003_implementation_certification_verdict.json")

        self.assertEqual(final["certification_disposition"], verdict["verdict"])
        self.assertEqual(final["certification_disposition"], "ECS003_IMPLEMENTATION_CERTIFICATION_DENIED")
        self.assertEqual(final["reproduction_disposition"], "NOT_REPRODUCIBLE")
        self.assertFalse(sufficiency["behavioral_verification_succeeds"])
        self.assertFalse(sufficiency["certification_blockers_equal_zero"])

    def test_every_requirement_has_one_permitted_disposition(self):
        proofs = self._read("requirement_proof_registry.json")
        allowed = {"PROVEN", "NOT_PROVEN", "NOT_APPLICABLE"}
        requirement_ids = [row["requirement_id"] for row in proofs]

        self.assertGreater(len(proofs), 0)
        self.assertEqual(len(requirement_ids), len(set(requirement_ids)))
        for proof in proofs:
            self.assertIn(proof["disposition"], allowed)
            if proof["disposition"] == "NOT_PROVEN":
                self.assertTrue(proof["finding_references"])

    def test_package_inputs_are_non_identical_and_hash_recorded(self):
        identity = self._read("package_identity_registry.json")
        repo_hash = identity["repository_package"]["sha256"]
        evidence_hash = identity["evidence_only_package"]["sha256"]

        self.assertNotEqual(repo_hash, evidence_hash)
        self.assertNotEqual(identity["repository_package"]["bytes"], identity["evidence_only_package"]["bytes"])
        self.assertGreater(identity["repository_package"]["entry_count"], identity["evidence_only_package"]["entry_count"])

    def test_raw_execution_evidence_exists_for_each_execution(self):
        executions = self._read("independent_execution_registry.json")
        evidence = {row["evidence_id"]: row for row in self._read("raw_execution_evidence_registry.json")}

        self.assertGreater(len(executions), 0)
        for execution in executions:
            self.assertEqual(len(execution["evidence"]), 3)
            for evidence_id in execution["evidence"]:
                self.assertIn(evidence_id, evidence)


if __name__ == "__main__":
    unittest.main()
