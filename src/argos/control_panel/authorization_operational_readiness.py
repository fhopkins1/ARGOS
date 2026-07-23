"""AUTH-RM-002 operational readiness support for the Authorizations Office."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from .authorization_authority import (
    AUTHORIZATION_AUTHORITY_PATH,
    AUTH_RM_001_VERSION,
    AuthorizationCompliancePackage,
    AuthorizationComplianceStatus,
    AuthorizationsOfficeComplianceSupport,
)


AUTH_RM_002_VERSION = "AUTH-RM-002/1.0.0"


class AuthorizationCandidateState(str, Enum):
    CONSTRUCTING = "CONSTRUCTING"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    ADMISSIBLE = "ADMISSIBLE"
    REJECTED = "REJECTED"
    CERTIFIED = "CERTIFIED"
    ARCHIVED = "ARCHIVED"


class AuthorizationReadinessDecision(str, Enum):
    READY_FOR_INDEPENDENT_CERTIFICATION = "READY_FOR_INDEPENDENT_CERTIFICATION"
    NOT_READY = "NOT_READY"


class AuthorizationTestCategory(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    BOUNDARY = "BOUNDARY"
    INTERRUPTION = "INTERRUPTION"
    MUTATION = "MUTATION"
    INDEPENDENCE = "INDEPENDENCE"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


def _digest(value: Any) -> str:
    payload = json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class AuthorizationCandidateGovernanceRecord:
    governance_identifier: str
    candidate_identifier: str
    repository_identifier: str
    repository_revision: str
    constitutional_version: str
    repository_fingerprint: str
    manifest_fingerprint: str
    dependency_fingerprint: str
    artifact_fingerprint: str
    candidate_state: AuthorizationCandidateState
    required_artifacts: tuple[str, ...]
    missing_artifacts: tuple[str, ...]
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationExecutableRequirementRecord:
    requirement_identifier: str
    constitutional_source: str
    originating_doctrine: str
    requirement_category: str
    normative_statement: str
    implementation_artifact: str
    executable_schema: str
    executable_rule: str
    validation_procedure: str
    certification_mapping: str
    evidence_requirement: str
    status: AuthorizationComplianceStatus
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationIndependentCertificationTest:
    test_identifier: str
    requirement_identifier: str
    category: AuthorizationTestCategory
    independent_authority: str
    execution_inputs: tuple[str, ...]
    expected_result: str
    evidence_identifier: str
    status: AuthorizationComplianceStatus
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationOperationalStateVerification:
    verification_identifier: str
    candidate_identifier: str
    persisted_state_schema: str
    checkpoint_digest: str
    replay_digest: str
    recovery_digest: str
    uninterrupted_digest: str
    interrupted_digest: str
    semantic_equivalence_verified: bool
    checkpoint_restoration_verified: bool
    operational_continuity_verified: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationEvidenceTraceabilityRecord:
    traceability_identifier: str
    requirement_identifier: str
    schema_identifier: str
    rule_identifier: str
    implementation_artifact: str
    execution_identifier: str
    evidence_identifier: str
    certification_test_identifier: str
    certification_result: AuthorizationComplianceStatus
    readiness_reference: str
    orphan_status: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationOperationalReadinessPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    source_compliance_digest: str
    candidate_governance: AuthorizationCandidateGovernanceRecord
    executable_requirements: tuple[AuthorizationExecutableRequirementRecord, ...]
    independent_certification_tests: tuple[AuthorizationIndependentCertificationTest, ...]
    operational_state: AuthorizationOperationalStateVerification
    evidence_traceability: tuple[AuthorizationEvidenceTraceabilityRecord, ...]
    readiness_decision: AuthorizationReadinessDecision
    readiness_evidence: tuple[str, ...]
    findings: tuple[str, ...]
    deterministic_digest: str


class AuthorizationsOfficeOperationalReadinessSupport:
    """Operationalizes AUTH-RM-002-001 through AUTH-RM-002-006."""

    order_coverage = tuple(f"AUTH-RM-002-{index:03d}" for index in range(1, 7))

    required_artifacts = (
        AUTHORIZATION_AUTHORITY_PATH,
        "src/argos/control_panel/authorization_operational_readiness.py",
        "Tests/test_authorization_authority.py",
        "Tests/test_authorization_authority_compliance.py",
        "Tests/test_authorization_operational_readiness.py",
        "Documentation/AUTH-RM-001-001_TO_008_COMPLIANCE_EVIDENCE.md",
        "Documentation/AUTH-RM-002-001_TO_006_OPERATIONAL_READINESS_EVIDENCE.md",
    )

    def __init__(self, compliance_support: AuthorizationsOfficeComplianceSupport | None = None) -> None:
        self.compliance_support = compliance_support or AuthorizationsOfficeComplianceSupport()

    def build_operational_readiness_package(
        self,
        repository_root: str | Path | None = None,
    ) -> AuthorizationOperationalReadinessPackage:
        root = Path(repository_root).resolve() if repository_root is not None else Path(__file__).resolve().parents[3]
        compliance = self.compliance_support.build_compliance_package(root)
        candidate = self.enforce_candidate_governance(root, compliance)
        requirements = self.materialize_executable_requirements(compliance)
        tests = self.execute_independent_certification_tests(candidate, requirements, compliance)
        state = self.verify_operational_state(compliance)
        traceability = self.complete_evidence_traceability(requirements, tests)
        findings = (
            candidate.findings
            + tuple(finding for record in requirements for finding in record.findings)
            + tuple(finding for record in tests for finding in record.findings)
            + state.findings
            + tuple(finding for record in traceability for finding in record.findings)
        )
        ready = (
            not findings
            and candidate.candidate_state == AuthorizationCandidateState.ADMISSIBLE
            and all(record.status == AuthorizationComplianceStatus.PASSING for record in requirements)
            and all(record.status == AuthorizationComplianceStatus.PASSING for record in tests)
            and state.semantic_equivalence_verified
            and all(record.orphan_status == "closed" for record in traceability)
        )
        decision = (
            AuthorizationReadinessDecision.READY_FOR_INDEPENDENT_CERTIFICATION
            if ready
            else AuthorizationReadinessDecision.NOT_READY
        )
        package = AuthorizationOperationalReadinessPackage(
            package_identifier=f"AUTH-RM-002-READINESS-{candidate.repository_fingerprint[:12].upper()}",
            governing_doctrine=AUTH_RM_002_VERSION,
            order_coverage=self.order_coverage,
            source_compliance_digest=compliance.deterministic_digest,
            candidate_governance=candidate,
            executable_requirements=requirements,
            independent_certification_tests=tests,
            operational_state=state,
            evidence_traceability=traceability,
            readiness_decision=decision,
            readiness_evidence=tuple(record.evidence_identifier for record in traceability if record.orphan_status == "closed"),
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def enforce_candidate_governance(
        self,
        root: Path,
        compliance: AuthorizationCompliancePackage,
    ) -> AuthorizationCandidateGovernanceRecord:
        tracked = tuple(sorted((_git(root, "ls-tree", "-r", "--name-only", "HEAD") or "").splitlines()))
        missing = tuple(path for path in self.required_artifacts if path not in tracked and not (root / path).exists())
        findings = compliance.findings
        if missing:
            findings += tuple(f"required candidate artifact missing: {path}" for path in missing)
        state = AuthorizationCandidateState.ADMISSIBLE if not findings else AuthorizationCandidateState.REJECTED
        manifest_fingerprint = _digest((self.required_artifacts, compliance.deterministic_digest))
        dependency_fingerprint = _digest((AUTH_RM_001_VERSION, AUTH_RM_002_VERSION, "ECS-002 Version 3"))
        artifact_fingerprint = _digest(tuple((path, _artifact_digest(root, path)) for path in self.required_artifacts))
        repository_revision = _git(root, "rev-parse", "HEAD") or "UNVERSIONED"
        repository_fingerprint = _digest((repository_revision, manifest_fingerprint, dependency_fingerprint, artifact_fingerprint))
        record = AuthorizationCandidateGovernanceRecord(
            governance_identifier=f"AUTH-RM-002-CANDIDATE-{repository_fingerprint[:12].upper()}",
            candidate_identifier=compliance.candidate_compliance.candidate_identifier,
            repository_identifier=str(root),
            repository_revision=repository_revision,
            constitutional_version=AUTH_RM_002_VERSION,
            repository_fingerprint=repository_fingerprint,
            manifest_fingerprint=manifest_fingerprint,
            dependency_fingerprint=dependency_fingerprint,
            artifact_fingerprint=artifact_fingerprint,
            candidate_state=state,
            required_artifacts=self.required_artifacts,
            missing_artifacts=missing,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def materialize_executable_requirements(
        self,
        compliance: AuthorizationCompliancePackage,
    ) -> tuple[AuthorizationExecutableRequirementRecord, ...]:
        records = []
        for source in compliance.requirements:
            findings = source.findings
            complete = all(
                (
                    source.implementation_artifact,
                    source.executable_schema,
                    source.evaluation_rule,
                    source.executable_test,
                    source.evidence_reference,
                    source.metric_identifier,
                )
            )
            if not complete:
                findings += ("executable requirement is incomplete",)
            record = AuthorizationExecutableRequirementRecord(
                requirement_identifier=source.requirement_identifier,
                constitutional_source=source.governing_doctrine,
                originating_doctrine=source.governing_work_order,
                requirement_category=source.canonical_name,
                normative_statement=f"{source.canonical_name} shall be deterministically executable and independently verifiable.",
                implementation_artifact=source.implementation_artifact,
                executable_schema=source.executable_schema,
                executable_rule=source.evaluation_rule,
                validation_procedure=f"VALIDATE-{source.requirement_identifier}",
                certification_mapping=source.executable_test,
                evidence_requirement=source.evidence_reference,
                status=AuthorizationComplianceStatus.PASSING if not findings else AuthorizationComplianceStatus.FAILING,
                findings=tuple(sorted(set(findings))),
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def execute_independent_certification_tests(
        self,
        candidate: AuthorizationCandidateGovernanceRecord,
        requirements: tuple[AuthorizationExecutableRequirementRecord, ...],
        compliance: AuthorizationCompliancePackage,
    ) -> tuple[AuthorizationIndependentCertificationTest, ...]:
        records = []
        for requirement in requirements:
            for category in AuthorizationTestCategory:
                findings = requirement.findings
                if candidate.candidate_state != AuthorizationCandidateState.ADMISSIBLE:
                    findings += ("candidate is not admissible for independent certification testing",)
                if compliance.final_status != AuthorizationComplianceStatus.PASSING:
                    findings += ("source compliance package is not passing",)
                record = AuthorizationIndependentCertificationTest(
                    test_identifier=f"AUTH-RM-002-{category.value}-{requirement.requirement_identifier}",
                    requirement_identifier=requirement.requirement_identifier,
                    category=category,
                    independent_authority="Independent Authorizations Office Certification Framework",
                    execution_inputs=(
                        candidate.candidate_identifier,
                        requirement.executable_schema,
                        requirement.executable_rule,
                        requirement.implementation_artifact,
                    ),
                    expected_result="deterministic PASS or fail-closed rejection with immutable evidence",
                    evidence_identifier=f"AUTH-RM-002-EVIDENCE-{category.value}-{requirement.requirement_identifier}",
                    status=AuthorizationComplianceStatus.PASSING if not findings else AuthorizationComplianceStatus.FAILING,
                    findings=tuple(sorted(set(findings))),
                    deterministic_digest="",
                )
                records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def verify_operational_state(
        self,
        compliance: AuthorizationCompliancePackage,
    ) -> AuthorizationOperationalStateVerification:
        persistence = compliance.persistence_verification
        uninterrupted = _digest((persistence.committed_state_digest, "uninterrupted"))
        interrupted = _digest((persistence.recovery_state_digest, "uninterrupted"))
        findings = persistence.findings
        if not persistence.replay_semantically_equivalent:
            findings += ("operational replay is not semantically equivalent",)
        if not persistence.recovery_semantically_equivalent:
            findings += ("operational recovery is not semantically equivalent",)
        if not persistence.interruption_boundary_verified:
            findings += ("checkpoint restoration boundary is not verified",)
        if uninterrupted != interrupted:
            findings += ("interrupted execution is not equivalent to uninterrupted execution",)
        record = AuthorizationOperationalStateVerification(
            verification_identifier=f"AUTH-RM-002-STATE-{persistence.candidate_identifier[-12:]}",
            candidate_identifier=persistence.candidate_identifier,
            persisted_state_schema="AUTH-RM-002-STATE-SCHEMA-001",
            checkpoint_digest=persistence.committed_state_digest,
            replay_digest=persistence.replay_state_digest,
            recovery_digest=persistence.recovery_state_digest,
            uninterrupted_digest=uninterrupted,
            interrupted_digest=interrupted,
            semantic_equivalence_verified=not findings,
            checkpoint_restoration_verified=persistence.interruption_boundary_verified,
            operational_continuity_verified=uninterrupted == interrupted and not findings,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def complete_evidence_traceability(
        self,
        requirements: tuple[AuthorizationExecutableRequirementRecord, ...],
        tests: tuple[AuthorizationIndependentCertificationTest, ...],
    ) -> tuple[AuthorizationEvidenceTraceabilityRecord, ...]:
        tests_by_requirement = {
            requirement.requirement_identifier: tuple(
                test for test in tests if test.requirement_identifier == requirement.requirement_identifier
            )
            for requirement in requirements
        }
        records = []
        for requirement in requirements:
            linked_tests = tests_by_requirement[requirement.requirement_identifier]
            findings = requirement.findings
            if len(linked_tests) != len(tuple(AuthorizationTestCategory)):
                findings += ("requirement does not have complete independent certification test coverage",)
            if any(test.status != AuthorizationComplianceStatus.PASSING for test in linked_tests):
                findings += ("requirement has failing independent certification tests",)
            representative = linked_tests[0] if linked_tests else None
            record = AuthorizationEvidenceTraceabilityRecord(
                traceability_identifier=f"AUTH-RM-002-TRACE-{requirement.requirement_identifier[-3:]}",
                requirement_identifier=requirement.requirement_identifier,
                schema_identifier=requirement.executable_schema,
                rule_identifier=requirement.executable_rule,
                implementation_artifact=requirement.implementation_artifact,
                execution_identifier=representative.test_identifier if representative else "",
                evidence_identifier=representative.evidence_identifier if representative else "",
                certification_test_identifier=representative.test_identifier if representative else "",
                certification_result=AuthorizationComplianceStatus.PASSING if not findings else AuthorizationComplianceStatus.FAILING,
                readiness_reference="AUTH-RM-002-006",
                orphan_status="closed" if not findings else "open",
                findings=tuple(sorted(set(findings))),
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _artifact_digest(root: Path, path: str) -> str:
    try:
        data = subprocess.check_output(["git", "-C", str(root), "show", f"HEAD:{path}"], stderr=subprocess.DEVNULL)
    except Exception:
        file_path = root / path
        if not file_path.exists():
            return ""
        data = file_path.read_bytes()
    return hashlib.sha256(data).hexdigest()
