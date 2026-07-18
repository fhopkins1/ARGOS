"""EO-DG read-only integrity guard.

EO-DG verifies that observation surfaces stay observational. It owns assurance
evidence only; it does not own, repair, or mutate protected enterprise state.
"""

from __future__ import annotations

import ast
import asyncio
from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import inspect
import json
from pathlib import Path
from typing import Any, AsyncIterable, Callable, Iterable

from argos.foundation.contracts import utc_timestamp

from .constitutional_invariants import ConstitutionalInvariantEngine, InvariantResultState


EO_DG_VERSION = "EO-DG.1"


class ReadSurfaceType(str, Enum):
    PURE_SNAPSHOT = "PURE_SNAPSHOT"
    DERIVED_PROJECTION = "DERIVED_PROJECTION"
    CACHED_READ = "CACHED_READ"
    HISTORICAL_QUERY = "HISTORICAL_QUERY"
    REPLAY_VIEW = "REPLAY_VIEW"
    DECISION_LAB_VIEW = "DECISION_LAB_VIEW"
    HEALTH_CHECK = "HEALTH_CHECK"
    STATUS_CHECK = "STATUS_CHECK"
    STREAMING_OR_POLLING_READ = "STREAMING_OR_POLLING_READ"
    ADMINISTRATIVE_INSPECTION = "ADMINISTRATIVE_INSPECTION"
    MUTATING_COMMAND_FALSELY_EXPOSED_AS_READ = "MUTATING_COMMAND_FALSELY_EXPOSED_AS_READ"


class ReadConsistencyLevel(str, Enum):
    STRONG_SNAPSHOT = "STRONG_SNAPSHOT"
    AUTHORITY_CONSISTENT = "AUTHORITY_CONSISTENT"
    EVENTUAL_READ_MODEL = "EVENTUAL_READ_MODEL"
    TELEMETRY_ONLY = "TELEMETRY_ONLY"


class ReadCertificationStatus(str, Enum):
    CERTIFIED_READ_ONLY = "CERTIFIED_READ_ONLY"
    CONDITIONALLY_READ_ONLY = "CONDITIONALLY_READ_ONLY"
    NOT_CERTIFIED = "NOT_CERTIFIED"
    MUTATING_COMMAND = "MUTATING_COMMAND"
    PROOF_ONLY = "PROOF_ONLY"
    SIMULATION_ONLY = "SIMULATION_ONLY"
    TEST_ONLY = "TEST_ONLY"
    DEPRECATED = "DEPRECATED"
    QUARANTINED = "QUARANTINED"


class ReadIntegrityStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ReadIntegritySeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    ENHANCEMENT = "ENHANCEMENT"


class ReadFindingClass(str, Enum):
    READ_SURFACE = "READ_SURFACE"
    GET_ROUTE = "GET_ROUTE"
    COMMANDER = "COMMANDER"
    DASHBOARD = "DASHBOARD"
    RUNTIME_SNAPSHOT = "RUNTIME_SNAPSHOT"
    BROKER_READ = "BROKER_READ"
    POSITION_READ = "POSITION_READ"
    EOCK_READ = "EOCK_READ"
    PERFORMANCE_TRUTH_READ = "PERFORMANCE_TRUTH_READ"
    CLOSED_POSITION_TRUTH_READ = "CLOSED_POSITION_TRUTH_READ"
    HISTORIAN_READ = "HISTORIAN_READ"
    REPLAY_READ = "REPLAY_READ"
    DECISION_LAB_READ = "DECISION_LAB_READ"
    TRANSACTION_READ = "TRANSACTION_READ"
    PROMOTION_READ = "PROMOTION_READ"
    PERSISTENCE_READ = "PERSISTENCE_READ"
    RECOVERY_READ = "RECOVERY_READ"
    POLICY_READ = "POLICY_READ"
    DOCTRINE_READ = "DOCTRINE_READ"
    API_CALL = "API_CALL"
    COST_MUTATION = "COST_MUTATION"
    OFFICE_WAKE = "OFFICE_WAKE"
    MISSION_MUTATION = "MISSION_MUTATION"
    WORKFLOW_MUTATION = "WORKFLOW_MUTATION"
    TOKEN_MUTATION = "TOKEN_MUTATION"
    TRUTH_MUTATION = "TRUTH_MUTATION"
    CACHE = "CACHE"
    CONCURRENCY = "CONCURRENCY"
    CONSISTENCY = "CONSISTENCY"
    ARCHITECTURAL_BYPASS = "ARCHITECTURAL_BYPASS"
    SECURITY_BOUNDARY = "SECURITY_BOUNDARY"
    ENVIRONMENT = "ENVIRONMENT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DigestProfile:
    profile_id: str
    protected_authorities: tuple[str, ...]
    included_fields: tuple[str, ...]
    excluded_fields: tuple[str, ...]
    canonical_ordering: str
    normalization_rules: tuple[str, ...]
    timestamp_handling: str
    floating_point_handling: str
    hash_algorithm: str
    schema_version: str = EO_DG_VERSION


