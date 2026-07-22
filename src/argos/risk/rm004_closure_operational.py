"""Operational RISK-RM-004 closure registry support."""

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
class RiskRm004ClosureOperationalRecord:
    record_identifier: str
    work_order_identifier: str
    title: str
    constitutional_owner: str
    required_domains: tuple[str, ...]
    implemented_domains: tuple[str, ...]
    deterministic_guards: tuple[str, ...]
    certification_evidence: tuple[str, ...]
    audit_requirements: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm004ClosureOperationalPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    candidate_identifier: str
    records: Mapping[str, RiskRm004ClosureOperationalRecord]
    closure_trace: Mapping[str, tuple[str, ...]]
    immutable_audit_references: tuple[str, ...]
    replay_digest: str
    final_completion_readiness: EnterpriseCertificationDecision
    deterministic_digest: str


class RiskRm004ClosureOperationalSupport:
    """Build deterministic operational evidence for RISK-RM-004-011 through 020."""

    order_coverage = (
        "RISK-RM-004-011",
        "RISK-RM-004-012",
        "RISK-RM-004-013",
        "RISK-RM-004-014",
        "RISK-RM-004-015",
        "RISK-RM-004-016",
        "RISK-RM-004-017",
        "RISK-RM-004-018",
        "RISK-RM-004-019",
        "RISK-RM-004-020",
    )

    def build_operational_package(self, *, candidate_identifier: str = "RISK-RM-004-011-TO-020-CANDIDATE") -> RiskRm004ClosureOperationalPackage:
        records = {
            "RISK-RM-004-011": self.evaluate_rule_registry(),
            "RISK-RM-004-012": self.evaluate_schema_registry(),
            "RISK-RM-004-013": self.evaluate_cross_reference_matrix(),
            "RISK-RM-004-014": self.evaluate_evidence_registry(),
            "RISK-RM-004-015": self.evaluate_decision_registry(),
            "RISK-RM-004-016": self.evaluate_certification_package_schema(),
            "RISK-RM-004-017": self.evaluate_traceability_matrix(),
            "RISK-RM-004-018": self.evaluate_certification_procedure(),
            "RISK-RM-004-019": self.evaluate_exception_registry(),
            "RISK-RM-004-020": self.evaluate_certification_closure(),
        }
        final = EnterpriseCertificationDecision.PASS if all(record.result == EnterpriseCertificationDecision.PASS for record in records.values()) else EnterpriseCertificationDecision.FAIL
        replay_digest = _digest(records)
        package = RiskRm004ClosureOperationalPackage(
            package_identifier=f"RISK-RM-004-CLOSURE-OPERATIONAL-{replay_digest[:12].upper()}",
            governing_doctrine="RISK-RM-004-011-TO-020/1.0.0",
            order_coverage=self.order_coverage,
            candidate_identifier=candidate_identifier,
            records=_freeze(records),
            closure_trace=_freeze(
                {
                    "rules_to_schemas": ("RISK-RM-004-011", "RISK-RM-004-012"),
                    "registries_to_cross_reference": ("RISK-RM-004-011", "RISK-RM-004-012", "RISK-RM-004-013", "RISK-RM-004-014", "RISK-RM-004-015"),
                    "package_to_traceability": ("RISK-RM-004-016", "RISK-RM-004-017"),
                    "procedure_to_exceptions": ("RISK-RM-004-018", "RISK-RM-004-019"),
                    "procedure_to_closure": ("RISK-RM-004-018", "RISK-RM-004-020"),
                }
            ),
            immutable_audit_references=tuple(record.record_identifier for record in records.values()),
            replay_digest=replay_digest,
            final_completion_readiness=final,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_rule_registry(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004ClosureOperationalRecord:
        return self._record("RISK-RM-004-011", "Constitutional Rule Registry", ("rule identity", "rule ownership", "applicability", "precedence", "versioning", "dependencies", "validation", "certification effect"), implemented_domains, ("only registry rules may affect certification", "rules never redefine doctrine", "precedence is deterministic"), ("rule catalog", "rule dependency graph", "rule certification audit"), findings)

    def evaluate_schema_registry(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004ClosureOperationalRecord:
        return self._record("RISK-RM-004-012", "Constitutional Schema Registry", ("schema identity", "schema ownership", "classification", "applicability", "compatibility", "version governance", "validation requirements", "audit requirements"), implemented_domains, ("schemas are authoritative", "schema compatibility is explicit", "schema validation is mandatory"), ("schema registry", "schema compatibility evidence", "schema validation audit"), findings)

    def evaluate_cross_reference_matrix(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004ClosureOperationalRecord:
        return self._record("RISK-RM-004-013", "Registry Cross-Reference Matrix", ("registry relationships", "identifier spaces", "schema links", "rule links", "artifact dependencies", "dependency structure", "replay support", "auditability"), implemented_domains, ("no registry is isolated", "relationships are deterministic", "matrix does not redefine contents"), ("cross-reference matrix", "dependency matrix", "registry relationship audit"), findings)

    def evaluate_evidence_registry(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004ClosureOperationalRecord:
        return self._record("RISK-RM-004-014", "Certification Evidence Registry", ("evidence ownership", "evidence identity", "evidence classes", "admissibility", "provenance", "integrity verification", "retention", "lifecycle"), implemented_domains, ("certification evidence is immutable", "inadmissible evidence cannot certify", "evidence registry excludes operational Risk evidence"), ("evidence registry", "admissibility record", "integrity verification report"), findings)

    def evaluate_decision_registry(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004ClosureOperationalRecord:
        return self._record("RISK-RM-004-015", "Constitutional Decision Registry", ("decision ownership", "decision categories", "evaluation authority", "deterministic execution", "approval semantics", "persistence", "replay", "auditability"), implemented_domains, ("no decision outside registry", "decisions are deterministic", "approval semantics are explicit"), ("decision registry", "decision audit", "approval/rejection evidence"), findings)

    def evaluate_certification_package_schema(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004ClosureOperationalRecord:
        return self._record("RISK-RM-004-016", "Constitutional Certification Package Schema", ("package structure", "artifact inclusion", "object relationships", "evidence requirements", "registry dependencies", "manifest dependencies", "validation", "archival"), implemented_domains, ("package is self-contained", "package schema does not redefine behavior", "incomplete package is rejected"), ("package schema", "package validation evidence", "artifact inclusion matrix"), findings)

    def evaluate_traceability_matrix(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004ClosureOperationalRecord:
        return self._record("RISK-RM-004-017", "Certification Traceability Matrix", ("traceability identity", "traceability scope", "relationships", "lineage", "dependency mapping", "certification linkage", "audit linkage", "invariants"), implemented_domains, ("traceability is end-to-end", "lineage is bidirectional", "orphaned certification result is prohibited"), ("traceability matrix", "lineage report", "certification linkage evidence"), findings)

    def evaluate_certification_procedure(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004ClosureOperationalRecord:
        return self._record("RISK-RM-004-018", "Constitutional Certification Procedure", ("initiation", "evidence validation", "evaluation sequencing", "registry verification", "rule evaluation", "approval", "rejection", "fail-closed behavior"), implemented_domains, ("procedure order is immutable", "authority cannot reorder workflow", "procedure preserves all evidence"), ("procedure specification", "state transition log", "registry verification report"), findings)

    def evaluate_exception_registry(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004ClosureOperationalRecord:
        return self._record("RISK-RM-004-019", "Certification Exception Registry", ("exception ownership", "exception identity", "admissibility", "approval authority", "documentation", "audit obligations", "lifecycle", "safeguards"), implemented_domains, ("exceptions cannot modify doctrine", "unapproved exceptions fail closed", "exceptions are auditable"), ("exception registry", "approval evidence", "safeguard audit"), findings)

    def evaluate_certification_closure(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm004ClosureOperationalRecord:
        return self._record("RISK-RM-004-020", "Independent Risk Office Certification Closure", ("completion", "issuance", "evidence archival", "certification permanence", "constitutional closure", "post-certification integrity", "recertification prerequisites", "long-term governance"), implemented_domains, ("closed certification is immutable", "closure preserves evidence", "supersession requires authorized recertification"), ("closure record", "certificate issuance evidence", "archival evidence"), findings)

    def _record(
        self,
        work_order_identifier: str,
        title: str,
        required_domains: tuple[str, ...],
        implemented_domains: tuple[str, ...] | None,
        deterministic_guards: tuple[str, ...],
        certification_evidence: tuple[str, ...],
        findings: tuple[str, ...],
    ) -> RiskRm004ClosureOperationalRecord:
        implemented = implemented_domains if implemented_domains is not None else required_domains
        derived_findings = list(findings)
        derived_findings.extend(f"required domain missing: {domain}" for domain in required_domains if domain not in implemented)
        if not deterministic_guards:
            derived_findings.append("deterministic guards missing")
        if not certification_evidence:
            derived_findings.append("certification evidence missing")
        audit = ("record identifier", "work order identifier", "constitutional owner", "deterministic digest", "certification result")
        record = RiskRm004ClosureOperationalRecord(
            record_identifier=f"{work_order_identifier}-CLOSURE-{_digest((title, implemented, deterministic_guards, certification_evidence))[:12].upper()}",
            work_order_identifier=work_order_identifier,
            title=title,
            constitutional_owner=RISK_OWNER,
            required_domains=required_domains,
            implemented_domains=implemented,
            deterministic_guards=deterministic_guards,
            certification_evidence=certification_evidence,
            audit_requirements=audit,
            findings=tuple(derived_findings),
            result=EnterpriseCertificationDecision.PASS if not derived_findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))
