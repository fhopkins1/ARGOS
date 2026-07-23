from dataclasses import replace
from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.trader.requirement_proof import ProofStatus, build_requirement_registry, derive_final_verdict  # noqa: E402
from argos.trader.requirement_verifier import (  # noqa: E402
    EvidenceValidationState,
    ExecutionDisposition,
    build_behavioral_proof_package,
    demonstrate_fail_closed_behavior,
    dispatch_verifier,
    execute_behavioral_verification_system,
    produce_and_validate_evidence,
    recalculate_proofs,
    validate_raw_evidence,
)


class TraderRequirementVerifierTests(unittest.TestCase):
    def test_actual_verifier_execution_creates_execution_and_valid_evidence(self) -> None:
        package = build_behavioral_proof_package("candidate-digest")
        execution = package.execution_registry[0]
        evidence = package.raw_evidence_registry[0]

        self.assertEqual(execution.disposition, ExecutionDisposition.PASS)
        self.assertIn("actual Trader implementation path invoked", execution.observed_events)
        self.assertEqual(execution.comparison_result, "MATCH")
        self.assertEqual(evidence.validation_state, EvidenceValidationState.VALID)
        self.assertTrue(evidence.raw_content)

    def test_all_proofs_recalculate_from_current_executions(self) -> None:
        package = build_behavioral_proof_package("candidate-digest")

        self.assertTrue(package.proof_objects)
        self.assertTrue(all(proof.disposition == ProofStatus.PASS for proof in package.proof_objects))
        self.assertEqual(package.final_verdict["verdict"], "UNCONDITIONAL PASS")

    def test_missing_verifier_forces_not_executed_and_fail_verdict(self) -> None:
        requirement = build_requirement_registry("candidate-digest")[0]
        proof = recalculate_proofs((requirement,), (), (), ())[0]
        verdict = derive_final_verdict((proof,), ("same", "same"))

        self.assertEqual(proof.disposition, ProofStatus.NOT_EXECUTED)
        self.assertEqual(verdict["verdict"], "FAIL")

    def test_defect_changes_observed_result_and_fails_evidence_validation(self) -> None:
        package = build_behavioral_proof_package("candidate-digest")
        verifier = package.verifier_registry[0]
        fixture = replace(package.fixture_registry[0], expected={**package.fixture_registry[0].expected, "disposition": "FAIL"})
        execution = dispatch_verifier(verifier, fixture, "candidate-digest")
        evidence = produce_and_validate_evidence(execution, fixture, "candidate-digest")

        self.assertEqual(execution.disposition, ExecutionDisposition.FAIL)
        self.assertEqual(evidence.validation_state, EvidenceValidationState.INVALID)
        self.assertIn("expected and observed results diverged", evidence.validation_report)

    def test_evidence_rejects_candidate_summary_metadata_and_digest_mismatch(self) -> None:
        package = build_behavioral_proof_package("candidate-digest")
        execution = package.execution_registry[0]
        fixture = package.fixture_registry[0]
        evidence = package.raw_evidence_registry[0].evidence

        candidate_summary = replace(evidence, source="certification_result.json")
        bad_digest = replace(evidence, content_digest="bad")
        no_raw = validate_raw_evidence(evidence, {}, execution, fixture)

        self.assertEqual(validate_raw_evidence(candidate_summary, {"raw": True}, execution, fixture).validation_state, EvidenceValidationState.INVALID)
        self.assertEqual(validate_raw_evidence(bad_digest, {"raw": True}, execution, fixture).validation_state, EvidenceValidationState.INVALID)
        self.assertEqual(no_raw.validation_state, EvidenceValidationState.INVALID)

    def test_timeout_and_contradiction_demonstrations_fail_closed(self) -> None:
        package = build_behavioral_proof_package("candidate-digest")
        demo = demonstrate_fail_closed_behavior(
            package.requirement_registry[0],
            package.verifier_registry[0],
            package.fixture_registry[0],
            "candidate-digest",
        )

        self.assertEqual(demo["timeout"]["execution_disposition"], "TIMEOUT")
        self.assertEqual(demo["synthetic_evidence"]["validation_state"], "INVALID")
        self.assertEqual(demo["contradiction"]["validation_state"], "CONTRADICTORY")
        self.assertEqual(demo["missing_verifier"]["final_verdict"], "FAIL")

    def test_behavioral_system_summary_is_clean_room_reproducible(self) -> None:
        first = execute_behavioral_verification_system("candidate-digest")
        second = execute_behavioral_verification_system("candidate-digest")

        self.assertEqual(first["final_verdict"]["verdict"], "UNCONDITIONAL PASS")
        self.assertEqual(first["package_digest"], second["package_digest"])
        self.assertEqual(first["verifier_count"], first["execution_count"])
        self.assertEqual(first["execution_count"], first["evidence_count"])


if __name__ == "__main__":
    unittest.main()