@dataclass(frozen=True)
class ReadSurfaceDefinition:
    surface_id: str
    name: str
    route_or_callable: str
    file: str
    symbol: str
    surface_type: ReadSurfaceType
    owning_presentation_layer: str
    permitted_truth_domains: tuple[str, ...]
    permitted_operating_modes: tuple[str, ...]
    required_authorities_read: tuple[str, ...]
    expected_output_schema: str
    protected_state_domains: tuple[str, ...]
    permitted_ephemeral_side_effects: tuple[str, ...]
    prohibited_effects: tuple[str, ...]
    digest_profile: str
    consistency_level: ReadConsistencyLevel
    expected_latency_ms: int
    caching_rules: str
    error_behavior: str
    test_coverage: tuple[str, ...]
    certification_status: ReadCertificationStatus
    schema_version: str = EO_DG_VERSION


@dataclass(frozen=True)
class ProtectedStateDomain:
    domain_id: str
    name: str
    authorities: tuple[str, ...]
    protected_fields: tuple[str, ...]
    prohibited_read_mutations: tuple[str, ...]
    digest_profile: str


@dataclass(frozen=True)
class ReadCounterSnapshot:
    api_calls: int = 0
    cost_total_units: float = 0.0
    office_wake_count: int = 0
    token_transfer_count: int = 0
    broker_event_count: int = 0
    persistence_sequence: int = 0
    transaction_journal_size: int = 0
    truth_record_count: int = 0
    historian_record_count: int = 0


@dataclass(frozen=True)
class ReadIntegrityResult:
    evaluation_id: str
    surface_id: str
    surface_version: str
    invocation_id: str
    runtime_mode: str
    truth_domain: str
    pre_read_digests: dict[str, str]
    post_read_digests: dict[str, str]
    changed_domains: tuple[str, ...]
    changed_entities: tuple[str, ...]
    pre_counters: dict[str, Any]
    post_counters: dict[str, Any]
    permitted_ephemeral_differences: tuple[str, ...]
    prohibited_differences: tuple[str, ...]
    result: ReadIntegrityStatus
    severity: ReadIntegritySeverity
    blocking_status: str
    evidence_paths: tuple[str, ...]
    timestamp_utc: str
    deterministic_sequence: int
    evaluator_version: str
    remediation_owner: str
    eoda_invariant_status: str


@dataclass(frozen=True)
class ReadEvidenceRecord:
    result: ReadIntegrityResult
    response_digest: str
    evidence_hash: str
    stored_separately_from_financial_truth: bool = True


@dataclass(frozen=True)
class RouteAuditFinding:
    route: str
    method: str
    finding_class: ReadFindingClass
    severity: ReadIntegritySeverity
    reason: str
    blocks_ci: bool


@dataclass(frozen=True)
class StaticReadArchitectureReport:
    scanned_file: str
    get_routes: tuple[str, ...]
    command_routes: tuple[str, ...]
    findings: tuple[RouteAuditFinding, ...]
    unregistered_get_routes: tuple[str, ...]
    verdict: str


def semantic_digest_profiles() -> tuple[DigestProfile, ...]:
    return (
        _profile("DIGEST-RUNTIME", ("Canonical Runtime", "Runtime Provider"), ("runtime", "scheduler", "missions", "workflows", "tokens"), ("lastAccessed", "requestCount", "readLatencyMs", "timestamp", "timestampUtc"), "sort keys", ("enum values", "stable tuple ordering"), "ignore ephemeral timestamps", "round floats to 8dp"),
        _profile("DIGEST-LAWVII", ("Workflow Orchestrator",), ("workflows", "tokens", "owners", "transferSequence"), ("lastViewedAt", "uiExpanded"), "sort by workflow/token id", ("owner normalized",), "preserve workflow event timestamps", "round floats to 8dp"),
        _profile("DIGEST-BROKER", ("Paper Broker",), ("orders", "events", "fills", "cash", "buyingPower", "settlements"), ("lastQuoteViewedAt", "dashboardHits"), "sort by order/fill/event id", ("numbers normalized",), "preserve broker event timestamps", "round floats to 8dp"),
        _profile("DIGEST-POSITION", ("Position Registry", "EO-CK"), ("positions", "history", "enrollments", "surveillance", "exits"), ("expandedRows", "viewFilters"), "sort by position id", ("numbers normalized",), "preserve position event timestamps", "round floats to 8dp"),
        _profile("DIGEST-TRUTH", ("Performance Truth", "Closed Position Truth", "Truth Promotion Authority"), ("performanceTruth", "closedPositionTruth", "promotionDecisions", "truthEnvelopes"), ("renderedAt", "viewCount"), "sort by truth id", ("domain normalized",), "preserve observation timestamps", "round floats to 8dp"),
        _profile("DIGEST-HISTORIAN", ("Historian",), ("records", "archives", "lessons"), ("lastAccessed",), "sort by record id", ("version normalized",), "preserve historical timestamps", "round floats to 8dp"),
        _profile("DIGEST-TRANSACTION", ("Transaction Coordinator",), ("intents", "participants", "acknowledgments", "journal", "outbox", "reconciliation"), ("readCursor", "lastViewedAt"), "sort by transaction/journal sequence", ("enum values",), "preserve journal timestamps", "round floats to 8dp"),
        _profile("DIGEST-GOVERNANCE", ("Policy", "Doctrine", "Commander"), ("policy", "doctrine", "directives", "authorizations"), ("selectedTab", "expandedPanels"), "sort by version/directive id", ("version normalized",), "preserve approval timestamps", "round floats to 8dp"),
        _profile("DIGEST-COST", ("Cost Governor", "API Gateway"), ("costLedger", "reservations", "apiUsage", "budget"), ("dashboardHits", "latencyMs"), "sort by ledger sequence", ("numbers normalized",), "preserve cost event timestamps", "round floats to 8dp"),
        _profile("DIGEST-ALL-AUTHORITATIVE", ("all",), ("all protected domains",), ("lastAccessed", "requestCount", "readLatencyMs", "timestamp", "timestampUtc", "traceId", "spanId"), "sort all dictionary keys and ids", ("drop ephemeral metadata", "normalize tuples/lists", "round floats"), "ignore ephemeral read timestamps", "round floats to 8dp"),
    )


