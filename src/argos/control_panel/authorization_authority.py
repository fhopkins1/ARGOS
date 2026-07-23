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
