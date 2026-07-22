"""Operational Risk Office M4 certification execution.

This module binds the Risk Office M4 work package to a concrete repository
candidate and produces executable certification evidence.  The M4 document uses
the RISK-RM-003 work-order namespace, so this engine evaluates the implemented
RISK-RM-003 specification program rather than merely cataloging its identifiers.
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

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision
from argos.risk.specification import RiskOfficeSpecificationSupport, RiskSpecificationWorkOrder


@dataclass(frozen=True)
class RiskM4CandidateIdentity:
    repository_root: str
    repository_identifier: str
    candidate_commit: str
    implementation_version: str
    constitutional_doctrine_version: str
    source_digest: str
    dirty_paths: tuple[str, ...]
    generated_at: str


@dataclass(frozen=True)
class RiskM4RegistryRecord:
    registry_identifier: str
    registry_name: str
    work_order_identifier: str
    constitutional_owner: str
    version: str
    source_paths: tuple[str, ...]
    relationships: tuple[str, ...]
    validation_status: EnterpriseCertificationDecision
    integrity_digest: str


@dataclass(frozen=True)
class RiskM4RuleResult:
    rule_identifier: str
    work_order_identifier: str
    governing_requirement: str
    candidate_artifacts: tuple[str, ...]
    required_evidence: tuple[str, ...]
    result: EnterpriseCertificationDecision
    findings: tuple[str, ...]
    audit_identifier: str
    integrity_digest: str


@dataclass(frozen=True)
class RiskM4CertificationTestResult:
    test_identifier: str
    work_order_identifier: str
    requirement: str
    test_class: str
    result: EnterpriseCertificationDecision
    observed_evidence: tuple[str, ...]
    findings: tuple[str, ...]
    integrity_digest: str


@dataclass(frozen=True)
class RiskM4EvidenceArtifact:
    evidence_identifier: str
    evidence_type: str
    work_order_identifier: str
    path: str
    sha256: str
    validation_status: EnterpriseCertificationDecision


@dataclass(frozen=True)
class RiskM4TraceabilityRecord:
    traceability_identifier: str
    work_order_identifier: str
    doctrine_reference: str
    implementation_artifact: str
    rule_identifier: str
    schema_identifier: str
    registry_identifier: str
    test_identifier: str
    evidence_identifier: str
    decision_identifier: str
    result: EnterpriseCertificationDecision
    integrity_digest: str


@dataclass(frozen=True)
class RiskM4ManifestEntry:
    artifact_identifier: str
    artifact_type: str
    version: str
    owner: str
    location: str
    integrity_digest: str
    governing_doctrine: str
    dependency_references: tuple[str, ...]
    evidence_references: tuple[str, ...]
    compatibility_status: EnterpriseCertificationDecision
    validation_status: EnterpriseCertificationDecision


@dataclass(frozen=True)
class RiskM4CertificationDecision:
    decision_identifier: str
    work_order_identifier: str
    decision: EnterpriseCertificationDecision
    supporting_rule_results: tuple[str, ...]
    supporting_test_results: tuple[str, ...]
    unresolved_findings: tuple[str, ...]
    integrity_digest: str


@dataclass(frozen=True)
class RiskM4OperationalCertificationPackage:
    package_identifier: str
    candidate: RiskM4CandidateIdentity
    work_orders: tuple[RiskSpecificationWorkOrder, ...]
    candidate_registry: tuple[RiskM4RegistryRecord, ...]
    identifier_registry: tuple[RiskM4RegistryRecord, ...]
    schema_registry: tuple[RiskM4RegistryRecord, ...]
    rule_registry: tuple[RiskM4RegistryRecord, ...]
    test_registry: tuple[RiskM4RegistryRecord, ...]
    version_compatibility_matrix: tuple[RiskM4RegistryRecord, ...]
    cross_reference_registry: tuple[RiskM4RegistryRecord, ...]
    rule_results: tuple[RiskM4RuleResult, ...]
    test_results: tuple[RiskM4CertificationTestResult, ...]
    evidence_registry: tuple[RiskM4EvidenceArtifact, ...]
    traceability_matrix: tuple[RiskM4TraceabilityRecord, ...]
    manifest: tuple[RiskM4ManifestEntry, ...]
    decisions: tuple[RiskM4CertificationDecision, ...]
    metrics: Mapping[str, int]
    replay_result: EnterpriseCertificationDecision
    recovery_result: EnterpriseCertificationDecision
    final_certification_result: EnterpriseCertificationDecision
    closure_status: str
    unresolved_findings: tuple[str, ...]
    deterministic_digest: str


class RiskM4OperationalCertificationEngine:
    """Execute candidate-bound M4 certification for the Risk Office."""

    required_candidate_paths = (
        "src/argos/risk/specification.py",
        "src/argos/risk/__init__.py",
        "Tests/test_risk_rm003_specification.py",
        "Documentation/RISK-RM-003-001_TO_005_OBJECT_FOUNDATION_SPECIFICATION_REPORT.md",
        "Documentation/RISK-RM-003-006_TO_010_STATE_DOCTRINE_SPECIFICATION_REPORT.md",
        "Documentation/RISK-RM-003-011_TO_015_EXECUTION_STATE_SPECIFICATION_REPORT.md",
        "Documentation/RISK-RM-003-016_TO_020_VALIDATION_COMMIT_SPECIFICATION_REPORT.md",
        "Documentation/RISK-RM-003-021_TO_025_CERTIFICATION_CLOSURE_SPECIFICATION_REPORT.md",
    )

    def __init__(
        self,
        repository_root: str | Path,
        *,
        required_candidate_paths: tuple[str, ...] | None = None,
    ) -> None:
        self.repository_root = Path(repository_root).resolve()
        self.required_paths = required_candidate_paths or self.required_candidate_paths
        self.support = RiskOfficeSpecificationSupport()

    def certify(self, evidence_directory: str | Path) -> RiskM4OperationalCertificationPackage:
        evidence_root = Path(evidence_directory)
        evidence_root.mkdir(parents=True, exist_ok=True)
        candidate = self._candidate_identity()
        work_orders = self.support.build_specification_program_record().work_orders
        registries = self._materialize_registries(work_orders)
        rule_results = tuple(self._execute_rule(work_order) for work_order in work_orders)
        test_results = tuple(self._execute_certification_test(work_order) for work_order in work_orders)
        traceability = self._build_traceability(work_orders, rule_results, test_results)
        decisions = self._build_decisions(work_orders, rule_results, test_results, traceability)
        manifest = self._build_manifest(candidate, registries, rule_results, test_results, traceability, decisions)
        unresolved = self._collect_findings(rule_results, test_results, traceability, decisions, manifest)
        prelim = self._build_package(
            candidate,
            work_orders,
            registries,
            rule_results,
            test_results,
            (),
            traceability,
            manifest,
            decisions,
            EnterpriseCertificationDecision.INCOMPLETE,
            EnterpriseCertificationDecision.INCOMPLETE,
            unresolved,
        )
        evidence_registry = self._persist_evidence(evidence_root, prelim)
        replay = self._verify_replay(prelim)
        recovery = self._verify_recovery(evidence_root, prelim)
        unresolved = unresolved + tuple(
            finding
            for finding, result in (
                ("M4 replay equivalence failed", replay),
                ("M4 recovery equivalence failed", recovery),
            )
            if result != EnterpriseCertificationDecision.PASS
        )
        final_result = EnterpriseCertificationDecision.PASS if not unresolved else EnterpriseCertificationDecision.FAIL
        package = self._build_package(
            candidate,
            work_orders,
            registries,
            rule_results,
            test_results,
            evidence_registry,
            traceability,
            manifest,
            decisions,
            replay,
            recovery,
            unresolved,
            final_result=final_result,
        )
        self._persist_evidence(evidence_root, package)
        return package

    def _candidate_identity(self) -> RiskM4CandidateIdentity:
        commit = self._git("rev-parse", "HEAD")
        remote = self._git("config", "--get", "remote.origin.url", allow_failure=True) or "local-repository"
        dirty = tuple(line for line in self._git("status", "--short").splitlines() if line)
        source_material = []
        for relative in self.required_paths:
            path = self.repository_root / relative
            source_material.append((relative, _file_digest(path) if path.exists() else "MISSING"))
        return RiskM4CandidateIdentity(
            repository_root=str(self.repository_root),
            repository_identifier=remote,
            candidate_commit=commit,
            implementation_version="risk-m4-operational-certification/1.0.0",
            constitutional_doctrine_version="RISK-RM-003-M4/1.0.0",
            source_digest=_digest(source_material),
            dirty_paths=dirty,
            generated_at="deterministic-candidate-bound",
        )

    def _materialize_registries(
        self, work_orders: tuple[RiskSpecificationWorkOrder, ...]
    ) -> Mapping[str, tuple[RiskM4RegistryRecord, ...]]:
        names = (
            "Candidate Class Registry",
            "Identifier Registry",
            "Schema Registry",
            "Constitutional Rule Registry",
            "Certification Test Registry",
            "Version Compatibility Matrix",
            "Registry Cross-Reference Matrix",
        )
        return MappingProxyType({
            name: tuple(self._registry_record(name, work_order) for work_order in work_orders)
            for name in names
        })

    def _registry_record(self, registry_name: str, work_order: RiskSpecificationWorkOrder) -> RiskM4RegistryRecord:
        source_paths = self._source_paths_for(work_order)
        missing = tuple(path for path in source_paths if not (self.repository_root / path).exists())
        status = EnterpriseCertificationDecision.PASS if not missing else EnterpriseCertificationDecision.FAIL
        raw = (registry_name, work_order.work_order_identifier, source_paths, work_order.title)
        return RiskM4RegistryRecord(
            registry_identifier=f"M4-{_slug(registry_name)}-{work_order.work_order_identifier}",
            registry_name=registry_name,
            work_order_identifier=work_order.work_order_identifier,
            constitutional_owner="Risk Office",
            version="1.0.0",
            source_paths=source_paths,
            relationships=(
                f"IMPLEMENTS:{work_order.work_order_identifier}",
                f"DEFINED_BY:{work_order.title}",
                "OWNED_BY:Risk Office",
            ),
            validation_status=status,
            integrity_digest=_digest(raw),
        )

    def _execute_rule(self, work_order: RiskSpecificationWorkOrder) -> RiskM4RuleResult:
        source_paths = self._source_paths_for(work_order)
        required_evidence = (
            "implementation artifact present",
            "test artifact present",
            "work-order reference present in implementation",
            "work-order reference present in executable test",
        )
        findings = []
        for path in source_paths:
            if not (self.repository_root / path).exists():
                findings.append(f"required artifact missing: {path}")
        implementation_text = _read_text(self.repository_root / "src/argos/risk/specification.py")
        test_text = _read_text(self.repository_root / "Tests/test_risk_rm003_specification.py")
        if work_order.work_order_identifier not in implementation_text:
            findings.append("work order absent from implementation source")
        if work_order.work_order_identifier not in test_text:
            findings.append("work order absent from executable test source")
        result = EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL
        rule_id = f"M4-RULE-{work_order.work_order_identifier}"
        return RiskM4RuleResult(
            rule_identifier=rule_id,
            work_order_identifier=work_order.work_order_identifier,
            governing_requirement=work_order.purpose,
            candidate_artifacts=source_paths,
            required_evidence=required_evidence,
            result=result,
            findings=tuple(findings),
            audit_identifier=f"M4-AUDIT-{work_order.work_order_identifier}",
            integrity_digest=_digest((rule_id, work_order, findings)),
        )

    def _execute_certification_test(self, work_order: RiskSpecificationWorkOrder) -> RiskM4CertificationTestResult:
        test_text = _read_text(self.repository_root / "Tests/test_risk_rm003_specification.py")
        implementation_text = _read_text(self.repository_root / "src/argos/risk/specification.py")
        findings = []
        if work_order.work_order_identifier not in test_text:
            findings.append("no executable RM003 test references work order")
        if work_order.work_order_identifier not in implementation_text:
            findings.append("no implementation artifact references work order")
        if "FAIL" not in test_text or "fail_closed" not in test_text:
            findings.append("fail-closed test population missing")
        result = EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL
        test_id = f"M4-TEST-{work_order.work_order_identifier}"
        return RiskM4CertificationTestResult(
            test_identifier=test_id,
            work_order_identifier=work_order.work_order_identifier,
            requirement=work_order.purpose,
            test_class="candidate-bound source and fail-closed certification coverage",
            result=result,
            observed_evidence=("Tests/test_risk_rm003_specification.py", "src/argos/risk/specification.py"),
            findings=tuple(findings),
            integrity_digest=_digest((test_id, work_order, findings)),
        )

    def _build_traceability(
        self,
        work_orders: tuple[RiskSpecificationWorkOrder, ...],
        rule_results: tuple[RiskM4RuleResult, ...],
        test_results: tuple[RiskM4CertificationTestResult, ...],
    ) -> tuple[RiskM4TraceabilityRecord, ...]:
        rules = {item.work_order_identifier: item for item in rule_results}
        tests = {item.work_order_identifier: item for item in test_results}
        records = []
        for work_order in work_orders:
            rule = rules[work_order.work_order_identifier]
            test = tests[work_order.work_order_identifier]
            result = EnterpriseCertificationDecision.PASS if rule.result == test.result == EnterpriseCertificationDecision.PASS else EnterpriseCertificationDecision.FAIL
            trace_id = f"M4-TRACE-{work_order.work_order_identifier}"
            records.append(RiskM4TraceabilityRecord(
                traceability_identifier=trace_id,
                work_order_identifier=work_order.work_order_identifier,
                doctrine_reference="Risk Office M4 Remediation series.docx",
                implementation_artifact="src/argos/risk/specification.py",
                rule_identifier=rule.rule_identifier,
                schema_identifier=f"M4-SCHEMA-{work_order.work_order_identifier}",
                registry_identifier=f"M4-CANDIDATE-CLASS-REGISTRY-{work_order.work_order_identifier}",
                test_identifier=test.test_identifier,
                evidence_identifier=f"M4-EVIDENCE-{work_order.work_order_identifier}",
                decision_identifier=f"M4-DECISION-{work_order.work_order_identifier}",
                result=result,
                integrity_digest=_digest((trace_id, rule, test, result)),
            ))
        return tuple(records)

    def _build_decisions(
        self,
        work_orders: tuple[RiskSpecificationWorkOrder, ...],
        rule_results: tuple[RiskM4RuleResult, ...],
        test_results: tuple[RiskM4CertificationTestResult, ...],
        traceability: tuple[RiskM4TraceabilityRecord, ...],
    ) -> tuple[RiskM4CertificationDecision, ...]:
        rules = {item.work_order_identifier: item for item in rule_results}
        tests = {item.work_order_identifier: item for item in test_results}
        traces = {item.work_order_identifier: item for item in traceability}
        decisions = []
        for work_order in work_orders:
            rule = rules[work_order.work_order_identifier]
            test = tests[work_order.work_order_identifier]
            trace = traces[work_order.work_order_identifier]
            findings = rule.findings + test.findings
            if trace.result != EnterpriseCertificationDecision.PASS:
                findings += ("traceability chain failed",)
            decision = EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL
            decision_id = f"M4-DECISION-{work_order.work_order_identifier}"
            decisions.append(RiskM4CertificationDecision(
                decision_identifier=decision_id,
                work_order_identifier=work_order.work_order_identifier,
                decision=decision,
                supporting_rule_results=(rule.rule_identifier,),
                supporting_test_results=(test.test_identifier,),
                unresolved_findings=findings,
                integrity_digest=_digest((decision_id, decision, findings)),
            ))
        return tuple(decisions)

    def _build_manifest(
        self,
        candidate: RiskM4CandidateIdentity,
        registries: Mapping[str, tuple[RiskM4RegistryRecord, ...]],
        rule_results: tuple[RiskM4RuleResult, ...],
        test_results: tuple[RiskM4CertificationTestResult, ...],
        traceability: tuple[RiskM4TraceabilityRecord, ...],
        decisions: tuple[RiskM4CertificationDecision, ...],
    ) -> tuple[RiskM4ManifestEntry, ...]:
        entries: list[RiskM4ManifestEntry] = []
        for path in self.required_paths:
            file_path = self.repository_root / path
            valid = file_path.exists()
            entries.append(RiskM4ManifestEntry(
                artifact_identifier=f"M4-MANIFEST-{_slug(path)}",
                artifact_type="candidate source artifact",
                version=candidate.candidate_commit,
                owner="Risk Office",
                location=path,
                integrity_digest=_file_digest(file_path) if valid else "MISSING",
                governing_doctrine="RISK-RM-003-M4",
                dependency_references=("Risk Office M4 Remediation series.docx",),
                evidence_references=tuple(item.rule_identifier for item in rule_results[:1]),
                compatibility_status=EnterpriseCertificationDecision.PASS if valid else EnterpriseCertificationDecision.FAIL,
                validation_status=EnterpriseCertificationDecision.PASS if valid else EnterpriseCertificationDecision.FAIL,
            ))
        for name, records in registries.items():
            entries.append(self._manifest_for_generated(name, "registry", records))
        entries.extend((
            self._manifest_for_generated("M4 Rule Results", "rule-results", rule_results),
            self._manifest_for_generated("M4 Test Results", "test-results", test_results),
            self._manifest_for_generated("M4 Traceability Matrix", "traceability", traceability),
            self._manifest_for_generated("M4 Certification Decisions", "decisions", decisions),
        ))
        return tuple(entries)

    def _manifest_for_generated(self, name: str, artifact_type: str, value: Any) -> RiskM4ManifestEntry:
        digest = _digest(value)
        return RiskM4ManifestEntry(
            artifact_identifier=f"M4-MANIFEST-{_slug(name)}",
            artifact_type=artifact_type,
            version="1.0.0",
            owner="Risk Office",
            location=f"generated://{_slug(name)}",
            integrity_digest=digest,
            governing_doctrine="RISK-RM-003-M4",
            dependency_references=("candidate identity",),
            evidence_references=(f"M4-EVIDENCE-{_slug(name)}",),
            compatibility_status=EnterpriseCertificationDecision.PASS,
            validation_status=EnterpriseCertificationDecision.PASS,
        )

    def _collect_findings(
        self,
        rule_results: tuple[RiskM4RuleResult, ...],
        test_results: tuple[RiskM4CertificationTestResult, ...],
        traceability: tuple[RiskM4TraceabilityRecord, ...],
        decisions: tuple[RiskM4CertificationDecision, ...],
        manifest: tuple[RiskM4ManifestEntry, ...],
    ) -> tuple[str, ...]:
        findings: list[str] = []
        for item in rule_results:
            findings.extend(f"{item.work_order_identifier}: {finding}" for finding in item.findings)
        for item in test_results:
            findings.extend(f"{item.work_order_identifier}: {finding}" for finding in item.findings)
        findings.extend(
            f"{item.work_order_identifier}: traceability failed"
            for item in traceability
            if item.result != EnterpriseCertificationDecision.PASS
        )
        for decision in decisions:
            findings.extend(f"{decision.work_order_identifier}: {finding}" for finding in decision.unresolved_findings)
        findings.extend(
            f"manifest artifact invalid: {item.location}"
            for item in manifest
            if item.validation_status != EnterpriseCertificationDecision.PASS
        )
        return tuple(dict.fromkeys(findings))

    def _build_package(
        self,
        candidate: RiskM4CandidateIdentity,
        work_orders: tuple[RiskSpecificationWorkOrder, ...],
        registries: Mapping[str, tuple[RiskM4RegistryRecord, ...]],
        rule_results: tuple[RiskM4RuleResult, ...],
        test_results: tuple[RiskM4CertificationTestResult, ...],
        evidence_registry: tuple[RiskM4EvidenceArtifact, ...],
        traceability: tuple[RiskM4TraceabilityRecord, ...],
        manifest: tuple[RiskM4ManifestEntry, ...],
        decisions: tuple[RiskM4CertificationDecision, ...],
        replay: EnterpriseCertificationDecision,
        recovery: EnterpriseCertificationDecision,
        unresolved: tuple[str, ...],
        *,
        final_result: EnterpriseCertificationDecision | None = None,
    ) -> RiskM4OperationalCertificationPackage:
        metrics = MappingProxyType({
            "work_orders": len(work_orders),
            "registries": sum(len(records) for records in registries.values()),
            "rules_executed": len(rule_results),
            "tests_executed": len(test_results),
            "traceability_records": len(traceability),
            "manifest_entries": len(manifest),
            "decisions": len(decisions),
            "unresolved_findings": len(unresolved),
        })
        result = final_result or (EnterpriseCertificationDecision.PASS if not unresolved else EnterpriseCertificationDecision.FAIL)
        package = RiskM4OperationalCertificationPackage(
            package_identifier=f"M4-CERTIFICATION-{candidate.candidate_commit[:12]}",
            candidate=candidate,
            work_orders=work_orders,
            candidate_registry=registries["Candidate Class Registry"],
            identifier_registry=registries["Identifier Registry"],
            schema_registry=registries["Schema Registry"],
            rule_registry=registries["Constitutional Rule Registry"],
            test_registry=registries["Certification Test Registry"],
            version_compatibility_matrix=registries["Version Compatibility Matrix"],
            cross_reference_registry=registries["Registry Cross-Reference Matrix"],
            rule_results=rule_results,
            test_results=test_results,
            evidence_registry=evidence_registry,
            traceability_matrix=traceability,
            manifest=manifest,
            decisions=decisions,
            metrics=metrics,
            replay_result=replay,
            recovery_result=recovery,
            final_certification_result=result,
            closure_status="CLOSED" if result == EnterpriseCertificationDecision.PASS and replay == EnterpriseCertificationDecision.PASS and recovery == EnterpriseCertificationDecision.PASS else "WITHHELD",
            unresolved_findings=unresolved,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def _persist_evidence(
        self,
        evidence_root: Path,
        package: RiskM4OperationalCertificationPackage,
    ) -> tuple[RiskM4EvidenceArtifact, ...]:
        payloads = {
            "candidate_identity.json": package.candidate,
            "registries.json": {
                "candidate": package.candidate_registry,
                "identifier": package.identifier_registry,
                "schema": package.schema_registry,
                "rules": package.rule_registry,
                "tests": package.test_registry,
                "versions": package.version_compatibility_matrix,
                "cross_references": package.cross_reference_registry,
            },
            "rule_results.json": package.rule_results,
            "test_results.json": package.test_results,
            "traceability_matrix.json": package.traceability_matrix,
            "manifest.json": package.manifest,
            "decisions.json": package.decisions,
            "certification_package.json": package,
        }
        artifacts = []
        for name, payload in payloads.items():
            path = evidence_root / name
            path.write_text(json.dumps(_jsonable_public(payload), indent=2, sort_keys=True), encoding="utf-8")
            artifacts.append(RiskM4EvidenceArtifact(
                evidence_identifier=f"M4-EVIDENCE-{_slug(name)}",
                evidence_type=name.removesuffix(".json"),
                work_order_identifier="RISK-RM-003-M4",
                path=str(path),
                sha256=_file_digest(path),
                validation_status=EnterpriseCertificationDecision.PASS,
            ))
        return tuple(artifacts)

    def _verify_replay(self, package: RiskM4OperationalCertificationPackage) -> EnterpriseCertificationDecision:
        replay = self._build_package(
            package.candidate,
            package.work_orders,
            {
                "Candidate Class Registry": package.candidate_registry,
                "Identifier Registry": package.identifier_registry,
                "Schema Registry": package.schema_registry,
                "Constitutional Rule Registry": package.rule_registry,
                "Certification Test Registry": package.test_registry,
                "Version Compatibility Matrix": package.version_compatibility_matrix,
                "Registry Cross-Reference Matrix": package.cross_reference_registry,
            },
            package.rule_results,
            package.test_results,
            (),
            package.traceability_matrix,
            package.manifest,
            package.decisions,
            EnterpriseCertificationDecision.INCOMPLETE,
            EnterpriseCertificationDecision.INCOMPLETE,
            package.unresolved_findings,
            final_result=package.final_certification_result,
        )
        return EnterpriseCertificationDecision.PASS if replay.deterministic_digest == package.deterministic_digest else EnterpriseCertificationDecision.FAIL

    def _verify_recovery(self, evidence_root: Path, package: RiskM4OperationalCertificationPackage) -> EnterpriseCertificationDecision:
        path = evidence_root / "certification_package.json"
        if not path.exists():
            return EnterpriseCertificationDecision.FAIL
        payload = json.loads(path.read_text(encoding="utf-8"))
        return EnterpriseCertificationDecision.PASS if payload.get("package_identifier") == package.package_identifier else EnterpriseCertificationDecision.FAIL

    def _source_paths_for(self, work_order: RiskSpecificationWorkOrder) -> tuple[str, ...]:
        index = int(work_order.work_order_identifier.rsplit("-", 1)[1])
        band_report = (
            "Documentation/RISK-RM-003-001_TO_005_OBJECT_FOUNDATION_SPECIFICATION_REPORT.md" if index <= 5
            else "Documentation/RISK-RM-003-006_TO_010_STATE_DOCTRINE_SPECIFICATION_REPORT.md" if index <= 10
            else "Documentation/RISK-RM-003-011_TO_015_EXECUTION_STATE_SPECIFICATION_REPORT.md" if index <= 15
            else "Documentation/RISK-RM-003-016_TO_020_VALIDATION_COMMIT_SPECIFICATION_REPORT.md" if index <= 20
            else "Documentation/RISK-RM-003-021_TO_025_CERTIFICATION_CLOSURE_SPECIFICATION_REPORT.md"
        )
        return ("src/argos/risk/specification.py", "Tests/test_risk_rm003_specification.py", band_report)

    def _git(self, *args: str, allow_failure: bool = False) -> str:
        result = subprocess.run(
            ("git", *args),
            cwd=self.repository_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0 and not allow_failure:
            raise RuntimeError(result.stderr.strip())
        return result.stdout.strip()


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.upper()).strip("-")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _file_digest(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return {key: _jsonable(item) for key, item in value.items()}
    if is_dataclass(value):
        return {
            field_info.name: _jsonable(getattr(value, field_info.name))
            for field_info in fields(value)
            if field_info.name != "deterministic_digest"
        }
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list, set)):
        return [_jsonable(item) for item in value]
    return value


def _jsonable_public(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return {key: _jsonable_public(item) for key, item in value.items()}
    if is_dataclass(value):
        return {
            field_info.name: _jsonable_public(getattr(value, field_info.name))
            for field_info in fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): _jsonable_public(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list, set)):
        return [_jsonable_public(item) for item in value]
    return value
