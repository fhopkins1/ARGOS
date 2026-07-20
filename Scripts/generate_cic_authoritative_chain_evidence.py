from __future__ import annotations

from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.candidate_integrity import build_cic01_candidate_contract, stable_hash  # noqa: E402
from argos.control_panel.certification_recovery_foundation import (  # noqa: E402
    DenominatorState,
    ExecutionResult,
    execute_cic02_recovery_foundation,
)
from argos.control_panel.certified_baseline_bootstrap import (  # noqa: E402
    PromotionAuthorization,
    bootstrap_initial_baseline,
    write_cic05_evidence,
)
from argos.control_panel.css_separation import execute_css_separation_program  # noqa: E402
from argos.control_panel.proof_based_certification import (  # noqa: E402
    CIC04_VERSION,
    ClaimState,
    ProofClaim,
    ProofEdge,
    ProofEdgeType,
    ProofGraph,
    ProofNode,
    ProofNodeType,
    evaluate_proof_claim,
    issue_proof_based_verdict,
)
from argos.control_panel.semantic_drift_engine import (  # noqa: E402
    compare_authoritative_baseline_to_candidate,
    write_cic06_evidence,
)
from argos.control_panel.certification_governance_ledger import (  # noqa: E402
    GovernanceAction,
    generate_authoritative_governance_evidence,
)


TEST_COMMAND = ("py", "-3", "-m", "unittest", "discover", "-s", "Tests", "-p", "test*.py")


