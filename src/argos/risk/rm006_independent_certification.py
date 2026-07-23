"""Independent Risk Office certification and closure support for RISK-RM-006."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision
from argos.risk.rm005_closure_operational import FIXED_CERTIFICATION_TIMESTAMP
from argos.risk.rm005a_operational import RiskRm005aOperationalCompletionPackage, RiskRm005aOperationalSupport


INDEPENDENT_AUTHORITY = "Independent Risk Office Certification Authority"


def _jsonable(value: Any) -> Any:
    if isinstance(value, EnterpriseCertificationDecision):
        return value.value
    if is_dataclass(value):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _freeze(values: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted(values.items())))


@dataclass(frozen=True)
class RiskRm006CandidateAcceptanceRecord:
    acceptance_identifier: str
    candidate_identifier: str
    candidate_digest: str
    repository_identifier: str
    immutable_revision: str
    accepted_by_authority: str
    acceptance_timestamp: str
    admissibility_evidence: tuple[str, ...]
    findings: tuple[str, ...]
    accepted: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm006ExecutionRecord:
    execution_identifier: str
    candidate_identifier: str
    execution_authority: str
    executed_operations: tuple[str, ...]
    evidence_inputs: tuple[str, ...]
    generated_findings: tuple[str, ...]
    invariant_results: Mapping[str, EnterpriseCertificationDecision]
    replay_verified: bool
    recovery_verified: bool
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm006FindingAdjudicationRecord:
    adjudication_identifier: str
    finding_identifier: str
    finding_text: str
    classification: str
    severity: str
    certification_impact: str
    evidence_basis: tuple[str, ...]
    disposition: str
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm006CertificationDeterminationRecord:
    determination_identifier: str
    candidate_identifier: str
    candidate_digest: str
    issuing_authority: str
    determination: EnterpriseCertificationDecision
    determination_label: str
    admissible_inputs: tuple[str, ...]
    adjudicated_blocking_findings: int
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm006ClosureRecord:
    closure_identifier: str
    candidate_identifier: str
    candidate_digest: str
    closure_authority: str
    sealed_package_identifier: str
    archive_identifier: str
    recertification_governance: tuple[str, ...]
    closure_timestamp: str
    precondition_results: Mapping[str, EnterpriseCertificationDecision]
    package_signature: str
    findings: tuple[str, ...]
    closed: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm006IndependentCertificationPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    operational_completion_package: RiskRm005aOperationalCompletionPackage
    candidate_acceptance: RiskRm006CandidateAcceptanceRecord
    certification_execution: RiskRm006ExecutionRecord
    finding_adjudications: tuple[RiskRm006FindingAdjudicationRecord, ...]
    certification_determination: RiskRm006CertificationDeterminationRecord
    constitutional_closure: RiskRm006ClosureRecord
    immutable_audit_references: tuple[str, ...]
    final_completion_readiness: EnterpriseCertificationDecision
    deterministic_digest: str


class RiskRm006IndependentCertificationSupport:
    """Execute independent Risk Office certification for RISK-RM-006-001 through 005."""

    order_coverage = (
        "RISK-RM-006-001",
        "RISK-RM-006-002",
        "RISK-RM-006-003",
        "RISK-RM-006-004",
        "RISK-RM-006-005",
    )

    execution_operations = (
        "Candidate Artifact Verification",
        "Schema Validation Review",
        "Registry Completeness Review",
        "Constitutional Rule Execution Review",
        "Certification Test Execution Review",
        "Metric Threshold Review",
        "Evidence Admissibility Review",
        "Traceability Review",
        "Replay Verification Review",
        "Recovery Verification Review",
        "Constitutional Invariant Review",
    )

    def build_independent_certification_package(
        self,
        candidate_root: str | Path | None = None,
    ) -> RiskRm006IndependentCertificationPackage:
        root = Path(candidate_root).resolve() if candidate_root is not None else Path(__file__).resolve().parents[3]
        operational_package = RiskRm005aOperationalSupport().build_operational_package(root)
        acceptance = self.accept_candidate(operational_package)
        execution = self.execute_independent_certification(operational_package, acceptance)
        adjudications = self.adjudicate_findings(execution)
        determination = self.issue_certification_determination(operational_package, acceptance, execution, adjudications)
        closure = self.close_constitutional_certification(operational_package, acceptance, execution, adjudications, determination)
        final = EnterpriseCertificationDecision.PASS if (
            acceptance.result == EnterpriseCertificationDecision.PASS
            and execution.result == EnterpriseCertificationDecision.PASS
            and all(record.result == EnterpriseCertificationDecision.PASS for record in adjudications)
            and determination.determination == EnterpriseCertificationDecision.PASS
            and closure.result == EnterpriseCertificationDecision.PASS
            and closure.closed
        ) else EnterpriseCertificationDecision.FAIL
        package = RiskRm006IndependentCertificationPackage(
            package_identifier=f"RISK-RM-006-INDEPENDENT-{_digest((operational_package.deterministic_digest, closure.deterministic_digest))[:12].upper()}",
            governing_doctrine="RISK-RM-006-001-TO-005/1.0.0",
            order_coverage=self.order_coverage,
            operational_completion_package=operational_package,
            candidate_acceptance=acceptance,
            certification_execution=execution,
            finding_adjudications=adjudications,
            certification_determination=determination,
            constitutional_closure=closure,
            immutable_audit_references=(
                acceptance.acceptance_identifier,
                execution.execution_identifier,
                determination.determination_identifier,
                closure.closure_identifier,
            ),
            final_completion_readiness=final,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def accept_candidate(
        self,
        operational_package: RiskRm005aOperationalCompletionPackage,
        *,
        force_rejection: tuple[str, ...] = (),
    ) -> RiskRm006CandidateAcceptanceRecord:
        governance = operational_package.candidate_governance
        findings = list(force_rejection)
        if operational_package.final_completion_readiness != EnterpriseCertificationDecision.PASS:
            findings.append("operational completion package is not ready for independent certification")
        if governance.result != EnterpriseCertificationDecision.PASS:
            findings.extend(governance.findings)
        if not governance.candidate_identifier or not governance.candidate_digest:
            findings.append("candidate identity is incomplete")
        if governance.immutable_commit_identifier == "UNVERSIONED-CANDIDATE":
            findings.append("candidate immutable revision is unavailable")
        record = RiskRm006CandidateAcceptanceRecord(
            acceptance_identifier=f"RISK-RM006-ACCEPT-{governance.candidate_digest[:12].upper()}",
            candidate_identifier=governance.candidate_identifier,
            candidate_digest=governance.candidate_digest,
            repository_identifier=governance.repository_identifier,
            immutable_revision=governance.immutable_commit_identifier,
            accepted_by_authority=INDEPENDENT_AUTHORITY,
            acceptance_timestamp=FIXED_CERTIFICATION_TIMESTAMP,
            admissibility_evidence=(governance.deterministic_digest, operational_package.evidence_completion_review.deterministic_digest),
            findings=tuple(findings),
            accepted=not findings,
            result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def execute_independent_certification(
        self,
        operational_package: RiskRm005aOperationalCompletionPackage,
        acceptance: RiskRm006CandidateAcceptanceRecord,
        *,
        injected_findings: tuple[str, ...] = (),
    ) -> RiskRm006ExecutionRecord:
        invariant_results = {
            "single_candidate": EnterpriseCertificationDecision.PASS if acceptance.accepted else EnterpriseCertificationDecision.FAIL,
            "candidate_bound_evidence": operational_package.evidence_completion_review.result,
            "authority_separation": operational_package.authority_separation.result,
            "rule_registry_complete": EnterpriseCertificationDecision.PASS if operational_package.constitutional_rule_registry else EnterpriseCertificationDecision.FAIL,
            "traceability_complete": operational_package.closure_package.certification_decision.decision,
            "replay_verified": operational_package.closure_package.replay_recovery_record.result,
            "recovery_verified": operational_package.closure_package.replay_recovery_record.result,
        }
        generated_findings = list(injected_findings)
        if acceptance.result != EnterpriseCertificationDecision.PASS:
            generated_findings.extend(acceptance.findings)
        generated_findings.extend(
            f"invariant failed: {name}" for name, result in invariant_results.items() if result != EnterpriseCertificationDecision.PASS
        )
        findings = tuple(generated_findings)
        record = RiskRm006ExecutionRecord(
            execution_identifier=f"RISK-RM006-EXEC-{acceptance.candidate_digest[:12].upper()}",
            candidate_identifier=acceptance.candidate_identifier,
            execution_authority=INDEPENDENT_AUTHORITY,
            executed_operations=self.execution_operations,
            evidence_inputs=(
                acceptance.deterministic_digest,
                operational_package.deterministic_digest,
                operational_package.closure_package.deterministic_digest,
            ),
            generated_findings=findings,
            invariant_results=_freeze(invariant_results),
            replay_verified=invariant_results["replay_verified"] == EnterpriseCertificationDecision.PASS,
            recovery_verified=invariant_results["recovery_verified"] == EnterpriseCertificationDecision.PASS,
            findings=findings,
            result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def adjudicate_findings(self, execution: RiskRm006ExecutionRecord) -> tuple[RiskRm006FindingAdjudicationRecord, ...]:
        if not execution.generated_findings:
            record = RiskRm006FindingAdjudicationRecord(
                adjudication_identifier=f"RISK-RM006-ADJ-{execution.execution_identifier[-12:]}-NONE",
                finding_identifier="NO-FINDINGS",
                finding_text="No independent certification findings were produced.",
                classification="NO_FINDING",
                severity="NONE",
                certification_impact="NON_BLOCKING",
                evidence_basis=(execution.deterministic_digest,),
                disposition="ADJUDICATED_NO_FINDINGS",
                findings=(),
                result=EnterpriseCertificationDecision.PASS,
                deterministic_digest="",
            )
            return (replace(record, deterministic_digest=_digest(record)),)
        records = []
        for index, finding in enumerate(sorted(set(execution.generated_findings)), start=1):
            record = RiskRm006FindingAdjudicationRecord(
                adjudication_identifier=f"RISK-RM006-ADJ-{index:03d}",
                finding_identifier=f"RISK-RM006-FINDING-{index:03d}",
                finding_text=finding,
                classification="CONSTITUTIONAL_BLOCKER",
                severity="BLOCKING",
                certification_impact="CERTIFICATION_PROHIBITED",
                evidence_basis=(execution.deterministic_digest,),
                disposition="ADJUDICATED_VALID_BLOCKING_FINDING",
                findings=(finding,),
                result=EnterpriseCertificationDecision.FAIL,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def issue_certification_determination(
        self,
        operational_package: RiskRm005aOperationalCompletionPackage,
        acceptance: RiskRm006CandidateAcceptanceRecord,
        execution: RiskRm006ExecutionRecord,
        adjudications: tuple[RiskRm006FindingAdjudicationRecord, ...],
    ) -> RiskRm006CertificationDeterminationRecord:
        blocking = sum(1 for record in adjudications if record.certification_impact == "CERTIFICATION_PROHIBITED")
        findings = []
        if acceptance.result != EnterpriseCertificationDecision.PASS:
            findings.append("candidate acceptance failed")
        if execution.result != EnterpriseCertificationDecision.PASS:
            findings.append("independent certification execution failed")
        if blocking:
            findings.append("blocking adjudicated findings prohibit certification")
        if operational_package.authority_separation.independent_certification_decision != "RESERVED_FOR_RISK_RM_006":
            findings.append("independent authority reservation was not preserved")
        determination = EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL
        record = RiskRm006CertificationDeterminationRecord(
            determination_identifier=f"RISK-RM006-DETERMINATION-{acceptance.candidate_digest[:12].upper()}",
            candidate_identifier=acceptance.candidate_identifier,
            candidate_digest=acceptance.candidate_digest,
            issuing_authority=INDEPENDENT_AUTHORITY,
            determination=determination,
            determination_label="INDEPENDENT RISK OFFICE CERTIFICATION PASS" if determination == EnterpriseCertificationDecision.PASS else "INDEPENDENT RISK OFFICE CERTIFICATION FAIL",
            admissible_inputs=(
                acceptance.deterministic_digest,
                execution.deterministic_digest,
                _digest(adjudications),
                operational_package.evidence_completion_review.deterministic_digest,
            ),
            adjudicated_blocking_findings=blocking,
            findings=tuple(findings),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def close_constitutional_certification(
        self,
        operational_package: RiskRm005aOperationalCompletionPackage,
        acceptance: RiskRm006CandidateAcceptanceRecord,
        execution: RiskRm006ExecutionRecord,
        adjudications: tuple[RiskRm006FindingAdjudicationRecord, ...],
        determination: RiskRm006CertificationDeterminationRecord,
    ) -> RiskRm006ClosureRecord:
        preconditions = {
            "candidate_accepted": acceptance.result,
            "execution_completed": execution.result,
            "findings_adjudicated": EnterpriseCertificationDecision.PASS if all(record.result == EnterpriseCertificationDecision.PASS for record in adjudications) else EnterpriseCertificationDecision.FAIL,
            "single_determination_issued": EnterpriseCertificationDecision.PASS if determination.determination_identifier else EnterpriseCertificationDecision.FAIL,
            "evidence_validated": operational_package.evidence_completion_review.result,
            "replay_succeeded": operational_package.closure_package.replay_recovery_record.result,
            "recovery_succeeded": operational_package.closure_package.replay_recovery_record.result,
            "determination_passed": determination.determination,
        }
        findings = tuple(f"closure precondition failed: {name}" for name, result in preconditions.items() if result != EnterpriseCertificationDecision.PASS)
        closed = not findings
        signature_payload = (
            operational_package.closure_package.certification_package.integrity_digest,
            determination.deterministic_digest,
            acceptance.candidate_digest,
            INDEPENDENT_AUTHORITY,
        )
        record = RiskRm006ClosureRecord(
            closure_identifier=f"RISK-RM006-CLOSURE-{acceptance.candidate_digest[:12].upper()}",
            candidate_identifier=acceptance.candidate_identifier,
            candidate_digest=acceptance.candidate_digest,
            closure_authority=INDEPENDENT_AUTHORITY,
            sealed_package_identifier=operational_package.closure_package.certification_package.package_identifier,
            archive_identifier=f"RISK-RM006-ARCHIVE-{acceptance.candidate_digest[:16].upper()}",
            recertification_governance=(
                "recertification required after candidate artifact change",
                "recertification required after doctrine version change",
                "recertification required after registry, schema, or rule version change",
            ),
            closure_timestamp=FIXED_CERTIFICATION_TIMESTAMP,
            precondition_results=_freeze(preconditions),
            package_signature=_digest(signature_payload),
            findings=findings,
            closed=closed,
            result=EnterpriseCertificationDecision.PASS if closed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))
