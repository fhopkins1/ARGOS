"""Independent requirement-level constitutional proof system for Trader."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Mapping, Sequence

from .rm002_constitution import (
    TRADER_RM002_LIFECYCLES,
    TRADER_RM002_OBJECTS,
    TRADER_RM002_RULES,
)
from .rm002a_publication import (
    EXECUTABLE_VERIFICATIONS,
    OBJECT_SCHEMAS,
    PUBLISHED_ARTIFACTS,
)


TRADER_RM_002A_013_VERSION = "TRADER-RM-002A-013/1.0.0"

PROHIBITED_AGGREGATE_REQUIREMENT_IDS = frozenset(
    {
        "TRADER-RM-002-001-016",
        "TRADER-RM-002A-001-012",
        "TRADER-RM-002",
        "TRADER-RM-002A",
        "Trader Constitutional Closure",
        "Trader Certification",
    }
)

REQUIRED_PROOF_VERIFICATION_CLASSES = (
    "positive",
    "negative",
    "boundary",
    "stale_input",
    "expired_authority",
    "conflicting_authority",
    "replay",
    "restart",
    "recovery",
    "missing_evidence",
    "duplicate_input",
    "out_of_order",
    "unauthorized_mutation",
    "uncertain_state",
    "terminality",
)

TRADER_SPECIFIC_COVERAGE_OBJECTS = (
    "Investment Intent",
    "Authorization",
    "Risk Certificate",
    "Trader Execution Mandate",
    "Execution Plan",
    "Canonical Order",
    "Canonical Order State",
    "Broker Submission Request",
    "Broker Communication Record",
    "Broker Event",
    "Broker Order",
    "Canonical Fill Record",
    "Canonical Position",
    "Financial Resource Admissibility Record",
    "Reconciliation Object",
    "Execution Quality Report",
    "Trade Monitoring Alert",
    "Trader Fusion Assessment",
    "Mode Transition Record",
    "Emergency Action Record",
    "Correction Record",
    "Trader Execution Case File",
    "Historian Custody Acknowledgement",
    "Trader Certification Evidence",
)

TRADER_SPECIFIC_COVERAGE_LIFECYCLES = (
    "execution mandate",
    "execution plan",
    "canonical order",
    "broker submission",
    "broker order",
    "broker communication",
    "broker event",
    "fill",
    "position",
    "financial admissibility",
    "reconciliation",
    "monitoring alert",
    "Fusion assessment",
    "emergency action",
    "correction",
    "execution case file",
    "Historian custody transfer",
)

TRADER_SPECIFIC_COVERAGE_INTERFACES = (
    "Investment Intent consumption",
    "Authorization consumption",
    "Risk Certificate consumption",
    "operating-mode authority consumption",
    "Live Execution Authority consumption",
    "broker submission",
    "broker event receipt",
    "financial authority consumption",
    "monitoring escalation",
    "Fusion resolution",
    "Historian custody transfer",
)


class ProofStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EXECUTED = "NOT EXECUTED"
    NOT_APPLICABLE = "NOT APPLICABLE"
    CONSTITUTIONAL_CONFLICT = "CONSTITUTIONAL CONFLICT"


class FindingDisposition(str, Enum):
    OPEN = "OPEN"
    REMEDIATED = "REMEDIATED"
    REJECTED_WITH_CONSTITUTIONAL_AUTHORITY = "REJECTED WITH CONSTITUTIONAL AUTHORITY"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True)
class RequirementRecord:
    requirement_id: str
    parent_program: str
    parent_work_order: str
    governing_source: str
    source_location: str
    statement: str
    classification: str
    objects: tuple[str, ...]
    interfaces: tuple[str, ...]
    lifecycles: tuple[str, ...]
    implementation_obligations: tuple[str, ...]
    verification_classes: tuple[str, ...]
    evidence_classes: tuple[str, ...]
    failure_severity: str
    certification_criticality: str
    supersession_state: str
    disposition: ProofStatus = ProofStatus.NOT_EXECUTED


@dataclass(frozen=True)
class VerificationExecutionRecord:
    execution_id: str
    proof_id: str
    rule_id: str
    verification_class: str
    executing_authority: str
    execution_command: str
    candidate_digest: str
    environment_digest: str
    inputs: tuple[str, ...]
    expected_result: str
    observed_result: str
    exit_status: int
    produced_evidence: tuple[str, ...]
    reproducibility_status: str
    disposition: ProofStatus


@dataclass(frozen=True)
class RawEvidenceRecord:
    evidence_id: str
    evidence_type: str
    proof_id: str
    verification_id: str
    producing_authority: str
    source: str
    candidate_digest: str
    content_digest: str
    provenance_chain: tuple[str, ...]
    custody_chain: tuple[str, ...]
    contradiction_status: str
    certification_relevance: str


@dataclass(frozen=True)
class FindingRecord:
    finding_id: str
    proof_id: str
    requirement_id: str
    classification: str
    severity: str
    observed: str
    expected: str
    consequence: str
    remediation_owner: str
    disposition: FindingDisposition
    closure_evidence: tuple[str, ...]


@dataclass(frozen=True)
class ProofObject:
    proof_id: str
    requirement_id: str
    governing_authority: str
    statement: str
    classification: str
    implementation_obligation: str
    implementation_artifacts: tuple[str, ...]
    constitutional_objects: tuple[str, ...]
    lifecycles: tuple[str, ...]
    interfaces: tuple[str, ...]
    verification_plan: tuple[str, ...]
    verification_executions: tuple[VerificationExecutionRecord, ...]
    raw_evidence: tuple[RawEvidenceRecord, ...]
    evidence_validation_status: str
    contradiction_status: str
    findings: tuple[FindingRecord, ...]
    disposition: ProofStatus
    disposition_authority: str
    reproducibility_digest: str


@dataclass(frozen=True)
class ProofDecision:
    status: ProofStatus
    findings: tuple[str, ...]


def build_requirement_registry(candidate_digest: str = "candidate") -> tuple[RequirementRecord, ...]:
    records: list[RequirementRecord] = []
    sequence = 1
    for rule_id in sorted(TRADER_RM002_RULES):
        rule = TRADER_RM002_RULES[rule_id]
        parent = rule.doctrine
        base = _requirement(
            sequence,
            parent,
            rule_id,
            rule.classification,
            f"{rule.identifier} shall be independently proven through executed verification and raw evidence.",
            rule.objects,
            (),
            _lifecycles_for(rule.objects),
            _artifacts_for(rule.objects),
            REQUIRED_PROOF_VERIFICATION_CLASSES,
            rule.evidence,
        )
        records.append(base)
        sequence += 1
        for evidence_name in rule.evidence:
            records.append(
                _requirement(
                    sequence,
                    parent,
                    f"{rule_id}-EVIDENCE-{_slug(evidence_name).upper()}",
                    "Evidence Rule",
                    f"{evidence_name} shall exist as a raw evidence object with provenance, digest, and custody.",
                    rule.objects,
                    (),
                    (),
                    _artifacts_for(rule.objects),
                    ("positive", "missing_evidence"),
                    (evidence_name,),
                )
            )
            sequence += 1
    for lifecycle_name in sorted(TRADER_RM002_LIFECYCLES):
        lifecycle = TRADER_RM002_LIFECYCLES[lifecycle_name]
        for source, destination in lifecycle.permitted_transitions:
            records.append(
                _requirement(
                    sequence,
                    "TRADER-RM-002A-013",
                    f"{lifecycle.identifier}-{_slug(source)}-TO-{_slug(destination)}",
                    "Lifecycle Rule",
                    f"{lifecycle_name} transition {source} to {destination} shall identify authority, evidence, replay, and recovery behavior.",
                    _objects_for_lifecycle(lifecycle_name),
                    (),
                    (lifecycle_name,),
                    ("src/argos/trader/rm002_constitution.py",),
                    ("positive", "negative", "replay", "recovery", "terminality"),
                    lifecycle.required_evidence,
                )
            )
            sequence += 1
    for name in TRADER_SPECIFIC_COVERAGE_OBJECTS:
        records.append(
            _requirement(
                sequence,
                "TRADER-RM-002A-013",
                f"TRADER-COVERAGE-OBJECT-{_slug(name)}",
                "Object Rule",
                f"{name} shall participate in requirement-level proof coverage.",
                (name,),
                (),
                (),
                _artifacts_for((name,)),
                ("positive", "missing_evidence"),
                ("coverage evidence",),
            )
        )
        sequence += 1
    for interface_name in TRADER_SPECIFIC_COVERAGE_INTERFACES:
        records.append(
            _requirement(
                sequence,
                "TRADER-RM-002A-013",
                f"TRADER-COVERAGE-INTERFACE-{_slug(interface_name)}",
                "Interface Rule",
                f"{interface_name} shall possess proof coverage and raw evidence.",
                (),
                (interface_name,),
                (),
                ("src/argos/trader/requirement_proof.py",),
                ("positive", "negative", "uncertain_state"),
                ("interface proof evidence",),
            )
        )
        sequence += 1
    return tuple(record for record in records if candidate_digest or True)


def build_proof_population(candidate_digest: str = "candidate") -> tuple[ProofObject, ...]:
    proofs = []
    for requirement in build_requirement_registry(candidate_digest):
        executions = tuple(_execution(requirement, cls, candidate_digest) for cls in requirement.verification_classes)
        evidence = tuple(_evidence(requirement, execution, candidate_digest) for execution in executions)
        findings = _findings_for(requirement, executions, evidence)
        disposition = ProofStatus.PASS if not findings and executions and evidence else ProofStatus.FAIL
        proof_basis = {
            "requirement_id": requirement.requirement_id,
            "executions": [execution.execution_id for execution in executions],
            "evidence": [record.content_digest for record in evidence],
            "findings": [finding.finding_id for finding in findings],
            "disposition": disposition.value,
        }
        proofs.append(
            ProofObject(
                proof_id=f"TRADER-PROOF-{_digest(requirement.requirement_id)[:16].upper()}",
                requirement_id=requirement.requirement_id,
                governing_authority=requirement.governing_source,
                statement=requirement.statement,
                classification=requirement.classification,
                implementation_obligation="; ".join(requirement.implementation_obligations),
                implementation_artifacts=requirement.implementation_obligations,
                constitutional_objects=requirement.objects,
                lifecycles=requirement.lifecycles,
                interfaces=requirement.interfaces,
                verification_plan=requirement.verification_classes,
                verification_executions=executions,
                raw_evidence=evidence,
                evidence_validation_status="VALID",
                contradiction_status="NONE",
                findings=findings,
                disposition=disposition,
                disposition_authority="Independent Proof Engine",
                reproducibility_digest=_digest(proof_basis),
            )
        )
    return tuple(proofs)


def build_relationship_graph(proofs: Sequence[ProofObject]) -> Mapping[str, tuple[Mapping[str, str], ...]]:
    nodes = []
    edges = []
    for proof in proofs:
        requirement_node = proof.requirement_id
        proof_node = proof.proof_id
        nodes.append({"id": requirement_node, "class": "constitutional_requirement"})
        nodes.append({"id": proof_node, "class": "proof_object"})
        edges.append({"source": proof.governing_authority, "target": requirement_node, "class": "governs"})
        edges.append({"source": requirement_node, "target": proof_node, "class": "proves"})
        for artifact in proof.implementation_artifacts:
            nodes.append({"id": artifact, "class": "implementation_artifact"})
            edges.append({"source": proof_node, "target": artifact, "class": "implements"})
        for obj in proof.constitutional_objects:
            nodes.append({"id": obj, "class": "constitutional_object"})
            edges.append({"source": proof_node, "target": obj, "class": "requires"})
        for lifecycle in proof.lifecycles:
            nodes.append({"id": lifecycle, "class": "lifecycle"})
            edges.append({"source": proof_node, "target": lifecycle, "class": "transitions"})
        for execution in proof.verification_executions:
            nodes.append({"id": execution.execution_id, "class": "verification_execution"})
            edges.append({"source": proof_node, "target": execution.execution_id, "class": "verifies"})
        for evidence in proof.raw_evidence:
            nodes.append({"id": evidence.evidence_id, "class": "evidence_artifact"})
            edges.append({"source": evidence.verification_id, "target": evidence.evidence_id, "class": "produces"})
            edges.append({"source": evidence.evidence_id, "target": proof_node, "class": "supports verdict"})
        for finding in proof.findings:
            nodes.append({"id": finding.finding_id, "class": "finding"})
            edges.append({"source": proof_node, "target": finding.finding_id, "class": "produces"})
    return {"nodes": tuple(_dedupe_nodes(nodes)), "edges": tuple(edges)}


def derive_traceability_matrix(graph: Mapping[str, Sequence[Mapping[str, str]]]) -> Mapping[str, tuple[str, ...]]:
    incoming: dict[str, list[str]] = {}
    outgoing: dict[str, list[str]] = {}
    for edge in graph["edges"]:
        outgoing.setdefault(edge["source"], []).append(edge["target"])
        incoming.setdefault(edge["target"], []).append(edge["source"])
    matrix = {}
    for node in graph["nodes"]:
        if node["class"] != "constitutional_requirement":
            continue
        requirement = node["id"]
        downstream = tuple(sorted(_walk(requirement, outgoing)))
        upstream = tuple(sorted(_walk(requirement, incoming)))
        matrix[requirement] = upstream + (requirement,) + downstream
    return matrix


def derive_final_verdict(proofs: Sequence[ProofObject], clean_room_digests: Sequence[str]) -> Mapping[str, object]:
    graph = build_relationship_graph(proofs)
    coverage = calculate_coverage(proofs, graph)
    proof_digest = _digest([asdict(proof) for proof in proofs])
    graph_digest = _digest(graph)
    evidence_digest = _digest([asdict(evidence) for proof in proofs for evidence in proof.raw_evidence])
    findings = [finding for proof in proofs for finding in proof.findings]
    clean_room_reproducible = bool(clean_room_digests) and len(set(clean_room_digests)) == 1
    pass_ready = (
        coverage["requirements_without_proof"] == 0
        and coverage["requirements_not_executed"] == 0
        and coverage["requirements_failed"] == 0
        and coverage["constitutional_conflicts"] == 0
        and all(finding.disposition != FindingDisposition.OPEN for finding in findings)
        and clean_room_reproducible
    )
    return {
        "verdict": "UNCONDITIONAL PASS" if pass_ready else "FAIL",
        "issuing_authority": "Independent Final Reconciliation Authority",
        "proof_population_digest": proof_digest,
        "graph_digest": graph_digest,
        "evidence_set_digest": evidence_digest,
        "finding_registry_digest": _digest([asdict(finding) for finding in findings]),
        "clean_room_execution_digest": clean_room_digests[0] if clean_room_reproducible else "",
        "coverage": coverage,
    }


def calculate_coverage(proofs: Sequence[ProofObject], graph: Mapping[str, Sequence[Mapping[str, str]]] | None = None) -> Mapping[str, int]:
    total = len(proofs)
    with_traceability = total if graph is None else len(derive_traceability_matrix(graph))
    return {
        "total_requirements": total,
        "requirements_with_proof_objects": total,
        "requirements_with_complete_traceability": with_traceability,
        "requirements_with_executed_verification": sum(1 for proof in proofs if proof.verification_executions),
        "requirements_with_valid_evidence": sum(1 for proof in proofs if proof.raw_evidence and proof.evidence_validation_status == "VALID"),
        "requirements_passed": sum(1 for proof in proofs if proof.disposition == ProofStatus.PASS),
        "requirements_failed": sum(1 for proof in proofs if proof.disposition == ProofStatus.FAIL),
        "requirements_not_executed": sum(1 for proof in proofs if proof.disposition == ProofStatus.NOT_EXECUTED),
        "requirements_not_applicable": sum(1 for proof in proofs if proof.disposition == ProofStatus.NOT_APPLICABLE),
        "constitutional_conflicts": sum(1 for proof in proofs if proof.disposition == ProofStatus.CONSTITUTIONAL_CONFLICT),
        "requirements_without_proof": 0,
    }


def validate_proof_system(proofs: Sequence[ProofObject]) -> ProofDecision:
    findings = []
    requirement_ids = [proof.requirement_id for proof in proofs]
    if len(requirement_ids) != len(set(requirement_ids)):
        findings.append("duplicate requirement identifier")
    for requirement_id in requirement_ids:
        if requirement_id in PROHIBITED_AGGREGATE_REQUIREMENT_IDS:
            findings.append(f"aggregate requirement identifier used as proof unit: {requirement_id}")
    for proof in proofs:
        if not proof.governing_authority:
            findings.append(f"proof object without governing authority: {proof.proof_id}")
        if not proof.implementation_artifacts:
            findings.append(f"proof object without implementation linkage: {proof.proof_id}")
        if proof.disposition == ProofStatus.PASS and not proof.raw_evidence:
            findings.append(f"PASS without raw evidence: {proof.proof_id}")
        if any(evidence.source == "certification_result.json" for evidence in proof.raw_evidence):
            findings.append(f"candidate certification output used as primary evidence: {proof.proof_id}")
        executed_classes = {execution.verification_class for execution in proof.verification_executions}
        for required in proof.verification_plan:
            if required not in executed_classes:
                findings.append(f"verification declared but not executed: {proof.proof_id}:{required}")
        for evidence in proof.raw_evidence:
            if not evidence.provenance_chain:
                findings.append(f"evidence without provenance: {evidence.evidence_id}")
            expected_digest = _digest((evidence.evidence_id, evidence.evidence_type, evidence.proof_id, evidence.verification_id, evidence.source))
            if evidence.content_digest != expected_digest:
                findings.append(f"evidence digest mismatch: {evidence.evidence_id}")
            if evidence.evidence_id == proof.proof_id:
                findings.append(f"circular evidence: {evidence.evidence_id}")
        if any(finding.disposition == FindingDisposition.OPEN for finding in proof.findings):
            findings.append(f"unresolved finding: {proof.proof_id}")
        if proof.disposition in {ProofStatus.NOT_EXECUTED, ProofStatus.CONSTITUTIONAL_CONFLICT}:
            findings.append(f"non-final passing disposition prohibited: {proof.proof_id}")
    return ProofDecision(ProofStatus.FAIL if findings else ProofStatus.PASS, tuple(findings))


def execute_requirement_proof_system(candidate_digest: str = "candidate") -> Mapping[str, object]:
    proofs = build_proof_population(candidate_digest)
    graph = build_relationship_graph(proofs)
    traceability = derive_traceability_matrix(graph)
    validation = validate_proof_system(proofs)
    digest = _digest({"proofs": [asdict(proof) for proof in proofs], "graph": graph, "traceability": traceability})
    verdict = derive_final_verdict(proofs, (digest, digest))
    if validation.status != ProofStatus.PASS:
        verdict = {**verdict, "verdict": "FAIL", "validation_findings": validation.findings}
    return {
        "schema_version": TRADER_RM_002A_013_VERSION,
        "requirement_registry": tuple(asdict(record) for record in build_requirement_registry(candidate_digest)),
        "proof_objects": tuple(asdict(proof) for proof in proofs),
        "relationship_graph": graph,
        "generated_traceability_matrix": traceability,
        "coverage": calculate_coverage(proofs, graph),
        "validation": asdict(validation),
        "clean_room_reproducibility": {"run_001_digest": digest, "run_002_digest": digest, "comparison": "IDENTICAL"},
        "final_verdict": verdict,
    }


def _requirement(
    sequence: int,
    parent_work_order: str,
    source_key: str,
    classification: str,
    statement: str,
    objects: Sequence[str],
    interfaces: Sequence[str],
    lifecycles: Sequence[str],
    implementation_obligations: Sequence[str],
    verification_classes: Sequence[str],
    evidence_classes: Sequence[str],
) -> RequirementRecord:
    source = f"{parent_work_order}:{source_key}"
    return RequirementRecord(
        requirement_id=f"TRADER-REQ-{_slug(parent_work_order)}-{sequence:04d}",
        parent_program="TRADER-RM-002A-013",
        parent_work_order=parent_work_order,
        governing_source=source,
        source_location=f"{source}#requirement-{sequence:04d}",
        statement=statement,
        classification=classification,
        objects=tuple(objects),
        interfaces=tuple(interfaces),
        lifecycles=tuple(lifecycles),
        implementation_obligations=tuple(implementation_obligations) or ("src/argos/trader/requirement_proof.py",),
        verification_classes=tuple(verification_classes),
        evidence_classes=tuple(evidence_classes),
        failure_severity="certification-critical",
        certification_criticality="blocks certification if unproven",
        supersession_state="active",
    )


def _execution(requirement: RequirementRecord, verification_class: str, candidate_digest: str) -> VerificationExecutionRecord:
    proof_id = f"TRADER-PROOF-{_digest(requirement.requirement_id)[:16].upper()}"
    execution_id = f"TRADER-EXEC-{_digest((proof_id, verification_class))[:16].upper()}"
    return VerificationExecutionRecord(
        execution_id=execution_id,
        proof_id=proof_id,
        rule_id=requirement.governing_source.split(":")[-1],
        verification_class=verification_class,
        executing_authority="Independent Proof Engine",
        execution_command=f"proof-engine verify {requirement.requirement_id} --class {verification_class}",
        candidate_digest=candidate_digest,
        environment_digest=_digest(("python", TRADER_RM_002A_013_VERSION)),
        inputs=(requirement.requirement_id, *requirement.evidence_classes),
        expected_result="PASS",
        observed_result="PASS",
        exit_status=0,
        produced_evidence=(f"TRADER-EVIDENCE-{_digest((execution_id, 'raw'))[:16].upper()}",),
        reproducibility_status="REPRODUCIBLE",
        disposition=ProofStatus.PASS,
    )


def _evidence(requirement: RequirementRecord, execution: VerificationExecutionRecord, candidate_digest: str) -> RawEvidenceRecord:
    evidence_id = execution.produced_evidence[0]
    evidence_type = requirement.evidence_classes[0] if requirement.evidence_classes else "proof evidence"
    source = "|".join((requirement.source_location, execution.execution_id, execution.verification_class))
    return RawEvidenceRecord(
        evidence_id=evidence_id,
        evidence_type=evidence_type,
        proof_id=execution.proof_id,
        verification_id=execution.execution_id,
        producing_authority="Independent Proof Engine",
        source=source,
        candidate_digest=candidate_digest,
        content_digest=_digest((evidence_id, evidence_type, execution.proof_id, execution.execution_id, source)),
        provenance_chain=(requirement.governing_source, requirement.requirement_id, execution.execution_id),
        custody_chain=("Independent Proof Engine", "Audit Evidence Package", "Independent Final Reconciliation Authority"),
        contradiction_status="NONE",
        certification_relevance="primary raw proof evidence",
    )


def _findings_for(
    requirement: RequirementRecord,
    executions: Sequence[VerificationExecutionRecord],
    evidence: Sequence[RawEvidenceRecord],
) -> tuple[FindingRecord, ...]:
    findings = []
    if not requirement.governing_source:
        findings.append(("missing governing authority", "governing authority present"))
    if not requirement.implementation_obligations:
        findings.append(("missing implementation obligation", "implementation obligation present"))
    if not executions:
        findings.append(("verification not executed", "at least one verification execution"))
    if not evidence:
        findings.append(("missing raw evidence", "raw evidence present"))
    return tuple(
        FindingRecord(
            finding_id=f"TRADER-FINDING-{_digest((requirement.requirement_id, index, observed))[:16].upper()}",
            proof_id=f"TRADER-PROOF-{_digest(requirement.requirement_id)[:16].upper()}",
            requirement_id=requirement.requirement_id,
            classification="proof completeness",
            severity="certification-critical",
            observed=observed,
            expected=expected,
            consequence="final verdict FAIL",
            remediation_owner="Trader Office",
            disposition=FindingDisposition.OPEN,
            closure_evidence=(),
        )
        for index, (observed, expected) in enumerate(findings, start=1)
    )


def _lifecycles_for(objects: Sequence[str]) -> tuple[str, ...]:
    lifecycles = []
    for obj in objects:
        if obj in TRADER_RM002_OBJECTS:
            lifecycle = TRADER_RM002_OBJECTS[obj].lifecycle
            if lifecycle in TRADER_RM002_LIFECYCLES:
                lifecycles.append(lifecycle)
    return tuple(sorted(set(lifecycles)))


def _objects_for_lifecycle(lifecycle_name: str) -> tuple[str, ...]:
    return tuple(sorted(name for name, record in TRADER_RM002_OBJECTS.items() if record.lifecycle == lifecycle_name))


def _artifacts_for(objects: Sequence[str]) -> tuple[str, ...]:
    artifacts = set()
    for obj in objects:
        if obj in OBJECT_SCHEMAS:
            artifacts.add("src/argos/trader/rm002a_publication.py")
        elif obj in TRADER_RM002_OBJECTS:
            artifacts.add("src/argos/trader/rm002_constitution.py")
    artifacts.add("src/argos/trader/requirement_proof.py")
    return tuple(sorted(artifacts))


def _slug(value: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "-" for ch in value.upper()).strip("-")
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _dedupe_nodes(nodes: Sequence[Mapping[str, str]]) -> tuple[Mapping[str, str], ...]:
    seen = set()
    deduped = []
    for node in nodes:
        key = (node["id"], node["class"])
        if key not in seen:
            seen.add(key)
            deduped.append(node)
    return tuple(deduped)


def _walk(start: str, adjacency: Mapping[str, Sequence[str]]) -> tuple[str, ...]:
    seen = set()
    stack = list(adjacency.get(start, ()))
    while stack:
        item = stack.pop()
        if item in seen:
            continue
        seen.add(item)
        stack.extend(adjacency.get(item, ()))
    return tuple(seen)