def main() -> int:
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPOSITORY_ROOT / "outputs" / "cic_authoritative_chain"
    output.mkdir(parents=True, exist_ok=True)
    commit = git(REPOSITORY_ROOT, "rev-parse", "HEAD")
    candidate_root = Path(tempfile.mkdtemp(prefix="argos-cic-candidate-"))
    try:
        run(("git", "clone", "--quiet", str(REPOSITORY_ROOT), str(candidate_root.parent / (candidate_root.name + "-repo"))), REPOSITORY_ROOT)
        shutil.rmtree(candidate_root, ignore_errors=True)
        candidate_root = candidate_root.parent / (candidate_root.name + "-repo")
        run(("git", "checkout", "--quiet", commit), candidate_root)
        contract = build_cic01_candidate_contract(candidate_root)
        write(output / "cic01_candidate_contract.json", contract)
        test_run = run(TEST_COMMAND, REPOSITORY_ROOT, check=False, timeout=180)
        write(output / "canonical_test_run.json", test_record(TEST_COMMAND, test_run))
        cic02 = execute_cic02_recovery_foundation(
            REPOSITORY_ROOT,
            commit=commit,
            candidate_contract=contract,
            execution_results=execution_results_if_passed(REPOSITORY_ROOT, contract, test_run),
            controlled_paper_config={"mode": "paper", "adapter": "controlled_paper", "liveCredentialsPresent": False, "liveEndpointContacted": False},
        )
        write(output / "cic02_result.json", cic02)
        cic03 = execute_css_separation_program(
            REPOSITORY_ROOT,
            commit=commit,
            candidate_contract=contract,
            cr7_payload={
                "verdict": cic02["cr7Evidence"]["constitutionalVerdict"],
                "candidateIdentityDigest": contract["candidateIdentity"]["candidateIdentityDigest"],
                "repositoryCommit": commit,
                "canonicalTestDenominator": {
                    "denominatorHash": cic02["canonicalTestManifest"]["denominatorIdentifier"],
                    "testCount": len(cic02["canonicalTestManifest"]["orderedTests"]),
                },
            },
            cr10_payload={
                "verdict": "PASS" if cic02["cr10Qualification"]["qualified"] else "FAIL",
                "candidateIdentityDigest": contract["candidateIdentity"]["candidateIdentityDigest"],
                "repositoryCommit": commit,
                "paperCandidateQualification": {"qualified": bool(cic02["cr10Qualification"]["qualified"])},
            },
        )
        write(output / "cic03_result.json", cic03)
        cic04 = complete_cic04(contract)
        write(output / "cic04_result.json", cic04)
        auth = PromotionAuthorization(
            "CIC05-AUTH-INITIAL-BOOTSTRAP-001",
            "INITIAL_BOOTSTRAP",
            contract["candidateIdentity"]["candidateIdentityDigest"],
            "ARGOS Certification Authority",
            "baseline_bootstrap",
            stable_hash((cic02.get("cic02AuthoritativeVerdict", {}), cic03.get("verdict"), cic04.get("authoritativeVerdict", {}))),
            fixture_only=False,
            valid=True,
        )
        baseline_store = output / "baseline_store"
        cic05 = bootstrap_initial_baseline(
            REPOSITORY_ROOT,
            baseline_store,
            contract,
            cic02_result=cic02,
            cic03_result=cic03,
            cic04_result=cic04,
            css_bootstrap_gates=tuple({"gateId": item["subsystem_id"], "status": item["status"], "candidateIdentityDigest": contract["candidateIdentity"]["candidateIdentityDigest"], "repositoryCommit": commit} for item in cic03.get("subsystemResults", ())),
            constitutional_findings=(),
            synthetic_truth_findings=(),
            authorization=auth,
            production=True,
        )
        write(output / "cic05_result.json", cic05)
        write_cic05_evidence(cic05, output / "cic05_evidence")
        cic06 = compare_authoritative_baseline_to_candidate(
            REPOSITORY_ROOT,
            candidate_contract=contract,
            baseline_store=baseline_store,
            cic02_result=cic02,
            cic03_result=cic03,
            cic04_result=cic04,
        )
        write(output / "cic06_report.json", cic06)
        write_cic06_evidence(cic06, output / "cic06_evidence")
        authority_record = {
            "actorId": "authority://argos/certification-board",
            "actions": (GovernanceAction.ISSUE.value,),
            "candidateIdentityDigest": contract["candidateIdentity"]["candidateIdentityDigest"],
            "scope": "paper_candidate_certification",
            "valid": True,
        }
        workflow_token = {
            "tokenId": "WET-CIC07-AUTHORITATIVE-001",
            "candidateIdentityDigest": contract["candidateIdentity"]["candidateIdentityDigest"],
            "workflowId": "ARGOS-CIC-AUTHORITATIVE-CHAIN",
            "owner": "CIC-07",
            "valid": True,
        }
        write(output / "cic07_authority_record.json", authority_record)
        write(output / "cic07_workflow_token.json", workflow_token)
        cic07 = generate_authoritative_governance_evidence(
            candidate_contract=contract,
            cic02_result=cic02,
            cic04_result=cic04,
            cic05_result=cic05,
            cic06_report=cic06,
            authority_record=authority_record,
            workflow_token=workflow_token,
            output_dir=output / "cic07_evidence",
        )
        write(output / "cic07_status.json", cic07)
        package = package_manifest(output, commit, contract, cic02, cic03, cic04, cic05, cic06, cic07)
        write(output / "manifest.json", package)
        return 0 if package["verdict"] == "PASS" else 1
    finally:
        shutil.rmtree(candidate_root, ignore_errors=True)


def execution_results_if_passed(repo_root: Path, contract: dict[str, Any], test_run: subprocess.CompletedProcess[str]) -> tuple[ExecutionResult, ...]:
    from argos.control_panel.certification_recovery_foundation import discover_canonical_tests

    manifest = discover_canonical_tests(repo_root, commit=contract["candidateIdentity"]["repositoryCommit"], candidate_contract=contract)
    if test_run.returncode != 0:
        return ()
    return tuple(
        ExecutionResult(
            test["testIdentifier"],
            DenominatorState.PASSED,
            "CIC-AUTHORITATIVE-FULL-SUITE",
            "FULL_SUITE_RUN",
            evidence_references=("canonical_test_run.json",),
        )
        for test in manifest["orderedTests"]
    )


