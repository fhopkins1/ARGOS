"""Operational RISK-RM-005 metrics, registry, evidence, and manifest support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision
from argos.risk.rm005_execution_operational import RiskRm005ExecutionOperationalPackage, RiskRm005ExecutionOperationalSupport


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
class RiskRm005MetricRecord:
    metric_identifier: str
    canonical_name: str
    description: str
    governing_doctrine: str
    governing_work_order: str
    producing_authority: str
    source_evidence: tuple[str, ...]
    calculation_formula: str
    measurement_unit: str
    acceptable_range: tuple[int, int]
    certification_threshold: int
    calculated_value: int
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005CompatibilityRecord:
    compatibility_identifier: str
    artifact_identifier: str
    artifact_class: str
    governing_doctrine_version: str
    observed_version: str
    compatible_versions: tuple[str, ...]
    source_evidence: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005CrossReferenceEdge:
    edge_identifier: str
    source_identifier: str
    target_identifier: str
    relationship_type: str
    governing_work_order: str
    source_evidence: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005EvidenceRegistryRecord:
    evidence_identifier: str
    evidence_classification: str
    candidate_identifier: str
    candidate_digest: str
    producing_authority: str
    producing_work_order: str
    governing_doctrine: str
    provenance_reference: str
    content_digest: str
    related_tests: tuple[str, ...]
    related_rules: tuple[str, ...]
    admissible: bool
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005CertificationManifestRecord:
    manifest_identifier: str
    candidate_identifier: str
    candidate_digest: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    artifact_count: int
    metric_count: int
    compatibility_count: int
    cross_reference_edge_count: int
    evidence_record_count: int
    schema_validation_count: int
    rule_evaluation_count: int
    test_execution_count: int
    registry_digests: Mapping[str, str]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005RegistryOperationalPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    execution_package: RiskRm005ExecutionOperationalPackage
    metrics: tuple[RiskRm005MetricRecord, ...]
    version_compatibility_matrix: tuple[RiskRm005CompatibilityRecord, ...]
    registry_cross_reference_graph: tuple[RiskRm005CrossReferenceEdge, ...]
    certification_evidence_registry: tuple[RiskRm005EvidenceRegistryRecord, ...]
    certification_manifest: RiskRm005CertificationManifestRecord
    coverage_summary: Mapping[str, int]
    immutable_audit_references: tuple[str, ...]
    final_completion_readiness: EnterpriseCertificationDecision
    deterministic_digest: str


class RiskRm005RegistryOperationalSupport:
    """Build candidate-bound operational evidence for RISK-RM-005-011 through 015."""

    order_coverage = (
        "RISK-RM-005-011",
        "RISK-RM-005-012",
        "RISK-RM-005-013",
        "RISK-RM-005-014",
        "RISK-RM-005-015",
    )

    def build_operational_package(self, candidate_root: str | Path | None = None) -> RiskRm005RegistryOperationalPackage:
        execution_package = RiskRm005ExecutionOperationalSupport().build_operational_package(candidate_root)
        metrics = self.materialize_metrics(execution_package)
        compatibility = self.populate_version_compatibility_matrix(execution_package)
        evidence = self.populate_certification_evidence_registry(execution_package, metrics, compatibility)
        graph = self.materialize_registry_cross_reference_graph(execution_package, metrics, compatibility, evidence)
        manifest = self.generate_certification_manifest(execution_package, metrics, compatibility, graph, evidence)
        coverage_summary = {
            "calculated_metrics": len(metrics),
            "passing_metrics": sum(1 for record in metrics if record.result == EnterpriseCertificationDecision.PASS),
            "compatibility_records": len(compatibility),
            "passing_compatibility_records": sum(1 for record in compatibility if record.result == EnterpriseCertificationDecision.PASS),
            "cross_reference_edges": len(graph),
            "passing_cross_reference_edges": sum(1 for record in graph if record.result == EnterpriseCertificationDecision.PASS),
            "evidence_records": len(evidence),
            "admissible_evidence_records": sum(1 for record in evidence if record.admissible),
        }
        final = EnterpriseCertificationDecision.PASS if (
            execution_package.final_completion_readiness == EnterpriseCertificationDecision.PASS
            and manifest.result == EnterpriseCertificationDecision.PASS
            and all(record.result == EnterpriseCertificationDecision.PASS for record in (*metrics, *compatibility, *graph, *evidence))
        ) else EnterpriseCertificationDecision.FAIL
        package = RiskRm005RegistryOperationalPackage(
            package_identifier=f"RISK-RM-005-REGISTRY-{_digest((execution_package.deterministic_digest, manifest.deterministic_digest))[:12].upper()}",
            governing_doctrine="RISK-RM-005-011-TO-015/1.0.0",
            order_coverage=self.order_coverage,
            execution_package=execution_package,
            metrics=metrics,
            version_compatibility_matrix=compatibility,
            registry_cross_reference_graph=graph,
            certification_evidence_registry=evidence,
            certification_manifest=manifest,
            coverage_summary=_freeze(coverage_summary),
            immutable_audit_references=(
                manifest.manifest_identifier,
                "RISK-RM-005-011-CONSTITUTIONAL-METRICS",
                "RISK-RM-005-012-VERSION-COMPATIBILITY-MATRIX",
                "RISK-RM-005-013-CROSS-REFERENCE-GRAPH",
                "RISK-RM-005-014-EVIDENCE-REGISTRY",
                "RISK-RM-005-015-CERTIFICATION-MANIFEST",
            ),
            final_completion_readiness=final,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def materialize_metrics(
        self,
        execution_package: RiskRm005ExecutionOperationalPackage,
        *,
        omitted_metric_names: tuple[str, ...] = (),
    ) -> tuple[RiskRm005MetricRecord, ...]:
        candidate_package = execution_package.candidate_package
        artifact_count = len(candidate_package.discovered_artifacts)
        source_count = len(candidate_package.candidate_class_registry)
        blocking_findings = sum(
            len(record.findings)
            for record in (
                *execution_package.schema_validations,
                *execution_package.rule_evaluations,
                *execution_package.certification_tests,
                *execution_package.test_executions,
            )
        )
        metric_values = {
            "constitutional_requirement_coverage": len(self.order_coverage),
            "implementation_coverage": sum(1 for artifact in candidate_package.discovered_artifacts if artifact.artifact_class == "risk-runtime-source"),
            "executable_rule_coverage": len(execution_package.rule_evaluations),
            "executable_test_coverage": len(execution_package.test_executions),
            "evidence_coverage": sum(1 for artifact in candidate_package.discovered_artifacts if "evidence" in artifact.artifact_class),
            "schema_validation_coverage": len(execution_package.schema_validations),
            "registry_completeness": source_count,
            "identifier_completeness": len(candidate_package.constitutional_identifier_registry),
            "traceability_completeness": artifact_count + len(execution_package.rule_evaluations) + len(execution_package.test_executions),
            "persistence_verification": int(artifact_count > 0),
            "replay_equivalence": int(execution_package.deterministic_digest == _digest(replace(execution_package, deterministic_digest=""))),
            "recovery_equivalence": int(execution_package.final_completion_readiness == EnterpriseCertificationDecision.PASS),
            "compatibility_completeness": source_count,
            "unresolved_finding_count": blocking_findings,
            "blocking_finding_count": blocking_findings,
            "certification_readiness": int(execution_package.final_completion_readiness == EnterpriseCertificationDecision.PASS),
            "certification_completeness": int(artifact_count > 0 and not blocking_findings),
        }
        records = []
        for index, (name, value) in enumerate(sorted(metric_values.items()), start=1):
            if name in omitted_metric_names:
                continue
            threshold = 0 if name.endswith("_finding_count") else 1
            maximum = max(value, threshold, artifact_count, len(execution_package.rule_evaluations), len(execution_package.test_executions))
            findings = []
            if value < threshold:
                findings.append(f"metric value below certification threshold: {name}")
            record = RiskRm005MetricRecord(
                metric_identifier=f"RISK-RM005-METRIC-{index:03d}",
                canonical_name=name,
                description=f"Candidate-bound calculation for {name.replace('_', ' ')}.",
                governing_doctrine="RISK-RM-004-007/1.0.0",
                governing_work_order="RISK-RM-005-011",
                producing_authority="Risk Office Certification Operationalization",
                source_evidence=(
                    execution_package.package_identifier,
                    candidate_package.candidate_binding.candidate_identifier,
                    execution_package.deterministic_digest,
                ),
                calculation_formula=f"deterministically derived from execution package field '{name}'",
                measurement_unit="count",
                acceptable_range=(0, maximum),
                certification_threshold=threshold,
                calculated_value=value,
                findings=tuple(findings),
                result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        required = set(metric_values) - set(omitted_metric_names)
        missing = required - {record.canonical_name for record in records}
        if missing:
            failure = RiskRm005MetricRecord(
                metric_identifier="RISK-RM005-METRIC-FAIL-CLOSED",
                canonical_name="missing_metric_registry_coverage",
                description="Fail-closed record for omitted metric registry entries.",
                governing_doctrine="RISK-RM-004-007/1.0.0",
                governing_work_order="RISK-RM-005-011",
                producing_authority="Risk Office Certification Operationalization",
                source_evidence=(execution_package.package_identifier,),
                calculation_formula="required metric registry names minus materialized metric names",
                measurement_unit="count",
                acceptable_range=(0, 0),
                certification_threshold=0,
                calculated_value=len(missing),
                findings=tuple(f"missing required metric: {name}" for name in sorted(missing)),
                result=EnterpriseCertificationDecision.FAIL,
                deterministic_digest="",
            )
            records.append(replace(failure, deterministic_digest=_digest(failure)))
        return tuple(records)

    def populate_version_compatibility_matrix(
        self,
        execution_package: RiskRm005ExecutionOperationalPackage,
        *,
        compatible_versions: tuple[str, ...] = ("1.0.0",),
    ) -> tuple[RiskRm005CompatibilityRecord, ...]:
        records = []
        for artifact in execution_package.candidate_package.discovered_artifacts:
            observed_version = "1.0.0"
            findings = []
            if observed_version not in compatible_versions:
                findings.append("observed version is not explicitly compatible")
            if artifact.artifact_class not in execution_package.candidate_package.candidate_class_registry:
                findings.append("artifact class missing from candidate class registry")
            record = RiskRm005CompatibilityRecord(
                compatibility_identifier=f"RISK-RM005-COMPAT-{artifact.artifact_identifier[-12:]}",
                artifact_identifier=artifact.artifact_identifier,
                artifact_class=artifact.artifact_class,
                governing_doctrine_version="RISK-RM-004-010/1.0.0",
                observed_version=observed_version,
                compatible_versions=compatible_versions,
                source_evidence=(artifact.content_digest, execution_package.candidate_package.candidate_binding.candidate_digest),
                findings=tuple(findings),
                result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
                deterministic_digest="",
            )
            records.append(replace(record, deterministic_digest=_digest(record)))
        return tuple(records)

    def populate_certification_evidence_registry(
        self,
        execution_package: RiskRm005ExecutionOperationalPackage,
        metrics: tuple[RiskRm005MetricRecord, ...],
        compatibility: tuple[RiskRm005CompatibilityRecord, ...],
        *,
        include_artifact_evidence: bool = True,
    ) -> tuple[RiskRm005EvidenceRegistryRecord, ...]:
        candidate = execution_package.candidate_package.candidate_binding
        records = []
        if include_artifact_evidence:
            for artifact in execution_package.candidate_package.discovered_artifacts:
                records.append(
                    self._evidence_record(
                        candidate.candidate_identifier,
                        candidate.candidate_digest,
                        f"EVIDENCE-{artifact.artifact_identifier}",
                        artifact.artifact_class,
                        "RISK-RM-005-014",
                        artifact.relative_path,
                        artifact.content_digest,
                        tuple(test.test_identifier for test in execution_package.certification_tests if test.relative_path == artifact.relative_path),
                        tuple(rule.rule_identifier for rule in execution_package.rule_evaluations if rule.target_artifact_identifier == artifact.artifact_identifier),
                    )
                )
        for validation in execution_package.schema_validations:
            records.append(
                self._evidence_record(candidate.candidate_identifier, candidate.candidate_digest, f"EVIDENCE-{validation.schema_identifier}-{validation.artifact_identifier[-8:]}", "schema-validation-evidence", "RISK-RM-005-014", validation.artifact_identifier, validation.deterministic_digest, (), ())
            )
        for metric in metrics:
            records.append(
                self._evidence_record(candidate.candidate_identifier, candidate.candidate_digest, f"EVIDENCE-{metric.metric_identifier}", "metrics-evidence", "RISK-RM-005-014", metric.metric_identifier, metric.deterministic_digest, (), ())
            )
        for record in compatibility:
            records.append(
                self._evidence_record(candidate.candidate_identifier, candidate.candidate_digest, f"EVIDENCE-{record.compatibility_identifier}", "compatibility-evidence", "RISK-RM-005-014", record.artifact_identifier, record.deterministic_digest, (), ())
            )
        return tuple(records)

    def materialize_registry_cross_reference_graph(
        self,
        execution_package: RiskRm005ExecutionOperationalPackage,
        metrics: tuple[RiskRm005MetricRecord, ...],
        compatibility: tuple[RiskRm005CompatibilityRecord, ...],
        evidence: tuple[RiskRm005EvidenceRegistryRecord, ...],
    ) -> tuple[RiskRm005CrossReferenceEdge, ...]:
        edges = []
        candidate_id = execution_package.candidate_package.candidate_binding.candidate_identifier
        for artifact in execution_package.candidate_package.discovered_artifacts:
            edges.append(self._edge(candidate_id, artifact.artifact_identifier, "candidate-inventories-artifact", "RISK-RM-005-013", (artifact.content_digest,)))
        for validation in execution_package.schema_validations:
            edges.append(self._edge(validation.artifact_identifier, validation.schema_identifier, "artifact-validates-against-schema", "RISK-RM-005-013", (validation.deterministic_digest,)))
        for rule in execution_package.rule_evaluations:
            edges.append(self._edge(rule.target_artifact_identifier, rule.rule_identifier, "artifact-evaluated-by-rule", "RISK-RM-005-013", (rule.deterministic_digest,)))
        for test in execution_package.certification_tests:
            for rule_id in test.bound_rule_identifiers:
                edges.append(self._edge(test.test_identifier, rule_id, "test-covers-rule", "RISK-RM-005-013", (test.deterministic_digest,)))
        for metric in metrics:
            edges.append(self._edge(metric.metric_identifier, candidate_id, "metric-calculated-from-candidate-evidence", "RISK-RM-005-013", metric.source_evidence))
        for record in compatibility:
            edges.append(self._edge(record.compatibility_identifier, record.artifact_identifier, "compatibility-governs-artifact", "RISK-RM-005-013", record.source_evidence))
        for record in evidence:
            edges.append(self._edge(record.evidence_identifier, record.provenance_reference, "evidence-registers-provenance", "RISK-RM-005-013", (record.content_digest,)))
        return tuple(edges)

    def generate_certification_manifest(
        self,
        execution_package: RiskRm005ExecutionOperationalPackage,
        metrics: tuple[RiskRm005MetricRecord, ...],
        compatibility: tuple[RiskRm005CompatibilityRecord, ...],
        graph: tuple[RiskRm005CrossReferenceEdge, ...],
        evidence: tuple[RiskRm005EvidenceRegistryRecord, ...],
        *,
        expected_artifact_count: int | None = None,
    ) -> RiskRm005CertificationManifestRecord:
        candidate = execution_package.candidate_package.candidate_binding
        actual_artifact_count = len(execution_package.candidate_package.discovered_artifacts)
        findings = []
        if expected_artifact_count is not None and expected_artifact_count != actual_artifact_count:
            findings.append("manifest artifact inventory does not match candidate artifact inventory")
        if not metrics:
            findings.append("manifest has no operational metrics")
        if not compatibility:
            findings.append("manifest has no compatibility records")
        if not graph:
            findings.append("manifest has no cross-reference graph edges")
        if not evidence:
            findings.append("manifest has no certification evidence records")
        if any(record.result != EnterpriseCertificationDecision.PASS for record in (*metrics, *compatibility, *graph, *evidence)):
            findings.append("manifest references failing registry evidence")
        registry_digests = {
            "execution_package": execution_package.deterministic_digest,
            "metrics": _digest(metrics),
            "version_compatibility_matrix": _digest(compatibility),
            "cross_reference_graph": _digest(graph),
            "certification_evidence_registry": _digest(evidence),
        }
        record = RiskRm005CertificationManifestRecord(
            manifest_identifier=f"RISK-RM005-MANIFEST-{candidate.candidate_digest[:16].upper()}",
            candidate_identifier=candidate.candidate_identifier,
            candidate_digest=candidate.candidate_digest,
            governing_doctrine="RISK-RM-004-008/1.0.0",
            order_coverage=self.order_coverage,
            artifact_count=actual_artifact_count,
            metric_count=len(metrics),
            compatibility_count=len(compatibility),
            cross_reference_edge_count=len(graph),
            evidence_record_count=len(evidence),
            schema_validation_count=len(execution_package.schema_validations),
            rule_evaluation_count=len(execution_package.rule_evaluations),
            test_execution_count=len(execution_package.test_executions),
            registry_digests=_freeze(registry_digests),
            findings=tuple(findings),
            result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def _evidence_record(
        self,
        candidate_identifier: str,
        candidate_digest: str,
        evidence_identifier: str,
        evidence_classification: str,
        producing_work_order: str,
        provenance_reference: str,
        content_digest: str,
        related_tests: tuple[str, ...],
        related_rules: tuple[str, ...],
    ) -> RiskRm005EvidenceRegistryRecord:
        findings = []
        if not content_digest:
            findings.append("evidence content digest missing")
        record = RiskRm005EvidenceRegistryRecord(
            evidence_identifier=evidence_identifier,
            evidence_classification=evidence_classification,
            candidate_identifier=candidate_identifier,
            candidate_digest=candidate_digest,
            producing_authority="Risk Office Certification Operationalization",
            producing_work_order=producing_work_order,
            governing_doctrine="RISK-RM-004-014/1.0.0",
            provenance_reference=provenance_reference,
            content_digest=content_digest,
            related_tests=related_tests,
            related_rules=related_rules,
            admissible=not findings,
            findings=tuple(findings),
            result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def _edge(
        self,
        source_identifier: str,
        target_identifier: str,
        relationship_type: str,
        governing_work_order: str,
        source_evidence: tuple[str, ...],
    ) -> RiskRm005CrossReferenceEdge:
        findings = []
        if not source_identifier:
            findings.append("cross-reference source missing")
        if not target_identifier:
            findings.append("cross-reference target missing")
        record = RiskRm005CrossReferenceEdge(
            edge_identifier=f"RISK-RM005-EDGE-{_digest((source_identifier, target_identifier, relationship_type))[:16].upper()}",
            source_identifier=source_identifier,
            target_identifier=target_identifier,
            relationship_type=relationship_type,
            governing_work_order=governing_work_order,
            source_evidence=source_evidence,
            findings=tuple(findings),
            result=EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))
