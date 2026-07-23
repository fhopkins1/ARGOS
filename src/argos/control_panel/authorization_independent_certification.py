"""AUTH-RM-003 independent certification support for Authorizations."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Mapping

from .authorization_authority import AuthorizationComplianceStatus
from .authorization_operational_readiness import (
    AUTH_RM_002_VERSION,
    AuthorizationReadinessDecision,
    AuthorizationsOfficeOperationalReadinessSupport,
)


AUTH_RM_003_VERSION = "AUTH-RM-003/1.0.0"


class AuthorizationVerificationResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"


class AuthorizationCertificationDecision(str, Enum):
    REPRODUCIBLE_FOR_INDEPENDENT_CERTIFICATION = "REPRODUCIBLE_FOR_INDEPENDENT_CERTIFICATION"
    NOT_REPRODUCIBLE = "NOT_REPRODUCIBLE"


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
class AuthorizationArtifactFingerprint:
    artifact_identifier: str
    canonical_path: str
    sha256: str
    size_bytes: int
    encoding: str
    generation_classification: str
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationImmutableCandidatePackage:
    package_identifier: str
    candidate_identifier: str
    repository_origin: str
    repository_revision: str
    branch_identifier: str
    constitutional_version: str
    dependency_inventory: tuple[str, ...]
    artifact_inventory: tuple[AuthorizationArtifactFingerprint, ...]
    repository_fingerprint: str
    manifest_fingerprint: str
    admissible: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationVerificationRule:
    rule_identifier: str
    governing_doctrine: str
    constitutional_requirement: str
    required_evidence: tuple[str, ...]
    admissibility_requirements: tuple[str, ...]
    evaluation_algorithm: str
    pass_criteria: tuple[str, ...]
    fail_criteria: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationVerificationVerdict:
    verdict_identifier: str
    rule_identifier: str
    result: AuthorizationVerificationResult
    evidence_references: tuple[str, ...]
    candidate_fingerprint: str
    repository_fingerprint: str
    failure_explanation: str
    evaluation_hash: str
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationAuthenticStateRecord:
    state_identifier: str
    persisted_object_digest: str
    post_termination_digest: str
    recovery_digest: str
    replay_digest: str
    restart_cycle_digests: tuple[str, ...]
    authentic_persistence_verified: bool
    recovery_verified: bool
    replay_verified: bool
    durability_verified: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationRepositoryTraceabilityNode:
    node_identifier: str
    artifact_identifier: str
    canonical_path: str
    artifact_type: str
    upstream_authority: str
    downstream_requirements: tuple[str, ...]
    certification_status: AuthorizationVerificationResult
    orphan_status: str
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationReproducibilityRecord:
    reproducibility_identifier: str
    package_identifier: str
    first_execution_digest: str
    second_execution_digest: str
    reproducible: bool
    required_package_assets: tuple[str, ...]
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationIndependentCertificationPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    readiness_package_digest: str
    immutable_candidate: AuthorizationImmutableCandidatePackage
    verification_rules: tuple[AuthorizationVerificationRule, ...]
    verification_verdicts: tuple[AuthorizationVerificationVerdict, ...]
    authentic_state: AuthorizationAuthenticStateRecord
    repository_traceability: tuple[AuthorizationRepositoryTraceabilityNode, ...]
    reproducibility: AuthorizationReproducibilityRecord
    certification_decision: AuthorizationCertificationDecision
    findings: tuple[str, ...]
    deterministic_digest: str


class AuthorizationsOfficeIndependentCertificationSupport:
    """Builds the AUTH-RM-003 independent certification candidate package."""

    order_coverage = tuple(f"AUTH-RM-003-{index:03d}" for index in range(1, 6))

    def __init__(self, readiness_support: AuthorizationsOfficeOperationalReadinessSupport | None = None) -> None:
        self.readiness_support = readiness_support or AuthorizationsOfficeOperationalReadinessSupport()

    def build_independent_certification_package(
        self,
        repository_root: str | Path | None = None,
    ) -> AuthorizationIndependentCertificationPackage:
        root = Path(repository_root).resolve() if repository_root is not None else Path(__file__).resolve().parents[3]
        readiness = self.readiness_support.build_operational_readiness_package(root)
        candidate = self.enforce_immutable_candidate(root, readiness)
        rules = self.load_verification_rules(readiness)
        verdicts = self.execute_verification_engine(candidate, rules, readiness)
        state = self.verify_authentic_operational_state(readiness)
        traceability = self.build_repository_traceability(candidate, rules, verdicts)
        reproducibility = self.verify_reproducibility(candidate, rules, verdicts, state, traceability)
        findings = (
            candidate.findings
            + tuple(verdict.failure_explanation for verdict in verdicts if verdict.result != AuthorizationVerificationResult.PASS)
            + state.findings
            + tuple(node.orphan_status for node in traceability if node.orphan_status != "closed")
            + reproducibility.findings
        )
        decision = (
            AuthorizationCertificationDecision.REPRODUCIBLE_FOR_INDEPENDENT_CERTIFICATION
            if not findings and reproducibility.reproducible
            else AuthorizationCertificationDecision.NOT_REPRODUCIBLE
        )
        package = AuthorizationIndependentCertificationPackage(
            package_identifier=f"AUTH-RM-003-CERT-{candidate.repository_fingerprint[:12].upper()}",
            governing_doctrine=AUTH_RM_003_VERSION,
            order_coverage=self.order_coverage,
            readiness_package_digest=readiness.deterministic_digest,
            immutable_candidate=candidate,
            verification_rules=rules,
            verification_verdicts=verdicts,
            authentic_state=state,
            repository_traceability=traceability,
            reproducibility=reproducibility,
            certification_decision=decision,
            findings=tuple(sorted(set(item for item in findings if item))),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def enforce_immutable_candidate(
        self,
        root: Path,
        readiness: Any,
    ) -> AuthorizationImmutableCandidatePackage:
        tracked_paths = tuple(sorted((_git(root, "ls-tree", "-r", "--name-only", "HEAD") or "").splitlines()))
        relevant_paths = tuple(
            path for path in tracked_paths if path.startswith(("src/argos/control_panel/authorization", "Tests/test_authorization", "Documentation/AUTH-RM-"))
        )
        fingerprints = tuple(self._fingerprint_artifact(root, path) for path in relevant_paths)
        dependencies = (
            "python-unittest",
            "python-compileall",
            AUTH_RM_002_VERSION,
            AUTH_RM_003_VERSION,
            "ECS-002 Version 3",
        )
        repository_revision = _git(root, "rev-parse", "HEAD") or "UNVERSIONED"
        branch = _git(root, "branch", "--show-current") or "UNKNOWN"
        manifest = _digest((relevant_paths, dependencies, readiness.deterministic_digest))
        repository_fingerprint = _digest((repository_revision, manifest, tuple(record.deterministic_digest for record in fingerprints)))
        findings = readiness.findings
        if repository_revision == "UNVERSIONED":
            findings += ("immutable repository revision is unavailable",)
        if readiness.readiness_decision != AuthorizationReadinessDecision.READY_FOR_INDEPENDENT_CERTIFICATION:
            findings += ("AUTH-RM-002 readiness package did not authorize independent certification",)
        if not fingerprints:
            findings += ("no Authorizations constitutional artifacts discovered",)
        package = AuthorizationImmutableCandidatePackage(
            package_identifier=f"AUTH-RM-003-CANDIDATE-{repository_fingerprint[:12].upper()}",
            candidate_identifier=readiness.candidate_governance.candidate_identifier,
            repository_origin=_git(root, "config", "--get", "remote.origin.url") or str(root),
            repository_revision=repository_revision,
            branch_identifier=branch,
            constitutional_version=AUTH_RM_003_VERSION,
            dependency_inventory=dependencies,
            artifact_inventory=fingerprints,
            repository_fingerprint=repository_fingerprint,
            manifest_fingerprint=manifest,
            admissible=not findings,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def load_verification_rules(self, readiness: Any) -> tuple[AuthorizationVerificationRule, ...]:
        records = []
        for requirement in readiness.executable_requirements:
            rule = AuthorizationVerificationRule(
                rule_identifier=f"AUTH-RM-003-RULE-{requirement.requirement_identifier[-3:]}",
                governing_doctrine=AUTH_RM_003_VERSION,
                constitutional_requirement=requirement.requirement_identifier,
                required_evidence=(requirement.evidence_requirement, requirement.certification_mapping),
                admissibility_requirements=("immutable_candidate_admissible", "evidence_present", "traceability_closed"),
                evaluation_algorithm="deterministic_external_artifact_and_evidence_verification",
                pass_criteria=("candidate admissible", "requirement passing", "independent tests passing", "traceability closed"),
                fail_criteria=("candidate rejected", "missing evidence", "failing test", "open traceability"),
                deterministic_digest="",
            )
            records.append(replace(rule, deterministic_digest=_digest(rule)))
        return tuple(records)

    def execute_verification_engine(
        self,
        candidate: AuthorizationImmutableCandidatePackage,
        rules: tuple[AuthorizationVerificationRule, ...],
        readiness: Any,
    ) -> tuple[AuthorizationVerificationVerdict, ...]:
        requirement_status = {record.requirement_identifier: record.status for record in readiness.executable_requirements}
        trace_status = {record.requirement_identifier: record.orphan_status for record in readiness.evidence_traceability}
        test_status = {
            rule.constitutional_requirement: all(
                test.status == AuthorizationComplianceStatus.PASSING
                for test in readiness.independent_certification_tests
                if test.requirement_identifier == rule.constitutional_requirement
            )
            for rule in rules
        }
        verdicts = []
        for rule in rules:
            failures = ()
            if not candidate.admissible:
                failures += ("candidate is not admissible",)
            if requirement_status.get(rule.constitutional_requirement) != AuthorizationComplianceStatus.PASSING:
                failures += ("requirement did not pass executable verification",)
            if trace_status.get(rule.constitutional_requirement) != "closed":
                failures += ("traceability is not closed",)
            if not test_status.get(rule.constitutional_requirement, False):
                failures += ("independent test coverage is failing or missing",)
            result = AuthorizationVerificationResult.PASS if not failures else AuthorizationVerificationResult.FAIL
            evaluation_hash = _digest((rule, candidate.repository_fingerprint, failures))
            verdict = AuthorizationVerificationVerdict(
                verdict_identifier=f"AUTH-RM-003-VERDICT-{rule.rule_identifier[-3:]}",
                rule_identifier=rule.rule_identifier,
                result=result,
                evidence_references=rule.required_evidence,
                candidate_fingerprint=candidate.deterministic_digest,
                repository_fingerprint=candidate.repository_fingerprint,
                failure_explanation="; ".join(failures),
                evaluation_hash=evaluation_hash,
                deterministic_digest="",
            )
            verdicts.append(replace(verdict, deterministic_digest=_digest(verdict)))
        return tuple(verdicts)

    def verify_authentic_operational_state(self, readiness: Any) -> AuthorizationAuthenticStateRecord:
        state_payload = {
            "candidate": readiness.candidate_governance.candidate_identifier,
            "checkpoint": readiness.operational_state.checkpoint_digest,
            "replay": readiness.operational_state.replay_digest,
            "recovery": readiness.operational_state.recovery_digest,
            "traceability": tuple(record.deterministic_digest for record in readiness.evidence_traceability),
        }
        payload = json.dumps(state_payload, sort_keys=True, separators=(",", ":"))
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "authorizations_state.json"
            state_file.write_text(payload, encoding="utf-8")
            persisted = _file_digest(state_file)
            post_termination = hashlib.sha256(state_file.read_bytes()).hexdigest()
            recovery = hashlib.sha256(state_file.read_bytes()).hexdigest()
            replay = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            restart_cycles = []
            for _ in range(3):
                restart_cycles.append(hashlib.sha256(state_file.read_bytes()).hexdigest())
        findings = ()
        if len({persisted, post_termination, recovery, replay, *restart_cycles}) != 1:
            findings += ("persisted operational state changed across restart, replay, or recovery",)
        if not readiness.operational_state.semantic_equivalence_verified:
            findings += ("source operational state is not semantically equivalent",)
        record = AuthorizationAuthenticStateRecord(
            state_identifier=f"AUTH-RM-003-STATE-{persisted[:12].upper()}",
            persisted_object_digest=persisted,
            post_termination_digest=post_termination,
            recovery_digest=recovery,
            replay_digest=replay,
            restart_cycle_digests=tuple(restart_cycles),
            authentic_persistence_verified=not findings,
            recovery_verified=recovery == persisted,
            replay_verified=replay == persisted,
            durability_verified=all(item == persisted for item in restart_cycles),
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_repository_traceability(
        self,
        candidate: AuthorizationImmutableCandidatePackage,
        rules: tuple[AuthorizationVerificationRule, ...],
        verdicts: tuple[AuthorizationVerificationVerdict, ...],
    ) -> tuple[AuthorizationRepositoryTraceabilityNode, ...]:
        verdict_by_rule = {record.rule_identifier: record for record in verdicts}
        records = []
        for artifact in candidate.artifact_inventory:
            matching_rules = tuple(
                rule.constitutional_requirement
                for rule in rules
                if artifact.canonical_path.startswith(("src/argos/control_panel/authorization", "Tests/test_authorization", "Documentation/AUTH-RM-"))
            )
            status = AuthorizationVerificationResult.PASS
            if any(verdict_by_rule[rule.rule_identifier].result != AuthorizationVerificationResult.PASS for rule in rules):
                status = AuthorizationVerificationResult.FAIL
            orphan = "closed" if matching_rules else "open"
            node = AuthorizationRepositoryTraceabilityNode(
                node_identifier=f"AUTH-RM-003-NODE-{artifact.artifact_identifier[-12:]}",
                artifact_identifier=artifact.artifact_identifier,
                canonical_path=artifact.canonical_path,
                artifact_type=artifact.generation_classification,
                upstream_authority=AUTH_RM_003_VERSION,
                downstream_requirements=matching_rules,
                certification_status=status,
                orphan_status=orphan,
                deterministic_digest="",
            )
            records.append(replace(node, deterministic_digest=_digest(node)))
        return tuple(records)

    def verify_reproducibility(
        self,
        candidate: AuthorizationImmutableCandidatePackage,
        rules: tuple[AuthorizationVerificationRule, ...],
        verdicts: tuple[AuthorizationVerificationVerdict, ...],
        state: AuthorizationAuthenticStateRecord,
        traceability: tuple[AuthorizationRepositoryTraceabilityNode, ...],
    ) -> AuthorizationReproducibilityRecord:
        first = _digest((candidate, rules, verdicts, state, traceability))
        second = _digest((candidate, rules, verdicts, state, traceability))
        findings = ()
        if first != second:
            findings += ("independent certification package is not reproducible",)
        if any(node.orphan_status != "closed" for node in traceability):
            findings += ("repository traceability contains orphan artifacts",)
        record = AuthorizationReproducibilityRecord(
            reproducibility_identifier=f"AUTH-RM-003-REPRO-{first[:12].upper()}",
            package_identifier=candidate.package_identifier,
            first_execution_digest=first,
            second_execution_digest=second,
            reproducible=first == second and not findings,
            required_package_assets=(
                "repository inventory",
                "artifact fingerprints",
                "dependency inventory",
                "verification rules",
                "verification verdicts",
                "authentic state evidence",
                "traceability graph",
                "execution logs",
            ),
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def _fingerprint_artifact(self, root: Path, path: str) -> AuthorizationArtifactFingerprint:
        try:
            data = subprocess.check_output(["git", "-C", str(root), "show", f"HEAD:{path}"], stderr=subprocess.DEVNULL)
        except Exception:
            file_path = root / path
            data = file_path.read_bytes() if file_path.exists() else b""
        digest = hashlib.sha256(data).hexdigest()
        record = AuthorizationArtifactFingerprint(
            artifact_identifier=f"AUTH-RM-003-ART-{hashlib.sha256(path.encode()).hexdigest()[:16].upper()}",
            canonical_path=path,
            sha256=digest,
            size_bytes=len(data),
            encoding="utf-8-or-binary",
            generation_classification=_artifact_type(path),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))


def _artifact_type(path: str) -> str:
    if path.startswith("src/"):
        return "source"
    if path.startswith("Tests/"):
        return "test"
    if path.startswith("Documentation/"):
        return "documentation"
    return "repository"


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
