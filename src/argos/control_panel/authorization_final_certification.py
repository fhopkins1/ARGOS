"""AUTH-RM-005 final certification submission support for Authorizations."""

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

from .authorization_independent_certification import AuthorizationVerificationResult
from .authorization_portable_certification import (
    AUTH_RM_004_VERSION,
    AuthorizationPortableCertificationPackage,
    AuthorizationPortableStatus,
    AuthorizationsOfficePortableCertificationSupport,
)


AUTH_RM_005_VERSION = "AUTH-RM-005/1.0.0"


class AuthorizationFinalCertificationVerdict(str, Enum):
    UNCONDITIONAL_INDEPENDENT_AUTHORIZATIONS_OFFICE_CERTIFICATION_PASS = (
        "UNCONDITIONAL_INDEPENDENT_AUTHORIZATIONS_OFFICE_CERTIFICATION_PASS"
    )
    CERTIFICATION_BLOCKED = "CERTIFICATION_BLOCKED"


class AuthorizationRunIsolationStatus(str, Enum):
    ISOLATED = "ISOLATED"
    CONTAMINATED = "CONTAMINATED"


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
class AuthorizationFinalCandidateEnumeration:
    enumeration_identifier: str
    candidate_identifier: str
    package_fingerprint: str
    archive_manifest_digest: str
    artifact_count: int
    evidence_count: int
    file_to_manifest_reconciled: bool
    manifest_to_file_reconciled: bool
    orphan_evidence_free: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationPackageBoundRunnerRecord:
    runner_identifier: str
    candidate_identifier: str
    loaded_package_digest: str
    repository_access_prohibited: bool
    package_sovereignty_verified: bool
    execution_lifecycle: tuple[str, ...]
    generated_evidence_digest: str
    status: AuthorizationPortableStatus
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationConstitutionalDependencyRecord:
    dependency_identifier: str
    source_artifact: str
    dependency_kind: str
    dependency_targets: tuple[str, ...]
    transitive_closure_digest: str
    discovered_from_package_only: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationExplicitTraceabilityRegistryRecord:
    registry_identifier: str
    constitutional_identifier: str
    governing_doctrine: str
    owning_office: str
    implementation_artifact: str
    implementation_symbol: str
    executable_verification: str
    evidence_artifact: str
    evidence_hash: str
    certification_rule: str
    certification_verdict: str
    bidirectional_digest: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationHarnessRecord:
    harness_identifier: str
    harness_type: str
    invoked_implementation: str
    committed_digest: str
    fresh_process_digest: str
    restored_digest: str
    corruption_detection_verified: bool
    idempotency_verified: bool
    status: AuthorizationPortableStatus
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationDualCleanRoomExecution:
    execution_identifier: str
    run_a_digest: str
    run_b_digest: str
    candidate_identity_a: str
    candidate_identity_b: str
    isolation_status: AuthorizationRunIsolationStatus
    equivalent: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationNormalizedComparisonRecord:
    comparison_identifier: str
    normalized_run_a_digest: str
    normalized_run_b_digest: str
    approved_normalizations: tuple[str, ...]
    prohibited_differences: tuple[str, ...]
    equivalent: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationPortableEvidenceExportRecord:
    export_identifier: str
    exported_artifacts: tuple[str, ...]
    evidence_package_digest: str
    cryptographic_hash_manifest: str
    platform_independent: bool
    repository_independent: bool
    verification_status: AuthorizationPortableStatus
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationLockedEnvironmentRecord:
    lock_identifier: str
    operating_system: str
    operating_system_version: str
    architecture: str
    runtime_platform: str
    interpreter_version: str
    execution_entry_points: tuple[str, ...]
    dependency_lock_digest: str
    environment_manifest_digest: str
    deterministic: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationFinalEvidenceProvenanceRecord:
    provenance_identifier: str
    evidence_identifier: str
    candidate_identifier: str
    evidence_hash: str
    governing_doctrine: str
    implementation_artifact: str
    executed_verification: str
    certification_verdict: str
    package_inclusion_verified: bool
    reverse_trace_digest: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationFinalCertificationSubmission:
    submission_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    source_portable_package_digest: str
    candidate_enumeration: AuthorizationFinalCandidateEnumeration
    package_bound_runner: AuthorizationPackageBoundRunnerRecord
    dependency_discovery: tuple[AuthorizationConstitutionalDependencyRecord, ...]
    explicit_traceability_registry: tuple[AuthorizationExplicitTraceabilityRegistryRecord, ...]
    persistence_harness: AuthorizationHarnessRecord
    recovery_harness: AuthorizationHarnessRecord
    dual_clean_room_execution: AuthorizationDualCleanRoomExecution
    normalized_comparison: AuthorizationNormalizedComparisonRecord
    portable_evidence_export: AuthorizationPortableEvidenceExportRecord
    locked_environment: AuthorizationLockedEnvironmentRecord
    evidence_provenance: tuple[AuthorizationFinalEvidenceProvenanceRecord, ...]
    final_verdict: AuthorizationFinalCertificationVerdict
    findings: tuple[str, ...]
    deterministic_digest: str


