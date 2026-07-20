from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.candidate_integrity import build_cic01_candidate_contract, stable_hash  # noqa: E402
from argos.control_panel.certified_baseline_bootstrap import (  # noqa: E402
    CIC05FailureCode,
    PromotionAuthorization,
    bootstrap_initial_baseline,
    evaluate_baseline_eligibility,
    load_authoritative_baseline,
    verify_baseline,
)
from argos.control_panel.certification_governance_ledger import (  # noqa: E402
    GovernanceAction,
    evaluate_certification_eligibility,
    generate_authoritative_governance_evidence,
)
from argos.control_panel.semantic_drift_engine import (  # noqa: E402
    DriftClassification,
    compare_authoritative_baseline_to_candidate,
    validate_required_domain_inputs,
)
from Tests.test_cic01_candidate_integrity import DeterministicGitRepo  # noqa: E402


def cic02_pass(contract: dict) -> dict:
    candidate = contract["candidateIdentity"]
    cr7 = {"constitutionalVerdict": "PASS", "candidateIdentity": candidate, "commitIdentity": candidate["repositoryCommit"], "deterministicContentHash": stable_hash("cr7")}
    cr10 = {"qualified": True, "candidateIdentity": candidate, "repositoryCommit": candidate["repositoryCommit"], "deterministicHash": stable_hash("cr10")}
    verdict = {"status": "PASS", "verdictDigest": stable_hash("cic02"), "candidateContractDigest": contract["candidateContractDigest"]}
    return {"repositoryCommit": candidate["repositoryCommit"], "cr7Evidence": cr7, "cr10Qualification": cr10, "cic02AuthoritativeVerdict": verdict, "canonicalTestManifest": {"orderedTests": ({"testIdentifier": "t", "sourceHash": "h"},)}}


def cic03_pass(contract: dict) -> dict:
    candidate = contract["candidateIdentity"]
    return {"verdict": "PASS", "repositoryCommit": candidate["repositoryCommit"], "candidateIdentity": candidate, "subsystemResults": tuple({"subsystem_id": f"CSS-00{i}", "status": "PASS", "evidence_hash": stable_hash(i), "candidateIdentityDigest": candidate["candidateIdentityDigest"], "repositoryCommit": candidate["repositoryCommit"]} for i in range(1, 7))}


def cic04_pass(contract: dict) -> dict:
    candidate = contract["candidateIdentity"]
    verdict = {"status": "PASS", "gateSatisfied": True, "verdictDigest": stable_hash("cic04"), "candidateIdentityDigest": candidate["candidateIdentityDigest"], "repositoryCommit": candidate["repositoryCommit"], "evaluatedClaimIdentifiers": ("claim",)}
    return {"verdict": "PASS", "repositoryCommit": candidate["repositoryCommit"], "candidateIdentityDigest": candidate["candidateIdentityDigest"], "authoritativeVerdict": verdict}


def auth(contract: dict) -> PromotionAuthorization:
    return PromotionAuthorization("auth", "INITIAL_BOOTSTRAP", contract["candidateIdentity"]["candidateIdentityDigest"], "authority", "baseline_bootstrap", stable_hash("gates"), valid=True)


