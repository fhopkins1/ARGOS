"""Runtime state for the local ARGOS Control Panel dashboard."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
import os
import threading
import time
from typing import Any

from argos.executive import (
    ARGOSControlPanel,
    HumanAuthority,
    HumanOverrideService,
    OverrideLevel,
    RealWorldTradingGate,
)
from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.persistence import InMemoryPersistenceRepository, canonical_schemas

from .api_execution_gateway import ApiExecutionGateway, ApiExecutionRequest, real_api_config_from_env
from .api_runtime_monitor import ApiRuntimeMonitor
from .command_console import CommandConsole
from .cnac import CommanderNotificationAlertCenter
from .credit_governor import EnterpriseCreditGovernor
from .cognitive_contract import PromptContractLibrary, build_prompt_contract_envelope, prompt_contract_trace
from .cognitive_pilot import ControlledCognitivePilot, ControlledCognitivePilotLimits
from .decision_laboratory import DecisionLaboratory
from .eab import EnterpriseActivityBus
from .ecc import EnterpriseCommandCenter
from .infrastructure import InfrastructureResourceManager
from .ioe import InteractiveOrganizationExplorer
from .lppc import LivePortfolioPerformanceConsole
from .performance_truth_engine import PerformanceTruthEngine
from .scheduler import OfficeScheduler
from .strategy_performance_console import LiveStrategyPerformanceConsole
from .workflow_orchestrator import EnterpriseWorkflowOrchestrator
from .workflow_runtime_monitor import WorkflowRuntimeMonitor


@dataclass(frozen=True)
class OperatingCostSnapshot:
    """Visible API credit and operating expense snapshot."""

    session_api_credits_usd: float
    today_api_credits_usd: float
    month_to_date_api_credits_usd: float
    projected_monthly_api_credits_usd: float
    other_operating_expenses_usd: float
    total_operating_burn_usd: float
    budget_limit_usd: float
    budget_status: str
    real_api_usage_usd: float
    simulated_paper_trading_telemetry_usd: float
    workflow_token_authorized_api_usage_usd: float


@dataclass(frozen=True)
class OfficeCommand:
    """Command routed to an ARGOS group or office."""

    command_id: str
    target: str
    action: str
    status: str
    timestamp_utc: str


class ControlPanelRuntime:
    """In-memory local dashboard runtime."""

    def __init__(self) -> None:
        self.audit = AuditService()
        self.persistence = InMemoryPersistenceRepository(canonical_schemas())
        self.override = HumanOverrideService(self.audit, self.persistence)
        self.config = ConfigurationService.load(
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
        self.control = ARGOSControlPanel(self.config, self.persistence, self.audit, self.override)
        self.eab = EnterpriseActivityBus(self.audit, self.persistence)
        self.command_console = CommandConsole()
        self.credit_governor = EnterpriseCreditGovernor()
        self.prompt_contract_library = PromptContractLibrary()
        self._real_api_config = real_api_config_from_env()
        self.controlled_cognitive_pilot = ControlledCognitivePilot(
            enabled=_env_bool("ARGOS_ENABLE_CONTROLLED_COGNITIVE_PILOT", self._real_api_config.enabled),
            limits=ControlledCognitivePilotLimits(
                maximum_session_workflows=max(1, int(_env_float("ARGOS_COGNITIVE_PILOT_MAX_WORKFLOWS", 10))),
                maximum_total_pilot_cost_usd=_env_float("ARGOS_COGNITIVE_PILOT_MAX_TOTAL_COST_USD", 0.05),
                maximum_workflow_cost_usd=_env_float("ARGOS_COGNITIVE_PILOT_MAX_WORKFLOW_COST_USD", 0.005),
                maximum_api_timeout_seconds=max(1, int(_env_float("ARGOS_COGNITIVE_PILOT_MAX_TIMEOUT_SECONDS", 20))),
                maximum_retries=max(0, int(_env_float("ARGOS_COGNITIVE_PILOT_MAX_RETRIES", 1))),
            ),
        )
        self.decision_laboratory = DecisionLaboratory()
        self.api_runtime_monitor = ApiRuntimeMonitor()
        self.cnac = CommanderNotificationAlertCenter()
        self.ecc = EnterpriseCommandCenter(self.audit, self.persistence)
        self.infrastructure = InfrastructureResourceManager()
        self.ioe = InteractiveOrganizationExplorer()
        self.lppc = LivePortfolioPerformanceConsole()
        self.performance_truth_engine = PerformanceTruthEngine()
        self.strategy_performance_console = LiveStrategyPerformanceConsole()
        self.scheduler = OfficeScheduler()
        self.workflow_orchestrator = EnterpriseWorkflowOrchestrator()
        self.workflow_runtime_monitor = WorkflowRuntimeMonitor()
        self.api_execution_gateway = ApiExecutionGateway(
            workflow_snapshot=self.workflow_orchestrator.snapshot,
            authorize_credit=self._authorize_gateway_credit,
            complete_credit_activation=self.complete_credit_activation,
            real_api_config=self._real_api_config,
            prompt_contract_library=self.prompt_contract_library,
        )
        self.authority = HumanAuthority("AUTH-001", "STF-001", OverrideLevel.LEVEL_6_EMERGENCY_LIQUIDATION)
        self._commands: list[OfficeCommand] = []
        self._activity: list[dict[str, str]] = []
        self._event_lock = threading.RLock()
        self._session_api_credits_usd = 0.0
        self._today_api_credits_usd = 0.0
        self._month_to_date_api_credits_usd = 0.0
        self._other_operating_expenses_usd = 42.75
        self._budget_limit_usd = 250.0
        self._self_training_ticks = 0
        self._workflow_api_usage_usd: dict[str, float] = {}
        self._workflow_lock = threading.RLock()
        self._workflow_demo_stage_delay_seconds = _env_float("ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS", 0.0)
        self._paper_runner_lock = threading.RLock()
        self._paper_runner_stop = threading.Event()
        self._paper_runner_pause_requested = threading.Event()
        self._paper_runner_step_requested = threading.Event()
        self._paper_runner_thread: threading.Thread | None = None
        self._paper_workflow_cycle_interval_seconds = max(0.05, _env_float("ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS", 0.1))
        self._enable_placeholder_credit_proof = _env_bool("ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF", True)
        self._paper_gateway_execution_recorded: set[str] = set()

    def state(self) -> dict[str, Any]:
        """Return complete dashboard state."""
        snapshot = self.control.visible_snapshot()
        costs = self._cost_snapshot()
        resources = {"cpu": 23, "memory": 41, "storage": 35, "network": 27}
        eab_snapshot = self.eab.snapshot()
        self.cnac.ingest(tuple(reversed(eab_snapshot["events"])))
        cnac_snapshot = self.cnac.snapshot()
        activity = tuple(eab_snapshot["feed"] or reversed(self._activity[-9:] or _default_activity()))
        commands = tuple(asdict(command) for command in reversed(self._commands[-20:]))
        scheduler_snapshot = self.scheduler.snapshot()
        infrastructure_snapshot = self.infrastructure.snapshot(
            timestamp_utc=_now(),
            resources=resources,
            costs=asdict(costs),
            scheduler=scheduler_snapshot,
            eab=eab_snapshot,
            organizations=_groups(),
            audit_event_count=len(self.audit.audit_log.events),
        )
        ecc_snapshot = self.ecc.snapshot(
            control=asdict(snapshot),
            resources=resources,
            activity=activity,
            commands=commands,
            costs=asdict(costs),
        )
        ioe_snapshot = self.ioe.snapshot(
            ecc=ecc_snapshot,
            eab=eab_snapshot,
            cnac=cnac_snapshot,
            scheduler=scheduler_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        lppc_snapshot = self.lppc.snapshot(
            timestamp_utc=_now(),
            control=asdict(snapshot),
            eab=eab_snapshot,
            risk_status="SYNCHRONIZED",
            historian_status="SYNCHRONIZED",
            broker_status="CONNECTED" if snapshot.real_world_trading_active else "PAPER_ONLY",
            audit_event_count=len(self.audit.audit_log.events),
        )
        credit_governor_snapshot = self.credit_governor.snapshot(
            timestamp_utc=_now(),
            scheduler=scheduler_snapshot,
            infrastructure=infrastructure_snapshot,
            eab=eab_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        api_runtime_snapshot = self.api_runtime_monitor.snapshot(
            timestamp_utc=_now(),
            costs=asdict(costs),
            credit_governor=credit_governor_snapshot,
            paper_trading_active=snapshot.paper_trading_active,
            audit_event_count=len(self.audit.audit_log.events),
        )
        workflow_orchestrator_snapshot = self.workflow_orchestrator.snapshot()
        workflow_runtime_monitor_snapshot = self.workflow_runtime_monitor.snapshot(
            orchestrator=workflow_orchestrator_snapshot,
            timestamp_utc=_now(),
        )
        api_execution_gateway_snapshot = self.api_execution_gateway.snapshot()
        performance_truth_snapshot = self.performance_truth_engine.snapshot(execution_environment="paper")
        strategy_performance_snapshot = self.strategy_performance_console.snapshot(
            timestamp_utc=_now(),
            lppc=lppc_snapshot,
            workflow_orchestrator=workflow_orchestrator_snapshot,
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            api_execution_gateway=api_execution_gateway_snapshot,
            performance_truth=performance_truth_snapshot,
            control=asdict(snapshot),
            audit_event_count=len(self.audit.audit_log.events),
        )
        decision_laboratory_snapshot = self.decision_laboratory.snapshot(
            workflow_orchestrator=workflow_orchestrator_snapshot,
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            performance_truth=performance_truth_snapshot,
            strategy_performance=strategy_performance_snapshot,
        )
        controlled_cognitive_pilot_snapshot = self.controlled_cognitive_pilot.snapshot(
            workflow_orchestrator=workflow_orchestrator_snapshot,
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            api_runtime_monitor=api_runtime_snapshot,
            api_execution_gateway=api_execution_gateway_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            performance_truth=performance_truth_snapshot,
        )
        return {
            "timestampUtc": _now(),
            "systemStatus": "NOMINAL",
            "environment": self.config.configuration.environment.value,
            "control": asdict(snapshot),
            "costs": asdict(costs),
            "groups": _groups(),
            "groupCards": _group_cards(snapshot.paper_trading_active),
            "healthSeries": _health_series(snapshot.paper_trading_active),
            "resources": resources,
            "kpis": _kpis(snapshot.paper_trading_active),
            "schedule": _schedule(),
            "activity": activity,
            "commands": commands,
            "offices": _offices(),
            "auditEventCount": len(self.audit.audit_log.events),
            "realWorldTradingSafety": "BLOCKED_BY_CONFIGURATION",
            "eab": eab_snapshot,
            "commandConsole": self.command_console.snapshot(),
            "cnac": cnac_snapshot,
            "scheduler": scheduler_snapshot,
            "ecc": ecc_snapshot,
            "infrastructure": infrastructure_snapshot,
            "ioe": ioe_snapshot,
            "lppc": lppc_snapshot,
            "creditGovernor": credit_governor_snapshot,
            "apiRuntimeMonitor": api_runtime_snapshot,
            "apiExecutionGateway": api_execution_gateway_snapshot,
            "promptContract": self.prompt_contract_library.snapshot(),
            "performanceTruthEngine": performance_truth_snapshot,
            "decisionLaboratory": decision_laboratory_snapshot,
            "controlledCognitivePilot": controlled_cognitive_pilot_snapshot,
            "workflowOrchestrator": workflow_orchestrator_snapshot,
            "workflowRuntimeMonitor": workflow_runtime_monitor_snapshot,
            "strategyPerformanceConsole": strategy_performance_snapshot,
        }

    def start_paper_self_training(self) -> dict[str, Any]:
        """Start paper self-training and execute a deterministic tokenized proof-of-life workflow."""
        prior_workflow_count = self.workflow_orchestrator.snapshot()["metrics"]["workflowCount"]
        record = self.control.initiate_paper_trading_self_training(self.authority, "User initiated ARGOS paper self-training from Control Panel.")
        self._paper_runner_pause_requested.clear()
        self._paper_runner_step_requested.clear()
        self.controlled_cognitive_pilot.start()
        self._ensure_paper_trading_workflow_runner(record.action_id)
        workflow = self._wait_for_new_paper_workflow(prior_workflow_count)
        self._publish_enterprise_event(
            organization="Trader",
            office="Trade Monitoring",
            workflow="Paper Trading Workflow",
            task_identifier=record.action_id,
            event_category="TRADING",
            severity="NOTICE",
            summary="Paper self-training started",
            detailed_description="Commander Interface initiated deterministic paper trading self-training through a tokenized workflow proof of life.",
            supporting_evidence=(record.action_id, workflow.workflow_id if workflow else "PAPER-RUNNER-ACTIVE"),
            correlation_identifier=record.action_id,
        )
        self._publish_enterprise_event(
            organization="Trader",
            office="Enterprise Workflow Orchestrator",
            workflow="Paper Trading Workflow",
            task_identifier=record.action_id,
            event_category="WORKFLOW",
            severity="INFO",
            summary="Paper trading workflow runner armed",
            detailed_description="The deterministic paper trading workflow loop is armed for one active tokenized workflow at a time.",
            supporting_evidence=(record.action_id, workflow.workflow_id if workflow else "PAPER-RUNNER-ACTIVE", "OE-010"),
            correlation_identifier=record.action_id,
        )
        self._publish_enterprise_event(
            organization="Trader",
            office="API Execution Gateway",
            workflow="Paper Trading Workflow",
            task_identifier=record.action_id,
            event_category="API_RUNTIME",
            severity="INFO",
            summary="Paper trading gateway policy armed",
            detailed_description="Paper trading may use the API Execution Gateway only through LAW VII token-authorized dry-run requests.",
            supporting_evidence=(record.action_id, workflow.workflow_id if workflow else "PAPER-RUNNER-ACTIVE", "OE-011A"),
            correlation_identifier=record.action_id,
        )
        self._activity.append(_activity("EXECUTIVE", "Paper self-training authorized", record.action_id, "SUCCESS"))
        return self.state()

    def halt_paper_self_training(self) -> dict[str, Any]:
        """Halt paper self-training and route commands to all groups."""
        record = self.control.halt_paper_trading_self_training(self.authority, "User halted ARGOS paper self-training from Control Panel.")
        self._paper_runner_stop.set()
        self._paper_runner_pause_requested.clear()
        self._paper_runner_step_requested.set()
        self._route_enterprise_command("halt_paper_self_training")
        self._publish_enterprise_event(
            organization="Trader",
            office="Trade Monitoring",
            workflow="Paper Trading Workflow",
            task_identifier=record.action_id,
            event_category="TRADING",
            severity="WARNING",
            summary="Paper self-training halted",
            detailed_description="Commander Interface halted deterministic paper trading self-training.",
            supporting_evidence=(record.action_id,),
            correlation_identifier=record.action_id,
        )
        self._activity.append(_activity("EXECUTIVE", "Paper self-training halted", record.action_id, "SUCCESS"))
        return self.state()

    def pause_after_current_stage(self) -> dict[str, Any]:
        """Pause paper workflow advancement after the current stage completes."""
        self._paper_runner_pause_requested.set()
        self._paper_runner_step_requested.clear()
        self._publish_enterprise_event(
            organization="Commander Interface",
            office="Command Bridge",
            workflow="Paper Trading Workflow",
            task_identifier="BRIDGE-PAUSE",
            event_category="COMMAND",
            severity="NOTICE",
            summary="Pause requested after current stage",
            detailed_description="Commander requested workflow pause at the next safe stage boundary.",
            supporting_evidence=("OE-100",),
            correlation_identifier="BRIDGE-PAUSE",
            status="PAUSE_REQUESTED",
        )
        return self.state()

    def step_paused_workflow(self) -> dict[str, Any]:
        """Permit exactly one paused paper workflow stage to advance."""
        self._paper_runner_step_requested.set()
        self._publish_enterprise_event(
            organization="Commander Interface",
            office="Command Bridge",
            workflow="Paper Trading Workflow",
            task_identifier="BRIDGE-STEP",
            event_category="COMMAND",
            severity="NOTICE",
            summary="Single workflow step authorized",
            detailed_description="Commander authorized one paused workflow transition to proceed.",
            supporting_evidence=("OE-100",),
            correlation_identifier="BRIDGE-STEP",
            status="STEP_AUTHORIZED",
        )
        return self.state()

    def resume_after_pause(self) -> dict[str, Any]:
        """Resume paper workflow advancement after a Commander pause."""
        self._paper_runner_pause_requested.clear()
        self._paper_runner_step_requested.set()
        self._publish_enterprise_event(
            organization="Commander Interface",
            office="Command Bridge",
            workflow="Paper Trading Workflow",
            task_identifier="BRIDGE-RESUME",
            event_category="COMMAND",
            severity="NOTICE",
            summary="Workflow resume requested",
            detailed_description="Commander requested workflow advancement to resume after a paused stage boundary.",
            supporting_evidence=("OE-102", "Seeker Subcommand Bridge"),
            correlation_identifier="BRIDGE-RESUME",
            audit_identifier=f"AUD-BRIDGE-RESUME-{len(self._commands) + 1:04d}",
        )
        return self.state()

    def deposit_user_funds(self, amount_usd: float) -> dict[str, Any]:
        """Deposit user funds into active treasury."""
        record = self.control.deposit_user_funds_to_active_treasury(self.authority, "USER-001", amount_usd, "User deposited funds into active treasury.")
        self._publish_enterprise_event(
            organization="Executive",
            office="Control Panel",
            workflow="Treasury Control Workflow",
            task_identifier=record.action_id,
            event_category="COMMAND",
            severity="NOTICE",
            summary=f"Active treasury deposit recorded: ${amount_usd:.2f}",
            detailed_description="Commander Interface recorded user funds deposited into active treasury.",
            supporting_evidence=(record.action_id,),
            correlation_identifier=record.action_id,
            portfolio="Active Treasury",
        )
        self._activity.append(_activity("EXECUTIVE", f"Active treasury deposit ${amount_usd:.2f}", record.action_id, record.status.value.upper()))
        return self.state()

    def halt_user_funds(self) -> dict[str, Any]:
        """Halt active treasury deposits."""
        record = self.control.halt_user_funds_into_active_treasury(self.authority, "User halted funds into active treasury.")
        self._publish_enterprise_event(
            organization="Executive",
            office="Control Panel",
            workflow="Treasury Control Workflow",
            task_identifier=record.action_id,
            event_category="COMMAND",
            severity="WARNING",
            summary="Active treasury deposits halted",
            detailed_description="Commander Interface halted user-fund deposits into active treasury.",
            supporting_evidence=(record.action_id,),
            correlation_identifier=record.action_id,
            portfolio="Active Treasury",
        )
        self._activity.append(_activity("EXECUTIVE", "Active treasury deposits halted", record.action_id, "SUCCESS"))
        return self.state()

    def request_real_world_trading(self) -> dict[str, Any]:
        """Request live trading; denied by default until future gates are implemented."""
        gates = RealWorldTradingGate(True, False, False, self.control.active_treasury_balance_usd > 0, True, False)
        record = self.control.initiate_real_world_trading_from_active_treasury(self.authority, gates, "User requested real-world trading from active treasury.")
        self._publish_enterprise_event(
            organization="Trader",
            office="Trade Execution",
            workflow="Live Trading Gate Workflow",
            task_identifier=record.action_id,
            event_category="TRADING",
            severity="CRITICAL",
            summary="Real-world trading request denied by safety gates",
            detailed_description="Live trading remains blocked by deterministic configuration and authorization gates.",
            supporting_evidence=(record.action_id,),
            correlation_identifier=record.action_id,
            portfolio="Active Treasury",
            status="DENIED",
        )
        self._activity.append(_activity("TRADER", "Real-world trading request denied by safety gates", record.action_id, "DENIED"))
        return self.state()

    def halt_real_world_trading(self) -> dict[str, Any]:
        """Halt live trading path."""
        record = self.control.halt_real_world_trading(self.authority, "User halted real-world trading from Control Panel.")
        self._publish_enterprise_event(
            organization="Trader",
            office="Trade Monitoring",
            workflow="Live Trading Gate Workflow",
            task_identifier=record.action_id,
            event_category="TRADING",
            severity="WARNING",
            summary="Real-world trading halt asserted",
            detailed_description="Commander Interface asserted the live-trading halt path.",
            supporting_evidence=(record.action_id,),
            correlation_identifier=record.action_id,
            portfolio="Active Treasury",
        )
        self._activity.append(_activity("TRADER", "Real-world trading halt asserted", record.action_id, "SUCCESS"))
        return self.state()

    def set_api_budget(self, amount_usd: float) -> dict[str, Any]:
        """Set visible API-credit budget."""
        self._budget_limit_usd = max(0.0, round(float(amount_usd), 2))
        self._publish_enterprise_event(
            organization="Infrastructure",
            office="Runtime",
            workflow="Operating Expense Workflow",
            task_identifier="API-BUDGET",
            event_category="INFRASTRUCTURE",
            severity="NOTICE",
            summary=f"API credit budget set to ${self._budget_limit_usd:.2f}",
            detailed_description="Commander Interface updated visible API-credit budget controls.",
            correlation_identifier=f"API-BUDGET-{len(self.eab.search({})) + 1:06d}",
        )
        self._activity.append(_activity("INFRASTRUCTURE", f"API credit budget set to ${self._budget_limit_usd:.2f}", "BUDGET", "SUCCESS"))
        return self.state()

    def commander_action(self, action: str, target: str, detail: str = "") -> dict[str, Any]:
        """Perform an audited Enterprise Command Center Commander action."""
        record = self.ecc.perform_action(action, target, detail)
        if action == "pause_organization":
            self._suspend_organization(target, "Commander")
        elif action == "resume_organization":
            self._activate_organization(target, "Commander")
        elif action == "change_operating_mode":
            self._configure_organization_mode(target, detail or "Continuous Operation")
        elif action == "configure_schedule":
            self._configure_organization_schedule(target, detail or "continuous monitoring")
        self._publish_enterprise_event(
            organization="Commander Interface",
            office="Enterprise Command Center",
            workflow="Commander Action Workflow",
            task_identifier=record.action_id,
            event_category="COMMAND",
            severity="WARNING" if action == "pause_organization" else "NOTICE",
            summary=f"{action.replace('_', ' ').title()} issued for {target}",
            detailed_description=f"Commander action {action} was routed to {target} through the ECC.",
            supporting_evidence=(record.document_id,),
            correlation_identifier=record.action_id,
            audit_identifier=record.audit_id,
        )
        self._activity.append(_activity("ECC", f"{action.replace('_', ' ').title()} for {target}", record.action_id, record.status))
        return self.state()

    def export_ecc_report(self) -> dict[str, Any]:
        """Return a deterministic Enterprise Command Center report."""
        report = self.ecc.export_report()
        self.ecc.perform_action("export_reports", "Executive", report["reportId"])
        state = self.state()
        state["eccReport"] = report
        return state

    def eab_events(self, filters: dict[str, str] | None = None) -> dict[str, Any]:
        """Return filtered Enterprise Activity Bus state."""
        state = self.state()
        state["eab"] = self.eab.snapshot(filters)
        self.cnac.ingest(tuple(reversed(state["eab"]["events"])))
        state["cnac"] = self.cnac.snapshot()
        return state

    def cnac_notifications(self, filters: dict[str, str] | None = None) -> dict[str, Any]:
        """Return filtered Commander notifications."""
        state = self.state()
        state["cnac"] = self.cnac.snapshot(filters)
        return state

    def ioe_explorer(self, filters: dict[str, str] | None = None) -> dict[str, Any]:
        """Return filtered Interactive Organization Explorer state."""
        state = self.state()
        state["ioe"] = self.ioe.snapshot(
            ecc=state["ecc"],
            eab=state["eab"],
            cnac=state["cnac"],
            scheduler=state["scheduler"],
            audit_event_count=state["auditEventCount"],
            filters=filters,
        )
        return state

    def ioe_action(self, action: str, node_id: str) -> dict[str, Any]:
        """Perform a Commander explorer action."""
        record = self.ioe.perform_action(action, node_id, _now())
        self._publish_enterprise_event(
            organization="Commander Interface",
            office="Interactive Organization Explorer",
            workflow="Explorer Navigation Workflow",
            task_identifier=record.action_id,
            event_category="NAVIGATION",
            severity="INFO",
            summary=f"IOE {action} action completed for {node_id}",
            detailed_description=f"Commander executed {action} against explorer node {node_id}.",
            supporting_evidence=(node_id,),
            correlation_identifier=record.action_id,
            status=record.status,
        )
        return self.state()

    def command_console_execute(
        self,
        command_name: str,
        category: str = "",
        target: str = "",
        detail: str = "",
        amount_usd: float = 0.0,
    ) -> dict[str, Any]:
        """Validate, authorize, execute, and archive one Commander command."""
        record = self.command_console.issue(
            command_name=command_name,
            category=category,
            target=target,
            detail=detail,
            amount_usd=amount_usd,
            authority_level=self.authority.max_level.value,
            context=self._command_context(),
            timestamp_utc=_now(),
        )
        if not record.validation.accepted:
            self._publish_command_console_event(record, "REJECTED")
            return self.state()

        result_summary = "Command completed."
        evidence: tuple[str, ...] = (record.command_id,)
        try:
            if command_name == "start_paper_self_training":
                self.start_paper_self_training()
                result_summary = "Paper self-training started."
            elif command_name == "halt_paper_self_training":
                self.halt_paper_self_training()
                result_summary = "Paper self-training halted."
            elif command_name == "deposit_user_funds":
                self.deposit_user_funds(amount_usd)
                result_summary = f"Deposited ${amount_usd:.2f} into active treasury."
            elif command_name == "halt_user_funds":
                self.halt_user_funds()
                result_summary = "User funds into active treasury halted."
            elif command_name == "halt_real_world_trading":
                self.halt_real_world_trading()
                result_summary = "Real-world trading halt asserted."
            elif command_name in {
                "pause_organization",
                "resume_organization",
                "change_operating_mode",
                "configure_schedule",
                "review_evidence",
                "inspect_workflows",
                "view_historical_activity",
            }:
                self.commander_action(command_name, target or "Executive", detail)
                result_summary = f"{command_name.replace('_', ' ').title()} routed to {target or 'Executive'}."
            elif command_name == "export_reports":
                exported = self.export_ecc_report()
                evidence = (record.command_id, exported.get("eccReport", {}).get("reportId", "ECC-REPORT"))
                result_summary = "Deterministic ECC report exported."
            elif command_name == "daily_briefing":
                briefing = self.generate_commander_briefing("Daily Enterprise Report")
                evidence = (record.command_id, briefing.get("commanderBriefing", {}).get("briefing_id", "DAILY-BRIEFING"))
                result_summary = "Daily Enterprise Report generated."
            else:
                raise ValueError(f"unsupported executable command: {command_name}")
            completed = self.command_console.complete(
                record.command_id,
                execution_status="SUCCESS",
                detailed_results=result_summary,
                supporting_evidence=evidence,
                audit_identifier="PENDING_EAB_AUDIT",
            )
            event = self._publish_command_console_event(completed, "COMPLETED")
            self.command_console.complete(
                record.command_id,
                execution_status="SUCCESS",
                detailed_results=result_summary,
                supporting_evidence=evidence + (event.event_id,),
                audit_identifier=event.audit_identifier,
            )
        except Exception as exc:
            failed = self.command_console.complete(
                record.command_id,
                execution_status="FAILED",
                detailed_results=str(exc),
                supporting_evidence=evidence,
                audit_identifier="FAILED_BEFORE_AUDIT",
            )
            self._publish_command_console_event(failed, "FAILED")
        return self.state()

    def command_console_macro(self, macro_name: str) -> dict[str, Any]:
        """Execute a deterministic reusable Commander macro."""
        commands = self.command_console.macro_commands(macro_name)
        for command in commands:
            self.command_console_execute(command, detail=macro_name)
        self._publish_enterprise_event(
            organization="Commander Interface",
            office="Command Console",
            workflow="Commander Macro Workflow",
            task_identifier=macro_name.upper().replace(" ", "-"),
            event_category="COMMAND",
            severity="CRITICAL" if macro_name == "Emergency Shutdown" else "NOTICE",
            summary=f"Commander macro executed: {macro_name}",
            detailed_description=f"Command Console expanded {macro_name} into {', '.join(commands)}.",
            supporting_evidence=commands,
            correlation_identifier=f"CC-MACRO-{len(self.eab.search({})) + 1:06d}",
            status="ARCHIVED",
        )
        return self.state()

    def command_console_history(self, filters: dict[str, str] | None = None) -> dict[str, Any]:
        """Return filtered Command Console history."""
        state = self.state()
        state["commandConsole"] = self.command_console.snapshot(filters)
        return state

    def infrastructure_state(self) -> dict[str, Any]:
        """Return current Infrastructure & AI Resource Management state."""
        return self.state()

    def lppc_state(self) -> dict[str, Any]:
        """Return current Live Portfolio & Performance Console state."""
        return self.state()

    def strategy_performance_state(self) -> dict[str, Any]:
        """Return current Live Strategy Performance Console state."""
        return self.state()

    def performance_truth_state(self) -> dict[str, Any]:
        """Return current Performance Truth Engine state."""
        return self.state()

    def decision_laboratory_state(self, search_query: str = "") -> dict[str, Any]:
        """Return current Decision Laboratory state."""
        state = self.state()
        if search_query:
            state["decisionLaboratory"] = self.decision_laboratory.snapshot(
                workflow_orchestrator=state["workflowOrchestrator"],
                workflow_runtime_monitor=state["workflowRuntimeMonitor"],
                performance_truth=state["performanceTruthEngine"],
                strategy_performance=state["strategyPerformanceConsole"],
                search_query=search_query,
            )
        return state

    def create_decision_lab_experiment(self, workflow_id: str, parameter_changes: dict[str, Any], parent_experiment_id: str = "") -> dict[str, Any]:
        """Fork a completed Decision Object into an isolated experiment."""
        self.decision_laboratory.create_experiment(
            workflow_id,
            parameter_changes,
            parent_experiment_id=parent_experiment_id,
            workflow_orchestrator=self.workflow_orchestrator.snapshot(),
            performance_truth=self.performance_truth_engine.snapshot(execution_environment="paper"),
        )
        self._publish_enterprise_event(
            organization="Historian",
            office="Decision Laboratory",
            workflow="Decision Experiment",
            task_identifier=workflow_id,
            event_category="HISTORIAN",
            severity="INFO",
            summary="Decision Laboratory experiment created",
            detailed_description="Commander forked a completed Decision Object into an isolated laboratory experiment.",
            supporting_evidence=(workflow_id, "OE-011D"),
            correlation_identifier=workflow_id,
        )
        return self.state()

    def start_decision_lab_replay(self, workflow_id: str) -> dict[str, Any]:
        """Start deterministic replay for a completed workflow."""
        self.decision_laboratory.start_replay(workflow_id, workflow_orchestrator=self.workflow_orchestrator.snapshot())
        return self.state()

    def control_decision_lab_replay(self, replay_id: str, action: str, value: str = "") -> dict[str, Any]:
        """Apply Decision Laboratory replay controls."""
        self.decision_laboratory.replay_control(replay_id, action, value)
        return self.state()

    def credit_governor_state(self) -> dict[str, Any]:
        """Return current Enterprise Credit Governor state."""
        return self.state()

    def configure_credit_governor(
        self,
        daily_budget_usd: float,
        weekly_budget_usd: float,
        monthly_budget_usd: float,
        office: str = "",
        office_budget_usd: float | None = None,
        workflow: str = "",
        workflow_budget_usd: float | None = None,
        task_identifier: str = "",
        task_budget_usd: float | None = None,
    ) -> dict[str, Any]:
        """Configure credit-governor budgets."""
        override = self.credit_governor.configure_budgets(
            daily_budget_usd=daily_budget_usd,
            weekly_budget_usd=weekly_budget_usd,
            monthly_budget_usd=monthly_budget_usd,
            office=office,
            office_budget_usd=office_budget_usd,
            workflow=workflow,
            workflow_budget_usd=workflow_budget_usd,
            task_identifier=task_identifier,
            task_budget_usd=task_budget_usd,
            timestamp_utc=_now(),
        )
        self._budget_limit_usd = max(0.0, round(float(monthly_budget_usd), 2))
        self._publish_enterprise_event(
            organization="Infrastructure",
            office="Enterprise Credit Governor",
            workflow="Credit Budget Governance Workflow",
            task_identifier=override["overrideId"],
            event_category="INFRASTRUCTURE",
            severity="NOTICE",
            summary="Enterprise credit budgets configured",
            detailed_description="Commander updated daily, weekly, monthly, office, workflow, or task credit budgets.",
            supporting_evidence=(override["overrideId"],),
            correlation_identifier=override["overrideId"],
            status="CONFIGURED",
        )
        return self.state()

    def request_credit_activation(
        self,
        task_identifier: str,
        activating_source: str,
        receiving_office: str,
        purpose: str,
        required_output: str,
        maximum_runtime_minutes: int,
        maximum_credit_budget_usd: float,
        workflow: str,
        organization: str,
        evidence_package: tuple[str, ...] = (),
        return_route: str = "Commander Interface",
        workflow_id: str = "",
        workflow_token_id: str = "",
        office: str = "",
    ) -> dict[str, Any]:
        """Request a governed AI activation."""
        current = self.state()
        scoped_office = office or receiving_office
        if scoped_office != receiving_office:
            law_ok, law_code, law_reason = False, "LAW_VII_VIOLATION_NON_OWNER_API_USAGE", "API usage office must match the receiving office that would consume credits."
        else:
            law_ok, law_code, law_reason = self._validate_law_vii_api_usage(
                workflow_id=workflow_id,
                workflow_token_id=workflow_token_id,
                office=scoped_office,
                credit_amount=maximum_credit_budget_usd,
            )
        audit_identifier = f"AE-CREDIT-ACT-{len(self.audit.audit_log.events) + 1:06d}"
        if not law_ok:
            activation = self.credit_governor.record_blocked_activation(
                task_identifier=task_identifier,
                activating_source=activating_source,
                receiving_office=receiving_office,
                purpose=purpose,
                required_output=required_output,
                maximum_runtime_minutes=maximum_runtime_minutes,
                maximum_credit_budget_usd=maximum_credit_budget_usd,
                evidence_package=evidence_package,
                return_route=return_route,
                workflow=workflow,
                organization=organization,
                audit_identifier=audit_identifier,
                workflow_id=workflow_id,
                workflow_token_id=workflow_token_id,
                law_vii_validation=law_code,
                reason=law_reason,
            )
            self.api_runtime_monitor.record_law_vii_violation(law_code, law_reason, (activation.activation_id, workflow_id, scoped_office))
            self._publish_enterprise_event(
                organization="Infrastructure",
                office="Enterprise Credit Governor",
                workflow="AI Activation Governance Workflow",
                task_identifier=activation.activation_id,
                event_category="INFRASTRUCTURE",
                severity="CRITICAL",
                summary=law_code,
                detailed_description=law_reason,
                supporting_evidence=(activation.activation_id, workflow_id, scoped_office),
                correlation_identifier=activation.activation_id,
                status="REJECTED",
            )
            return self.state()
        activation = self.credit_governor.request_activation(
            task_identifier=task_identifier,
            activating_source=activating_source,
            receiving_office=receiving_office,
            purpose=purpose,
            required_output=required_output,
            maximum_runtime_minutes=maximum_runtime_minutes,
            maximum_credit_budget_usd=maximum_credit_budget_usd,
            evidence_package=evidence_package,
            return_route=return_route,
            workflow=workflow,
            organization=organization,
            audit_identifier=audit_identifier,
            current_spend=current["creditGovernor"]["spendReport"],
            paper_trading_active=bool(current["control"]["paper_trading_active"]),
            workflow_id=workflow_id,
            workflow_token_id=workflow_token_id,
            law_vii_validation=law_code,
        )
        if activation.status == "APPROVED":
            self._record_api_credit_usage(workflow_id, activation.maximum_credit_budget_usd)
            self.api_runtime_monitor.register_activation(activation, _now())
        self._publish_enterprise_event(
            organization="Infrastructure",
            office="Enterprise Credit Governor",
            workflow="AI Activation Governance Workflow",
            task_identifier=activation.activation_id,
            event_category="INFRASTRUCTURE",
            severity="NOTICE" if activation.status == "APPROVED" else "WARNING",
            summary=f"AI activation {activation.status.lower()}: {activation.receiving_office}",
            detailed_description=activation.reason,
            supporting_evidence=(activation.activation_id, *activation.evidence_package),
            correlation_identifier=activation.activation_id,
            status=activation.status,
        )
        return self.state()

    def complete_credit_activation(self, activation_id: str) -> dict[str, Any]:
        """Complete an AI activation and return the office to dormancy."""
        activation = self.credit_governor.complete_activation(activation_id)
        self.api_runtime_monitor.complete_activation(activation.activation_id, _now())
        self._publish_enterprise_event(
            organization="Infrastructure",
            office="Enterprise Credit Governor",
            workflow="AI Activation Governance Workflow",
            task_identifier=activation.activation_id,
            event_category="INFRASTRUCTURE",
            severity="INFO",
            summary=f"AI activation completed: {activation.receiving_office}",
            detailed_description=activation.reason,
            supporting_evidence=(activation.activation_id,),
            correlation_identifier=activation.activation_id,
            status="COMPLETED",
        )
        return self.state()

    def api_runtime_monitor_state(self) -> dict[str, Any]:
        """Return current API Runtime Monitor state."""
        return self.state()

    def api_runtime_monitor_control(self, action: str, target: str, value: str = "") -> dict[str, Any]:
        """Apply a Commander API Runtime Monitor control."""
        record = self.api_runtime_monitor.control(action, target, value)
        self._publish_enterprise_event(
            organization="Infrastructure",
            office="API Runtime Monitor",
            workflow="API Runtime Control Workflow",
            task_identifier=record.control_id,
            event_category="INFRASTRUCTURE",
            severity="NOTICE" if record.status != "REJECTED" else "WARNING",
            summary=f"API runtime control {record.status.lower()}: {record.action}",
            detailed_description=f"Commander applied API runtime control to {record.target}.",
            supporting_evidence=(record.control_id,),
            correlation_identifier=record.control_id,
            status=record.status,
        )
        return self.state()

    def reset_api_runtime_session(self) -> dict[str, Any]:
        """Clear volatile API runtime session state without erasing immutable audit logs."""
        record = self.api_runtime_monitor.reset_session()
        self._session_api_credits_usd = 0.0
        self._workflow_api_usage_usd = {}
        self._publish_enterprise_event(
            organization="Infrastructure",
            office="API Runtime Monitor",
            workflow="API Runtime Control Workflow",
            task_identifier=record.control_id,
            event_category="INFRASTRUCTURE",
            severity="NOTICE",
            summary="API runtime session reset",
            detailed_description="Commander cleared volatile API runtime chart, entity, activation-chain, alert, and session-cost state without erasing audit records.",
            supporting_evidence=(record.control_id,),
            correlation_identifier=record.control_id,
            status="RESET",
        )
        return self.state()

    def workflow_orchestrator_state(self) -> dict[str, Any]:
        """Return current Enterprise Workflow Orchestrator state."""
        return self.state()

    def workflow_runtime_monitor_state(self) -> dict[str, Any]:
        """Return current Workflow Runtime Monitor state."""
        return self.state()

    def create_workflow(
        self,
        name: str,
        stages: tuple[str, ...],
        runtime_budget: int,
        credit_budget: float,
        expected_output_schema: tuple[str, ...],
    ) -> dict[str, Any]:
        """Create, validate, queue, and assign a deterministic workflow."""
        workflow = self.workflow_orchestrator.create_validate_queue_assign(
            name=name,
            stages=stages,
            runtime_budget=runtime_budget,
            credit_budget=credit_budget,
            expected_output_schema=expected_output_schema,
        )
        self._publish_workflow_event(workflow.workflow_id, "Workflow created, validated, queued, and assigned", "ASSIGNED")
        return self.state()

    def start_workflow_execution(self, workflow_id: str) -> dict[str, Any]:
        """Start execution for the current token owner."""
        workflow = self.workflow_orchestrator.start_execution(workflow_id)
        self._publish_workflow_event(workflow.workflow_id, f"Workflow executing at {workflow.token.current_owner}", "EXECUTING")
        return self.state()

    def produce_workflow_output(
        self,
        workflow_id: str,
        output: dict[str, Any],
        runtime: int,
        credits: float,
        token_usage: int,
        execution_time_seconds: int,
    ) -> dict[str, Any]:
        """Emit and validate structured output for a workflow stage."""
        workflow = self.workflow_orchestrator.produce_structured_output(
            workflow_id,
            output,
            runtime=runtime,
            credits=credits,
            token_usage=token_usage,
            execution_time_seconds=execution_time_seconds,
        )
        self._publish_workflow_event(workflow.workflow_id, "Structured output produced and validated", "OUTPUT_VALIDATED")
        return self.state()

    def transfer_workflow_token(self, workflow_id: str, reason: str = "Structured output validated") -> dict[str, Any]:
        """Transfer workflow token ownership after validated output."""
        workflow = self.workflow_orchestrator.transfer_ownership(workflow_id, reason)
        self._publish_workflow_event(workflow.workflow_id, f"Workflow token transferred from {workflow.token.previous_owner}", workflow.token.workflow_status)
        return self.state()

    def advance_workflow_stage(self, workflow_id: str) -> dict[str, Any]:
        """Advance a transferred workflow through Next Stage and Assigned gates."""
        workflow = self.workflow_orchestrator.advance_next_stage(workflow_id)
        workflow = self.workflow_orchestrator.assign_transferred_stage(workflow.workflow_id)
        self._publish_workflow_event(workflow.workflow_id, f"Workflow assigned to next owner {workflow.token.current_owner}", "ASSIGNED")
        return self.state()

    def archive_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Archive a completed workflow."""
        workflow = self.workflow_orchestrator.archive_workflow(workflow_id)
        self._publish_workflow_event(workflow.workflow_id, "Workflow archived", "ARCHIVED")
        return self.state()

    def _ensure_paper_trading_workflow_runner(self, action_id: str) -> None:
        """Start one continuing paper workflow runner if none is alive."""
        with self._paper_runner_lock:
            if self._paper_runner_thread and self._paper_runner_thread.is_alive():
                return
            self._paper_runner_stop.clear()
            self._paper_runner_thread = threading.Thread(
                target=self._paper_trading_workflow_loop,
                args=(action_id,),
                daemon=True,
                name="ARGOS-PaperWorkflowRunner",
            )
            self._paper_runner_thread.start()

    def _paper_trading_workflow_loop(self, action_id: str) -> None:
        """Continuously run one paper workflow at a time while paper trading is active."""
        cycle = 0
        while not self._paper_runner_stop.is_set() and self.control.paper_trading_active:
            completed_pilot_workflows = self._completed_paper_workflow_count()
            can_start, stop_reason = self.controlled_cognitive_pilot.should_start_next_workflow(
                completed_pilot_workflows=completed_pilot_workflows,
                real_api_cost_usd=self.api_execution_gateway.snapshot()["realApiSessionSpendUsd"],
            )
            if not can_start:
                self.control.paper_trading_active = False
                self.controlled_cognitive_pilot.complete(stop_reason)
                self._publish_enterprise_event(
                    organization="Commander Interface",
                    office="Controlled Cognitive Pilot",
                    workflow="OE-011G Pilot Workflow",
                    task_identifier=action_id,
                    event_category="PILOT",
                    severity="NOTICE",
                    summary="Controlled cognitive pilot complete",
                    detailed_description=stop_reason,
                    supporting_evidence=(str(completed_pilot_workflows),),
                    correlation_identifier=action_id,
                    status="COMPLETE",
                )
                break
            cycle += 1
            workflow = self._create_paper_trading_session_workflow(f"{action_id}-CYCLE-{cycle:06d}")
            self._complete_paper_trading_session_workflow(workflow.workflow_id, f"{action_id}-CYCLE-{cycle:06d}", self._workflow_demo_stage_delay_seconds)
            if self._paper_runner_stop.is_set() or not self.control.paper_trading_active:
                break
            self._paper_runner_stop.wait(self._paper_workflow_cycle_interval_seconds)

    def _wait_for_new_paper_workflow(self, prior_workflow_count: int) -> Any:
        """Wait briefly until the runner has created the first workflow."""
        deadline = time.time() + 1.0
        latest = None
        while time.time() < deadline:
            workflows = self.workflow_orchestrator.snapshot()["workflows"]
            paper_workflows = [item for item in workflows if item["workflow_type"] == "paper_trading_session"]
            if len(workflows) > prior_workflow_count and paper_workflows:
                latest_id = paper_workflows[-1]["workflow_id"]
                return self.workflow_orchestrator.workflow(latest_id)
            time.sleep(0.01)
        workflows = self.workflow_orchestrator.snapshot()["workflows"]
        paper_workflows = [item for item in workflows if item["workflow_type"] == "paper_trading_session"]
        if paper_workflows:
            latest = self.workflow_orchestrator.workflow(paper_workflows[-1]["workflow_id"])
        return latest

    def _completed_paper_workflow_count(self) -> int:
        return sum(
            1
            for item in self.workflow_orchestrator.snapshot()["workflows"]
            if item["workflow_type"] == "paper_trading_session" and item["token"]["workflow_status"] == "Archived"
        )

    def _create_paper_trading_session_workflow(self, action_id: str) -> Any:
        """Create and begin one deterministic paper-trading workflow without API usage."""
        del action_id
        stages = ("Seeker", "Analyst", "Risk", "Trader", "Historian")
        expected_output_schema = ("summary", "evidence", "audit_identifier", "workflow_type", "workflow_stage", "initial_stage")
        with self._workflow_lock:
            workflow = self.workflow_orchestrator.create_validate_queue_assign(
                name="Paper Trading Session",
                stages=stages,
                runtime_budget=100,
                credit_budget=min(0.01, self.controlled_cognitive_pilot.limits.maximum_workflow_cost_usd if self.controlled_cognitive_pilot.enabled else 0.01),
                expected_output_schema=expected_output_schema,
                workflow_type="paper_trading_session",
                initial_stage="market_preparation",
            )
            self._publish_workflow_event(workflow.workflow_id, "Paper trading workflow created, validated, queued, and assigned", "ASSIGNED")
            workflow = self.workflow_orchestrator.start_execution(workflow.workflow_id)
            self._publish_workflow_event(workflow.workflow_id, f"Paper trading workflow executing at {workflow.token.current_owner}", "EXECUTING")
            return workflow

    def _complete_paper_trading_session_workflow(self, workflow_id: str, action_id: str, stage_delay_seconds: float) -> Any:
        """Advance a paper workflow through placeholder stages while preserving exclusive token ownership."""
        workflow = None
        while True:
            if stage_delay_seconds > 0:
                time.sleep(stage_delay_seconds)
            with self._workflow_lock:
                workflow = self.workflow_orchestrator.workflow(workflow_id)
                if workflow.token.workflow_status == "Archived":
                    return workflow
                owner = workflow.token.current_owner
                gateway_response = None
                if owner == "Analyst" and self._enable_placeholder_credit_proof and workflow.workflow_id not in self._paper_gateway_execution_recorded:
                    gateway_response = self._execute_analyst_gateway_request(workflow, action_id)
                    self._paper_gateway_execution_recorded.add(workflow.workflow_id)
                    if gateway_response.blocked:
                        self._paper_runner_stop.set()
                        self.controlled_cognitive_pilot.abort(gateway_response.violation_code)
                        self._publish_workflow_event(workflow.workflow_id, f"Analyst gateway blocked: {gateway_response.violation_code}", "BLOCKED")
                        return workflow
                output = {
                    "summary": f"{owner} completed deterministic paper trading placeholder stage.",
                    "evidence": f"{action_id}:{owner}:placeholder",
                    "audit_identifier": workflow.token.audit_identifier,
                    "workflow_type": "paper_trading_session",
                    "workflow_stage": owner,
                    "initial_stage": "market_preparation",
                }
                credits = 0.0
                token_usage = 0
                if gateway_response and gateway_response.allowed:
                    output = gateway_response.structured_output
                    credits = gateway_response.actual_cost_usd
                    token_usage = gateway_response.input_tokens + gateway_response.output_tokens
                output["decision_object"] = self._paper_decision_object(workflow, owner, action_id, gateway_response)
                output["prompt_contract"] = output.get("prompt_contract") or output["decision_object"].get("promptContract", {})
                workflow = self.workflow_orchestrator.produce_structured_output(
                    workflow.workflow_id,
                    output,
                    runtime=1,
                    credits=credits,
                    token_usage=token_usage,
                    execution_time_seconds=1,
                )
                self._publish_workflow_event(workflow.workflow_id, f"Structured output produced by {owner}", "OUTPUT_VALIDATED")
                workflow = self.workflow_orchestrator.transfer_ownership(workflow.workflow_id, f"{owner} placeholder output validated")
                self._publish_workflow_event(workflow.workflow_id, f"Workflow token transferred from {owner}", workflow.token.workflow_status)
                if workflow.token.workflow_status == "Completed":
                    workflow = self.workflow_orchestrator.archive_workflow(workflow.workflow_id)
                    self.performance_truth_engine.record_completed_workflow(workflow, execution_environment="paper")
                    self._publish_workflow_event(workflow.workflow_id, "Paper trading workflow archived", "ARCHIVED")
                    return workflow
                if self._paper_runner_pause_requested.is_set():
                    self._publish_workflow_event(workflow.workflow_id, "Workflow paused at Commander stage boundary", "PAUSED")
                    while self._paper_runner_pause_requested.is_set() and not self._paper_runner_stop.is_set() and self.control.paper_trading_active:
                        if self._paper_runner_step_requested.wait(0.1):
                            self._paper_runner_step_requested.clear()
                            break
                workflow = self.workflow_orchestrator.advance_next_stage(workflow.workflow_id)
                workflow = self.workflow_orchestrator.assign_transferred_stage(workflow.workflow_id)
                self._publish_workflow_event(workflow.workflow_id, f"Workflow assigned to next owner {workflow.token.current_owner}", "ASSIGNED")
                workflow = self.workflow_orchestrator.start_execution(workflow.workflow_id)
                self._publish_workflow_event(workflow.workflow_id, f"Paper trading workflow executing at {workflow.token.current_owner}", "EXECUTING")
        return workflow

    def _paper_decision_object(self, workflow: Any, owner: str, action_id: str, gateway_response: Any = None) -> dict[str, Any]:
        """Return one immutable deterministic Decision Object revision for a paper workflow stage."""
        revision = workflow.current_stage_index + 1
        confidence_delta_by_owner = {
            "Seeker": 0.04,
            "Analyst": 0.07,
            "Risk": 0.03,
            "Trader": 0.05,
            "Historian": 0.02,
        }
        risk_adjustment_by_owner = {
            "Seeker": 0.0,
            "Analyst": -0.01,
            "Risk": -0.07,
            "Trader": -0.02,
            "Historian": 0.0,
        }
        confidence_delta = confidence_delta_by_owner.get(owner, 0.01)
        risk_adjustment = risk_adjustment_by_owner.get(owner, 0.0)
        analyst_contract = {}
        gateway_metadata = {}
        revision_source = "deterministic_placeholder"
        prompt_contract = {}
        if gateway_response is not None and gateway_response.allowed:
            gateway_metadata = gateway_response.structured_output.get("api_execution_gateway", {})
            analyst_contract = gateway_response.structured_output.get("analyst_contract", {})
            prompt_contract = gateway_response.structured_output.get("prompt_contract", {})
            if gateway_response.fallback_used:
                revision_source = "dry_run_fallback"
            elif gateway_response.execution_mode == "real_api_pilot":
                revision_source = "real_api_pilot"
            else:
                revision_source = "dry_run"
        recommendation = "PAPER_APPROVE" if owner == "Trader" else ("PAPER_REVIEW_COMPLETE" if owner == "Historian" else "PAPER_MONITOR")
        if owner == "Analyst" and analyst_contract:
            recommendation = str(analyst_contract.get("recommendation", recommendation))
        confidence = round(0.50 + sum(confidence_delta_by_owner.get(stage, 0.0) for stage in workflow.stages[:revision]), 4)
        if owner == "Analyst" and isinstance(analyst_contract.get("confidence"), (int, float)):
            confidence = round(float(analyst_contract["confidence"]), 4)
        supporting_signals = (f"{owner}_structured_output", "paper_trading_session", action_id)
        if owner == "Analyst" and analyst_contract.get("supporting_signals"):
            supporting_signals = tuple(str(item) for item in analyst_contract.get("supporting_signals", ()))
        return {
            "decisionObjectId": f"DO-{workflow.workflow_id.replace('EWO-WF-', '')}",
            "workflowId": workflow.workflow_id,
            "revision": revision,
            "office": owner,
            "revisionSource": revision_source,
            "confidence": confidence,
            "confidenceDelta": confidence_delta,
            "recommendation": recommendation,
            "evidenceCount": revision * 2,
            "supportingSignals": supporting_signals,
            "riskScore": round(max(0.05, 0.48 + sum(risk_adjustment_by_owner.get(stage, 0.0) for stage in workflow.stages[:revision])), 4),
            "riskAdjustment": risk_adjustment,
            "positionSizeRecommendation": round(float(analyst_contract.get("position_size_recommendation", min(0.05, 0.01 + revision * 0.006))), 4),
            "targetPrice": None if analyst_contract.get("target_price") is None and owner == "Analyst" and analyst_contract else round(float(analyst_contract.get("target_price", 100.0 + revision * 2.25)), 4),
            "stopLoss": None if analyst_contract.get("stop_loss") is None and owner == "Analyst" and analyst_contract else round(float(analyst_contract.get("stop_loss", 96.0 - revision * 0.65)), 4),
            "expectedReturn": round(float(analyst_contract.get("expected_return", 0.01 + revision * 0.0045)), 4),
            "currentStrategy": "Workflow Proof Strategy" if owner in {"Seeker", "Analyst"} else "Risk Adjusted Paper Strategy",
            "supportingAuditIdentifier": workflow.token.audit_identifier,
            "apiExecutionMode": gateway_response.execution_mode if gateway_response else "",
            "apiProvider": gateway_response.provider if gateway_response else "",
            "apiModel": gateway_response.model if gateway_response else "",
            "apiFallbackUsed": bool(gateway_response.fallback_used) if gateway_response else False,
            "apiValidationStatus": gateway_response.validation_status if gateway_response else "",
            "apiGatewayMetadata": gateway_metadata,
            "promptContract": prompt_contract or prompt_contract_trace(
                build_prompt_contract_envelope(
                    library=self.prompt_contract_library,
                    workflow_id=workflow.workflow_id,
                    workflow_token_id=workflow.token.audit_identifier,
                    decision_object_id=f"DO-{workflow.workflow_id.replace('EWO-WF-', '')}",
                    current_office=owner,
                    current_stage=owner,
                    current_revision=revision,
                    execution_environment="paper",
                    strategy="Workflow Proof Strategy" if owner in {"Seeker", "Analyst"} else "Risk Adjusted Paper Strategy",
                    portfolio_context={"portfolio": "paper"},
                    risk_constraints={"live_trading": False, "max_position_size": 0.05},
                    commander_constraints={"no_live_trading": True},
                    task=f"{owner} deterministic paper workflow stage",
                    budget={"max_cost_usd": 0.0, "max_latency_seconds": 20},
                    audit_identifier=workflow.token.audit_identifier,
                    decision_object={"decisionObjectId": f"DO-{workflow.workflow_id.replace('EWO-WF-', '')}", "revision": revision},
                    evidence_package={"action_id": action_id},
                )
            ),
            "immutable": True,
        }

    def _execute_analyst_gateway_request(self, workflow: Any, action_id: str) -> Any:
        """Execute the one governed Analyst gateway request for a paper workflow."""
        real_enabled = self._real_api_config.enabled
        model = self._real_api_config.model if real_enabled else "dry-run-model"
        provider = self._real_api_config.provider if real_enabled else "none"
        execution_mode = "real_api_pilot" if real_enabled else "dry_run"
        prompt_template_id = "PROMPT-PAPER-ANALYST-REAL-API-PILOT" if real_enabled else "PROMPT-PAPER-ANALYST-DRY-RUN"
        seeker_output = workflow.output_history[0] if workflow.output_history else {}
        decision_object_id = f"DO-{workflow.workflow_id.replace('EWO-WF-', '')}"
        audit_identifier = f"AE-GATEWAY-{workflow.workflow_id}-ANALYST"
        prompt_contract = build_prompt_contract_envelope(
            library=self.prompt_contract_library,
            workflow_id=workflow.workflow_id,
            workflow_token_id=workflow.token.audit_identifier,
            decision_object_id=decision_object_id,
            current_office="Analyst",
            current_stage="Analyst",
            current_revision=workflow.current_stage_index + 1,
            execution_environment="paper",
            strategy="Workflow Proof Strategy",
            portfolio_context={"portfolio": "paper", "asset": "ARGOS-PAPER-BASKET"},
            risk_constraints={"live_trading": False, "max_position_size": 0.05, "max_cost_usd": self._real_api_config.max_cost_per_workflow_usd},
            commander_constraints={"no_live_trading": True, "paper_only": True},
            task="Analyze Seeker evidence and produce a schema-valid paper recommendation.",
            budget={
                "max_cost_usd": self._real_api_config.max_cost_per_workflow_usd if real_enabled else 0.001,
                "max_input_tokens": self._real_api_config.max_input_tokens if real_enabled else 128,
                "max_output_tokens": self._real_api_config.max_output_tokens if real_enabled else 128,
                "max_latency_seconds": self._real_api_config.timeout_seconds if real_enabled else 30,
            },
            audit_identifier=audit_identifier,
            decision_object={"decisionObjectId": decision_object_id, "workflowId": workflow.workflow_id},
            evidence_package={"seeker_revision": seeker_output, "action_id": action_id},
        )
        return self.api_execution_gateway.execute_model_request(
            ApiExecutionRequest(
                workflow_id=workflow.workflow_id,
                workflow_token_id=workflow.token.audit_identifier,
                requesting_office="Analyst",
                workflow_stage="Analyst",
                task_type="paper_trading_market_analysis",
                model=model,
                prompt_template_id=prompt_contract["prompt_template_id"] if real_enabled else prompt_template_id,
                prompt_payload={
                    "action_id": action_id,
                    "workflow_id": workflow.workflow_id,
                    "stage": "Analyst",
                    "decision_object_id": decision_object_id,
                    "current_decision_object": {"decisionObjectId": decision_object_id, "workflowId": workflow.workflow_id},
                    "seeker_revision": seeker_output.get("decision_object", seeker_output),
                    "paper_market_context": {"environment": "paper", "asset": "ARGOS-PAPER-BASKET", "market_data_source": "deterministic_placeholder"},
                    "strategy_context": {"strategy": "Workflow Proof Strategy", "objective": "controlled paper cognition pilot"},
                    "risk_constraints": {"live_trading": False, "max_position_size": 0.05, "max_cost_usd": self._real_api_config.max_cost_per_workflow_usd},
                },
                expected_output_schema=("summary", "evidence", "audit_identifier", "workflow_type", "workflow_stage", "initial_stage"),
                max_runtime_seconds=min(self._real_api_config.timeout_seconds, self.controlled_cognitive_pilot.limits.maximum_api_timeout_seconds) if real_enabled and self.controlled_cognitive_pilot.enabled else (self._real_api_config.timeout_seconds if real_enabled else 30),
                max_cost_usd=min(self._real_api_config.max_cost_per_workflow_usd, self.controlled_cognitive_pilot.limits.maximum_workflow_cost_usd) if real_enabled and self.controlled_cognitive_pilot.enabled else (self._real_api_config.max_cost_per_workflow_usd if real_enabled else 0.001),
                max_input_tokens=self._real_api_config.max_input_tokens if real_enabled else 128,
                max_output_tokens=self._real_api_config.max_output_tokens if real_enabled else 128,
                audit_identifier=audit_identifier,
                dry_run=not real_enabled,
                execution_mode=execution_mode,
                provider=provider,
                decision_object_id=decision_object_id,
                allow_fallback_to_dry_run=self._real_api_config.fallback_to_dry_run,
                prompt_contract_envelope=prompt_contract,
            )
        )

    def _authorize_gateway_credit(self, request: ApiExecutionRequest) -> dict[str, Any]:
        """Authorize one gateway request through the existing credit governor boundary."""
        purpose = "Real API Pilot" if request.execution_mode == "real_api_pilot" else "Ambiguous reasoning"
        return self.request_credit_activation(
            task_identifier=f"{request.workflow_id}-{request.task_type}",
            activating_source="Seeker" if request.requesting_office == "Analyst" else "Commander",
            receiving_office=request.requesting_office,
            purpose=purpose,
            required_output=f"{request.execution_mode} gateway output for {request.task_type}",
            maximum_runtime_minutes=max(1, round(request.max_runtime_seconds / 60)),
            maximum_credit_budget_usd=request.max_cost_usd,
            workflow="Paper Trading Workflow",
            organization=request.requesting_office,
            evidence_package=("TRADE-CANDIDATE", "THRESHOLD", request.prompt_template_id),
            return_route="Risk" if request.requesting_office == "Analyst" else "Commander Interface",
            workflow_id=request.workflow_id,
            workflow_token_id=request.workflow_token_id,
            office=request.requesting_office,
        )

    def configure_infrastructure(
        self,
        daily_budget_usd: float,
        monthly_budget_usd: float,
        runtime_limit_minutes: int,
        resource_mode: str,
        organization: str = "",
        organization_limit_usd: float | None = None,
    ) -> dict[str, Any]:
        """Apply Commander infrastructure controls."""
        override = self.infrastructure.configure_controls(
            daily_budget_usd=daily_budget_usd,
            monthly_budget_usd=monthly_budget_usd,
            runtime_limit_minutes=runtime_limit_minutes,
            resource_mode=resource_mode,
            organization=organization,
            organization_limit_usd=organization_limit_usd,
            timestamp_utc=_now(),
        )
        self._budget_limit_usd = max(0.0, round(float(monthly_budget_usd), 2))
        self._publish_enterprise_event(
            organization="Infrastructure",
            office="AI Resource Management",
            workflow="Infrastructure Control Workflow",
            task_identifier=override["overrideId"],
            event_category="INFRASTRUCTURE",
            severity="NOTICE",
            summary=f"Infrastructure controls set to {override['resourceMode']}",
            detailed_description="Commander updated AI resource budget, runtime, mode, or organization limits.",
            supporting_evidence=(override["overrideId"],),
            correlation_identifier=override["overrideId"],
            status="CONFIGURED",
        )
        return self.state()

    def record_infrastructure_optimization(self, action: str) -> dict[str, Any]:
        """Record a Commander-selected optimization action."""
        item = self.infrastructure.record_optimization_action(action, _now())
        self._publish_enterprise_event(
            organization="Infrastructure",
            office="AI Resource Management",
            workflow="Optimization Action Workflow",
            task_identifier=item["actionId"],
            event_category="INFRASTRUCTURE",
            severity="NOTICE",
            summary=f"Optimization action recorded: {action}",
            detailed_description="Commander recorded an infrastructure optimization action for historical evaluation.",
            supporting_evidence=(item["actionId"],),
            correlation_identifier=item["actionId"],
            status="RECORDED",
        )
        return self.state()

    def acknowledge_notification(self, notification_id: str) -> dict[str, Any]:
        """Acknowledge a Commander notification."""
        acknowledged = self.cnac.acknowledge(notification_id)
        self._publish_enterprise_event(
            organization="Commander Interface",
            office="Commander Notification & Alert Center",
            workflow="Notification Acknowledgment Workflow",
            task_identifier=acknowledged.notification_id,
            event_category="NOTIFICATION",
            severity="INFO",
            summary=f"Notification acknowledged: {acknowledged.notification_id}",
            detailed_description=f"Commander acknowledged {acknowledged.source_event_id}.",
            supporting_evidence=(acknowledged.source_event_id,),
            correlation_identifier=acknowledged.correlation_identifier,
            status="ACKNOWLEDGED",
        )
        return self.state()

    def escalate_notifications(self) -> dict[str, Any]:
        """Escalate unresolved Commander notifications."""
        self.cnac.escalate_unresolved()
        self._publish_enterprise_event(
            organization="Commander Interface",
            office="Commander Notification & Alert Center",
            workflow="Alert Escalation Workflow",
            task_identifier="CNAC-ESCALATE",
            event_category="NOTIFICATION",
            severity="WARNING",
            summary="Unresolved Commander alerts escalated",
            detailed_description="CNAC applied deterministic escalation rules to unresolved warnings and critical events.",
            correlation_identifier=f"CNAC-ESCALATE-{len(self.eab.search({})) + 1:06d}",
            status="ESCALATED",
        )
        return self.state()

    def generate_commander_briefing(self, briefing_type: str) -> dict[str, Any]:
        """Generate a recurring Commander briefing."""
        briefing = self.cnac.generate_briefing(briefing_type)
        self._publish_enterprise_event(
            organization="Commander Interface",
            office="Commander Notification & Alert Center",
            workflow="Commander Briefing Workflow",
            task_identifier=briefing.briefing_id,
            event_category="NOTIFICATION",
            severity="NOTICE",
            summary=f"{briefing_type} generated",
            detailed_description=f"CNAC generated {briefing_type} with {briefing.notification_count} notifications.",
            supporting_evidence=(briefing.briefing_id,),
            correlation_identifier=briefing.briefing_id,
            status="PUBLISHED",
        )
        state = self.state()
        state["commanderBriefing"] = briefing.__dict__
        return state

    def _command_context(self) -> dict[str, Any]:
        costs = self._cost_snapshot()
        return {
            "system_status": "NOMINAL",
            "organizations": tuple(group["name"] for group in _groups()) + ("Infrastructure",),
            "live_trading_enabled": self.config.configuration.live_trading_enabled,
            "risk_certified": False,
            "budget_status": costs.budget_status,
            "user_funds_halted": self.control.user_funds_halted,
        }

    def _publish_command_console_event(self, record: Any, status: str) -> Any:
        severity = "WARNING" if status in {"REJECTED", "FAILED"} else "NOTICE"
        return self._publish_enterprise_event(
            organization="Commander Interface",
            office="Command Console",
            workflow="Commander Command Workflow",
            task_identifier=record.command_id,
            event_category="COMMAND",
            severity=severity,
            summary=f"Command {record.command_name} {status.lower()}",
            detailed_description=record.detailed_results,
            supporting_evidence=record.supporting_evidence,
            correlation_identifier=record.correlation_identifier,
            status=status,
        )

    def configure_office_schedule(
        self,
        organization: str,
        office: str,
        operating_mode: str,
        resource_budget_usd: float,
        runtime_limit_minutes: int,
        time_zone: str = "America/Cancun",
        business_hours: str = "09:30-16:00",
    ) -> dict[str, Any]:
        """Configure a single office schedule from the dashboard."""
        configured = self.scheduler.configure(
            organization=organization,
            office=office,
            operating_mode=operating_mode,
            time_zone=time_zone,
            business_hours=business_hours,
            scheduled_tasks=("commander-configured-task",),
            wake_triggers=("Commander", "Enterprise Event", "Critical Alert"),
            sleep_triggers=("Workflow Complete", "Commander", "Runtime Limit"),
            runtime_limit_minutes=runtime_limit_minutes,
            resource_budget_usd=resource_budget_usd,
        )
        self._publish_enterprise_event(
            organization="Commander Interface",
            office="Office Scheduler",
            workflow="Schedule Configuration Workflow",
            task_identifier=configured.schedule_id,
            event_category="SCHEDULING",
            severity="NOTICE",
            summary=f"{organization}/{office} schedule configured",
            detailed_description=f"Operating mode set to {configured.operating_mode.value}; runtime limit {configured.runtime_limit_minutes} minutes.",
            supporting_evidence=(configured.schedule_id,),
            correlation_identifier=configured.schedule_id,
            status="CONFIGURED",
        )
        return self.state()

    def activate_office(self, organization: str, office: str, trigger: str = "Commander") -> dict[str, Any]:
        """Activate a single office."""
        activated = self.scheduler.activate(organization, office, trigger)
        self._publish_scheduler_transition(activated, "Office activated", "ACTIVE")
        return self.state()

    def suspend_office(self, organization: str, office: str, trigger: str = "Commander") -> dict[str, Any]:
        """Suspend a single office."""
        suspended = self.scheduler.suspend(organization, office, trigger)
        self._publish_scheduler_transition(suspended, "Office suspended", "SLEEPING")
        return self.state()

    def _route_enterprise_command(self, action: str) -> None:
        for target in ("Executive", "Seeker", "Analyst", "Risk", "Trader", "Historian", "Librarian", "Academy"):
            self._commands.append(
                OfficeCommand(
                    f"CMD-{len(self._commands) + 1:06d}",
                    target,
                    action,
                    "ACKNOWLEDGED",
                    _now(),
                )
            )
            self._publish_enterprise_event(
                organization="Commander Interface",
                office="Enterprise Activity Bus",
                workflow="Command Distribution Workflow",
                task_identifier=self._commands[-1].command_id,
                event_category="COMMAND",
                severity="INFO",
                summary=f"{action} routed to {target}",
                detailed_description=f"The Enterprise Activity Bus distributed {action} to {target}.",
                supporting_evidence=(self._commands[-1].command_id,),
                correlation_identifier=self._commands[-1].command_id,
            )

    def _publish_enterprise_event(self, **kwargs: Any) -> Any:
        with self._event_lock:
            return self.eab.publish(**kwargs)

    def _publish_workflow_event(self, workflow_id: str, summary: str, status: str) -> None:
        self._publish_enterprise_event(
            organization="Infrastructure",
            office="Enterprise Workflow Orchestrator",
            workflow="Workflow Execution Orchestration",
            task_identifier=workflow_id,
            event_category="WORKFLOW",
            severity="NOTICE",
            summary=summary,
            detailed_description="OE-010 deterministic workflow execution event.",
            supporting_evidence=(workflow_id,),
            correlation_identifier=workflow_id,
            status=status,
        )

    def _activate_organization(self, organization: str, trigger: str) -> None:
        for item in self.scheduler.snapshot()["offices"]:
            if item["organization"] == organization:
                activated = self.scheduler.activate(organization, item["office"], trigger)
                self._publish_scheduler_transition(activated, "Office activated", "ACTIVE")

    def _suspend_organization(self, organization: str, trigger: str) -> None:
        for item in self.scheduler.snapshot()["offices"]:
            if item["organization"] == organization:
                suspended = self.scheduler.suspend(organization, item["office"], trigger)
                self._publish_scheduler_transition(suspended, "Office suspended", "SLEEPING")

    def _configure_organization_mode(self, organization: str, mode: str) -> None:
        for item in self.scheduler.snapshot()["offices"]:
            if item["organization"] == organization:
                configured = self.scheduler.configure(
                    organization=organization,
                    office=item["office"],
                    operating_mode=mode,
                    scheduled_tasks=("commander-mode-change",),
                    wake_triggers=("Commander", "Enterprise Event", "Critical Alert"),
                    sleep_triggers=("Workflow Complete", "Commander", "Runtime Limit"),
                    runtime_limit_minutes=item["runtime_limit_minutes"],
                    resource_budget_usd=item["resource_budget_usd"],
                )
                self._publish_scheduler_transition(configured, f"Office mode set to {configured.operating_mode.value}", "CONFIGURED")

    def _configure_organization_schedule(self, organization: str, detail: str) -> None:
        for item in self.scheduler.snapshot()["offices"]:
            if item["organization"] == organization:
                configured = self.scheduler.configure(
                    organization=organization,
                    office=item["office"],
                    operating_mode=item["operating_mode"],
                    scheduled_tasks=(detail,),
                    wake_triggers=("Commander", "Enterprise Event", "Critical Alert", "Scheduled Event"),
                    sleep_triggers=("Workflow Complete", "Commander", "Runtime Limit"),
                    runtime_limit_minutes=item["runtime_limit_minutes"],
                    resource_budget_usd=item["resource_budget_usd"],
                )
                self._publish_scheduler_transition(configured, "Office schedule configured", "CONFIGURED")

    def _publish_scheduler_transition(self, office: Any, summary: str, status: str) -> None:
        self._publish_enterprise_event(
            organization="Commander Interface",
            office="Office Scheduler",
            workflow="Operating Mode Workflow",
            task_identifier=office.schedule_id,
            event_category="SCHEDULING",
            severity="NOTICE" if status != "SLEEPING" else "INFO",
            summary=f"{summary}: {office.organization}/{office.office}",
            detailed_description=f"{office.organization}/{office.office} transitioned to {office.status} in {office.operating_mode.value} mode.",
            supporting_evidence=(office.schedule_id,),
            correlation_identifier=office.schedule_id,
            status=status,
        )

    def _accrue_training_cost(self) -> None:
        self._self_training_ticks += 1
        return

    def _validate_law_vii_api_usage(self, *, workflow_id: str, workflow_token_id: str, office: str, credit_amount: float) -> tuple[bool, str, str]:
        ok, code, reason = self.workflow_orchestrator.validate_api_usage(workflow_id, workflow_token_id, office, credit_amount)
        if not ok:
            return ok, code, reason
        reserved = self._workflow_api_usage_usd.get(workflow_id, 0.0)
        workflow = next((item for item in self.workflow_orchestrator.snapshot()["workflows"] if item["workflow_id"] == workflow_id), None)
        if workflow is None:
            return False, "LAW_VII_VIOLATION_UNSCOPED_API_USAGE", "API usage referenced an unknown workflow."
        if workflow["credits_used"] + reserved + max(0.0, float(credit_amount)) > workflow["token"]["credit_budget"]:
            return False, "LAW_VII_VIOLATION_BUDGET_EXCEEDED", f"Workflow {workflow_id} credit budget would be exceeded."
        return ok, code, reason

    def _record_api_credit_usage(self, workflow_id: str, amount_usd: float) -> None:
        amount = round(max(0.0, float(amount_usd)), 4)
        self._workflow_api_usage_usd[workflow_id] = round(self._workflow_api_usage_usd.get(workflow_id, 0.0) + amount, 4)
        self._session_api_credits_usd = round(self._session_api_credits_usd + amount, 4)
        self._today_api_credits_usd = round(self._today_api_credits_usd + amount, 4)
        self._month_to_date_api_credits_usd = round(self._month_to_date_api_credits_usd + amount, 4)

    def _cost_snapshot(self) -> OperatingCostSnapshot:
        projected = round(max(self._month_to_date_api_credits_usd * 12, self._today_api_credits_usd * 30), 4)
        total = round(self._month_to_date_api_credits_usd + self._other_operating_expenses_usd, 4)
        ratio = total / self._budget_limit_usd if self._budget_limit_usd else 1.0
        status = "GREEN" if ratio < 0.65 else "YELLOW" if ratio < 0.9 else "RED"
        return OperatingCostSnapshot(
            self._session_api_credits_usd,
            self._today_api_credits_usd,
            self._month_to_date_api_credits_usd,
            projected,
            self._other_operating_expenses_usd,
            total,
            self._budget_limit_usd,
            status,
            self._session_api_credits_usd,
            0.0,
            round(sum(self._workflow_api_usage_usd.values()), 4),
        )


