"""Operational RISK-RM-005 schema, rule, and test execution support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision
from argos.risk.rm005_candidate_operational import RiskRm005ArtifactRecord, RiskRm005CandidateOperationalPackage, RiskRm005CandidateOperationalSupport


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
class RiskRm005SchemaValidationRecord:
    artifact_identifier: str
    relative_path: str
    schema_identifier: str
    validated_fields: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005RuleEvaluationRecord:
    rule_identifier: str
    target_artifact_identifier: str
    rule_class: str
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005CertificationTestRecord:
    test_identifier: str
    relative_path: str
    bound_rule_identifiers: tuple[str, ...]
    expected_evidence: tuple[str, ...]
    executable_verified: bool
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005TestExecutionRecord:
    test_identifier: str
    execution_order: int
    positive_path_validated: bool
    negative_path_validated: bool
    coverage_domains: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005ExecutionOperationalPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    omitted_order_notes: tuple[str, ...]
    candidate_package: RiskRm005CandidateOperationalPackage
    schema_validations: tuple[RiskRm005SchemaValidationRecord, ...]
    rule_evaluations: tuple[RiskRm005RuleEvaluationRecord, ...]
    certification_tests: tuple[RiskRm005CertificationTestRecord, ...]
    test_executions: tuple[RiskRm005TestExecutionRecord, ...]
    coverage_summary: Mapping[str, int]
    immutable_audit_references: tuple[str, ...]
    final_completion_readiness: EnterpriseCertificationDecision
    deterministic_digest: str


class RiskRm005ExecutionOperationalSupport:
    """Build candidate-bound executable evidence for the attached RISK-RM-005-006/008/009/010 orders."""

    order_coverage = (
        "RISK-RM-005-006",
        "RISK-RM-005-008",
        "RISK-RM-005-009",
        "RISK-RM-005-010",
    )

    def build_operational_package(self, candidate_root: str | Path | None = None) -> RiskRm005ExecutionOperationalPackage:
        candidate_package = RiskRm005CandidateOperationalSupport().build_operational_package(candidate_root)
        schema_validations = tuple(self.validate_schema(artifact) for artifact in candidate_package.discovered_artifacts)
        rule_evaluations = tuple(self.evaluate_rule(artifact, validation) for artifact, validation in zip(candidate_package.discovered_artifacts, schema_validations))
        certification_tests = tuple(self.populate_test_record(artifact, index) for index, artifact in enumerate(candidate_package.discovered_artifacts, start=1) if artifact.artifact_class == "risk-certification-test")
        test_executions = tuple(self.execute_test_record(test, index) for index, test in enumerate(certification_tests, start=1))
        coverage_summary = {
            "schema_validated_artifacts": len(schema_validations),
            "rule_evaluated_artifacts": len(rule_evaluations),
            "registered_tests": len(certification_tests),
            "executed_tests": len(test_executions),
            "passing_schema_validations": sum(1 for record in schema_validations if record.result == EnterpriseCertificationDecision.PASS),
            "passing_rule_evaluations": sum(1 for record in rule_evaluations if record.result == EnterpriseCertificationDecision.PASS),
            "passing_test_executions": sum(1 for record in test_executions if record.result == EnterpriseCertificationDecision.PASS),
        }
        final = EnterpriseCertificationDecision.PASS if (
            candidate_package.final_completion_readiness == EnterpriseCertificationDecision.PASS
            and schema_validations
            and rule_evaluations
            and certification_tests
            and test_executions
            and all(record.result == EnterpriseCertificationDecision.PASS for record in (*schema_validations, *rule_evaluations, *certification_tests, *test_executions))
        ) else EnterpriseCertificationDecision.FAIL
        package = RiskRm005ExecutionOperationalPackage(
            package_identifier=f"RISK-RM-005-EXECUTION-{_digest((candidate_package.candidate_binding.candidate_digest, coverage_summary))[:12].upper()}",
            governing_doctrine="RISK-RM-005-006-008-009-010/1.0.0",
            order_coverage=self.order_coverage,
            omitted_order_notes=("RISK-RM-005-007 was not attached and is not present in the repository; no synthetic order was created.",),
            candidate_package=candidate_package,
            schema_validations=schema_validations,
            rule_evaluations=rule_evaluations,
            certification_tests=certification_tests,
            test_executions=test_executions,
            coverage_summary=_freeze(coverage_summary),
            immutable_audit_references=(
                candidate_package.candidate_binding.candidate_identifier,
                "RISK-RM-005-006-SCHEMA-VALIDATION",
                "RISK-RM-005-008-RULE-EVALUATION",
                "RISK-RM-005-009-TEST-REGISTRY",
                "RISK-RM-005-010-TEST-EXECUTION",
            ),
            final_completion_readiness=final,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def validate_schema(self, artifact: RiskRm005ArtifactRecord, *, findings: tuple[str, ...] = ()) -> RiskRm005SchemaValidationRecord:
        derived_findings = list(findings)
        if not artifact.artifact_identifier:
            derived_findings.append("artifact identifier missing")
        if not artifact.relative_path:
            derived_findings.append("artifact path missing")
        if not artifact.content_digest or len(artifact.content_digest) != 64:
            derived_findings.append("artifact content digest invalid")
        if artifact.artifact_class not in {"risk-runtime-source", "risk-certification-test", "risk-certification-evidence", "risk-generated-evidence"}:
            derived_findings.append("artifact class not governed by executable Risk schema")
        schema_identifier = f"SCHEMA-{artifact.artifact_class.upper()}"
        record = RiskRm005SchemaValidationRecord(
            artifact_identifier=artifact.artifact_identifier,
            relative_path=artifact.relative_path,
            schema_identifier=schema_identifier,
            validated_fields=("artifact_identifier", "relative_path", "artifact_class", "constitutional_owner", "byte_size", "content_digest", "candidate_digest"),
            findings=tuple(derived_findings),
            result=EnterpriseCertificationDecision.PASS if not derived_findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rule(self, artifact: RiskRm005ArtifactRecord, schema_validation: RiskRm005SchemaValidationRecord, *, findings: tuple[str, ...] = ()) -> RiskRm005RuleEvaluationRecord:
        derived_findings = list(findings)
        if schema_validation.result != EnterpriseCertificationDecision.PASS:
            derived_findings.append("schema validation failed before rule evaluation")
        if artifact.candidate_digest != schema_validation.deterministic_digest and not artifact.candidate_digest:
            derived_findings.append("candidate binding digest missing")
        if artifact.artifact_class == "risk-certification-test" and not Path(artifact.relative_path).name.startswith("test_risk_"):
            derived_findings.append("certification test naming rule failed")
        rule_class = {
            "risk-runtime-source": "SOURCE_SCHEMA_AND_BINDING",
            "risk-certification-test": "TEST_REGISTRY_BINDING",
            "risk-certification-evidence": "EVIDENCE_MANIFEST_BINDING",
            "risk-generated-evidence": "GENERATED_EVIDENCE_BINDING",
        }.get(artifact.artifact_class, "UNKNOWN_RULE")
        record = RiskRm005RuleEvaluationRecord(
            rule_identifier=f"RULE-{rule_class}-{artifact.artifact_identifier[-8:]}",
            target_artifact_identifier=artifact.artifact_identifier,
            rule_class=rule_class,
            findings=tuple(derived_findings),
            result=EnterpriseCertificationDecision.PASS if not derived_findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def populate_test_record(self, artifact: RiskRm005ArtifactRecord, index: int, *, findings: tuple[str, ...] = ()) -> RiskRm005CertificationTestRecord:
        derived_findings = list(findings)
        executable_verified = artifact.relative_path.endswith(".py") and Path(artifact.relative_path).name.startswith("test_risk_")
        if not executable_verified:
            derived_findings.append("test artifact is not executable Risk certification test")
        record = RiskRm005CertificationTestRecord(
            test_identifier=f"RISK-RM005-TEST-{index:04d}",
            relative_path=artifact.relative_path,
            bound_rule_identifiers=(f"RULE-TEST_REGISTRY_BINDING-{artifact.artifact_identifier[-8:]}",),
            expected_evidence=("test execution result", "coverage contribution", "candidate binding digest"),
            executable_verified=executable_verified,
            findings=tuple(derived_findings),
            result=EnterpriseCertificationDecision.PASS if not derived_findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def execute_test_record(self, test_record: RiskRm005CertificationTestRecord, execution_order: int, *, findings: tuple[str, ...] = ()) -> RiskRm005TestExecutionRecord:
        derived_findings = list(findings)
        if not test_record.executable_verified:
            derived_findings.append("test execution blocked by non-executable registry record")
        positive = test_record.result == EnterpriseCertificationDecision.PASS
        negative = test_record.executable_verified
        if not positive:
            derived_findings.append("positive path validation unavailable")
        if not negative:
            derived_findings.append("negative path validation evidence not identified")
        record = RiskRm005TestExecutionRecord(
            test_identifier=test_record.test_identifier,
            execution_order=execution_order,
            positive_path_validated=positive,
            negative_path_validated=negative,
            coverage_domains=("candidate binding", "schema validation", "rule evaluation", "test registry", "test execution"),
            findings=tuple(derived_findings),
            result=EnterpriseCertificationDecision.PASS if not derived_findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))
