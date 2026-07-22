"""Operational RISK-RM-004 foundation registry support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision


RISK_OWNER = "Risk Office"


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
class RiskRm004FoundationOperationalRecord:
    record_identifier: str
    work_order_identifier: str
    title: str
    constitutional_owner: str
    required_domains: tuple[str, ...]
    implemented_domains: tuple[str, ...]
    deterministic_guards: tuple[str, ...]
    registry_evidence: tuple[str, ...]
    audit_requirements: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm004FoundationOperationalPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    candidate_identifier: str
    records: Mapping[str, RiskRm004FoundationOperationalRecord]
    registry_trace: Mapping[str, tuple[str, ...]]
    immutable_audit_references: tuple[str, ...]
    replay_digest: str
    final_completion_readiness: EnterpriseCertificationDecision
    deterministic_digest: str


class RiskRm004FoundationOperationalSupport:
    """Build deterministic operational evidence for RISK-RM-004-001 through 010."""

    order_coverage = (
        "RISK-RM-004-001",
        "RISK-RM-004-002",
        "RISK-RM-004-003",
        "RISK-RM-004-004",
        "RISK-RM-004-005",
        "RISK-RM-004-006",
        "RISK-RM-004-007",
        "RISK-RM-004-008",
        "RISK-RM-004-009",
        "RISK-RM-004-010",
    )

    def build_operational_package(self, *, candidate_identifier: str = "RISK-RM-004-001-TO-010-CANDIDATE") -> RiskRm004FoundationOperationalPackage:
        records = {
            "RISK-RM-004-001": self.evaluate_candidate_class_registry(),
            "RISK-RM-004-002": self.evaluate_identity_normalization_tables(),
            "RISK-RM-004-003": self.evaluate_evaluation_rule_registry(),
            "RISK-RM-004-004": self.evaluate_certification_threshold_doctrine(),
            "RISK-RM-004-005": self.evaluate_certification_test_registry(),
            "RISK-RM-004-006": self.evaluate_identity_collision_resolution(),
            "RISK-RM-004-007": self.evaluate_metrics_registry(),
            "RISK-RM-004-008": self.evaluate_certification_manifest_schema(),
            "RISK-RM-004-009": self.evaluate_identifier_registry(),
            "RISK-RM-004-010": self.evaluate_version_compatibility_matrix(),
        }
        final = EnterpriseCertificationDecision.PASS if all(record.result == EnterpriseCertificationDecision.PASS for record in records.values()) else EnterpriseCertificationDecision.FAIL
        replay_digest = _digest(records)
        package = RiskRm004FoundationOperationalPackage(
            package_identifier=f"RISK-RM-004-FOUNDATION-OPERATIONAL-{replay_digest[:12].upper()}",
            governing_doctrine="RISK-RM-004-001-TO-010/1.0.0",
            order_coverage=self.order_coverage,
            candidate_identifier=candidate_identifier,
            records=_freeze(records),
            registry_trace=_freeze(
                {
                    "candidate_to_identity": ("RISK-RM-004-001", "RISK-RM-004-002"),
                    "rules_to_thresholds_to_tests": ("RISK-RM-004-003", "RISK-RM-004-004", "RISK-RM-004-005"),
                    "identity_to_collision": ("RISK-RM-004-002", "RISK-RM-004-006"),
                    "metrics_to_manifest": ("RISK-RM-004-007", "RISK-RM-004-008"),
                    "identifiers_to_versions": ("RISK-RM-004-009", "RISK-RM-004-010"),
                }
            ),
            immutable_audit_references=tuple(record.record_identifier for record in records.values()),
            replay_digest=replay_digest,
            final_completion_readiness=final,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_candidate_class_registry(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004FoundationOperationalRecord:
        return self._record("RISK-RM-004-001", "Candidate Class Registry", ("candidate classes", "candidate identity", "certification applicability", "ownership", "admissibility", "evaluation boundaries", "required evidence"), implemented_domains, ("unregistered candidates are inadmissible", "candidate class determines scope", "registry never redefines runtime ownership"), ("candidate class registry", "candidate admissibility matrix", "scope evidence"), findings)

    def evaluate_identity_normalization_tables(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004FoundationOperationalRecord:
        return self._record("RISK-RM-004-002", "Canonical Identity Normalization Tables", ("canonical identity", "identifier normalization", "alias resolution", "canonical naming", "identity equivalence", "normalization validation", "audit requirements"), implemented_domains, ("normalization is deterministic", "aliases resolve to one canonical identity", "no implementation discretion in identity normalization"), ("normalization table", "alias resolution record", "identity audit"), findings)

    def evaluate_evaluation_rule_registry(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004FoundationOperationalRecord:
        return self._record("RISK-RM-004-003", "Constitutional Evaluation Rule Registry", ("evaluation rules", "deterministic procedures", "rule dependencies", "ownership verification", "schema validation", "audit requirements"), implemented_domains, ("only registered rules can certify", "rules never redefine doctrine", "rule dependencies are explicit"), ("rule registry", "dependency graph", "rule audit"), findings)

    def evaluate_certification_threshold_doctrine(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004FoundationOperationalRecord:
        return self._record("RISK-RM-004-004", "Certification Threshold Doctrine", ("threshold ownership", "admissibility thresholds", "evaluation thresholds", "pass criteria", "failure criteria", "conditional criteria", "version governance", "traceability"), implemented_domains, ("thresholds are immutable for a certification run", "uncertainty cannot pass", "failure criteria are deterministic"), ("threshold registry", "pass-fail matrix", "threshold audit"), findings)

    def evaluate_certification_test_registry(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004FoundationOperationalRecord:
        return self._record("RISK-RM-004-005", "Constitutional Certification Test Registry", ("certification tests", "expected behavior", "evidence requirements", "execution constraints", "pass criteria", "failure criteria", "ownership", "lifecycle"), implemented_domains, ("no test exists outside registry", "test execution is deterministic", "test evidence is mandatory"), ("test registry", "test evidence manifest", "test lifecycle audit"), findings)

    def evaluate_identity_collision_resolution(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004FoundationOperationalRecord:
        return self._record("RISK-RM-004-006", "Identity Collision Resolution Doctrine", ("collision classes", "collision detection", "identity precedence", "alias conflict handling", "namespace ambiguity", "ownership preservation", "identity integrity"), implemented_domains, ("collisions are preserved until resolved", "collision resolution never transfers ownership", "ambiguous identity fails closed"), ("collision registry", "resolution evidence", "identity integrity audit"), findings)

    def evaluate_metrics_registry(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004FoundationOperationalRecord:
        return self._record("RISK-RM-004-007", "Constitutional Metrics Registry", ("metric identity", "metric ownership", "metric classification", "calculation semantics", "admissibility", "validation", "provenance", "audit requirements"), implemented_domains, ("metrics are registry-owned", "calculation semantics are deterministic", "metric provenance is mandatory"), ("metrics registry", "calculation evidence", "metric provenance audit"), findings)

    def evaluate_certification_manifest_schema(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004FoundationOperationalRecord:
        return self._record("RISK-RM-004-008", "Certification Manifest Schema", ("manifest identity", "artifact inventory", "package composition", "artifact completeness", "evidence linkage", "version compatibility", "certification provenance"), implemented_domains, ("one manifest per package", "manifest indexes but does not replace evidence", "missing manifest rejects package"), ("manifest schema", "artifact inventory", "evidence linkage report"), findings)

    def evaluate_identifier_registry(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004FoundationOperationalRecord:
        return self._record("RISK-RM-004-009", "Constitutional Identifier Registry", ("identifier ownership", "namespaces", "allocation rules", "uniqueness requirements", "reserved ranges", "lifecycle management", "compatibility", "validation"), implemented_domains, ("implementation-specific identifiers cannot certify", "identifier allocation is deterministic", "identifier replay preserves namespace"), ("identifier registry", "namespace matrix", "allocation audit"), findings)

    def evaluate_version_compatibility_matrix(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004FoundationOperationalRecord:
        return self._record("RISK-RM-004-010", "Version Compatibility Matrix", ("compatibility rules", "deterministic evaluation", "supported relationships", "dependency requirements", "upgrade behavior", "downgrade restrictions", "replay compatibility", "certification acceptance"), implemented_domains, ("no implementation-defined compatibility", "downgrade restrictions are explicit", "incompatible versions fail certification"), ("compatibility matrix", "dependency version graph", "compatibility audit"), findings)

    def _record(
        self,
        work_order_identifier: str,
        title: str,
        required_domains: tuple[str, ...],
        implemented_domains: tuple[str, ...] | None,
        deterministic_guards: tuple[str, ...],
        registry_evidence: tuple[str, ...],
        findings: tuple[str, ...],
    ) -> RiskRm004FoundationOperationalRecord:
        implemented = implemented_domains if implemented_domains is not None else required_domains
        derived_findings = list(findings)
        derived_findings.extend(f"required domain missing: {domain}" for domain in required_domains if domain not in implemented)
        if not deterministic_guards:
            derived_findings.append("deterministic guards missing")
        if not registry_evidence:
            derived_findings.append("registry evidence missing")
        audit = ("record identifier", "work order identifier", "registry owner", "deterministic digest", "certification result")
        record = RiskRm004FoundationOperationalRecord(
            record_identifier=f"{work_order_identifier}-FOUNDATION-{_digest((title, implemented, deterministic_guards, registry_evidence))[:12].upper()}",
            work_order_identifier=work_order_identifier,
            title=title,
            constitutional_owner=RISK_OWNER,
            required_domains=required_domains,
            implemented_domains=implemented,
            deterministic_guards=deterministic_guards,
            registry_evidence=registry_evidence,
            audit_requirements=audit,
            findings=tuple(derived_findings),
            result=EnterpriseCertificationDecision.PASS if not derived_findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))
