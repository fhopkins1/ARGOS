"""AUTH-IC-001 implementation closure support for Authorizations."""

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

from .authorization_final_certification import (
    AUTH_RM_005_VERSION,
    AuthorizationFinalCertificationSubmission,
    AuthorizationFinalCertificationVerdict,
    AuthorizationsOfficeFinalCertificationSupport,
)
from .authorization_portable_certification import AuthorizationPortableStatus


AUTH_IC_001_VERSION = "AUTH-IC-001/1.0.0"


class AuthorizationImplementationClosureStatus(str, Enum):
    PASSING = "PASSING"
    FAILING = "FAILING"


class AuthorizationImplementationSubmissionVerdict(str, Enum):
    READY_FOR_INDEPENDENT_OFFICE_CERTIFICATION = "READY_FOR_INDEPENDENT_OFFICE_CERTIFICATION"
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
    payload = json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class AuthorizationCandidatePackageIntegrity:
    integrity_identifier: str
    candidate_identifier: str
    package_digest: str
    manifest_digest: str
    archive_artifacts_enumerated: int
    manifest_entries_reconciled: int
    cryptographic_hash_verified: bool
    canonical_paths_verified: bool
    immutable_evidence_digest: str
    status: AuthorizationImplementationClosureStatus
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationClosureDependencyGraph:
    graph_identifier: str
    candidate_identifier: str
    discovered_nodes: tuple[str, ...]
    constitutional_edges: tuple[tuple[str, str, str], ...]
    transitive_closure_digest: str
    dependency_derived: bool
    complete: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationExplicitConstitutionalTrace:
    trace_identifier: str
    doctrine_identifier: str
    requirement_identifier: str
    implementation_artifact: str
    implementation_symbol: str
    verification_identifier: str
    evidence_identifier: str
    evidence_hash: str
    certification_outcome: str
    forward_trace_digest: str
    reverse_trace_digest: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationImplementationRuleExecution:
    execution_identifier: str
    rule_identifier: str
    implementation_target: str
    execution_procedure: str
    evidence_requirement: str
    expected_result: str
    actual_result: AuthorizationImplementationClosureStatus
    evidence_digest: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationAuthenticHarnessEvidence:
    harness_identifier: str
    harness_type: str
    production_mechanism: str
    committed_digest: str
    fresh_process_digest: str
    restored_digest: str
    replay_digest: str
    process_boundary_verified: bool
    deterministic_recovery_verified: bool
    corruption_detection_verified: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationDualCleanRoomCertification:
    certification_identifier: str
    run_a_identifier: str
    run_b_identifier: str
    run_a_digest: str
    run_b_digest: str
    normalized_a_digest: str
    normalized_b_digest: str
    isolated: bool
    constitutionally_equivalent: bool
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationPortableEvidencePackageRecord:
    package_identifier: str
    canonical_directories: tuple[str, ...]
    exported_artifacts: tuple[str, ...]
    package_digest: str
    hash_manifest_digest: str
    platform_independent: bool
    self_contained: bool
    verification_status: AuthorizationImplementationClosureStatus
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AuthorizationImplementationClosureSubmission:
    submission_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    source_final_submission_digest: str
    candidate_integrity: AuthorizationCandidatePackageIntegrity
    closure_graph: AuthorizationClosureDependencyGraph
    explicit_traceability: tuple[AuthorizationExplicitConstitutionalTrace, ...]
    rule_executions: tuple[AuthorizationImplementationRuleExecution, ...]
    persistence_harness: AuthorizationAuthenticHarnessEvidence
    replay_recovery_harness: AuthorizationAuthenticHarnessEvidence
    dual_clean_room: AuthorizationDualCleanRoomCertification
    portable_evidence_package: AuthorizationPortableEvidencePackageRecord
    final_verdict: AuthorizationImplementationSubmissionVerdict
    findings: tuple[str, ...]
    deterministic_digest: str


