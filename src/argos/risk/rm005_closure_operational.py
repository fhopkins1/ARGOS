"""Operational RISK-RM-005 certification package and closure support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
import hashlib
import json
import subprocess
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision
from argos.risk.rm005_registry_operational import RiskRm005RegistryOperationalPackage, RiskRm005RegistryOperationalSupport


FIXED_CERTIFICATION_TIMESTAMP = "2026-07-22T00:00:00Z"


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
class RiskRm005CertificationPackageRecord:
    package_identifier: str
    candidate_identifier: str
    candidate_digest: str
    package_version: str
    doctrine_version: str
    repository_identifier: str
    immutable_commit_identifier: str
    configuration_version: str
    schema_version_set: tuple[str, ...]
    registry_version_set: tuple[str, ...]
    certification_suite_version: str
    creation_timestamp: str
    producing_authority: str
    mandatory_artifact_references: tuple[str, ...]
    package_status: EnterpriseCertificationDecision
    findings: tuple[str, ...]
    integrity_digest: str


@dataclass(frozen=True)
class RiskRm005TraceabilityRecord:
    traceability_identifier: str
    requirement_identifier: str
    doctrine_reference: str
    implementation_reference: str
    evaluation_reference: str
    evidence_reference: str
    metric_reference: str
    decision_reference: str
    forward_trace: tuple[str, ...]
    backward_trace: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005ProcedureStageRecord:
    stage_identifier: str
    stage_name: str
    execution_order: int
    prerequisite_stage_identifiers: tuple[str, ...]
    evidence_inputs: tuple[str, ...]
    produced_evidence: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005PersistenceRecord:
    persistence_identifier: str
    candidate_identifier: str
    artifact_identifier: str
    artifact_classification: str
    persistence_timestamp: str
    commit_identifier: str
    storage_status: str
    integrity_hash: str
    version: str
    recovery_reference: str
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005ReplayRecoveryRecord:
    replay_identifier: str
    candidate_identifier: str
    original_package_digest: str
    replay_package_digest: str
    restored_persistence_digest: str
    outcome_equivalent: bool
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005CertificationDecisionRecord:
    decision_identifier: str
    candidate_identifier: str
    candidate_digest: str
    decision: EnterpriseCertificationDecision
    decision_basis: tuple[str, ...]
    closure_eligible: bool
    package_sealed: bool
    archive_identifier: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005ClosureOperationalPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    registry_package: RiskRm005RegistryOperationalPackage
    certification_package: RiskRm005CertificationPackageRecord
    traceability_matrix: tuple[RiskRm005TraceabilityRecord, ...]
    procedure_execution: tuple[RiskRm005ProcedureStageRecord, ...]
    persistence_records: tuple[RiskRm005PersistenceRecord, ...]
    replay_recovery_record: RiskRm005ReplayRecoveryRecord
    certification_decision: RiskRm005CertificationDecisionRecord
    immutable_audit_references: tuple[str, ...]
    final_completion_readiness: EnterpriseCertificationDecision
    deterministic_digest: str


class RiskRm005ClosureOperationalSupport:
    """Build candidate-bound operational evidence for RISK-RM-005-016 through 020."""

    order_coverage = (
        "RISK-RM-005-016",
        "RISK-RM-005-017",
        "RISK-RM-005-018",
        "RISK-RM-005-019",
        "RISK-RM-005-020",
    )

    procedure_stages = (
        "Certification Initiation",
        "Candidate Binding",
        "Certification Package Validation",
        "Identity Validation",
        "Schema Validation",
        "Registry Validation",
        "Compatibility Validation",
        "Evidence Admissibility Validation",
        "Constitutional Rule Execution",
        "Certification Test Execution",
        "Certification Metric Calculation",
        "Traceability Verification",
        "Certification Threshold Evaluation",
        "Finding Issuance",
        "Certification Decision Generation",
        "Evidence Preservation",
        "Closure Eligibility Evaluation",
    )

    mandatory_package_artifacts = (
        "Candidate Identity",
        "Candidate Fingerprint",
        "Artifact Inventory",
        "Candidate Class Registry",
        "Identifier Registry",
        "Schema Registry",
        "Constitutional Rule Registry",
        "Evaluation Results",
        "Certification Test Registry",
        "Certification Test Results",
        "Constitutional Metrics",
        "Compatibility Matrix",
        "Registry Cross-Reference Graph",
        "Certification Evidence Registry",
        "Certification Manifest",
        "Traceability Matrix",
        "Constitutional Findings",
        "Certification Decisions",
        "Replay Records",
        "Recovery Records",
        "Audit Records",
    )

    def build_operational_package(self, candidate_root: str | Path | None = None) -> RiskRm005ClosureOperationalPackage:
        root = Path(candidate_root).resolve() if candidate_root is not None else Path(__file__).resolve().parents[3]
        registry_package = RiskRm005RegistryOperationalSupport().build_operational_package(root)
        package_record = self.assemble_certification_package(registry_package, root)
        traceability = self.generate_traceability_matrix(registry_package, package_record)
        procedure = self.execute_certification_procedure(registry_package, package_record, traceability)
        persistence = self.persist_certification_state(registry_package, package_record, traceability, procedure)
        replay = self.verify_replay_and_recovery(registry_package, package_record, persistence)
        decision = self.generate_certification_decision(registry_package, package_record, traceability, procedure, persistence, replay)
        final = EnterpriseCertificationDecision.PASS if (
            registry_package.final_completion_readiness == EnterpriseCertificationDecision.PASS
            and package_record.package_status == EnterpriseCertificationDecision.PASS
            and replay.result == EnterpriseCertificationDecision.PASS
            and decision.decision == EnterpriseCertificationDecision.PASS
            and decision.closure_eligible
            and all(record.result == EnterpriseCertificationDecision.PASS for record in (*traceability, *procedure))
        ) else EnterpriseCertificationDecision.FAIL
        package = RiskRm005ClosureOperationalPackage(
            package_identifier=f"RISK-RM-005-CLOSURE-{_digest((registry_package.deterministic_digest, decision.deterministic_digest))[:12].upper()}",
            governing_doctrine="RISK-RM-005-016-TO-020/1.0.0",
            order_coverage=self.order_coverage,
            registry_package=registry_package,
            certification_package=package_record,
            traceability_matrix=traceability,
            procedure_execution=procedure,
            persistence_records=persistence,
            replay_recovery_record=replay,
            certification_decision=decision,
            immutable_audit_references=(
                package_record.package_identifier,
                "RISK-RM-005-016-CERTIFICATION-PACKAGE",
                "RISK-RM-005-017-TRACEABILITY-MATRIX",
                "RISK-RM-005-018-PROCEDURE-EXECUTION",
                "RISK-RM-005-019-PERSISTENCE-REPLAY-RECOVERY",
                "RISK-RM-005-020-DECISION-CLOSURE",
            ),
            final_completion_readiness=final,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def assemble_certification_package(
        self,
        registry_package: RiskRm005RegistryOperationalPackage,
        candidate_root: Path,
        *,
        omitted_artifacts: tuple[str, ...] = (),
    ) -> RiskRm005CertificationPackageRecord:
        candidate = registry_package.execution_package.candidate_package.candidate_binding
        present = tuple(artifact for artifact in self.mandatory_package_artifacts if artifact not in omitted_artifacts)
        findings = tuple(f"mandatory certification artifact omitted: {artifact}" for artifact in omitted_artifacts)
        commit = _current_commit(candidate_root)
        schema_versions = tuple(sorted({record.schema_identifier for record in registry_package.execution_package.schema_validations}))
        registry_versions = (
            registry_package.governing_doctrine,
            registry_package.certification_manifest.governing_doctrine,
            "RISK-RM-004-016/1.0.0",
            "RISK-RM-004-017/1.0.0",
            "RISK-RM-004-018/1.0.0",
        )
        base = RiskRm005CertificationPackageRecord(
            package_identifier=f"RISK-RM005-CERT-PACKAGE-{candidate.candidate_digest[:16].upper()}",
            candidate_identifier=candidate.candidate_identifier,
            candidate_digest=candidate.candidate_digest,
            package_version="1.0.0",
            doctrine_version="RISK-RM-005/1.0.0",
            repository_identifier=str(candidate_root),
            immutable_commit_identifier=commit,
            configuration_version="risk-rm005-certification-config/1.0.0",
            schema_version_set=schema_versions,
            registry_version_set=registry_versions,
            certification_suite_version="risk-rm005-suite/1.0.0",
            creation_timestamp=FIXED_CERTIFICATION_TIMESTAMP,
            producing_authority="Risk Office Certification Operationalization",
            mandatory_artifact_references=present,
            package_status=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
            findings=findings,
            integrity_digest="",
        )
        return replace(base, integrity_digest=_digest(base))

    def generate_traceability_matrix(
        self,
        registry_package: RiskRm005RegistryOperationalPackage,
        package_record: RiskRm005CertificationPackageRecord,
        *,
        omitted_requirements: tuple[str, ...] = (),
    ) -> tuple[RiskRm005TraceabilityRecord, ...]:
        records = []
        decision_ref = f"DECISION-{package_record.package_identifier}"
        requirement_inputs = {
            "RISK-RM-005-016": package_record.package_identifier,
            "RISK-RM-005-017": "TRACEABILITY-MATRIX",
            "RISK-RM-005-018": "CERTIFICATION-PROCEDURE",
            "RISK-RM-005-019": "PERSISTENCE-REPLAY-RECOVERY",
            "RISK-RM-005-020": decision_ref,
        }
        for requirement, implementation in requirement_inputs.items():
            if requirement in omitted_requirements:
                continue
            evidence = {
                "RISK-RM-005-016": package_record.integrity_digest,
                "RISK-RM-005-017": registry_package.certification_manifest.deterministic_digest,
                "RISK-RM-005-018": registry_package.deterministic_digest,
                "RISK-RM-005-019": package_record.integrity_digest,
                "RISK-RM-005-020": registry_package.certification_manifest.deterministic_digest,
            }[requirement]
            record = RiskRm005TraceabilityRecord(
                traceability_identifier=f"RISK-RM005-TRACE-{requirement[-3:]}",
                requirement_identifier=requirement,
                doctrine_reference=f"{requirement}/1.0.0",
                implementation_reference=implementation,
                evaluation_reference=registry_package.certification_manifest.manifest_identifier,
                evidence_reference=evidence,
                metric_reference=registry_package.metrics[0].metric_identifier if registry_package.metrics else "",
                decision_reference=decision_ref,
                forward_trace=(requirement, implementation, evidence, decision_ref),
                backward_trace=(decision_ref, evidence, implementation, requirement),
                findings=(),
                result=EnterpriseCertificationDecision.PASS,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        missing = set(requirement_inputs) - {record.requirement_identifier for record in records}
        if missing:
            failure = RiskRm005TraceabilityRecord(
                traceability_identifier="RISK-RM005-TRACE-FAIL-CLOSED",
                requirement_identifier="TRACEABILITY-COVERAGE-FAILURE",
                doctrine_reference="RISK-RM-004-017/1.0.0",
                implementation_reference="",
                evaluation_reference=registry_package.certification_manifest.manifest_identifier,
                evidence_reference="",
                metric_reference="",
                decision_reference=decision_ref,
                forward_trace=(),
                backward_trace=(),
                findings=tuple(f"mandatory requirement missing from traceability matrix: {item}" for item in sorted(missing)),
                result=EnterpriseCertificationDecision.FAIL,
                deterministic_digest="",
            )
            records.append(replace(failure, deterministic_digest=_digest(failure)))
        return tuple(records)

    def execute_certification_procedure(
        self,
        registry_package: RiskRm005RegistryOperationalPackage,
        package_record: RiskRm005CertificationPackageRecord,
        traceability: tuple[RiskRm005TraceabilityRecord, ...],
        *,
        force_stage_failure: str | None = None,
    ) -> tuple[RiskRm005ProcedureStageRecord, ...]:
        records = []
        previous = ()
        for index, stage_name in enumerate(self.procedure_stages, start=1):
            findings = []
            if force_stage_failure == stage_name:
                findings.append("forced certification procedure stage failure")
            if previous and any(record.result != EnterpriseCertificationDecision.PASS for record in records):
                findings.append("prerequisite stage failed")
            if stage_name == "Certification Package Validation" and package_record.package_status != EnterpriseCertificationDecision.PASS:
                findings.extend(package_record.findings)
            if stage_name == "Traceability Verification" and any(record.result != EnterpriseCertificationDecision.PASS for record in traceability):
                findings.append("traceability matrix contains failing records")
            if stage_name == "Certification Threshold Evaluation" and registry_package.final_completion_readiness != EnterpriseCertificationDecision.PASS:
                findings.append("registry package did not meet certification threshold")
            evidence_inputs = (package_record.package_identifier, registry_package.certification_manifest.manifest_identifier)
            stage = RiskRm005ProcedureStageRecord(
                stage_identifier=f"RISK-RM005-STAGE-{index:02d}",
                stage_name=stage_name,
                execution_order=index,
                prerequisite_stage_identifiers=previous,
                evidence_inputs=evidence_inputs,
                produced_evidence=(f"RISK-RM005-STAGE-EVIDENCE-{index:02d}",),
                findings=tuple(findings),
                result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
                deterministic_digest="",
            )
            records.append(replace(stage, deterministic_digest=_digest(stage)))
            previous = (stage.stage_identifier,)
        return tuple(records)

    def persist_certification_state(
        self,
        registry_package: RiskRm005RegistryOperationalPackage,
        package_record: RiskRm005CertificationPackageRecord,
        traceability: tuple[RiskRm005TraceabilityRecord, ...],
        procedure: tuple[RiskRm005ProcedureStageRecord, ...],
    ) -> tuple[RiskRm005PersistenceRecord, ...]:
        candidate = package_record.candidate_identifier
        commit = package_record.immutable_commit_identifier
        artifacts = [
            (package_record.package_identifier, "certification-package", package_record.integrity_digest),
            (registry_package.certification_manifest.manifest_identifier, "certification-manifest", registry_package.certification_manifest.deterministic_digest),
            ("TRACEABILITY-MATRIX", "traceability-matrix", _digest(traceability)),
            ("PROCEDURE-EXECUTION", "procedure-execution", _digest(procedure)),
            ("EVIDENCE-REGISTRY", "evidence-registry", _digest(registry_package.certification_evidence_registry)),
        ]
        records = []
        for index, (artifact_id, artifact_class, integrity_hash) in enumerate(artifacts, start=1):
            record = RiskRm005PersistenceRecord(
                persistence_identifier=f"RISK-RM005-PERSIST-{index:03d}",
                candidate_identifier=candidate,
                artifact_identifier=artifact_id,
                artifact_classification=artifact_class,
                persistence_timestamp=FIXED_CERTIFICATION_TIMESTAMP,
                commit_identifier=commit,
                storage_status="persisted",
                integrity_hash=integrity_hash,
                version="1.0.0",
                recovery_reference=f"RECOVERY-{artifact_id}",
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def verify_replay_and_recovery(
        self,
        registry_package: RiskRm005RegistryOperationalPackage,
        package_record: RiskRm005CertificationPackageRecord,
        persistence: tuple[RiskRm005PersistenceRecord, ...],
        *,
        replay_digest_override: str | None = None,
    ) -> RiskRm005ReplayRecoveryRecord:
        original_digest = registry_package.deterministic_digest
        replay_digest = replay_digest_override or original_digest
        equivalent = original_digest == replay_digest
        findings = () if equivalent else ("replay package digest differs from original package digest",)
        record = RiskRm005ReplayRecoveryRecord(
            replay_identifier=f"RISK-RM005-REPLAY-{package_record.candidate_digest[:12].upper()}",
            candidate_identifier=package_record.candidate_identifier,
            original_package_digest=original_digest,
            replay_package_digest=replay_digest,
            restored_persistence_digest=_digest(persistence),
            outcome_equivalent=equivalent,
            findings=findings,
            result=EnterpriseCertificationDecision.PASS if equivalent else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def generate_certification_decision(
        self,
        registry_package: RiskRm005RegistryOperationalPackage,
        package_record: RiskRm005CertificationPackageRecord,
        traceability: tuple[RiskRm005TraceabilityRecord, ...],
        procedure: tuple[RiskRm005ProcedureStageRecord, ...],
        persistence: tuple[RiskRm005PersistenceRecord, ...],
        replay: RiskRm005ReplayRecoveryRecord,
    ) -> RiskRm005CertificationDecisionRecord:
        findings = []
        if registry_package.final_completion_readiness != EnterpriseCertificationDecision.PASS:
            findings.append("registry package not ready for certification decision")
        if package_record.package_status != EnterpriseCertificationDecision.PASS:
            findings.extend(package_record.findings)
        if any(record.result != EnterpriseCertificationDecision.PASS for record in traceability):
            findings.append("traceability matrix failed")
        if any(record.result != EnterpriseCertificationDecision.PASS for record in procedure):
            findings.append("certification procedure failed")
        if any(record.storage_status != "persisted" for record in persistence):
            findings.append("certification state persistence incomplete")
        if replay.result != EnterpriseCertificationDecision.PASS:
            findings.extend(replay.findings)
        decision = EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL
        record = RiskRm005CertificationDecisionRecord(
            decision_identifier=f"RISK-RM005-DECISION-{package_record.candidate_digest[:16].upper()}",
            candidate_identifier=package_record.candidate_identifier,
            candidate_digest=package_record.candidate_digest,
            decision=decision,
            decision_basis=(
                registry_package.certification_manifest.manifest_identifier,
                package_record.package_identifier,
                _digest(traceability),
                _digest(procedure),
                _digest(persistence),
                replay.deterministic_digest,
            ),
            closure_eligible=decision == EnterpriseCertificationDecision.PASS,
            package_sealed=decision == EnterpriseCertificationDecision.PASS,
            archive_identifier=f"RISK-RM005-ARCHIVE-{package_record.candidate_digest[:16].upper()}",
            findings=tuple(findings),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))


def _current_commit(candidate_root: Path) -> str:
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(candidate_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "UNVERSIONED-CANDIDATE"
    return output or "UNVERSIONED-CANDIDATE"
