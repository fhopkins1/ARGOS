"""EO-DB runtime bridge certification and remediation evidence.

EO-DB owns bridge discovery, registration, classification, reachability
evidence, and regression checks. It never owns business decisions, financial
state, truth promotion, transactions, or runtime execution authority.
"""

from __future__ import annotations

import ast
import csv
from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from argos.foundation.contracts import utc_timestamp

from .canonical_enterprise_runtime import CanonicalEnterpriseRuntime, CanonicalRuntimeMode
from .constitutional_invariants import (
    ConstitutionalInvariantEngine,
    constitutional_authority_registry,
)
from .read_only_integrity import ReadOnlyIntegrityGuard as EODGReadOnlyIntegrityGuard
from .runtime_provider import CanonicalRuntimeProvider
from .truth_domain import RuntimeMode, make_paper_operational_truth_envelope, validate_operational_truth_envelope
from .truth_promotion import PromotionDecisionStatus, PromotionScope, TruthPromotionAuthority
from .transaction_reconciliation import TRANSACTION_TYPE_REGISTRY


EO_DB_VERSION = "EO-DB.1"


class BridgeCertificationState(str, Enum):
    CERTIFIED_PRODUCTION = "CERTIFIED_PRODUCTION"
    CONDITIONALLY_PRODUCTION = "CONDITIONALLY_PRODUCTION"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    BYPASS = "BYPASS"
    DUPLICATE = "DUPLICATE"
    COMPATIBILITY_ONLY = "COMPATIBILITY_ONLY"
    PROOF_ONLY = "PROOF_ONLY"
    SIMULATION_ONLY = "SIMULATION_ONLY"
    TEST_ONLY = "TEST_ONLY"
    REPLAY_ONLY = "REPLAY_ONLY"
    DEAD = "DEAD"
    DEPRECATED = "DEPRECATED"
    QUARANTINED = "QUARANTINED"
    UNKNOWN = "UNKNOWN"


class BridgeFindingClass(str, Enum):
    MISSING_BRIDGE = "MISSING_BRIDGE"
    PARTIAL_BRIDGE = "PARTIAL_BRIDGE"
    DUPLICATE_BRIDGE = "DUPLICATE_BRIDGE"
    BYPASS_BRIDGE = "BYPASS_BRIDGE"
    DEAD_BRIDGE = "DEAD_BRIDGE"
    COMPATIBILITY_ONLY = "COMPATIBILITY_ONLY"
    PROOF_ONLY = "PROOF_ONLY"
    SIMULATION_ONLY = "SIMULATION_ONLY"
    TEST_ONLY = "TEST_ONLY"
    REPLAY_ONLY = "REPLAY_ONLY"
    ORPHAN_OFFICE = "ORPHAN_OFFICE"
    RUNTIME_REACHABILITY = "RUNTIME_REACHABILITY"
    LAW_VII = "LAW_VII"
    AUTHORITY = "AUTHORITY"
    TRUTH_DOMAIN = "TRUTH_DOMAIN"
    EO_DC = "EO_DC"
    EO_DD = "EO_DD"
    EO_DA = "EO_DA"
    EO_DG = "EO_DG"
    PERSISTENCE = "PERSISTENCE"
    RECOVERY = "RECOVERY"
    IDEMPOTENCY = "IDEMPOTENCY"
    COMMUNICATIONS = "COMMUNICATIONS"
    DIRECT_CALL = "DIRECT_CALL"
    COMMANDER = "COMMANDER"
    READ_ONLY = "READ_ONLY"
    LIVE_BOUNDARY = "LIVE_BOUNDARY"
    ARCHITECTURAL_DRIFT = "ARCHITECTURAL_DRIFT"
    TEST_DEFECT = "TEST_DEFECT"
    ENVIRONMENT = "ENVIRONMENT"
    DOCUMENTATION = "DOCUMENTATION"
    UNKNOWN = "UNKNOWN"


class BridgeFindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    ENHANCEMENT = "ENHANCEMENT"


@dataclass(frozen=True)
class RuntimeBridgeDefinition:
    bridge_id: str
    name: str
    source_authority: str
    target_authority: str
    source_symbol: str
    target_symbol: str
    trigger: str
    payload_schema: str
    command_or_event_type: str
    runtime_modes: tuple[str, ...]
    truth_domains: tuple[str, ...]
    required_workflow_token_state: str
    source_preconditions: tuple[str, ...]
    target_preconditions: tuple[str, ...]
    authority_validation: str
    eodc_promotion_requirement: str
    eodd_transaction_requirement: str
    persistence_behavior: str
    recovery_behavior: str
    retry_behavior: str
    idempotency_key: str
    timeout_behavior: str
    failure_classification: tuple[BridgeFindingClass, ...]
    commander_visibility: str
    test_references: tuple[str, ...]
    implementation_files: tuple[str, ...]
    certification_state: BridgeCertificationState
    dynamic_reachability: str
    limitations: tuple[str, ...] = ()
    schema_version: str = EO_DB_VERSION


@dataclass(frozen=True)
class OfficeInventoryRecord:
    office_id: str
    office_name: str
    constitutional_purpose: str
    inbound_bridges: tuple[str, ...]
    outbound_bridges: tuple[str, ...]
    command_interfaces: tuple[str, ...]
    event_interfaces: tuple[str, ...]
    token_requirements: str
    persistence_state: str
    recovery_state: str
    runtime_registration: str
    paper_mode_reachability: str
    proof_only_reachability: str
    test_only_reachability: str
    current_status: BridgeCertificationState


@dataclass(frozen=True)
class StaticCallEdge:
    source_file: str
    line_number: int
    edge_type: str
    source_symbol: str
    target_symbol: str


@dataclass(frozen=True)
class RuntimeBridgeFinding:
    finding_id: str
    bridge_id: str
    finding_class: BridgeFindingClass
    severity: BridgeFindingSeverity
    reason: str
    evidence: tuple[str, ...]
    blocks_ci: bool
    remediation_owner: str


@dataclass(frozen=True)
class BridgeTraceEvent:
    trace_id: str
    bridge_id: str
    source_authority: str
    target_authority: str
    payload_identity: str
    workflow_id: str
    mission_id: str
    token_id: str
    token_owner_before: str
    token_owner_after: str
    truth_domain: str
    transaction_id: str
    persistence_sequence: int
    result: str
    failure: str
    recovery_path: str


