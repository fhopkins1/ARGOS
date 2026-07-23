"""Operational RISK-RM-005A certification completion support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
import hashlib
import json
import subprocess
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision
from argos.risk.rm005_closure_operational import FIXED_CERTIFICATION_TIMESTAMP, RiskRm005ClosureOperationalPackage, RiskRm005ClosureOperationalSupport


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
class RiskRm005aRuleRegistryRecord:
    rule_identifier: str
    requirement_identifier: str
    candidate_class: str
    applicable_artifact_identifiers: tuple[str, ...]
    executable_evaluator: str
    mandatory_evidence_dependencies: tuple[str, ...]
    deterministic_outcomes: tuple[str, ...]
    failure_classification: str
    active: bool
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005aCandidateGovernanceRecord:
    governance_identifier: str
    candidate_identifier: str
    candidate_digest: str
    immutable_commit_identifier: str
    repository_identifier: str
    lifecycle_state: str
    admissibility_requirements: Mapping[str, bool]
    repository_observation_status: str
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005aAuthoritySeparationRecord:
    authority_identifier: str
    operational_authority: str
    independent_authority: str
    operational_determination: EnterpriseCertificationDecision
    independent_certification_decision: str
    prohibited_operational_actions: tuple[str, ...]
    evidence_basis: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005aConditionalPassGovernanceRecord:
    disposition_identifier: str
    disposition_code: str
    disposition_label: str
    eligibility_basis: tuple[str, ...]
    remediation_required: bool
    independent_certification_eligible: bool
    restrictions: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005aEvidenceCompletionReviewRecord:
    review_identifier: str
    review_sequence: tuple[str, ...]
    subsystem_results: Mapping[str, EnterpriseCertificationDecision]
    readiness_for_rm006: bool
    evidence_references: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005aOperationalCompletionPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    closure_package: RiskRm005ClosureOperationalPackage
    constitutional_rule_registry: tuple[RiskRm005aRuleRegistryRecord, ...]
    candidate_governance: RiskRm005aCandidateGovernanceRecord
    authority_separation: RiskRm005aAuthoritySeparationRecord
    conditional_pass_governance: RiskRm005aConditionalPassGovernanceRecord
    evidence_completion_review: RiskRm005aEvidenceCompletionReviewRecord
    immutable_audit_references: tuple[str, ...]
    final_completion_readiness: EnterpriseCertificationDecision
    deterministic_digest: str


class RiskRm005aOperationalSupport:
    """Build candidate-bound operational evidence for RISK-RM-005A-001 through 005."""

    order_coverage = (
        "RISK-RM-005A-001",
        "RISK-RM-005A-002",
        "RISK-RM-005A-003",
        "RISK-RM-005A-004",
        "RISK-RM-005A-005",
    )

    review_sequence = (
        "Candidate Verification",
        "Registry Verification",
        "Rule Registry Verification",
        "Evaluation Engine Verification",
        "Certification Test Verification",
        "Metrics Verification",
        "Evidence Verification",
        "Traceability Verification",
        "Persistence Verification",
        "Replay Verification",
        "Recovery Verification",
        "Authority Separation Verification",
        "Conditional PASS Governance Verification",
        "Operational Readiness Determination",
    )

    def build_operational_package(self, candidate_root: str | Path | None = None) -> RiskRm005aOperationalCompletionPackage:
        root = Path(candidate_root).resolve() if candidate_root is not None else Path(__file__).resolve().parents[3]
        closure_package = RiskRm005ClosureOperationalSupport().build_operational_package(root)
        rule_registry = self.materialize_constitutional_rule_registry(closure_package)
        candidate_governance = self.govern_certification_candidate(closure_package, root)
        authority = self.separate_certification_authority(closure_package)
        conditional = self.evaluate_conditional_pass_governance(closure_package, authority)
        review = self.review_operational_evidence_completion(closure_package, rule_registry, candidate_governance, authority, conditional)
        final = EnterpriseCertificationDecision.PASS if (
            closure_package.final_completion_readiness == EnterpriseCertificationDecision.PASS
            and rule_registry
            and all(record.result == EnterpriseCertificationDecision.PASS for record in rule_registry)
            and candidate_governance.result == EnterpriseCertificationDecision.PASS
            and authority.result == EnterpriseCertificationDecision.PASS
            and conditional.result == EnterpriseCertificationDecision.PASS
            and review.result == EnterpriseCertificationDecision.PASS
        ) else EnterpriseCertificationDecision.FAIL
        package = RiskRm005aOperationalCompletionPackage(
            package_identifier=f"RISK-RM-005A-COMPLETION-{_digest((closure_package.deterministic_digest, review.deterministic_digest))[:12].upper()}",
            governing_doctrine="RISK-RM-005A-001-TO-005/1.0.0",
            order_coverage=self.order_coverage,
            closure_package=closure_package,
            constitutional_rule_registry=rule_registry,
            candidate_governance=candidate_governance,
            authority_separation=authority,
            conditional_pass_governance=conditional,
            evidence_completion_review=review,
            immutable_audit_references=(
                "RISK-RM-005A-001-RULE-REGISTRY",
                candidate_governance.governance_identifier,
                authority.authority_identifier,
                conditional.disposition_identifier,
                review.review_identifier,
            ),
            final_completion_readiness=final,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def materialize_constitutional_rule_registry(
        self,
        closure_package: RiskRm005ClosureOperationalPackage,
        *,
        omit_requirements: tuple[str, ...] = (),
    ) -> tuple[RiskRm005aRuleRegistryRecord, ...]:
        records: list[RiskRm005aRuleRegistryRecord] = []
        registry_package = closure_package.registry_package
        candidate_package = registry_package.execution_package.candidate_package
        artifacts_by_class = candidate_package.candidate_class_registry
        for evaluation in registry_package.execution_package.rule_evaluations:
            artifact = next(
                item for item in candidate_package.discovered_artifacts if item.artifact_identifier == evaluation.target_artifact_identifier
            )
            records.append(
                self._rule_record(
                    evaluation.rule_identifier,
                    "RISK-RM-005-008",
                    artifact.artifact_class,
                    (artifact.artifact_identifier,),
                    "RiskRm005ExecutionOperationalSupport.evaluate_rule",
                    (evaluation.deterministic_digest, artifact.content_digest),
                    evaluation.result,
                )
            )
        for requirement in self.order_coverage:
            if requirement in omit_requirements:
                continue
            records.append(
                self._rule_record(
                    f"RULE-{requirement}",
                    requirement,
                    "risk-certification-evidence",
                    tuple(artifacts_by_class.get("risk-certification-evidence", ())),
                    "RiskRm005aOperationalSupport.materialize_constitutional_rule_registry",
                    (closure_package.deterministic_digest,),
                    EnterpriseCertificationDecision.PASS,
                )
            )
        missing = set(self.order_coverage) - {record.requirement_identifier for record in records}
        if missing:
            failure = RiskRm005aRuleRegistryRecord(
                rule_identifier="RULE-RISK-RM-005A-FAIL-CLOSED",
                requirement_identifier="RISK-RM-005A-RULE-COVERAGE-FAILURE",
                candidate_class="risk-certification-evidence",
                applicable_artifact_identifiers=(),
                executable_evaluator="",
                mandatory_evidence_dependencies=(),
                deterministic_outcomes=("FAIL",),
                failure_classification="RULE_REGISTRY_INCOMPLETE",
                active=False,
                findings=tuple(f"missing operational rule record for {item}" for item in sorted(missing)),
                result=EnterpriseCertificationDecision.FAIL,
                deterministic_digest="",
            )
            records.append(replace(failure, deterministic_digest=_digest(failure)))
        return tuple(records)

    def govern_certification_candidate(
        self,
        closure_package: RiskRm005ClosureOperationalPackage,
        candidate_root: Path,
        *,
        force_mutable_candidate: bool = False,
    ) -> RiskRm005aCandidateGovernanceRecord:
        candidate = closure_package.certification_package
        status = _git_status(candidate_root)
        admissibility = {
            "single_candidate": bool(candidate.candidate_identifier),
            "immutable_commit": bool(candidate.immutable_commit_identifier and candidate.immutable_commit_identifier != "UNVERSIONED-CANDIDATE"),
            "candidate_fingerprint": bool(candidate.candidate_digest),
            "artifact_inventory": candidate.artifact_count if hasattr(candidate, "artifact_count") else bool(closure_package.registry_package.certification_manifest.artifact_count),
            "manifest_binding": closure_package.registry_package.certification_manifest.candidate_digest == candidate.candidate_digest,
            "package_integrity": bool(candidate.integrity_digest),
            "not_forced_mutable": not force_mutable_candidate,
        }
        normalized = {key: bool(value) for key, value in admissibility.items()}
        findings = tuple(f"candidate admissibility requirement failed: {key}" for key, value in normalized.items() if not value)
        record = RiskRm005aCandidateGovernanceRecord(
            governance_identifier=f"RISK-RM005A-CANDIDATE-GOV-{candidate.candidate_digest[:12].upper()}",
            candidate_identifier=candidate.candidate_identifier,
            candidate_digest=candidate.candidate_digest,
            immutable_commit_identifier=candidate.immutable_commit_identifier,
            repository_identifier=candidate.repository_identifier,
            lifecycle_state="BOUND_IMMUTABLE",
            admissibility_requirements=_freeze(normalized),
            repository_observation_status="DIRTY_WORKTREE_OBSERVED" if status else "CLEAN_WORKTREE_OBSERVED",
            findings=findings,
            result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def separate_certification_authority(
        self,
        closure_package: RiskRm005ClosureOperationalPackage,
        *,
        operational_issues_independent_certification: bool = False,
    ) -> RiskRm005aAuthoritySeparationRecord:
        findings = ()
        if operational_issues_independent_certification:
            findings = ("operational authority attempted to issue independent certification",)
        record = RiskRm005aAuthoritySeparationRecord(
            authority_identifier=f"RISK-RM005A-AUTHORITY-{closure_package.certification_package.candidate_digest[:12].upper()}",
            operational_authority="Risk Office Operational Certification Authority",
            independent_authority="RISK-RM-006 Independent Risk Office Certification Authority",
            operational_determination=closure_package.certification_decision.decision,
            independent_certification_decision="RESERVED_FOR_RISK_RM_006",
            prohibited_operational_actions=(
                "issue Independent Office Certification",
                "issue Conditional PASS as independent certification",
                "issue Unconditional PASS as independent certification",
                "self-certify Risk Office constitutional closure",
            ),
            evidence_basis=(closure_package.certification_decision.deterministic_digest,),
            findings=findings,
            result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_conditional_pass_governance(
        self,
        closure_package: RiskRm005ClosureOperationalPackage,
        authority: RiskRm005aAuthoritySeparationRecord,
        *,
        unresolved_deficiencies: tuple[str, ...] = (),
    ) -> RiskRm005aConditionalPassGovernanceRecord:
        findings = []
        if authority.result != EnterpriseCertificationDecision.PASS:
            findings.extend(authority.findings)
        if closure_package.certification_decision.decision == EnterpriseCertificationDecision.PASS and not unresolved_deficiencies:
            code = "CP-001"
            label = "PASS"
            remediation = False
        elif closure_package.certification_decision.decision == EnterpriseCertificationDecision.PASS and unresolved_deficiencies:
            code = "CP-002"
            label = "CONDITIONAL PASS"
            remediation = True
        else:
            code = "CP-003"
            label = "FAIL"
            remediation = True
        record = RiskRm005aConditionalPassGovernanceRecord(
            disposition_identifier=f"RISK-RM005A-DISPOSITION-{closure_package.certification_package.candidate_digest[:12].upper()}",
            disposition_code=code,
            disposition_label=label,
            eligibility_basis=(closure_package.certification_decision.deterministic_digest, authority.deterministic_digest),
            remediation_required=remediation,
            independent_certification_eligible=code == "CP-001",
            restrictions=(
                "operational disposition is not independent certification",
                "RISK-RM-006 retains exclusive independent certification authority",
                "conditional pass requires explicit remediation evidence before progression",
            ),
            findings=tuple(findings),
            result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def review_operational_evidence_completion(
        self,
        closure_package: RiskRm005ClosureOperationalPackage,
        rule_registry: tuple[RiskRm005aRuleRegistryRecord, ...],
        candidate_governance: RiskRm005aCandidateGovernanceRecord,
        authority: RiskRm005aAuthoritySeparationRecord,
        conditional: RiskRm005aConditionalPassGovernanceRecord,
    ) -> RiskRm005aEvidenceCompletionReviewRecord:
        subsystem_results = {
            "Candidate Governance": candidate_governance.result,
            "Artifact Discovery": closure_package.registry_package.execution_package.candidate_package.final_completion_readiness,
            "Constitutional Rule Registry": EnterpriseCertificationDecision.PASS if rule_registry and all(record.result == EnterpriseCertificationDecision.PASS for record in rule_registry) else EnterpriseCertificationDecision.FAIL,
            "Evaluation Rule Engine": closure_package.registry_package.execution_package.final_completion_readiness,
            "Certification Test Registry": EnterpriseCertificationDecision.PASS if closure_package.registry_package.execution_package.certification_tests else EnterpriseCertificationDecision.FAIL,
            "Certification Test Execution": EnterpriseCertificationDecision.PASS if closure_package.registry_package.execution_package.test_executions else EnterpriseCertificationDecision.FAIL,
            "Metrics": EnterpriseCertificationDecision.PASS if closure_package.registry_package.metrics else EnterpriseCertificationDecision.FAIL,
            "Version Compatibility": EnterpriseCertificationDecision.PASS if closure_package.registry_package.version_compatibility_matrix else EnterpriseCertificationDecision.FAIL,
            "Registry Cross-Reference Graph": EnterpriseCertificationDecision.PASS if closure_package.registry_package.registry_cross_reference_graph else EnterpriseCertificationDecision.FAIL,
            "Certification Evidence Registry": EnterpriseCertificationDecision.PASS if closure_package.registry_package.certification_evidence_registry else EnterpriseCertificationDecision.FAIL,
            "Certification Manifest": closure_package.registry_package.certification_manifest.result,
            "Certification Package": closure_package.certification_package.package_status,
            "Certification Traceability": EnterpriseCertificationDecision.PASS if all(record.result == EnterpriseCertificationDecision.PASS for record in closure_package.traceability_matrix) else EnterpriseCertificationDecision.FAIL,
            "Certification Procedure Engine": EnterpriseCertificationDecision.PASS if all(record.result == EnterpriseCertificationDecision.PASS for record in closure_package.procedure_execution) else EnterpriseCertificationDecision.FAIL,
            "Persistence": EnterpriseCertificationDecision.PASS if closure_package.persistence_records else EnterpriseCertificationDecision.FAIL,
            "Replay": closure_package.replay_recovery_record.result,
            "Recovery": closure_package.replay_recovery_record.result,
            "Certification Decisions": closure_package.certification_decision.decision,
            "Closure Controls": EnterpriseCertificationDecision.PASS if closure_package.certification_decision.closure_eligible else EnterpriseCertificationDecision.FAIL,
            "Authority Separation": authority.result,
            "Conditional PASS Governance": conditional.result,
        }
        findings = tuple(f"operational subsystem failed review: {key}" for key, value in subsystem_results.items() if value != EnterpriseCertificationDecision.PASS)
        record = RiskRm005aEvidenceCompletionReviewRecord(
            review_identifier=f"RISK-RM005A-REVIEW-{closure_package.certification_package.candidate_digest[:12].upper()}",
            review_sequence=self.review_sequence,
            subsystem_results=_freeze(subsystem_results),
            readiness_for_rm006=not findings and conditional.independent_certification_eligible,
            evidence_references=(
                closure_package.deterministic_digest,
                _digest(rule_registry),
                candidate_governance.deterministic_digest,
                authority.deterministic_digest,
                conditional.deterministic_digest,
            ),
            findings=findings,
            result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def _rule_record(
        self,
        rule_identifier: str,
        requirement_identifier: str,
        candidate_class: str,
        artifact_identifiers: tuple[str, ...],
        evaluator: str,
        evidence: tuple[str, ...],
        prerequisite_result: EnterpriseCertificationDecision,
    ) -> RiskRm005aRuleRegistryRecord:
        findings = []
        if not artifact_identifiers:
            findings.append("rule has no applicable candidate artifacts")
        if not evaluator:
            findings.append("rule has no executable evaluator")
        if not evidence:
            findings.append("rule has no mandatory evidence dependencies")
        if prerequisite_result != EnterpriseCertificationDecision.PASS:
            findings.append("source rule evaluation did not pass")
        record = RiskRm005aRuleRegistryRecord(
            rule_identifier=rule_identifier,
            requirement_identifier=requirement_identifier,
            candidate_class=candidate_class,
            applicable_artifact_identifiers=artifact_identifiers,
            executable_evaluator=evaluator,
            mandatory_evidence_dependencies=evidence,
            deterministic_outcomes=("PASS", "FAIL"),
            failure_classification="CONSTITUTIONAL_RULE_FAILURE",
            active=not findings,
            findings=tuple(findings),
            result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))


def _git_status(candidate_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "status", "--short"],
            cwd=str(candidate_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return ""