def protected_state_registry() -> tuple[ProtectedStateDomain, ...]:
    return (
        _domain("STATE-RUNTIME", "Runtime and orchestration", ("Canonical Runtime", "Scheduler", "Mission Planner", "Workflow Orchestrator"), ("runtimeMode", "startupState", "haltState", "missions", "workflows", "tokens", "officeWakeState"), ("create mission", "advance workflow", "transfer token", "wake office"), "DIGEST-RUNTIME"),
        _domain("STATE-TRADING", "Trading", ("Trader", "Paper Broker"), ("orderIntents", "brokerOrders", "brokerEvents", "fills", "cash", "buyingPower", "settlements"), ("submit order", "process broker event", "create fill", "cancel order"), "DIGEST-BROKER"),
        _domain("STATE-POSITIONS", "Positions", ("Position Registry", "EO-CK", "Exit Decision"), ("positions", "quantity", "averageCost", "realizedPnl", "history", "enrollment", "surveillance", "exitState"), ("mutate position", "append history", "enroll EO-CK", "close position"), "DIGEST-POSITION"),
        _domain("STATE-TRUTH", "Truth and history", ("Performance Truth", "Closed Position Truth", "Truth Promotion Authority", "Historian"), ("performanceTruth", "closedPositionTruth", "historianRecords", "promotionDecisions", "truthEnvelopes"), ("ingest truth", "build closed truth", "append historian", "approve promotion"), "DIGEST-TRUTH"),
        _domain("STATE-TRANSACTIONS", "Transactions", ("Transaction Coordinator",), ("intents", "participantStates", "acknowledgments", "journal", "outbox", "reconciliation"), ("create intent", "acknowledge participant", "reconcile", "commit transaction", "deliver outbox"), "DIGEST-TRANSACTION"),
        _domain("STATE-GOVERNANCE", "Governance", ("Policy", "Doctrine", "Commander"), ("policyVersions", "doctrineVersions", "authorizations", "directives"), ("approve policy", "activate doctrine", "acknowledge alert", "create directive"), "DIGEST-GOVERNANCE"),
        _domain("STATE-PERSISTENCE", "Persistence and recovery", ("Persistence", "Recovery", "Replay"), ("persistenceSequence", "schemaVersions", "checkpoints", "recoveryCursor", "replayCursor"), ("persist authoritative record", "create checkpoint", "advance recovery", "advance replay"), "DIGEST-RUNTIME"),
        _domain("STATE-COST", "Cost and APIs", ("Cost Governor", "API Gateway"), ("costTotals", "reservations", "apiUsage", "retryCounts"), ("charge cost", "reserve budget", "invoke API", "increment authoritative retries"), "DIGEST-COST"),
        _domain("STATE-ASSURANCE", "Assurance", ("EO-DA", "EO-DE", "EO-DF"), ("violations", "faultCampaigns", "enduranceCampaigns"), ("rerun campaign", "close finding", "change verdict"), "DIGEST-ALL-AUTHORITATIVE"),
    )