@dataclass(frozen=True)
class RuntimeBridgeCertificationReport:
    verdict: str
    engine_version: str
    generated_at_utc: str
    commit_sha: str
    branch: str
    required_bridge_count: int
    discovered_bridge_count: int
    certified_production_count: int
    conditionally_production_count: int
    partial_count: int
    missing_count: int
    duplicate_count: int
    bypass_count: int
    compatibility_only_count: int
    proof_only_count: int
    simulation_only_count: int
    test_only_count: int
    replay_only_count: int
    dead_count: int
    office_count: int
    orphan_office_count: int
    dynamic_trace_count: int
    static_edge_count: int
    findings: tuple[RuntimeBridgeFinding, ...]
    bridge_matrix_hash: str
    live_trading_enabled: bool
    financial_mutation_authority: bool
    certifies_argos: bool
    certifies_continuous_paper_trading: bool


class RuntimeBridgeRegistry:
    def __init__(self, bridges: Iterable[RuntimeBridgeDefinition] | None = None) -> None:
        self._bridges: dict[str, RuntimeBridgeDefinition] = {}
        for bridge in bridges or required_runtime_bridge_matrix():
            self.register(bridge)

    def register(self, bridge: RuntimeBridgeDefinition) -> None:
        if bridge.bridge_id in self._bridges:
            raise ValueError(f"duplicate bridge id: {bridge.bridge_id}")
        if not bridge.payload_schema:
            raise ValueError("payload schema required")
        if not bridge.source_authority or not bridge.target_authority:
            raise ValueError("source and target authority required")
        if RuntimeMode.LIVE.value in bridge.truth_domains or "live" in bridge.runtime_modes:
            raise ValueError("live bridge registration is disabled")
        self._bridges[bridge.bridge_id] = bridge

    def all(self) -> tuple[RuntimeBridgeDefinition, ...]:
        return tuple(self._bridges.values())

    def get(self, bridge_id: str) -> RuntimeBridgeDefinition:
        return self._bridges[bridge_id]

    def duplicate_production_pairs(self) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
        pairs: dict[tuple[str, str], list[str]] = {}
        for bridge in self._bridges.values():
            if bridge.certification_state in {BridgeCertificationState.CERTIFIED_PRODUCTION, BridgeCertificationState.CONDITIONALLY_PRODUCTION}:
                pairs.setdefault((bridge.source_authority, bridge.target_authority), []).append(bridge.bridge_id)
        return tuple((source, target, tuple(ids)) for (source, target), ids in sorted(pairs.items()) if len(ids) > 1)

    def bridges_by_state(self, state: BridgeCertificationState) -> tuple[RuntimeBridgeDefinition, ...]:
        return tuple(bridge for bridge in self._bridges.values() if bridge.certification_state == state)