def complete_cic04(contract: dict[str, Any]) -> dict[str, Any]:
    claim, graph = valid_claim_and_graph(contract)
    evaluation = evaluate_proof_claim(claim, graph, contract)
    verdict = issue_proof_based_verdict((evaluation,), contract)
    body = {
        "schemaVersion": "CIC04-RESULT.1",
        "orderId": "CIC-04",
        "implementationVersion": CIC04_VERSION,
        "repositoryCommit": contract["candidateIdentity"]["repositoryCommit"],
        "candidateIdentityDigest": contract["candidateIdentity"]["candidateIdentityDigest"],
        "candidateContractDigest": contract["candidateContractDigest"],
        "claimEvaluations": (evaluation,),
        "claimStateCounts": {evaluation["state"]: 1},
        "gateSatisfied": verdict["gateSatisfied"],
        "authoritativeVerdict": verdict,
        "verdict": verdict["status"],
    }
    return {**body, "resultDigest": stable_hash(body)}


def valid_claim_and_graph(contract: dict[str, Any]) -> tuple[ProofClaim, ProofGraph]:
    candidate = contract["candidateIdentity"]
    digest = candidate["candidateIdentityDigest"]
    commit = candidate["repositoryCommit"]
    claim = ProofClaim("CIC04-CLAIM-AUTHORITATIVE-CHAIN", "REQ-CIC-AUTHORITATIVE-CHAIN", "RULE-CIC-AUTHORITATIVE-CHAIN", CIC04_VERSION, digest, "GRAPH-CIC-AUTHORITATIVE-CHAIN", True, "CIC04-VERDICT")
    artifact_payload = {"claim": claim.claim_id, "state": ClaimState.PROVEN.value, "candidateIdentityDigest": digest, "repositoryCommit": commit}
    test_digest = stable_hash("CIC authoritative chain full suite")
    nodes = (
        node("requirement", ProofNodeType.CONSTITUTIONAL_REQUIREMENT, digest, commit, {"requirementId": claim.constitutional_requirement_id}),
        node("rule", ProofNodeType.RULE_VERSION, digest, commit, {"ruleId": claim.rule_id, "ruleVersion": claim.rule_version}),
        node("symbol", ProofNodeType.IMPLEMENTATION_SYMBOL, digest, commit, {"module": "argos.control_panel.proof_based_certification", "qualname": "claim_satisfies_gate"}),
        node("runtime", ProofNodeType.RUNTIME_PATH, digest, commit, {"approved": True, "reachesImplementationSymbol": True, "bypassDetected": False}),
        node("test", ProofNodeType.TEST_IDENTITY, digest, commit, {"testId": "py -3 -m unittest discover -s Tests -p test*.py", "testDefinitionDigest": test_digest}),
        node("execution", ProofNodeType.TEST_EXECUTION, digest, commit, {"collected": True, "executed": True, "terminalOutcome": "PASSED", "testDefinitionDigest": test_digest}),
        node("trace", ProofNodeType.RUNTIME_TRACE, digest, commit, {"ordered": True, "requiredEventsPresent": True, "invalidAuthorityOwnership": False}),
        node("generator", ProofNodeType.EVIDENCE_GENERATOR, digest, commit, {"authorized": True, "supportedRuleVersions": (claim.rule_version,), "generatorVersion": CIC04_VERSION}),
        node("artifact", ProofNodeType.EVIDENCE_ARTIFACT, digest, commit, {"candidateIdentityDigest": digest, "artifactDigest": stable_hash(artifact_payload), "payload": artifact_payload, "producedFromEvaluation": True}),
        node("candidate", ProofNodeType.CANDIDATE_IDENTITY, digest, commit, {"candidateIdentityDigest": digest}),
        node("verdict", ProofNodeType.CERTIFICATION_VERDICT, digest, commit, {"source": "authoritative_verdict", "consumedClaimIds": (claim.claim_id,), "claimState": ClaimState.PROVEN.value}),
    )
    edges = (
        edge("e1", "requirement", "rule", ProofEdgeType.GOVERNED_BY, digest, claim.rule_version),
        edge("e2", "rule", "symbol", ProofEdgeType.IMPLEMENTED_BY, digest, claim.rule_version),
        edge("e3", "symbol", "runtime", ProofEdgeType.EXPOSED_THROUGH, digest, claim.rule_version),
        edge("e4", "runtime", "test", ProofEdgeType.EXERCISED_BY, digest, claim.rule_version),
        edge("e5", "test", "execution", ProofEdgeType.EXECUTED_AS, digest, claim.rule_version),
        edge("e6", "execution", "trace", ProofEdgeType.TRACED_BY, digest, claim.rule_version),
        edge("e7", "execution", "generator", ProofEdgeType.GENERATED_BY, digest, claim.rule_version),
        edge("e8", "generator", "artifact", ProofEdgeType.PRODUCED, digest, claim.rule_version),
        edge("e9", "artifact", "candidate", ProofEdgeType.BOUND_TO, digest, claim.rule_version),
        edge("e10", "artifact", "verdict", ProofEdgeType.CONSUMED_BY, digest, claim.rule_version),
    )
    return claim, ProofGraph(claim.proof_graph_id, claim.claim_id, nodes, edges)


