"""Canonical Series C runtime composition for ARGOS OR-005 Part 1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import utc_timestamp
from argos.foundation.persistence import InMemoryPersistenceRepository, canonical_schemas
from argos.foundation.prompts import PromptRepository
from argos.trader import DeterministicPaperBrokerage, OrderManagementOffice, PaperBrokerAccount
from argos.trader.execution_quality import ExecutionQualityOffice
from argos.trader.paper_brokerage import PaperBrokerMarketDataAdapter

from .api_execution_gateway import ApiExecutionGateway, ApiExecutionRequest, RealApiPilotConfig
from .canonical_bridge_fabric import CanonicalBridgeExecutor, make_bridge_request
from .closed_position_truth import ClosedPositionTruthBuilder
from .enterprise_communications_bus import EnterpriseCommunicationsBus
from .enterprise_cost_governor import EnterpriseCostGovernor, ReservationState
from .enterprise_doctrine_policy_manager import EnterpriseDoctrinePolicyManager
from .enterprise_efficiency_analytics import EnterpriseEfficiencyAnalytics
from .enterprise_memory_cache import EnterpriseMemoryCache
from .enterprise_priority_engine import EnterprisePriorityEngine
from .event_detection_engine import EventDetectionEngine
from .information_freshness_engine import InformationFreshnessEngine
from .market_data_provider import MarketDataProviderAbstractionLayer
from .mission_planner import EnterpriseMissionPlanner, MissionPlanStatus
from .office_duty_officer import OfficeDutyOfficerRegistry, OfficeTaskingRequest
from .office_lifecycle import OfficeActivationAuthority, OfficeLifecycleController
from .performance_truth_engine import PerformanceTruthEngine
from .position_lifecycle_manager import EnterprisePositionLifecycleManager
from .position_monitoring_network import PositionMonitoringNetwork
from .scheduler import EnterpriseOperatingMode, EnterpriseOperationsScheduler
from .strategic_intelligence_command import StrategicIntelligenceCommand
from .truth_domain import RuntimeMode
from .workflow_delta_engine import WorkflowDeltaEngine
from .workflow_orchestrator import EnterpriseWorkflowOrchestrator, WorkflowStatus


class CanonicalRuntimeMode(str, Enum):
    STOPPED = "stopped"
    INITIALIZING = "initializing"
    RECOVERING = "recovering"
    READY = "ready"
    PAPER_IDLE = "paper_idle"
    PAPER_ACTIVE = "paper_active"
    PAPER_DEGRADED = "paper_degraded"
    HALTING = "halting"
    HALTED = "halted"
    FAULTED = "faulted"
    PROOF = "proof"
    SIMULATION = "simulation"
    LIVE_DISABLED = "live_disabled"


@dataclass(frozen=True)
class RuntimeFailure:
    code: str
    component: str
    severity: str
    recoverable: bool
    explanation: str
    recommended_remediation: str
    timestamp_utc: str
    mission_id: str = ""
    workflow_id: str = ""


class CanonicalRuntimeError(RuntimeError):
    """Raised when canonical runtime startup or admission fails closed."""

    def __init__(self, failure: RuntimeFailure) -> None:
        super().__init__(f"{failure.code}: {failure.explanation}")
        self.failure = failure


@dataclass(frozen=True)
class RuntimeAdmissionRecord:
    admission_id: str
    timestamp_utc: str
    trigger_type: str
    subject_id: str
    scheduler_mission_id: str
    mission_plan_id: str
    priority_snapshot_id: str
    workflow_id: str
    workflow_token_id: str
    duty_decisions: tuple[dict[str, Any], ...]
    cost_reservation_id: str
    status: str
    explanation: str


@dataclass(frozen=True)
class StatefulAuthorityDiagnostic:
    authority: str
    runtime_attribute: str
    implementation: str
    identity: int
    duplicate: bool
    construction_site: str


@dataclass(frozen=True)
class SeriesCComponentInventoryItem:
    eo_id: str
    title: str
    implementation: str
    canonical_class: str
    runtime_attribute: str
    authority: str
    state_owner: bool
    truth_domain: str
    status: str
    or005_action: str


@dataclass
class CanonicalEnterpriseComponents:
    scheduler: EnterpriseOperationsScheduler
    mission_planner: EnterpriseMissionPlanner
    duty_officers: OfficeDutyOfficerRegistry
    event_detection: EventDetectionEngine
    workflow_orchestrator: EnterpriseWorkflowOrchestrator
    communications_bus: EnterpriseCommunicationsBus
    cost_governor: EnterpriseCostGovernor
    api_gateway: ApiExecutionGateway
    freshness_engine: InformationFreshnessEngine
    memory_cache: EnterpriseMemoryCache
    workflow_delta: WorkflowDeltaEngine
    priority_engine: EnterprisePriorityEngine
    doctrine_policy: EnterpriseDoctrinePolicyManager
    efficiency_analytics: EnterpriseEfficiencyAnalytics
    strategic_intelligence: StrategicIntelligenceCommand
    market_data: MarketDataProviderAbstractionLayer
    paper_broker: DeterministicPaperBrokerage
    performance_truth: PerformanceTruthEngine
    position_monitoring: PositionMonitoringNetwork
    position_lifecycle: EnterprisePositionLifecycleManager
    closed_position_truth: ClosedPositionTruthBuilder


class CanonicalEnterpriseRuntime:
    """Single explicit composition root for the paper Series C runtime."""

    def __init__(
        self,
        *,
        requested_mode: CanonicalRuntimeMode = CanonicalRuntimeMode.PAPER_IDLE,
        live_trading_enabled: bool = False,
        components: CanonicalEnterpriseComponents | None = None,
    ) -> None:
        self.requested_mode = requested_mode
        self.live_trading_enabled = live_trading_enabled
        self.mode = CanonicalRuntimeMode.STOPPED
        self.components = components or self._build_components()
        self._authority_construction_sites = MappingProxyType(
            {
                "workflow_orchestrator": "CanonicalEnterpriseRuntime._build_components",
                "scheduler": "CanonicalEnterpriseRuntime._build_components",
                "mission_planner": "CanonicalEnterpriseRuntime._build_components",
                "duty_officers": "EnterpriseOperationsScheduler.duty_officers",
                "communications_bus": "CanonicalEnterpriseRuntime._build_components",
                "paper_broker": "CanonicalEnterpriseRuntime._build_components",
                "performance_truth": "CanonicalEnterpriseRuntime._build_components",
                "position_monitoring": "CanonicalEnterpriseRuntime._build_components",
                "doctrine_policy": "CanonicalEnterpriseRuntime._build_components",
                "position_lifecycle": "CanonicalEnterpriseRuntime._build_components",
            }
        )
        self._loop_started = False
        self._start_count = 0
        self._halt_count = 0
        self._failures: list[RuntimeFailure] = []
        self._admissions: list[RuntimeAdmissionRecord] = []
        self._strategic_mandates: dict[str, dict[str, Any]] = {}
        self.bridge_executor = CanonicalBridgeExecutor(runtime_instance_id="ARGOS-CANONICAL-RUNTIME")
        self.office_lifecycle = OfficeLifecycleController(bridge_executor=self.bridge_executor)

    @staticmethod
    def _build_components() -> CanonicalEnterpriseComponents:
        scheduler = EnterpriseOperationsScheduler()
        mission_planner = EnterpriseMissionPlanner()
        duty_officers = scheduler.duty_officers
        event_detection = EventDetectionEngine()
        workflow_orchestrator = EnterpriseWorkflowOrchestrator()
        communications_bus = EnterpriseCommunicationsBus()
        cost_governor = EnterpriseCostGovernor()
        freshness_engine = InformationFreshnessEngine()
        memory_cache = EnterpriseMemoryCache(freshness_engine)
        workflow_delta = WorkflowDeltaEngine(freshness_engine, memory_cache)
        priority_engine = EnterprisePriorityEngine()
        doctrine_policy = EnterpriseDoctrinePolicyManager()
        efficiency_analytics = EnterpriseEfficiencyAnalytics()
        strategic_intelligence = StrategicIntelligenceCommand()
        market_data = MarketDataProviderAbstractionLayer()
        performance_truth = PerformanceTruthEngine()
        position_monitoring = PositionMonitoringNetwork()
        closed_position_truth = ClosedPositionTruthBuilder()
        audit = AuditService()
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        config = ConfigurationService.load(
            {
                "environment": "development",
                "config_version": "1.0.0",
                "schema_version": "1.0.0",
                "log_level": "INFO",
                "live_trading_enabled": False,
                "feature_flags": {},
                "secret_references": [],
            },
            {},
        )
        prompt_repository = PromptRepository()
        order_management = OrderManagementOffice(config, persistence, audit, prompt_repository)
        execution_quality = ExecutionQualityOffice(config, persistence, audit, prompt_repository)
        paper_broker = DeterministicPaperBrokerage(
            order_management=order_management,
            execution_quality=execution_quality,
            performance_truth=performance_truth,
            communications_bus=communications_bus,
            position_monitoring=position_monitoring,
            market_data=PaperBrokerMarketDataAdapter(market_data),
            account=PaperBrokerAccount("ACCT-PAPER-001", 100000.0, 0.0, 100000.0),
        )
        position_lifecycle = EnterprisePositionLifecycleManager(
            performance_truth=performance_truth,
            paper_broker=paper_broker,
            market_data_provider=market_data,
            monitoring_network=position_monitoring,
            closed_truth_builder=closed_position_truth,
            communications_bus=communications_bus,
        )
        api_gateway = ApiExecutionGateway(
            workflow_snapshot=workflow_orchestrator.snapshot,
            authorize_credit=lambda request: _gateway_credit_authorization(workflow_orchestrator, request),
            complete_credit_activation=lambda activation_id: {"activationId": activation_id, "status": "COMPLETED"},
            authorize_cost=cost_governor.authorize_gateway_request,
            record_cost_usage=cost_governor.record_gateway_usage,
            real_api_config=RealApiPilotConfig(enabled=False),
        )
        return CanonicalEnterpriseComponents(
            scheduler=scheduler,
            mission_planner=mission_planner,
            duty_officers=duty_officers,
            event_detection=event_detection,
            workflow_orchestrator=workflow_orchestrator,
            communications_bus=communications_bus,
            cost_governor=cost_governor,
            api_gateway=api_gateway,
            freshness_engine=freshness_engine,
            memory_cache=memory_cache,
            workflow_delta=workflow_delta,
            priority_engine=priority_engine,
            doctrine_policy=doctrine_policy,
            efficiency_analytics=efficiency_analytics,
            strategic_intelligence=strategic_intelligence,
            market_data=market_data,
            paper_broker=paper_broker,
            performance_truth=performance_truth,
            position_monitoring=position_monitoring,
            position_lifecycle=position_lifecycle,
            closed_position_truth=closed_position_truth,
        )

    def start(self) -> dict[str, Any]:
        if self._loop_started:
            return self.runtime_status()
        self.mode = CanonicalRuntimeMode.INITIALIZING
        self._validate_startup()
        self.components.scheduler.set_enabled(True, actor="CanonicalEnterpriseRuntime", reason="OR-005 canonical paper runtime startup.")
        self.components.scheduler.set_mode(EnterpriseOperatingMode.FULL_PAPER_TRADING.value, actor="CanonicalEnterpriseRuntime", reason="Paper startup begins idle; work requires mission admission.")
        self.mode = CanonicalRuntimeMode.PAPER_IDLE
        self._loop_started = True
        self._start_count += 1
        return self.runtime_status()

    def halt(self, *, reason: str = "Commander or runtime halt requested.") -> dict[str, Any]:
        if self.mode == CanonicalRuntimeMode.HALTED and not self._loop_started:
            return self.runtime_status()
        self.mode = CanonicalRuntimeMode.HALTING
        self.components.scheduler.set_mode(EnterpriseOperatingMode.HALTED.value, actor="CanonicalEnterpriseRuntime", reason=reason)
        self._loop_started = False
        self._halt_count += 1
        self.mode = CanonicalRuntimeMode.HALTED
        return self.runtime_status()

    def admit_scheduled_obligation(self, template_id: str, *, now: str | None = None) -> RuntimeAdmissionRecord:
        self._require_started()
        mission = self.components.scheduler.create_scheduled_mission(template_id, now=now)
        plan_snapshot = self.components.mission_planner.plan_scheduled_obligation(asdict(mission), submit_to_scheduler=False)
        plan = _latest_plan(plan_snapshot)
        cost = self.components.cost_governor.request_reservation_from_plan(plan, mission_id=mission.mission_id)
        priority = self.components.priority_engine.evaluate(
            {
                "enterpriseOperationsScheduler": self.components.scheduler.snapshot(),
                "enterpriseMissionPlanner": self.components.mission_planner.snapshot(),
                "enterpriseCostGovernor": self.components.cost_governor.snapshot(),
                "eventDetectionEngine": self.components.event_detection.snapshot(),
                "informationFreshnessEngine": self.components.freshness_engine.snapshot(),
                "enterpriseMemoryCache": self.components.memory_cache.snapshot(),
                "workflowDeltaEngine": self.components.workflow_delta.snapshot(),
            }
        )
        first_stage = _first_stage(plan)
        workflow = self.components.workflow_orchestrator.create_validate_queue_assign(
            name=mission.mission_name,
            stages=(first_stage,),
            runtime_budget=mission.maximum_runtime_seconds,
            credit_budget=mission.maximum_api_cost,
            expected_output_schema=("mission_result", "audit_reference"),
            workflow_type=mission.workflow_type,
            initial_stage=mission.workflow_type,
        )
        dispatched = self.components.scheduler.dispatch_mission(mission.mission_id, workflow_id=workflow.workflow_id, token_id=workflow.token.audit_identifier)
        self.bridge_executor.ownership.establish(workflow.workflow_id, "Workflow Orchestrator", workflow.token.audit_identifier)
        bridge_payload = {"mission_id": mission.mission_id, "workflow_id": workflow.workflow_id, "template_id": template_id}
        self.bridge_executor.execute(
            make_bridge_request(
                bridge_id="BRIDGE-WORKFLOW-OFFICE-001",
                runtime_instance_id=self.bridge_executor.runtime_instance_id,
                workflow_id=workflow.workflow_id,
                source="Workflow Orchestrator",
                destination=first_stage,
                artifact_id=workflow.workflow_id,
                payload=bridge_payload,
                current_owner="Workflow Orchestrator",
                next_owner=first_stage,
                token_id=workflow.token.audit_identifier,
            )
        )
        self.office_lifecycle.activate(first_stage, authority=OfficeActivationAuthority.CANONICAL_BRIDGE, workflow_id=workflow.workflow_id, token_id=workflow.token.audit_identifier, current_owner=first_stage, proof_domain=RuntimeMode.PAPER.value)
        duty_decisions = self._duty_decisions_for(dispatched, workflow)
        record = RuntimeAdmissionRecord(
            admission_id=f"OR005-ADM-{len(self._admissions) + 1:06d}",
            timestamp_utc=utc_timestamp(),
            trigger_type="scheduled_obligation",
            subject_id=template_id,
            scheduler_mission_id=mission.mission_id,
            mission_plan_id=plan.get("mission_plan_id", ""),
            priority_snapshot_id=(priority.get("latestQueueSnapshot") or {}).get("queue_snapshot_id", ""),
            workflow_id=workflow.workflow_id,
            workflow_token_id=workflow.token.audit_identifier,
            duty_decisions=tuple(duty_decisions),
            cost_reservation_id=getattr(cost, "reservation_id", ""),
            status="ADMITTED" if dispatched.status == "Running" else "DEFERRED",
            explanation="Scheduler, Mission Planner, Cost Governor, Priority Engine, Workflow Token, and Duty Officer admission path completed.",
        )
        self._admissions.append(record)
        self.mode = CanonicalRuntimeMode.PAPER_ACTIVE if record.status == "ADMITTED" else CanonicalRuntimeMode.PAPER_DEGRADED
        return record

    def request_seeker_work(self, *, mandate_id: str, mission_id: str = "", workflow_id: str = "") -> dict[str, Any]:
        self._require_started()
        mandate = self._strategic_mandates.get(mandate_id)
        if not mandate:
            failure = self._failure("MISSING_STRATEGIC_MANDATE", "Seeker", "Seeker work requires a Strategic Intelligence mandate.")
            return {"accepted": False, "failure": asdict(failure)}
        if mandate.get("decision") == "avoid" or mandate.get("expires_at", "9999") < utc_timestamp():
            failure = self._failure("STRATEGIC_MANDATE_NOT_ACTIONABLE", "Seeker", "Strategic Intelligence mandate forbids or has expired for this work.")
            return {"accepted": False, "failure": asdict(failure)}
        return {"accepted": True, "mandate": mandate, "mission_id": mission_id, "workflow_id": workflow_id}

    def create_strategic_mandate(self, *, subject: str, decision: str = "allow", expires_at: str = "9999-12-31T23:59:59Z") -> dict[str, Any]:
        self._require_started()
        if decision not in {"allow", "avoid", "no_search"}:
            raise ValueError("strategic mandate decision must be allow, avoid, or no_search")
        snapshot = self.components.strategic_intelligence.snapshot(timestamp_utc=utc_timestamp(), sources={})
        mandate = {
            "mandate_id": f"SIC-MANDATE-{len(self._strategic_mandates) + 1:06d}",
            "subject": subject,
            "decision": decision,
            "expires_at": expires_at,
            "source_report_ids": tuple(item.get("report_id", "") for item in snapshot.get("latestStrategicReports", ())),
            "runtime_authored": False,
            "authority": "Strategic Intelligence Command",
        }
        self._strategic_mandates[mandate["mandate_id"]] = mandate
        return mandate

    def execute_api_request(self, request: ApiExecutionRequest) -> dict[str, Any]:
        self._require_started()
        if not getattr(request, "cost_reservation_id", ""):
            failure = self._failure("COST_RESERVATION_REQUIRED", "API Execution Gateway", "Certified paper runtime rejects unreserved API execution.")
            return {"allowed": False, "blocked": True, "failure": asdict(failure)}
        response = self.components.api_gateway.execute_model_request(request)
        return asdict(response)

    def read_only_snapshot(self) -> dict[str, Any]:
        """Pure observation state that avoids component snapshot calls with side effects."""
        workflow = self.components.workflow_orchestrator.snapshot()
        return {
            "mode": self.mode.value,
            "truthDomain": RuntimeMode.PAPER.value if self.mode in {CanonicalRuntimeMode.PAPER_IDLE, CanonicalRuntimeMode.PAPER_ACTIVE, CanonicalRuntimeMode.PAPER_DEGRADED} else self.mode.value.upper(),
            "loopStarted": self._loop_started,
            "startCount": self._start_count,
            "haltCount": self._halt_count,
            "componentIds": self.component_identity(),
            "statefulAuthorityDiagnostics": tuple(asdict(item) for item in self.stateful_authority_diagnostics()),
            "workflowCounts": workflow["metrics"],
            "missionAdmissionCount": len(self._admissions),
            "failureCount": len(self._failures),
            "paperBrokerOrderCount": sum(len(items) for items in self.components.paper_broker.order_book.snapshot().values()),
            "positionCount": len(self.components.performance_truth.position_registry.active_positions()),
            "bridgeFabric": self.bridge_executor.snapshot(),
            "officeLifecycle": self.office_lifecycle.read_only_snapshot(),
        }

    def enterprise_persistence_snapshot(self) -> dict[str, Any]:
        """Return authoritative and checkpointable state for OR-006 persistence."""
        return {
            "runtime": {
                "mode": self.mode.value,
                "requested_mode": self.requested_mode.value,
                "live_trading_enabled": self.live_trading_enabled,
                "loop_started": self._loop_started,
                "start_count": self._start_count,
                "halt_count": self._halt_count,
                "failures": tuple(asdict(item) for item in self._failures),
                "admissions": tuple(asdict(item) for item in self._admissions),
                "strategic_mandates": tuple(self._strategic_mandates.values()),
            },
            "missions": {
                "scheduler": self.components.scheduler.snapshot(),
                "mission_planner": self.components.mission_planner.snapshot(),
                "duty_officers": self.components.duty_officers.snapshot(self.components.scheduler.snapshot()),
            },
            "workflows": self.components.workflow_orchestrator.snapshot(),
            "broker": {
                "account": asdict(self.components.paper_broker.account),
                "order_book": self.components.paper_broker.order_book.snapshot(),
                "authority": "DeterministicPaperBrokerage",
            },
            "positions": self.components.performance_truth.position_registry.snapshot(),
            "performance_truth": self.components.performance_truth.snapshot(execution_environment="paper"),
            "policy": self.components.doctrine_policy.snapshot(),
        }

    def restore_enterprise_persistence_snapshot(self, payload: dict[str, Any]) -> None:
        """Restore runtime-owned continuity state after authoritative components recover."""
        self.mode = CanonicalRuntimeMode(payload.get("mode", CanonicalRuntimeMode.STOPPED.value))
        self.requested_mode = CanonicalRuntimeMode(payload.get("requested_mode", self.requested_mode.value))
        self.live_trading_enabled = bool(payload.get("live_trading_enabled", False))
        self._loop_started = bool(payload.get("loop_started", False))
        self._start_count = int(payload.get("start_count", 0) or 0)
        self._halt_count = int(payload.get("halt_count", 0) or 0)
        self._failures = tuple(RuntimeFailure(**item) for item in payload.get("failures", ()))  # type: ignore[assignment]
        self._failures = list(self._failures)
        self._admissions = tuple(RuntimeAdmissionRecord(**item) for item in payload.get("admissions", ()))  # type: ignore[assignment]
        self._admissions = list(self._admissions)
        self._strategic_mandates = {str(item.get("mandate_id", "")): dict(item) for item in payload.get("strategic_mandates", ()) if item.get("mandate_id")}

    def read_only_digest(self) -> str:
        return _stable_hash(self.read_only_snapshot())

    def runtime_status(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "requestedMode": self.requested_mode.value,
            "liveTradingEnabled": self.live_trading_enabled,
            "loopStarted": self._loop_started,
            "startCount": self._start_count,
            "haltCount": self._halt_count,
            "failures": tuple(asdict(item) for item in self._failures),
            "authority": {
                "runtimeMakesFinancialDecisions": False,
                "runtimeCreatesBrokerFills": False,
                "runtimeMutatesPositions": False,
                "brokerAuthority": "DeterministicPaperBrokerage",
                "positionAuthority": "PositionRegistry via PerformanceTruth and EnterprisePositionLifecycleManager",
                "performanceTruthCreatesOutcomes": False,
            },
        }

    def component_identity(self) -> dict[str, int]:
        return {name: id(value) for name, value in self.components.__dict__.items()}

    def stateful_authority_diagnostics(self) -> tuple[StatefulAuthorityDiagnostic, ...]:
        identities = self.component_identity()
        reverse: dict[int, list[str]] = {}
        for name, identity in identities.items():
            reverse.setdefault(identity, []).append(name)
        diagnostics = []
        for name in self._authority_construction_sites:
            identity = identities.get(name, 0)
            aliases = set(reverse.get(identity, ()))
            duplicate = len(aliases) > 1 and aliases != {"scheduler", "duty_officers"}
            value = getattr(self.components, name)
            diagnostics.append(
                StatefulAuthorityDiagnostic(
                    authority=name,
                    runtime_attribute=name,
                    implementation=value.__class__.__name__,
                    identity=identity,
                    duplicate=duplicate,
                    construction_site=self._authority_construction_sites[name],
                )
            )
        return tuple(diagnostics)

    def stateful_authority_duplicates(self) -> tuple[str, ...]:
        identities = self.component_identity()
        reverse: dict[int, list[str]] = {}
        for name, identity in identities.items():
            reverse.setdefault(identity, []).append(name)
        return tuple(",".join(names) for names in reverse.values() if len(names) > 1 and set(names) != {"scheduler", "duty_officers"})

    def series_c_inventory(self) -> tuple[SeriesCComponentInventoryItem, ...]:
        return SERIES_C_INVENTORY

    def _validate_startup(self) -> None:
        if self.live_trading_enabled or self.requested_mode == CanonicalRuntimeMode.LIVE_DISABLED:
            self.mode = CanonicalRuntimeMode.LIVE_DISABLED
            self._raise_failure("LIVE_TRADING_DISABLED", "CanonicalEnterpriseRuntime", "Live trading remains disabled under OR-005.")
        required = {
            "scheduler": self.components.scheduler,
            "mission_planner": self.components.mission_planner,
            "duty_officers": self.components.duty_officers,
            "event_detection": self.components.event_detection,
            "workflow_orchestrator": self.components.workflow_orchestrator,
            "communications_bus": self.components.communications_bus,
            "cost_governor": self.components.cost_governor,
            "api_gateway": self.components.api_gateway,
            "freshness_engine": self.components.freshness_engine,
            "memory_cache": self.components.memory_cache,
            "workflow_delta": self.components.workflow_delta,
            "priority_engine": self.components.priority_engine,
            "paper_broker": self.components.paper_broker,
            "performance_truth": self.components.performance_truth,
            "position_lifecycle": self.components.position_lifecycle,
        }
        missing = [name for name, component in required.items() if component is None]
        if missing:
            self._raise_failure("MISSING_CRITICAL_DEPENDENCY", ",".join(missing), "Canonical runtime critical dependency missing.")
        duplicates = self.stateful_authority_duplicates()
        if duplicates:
            self._raise_failure("DUPLICATE_STATEFUL_AUTHORITY", "CanonicalEnterpriseRuntime", f"Duplicate component authority detected: {duplicates}.")
        from .constitutional_invariants import ConstitutionalInvariantEngine

        invariant_sweep = ConstitutionalInvariantEngine().evaluate_startup(self)
        if invariant_sweep.verdict == "FAIL":
            self._raise_failure("CONSTITUTIONAL_INVARIANT_STARTUP_FAILURE", "ConstitutionalInvariantEngine", f"EO-DA startup invariant failure: {invariant_sweep.blocking_count} blocking findings.")

    def _duty_decisions_for(self, mission: Any, workflow: Any) -> list[dict[str, Any]]:
        eos_snapshot = self.components.scheduler.snapshot()
        decisions: list[dict[str, Any]] = []
        for office in mission.required_offices:
            request = OfficeTaskingRequest(
                request_id=f"OR005-ODO-{len(decisions) + 1:06d}",
                created_at=utc_timestamp(),
                source_office_id="EnterpriseOperationsScheduler",
                target_office_id=_canonical_office_id(office),
                mission_id=mission.mission_id,
                workflow_id=workflow.workflow_id,
                decision_object_id="",
                execution_token_id=workflow.token.audit_identifier,
                request_type=_request_type_for_office(office),
                task_description=mission.description,
                priority=mission.priority,
                criticality=mission.criticality,
                deadline="",
                event_reference=mission.trigger_reference,
                commander_directive_id=mission.commander_directive_id,
                required_output="mission_result",
                input_artifacts=("mission_record", "workflow_token"),
                freshness_requirement=mission.minimum_data_freshness,
                estimated_value=75.0,
                estimated_cost=max(0.0, mission.maximum_api_cost / max(1, len(mission.required_offices))),
                deduplication_key=f"{mission.mission_id}:{office}",
                routing_history=(),
                authorization_context={"schedulerMissionStatus": mission.status},
                status="Received",
                audit_reference=f"OR005-ODO-AUDIT-{len(decisions) + 1:06d}",
            )
            decisions.append(asdict(self.components.duty_officers.submit_request(request, eos_snapshot)))
        return decisions

    def _require_started(self) -> None:
        if not self._loop_started:
            self._raise_failure("RUNTIME_NOT_STARTED", "CanonicalEnterpriseRuntime", "Runtime admission requires a started canonical paper runtime.")

    def _failure(self, code: str, component: str, explanation: str, *, recoverable: bool = True) -> RuntimeFailure:
        failure = RuntimeFailure(code, component, "HIGH", recoverable, explanation, "Correct the authoritative prerequisite and retry through the canonical runtime.", utc_timestamp())
        self._failures.append(failure)
        return failure

    def _raise_failure(self, code: str, component: str, explanation: str) -> None:
        failure = self._failure(code, component, explanation, recoverable=False)
        self.mode = CanonicalRuntimeMode.FAULTED if code != "LIVE_TRADING_DISABLED" else CanonicalRuntimeMode.LIVE_DISABLED
        raise CanonicalRuntimeError(failure)


def _gateway_credit_authorization(orchestrator: EnterpriseWorkflowOrchestrator, request: ApiExecutionRequest) -> dict[str, Any]:
    valid, code, reason = orchestrator.validate_api_usage(request.workflow_id, request.workflow_token_id, request.requesting_office, request.max_cost_usd)
    status = "APPROVED" if valid else "REJECTED"
    return {
        "creditGovernor": {
            "activations": (
                {
                    "activation_id": f"OR005-CREDIT-{request.audit_identifier or 'REQUEST'}",
                    "status": status,
                    "law_vii_validation": "" if valid else code,
                    "reason": "Workflow token owner authorized." if valid else reason,
                },
            )
        }
    }


def _latest_plan(snapshot: dict[str, Any]) -> dict[str, Any]:
    plans = tuple(snapshot.get("allMissionPlans", ()))
    if not plans:
        return {}
    ready = tuple(item for item in plans if item.get("status") in {MissionPlanStatus.READY_FOR_SUBMISSION.value, MissionPlanStatus.SUBMITTED.value})
    return (ready or plans)[-1]


def _first_stage(plan: dict[str, Any]) -> str:
    assignments = tuple(plan.get("office_assignments", ()) or ())
    if not assignments:
        return "Executive"
    first = assignments[0]
    if isinstance(first, dict):
        return str(first.get("office_id", "Executive") or "Executive")
    return str(getattr(first, "office_id", "Executive") or "Executive")


def _canonical_office_id(office: str) -> str:
    value = str(office)
    if "Position" in value or "Trader" in value or "Broker" in value:
        return "Trader"
    if "Risk" in value:
        return "Risk"
    if "Strategic" in value:
        return "Strategic Intelligence"
    if "Historian" in value:
        return "Historian"
    if "Librarian" in value:
        return "Librarian"
    if "Commander" in value or "Executive" in value:
        return "Executive"
    if "Analyst" in value:
        return "Analyst"
    if "Seeker" in value:
        return "Seeker"
    return value


def _request_type_for_office(office: str) -> str:
    office_id = _canonical_office_id(office)
    return {
        "Executive": "briefing_request",
        "Seeker": "market_discovery",
        "Analyst": "candidate_analysis",
        "Strategic Intelligence": "strategic_theme_review",
        "Risk": "risk_review",
        "Trader": "broker_reconciliation",
        "Historian": "archive_request",
        "Librarian": "knowledge_retrieval",
        "Academy": "training_request",
    }.get(office_id, "general_review")


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


SERIES_C_INVENTORY: tuple[SeriesCComponentInventoryItem, ...] = (
    SeriesCComponentInventoryItem("EO-CA", "Enterprise Operations Scheduler", "src/argos/control_panel/scheduler.py", "EnterpriseOperationsScheduler", "scheduler", "Owns scheduled obligation eligibility and mission dispatch.", True, "paper/control", "active_canonical_part1", "retain_connect"),
    SeriesCComponentInventoryItem("EO-CB", "Office Duty Officer", "src/argos/control_panel/office_duty_officer.py", "OfficeDutyOfficerRegistry", "duty_officers", "Owns office wake eligibility and suppression.", True, "paper/control", "active_canonical_part1", "retain_connect"),
    SeriesCComponentInventoryItem("EO-CC", "Event Detection Engine", "src/argos/control_panel/event_detection_engine.py", "EventDetectionEngine", "event_detection", "Owns deterministic event recognition.", True, "paper/control", "active_canonical_part1", "retain_connect"),
    SeriesCComponentInventoryItem("EO-CD", "Enterprise Mission Planner", "src/argos/control_panel/mission_planner.py", "EnterpriseMissionPlanner", "mission_planner", "Owns bounded mission plan creation.", True, "paper/control", "active_canonical_part1", "retain_connect"),
    SeriesCComponentInventoryItem("EO-CE", "Enterprise Cost Governor", "src/argos/control_panel/enterprise_cost_governor.py", "EnterpriseCostGovernor", "cost_governor", "Owns cost reservation and gateway authorization.", True, "paper/control", "active_canonical_part1", "retain_connect"),
    SeriesCComponentInventoryItem("EO-CF", "Information Freshness Engine", "src/argos/control_panel/information_freshness_engine.py", "InformationFreshnessEngine", "freshness_engine", "Owns freshness decisions.", True, "paper/control", "active_canonical_part1", "retain_connect"),
    SeriesCComponentInventoryItem("EO-CG", "Enterprise Memory Cache", "src/argos/control_panel/enterprise_memory_cache.py", "EnterpriseMemoryCache", "memory_cache", "Owns cache admission and reuse records.", True, "paper/control", "active_canonical_part1", "retain_connect"),
    SeriesCComponentInventoryItem("EO-CH", "Workflow Delta Engine", "src/argos/control_panel/workflow_delta_engine.py", "WorkflowDeltaEngine", "workflow_delta", "Owns change impact and delta packages.", True, "paper/control", "active_canonical_part1", "retain_connect"),
    SeriesCComponentInventoryItem("EO-CI", "Office Wakefulness Manager", "src/argos/control_panel/office_duty_officer.py", "OfficeDutyOfficerRegistry", "duty_officers", "Capability found under EO-CB duty state and scheduler office state; no separate canonical module found.", False, "paper/control", "found_under_eo_cb_eo_ca", "alias_document_do_not_duplicate"),
    SeriesCComponentInventoryItem("EO-CJ", "Enterprise Priority Engine", "src/argos/control_panel/enterprise_priority_engine.py", "EnterprisePriorityEngine", "priority_engine", "Owns deterministic work ordering recommendations.", True, "paper/control", "active_canonical_part1", "retain_connect"),
    SeriesCComponentInventoryItem("EO-CK", "Position Monitoring Network", "src/argos/control_panel/position_monitoring_network.py", "PositionMonitoringNetwork", "position_monitoring", "Owns position observation events.", True, "paper/control", "active_canonical_part1", "retain_connect"),
    SeriesCComponentInventoryItem("EO-CL", "Enterprise Communications Bus", "src/argos/control_panel/enterprise_communications_bus.py", "EnterpriseCommunicationsBus", "communications_bus", "Owns enterprise message delivery/audit.", True, "paper/control", "active_canonical_part1", "retain_connect"),
    SeriesCComponentInventoryItem("EO-CM", "Commander Mission Generator", "src/argos/control_panel/commander_daily_review_workspace.py", "CommanderDailyReviewWorkspace", "commander_read_model", "No separate mission generator found; commander directives flow through Mission Planner and Scheduler.", False, "paper/control", "documented_gap_part2", "resolve_in_part2"),
    SeriesCComponentInventoryItem("EO-CN", "Enterprise Efficiency Analytics", "src/argos/control_panel/enterprise_efficiency_analytics.py", "EnterpriseEfficiencyAnalytics", "efficiency_analytics", "Owns runtime efficiency metrics and findings.", True, "paper/control", "active_canonical_part1", "retain_connect"),
    SeriesCComponentInventoryItem("EO-CO", "Enterprise Doctrine and Policy Manager", "src/argos/control_panel/enterprise_doctrine_policy_manager.py", "EnterpriseDoctrinePolicyManager", "doctrine_policy", "Owns doctrine and policy configuration; documentation now required by OR-005.", True, "paper/control", "active_canonical_part1", "retain_connect"),
)