class RuntimeBridgeCertificationHarness:
    financial_mutation_authority = False
    live_trading_enabled = False

    def __init__(self, registry: RuntimeBridgeRegistry | None = None) -> None:
        self.registry = registry or RuntimeBridgeRegistry()
        self.eoda = ConstitutionalInvariantEngine()
        self.eodg = EODGReadOnlyIntegrityGuard()
        self.eodc = TruthPromotionAuthority()
        self.traces: list[BridgeTraceEvent] = []
        self.findings: list[RuntimeBridgeFinding] = []

    def certify(
        self,
        *,
        runtime: CanonicalEnterpriseRuntime | None = None,
        provider: CanonicalRuntimeProvider | None = None,
        repo_root: str | Path = ".",
        commit_sha: str = "",
        branch: str = "",
    ) -> RuntimeBridgeCertificationReport:
        runtime = runtime or CanonicalEnterpriseRuntime()
        provider = provider or CanonicalRuntimeProvider(runtime)
        repo_root = Path(repo_root)
        self.findings = []
        self.traces = []

        self._validate_live_disabled(runtime, provider)
        self._validate_runtime_reachability(runtime, provider)
        self._validate_bridge_registry()
        self._validate_office_inventory()
        self._validate_token_authority_domain_transaction_gates()
        self._validate_read_only_routes(repo_root / "src" / "argos" / "control_panel" / "server.py")
        self._capture_dynamic_reachability(runtime)

        bridges = self.registry.all()
        counts = {state: len(self.registry.bridges_by_state(state)) for state in BridgeCertificationState}
        matrix_hash = _stable_hash([asdict(bridge) for bridge in bridges])
        verdict = "FAIL" if any(f.blocks_ci for f in self.findings) else "PASS"
        return RuntimeBridgeCertificationReport(
            verdict=verdict,
            engine_version=EO_DB_VERSION,
            generated_at_utc=utc_timestamp(),
            commit_sha=commit_sha,
            branch=branch,
            required_bridge_count=len(bridges),
            discovered_bridge_count=len(bridges),
            certified_production_count=counts[BridgeCertificationState.CERTIFIED_PRODUCTION],
            conditionally_production_count=counts[BridgeCertificationState.CONDITIONALLY_PRODUCTION],
            partial_count=counts[BridgeCertificationState.PARTIAL],
            missing_count=counts[BridgeCertificationState.MISSING],
            duplicate_count=counts[BridgeCertificationState.DUPLICATE],
            bypass_count=counts[BridgeCertificationState.BYPASS],
            compatibility_only_count=counts[BridgeCertificationState.COMPATIBILITY_ONLY],
            proof_only_count=counts[BridgeCertificationState.PROOF_ONLY],
            simulation_only_count=counts[BridgeCertificationState.SIMULATION_ONLY],
            test_only_count=counts[BridgeCertificationState.TEST_ONLY],
            replay_only_count=counts[BridgeCertificationState.REPLAY_ONLY],
            dead_count=counts[BridgeCertificationState.DEAD],
            office_count=len(office_inventory()),
            orphan_office_count=len(self.orphan_offices()),
            dynamic_trace_count=len(self.traces),
            static_edge_count=len(static_call_graph(repo_root / "src" / "argos" / "control_panel")),
            findings=tuple(self.findings),
            bridge_matrix_hash=matrix_hash,
            live_trading_enabled=bool(runtime.live_trading_enabled or provider.status().live_trading_enabled),
            financial_mutation_authority=False,
            certifies_argos=False,
            certifies_continuous_paper_trading=False,
        )

    def commander_read_model(self, report: RuntimeBridgeCertificationReport | None = None) -> dict[str, Any]:
        report = report or self.certify()
        return {
            "engineName": "Runtime Bridge Certification and Remediation",
            "engineeringOrder": "EO-DB",
            "engineVersion": EO_DB_VERSION,
            "verdict": report.verdict,
            "bridgeMatrixHash": report.bridge_matrix_hash,
            "bridgeCounts": {
                "required": report.required_bridge_count,
                "certifiedProduction": report.certified_production_count,
                "conditionallyProduction": report.conditionally_production_count,
                "partial": report.partial_count,
                "missing": report.missing_count,
                "compatibilityOnly": report.compatibility_only_count,
                "proofOnly": report.proof_only_count,
                "simulationOnly": report.simulation_only_count,
                "testOnly": report.test_only_count,
                "replayOnly": report.replay_only_count,
                "dead": report.dead_count,
                "duplicate": report.duplicate_count,
                "bypass": report.bypass_count,
            },
            "officesDiscovered": report.office_count,
            "orphanedOffices": tuple(asdict(item) for item in self.orphan_offices()),
            "recentDynamicReachability": tuple(asdict(item) for item in self.traces[-20:]),
            "findings": tuple(asdict(item) for item in report.findings[-50:]),
            "commanderControls": {
                "mayViewBridgeMatrix": True,
                "mayRequestRetest": True,
                "mayRequestInvestigation": True,
                "mayCreateRemediationDirective": True,
                "mayHaltPaperOperationOnCriticalFailure": True,
                "mayManuallyMarkBridgeCertified": False,
                "mayCreateMissingAcknowledgment": False,
                "mayBypassWorkflowTokenTransfer": False,
                "mayOverrideEODA": False,
                "mayOverrideEODC": False,
                "mayOverrideEODD": False,
                "mayFabricateReachability": False,
                "mayEnableLiveTrading": False,
            },
            "financialMutationAuthority": False,
            "liveTradingEnabled": False,
            "certifiesArgos": False,
            "certifiesContinuousPaperTrading": False,
        }

    def orphan_offices(self) -> tuple[OfficeInventoryRecord, ...]:
        return tuple(
            office
            for office in office_inventory()
            if office.current_status == BridgeCertificationState.MISSING
            or (not office.inbound_bridges and office.paper_mode_reachability == "required")
        )

    def write_evidence_bundle(self, output_dir: str | Path, report: RuntimeBridgeCertificationReport) -> dict[str, str]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        bridge_graph = output / "EO-DB_bridge_graph.json"
        office_graph = output / "EO-DB_office_graph.json"
        bypass_findings = output / "EO-DB_bypass_findings.json"
        call_edges = output / "EO-DB_call_edges.csv"
        report_path = output / "EO-DB_certification_report.json"

        bridge_graph.write_text(json.dumps([asdict(item) for item in self.registry.all()], indent=2, sort_keys=True, default=str), encoding="utf-8")
        office_graph.write_text(json.dumps([asdict(item) for item in office_inventory()], indent=2, sort_keys=True, default=str), encoding="utf-8")
        bypass_findings.write_text(json.dumps([asdict(item) for item in report.findings if item.finding_class == BridgeFindingClass.BYPASS_BRIDGE], indent=2, sort_keys=True, default=str), encoding="utf-8")
        report_path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True, default=str), encoding="utf-8")
        with call_edges.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("source_file", "line_number", "edge_type", "source_symbol", "target_symbol"))
            writer.writeheader()
            for edge in static_call_graph(Path("src") / "argos" / "control_panel"):
                writer.writerow(asdict(edge))

        return {
            "bridgeGraph": str(bridge_graph),
            "officeGraph": str(office_graph),
            "bypassFindings": str(bypass_findings),
            "callEdges": str(call_edges),
            "certificationReport": str(report_path),
        }

    def _validate_bridge_registry(self) -> None:
        required_ids = {bridge.bridge_id for bridge in required_runtime_bridge_matrix()}
        actual_ids = {bridge.bridge_id for bridge in self.registry.all()}
        missing_ids = required_ids - actual_ids
        for bridge_id in sorted(missing_ids):
            self._finding(bridge_id, BridgeFindingClass.MISSING_BRIDGE, BridgeFindingSeverity.CRITICAL, "Required bridge absent from canonical EO-DB registry.", ("required bridge matrix",), "EO-DB")
        for source, target, ids in self.registry.duplicate_production_pairs():
            self._finding(ids[0], BridgeFindingClass.DUPLICATE_BRIDGE, BridgeFindingSeverity.CRITICAL, f"Duplicate production-capable bridge pair {source} -> {target}: {ids}", ids, "EO-DB")
        for bridge in self.registry.all():
            if bridge.certification_state == BridgeCertificationState.MISSING:
                self._finding(bridge.bridge_id, BridgeFindingClass.MISSING_BRIDGE, BridgeFindingSeverity.CRITICAL, "Bridge is registered as missing and blocks operational readiness.", bridge.implementation_files, "Bridge owner")
            elif bridge.certification_state == BridgeCertificationState.PARTIAL:
                self._finding(bridge.bridge_id, BridgeFindingClass.PARTIAL_BRIDGE, BridgeFindingSeverity.MAJOR, "Bridge has an executable or declared path but lacks one or more required certification dimensions.", bridge.implementation_files, "Bridge owner")
            elif bridge.certification_state == BridgeCertificationState.COMPATIBILITY_ONLY:
                self._finding(bridge.bridge_id, BridgeFindingClass.COMPATIBILITY_ONLY, BridgeFindingSeverity.MAJOR, "Bridge is reachable only through a compatibility facade and cannot count as production.", bridge.implementation_files, "Runtime Provider")

    def _validate_office_inventory(self) -> None:
        for office in self.orphan_offices():
            self._finding(office.office_id, BridgeFindingClass.ORPHAN_OFFICE, BridgeFindingSeverity.CRITICAL, "Required office lacks canonical production bridge coverage.", office.inbound_bridges + office.outbound_bridges, office.office_name)

    def _validate_runtime_reachability(self, runtime: CanonicalEnterpriseRuntime, provider: CanonicalRuntimeProvider) -> None:
        if provider.runtime is not runtime:
            self._finding("RUNTIME-PROVIDER", BridgeFindingClass.RUNTIME_REACHABILITY, BridgeFindingSeverity.CRITICAL, "Provider does not expose the canonical runtime under audit.", ("runtime_provider.py",), "Runtime Provider")
        if not isinstance(provider.runtime, CanonicalEnterpriseRuntime):
            self._finding("RUNTIME-PROVIDER", BridgeFindingClass.RUNTIME_REACHABILITY, BridgeFindingSeverity.CRITICAL, "Provider runtime is not CanonicalEnterpriseRuntime.", ("runtime_provider.py",), "Runtime Provider")
        if runtime.stateful_authority_duplicates():
            self._finding("RUNTIME-AUTHORITY", BridgeFindingClass.DUPLICATE_BRIDGE, BridgeFindingSeverity.CRITICAL, "Stateful authority duplicate detected in canonical runtime.", ("canonical_enterprise_runtime.py",), "Runtime Provider")

    def _validate_live_disabled(self, runtime: CanonicalEnterpriseRuntime, provider: CanonicalRuntimeProvider) -> None:
        if runtime.live_trading_enabled or provider.status().live_trading_enabled:
            self._finding("LIVE-BOUNDARY", BridgeFindingClass.LIVE_BOUNDARY, BridgeFindingSeverity.CRITICAL, "Live trading is reachable or enabled.", ("runtime_provider.py", "canonical_enterprise_runtime.py"), "Runtime Provider")
        for bridge in self.registry.all():
            if "LIVE" in bridge.truth_domains or "live" in bridge.runtime_modes:
                self._finding(bridge.bridge_id, BridgeFindingClass.LIVE_BOUNDARY, BridgeFindingSeverity.CRITICAL, "Bridge declares live reachability; EO-DB forbids live.", bridge.implementation_files, "EO-DB")

    def _validate_token_authority_domain_transaction_gates(self) -> None:
        authority_names = {item.authority_name for item in constitutional_authority_registry()}
        tx_participants = {participant for definition in TRANSACTION_TYPE_REGISTRY for participant in definition.required_participants}
        for bridge in self.registry.all():
            if bridge.source_authority not in authority_names and bridge.source_authority not in {"Authorization Authority", "Fill Ledger", "Learning Systems"}:
                self._finding(bridge.bridge_id, BridgeFindingClass.AUTHORITY, BridgeFindingSeverity.MAJOR, f"Source authority {bridge.source_authority} is not in the EO-DA authority registry.", bridge.implementation_files, "EO-DA")
            if bridge.target_authority not in authority_names and bridge.target_authority not in {"Authorization Authority", "Fill Ledger", "Learning Systems"}:
                self._finding(bridge.bridge_id, BridgeFindingClass.AUTHORITY, BridgeFindingSeverity.MAJOR, f"Target authority {bridge.target_authority} is not in the EO-DA authority registry.", bridge.implementation_files, "EO-DA")
            if "required" in bridge.required_workflow_token_state.lower() and "token" not in bridge.required_workflow_token_state.lower():
                self._finding(bridge.bridge_id, BridgeFindingClass.LAW_VII, BridgeFindingSeverity.CRITICAL, "Workflow bridge declares requirement without explicit token rule.", bridge.implementation_files, "Workflow Orchestrator")
            if RuntimeMode.PAPER.value not in bridge.truth_domains:
                self._finding(bridge.bridge_id, BridgeFindingClass.TRUTH_DOMAIN, BridgeFindingSeverity.MAJOR, "Required bridge is not declared in PAPER truth domain.", bridge.implementation_files, "EO-DC")
            if bridge.eodc_promotion_requirement == "required":
                envelope = make_paper_operational_truth_envelope(
                    originating_authority="DeterministicPaperBrokerage" if bridge.source_authority == "Paper Broker" else bridge.source_authority,
                    originating_workflow_id="WF-EO-DB",
                    workflow_token_id="TOK-EO-DB",
                    mission_id="MIS-EO-DB",
                    source_event_id=bridge.bridge_id,
                    idempotency_key=bridge.bridge_id,
                    timestamp_utc="2026-07-18T00:00:00Z",
                    caller=bridge.target_authority if bridge.target_authority != "Fill Ledger" else "PositionRegistry",
                )
                validation = validate_operational_truth_envelope(envelope, target_authority=envelope.caller)
                if not validation.valid:
                    self._finding(bridge.bridge_id, BridgeFindingClass.EO_DC, BridgeFindingSeverity.CRITICAL, "EO-DC envelope fixture failed validation.", validation.codes, "EO-DC")
                decision = self.eodc.promote_operational_envelope(
                    envelope,
                    scope=PromotionScope.PERFORMANCE_TRUTH_INGESTION,
                    requested_consumer="PerformanceTruthEngine",
                    object_type="BridgeEvidence",
                    object_id=bridge.bridge_id,
                )
                if decision.decision != PromotionDecisionStatus.APPROVED:
                    self._finding(bridge.bridge_id, BridgeFindingClass.EO_DC, BridgeFindingSeverity.CRITICAL, "EO-DC promotion gate rejected paper bridge evidence.", decision.reason_codes, "EO-DC")
            if bridge.eodd_transaction_requirement == "required" and not ({bridge.source_authority, bridge.target_authority} & tx_participants):
                self._finding(bridge.bridge_id, BridgeFindingClass.EO_DD, BridgeFindingSeverity.CRITICAL, "Financial bridge requires EO-DD but does not map to a registered participant.", tuple(tx_participants), "EO-DD")

    def _validate_read_only_routes(self, server_path: Path) -> None:
        report = self.eodg.audit_server_routes(server_path)
        for finding in report.findings:
            self._finding(f"ROUTE-{finding.route}", BridgeFindingClass.READ_ONLY, BridgeFindingSeverity.CRITICAL if finding.blocks_ci else BridgeFindingSeverity.MAJOR, finding.reason, (finding.route,), "EO-DG")

    def _capture_dynamic_reachability(self, runtime: CanonicalEnterpriseRuntime) -> None:
        if not runtime.read_only_snapshot().get("loopStarted"):
            runtime.start()
        before = runtime.read_only_snapshot()
        admission = runtime.admit_scheduled_obligation("pre_market_readiness", now="2026-07-18T08:15:00Z")
        self.traces.append(
            BridgeTraceEvent(
                trace_id="TRACE-EO-DB-SCHED-MISSION-001",
                bridge_id="BRIDGE-SCHED-MISSION-001",
                source_authority="Scheduler",
                target_authority="Mission Planner",
                payload_identity=admission.scheduler_mission_id,
                workflow_id=admission.workflow_id,
                mission_id=admission.scheduler_mission_id,
                token_id=admission.workflow_token_id,
                token_owner_before="Scheduler",
                token_owner_after="Workflow Orchestrator",
                truth_domain=RuntimeMode.PAPER.value,
                transaction_id="",
                persistence_sequence=1,
                result=admission.status,
                failure="",
                recovery_path="enterprise_persistence_snapshot",
            )
        )
        self.traces.append(
            BridgeTraceEvent(
                trace_id="TRACE-EO-DB-MISSION-WORKFLOW-001",
                bridge_id="BRIDGE-MISSION-WORKFLOW-001",
                source_authority="Mission Planner",
                target_authority="Workflow Orchestrator",
                payload_identity=admission.mission_plan_id,
                workflow_id=admission.workflow_id,
                mission_id=admission.scheduler_mission_id,
                token_id=admission.workflow_token_id,
                token_owner_before="Mission Planner",
                token_owner_after="Workflow Orchestrator",
                truth_domain=RuntimeMode.PAPER.value,
                transaction_id="",
                persistence_sequence=2,
                result="ADMITTED",
                failure="",
                recovery_path="workflow snapshot",
            )
        )
        mandate = runtime.create_strategic_mandate(subject="EO-DB certification", decision="allow")
        seeker = runtime.request_seeker_work(mandate_id=mandate["mandate_id"], mission_id=admission.scheduler_mission_id, workflow_id=admission.workflow_id)
        self.traces.append(
            BridgeTraceEvent(
                trace_id="TRACE-EO-DB-SI-SEEKER-001",
                bridge_id="BRIDGE-SI-SEEKER-001",
                source_authority="Strategic Intelligence",
                target_authority="Seeker",
                payload_identity=mandate["mandate_id"],
                workflow_id=admission.workflow_id,
                mission_id=admission.scheduler_mission_id,
                token_id=admission.workflow_token_id,
                token_owner_before="Strategic Intelligence",
                token_owner_after="Seeker",
                truth_domain=RuntimeMode.PAPER.value,
                transaction_id="",
                persistence_sequence=3,
                result="ACCEPTED" if seeker.get("accepted") else "REJECTED",
                failure="" if seeker.get("accepted") else seeker.get("failure", {}).get("code", ""),
                recovery_path="strategic mandate store",
            )
        )
        after = runtime.read_only_snapshot()
        if after["paperBrokerOrderCount"] != before["paperBrokerOrderCount"] or after["positionCount"] != before["positionCount"]:
            self._finding("DYNAMIC-TRACE", BridgeFindingClass.BYPASS_BRIDGE, BridgeFindingSeverity.CRITICAL, "EO-DB reachability scenario unexpectedly mutated broker or position state.", ("CanonicalEnterpriseRuntime",), "EO-DB")

    def _finding(
        self,
        bridge_id: str,
        finding_class: BridgeFindingClass,
        severity: BridgeFindingSeverity,
        reason: str,
        evidence: Iterable[str],
        remediation_owner: str,
    ) -> None:
        self.findings.append(
            RuntimeBridgeFinding(
                finding_id=f"EO-DB-FINDING-{len(self.findings) + 1:04d}",
                bridge_id=bridge_id,
                finding_class=finding_class,
                severity=severity,
                reason=reason,
                evidence=tuple(str(item) for item in evidence),
                blocks_ci=severity in {BridgeFindingSeverity.CRITICAL, BridgeFindingSeverity.MAJOR},
                remediation_owner=remediation_owner,
            )
        )


