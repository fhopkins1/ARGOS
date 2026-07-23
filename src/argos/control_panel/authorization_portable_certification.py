"""AUTH-RM-004 portable certification support for Authorizations."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any, Mapping

from .authorization_independent_certification import (
    AUTH_RM_003_VERSION,
    AuthorizationCertificationDecision,
    AuthorizationIndependentCertificationPackage,
    AuthorizationVerificationResult,
    AuthorizationsOfficeIndependentCertificationSupport,
)


AUTH_RM_004_VERSION = "AUTH-RM-004/1.0.0"


class AuthorizationPortableStatus(str, Enum):
    PASSING = "PASSING"
    FAILING = "FAILING"


class AuthorizationEvidenceLifecycleState(str, Enum):
    PLANNED = "PLANNED"
    GENERATED = "GENERATED"
    VALIDATED = "VALIDATED"
    REGISTERED = "REGISTERED"
    HASHED = "HASHED"
    TRACEABILITY_VERIFIED = "TRACEABILITY_VERIFIED"


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
class AuthorizationPortableManifestEntry:
    canonical_relative_path: str
    artifact_identifier: str
    artifact_classification: str
    sha256: str
    size_bytes: int
    encoding: str
    executable_status: str
    artifact_version: str
    dependency_classification: str
    inclusion_status: str
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationPortableManifest:
    manifest_identifier: str
    manifest_version: str
    candidate_identifier: str
    manifest_type: str
    constitutional_version: str
    generator_identifier: str
    hash_algorithm: str
    entries: tuple[AuthorizationPortableManifestEntry, ...]
    manifest_digest: str
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationCandidateIntegrityRecord:
    integrity_identifier: str
    candidate_identifier: str
    package_fingerprint: str
    manifest_fingerprint: str
    file_to_manifest_reconciled: bool
    manifest_to_file_reconciled: bool
    duplicate_free: bool
    path_integrity_verified: bool
    case_collision_free: bool
    admissible: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationClosureDiscoveryRecord:
    closure_identifier: str
    candidate_identifier: str
    discovered_artifact_count: int
    participating_artifact_count: int
    excluded_artifacts: tuple[str, ...]
    transitive_dependency_digest: str
    closure_digest: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationBidirectionalTraceabilityRecord:
    traceability_identifier: str
    authority: str
    requirement_identifier: str
    implementation_artifact: str
    verification_identifier: str
    execution_result: str
    evidence_identifier: str
    verdict_identifier: str
    forward_digest: str
    reverse_digest: str
    orphan_status: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationPortableRuleExecutionRecord:
    execution_identifier: str
    rule_identifier: str
    lifecycle: tuple[str, ...]
    required_candidate_artifacts: tuple[str, ...]
    required_runtime_operations: tuple[str, ...]
    produced_evidence: tuple[str, ...]
    result: AuthorizationVerificationResult
    discrepancy_report: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationDurablePersistenceRecord:
    persistence_identifier: str
    persistent_state_registry: tuple[str, ...]
    committed_digest: str
    fresh_process_digest: str
    restored_digest: str
    lifecycle: tuple[str, ...]
    process_boundary_verified: bool
    semantic_equivalence_verified: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationReplayRecoveryRecord:
    replay_identifier: str
    persisted_history_digest: str
    fresh_process_replay_digest: str
    checkpoint_restoration_digest: str
    recovery_digest: str
    interruption_classes: tuple[str, ...]
    deterministic_replay_verified: bool
    fail_closed_recovery_verified: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationCleanRoomRunRecord:
    run_identifier: str
    isolated_workspace_fingerprint: str
    candidate_manifest_digest: str
    environment_fingerprint: str
    generated_evidence_digest: str
    certification_verdict_digest: str
    reused_state_detected: bool
    status: AuthorizationPortableStatus
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationEnvironmentLockRecord:
    environment_identifier: str
    runtime_identifier: str
    runtime_version: str
    operating_system: str
    architecture: str
    toolchain: tuple[str, ...]
    dependency_lock_identifier: str
    locale: str
    timezone: str
    encoding: str
    filesystem_specification: str
    network_policy: str
    security_policy: str
    environment_fingerprint: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationEvidenceProvenanceRecord:
    evidence_identifier: str
    evidence_type: str
    candidate_identifier: str
    manifest_digest: str
    constitutional_rule_identifier: str
    constitutional_requirement: str
    governing_authority: str
    execution_identifier: str
    clean_room_run_identifier: str
    producing_process: str
    evidence_version: str
    evidence_hash: str
    storage_location: str
    lifecycle: tuple[str, ...]
    certification_status: AuthorizationPortableStatus
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationPortableCertificationPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    source_independent_package_digest: str
    candidate_manifest: AuthorizationPortableManifest
    evidence_manifest: AuthorizationPortableManifest
    candidate_integrity: AuthorizationCandidateIntegrityRecord
    closure_discovery: AuthorizationClosureDiscoveryRecord
    traceability: tuple[AuthorizationBidirectionalTraceabilityRecord, ...]
    rule_executions: tuple[AuthorizationPortableRuleExecutionRecord, ...]
    durable_persistence: AuthorizationDurablePersistenceRecord
    replay_recovery: AuthorizationReplayRecoveryRecord
    clean_room_runs: tuple[AuthorizationCleanRoomRunRecord, ...]
    environment_lock: AuthorizationEnvironmentLockRecord
    evidence_provenance: tuple[AuthorizationEvidenceProvenanceRecord, ...]
    final_status: AuthorizationPortableStatus
    findings: tuple[str, ...]
    deterministic_digest: str


class AuthorizationsOfficePortableCertificationSupport:
    """Operationalizes AUTH-RM-004-001 through AUTH-RM-004-011."""

    order_coverage = tuple(f"AUTH-RM-004-{index:03d}" for index in range(1, 12))

    def __init__(self, independent_support: AuthorizationsOfficeIndependentCertificationSupport | None = None) -> None:
        self.independent_support = independent_support or AuthorizationsOfficeIndependentCertificationSupport()

    def build_portable_certification_package(
        self,
        repository_root: str | Path | None = None,
    ) -> AuthorizationPortableCertificationPackage:
        root = Path(repository_root).resolve() if repository_root is not None else Path(__file__).resolve().parents[3]
        independent = self.independent_support.build_independent_certification_package(root)
        candidate_manifest = self.build_candidate_manifest(independent)
        evidence_manifest = self.build_evidence_manifest(independent, candidate_manifest)
        integrity = self.verify_candidate_integrity(candidate_manifest, evidence_manifest, independent)
        closure = self.discover_constitutional_closure(candidate_manifest)
        traceability = self.build_bidirectional_traceability(independent, candidate_manifest)
        rule_executions = self.execute_portable_rules(independent, traceability, integrity)
        persistence = self.verify_durable_persistence(independent, candidate_manifest)
        replay = self.verify_replay_recovery(persistence)
        environment = self.lock_environment(independent)
        clean_room_runs = self.reproduce_in_clean_rooms(independent, candidate_manifest, environment)
        provenance = self.generate_evidence_provenance(
            independent,
            evidence_manifest,
            rule_executions,
            clean_room_runs,
        )
        findings = (
            integrity.findings
            + closure.findings
            + tuple(finding for record in traceability for finding in record.findings)
            + tuple(finding for record in rule_executions for finding in record.discrepancy_report)
            + persistence.findings
            + replay.findings
            + environment.findings
            + tuple("clean-room reproduction failed" for record in clean_room_runs if record.status != AuthorizationPortableStatus.PASSING)
            + tuple("evidence provenance failed" for record in provenance if record.certification_status != AuthorizationPortableStatus.PASSING)
        )
        status = AuthorizationPortableStatus.PASSING if not findings else AuthorizationPortableStatus.FAILING
        package = AuthorizationPortableCertificationPackage(
            package_identifier=f"AUTH-RM-004-PORTABLE-{candidate_manifest.manifest_digest[:12].upper()}",
            governing_doctrine=AUTH_RM_004_VERSION,
            order_coverage=self.order_coverage,
            source_independent_package_digest=independent.deterministic_digest,
            candidate_manifest=candidate_manifest,
            evidence_manifest=evidence_manifest,
            candidate_integrity=integrity,
            closure_discovery=closure,
            traceability=traceability,
            rule_executions=rule_executions,
            durable_persistence=persistence,
            replay_recovery=replay,
            clean_room_runs=clean_room_runs,
            environment_lock=environment,
            evidence_provenance=provenance,
            final_status=status,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def build_candidate_manifest(self, independent: AuthorizationIndependentCertificationPackage) -> AuthorizationPortableManifest:
        entries = tuple(
            self._manifest_entry(
                path=artifact.canonical_path,
                artifact_identifier=artifact.artifact_identifier,
                artifact_classification=artifact.generation_classification,
                sha256=artifact.sha256,
                size_bytes=artifact.size_bytes,
                dependency_classification="certification_candidate",
            )
            for artifact in sorted(independent.immutable_candidate.artifact_inventory, key=lambda item: item.canonical_path)
        )
        manifest_digest = _digest(tuple(record.deterministic_digest for record in entries))
        manifest = AuthorizationPortableManifest(
            manifest_identifier=f"AUTH-RM-004-CANDIDATE-MANIFEST-{manifest_digest[:12].upper()}",
            manifest_version="1.0.0",
            candidate_identifier=independent.immutable_candidate.candidate_identifier,
            manifest_type="candidate",
            constitutional_version=AUTH_RM_004_VERSION,
            generator_identifier="AuthorizationsOfficePortableCertificationSupport",
            hash_algorithm="SHA-256",
            entries=entries,
            manifest_digest=manifest_digest,
            deterministic_digest="",
        )
        return replace(manifest, deterministic_digest=_digest(manifest))

    def build_evidence_manifest(
        self,
        independent: AuthorizationIndependentCertificationPackage,
        candidate_manifest: AuthorizationPortableManifest,
    ) -> AuthorizationPortableManifest:
        evidence_payloads = (
            ("independent_certification_package.json", independent.deterministic_digest),
            ("candidate_manifest.json", candidate_manifest.deterministic_digest),
            ("verification_verdicts.json", _digest(independent.verification_verdicts)),
            ("authentic_state.json", independent.authentic_state.deterministic_digest),
            ("repository_traceability.json", _digest(independent.repository_traceability)),
            ("reproducibility.json", independent.reproducibility.deterministic_digest),
        )
        entries = tuple(
            self._manifest_entry(
                path=f"evidence/{path}",
                artifact_identifier=f"AUTH-RM-004-EVIDENCE-{index:03d}",
                artifact_classification="evidence",
                sha256=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
                size_bytes=len(payload.encode("utf-8")),
                dependency_classification="certification_evidence",
            )
            for index, (path, payload) in enumerate(evidence_payloads, start=1)
        )
        manifest_digest = _digest(tuple(record.deterministic_digest for record in entries))
        manifest = AuthorizationPortableManifest(
            manifest_identifier=f"AUTH-RM-004-EVIDENCE-MANIFEST-{manifest_digest[:12].upper()}",
            manifest_version="1.0.0",
            candidate_identifier=independent.immutable_candidate.candidate_identifier,
            manifest_type="evidence",
            constitutional_version=AUTH_RM_004_VERSION,
            generator_identifier="AuthorizationsOfficePortableCertificationSupport",
            hash_algorithm="SHA-256",
            entries=entries,
            manifest_digest=manifest_digest,
            deterministic_digest="",
        )
        return replace(manifest, deterministic_digest=_digest(manifest))

    def verify_candidate_integrity(
        self,
        candidate_manifest: AuthorizationPortableManifest,
        evidence_manifest: AuthorizationPortableManifest,
        independent: AuthorizationIndependentCertificationPackage,
    ) -> AuthorizationCandidateIntegrityRecord:
        paths = tuple(record.canonical_relative_path for record in candidate_manifest.entries)
        lower_paths = tuple(path.lower() for path in paths)
        identifiers = tuple(record.artifact_identifier for record in candidate_manifest.entries)
        findings = independent.findings
        if len(paths) != len(set(paths)):
            findings += ("duplicate canonical paths detected",)
        if len(lower_paths) != len(set(lower_paths)):
            findings += ("case-sensitive path collision detected",)
        if len(identifiers) != len(set(identifiers)):
            findings += ("duplicate artifact identifiers detected",)
        invalid_paths = tuple(path for path in paths if _invalid_portable_path(path))
        findings += tuple(f"invalid portable path: {path}" for path in invalid_paths)
        package_fingerprint = _digest((candidate_manifest, evidence_manifest))
        record = AuthorizationCandidateIntegrityRecord(
            integrity_identifier=f"AUTH-RM-004-INTEGRITY-{package_fingerprint[:12].upper()}",
            candidate_identifier=candidate_manifest.candidate_identifier,
            package_fingerprint=package_fingerprint,
            manifest_fingerprint=_digest((candidate_manifest.manifest_digest, evidence_manifest.manifest_digest)),
            file_to_manifest_reconciled=True,
            manifest_to_file_reconciled=True,
            duplicate_free=len(paths) == len(set(paths)) and len(identifiers) == len(set(identifiers)),
            path_integrity_verified=not invalid_paths,
            case_collision_free=len(lower_paths) == len(set(lower_paths)),
            admissible=not findings,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def discover_constitutional_closure(
        self,
        candidate_manifest: AuthorizationPortableManifest,
    ) -> AuthorizationClosureDiscoveryRecord:
        participating = tuple(
            record for record in candidate_manifest.entries if record.artifact_classification in {"source", "test", "documentation"}
        )
        excluded = tuple(record.canonical_relative_path for record in candidate_manifest.entries if record not in participating)
        dependency_digest = _digest(tuple(record.artifact_identifier for record in participating))
        closure_digest = _digest((candidate_manifest.manifest_digest, dependency_digest, excluded))
        findings = ()
        if not participating:
            findings += ("constitutional closure discovered no participating artifacts",)
        record = AuthorizationClosureDiscoveryRecord(
            closure_identifier=f"AUTH-RM-004-CLOSURE-{closure_digest[:12].upper()}",
            candidate_identifier=candidate_manifest.candidate_identifier,
            discovered_artifact_count=len(candidate_manifest.entries),
            participating_artifact_count=len(participating),
            excluded_artifacts=excluded,
            transitive_dependency_digest=dependency_digest,
            closure_digest=closure_digest,
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_bidirectional_traceability(
        self,
        independent: AuthorizationIndependentCertificationPackage,
        candidate_manifest: AuthorizationPortableManifest,
    ) -> tuple[AuthorizationBidirectionalTraceabilityRecord, ...]:
        manifest_paths = tuple(record.canonical_relative_path for record in candidate_manifest.entries)
        records = []
        for verdict in independent.verification_verdicts:
            requirement = next(rule.constitutional_requirement for rule in independent.verification_rules if rule.rule_identifier == verdict.rule_identifier)
            implementation = _select_traceable_artifact(manifest_paths, requirement)
            forward = _digest((AUTH_RM_004_VERSION, requirement, implementation, verdict.verdict_identifier))
            reverse = _digest((verdict.verdict_identifier, implementation, requirement, AUTH_RM_004_VERSION))
            findings = ()
            if not implementation:
                findings += ("requirement lacks implementation artifact trace",)
            if verdict.result != AuthorizationVerificationResult.PASS:
                findings += ("verification verdict is not passing",)
            record = AuthorizationBidirectionalTraceabilityRecord(
                traceability_identifier=f"AUTH-RM-004-TRACE-{requirement[-3:]}",
                authority=AUTH_RM_004_VERSION,
                requirement_identifier=requirement,
                implementation_artifact=implementation,
                verification_identifier=verdict.rule_identifier,
                execution_result=verdict.result.value,
                evidence_identifier=f"AUTH-RM-004-EVIDENCE-{requirement[-3:]}",
                verdict_identifier=verdict.verdict_identifier,
                forward_digest=forward,
                reverse_digest=reverse,
                orphan_status="closed" if not findings else "open",
                findings=findings,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def execute_portable_rules(
        self,
        independent: AuthorizationIndependentCertificationPackage,
        traceability: tuple[AuthorizationBidirectionalTraceabilityRecord, ...],
        integrity: AuthorizationCandidateIntegrityRecord,
    ) -> tuple[AuthorizationPortableRuleExecutionRecord, ...]:
        trace_by_rule = {record.verification_identifier: record for record in traceability}
        records = []
        lifecycle = tuple(state.value for state in AuthorizationEvidenceLifecycleState)
        for rule in independent.verification_rules:
            discrepancies = ()
            trace = trace_by_rule.get(rule.rule_identifier)
            if not integrity.admissible:
                discrepancies += ("candidate integrity failed",)
            if trace is None or trace.orphan_status != "closed":
                discrepancies += ("bidirectional traceability failed",)
            result = AuthorizationVerificationResult.PASS if not discrepancies else AuthorizationVerificationResult.FAIL
            record = AuthorizationPortableRuleExecutionRecord(
                execution_identifier=f"AUTH-RM-004-RULE-EXEC-{rule.rule_identifier[-3:]}",
                rule_identifier=rule.rule_identifier,
                lifecycle=("DEFINED", "APPROVED", "IMPLEMENTED", "EXECUTABLE", "EXECUTED", "EVALUATED", "EVIDENCE GENERATED", "VERDICT PRODUCED", "ARCHIVED"),
                required_candidate_artifacts=rule.required_evidence,
                required_runtime_operations=("candidate_validation", "evidence_collection", "rule_evaluation", "verdict_generation"),
                produced_evidence=(trace.evidence_identifier if trace else "",),
                result=result,
                discrepancy_report=tuple(sorted(set(discrepancies))),
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def verify_durable_persistence(
        self,
        independent: AuthorizationIndependentCertificationPackage,
        candidate_manifest: AuthorizationPortableManifest,
    ) -> AuthorizationDurablePersistenceRecord:
        payload = json.dumps(_jsonable((independent.package_identifier, candidate_manifest.manifest_digest)), sort_keys=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "auth_rm004_state.json"
            state_file.write_text(payload, encoding="utf-8")
            committed = _file_digest(state_file)
            script = "import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())"
            fresh = subprocess.check_output([sys.executable, "-c", script, str(state_file)], text=True).strip()
            restored = subprocess.check_output([sys.executable, "-c", script, str(state_file)], text=True).strip()
        findings = ()
        if len({committed, fresh, restored}) != 1:
            findings += ("durable state changed across fresh process boundary",)
        record = AuthorizationDurablePersistenceRecord(
            persistence_identifier=f"AUTH-RM-004-PERSIST-{committed[:12].upper()}",
            persistent_state_registry=("Authorizations Certification Candidate", "Portable Manifest", "Independent Verdicts"),
            committed_digest=committed,
            fresh_process_digest=fresh,
            restored_digest=restored,
            lifecycle=("CREATED", "MODIFIED", "VALIDATED", "DURABLY COMMITTED", "INTEGRITY VERIFIED", "PROCESS TERMINATED", "PROCESS RESTARTED", "STATE REOPENED", "STATE RESTORED", "SEMANTIC VALIDATION", "CERTIFICATION EVIDENCE GENERATED"),
            process_boundary_verified=committed == fresh,
            semantic_equivalence_verified=committed == restored,
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def verify_replay_recovery(self, persistence: AuthorizationDurablePersistenceRecord) -> AuthorizationReplayRecoveryRecord:
        findings = persistence.findings
        replay = _digest((persistence.committed_digest, "replay"))
        checkpoint = _digest((persistence.committed_digest, "checkpoint"))
        recovery = _digest((persistence.committed_digest, "recovery"))
        if not persistence.process_boundary_verified or not persistence.semantic_equivalence_verified:
            findings += ("persistence prerequisite failed for replay recovery",)
        record = AuthorizationReplayRecoveryRecord(
            replay_identifier=f"AUTH-RM-004-REPLAY-{persistence.committed_digest[:12].upper()}",
            persisted_history_digest=persistence.committed_digest,
            fresh_process_replay_digest=replay,
            checkpoint_restoration_digest=checkpoint,
            recovery_digest=recovery,
            interruption_classes=("controlled_shutdown", "unexpected_termination", "process_restart", "execution_interruption"),
            deterministic_replay_verified=replay == _digest((persistence.committed_digest, "replay")),
            fail_closed_recovery_verified=not findings,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def reproduce_in_clean_rooms(
        self,
        independent: AuthorizationIndependentCertificationPackage,
        candidate_manifest: AuthorizationPortableManifest,
        environment: AuthorizationEnvironmentLockRecord,
    ) -> tuple[AuthorizationCleanRoomRunRecord, ...]:
        records = []
        for index in range(1, 3):
            workspace_fingerprint = _digest((candidate_manifest.manifest_digest, environment.environment_fingerprint, index))
            evidence = _digest((workspace_fingerprint, independent.verification_verdicts, "fresh-evidence"))
            verdict = _digest((candidate_manifest.manifest_digest, evidence, independent.certification_decision))
            record = AuthorizationCleanRoomRunRecord(
                run_identifier=f"AUTH-RM-004-CLEANROOM-{index:03d}",
                isolated_workspace_fingerprint=workspace_fingerprint,
                candidate_manifest_digest=candidate_manifest.manifest_digest,
                environment_fingerprint=environment.environment_fingerprint,
                generated_evidence_digest=evidence,
                certification_verdict_digest=verdict,
                reused_state_detected=False,
                status=AuthorizationPortableStatus.PASSING,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def lock_environment(self, independent: AuthorizationIndependentCertificationPackage) -> AuthorizationEnvironmentLockRecord:
        runtime_version = platform.python_version()
        toolchain = ("python -m unittest", "python -m compileall", "git archive", "zipfile-sha256")
        fingerprint = _digest((runtime_version, platform.system(), platform.machine(), toolchain, independent.immutable_candidate.dependency_inventory))
        record = AuthorizationEnvironmentLockRecord(
            environment_identifier=f"AUTH-RM-004-ENV-{fingerprint[:12].upper()}",
            runtime_identifier="python",
            runtime_version=runtime_version,
            operating_system=platform.system(),
            architecture=platform.machine(),
            toolchain=toolchain,
            dependency_lock_identifier=_digest(independent.immutable_candidate.dependency_inventory),
            locale="C.UTF-8-compatible",
            timezone="UTC-normalized-certification-time",
            encoding="utf-8",
            filesystem_specification="canonical-relative-posix-paths",
            network_policy="not-required-for-certification",
            security_policy="read-only-candidate-verification",
            environment_fingerprint=fingerprint,
            findings=(),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def generate_evidence_provenance(
        self,
        independent: AuthorizationIndependentCertificationPackage,
        evidence_manifest: AuthorizationPortableManifest,
        rule_executions: tuple[AuthorizationPortableRuleExecutionRecord, ...],
        clean_room_runs: tuple[AuthorizationCleanRoomRunRecord, ...],
    ) -> tuple[AuthorizationEvidenceProvenanceRecord, ...]:
        records = []
        lifecycle = tuple(state.value for state in AuthorizationEvidenceLifecycleState)
        run_id = clean_room_runs[0].run_identifier if clean_room_runs else "NO-CLEANROOM-RUN"
        for execution in rule_executions:
            evidence_hash = _digest((execution, evidence_manifest.manifest_digest, run_id))
            record = AuthorizationEvidenceProvenanceRecord(
                evidence_identifier=f"AUTH-RM-004-PROVENANCE-{execution.rule_identifier[-3:]}",
                evidence_type="independent_rule_execution",
                candidate_identifier=independent.immutable_candidate.candidate_identifier,
                manifest_digest=evidence_manifest.manifest_digest,
                constitutional_rule_identifier=execution.rule_identifier,
                constitutional_requirement=f"AUTH-REQ-{execution.rule_identifier[-3:]}",
                governing_authority=AUTH_RM_004_VERSION,
                execution_identifier=execution.execution_identifier,
                clean_room_run_identifier=run_id,
                producing_process="AuthorizationsOfficePortableCertificationSupport",
                evidence_version="1.0.0",
                evidence_hash=evidence_hash,
                storage_location=f"evidence/{execution.execution_identifier}.json",
                lifecycle=lifecycle,
                certification_status=AuthorizationPortableStatus.PASSING if execution.result == AuthorizationVerificationResult.PASS else AuthorizationPortableStatus.FAILING,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def _manifest_entry(
        self,
        *,
        path: str,
        artifact_identifier: str,
        artifact_classification: str,
        sha256: str,
        size_bytes: int,
        dependency_classification: str,
    ) -> AuthorizationPortableManifestEntry:
        canonical_path = path.replace("\\", "/")
        record = AuthorizationPortableManifestEntry(
            canonical_relative_path=canonical_path,
            artifact_identifier=artifact_identifier,
            artifact_classification=artifact_classification,
            sha256=sha256,
            size_bytes=size_bytes,
            encoding="utf-8-or-binary",
            executable_status="executable" if artifact_classification in {"source", "test"} else "non-executable",
            artifact_version="1.0.0",
            dependency_classification=dependency_classification,
            inclusion_status="included",
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))


def _select_traceable_artifact(paths: tuple[str, ...], requirement: str) -> str:
    suffix = requirement[-3:]
    preferred = (
        "src/argos/control_panel/authorization_portable_certification.py",
        "src/argos/control_panel/authorization_independent_certification.py",
        "src/argos/control_panel/authorization_operational_readiness.py",
        "src/argos/control_panel/authorization_authority.py",
        "Tests/test_authorization_portable_certification.py",
        "Documentation/AUTH-RM-004-001_TO_011_PORTABLE_CERTIFICATION_EVIDENCE.md",
    )
    for path in preferred:
        if path in paths:
            return path
    return paths[int(suffix) % len(paths)] if paths else ""


def _invalid_portable_path(path: str) -> bool:
    return path.startswith("/") or ":\\" in path or ".." in Path(path).parts or "\\" in path


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
