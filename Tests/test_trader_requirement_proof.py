from dataclasses import replace
from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.trader.requirement_proof import (  # noqa: E402
    PROHIBITED_AGGREGATE_REQUIREMENT_IDS,
    ProofStatus,
    RawEvidenceRecord,
    build_proof_population,
    build_relationship_graph,
    build_requirement_registry,
    calculate_coverage,
    derive_final_verdict,
    derive_traceability_matrix,
    execute_requirement_proof_system,
    validate_proof_system,
)


class TraderRequirementProofTests(unittest.TestCase):
    def test_requirement_registry_uses_stable_non_aggregate_identifiers(self) -> None:
        requirements = build_requirement_registry("candidate-digest")
        identifiers = [record.requirement_id for record in requirements]

        self.assertGreater(len(requirements), 100)
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertFalse(PROHIBITED_AGGREGATE_REQUIREMENT_IDS.intersection(identifiers))
        self.assertTrue(all(identifier.startswith("TRADER-REQ-") for identifier in identifiers))

    def test_complete_proof_population_passes_and_generates_raw_evidence(self) -> None:
        proofs = build_proof_population("candidate-digest")
        validation = validate_proof_system(proofs)

        self.assertEqual(validation.status, ProofStatus.PASS, validation.findings)
        for proof in proofs:
            self.assertEqual(proof.disposition, ProofStatus.PASS)
            self.assertTrue(proof.verification_executions)
            self.assertTrue(proof.raw_evidence)
            self.assertNotIn("certification_result.json", {record.source for record in proof.raw_evidence})

    def test_graph_drives_bidirectional_traceability(self) -> None:
        proofs = build_proof_population("candidate-digest")
        graph = build_relationship_graph(proofs)
        matrix = derive_traceability_matrix(graph)

        self.assertEqual(len(matrix), len(proofs))
        first = proofs[0]
        self.assertIn(first.proof_id, matrix[first.requirement_id])
        self.assertTrue(any(edge["class"] == "supports verdict" for edge in graph["edges"]))

    def test_final_verdict_derives_from_proof_population_not_candidate_summary(self) -> None:
        proofs = build_proof_population("candidate-digest")
        digest = proofs[0].reproducibility_digest
        verdict = derive_final_verdict(proofs, (digest, digest))

        self.assertEqual(verdict["verdict"], "UNCONDITIONAL PASS")
        self.assertEqual(verdict["issuing_authority"], "Independent Final Reconciliation Authority")
        self.assertEqual(verdict["coverage"]["requirements_failed"], 0)

    def test_final_verdict_fails_for_non_reproducible_clean_room_outputs(self) -> None:
        proofs = build_proof_population("candidate-digest")
        verdict = derive_final_verdict(proofs, ("run-a", "run-b"))

        self.assertEqual(verdict["verdict"], "FAIL")

    def test_validator_rejects_missing_requirement_duplicate_and_aggregate_identifier(self) -> None:
        proof = build_proof_population("candidate-digest")[0]
        duplicate = (proof, proof)
        aggregate = (replace(proof, requirement_id=next(iter(PROHIBITED_AGGREGATE_REQUIREMENT_IDS))),)

        self.assertEqual(validate_proof_system(duplicate).status, ProofStatus.FAIL)
        aggregate_result = validate_proof_system(aggregate)
        self.assertEqual(aggregate_result.status, ProofStatus.FAIL)
        self.assertTrue(any("aggregate requirement identifier" in finding for finding in aggregate_result.findings))

    def test_validator_rejects_unexecuted_verification_and_pass_without_raw_evidence(self) -> None:
        proof = build_proof_population("candidate-digest")[0]
        unexecuted = replace(proof, verification_executions=proof.verification_executions[:-1])
        no_evidence = replace(proof, raw_evidence=())

        self.assertEqual(validate_proof_system((unexecuted,)).status, ProofStatus.FAIL)
        result = validate_proof_system((no_evidence,))
        self.assertEqual(result.status, ProofStatus.FAIL)
        self.assertTrue(any("PASS without raw evidence" in finding for finding in result.findings))

    def test_validator_rejects_label_evidence_digest_mismatch_and_candidate_verdict_evidence(self) -> None:
        proof = build_proof_population("candidate-digest")[0]
        evidence = proof.raw_evidence[0]
        bad_digest = replace(evidence, content_digest="not-the-digest")
        candidate_summary = replace(evidence, source="certification_result.json")
        no_provenance = replace(evidence, provenance_chain=())

        self.assertEqual(validate_proof_system((replace(proof, raw_evidence=(bad_digest,)),)).status, ProofStatus.FAIL)
        self.assertEqual(validate_proof_system((replace(proof, raw_evidence=(candidate_summary,)),)).status, ProofStatus.FAIL)
        self.assertEqual(validate_proof_system((replace(proof, raw_evidence=(no_provenance,)),)).status, ProofStatus.FAIL)

    def test_validator_rejects_circular_evidence_unresolved_conflict_and_not_executed(self) -> None:
        proof = build_proof_population("candidate-digest")[0]
        circular = replace(proof.raw_evidence[0], evidence_id=proof.proof_id)
        conflict = replace(proof, disposition=ProofStatus.CONSTITUTIONAL_CONFLICT)
        not_executed = replace(proof, disposition=ProofStatus.NOT_EXECUTED)

        self.assertEqual(validate_proof_system((replace(proof, raw_evidence=(circular,)),)).status, ProofStatus.FAIL)
        self.assertEqual(validate_proof_system((conflict,)).status, ProofStatus.FAIL)
        self.assertEqual(validate_proof_system((not_executed,)).status, ProofStatus.FAIL)

    def test_coverage_and_execution_package_are_requirement_level(self) -> None:
        package = execute_requirement_proof_system("candidate-digest")
        coverage = package["coverage"]

        self.assertEqual(package["final_verdict"]["verdict"], "UNCONDITIONAL PASS")
        self.assertEqual(package["clean_room_reproducibility"]["comparison"], "IDENTICAL")
        self.assertEqual(coverage["total_requirements"], coverage["requirements_passed"])
        self.assertGreater(coverage["total_requirements"], len(build_proof_population("candidate-digest")) - 1)


if __name__ == "__main__":
    unittest.main()
