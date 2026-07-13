"""EO-DA constitutional invariant engine for ARGOS assurance evidence."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Callable

from argos.foundation.contracts import utc_timestamp

from .truth_domain import (
    OperationalTruthEnvelope,
    TruthEnvelopeError,
    require_operational_truth_envelope,
    validate_operational_truth_envelope,
)


EO_DA_VERSION = "EO-DA.1"


class InvariantDomain(str, Enum):
    RUNTIME = "RUNTIME"
    AUTHORITY = "AUTHORITY"
    LAW_VII = "LAW_VII"
    MISSION = "MISSION"
    OFFICE = "OFFICE"
    BROKER = "BROKER"
    POSITION = "POSITION"
    EXIT = "EXIT"
    TRUTH_DOMAIN = "TRUTH_DOMAIN"
    PERFORMANCE_TRUTH = "PERFORMANCE_TRUTH"
    HISTORIAN = "HISTORIAN"
    PERSISTENCE = "PERSISTENCE"
    RECOVERY = "RECOVERY"
    REPLAY = "REPLAY"
    READ_ONLY = "READ_ONLY"
    COMMANDER = "COMMANDER"
    POLICY = "POLICY"
    DOCTRINE = "DOCTRINE"
    COST = "COST"
    API_GATEWAY = "API_GATEWAY"
    COMMUNICATIONS = "COMMUNICATIONS"
    DUPLICATE_AUTHORITY = "DUPLICATE_AUTHORITY"
    ARCHITECTURAL_DRIFT = "ARCHITECTURAL_DRIFT"
    TEST_DEFECT = "TEST_DEFECT"
    ENVIRONMENT = "ENVIRONMENT"
    DOCUMENTATION = "DOCUMENTATION"
    UNKNOWN = "UNKNOWN"


class InvariantSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    ENHANCEMENT = "ENHANCEMENT"


class BlockingLevel(str, Enum):
    NONE = "NONE"
    WORKFLOW = "WORKFLOW"
    OPERATION = "OPERATION"
    PAPER_RUNTIME = "PAPER_RUNTIME"
    CI = "CI"


class EvaluationStage(str, Enum):
    STATIC_REPOSITORY = "STATIC_REPOSITORY"
    STARTUP = "STARTUP"
    TRANSITION_PRECONDITION = "TRANSITION_PRECONDITION"
    TRANSITION_POSTCONDITION = "TRANSITION_POSTCONDITION"
    CONTINUOUS_RUNTIME = "CONTINUOUS_RUNTIME"
    READ_ONLY_INTEGRITY = "READ_ONLY_INTEGRITY"
    RECOVERY = "RECOVERY"
    REPLAY = "REPLAY"
    CI_CERTIFICATION = "CI_CERTIFICATION"


class InvariantResultState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_EVALUATED = "NOT_EVALUATED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class InvariantDefinition:
    invariant_id: str
    name: str
    constitutional_domain: InvariantDomain
    description: str
    rationale: str
    severity: InvariantSeverity
    blocking_level: BlockingLevel
    evaluation_stage: EvaluationStage
    applicable_operating_modes: tuple[str, ...]
    applicable_truth_domains: tuple[str, ...]
    inspected_authorities: tuple[str, ...]
    required_evidence: tuple[str, ...]
    evaluation_function: str
    expected_result: str
    violation_code: str
    remediation_owner: str
    documentation_reference: str
    schema_version: str = EO_DA_VERSION


@dataclass(frozen=True)
class InvariantEvaluationResult:
    evaluation_id: str
    invariant_id: str
    invariant_version: str
    result: InvariantResultState
    severity: InvariantSeverity
    blocking_status: BlockingLevel
    runtime_mode: str
    truth_domain: str
    evaluated_entity: str
    workflow_id: str
    mission_id: str
    token_id: str
    authority: str
    evidence_references: tuple[str, ...]
    observed_values: dict[str, Any]
    expected_values: dict[str, Any]
    violation_code: str
    timestamp_utc: str
    deterministic_sequence: int
    evaluator_version: str
    remediation_recommendation: str


@dataclass(frozen=True)
class ConstitutionalAuthority:
    authority_name: str
    owned_entities: tuple[str, ...]
    permitted_writes: tuple[str, ...]
    prohibited_writes: tuple[str, ...]
    runtime_instance_identity: str
    truth_domains: tuple[str, ...]
    persistence_namespace: str
    associated_invariants: tuple[str, ...]
    source_implementation: str
    construction_site: str
    active_status: str


@dataclass(frozen=True)
class AuthoritativeWriteSite:
    writer: str
    authority: str
    entity: str
    operation: str
    truth_domain: str
    provenance_requirement: str
    token_requirement: str
    idempotency_requirement: str
    persistence_requirement: str
    pre_write_invariants: tuple[str, ...]
    post_write_invariants: tuple[str, ...]
    source_reference: str


@dataclass(frozen=True)
class InvariantViolationRecord:
    violation_id: str
    invariant_id: str
    violation_code: str
    severity: InvariantSeverity
    domain: InvariantDomain
    blocking_status: BlockingLevel
    affected_authority: str
    affected_workflow: str
    affected_truth_domain: str
    evidence: tuple[str, ...]
    remediation_owner: str
    first_observed_utc: str
    last_observed_utc: str
    occurrence_count: int
    current_status: str
    resolution_evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class InvariantSweepResult:
    verdict: str
    engine_version: str
    evaluation_count: int
    pass_count: int
    fail_count: int
    blocking_count: int
    results: tuple[InvariantEvaluationResult, ...]
    violations: tuple[InvariantViolationRecord, ...]
    runtime_overhead_ms: float
    live_trading_enabled: bool
    financial_mutation_authority: bool


def constitutional_invariant_catalog() -> tuple[InvariantDefinition, ...]:
    return (
        _definition("INV-RUNTIME-001", "Single Canonical Runtime", InvariantDomain.RUNTIME, InvariantSeverity.CRITICAL, BlockingLevel.PAPER_RUNTIME, EvaluationStage.STARTUP, "evaluate_runtime_uniqueness", "Exactly one canonical runtime is active and live remains disabled.", "DUPLICATE_OR_LIVE_RUNTIME", "Runtime Provider", "EO-DA_Runtime_and_CI_Enforcement.md", ("Canonical Runtime", "Runtime Provider")),
        _definition("INV-AUTHORITY-001", "Stateful Authority Uniqueness", InvariantDomain.DUPLICATE_AUTHORITY, InvariantSeverity.CRITICAL, BlockingLevel.PAPER_RUNTIME, EvaluationStage.STARTUP, "evaluate_authority_uniqueness", "Stateful authority identities are unique except documented Scheduler/Duty alias.", "DUPLICATE_STATEFUL_AUTHORITY", "Runtime Provider", "EO-DA_Authority_Registry.md", ("Canonical Runtime",)),
        _definition("INV-LAWVII-001", "Workflow Token Exclusivity", InvariantDomain.LAW_VII, InvariantSeverity.CRITICAL, BlockingLevel.WORKFLOW, EvaluationStage.CONTINUOUS_RUNTIME, "evaluate_law_vii", "Every active workflow has one token and one legal owner.", "LAW_VII_TOKEN_VIOLATION", "Workflow Orchestrator", "EO-DA_LAW_VII_Monitoring_Model.md", ("Workflow Orchestrator", "Token authority")),
        _definition("INV-BROKER-001", "Broker Owns Fills", InvariantDomain.BROKER, InvariantSeverity.CRITICAL, BlockingLevel.OPERATION, EvaluationStage.TRANSITION_POSTCONDITION, "evaluate_broker_position_reconciliation", "Fills exist only under Broker orders and rejected orders have no fills.", "BROKER_FILL_AUTHORITY_VIOLATION", "Paper Broker", "EO-DA_Broker_Position_Reconciliation_Invariants.md", ("Paper Broker", "Performance Truth")),
        _definition("INV-POSITION-001", "Positions Require Fills", InvariantDomain.POSITION, InvariantSeverity.CRITICAL, BlockingLevel.OPERATION, EvaluationStage.TRANSITION_POSTCONDITION, "evaluate_broker_position_reconciliation", "Positions must be lineaged to broker fills and closed truth must be unique.", "POSITION_FILL_RECONCILIATION_VIOLATION", "Position Registry", "EO-DA_Broker_Position_Reconciliation_Invariants.md", ("Position Registry", "Performance Truth")),
        _definition("INV-TRUTH-001", "Validated Operational Truth Envelope", InvariantDomain.TRUTH_DOMAIN, InvariantSeverity.CRITICAL, BlockingLevel.OPERATION, EvaluationStage.TRANSITION_PRECONDITION, "evaluate_truth_envelope", "Authoritative paper truth requires validated PAPER operational envelope.", "TRUTH_DOMAIN_GATE_REJECTED", "Truth Domain Gate", "EO-DA_Truth_Domain_Gating_Model.md", ("Performance Truth", "Persistence")),
        _definition("INV-PERSISTENCE-001", "Persistence Provenance Gate", InvariantDomain.PERSISTENCE, InvariantSeverity.CRITICAL, BlockingLevel.OPERATION, EvaluationStage.TRANSITION_PRECONDITION, "evaluate_persistence_envelope", "Authoritative persisted broker, position, and performance truth have provenance/idempotency/schema.", "PERSISTENCE_AUTHORITY_VIOLATION", "Persistence", "EO-DA_Runtime_and_CI_Enforcement.md", ("Persistence",)),
        _definition("INV-READONLY-001", "Read-Only Digest Stability", InvariantDomain.READ_ONLY, InvariantSeverity.CRITICAL, BlockingLevel.PAPER_RUNTIME, EvaluationStage.READ_ONLY_INTEGRITY, "evaluate_read_only_guard", "Read-only operations do not mutate authoritative semantic digest.", "READ_ONLY_MUTATION_DETECTED", "Runtime Provider", "EO-DA_Read_Only_Integrity_Model.md", ("Dashboard", "Commander", "Runtime")),
        _definition("INV-COMMANDER-001", "Commander Observes And Directs", InvariantDomain.COMMANDER, InvariantSeverity.MAJOR, BlockingLevel.OPERATION, EvaluationStage.STATIC_REPOSITORY, "evaluate_static_architecture", "Commander routes must not directly create fills, orders, positions, performance truth, or live mode.", "COMMANDER_AUTHORITY_BYPASS", "Commander", "EO-DA_Runtime_and_CI_Enforcement.md", ("Commander", "Server routes")),
        _definition("INV-ARCH-001", "Production Route Canonical Provider", InvariantDomain.ARCHITECTURAL_DRIFT, InvariantSeverity.MAJOR, BlockingLevel.CI, EvaluationStage.STATIC_REPOSITORY, "evaluate_static_architecture", "Production paper routes delegate to the canonical runtime provider.", "PRODUCTION_ROUTE_BYPASS", "Runtime Provider", "EO-DA_Runtime_and_CI_Enforcement.md", ("Server routes",)),
        _definition("INV-API-001", "External Model Gateway Boundary", InvariantDomain.API_GATEWAY, InvariantSeverity.MAJOR, BlockingLevel.CI, EvaluationStage.STATIC_REPOSITORY, "evaluate_static_architecture", "Runtime model execution routes through API Execution Gateway.", "API_GATEWAY_BYPASS", "API Gateway", "EO-DA_Runtime_and_CI_Enforcement.md", ("API Gateway", "Runtime")),
        _definition("INV-LIVE-001", "Live Trading Disabled", InvariantDomain.RUNTIME, InvariantSeverity.CRITICAL, BlockingLevel.PAPER_RUNTIME, EvaluationStage.STARTUP, "evaluate_runtime_uniqueness", "Live mode remains unreachable and disabled.", "LIVE_TRADING_REACHABLE", "Runtime Provider", "EO-DA_Runtime_and_CI_Enforcement.md", ("Canonical Runtime", "Server routes")),
    )


def constitutional_authority_registry() -> tuple[ConstitutionalAuthority, ...]:
    return (
        _authority("Runtime Provider", ("process runtime singleton",), ("start/halt canonical runtime",), ("orders", "fills", "positions", "performance truth"), "runtime_provider.py", "module singleton"),
        _authority("Canonical Runtime", ("runtime mode", "mission admissions"), ("scheduler coordination", "mission admission"), ("orders", "fills", "position quantity", "performance truth"), "canonical_enterprise_runtime.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("Scheduler", ("scheduled missions",), ("mission scheduling state",), ("broker events", "positions", "truth"), "scheduler.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("Mission Planner", ("mission plans",), ("bounded mission plans",), ("office outputs", "orders", "fills"), "mission_planner.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("Duty Officer", ("office wake eligibility",), ("duty decisions",), ("token transfer", "orders", "fills"), "office_duty_officer.py", "EnterpriseOperationsScheduler.duty_officers"),
        _authority("Workflow Orchestrator", ("workflows", "Workflow Execution Tokens"), ("workflow lifecycle", "token ownership"), ("orders", "fills", "positions"), "workflow_orchestrator.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("Strategic Intelligence", ("strategic mandates",), ("strategic reports",), ("opportunities", "orders", "fills"), "strategic_intelligence_command.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("Seeker", ("opportunity candidates",), ("office output only",), ("risk approval", "orders", "fills"), "seeker package", "office chain"),
        _authority("Analyst", ("analysis products",), ("analysis output",), ("execution approval", "orders", "fills"), "analyst package", "office chain"),
        _authority("Risk", ("risk disposition",), ("risk approval/rejection",), ("broker order construction", "fills"), "risk package", "office chain"),
        _authority("Executive", ("authorization decisions",), ("authorizations",), ("fills", "position quantity"), "executive package", "office chain"),
        _authority("Trader", ("order intent",), ("paper order tickets",), ("broker outcomes", "fills", "position quantity"), "trader/paper_brokerage.py", "office chain"),
        _authority("Paper Broker", ("broker orders", "broker events", "fills", "settlements"), ("broker order book", "broker outcomes"), ("position quantity", "performance truth without envelope", "live execution"), "trader/paper_brokerage.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("Position Registry", ("positions", "position history"), ("position creation/increase/reduction/closure from fills"), ("broker events", "fills"), "position_registry.py", "PerformanceTruthEngine"),
        _authority("EO-CK", ("position monitoring enrollment",), ("monitoring observations",), ("orders", "fills", "position quantity"), "position_monitoring_network.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("Surveillance", ("position surveillance snapshots",), ("read-only observations",), ("orders", "fills", "positions"), "position_surveillance_engine.py", "runtime state"),
        _authority("Exit Decision", ("exit recommendations",), ("recommendations",), ("orders", "fills", "position quantity"), "position_exit_decision_engine.py", "runtime state"),
        _authority("Performance Truth", ("performance ledgers",), ("authoritative facts from broker/position evidence",), ("broker outcomes", "fabricated execution"), "performance_truth_engine.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("Closed Position Truth", ("closed lifecycle truth",), ("closed position records from reconciled evidence",), ("fills", "positions", "degraded authoritative truth"), "closed_position_truth.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("Historian", ("historical preservation",), ("archives and recommendations",), ("financial truth creation", "orders", "fills"), "historian package", "office chain"),
        _authority("Commander", ("directives", "read model"), ("halt", "remediation directive", "mission directive"), ("orders", "fills", "positions", "performance truth", "live enablement"), "executive/control panel", "Commander surfaces"),
        _authority("Doctrine", ("doctrine versions",), ("doctrine records",), ("orders", "fills"), "enterprise_doctrine_policy_manager.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("Policy", ("policy versions",), ("policy decisions",), ("orders", "fills"), "enterprise_doctrine_policy_manager.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("Persistence", ("hash-chain records",), ("durable records and recovery audit"), ("financial fact creation", "repair without evidence"), "enterprise_persistence.py", "DurableEnterprisePersistenceStore"),
        _authority("Replay", ("replay scenarios",), ("isolated replay runs",), ("active paper truth", "active tokens"), "market_replay_engine.py", "runtime state"),
        _authority("Communications Bus", ("messages",), ("delivery/audit/quarantine records",), ("token transfer", "orders", "fills"), "enterprise_communications_bus.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("Cost Governor", ("cost reservations",), ("cost authorization/ledger",), ("orders", "fills", "token transfer"), "enterprise_cost_governor.py", "CanonicalEnterpriseRuntime._build_components"),
        _authority("API Gateway", ("model execution boundary",), ("authorized API execution audit",), ("workflow ownership", "orders", "fills"), "api_execution_gateway.py", "CanonicalEnterpriseRuntime._build_components"),
    )


def authoritative_write_site_registry() -> tuple[AuthoritativeWriteSite, ...]:
    return (
        _write("EnterpriseOperationsScheduler", "Scheduler", "missions", "create/dispatch mission", "PAPER", "mission template", "workflow token after dispatch", "mission_id", "enterprise_mission_state", ("INV-RUNTIME-001",), ("INV-LAWVII-001",), "scheduler.py"),
        _write("EnterpriseMissionPlanner", "Mission Planner", "mission plans", "plan scheduled obligation", "PAPER", "mission evidence", "not required until workflow admission", "mission_plan_id", "enterprise_mission_state", ("INV-RUNTIME-001",), ("INV-LAWVII-001",), "mission_planner.py"),
        _write("EnterpriseWorkflowOrchestrator", "Workflow Orchestrator", "workflows/tokens", "create/transfer/archive workflow", "PAPER", "workflow definition", "required", "workflow_id + token audit id", "enterprise_workflow_state", ("INV-LAWVII-001",), ("INV-LAWVII-001",), "workflow_orchestrator.py"),
        _write("Trader", "Trader", "order intent", "construct order ticket", "PAPER", "certified decision object", "required", "order_id", "broker state after broker accepts", ("INV-TRUTH-001", "INV-LAWVII-001"), ("INV-BROKER-001",), "trader/paper_brokerage.py"),
        _write("DeterministicPaperBrokerage", "Paper Broker", "orders/events/fills", "accept/reject/fill/settle", "PAPER", "broker event provenance", "required", "order_id/fill_id/event_id", "enterprise_broker_state", ("INV-BROKER-001", "INV-TRUTH-001"), ("INV-POSITION-001",), "trader/paper_brokerage.py"),
        _write("PositionRegistry", "Position Registry", "positions/history", "create/increase/reduce/close", "PAPER", "broker fill evidence", "workflow lineage required", "fill_id/position_id", "enterprise_position_state", ("INV-BROKER-001",), ("INV-POSITION-001",), "position_registry.py"),
        _write("PerformanceTruthEngine", "Performance Truth", "performance truth ledgers", "record broker authoritative order", "PAPER", "validated operational truth envelope", "required", "order_id", "enterprise_performance_truth", ("INV-TRUTH-001",), ("INV-POSITION-001",), "performance_truth_engine.py"),
        _write("ClosedPositionTruthBuilder", "Closed Position Truth", "closed position truth", "build closed lifecycle truth", "PAPER", "closed position and complete evidence", "workflow lineage required", "position_id", "enterprise_performance_truth", ("INV-POSITION-001",), ("INV-POSITION-001",), "closed_position_truth.py"),
        _write("DurableEnterprisePersistenceStore", "Persistence", "authoritative persistent records", "persist/commit transaction", "PAPER", "validated operational truth envelope for operational authorities", "contextual", "idempotency_key", "hash-chain backup", ("INV-PERSISTENCE-001",), ("INV-PERSISTENCE-001",), "enterprise_persistence.py"),
        _write("EnterpriseDoctrinePolicyManager", "Doctrine/Policy", "doctrine and policy", "create/distribute/activate", "PAPER", "policy schema and approval", "not financial", "policy_version", "enterprise_policy_state", ("INV-RUNTIME-001",), ("INV-PERSISTENCE-001",), "enterprise_doctrine_policy_manager.py"),
    )


class TruthDomainInvariantGate:
    """Reusable EO-DA truth gate that delegates to Phase III.5 envelopes."""

    def validate(self, envelope: OperationalTruthEnvelope | dict[str, Any] | None, *, target_authority: str, allowed_authorities: set[str] | None = None) -> InvariantEvaluationResult:
        validation = validate_operational_truth_envelope(envelope, target_authority=target_authority, allowed_authorities=allowed_authorities)
        return _result(
            definition=_definition_by_id("INV-TRUTH-001"),
            state=InvariantResultState.PASS if validation.valid else InvariantResultState.FAIL,
            sequence=1,
            runtime_mode="paper",
            truth_domain=str(validation.envelope.get("truth_domain", "")),
            evaluated_entity=str(validation.envelope.get("source_event_id", "")),
            workflow_id=str(validation.envelope.get("originating_workflow_id", "")),
            mission_id=str(validation.envelope.get("mission_id", "")),
            token_id=str(validation.envelope.get("workflow_token_id", "")),
            authority=str(validation.envelope.get("originating_authority", "")),
            evidence=("Phase III.5 OperationalTruthEnvelope",),
            observed={"codes": validation.codes, "envelope": validation.envelope},
            expected={"valid": True, "targetAuthority": target_authority},
        )

    def require(self, envelope: OperationalTruthEnvelope | dict[str, Any] | None, *, target_authority: str, allowed_authorities: set[str] | None = None) -> dict[str, Any]:
        try:
            return require_operational_truth_envelope(envelope, target_authority=target_authority, allowed_authorities=allowed_authorities)
        except TruthEnvelopeError:
            raise


class ReadOnlyIntegrityGuard:
    """Digest read-only operations and report mutation evidence."""

    def evaluate(self, digest_provider: Callable[[], str], read_operation: Callable[[], Any], *, entity: str = "read-only surface") -> tuple[Any, InvariantEvaluationResult]:
        before = digest_provider()
        value = read_operation()
        after = digest_provider()
        definition = _definition_by_id("INV-READONLY-001")
        return value, _result(
            definition=definition,
            state=InvariantResultState.PASS if before == after else InvariantResultState.FAIL,
            sequence=1,
            runtime_mode="paper",
            truth_domain="PAPER",
            evaluated_entity=entity,
            authority="ReadOnlyIntegrityGuard",
            evidence=("semantic digest before/after read",),
            observed={"before": before, "after": after},
            expected={"digestStable": True},
        )


class LawVIIMonitor:
    """Deterministic monitor for Workflow Execution Token invariants."""

    terminal_statuses = {"Completed", "Archived"}

    def evaluate(self, workflow_snapshot: dict[str, Any]) -> InvariantEvaluationResult:
        violations = self.violations(workflow_snapshot)
        definition = _definition_by_id("INV-LAWVII-001")
        return _result(
            definition=definition,
            state=InvariantResultState.PASS if not violations else InvariantResultState.FAIL,
            sequence=1,
            runtime_mode="paper",
            truth_domain="PAPER",
            evaluated_entity="workflow_orchestrator",
            authority="Workflow Orchestrator",
            evidence=("workflow snapshot",),
            observed={"violations": violations, "metrics": workflow_snapshot.get("metrics", {})},
            expected={"oneTokenPerActiveWorkflow": True, "oneOwnerPerToken": True, "terminalHasNoOwner": True},
        )

    def violations(self, workflow_snapshot: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        rows = []
        seen_tokens: set[str] = set()
        seen_workflows: set[str] = set()
        for workflow in workflow_snapshot.get("workflows", ()) or ():
            workflow_id = str(workflow.get("workflow_id", ""))
            token = dict(workflow.get("token", {}) or {})
            token_id = str(token.get("audit_identifier", ""))
            status = str(token.get("workflow_status", ""))
            owner = str(token.get("current_owner", ""))
            next_owner = str(token.get("next_owner", ""))
            stages = tuple(workflow.get("stages", ()) or ())
            if not workflow_id or not token:
                rows.append({"code": "MISSING_WORKFLOW_TOKEN", "workflowId": workflow_id})
            if token.get("workflow_id") != workflow_id:
                rows.append({"code": "TOKEN_WORKFLOW_MISMATCH", "workflowId": workflow_id, "tokenWorkflowId": token.get("workflow_id", "")})
            if workflow_id in seen_workflows:
                rows.append({"code": "DUPLICATE_WORKFLOW_ID", "workflowId": workflow_id})
            seen_workflows.add(workflow_id)
            if token_id in seen_tokens:
                rows.append({"code": "DUPLICATE_TOKEN_ID", "workflowId": workflow_id, "tokenId": token_id})
            if token_id:
                seen_tokens.add(token_id)
            if status not in self.terminal_statuses and not (owner or next_owner):
                rows.append({"code": "ACTIVE_TOKEN_WITHOUT_OWNER", "workflowId": workflow_id, "tokenId": token_id})
            if owner and stages and owner not in stages:
                rows.append({"code": "OWNER_NOT_IN_WORKFLOW_STAGES", "workflowId": workflow_id, "owner": owner})
            if status in self.terminal_statuses and owner:
                rows.append({"code": "TERMINAL_TOKEN_HAS_OWNER", "workflowId": workflow_id, "owner": owner})
            active_offices = tuple(name for name, state in dict(workflow.get("office_states", {}) or {}).items() if state != "Dormant")
            if owner and active_offices and active_offices != (owner,):
                rows.append({"code": "OFFICE_STATE_OWNER_MISMATCH", "workflowId": workflow_id, "owner": owner, "activeOffices": active_offices})
        return tuple(rows)


class BrokerPositionInvariantMonitor:
    """Verify broker/fill/position/closed-truth consistency without repair."""

    def evaluate(self, performance_truth: dict[str, Any]) -> tuple[InvariantEvaluationResult, InvariantEvaluationResult]:
        violations = self.violations(performance_truth)
        broker_violations = tuple(item for item in violations if item["domain"] == "BROKER")
        position_violations = tuple(item for item in violations if item["domain"] == "POSITION")
        return (
            _result(_definition_by_id("INV-BROKER-001"), InvariantResultState.PASS if not broker_violations else InvariantResultState.FAIL, 1, "paper", "PAPER", "broker/order/fill ledgers", "Paper Broker", ("performance truth order ledger",), {"violations": broker_violations}, {"fillsHaveBrokerOrders": True}),
            _result(_definition_by_id("INV-POSITION-001"), InvariantResultState.PASS if not position_violations else InvariantResultState.FAIL, 2, "paper", "PAPER", "position registry", "Position Registry", ("performance truth position registry",), {"violations": position_violations}, {"positionsHaveFills": True, "closedTruthUnique": True}),
        )

    def violations(self, performance_truth: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        violations: list[dict[str, Any]] = []
        orders = tuple(dict(item) for item in performance_truth.get("orderLedger", ()) or ())
        filled_orders = {str(order.get("order_id", "")): order for order in orders if float(order.get("filled_quantity", 0.0) or 0.0) > 0}
        for order in orders:
            if str(order.get("status", "")).upper() in {"REJECTED", "CANCELLED", "EXPIRED"} and float(order.get("filled_quantity", 0.0) or 0.0) > 0:
                violations.append({"domain": "BROKER", "code": "TERMINAL_NON_EXECUTED_ORDER_HAS_FILL", "orderId": order.get("order_id", "")})
            if float(order.get("filled_quantity", 0.0) or 0.0) > 0 and not str(order.get("order_id", "")):
                violations.append({"domain": "BROKER", "code": "FILL_WITHOUT_ORDER_ID"})
        registry = dict(performance_truth.get("positionRegistry", {}) or {})
        for position in registry.get("allPositions", ()) or ():
            position_id = str(position.get("position_id", ""))
            fill_ids = tuple(position.get("fill_ids", ()) or ())
            broker_order_ids = tuple(position.get("broker_order_ids", ()) or ())
            if float(position.get("quantity", 0.0) or 0.0) != 0.0 and not (fill_ids or broker_order_ids):
                violations.append({"domain": "POSITION", "code": "OPEN_POSITION_WITHOUT_FILL_LINEAGE", "positionId": position_id})
            missing_orders = tuple(order_id for order_id in broker_order_ids if order_id not in filled_orders)
            if missing_orders:
                violations.append({"domain": "POSITION", "code": "POSITION_REFERENCES_UNFILLED_ORDER", "positionId": position_id, "orderIds": missing_orders})
        closed = tuple(dict(item) for item in performance_truth.get("closedPositionTruth", ()) or ())
        counts: dict[str, int] = {}
        for record in closed:
            counts[str(record.get("position_id", ""))] = counts.get(str(record.get("position_id", "")), 0) + 1
        for position_id, count in counts.items():
            if count > 1:
                violations.append({"domain": "POSITION", "code": "DUPLICATE_CLOSED_POSITION_TRUTH", "positionId": position_id, "count": count})
        return tuple(violations)


class ConstitutionalInvariantEngine:
    """Canonical EO-DA engine: observes, evaluates, blocks by result, never mutates financial truth."""

    def __init__(self, repository_root: str | Path | None = None) -> None:
        self.repository_root = Path(repository_root) if repository_root else Path.cwd()
        self.definitions = constitutional_invariant_catalog()
        self.authorities = constitutional_authority_registry()
        self.write_sites = authoritative_write_site_registry()
        self.truth_gate = TruthDomainInvariantGate()
        self.read_only_guard = ReadOnlyIntegrityGuard()
        self.law_vii_monitor = LawVIIMonitor()
        self.broker_position_monitor = BrokerPositionInvariantMonitor()
        self._violations: dict[str, InvariantViolationRecord] = {}

    def evaluate_startup(self, runtime: Any) -> InvariantSweepResult:
        started = time.perf_counter()
        results = (
            self.evaluate_runtime_uniqueness(runtime, sequence=1),
            self.evaluate_authority_uniqueness(runtime, sequence=2),
            self.law_vii_monitor.evaluate(runtime.components.workflow_orchestrator.snapshot()),
        )
        return self._sweep(results, started, live_trading_enabled=bool(getattr(runtime, "live_trading_enabled", False)))

    def evaluate_continuous(self, runtime: Any) -> InvariantSweepResult:
        started = time.perf_counter()
        truth = runtime.components.performance_truth.snapshot(execution_environment="paper")
        broker_result, position_result = self.broker_position_monitor.evaluate(truth)
        results = (
            self.evaluate_runtime_uniqueness(runtime, sequence=1),
            self.evaluate_authority_uniqueness(runtime, sequence=2),
            self.law_vii_monitor.evaluate(runtime.components.workflow_orchestrator.snapshot()),
            broker_result,
            position_result,
        )
        return self._sweep(results, started, live_trading_enabled=bool(getattr(runtime, "live_trading_enabled", False)))

    def evaluate_static_architecture(self) -> InvariantSweepResult:
        started = time.perf_counter()
        source_findings = _static_source_findings(self.repository_root)
        commander = tuple(item for item in source_findings if item["code"] == "COMMANDER_AUTHORITY_BYPASS")
        route = tuple(item for item in source_findings if item["code"] == "PRODUCTION_ROUTE_BYPASS")
        api = tuple(item for item in source_findings if item["code"] == "API_GATEWAY_BYPASS")
        results = (
            _result(_definition_by_id("INV-COMMANDER-001"), InvariantResultState.PASS if not commander else InvariantResultState.FAIL, 1, "static", "PAPER", "server/commander routes", "Commander", ("AST/static source scan",), {"findings": commander}, {"noCommanderFinancialMutation": True}),
            _result(_definition_by_id("INV-ARCH-001"), InvariantResultState.PASS if not route else InvariantResultState.FAIL, 2, "static", "PAPER", "server routes", "Runtime Provider", ("AST/static source scan",), {"findings": route}, {"productionPaperRoutesUseProvider": True}),
            _result(_definition_by_id("INV-API-001"), InvariantResultState.PASS if not api else InvariantResultState.FAIL, 3, "static", "PAPER", "model API calls", "API Gateway", ("AST/static source scan",), {"findings": api}, {"externalCallsUseGateway": True}),
        )
        return self._sweep(results, started, live_trading_enabled=False)

    def evaluate_runtime_uniqueness(self, runtime: Any, *, sequence: int = 1) -> InvariantEvaluationResult:
        status = runtime.runtime_status() if hasattr(runtime, "runtime_status") else {}
        live = bool(status.get("liveTradingEnabled", getattr(runtime, "live_trading_enabled", False)))
        loop_started = bool(status.get("loopStarted", False))
        start_count = int(status.get("startCount", 0) or 0)
        bad = live or start_count > 1 and loop_started
        return _result(_definition_by_id("INV-RUNTIME-001"), InvariantResultState.FAIL if bad else InvariantResultState.PASS, sequence, str(status.get("mode", "")), "PAPER", "CanonicalEnterpriseRuntime", "Canonical Runtime", ("runtime_status",), {"liveTradingEnabled": live, "loopStarted": loop_started, "startCount": start_count}, {"liveTradingEnabled": False, "duplicateLoop": False})

    def evaluate_authority_uniqueness(self, runtime: Any, *, sequence: int = 1) -> InvariantEvaluationResult:
        duplicates = tuple(runtime.stateful_authority_duplicates()) if hasattr(runtime, "stateful_authority_duplicates") else ()
        diagnostics = tuple(asdict(item) for item in runtime.stateful_authority_diagnostics()) if hasattr(runtime, "stateful_authority_diagnostics") else ()
        return _result(_definition_by_id("INV-AUTHORITY-001"), InvariantResultState.PASS if not duplicates else InvariantResultState.FAIL, sequence, str(getattr(getattr(runtime, "mode", ""), "value", "")), "PAPER", "stateful authorities", "Canonical Runtime", ("stateful_authority_diagnostics",), {"duplicates": duplicates, "diagnostics": diagnostics}, {"duplicates": ()})

    def guard_truth_write(self, envelope: OperationalTruthEnvelope | dict[str, Any] | None, *, target_authority: str, allowed_authorities: set[str] | None = None) -> InvariantEvaluationResult:
        return self.truth_gate.validate(envelope, target_authority=target_authority, allowed_authorities=allowed_authorities)

    def guard_read_only(self, digest_provider: Callable[[], str], read_operation: Callable[[], Any], *, entity: str = "read-only surface") -> tuple[Any, InvariantEvaluationResult]:
        return self.read_only_guard.evaluate(digest_provider, read_operation, entity=entity)

    def commander_health_read_model(self, sweep: InvariantSweepResult) -> dict[str, Any]:
        return {
            "engineName": "Constitutional Invariant Engine",
            "engineeringOrder": "EO-DA",
            "verdict": sweep.verdict,
            "blockingViolations": tuple(asdict(item) for item in sweep.violations if item.blocking_status != BlockingLevel.NONE),
            "failedInvariants": tuple(asdict(item) for item in sweep.results if item.result == InvariantResultState.FAIL),
            "authorityRegistryCount": len(self.authorities),
            "writeSiteRegistryCount": len(self.write_sites),
            "lastSweep": {
                "evaluationCount": sweep.evaluation_count,
                "passCount": sweep.pass_count,
                "failCount": sweep.fail_count,
                "blockingCount": sweep.blocking_count,
                "runtimeOverheadMs": sweep.runtime_overhead_ms,
            },
            "commanderLimitations": {
                "mayMarkCriticalPassed": False,
                "mayEraseViolation": False,
                "mayCreateOrder": False,
                "mayCreateFill": False,
                "mayMutatePosition": False,
                "mayEnableLiveTrading": False,
            },
            "financialMutationAuthority": False,
        }

    def _sweep(self, results: tuple[InvariantEvaluationResult, ...], started: float, *, live_trading_enabled: bool) -> InvariantSweepResult:
        violations = tuple(self._record_violation(result) for result in results if result.result == InvariantResultState.FAIL)
        blocking = tuple(result for result in results if result.result == InvariantResultState.FAIL and result.blocking_status != BlockingLevel.NONE)
        verdict = "FAIL" if any(result.severity == InvariantSeverity.CRITICAL for result in blocking) else "CONDITIONAL PASS" if blocking else "PASS"
        return InvariantSweepResult(
            verdict=verdict,
            engine_version=EO_DA_VERSION,
            evaluation_count=len(results),
            pass_count=sum(1 for item in results if item.result == InvariantResultState.PASS),
            fail_count=sum(1 for item in results if item.result == InvariantResultState.FAIL),
            blocking_count=len(blocking),
            results=results,
            violations=violations,
            runtime_overhead_ms=round((time.perf_counter() - started) * 1000, 4),
            live_trading_enabled=live_trading_enabled,
            financial_mutation_authority=False,
        )

    def _record_violation(self, result: InvariantEvaluationResult) -> InvariantViolationRecord:
        definition = _definition_by_id(result.invariant_id)
        signature = _stable_hash({"invariant": result.invariant_id, "entity": result.evaluated_entity, "observed": result.observed_values, "code": result.violation_code})
        existing = self._violations.get(signature)
        now = utc_timestamp()
        if existing:
            updated = InvariantViolationRecord(**{**asdict(existing), "last_observed_utc": now, "occurrence_count": existing.occurrence_count + 1})
            self._violations[signature] = updated
            return updated
        record = InvariantViolationRecord(
            violation_id=f"EO-DA-VIOL-{len(self._violations) + 1:06d}",
            invariant_id=result.invariant_id,
            violation_code=result.violation_code,
            severity=result.severity,
            domain=definition.constitutional_domain,
            blocking_status=result.blocking_status,
            affected_authority=result.authority,
            affected_workflow=result.workflow_id,
            affected_truth_domain=result.truth_domain,
            evidence=result.evidence_references,
            remediation_owner=definition.remediation_owner,
            first_observed_utc=now,
            last_observed_utc=now,
            occurrence_count=1,
            current_status="detected",
        )
        self._violations[signature] = record
        return record


def _definition(invariant_id: str, name: str, domain: InvariantDomain, severity: InvariantSeverity, blocking: BlockingLevel, stage: EvaluationStage, function: str, description: str, violation: str, owner: str, doc: str, authorities: tuple[str, ...]) -> InvariantDefinition:
    return InvariantDefinition(invariant_id, name, domain, description, "Executable constitutional protection for ARGOS authority and truth boundaries.", severity, blocking, stage, ("paper", "startup", "ci"), ("PAPER",), authorities, ("runtime snapshot", "source scan", "registry declarations"), function, "PASS", violation, owner, doc)


def _authority(name: str, owned: tuple[str, ...], permitted: tuple[str, ...], prohibited: tuple[str, ...], implementation: str, construction: str) -> ConstitutionalAuthority:
    return ConstitutionalAuthority(name, owned, permitted, prohibited, "runtime-bound", ("PAPER",), name.lower().replace(" ", "_"), tuple(item.invariant_id for item in constitutional_invariant_catalog() if name in item.inspected_authorities), implementation, construction, "active_or_registered")


def _write(writer: str, authority: str, entity: str, operation: str, truth_domain: str, provenance: str, token: str, idempotency: str, persistence: str, pre: tuple[str, ...], post: tuple[str, ...], source: str) -> AuthoritativeWriteSite:
    return AuthoritativeWriteSite(writer, authority, entity, operation, truth_domain, provenance, token, idempotency, persistence, pre, post, source)


def _definition_by_id(invariant_id: str) -> InvariantDefinition:
    return next(item for item in constitutional_invariant_catalog() if item.invariant_id == invariant_id)


def _result(
    definition: InvariantDefinition,
    state: InvariantResultState,
    sequence: int,
    runtime_mode: str,
    truth_domain: str,
    evaluated_entity: str,
    authority: str,
    evidence: tuple[str, ...],
    observed: dict[str, Any],
    expected: dict[str, Any],
    workflow_id: str = "",
    mission_id: str = "",
    token_id: str = "",
) -> InvariantEvaluationResult:
    payload = {"invariant": definition.invariant_id, "sequence": sequence, "entity": evaluated_entity, "observed": observed}
    return InvariantEvaluationResult(
        evaluation_id=f"EO-DA-EVAL-{hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode('utf-8')).hexdigest()[:12].upper()}",
        invariant_id=definition.invariant_id,
        invariant_version=definition.schema_version,
        result=state,
        severity=definition.severity,
        blocking_status=definition.blocking_level if state == InvariantResultState.FAIL else BlockingLevel.NONE,
        runtime_mode=runtime_mode,
        truth_domain=truth_domain,
        evaluated_entity=evaluated_entity,
        workflow_id=workflow_id,
        mission_id=mission_id,
        token_id=token_id,
        authority=authority,
        evidence_references=evidence,
        observed_values=observed,
        expected_values=expected,
        violation_code=definition.violation_code if state == InvariantResultState.FAIL else "",
        timestamp_utc=utc_timestamp(),
        deterministic_sequence=sequence,
        evaluator_version=EO_DA_VERSION,
        remediation_recommendation=f"Assigned to {definition.remediation_owner}: {definition.description}",
    )


def _static_source_findings(repository_root: Path) -> tuple[dict[str, Any], ...]:
    findings: list[dict[str, Any]] = []
    server_path = repository_root / "src" / "argos" / "control_panel" / "server.py"
    if server_path.exists():
        text = server_path.read_text(encoding="utf-8", errors="ignore")
        if "/api/paper/start" in text and "get_server_runtime_provider()" not in text:
            findings.append({"code": "PRODUCTION_ROUTE_BYPASS", "file": str(server_path), "symbol": "/api/paper/start"})
        tree = ast.parse(text)
        prohibited = {"BrokerFillRecord", "PaperBrokerOrderRecord", "PositionObject", "PerformanceTruthEngine", "DeterministicPaperBrokerage"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = _call_name(node.func)
                if name in prohibited:
                    findings.append({"code": "COMMANDER_AUTHORITY_BYPASS", "file": str(server_path), "symbol": name})
    runtime_path = repository_root / "src" / "argos" / "control_panel" / "canonical_enterprise_runtime.py"
    if runtime_path.exists():
        text = runtime_path.read_text(encoding="utf-8", errors="ignore")
        if "ApiExecutionGateway" not in text:
            findings.append({"code": "API_GATEWAY_BYPASS", "file": str(runtime_path), "symbol": "ApiExecutionGateway"})
        if "live_trading_enabled: bool = False" not in text:
            findings.append({"code": "LIVE_TRADING_REACHABLE", "file": str(runtime_path), "symbol": "live_trading_enabled"})
    return tuple(findings)


def _call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _stable_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()