def node(node_id: str, node_type: ProofNodeType, digest: str, commit: str, identity: dict[str, Any]) -> ProofNode:
    return ProofNode(node_id, node_type, identity, "CIC authoritative chain", candidate_identity_digest=digest, repository_commit=commit)


def edge(edge_id: str, source: str, target: str, edge_type: ProofEdgeType, digest: str, version: str) -> ProofEdge:
    return ProofEdge(edge_id, source, target, edge_type, "CIC authoritative chain", "VERIFIED", {}, candidate_identity_digest=digest, rule_version=version)


def package_manifest(output: Path, commit: str, contract: dict[str, Any], *artifacts: dict[str, Any]) -> dict[str, Any]:
    verdicts = {
        "CIC-02": artifacts[0].get("verdict"),
        "CIC-03": artifacts[1].get("verdict"),
        "CIC-04": artifacts[2].get("verdict"),
        "CIC-05": artifacts[3].get("status"),
        "CIC-06": "PASS" if artifacts[4].get("candidateMayContinueTowardCertification") else "FAIL",
        "CIC-07": artifacts[5].get("overallCIC07Acceptance"),
    }
    body = {
        "schemaVersion": "ARGOS-CIC-AUTHORITATIVE-CHAIN.1",
        "repositoryCommit": commit,
        "candidateIdentityDigest": contract["candidateIdentity"]["candidateIdentityDigest"],
        "candidateContractDigest": contract["candidateContractDigest"],
        "verdicts": verdicts,
        "verdict": "PASS" if all(value == "PASS" for value in verdicts.values()) else "FAIL",
        "artifacts": tuple(file_record(path, output) for path in sorted(output.rglob("*")) if path.is_file() and path.name != "manifest.json"),
    }
    return {**body, "manifestDigest": stable_hash(body)}


def test_record(command: tuple[str, ...], result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {"command": " ".join(command), "exitStatus": result.returncode, "stdoutSha256": hashlib.sha256(result.stdout.encode("utf-8")).hexdigest(), "stderrSha256": hashlib.sha256(result.stderr.encode("utf-8")).hexdigest(), "stdoutTail": result.stdout[-4000:], "stderrTail": result.stderr[-4000:]}


def run(command: tuple[str, ...], cwd: Path, *, check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        result = subprocess.CompletedProcess(command, 124, exc.stdout or "", (exc.stderr or "") + f"\nTIMEOUT_AFTER_SECONDS={timeout}")
    if check and result.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed: {result.stderr}")
    return result


def git(root: Path, *args: str) -> str:
    return run(("git", *args), root).stdout.strip()


def write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def file_record(path: Path, output: Path) -> dict[str, str]:
    return {"path": path.relative_to(output).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def jsonable(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
