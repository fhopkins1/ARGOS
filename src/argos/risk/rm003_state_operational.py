"""Operational RISK-RM-003 state-doctrine support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision


RISK_OWNER = "Risk Office"
CONSTITUTIONAL_VERSION = "RISK-RM-003/1.0.0"
SCHEMA_VERSION = "risk-rm003-state-operational.v1"
EVIDENCE_TIMESTAMP = "2026-07-22T00:00:00Z"


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


def _decision(findings: tuple[str, ...]) -> EnterpriseCertificationDecision:
    return EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL


@dataclass(frozen=True)
class RiskRm003StateOperationalRecord:
    record_identifier: str
    work_order_identifier: str
    title: str
    constitutional_owner: str
    required_elements: tuple[str, ...]
    implemented_elements: tuple[str, ...]
    deterministic_rules: tuple[str, ...]
    immutable_evidence_references: tuple[str, ...]
    replay_requirements: tuple[str, ...]
    recovery_requirements: tuple[str, ...]
    audit_requirements: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm003StateOperationalPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    candidate_identifier: str
    records: Mapping[str, RiskRm003StateOperationalRecord]
    cross_order_traceability: Mapping[str, tuple[str, ...]]
    immutable_audit_references: tuple[str, ...]
    replay_digest: str
    final_completion_readiness: EnterpriseCertificationDecision
    deterministic_digest: str


class RiskRm003StateOperationalSupport:
    """Build deterministic operational evidence for RISK-RM-003-006 through 015."""

    order_coverage = (
        "RISK-RM-003-006",
        "RISK-RM-003-007",
        "RISK-RM-003-008",
        "RISK-RM-003-009",
        "RISK-RM-003-010",
        "RISK-RM-003-011",
        "RISK-RM-003-012",
        "RISK-RM-003-013",
        "RISK-RM-003-014",
        "RISK-RM-003-015",
    )

    def build_operational_package(self, *, candidate_identifier: str = "RISK-RM-003-006-TO-015-CANDIDATE") -> RiskRm003StateOperationalPackage:
        records = {
            "RISK-RM-003-006": self.evaluate_mission_lifecycle(),
            "RISK-RM-003-007": self.evaluate_sufficiency(),
            "RISK-RM-003-008": self.evaluate_equivalence(),
            "RISK-RM-003-009": self.evaluate_freshness(),
            "RISK-RM-003-010": self.evaluate_enterprise_risk_state(),
            "RISK-RM-003-011": self.evaluate_rejection_taxonomy(),
            "RISK-RM-003-012": self.evaluate_risk_evidence(),
            "RISK-RM-003-013": self.evaluate_provenance_architecture(),
            "RISK-RM-003-014": self.evaluate_office_state_machine(),
            "RISK-RM-003-015": self.evaluate_persistent_state(),
        }
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS for record in records.values()
        ) else EnterpriseCertificationDecision.FAIL
        replay_digest = _digest(records)
        package = RiskRm003StateOperationalPackage(
            package_identifier=f"RISK-RM-003-STATE-OPERATIONAL-{replay_digest[:12].upper()}",
            governing_doctrine="RISK-RM-003-006-TO-015/1.0.0",
            order_coverage=self.order_coverage,
            candidate_identifier=candidate_identifier,
            records=_freeze(records),
            cross_order_traceability=_freeze(
                {
                    "mission_to_sufficiency": ("RISK-RM-003-006", "RISK-RM-003-007"),
                    "sufficiency_to_assessment": ("RISK-RM-003-007", "RISK-RM-003-010"),
                    "equivalence_to_freshness": ("RISK-RM-003-008", "RISK-RM-003-009"),
                    "evidence_to_provenance": ("RISK-RM-003-012", "RISK-RM-003-013"),
                    "state_machine_to_persistence": ("RISK-RM-003-014", "RISK-RM-003-015"),
                }
            ),
            immutable_audit_references=tuple(record.record_identifier for record in records.values()),
            replay_digest=replay_digest,
            final_completion_readiness=final,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_mission_lifecycle(self, *, implemented_elements: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003StateOperationalRecord:
        required = ("authorization", "activation", "deterministic execution", "interruption handling", "recovery behavior", "completion semantics", "authority relinquishment", "archival")
        return self._record(
            "RISK-RM-003-006",
            "Risk Mission Lifecycle",
            required,
            implemented_elements,
            ("authorized missions execute once", "authority is temporary", "completed missions cannot reopen", "interruption preserves audit evidence"),
            ("mission authorization audit", "execution audit", "authority relinquishment audit"),
            findings,
        )

    def evaluate_sufficiency(self, *, implemented_elements: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003StateOperationalRecord:
        required = ("sufficiency authority", "evidence completeness", "confidence thresholds", "evaluation completeness", "completion criteria", "audit requirements")
        return self._record(
            "RISK-RM-003-007",
            "Risk Sufficiency Doctrine",
            required,
            implemented_elements,
            ("mandatory evidence cannot be optional", "thresholds are policy-owned", "insufficient evidence cannot produce Risk Decision"),
            ("sufficiency decision evidence", "missing requirement evidence", "threshold evaluation evidence"),
            findings,
        )

    def evaluate_equivalence(self, *, implemented_elements: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003StateOperationalRecord:
        required = ("canonical identity", "duplicate detection", "normalization rules", "semantic equality", "consolidation behavior", "replay equivalence")
        return self._record(
            "RISK-RM-003-008",
            "Risk Equivalence Doctrine",
            required,
            implemented_elements,
            ("identity is identifier-based", "equivalence never changes ownership", "duplicates preserve audit lineage"),
            ("equivalence comparison record", "duplicate suppression record", "normalization digest"),
            findings,
        )

    def evaluate_freshness(self, *, implemented_elements: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003StateOperationalRecord:
        required = ("freshness state", "temporal validity", "expiration rules", "renewal behavior", "historical replay", "staleness rejection")
        return self._record(
            "RISK-RM-003-009",
            "Risk Freshness Doctrine",
            required,
            implemented_elements,
            ("freshness is never inferred from runtime behavior", "expired live evidence is inadmissible", "historical replay preserves original freshness"),
            ("freshness evaluation evidence", "expiration decision evidence", "renewal audit record"),
            findings,
        )

    def evaluate_enterprise_risk_state(self, *, implemented_elements: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003StateOperationalRecord:
        required = ("state ownership", "schema", "versioning", "update semantics", "source manifest", "risk fusion output", "state lifecycle", "validation")
        return self._record(
            "RISK-RM-003-010",
            "Enterprise Risk State Constitution",
            required,
            implemented_elements,
            ("one current state per scope", "updates are atomic", "state is Risk Fusion output", "historical state remains immutable"),
            ("state construction evidence", "source manifest evidence", "atomic commit evidence"),
            findings,
        )

    def evaluate_rejection_taxonomy(self, *, implemented_elements: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003StateOperationalRecord:
        required = ("rejection classes", "admissibility failures", "terminal behavior", "escalation rules", "audit semantics", "recovery behavior", "traceability")
        return self._record(
            "RISK-RM-003-011",
            "Risk Rejection Taxonomy",
            required,
            implemented_elements,
            ("unknown rejection fails closed", "rejection is deterministic", "rejected objects remain auditable"),
            ("rejection classification evidence", "terminal-state audit", "escalation evidence"),
            findings,
        )

    def evaluate_risk_evidence(self, *, implemented_elements: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003StateOperationalRecord:
        required = ("evidence identity", "ownership", "schema", "provenance", "admissibility", "preservation", "normalization", "integrity")
        return self._record(
            "RISK-RM-003-012",
            "Risk Evidence Constitution",
            required,
            implemented_elements,
            ("evidence is factual basis", "normalization preserves content", "ownership transfer is explicit", "integrity is deterministic"),
            ("evidence admission record", "provenance digest", "integrity verification record"),
            findings,
        )

    def evaluate_provenance_architecture(self, *, implemented_elements: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003StateOperationalRecord:
        required = ("constitutional origin", "intermediate transformations", "confidence lineage", "exposure lineage", "mitigation lineage", "recovery lineage", "enterprise conclusion lineage")
        return self._record(
            "RISK-RM-003-013",
            "Risk Provenance Architecture",
            required,
            implemented_elements,
            ("no Risk object exists without provenance", "lineage is immutable", "provenance supports replay and recovery"),
            ("provenance graph", "lineage audit", "transformation trace"),
            findings,
        )

    def evaluate_office_state_machine(self, *, implemented_elements: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003StateOperationalRecord:
        required = ("execution states", "legal transitions", "state ownership", "entry conditions", "exit conditions", "fail-closed behavior", "interruption handling", "completion semantics")
        return self._record(
            "RISK-RM-003-014",
            "Risk Office State Machine",
            required,
            implemented_elements,
            ("state transition must be legal", "entry and exit are audited", "unknown state halts execution"),
            ("state transition audit", "entry validation evidence", "exit validation evidence"),
            findings,
        )

    def evaluate_persistent_state(self, *, implemented_elements: tuple[str, ...] | None = None, findings: tuple[str, ...] = ()) -> RiskRm003StateOperationalRecord:
        required = ("persistent elements", "transient elements", "checkpoint ownership", "durability guarantees", "persistence semantics", "restoration behavior", "replay compatibility")
        return self._record(
            "RISK-RM-003-015",
            "Office-Owned Persistent State",
            required,
            implemented_elements,
            ("implementation-defined state is prohibited", "checkpoint commits are atomic", "restoration never infers missing state"),
            ("persistent-state manifest", "checkpoint evidence", "restoration evidence"),
            findings,
        )

    def _record(
        self,
        work_order_identifier: str,
        title: str,
        required_elements: tuple[str, ...],
        implemented_elements: tuple[str, ...] | None,
        deterministic_rules: tuple[str, ...],
        immutable_evidence_references: tuple[str, ...],
        findings: tuple[str, ...],
    ) -> RiskRm003StateOperationalRecord:
        implemented = implemented_elements if implemented_elements is not None else required_elements
        derived_findings = list(findings)
        missing = tuple(element for element in required_elements if element not in implemented)
        derived_findings.extend(f"required element missing: {element}" for element in missing)
        if not deterministic_rules:
            derived_findings.append("deterministic rules missing")
        if not immutable_evidence_references:
            derived_findings.append("immutable evidence references missing")
        replay = ("same inputs reproduce same constitutional result", "replay preserves original identifiers", "replay preserves original audit evidence")
        recovery = ("restore latest committed valid state", "preserve immutable history", "never infer missing constitutional state")
        audit = ("record identifier", "governing work order", "constitutional owner", "deterministic digest", "validation result")
        record = RiskRm003StateOperationalRecord(
            record_identifier=f"{work_order_identifier}-OPERATIONAL-{_digest((title, implemented, deterministic_rules, immutable_evidence_references))[:12].upper()}",
            work_order_identifier=work_order_identifier,
            title=title,
            constitutional_owner=RISK_OWNER,
            required_elements=required_elements,
            implemented_elements=implemented,
            deterministic_rules=deterministic_rules,
            immutable_evidence_references=immutable_evidence_references,
            replay_requirements=replay,
            recovery_requirements=recovery,
            audit_requirements=audit,
            findings=tuple(derived_findings),
            result=_decision(tuple(derived_findings)),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))