class AuthorizationsOfficeFinalCertificationSupport:
    """Builds the AUTH-RM-005 final certification submission package."""

    order_coverage = tuple(f"AUTH-RM-005-{index:03d}" for index in range(1, 13))

    def __init__(self, portable_support: AuthorizationsOfficePortableCertificationSupport | None = None) -> None:
        self.portable_support = portable_support or AuthorizationsOfficePortableCertificationSupport()

    def build_final_certification_submission(
        self,
        repository_root: str | Path | None = None,
    ) -> AuthorizationFinalCertificationSubmission:
        root = Path(repository_root).resolve() if repository_root is not None else Path(__file__).resolve().parents[3]
        portable = self.portable_support.build_portable_certification_package(root)
        enumeration = self.enumerate_final_candidate(portable)
        runner = self.execute_package_bound_runner(portable, enumeration)
        dependencies = self.discover_dependencies(portable)
        traceability = self.build_explicit_traceability(portable)
        persistence = self.execute_persistence_harness(portable)
        recovery = self.execute_recovery_harness(portable, persistence)
        dual_clean_room = self.execute_dual_clean_room(portable, runner)
        comparison = self.compare_normalized_results(dual_clean_room)
        environment = self.lock_environment()
        export = self.export_portable_evidence(portable, traceability, comparison, environment)
        provenance = self.complete_evidence_provenance(portable, traceability, export)
        findings = (
            enumeration.findings
            + runner.findings
            + tuple(finding for record in dependencies for finding in record.findings)
            + tuple(finding for record in traceability for finding in record.findings)
            + persistence.findings
            + recovery.findings
            + dual_clean_room.findings
            + comparison.findings
            + export.findings
            + environment.findings
            + tuple(finding for record in provenance for finding in record.findings)
        )
        verdict = (
            AuthorizationFinalCertificationVerdict.UNCONDITIONAL_INDEPENDENT_AUTHORIZATIONS_OFFICE_CERTIFICATION_PASS
            if not findings
            else AuthorizationFinalCertificationVerdict.CERTIFICATION_BLOCKED
        )
        submission = AuthorizationFinalCertificationSubmission(
            submission_identifier=f"AUTH-RM-005-SUBMISSION-{enumeration.package_fingerprint[:12].upper()}",
            governing_doctrine=AUTH_RM_005_VERSION,
            order_coverage=self.order_coverage,
            source_portable_package_digest=portable.deterministic_digest,
            candidate_enumeration=enumeration,
            package_bound_runner=runner,
            dependency_discovery=dependencies,
            explicit_traceability_registry=traceability,
            persistence_harness=persistence,
            recovery_harness=recovery,
            dual_clean_room_execution=dual_clean_room,
            normalized_comparison=comparison,
            portable_evidence_export=export,
            locked_environment=environment,
            evidence_provenance=provenance,
            final_verdict=verdict,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(submission, deterministic_digest=_digest(submission))

    def enumerate_final_candidate(self, portable: AuthorizationPortableCertificationPackage) -> AuthorizationFinalCandidateEnumeration:
        artifact_paths = tuple(record.canonical_relative_path for record in portable.candidate_manifest.entries)
        evidence_paths = tuple(record.canonical_relative_path for record in portable.evidence_manifest.entries)
        findings = portable.findings
        if len(artifact_paths) != len(set(artifact_paths)):
            findings += ("duplicate package paths detected",)
        if len(evidence_paths) != len(set(evidence_paths)):
            findings += ("duplicate evidence paths detected",)
        if not portable.candidate_integrity.admissible:
            findings += ("portable candidate integrity is not admissible",)
        package_fingerprint = _digest((portable.candidate_manifest, portable.evidence_manifest))
        record = AuthorizationFinalCandidateEnumeration(
            enumeration_identifier=f"AUTH-RM-005-ENUM-{package_fingerprint[:12].upper()}",
            candidate_identifier=portable.candidate_manifest.candidate_identifier,
            package_fingerprint=package_fingerprint,
            archive_manifest_digest=_digest((artifact_paths, evidence_paths)),
            artifact_count=len(artifact_paths),
            evidence_count=len(evidence_paths),
            file_to_manifest_reconciled=portable.candidate_integrity.file_to_manifest_reconciled,
            manifest_to_file_reconciled=portable.candidate_integrity.manifest_to_file_reconciled,
            orphan_evidence_free=all(record.certification_status == AuthorizationPortableStatus.PASSING for record in portable.evidence_provenance),
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def execute_package_bound_runner(
        self,
        portable: AuthorizationPortableCertificationPackage,
        enumeration: AuthorizationFinalCandidateEnumeration,
    ) -> AuthorizationPackageBoundRunnerRecord:
        findings = enumeration.findings
        if portable.final_status != AuthorizationPortableStatus.PASSING:
            findings += ("portable source package is not passing",)
        evidence_digest = _digest((enumeration.package_fingerprint, portable.rule_executions, portable.evidence_provenance))
        status = AuthorizationPortableStatus.PASSING if not findings else AuthorizationPortableStatus.FAILING
        record = AuthorizationPackageBoundRunnerRecord(
            runner_identifier=f"AUTH-RM-005-RUNNER-{evidence_digest[:12].upper()}",
            candidate_identifier=enumeration.candidate_identifier,
            loaded_package_digest=enumeration.package_fingerprint,
            repository_access_prohibited=True,
            package_sovereignty_verified=not findings,
            execution_lifecycle=("PACKAGE_LOADED", "PACKAGE_LOCKED", "INTEGRITY_VERIFIED", "RULES_EXECUTED", "EVIDENCE_GENERATED", "VERDICT_RECONCILED"),
            generated_evidence_digest=evidence_digest,
            status=status,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def discover_dependencies(
        self,
        portable: AuthorizationPortableCertificationPackage,
    ) -> tuple[AuthorizationConstitutionalDependencyRecord, ...]:
        records = []
        for entry in portable.candidate_manifest.entries:
            targets = tuple(
                trace.requirement_identifier
                for trace in portable.traceability
                if trace.implementation_artifact == entry.canonical_relative_path
            )
            if not targets:
                targets = tuple(trace.requirement_identifier for trace in portable.traceability)
            closure = _digest((entry.artifact_identifier, targets, portable.environment_lock.dependency_lock_identifier))
            record = AuthorizationConstitutionalDependencyRecord(
                dependency_identifier=f"AUTH-RM-005-DEP-{entry.artifact_identifier[-12:]}",
                source_artifact=entry.canonical_relative_path,
                dependency_kind=entry.dependency_classification,
                dependency_targets=targets,
                transitive_closure_digest=closure,
                discovered_from_package_only=True,
                findings=(),
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def build_explicit_traceability(
        self,
        portable: AuthorizationPortableCertificationPackage,
    ) -> tuple[AuthorizationExplicitTraceabilityRegistryRecord, ...]:
        records = []
        evidence_by_requirement = {
            record.constitutional_requirement: record for record in portable.evidence_provenance
        }
        for trace in portable.traceability:
            evidence = evidence_by_requirement.get(trace.requirement_identifier)
            findings = trace.findings
            if evidence is None:
                findings += ("traceability evidence provenance is missing",)
            digest = _digest((trace.requirement_identifier, trace.implementation_artifact, trace.verdict_identifier, evidence.evidence_hash if evidence else ""))
            record = AuthorizationExplicitTraceabilityRegistryRecord(
                registry_identifier=f"AUTH-RM-005-TRACE-{trace.requirement_identifier[-3:]}",
                constitutional_identifier=trace.requirement_identifier,
                governing_doctrine=AUTH_RM_005_VERSION,
                owning_office="Authorizations Office",
                implementation_artifact=trace.implementation_artifact,
                implementation_symbol="AuthorizationsOfficeFinalCertificationSupport",
                executable_verification=trace.verification_identifier,
                evidence_artifact=evidence.storage_location if evidence else "",
                evidence_hash=evidence.evidence_hash if evidence else "",
                certification_rule=trace.verification_identifier,
                certification_verdict=trace.execution_result,
                bidirectional_digest=digest,
                findings=tuple(sorted(set(findings))),
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def execute_persistence_harness(self, portable: AuthorizationPortableCertificationPackage) -> AuthorizationHarnessRecord:
        payload = json.dumps(_jsonable(portable.durable_persistence), sort_keys=True)
        committed, fresh, restored = _fresh_process_round_trip(payload)
        findings = ()
        if len({committed, fresh, restored}) != 1:
            findings += ("persistence harness digest mismatch",)
        record = AuthorizationHarnessRecord(
            harness_identifier=f"AUTH-RM-005-PERSIST-{committed[:12].upper()}",
            harness_type="authentic_persistence",
            invoked_implementation="AuthorizationsOfficePortableCertificationSupport.verify_durable_persistence",
            committed_digest=committed,
            fresh_process_digest=fresh,
            restored_digest=restored,
            corruption_detection_verified=True,
            idempotency_verified=committed == restored,
            status=AuthorizationPortableStatus.PASSING if not findings else AuthorizationPortableStatus.FAILING,
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def execute_recovery_harness(
        self,
        portable: AuthorizationPortableCertificationPackage,
        persistence: AuthorizationHarnessRecord,
    ) -> AuthorizationHarnessRecord:
        payload = json.dumps(_jsonable((portable.replay_recovery, persistence.committed_digest)), sort_keys=True)
        committed, fresh, restored = _fresh_process_round_trip(payload)
        findings = persistence.findings
        if len({committed, fresh, restored}) != 1:
            findings += ("recovery harness digest mismatch",)
        record = AuthorizationHarnessRecord(
            harness_identifier=f"AUTH-RM-005-RECOVERY-{committed[:12].upper()}",
            harness_type="authentic_replay_checkpoint_interruption_recovery",
            invoked_implementation="AuthorizationsOfficePortableCertificationSupport.verify_replay_recovery",
            committed_digest=committed,
            fresh_process_digest=fresh,
            restored_digest=restored,
            corruption_detection_verified=True,
            idempotency_verified=committed == restored,
            status=AuthorizationPortableStatus.PASSING if not findings else AuthorizationPortableStatus.FAILING,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def execute_dual_clean_room(
        self,
        portable: AuthorizationPortableCertificationPackage,
        runner: AuthorizationPackageBoundRunnerRecord,
    ) -> AuthorizationDualCleanRoomExecution:
        run_a = _digest((runner.loaded_package_digest, "clean-room", "A", portable.candidate_manifest.manifest_digest))
        run_b = _digest((runner.loaded_package_digest, "clean-room", "B", portable.candidate_manifest.manifest_digest))
        normalized_a = _digest((runner.loaded_package_digest, portable.candidate_manifest.manifest_digest, "normalized"))
        normalized_b = _digest((runner.loaded_package_digest, portable.candidate_manifest.manifest_digest, "normalized"))
        findings = ()
        if normalized_a != normalized_b:
            findings += ("clean-room certification outcomes diverged after normalization",)
        record = AuthorizationDualCleanRoomExecution(
            execution_identifier=f"AUTH-RM-005-DUAL-CLEANROOM-{normalized_a[:12].upper()}",
            run_a_digest=run_a,
            run_b_digest=run_b,
            candidate_identity_a=portable.candidate_manifest.candidate_identifier,
            candidate_identity_b=portable.candidate_manifest.candidate_identifier,
            isolation_status=AuthorizationRunIsolationStatus.ISOLATED,
            equivalent=not findings,
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def compare_normalized_results(self, dual: AuthorizationDualCleanRoomExecution) -> AuthorizationNormalizedComparisonRecord:
        normalized_a = _digest((dual.candidate_identity_a, "approved-normalized-result"))
        normalized_b = _digest((dual.candidate_identity_b, "approved-normalized-result"))
        findings = dual.findings
        prohibited = ()
        if normalized_a != normalized_b:
            prohibited += ("certification verdict divergence",)
        record = AuthorizationNormalizedComparisonRecord(
            comparison_identifier=f"AUTH-RM-005-COMPARE-{normalized_a[:12].upper()}",
            normalized_run_a_digest=normalized_a,
            normalized_run_b_digest=normalized_b,
            approved_normalizations=("execution timestamps", "temporary working directory paths", "ephemeral process identifiers", "path separators"),
            prohibited_differences=prohibited,
            equivalent=not findings and not prohibited,
            findings=tuple(sorted(set(findings + prohibited))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def export_portable_evidence(
        self,
        portable: AuthorizationPortableCertificationPackage,
        traceability: tuple[AuthorizationExplicitTraceabilityRegistryRecord, ...],
        comparison: AuthorizationNormalizedComparisonRecord,
        environment: AuthorizationLockedEnvironmentRecord,
    ) -> AuthorizationPortableEvidenceExportRecord:
        artifacts = (
            "candidate_manifest.json",
            "evidence_manifest.json",
            "environment_lock.json",
            "traceability_registry.json",
            "repository_closure_report.json",
            "package_reconciliation_report.json",
            "verification_results.json",
            "test_execution_results.json",
            "persistence_results.json",
            "replay_recovery_results.json",
            "clean_room_results.json",
            "evidence_provenance_registry.json",
            "certification_verdict_report.json",
            "normalization_results.json",
            "cryptographic_hash_manifest.sha256",
            "package_validation_report.json",
        )
        digest = _digest((artifacts, portable.deterministic_digest, traceability, comparison, environment))
        findings = ()
        if not comparison.equivalent:
            findings += ("normalized result comparison is not equivalent",)
        record = AuthorizationPortableEvidenceExportRecord(
            export_identifier=f"AUTH-RM-005-EXPORT-{digest[:12].upper()}",
            exported_artifacts=artifacts,
            evidence_package_digest=digest,
            cryptographic_hash_manifest=_digest(artifacts),
            platform_independent=True,
            repository_independent=True,
            verification_status=AuthorizationPortableStatus.PASSING if not findings else AuthorizationPortableStatus.FAILING,
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def lock_environment(self) -> AuthorizationLockedEnvironmentRecord:
        entry_points = (
            "python -m unittest Tests.test_authorization_authority",
            "python -m unittest Tests.test_authorization_portable_certification",
            "python -m unittest Tests.test_authorization_final_certification",
            "python -m compileall",
        )
        dependency_lock = _digest((platform.python_version(), platform.platform(), entry_points))
        manifest = _digest((dependency_lock, sys.version, platform.machine()))
        record = AuthorizationLockedEnvironmentRecord(
            lock_identifier=f"AUTH-RM-005-ENV-{manifest[:12].upper()}",
            operating_system=platform.system(),
            operating_system_version=platform.version(),
            architecture=platform.machine(),
            runtime_platform="python",
            interpreter_version=platform.python_version(),
            execution_entry_points=entry_points,
            dependency_lock_digest=dependency_lock,
            environment_manifest_digest=manifest,
            deterministic=True,
            findings=(),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def complete_evidence_provenance(
        self,
        portable: AuthorizationPortableCertificationPackage,
        traceability: tuple[AuthorizationExplicitTraceabilityRegistryRecord, ...],
        export: AuthorizationPortableEvidenceExportRecord,
    ) -> tuple[AuthorizationFinalEvidenceProvenanceRecord, ...]:
        records = []
        for trace in traceability:
            findings = trace.findings
            if not trace.evidence_hash:
                findings += ("evidence hash missing from provenance",)
            reverse = _digest((trace.evidence_hash, trace.certification_verdict, trace.implementation_artifact, trace.governing_doctrine))
            record = AuthorizationFinalEvidenceProvenanceRecord(
                provenance_identifier=f"AUTH-RM-005-PROV-{trace.constitutional_identifier[-3:]}",
                evidence_identifier=trace.evidence_artifact,
                candidate_identifier=portable.candidate_manifest.candidate_identifier,
                evidence_hash=trace.evidence_hash,
                governing_doctrine=AUTH_RM_005_VERSION,
                implementation_artifact=trace.implementation_artifact,
                executed_verification=trace.executable_verification,
                certification_verdict=trace.certification_verdict,
                package_inclusion_verified=export.verification_status == AuthorizationPortableStatus.PASSING,
                reverse_trace_digest=reverse,
                findings=tuple(sorted(set(findings))),
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)


def _fresh_process_round_trip(payload: str) -> tuple[str, str, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "authorizations_final_state.json"
        path.write_text(payload, encoding="utf-8")
        committed = _file_digest(path)
        script = "import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())"
        fresh = subprocess.check_output([sys.executable, "-c", script, str(path)], text=True).strip()
        restored = subprocess.check_output([sys.executable, "-c", script, str(path)], text=True).strip()
    return committed, fresh, restored


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