def read_surface_registry() -> tuple[ReadSurfaceDefinition, ...]:
    return (
        _surface("READ-RUNTIME-SNAPSHOT-001", "Runtime state", "/api/state", "src/argos/control_panel/runtime.py", "ControlPanelRuntime.state", ReadSurfaceType.PURE_SNAPSHOT, "Dashboard", ("PAPER",), ("paper", "proof"), ("Canonical Runtime", "Scheduler", "Workflow Orchestrator"), "runtime state json", ("STATE-RUNTIME", "STATE-TRADING", "STATE-POSITIONS", "STATE-TRUTH"), "DIGEST-ALL-AUTHORITATIVE", ReadConsistencyLevel.AUTHORITY_CONSISTENT, ReadCertificationStatus.CONDITIONALLY_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
        _surface("READ-COMMANDER-001", "Commander strategic dashboard", "/api/commander/strategic-dashboard", "src/argos/control_panel/runtime.py", "commander_strategic_dashboard_state", ReadSurfaceType.DERIVED_PROJECTION, "Commander", ("PAPER",), ("paper",), ("Commander", "Performance Truth", "Policy"), "commander dashboard json", ("STATE-GOVERNANCE", "STATE-TRUTH"), "DIGEST-ALL-AUTHORITATIVE", ReadConsistencyLevel.EVENTUAL_READ_MODEL, ReadCertificationStatus.CONDITIONALLY_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
        _surface("READ-DASHBOARD-001", "Dashboard state", "/api/state", "src/argos/control_panel/server.py", "do_GET /api/state", ReadSurfaceType.STREAMING_OR_POLLING_READ, "Dashboard", ("PAPER",), ("paper", "proof"), ("all read models",), "dashboard json", ("STATE-RUNTIME", "STATE-TRADING", "STATE-POSITIONS", "STATE-TRUTH", "STATE-COST"), "DIGEST-ALL-AUTHORITATIVE", ReadConsistencyLevel.AUTHORITY_CONSISTENT, ReadCertificationStatus.CONDITIONALLY_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
        _surface("READ-API-STATUS-001", "Runtime provider status", "/api/runtime/provider", "src/argos/control_panel/server.py", "provider.status", ReadSurfaceType.STATUS_CHECK, "API", ("PAPER",), ("paper", "stopped"), ("Runtime Provider",), "provider status json", ("STATE-RUNTIME",), "DIGEST-RUNTIME", ReadConsistencyLevel.STRONG_SNAPSHOT, ReadCertificationStatus.CERTIFIED_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
        _surface("READ-BROKER-SUMMARY-001", "Trader bridge broker summary", "/api/trader/bridge", "src/argos/control_panel/runtime.py", "trader_bridge_state", ReadSurfaceType.DERIVED_PROJECTION, "Dashboard", ("PAPER",), ("paper",), ("Paper Broker", "Position Registry"), "trader bridge json", ("STATE-TRADING", "STATE-POSITIONS"), "DIGEST-ALL-AUTHORITATIVE", ReadConsistencyLevel.AUTHORITY_CONSISTENT, ReadCertificationStatus.CONDITIONALLY_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
        _surface("READ-POSITION-SUMMARY-001", "Position monitoring summary", "/api/position-monitoring/state", "src/argos/control_panel/runtime.py", "position_monitoring_state", ReadSurfaceType.DERIVED_PROJECTION, "Dashboard", ("PAPER",), ("paper",), ("Position Registry", "EO-CK"), "position monitoring json", ("STATE-POSITIONS",), "DIGEST-POSITION", ReadConsistencyLevel.EVENTUAL_READ_MODEL, ReadCertificationStatus.CONDITIONALLY_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
        _surface("READ-PERFORMANCE-TRUTH-001", "Performance Truth state", "/api/performance-truth/state", "src/argos/control_panel/runtime.py", "performance_truth_state", ReadSurfaceType.PURE_SNAPSHOT, "Dashboard", ("PAPER",), ("paper",), ("Performance Truth",), "performance truth json", ("STATE-TRUTH",), "DIGEST-TRUTH", ReadConsistencyLevel.AUTHORITY_CONSISTENT, ReadCertificationStatus.CONDITIONALLY_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
        _surface("READ-REPLAY-VIEW-001", "Market replay view", "/api/market-replay/state", "src/argos/control_panel/runtime.py", "market_replay_state", ReadSurfaceType.REPLAY_VIEW, "Dashboard", ("REPLAY", "PAPER"), ("replay", "paper"), ("Replay",), "replay state json", ("STATE-PERSISTENCE", "STATE-TRADING", "STATE-TRUTH"), "DIGEST-ALL-AUTHORITATIVE", ReadConsistencyLevel.EVENTUAL_READ_MODEL, ReadCertificationStatus.CONDITIONALLY_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
        _surface("READ-DECISION-LAB-001", "Decision Laboratory view", "/api/decision-laboratory/state", "src/argos/control_panel/runtime.py", "decision_laboratory_state", ReadSurfaceType.DECISION_LAB_VIEW, "Dashboard", ("SIMULATION", "PAPER"), ("simulation", "paper"), ("Decision Laboratory",), "decision laboratory json", ("STATE-PERSISTENCE", "STATE-TRUTH"), "DIGEST-ALL-AUTHORITATIVE", ReadConsistencyLevel.EVENTUAL_READ_MODEL, ReadCertificationStatus.CONDITIONALLY_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
        _surface("READ-EO-DD-001", "Transaction coordinator read model", "callable", "src/argos/control_panel/transaction_reconciliation.py", "commander_read_model", ReadSurfaceType.ADMINISTRATIVE_INSPECTION, "Commander", ("PAPER",), ("paper",), ("Transaction Coordinator",), "transaction read model json", ("STATE-TRANSACTIONS",), "DIGEST-TRANSACTION", ReadConsistencyLevel.STRONG_SNAPSHOT, ReadCertificationStatus.CERTIFIED_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
        _surface("READ-EO-DC-001", "Truth promotion read model", "callable", "src/argos/control_panel/truth_promotion.py", "commander_read_model", ReadSurfaceType.ADMINISTRATIVE_INSPECTION, "Commander", ("PAPER",), ("paper",), ("Truth Promotion Authority",), "promotion read model json", ("STATE-TRUTH",), "DIGEST-TRUTH", ReadConsistencyLevel.STRONG_SNAPSHOT, ReadCertificationStatus.CERTIFIED_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
        _surface("READ-EO-DE-001", "Fault campaign read model", "callable", "src/argos/control_panel/fault_injection_lab.py", "commander_read_model", ReadSurfaceType.ADMINISTRATIVE_INSPECTION, "Commander", ("TEST", "PAPER"), ("test", "paper"), ("EO-DE",), "fault campaign json", ("STATE-ASSURANCE",), "DIGEST-ALL-AUTHORITATIVE", ReadConsistencyLevel.TELEMETRY_ONLY, ReadCertificationStatus.CERTIFIED_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
        _surface("READ-EO-DF-001", "Endurance campaign read model", "callable", "src/argos/control_panel/long_duration_operations_lab.py", "commander_read_model", ReadSurfaceType.ADMINISTRATIVE_INSPECTION, "Commander", ("TEST", "PAPER"), ("test", "paper"), ("EO-DF",), "endurance campaign json", ("STATE-ASSURANCE",), "DIGEST-ALL-AUTHORITATIVE", ReadConsistencyLevel.TELEMETRY_ONLY, ReadCertificationStatus.CERTIFIED_READ_ONLY, ("Tests.test_eodg_read_only_integrity",)),
    )


class ReadSurfaceRegistry:
    def __init__(self, surfaces: tuple[ReadSurfaceDefinition, ...] | None = None) -> None:
        self._surfaces: dict[str, ReadSurfaceDefinition] = {}
        for surface in surfaces or read_surface_registry():
            self.register(surface)

    def register(self, surface: ReadSurfaceDefinition) -> None:
        if surface.surface_id in self._surfaces:
            raise ValueError(f"duplicate read surface id: {surface.surface_id}")
        if not surface.consistency_level:
            raise ValueError("consistency level required")
        if not surface.prohibited_effects:
            raise ValueError("prohibited effects required")
        self._surfaces[surface.surface_id] = surface

    def get(self, surface_id: str) -> ReadSurfaceDefinition:
        if surface_id not in self._surfaces:
            raise KeyError(f"unregistered read surface: {surface_id}")
        return self._surfaces[surface_id]

    def all(self) -> tuple[ReadSurfaceDefinition, ...]:
        return tuple(self._surfaces.values())

    def routes(self) -> set[str]:
        return {surface.route_or_callable for surface in self._surfaces.values() if surface.route_or_callable.startswith("/")}


class SemanticDigestEngine:
    def __init__(self, profiles: tuple[DigestProfile, ...] | None = None) -> None:
        self.profiles = {profile.profile_id: profile for profile in profiles or semantic_digest_profiles()}

    def digest(self, state: Any, profile_id: str = "DIGEST-ALL-AUTHORITATIVE") -> str:
        profile = self.profiles[profile_id]
        payload = {"schemaVersion": profile.schema_version, "profileId": profile.profile_id, "state": _normalize(_project_state_for_profile(state, profile.profile_id), set(profile.excluded_fields))}
        return _stable_hash(payload)

    def multi_digest(self, state: dict[str, Any], profile_ids: tuple[str, ...]) -> dict[str, str]:
        return {profile_id: self.digest(state, profile_id) for profile_id in profile_ids}


class ReadIntegrityEvidenceStore:
    def __init__(self) -> None:
        self.records: list[ReadEvidenceRecord] = []

    def append(self, result: ReadIntegrityResult, response: Any) -> ReadEvidenceRecord:
        response_digest = _stable_hash(_normalize(response, set()))
        evidence_hash = _stable_hash({"result": asdict(result), "responseDigest": response_digest})
        record = ReadEvidenceRecord(result=result, response_digest=response_digest, evidence_hash=evidence_hash)
        self.records.append(record)
        return record

    def snapshot(self) -> dict[str, Any]:
        return {"recordCount": len(self.records), "records": tuple(asdict(record) for record in self.records)}


class ReadOnlyIntegrityGuard:
    financial_mutation_authority = False
    live_trading_enabled = False

    def __init__(self, registry: ReadSurfaceRegistry | None = None, digest_engine: SemanticDigestEngine | None = None, evidence_store: ReadIntegrityEvidenceStore | None = None) -> None:
        self.registry = registry or ReadSurfaceRegistry()
        self.digest_engine = digest_engine or SemanticDigestEngine()
        self.evidence_store = evidence_store or ReadIntegrityEvidenceStore()
        self._sequence = 0
        self._eoda = ConstitutionalInvariantEngine()
        self._quarantined: set[str] = set()

    def guard_read(
        self,
        surface_id: str,
        read_operation: Callable[[], Any],
        state_provider: Callable[[], dict[str, Any]],
        *,
        counters_provider: Callable[[], ReadCounterSnapshot] | None = None,
        invocation_id: str = "",
        runtime_mode: str = "paper",
        truth_domain: str = "PAPER",
    ) -> tuple[Any, ReadIntegrityResult]:
        surface = self.registry.get(surface_id)
        self._validate_surface(surface, runtime_mode=runtime_mode, truth_domain=truth_domain)
        before_state = state_provider()
        before_counters = counters_provider() if counters_provider else ReadCounterSnapshot()
        pre = self._digests(before_state, surface)
        response = read_operation()
        after_state = state_provider()
        after_counters = counters_provider() if counters_provider else ReadCounterSnapshot()
        post = self._digests(after_state, surface)
        result = self._result(surface, invocation_id, runtime_mode, truth_domain, pre, post, before_counters, after_counters, response)
        self.evidence_store.append(result, response)
        if result.result == ReadIntegrityStatus.FAIL and result.severity == ReadIntegritySeverity.CRITICAL:
            self._quarantined.add(surface_id)
        return response, result

    async def guard_async_read(
        self,
        surface_id: str,
        read_operation: Callable[[], Any],
        state_provider: Callable[[], dict[str, Any]],
        *,
        counters_provider: Callable[[], ReadCounterSnapshot] | None = None,
        invocation_id: str = "",
        runtime_mode: str = "paper",
        truth_domain: str = "PAPER",
    ) -> tuple[Any, ReadIntegrityResult]:
        surface = self.registry.get(surface_id)
        self._validate_surface(surface, runtime_mode=runtime_mode, truth_domain=truth_domain)
        before_state = state_provider()
        before_counters = counters_provider() if counters_provider else ReadCounterSnapshot()
        pre = self._digests(before_state, surface)
        response = read_operation()
        if inspect.isawaitable(response):
            response = await response
        after_state = state_provider()
        after_counters = counters_provider() if counters_provider else ReadCounterSnapshot()
        result = self._result(surface, invocation_id, runtime_mode, truth_domain, pre, self._digests(after_state, surface), before_counters, after_counters, response)
        self.evidence_store.append(result, response)
        if result.result == ReadIntegrityStatus.FAIL and result.severity == ReadIntegritySeverity.CRITICAL:
            self._quarantined.add(surface_id)
        return response, result

    def guard_streaming_read(
        self,
        surface_id: str,
        stream: Callable[[], Iterable[Any]],
        state_provider: Callable[[], dict[str, Any]],
        *,
        counters_provider: Callable[[], ReadCounterSnapshot] | None = None,
        invocation_id: str = "",
        max_items: int = 1000,
    ) -> tuple[tuple[Any, ...], ReadIntegrityResult]:
        return self.guard_read(
            surface_id,
            lambda: tuple(item for index, item in enumerate(stream()) if index < max_items),
            state_provider,
            counters_provider=counters_provider,
            invocation_id=invocation_id,
        )

    def guard_polling_read(
        self,
        surface_id: str,
        read_operation: Callable[[], Any],
        state_provider: Callable[[], dict[str, Any]],
        *,
        repetitions: int = 1000,
        counters_provider: Callable[[], ReadCounterSnapshot] | None = None,
    ) -> tuple[tuple[Any, ...], ReadIntegrityResult]:
        return self.guard_read(
            surface_id,
            lambda: tuple(read_operation() for _ in range(repetitions)),
            state_provider,
            counters_provider=counters_provider,
            invocation_id=f"poll-{repetitions}",
        )

    def audit_server_routes(self, server_path: str | Path) -> StaticReadArchitectureReport:
        path = Path(server_path)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        get_routes = tuple(_routes_in_method(tree, "do_GET"))
        command_routes = tuple(_routes_in_method(tree, "do_POST"))
        registered = self.registry.routes()
        unregistered = tuple(route for route in get_routes if route.startswith("/api/") and route not in registered)
        findings: list[RouteAuditFinding] = []
        mutating_terms = ("start", "halt", "submit", "transfer", "recover", "replay/start", "activate", "approve", "cancel", "deposit", "configure", "execute", "acknowledge")
        for route in get_routes:
            if any(term in route for term in mutating_terms):
                findings.append(RouteAuditFinding(route, "GET", ReadFindingClass.GET_ROUTE, ReadIntegritySeverity.CRITICAL, "GET route name indicates command/mutation behavior", True))
        for route in unregistered:
            findings.append(RouteAuditFinding(route, "GET", ReadFindingClass.READ_SURFACE, ReadIntegritySeverity.MAJOR, "production GET read surface is not registered", True))
        return StaticReadArchitectureReport(str(path), get_routes, command_routes, tuple(findings), unregistered, "FAIL" if findings else "PASS")

    def commander_read_model(self) -> dict[str, Any]:
        return {
            "engineName": "Read-Only Integrity Guard",
            "engineeringOrder": "EO-DG",
            "engineVersion": EO_DG_VERSION,
            "registeredSurfaceCount": len(self.registry.all()),
            "certifiedReadOnlySurfaces": tuple(surface.surface_id for surface in self.registry.all() if surface.certification_status == ReadCertificationStatus.CERTIFIED_READ_ONLY),
            "conditionallyReadOnlySurfaces": tuple(surface.surface_id for surface in self.registry.all() if surface.certification_status == ReadCertificationStatus.CONDITIONALLY_READ_ONLY),
            "quarantinedSurfaces": tuple(sorted(self._quarantined)),
            "protectedStateDomains": tuple(asdict(domain) for domain in protected_state_registry()),
            "digestProfiles": tuple(asdict(profile) for profile in semantic_digest_profiles()),
            "lastEvaluations": tuple(asdict(record.result) for record in self.evidence_store.records[-20:]),
            "commanderControls": {
                "mayViewSurfaces": True,
                "mayRequestRetest": True,
                "mayRequestInvestigation": True,
                "mayDisableUnsafeView": True,
                "mayCreateRemediationDirective": True,
                "mayMarkFailedSurfaceCertified": False,
                "mayEditDigestResults": False,
                "mayEraseEvidence": False,
                "mayWhitelistCriticalFinancialMutation": False,
                "mayEnableLiveTrading": False,
            },
            "financialMutationAuthority": self.financial_mutation_authority,
            "liveTradingEnabled": self.live_trading_enabled,
            "certifiesContinuousPaperTrading": False,
        }

    def _validate_surface(self, surface: ReadSurfaceDefinition, *, runtime_mode: str, truth_domain: str) -> None:
        if surface.surface_type == ReadSurfaceType.MUTATING_COMMAND_FALSELY_EXPOSED_AS_READ:
            raise ValueError("mutating command cannot be guarded as read")
        if truth_domain not in surface.permitted_truth_domains:
            raise ValueError("truth domain not permitted for read surface")
        if runtime_mode not in surface.permitted_operating_modes:
            raise ValueError("runtime mode not permitted for read surface")
        if self.live_trading_enabled:
            raise ValueError("live trading must remain disabled")

    def _digests(self, state: dict[str, Any], surface: ReadSurfaceDefinition) -> dict[str, str]:
        profiles = tuple(dict.fromkeys((surface.digest_profile, "DIGEST-ALL-AUTHORITATIVE")))
        return self.digest_engine.multi_digest(state, profiles)

    def _result(
        self,
        surface: ReadSurfaceDefinition,
        invocation_id: str,
        runtime_mode: str,
        truth_domain: str,
        pre: dict[str, str],
        post: dict[str, str],
        before_counters: ReadCounterSnapshot,
        after_counters: ReadCounterSnapshot,
        response: Any,
    ) -> ReadIntegrityResult:
        self._sequence += 1
        changed = tuple(key for key in sorted(pre) if pre[key] != post.get(key))
        counter_changes = _counter_changes(before_counters, after_counters)
        prohibited = tuple(changed) + tuple(counter_changes)
        status = ReadIntegrityStatus.PASS if not prohibited else ReadIntegrityStatus.FAIL
        severity = ReadIntegritySeverity.CRITICAL if prohibited else ReadIntegritySeverity.ENHANCEMENT
        invariant = self._eoda.read_only_guard.evaluate(lambda: pre.get(surface.digest_profile, ""), lambda: response, entity=surface.surface_id)[1]
        if prohibited:
            invariant = replace(invariant, result=InvariantResultState.FAIL)
        return ReadIntegrityResult(
            evaluation_id=f"EO-DG-EVAL-{self._sequence:06d}",
            surface_id=surface.surface_id,
            surface_version=surface.schema_version,
            invocation_id=invocation_id or f"EO-DG-INV-{self._sequence:06d}",
            runtime_mode=runtime_mode,
            truth_domain=truth_domain,
            pre_read_digests=pre,
            post_read_digests=post,
            changed_domains=changed,
            changed_entities=changed,
            pre_counters=asdict(before_counters),
            post_counters=asdict(after_counters),
            permitted_ephemeral_differences=surface.permitted_ephemeral_side_effects,
            prohibited_differences=prohibited,
            result=status,
            severity=severity,
            blocking_status="PAPER_RUNTIME" if status == ReadIntegrityStatus.FAIL else "NONE",
            evidence_paths=(f"read-integrity://{surface.surface_id}/{self._sequence:06d}",),
            timestamp_utc=utc_timestamp(),
            deterministic_sequence=self._sequence,
            evaluator_version=EO_DG_VERSION,
            remediation_owner="Runtime Provider" if status == ReadIntegrityStatus.FAIL else "",
            eoda_invariant_status=invariant.result.value if hasattr(invariant.result, "value") else str(invariant.result),
        )


def _profile(profile_id: str, authorities: tuple[str, ...], included: tuple[str, ...], excluded: tuple[str, ...], ordering: str, rules: tuple[str, ...], timestamps: str, floats: str) -> DigestProfile:
    return DigestProfile(profile_id, authorities, included, excluded, ordering, rules, timestamps, floats, "SHA-256")


def _domain(domain_id: str, name: str, authorities: tuple[str, ...], fields: tuple[str, ...], mutations: tuple[str, ...], digest: str) -> ProtectedStateDomain:
    return ProtectedStateDomain(domain_id, name, authorities, fields, mutations, digest)


def _surface(
    surface_id: str,
    name: str,
    route: str,
    file: str,
    symbol: str,
    surface_type: ReadSurfaceType,
    layer: str,
    domains: tuple[str, ...],
    modes: tuple[str, ...],
    authorities: tuple[str, ...],
    schema: str,
    protected: tuple[str, ...],
    digest: str,
    consistency: ReadConsistencyLevel,
    certification: ReadCertificationStatus,
    tests: tuple[str, ...],
) -> ReadSurfaceDefinition:
    return ReadSurfaceDefinition(
        surface_id=surface_id,
        name=name,
        route_or_callable=route,
        file=file,
        symbol=symbol,
        surface_type=surface_type,
        owning_presentation_layer=layer,
        permitted_truth_domains=domains,
        permitted_operating_modes=modes,
        required_authorities_read=authorities,
        expected_output_schema=schema,
        protected_state_domains=protected,
        permitted_ephemeral_side_effects=("cache hit counter", "read latency statistic", "local serialization buffer", "trace span"),
        prohibited_effects=("financial truth mutation", "workflow/token mutation", "office wake", "external API call", "authoritative cost change", "truth promotion", "transaction advancement"),
        digest_profile=digest,
        consistency_level=consistency,
        expected_latency_ms=100,
        caching_rules="ephemeral metadata only; no authoritative cache mutation",
        error_behavior="fail closed and preserve evidence",
        test_coverage=tests,
        certification_status=certification,
    )


def _normalize(value: Any, excluded_fields: set[str]) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return _normalize(asdict(value), excluded_fields)
    if isinstance(value, dict):
        normalized = {}
        for key, item in value.items():
            key_str = str(key)
            if key_str in excluded_fields or key_str in {"lastAccessed", "last_accessed", "requestCount", "request_count", "readLatencyMs", "read_latency_ms", "traceId", "spanId"}:
                continue
            normalized[key_str] = _normalize(item, excluded_fields)
        return {key: normalized[key] for key in sorted(normalized)}
    if isinstance(value, (list, tuple, set)):
        items = [_normalize(item, excluded_fields) for item in value]
        return tuple(sorted(items, key=lambda item: json.dumps(item, sort_keys=True, default=str)))
    if isinstance(value, float):
        return round(value, 8)
    return value


def _project_state_for_profile(state: Any, profile_id: str) -> Any:
    if not isinstance(state, dict) or profile_id == "DIGEST-ALL-AUTHORITATIVE":
        return state
    keys_by_profile = {
        "DIGEST-RUNTIME": ("runtime", "scheduler", "missions", "workflows", "tokens", "offices"),
        "DIGEST-LAWVII": ("workflows", "tokens"),
        "DIGEST-BROKER": ("broker", "orders", "fills", "cash", "buyingPower"),
        "DIGEST-POSITION": ("positions", "eock", "surveillance", "exits"),
        "DIGEST-TRUTH": ("truth", "performanceTruth", "closedPositionTruth", "promotionDecisions"),
        "DIGEST-HISTORIAN": ("historian", "history", "archives"),
        "DIGEST-TRANSACTION": ("transactions", "journal", "outbox", "reconciliation"),
        "DIGEST-GOVERNANCE": ("governance", "policy", "doctrine", "commander"),
        "DIGEST-COST": ("cost", "api", "budget", "reservations"),
    }
    selected = keys_by_profile.get(profile_id)
    if not selected:
        return state
    return {key: state[key] for key in selected if key in state}


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(_normalize(payload, set()), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _counter_changes(before: ReadCounterSnapshot, after: ReadCounterSnapshot) -> tuple[str, ...]:
    changes = []
    for field, before_value in asdict(before).items():
        after_value = asdict(after)[field]
        if after_value != before_value:
            changes.append(field)
    return tuple(changes)


def _routes_in_method(tree: ast.AST, method_name: str) -> tuple[str, ...]:
    routes: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            for child in ast.walk(node):
                if isinstance(child, ast.Compare):
                    for comparator in child.comparators:
                        if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str) and comparator.value.startswith("/api/"):
                            routes.append(comparator.value)
                if isinstance(child, ast.Dict):
                    for key in child.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str) and key.value.startswith("/api/"):
                            routes.append(key.value)
    return tuple(dict.fromkeys(routes))