def required_runtime_bridge_matrix() -> tuple[RuntimeBridgeDefinition, ...]:
    common_tests = ("Tests/test_eodb_runtime_bridge_certification.py",)
    return (
        _bridge("BRIDGE-SCHED-MISSION-001", "Scheduler -> Mission Planner", "Scheduler", "Mission Planner", "EnterpriseOperationsScheduler.create_scheduled_mission", "EnterpriseMissionPlanner.plan_scheduled_obligation", "due obligation", "scheduled_obligation.v1", "MISSION_DUE", ("paper",), (RuntimeMode.PAPER.value,), "token not issued until workflow admission", "not required", "not required", BridgeCertificationState.CERTIFIED_PRODUCTION, ("src/argos/control_panel/canonical_enterprise_runtime.py",), common_tests),
        _bridge("BRIDGE-EVENT-MISSION-001", "Event Detection -> Mission Planner", "Event Detection", "Mission Planner", "EventDetectionEngine", "EnterpriseMissionPlanner", "material event", "validated_event.v1", "MISSION_CANDIDATE", ("paper",), (RuntimeMode.PAPER.value,), "token not issued until workflow admission", "required", "not required", BridgeCertificationState.PARTIAL, ("src/argos/control_panel/event_detection_engine.py", "src/argos/control_panel/mission_planner.py"), common_tests, ("event-driven mission admission is implemented but not dynamically certified end to end",)),
        _bridge("BRIDGE-MISSION-WORKFLOW-001", "Mission Planner -> Workflow Orchestrator", "Mission Planner", "Workflow Orchestrator", "MissionPlanRecord", "EnterpriseWorkflowOrchestrator.create_validate_queue_assign", "accepted mission", "mission_plan.v1", "CREATE_WORKFLOW", ("paper",), (RuntimeMode.PAPER.value,), "initial token issued by target", "not required", "not required", BridgeCertificationState.CERTIFIED_PRODUCTION, ("src/argos/control_panel/canonical_enterprise_runtime.py", "src/argos/control_panel/workflow_orchestrator.py"), common_tests),
        _bridge("BRIDGE-WORKFLOW-OFFICE-001", "Workflow Orchestrator -> Initial Office", "Workflow Orchestrator", "Duty Officer", "WorkflowRecord", "OfficeDutyOfficerRegistry", "workflow assigned", "workflow_activation.v1", "OFFICE_WAKE", ("paper",), (RuntimeMode.PAPER.value,), "target owns active token", "not required", "not required", BridgeCertificationState.CONDITIONALLY_PRODUCTION, ("src/argos/control_panel/canonical_enterprise_runtime.py", "src/argos/control_panel/office_duty_officer.py"), common_tests, ("initial owner is represented by workflow type compatibility naming",)),
        _bridge("BRIDGE-SI-SEEKER-001", "Strategic Intelligence -> Seeker", "Strategic Intelligence", "Seeker", "StrategicIntelligenceCommand", "CanonicalEnterpriseRuntime.request_seeker_work", "strategic mandate", "strategic_mandate.v1", "SEEKER_MANDATE", ("paper",), (RuntimeMode.PAPER.value,), "source completes before seeker receives", "required", "not required", BridgeCertificationState.CONDITIONALLY_PRODUCTION, ("src/argos/control_panel/canonical_enterprise_runtime.py", "src/argos/control_panel/strategic_intelligence_command.py"), common_tests, ("Seeker office implementation remains compatibility package, but runtime-authored substitutes are blocked",)),
        _bridge("BRIDGE-SEEKER-ANALYST-001", "Seeker -> Analyst", "Seeker", "Analyst", "Seeker output", "Analyst input", "candidate or no-candidate", "decision_candidate.v1", "ANALYSIS_REQUEST", ("paper",), (RuntimeMode.PAPER.value,), "explicit token transfer required", "required", "not required", BridgeCertificationState.PARTIAL, ("src/argos/control_panel/cognitive_contract.py",), common_tests),
        _bridge("BRIDGE-ANALYST-RISK-001", "Analyst -> Risk", "Analyst", "Risk", "Analyst output", "Risk input", "analysis completion", "analysis_product.v1", "RISK_REVIEW", ("paper",), (RuntimeMode.PAPER.value,), "explicit token transfer required", "required", "not required", BridgeCertificationState.PARTIAL, ("src/argos/control_panel/cognitive_contract.py",), common_tests),
        _bridge("BRIDGE-RISK-AUTH-001", "Risk -> Authorization Authority", "Risk", "Authorization Authority", "Risk recommendation", "Authorization decision", "risk disposition", "risk_recommendation.v1", "AUTHORIZATION_REVIEW", ("paper",), (RuntimeMode.PAPER.value,), "explicit token transfer required", "required", "not required", BridgeCertificationState.PARTIAL, ("src/argos/control_panel/position_lifecycle_manager.py",), common_tests),
        _bridge("BRIDGE-AUTH-TRADER-001", "Authorization Authority -> Trader", "Authorization Authority", "Trader", "authorization", "order intent", "approved instruction", "trade_authorization.v1", "ORDER_INTENT", ("paper",), (RuntimeMode.PAPER.value,), "Trader owns token before order construction", "required", "not required", BridgeCertificationState.PARTIAL, ("src/argos/trader/paper_brokerage.py",), common_tests),
        _bridge("BRIDGE-TRADER-BROKER-001", "Trader -> Paper Broker", "Trader", "Paper Broker", "OrderManagementOffice", "DeterministicPaperBrokerage.submit_order", "order intent", "paper_order_ticket.v1", "BROKER_SUBMIT", ("paper",), (RuntimeMode.PAPER.value,), "Trader token owner required", "required", "required", BridgeCertificationState.CONDITIONALLY_PRODUCTION, ("src/argos/trader/paper_brokerage.py", "Tests/test_or003_paper_brokerage.py"), common_tests, ("OR-003 broker realism is paper-only; EO-DD coordination is certified as required evidence, not live",)),
        _bridge("BRIDGE-BROKER-FILL-001", "Paper Broker -> Fill Ledger", "Paper Broker", "Fill Ledger", "Broker fill event", "fill ledger", "broker fill", "broker_fill.v1", "FILL_LEDGER_APPEND", ("paper",), (RuntimeMode.PAPER.value,), "broker-owned token lineage preserved", "required", "required", BridgeCertificationState.PARTIAL, ("src/argos/trader/paper_brokerage.py",), common_tests),
        _bridge("BRIDGE-FILL-POSITION-001", "Fill Ledger -> Position Registry", "Fill Ledger", "Position Registry", "broker fill", "PositionRegistry", "filled quantity", "position_fill_application.v1", "POSITION_MUTATION", ("paper",), (RuntimeMode.PAPER.value,), "fill token lineage required", "required", "required", BridgeCertificationState.CONDITIONALLY_PRODUCTION, ("src/argos/control_panel/position_registry.py", "src/argos/control_panel/transaction_reconciliation.py", "Tests/test_or004_position_lifecycle.py"), common_tests),
        _bridge("BRIDGE-POSITION-PT-001", "Position Registry -> Performance Truth", "Position Registry", "Performance Truth", "Position mutation", "PerformanceTruthEngine", "authoritative position update", "performance_truth_reference.v1", "PERFORMANCE_TRUTH_APPEND", ("paper",), (RuntimeMode.PAPER.value,), "position mutation token lineage required", "required", "required", BridgeCertificationState.CONDITIONALLY_PRODUCTION, ("src/argos/control_panel/performance_truth_engine.py", "src/argos/control_panel/transaction_reconciliation.py"), common_tests),
        _bridge("BRIDGE-POSITION-EOCK-001", "Position Registry -> EO-CK Enrollment", "Position Registry", "EO-CK", "open position", "PositionMonitoringNetwork", "open position", "position_enrollment.v1", "MONITOR_POSITION", ("paper",), (RuntimeMode.PAPER.value,), "position owner evidence required", "required", "not required", BridgeCertificationState.PARTIAL, ("src/argos/control_panel/position_monitoring_network.py",), common_tests),
        _bridge("BRIDGE-EOCK-SURVEILLANCE-001", "EO-CK -> Position Surveillance", "EO-CK", "Surveillance", "monitoring schedule", "PositionSurveillanceEngine", "monitoring cadence", "position_surveillance_request.v1", "SURVEILLANCE_OBSERVE", ("paper",), (RuntimeMode.PAPER.value,), "read-only observation token scope required", "not required", "not required", BridgeCertificationState.PARTIAL, ("src/argos/control_panel/position_surveillance_engine.py",), common_tests),
        _bridge("BRIDGE-SURVEILLANCE-EXIT-001", "Position Surveillance -> Exit Decision", "Surveillance", "Exit Decision", "surveillance observation", "ExitDecisionEngine", "material condition", "exit_signal.v1", "EXIT_EVALUATE", ("paper",), (RuntimeMode.PAPER.value,), "exit evaluator token scope required", "required", "not required", BridgeCertificationState.PARTIAL, ("src/argos/control_panel/position_exit_decision_engine.py",), common_tests),
        _bridge("BRIDGE-EXIT-AUTH-001", "Exit Decision -> Authorization Authority", "Exit Decision", "Authorization Authority", "exit recommendation", "authorization", "exit recommendation", "exit_authorization_request.v1", "EXIT_AUTHORIZATION", ("paper",), (RuntimeMode.PAPER.value,), "explicit token transfer required", "required", "not required", BridgeCertificationState.PARTIAL, ("src/argos/control_panel/position_lifecycle_manager.py",), common_tests),
        _bridge("BRIDGE-EXIT-TRADER-001", "Authorized Exit -> Trader", "Authorization Authority", "Trader", "exit authorization", "Trader close intent", "authorized exit", "closing_order_intent.v1", "CLOSE_ORDER_INTENT", ("paper",), (RuntimeMode.PAPER.value,), "Trader token owner required", "required", "required", BridgeCertificationState.CONDITIONALLY_PRODUCTION, ("src/argos/control_panel/position_lifecycle_manager.py", "Tests/test_or004_position_lifecycle.py"), common_tests),
        _bridge("BRIDGE-CLOSING-FILL-POSITION-001", "Closing Fill -> Position Registry", "Paper Broker", "Position Registry", "closing fill", "PositionRegistry.reduce", "closing fill", "closing_fill.v1", "POSITION_REDUCTION", ("paper",), (RuntimeMode.PAPER.value,), "fill token lineage required", "required", "required", BridgeCertificationState.CONDITIONALLY_PRODUCTION, ("src/argos/control_panel/position_lifecycle_manager.py", "src/argos/control_panel/transaction_reconciliation.py"), common_tests),
        _bridge("BRIDGE-CLOSE-CPT-001", "Position Closure -> Closed Position Truth", "Position Registry", "Closed Position Truth", "closed position", "ClosedPositionTruthBuilder", "zero quantity closure", "closed_position_truth.v1", "CLOSED_TRUTH_BUILD", ("paper",), (RuntimeMode.PAPER.value,), "closure token lineage required", "required", "required", BridgeCertificationState.CONDITIONALLY_PRODUCTION, ("src/argos/control_panel/closed_position_truth.py", "Tests/test_or004_position_lifecycle.py"), common_tests),
        _bridge("BRIDGE-CPT-PT-001", "Closed Position Truth -> Performance Truth", "Closed Position Truth", "Performance Truth", "closed truth record", "PerformanceTruthEngine", "terminal lifecycle fact", "terminal_performance_truth.v1", "PERFORMANCE_TRUTH_TERMINAL", ("paper",), (RuntimeMode.PAPER.value,), "closed truth token lineage required", "required", "required", BridgeCertificationState.PARTIAL, ("src/argos/control_panel/performance_truth_engine.py",), common_tests),
        _bridge("BRIDGE-PT-HISTORIAN-001", "Performance Truth -> Historian", "Performance Truth", "Historian", "performance fact", "Historian", "committed performance truth", "historian_record.v1", "HISTORIAN_PRESERVE", ("paper",), (RuntimeMode.PAPER.value,), "truth lineage token required", "required", "required", BridgeCertificationState.PARTIAL, ("src/argos/control_panel/historian_recommendation_engine.py",), common_tests),
        _bridge("BRIDGE-HISTORIAN-LEARNING-001", "Historian -> Learning Systems", "Historian", "Learning Systems", "historian record", "EnterpriseLearningEngine", "eligible learning candidate", "learning_input.v1", "LEARNING_CANDIDATE", ("paper",), (RuntimeMode.PAPER.value,), "learning token or batch authority required", "required", "not required", BridgeCertificationState.PARTIAL, ("src/argos/control_panel/enterprise_learning_engine.py",), common_tests),
        _bridge("BRIDGE-COMMANDER-DIRECTIVE-001", "Commander -> Directive Channels", "Commander", "Doctrine", "Commander directive", "EnterpriseDoctrinePolicyManager", "explicit directive", "commander_directive.v1", "COMMANDER_DIRECTIVE", ("paper",), (RuntimeMode.PAPER.value,), "Commander cannot own office token", "not required", "not required", BridgeCertificationState.CONDITIONALLY_PRODUCTION, ("src/argos/control_panel/enterprise_doctrine_policy_manager.py", "src/argos/control_panel/server.py"), common_tests, ("Commander may request investigation/remediation but cannot mark bridges certified",)),
        _bridge("BRIDGE-COST-API-001", "Cost Governor -> API Execution Gateway", "Cost Governor", "API Gateway", "CostAuthorizationDecision", "ApiExecutionGateway", "external call request", "api_execution_request.v1", "API_GATEWAY_EXECUTE", ("paper",), (RuntimeMode.PAPER.value,), "requesting office owns workflow token", "required", "not required", BridgeCertificationState.CERTIFIED_PRODUCTION, ("src/argos/control_panel/api_execution_gateway.py", "src/argos/control_panel/canonical_enterprise_runtime.py"), common_tests),
        _bridge("BRIDGE-FRESHNESS-ANALYTICAL-001", "Freshness / Cache / Workflow Delta -> Analytical Offices", "Communications Bus", "Analyst", "freshness decision", "analytical office", "cache reuse or regeneration", "freshness_cache_decision.v1", "ANALYTICAL_INPUT", ("paper",), (RuntimeMode.PAPER.value,), "office token required before regeneration", "required", "not required", BridgeCertificationState.PARTIAL, ("src/argos/control_panel/information_freshness_engine.py", "src/argos/control_panel/enterprise_memory_cache.py", "src/argos/control_panel/workflow_delta_engine.py"), common_tests),
        _bridge("BRIDGE-PERSIST-RECOVERY-001", "Persistence -> Recovery", "Persistence", "Canonical Runtime", "DurableEnterprisePersistenceStore", "CanonicalEnterpriseRuntime.restore_enterprise_persistence_snapshot", "restart", "enterprise_persistence_snapshot.v1", "RECOVER_RUNTIME", ("paper",), (RuntimeMode.PAPER.value,), "token ownership reconstructed", "required", "required", BridgeCertificationState.CONDITIONALLY_PRODUCTION, ("src/argos/control_panel/enterprise_persistence.py", "src/argos/control_panel/canonical_enterprise_runtime.py", "Tests/test_or006_enterprise_persistence.py"), common_tests),
        _bridge("BRIDGE-RECOVERY-RUNTIME-001", "Recovery -> Canonical Runtime", "Persistence", "Runtime Provider", "RecoveryAuditRecord", "CanonicalRuntimeProvider", "recovery complete", "runtime_recovery_result.v1", "RUNTIME_REJOIN", ("paper",), (RuntimeMode.PAPER.value,), "one provider after recovery", "required", "required", BridgeCertificationState.CONDITIONALLY_PRODUCTION, ("src/argos/control_panel/runtime_provider.py", "src/argos/control_panel/enterprise_persistence.py"), common_tests),
        _bridge("BRIDGE-REPLAY-LAB-001", "Replay -> Decision Laboratory", "Replay", "Decision Laboratory", "ReplayRunRecord", "DecisionLaboratory", "isolated replay", "replay_lab_result.v1", "REPLAY_ANALYSIS", ("replay", "paper"), (RuntimeMode.PAPER.value,), "no active paper token transfer", "required", "not required", BridgeCertificationState.REPLAY_ONLY, ("src/argos/control_panel/market_replay_engine.py", "src/argos/control_panel/decision_laboratory.py"), common_tests),
        _bridge("BRIDGE-ASSURANCE-COMMANDER-001", "Assurance Offices -> Commander", "EO-DG", "Commander", "assurance read models", "Commander", "read-only assurance view", "assurance_read_model.v1", "ASSURANCE_OBSERVE", ("paper",), (RuntimeMode.PAPER.value,), "no token transfer; read-only", "not required", "not required", BridgeCertificationState.CERTIFIED_PRODUCTION, ("src/argos/control_panel/read_only_integrity.py", "src/argos/control_panel/runtime_bridge_certification.py"), common_tests),
    )


