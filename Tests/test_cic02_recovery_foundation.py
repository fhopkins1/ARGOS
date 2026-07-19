from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.certification_recovery_foundation import (  # noqa: E402
    DenominatorState,
    ExecutionResult,
    build_cr7_evidence_envelope,
    build_denominator_ledger,
    discover_canonical_tests,
    execute_cic02_recovery_foundation,
    issue_cr7_verdict,
    validate_cic02_evidence_package,
    publish_cr_prerequisite_verdict,
    qualify_controlled_paper_candidate,
)
from argos.candidate_integrity import build_cic01_candidate_contract  # noqa: E402
from Tests.test_cic01_candidate_integrity import DeterministicGitRepo  # noqa: E402


class CIC02RecoveryFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = discover_canonical_tests(REPOSITORY_ROOT, commit="TEST-COMMIT")

    def test_discovery_builds_deterministic_canonical_manifest(self) -> None:
        repeated = discover_canonical_tests(REPOSITORY_ROOT, commit="TEST-COMMIT")

        self.assertEqual(self.manifest["manifestHash"], repeated["manifestHash"])
        self.assertEqual("PASS", self.manifest["verdict"])
        self.assertGreater(len(self.manifest["orderedTests"]), 1000)
        self.assertEqual(self.manifest["orderedTests"][0]["canonicalOrderingIndex"], 1)
        self.assertTrue(self.manifest["denominatorIdentifier"])

    def test_denominator_ledger_accounts_for_not_executed_tests_as_failure(self) -> None:
        ledger = build_denominator_ledger(self.manifest)

        self.assertEqual("FAIL", ledger["verdict"])
        self.assertEqual(len(self.manifest["orderedTests"]), ledger["recordCount"])
        self.assertEqual(len(self.manifest["orderedTests"]), ledger["stateCounts"][DenominatorState.NOT_EXECUTED.value])
        self.assertTrue(any(code.startswith("NON_PASS:") for code in ledger["failureCodes"]))

    def test_complete_pass_execution_can_produce_cr7_pass_envelope(self) -> None:
        results = tuple(
            ExecutionResult(
                test_id=test["testIdentifier"],
                state=DenominatorState.PASSED,
                execution_identifier="EXEC-TEST",
                execution_timestamp="2026-07-19T00:00:00Z",
                evidence_references=("unit-test",),
            )
            for test in self.manifest["orderedTests"]
        )
        ledger = build_denominator_ledger(self.manifest, results)
        envelope = build_cr7_evidence_envelope(self.manifest, ledger, commit="TEST-COMMIT")

        self.assertEqual("PASS", ledger["verdict"])
        self.assertEqual("PASS", envelope["constitutionalVerdict"])
        self.assertEqual(envelope["totalTests"], envelope["passCount"])
        self.assertTrue(envelope["deterministicContentHash"])

    def test_timeout_interrupted_error_and_unknown_states_fail_closed(self) -> None:
        states = (
            DenominatorState.TIMEOUT,
            DenominatorState.INTERRUPTED,
            DenominatorState.ERROR,
            DenominatorState.UNKNOWN,
        )
        for state in states:
            with self.subTest(state=state):
                result = ExecutionResult(
                    test_id=self.manifest["orderedTests"][0]["testIdentifier"],
                    state=state,
                    execution_identifier="EXEC-BAD",
                    execution_timestamp="2026-07-19T00:00:00Z",
                )
                ledger = build_denominator_ledger(self.manifest, (result,))
                self.assertEqual("FAIL", ledger["verdict"])
                self.assertIn(state.value, ledger["stateCounts"])

    def test_cr10_qualification_rejects_failed_or_mismatched_cr7_evidence(self) -> None:
        ledger = build_denominator_ledger(self.manifest)
        envelope = build_cr7_evidence_envelope(self.manifest, ledger, commit="OTHER-COMMIT")
        qualification = qualify_controlled_paper_candidate(REPOSITORY_ROOT, envelope, commit="TEST-COMMIT")

        self.assertFalse(qualification["qualified"])
        self.assertIn("CR7_EVIDENCE_NOT_PASS", qualification["failureCodes"])
        self.assertIn("CR7_CANDIDATE_COMMIT_MISMATCH", qualification["failureCodes"])

    def test_css_prerequisite_publication_is_immutable_and_fail_closed(self) -> None:
        payload = execute_cic02_recovery_foundation(REPOSITORY_ROOT, commit="TEST-COMMIT")
        publication = payload["cssPrerequisitePublication"]

        self.assertEqual("CIC-02", payload["orderId"])
        self.assertEqual("FAIL", payload["verdict"])
        self.assertEqual("FAIL", publication["verdictStatus"])
        self.assertTrue(publication["appendOnly"])
        self.assertFalse(payload["runtimeInterface"]["mutable"])

    def test_publication_detects_cr7_cr10_candidate_mismatch(self) -> None:
        ledger = build_denominator_ledger(self.manifest)
        envelope = build_cr7_evidence_envelope(self.manifest, ledger, commit="TEST-COMMIT")
        qualification = qualify_controlled_paper_candidate(REPOSITORY_ROOT, envelope, commit="TEST-COMMIT")
        altered = dict(qualification)
        altered["candidateIdentity"] = {**qualification["candidateIdentity"], "stable_identity_hash": "different"}
        publication = publish_cr_prerequisite_verdict(envelope, altered)

        self.assertEqual("FAIL", publication["verdictStatus"])
        self.assertIn("CR7_CR10_CANDIDATE_MISMATCH", publication["failureCodes"])

    def test_cic02_requires_cic01_contract_and_rejects_ambient_head_substitution(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)
            commit = contract["candidateIdentity"]["repositoryCommit"]

        payload = execute_cic02_recovery_foundation(REPOSITORY_ROOT, commit=commit, candidate_contract=contract)
        missing_contract_payload = execute_cic02_recovery_foundation(REPOSITORY_ROOT, commit=commit)

        self.assertEqual(contract["candidateContractDigest"], payload["cic01CandidateContractDigest"])
        self.assertNotIn("CIC01_CONTRACT_REQUIRED", payload["cic01CandidateContractValidation"]["failureCodes"])
        self.assertIn("CIC01_CONTRACT_REQUIRED", missing_contract_payload["cic01CandidateContractValidation"]["failureCodes"])
        self.assertEqual("FAIL", missing_contract_payload["cic02AuthoritativeVerdict"]["status"])

    def test_summary_cannot_override_authoritative_cr7_verdict(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)

        ledger = build_denominator_ledger(self.manifest)
        envelope = build_cr7_evidence_envelope(self.manifest, ledger, commit=contract["candidateIdentity"]["repositoryCommit"])
        verdict = issue_cr7_verdict(contract, envelope)

        self.assertEqual("FAIL", verdict["status"])
        self.assertIn("CR7_EVIDENCE_NOT_PASS", verdict["failureCodes"])
        self.assertEqual("PASS", {"mutableSummary": "PASS"}["mutableSummary"])

    def test_cic02_package_validation_rejects_mixed_candidate_package(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)
        payload = execute_cic02_recovery_foundation(
            REPOSITORY_ROOT,
            commit=contract["candidateIdentity"]["repositoryCommit"],
            candidate_contract=contract,
        )
        package = {
            "cic01CandidateContract": contract,
            "cr7Evidence": payload["cr7Evidence"],
            "cr10Qualification": payload["cr10Qualification"],
            "cssPrerequisitePublication": payload["cssPrerequisitePublication"],
            "cic02AuthoritativeVerdict": payload["cic02AuthoritativeVerdict"],
        }
        package["cr10Qualification"] = {
            **package["cr10Qualification"],
            "candidateIdentity": {**package["cr10Qualification"]["candidateIdentity"], "candidateIdentityDigest": "different"},
        }

        validation = validate_cic02_evidence_package(package)

        self.assertFalse(validation["valid"])


if __name__ == "__main__":
    unittest.main()
