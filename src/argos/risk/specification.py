"""RISK-RM-003 constitutional specification program support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision


@dataclass(frozen=True)
class RiskSpecificationWorkOrder:
    work_order_identifier: str
    title: str
    purpose: str


@dataclass(frozen=True)
class RiskRm003SpecificationProgramRecord:
    record_identifier: str
    program_identifier: str
    objectives: tuple[str, ...]
    constitutional_principles: tuple[str, ...]
    complete_specification_fields: tuple[str, ...]
    work_orders: tuple[RiskSpecificationWorkOrder, ...]
    work_order_completion_requirements: tuple[str, ...]
    deliverables: tuple[str, ...]
    completion_criteria: tuple[str, ...]
    excluded_certification_domains: tuple[str, ...]
    missing_work_order_findings: tuple[str, ...]
    ownership_boundary_findings: tuple[str, ...]
    guarantee_regression_findings: tuple[str, ...]
    interpretation_findings: tuple[str, ...]
    deliverable_gaps: tuple[str, ...]
    evidence_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


class RiskOfficeSpecificationSupport:
    """Build deterministic RISK-RM-003 specification-program evidence."""

    def build_specification_program_record(
        self,
        *,
        missing_work_order_findings: tuple[str, ...] = (),
        ownership_boundary_findings: tuple[str, ...] = (),
        guarantee_regression_findings: tuple[str, ...] = (),
        interpretation_findings: tuple[str, ...] = (),
        deliverable_gaps: tuple[str, ...] = (),
        evidence_gaps: tuple[str, ...] = (),
    ) -> RiskRm003SpecificationProgramRecord:
        objectives = ("immutable engineering specifications for every Risk-owned responsibility", "complete constitutional object definitions", "complete deterministic risk evaluation semantics", "immutable risk assessment architecture", "complete mitigation and recovery behavior", "deterministic confidence evaluation", "immutable validation behavior", "deterministic persistence replay and recovery semantics", "immutable traceability requirements", "no remaining engineering interpretation", "readiness for RISK-RM-004")
        principles = ("Immutable Constitutional Engineering", "Deterministic Risk Evaluation", "Complete Constitutional Specification", "Elimination of Engineering Interpretation", "Independent Office Certification")
        fields_required = ("ownership", "identity", "schema", "lifecycle", "invariants", "validation", "persistence", "replay", "recovery", "auditability")
        requirements = ("define immutable constitutional engineering specifications", "eliminate implementation interpretation", "preserve previously certified ARGOS doctrine", "establish deterministic constitutional behavior", "define ownership validation persistence replay recovery and audit requirements", "produce certification-suitable constitutional evidence", "never redefine ownership outside Risk Office", "never weaken RISK-RM-001 or RISK-RM-002 guarantees")
        deliverables = ("complete constitutional engineering specifications for every Risk-owned object", "deterministic risk evaluation architecture", "complete lifecycle specifications", "immutable validation doctrine", "complete persistence replay and recovery specifications", "complete traceability architecture", "immutable confidence exposure mitigation and risk fusion models", "complete independent certification test suite")
        criteria = ("every Constitutional Specification Work Order complete", "every Risk-owned constitutional object has complete engineering specification", "deterministic execution specified for all Risk-owned responsibilities", "no engineering interpretation remains", "sufficient engineering evidence exists to begin RISK-RM-004")
        excluded = ("Enterprise Integration Certification", "Workflow Certification", "Bridge Certification", "Enterprise Constitutional Certification")
        work_orders = _risk_rm003_work_orders()
        expected_ids = tuple(f"RISK-RM-003-{index:03d}" for index in range(1, 26))
        actual_ids = tuple(order.work_order_identifier for order in work_orders)
        missing_ids = tuple(identifier for identifier in expected_ids if identifier not in actual_ids)
        passed = not missing_ids and not missing_work_order_findings and not ownership_boundary_findings and not guarantee_regression_findings and not interpretation_findings and not deliverable_gaps and not evidence_gaps
        record = RiskRm003SpecificationProgramRecord(
            record_identifier=f"RISK-RM-003-PROGRAM-{_digest((work_orders, objectives))[:12].upper()}",
            program_identifier="RISK-RM-003",
            objectives=objectives,
            constitutional_principles=principles,
            complete_specification_fields=fields_required,
            work_orders=work_orders,
            work_order_completion_requirements=requirements,
            deliverables=deliverables,
            completion_criteria=criteria,
            excluded_certification_domains=excluded,
            missing_work_order_findings=missing_ids + missing_work_order_findings,
            ownership_boundary_findings=ownership_boundary_findings,
            guarantee_regression_findings=guarantee_regression_findings,
            interpretation_findings=interpretation_findings,
            deliverable_gaps=deliverable_gaps,
            evidence_gaps=evidence_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))


def _risk_rm003_work_orders() -> tuple[RiskSpecificationWorkOrder, ...]:
    rows = (
        ("RISK-RM-003-001", "Risk Assessment Canonical Object", "Define the immutable constitutional Risk Assessment object, including ownership, identity, schema, authority, lifecycle relationships, and invariants."),
        ("RISK-RM-003-002", "Risk Evaluation Plan Constitutional Contract", "Define the canonical Risk Evaluation Plan, execution constraints, admissibility rules, evaluation sequencing, and constitutional completion contract."),
        ("RISK-RM-003-003", "Risk Evaluation Package Constitution", "Define the immutable Risk Evaluation Package schema, ownership, admissibility, validation requirements, object relationships, and constitutional integrity."),
        ("RISK-RM-003-004", "Risk Evaluation Graph Constitution", "Define the canonical Risk Evaluation Graph governing evidence relationships, dependency structure, provenance, evaluation ordering, and deterministic execution."),
        ("RISK-RM-003-005", "Risk Object Lifecycle", "Define deterministic lifecycle states governing every Risk-owned object from creation through supersession, archival, and retirement."),
        ("RISK-RM-003-006", "Risk Evaluation Mission Lifecycle", "Define the complete execution lifecycle governing constitutional Risk Evaluation Missions from authorization through authority relinquishment."),
        ("RISK-RM-003-007", "Risk Sufficiency Doctrine", "Define deterministic sufficiency evaluation, constitutional completion criteria, minimum evidence requirements, and risk acceptance thresholds."),
        ("RISK-RM-003-008", "Risk Equivalence Doctrine", "Define canonical equivalence, duplicate detection, normalization rules, semantic equality, and consolidation behavior for Risk-owned objects."),
        ("RISK-RM-003-009", "Risk Freshness Doctrine", "Define evidence freshness, temporal validity, expiration rules, replay admissibility, and constitutional staleness behavior."),
        ("RISK-RM-003-010", "Enterprise Risk State Constitution", "Define the immutable Enterprise Risk State, ownership, versioning, update semantics, constitutional relationships, and invariants."),
        ("RISK-RM-003-011", "Risk Rejection Taxonomy", "Define deterministic rejection classes, rejection causes, terminal behavior, audit semantics, and constitutional failure handling."),
        ("RISK-RM-003-012", "Risk Evidence Constitution", "Define immutable Risk Evidence schema, provenance, admissibility, preservation, normalization, ownership, and constitutional integrity."),
        ("RISK-RM-003-013", "Risk Provenance Architecture", "Define complete provenance linking evidence, intermediate evaluations, confidence calculations, mitigation plans, recovery plans, and final Risk Assessments."),
        ("RISK-RM-003-014", "Risk Office State Machine", "Define every constitutional execution state, legal transition, invariant, fail-closed behavior, interruption handling, and completion state."),
        ("RISK-RM-003-015", "Office-Owned Persistent State", "Define every Risk-owned persistent state element, constitutionally transient state element, checkpoint ownership, and durability requirements."),
        ("RISK-RM-003-016", "Risk Validation Framework", "Define deterministic validation governing evidence integrity, confidence calculations, exposure evaluation, mitigation correctness, object consistency, and constitutional integrity."),
        ("RISK-RM-003-017", "Constitutional Commit Boundaries", "Define every atomic constitutional commit boundary, transactional guarantee, persistence obligation, rollback behavior, and associated invariants."),
        ("RISK-RM-003-018", "Replay Semantic Equivalence", "Define replay invariants, semantic equivalence, deterministic reproduction, replay validation, and constitutionally acceptable runtime differences."),
        ("RISK-RM-003-019", "Constitutional Configuration Object", "Define immutable Risk configuration ownership, schema, validation, version governance, compatibility rules, and integrity verification."),
        ("RISK-RM-003-020", "Constitutional Error Taxonomy", "Define deterministic constitutional error classes, failure handling, recovery semantics, escalation behavior, and audit requirements."),
        ("RISK-RM-003-021", "Constitutional Traceability Architecture", "Define complete traceability linking doctrine, implementation, evaluation evidence, testing, certification artifacts, remediation history, and audit results."),
        ("RISK-RM-003-022", "Confidence and Exposure Constitution", "Define immutable confidence objects, exposure models, uncertainty representation, confidence propagation, aggregation rules, and deterministic evaluation."),
        ("RISK-RM-003-023", "Risk Mitigation Constitution", "Define constitutional representation, ownership, evaluation, prioritization, execution readiness, and preservation of mitigation and recovery strategies."),
        ("RISK-RM-003-024", "Risk Fusion Doctrine", "Define deterministic fusion of position, portfolio, liquidity, volatility, tail, systemic, and recovery risk into a single immutable constitutional Enterprise Risk Assessment."),
        ("RISK-RM-003-025", "Independent Risk Office Certification Suite", "Define the complete constitutional certification test suite required to demonstrate deterministic Risk Office behavior prior to independent certification."),
    )
    return tuple(RiskSpecificationWorkOrder(*row) for row in rows)


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