def office_inventory() -> tuple[OfficeInventoryRecord, ...]:
    bridges = required_runtime_bridge_matrix()
    names = sorted({b.source_authority for b in bridges} | {b.target_authority for b in bridges})
    records = []
    for index, name in enumerate(names, start=1):
        inbound = tuple(b.bridge_id for b in bridges if b.target_authority == name)
        outbound = tuple(b.bridge_id for b in bridges if b.source_authority == name)
        bridge_states = [b.certification_state for b in bridges if b.bridge_id in inbound + outbound]
        if bridge_states and all(state in {BridgeCertificationState.CERTIFIED_PRODUCTION, BridgeCertificationState.CONDITIONALLY_PRODUCTION} for state in bridge_states):
            status = BridgeCertificationState.CONDITIONALLY_PRODUCTION if BridgeCertificationState.CONDITIONALLY_PRODUCTION in bridge_states else BridgeCertificationState.CERTIFIED_PRODUCTION
        elif bridge_states:
            status = BridgeCertificationState.PARTIAL
        else:
            status = BridgeCertificationState.MISSING
        records.append(
            OfficeInventoryRecord(
                office_id=f"OFFICE-EO-DB-{index:03d}",
                office_name=name,
                constitutional_purpose=f"{name} bridge authority and handoff participant.",
                inbound_bridges=inbound,
                outbound_bridges=outbound,
                command_interfaces=tuple(b.command_or_event_type for b in bridges if b.source_authority == name),
                event_interfaces=tuple(b.command_or_event_type for b in bridges if b.target_authority == name),
                token_requirements="explicit where bridge crosses workflow ownership; read-only where observational",
                persistence_state="declared per bridge registry",
                recovery_state="declared per bridge registry",
                runtime_registration="CanonicalEnterpriseRuntime or compatibility facade classification",
                paper_mode_reachability="required",
                proof_only_reachability="not counted as production",
                test_only_reachability="not counted as production",
                current_status=status,
            )
        )
    return tuple(records)


