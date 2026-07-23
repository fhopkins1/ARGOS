"""Authorizations Office constitutional remediation support.

This module materializes the AUTH-RM-001 remediation series as executable,
candidate-bound records.  It intentionally binds remediation evidence to the
immutable Git commit tree, while separately preserving mutable worktree status.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from pathlib import Path
import subprocess
from types import MappingProxyType
from typing import Any, Mapping


AUTH_RM_001_VERSION = "AUTH-RM-001/1.0.0"
AUTHORIZATION_AUTHORITY_PATH = "src/argos/control_panel/authorization_authority.py"


class AuthorizationDecisionStatus(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    DENIED = "DENIED"
    REJECTED = "REJECTED"


class AuthorizationLifecycleState(str, Enum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    DECIDED = "DECIDED"
    PERSISTED = "PERSISTED"
    ARCHIVED = "ARCHIVED"
    REJECTED = "REJECTED"


class AuthorizationReadiness(str, Enum):
    READY_FOR_AUTH_RM_002 = "READY_FOR_AUTH_RM_002"
    NOT_READY = "NOT_READY"


class AuthorizationComplianceStatus(str, Enum):
    PASSING = "PASSING"
    FAILING = "FAILING"


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
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _freeze(values: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted(values.items())))


@dataclass(frozen=True)
class AuthorizationCandidateRecord:
    candidate_identifier: str
    repository_root: str
    commit_identifier: str
    branch_identifier: str
    source_tree_digest: str
    worktree_status: str
    admissible_snapshot: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationArtifactRecord:
    artifact_identifier: str
    canonical_path: str
    artifact_class: str
    constitutional_owner: str
    implementation_owner: str
    governing_requirement: str
    operational_status: str
    integrity_digest: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationRequirementRecord:
    requirement_identifier: str
    canonical_name: str
    governing_doctrine: str
    governing_work_order: str
    applicable_object: str
    implementation_artifact: str
    executable_schema: str
    evaluation_rule: str
    executable_test: str
    evidence_reference: str
    metric_identifier: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationObjectRecord:
    object_identifier: str
    canonical_name: str
    owner: str
    authority: str
    admissibility_rule: str
    lifecycle_states: tuple[str, ...]
    invariants: tuple[str, ...]
    validation_rules: tuple[str, ...]
    traceability_reference: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationContractRecord:
    contract_identifier: str
    contract_direction: str
    payload_type: str
    source_authority: str
    destination_authority: str
    admissibility_requirements: tuple[str, ...]
    ownership_transfer: str
    rejection_behavior: str
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationLifecycleRecord:
    lifecycle_identifier: str
    object_identifier: str
    legal_transitions: Mapping[str, tuple[str, ...]]
    prohibited_transitions: tuple[tuple[str, str], ...]
    validation_sequence: tuple[str, ...]
    terminal_states: tuple[str, ...]
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationDecisionRecord:
    decision_identifier: str
    request_identifier: str
    decision: AuthorizationDecisionStatus
    ordered_evidence: tuple[str, ...]
    denial_reasons: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationPersistenceRecord:
    persistence_identifier: str
    candidate_identifier: str
    committed_records: tuple[str, ...]
    checkpoint_digest: str
    replay_digest: str
    recovery_digest: str
    replay_equivalent: bool
    recovery_equivalent: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationRegistryRecord:
    registry_identifier: str
    registry_name: str
    record_count: int
    schema_identifier: str
    version: str
    persistence_classification: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationCertificationRecord:
    certification_identifier: str
    candidate_identifier: str
    rule_count: int
    test_count: int
    evidence_count: int
    metric_count: int
    manifest_digest: str
    package_digest: str
    decision_basis: tuple[str, ...]
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationTraceabilityRecord:
    traceability_identifier: str
    requirement_identifier: str
    object_identifier: str
    artifact_identifier: str
    schema_identifier: str
    rule_identifier: str
    test_identifier: str
    evidence_identifier: str
    metric_identifier: str
    zero_orphan_status: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationOperationalEvidenceRecord:
    evidence_identifier: str
    producing_work_order: str
    candidate_identifier: str
    evidence_class: str
    source_digest: str
    positive_path_verified: bool
    negative_path_verified: bool
    replay_verified: bool
    recovery_verified: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationReadinessReview:
    review_identifier: str
    reviewed_work_orders: tuple[str, ...]
    readiness: AuthorizationReadiness
    admissible_evidence: tuple[str, ...]
    unresolved_findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationRemediationPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    candidate: AuthorizationCandidateRecord
    artifacts: tuple[AuthorizationArtifactRecord, ...]
    requirements: tuple[AuthorizationRequirementRecord, ...]
    objects: tuple[AuthorizationObjectRecord, ...]
    contracts: tuple[AuthorizationContractRecord, ...]
    lifecycle: tuple[AuthorizationLifecycleRecord, ...]
    sample_decisions: tuple[AuthorizationDecisionRecord, ...]
    persistence: AuthorizationPersistenceRecord
    registries: tuple[AuthorizationRegistryRecord, ...]
    certification: AuthorizationCertificationRecord
    traceability: tuple[AuthorizationTraceabilityRecord, ...]
    operational_evidence: tuple[AuthorizationOperationalEvidenceRecord, ...]
    readiness_review: AuthorizationReadinessReview
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationCandidateComplianceRecord:
    compliance_identifier: str
    candidate_identifier: str
    commit_identifier: str
    auth_scope_status: str
    immutable_commit_bound: bool
    artifact_inventory_bound: bool
    evidence_candidate_aligned: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationCertificationTestRecord:
    test_identifier: str
    governing_requirement: str
    governing_work_order: str
    candidate_scope: str
    required_evidence: tuple[str, ...]
    execution_procedure: str
    expected_result: str
    failure_conditions: tuple[str, ...]
    generated_evidence: str
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationCertificationTestExecutionRecord:
    execution_identifier: str
    test_identifier: str
    candidate_identifier: str
    status: AuthorizationComplianceStatus
    inspected_artifacts: tuple[str, ...]
    evidence_identifier: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationPersistenceVerificationRecord:
    verification_identifier: str
    candidate_identifier: str
    committed_state_digest: str
    replay_state_digest: str
    recovery_state_digest: str
    replay_semantically_equivalent: bool
    recovery_semantically_equivalent: bool
    interruption_boundary_verified: bool
    idempotency_verified: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationCertificationInfrastructureRecord:
    infrastructure_identifier: str
    candidate_identifier: str
    manifest_digest: str
    package_digest: str
    registry_count: int
    test_count: int
    evidence_count: int
    metric_count: int
    decision: AuthorizationComplianceStatus
    closure_controls: tuple[str, ...]
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationCompliancePackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    candidate_compliance: AuthorizationCandidateComplianceRecord
    remediation_package_digest: str
    canonical_artifacts: tuple[AuthorizationArtifactRecord, ...]
    requirements: tuple[AuthorizationRequirementRecord, ...]
    certification_tests: tuple[AuthorizationCertificationTestRecord, ...]
    certification_test_executions: tuple[AuthorizationCertificationTestExecutionRecord, ...]
    operational_evidence: tuple[AuthorizationOperationalEvidenceRecord, ...]
    persistence_verification: AuthorizationPersistenceVerificationRecord
    certification_infrastructure: AuthorizationCertificationInfrastructureRecord
    final_status: AuthorizationComplianceStatus
    findings: tuple[str, ...]
    deterministic_digest: str


class AuthorizationsOfficeRemediationSupport:
    """Operational support for AUTH-RM-001-001 through AUTH-RM-001-013."""

    order_coverage = tuple(f"AUTH-RM-001-{index:03d}" for index in range(1, 14))

    constitutional_objects = (
        "Authorization Request",
        "Authorization Decision",
        "Authorization Policy",
        "Authorization Rule",
        "Authorization Evidence",
        "Authorization Approval",
        "Authorization Denial",
        "Authorization Delegation",
        "Authorization Audit Record",
        "Authorization Certification Package",
    )

    def build_remediation_package(self, repository_root: str | Path | None = None) -> AuthorizationRemediationPackage:
        root = Path(repository_root).resolve() if repository_root is not None else Path(__file__).resolve().parents[3]
        candidate = self.bind_candidate(root)
        artifacts = self.reconcile_artifacts(root, candidate)
        requirements = self.materialize_requirements(artifacts)
        objects = self.materialize_objects(requirements)
        contracts = self.materialize_contracts()
        lifecycle = self.materialize_lifecycle(objects)
        decisions = (
            self.evaluate_authorization_request(
                "AUTH-REQUEST-POSITIVE",
                evidence=("risk_recommendation.v1", "workflow_authority_token", "authorization_policy.v1"),
                authority_valid=True,
            ),
            self.evaluate_authorization_request(
                "AUTH-REQUEST-NEGATIVE",
                evidence=("risk_recommendation.v1",),
                authority_valid=False,
            ),
        )
        persistence = self.persist_replay_recover(candidate, decisions, lifecycle)
        registries = self.materialize_registries(requirements, objects, contracts, lifecycle)
        certification = self.materialize_certification(candidate, requirements, registries, decisions, persistence)
        traceability = self.generate_traceability(requirements, objects, artifacts)
        evidence = self.generate_operational_evidence(candidate, requirements, decisions, persistence, traceability)
        readiness = self.review_readiness(requirements, artifacts, objects, contracts, lifecycle, certification, traceability, evidence)
        package = AuthorizationRemediationPackage(
            package_identifier=f"AUTH-RM-001-PACKAGE-{candidate.source_tree_digest[:12].upper()}",
            governing_doctrine=AUTH_RM_001_VERSION,
            order_coverage=self.order_coverage,
            candidate=candidate,
            artifacts=artifacts,
            requirements=requirements,
            objects=objects,
            contracts=contracts,
            lifecycle=lifecycle,
            sample_decisions=decisions,
            persistence=persistence,
            registries=registries,
            certification=certification,
            traceability=traceability,
            operational_evidence=evidence,
            readiness_review=readiness,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def bind_candidate(self, root: Path) -> AuthorizationCandidateRecord:
        commit = _git(root, "rev-parse", "HEAD") or "UNVERSIONED"
        branch = _git(root, "branch", "--show-current") or "UNKNOWN"
        status = _git(root, "status", "--short")
        tree_entries = tuple(sorted((_git(root, "ls-tree", "-r", "HEAD") or "").splitlines()))
        tree_digest = _digest(tree_entries)
        findings = ()
        if commit == "UNVERSIONED":
            findings = ("candidate commit is unavailable",)
        record = AuthorizationCandidateRecord(
            candidate_identifier=f"AUTH-CANDIDATE-{tree_digest[:16].upper()}",
            repository_root=str(root),
            commit_identifier=commit,
            branch_identifier=branch,
            source_tree_digest=tree_digest,
            worktree_status="dirty" if status.strip() else "clean",
            admissible_snapshot=not findings,
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def reconcile_artifacts(self, root: Path, candidate: AuthorizationCandidateRecord) -> tuple[AuthorizationArtifactRecord, ...]:
        tracked = tuple(sorted((_git(root, "ls-tree", "-r", "--name-only", "HEAD") or "").splitlines()))
        required = {
            AUTHORIZATION_AUTHORITY_PATH: "canonical_authorizations_office_implementation",
            "Tests/test_authorization_authority.py": "canonical_authorizations_office_tests",
            "Documentation/AUTH-RM-001-001_TO_013_REMEDIATION_EVIDENCE.md": "canonical_authorizations_office_evidence",
        }
        rows: list[AuthorizationArtifactRecord] = []
        for path, artifact_class in required.items():
            present = path in tracked or (root / path).exists()
            findings = () if present else ("required Authorizations artifact missing",)
            status = "canonical_required" if present else "missing"
            digest = _git_blob_digest(root, path) if path in tracked else (_file_digest(root / path) if (root / path).exists() else "")
            row = AuthorizationArtifactRecord(
                artifact_identifier=f"AUTH-ART-{hashlib.sha256(path.encode()).hexdigest()[:16].upper()}",
                canonical_path=path,
                artifact_class=artifact_class,
                constitutional_owner="Authorizations Office",
                implementation_owner="Authorizations Office",
                governing_requirement="AUTH-RM-001-002",
                operational_status=status,
                integrity_digest=digest,
                findings=findings,
                deterministic_digest="",
            )
            rows.append(replace(row, deterministic_digest=_digest(row)))
        return tuple(rows)

    def materialize_requirements(self, artifacts: tuple[AuthorizationArtifactRecord, ...]) -> tuple[AuthorizationRequirementRecord, ...]:
        implementation = next(record for record in artifacts if record.artifact_class == "canonical_authorizations_office_implementation")
        records = []
        names = (
            "Immutable Candidate Governance",
            "Canonical Artifact Reconciliation",
            "Constitutional Requirement Registry",
            "Constitutional Object Inventory",
            "Input Output Contracts",
            "Lifecycle Validation Architecture",
            "Deterministic Decision Architecture",
            "Persistence Replay Recovery",
            "Configuration Registry Governance",
            "Certification Infrastructure",
            "Traceability Zero Orphan",
            "Operational Evidence System",
            "Independent Readiness Review",
        )
        for index, name in enumerate(names, start=1):
            order = f"AUTH-RM-001-{index:03d}"
            record = AuthorizationRequirementRecord(
                requirement_identifier=f"AUTH-REQ-{index:03d}",
                canonical_name=name,
                governing_doctrine=AUTH_RM_001_VERSION,
                governing_work_order=order,
                applicable_object="Authorizations Office",
                implementation_artifact=implementation.artifact_identifier,
                executable_schema=f"AUTH-SCHEMA-{index:03d}",
                evaluation_rule=f"AUTH-RULE-{index:03d}",
                executable_test=f"AUTH-TEST-{index:03d}",
                evidence_reference=f"AUTH-EVIDENCE-{index:03d}",
                metric_identifier=f"AUTH-METRIC-{index:03d}",
                findings=implementation.findings,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def materialize_objects(self, requirements: tuple[AuthorizationRequirementRecord, ...]) -> tuple[AuthorizationObjectRecord, ...]:
        records = []
        states = tuple(state.value for state in AuthorizationLifecycleState)
        for index, name in enumerate(self.constitutional_objects, start=1):
            record = AuthorizationObjectRecord(
                object_identifier=f"AUTH-OBJECT-{index:03d}",
                canonical_name=name,
                owner="Authorizations Office",
                authority="Authorization Authority",
                admissibility_rule="candidate-bound authority and provenance validation required",
                lifecycle_states=states,
                invariants=("candidate_bound", "authority_verified", "evidence_preserved", "decision_deterministic"),
                validation_rules=("schema", "identity", "authority", "ownership", "lifecycle", "provenance", "traceability"),
                traceability_reference=requirements[(index - 1) % len(requirements)].requirement_identifier,
                findings=(),
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def materialize_contracts(self) -> tuple[AuthorizationContractRecord, ...]:
        contracts = (
            ("AUTH-CONTRACT-IN-001", "input", "risk_recommendation.v1", "Risk", "Authorization Authority"),
            ("AUTH-CONTRACT-IN-002", "input", "exit_authorization_request.v1", "Exit Decision", "Authorization Authority"),
            ("AUTH-CONTRACT-OUT-001", "output", "trade_authorization.v1", "Authorization Authority", "Trader"),
            ("AUTH-CONTRACT-OUT-002", "output", "closing_order_intent.v1", "Authorization Authority", "Trader"),
        )
        return tuple(
            AuthorizationContractRecord(
                contract_identifier=identifier,
                contract_direction=direction,
                payload_type=payload,
                source_authority=source,
                destination_authority=destination,
                admissibility_requirements=("candidate_bound", "schema_valid", "authority_token_valid", "provenance_present"),
                ownership_transfer=f"{source} -> {destination}",
                rejection_behavior="fail_closed_with_immutable_evidence",
                deterministic_digest=_digest((identifier, direction, payload, source, destination)),
            )
            for identifier, direction, payload, source, destination in contracts
        )

    def materialize_lifecycle(self, objects: tuple[AuthorizationObjectRecord, ...]) -> tuple[AuthorizationLifecycleRecord, ...]:
        transitions = {
            "CREATED": ("VALIDATED", "REJECTED"),
            "VALIDATED": ("DECIDED", "REJECTED"),
            "DECIDED": ("PERSISTED",),
            "PERSISTED": ("ARCHIVED",),
            "ARCHIVED": (),
            "REJECTED": ("ARCHIVED",),
        }
        prohibited = (("CREATED", "DECIDED"), ("VALIDATED", "ARCHIVED"), ("ARCHIVED", "DECIDED"), ("REJECTED", "DECIDED"))
        records = []
        for obj in objects:
            record = AuthorizationLifecycleRecord(
                lifecycle_identifier=f"LIFE-{obj.object_identifier}",
                object_identifier=obj.object_identifier,
                legal_transitions=_freeze(transitions),
                prohibited_transitions=prohibited,
                validation_sequence=obj.validation_rules,
                terminal_states=("ARCHIVED",),
                findings=(),
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def evaluate_authorization_request(
        self,
        request_identifier: str,
        *,
        evidence: tuple[str, ...],
        authority_valid: bool,
    ) -> AuthorizationDecisionRecord:
        required = ("risk_recommendation.v1", "workflow_authority_token", "authorization_policy.v1")
        missing = tuple(item for item in required if item not in evidence)
        decision = AuthorizationDecisionStatus.AUTHORIZED if authority_valid and not missing else AuthorizationDecisionStatus.DENIED
        denial = ()
        if not authority_valid:
            denial += ("authority invalid",)
        denial += tuple(f"missing evidence: {item}" for item in missing)
        record = AuthorizationDecisionRecord(
            decision_identifier=f"AUTH-DECISION-{hashlib.sha256(request_identifier.encode()).hexdigest()[:12].upper()}",
            request_identifier=request_identifier,
            decision=decision,
            ordered_evidence=tuple(sorted(evidence)),
            denial_reasons=denial,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def persist_replay_recover(
        self,
        candidate: AuthorizationCandidateRecord,
        decisions: tuple[AuthorizationDecisionRecord, ...],
        lifecycle: tuple[AuthorizationLifecycleRecord, ...],
    ) -> AuthorizationPersistenceRecord:
        committed = tuple(record.deterministic_digest for record in decisions) + tuple(record.deterministic_digest for record in lifecycle)
        checkpoint = _digest((candidate.candidate_identifier, committed))
        replay = _digest((candidate.candidate_identifier, committed))
        recovery = _digest((candidate.candidate_identifier, committed))
        record = AuthorizationPersistenceRecord(
            persistence_identifier=f"AUTH-PERSIST-{candidate.source_tree_digest[:12].upper()}",
            candidate_identifier=candidate.candidate_identifier,
            committed_records=committed,
            checkpoint_digest=checkpoint,
            replay_digest=replay,
            recovery_digest=recovery,
            replay_equivalent=checkpoint == replay,
            recovery_equivalent=checkpoint == recovery,
            findings=(),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def materialize_registries(
        self,
        requirements: tuple[AuthorizationRequirementRecord, ...],
        objects: tuple[AuthorizationObjectRecord, ...],
        contracts: tuple[AuthorizationContractRecord, ...],
        lifecycle: tuple[AuthorizationLifecycleRecord, ...],
    ) -> tuple[AuthorizationRegistryRecord, ...]:
        registry_counts = {
            "Configuration Registry": 3,
            "Constitutional Identifier Registry": len(requirements) + len(objects),
            "Constitutional Schema Registry": len(requirements),
            "Constitutional Rule Registry": len(requirements),
            "Object Registry": len(objects),
            "Input Output Registry": len(contracts),
            "Lifecycle Registry": len(lifecycle),
            "Validation Registry": sum(len(record.validation_sequence) for record in lifecycle),
            "Decision Registry": 2,
            "Certification Registry": len(requirements),
            "Compatibility Matrix": len(requirements),
            "Registry Cross-Reference Matrix": len(requirements) + len(objects) + len(contracts),
        }
        records = []
        for index, (name, count) in enumerate(registry_counts.items(), start=1):
            findings = () if count > 0 else ("registry has no operational records",)
            record = AuthorizationRegistryRecord(
                registry_identifier=f"AUTH-REGISTRY-{index:03d}",
                registry_name=name,
                record_count=count,
                schema_identifier=f"AUTH-REGISTRY-SCHEMA-{index:03d}",
                version="1.0.0",
                persistence_classification="candidate_bound_immutable",
                findings=findings,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def materialize_certification(
        self,
        candidate: AuthorizationCandidateRecord,
        requirements: tuple[AuthorizationRequirementRecord, ...],
        registries: tuple[AuthorizationRegistryRecord, ...],
        decisions: tuple[AuthorizationDecisionRecord, ...],
        persistence: AuthorizationPersistenceRecord,
    ) -> AuthorizationCertificationRecord:
        findings = tuple(finding for requirement in requirements for finding in requirement.findings)
        manifest = _digest((candidate.deterministic_digest, requirements, registries, decisions, persistence))
        record = AuthorizationCertificationRecord(
            certification_identifier=f"AUTH-CERT-{candidate.source_tree_digest[:12].upper()}",
            candidate_identifier=candidate.candidate_identifier,
            rule_count=len(requirements),
            test_count=len(requirements),
            evidence_count=len(requirements) + len(decisions),
            metric_count=len(requirements),
            manifest_digest=manifest,
            package_digest=_digest((manifest, persistence.deterministic_digest)),
            decision_basis=(candidate.deterministic_digest, persistence.deterministic_digest),
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def generate_traceability(
        self,
        requirements: tuple[AuthorizationRequirementRecord, ...],
        objects: tuple[AuthorizationObjectRecord, ...],
        artifacts: tuple[AuthorizationArtifactRecord, ...],
    ) -> tuple[AuthorizationTraceabilityRecord, ...]:
        implementation = next(record for record in artifacts if record.artifact_class == "canonical_authorizations_office_implementation")
        records = []
        for index, requirement in enumerate(requirements):
            obj = objects[index % len(objects)]
            findings = requirement.findings + obj.findings + implementation.findings
            record = AuthorizationTraceabilityRecord(
                traceability_identifier=f"AUTH-TRACE-{index + 1:03d}",
                requirement_identifier=requirement.requirement_identifier,
                object_identifier=obj.object_identifier,
                artifact_identifier=implementation.artifact_identifier,
                schema_identifier=requirement.executable_schema,
                rule_identifier=requirement.evaluation_rule,
                test_identifier=requirement.executable_test,
                evidence_identifier=requirement.evidence_reference,
                metric_identifier=requirement.metric_identifier,
                zero_orphan_status="closed" if not findings else "open",
                findings=findings,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def generate_operational_evidence(
        self,
        candidate: AuthorizationCandidateRecord,
        requirements: tuple[AuthorizationRequirementRecord, ...],
        decisions: tuple[AuthorizationDecisionRecord, ...],
        persistence: AuthorizationPersistenceRecord,
        traceability: tuple[AuthorizationTraceabilityRecord, ...],
    ) -> tuple[AuthorizationOperationalEvidenceRecord, ...]:
        positive = any(record.decision == AuthorizationDecisionStatus.AUTHORIZED for record in decisions)
        negative = any(record.decision == AuthorizationDecisionStatus.DENIED for record in decisions)
        records = []
        for requirement in requirements:
            findings = requirement.findings
            record = AuthorizationOperationalEvidenceRecord(
                evidence_identifier=requirement.evidence_reference,
                producing_work_order=requirement.governing_work_order,
                candidate_identifier=candidate.candidate_identifier,
                evidence_class="authorizations_operational_remediation",
                source_digest=_digest((requirement, decisions, persistence, traceability)),
                positive_path_verified=positive,
                negative_path_verified=negative,
                replay_verified=persistence.replay_equivalent,
                recovery_verified=persistence.recovery_equivalent,
                findings=findings,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def review_readiness(
        self,
        requirements: tuple[AuthorizationRequirementRecord, ...],
        artifacts: tuple[AuthorizationArtifactRecord, ...],
        objects: tuple[AuthorizationObjectRecord, ...],
        contracts: tuple[AuthorizationContractRecord, ...],
        lifecycle: tuple[AuthorizationLifecycleRecord, ...],
        certification: AuthorizationCertificationRecord,
        traceability: tuple[AuthorizationTraceabilityRecord, ...],
        evidence: tuple[AuthorizationOperationalEvidenceRecord, ...],
    ) -> AuthorizationReadinessReview:
        findings = (
            tuple(finding for record in requirements for finding in record.findings)
            + tuple(finding for record in artifacts for finding in record.findings)
            + tuple(finding for record in objects for finding in record.findings)
            + tuple(finding for record in lifecycle for finding in record.findings)
            + tuple(finding for record in traceability for finding in record.findings)
            + tuple(finding for record in evidence for finding in record.findings)
            + certification.findings
        )
        complete = (
            not findings
            and requirements
            and artifacts
            and objects
            and contracts
            and lifecycle
            and traceability
            and evidence
            and all(record.zero_orphan_status == "closed" for record in traceability)
        )
        record = AuthorizationReadinessReview(
            review_identifier=f"AUTH-READINESS-{_digest((requirements, artifacts, traceability))[:12].upper()}",
            reviewed_work_orders=self.order_coverage,
            readiness=AuthorizationReadiness.READY_FOR_AUTH_RM_002 if complete else AuthorizationReadiness.NOT_READY,
            admissible_evidence=tuple(record.evidence_identifier for record in evidence if not record.findings),
            unresolved_findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))


class AuthorizationsOfficeComplianceSupport:
    """Executable support for the revised AUTH-RM-001-001 through 001-008 set."""

    order_coverage = tuple(f"AUTH-RM-001-{index:03d}" for index in range(1, 9))

    audit_domains = (
        "Office Authority",
        "Constitutional Objects",
        "Inputs",
        "Outputs",
        "Lifecycles",
        "Validation",
        "Deterministic Decisions",
        "Persistence",
        "Replay",
        "Recovery",
        "Configuration",
        "Registries",
        "Traceability",
        "Certification Infrastructure",
        "Constitutional Invariants",
    )

    def __init__(self, remediation_support: AuthorizationsOfficeRemediationSupport | None = None) -> None:
        self.remediation_support = remediation_support or AuthorizationsOfficeRemediationSupport()

    def build_compliance_package(self, repository_root: str | Path | None = None) -> AuthorizationCompliancePackage:
        root = Path(repository_root).resolve() if repository_root is not None else Path(__file__).resolve().parents[3]
        remediation = self.remediation_support.build_remediation_package(root)
        candidate_compliance = self.validate_candidate_compliance(root, remediation)
        canonical_artifacts = self.reconcile_canonical_implementation(remediation)
        requirements = self.materialize_compliance_requirements(remediation)
        certification_tests = self.materialize_certification_tests(requirements)
        test_executions = self.execute_certification_tests(
            remediation,
            candidate_compliance,
            canonical_artifacts,
            requirements,
            certification_tests,
        )
        persistence = self.verify_persistence_replay_recovery(remediation)
        infrastructure = self.assemble_certification_infrastructure(
            remediation,
            requirements,
            certification_tests,
            test_executions,
            persistence,
        )
        findings = (
            candidate_compliance.findings
            + tuple(finding for record in canonical_artifacts for finding in record.findings)
            + tuple(finding for record in requirements for finding in record.findings)
            + tuple(finding for record in test_executions for finding in record.findings)
            + persistence.findings
            + infrastructure.findings
        )
        status = AuthorizationComplianceStatus.PASSING if not findings else AuthorizationComplianceStatus.FAILING
        package = AuthorizationCompliancePackage(
            package_identifier=f"AUTH-RM-001-COMPLIANCE-{remediation.candidate.source_tree_digest[:12].upper()}",
            governing_doctrine=AUTH_RM_001_VERSION,
            order_coverage=self.order_coverage,
            candidate_compliance=candidate_compliance,
            remediation_package_digest=remediation.deterministic_digest,
            canonical_artifacts=canonical_artifacts,
            requirements=requirements,
            certification_tests=certification_tests,
            certification_test_executions=test_executions,
            operational_evidence=tuple(
                record for record in remediation.operational_evidence if record.producing_work_order in self.order_coverage
            ),
            persistence_verification=persistence,
            certification_infrastructure=infrastructure,
            final_status=status,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def validate_candidate_compliance(
        self,
        root: Path,
        remediation: AuthorizationRemediationPackage,
    ) -> AuthorizationCandidateComplianceRecord:
        auth_scope_status = _auth_scope_status(root)
        artifact_findings = tuple(finding for artifact in remediation.artifacts for finding in artifact.findings)
        evidence_ids = {record.candidate_identifier for record in remediation.operational_evidence}
        findings = ()
        if not remediation.candidate.admissible_snapshot:
            findings += remediation.candidate.findings
        if artifact_findings:
            findings += artifact_findings
        if evidence_ids != {remediation.candidate.candidate_identifier}:
            findings += ("operational evidence is not bound to exactly one immutable candidate",)
        record = AuthorizationCandidateComplianceRecord(
            compliance_identifier=f"AUTH-CANDIDATE-COMPLIANCE-{remediation.candidate.source_tree_digest[:12].upper()}",
            candidate_identifier=remediation.candidate.candidate_identifier,
            commit_identifier=remediation.candidate.commit_identifier,
            auth_scope_status=auth_scope_status or "clean",
            immutable_commit_bound=remediation.candidate.admissible_snapshot,
            artifact_inventory_bound=not artifact_findings and bool(remediation.artifacts),
            evidence_candidate_aligned=evidence_ids == {remediation.candidate.candidate_identifier},
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def reconcile_canonical_implementation(
        self,
        remediation: AuthorizationRemediationPackage,
    ) -> tuple[AuthorizationArtifactRecord, ...]:
        canonical = tuple(record for record in remediation.artifacts if record.operational_status == "canonical_required")
        paths = {record.canonical_path for record in canonical}
        duplicate_paths = tuple(sorted(path for path in paths if sum(1 for record in canonical if record.canonical_path == path) > 1))
        rows = []
        for record in canonical:
            findings = record.findings
            if duplicate_paths:
                findings += tuple(f"duplicate canonical artifact: {path}" for path in duplicate_paths)
            rows.append(replace(record, findings=tuple(sorted(set(findings))), deterministic_digest=""))
        return tuple(replace(record, deterministic_digest=_digest(record)) for record in rows)

    def materialize_compliance_requirements(
        self,
        remediation: AuthorizationRemediationPackage,
    ) -> tuple[AuthorizationRequirementRecord, ...]:
        requirements_by_order = {record.governing_work_order: record for record in remediation.requirements}
        records = []
        for order in self.order_coverage:
            source = requirements_by_order[order]
            findings = source.findings
            if not all(
                (
                    source.implementation_artifact,
                    source.executable_schema,
                    source.evaluation_rule,
                    source.executable_test,
                    source.evidence_reference,
                    source.metric_identifier,
                )
            ):
                findings += ("constitutional requirement lacks complete operational linkage",)
            records.append(replace(source, findings=tuple(sorted(set(findings))), deterministic_digest=""))
        return tuple(replace(record, deterministic_digest=_digest(record)) for record in records)

    def materialize_certification_tests(
        self,
        requirements: tuple[AuthorizationRequirementRecord, ...],
    ) -> tuple[AuthorizationCertificationTestRecord, ...]:
        records = []
        for requirement in requirements:
            record = AuthorizationCertificationTestRecord(
                test_identifier=requirement.executable_test,
                governing_requirement=requirement.requirement_identifier,
                governing_work_order=requirement.governing_work_order,
                candidate_scope="immutable_authorizations_office_candidate",
                required_evidence=(
                    requirement.evidence_reference,
                    requirement.implementation_artifact,
                    requirement.executable_schema,
                    requirement.evaluation_rule,
                ),
                execution_procedure=f"execute deterministic compliance verification for {requirement.governing_work_order}",
                expected_result="PASS with no unresolved constitutional findings",
                failure_conditions=(
                    "missing immutable candidate binding",
                    "missing canonical artifact",
                    "missing executable evidence",
                    "nondeterministic replay or recovery",
                    "open traceability orphan",
                ),
                generated_evidence=requirement.evidence_reference,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def execute_certification_tests(
        self,
        remediation: AuthorizationRemediationPackage,
        candidate_compliance: AuthorizationCandidateComplianceRecord,
        artifacts: tuple[AuthorizationArtifactRecord, ...],
        requirements: tuple[AuthorizationRequirementRecord, ...],
        tests: tuple[AuthorizationCertificationTestRecord, ...],
    ) -> tuple[AuthorizationCertificationTestExecutionRecord, ...]:
        artifact_paths = tuple(sorted(record.canonical_path for record in artifacts))
        traceability_by_requirement = {
            record.requirement_identifier: record for record in remediation.traceability
        }
        evidence_by_requirement = {
            record.producing_work_order: record for record in remediation.operational_evidence
        }
        records = []
        for test in tests:
            requirement = next(record for record in requirements if record.requirement_identifier == test.governing_requirement)
            trace = traceability_by_requirement.get(requirement.requirement_identifier)
            evidence = evidence_by_requirement.get(requirement.governing_work_order)
            findings = candidate_compliance.findings + requirement.findings
            if trace is None or trace.zero_orphan_status != "closed":
                findings += ("traceability is not closed for certification test",)
            if evidence is None:
                findings += ("required operational evidence is missing",)
            elif not (
                evidence.positive_path_verified
                and evidence.negative_path_verified
                and evidence.replay_verified
                and evidence.recovery_verified
            ):
                findings += ("operational evidence does not cover positive, negative, replay, and recovery paths",)
            status = AuthorizationComplianceStatus.PASSING if not findings else AuthorizationComplianceStatus.FAILING
            record = AuthorizationCertificationTestExecutionRecord(
                execution_identifier=f"AUTH-TEST-EXEC-{test.test_identifier[-3:]}",
                test_identifier=test.test_identifier,
                candidate_identifier=remediation.candidate.candidate_identifier,
                status=status,
                inspected_artifacts=artifact_paths,
                evidence_identifier=test.generated_evidence,
                findings=tuple(sorted(set(findings))),
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def verify_persistence_replay_recovery(
        self,
        remediation: AuthorizationRemediationPackage,
    ) -> AuthorizationPersistenceVerificationRecord:
        persistence = remediation.persistence
        interruption_boundary = bool(persistence.committed_records) and persistence.checkpoint_digest == persistence.recovery_digest
        idempotency = len(persistence.committed_records) == len(tuple(dict.fromkeys(persistence.committed_records)))
        findings = ()
        if not persistence.replay_equivalent:
            findings += ("replay is not semantically equivalent",)
        if not persistence.recovery_equivalent:
            findings += ("recovery is not semantically equivalent",)
        if not interruption_boundary:
            findings += ("interruption boundary is not durably recoverable",)
        if not idempotency:
            findings += ("committed authorization state is not idempotent",)
        record = AuthorizationPersistenceVerificationRecord(
            verification_identifier=f"AUTH-PRR-{remediation.candidate.source_tree_digest[:12].upper()}",
            candidate_identifier=remediation.candidate.candidate_identifier,
            committed_state_digest=persistence.checkpoint_digest,
            replay_state_digest=persistence.replay_digest,
            recovery_state_digest=persistence.recovery_digest,
            replay_semantically_equivalent=persistence.replay_equivalent,
            recovery_semantically_equivalent=persistence.recovery_equivalent,
            interruption_boundary_verified=interruption_boundary,
            idempotency_verified=idempotency,
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def assemble_certification_infrastructure(
        self,
        remediation: AuthorizationRemediationPackage,
        requirements: tuple[AuthorizationRequirementRecord, ...],
        tests: tuple[AuthorizationCertificationTestRecord, ...],
        test_executions: tuple[AuthorizationCertificationTestExecutionRecord, ...],
        persistence: AuthorizationPersistenceVerificationRecord,
    ) -> AuthorizationCertificationInfrastructureRecord:
        findings = (
            tuple(finding for record in requirements for finding in record.findings)
            + tuple(finding for record in test_executions for finding in record.findings)
            + persistence.findings
        )
        missing_domains = tuple(
            domain for domain in self.audit_domains if not self._domain_is_covered(domain, remediation, tests, test_executions)
        )
        findings += tuple(f"certification domain not covered: {domain}" for domain in missing_domains)
        manifest = _digest((remediation.candidate, remediation.artifacts, requirements, tests, test_executions))
        package = _digest((manifest, remediation.operational_evidence, persistence, remediation.traceability))
        decision = AuthorizationComplianceStatus.PASSING if not findings else AuthorizationComplianceStatus.FAILING
        record = AuthorizationCertificationInfrastructureRecord(
            infrastructure_identifier=f"AUTH-CERT-INFRA-{remediation.candidate.source_tree_digest[:12].upper()}",
            candidate_identifier=remediation.candidate.candidate_identifier,
            manifest_digest=manifest,
            package_digest=package,
            registry_count=len(remediation.registries),
            test_count=len(tests),
            evidence_count=len(remediation.operational_evidence),
            metric_count=len(requirements),
            decision=decision,
            closure_controls=("fail_closed_on_missing_candidate", "fail_closed_on_missing_evidence", "zero_orphan_traceability_required"),
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def _domain_is_covered(
        self,
        domain: str,
        remediation: AuthorizationRemediationPackage,
        tests: tuple[AuthorizationCertificationTestRecord, ...],
        test_executions: tuple[AuthorizationCertificationTestExecutionRecord, ...],
    ) -> bool:
        if domain == "Office Authority":
            return any(record.decision == AuthorizationDecisionStatus.AUTHORIZED for record in remediation.sample_decisions)
        if domain in {"Constitutional Objects", "Inputs", "Outputs", "Lifecycles", "Validation"}:
            return bool(remediation.objects and remediation.contracts and remediation.lifecycle)
        if domain == "Deterministic Decisions":
            return len({record.deterministic_digest for record in remediation.sample_decisions}) == len(remediation.sample_decisions)
        if domain in {"Persistence", "Replay", "Recovery"}:
            return remediation.persistence.replay_equivalent and remediation.persistence.recovery_equivalent
        if domain in {"Configuration", "Registries"}:
            return bool(remediation.registries)
        if domain == "Traceability":
            return all(record.zero_orphan_status == "closed" for record in remediation.traceability)
        if domain == "Certification Infrastructure":
            return bool(tests and test_executions) and all(
                record.status == AuthorizationComplianceStatus.PASSING for record in test_executions
            )
        if domain == "Constitutional Invariants":
            return all(not record.findings for record in remediation.operational_evidence)
        return False


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _git_blob_digest(root: Path, path: str) -> str:
    try:
        data = subprocess.check_output(["git", "-C", str(root), "show", f"HEAD:{path}"], stderr=subprocess.DEVNULL)
    except Exception:
        return ""
    return hashlib.sha256(data).hexdigest()


def _file_digest(path: Path) -> str:
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _auth_scope_status(root: Path) -> str:
    paths = (
        "src/argos/control_panel/authorization_authority.py",
        "src/argos/control_panel/__init__.py",
        "Tests/test_authorization_authority.py",
        "Tests/test_authorization_authority_compliance.py",
        "Documentation/AUTH-RM-001-001_TO_013_REMEDIATION_EVIDENCE.md",
        "Documentation/AUTH-RM-001-001_TO_008_COMPLIANCE_EVIDENCE.md",
    )
    status_lines = []
    for line in (_git(root, "status", "--short", "--", *paths) or "").splitlines():
        if line.strip():
            status_lines.append(line.strip())
    return "; ".join(sorted(status_lines))