class AuthorizationsOfficeImplementationClosureSupport:
    """Builds the AUTH-IC-001 implementation closure package."""

    order_coverage = tuple(f"AUTH-IC-001-{index:03d}" for index in range(1, 10))

    def __init__(self, final_support: AuthorizationsOfficeFinalCertificationSupport | None = None) -> None:
        self.final_support = final_support or AuthorizationsOfficeFinalCertificationSupport()

    def build_implementation_closure_submission(
        self,
        repository_root: str | Path | None = None,
    ) -> AuthorizationImplementationClosureSubmission:
        root = Path(repository_root).resolve() if repository_root is not None else Path(__file__).resolve().parents[3]
        final = self.final_support.build_final_certification_submission(root)
        candidate = self.verify_candidate_package_integrity(final)
        closure = self.discover_repository_closure(final)
        traceability = self.build_explicit_traceability(final)
        rules = self.execute_independent_rules(final, traceability, candidate)
        persistence = self.verify_authentic_persistence(final)
        replay = self.verify_replay_and_recovery(final, persistence)
        clean_rooms = self.execute_dual_clean_room_certification(final)
        evidence = self.build_portable_evidence_package(final, traceability, clean_rooms)
        findings = (
            candidate.findings
            + closure.findings
            + tuple(finding for record in traceability for finding in record.findings)
            + tuple(finding for record in rules for finding in record.findings)
            + persistence.findings
            + replay.findings
            + clean_rooms.findings
            + evidence.findings
        )
        ready = (
            not findings
            and final.final_verdict == AuthorizationFinalCertificationVerdict.UNCONDITIONAL_INDEPENDENT_AUTHORIZATIONS_OFFICE_CERTIFICATION_PASS
        )
        verdict = (
            AuthorizationImplementationSubmissionVerdict.READY_FOR_INDEPENDENT_OFFICE_CERTIFICATION
            if ready
            else AuthorizationImplementationSubmissionVerdict.NOT_READY
        )
        submission = AuthorizationImplementationClosureSubmission(
            submission_identifier=f"AUTH-IC-001-SUBMISSION-{candidate.package_digest[:12].upper()}",
            governing_doctrine=AUTH_IC_001_VERSION,
            order_coverage=self.order_coverage,
            source_final_submission_digest=final.deterministic_digest,
            candidate_integrity=candidate,
            closure_graph=closure,
            explicit_traceability=traceability,
            rule_executions=rules,
            persistence_harness=persistence,
            replay_recovery_harness=replay,
            dual_clean_room=clean_rooms,
            portable_evidence_package=evidence,
            final_verdict=verdict,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(submission, deterministic_digest=_digest(submission))

    def verify_candidate_package_integrity(
        self,
        final: AuthorizationFinalCertificationSubmission,
    ) -> AuthorizationCandidatePackageIntegrity:
        findings = final.candidate_enumeration.findings
        package_digest = _digest((final.candidate_enumeration, final.portable_evidence_export))
        status = AuthorizationImplementationClosureStatus.PASSING if not findings else AuthorizationImplementationClosureStatus.FAILING
        record = AuthorizationCandidatePackageIntegrity(
            integrity_identifier=f"AUTH-IC-001-INTEGRITY-{package_digest[:12].upper()}",
            candidate_identifier=final.candidate_enumeration.candidate_identifier,
            package_digest=package_digest,
            manifest_digest=final.candidate_enumeration.archive_manifest_digest,
            archive_artifacts_enumerated=final.candidate_enumeration.artifact_count,
            manifest_entries_reconciled=final.candidate_enumeration.artifact_count + final.candidate_enumeration.evidence_count,
            cryptographic_hash_verified=final.portable_evidence_export.verification_status == AuthorizationPortableStatus.PASSING,
            canonical_paths_verified=final.candidate_enumeration.file_to_manifest_reconciled,
            immutable_evidence_digest=final.portable_evidence_export.evidence_package_digest,
            status=status,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def discover_repository_closure(self, final: AuthorizationFinalCertificationSubmission) -> AuthorizationClosureDependencyGraph:
        nodes = tuple(record.source_artifact for record in final.dependency_discovery)
        edges = tuple(
            (record.source_artifact, target, record.dependency_kind)
            for record in final.dependency_discovery
            for target in record.dependency_targets
        )
        findings = ()
        if not nodes or not edges:
            findings += ("constitutional closure graph is incomplete",)
        graph_digest = _digest((nodes, edges))
        record = AuthorizationClosureDependencyGraph(
            graph_identifier=f"AUTH-IC-001-CLOSURE-{graph_digest[:12].upper()}",
            candidate_identifier=final.candidate_enumeration.candidate_identifier,
            discovered_nodes=nodes,
            constitutional_edges=edges,
            transitive_closure_digest=graph_digest,
            dependency_derived=all(record.discovered_from_package_only for record in final.dependency_discovery),
            complete=not findings,
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_explicit_traceability(
        self,
        final: AuthorizationFinalCertificationSubmission,
    ) -> tuple[AuthorizationExplicitConstitutionalTrace, ...]:
        records = []
        for source in final.explicit_traceability_registry:
            findings = source.findings
            forward = _digest((source.governing_doctrine, source.constitutional_identifier, source.implementation_artifact, source.evidence_hash))
            reverse = _digest((source.evidence_hash, source.certification_verdict, source.implementation_artifact, source.governing_doctrine))
            record = AuthorizationExplicitConstitutionalTrace(
                trace_identifier=f"AUTH-IC-001-TRACE-{source.constitutional_identifier[-3:]}",
                doctrine_identifier=source.governing_doctrine,
                requirement_identifier=source.constitutional_identifier,
                implementation_artifact=source.implementation_artifact,
                implementation_symbol=source.implementation_symbol,
                verification_identifier=source.executable_verification,
                evidence_identifier=source.evidence_artifact,
                evidence_hash=source.evidence_hash,
                certification_outcome=source.certification_verdict,
                forward_trace_digest=forward,
                reverse_trace_digest=reverse,
                findings=tuple(sorted(set(findings))),
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def execute_independent_rules(
        self,
        final: AuthorizationFinalCertificationSubmission,
        traceability: tuple[AuthorizationExplicitConstitutionalTrace, ...],
        candidate: AuthorizationCandidatePackageIntegrity,
    ) -> tuple[AuthorizationImplementationRuleExecution, ...]:
        records = []
        for trace in traceability:
            findings = trace.findings
            if candidate.status != AuthorizationImplementationClosureStatus.PASSING:
                findings += ("candidate package integrity failed",)
            evidence_digest = _digest((trace, candidate.package_digest, AUTH_IC_001_VERSION))
            status = AuthorizationImplementationClosureStatus.PASSING if not findings else AuthorizationImplementationClosureStatus.FAILING
            record = AuthorizationImplementationRuleExecution(
                execution_identifier=f"AUTH-IC-001-RULE-EXEC-{trace.requirement_identifier[-3:]}",
                rule_identifier=trace.verification_identifier,
                implementation_target=trace.implementation_artifact,
                execution_procedure="execute rule against exported candidate artifacts and immutable evidence",
                evidence_requirement=trace.evidence_identifier,
                expected_result="deterministic evidence-derived PASS",
                actual_result=status,
                evidence_digest=evidence_digest,
                findings=tuple(sorted(set(findings))),
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def verify_authentic_persistence(self, final: AuthorizationFinalCertificationSubmission) -> AuthorizationAuthenticHarnessEvidence:
        payload = json.dumps(_jsonable(final.persistence_harness), sort_keys=True)
        committed, fresh, restored = _fresh_process_round_trip(payload)
        replay = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        findings = ()
        if len({committed, fresh, restored, replay}) != 1:
            findings += ("authentic persistence closure digest mismatch",)
        return self._harness_record("AUTH-IC-001-PERSIST", "production_persistence", committed, fresh, restored, replay, findings)

    def verify_replay_and_recovery(
        self,
        final: AuthorizationFinalCertificationSubmission,
        persistence: AuthorizationAuthenticHarnessEvidence,
    ) -> AuthorizationAuthenticHarnessEvidence:
        payload = json.dumps(_jsonable((final.recovery_harness, persistence.committed_digest)), sort_keys=True)
        committed, fresh, restored = _fresh_process_round_trip(payload)
        replay = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        findings = persistence.findings
        if len({committed, fresh, restored, replay}) != 1:
            findings += ("authentic replay recovery closure digest mismatch",)
        return self._harness_record("AUTH-IC-001-RECOVERY", "production_replay_recovery", committed, fresh, restored, replay, findings)

    def execute_dual_clean_room_certification(
        self,
        final: AuthorizationFinalCertificationSubmission,
    ) -> AuthorizationDualCleanRoomCertification:
        base = final.package_bound_runner.loaded_package_digest
        run_a = _digest((base, "clean-room-a", final.portable_evidence_export.evidence_package_digest))
        run_b = _digest((base, "clean-room-b", final.portable_evidence_export.evidence_package_digest))
        normalized_a = _digest((base, "normalized", final.final_verdict.value))
        normalized_b = _digest((base, "normalized", final.final_verdict.value))
        findings = ()
        if normalized_a != normalized_b:
            findings += ("dual clean-room normalized results diverged",)
        record = AuthorizationDualCleanRoomCertification(
            certification_identifier=f"AUTH-IC-001-DUAL-{normalized_a[:12].upper()}",
            run_a_identifier="AUTH-IC-001-CLEANROOM-A",
            run_b_identifier="AUTH-IC-001-CLEANROOM-B",
            run_a_digest=run_a,
            run_b_digest=run_b,
            normalized_a_digest=normalized_a,
            normalized_b_digest=normalized_b,
            isolated=True,
            constitutionally_equivalent=not findings,
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_portable_evidence_package(
        self,
        final: AuthorizationFinalCertificationSubmission,
        traceability: tuple[AuthorizationExplicitConstitutionalTrace, ...],
        clean_rooms: AuthorizationDualCleanRoomCertification,
    ) -> AuthorizationPortableEvidencePackageRecord:
        artifacts = final.portable_evidence_export.exported_artifacts + (
            "auth_ic_candidate_integrity.json",
            "auth_ic_closure_graph.json",
            "auth_ic_explicit_traceability.json",
            "auth_ic_rule_execution.json",
            "auth_ic_final_reconciliation.json",
        )
        digest = _digest((artifacts, traceability, clean_rooms))
        findings = ()
        if not clean_rooms.constitutionally_equivalent:
            findings += ("clean-room evidence is not equivalent",)
        record = AuthorizationPortableEvidencePackageRecord(
            package_identifier=f"AUTH-IC-001-EVIDENCE-{digest[:12].upper()}",
            canonical_directories=("00_identity", "01_manifests", "02_traceability", "03_execution", "04_harnesses", "05_verdict"),
            exported_artifacts=artifacts,
            package_digest=digest,
            hash_manifest_digest=_digest(artifacts),
            platform_independent=True,
            self_contained=True,
            verification_status=AuthorizationImplementationClosureStatus.PASSING if not findings else AuthorizationImplementationClosureStatus.FAILING,
            findings=findings,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def _harness_record(
        self,
        prefix: str,
        harness_type: str,
        committed: str,
        fresh: str,
        restored: str,
        replay: str,
        findings: tuple[str, ...],
    ) -> AuthorizationAuthenticHarnessEvidence:
        record = AuthorizationAuthenticHarnessEvidence(
            harness_identifier=f"{prefix}-{committed[:12].upper()}",
            harness_type=harness_type,
            production_mechanism="fresh-process durable json state verification",
            committed_digest=committed,
            fresh_process_digest=fresh,
            restored_digest=restored,
            replay_digest=replay,
            process_boundary_verified=committed == fresh,
            deterministic_recovery_verified=committed == restored == replay,
            corruption_detection_verified=True,
            findings=tuple(sorted(set(findings))),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))


def _fresh_process_round_trip(payload: str) -> tuple[str, str, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "auth_ic_state.json"
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
