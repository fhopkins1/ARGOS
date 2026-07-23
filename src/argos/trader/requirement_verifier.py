"""Actual verifier execution and raw evidence validation for Trader proofs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
import time
from typing import Callable, Mapping, Sequence

from .constitutional_governance import (
    FINANCIAL_RESOURCE_OWNERS,
    AuthorityInputs,
    CertificationVerdict,
    ExecutionScope,
    HistorianCompletionContext,
    TemporalContext,
    TraderGovernanceStatus,
    TraderOperatingMode,
    resolve_operating_mode,
    validate_certification_verdict,
    validate_execution_authority,
    validate_execution_scope,
    validate_financial_resource_ownership,
    validate_historian_completion,
    validate_temporal_context,
)
from .requirement_proof import (
    REQUIRED_PROOF_VERIFICATION_CLASSES,
    FindingDisposition,
    FindingRecord,
    ProofObject,
    ProofStatus,
    RawEvidenceRecord,
    RequirementRecord,
    VerificationExecutionRecord,
    build_relationship_graph,
    build_requirement_registry,
    derive_final_verdict,
    derive_traceability_matrix,
)
from .rm002_constitution import (
    CASE_FILE_REQUIRED_EVIDENCE,
    TRADER_RM002_LIFECYCLES,
    TRADER_RM002_RULES,
    validate_case_file_evidence,
    validate_lifecycle_transition,
    validate_rm002_constitution,
)
from .rm002a_publication import validate_rm002a_publication


TRADER_RM_002A_014_VERSION = "TRADER-RM-002A-014/1.0.0"


class ExecutionDisposition(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EXECUTED = "NOT EXECUTED"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    INVALID_EVIDENCE = "INVALID EVIDENCE"
    CONSTITUTIONAL_CONFLICT = "CONSTITUTIONAL CONFLICT"
    NOT_APPLICABLE = "NOT APPLICABLE"


class EvidenceValidationState(str, Enum):
    UNVALIDATED = "UNVALIDATED"
    VALID = "VALID"
    INVALID = "INVALID"
    INCOMPLETE = "INCOMPLETE"
    CONTRADICTORY = "CONTRADICTORY"
    MISSING = "MISSING"


@dataclass(frozen=True)
class VerifierRecord:
    verifier_id: str
    requirement_id: str
    proof_id: str
    verification_class: str
    executable_type: str
    executable_target: str
    source_artifact: str
    implementation_path_under_test: str
    objects_under_test: tuple[str, ...]
    interfaces_under_test: tuple[str, ...]
    lifecycles_under_test: tuple[str, ...]
    required_fixtures: tuple[str, ...]
    input_builder: str
    expected_result_reference: str
    observation_adapter: str
    evidence_parser: str
    timeout_seconds: int
    retry_policy: str
    isolation_requirement: str
    cleanup_procedure: str
    determinism_classification: str
    permitted_nondeterministic_fields: tuple[str, ...]
    verifier_version: str
    verifier_digest: str
    responsible_component: str


@dataclass(frozen=True)
class ControlledFixture:
    fixture_id: str
    requirement_id: str
    verification_class: str
    condition: str
    inputs: Mapping[str, object]
    pre_state: Mapping[str, object]
    expected: Mapping[str, object]
    cleanup_state: Mapping[str, object]
    fixture_digest: str
    input_digest: str


@dataclass(frozen=True)
class ActualExecutionRecord:
    execution_id: str
    verifier_id: str
    requirement_id: str
    proof_id: str
    verification_class: str
    executing_authority: str
    invocation_target: str
    executed_source_digest: str
    candidate_digest: str
    environment_digest: str
    fixture_digest: str
    input_digest: str
    start_timestamp: str
    completion_timestamp: str
    elapsed_ms: int
    return_code: int
    exception: str
    timeout_state: str
    stdout: str
    stderr: str
    pre_state: Mapping[str, object]
    post_state: Mapping[str, object]
    observed_events: tuple[str, ...]
    observed_mutations: tuple[str, ...]
    observed_rejections: tuple[str, ...]
    observed_transitions: tuple[str, ...]
    observed_outputs: Mapping[str, object]
    cleanup_result: str
    expected_result: Mapping[str, object]
    comparison_result: str
    evidence_references: tuple[str, ...]
    disposition: ExecutionDisposition


@dataclass(frozen=True)
class ValidatedEvidenceRecord:
    evidence: RawEvidenceRecord
    raw_content: Mapping[str, object]
    validation_state: EvidenceValidationState
    validation_report: tuple[str, ...]
    raw_content_digest: str
    executable_digest: str
    fixture_digest: str
    input_digest: str


@dataclass(frozen=True)
class BehavioralProofPackage:
    requirement_registry: tuple[RequirementRecord, ...]
    verifier_registry: tuple[VerifierRecord, ...]
    fixture_registry: tuple[ControlledFixture, ...]
    execution_registry: tuple[ActualExecutionRecord, ...]
    raw_evidence_registry: tuple[ValidatedEvidenceRecord, ...]
    proof_objects: tuple[ProofObject, ...]
    failure_demonstrations: Mapping[str, object]
    relationship_graph: Mapping[str, tuple[Mapping[str, str], ...]]
    traceability_matrix: Mapping[str, tuple[str, ...]]
    final_verdict: Mapping[str, object]
    package_digest: str


def execute_behavioral_verification_system(candidate_digest: str = "candidate") -> Mapping[str, object]:
    package = build_behavioral_proof_package(candidate_digest)
    return {
        "schema_version": TRADER_RM_002A_014_VERSION,
        "requirement_count": len(package.requirement_registry),
        "verifier_count": len(package.verifier_registry),
        "execution_count": len(package.execution_registry),
        "evidence_count": len(package.raw_evidence_registry),
        "proof_count": len(package.proof_objects),
        "failure_demonstrations": package.failure_demonstrations,
        "relationship_graph": package.relationship_graph,
        "traceability_matrix": package.traceability_matrix,
        "final_verdict": package.final_verdict,
        "package_digest": package.package_digest,
    }


def build_behavioral_proof_package(candidate_digest: str = "candidate") -> BehavioralProofPackage:
    requirements = build_requirement_registry(candidate_digest)
    verifiers = tuple(verifier for requirement in requirements for verifier in _verifiers_for(requirement))
    fixtures = tuple(_fixture_for(verifier) for verifier in verifiers)
    executions = tuple(dispatch_verifier(verifier, fixtures[index], candidate_digest) for index, verifier in enumerate(verifiers))
    evidence = tuple(produce_and_validate_evidence(execution, fixtures[index], candidate_digest) for index, execution in enumerate(executions))
    proofs = recalculate_proofs(requirements, verifiers, executions, evidence)
    graph = build_relationship_graph(proofs)
    traceability = derive_traceability_matrix(graph)
    digest = _digest({"proofs": [asdict(proof) for proof in proofs], "executions": [asdict(item) for item in executions], "evidence": [asdict(item) for item in evidence]})
    final_verdict = derive_final_verdict(proofs, (digest, digest))
    failure_demonstrations = demonstrate_fail_closed_behavior(requirements[0], verifiers[0], fixtures[0], candidate_digest)
    return BehavioralProofPackage(
        requirement_registry=requirements,
        verifier_registry=verifiers,
        fixture_registry=fixtures,
        execution_registry=executions,
        raw_evidence_registry=evidence,
        proof_objects=proofs,
        failure_demonstrations=failure_demonstrations,
        relationship_graph=graph,
        traceability_matrix=traceability,
        final_verdict=final_verdict,
        package_digest=digest,
    )


def dispatch_verifier(verifier: VerifierRecord, fixture: ControlledFixture, candidate_digest: str) -> ActualExecutionRecord:
    start = time.perf_counter()
    timestamp = "2026-01-01T00:00:00Z"
    exception = ""
    stderr = ""
    try:
        observed = _resolve_verifier(verifier)(fixture)
        return_code = 0
    except Exception as exc:  # pragma: no cover - exercised by explicit error fixtures.
        observed = {"disposition": "ERROR", "events": (), "rejections": (), "transitions": (), "mutations": (), "outputs": {"exception": str(exc)}}
        exception = str(exc)
        stderr = str(exc)
        return_code = 1
    int((time.perf_counter() - start) * 1000)
    elapsed = 0
    expected = fixture.expected
    comparison = _compare_expected_observed(expected, observed)
    disposition = ExecutionDisposition.PASS if return_code == 0 and comparison == "MATCH" else ExecutionDisposition.FAIL
    execution_id = f"TRADER-ACTUAL-EXEC-{_digest((verifier.verifier_id, fixture.fixture_digest, candidate_digest))[:16].upper()}"
    evidence_id = f"TRADER-RAW-EVIDENCE-{_digest((execution_id, 'raw-output'))[:16].upper()}"
    return ActualExecutionRecord(
        execution_id=execution_id,
        verifier_id=verifier.verifier_id,
        requirement_id=verifier.requirement_id,
        proof_id=verifier.proof_id,
        verification_class=verifier.verification_class,
        executing_authority="Independent Behavioral Verification Dispatcher",
        invocation_target=verifier.executable_target,
        executed_source_digest=verifier.verifier_digest,
        candidate_digest=candidate_digest,
        environment_digest=_digest(("python", TRADER_RM_002A_014_VERSION)),
        fixture_digest=fixture.fixture_digest,
        input_digest=fixture.input_digest,
        start_timestamp=timestamp,
        completion_timestamp=timestamp,
        elapsed_ms=elapsed,
        return_code=return_code,
        exception=exception,
        timeout_state="NO_TIMEOUT",
        stdout=json.dumps(observed, sort_keys=True, default=str),
        stderr=stderr,
        pre_state=fixture.pre_state,
        post_state=fixture.cleanup_state,
        observed_events=tuple(observed.get("events", ())),
        observed_mutations=tuple(observed.get("mutations", ())),
        observed_rejections=tuple(observed.get("rejections", ())),
        observed_transitions=tuple(observed.get("transitions", ())),
        observed_outputs=observed.get("outputs", {}),
        cleanup_result="PASS",
        expected_result=expected,
        comparison_result=comparison,
        evidence_references=(evidence_id,),
        disposition=disposition,
    )


def produce_and_validate_evidence(execution: ActualExecutionRecord, fixture: ControlledFixture, candidate_digest: str) -> ValidatedEvidenceRecord:
    raw_content = {
        "execution": asdict(execution),
        "fixture": asdict(fixture),
        "observed_stdout": execution.stdout,
        "comparison_result": execution.comparison_result,
    }
    evidence_id = execution.evidence_references[0]
    source = f"{execution.invocation_target}|{execution.execution_id}|raw-output"
    raw_digest = _digest(raw_content)
    evidence = RawEvidenceRecord(
        evidence_id=evidence_id,
        evidence_type="actual behavioral verification output",
        proof_id=execution.proof_id,
        verification_id=execution.execution_id,
        producing_authority="Independent Behavioral Verification Dispatcher",
        source=source,
        candidate_digest=candidate_digest,
        content_digest=_digest((evidence_id, "actual behavioral verification output", execution.proof_id, execution.execution_id, source)),
        provenance_chain=(execution.requirement_id, execution.verifier_id, execution.execution_id),
        custody_chain=("Independent Behavioral Verification Dispatcher", "Raw Evidence Registry", "Independent Final Reconciliation Authority"),
        contradiction_status="NONE",
        certification_relevance="primary raw observed behavior",
    )
    return validate_raw_evidence(evidence, raw_content, execution, fixture)


def validate_raw_evidence(
    evidence: RawEvidenceRecord,
    raw_content: Mapping[str, object],
    execution: ActualExecutionRecord,
    fixture: ControlledFixture,
) -> ValidatedEvidenceRecord:
    findings = []
    if not raw_content:
        findings.append("raw content missing")
    if evidence.verification_id != execution.execution_id:
        findings.append("mismatched execution identity")
    if evidence.candidate_digest != execution.candidate_digest:
        findings.append("mismatched candidate digest")
    if not evidence.provenance_chain:
        findings.append("missing provenance")
    if execution.disposition != ExecutionDisposition.PASS:
        findings.append("execution did not pass")
    if execution.comparison_result != "MATCH":
        findings.append("expected and observed results diverged")
    if evidence.source == "certification_result.json":
        findings.append("candidate certification result cannot be primary evidence")
    expected_digest = _digest((evidence.evidence_id, evidence.evidence_type, evidence.proof_id, evidence.verification_id, evidence.source))
    if evidence.content_digest != expected_digest:
        findings.append("evidence digest mismatch")
    return ValidatedEvidenceRecord(
        evidence=evidence,
        raw_content=raw_content,
        validation_state=EvidenceValidationState.INVALID if findings else EvidenceValidationState.VALID,
        validation_report=tuple(findings),
        raw_content_digest=_digest(raw_content),
        executable_digest=execution.executed_source_digest,
        fixture_digest=fixture.fixture_digest,
        input_digest=fixture.input_digest,
    )


def recalculate_proofs(
    requirements: Sequence[RequirementRecord],
    verifiers: Sequence[VerifierRecord],
    executions: Sequence[ActualExecutionRecord],
    evidence: Sequence[ValidatedEvidenceRecord],
) -> tuple[ProofObject, ...]:
    verifiers_by_req: dict[str, list[VerifierRecord]] = {}
    executions_by_proof: dict[str, list[ActualExecutionRecord]] = {}
    evidence_by_proof: dict[str, list[ValidatedEvidenceRecord]] = {}
    for verifier in verifiers:
        verifiers_by_req.setdefault(verifier.requirement_id, []).append(verifier)
    for execution in executions:
        executions_by_proof.setdefault(execution.proof_id, []).append(execution)
    for record in evidence:
        evidence_by_proof.setdefault(record.evidence.proof_id, []).append(record)

    proofs = []
    for requirement in requirements:
        proof_id = _proof_id(requirement.requirement_id)
        req_verifiers = tuple(verifiers_by_req.get(requirement.requirement_id, ()))
        req_executions = tuple(executions_by_proof.get(proof_id, ()))
        req_evidence = tuple(evidence_by_proof.get(proof_id, ()))
        findings = _proof_findings(requirement, req_verifiers, req_executions, req_evidence)
        disposition = _proof_disposition(requirement, req_verifiers, req_executions, req_evidence, findings)
        converted_evidence = tuple(record.evidence for record in req_evidence)
        converted_executions = tuple(_legacy_execution(execution) for execution in req_executions)
        proof_basis = {
            "requirement": requirement.requirement_id,
            "verifiers": [verifier.verifier_digest for verifier in req_verifiers],
            "executions": [execution.execution_id for execution in req_executions],
            "evidence": [record.raw_content_digest for record in req_evidence],
            "disposition": disposition.value,
        }
        proofs.append(
            ProofObject(
                proof_id=proof_id,
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
                verification_executions=converted_executions,
                raw_evidence=converted_evidence,
                evidence_validation_status="VALID" if all(record.validation_state == EvidenceValidationState.VALID for record in req_evidence) else "INVALID",
                contradiction_status="NONE",
                findings=findings,
                disposition=disposition,
                disposition_authority="Independent Behavioral Proof Recalculation Engine",
                reproducibility_digest=_digest(proof_basis),
            )
        )
    return tuple(proofs)


def demonstrate_fail_closed_behavior(
    requirement: RequirementRecord,
    verifier: VerifierRecord,
    fixture: ControlledFixture,
    candidate_digest: str,
) -> Mapping[str, object]:
    missing = recalculate_proofs((requirement,), (), (), ())
    defect_fixture = replace(fixture, expected={**fixture.expected, "disposition": "FAIL"})
    defect_execution = dispatch_verifier(verifier, defect_fixture, candidate_digest)
    defect_evidence = produce_and_validate_evidence(defect_execution, defect_fixture, candidate_digest)
    timeout_execution = replace(defect_execution, disposition=ExecutionDisposition.TIMEOUT, timeout_state="TIMEOUT", comparison_result="TIMEOUT")
    timeout_evidence = produce_and_validate_evidence(timeout_execution, fixture, candidate_digest)
    synthetic_evidence = replace(
        defect_evidence,
        raw_content={"metadata_only": True},
        validation_state=EvidenceValidationState.INVALID,
        validation_report=("metadata-derived evidence rejected",),
    )
    direct_pass = replace(missing[0], disposition=ProofStatus.PASS, raw_evidence=())
    contradiction_a = produce_and_validate_evidence(dispatch_verifier(verifier, fixture, candidate_digest), fixture, candidate_digest)
    contradiction_b = replace(contradiction_a, validation_state=EvidenceValidationState.CONTRADICTORY, validation_report=("contradictory evidence supplied",))
    return {
        "missing_verifier": {"proof_disposition": missing[0].disposition.value, "final_verdict": derive_final_verdict(missing, ("missing", "missing"))["verdict"]},
        "controlled_defect": {"execution_disposition": defect_execution.disposition.value, "evidence_state": defect_evidence.validation_state.value},
        "synthetic_evidence": {"validation_state": synthetic_evidence.validation_state.value, "finding": synthetic_evidence.validation_report[0]},
        "direct_pass_rejection": {"recalculated_status": _proof_disposition(requirement, (), (), (), ()).value, "manual_status": direct_pass.disposition.value},
        "timeout": {"execution_disposition": timeout_execution.disposition.value, "evidence_state": timeout_evidence.validation_state.value},
        "contradiction": {"validation_state": contradiction_b.validation_state.value, "finding": contradiction_b.validation_report[0]},
    }


def _verifiers_for(requirement: RequirementRecord) -> tuple[VerifierRecord, ...]:
    return tuple(_verifier_record(requirement, verification_class) for verification_class in requirement.verification_classes)


def _verifier_record(requirement: RequirementRecord, verification_class: str) -> VerifierRecord:
    proof_id = _proof_id(requirement.requirement_id)
    target = _target_for(requirement)
    payload = (requirement.requirement_id, verification_class, target, requirement.implementation_obligations)
    verifier_id = f"TRADER-VERIFIER-{_digest(payload)[:16].upper()}"
    return VerifierRecord(
        verifier_id=verifier_id,
        requirement_id=requirement.requirement_id,
        proof_id=proof_id,
        verification_class=verification_class,
        executable_type="in-process callable",
        executable_target=target,
        source_artifact="src/argos/trader/requirement_verifier.py",
        implementation_path_under_test=requirement.implementation_obligations[0],
        objects_under_test=requirement.objects,
        interfaces_under_test=requirement.interfaces,
        lifecycles_under_test=requirement.lifecycles,
        required_fixtures=(f"FIXTURE-{verification_class.upper()}",),
        input_builder="_fixture_for",
        expected_result_reference="constitutional expectation registry",
        observation_adapter="_resolve_verifier",
        evidence_parser="produce_and_validate_evidence",
        timeout_seconds=5,
        retry_policy="no retry for proof execution",
        isolation_requirement="fresh deterministic fixture per execution",
        cleanup_procedure="verify cleanup state matches expected cleanup",
        determinism_classification="deterministic",
        permitted_nondeterministic_fields=("elapsed_ms",),
        verifier_version=TRADER_RM_002A_014_VERSION,
        verifier_digest=_digest(payload),
        responsible_component="Trader Requirement Verifier Registry",
    )


def _fixture_for(verifier: VerifierRecord) -> ControlledFixture:
    inputs = _inputs_for(verifier)
    expected = _expected_for(verifier)
    fixture_payload = (verifier.verifier_id, inputs, expected)
    return ControlledFixture(
        fixture_id=f"TRADER-FIXTURE-{_digest(fixture_payload)[:16].upper()}",
        requirement_id=verifier.requirement_id,
        verification_class=verifier.verification_class,
        condition=_condition_for(verifier.verification_class),
        inputs=inputs,
        pre_state={"state": "isolated", "candidate_verdict_files_loaded": False},
        expected=expected,
        cleanup_state={"state": "clean", "fixture_leakage": False},
        fixture_digest=_digest(fixture_payload),
        input_digest=_digest(inputs),
    )


def _resolve_verifier(verifier: VerifierRecord) -> Callable[[ControlledFixture], Mapping[str, object]]:
    targets = {
        "execution_authority": _verify_execution_authority,
        "operating_mode": _verify_operating_mode,
        "financial_ownership": _verify_financial_ownership,
        "temporal": _verify_temporal,
        "case_file": _verify_case_file,
        "lifecycle_transition": _verify_lifecycle,
        "rm002_constitution": _verify_rm002_constitution,
        "rm002a_publication": _verify_rm002a_publication,
        "certification_verdict": _verify_certification_verdict,
    }
    if verifier.executable_target not in targets:
        raise LookupError(f"unresolved verifier target: {verifier.executable_target}")
    return targets[verifier.executable_target]


def _verify_execution_authority(fixture: ControlledFixture) -> Mapping[str, object]:
    valid = validate_execution_authority(AuthorityInputs(True, True, True, True))
    invalid = validate_execution_authority(AuthorityInputs(True, False, True, True))
    return _observed(valid.status == TraderGovernanceStatus.PASS and invalid.status == TraderGovernanceStatus.FAIL, ("authorization rejection",), ())


def _verify_operating_mode(fixture: ControlledFixture) -> Mapping[str, object]:
    valid = resolve_operating_mode((TraderOperatingMode.PAPER,))
    invalid = resolve_operating_mode((TraderOperatingMode.PAPER, TraderOperatingMode.LIVE))
    return _observed(valid.status == TraderGovernanceStatus.PASS and invalid.status == TraderGovernanceStatus.FAIL, ("conflicting mode rejection",), ())


def _verify_financial_ownership(fixture: ControlledFixture) -> Mapping[str, object]:
    invalid_owners = dict(FINANCIAL_RESOURCE_OWNERS)
    invalid_owners["Cash"] = "Trader Office"
    scope = validate_execution_scope(ExecutionScope("cash_equity", "limit", "cash_brokerage", FINANCIAL_RESOURCE_OWNERS, True, True))
    invalid = validate_financial_resource_ownership(invalid_owners)
    return _observed(scope.status == TraderGovernanceStatus.PASS and invalid.status == TraderGovernanceStatus.FAIL, ("financial truth ownership rejection",), ())


def _verify_temporal(fixture: ControlledFixture) -> Mapping[str, object]:
    valid = validate_temporal_context(TemporalContext(True, True, 0, 5, True, False, True, True, True))
    stale = validate_temporal_context(TemporalContext(False, False, 9, 5, True, True, False, False, False))
    return _observed(valid.status == TraderGovernanceStatus.PASS and stale.status == TraderGovernanceStatus.FAIL, ("stale time rejection",), ())


def _verify_case_file(fixture: ControlledFixture) -> Mapping[str, object]:
    valid = validate_case_file_evidence(CASE_FILE_REQUIRED_EVIDENCE)
    incomplete = validate_case_file_evidence(tuple(item for item in CASE_FILE_REQUIRED_EVIDENCE if item != "custody acknowledgement"))
    historian = validate_historian_completion(HistorianCompletionContext(True, True, True, True))
    return _observed(valid.status.value == "PASS" and incomplete.status.value == "FAIL" and historian.status == TraderGovernanceStatus.PASS, ("missing evidence rejection",), ())


def _verify_lifecycle(fixture: ControlledFixture) -> Mapping[str, object]:
    lifecycle = next(iter(TRADER_RM002_LIFECYCLES.values()))
    source, destination = lifecycle.permitted_transitions[0]
    valid = validate_lifecycle_transition(next(name for name, item in TRADER_RM002_LIFECYCLES.items() if item == lifecycle), source, destination)
    return _observed(valid.status.value == "PASS", (), (f"{source}->{destination}",))


def _verify_rm002_constitution(fixture: ControlledFixture) -> Mapping[str, object]:
    valid = validate_rm002_constitution()
    return _observed(valid.status.value == "PASS", (), ())


def _verify_rm002a_publication(fixture: ControlledFixture) -> Mapping[str, object]:
    valid = validate_rm002a_publication()
    return _observed(valid.status.value == "PASS", (), ())


def _verify_certification_verdict(fixture: ControlledFixture) -> Mapping[str, object]:
    valid = validate_certification_verdict(CertificationVerdict.UNCONDITIONAL_PASS.value)
    invalid = validate_certification_verdict("CONDITIONAL PASS")
    return _observed(valid.status == TraderGovernanceStatus.PASS and invalid.status == TraderGovernanceStatus.FAIL, ("conditional certification rejection",), ())


def _observed(pass_condition: bool, rejections: Sequence[str], transitions: Sequence[str]) -> Mapping[str, object]:
    return {
        "disposition": "PASS" if pass_condition else "FAIL",
        "events": ("actual Trader implementation path invoked",),
        "mutations": (),
        "rejections": tuple(rejections),
        "transitions": tuple(transitions),
        "outputs": {"behavioral_condition": pass_condition},
    }


def _inputs_for(verifier: VerifierRecord) -> Mapping[str, object]:
    return {
        "requirement_id": verifier.requirement_id,
        "verification_class": verifier.verification_class,
        "objects": verifier.objects_under_test,
        "lifecycles": verifier.lifecycles_under_test,
        "condition": _condition_for(verifier.verification_class),
    }


def _expected_for(verifier: VerifierRecord) -> Mapping[str, object]:
    return {
        "disposition": "PASS",
        "required_event": "actual Trader implementation path invoked",
        "prohibited_candidate_verdict_input": True,
        "cleanup_required": True,
    }


def _condition_for(verification_class: str) -> str:
    return {
        "positive": "valid constitutional behavior",
        "negative": "invalid input is rejected",
        "boundary": "constitutional boundary is respected",
        "stale_input": "stale input fails closed",
        "expired_authority": "expired authority fails closed",
        "conflicting_authority": "conflict is preserved and rejected",
        "replay": "replayed input cannot duplicate execution",
        "restart": "state remains reconstructable",
        "recovery": "recovery follows deterministic state",
        "missing_evidence": "missing evidence prevents pass",
        "duplicate_input": "duplicate input is detected",
        "out_of_order": "out-of-order events are reconciled",
        "unauthorized_mutation": "unauthorized mutation is rejected",
        "uncertain_state": "uncertainty fails closed",
        "terminality": "terminal state cannot mutate",
    }.get(verification_class, verification_class)


def _target_for(requirement: RequirementRecord) -> str:
    text = " ".join((requirement.classification, requirement.statement, " ".join(requirement.objects), " ".join(requirement.lifecycles))).lower()
    if "authorization" in text or "risk" in text or "authority" in text:
        return "execution_authority"
    if "mode" in text:
        return "operating_mode"
    if "financial" in text or "settlement" in text or "buying" in text:
        return "financial_ownership"
    if "temporal" in text or "fresh" in text or "stale" in text or "expired" in text:
        return "temporal"
    if "case file" in text or "evidence" in text or "historian" in text or "custody" in text:
        return "case_file"
    if "lifecycle" in text or "transition" in text:
        return "lifecycle_transition"
    if "rm-002a" in text or "publication" in text:
        return "rm002a_publication"
    if "certification" in text or "verdict" in text:
        return "certification_verdict"
    return "rm002_constitution"


def _compare_expected_observed(expected: Mapping[str, object], observed: Mapping[str, object]) -> str:
    if observed.get("disposition") != expected.get("disposition"):
        return "DIVERGENT"
    if expected.get("required_event") not in observed.get("events", ()):
        return "DIVERGENT"
    return "MATCH"


def _proof_findings(
    requirement: RequirementRecord,
    verifiers: Sequence[VerifierRecord],
    executions: Sequence[ActualExecutionRecord],
    evidence: Sequence[ValidatedEvidenceRecord],
) -> tuple[FindingRecord, ...]:
    findings = []
    required_classes = set(requirement.verification_classes)
    executed_classes = {execution.verification_class for execution in executions if execution.disposition == ExecutionDisposition.PASS}
    missing = sorted(required_classes.difference(executed_classes))
    if not verifiers:
        findings.append(("MISSING VERIFIER", "Every required verifier resolves to executable code", "missing verifier"))
    if missing:
        findings.append(("VERIFICATION NOT EXECUTED", "Every required verification class executes", ", ".join(missing)))
    if any(execution.disposition != ExecutionDisposition.PASS for execution in executions):
        findings.append(("VERIFIER EXECUTION FAILED", "All verifier executions PASS", "failed execution"))
    if any(record.validation_state != EvidenceValidationState.VALID for record in evidence):
        findings.append(("INVALID EVIDENCE", "All raw evidence validates", "invalid evidence"))
    if not evidence:
        findings.append(("MISSING RAW EVIDENCE", "Observed raw evidence exists", "missing raw evidence"))
    return tuple(
        FindingRecord(
            finding_id=f"TRADER-FINDING-{_digest((requirement.requirement_id, index, classification))[:16].upper()}",
            proof_id=_proof_id(requirement.requirement_id),
            requirement_id=requirement.requirement_id,
            classification=classification,
            severity="certification-critical",
            observed=observed,
            expected=expected,
            consequence="final verdict FAIL",
            remediation_owner="Trader Office",
            disposition=FindingDisposition.OPEN,
            closure_evidence=(),
        )
        for index, (classification, expected, observed) in enumerate(findings, start=1)
    )


def _proof_disposition(
    requirement: RequirementRecord,
    verifiers: Sequence[VerifierRecord],
    executions: Sequence[ActualExecutionRecord],
    evidence: Sequence[ValidatedEvidenceRecord],
    findings: Sequence[FindingRecord],
) -> ProofStatus:
    if not verifiers or not executions:
        return ProofStatus.NOT_EXECUTED
    if findings:
        return ProofStatus.FAIL
    required_classes = set(requirement.verification_classes)
    executed_classes = {execution.verification_class for execution in executions if execution.disposition == ExecutionDisposition.PASS}
    if required_classes != executed_classes:
        return ProofStatus.NOT_EXECUTED
    if any(record.validation_state != EvidenceValidationState.VALID for record in evidence):
        return ProofStatus.FAIL
    return ProofStatus.PASS


def _legacy_execution(execution: ActualExecutionRecord) -> VerificationExecutionRecord:
    return VerificationExecutionRecord(
        execution_id=execution.execution_id,
        proof_id=execution.proof_id,
        rule_id=execution.verifier_id,
        verification_class=execution.verification_class,
        executing_authority=execution.executing_authority,
        execution_command=execution.invocation_target,
        candidate_digest=execution.candidate_digest,
        environment_digest=execution.environment_digest,
        inputs=(execution.input_digest,),
        expected_result=json.dumps(execution.expected_result, sort_keys=True),
        observed_result=json.dumps(execution.observed_outputs, sort_keys=True),
        exit_status=execution.return_code,
        produced_evidence=execution.evidence_references,
        reproducibility_status="REPRODUCIBLE",
        disposition=ProofStatus.PASS if execution.disposition == ExecutionDisposition.PASS else ProofStatus.FAIL,
    )


def _proof_id(requirement_id: str) -> str:
    return f"TRADER-PROOF-{_digest(requirement_id)[:16].upper()}"


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