def static_call_graph(root: str | Path) -> tuple[StaticCallEdge, ...]:
    root = Path(root)
    if not root.exists():
        return ()
    edges: list[StaticCallEdge] = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    edges.append(StaticCallEdge(str(path), node.lineno, "import", module, alias.name))
            elif isinstance(node, ast.Call):
                target = _call_name(node.func)
                if target:
                    edges.append(StaticCallEdge(str(path), node.lineno, "call", "", target))
    return tuple(edges)


def _bridge(
    bridge_id: str,
    name: str,
    source_authority: str,
    target_authority: str,
    source_symbol: str,
    target_symbol: str,
    trigger: str,
    payload_schema: str,
    command_or_event_type: str,
    runtime_modes: tuple[str, ...],
    truth_domains: tuple[str, ...],
    token_rule: str,
    eodc: str,
    eodd: str,
    state: BridgeCertificationState,
    implementation_files: tuple[str, ...],
    test_references: tuple[str, ...],
    limitations: tuple[str, ...] = (),
) -> RuntimeBridgeDefinition:
    return RuntimeBridgeDefinition(
        bridge_id=bridge_id,
        name=name,
        source_authority=source_authority,
        target_authority=target_authority,
        source_symbol=source_symbol,
        target_symbol=target_symbol,
        trigger=trigger,
        payload_schema=payload_schema,
        command_or_event_type=command_or_event_type,
        runtime_modes=runtime_modes,
        truth_domains=truth_domains,
        required_workflow_token_state=token_rule,
        source_preconditions=("source exists", "source authority registered"),
        target_preconditions=("target exists", "target authority registered"),
        authority_validation="EO-DA authority registry plus bridge source/target declaration",
        eodc_promotion_requirement=eodc,
        eodd_transaction_requirement=eodd,
        persistence_behavior="declared handoff state must be durable or reconstructable",
        recovery_behavior="restart must not duplicate mission, workflow, order, fill, position, truth, historian, or enrollment",
        retry_behavior="idempotent by declared idempotency key",
        idempotency_key=f"{bridge_id}:payload_identity",
        timeout_behavior="bounded retry then Commander-visible failure",
        failure_classification=(BridgeFindingClass.PARTIAL_BRIDGE if state == BridgeCertificationState.PARTIAL else BridgeFindingClass.UNKNOWN,),
        commander_visibility="visible through EO-DB Commander read model",
        test_references=test_references,
        implementation_files=implementation_files,
        certification_state=state,
        dynamic_reachability="canonical runtime trace required for certified production; otherwise classified with limitation",
        limitations=limitations,
    )


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _enclosing_symbol(tree: ast.AST, line_number: int) -> str:
    best = ""
    best_line = -1
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.lineno <= line_number and node.lineno > best_line:
            best = node.name
            best_line = node.lineno
    return best


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