class CIC05AuthoritativeChainTests(unittest.TestCase):
    def test_cic05_bootstrap_creates_verifiable_fourteen_domain_baseline(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)
            store = Path(tempfile.mkdtemp(prefix="argos-cic05-store-"))
            try:
                result = bootstrap_initial_baseline(repo.path, store, contract, cic02_result=cic02_pass(contract), cic03_result=cic03_pass(contract), cic04_result=cic04_pass(contract), css_bootstrap_gates=cic03_pass(contract)["subsystemResults"], authorization=auth(contract))
                loaded = load_authoritative_baseline(store)
            finally:
                shutil.rmtree(store, ignore_errors=True)

        self.assertEqual("PASS", result["status"])
        self.assertEqual(14, result["baseline"]["semanticManifest"]["completedDomainCount"])
        self.assertTrue(result["verification"]["valid"])
        self.assertEqual("PASS", loaded["status"])

    def test_cic05_rejects_missing_cr7_and_zero_commit(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)
        bad = {**contract, "candidateIdentity": {**contract["candidateIdentity"], "repositoryCommit": "0" * 40}}
        eligibility = evaluate_baseline_eligibility(bad, cic02_result={}, cic03_result=cic03_pass(contract), cic04_result=cic04_pass(contract), authorization=auth(contract))

        self.assertIn(CIC05FailureCode.ZERO_CANDIDATE_COMMIT.value, eligibility["failureCodes"])
        self.assertIn(CIC05FailureCode.CR7_NOT_PASS.value, eligibility["failureCodes"])

    def test_cic06_production_rejects_empty_unproven_domains(self) -> None:
        empty = {"domains": {domain: {"semanticObjects": (), "evidenceReferences": (), "proofReferences": (), "validationStatus": "VALID", "completenessVerdict": "COMPLETE"} for domain in (
            "REPOSITORY_IMPLEMENTATION",
            "RUNTIME_BEHAVIOR",
            "AUTHORITY_ASSIGNMENTS",
            "WORKFLOW_TOPOLOGY",
            "LAW_VII_ENFORCEMENT",
            "CERTIFICATION_RULES",
            "EVIDENCE_SCHEMAS_PROVENANCE",
            "TRACE_GRAPH",
            "CONSTITUTIONAL_GUARANTEES",
            "SYNTHETIC_TRUTH_REACHABILITY",
            "TEST_DENOMINATOR",
            "CANONICAL_BRIDGE_INVENTORY",
            "PROTECTED_MUTATION_SITES",
            "PROVIDER_FALLBACK_CONFIGURATION",
        )}}
        validation = validate_required_domain_inputs(empty, empty)

        self.assertFalse(validation["valid"])
        self.assertTrue(any("CIC06_EMPTY_VERSUS_EMPTY_UNKNOWN" in code for code in validation["failureCodes"]))

    def test_cic06_and_cic07_consume_authoritative_cic05_baseline(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)
            c02 = cic02_pass(contract)
            c03 = cic03_pass(contract)
            c04 = cic04_pass(contract)
            store = Path(tempfile.mkdtemp(prefix="argos-cic-chain-store-"))
            out = Path(tempfile.mkdtemp(prefix="argos-cic07-out-"))
            try:
                c05 = bootstrap_initial_baseline(repo.path, store, contract, cic02_result=c02, cic03_result=c03, cic04_result=c04, css_bootstrap_gates=c03["subsystemResults"], authorization=auth(contract))
                c06 = compare_authoritative_baseline_to_candidate(repo.path, candidate_contract=contract, baseline_store=store, cic02_result=c02, cic03_result=c03, cic04_result=c04)
                c07 = generate_authoritative_governance_evidence(
                    candidate_contract=contract,
                    cic02_result=c02,
                    cic04_result=c04,
                    cic05_result=c05,
                    cic06_report=c06,
                    authority_record={"actorId": "authority", "actions": (GovernanceAction.ISSUE.value,), "candidateIdentityDigest": contract["candidateIdentity"]["candidateIdentityDigest"], "scope": "paper_candidate_certification", "valid": True},
                    workflow_token={"tokenId": "token", "candidateIdentityDigest": contract["candidateIdentity"]["candidateIdentityDigest"], "valid": True},
                    output_dir=out,
                )
            finally:
                shutil.rmtree(store, ignore_errors=True)
                shutil.rmtree(out, ignore_errors=True)

        self.assertEqual(DriftClassification.NO_DRIFT.value, c06["finalDriftClassification"])
        self.assertTrue(c06["productionGeneration"]["demoRequestUsed"] is False)
        self.assertEqual("PASS", c07["overallCIC07Acceptance"])

    def test_cic07_rejects_demo_or_missing_cic06_report(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)
        decision, eligibility = evaluate_certification_eligibility(contract, cic02_pass(contract), cic04_pass(contract), {"status": "PASS", "verification": {"status": "VALID"}, "baseline": {"baselineIdentifier": "b", "baselineContentHash": "h"}}, {"candidateMayContinueTowardCertification": True})

        self.assertFalse(eligibility["eligible"])
        self.assertIn("CIC07_DRIFT_REPORT_DEMONSTRATION_DATA", eligibility["failureCodes"])
        self.assertEqual("FAIL", decision.constitutional_status)


if __name__ == "__main__":
    unittest.main()