def create_runtime() -> ControlPanelRuntime:
    """Create local dashboard runtime."""
    return ControlPanelRuntime()


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _env_float(name: str, default: float) -> float:
    try:
        return max(0.0, float(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _groups() -> tuple[dict[str, Any], ...]:
    return (
        {"name": "Executive", "status": "NOMINAL", "color": "#4d63ff"},
        {"name": "Seeker", "status": "NOMINAL", "color": "#8c4dff"},
        {"name": "Analyst", "status": "NOMINAL", "color": "#efb13e"},
        {"name": "Risk", "status": "NOMINAL", "color": "#ff534a"},
        {"name": "Trader", "status": "NOMINAL", "color": "#39d5ef"},
        {"name": "Historian", "status": "NOMINAL", "color": "#68e24f"},
        {"name": "Librarian", "status": "NOMINAL", "color": "#f3a820"},
        {"name": "Academy", "status": "NOMINAL", "color": "#a454ff"},
    )


def _group_cards(training: bool) -> tuple[dict[str, Any], ...]:
    base = (
        ("Executive", "ACTIVE DECISIONS", 12, "PENDING REVIEWS", 3, "RECENT ACTIONS", 28),
        ("Seeker", "ACTIVE MISSIONS", 8 if training else 0, "DISCOVERIES TODAY", 15 if training else 0, "EVIDENCE ITEMS", 342),
        ("Analyst", "ACTIVE ANALYSES", 11 if training else 0, "PENDING APPROVALS", 4, "COMPLETED TODAY", 9),
        ("Risk", "ACTIVE REVIEWS", 10, "RISK ALERTS", 2, "LIMIT VIOLATIONS", 0),
        ("Trader", "PAPER ORDERS", 6 if training else 0, "OPEN POSITIONS", 23 if training else 0, "SIM TRADES TODAY", 37 if training else 0),
        ("Historian", "NEW REPORTS", 7, "VALIDATIONS", 14, "INSIGHTS TODAY", 21),
        ("Librarian", "NEW DOCUMENTS", 18, "VERSION UPDATES", 23, "ACTIVE CONTROLS", 156),
        ("Academy", "ACTIVE STUDENTS", 124, "COURSES ACTIVE", 27, "ASSESSMENTS TODAY", 63),
    )
    return tuple(
        {"name": name, "status": "NOMINAL", "metrics": ((a, av), (b, bv), (c, cv))}
        for name, a, av, b, bv, c, cv in base
    )


def _kpis(training: bool) -> tuple[dict[str, Any], ...]:
    boost = 0.4 if training else 0.0
    return (
        {"name": "Decision Quality Score", "value": round(94.7 + boost, 1)},
        {"name": "Risk Adjusted Returns", "value": 1.87},
        {"name": "Execution Quality Score", "value": round(98.3, 1)},
        {"name": "Evidence Quality Score", "value": round(96.1 + boost, 1)},
        {"name": "Model Accuracy Score", "value": round(92.8 + boost, 1)},
        {"name": "Overall Performance Score", "value": round(95.2 + boost, 1)},
    )


def _health_series(training: bool) -> tuple[int, ...]:
    start = 82 if training else 79
    return tuple(min(100, start + ((index * 7) % 13) + index // 4) for index in range(24))


def _schedule() -> tuple[dict[str, str], ...]:
    return (
        {"time": "11:00", "event": "Executive Review Meeting"},
        {"time": "12:30", "event": "Risk Committee Meeting"},
        {"time": "14:00", "event": "Model Calibration Update"},
        {"time": "15:30", "event": "Historian Insights Briefing"},
    )


def _default_activity() -> tuple[dict[str, str], ...]:
    return (
        _activity("EXECUTIVE", "New investment decision approved", "EID-2025-0514-12", "SUCCESS"),
        _activity("SEEKER", "New evidence package discovered", "EP-2025-0514-87", "SUCCESS"),
        _activity("ANALYST", "Analysis completed and approved", "AN-2025-0514-66", "SUCCESS"),
        _activity("RISK", "Risk review completed", "RR-2025-0514-41", "SUCCESS"),
        _activity("TRADER", "Paper order simulation ready", "ORD-2025-0514-228", "SUCCESS"),
        _activity("HISTORIAN", "New performance report generated", "PR-2025-0514-19", "SUCCESS"),
        _activity("LIBRARIAN", "Document version updated", "DOC-2025-0514-552", "SUCCESS"),
        _activity("ACADEMY", "Student assessment completed", "ASMT-2025-0514-128", "SUCCESS"),
    )


def _activity(group: str, message: str, reference: str, status: str) -> dict[str, str]:
    return {"time": datetime.now().strftime("%H:%M:%S"), "group": group, "message": message, "reference": reference, "status": status}


def _offices() -> tuple[dict[str, Any], ...]:
    groups = {
        "Executive": ("Commander", "Chief of Staff", "Dashboard", "Human Override", "Control Panel"),
        "Seeker": ("Technical", "Fundamental", "Macro", "News", "Options", "Crypto", "Events", "Alternative Data", "Fusion"),
        "Analyst": ("Statistical", "Technical", "Fundamental", "Macro", "Derivatives", "Behavioral", "Risk Interaction", "Review", "Fusion"),
        "Risk": ("Position", "Portfolio", "Liquidity", "Volatility", "Tail", "Bubble", "Recovery", "Fusion", "Readiness"),
        "Trader": ("Execution", "Order Management", "Broker Integration", "Execution Quality", "Position Management", "Monitoring", "Fusion", "Readiness"),
        "Historian": ("Performance", "Hypothesis", "Model Calibration", "Prompt Evaluation", "Decision", "Evidence", "Fusion", "Readiness"),
        "Librarian": ("Institutional Knowledge", "Doctrine", "Specifications", "Knowledge Graph", "Learning Integration", "Fusion", "Readiness"),
        "Academy": ("Framework", "Instruction", "Curriculum", "Assessment", "Case Study", "Finance Tutor", "Fusion", "Readiness"),
    }
    return tuple({"group": group, "offices": offices, "status": "NOMINAL"} for group, offices in groups.items())
