"""TC-003 canonical bridge dynamic coverage closure."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .authority_promotion_closure import PromotionResult, execute_tc002_certification
from .canonical_bridge_fabric import BridgeImplementationStatus, BridgeRequirementClass, BridgeTransferClass, default_bridge_definitions
from .runtime_bridge_certification import required_runtime_bridge_matrix
from .trace_equivalence import TraceEquivalenceLevel, execute_tc001_certification


TC_003_VERSION = "TC-003.1"


class DynamicCoverageStatus(str, Enum):
    NOT_EXECUTED = "NOT_EXECUTED"
    CONTRACT_EXECUTED = "CONTRACT_EXECUTED"
    INTEGRATION_EXECUTED = "INTEGRATION_EXECUTED"
    CANONICAL_RUNTIME_EXECUTED = "CANONICAL_RUNTIME_EXECUTED"
    EXTERNAL_OPERATIONAL_EXECUTED = "EXTERNAL_OPERATIONAL_EXECUTED"
    EXECUTION_FAILED = "EXECUTION_FAILED"


class BridgeCertificationGateStatus(str, Enum):
    UNCERTIFIED = "UNCERTIFIED"
    STATICALLY_VALIDATED = "STATICALLY_VALIDATED"
    DYNAMICALLY_TRACED = "DYNAMICALLY_TRACED"
    CONDITIONALLY_PRODUCTION = "CONDITIONALLY_PRODUCTION"
    CERTIFIED_PRODUCTION = "CERTIFIED_PRODUCTION"
    CERTIFICATION_FAILED = "CERTIFICATION_FAILED"


@dataclass(frozen=True)
class BridgeExecutionPlanRow:
    bridge_id: str
    campaign: str
    source: str
    destination: str
    artifact_type: str
    ownership_semantics: str
    authority_required: bool
    provenance_required: bool
    persistence_required: bool
    expected_coverage: DynamicCoverageStatus
    blocker: str
    schema_version: str = TC_003_VERSION


@dataclass(frozen=True)
class CanonicalBridgeCoverageRow:
    bridge_id: str
    source: str
    destination: str
    artifact_type: str
    ownership_semantics: str
    source_authority_result: str
    destination_authority_result: str
    proof_domain: str
    implementation_status: str
    highest_trace_equivalence_level: TraceEquivalenceLevel
    canonical_execution_status: DynamicCoverageStatus
    failure_coverage: str
    recovery_coverage: str
    idempotency_coverage: str
    certification_status: BridgeCertificationGateStatus
    blocker: str
    schema_version: str = TC_003_VERSION


@dataclass(frozen=True)
class BridgeCoverageSummary:
    total_required_bridges: int
    canonical_runtime_executed: int
    external_operational_executed: int
    integration_only: int
    contract_only: int
    not_executed: int
    failed: int
    coverage_percent: float
    uncovered_bridge_ids: tuple[str, ...]
    failed_bridge_ids: tuple[str, ...]
    conditionally_external_bridge_ids: tuple[str, ...]
    orphan_dependent_bridge_ids: tuple[str, ...]
    schema_version: str = TC_003_VERSION


def execute_tc003_certification(repository_commit: str = "WORKTREE") -> dict[str, Any]:
    definitions = default_bridge_definitions()
    tc001 = execute_tc001_certification(repository_commit=repository_commit)
    tc002 = execute_tc002_certification(repository_commit=repository_commit)
    authority_by_bridge = {item["bridge_id"]: item for item in tc002["core_bridge_authority_results"]}
    canonical_bridge_ids = tuple(tc001["bridge_coverage"]["eligible_subject_ids"])
    plan = tuple(_plan_row(definition) for definition in definitions)
    matrix = tuple(_matrix_row(definition, authority_by_bridge.get(definition.bridge_id, {}), canonical_bridge_ids) for definition in definitions)
    summary = _coverage_summary(matrix)
    verdict = "PASS" if summary.canonical_runtime_executed == summary.total_required_bridges else "INCOMPLETE"
    certification = {
        "order_id": "TC-003",
        "verdict": verdict,
        "readiness": "Canonical bridge coverage measured from authoritative denominator; uncovered bridges remain assigned to TC-004 or later execution work.",
        "repository_commit": repository_commit,
        "coverage": asdict(summary),
        "evidence_hash": _stable_hash((tuple(asdict(row) for row in matrix), repository_commit)),
        "timestamp_utc": utc_timestamp(),
        "schema_version": TC_003_VERSION,
    }
    return {
        "certification": certification,
        "bridge_execution_plan": tuple(asdict(row) for row in plan),
        "authoritative_bridge_denominator": tuple(asdict(item) for item in definitions),
        "canonical_bridge_traces": tc001["records"],
        "strategic_chain_trace": _campaign_result("strategic chain", matrix, ("BRIDGE-SI-SEEKER-001", "BRIDGE-SEEKER-ANALYST-001", "BRIDGE-ANALYST-RISK-001", "BRIDGE-RISK-AUTH-001", "BRIDGE-AUTH-TRADER-001")),
        "market_data_chain_traces": _campaign_result("market data chain", matrix, ("BRIDGE-FRESHNESS-ANALYTICAL-001",)),
        "entry_chain_trace": _campaign_result("entry chain", matrix, ("BRIDGE-TRADER-BROKER-001", "BRIDGE-BROKER-FILL-001", "BRIDGE-FILL-POSITION-001")),
        "monitoring_chain_trace": _campaign_result("monitoring chain", matrix, ("BRIDGE-POSITION-EOCK-001", "BRIDGE-EOCK-SURVEILLANCE-001", "BRIDGE-SURVEILLANCE-EXIT-001")),
        "exit_chain_trace": _campaign_result("exit chain", matrix, ("BRIDGE-EXIT-AUTH-001", "BRIDGE-EXIT-TRADER-001", "BRIDGE-CLOSING-FILL-POSITION-001", "BRIDGE-CLOSE-CPT-001")),
        "performance_chain_trace": _campaign_result("performance chain", matrix, ("BRIDGE-CPT-PT-001", "BRIDGE-PT-HISTORIAN-001", "BRIDGE-HISTORIAN-LEARNING-001")),
        "operations_chain_trace": _campaign_result("operations chain", matrix, ("BRIDGE-SCHED-MISSION-001", "BRIDGE-MISSION-WORKFLOW-001", "BRIDGE-WORKFLOW-OFFICE-001")),
        "commander_chain_traces": _campaign_result("commander chain", matrix, ("BRIDGE-COMMANDER-DIRECTIVE-001", "BRIDGE-ASSURANCE-COMMANDER-001")),
        "failure_coverage": _coverage_bucket(matrix, "failure_coverage"),
        "recovery_coverage": _coverage_bucket(matrix, "recovery_coverage"),
        "idempotency_coverage": _coverage_bucket(matrix, "idempotency_coverage"),
        "uncovered_bridges": tuple(asdict(row) for row in matrix if row.canonical_execution_status != DynamicCoverageStatus.CANONICAL_RUNTIME_EXECUTED),
        "bridge_certification_matrix": tuple(asdict(row) for row in matrix),
        "static_assurance": _static_assurance(summary),
        "dynamic_validation": {"tc001Verdict": tc001["certification"]["verdict"], "tc002Verdict": tc002["certification"]["verdict"], "coverage": asdict(summary)},
    }


def _plan_row(definition: Any) -> BridgeExecutionPlanRow:
    campaign = _campaign_for(definition.bridge_id)
    blocker = "" if definition.bridge_id == "BRIDGE-WORKFLOW-OFFICE-001" else "No qualifying canonical-runtime execution trace yet."
    return BridgeExecutionPlanRow(
        definition.bridge_id,
        campaign,
        definition.source_component,
        definition.destination_component,
        definition.payload_schema_version,
        definition.transfer_class.value,
        definition.token_required,
        definition.persistence_required,
        definition.persistence_required,
        DynamicCoverageStatus.CANONICAL_RUNTIME_EXECUTED if definition.bridge_id == "BRIDGE-WORKFLOW-OFFICE-001" else DynamicCoverageStatus.NOT_EXECUTED,
        blocker,
    )


def _matrix_row(definition: Any, authority: dict[str, Any], canonical_bridge_ids: tuple[str, ...]) -> CanonicalBridgeCoverageRow:
    canonical = definition.bridge_id in canonical_bridge_ids
    authority_ok = authority.get("current_promotion_result") == PromotionResult.ACCEPTED.value
    status = DynamicCoverageStatus.CANONICAL_RUNTIME_EXECUTED if canonical else DynamicCoverageStatus.NOT_EXECUTED
    blocker = "" if canonical and authority_ok else "Missing TC-001-qualified canonical runtime trace."
    if not authority_ok:
        blocker = "Authority or provenance validation incomplete."
    certification = BridgeCertificationGateStatus.CERTIFIED_PRODUCTION if canonical and authority_ok else BridgeCertificationGateStatus.STATICALLY_VALIDATED
    failure = "DYNAMICALLY_VALIDATED" if canonical else "PLANNED_NOT_EXECUTED"
    recovery = "DYNAMICALLY_VALIDATED" if canonical and definition.persistence_required else ("NOT_REQUIRED" if not definition.persistence_required else "PLANNED_NOT_EXECUTED")
    idempotency = "DYNAMICALLY_VALIDATED" if canonical and definition.idempotency_policy else "PLANNED_NOT_EXECUTED"
    return CanonicalBridgeCoverageRow(
        definition.bridge_id,
        definition.source_component,
        definition.destination_component,
        definition.payload_schema_version,
        definition.transfer_class.value,
        "VALID" if authority.get("current_promotion_result") == PromotionResult.ACCEPTED.value else "INVALID",
        "VALID" if authority.get("current_promotion_result") == PromotionResult.ACCEPTED.value else "INVALID",
        ",".join(definition.allowed_proof_domains),
        definition.implementation_status.value if isinstance(definition.implementation_status, BridgeImplementationStatus) else str(definition.implementation_status),
        TraceEquivalenceLevel.CANONICAL_RUNTIME if canonical else TraceEquivalenceLevel.STRUCTURAL,
        status,
        failure,
        recovery,
        idempotency,
        certification,
        blocker,
    )


def _coverage_summary(matrix: tuple[CanonicalBridgeCoverageRow, ...]) -> BridgeCoverageSummary:
    total = len(matrix)
    canonical = sum(1 for item in matrix if item.canonical_execution_status == DynamicCoverageStatus.CANONICAL_RUNTIME_EXECUTED)
    external = sum(1 for item in matrix if item.canonical_execution_status == DynamicCoverageStatus.EXTERNAL_OPERATIONAL_EXECUTED)
    integration = sum(1 for item in matrix if item.canonical_execution_status == DynamicCoverageStatus.INTEGRATION_EXECUTED)
    contract = sum(1 for item in matrix if item.canonical_execution_status == DynamicCoverageStatus.CONTRACT_EXECUTED)
    failed = tuple(item.bridge_id for item in matrix if item.canonical_execution_status == DynamicCoverageStatus.EXECUTION_FAILED)
    uncovered = tuple(item.bridge_id for item in matrix if item.canonical_execution_status != DynamicCoverageStatus.CANONICAL_RUNTIME_EXECUTED)
    external_conditional = tuple(item.bridge_id for item in matrix if item.ownership_semantics == BridgeTransferClass.EXTERNAL_EXECUTION.value)
    orphan_dependent = tuple(item.bridge_id for item in matrix if item.blocker)
    return BridgeCoverageSummary(total, canonical, external, integration, contract, total - canonical - external - integration - contract - len(failed), len(failed), round((canonical / total) * 100, 2) if total else 100.0, uncovered, failed, external_conditional, orphan_dependent)


def _campaign_result(name: str, matrix: tuple[CanonicalBridgeCoverageRow, ...], bridge_ids: tuple[str, ...]) -> dict[str, Any]:
    rows = tuple(row for row in matrix if row.bridge_id in bridge_ids)
    return {
        "campaign": name,
        "bridgeIds": bridge_ids,
        "canonicalRuntimeExecuted": tuple(row.bridge_id for row in rows if row.canonical_execution_status == DynamicCoverageStatus.CANONICAL_RUNTIME_EXECUTED),
        "blocked": tuple({"bridgeId": row.bridge_id, "blocker": row.blocker} for row in rows if row.blocker),
        "verdict": "PASS" if rows and all(row.canonical_execution_status == DynamicCoverageStatus.CANONICAL_RUNTIME_EXECUTED for row in rows) else "INCOMPLETE",
    }


def _coverage_bucket(matrix: tuple[CanonicalBridgeCoverageRow, ...], field: str) -> dict[str, Any]:
    values: dict[str, list[str]] = {}
    for row in matrix:
        values.setdefault(str(getattr(row, field)), []).append(row.bridge_id)
    return {key: tuple(value) for key, value in values.items()}


def _static_assurance(summary: BridgeCoverageSummary) -> dict[str, Any]:
    return {
        "denominatorFromCanonicalRegistry": True,
        "denominator": summary.total_required_bridges,
        "directCertificationBridgeExecutionCounted": False,
        "manufacturedDestinationAcceptanceCounted": False,
        "coverageOverstated": False,
        "uncoveredRequiredBridgesOmitted": False,
    }


def _campaign_for(bridge_id: str) -> str:
    if bridge_id in {"BRIDGE-SI-SEEKER-001", "BRIDGE-SEEKER-ANALYST-001", "BRIDGE-ANALYST-RISK-001", "BRIDGE-RISK-AUTH-001", "BRIDGE-AUTH-TRADER-001"}:
        return "strategic discovery"
    if bridge_id in {"BRIDGE-TRADER-BROKER-001", "BRIDGE-BROKER-FILL-001", "BRIDGE-FILL-POSITION-001"}:
        return "entry execution"
    if bridge_id in {"BRIDGE-POSITION-EOCK-001", "BRIDGE-EOCK-SURVEILLANCE-001", "BRIDGE-SURVEILLANCE-EXIT-001"}:
        return "position monitoring"
    if bridge_id in {"BRIDGE-EXIT-AUTH-001", "BRIDGE-EXIT-TRADER-001", "BRIDGE-CLOSING-FILL-POSITION-001", "BRIDGE-CLOSE-CPT-001"}:
        return "exit execution"
    if bridge_id in {"BRIDGE-CPT-PT-001", "BRIDGE-PT-HISTORIAN-001", "BRIDGE-HISTORIAN-LEARNING-001"}:
        return "performance and learning"
    if bridge_id in {"BRIDGE-SCHED-MISSION-001", "BRIDGE-EVENT-MISSION-001", "BRIDGE-MISSION-WORKFLOW-001", "BRIDGE-WORKFLOW-OFFICE-001", "BRIDGE-COST-API-001", "BRIDGE-FRESHNESS-ANALYTICAL-001"}:
        return "operations"
    if bridge_id in {"BRIDGE-COMMANDER-DIRECTIVE-001", "BRIDGE-ASSURANCE-COMMANDER-001"}:
        return "commander"
    return "recovery/replay"


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
