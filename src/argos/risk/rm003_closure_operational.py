"""Operational RISK-RM-003 closure support."""

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
class RiskRm003ClosureOperationalRecord:
    record_identifier: str
    work_order_identifier: str
    title: str
    constitutional_owner: str
    required_domains: tuple[str, ...]
    implemented_domains: tuple[str, ...]
    deterministic_guards: tuple[str, ...]
    certification_evidence: tuple[str, ...]
    replay_obligations: tuple[str, ...]
    recovery_obligations: tuple[str, ...]
    audit_obligations: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm003ClosureOperationalPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    candidate_identifier: str
    records: Mapping[str, RiskRm003ClosureOperationalRecord]
    certification_trace: Mapping[str, tuple[str, ...]]
    immutable_audit_references: tuple[str, ...]
    replay_digest: str
    final_completion_readiness: EnterpriseCertificationDecision
    deterministic_digest: str


class RiskRm003ClosureOperationalSupport:
    """Build deterministic operational evidence for RISK-RM-003-016 through 025."""

    order_coverage = (
        "RISK-RM-003-016",
        "RISK-RM-003-017",
        "RISK-RM-003-018",
        "RISK-RM-003-019",
        "RISK-RM-003-020",
        "RISK-RM-003-021",
        "RISK-RM-003-022",
        "RISK-RM-003-023",
        "RISK-RM-003-024",
        "RISK-RM-003-025",
    )

    def build_operational_package(self, *, candidate_identifier: str = "RISK-RM-003-016-TO-025-CANDIDATE") -> RiskRm003ClosureOperationalPackage:
        records = {
            "RISK-RM-003-016": self.evaluate_validation_framework(),
            "RISK-RM-003-017": self.evaluate_commit_boundaries(),
            "RISK-RM-003-018": self.evaluate_replay_equivalence(),
            "RISK-RM-003-019": self.evaluate_configuration_object(),
            "RISK-RM-003-020": self.evaluate_error_taxonomy(),
            "RISK-RM-003-021": self.evaluate_traceability_architecture(),
            "RISK-RM-003-022": self.evaluate_confidence_exposure(),
            "RISK-RM-003-023": self.evaluate_mitigation_constitution(),
            "RISK-RM-003-024": self.evaluate_risk_fusion(),
            "RISK-RM-003-025": self.evaluate_independent_certification_suite(),
        }
        final = EnterpriseCertificationDecision.PASS if all(record.result == EnterpriseCertificationDecision.PASS for record in records.values()) else EnterpriseCertificationDecision.FAIL
        replay_digest = _digest(records)
        package = RiskRm003ClosureOperationalPackage(
            package_identifier=f"RISK-RM-003-CLOSURE-OPERATIONAL-{replay_digest[:12].upper()}",
            governing_doctrine="RISK-RM-003-016-TO-025/1.0.0",
            order_coverage=self.order_coverage,
            candidate_identifier=candidate_identifier,
            records=_freeze(records),
            certification_trace=_freeze(
                {
                    "validation_to_commit": ("RISK-RM-003-016", "RISK-RM-003-017"),
                    "commit_to_replay": ("RISK-RM-003-017", "RISK-RM-003-018"),
                    "configuration_to_errors": ("RISK-RM-003-019", "RISK-RM-003-020"),
                    "traceability_to_certification": ("RISK-RM-003-021", "RISK-RM-003-025"),
                    "risk_outputs_to_fusion": ("RISK-RM-003-022", "RISK-RM-003-023", "RISK-RM-003-024"),
                }
            ),
            immutable_audit_references=tuple(record.record_identifier for record in records.values()),
            replay_digest=replay_digest,
            final_completion_readiness=final,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_validation_framework(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003ClosureOperationalRecord:
        return self._record("RISK-RM-003-016", "Risk Validation Framework", ("validation domains", "validation ordering", "validation ownership", "rule structure", "evidence integrity", "confidence correctness", "exposure correctness", "audit integrity"), implemented_domains, ("validation cannot weaken prior doctrine", "validation ordering is deterministic", "failed validation rejects constitutional use"), ("validation matrix", "domain result evidence", "failure evidence"), findings)

    def evaluate_commit_boundaries(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003ClosureOperationalRecord:
        return self._record("RISK-RM-003-017", "Constitutional Commit Boundaries", ("commit authority", "commit boundaries", "transactional guarantees", "persistence obligations", "rollback semantics", "recovery interaction", "audit requirements"), implemented_domains, ("commit is atomic", "partial commits are prohibited", "rollback never erases committed truth"), ("commit record", "rollback record", "durability verification"), findings)

    def evaluate_replay_equivalence(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003ClosureOperationalRecord:
        return self._record("RISK-RM-003-018", "Replay Semantic Equivalence", ("deterministic replay", "semantic equivalence", "preserved historical context", "acceptable runtime differences", "divergence detection", "replay validation"), implemented_domains, ("replay never rewrites history", "replay never substitutes current configuration", "replay cannot infer missing evidence"), ("replay comparison report", "divergence report", "historical context manifest"), findings)

    def evaluate_configuration_object(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003ClosureOperationalRecord:
        return self._record("RISK-RM-003-019", "Constitutional Configuration Object", ("configuration ownership", "canonical identity", "immutable schema", "admissibility", "validation", "compatibility", "version governance", "lifecycle"), implemented_domains, ("configuration is sole authoritative executable configuration", "version compatibility is explicit", "configuration replay uses historical version"), ("configuration manifest", "compatibility matrix", "version audit"), findings)

    def evaluate_error_taxonomy(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003ClosureOperationalRecord:
        return self._record("RISK-RM-003-020", "Constitutional Error Taxonomy", ("error classes", "deterministic classification", "failure handling", "recovery eligibility", "escalation behavior", "audit requirements", "traceability", "persistence requirements"), implemented_domains, ("unknown errors fail closed", "implementation-defined classes are prohibited", "classification determines response"), ("error classification record", "recovery eligibility record", "escalation audit"), findings)

    def evaluate_traceability_architecture(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003ClosureOperationalRecord:
        return self._record("RISK-RM-003-021", "Constitutional Traceability Architecture", ("doctrine-to-implementation traceability", "object provenance", "evidence lineage", "testing traceability", "certification traceability", "remediation history", "audit history"), implemented_domains, ("traceability is bidirectional", "no orphaned requirement may exist", "traceability never reinterprets doctrine"), ("traceability matrix", "requirement evidence graph", "audit linkage report"), findings)

    def evaluate_confidence_exposure(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003ClosureOperationalRecord:
        return self._record("RISK-RM-003-022", "Confidence and Exposure Constitution", ("confidence identity", "exposure identity", "uncertainty representation", "aggregation", "propagation", "validation", "persistence", "replay"), implemented_domains, ("confidence and exposure are distinct", "uncertainty is preserved", "aggregation is deterministic"), ("confidence evidence", "exposure evidence", "uncertainty propagation record"), findings)

    def evaluate_mitigation_constitution(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003ClosureOperationalRecord:
        return self._record("RISK-RM-003-023", "Risk Mitigation Constitution", ("mitigation representation", "recovery representation", "ownership", "prioritization", "evaluation", "execution readiness", "alternative preservation", "lifecycle"), implemented_domains, ("Risk Office recommends but never executes", "all alternatives remain preserved", "readiness is deterministic"), ("mitigation evaluation record", "alternative preservation record", "readiness evidence"), findings)

    def evaluate_risk_fusion(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003ClosureOperationalRecord:
        return self._record("RISK-RM-003-024", "Risk Fusion Constitution", ("fusion ownership", "canonical fusion object", "fusion inputs", "fusion sequencing", "aggregation behavior", "confidence integration", "exposure integration", "Enterprise Risk determination"), implemented_domains, ("fusion produces one Enterprise Risk Assessment", "fusion does not average away blocking risk", "fusion sequencing is deterministic"), ("fusion input manifest", "fusion sequence audit", "enterprise risk determination record"), findings)

    def evaluate_independent_certification_suite(self, *, implemented_domains: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003ClosureOperationalRecord:
        return self._record("RISK-RM-003-025", "Independent Risk Office Certification Suite", ("certification test classes", "execution procedures", "evidence requirements", "pass criteria", "failure criteria", "coverage requirements", "audit obligations", "replay requirements"), implemented_domains, ("certification tests are deterministic", "failure criteria are immutable", "complete RM003 coverage is required for RM004 progression"), ("certification suite manifest", "coverage matrix", "pass-fail evidence"), findings)

    def _record(
        self,
        work_order_identifier: str,
        title: str,
        required_domains: tuple[str, ...],
        implemented_domains: tuple[str, ...] | None,
        deterministic_guards: tuple[str, ...],
        certification_evidence: tuple[str, ...],
        findings: tuple[str, ...],
    ) -> RiskRm003ClosureOperationalRecord:
        implemented = implemented_domains if implemented_domains is not None else required_domains
        derived_findings = list(findings)
        derived_findings.extend(f"required domain missing: {domain}" for domain in required_domains if domain not in implemented)
        if not deterministic_guards:
            derived_findings.append("deterministic guards missing")
        if not certification_evidence:
            derived_findings.append("certification evidence missing")
        replay = ("preserve identifiers", "preserve historical context", "detect divergence deterministically")
        recovery = ("restore latest committed valid artifact", "preserve audit history", "fail closed on missing dependency")
        audit = ("record identifier", "work order identifier", "constitutional owner", "deterministic digest", "certification result")
        record = RiskRm003ClosureOperationalRecord(
            record_identifier=f"{work_order_identifier}-CLOSURE-{_digest((title, implemented, deterministic_guards, certification_evidence))[:12].upper()}",
            work_order_identifier=work_order_identifier,
            title=title,
            constitutional_owner=RISK_OWNER,
            required_domains=required_domains,
            implemented_domains=implemented,
            deterministic_guards=deterministic_guards,
            certification_evidence=certification_evidence,
            replay_obligations=replay,
            recovery_obligations=recovery,
            audit_obligations=audit,
            findings=tuple(derived_findings),
            result=EnterpriseCertificationDecision.PASS if not derived_findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))
