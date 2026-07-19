from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import shutil
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.candidate_integrity import build_cic01_candidate_contract, stable_hash  # noqa: E402
from argos.control_panel.continuous_constitutional_certification import build_certification_claim_registry, build_repository_truth_index  # noqa: E402
from argos.control_panel.proof_based_certification import (  # noqa: E402
    CIC04_VERSION,
    ClaimState,
    ProofClaim,
    ProofEdge,
    ProofEdgeType,
    ProofGraph,
    ProofNode,
    ProofNodeType,
    claim_satisfies_gate,
    evaluate_proof_claim,
    generate_cic04_evidence,
    issue_proof_based_verdict,
)
from Tests.test_cic01_candidate_integrity import DeterministicGitRepo  # noqa: E402


class CIC04ProofBasedCertificationTests(unittest.TestCase):
    def test_only_proven_satisfies_gate(self) -> None:
        for state in ClaimState:
            self.assertEqual(state == ClaimState.PROVEN, claim_satisfies_gate(state))
        self.assertFalse(claim_satisfies_gate("PASS"))
        self.assertFalse(claim_satisfies_gate("CERTIFIED"))

    def test_complete_candidate_bound_proof_chain_is_proven(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)
            claim, graph = valid_claim_and_graph(contract)
            first = evaluate_proof_claim(claim, graph, contract)
            second = evaluate_proof_claim(claim, graph, contract)
            verdict = issue_proof_based_verdict((first,), contract)

        self.assertEqual(ClaimState.PROVEN.value, first["state"])
        self.assertTrue(first["gateSatisfied"])
        self.assertEqual(first["evaluationDigest"], second["evaluationDigest"])
        self.assertEqual("PASS", verdict["status"])

    def test_each_canonical_state_is_deterministically_produced(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)

        cases = {
            ClaimState.FAILED: lambda c, g: replace_node(g, "execution", terminalOutcome="FAILED"),
            ClaimState.INCOMPLETE: lambda c, g: remove_node(g, "rule"),
            ClaimState.STALE: lambda c, g: replace_node(g, "rule", ruleVersion="OLD"),
            ClaimState.WRONG_CANDIDATE: lambda c, g: replace_first_node_digest(g, "wrong"),
            ClaimState.UNTESTED: lambda c, g: replace_node(g, "execution", executed=False, terminalOutcome="NOT_EXECUTED"),
            ClaimState.UNREACHABLE: lambda c, g: replace_node(g, "runtime", reachesImplementationSymbol=False),
            ClaimState.TRACE_MISSING: lambda c, g: remove_node(g, "trace"),
            ClaimState.EVIDENCE_MISSING: lambda c, g: remove_node(g, "artifact"),
            ClaimState.BYPASS_DETECTED: lambda c, g: replace_node(g, "runtime", bypassDetected=True),
            ClaimState.UNKNOWN: lambda c, g: graph_with_unknown_edge(c, g),
        }
        for expected, mutate in cases.items():
            with self.subTest(expected=expected.value):
                claim, graph = valid_claim_and_graph(contract)
                evaluation = evaluate_proof_claim(claim, mutate(claim, graph), contract)
                self.assertEqual(expected.value, evaluation["state"])
                self.assertFalse(evaluation["gateSatisfied"])

    def test_presence_only_nodes_cannot_satisfy_claim(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)
            claim, graph = valid_claim_and_graph(contract)
            presence_only = ProofGraph(
                graph.graph_id,
                claim.claim_id,
                tuple(node for node in graph.nodes if node.node_id in {"requirement", "rule", "symbol", "test", "artifact", "verdict"}),
                (),
            )
            evaluation = evaluate_proof_claim(claim, presence_only, contract)

        self.assertNotEqual(ClaimState.PROVEN.value, evaluation["state"])
        self.assertIn("MISSING_EDGE", " ".join(evaluation["reasonCodes"]))

    def test_wrong_candidate_artifact_trace_and_verdict_are_rejected(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)
            claim, graph = valid_claim_and_graph(contract)
            wrong = replace_node(graph, "artifact", candidateIdentityDigest="other")
            evaluation = evaluate_proof_claim(claim, wrong, contract)

        self.assertEqual(ClaimState.WRONG_CANDIDATE.value, evaluation["state"])

    def test_execution_trace_evidence_and_verdict_negative_cases_fail_closed(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)
            claim, graph = valid_claim_and_graph(contract)

        variants = (
            replace_node(graph, "execution", terminalOutcome="SKIPPED"),
            replace_node(graph, "execution", terminalOutcome="TIMED_OUT"),
            replace_node(graph, "trace", requiredEventsPresent=False),
            replace_node(graph, "generator", authorized=False),
            replace_node(graph, "artifact", artifactDigest="bad"),
            replace_node(graph, "verdict", source="mutable_summary"),
        )
        for variant in variants:
            with self.subTest():
                evaluation = evaluate_proof_claim(claim, variant, contract)
                self.assertNotEqual(ClaimState.PROVEN.value, evaluation["state"])

    def test_css_claim_registry_uses_proof_state_not_presence_status(self) -> None:
        index = build_repository_truth_index(REPOSITORY_ROOT, commit="TEST-COMMIT")
        registry = build_certification_claim_registry(REPOSITORY_ROOT, commit="TEST-COMMIT", repository_index=index)

        self.assertEqual(5, registry["claimCount"])
        self.assertTrue(all(claim["proofState"] != ClaimState.PROVEN.value for claim in registry["claims"]))
        self.assertTrue(all(claim["verificationStatus"] == "FAIL" for claim in registry["claims"]))

    def test_cic04_evidence_generator_fails_closed_for_dirty_workspace(self) -> None:
        out = Path(tempfile.mkdtemp(prefix="argos-cic04-evidence-"))
        try:
            manifest = generate_cic04_evidence(REPOSITORY_ROOT, out)
            result_path = out / "cic04_result.json"
            self.assertTrue(result_path.exists())
        finally:
            shutil.rmtree(out, ignore_errors=True)

        self.assertEqual("FAIL", manifest["verdict"])


