"""CIC-04 proof-based certification claim evaluation.

Existence is not proof.  This module evaluates certification claims only from
explicit, candidate-bound proof graphs whose nodes and edges connect a
constitutional requirement to the final authoritative verdict.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import argparse
import hashlib
import importlib
import inspect
import json
from pathlib import Path
from typing import Any, Iterable

from argos.candidate_integrity import (
    CIC01Rejection,
    build_cic01_candidate_contract,
    stable_hash,
    validate_cic01_contract,
)
from argos.foundation.contracts import utc_timestamp


CIC04_VERSION = "CIC-04.1"
PROOF_GRAPH_SCHEMA_VERSION = "CIC04-PROOF-GRAPH.1"
PROOF_EVALUATION_SCHEMA_VERSION = "CIC04-PROOF-EVALUATION.1"
PROOF_VERDICT_SCHEMA_VERSION = "CIC04-PROOF-VERDICT.1"


class ClaimState(str, Enum):
    PROVEN = "PROVEN"
    FAILED = "FAILED"
    INCOMPLETE = "INCOMPLETE"
    STALE = "STALE"
    WRONG_CANDIDATE = "WRONG_CANDIDATE"
    UNTESTED = "UNTESTED"
    UNREACHABLE = "UNREACHABLE"
    TRACE_MISSING = "TRACE_MISSING"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    BYPASS_DETECTED = "BYPASS_DETECTED"
    UNKNOWN = "UNKNOWN"


class ProofNodeType(str, Enum):
    CONSTITUTIONAL_REQUIREMENT = "CONSTITUTIONAL_REQUIREMENT"
    RULE_VERSION = "RULE_VERSION"
    IMPLEMENTATION_SYMBOL = "IMPLEMENTATION_SYMBOL"
    RUNTIME_PATH = "RUNTIME_PATH"
    TEST_IDENTITY = "TEST_IDENTITY"
    TEST_EXECUTION = "TEST_EXECUTION"
    RUNTIME_TRACE = "RUNTIME_TRACE"
    EVIDENCE_GENERATOR = "EVIDENCE_GENERATOR"
    EVIDENCE_ARTIFACT = "EVIDENCE_ARTIFACT"
    CANDIDATE_IDENTITY = "CANDIDATE_IDENTITY"
    CERTIFICATION_VERDICT = "CERTIFICATION_VERDICT"


class ProofEdgeType(str, Enum):
    GOVERNED_BY = "GOVERNED_BY"
    IMPLEMENTED_BY = "IMPLEMENTED_BY"
    EXPOSED_THROUGH = "EXPOSED_THROUGH"
    EXERCISED_BY = "EXERCISED_BY"
    EXECUTED_AS = "EXECUTED_AS"
    TRACED_BY = "TRACED_BY"
    GENERATED_BY = "GENERATED_BY"
    PRODUCED = "PRODUCED"
    BOUND_TO = "BOUND_TO"
    CONSUMED_BY = "CONSUMED_BY"


STATE_PRECEDENCE = (
    ClaimState.BYPASS_DETECTED,
    ClaimState.WRONG_CANDIDATE,
    ClaimState.STALE,
    ClaimState.UNREACHABLE,
    ClaimState.UNTESTED,
    ClaimState.TRACE_MISSING,
    ClaimState.EVIDENCE_MISSING,
    ClaimState.FAILED,
    ClaimState.INCOMPLETE,
    ClaimState.UNKNOWN,
    ClaimState.PROVEN,
)


@dataclass(frozen=True)
class ProofClaim:
    claim_id: str
    constitutional_requirement_id: str
    rule_id: str
    rule_version: str
    candidate_identity_digest: str
    proof_graph_id: str
    runtime_trace_required: bool
    expected_verdict_consumer: str
    evaluator_identity: str = "argos.control_panel.proof_based_certification.evaluate_proof_claim"
    evaluator_version: str = CIC04_VERSION


@dataclass(frozen=True)
class ProofNode:
    node_id: str
    node_type: ProofNodeType
    canonical_identity: dict[str, Any]
    source_authority: str
    schema_version: str = PROOF_GRAPH_SCHEMA_VERSION
    verification_status: str = "DECLARED"
    candidate_identity_digest: str = ""
    repository_commit: str = ""
    content_digest: str = ""


@dataclass(frozen=True)
class ProofEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: ProofEdgeType
    verification_method: str
    verification_result: str
    evidence: dict[str, Any]
    candidate_identity_digest: str = ""
    rule_version: str = ""
    failure_reason: str = ""


@dataclass(frozen=True)
class ProofGraph:
    graph_id: str
    claim_id: str
    nodes: tuple[ProofNode, ...]
    edges: tuple[ProofEdge, ...]
    schema_version: str = PROOF_GRAPH_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        body = _jsonable(asdict(self))
        return {**body, "proofGraphDigest": stable_hash(body)}


def claim_satisfies_gate(state: ClaimState | str) -> bool:
    try:
        normalized = state if isinstance(state, ClaimState) else ClaimState(str(state))
    except ValueError:
        return False
    return normalized == ClaimState.PROVEN


def evaluate_proof_claim(claim: ProofClaim | dict[str, Any], graph: ProofGraph | dict[str, Any], candidate_contract: dict[str, Any]) -> dict[str, Any]:
    claim_obj = _claim(claim)
    graph_obj = _graph(graph)
    reasons: list[str] = []
    candidate_validation = validate_cic01_contract(candidate_contract) if candidate_contract else {"valid": False, "failureCodes": ("CIC01_CONTRACT_REQUIRED",)}
    candidate = (candidate_contract or {}).get("candidateIdentity", {})
    expected_digest = candidate.get("candidateIdentityDigest", claim_obj.candidate_identity_digest)
    expected_commit = candidate.get("repositoryCommit", "")
    if not candidate_validation["valid"]:
        reasons.extend(f"CANDIDATE_CONTRACT_INVALID:{code}" for code in candidate_validation["failureCodes"])
    if claim_obj.candidate_identity_digest != expected_digest:
        reasons.append("CLAIM_CANDIDATE_MISMATCH")

    nodes = {node.node_id: node for node in graph_obj.nodes}
    edges = {(edge.source_node_id, edge.target_node_id, edge.edge_type): edge for edge in graph_obj.edges}
    by_type: dict[ProofNodeType, list[ProofNode]] = {}
    for node in graph_obj.nodes:
        by_type.setdefault(node.node_type, []).append(node)

    required_types = tuple(ProofNodeType)
    if not claim_obj.runtime_trace_required:
        required_types = tuple(item for item in required_types if item != ProofNodeType.RUNTIME_TRACE)
    for node_type in required_types:
        if not by_type.get(node_type):
            reasons.append(f"MISSING_NODE:{node_type.value}")

    _require_edge(reasons, by_type, edges, ProofNodeType.CONSTITUTIONAL_REQUIREMENT, ProofNodeType.RULE_VERSION, ProofEdgeType.GOVERNED_BY)
    _require_edge(reasons, by_type, edges, ProofNodeType.RULE_VERSION, ProofNodeType.IMPLEMENTATION_SYMBOL, ProofEdgeType.IMPLEMENTED_BY)
    _require_edge(reasons, by_type, edges, ProofNodeType.IMPLEMENTATION_SYMBOL, ProofNodeType.RUNTIME_PATH, ProofEdgeType.EXPOSED_THROUGH)
    _require_edge(reasons, by_type, edges, ProofNodeType.RUNTIME_PATH, ProofNodeType.TEST_IDENTITY, ProofEdgeType.EXERCISED_BY)
    _require_edge(reasons, by_type, edges, ProofNodeType.TEST_IDENTITY, ProofNodeType.TEST_EXECUTION, ProofEdgeType.EXECUTED_AS)
    if claim_obj.runtime_trace_required:
        _require_edge(reasons, by_type, edges, ProofNodeType.TEST_EXECUTION, ProofNodeType.RUNTIME_TRACE, ProofEdgeType.TRACED_BY)
    _require_edge(reasons, by_type, edges, ProofNodeType.TEST_EXECUTION, ProofNodeType.EVIDENCE_GENERATOR, ProofEdgeType.GENERATED_BY)
    _require_edge(reasons, by_type, edges, ProofNodeType.EVIDENCE_GENERATOR, ProofNodeType.EVIDENCE_ARTIFACT, ProofEdgeType.PRODUCED)
    _require_edge(reasons, by_type, edges, ProofNodeType.EVIDENCE_ARTIFACT, ProofNodeType.CANDIDATE_IDENTITY, ProofEdgeType.BOUND_TO)
    _require_edge(reasons, by_type, edges, ProofNodeType.EVIDENCE_ARTIFACT, ProofNodeType.CERTIFICATION_VERDICT, ProofEdgeType.CONSUMED_BY)

    for node in graph_obj.nodes:
        if node.candidate_identity_digest and node.candidate_identity_digest != expected_digest:
            reasons.append(f"WRONG_CANDIDATE_NODE:{node.node_id}")
        if node.repository_commit and expected_commit and node.repository_commit != expected_commit:
            reasons.append(f"WRONG_COMMIT_NODE:{node.node_id}")
        if node.node_type in {ProofNodeType.RULE_VERSION, ProofNodeType.EVIDENCE_GENERATOR, ProofNodeType.EVIDENCE_ARTIFACT, ProofNodeType.CERTIFICATION_VERDICT}:
            version = node.canonical_identity.get("ruleVersion")
            if version and version != claim_obj.rule_version:
                reasons.append(f"STALE_RULE_VERSION:{node.node_id}:{version}")

    for edge in graph_obj.edges:
        if edge.verification_result != "VERIFIED":
            reasons.append(f"EDGE_NOT_VERIFIED:{edge.edge_id}")
        if edge.candidate_identity_digest and edge.candidate_identity_digest != expected_digest:
            reasons.append(f"WRONG_CANDIDATE_EDGE:{edge.edge_id}")
        if edge.rule_version and edge.rule_version != claim_obj.rule_version:
            reasons.append(f"STALE_EDGE_RULE_VERSION:{edge.edge_id}")

    _verify_implementation_symbol(reasons, by_type.get(ProofNodeType.IMPLEMENTATION_SYMBOL, ()))
    _verify_runtime_path(reasons, by_type.get(ProofNodeType.RUNTIME_PATH, ()))
    _verify_test_execution(reasons, by_type.get(ProofNodeType.TEST_IDENTITY, ()), by_type.get(ProofNodeType.TEST_EXECUTION, ()))
    if claim_obj.runtime_trace_required:
        _verify_runtime_trace(reasons, by_type.get(ProofNodeType.RUNTIME_TRACE, ()))
    _verify_generator(reasons, by_type.get(ProofNodeType.EVIDENCE_GENERATOR, ()), claim_obj.rule_version)
    _verify_artifact(reasons, by_type.get(ProofNodeType.EVIDENCE_ARTIFACT, ()), expected_digest)
    _verify_verdict(reasons, by_type.get(ProofNodeType.CERTIFICATION_VERDICT, ()), claim_obj.claim_id)

    state = _state_from_reasons(reasons)
    graph_dict = graph_obj.to_dict()
    body = {
        "schemaVersion": PROOF_EVALUATION_SCHEMA_VERSION,
        "orderId": "CIC-04",
        "claimId": claim_obj.claim_id,
        "constitutionalRequirementId": claim_obj.constitutional_requirement_id,
        "ruleId": claim_obj.rule_id,
        "ruleVersion": claim_obj.rule_version,
        "candidateIdentityDigest": expected_digest,
        "repositoryCommit": expected_commit,
        "proofGraphId": graph_obj.graph_id,
        "proofGraphDigest": graph_dict["proofGraphDigest"],
        "state": state.value,
        "gateSatisfied": claim_satisfies_gate(state),
        "reasonCodes": tuple(dict.fromkeys(reasons)),
        "diagnosticSummary": _diagnostic_summary(state, reasons),
        "evaluatorIdentity": claim_obj.evaluator_identity,
        "evaluatorVersion": claim_obj.evaluator_version,
        "immutable": True,
    }
    return {**body, "evaluationDigest": stable_hash(body)}


def issue_proof_based_verdict(evaluations: Iterable[dict[str, Any]], candidate_contract: dict[str, Any], *, verdict_id: str = "CIC04-VERDICT") -> dict[str, Any]:
    records = tuple(sorted(evaluations, key=lambda item: item.get("claimId", "")))
    candidate = candidate_contract.get("candidateIdentity", {})
    failures = []
    seen: dict[str, str] = {}
    for record in records:
        if record.get("candidateIdentityDigest") != candidate.get("candidateIdentityDigest"):
            failures.append(f"VERDICT_WRONG_CANDIDATE:{record.get('claimId', '')}")
        if not claim_satisfies_gate(record.get("state", "")):
            failures.append(f"CLAIM_NOT_PROVEN:{record.get('claimId', '')}:{record.get('state', '')}")
        prior = seen.setdefault(str(record.get("claimId", "")), str(record.get("evaluationDigest", "")))
        if prior != record.get("evaluationDigest"):
            failures.append(f"DUPLICATE_CONFLICTING_CLAIM:{record.get('claimId', '')}")
    body = {
        "schemaVersion": PROOF_VERDICT_SCHEMA_VERSION,
        "verdictIdentifier": verdict_id,
        "candidateIdentityDigest": candidate.get("candidateIdentityDigest", ""),
        "repositoryCommit": candidate.get("repositoryCommit", ""),
        "evaluatedClaimIdentifiers": tuple(record.get("claimId", "") for record in records),
        "claimStates": tuple((record.get("claimId", ""), record.get("state", "")) for record in records),
        "proofGraphDigests": tuple(record.get("proofGraphDigest", "") for record in records),
        "gateSatisfied": not failures and bool(records),
        "status": "PASS" if not failures and records else "FAIL",
        "failureCodes": tuple(dict.fromkeys(failures)),
        "verdictIssuer": "CIC-04 proof-based certification evaluator",
        "immutable": True,
    }
    return {**body, "verdictDigest": stable_hash(body)}


def execute_cic04_proof_certification(
    repo_root: str | Path = ".",
    *,
    candidate_contract: dict[str, Any] | None = None,
    proof_graphs: Iterable[tuple[ProofClaim | dict[str, Any], ProofGraph | dict[str, Any]]] = (),
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    contract = candidate_contract
    contract_rejection: dict[str, Any] | None = None
    if contract is None:
        try:
            contract = build_cic01_candidate_contract(root)
        except CIC01Rejection as exc:
            contract_rejection = exc.to_dict()
            contract = {"candidateIdentity": {"candidateIdentityDigest": "", "repositoryCommit": _git(root, "rev-parse", "HEAD")}, "candidateSnapshot": {}, "certificationInputLock": {}, "candidateContractDigest": ""}
    pairs = tuple(proof_graphs) or tuple(default_repository_claims(root, contract))
    evaluations = tuple(evaluate_proof_claim(claim, graph, contract) for claim, graph in pairs)
    verdict = issue_proof_based_verdict(evaluations, contract)
    body = {
        "schemaVersion": "CIC04-RESULT.1",
        "orderId": "CIC-04",
        "implementationVersion": CIC04_VERSION,
        "repositoryCommit": contract.get("candidateIdentity", {}).get("repositoryCommit", ""),
        "candidateIdentityDigest": contract.get("candidateIdentity", {}).get("candidateIdentityDigest", ""),
        "candidateContractDigest": contract.get("candidateContractDigest", ""),
        "candidateContractRejection": contract_rejection,
        "claimEvaluations": evaluations,
        "claimStateCounts": _state_counts(evaluations),
        "gateSatisfied": verdict["gateSatisfied"],
        "authoritativeVerdict": verdict,
        "verdict": verdict["status"],
    }
    return {**body, "resultDigest": stable_hash(body)}


def default_repository_claims(repo_root: Path, candidate_contract: dict[str, Any]) -> tuple[tuple[ProofClaim, ProofGraph], ...]:
    candidate = candidate_contract.get("candidateIdentity", {})
    digest = candidate.get("candidateIdentityDigest", "")
    commit = candidate.get("repositoryCommit", "")
    claim = ProofClaim(
        "CIC04-CLAIM-PRESENCE-IS-NOT-PROOF",
        "ARGOS-CONSTITUTIONAL-CERTIFICATION-CLAIMS",
        "CIC-04-PROOF-CHAIN",
        CIC04_VERSION,
        digest,
        "CIC04-GRAPH-DEFAULT",
        True,
        "CIC04-VERDICT",
    )
    graph = ProofGraph(
        "CIC04-GRAPH-DEFAULT",
        claim.claim_id,
        (
            _node("requirement", ProofNodeType.CONSTITUTIONAL_REQUIREMENT, digest, commit, {"requirementId": claim.constitutional_requirement_id}),
            _node("rule", ProofNodeType.RULE_VERSION, digest, commit, {"ruleId": claim.rule_id, "ruleVersion": claim.rule_version}),
            _node("symbol", ProofNodeType.IMPLEMENTATION_SYMBOL, digest, commit, {"module": "argos.control_panel.proof_based_certification", "qualname": "evaluate_proof_claim"}),
            _node("runtime", ProofNodeType.RUNTIME_PATH, digest, commit, {"approved": True, "reachesImplementationSymbol": True, "bypassDetected": False}),
            _node("test", ProofNodeType.TEST_IDENTITY, digest, commit, {"testId": "Tests.test_cic04_proof_based_certification.CIC04ProofBasedCertificationTests.test_complete_candidate_bound_proof_chain_is_proven", "testDefinitionDigest": "REQUIRES_ACTUAL_RUN"}),
        ),
        (
            _edge("e1", "requirement", "rule", ProofEdgeType.GOVERNED_BY, digest, claim.rule_version),
            _edge("e2", "rule", "symbol", ProofEdgeType.IMPLEMENTED_BY, digest, claim.rule_version),
            _edge("e3", "symbol", "runtime", ProofEdgeType.EXPOSED_THROUGH, digest, claim.rule_version),
            _edge("e4", "runtime", "test", ProofEdgeType.EXERCISED_BY, digest, claim.rule_version),
        ),
    )
    return ((claim, graph),)


def generate_cic04_evidence(repo_root: str | Path, output_dir: str | Path) -> dict[str, Any]:
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    result = execute_cic04_proof_certification(repo_root)
    _write_json(out / "cic04_result.json", result)
    _write_json(out / "claim_evaluations.json", result["claimEvaluations"])
    _write_json(out / "authoritative_verdict.json", result["authoritativeVerdict"])
    summary = (
        "# CIC-04 Proof-Based Certification Claims\n\n"
        f"Verdict: {result['verdict']}\n\n"
        f"Repository commit: {result['repositoryCommit']}\n\n"
        f"Claim states: {result['claimStateCounts']}\n\n"
        "Only `PROVEN` satisfies a certification gate. This summary is derived and non-authoritative.\n"
    )
    (out / "README_CIC04_SUMMARY.md").write_text(summary, encoding="utf-8")
    manifest_body = {
        "schemaVersion": "CIC04-EVIDENCE-MANIFEST.1",
        "repositoryCommit": result["repositoryCommit"],
        "verdict": result["verdict"],
        "artifacts": tuple(_file_record(path, out) for path in sorted(out.glob("*")) if path.is_file() and path.name != "manifest.json"),
    }
    manifest = {**manifest_body, "manifestDigest": stable_hash(manifest_body)}
    _write_json(out / "manifest.json", manifest)
    return manifest


def _require_edge(reasons: list[str], by_type: dict[ProofNodeType, list[ProofNode]], edges: dict[tuple[str, str, ProofEdgeType], ProofEdge], source_type: ProofNodeType, target_type: ProofNodeType, edge_type: ProofEdgeType) -> None:
    sources = by_type.get(source_type, ())
    targets = by_type.get(target_type, ())
    if not sources or not targets:
        return
    if not any((source.node_id, target.node_id, edge_type) in edges for source in sources for target in targets):
        reasons.append(f"MISSING_EDGE:{source_type.value}:{edge_type.value}:{target_type.value}")


def _verify_implementation_symbol(reasons: list[str], nodes: Iterable[ProofNode]) -> None:
    for node in nodes:
        module_name = node.canonical_identity.get("module", "")
        qualname = node.canonical_identity.get("qualname", "")
        try:
            obj: Any = importlib.import_module(module_name)
            for part in qualname.split("."):
                obj = getattr(obj, part)
            source = inspect.getsource(obj)
        except Exception:
            reasons.append(f"IMPLEMENTATION_SYMBOL_MISSING:{node.node_id}")
            continue
        expected = node.content_digest or node.canonical_identity.get("sourceDigest", "")
        if expected and expected != stable_hash(source):
            reasons.append(f"STALE_IMPLEMENTATION_SYMBOL:{node.node_id}")


def _verify_runtime_path(reasons: list[str], nodes: Iterable[ProofNode]) -> None:
    for node in nodes:
        if node.canonical_identity.get("bypassDetected"):
            reasons.append(f"BYPASS_DETECTED:{node.node_id}")
        if not node.canonical_identity.get("approved") or not node.canonical_identity.get("reachesImplementationSymbol"):
            reasons.append(f"UNREACHABLE_RUNTIME_PATH:{node.node_id}")


def _verify_test_execution(reasons: list[str], test_nodes: Iterable[ProofNode], execution_nodes: Iterable[ProofNode]) -> None:
    executions = tuple(execution_nodes)
    if not executions:
        reasons.append("TEST_EXECUTION_MISSING")
        return
    test_digest = next((node.canonical_identity.get("testDefinitionDigest", "") for node in test_nodes), "")
    for node in executions:
        identity = node.canonical_identity
        if not identity.get("collected") or not identity.get("executed"):
            reasons.append(f"TEST_NOT_EXECUTED:{node.node_id}")
        outcome = identity.get("terminalOutcome", "")
        if outcome != "PASSED":
            reasons.append(f"TEST_EXECUTION_NOT_PASS:{node.node_id}:{outcome}")
        if test_digest and identity.get("testDefinitionDigest") != test_digest:
            reasons.append(f"STALE_TEST_DEFINITION:{node.node_id}")


def _verify_runtime_trace(reasons: list[str], nodes: Iterable[ProofNode]) -> None:
    traces = tuple(nodes)
    if not traces:
        reasons.append("RUNTIME_TRACE_MISSING")
        return
    for node in traces:
        identity = node.canonical_identity
        if not identity.get("ordered") or not identity.get("requiredEventsPresent"):
            reasons.append(f"TRACE_REQUIRED_EVENTS_MISSING:{node.node_id}")
        if identity.get("invalidAuthorityOwnership"):
            reasons.append(f"TRACE_AUTHORITY_INVALID:{node.node_id}")


def _verify_generator(reasons: list[str], nodes: Iterable[ProofNode], rule_version: str) -> None:
    for node in nodes:
        identity = node.canonical_identity
        if not identity.get("authorized"):
            reasons.append(f"EVIDENCE_GENERATOR_UNAUTHORIZED:{node.node_id}")
        if rule_version not in tuple(identity.get("supportedRuleVersions", ())):
            reasons.append(f"STALE_GENERATOR_RULE_VERSION:{node.node_id}")


def _verify_artifact(reasons: list[str], nodes: Iterable[ProofNode], expected_digest: str) -> None:
    artifacts = tuple(nodes)
    if not artifacts:
        reasons.append("EVIDENCE_ARTIFACT_MISSING")
        return
    for node in artifacts:
        identity = node.canonical_identity
        if identity.get("candidateIdentityDigest") != expected_digest:
            reasons.append(f"EVIDENCE_ARTIFACT_WRONG_CANDIDATE:{node.node_id}")
        payload = identity.get("payload", {})
        if identity.get("artifactDigest") != stable_hash(payload):
            reasons.append(f"EVIDENCE_ARTIFACT_DIGEST_INVALID:{node.node_id}")
        if identity.get("selfDeclaredState") == ClaimState.PROVEN.value and not identity.get("producedFromEvaluation"):
            reasons.append(f"EVIDENCE_ARTIFACT_SELF_DECLARED_PROVEN:{node.node_id}")


def _verify_verdict(reasons: list[str], nodes: Iterable[ProofNode], claim_id: str) -> None:
    verdicts = tuple(nodes)
    if not verdicts:
        reasons.append("CERTIFICATION_VERDICT_MISSING")
        return
    for node in verdicts:
        identity = node.canonical_identity
        if identity.get("source") == "mutable_summary":
            reasons.append(f"MUTABLE_SUMMARY_REJECTED:{node.node_id}")
        if claim_id not in tuple(identity.get("consumedClaimIds", ())):
            reasons.append(f"VERDICT_DOES_NOT_CONSUME_CLAIM:{node.node_id}")
        if identity.get("claimState") != ClaimState.PROVEN.value:
            reasons.append(f"VERDICT_CONSUMES_NON_PROVEN_CLAIM:{node.node_id}")


def _state_from_reasons(reasons: Iterable[str]) -> ClaimState:
    reason_tuple = tuple(reasons)
    if not reason_tuple:
        return ClaimState.PROVEN
    mappings = (
        (ClaimState.BYPASS_DETECTED, ("BYPASS",)),
        (ClaimState.WRONG_CANDIDATE, ("WRONG_CANDIDATE", "WRONG_COMMIT")),
        (ClaimState.STALE, ("STALE",)),
        (ClaimState.UNREACHABLE, ("UNREACHABLE", "IMPLEMENTATION_SYMBOL_MISSING")),
        (ClaimState.UNTESTED, ("TEST_EXECUTION_MISSING", "TEST_NOT_EXECUTED")),
        (ClaimState.TRACE_MISSING, ("TRACE", "RUNTIME_TRACE_MISSING")),
        (ClaimState.EVIDENCE_MISSING, ("EVIDENCE_ARTIFACT_MISSING", "EVIDENCE_GENERATOR_UNAUTHORIZED", "EVIDENCE_ARTIFACT")),
        (ClaimState.FAILED, ("TEST_EXECUTION_NOT_PASS", "VERDICT_CONSUMES_NON_PROVEN")),
        (ClaimState.INCOMPLETE, ("MISSING_NODE", "MISSING_EDGE", "CERTIFICATION_VERDICT_MISSING")),
    )
    for state, needles in mappings:
        if any(any(needle in reason for needle in needles) for reason in reason_tuple):
            return state
    return ClaimState.UNKNOWN


def _diagnostic_summary(state: ClaimState, reasons: Iterable[str]) -> str:
    reason_tuple = tuple(reasons)
    if state == ClaimState.PROVEN:
        return "Complete candidate-bound proof chain verified."
    return f"{state.value}: {len(reason_tuple)} proof-chain issue(s) detected."


def _state_counts(evaluations: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in evaluations:
        state = str(item.get("state", ClaimState.UNKNOWN.value))
        counts[state] = counts.get(state, 0) + 1
    return counts


def _node(node_id: str, node_type: ProofNodeType, digest: str, commit: str, identity: dict[str, Any]) -> ProofNode:
    return ProofNode(node_id, node_type, identity, "CIC-04", candidate_identity_digest=digest, repository_commit=commit)


def _edge(edge_id: str, source: str, target: str, edge_type: ProofEdgeType, digest: str, rule_version: str) -> ProofEdge:
    return ProofEdge(edge_id, source, target, edge_type, "structured_reference", "VERIFIED", {}, candidate_identity_digest=digest, rule_version=rule_version)


def _claim(value: ProofClaim | dict[str, Any]) -> ProofClaim:
    if isinstance(value, ProofClaim):
        return value
    return ProofClaim(
        str(value["claim_id"]),
        str(value["constitutional_requirement_id"]),
        str(value["rule_id"]),
        str(value["rule_version"]),
        str(value["candidate_identity_digest"]),
        str(value["proof_graph_id"]),
        bool(value["runtime_trace_required"]),
        str(value["expected_verdict_consumer"]),
    )


def _graph(value: ProofGraph | dict[str, Any]) -> ProofGraph:
    if isinstance(value, ProofGraph):
        return value
    return ProofGraph(
        str(value["graph_id"]),
        str(value["claim_id"]),
        tuple(ProofNode(node_type=ProofNodeType(item["node_type"]), **{k: v for k, v in item.items() if k != "node_type"}) for item in value["nodes"]),
        tuple(ProofEdge(edge_type=ProofEdgeType(item["edge_type"]), **{k: v for k, v in item.items() if k != "edge_type"}) for item in value["edges"]),
    )


def _jsonable(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def _file_record(path: Path, root: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": _file_hash(path)}


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(root: Path, *args: str) -> str:
    result = __import__("subprocess").run(("git", *args), cwd=root, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def cic04_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CIC-04 proof-based certification evidence")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    manifest = generate_cic04_evidence(args.repo_root, args.output)
    print(json.dumps(_jsonable(manifest), indent=2, sort_keys=True))
    return 0 if manifest.get("verdict") == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cic04_main())