def valid_claim_and_graph(contract: dict) -> tuple[ProofClaim, ProofGraph]:
    candidate = contract["candidateIdentity"]
    digest = candidate["candidateIdentityDigest"]
    commit = candidate["repositoryCommit"]
    claim = ProofClaim(
        "CIC04-CLAIM-VALID",
        "REQ-CIC04",
        "RULE-CIC04",
        CIC04_VERSION,
        digest,
        "GRAPH-CIC04-VALID",
        True,
        "CIC04-VERDICT",
    )
    artifact_payload = {"claim": claim.claim_id, "state": ClaimState.PROVEN.value}
    test_digest = stable_hash("Tests.test_cic04_proof_based_certification.valid_claim")
    nodes = (
        node("requirement", ProofNodeType.CONSTITUTIONAL_REQUIREMENT, digest, commit, {"requirementId": claim.constitutional_requirement_id}),
        node("rule", ProofNodeType.RULE_VERSION, digest, commit, {"ruleId": claim.rule_id, "ruleVersion": claim.rule_version}),
        node("symbol", ProofNodeType.IMPLEMENTATION_SYMBOL, digest, commit, {"module": "argos.control_panel.proof_based_certification", "qualname": "claim_satisfies_gate"}),
        node("runtime", ProofNodeType.RUNTIME_PATH, digest, commit, {"approved": True, "reachesImplementationSymbol": True, "bypassDetected": False}),
        node("test", ProofNodeType.TEST_IDENTITY, digest, commit, {"testId": "Tests.test_cic04_proof_based_certification.valid_claim", "testDefinitionDigest": test_digest}),
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


def node(node_id, node_type, digest, commit, identity):
    return ProofNode(node_id, node_type, identity, "test", candidate_identity_digest=digest, repository_commit=commit)


def edge(edge_id, source, target, edge_type, digest, version):
    return ProofEdge(edge_id, source, target, edge_type, "test", "VERIFIED", {}, candidate_identity_digest=digest, rule_version=version)


def replace_node(graph: ProofGraph, node_id: str, **identity_updates) -> ProofGraph:
    nodes = []
    for item in graph.nodes:
        if item.node_id == node_id:
            identity = {**item.canonical_identity, **identity_updates}
            candidate_digest = str(identity_updates.get("candidateIdentityDigest", item.candidate_identity_digest))
            nodes.append(replace(item, canonical_identity=identity, candidate_identity_digest=candidate_digest))
        else:
            nodes.append(item)
    return replace(graph, nodes=tuple(nodes))


def replace_first_node_digest(graph: ProofGraph, digest: str) -> ProofGraph:
    first = replace(graph.nodes[0], candidate_identity_digest=digest)
    return replace(graph, nodes=(first, *graph.nodes[1:]))


def remove_node(graph: ProofGraph, node_id: str) -> ProofGraph:
    nodes = tuple(node for node in graph.nodes if node.node_id != node_id)
    edges = tuple(edge for edge in graph.edges if edge.source_node_id != node_id and edge.target_node_id != node_id)
    return replace(graph, nodes=nodes, edges=edges)


def graph_with_unknown_edge(claim: ProofClaim, graph: ProofGraph) -> ProofGraph:
    edges = tuple(replace(edge, verification_result="MAYBE") for edge in graph.edges)
    return replace(graph, edges=edges)


if __name__ == "__main__":
    unittest.main()
