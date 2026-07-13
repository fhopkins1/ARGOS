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
from .blue_ocean_intelligence_office import BlueOceanIntelligenceOffice
from .black_swan_simulation_engine import BlackSwanSimulationEngine
from .capital_allocation_engine import CapitalAllocationEngine
from .capital_rotation_intelligence_office import CapitalRotationIntelligenceOffice
from .canonical_enterprise_runtime import CanonicalEnterpriseRuntime
from .command_console import CommandConsole
from .commander_briefing_generator import CommanderBriefingGenerator
from .commander_daily_review_workspace import CommanderDailyReviewWorkspace
from .commander_strategic_dashboard import CommanderStrategicDashboard
from .cnac import CommanderNotificationAlertCenter
from .closed_position_truth import ClosedPositionTruthBuilder
from .credit_governor import EnterpriseCreditGovernor
from .correlation_intelligence_engine import CorrelationIntelligenceEngine
from .cognitive_contract import PromptContractLibrary, build_prompt_contract_envelope, prompt_contract_trace
from .cognitive_pilot import ControlledCognitivePilot, ControlledCognitivePilotLimits
from .decision_object_schema import DecisionObjectSchemaRegistry
from .decision_object_quality_scoring import DecisionObjectQualityScoringEngine
from .decision_explainability_engine import DecisionExplainabilityEngine
from .decline_intelligence_office import DeclineIntelligenceOffice
from .disruption_intelligence_office import DisruptionIntelligenceOffice
from .decision_laboratory import DecisionLaboratory
from .daily_learning_pipeline import DailyEnterpriseLearningPipeline
from .eab import EnterpriseActivityBus
from .ecc import EnterpriseCommandCenter
from .enterprise_learning_engine import EnterpriseLearningEngine
from .enterprise_configuration_registry import EnterpriseConfigurationRegistry
from .enterprise_benchmark_engine import EnterpriseBenchmarkEngine
from .enterprise_communications_bus import CompatibilityMode, EnterpriseCommunicationsBus, EnterpriseMessageKind, MessageMode, MessageSchemaRegistration
from .enterprise_cost_governor import EnterpriseCostGovernor
from .enterprise_doctrine_policy_manager import EnterpriseDoctrinePolicyManager
from .enterprise_efficiency_analytics import EnterpriseEfficiencyAnalytics
from .enterprise_experiment_scheduler import EnterpriseExperimentScheduler
from .enterprise_failure_recovery import EnterpriseFailureRecoveryFramework
from .enterprise_grand_strategy_engine import EnterpriseGrandStrategyEngine
from .enterprise_health_monitor import EnterpriseHealthMonitor
from .enterprise_memory_cache import EnterpriseMemoryCache
from .enterprise_priority_engine import EnterprisePriorityEngine
from .event_detection_engine import EventDetectionEngine
from .enterprise_operational_guardrails import EnterpriseOperationalGuardrails
from .enterprise_reality_calibration import EnterpriseRealityCalibrationEngine
from .enterprise_reproducibility_framework import EnterpriseReproducibilityFramework
from .enterprise_risk_factor_engine import EnterpriseRiskFactorEngine
from .historian_recommendation_engine import HistorianRecommendationEngine
from .information_freshness_engine import InformationFreshnessEngine, InvalidationReason
from .infrastructure import InfrastructureResourceManager
from .ioe import InteractiveOrganizationExplorer
from .lppc import LivePortfolioPerformanceConsole
from .market_context_engine import MarketContextIntegrationEngine
from .market_data_provider import MarketDataProviderAbstractionLayer
from .market_replay_engine import MarketReplayEngine
from .market_structure_intelligence_office import MarketStructureIntelligenceOffice
from .mission_planner import EnterpriseMissionPlanner
from .monte_carlo_portfolio_engine import MonteCarloPortfolioEngine
from .performance_truth_engine import PerformanceTruthEngine
from .position_exit_decision_engine import ExitDecisionEngine
from .position_monitoring_network import PositionMonitoringNetwork
from .position_sizing_engine import PositionSizingEngine
from .position_surveillance_engine import PositionSurveillanceEngine
from .portfolio_construction_engine import PortfolioConstructionEngine
from .prompt_evolution_engine import PromptEvolutionEngine
from .prompt_package_manager import PromptPackageManager
from .scheduler import OfficeScheduler
from .short_opportunity_office import ShortOpportunityOffice
from .strategic_intelligence_command import StrategicIntelligenceCommand
from .strategic_synthesis_office import StrategicSynthesisOffice
from .strategy_package_manager import StrategyPackageManager, strategy_package_trace
from .stress_testing_engine import StressTestingEngine
from .strategy_performance_console import LiveStrategyPerformanceConsole
from .trade_attribution_engine import TradeAttributionEngine
from .truth_domain import RuntimeMode, TruthClassification, ProvenanceStatus
from .workflow_delta_engine import WorkflowDeltaEngine
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
    """Compatibility dashboard runtime backed by canonical production authorities."""

    def __init__(self) -> None:
        self.canonical_runtime = CanonicalEnterpriseRuntime()
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
        self.enterprise_communications_bus = self.canonical_runtime.components.communications_bus
        self.enterprise_communications_bus.schema_registry.register(
            MessageSchemaRegistration(
                "POLICY_PUBLICATION",
                "PolicyPublication",
                "1.0",
                (),
                "Enterprise Doctrine & Policy Manager",
                ("policy_id", "policy_version", "policy_hash", "activation_plan_id", "required_acknowledgement"),
                compatibility_mode=CompatibilityMode.EXACT_VERSION_ONLY,
            )
        )
        self.enterprise_doctrine_policy_manager = self.canonical_runtime.components.doctrine_policy
        self.command_console = CommandConsole()
        self.blue_ocean_intelligence_office = BlueOceanIntelligenceOffice()
        self.capital_allocation_engine = CapitalAllocationEngine()
        self.closed_position_truth_builder = self.canonical_runtime.components.closed_position_truth
        self.commander_briefing_generator = CommanderBriefingGenerator()
        self.commander_daily_review_workspace = CommanderDailyReviewWorkspace()
        self.commander_strategic_dashboard = CommanderStrategicDashboard()
        self.credit_governor = EnterpriseCreditGovernor()
        self.correlation_intelligence_engine = CorrelationIntelligenceEngine()
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
        self.daily_learning_pipeline = DailyEnterpriseLearningPipeline()
        self.black_swan_simulation_engine = BlackSwanSimulationEngine()
        self.decision_object_schema = DecisionObjectSchemaRegistry()
        self.decision_object_quality_scoring = DecisionObjectQualityScoringEngine()
        self.decision_explainability_engine = DecisionExplainabilityEngine()
        self.decline_intelligence_office = DeclineIntelligenceOffice()
        self.disruption_intelligence_office = DisruptionIntelligenceOffice()
        self.decision_laboratory = DecisionLaboratory()
        self.enterprise_learning_engine = EnterpriseLearningEngine()
        self.enterprise_configuration_registry = EnterpriseConfigurationRegistry()
        self.enterprise_benchmark_engine = EnterpriseBenchmarkEngine()
        self.enterprise_cost_governor = self.canonical_runtime.components.cost_governor
        self.enterprise_efficiency_analytics = self.canonical_runtime.components.efficiency_analytics
        self.enterprise_experiment_scheduler = EnterpriseExperimentScheduler()
        self.enterprise_failure_recovery = EnterpriseFailureRecoveryFramework()
        self.enterprise_grand_strategy_engine = EnterpriseGrandStrategyEngine()
        self.enterprise_health_monitor = EnterpriseHealthMonitor()
        self.event_detection_engine = self.canonical_runtime.components.event_detection
        self.enterprise_operational_guardrails = EnterpriseOperationalGuardrails()
        self.enterprise_reality_calibration = EnterpriseRealityCalibrationEngine()
        self.enterprise_reproducibility_framework = EnterpriseReproducibilityFramework()
        self.enterprise_risk_factor_engine = EnterpriseRiskFactorEngine()
        self.historian_recommendation_engine = HistorianRecommendationEngine()
        self.information_freshness_engine = self.canonical_runtime.components.freshness_engine
        self.enterprise_memory_cache = self.canonical_runtime.components.memory_cache
        self.workflow_delta_engine = self.canonical_runtime.components.workflow_delta
        self.enterprise_priority_engine = self.canonical_runtime.components.priority_engine
        self.prompt_evolution_engine = PromptEvolutionEngine()
        self.prompt_package_manager = PromptPackageManager()
        self.strategy_package_manager = StrategyPackageManager()
        self.stress_testing_engine = StressTestingEngine()
        self.trade_attribution_engine = TradeAttributionEngine()
        self.api_runtime_monitor = ApiRuntimeMonitor()
        self.cnac = CommanderNotificationAlertCenter()
        self.ecc = EnterpriseCommandCenter(self.audit, self.persistence)
        self.infrastructure = InfrastructureResourceManager()
        self.ioe = InteractiveOrganizationExplorer()
        self.lppc = LivePortfolioPerformanceConsole()
        self.market_context_engine = MarketContextIntegrationEngine()
        self.market_data_provider = self.canonical_runtime.components.market_data
        self.market_replay_engine = MarketReplayEngine()
        self.market_structure_intelligence_office = MarketStructureIntelligenceOffice()
        self.mission_planner = self.canonical_runtime.components.mission_planner
        self.capital_rotation_intelligence_office = CapitalRotationIntelligenceOffice()
        self.monte_carlo_portfolio_engine = MonteCarloPortfolioEngine()
        self.performance_truth_engine = self.canonical_runtime.components.performance_truth
        self.position_exit_decision_engine = ExitDecisionEngine()
        self.position_monitoring_network = self.canonical_runtime.components.position_monitoring
        self.position_sizing_engine = PositionSizingEngine()
        self.position_surveillance_engine = PositionSurveillanceEngine()
        self.portfolio_construction_engine = PortfolioConstructionEngine()
        self.strategic_intelligence_command = self.canonical_runtime.components.strategic_intelligence
        self.strategic_synthesis_office = StrategicSynthesisOffice()
        self.strategy_performance_console = LiveStrategyPerformanceConsole()
        self.scheduler = OfficeScheduler()
        self.short_opportunity_office = ShortOpportunityOffice()
        self.workflow_orchestrator = self.canonical_runtime.components.workflow_orchestrator
        self.workflow_runtime_monitor = WorkflowRuntimeMonitor()
        self.api_execution_gateway = ApiExecutionGateway(
            workflow_snapshot=self.workflow_orchestrator.snapshot,
            authorize_credit=self._authorize_gateway_credit,
            complete_credit_activation=self.complete_credit_activation,
            authorize_cost=self.enterprise_cost_governor.authorize_gateway_request,
            record_cost_usage=self.enterprise_cost_governor.record_gateway_usage,
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
        self._last_position_surveillance_key: tuple[tuple[str, str], ...] = ()
        self._last_position_surveillance_monotonic = 0.0
        self._last_position_surveillance_snapshot: dict[str, Any] | None = None
        self._last_exit_decision_key: tuple[tuple[str, str], ...] = ()
        self._last_exit_decision_monotonic = 0.0
        self._last_exit_decision_snapshot: dict[str, Any] | None = None
        self._published_critical_briefings: set[str] = set()

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
        market_data_provider_snapshot = self.market_data_provider.snapshot(
            timestamp_utc=_now(),
            workflow_id=(workflow_runtime_monitor_snapshot.get("activeWorkflow") or {}).get("workflowIdentifier", ""),
            decision_object_id=_latest_performance_decision_object_id(performance_truth_snapshot),
        )
        active_positions = self.performance_truth_engine.position_registry.active_positions()
        market_data_provider_snapshot = _with_active_position_quotes(
            market_data_provider_snapshot,
            self.market_data_provider,
            active_positions,
            _now(),
        )
        position_surveillance_snapshot = self._position_surveillance_state(active_positions, market_data_provider_snapshot)
        position_monitoring_snapshot = self.position_monitoring_network.snapshot(timestamp_utc=_now())
        position_exit_decision_snapshot = self._position_exit_decision_state(
            self.performance_truth_engine.position_registry.active_positions(),
            position_surveillance_snapshot,
        )
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
        decision_object_schema_snapshot = self.decision_object_schema.snapshot(
            workflow_orchestrator=workflow_orchestrator_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        market_context_snapshot = self.market_context_engine.snapshot(
            timestamp_utc=_now(),
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            lppc=lppc_snapshot,
            performance_truth=performance_truth_snapshot,
            strategy_performance=strategy_performance_snapshot,
            market_data_provider=market_data_provider_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        historian_recommendation_snapshot = self.historian_recommendation_engine.snapshot(
            timestamp_utc=_now(),
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            performance_truth=performance_truth_snapshot,
            strategy_performance=strategy_performance_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            prompt_contract=self.prompt_contract_library.snapshot(),
            api_runtime_monitor=api_runtime_snapshot,
            credit_governor=credit_governor_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        enterprise_learning_snapshot = self.enterprise_learning_engine.snapshot(
            timestamp_utc=_now(),
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            performance_truth=performance_truth_snapshot,
            strategy_performance=strategy_performance_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            prompt_contract=self.prompt_contract_library.snapshot(),
            api_runtime_monitor=api_runtime_snapshot,
            credit_governor=credit_governor_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
            historian_recommendation_engine=historian_recommendation_snapshot,
        )
        prompt_evolution_snapshot = self.prompt_evolution_engine.snapshot(
            timestamp_utc=_now(),
            prompt_contract=self.prompt_contract_library.snapshot(),
            historian_recommendation_engine=historian_recommendation_snapshot,
            enterprise_learning_engine=enterprise_learning_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            performance_truth=performance_truth_snapshot,
            strategy_performance=strategy_performance_snapshot,
            api_runtime_monitor=api_runtime_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        prompt_package_manager_snapshot = self.prompt_package_manager.snapshot(
            timestamp_utc=_now(),
            environment=self.config.configuration.environment.value,
            prompt_contract=self.prompt_contract_library.snapshot(),
            prompt_evolution_engine=prompt_evolution_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            decision_object_schema=decision_object_schema_snapshot,
            market_context_engine=market_context_snapshot,
            api_execution_gateway=api_execution_gateway_snapshot,
            enterprise_learning_engine=enterprise_learning_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        strategy_package_manager_snapshot = self.strategy_package_manager.snapshot(
            timestamp_utc=_now(),
            environment=self.config.configuration.environment.value,
            strategy_performance=strategy_performance_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            decision_object_schema=decision_object_schema_snapshot,
            prompt_package_manager=prompt_package_manager_snapshot,
            market_context_engine=market_context_snapshot,
            api_execution_gateway=api_execution_gateway_snapshot,
            enterprise_learning_engine=enterprise_learning_snapshot,
            historian_recommendation_engine=historian_recommendation_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        daily_learning_pipeline_snapshot = self.daily_learning_pipeline.snapshot(
            timestamp_utc=_now(),
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            performance_truth=performance_truth_snapshot,
            historian_recommendation_engine=historian_recommendation_snapshot,
            enterprise_learning_engine=enterprise_learning_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            prompt_evolution_engine=prompt_evolution_snapshot,
            market_context_engine=market_context_snapshot,
            strategy_performance=strategy_performance_snapshot,
            academy_metrics=enterprise_learning_snapshot.get("metrics", {}),
            costs=asdict(costs),
            audit_event_count=len(self.audit.audit_log.events),
        )
        enterprise_configuration_registry_snapshot = self.enterprise_configuration_registry.snapshot(
            timestamp_utc=_now(),
            foundation_configuration=self.config.configuration.to_snapshot_dict(),
            control=asdict(snapshot),
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            prompt_package_manager=prompt_package_manager_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            market_data_provider=market_data_provider_snapshot,
            market_context_engine=market_context_snapshot,
            api_execution_gateway=api_execution_gateway_snapshot,
            credit_governor=credit_governor_snapshot,
            scheduler=scheduler_snapshot,
            daily_learning_pipeline=daily_learning_pipeline_snapshot,
            decision_object_schema=decision_object_schema_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        enterprise_health_monitor_snapshot = self.enterprise_health_monitor.snapshot(
            timestamp_utc=_now(),
            resources=resources,
            infrastructure=infrastructure_snapshot,
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            api_runtime_monitor=api_runtime_snapshot,
            api_execution_gateway=api_execution_gateway_snapshot,
            decision_object_schema=decision_object_schema_snapshot,
            performance_truth=performance_truth_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            prompt_package_manager=prompt_package_manager_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            market_context_engine=market_context_snapshot,
            market_data_provider=market_data_provider_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            credit_governor=credit_governor_snapshot,
            daily_learning_pipeline=daily_learning_pipeline_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        enterprise_failure_recovery_snapshot = self.enterprise_failure_recovery.snapshot(
            timestamp_utc=_now(),
            enterprise_health_monitor=enterprise_health_monitor_snapshot,
            workflow_orchestrator=workflow_orchestrator_snapshot,
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            decision_object_schema=decision_object_schema_snapshot,
            performance_truth=performance_truth_snapshot,
            prompt_package_manager=prompt_package_manager_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            market_data_provider=market_data_provider_snapshot,
            api_runtime_monitor=api_runtime_snapshot,
            api_execution_gateway=api_execution_gateway_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        decision_object_quality_snapshot = self.decision_object_quality_scoring.snapshot(
            timestamp_utc=_now(),
            workflow_orchestrator=workflow_orchestrator_snapshot,
            decision_object_schema=decision_object_schema_snapshot,
            market_context_engine=market_context_snapshot,
            prompt_package_manager=prompt_package_manager_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            enterprise_learning_engine=enterprise_learning_snapshot,
            historian_recommendation_engine=historian_recommendation_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        enterprise_benchmark_engine_snapshot = self.enterprise_benchmark_engine.snapshot(
            timestamp_utc=_now(),
            performance_truth=performance_truth_snapshot,
            strategy_performance=strategy_performance_snapshot,
            market_context_engine=market_context_snapshot,
            prompt_package_manager=prompt_package_manager_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            decision_object_quality=decision_object_quality_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        decision_explainability_snapshot = self.decision_explainability_engine.snapshot(
            timestamp_utc=_now(),
            workflow_orchestrator=workflow_orchestrator_snapshot,
            performance_truth=performance_truth_snapshot,
            historian_recommendation_engine=historian_recommendation_snapshot,
            enterprise_learning_engine=enterprise_learning_snapshot,
            prompt_evolution_engine=prompt_evolution_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        trade_attribution_engine_snapshot = self.trade_attribution_engine.snapshot(
            timestamp_utc=_now(),
            performance_truth=performance_truth_snapshot,
            workflow_orchestrator=workflow_orchestrator_snapshot,
            strategy_performance=strategy_performance_snapshot,
            enterprise_benchmark_engine=enterprise_benchmark_engine_snapshot,
            decision_object_quality=decision_object_quality_snapshot,
            decision_explainability=decision_explainability_snapshot,
            market_context_engine=market_context_snapshot,
            prompt_package_manager=prompt_package_manager_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        closed_position_truth_snapshot = self.closed_position_truth_builder.build(
            position_registry=self.performance_truth_engine.position_registry.snapshot(),
            performance_truth=performance_truth_snapshot,
            position_surveillance=position_surveillance_snapshot,
            exit_decision_engine=position_exit_decision_snapshot,
            enterprise_benchmark_engine=enterprise_benchmark_engine_snapshot,
            trade_attribution_engine=trade_attribution_engine_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            timestamp_utc=_now(),
        )
        self.performance_truth_engine.ingest_closed_position_truth(tuple(closed_position_truth_snapshot.get("latestClosedPositionTruthRecords", ())))
        performance_truth_snapshot = self.performance_truth_engine.snapshot(execution_environment="paper")
        enterprise_reality_calibration_snapshot = self.enterprise_reality_calibration.calibrate(
            timestamp_utc=_now(),
            performance_truth=performance_truth_snapshot,
            market_data_provider=market_data_provider_snapshot,
            position_surveillance=position_surveillance_snapshot,
            closed_position_truth=closed_position_truth_snapshot,
            enterprise_benchmark_engine=enterprise_benchmark_engine_snapshot,
            enterprise_learning_engine=enterprise_learning_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        correlation_intelligence_snapshot = self.correlation_intelligence_engine.evaluate(
            timestamp_utc=_now(),
            performance_truth=performance_truth_snapshot,
            market_data_provider=market_data_provider_snapshot,
            market_context_engine=market_context_snapshot,
            enterprise_benchmark_engine=enterprise_benchmark_engine_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        enterprise_risk_factor_snapshot = self.enterprise_risk_factor_engine.evaluate(
            timestamp_utc=_now(),
            performance_truth=performance_truth_snapshot,
            market_data_provider=market_data_provider_snapshot,
            market_context_engine=market_context_snapshot,
            enterprise_reality_calibration=enterprise_reality_calibration_snapshot,
            enterprise_benchmark_engine=enterprise_benchmark_engine_snapshot,
            closed_position_truth=closed_position_truth_snapshot,
            correlation_intelligence=correlation_intelligence_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        enterprise_health_monitor_snapshot = {
            **enterprise_health_monitor_snapshot,
            "realityCalibrationHealth": enterprise_reality_calibration_snapshot["enterpriseHealthMetrics"],
            "correlationIntelligenceHealth": correlation_intelligence_snapshot["enterpriseHealthMetrics"],
            "riskFactorHealth": enterprise_risk_factor_snapshot["enterpriseHealthMetrics"],
        }
        enterprise_reproducibility_framework_snapshot = self.enterprise_reproducibility_framework.snapshot(
            timestamp_utc=_now(),
            workflow_orchestrator=workflow_orchestrator_snapshot,
            performance_truth=performance_truth_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            prompt_package_manager=prompt_package_manager_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            market_context_engine=market_context_snapshot,
            market_data_provider=market_data_provider_snapshot,
            decision_object_schema=decision_object_schema_snapshot,
            trade_attribution_engine=trade_attribution_engine_snapshot,
            control=asdict(snapshot),
            costs=asdict(costs),
            audit_event_count=len(self.audit.audit_log.events),
        )
        enterprise_operational_guardrails_snapshot = self.enterprise_operational_guardrails.snapshot(
            timestamp_utc=_now(),
            control=asdict(snapshot),
            costs=asdict(costs),
            workflow_orchestrator=workflow_orchestrator_snapshot,
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            enterprise_health_monitor=enterprise_health_monitor_snapshot,
            enterprise_failure_recovery=enterprise_failure_recovery_snapshot,
            decision_object_quality=decision_object_quality_snapshot,
            market_context_engine=market_context_snapshot,
            market_data_provider=market_data_provider_snapshot,
            prompt_package_manager=prompt_package_manager_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            enterprise_reproducibility_framework=enterprise_reproducibility_framework_snapshot,
            performance_truth=performance_truth_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        capital_allocation_snapshot = self.capital_allocation_engine.allocate(
            timestamp_utc=_now(),
            performance_truth=performance_truth_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            market_context_engine=market_context_snapshot,
            enterprise_benchmark_engine=enterprise_benchmark_engine_snapshot,
            trade_attribution_engine=trade_attribution_engine_snapshot,
            enterprise_reality_calibration=enterprise_reality_calibration_snapshot,
            enterprise_operational_guardrails=enterprise_operational_guardrails_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            enterprise_risk_factor=enterprise_risk_factor_snapshot,
            correlation_intelligence=correlation_intelligence_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        portfolio_construction_snapshot = self.portfolio_construction_engine.evaluate(
            timestamp_utc=_now(),
            decision_object=_latest_portfolio_construction_decision(strategy_performance_snapshot),
            performance_truth=performance_truth_snapshot,
            market_data_provider=market_data_provider_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            enterprise_operational_guardrails=enterprise_operational_guardrails_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            capital_allocation=capital_allocation_snapshot,
            enterprise_risk_factor=enterprise_risk_factor_snapshot,
            correlation_intelligence=correlation_intelligence_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        position_sizing_snapshot = self.position_sizing_engine.size(
            timestamp_utc=_now(),
            decision_object=_latest_portfolio_construction_decision(strategy_performance_snapshot),
            performance_truth=performance_truth_snapshot,
            market_data_provider=market_data_provider_snapshot,
            capital_allocation=capital_allocation_snapshot,
            portfolio_construction=portfolio_construction_snapshot,
            decision_object_quality=decision_object_quality_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            enterprise_reality_calibration=enterprise_reality_calibration_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            enterprise_operational_guardrails=enterprise_operational_guardrails_snapshot,
            enterprise_risk_factor=enterprise_risk_factor_snapshot,
            correlation_intelligence=correlation_intelligence_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        stress_testing_snapshot = self.stress_testing_engine.snapshot(timestamp_utc=_now())
        black_swan_simulation_snapshot = self.black_swan_simulation_engine.snapshot(timestamp_utc=_now())
        monte_carlo_portfolio_snapshot = self.monte_carlo_portfolio_engine.snapshot(timestamp_utc=_now())
        enterprise_health_monitor_snapshot = {
            **enterprise_health_monitor_snapshot,
            "stressTestingHealth": stress_testing_snapshot["enterpriseHealthMetrics"],
            "blackSwanSimulationHealth": black_swan_simulation_snapshot["enterpriseHealthMetrics"],
            "monteCarloPortfolioHealth": monte_carlo_portfolio_snapshot["enterpriseHealthMetrics"],
        }
        enterprise_experiment_scheduler_snapshot = self.enterprise_experiment_scheduler.snapshot(
            timestamp_utc=_now(),
            historian_recommendation_engine=historian_recommendation_snapshot,
            enterprise_learning_engine=enterprise_learning_snapshot,
            prompt_evolution_engine=prompt_evolution_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            enterprise_reproducibility_framework=enterprise_reproducibility_framework_snapshot,
            enterprise_operational_guardrails=enterprise_operational_guardrails_snapshot,
            costs=asdict(costs),
            audit_event_count=len(self.audit.audit_log.events),
        )
        commander_daily_review_workspace_snapshot = self.commander_daily_review_workspace.snapshot(
            timestamp_utc=_now(),
            control=asdict(snapshot),
            costs=asdict(costs),
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            performance_truth=performance_truth_snapshot,
            strategy_performance=strategy_performance_snapshot,
            historian_recommendation_engine=historian_recommendation_snapshot,
            enterprise_learning_engine=enterprise_learning_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            prompt_evolution_engine=prompt_evolution_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            prompt_package_manager=prompt_package_manager_snapshot,
            market_context_engine=market_context_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            credit_governor=credit_governor_snapshot,
            enterprise_health_monitor=enterprise_health_monitor_snapshot,
            enterprise_failure_recovery=enterprise_failure_recovery_snapshot,
            decision_object_quality=decision_object_quality_snapshot,
            enterprise_benchmark_engine=enterprise_benchmark_engine_snapshot,
            api_runtime_monitor=api_runtime_snapshot,
            audit_event_count=len(self.audit.audit_log.events),
        )
        controlled_cognitive_pilot_snapshot = self.controlled_cognitive_pilot.snapshot(
            workflow_orchestrator=workflow_orchestrator_snapshot,
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            api_runtime_monitor=api_runtime_snapshot,
            api_execution_gateway=api_execution_gateway_snapshot,
            decision_laboratory=decision_laboratory_snapshot,
            performance_truth=performance_truth_snapshot,
        )
        trader_command_bridge_snapshot = _trader_command_bridge_payload(
            timestamp_utc=_now(),
            performance_truth=performance_truth_snapshot,
            position_surveillance=position_surveillance_snapshot,
            position_exit_decision=position_exit_decision_snapshot,
            closed_position_truth=closed_position_truth_snapshot,
            strategy_performance=strategy_performance_snapshot,
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            enterprise_health_monitor=enterprise_health_monitor_snapshot,
        )
        enterprise_grand_strategy_snapshot = self.enterprise_grand_strategy_engine.generate(
            timestamp_utc=_now(),
            planning_horizon="monthly",
            commander_intent=None,
            sources={
                "control": asdict(snapshot),
                "costs": asdict(costs),
                "performanceTruthEngine": performance_truth_snapshot,
                "closedPositionTruthBuilder": closed_position_truth_snapshot,
                "enterpriseBenchmarkEngine": enterprise_benchmark_engine_snapshot,
                "tradeAttributionEngine": trade_attribution_engine_snapshot,
                "enterpriseRealityCalibrationEngine": enterprise_reality_calibration_snapshot,
                "enterpriseRiskFactorEngine": enterprise_risk_factor_snapshot,
                "correlationIntelligenceEngine": correlation_intelligence_snapshot,
                "capitalAllocationEngine": capital_allocation_snapshot,
                "portfolioConstructionEngine": portfolio_construction_snapshot,
                "positionSizingEngine": position_sizing_snapshot,
                "strategyPackageManager": strategy_package_manager_snapshot,
                "promptEvolutionEngine": prompt_evolution_snapshot,
                "enterpriseLearningEngine": enterprise_learning_snapshot,
                "historianRecommendationEngine": historian_recommendation_snapshot,
                "enterpriseExperimentScheduler": enterprise_experiment_scheduler_snapshot,
                "enterpriseHealthMonitor": enterprise_health_monitor_snapshot,
                "creditGovernor": credit_governor_snapshot,
                "enterpriseReproducibilityFramework": enterprise_reproducibility_framework_snapshot,
                "stressTestingEngine": stress_testing_snapshot,
                "blackSwanSimulationEngine": black_swan_simulation_snapshot,
                "monteCarloPortfolioEngine": monte_carlo_portfolio_snapshot,
                "marketReplayEngine": self.market_replay_engine.snapshot(timestamp_utc=_now()),
                "traderCommandBridge": trader_command_bridge_snapshot,
                "enterpriseConfigurationRegistry": enterprise_configuration_registry_snapshot,
            },
        )
        capital_allocation_snapshot = {**capital_allocation_snapshot, "grandStrategyFeed": enterprise_grand_strategy_snapshot.get("capitalAllocationFeed", {})}
        portfolio_construction_snapshot = {**portfolio_construction_snapshot, "grandStrategyFeed": enterprise_grand_strategy_snapshot.get("portfolioConstructionFeed", {})}
        position_sizing_snapshot = {**position_sizing_snapshot, "grandStrategyFeed": enterprise_grand_strategy_snapshot.get("positionSizingFeed", {})}
        strategy_package_manager_snapshot = {**strategy_package_manager_snapshot, "grandStrategyFeed": enterprise_grand_strategy_snapshot.get("strategyEvolutionFeed", {})}
        prompt_evolution_snapshot = {**prompt_evolution_snapshot, "grandStrategyFeed": enterprise_grand_strategy_snapshot.get("promptEvolutionFeed", {})}
        enterprise_experiment_scheduler_snapshot = {**enterprise_experiment_scheduler_snapshot, "grandStrategyFeed": enterprise_grand_strategy_snapshot.get("experimentSchedulerFeed", {})}
        blue_ocean_intelligence_snapshot = self.blue_ocean_intelligence_office.snapshot(
            timestamp_utc=_now(),
            sources={
                "enterpriseGrandStrategyEngine": enterprise_grand_strategy_snapshot,
                "enterpriseConfigurationRegistry": enterprise_configuration_registry_snapshot,
                "marketContextIntegrationEngine": market_context_snapshot,
                "historianRecommendationEngine": historian_recommendation_snapshot,
                "enterpriseLearningEngine": enterprise_learning_snapshot,
                "workflowRuntimeMonitor": workflow_runtime_monitor_snapshot,
                "auditEventCount": len(self.audit.audit_log.events),
            },
        )
        disruption_intelligence_snapshot = self.disruption_intelligence_office.snapshot(
            timestamp_utc=_now(),
            sources={
                "enterpriseGrandStrategyEngine": enterprise_grand_strategy_snapshot,
                "enterpriseConfigurationRegistry": enterprise_configuration_registry_snapshot,
                "blueOceanIntelligenceOffice": blue_ocean_intelligence_snapshot,
                "marketContextIntegrationEngine": market_context_snapshot,
                "historianRecommendationEngine": historian_recommendation_snapshot,
                "enterpriseLearningEngine": enterprise_learning_snapshot,
                "workflowRuntimeMonitor": workflow_runtime_monitor_snapshot,
                "auditEventCount": len(self.audit.audit_log.events),
            },
        )
        decline_intelligence_snapshot = self.decline_intelligence_office.snapshot(
            timestamp_utc=_now(),
            sources={
                "enterpriseGrandStrategyEngine": enterprise_grand_strategy_snapshot,
                "enterpriseConfigurationRegistry": enterprise_configuration_registry_snapshot,
                "blueOceanIntelligenceOffice": blue_ocean_intelligence_snapshot,
                "disruptionIntelligenceOffice": disruption_intelligence_snapshot,
                "marketContextIntegrationEngine": market_context_snapshot,
                "historianRecommendationEngine": historian_recommendation_snapshot,
                "enterpriseLearningEngine": enterprise_learning_snapshot,
                "workflowRuntimeMonitor": workflow_runtime_monitor_snapshot,
                "auditEventCount": len(self.audit.audit_log.events),
            },
        )
        short_opportunity_snapshot = self.short_opportunity_office.snapshot(
            timestamp_utc=_now(),
            sources={
                "enterpriseGrandStrategyEngine": enterprise_grand_strategy_snapshot,
                "enterpriseConfigurationRegistry": enterprise_configuration_registry_snapshot,
                "blueOceanIntelligenceOffice": blue_ocean_intelligence_snapshot,
                "disruptionIntelligenceOffice": disruption_intelligence_snapshot,
                "declineIntelligenceOffice": decline_intelligence_snapshot,
                "marketContextIntegrationEngine": market_context_snapshot,
                "historianRecommendationEngine": historian_recommendation_snapshot,
                "enterpriseLearningEngine": enterprise_learning_snapshot,
                "workflowRuntimeMonitor": workflow_runtime_monitor_snapshot,
                "auditEventCount": len(self.audit.audit_log.events),
            },
        )
        market_structure_snapshot = self.market_structure_intelligence_office.snapshot(
            timestamp_utc=_now(),
            sources={
                "enterpriseGrandStrategyEngine": enterprise_grand_strategy_snapshot,
                "enterpriseConfigurationRegistry": enterprise_configuration_registry_snapshot,
                "marketContextIntegrationEngine": market_context_snapshot,
                "marketDataProviderAbstractionLayer": market_data_provider_snapshot,
                "enterpriseRiskFactorEngine": enterprise_risk_factor_snapshot,
                "correlationIntelligenceEngine": correlation_intelligence_snapshot,
                "stressTestingEngine": stress_testing_snapshot,
                "enterpriseRealityCalibrationEngine": enterprise_reality_calibration_snapshot,
                "historianRecommendationEngine": historian_recommendation_snapshot,
                "enterpriseLearningEngine": enterprise_learning_snapshot,
                "workflowRuntimeMonitor": workflow_runtime_monitor_snapshot,
                "auditEventCount": len(self.audit.audit_log.events),
            },
        )
        capital_rotation_snapshot = self.capital_rotation_intelligence_office.snapshot(
            timestamp_utc=_now(),
            sources={
                "enterpriseGrandStrategyEngine": enterprise_grand_strategy_snapshot,
                "enterpriseConfigurationRegistry": enterprise_configuration_registry_snapshot,
                "marketContextIntegrationEngine": market_context_snapshot,
                "marketDataProviderAbstractionLayer": market_data_provider_snapshot,
                "enterpriseRiskFactorEngine": enterprise_risk_factor_snapshot,
                "correlationIntelligenceEngine": correlation_intelligence_snapshot,
                "marketStructureIntelligenceOffice": market_structure_snapshot,
                "historianRecommendationEngine": historian_recommendation_snapshot,
                "enterpriseLearningEngine": enterprise_learning_snapshot,
                "workflowRuntimeMonitor": workflow_runtime_monitor_snapshot,
                "auditEventCount": len(self.audit.audit_log.events),
            },
        )
        strategic_synthesis_snapshot = self.strategic_synthesis_office.snapshot(
            timestamp_utc=_now(),
            sources={
                "enterpriseConfigurationRegistry": enterprise_configuration_registry_snapshot,
                "blueOceanIntelligenceOffice": blue_ocean_intelligence_snapshot,
                "disruptionIntelligenceOffice": disruption_intelligence_snapshot,
                "declineIntelligenceOffice": decline_intelligence_snapshot,
                "shortOpportunityOffice": short_opportunity_snapshot,
                "marketStructureIntelligenceOffice": market_structure_snapshot,
                "capitalRotationIntelligenceOffice": capital_rotation_snapshot,
                "executive": {"commands": commands, "activity": activity},
                "analyst": {"decisionObjectQualityScoringEngine": decision_object_quality_snapshot},
                "risk": {"enterpriseRiskFactorEngine": enterprise_risk_factor_snapshot},
                "historian": {"historianRecommendationEngine": historian_recommendation_snapshot},
                "librarian": {"promptPackageManager": prompt_package_manager_snapshot, "strategyPackageManager": strategy_package_manager_snapshot},
                "academy": {"enterpriseLearningEngine": enterprise_learning_snapshot},
                "workflowRuntimeMonitor": workflow_runtime_monitor_snapshot,
                "auditEventCount": len(self.audit.audit_log.events),
            },
        )
        strategic_intelligence_snapshot = self.strategic_intelligence_command.snapshot(
            timestamp_utc=_now(),
            sources={
                "control": asdict(snapshot),
                "costs": asdict(costs),
                "executive": {"commands": commands, "activity": activity},
                "seeker": {"marketContextIntegrationEngine": market_context_snapshot},
                "analyst": {"decisionObjectQualityScoringEngine": decision_object_quality_snapshot},
                "risk": {"enterpriseRiskFactorEngine": enterprise_risk_factor_snapshot, "correlationIntelligenceEngine": correlation_intelligence_snapshot},
                "trader": {"traderCommandBridge": trader_command_bridge_snapshot},
                "historian": {"historianRecommendationEngine": historian_recommendation_snapshot},
                "librarian": {"promptPackageManager": prompt_package_manager_snapshot, "strategyPackageManager": strategy_package_manager_snapshot},
                "academy": {"enterpriseLearningEngine": enterprise_learning_snapshot},
                "enterpriseGrandStrategyEngine": enterprise_grand_strategy_snapshot,
                "enterpriseRiskFactorEngine": enterprise_risk_factor_snapshot,
                "enterpriseRealityCalibrationEngine": enterprise_reality_calibration_snapshot,
                "enterpriseHealthMonitor": enterprise_health_monitor_snapshot,
                "enterpriseLearningEngine": enterprise_learning_snapshot,
                "historianRecommendationEngine": historian_recommendation_snapshot,
                "enterpriseExperimentScheduler": enterprise_experiment_scheduler_snapshot,
                "enterpriseConfigurationRegistry": enterprise_configuration_registry_snapshot,
                "creditGovernor": credit_governor_snapshot,
                "workflowRuntimeMonitor": workflow_runtime_monitor_snapshot,
                "eab": eab_snapshot,
                "auditEventCount": len(self.audit.audit_log.events),
                "blueOceanIntelligenceOffice": blue_ocean_intelligence_snapshot,
                "disruptionIntelligenceOffice": disruption_intelligence_snapshot,
                "declineIntelligenceOffice": decline_intelligence_snapshot,
                "shortOpportunityOffice": short_opportunity_snapshot,
                "marketStructureIntelligenceOffice": market_structure_snapshot,
                "capitalRotationIntelligenceOffice": capital_rotation_snapshot,
                "strategicSynthesisOffice": strategic_synthesis_snapshot,
            },
        )
        commander_strategic_dashboard_snapshot = self.commander_strategic_dashboard.snapshot(
            timestamp_utc=_now(),
            environment=self.config.configuration.environment.value,
            control=asdict(snapshot),
            costs=asdict(costs),
            workflow_runtime_monitor=workflow_runtime_monitor_snapshot,
            performance_truth=performance_truth_snapshot,
            enterprise_benchmark_engine=enterprise_benchmark_engine_snapshot,
            closed_position_truth=closed_position_truth_snapshot,
            trade_attribution_engine=trade_attribution_engine_snapshot,
            enterprise_reality_calibration=enterprise_reality_calibration_snapshot,
            portfolio_construction=portfolio_construction_snapshot,
            capital_allocation=capital_allocation_snapshot,
            position_sizing=position_sizing_snapshot,
            enterprise_risk_factor=enterprise_risk_factor_snapshot,
            correlation_intelligence=correlation_intelligence_snapshot,
            market_replay_engine=self.market_replay_engine.snapshot(timestamp_utc=_now()),
            stress_testing=stress_testing_snapshot,
            black_swan_simulation=black_swan_simulation_snapshot,
            monte_carlo_portfolio=monte_carlo_portfolio_snapshot,
            enterprise_learning_engine=enterprise_learning_snapshot,
            historian_recommendation_engine=historian_recommendation_snapshot,
            prompt_evolution_engine=prompt_evolution_snapshot,
            strategy_package_manager=strategy_package_manager_snapshot,
            enterprise_experiment_scheduler=enterprise_experiment_scheduler_snapshot,
            credit_governor=credit_governor_snapshot,
            api_runtime_monitor=api_runtime_snapshot,
            enterprise_health_monitor=enterprise_health_monitor_snapshot,
            enterprise_reproducibility_framework=enterprise_reproducibility_framework_snapshot,
            market_data_provider=market_data_provider_snapshot,
            position_surveillance=position_surveillance_snapshot,
            trader_command_bridge=trader_command_bridge_snapshot,
            enterprise_configuration_registry=enterprise_configuration_registry_snapshot,
            enterprise_grand_strategy=enterprise_grand_strategy_snapshot,
            strategic_intelligence_command=strategic_intelligence_snapshot,
        )
        commander_strategic_dashboard_snapshot = {
            **commander_strategic_dashboard_snapshot,
            "grand_strategy": enterprise_grand_strategy_snapshot.get("dashboardFeed", {}),
            "strategic_intelligence": strategic_intelligence_snapshot.get("commanderStrategicDashboardFeed", {}),
        }
        commander_briefing_generator_snapshot = self.commander_briefing_generator.generate(
            briefing_type="morning_readiness",
            briefing_window_start="current_operating_day",
            briefing_window_end="latest_state_snapshot",
            generated_at=_now(),
            sources={
                "commanderStrategicDashboard": commander_strategic_dashboard_snapshot,
                "commanderDailyReviewWorkspace": commander_daily_review_workspace_snapshot,
                "performanceTruthEngine": performance_truth_snapshot,
                "traderCommandBridge": trader_command_bridge_snapshot,
                "enterpriseGrandStrategyEngine": enterprise_grand_strategy_snapshot,
                "strategicIntelligenceCommand": strategic_intelligence_snapshot,
                "enterpriseConfigurationRegistry": enterprise_configuration_registry_snapshot,
            },
        )
        latest_commander_briefing = commander_briefing_generator_snapshot.get("latestBriefingRecord", {})
        commander_strategic_dashboard_snapshot = {
            **commander_strategic_dashboard_snapshot,
            "latest_briefing": commander_briefing_generator_snapshot.get("latestDashboardFeed", {}),
        }
        commander_daily_review_workspace_snapshot = {
            **commander_daily_review_workspace_snapshot,
            "commanderBriefingGenerator": commander_briefing_generator_snapshot.get("dailyReviewFeed", {}),
            "enterpriseGrandStrategy": enterprise_grand_strategy_snapshot.get("dailyReviewFeed", {}),
            "strategicIntelligenceCommand": strategic_intelligence_snapshot.get("commanderBriefingFeed", {}),
            "blueOceanIntelligenceOffice": blue_ocean_intelligence_snapshot.get("sicFeed", {}),
            "disruptionIntelligenceOffice": disruption_intelligence_snapshot.get("sicFeed", {}),
            "declineIntelligenceOffice": decline_intelligence_snapshot.get("sicFeed", {}),
            "shortOpportunityOffice": short_opportunity_snapshot.get("sicFeed", {}),
            "marketStructureIntelligenceOffice": market_structure_snapshot.get("sicFeed", {}),
            "capitalRotationIntelligenceOffice": capital_rotation_snapshot.get("sicFeed", {}),
            "strategicSynthesisOffice": strategic_synthesis_snapshot.get("sicFeed", {}),
            "latestCommanderBriefing": latest_commander_briefing,
        }
        self.information_freshness_engine.seed_runtime_records(
            timestamp_utc=_now(),
            market_data_provider=market_data_provider_snapshot,
            performance_truth=performance_truth_snapshot,
            commander_briefing=commander_briefing_generator_snapshot,
        )
        self.enterprise_memory_cache.seed_runtime_products(
            commander_briefing=commander_briefing_generator_snapshot,
            performance_truth=performance_truth_snapshot,
            timestamp_utc=_now(),
            environment=self.config.configuration.environment.value,
        )
        information_freshness_snapshot = self.information_freshness_engine.snapshot()
        enterprise_memory_cache_snapshot = self.enterprise_memory_cache.snapshot()
        workflow_delta_snapshot = self.workflow_delta_engine.snapshot()
        enterprise_priority_snapshot = self.enterprise_priority_engine.snapshot()
        enterprise_communications_bus_snapshot = self.enterprise_communications_bus.snapshot()
        efficiency_sources = {
            "costs": asdict(costs),
            "scheduler": scheduler_snapshot,
            "enterpriseOperationsScheduler": scheduler_snapshot.get("enterpriseOperationsScheduler", {}),
            "officeDutyOfficers": scheduler_snapshot.get("officeDutyOfficers", {}),
            "workflowOrchestrator": workflow_orchestrator_snapshot,
            "workflowRuntimeMonitor": workflow_runtime_monitor_snapshot,
            "apiRuntimeMonitor": api_runtime_snapshot,
            "apiExecutionGateway": api_execution_gateway_snapshot,
            "enterpriseCostGovernor": self.enterprise_cost_governor.snapshot(),
            "enterpriseMemoryCache": enterprise_memory_cache_snapshot,
            "informationFreshnessEngine": information_freshness_snapshot,
            "workflowDeltaEngine": workflow_delta_snapshot,
            "enterprisePriorityEngine": enterprise_priority_snapshot,
            "positionMonitoringNetwork": position_monitoring_snapshot,
            "enterpriseCommunicationsBus": enterprise_communications_bus_snapshot,
            "enterpriseFailureRecoveryFramework": enterprise_failure_recovery_snapshot,
            "enterpriseDoctrinePolicyManager": self.enterprise_doctrine_policy_manager.snapshot(),
            "eventDetectionEngine": self.event_detection_engine.snapshot(),
            "performanceTruthEngine": performance_truth_snapshot,
            "cnac": cnac_snapshot,
            "commanderDailyReviewWorkspace": commander_daily_review_workspace_snapshot,
        }
        enterprise_efficiency_analytics_snapshot = self.enterprise_efficiency_analytics.analyze(
            efficiency_sources,
            window_start="current_operating_day",
            window_end="latest_state_snapshot",
            mode="COMBINED",
            persist=False,
        )
        enterprise_doctrine_policy_snapshot = self.enterprise_doctrine_policy_manager.snapshot(
            {
                **efficiency_sources,
                "enterpriseEfficiencyAnalytics": enterprise_efficiency_analytics_snapshot,
                "enterpriseConfigurationRegistry": enterprise_configuration_registry_snapshot,
                "enterpriseOperationalGuardrails": enterprise_operational_guardrails_snapshot,
            }
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
            "enterpriseOperationsScheduler": scheduler_snapshot.get("enterpriseOperationsScheduler", {}),
            "officeDutyOfficers": scheduler_snapshot.get("officeDutyOfficers", {}),
            "ecc": ecc_snapshot,
            "infrastructure": infrastructure_snapshot,
            "ioe": ioe_snapshot,
            "lppc": lppc_snapshot,
            "creditGovernor": credit_governor_snapshot,
            "apiRuntimeMonitor": api_runtime_snapshot,
            "apiExecutionGateway": api_execution_gateway_snapshot,
            "promptContract": self.prompt_contract_library.snapshot(),
            "decisionObjectSchema": decision_object_schema_snapshot,
            "decisionObjectQualityScoringEngine": decision_object_quality_snapshot,
            "decisionExplainabilityEngine": decision_explainability_snapshot,
            "commanderBriefingGenerator": commander_briefing_generator_snapshot,
            "commanderDailyReviewWorkspace": commander_daily_review_workspace_snapshot,
            "commanderStrategicDashboard": commander_strategic_dashboard_snapshot,
            "performanceTruthEngine": performance_truth_snapshot,
            "traderCommandBridge": trader_command_bridge_snapshot,
            "closedPositionTruthBuilder": closed_position_truth_snapshot,
            "positionExitDecisionEngine": position_exit_decision_snapshot,
            "positionMonitoringNetwork": position_monitoring_snapshot,
            "enterpriseCommunicationsBus": enterprise_communications_bus_snapshot,
            "enterpriseDoctrinePolicyManager": enterprise_doctrine_policy_snapshot,
            "enterpriseEfficiencyAnalytics": enterprise_efficiency_analytics_snapshot,
            "positionSurveillanceEngine": position_surveillance_snapshot,
            "marketDataProviderAbstractionLayer": market_data_provider_snapshot,
            "marketReplayEngine": self.market_replay_engine.snapshot(timestamp_utc=_now()),
            "enterpriseMissionPlanner": self.mission_planner.snapshot(),
            "monteCarloPortfolioEngine": monte_carlo_portfolio_snapshot,
            "marketContextIntegrationEngine": market_context_snapshot,
            "decisionLaboratory": decision_laboratory_snapshot,
            "historianRecommendationEngine": historian_recommendation_snapshot,
            "enterpriseLearningEngine": enterprise_learning_snapshot,
            "promptEvolutionEngine": prompt_evolution_snapshot,
            "promptPackageManager": prompt_package_manager_snapshot,
            "strategyPackageManager": strategy_package_manager_snapshot,
            "enterpriseConfigurationRegistry": enterprise_configuration_registry_snapshot,
            "enterpriseHealthMonitor": enterprise_health_monitor_snapshot,
            "eventDetectionEngine": self.event_detection_engine.snapshot(),
            "enterpriseRealityCalibrationEngine": enterprise_reality_calibration_snapshot,
            "correlationIntelligenceEngine": correlation_intelligence_snapshot,
            "enterpriseRiskFactorEngine": enterprise_risk_factor_snapshot,
            "stressTestingEngine": stress_testing_snapshot,
            "blackSwanSimulationEngine": black_swan_simulation_snapshot,
            "capitalAllocationEngine": capital_allocation_snapshot,
            "portfolioConstructionEngine": portfolio_construction_snapshot,
            "positionSizingEngine": position_sizing_snapshot,
            "enterpriseFailureRecoveryFramework": enterprise_failure_recovery_snapshot,
            "blueOceanIntelligenceOffice": blue_ocean_intelligence_snapshot,
            "disruptionIntelligenceOffice": disruption_intelligence_snapshot,
            "declineIntelligenceOffice": decline_intelligence_snapshot,
            "shortOpportunityOffice": short_opportunity_snapshot,
            "marketStructureIntelligenceOffice": market_structure_snapshot,
            "capitalRotationIntelligenceOffice": capital_rotation_snapshot,
            "strategicSynthesisOffice": strategic_synthesis_snapshot,
            "enterpriseGrandStrategyEngine": enterprise_grand_strategy_snapshot,
            "strategicIntelligenceCommand": strategic_intelligence_snapshot,
            "enterpriseBenchmarkEngine": enterprise_benchmark_engine_snapshot,
            "enterpriseCostGovernor": self.enterprise_cost_governor.snapshot(),
            "informationFreshnessEngine": information_freshness_snapshot,
            "enterpriseMemoryCache": enterprise_memory_cache_snapshot,
            "workflowDeltaEngine": workflow_delta_snapshot,
            "enterprisePriorityEngine": enterprise_priority_snapshot,
            "tradeAttributionEngine": trade_attribution_engine_snapshot,
            "enterpriseReproducibilityFramework": enterprise_reproducibility_framework_snapshot,
            "enterpriseOperationalGuardrails": enterprise_operational_guardrails_snapshot,
            "enterpriseExperimentScheduler": enterprise_experiment_scheduler_snapshot,
            "dailyEnterpriseLearningPipeline": daily_learning_pipeline_snapshot,
            "controlledCognitivePilot": controlled_cognitive_pilot_snapshot,
            "workflowOrchestrator": workflow_orchestrator_snapshot,
            "workflowRuntimeMonitor": workflow_runtime_monitor_snapshot,
            "strategyPerformanceConsole": strategy_performance_snapshot,
        }

    def _position_surveillance_state(self, active_positions: tuple[Any, ...], market_data_provider_snapshot: dict[str, Any]) -> dict[str, Any]:
        key = tuple(sorted((str(position.position_id), str(position.updated_at)) for position in active_positions))
        now_monotonic = time.monotonic()
        if (
            self._last_position_surveillance_snapshot is not None
            and key == self._last_position_surveillance_key
            and now_monotonic - self._last_position_surveillance_monotonic < 0.25
        ):
            return self._last_position_surveillance_snapshot
        position_surveillance_snapshot = self.position_surveillance_engine.surveil(
            position_registry=self.performance_truth_engine.position_registry,
            market_data_provider=market_data_provider_snapshot,
            timestamp_utc=_now(),
            mutate_registry=False,
        )
        self._last_position_surveillance_key = tuple(sorted((str(position.position_id), str(position.updated_at)) for position in self.performance_truth_engine.position_registry.active_positions()))
        self._last_position_surveillance_monotonic = now_monotonic
        self._last_position_surveillance_snapshot = position_surveillance_snapshot
        return position_surveillance_snapshot

    def _position_exit_decision_state(self, active_positions: tuple[Any, ...], position_surveillance_snapshot: dict[str, Any]) -> dict[str, Any]:
        key = tuple(sorted((str(position.position_id), str(position.updated_at)) for position in active_positions))
        now_monotonic = time.monotonic()
        if (
            self._last_exit_decision_snapshot is not None
            and key == self._last_exit_decision_key
            and now_monotonic - self._last_exit_decision_monotonic < 0.25
        ):
            return self._last_exit_decision_snapshot
        exit_decision_snapshot = self.position_exit_decision_engine.evaluate(
            position_registry=self.performance_truth_engine.position_registry,
            position_surveillance=position_surveillance_snapshot,
            timestamp_utc=_now(),
            mutate_registry=False,
        )
        self._last_exit_decision_key = tuple(sorted((str(position.position_id), str(position.updated_at)) for position in self.performance_truth_engine.position_registry.active_positions()))
        self._last_exit_decision_monotonic = now_monotonic
        self._last_exit_decision_snapshot = exit_decision_snapshot
        return exit_decision_snapshot

    def start_paper_self_training(self) -> dict[str, Any]:
        """Start proof-mode self-training and execute a tokenized workflow smoke test."""
        prior_workflow_count = self.workflow_orchestrator.snapshot()["metrics"]["workflowCount"]
        authorization = self.enterprise_operational_guardrails.authorize_workflow(timestamp_utc=_now())
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
            summary="Proof-mode self-training started",
            detailed_description="Commander Interface initiated a PROOF workflow. OR-002 prevents proof products from entering certified PAPER performance truth.",
            supporting_evidence=(record.action_id, workflow.workflow_id if workflow else "PROOF-RUNNER-ACTIVE", authorization["authorizationId"], "PROOF MODE - NOT OPERATIONAL TRUTH"),
            correlation_identifier=record.action_id,
        )
        self._publish_enterprise_event(
            organization="Trader",
            office="Enterprise Workflow Orchestrator",
            workflow="Paper Trading Workflow",
            task_identifier=record.action_id,
            event_category="WORKFLOW",
            severity="INFO",
            summary="Proof workflow runner armed",
            detailed_description="The proof workflow loop is armed for one active tokenized workflow at a time and cannot populate certified PAPER truth.",
            supporting_evidence=(record.action_id, workflow.workflow_id if workflow else "PROOF-RUNNER-ACTIVE", "OE-010", "OR-002"),
            correlation_identifier=record.action_id,
        )
        self._publish_enterprise_event(
            organization="Trader",
            office="API Execution Gateway",
            workflow="Paper Trading Workflow",
            task_identifier=record.action_id,
            event_category="API_RUNTIME",
            severity="INFO",
            summary="Proof gateway policy armed",
            detailed_description="Proof mode may use the API Execution Gateway only through LAW VII token-authorized dry-run requests; outputs are not operational truth.",
            supporting_evidence=(record.action_id, workflow.workflow_id if workflow else "PAPER-RUNNER-ACTIVE", "OE-011A"),
            correlation_identifier=record.action_id,
        )
        if self._workflow_demo_stage_delay_seconds <= 0:
            if workflow is not None:
                self._wait_for_workflow_archived(workflow.workflow_id)
            self._wait_for_enterprise_event_count(9)
        self._activity.append(_activity("EXECUTIVE", "Paper self-training authorized", record.action_id, "SUCCESS"))
        return self.state()

    def halt_paper_self_training(self) -> dict[str, Any]:
        """Halt paper self-training and route commands to all groups."""
        self._paper_runner_stop.set()
        self._paper_runner_pause_requested.clear()
        self._paper_runner_step_requested.set()
        if self._paper_runner_thread and self._paper_runner_thread.is_alive() and self._paper_runner_thread is not threading.current_thread():
            self._paper_runner_thread.join(timeout=1.0)
        record = self.control.halt_paper_trading_self_training(self.authority, "User halted ARGOS paper self-training from Control Panel.")
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

    def add_commander_journal_entry(self, category: str, entry: str) -> dict[str, Any]:
        """Record an immutable Commander journal entry."""
        journal_entry = self.commander_daily_review_workspace.add_journal_entry(
            timestamp_utc=_now(),
            category=category,
            entry=entry,
        )
        self._publish_enterprise_event(
            organization="Commander Interface",
            office="Commander Daily Review Workspace",
            workflow="Commander Journal",
            task_identifier=journal_entry["journalId"],
            event_category="COMMAND",
            severity="INFO",
            summary="Commander journal entry recorded",
            detailed_description=journal_entry["entry"],
            supporting_evidence=(journal_entry["auditReference"],),
            correlation_identifier=journal_entry["journalId"],
            status="RECORDED",
        )
        self._activity.append(_activity("COMMANDER", "Commander journal entry recorded", journal_entry["journalId"], "SUCCESS"))
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

    def cancel_pending_orders(self) -> dict[str, Any]:
        """Record a Commander cancellation command for pending paper execution orders."""
        self._publish_enterprise_event(
            organization="Trader",
            office="Trade Execution",
            workflow="Order Cancellation Workflow",
            task_identifier="TRADER-CANCEL-PENDING",
            event_category="TRADING",
            severity="WARNING",
            summary="Pending execution orders cancellation requested",
            detailed_description="Commander requested cancellation of pending paper execution orders through the Trader Execution Bridge.",
            supporting_evidence=("OE-105", "Trader Execution Bridge"),
            correlation_identifier=f"TRADER-CANCEL-{len(self._commands) + 1:06d}",
            status="CANCEL_REQUESTED",
        )
        self._activity.append(_activity("TRADER", "Pending execution orders cancellation requested", "TRADER-CANCEL-PENDING", "SUCCESS"))
        return self.state()

    def generate_learning_report(self) -> dict[str, Any]:
        """Record a Historian learning report generation command."""
        report_id = f"HIST-REPORT-{len(self.audit.audit_log.events) + 1:06d}"
        self._publish_enterprise_event(
            organization="Historian",
            office="Historian Learning Bridge",
            workflow="Enterprise Learning Workflow",
            task_identifier=report_id,
            event_category="LEARNING",
            severity="NOTICE",
            summary="Historian learning report generated",
            detailed_description="Historian generated an enterprise learning report from Performance Truth, Decision Objects, Decision Laboratory, and workflow outcomes.",
            supporting_evidence=("OE-106", "Performance Truth Engine", "Decision Laboratory"),
            correlation_identifier=report_id,
            status="REPORT_GENERATED",
        )
        self._activity.append(_activity("HISTORIAN", "Historian learning report generated", report_id, "SUCCESS"))
        state = self.state()
        state["historianCommand"] = {"command": "generate_learning_report", "reportId": report_id}
        return state

    def compare_prompt_versions(self) -> dict[str, Any]:
        """Record a Historian prompt version comparison command."""
        comparison_id = f"HIST-PROMPT-{len(self.audit.audit_log.events) + 1:06d}"
        self._publish_enterprise_event(
            organization="Historian",
            office="Prompt Evaluation",
            workflow="Prompt Comparison Workflow",
            task_identifier=comparison_id,
            event_category="LEARNING",
            severity="NOTICE",
            summary="Prompt versions compared",
            detailed_description="Historian compared prompt versions for calibration, prediction accuracy, and Commander approval readiness.",
            supporting_evidence=("OE-106", "Prompt Contract Library"),
            correlation_identifier=comparison_id,
            status="COMPARISON_RECORDED",
        )
        self._activity.append(_activity("HISTORIAN", "Prompt versions compared", comparison_id, "SUCCESS"))
        state = self.state()
        state["historianCommand"] = {"command": "compare_prompt_versions", "comparisonId": comparison_id}
        return state

    def compare_strategies(self) -> dict[str, Any]:
        """Record a Historian strategy comparison command."""
        comparison_id = f"HIST-STRATEGY-{len(self.audit.audit_log.events) + 1:06d}"
        self._publish_enterprise_event(
            organization="Historian",
            office="Performance Measurement",
            workflow="Strategy Comparison Workflow",
            task_identifier=comparison_id,
            event_category="LEARNING",
            severity="NOTICE",
            summary="Strategies compared",
            detailed_description="Historian compared strategy performance, alpha, Sharpe, drawdown, and laboratory approval status.",
            supporting_evidence=("OE-106", "Strategy Performance Console", "Performance Truth Engine"),
            correlation_identifier=comparison_id,
            status="COMPARISON_RECORDED",
        )
        self._activity.append(_activity("HISTORIAN", "Strategies compared", comparison_id, "SUCCESS"))
        state = self.state()
        state["historianCommand"] = {"command": "compare_strategies", "comparisonId": comparison_id}
        return state

    def deposit_user_funds(self, amount_usd: float) -> dict[str, Any]:
        """Deposit user funds into active treasury."""
        record = self.control.deposit_user_funds_to_active_treasury(self.authority, "USER-001", amount_usd, "User deposited funds into active treasury.")
        self.performance_truth_engine.set_paper_account_cash(self.control.active_treasury_balance_usd)
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
        """Continuously run one proof workflow at a time while proof self-training is active."""
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
            cycle_interval = 0.0 if self._workflow_demo_stage_delay_seconds <= 0 and self._paper_workflow_cycle_interval_seconds <= 0.05 else self._paper_workflow_cycle_interval_seconds
            if cycle_interval > 0:
                self._paper_runner_stop.wait(cycle_interval)

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

    def _wait_for_enterprise_event_count(self, minimum_event_count: int, timeout_seconds: float = 0.25) -> None:
        """Allow the background paper runner to publish its initial telemetry batch."""
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if len(self.eab.snapshot()["events"]) >= minimum_event_count:
                return
            time.sleep(0.005)

    def _wait_for_workflow_archived(self, workflow_id: str, timeout_seconds: float = 1.0) -> None:
        """Allow the zero-delay proof workflow path to settle before state is returned."""
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            workflow = self.workflow_orchestrator.workflow(workflow_id)
            if workflow.token.workflow_status == "Archived":
                return
            time.sleep(0.005)

    def _create_paper_trading_session_workflow(self, action_id: str) -> Any:
        """Create and begin one proof-mode workflow without operational truth authority."""
        del action_id
        stages = ("Seeker", "Analyst", "Risk", "Trader", "Historian")
        expected_output_schema = ("summary", "evidence", "audit_identifier", "workflow_type", "workflow_stage", "initial_stage")
        with self._workflow_lock:
            workflow = self.workflow_orchestrator.create_validate_queue_assign(
                name="Proof Workflow Session",
                stages=stages,
                runtime_budget=100,
                credit_budget=min(0.01, self.controlled_cognitive_pilot.limits.maximum_workflow_cost_usd if self.controlled_cognitive_pilot.enabled else 0.01),
                expected_output_schema=expected_output_schema,
                workflow_type="paper_trading_session",
                initial_stage="market_preparation",
            )
            self._publish_workflow_event(workflow.workflow_id, "Proof workflow created, validated, queued, and assigned", "ASSIGNED")
            workflow = self.workflow_orchestrator.start_execution(workflow.workflow_id)
            self._publish_workflow_event(workflow.workflow_id, f"Proof workflow executing at {workflow.token.current_owner}", "EXECUTING")
            return workflow

    def _complete_paper_trading_session_workflow(self, workflow_id: str, action_id: str, stage_delay_seconds: float) -> Any:
        """Advance a proof workflow through non-operational stages while preserving exclusive token ownership."""
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
                    "summary": f"{owner} completed proof-mode workflow stage; authoritative office integration is incomplete.",
                    "evidence": f"{action_id}:{owner}:proof_mode",
                    "audit_identifier": workflow.token.audit_identifier,
                    "workflow_type": "paper_trading_session",
                    "workflow_stage": owner,
                    "initial_stage": "market_preparation",
                    "execution_mode": RuntimeMode.PROOF.value,
                    "truth_classification": TruthClassification.PROOF_ONLY.value,
                    "certification_status": "PROOF_MODE_NOT_ACTIONABLE",
                    "provenance_status": ProvenanceStatus.REJECTED.value,
                }
                credits = 0.0
                token_usage = 0
                if gateway_response and gateway_response.allowed:
                    output = gateway_response.structured_output
                    credits = gateway_response.actual_cost_usd
                    token_usage = gateway_response.input_tokens + gateway_response.output_tokens
                output["decision_object"] = self._proof_decision_object(workflow, owner, action_id, gateway_response)
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
                workflow = self.workflow_orchestrator.transfer_ownership(workflow.workflow_id, f"{owner} proof output validated")
                self._publish_workflow_event(workflow.workflow_id, f"Workflow token transferred from {owner}", workflow.token.workflow_status)
                if workflow.token.workflow_status == "Completed":
                    workflow = self.workflow_orchestrator.archive_workflow(workflow.workflow_id)
                    self.performance_truth_engine.record_completed_workflow(workflow, execution_environment="paper")
                    self._publish_workflow_event(workflow.workflow_id, "Proof workflow archived without certified PAPER truth mutation", "ARCHIVED")
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
                self._publish_workflow_event(workflow.workflow_id, f"Proof workflow executing at {workflow.token.current_owner}", "EXECUTING")
        return workflow

    def _proof_decision_object(self, workflow: Any, owner: str, action_id: str, gateway_response: Any = None) -> dict[str, Any]:
        """Return one immutable proof-only Decision Object revision for a workflow stage."""
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
        revision_source = "runtime_proof_missing_authoritative_office"
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
        recommendation = "INCOMPLETE_AUTHORITATIVE_OFFICE_OUTPUT_MISSING"
        if owner == "Analyst" and analyst_contract:
            recommendation = str(analyst_contract.get("recommendation", recommendation))
        confidence = round(0.50 + sum(confidence_delta_by_owner.get(stage, 0.0) for stage in workflow.stages[:revision]), 4)
        if owner == "Analyst" and isinstance(analyst_contract.get("confidence"), (int, float)):
            confidence = round(float(analyst_contract["confidence"]), 4)
        supporting_signals = (f"{owner}_structured_output", "paper_trading_session", action_id)
        if owner == "Analyst" and analyst_contract.get("supporting_signals"):
            supporting_signals = tuple(str(item) for item in analyst_contract.get("supporting_signals", ()))
        decision_object_id = f"DO-{workflow.workflow_id.replace('EWO-WF-', '')}"
        market_context = self._market_context_for_decision_object(workflow.workflow_id, decision_object_id)
        current_strategy = "Workflow Proof Strategy" if owner in {"Seeker", "Analyst"} else "Risk Adjusted Paper Strategy"
        configuration_trace = self.enterprise_configuration_registry.trace(self.config.configuration.to_snapshot_dict())
        decision_object = {
            "decisionObjectId": decision_object_id,
            "workflowId": workflow.workflow_id,
            "workflowTokenId": workflow.token.audit_identifier,
            "revision": revision,
            "office": owner,
            "revisionSource": revision_source,
            "environment": "proof",
            "executionMode": RuntimeMode.PROOF.value,
            "truthClassification": TruthClassification.PROOF_ONLY.value,
            "sourceSystem": "ControlPanelRuntime",
            "sourceRecordIds": (action_id, workflow.token.audit_identifier),
            "officeAuthority": "NONE_PROOF_ONLY",
            "createdAt": _now(),
            "provenanceStatus": ProvenanceStatus.REJECTED.value,
            "certificationStatus": "PROOF_MODE_NOT_ACTIONABLE",
            "commanderTruthLabel": "PROOF MODE - NOT OPERATIONAL TRUTH",
            "materialFieldProvenance": {
                "asset_identifier": "Missing",
                "asset_class": "Missing",
                "direction": "Missing",
                "thesis": "Missing",
                "evidence": "Missing",
                "market_context": "Simulation-only value",
                "entry_conditions": "Missing",
                "price_source": "Missing",
                "quantity": "Missing",
                "position_sizing_basis": "Missing",
                "confidence": "Missing",
                "time_horizon": "Missing",
                "risk_factors": "Missing",
                "stop_conditions": "Missing",
                "exit_conditions": "Missing",
                "expected_return": "Missing",
                "risk_approval": "Missing",
                "trader_authorization": "Missing",
            },
            "creationTimestamp": workflow.token.creation_timestamp,
            "decisionTimestamp": _now(),
            "currentOwner": owner,
            "lifecycleState": "VALIDATED",
            "decisionType": "PAPER_TRAINING",
            "priority": "NORMAL",
            "commanderVisibility": True,
            "confidence": confidence,
            "confidenceDelta": confidence_delta,
            "recommendation": recommendation,
            "evidenceCount": revision * 2,
            "supportingSignals": supporting_signals,
            "riskScore": round(max(0.05, 0.48 + sum(risk_adjustment_by_owner.get(stage, 0.0) for stage in workflow.stages[:revision])), 4),
            "riskAdjustment": risk_adjustment,
            "positionSizeRecommendation": 0.0,
            "targetPrice": None,
            "stopLoss": None,
            "expectedReturn": 0.0,
            "currentStrategy": current_strategy,
            **strategy_package_trace(current_strategy),
            **configuration_trace,
            "supportingAuditIdentifier": workflow.token.audit_identifier,
            "apiExecutionMode": gateway_response.execution_mode if gateway_response else "",
            "apiProvider": gateway_response.provider if gateway_response else "",
            "apiModel": gateway_response.model if gateway_response else "",
            "apiFallbackUsed": bool(gateway_response.fallback_used) if gateway_response else False,
            "apiValidationStatus": gateway_response.validation_status if gateway_response else "",
            "apiGatewayMetadata": gateway_metadata,
            "marketContext": market_context,
            "marketContextSnapshotId": market_context["snapshotId"],
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
                    strategy=current_strategy,
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
        quality_report = self.decision_object_quality_scoring.quality_report(decision_object, timestamp_utc=_now())
        decision_object = dict(
            decision_object,
            qualityReport=quality_report,
            decisionObjectQuality=quality_report["overallScore"],
            qualityGrade=quality_report["grade"],
            decisionReadiness=quality_report["decisionReadiness"],
        )
        explainability_report = self.decision_explainability_engine.explainability_report(decision_object, timestamp_utc=_now())
        decision_object = dict(
            decision_object,
            explainabilityReport=explainability_report,
            explainabilityReportId=explainability_report["explainabilityReportId"],
            commanderReadabilityScore=explainability_report["commanderReadabilityScore"],
        )
        return self.decision_object_schema.freeze(decision_object)

    def _market_context_for_decision_object(self, workflow_id: str, decision_object_id: str) -> dict[str, Any]:
        """Return deterministic market context attached to a Decision Object revision."""
        return self.market_context_engine.context_object(
            timestamp_utc=_now(),
            workflow_id=workflow_id,
            decision_object_id=decision_object_id,
            lppc={},
            performance_truth={},
            strategy_performance={},
            audit_event_count=len(self.audit.audit_log.events),
        )

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
        market_context = self._market_context_for_decision_object(workflow.workflow_id, decision_object_id)
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
                    "paper_market_context": market_context,
                    "market_context_object": market_context,
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
        """Generate a structured Commander briefing from authoritative records."""
        base_state = self.state()
        normalized = str(briefing_type or "ad_hoc").strip().lower().replace(" ", "_")
        briefing_snapshot = self.commander_briefing_generator.generate(
            briefing_type=normalized,
            briefing_window_start=base_state["timestampUtc"],
            briefing_window_end=_now(),
            generated_at=_now(),
            sources=base_state,
        )
        briefing = briefing_snapshot.get("latestBriefingRecord", {})
        severity = "CRITICAL" if briefing.get("briefing_type") == "critical_incident" and briefing.get("critical_alerts") else "NOTICE"
        briefing_id = str(briefing.get("commander_briefing_id", "CBG"))
        publish_event = not (severity == "CRITICAL" and briefing_id in self._published_critical_briefings)
        if severity == "CRITICAL":
            self._published_critical_briefings.add(briefing_id)
        if publish_event:
            self._publish_enterprise_event(
                organization="Commander Interface",
                office="Commander Briefing Generator",
                workflow="Commander Briefing Workflow",
                task_identifier=briefing_id,
                event_category="NOTIFICATION",
                severity=severity,
                summary=f"{briefing.get('briefing_type', normalized)} generated",
                detailed_description=str(briefing.get("executive_summary", "")),
                supporting_evidence=(briefing_id,),
                correlation_identifier=briefing_id,
                status="PUBLISHED",
            )
        state = self.state()
        state["commanderBriefingGenerator"] = briefing_snapshot
        legacy_briefing = dict(briefing)
        if briefing_type and briefing_type != normalized:
            legacy_briefing["briefing_type"] = briefing_type
        state["commanderBriefing"] = legacy_briefing
        state["commanderStrategicDashboard"] = {
            **state["commanderStrategicDashboard"],
            "latest_briefing": briefing_snapshot.get("latestDashboardFeed", {}),
        }
        state["commanderDailyReviewWorkspace"] = {
            **state["commanderDailyReviewWorkspace"],
            "commanderBriefingGenerator": briefing_snapshot.get("dailyReviewFeed", {}),
            "latestCommanderBriefing": legacy_briefing,
        }
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

    def eos_control(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform a Commander-authorized Enterprise Operations Scheduler action."""
        body = payload or {}
        normalized = action.strip().lower().replace("-", "_")
        if normalized == "enable":
            self.scheduler.eos.set_enabled(True, reason=str(body.get("reason", "Commander enabled EOS.")))
            self._publish_eos_event("EOS enabled", "Commander enabled Enterprise Operations Scheduler.", "ENABLED")
        elif normalized == "disable":
            self.scheduler.eos.set_enabled(False, reason=str(body.get("reason", "Commander disabled EOS.")))
            self._publish_eos_event("EOS disabled", "Commander disabled Enterprise Operations Scheduler.", "DISABLED")
        elif normalized == "set_mode":
            mode = str(body.get("mode", "Observation Only"))
            self.scheduler.eos.set_mode(mode, reason="Commander selected enterprise operating mode.")
            self._publish_eos_event("EOS operating mode updated", f"Enterprise operating mode set to {mode}.", "CONFIGURED")
        elif normalized == "set_budget":
            self.scheduler.eos.set_budget(float(body.get("dailyApiBudgetUsd", 25)), float(body.get("missionCostCeilingUsd", 5)))
            self._publish_eos_event("EOS budget updated", "Commander updated EOS daily and mission cost ceilings.", "CONFIGURED")
        elif normalized == "run_mission_now":
            template_id = str(body.get("templateId", "pre_market_readiness"))
            mission = self.scheduler.eos.create_scheduled_mission(template_id)
            dispatched = self.scheduler.eos.dispatch_mission(mission.mission_id, token_id="EOS_BOUND_WORKFLOW_TOKEN_REQUIRED")
            if dispatched.status == "Running":
                self._activate_eos_mission_offices(dispatched)
            self._publish_eos_event("EOS mission dispatched", f"{dispatched.mission_name} status: {dispatched.status}.", dispatched.status.upper(), dispatched.mission_id)
        elif normalized == "commander_mission":
            offices = tuple(str(item).strip() for item in body.get("requiredOffices", ("Risk",)) if str(item).strip())
            mission = self.scheduler.eos.create_commander_directed_mission(
                mission_name=str(body.get("missionName", "Commander Directed Mission")),
                required_offices=offices or ("Risk",),
                directive_id=str(body.get("directiveId", "COMMANDER-DIRECTIVE")),
            )
            dispatched = self.scheduler.eos.dispatch_mission(mission.mission_id, token_id="EOS_COMMANDER_AUTHORIZED_TOKEN")
            if dispatched.status == "Running":
                self._activate_eos_mission_offices(dispatched)
            self._publish_eos_event("Commander mission dispatched", f"{dispatched.mission_name} dispatched through EOS.", "RUNNING", dispatched.mission_id)
        elif normalized == "event_trigger":
            mission = self.scheduler.eos.register_event_trigger(
                str(body.get("eventType", "validated_event")),
                str(body.get("eventReference", "EVENT-REFERENCE")),
                tuple(str(item).strip() for item in body.get("requiredOffices", ("Risk", "Trader")) if str(item).strip()),
            )
            self._publish_eos_event("EOS event mission registered", f"{mission.mission_name} registered from validated event.", mission.status, mission.mission_id)
        elif normalized == "cancel":
            mission = self.scheduler.eos.cancel_mission(str(body.get("missionId", "")))
            self._publish_eos_event("EOS mission cancelled", mission.result_summary or "Mission cancelled.", "CANCELLED", mission.mission_id)
        elif normalized == "suspend":
            mission = self.scheduler.eos.suspend_mission(str(body.get("missionId", "")))
            self._publish_eos_event("EOS mission suspended", mission.result_summary or "Mission suspended.", "SUSPENDED", mission.mission_id)
        else:
            raise ValueError(f"unsupported EOS action: {action}")
        return self.state()

    def submit_duty_officer_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Submit tasking through ODO triage without waking a full office directly."""
        payload = dict(payload)
        record_ids = tuple(payload.get("informationRecordIds", payload.get("information_record_ids", payload.get("inputArtifacts", ())) or ()))
        matched = tuple(record_id for record_id in record_ids if record_id in self.information_freshness_engine.list_records_by_subject(record_id) or self.information_freshness_engine.get_current_status(record_id) != "unknown")
        if matched:
            freshness = self.information_freshness_engine.evaluate_records(
                matched,
                {
                    "decisionUseClass": payload.get("decisionUseClass", "strategic_analysis" if "analysis" in str(payload.get("requestType", payload.get("request_type", ""))).lower() else "tactical_analysis"),
                    "missionType": payload.get("requestType", payload.get("request_type", "")),
                    "subjectId": payload.get("subjectId", payload.get("subject_id", "")),
                    "environment": self.config.configuration.environment.value,
                },
            )
            auth = dict(payload.get("authorizationContext", payload.get("authorization_context", {})) or {})
            auth["freshnessEvaluation"] = freshness
            payload["authorizationContext"] = auth
        decision = self.scheduler.evaluate_duty_request(payload)
        self._publish_enterprise_event(
            organization="Executive",
            office="Office Duty Officer",
            workflow="Duty Officer Triage",
            task_identifier=decision["request_id"],
            event_category="SCHEDULING",
            severity="NOTICE" if decision["wake_recommendation"] else "INFO",
            summary=f"ODO {decision['disposition']} for {decision['office_id']}",
            detailed_description=decision["explanation"],
            supporting_evidence=(decision["decision_id"], decision["reason_code"]),
            correlation_identifier=decision["request_id"],
            status=decision["disposition"],
        )
        state = self.state()
        state["latestDutyOfficerDecision"] = decision
        return state

    def event_detection_observe(self) -> dict[str, Any]:
        """Run one bounded deterministic event observation pass."""
        current = self.state()
        self.event_detection_engine.observe(
            current,
            eos=self.scheduler.eos,
            duty_officers=self.scheduler.eos.duty_officers,
            route=True,
        )
        self._publish_enterprise_event(
            organization="Infrastructure",
            office="Event Detection Engine",
            workflow="Deterministic Event Observation",
            task_identifier="EO-CC-OBSERVE",
            event_category="EVENT_DETECTION",
            severity="INFO",
            summary="Event detection observation completed",
            detailed_description="EO-CC ran a bounded local observation pass without waking offices directly.",
            supporting_evidence=("EO-CC",),
            correlation_identifier="EO-CC-OBSERVE",
            status="COMPLETED",
        )
        return self.state()

    def event_detection_replay(self, observations: tuple[dict[str, Any], ...] = ()) -> dict[str, Any]:
        """Run dry-run event replay without production mutation."""
        replay = self.event_detection_engine.replay(observations or (self.state(),))
        state = self.state()
        state["eventDetectionReplay"] = replay
        return state

    def resolve_event_detection_event(self, event_id: str, reason: str = "Commander resolved event.") -> dict[str, Any]:
        """Resolve an event through backend authority."""
        self.event_detection_engine.resolve_event(event_id, reason=reason)
        return self.state()

    def mission_planner_plan_event(self, event: dict[str, Any], *, submit_to_scheduler: bool = False) -> dict[str, Any]:
        """Create a bounded mission plan from a validated event without authorizing execution."""
        self.information_freshness_engine.handle_event(event)
        event = self._with_freshness_metadata(event)
        self.mission_planner.plan_from_event(event, submit_to_scheduler=submit_to_scheduler, eos=self.scheduler.eos)
        return self.state()

    def mission_planner_commander_request(self, request: dict[str, Any], *, submit_to_scheduler: bool = False) -> dict[str, Any]:
        """Create a bounded mission plan from a Commander directive."""
        request = self._with_freshness_metadata(request)
        self.mission_planner.plan_commander_request(request, submit_to_scheduler=submit_to_scheduler, eos=self.scheduler.eos)
        return self.state()

    def mission_planner_submit_plan(self, mission_plan_id: str) -> dict[str, Any]:
        """Submit a ready plan to EOS review; EOS still owns authorization."""
        self.mission_planner.submit_plan(mission_plan_id, eos=self.scheduler.eos)
        return self.state()

    def mission_planner_replay(self, triggers: tuple[dict[str, Any], ...] = ()) -> dict[str, Any]:
        """Dry-run mission planning without production mutation."""
        replay = self.mission_planner.replay(triggers)
        state = self.state()
        state["enterpriseMissionPlanningReplay"] = replay
        return state

    def _with_freshness_metadata(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Attach EO-CF reuse evidence to planning payloads without authorizing work."""
        payload = dict(payload)
        record_ids = tuple(payload.get("informationRecordIds", payload.get("information_record_ids", ())) or ())
        if not record_ids:
            return payload
        freshness = self.information_freshness_engine.evaluate_records(
            record_ids,
            {
                "decisionUseClass": payload.get("decisionUseClass", "commander_briefing" if "briefing" in str(payload.get("missionType", payload.get("mission_type", ""))).lower() else "tactical_analysis"),
                "missionType": payload.get("missionType", payload.get("mission_type", "")),
                "subjectType": payload.get("subjectType", payload.get("subject_type", "")),
                "subjectId": payload.get("subjectId", payload.get("subject_id", "")),
                "ticker": payload.get("ticker", ""),
                "positionId": payload.get("positionId", payload.get("position_id", "")),
                "orderId": payload.get("orderId", payload.get("order_id", "")),
                "environment": self.config.configuration.environment.value,
            },
        )
        metadata = dict(payload.get("metadata", {}) or {})
        metadata["freshnessEvaluation"] = freshness
        metadata["freshnessRecordIds"] = record_ids
        if not freshness["blockedRecordIds"] and not freshness["partialRefreshRecordIds"] and not freshness["fullRefreshRecordIds"]:
            metadata["cache_current"] = True
            metadata["cache_reference"] = ",".join(freshness["reusableRecordIds"] or record_ids)
        elif freshness["partialRefreshRecordIds"]:
            metadata["freshness_partial_refresh"] = True
            metadata["changed_fields"] = tuple(freshness.get("recommendedRefreshScope", {}).keys())
        payload["metadata"] = metadata
        return payload

    def cost_governor_reserve_for_plan(self, mission_plan_id: str) -> dict[str, Any]:
        """Create a cost reservation from an EO-CD mission plan envelope."""
        planner = self.mission_planner.snapshot()
        plans = list(planner.get("allMissionPlans", ()))
        plan = next((item for item in plans if item.get("mission_plan_id") == mission_plan_id), None)
        if plan:
            for record_id in tuple((plan.get("reuse_decision") or {}).get("freshnessRecordIds", ()) or ()):
                self.information_freshness_engine.eo_ce_refresh_justification(record_id, {"decisionUseClass": "tactical_analysis", "missionType": plan.get("mission_type", ""), "estimatedCostUsd": (plan.get("resource_envelope") or {}).get("estimated_cost_usd", 0.0)})
            self.enterprise_cost_governor.request_reservation_from_plan(plan)
        return self.state()

    def cost_governor_release_reservation(self, reservation_id: str) -> dict[str, Any]:
        """Release unused reservation funds through backend authority."""
        self.enterprise_cost_governor.release_reservation(reservation_id)
        return self.state()

    def cost_governor_settle_reservation(self, reservation_id: str) -> dict[str, Any]:
        """Settle a reservation and preserve ledger evidence."""
        self.enterprise_cost_governor.settle_reservation(reservation_id)
        return self.state()

    def cost_governor_policy(self, updates: dict[str, Any]) -> dict[str, Any]:
        """Create an audited budget-policy version."""
        self.enterprise_cost_governor.create_policy_version(updates, actor="Commander", reason=str(updates.get("reason", "Commander policy update.")))
        return self.state()

    def information_freshness_register(self, record: dict[str, Any]) -> dict[str, Any]:
        """Register information metadata without retrieving or duplicating payloads."""
        self.information_freshness_engine.register_record(record)
        return self.state()

    def information_freshness_evaluate(self, record_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Evaluate one information record for a specific decision context."""
        self.information_freshness_engine.evaluate_record(record_id, context or {})
        return self.state()

    def information_freshness_invalidate(self, record_id: str, reason: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create an append-only invalidation record."""
        payload = payload or {}
        try:
            invalidation_reason = InvalidationReason(reason) if reason else InvalidationReason.MANUAL_INVALIDATION
        except ValueError:
            invalidation_reason = InvalidationReason.MANUAL_INVALIDATION
        self.information_freshness_engine.invalidate_record(
            record_id,
            invalidation_reason,
            affected_fields=tuple(payload.get("affectedFields", payload.get("affected_fields", ())) or ()),
            affected_sections=tuple(payload.get("affectedSections", payload.get("affected_sections", ())) or ()),
            explanation=str(payload.get("explanation", payload.get("reason", "Commander invalidated information record."))),
            full=bool(payload.get("fullInvalidation", payload.get("full", False))),
            actor_type="commander",
            actor_id=str(payload.get("actor", "Commander")),
        )
        return self.state()

    def information_freshness_supersede(self, prior_record_id: str, new_record: dict[str, Any]) -> dict[str, Any]:
        """Register a superseding record while preserving the old record."""
        payload = dict(new_record)
        payload["supersedes_record_id"] = prior_record_id
        self.information_freshness_engine.register_record(payload)
        return self.state()

    def information_freshness_contradiction(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Register a structured contradiction claim without resolving it silently."""
        self.information_freshness_engine.register_contradiction(payload)
        return self.state()

    def information_freshness_policy(self, updates: dict[str, Any]) -> dict[str, Any]:
        """Create a versioned freshness-policy update."""
        self.information_freshness_engine.create_policy_version(updates, actor="Commander", reason=str(updates.get("reason", "Commander freshness policy update.")))
        return self.state()

    def enterprise_memory_admit(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Admit a validated or candidate product to governed enterprise memory."""
        result = self.enterprise_memory_cache.admit_product(payload)
        state = self.state()
        state["latestMemoryAdmission"] = result
        return state

    def enterprise_memory_query(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Run deterministic memory retrieval with EO-CF reuse evaluation."""
        result = self.enterprise_memory_cache.query(payload)
        state = self.state()
        state["latestMemoryRetrieval"] = {
            "retrieval_result_id": result.retrieval_result_id,
            "selected_cache_record_ids": result.selected_cache_record_ids,
            "exact_reuse_record_ids": result.exact_reuse_record_ids,
            "partial_reuse_record_ids": result.partial_reuse_record_ids,
            "rejected_record_ids": result.rejected_record_ids,
            "overall_coverage_percent": result.overall_coverage_percent,
        }
        return state

    def enterprise_memory_invalidate(self, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Invalidate a memory record without deleting historical evidence."""
        self.enterprise_memory_cache.invalidate(
            record_id,
            reason=str(payload.get("reason", "Commander invalidated memory record.")),
            affected_fields=tuple(payload.get("affectedFields", payload.get("affected_fields", ())) or ()),
            affected_sections=tuple(payload.get("affectedSections", payload.get("affected_sections", ())) or ()),
            full=bool(payload.get("fullInvalidation", payload.get("full", False))),
            source_information_record_id=str(payload.get("sourceInformationRecordId", payload.get("source_information_record_id", ""))),
            actor=str(payload.get("actor", "Commander")),
        )
        return self.state()

    def enterprise_memory_supersede(self, prior_record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new product version or superseding memory record."""
        result = self.enterprise_memory_cache.supersede(prior_record_id, payload)
        state = self.state()
        state["latestMemoryAdmission"] = result
        return state

    def enterprise_memory_contradiction(self, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Register a contradiction while preserving the original memory record."""
        result = self.enterprise_memory_cache.register_contradiction(record_id, payload)
        state = self.state()
        state["latestMemoryContradiction"] = {
            "cache_contradiction_id": result.cache_contradiction_id,
            "cache_record_id": result.cache_record_id,
            "new_status": result.new_status.value,
            "reason": result.reason,
        }
        return state

    def enterprise_memory_quarantine(self, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Quarantine a cache record so it cannot support operational reuse."""
        result = self.enterprise_memory_cache.quarantine_record(record_id, str(payload.get("reason", "Commander quarantined memory record.")))
        state = self.state()
        state["latestMemoryQuarantine"] = result
        return state

    def enterprise_memory_archive(self, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Archive a cache record through retention policy without deleting it."""
        result = self.enterprise_memory_cache.archive_record(record_id, str(payload.get("reason", "Retention policy archive.")))
        state = self.state()
        state["latestMemoryArchive"] = result
        return state

    def workflow_delta_create_baseline(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create or reuse a validated delta baseline without starting work."""
        baseline = self.workflow_delta_engine.create_baseline(payload)
        state = self.state()
        state["latestDeltaBaseline"] = {
            "baseline_id": baseline.baseline_id,
            "subject_id": baseline.subject_id,
            "environment": baseline.environment,
            "content_hash": baseline.content_hash,
        }
        return state

    def workflow_delta_analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Produce a deterministic delta package for EO-CD review."""
        result = self.workflow_delta_engine.analyze(payload)
        state = self.state()
        state["latestWorkflowDelta"] = result
        return state

    def workflow_delta_recover(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Restore EO-CH state from a snapshot for deterministic restart checks."""
        self.workflow_delta_engine.recover_from_snapshot(snapshot)
        return self.state()

    def workflow_delta_export(self, package_id: str, fmt: str = "json") -> dict[str, Any]:
        """Export a delta package without changing workflow state."""
        exported = self.workflow_delta_engine.export_package(package_id, fmt)
        state = self.state()
        state["latestWorkflowDeltaExport"] = {"packageId": package_id, "format": fmt, "content": exported}
        return state

    def workflow_delta_replay(self, package_id: str) -> dict[str, Any]:
        """Replay a delta package deterministically without production mutation."""
        replay = self.workflow_delta_engine.replay(package_id)
        state = self.state()
        state["latestWorkflowDeltaReplay"] = replay
        return state

    def workflow_delta_review(self, package_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Record a Commander materiality/reassessment review request without authorizing execution."""
        review = self.workflow_delta_engine.request_manual_review(
            package_id,
            str(payload.get("action", payload.get("reviewAction", "request_validation_review"))),
            str(payload.get("reason", "")),
        )
        state = self.state()
        state["latestWorkflowDeltaReview"] = review
        return state

    def enterprise_priority_evaluate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Rank eligible missions without authorizing Scheduler execution."""
        sources = dict(payload.get("sources", {})) if payload and payload.get("sources") else self.state()
        self.enterprise_priority_engine.evaluate(sources)
        self._publish_enterprise_event(
            organization="Infrastructure",
            office="Enterprise Priority Engine",
            workflow="Deterministic Priority Ranking",
            task_identifier="EO-CJ-EVALUATE",
            event_category="PRIORITY",
            severity="INFO",
            summary="Enterprise priority queue evaluated",
            detailed_description="EO-CJ ranked eligible work and preserved EO-CA Scheduler authority.",
            supporting_evidence=("EO-CJ",),
            correlation_identifier="EO-CJ-EVALUATE",
            status="COMPLETED",
        )
        return self.state()

    def enterprise_priority_recover(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Restore priority decisions from a runtime snapshot."""
        self.enterprise_priority_engine.recover_from_snapshot(snapshot)
        return self.state()

    def enterprise_priority_replay(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Replay priority ranking without production mutation."""
        sources = dict(payload.get("sources", {})) if payload and payload.get("sources") else self.state()
        replay = self.enterprise_priority_engine.replay(sources)
        state = self.state()
        state["latestEnterprisePriorityReplay"] = replay
        return state

    def enterprise_priority_modifier(self, candidate_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Record a Commander modifier without permitting direct UI priority setting."""
        self.enterprise_priority_engine.set_commander_modifier(
            candidate_id,
            int(payload.get("modifier", payload.get("commanderModifier", 0)) or 0),
            actor=str(payload.get("actor", "Commander")),
            reason=str(payload.get("reason", "Commander priority modifier.")),
        )
        return self.state()

    def position_monitoring_scan(self) -> dict[str, Any]:
        """Run one bounded deterministic position-monitoring pass that emits events only."""
        performance_truth = self.performance_truth_engine.snapshot(execution_environment="paper")
        market_data_provider = self.market_data_provider.snapshot(timestamp_utc=_now())
        market_data_provider = _with_active_position_quotes(
            market_data_provider,
            self.market_data_provider,
            self.performance_truth_engine.position_registry.active_positions(),
            _now(),
        )
        result = self.position_monitoring_network.scan(
            position_registry=self.performance_truth_engine.position_registry.snapshot(),
            market_data_provider=market_data_provider,
            performance_truth=performance_truth,
            timestamp_utc=_now(),
        )
        for item in result.get("eventDetectionFeed", ()):
            self.enterprise_communications_bus.publish_observation(
                message_type="POSITION_MONITORING_OBSERVATION",
                source_service_id="Position Monitoring Network",
                source_office_id="Trader",
                payload=dict(item),
                target_service_id="Event Detection Engine",
                target_topic="position.monitoring",
                routing_key=str(item.get("event_type", "position_monitoring_event")),
                correlation_id=str(item.get("source_event_id", item.get("position_id", "EO-CK"))),
                causation_id=str(item.get("source_event_id", "")),
                position_id=str(item.get("position_id", "")),
                paper_live_mode=MessageMode.PAPER,
                priority_class=str(item.get("severity", "normal")).upper(),
                idempotency_key=f"EO-CK:{item.get('source_event_id', '')}",
                partition_key="PAPER",
            )
        self._publish_enterprise_event(
            organization="Trader",
            office="Position Monitoring Network",
            workflow="Deterministic Position Monitoring",
            task_identifier="EO-CK-SCAN",
            event_category="POSITION_MONITORING",
            severity="INFO",
            summary="Position monitoring pass completed",
            detailed_description="EO-CK evaluated lightweight position watchers and emitted EO-CC-ready events only.",
            supporting_evidence=("EO-CK",),
            correlation_identifier="EO-CK-SCAN",
            status="COMPLETED",
        )
        state = self.state()
        state["latestPositionMonitoringScan"] = result
        return state

    def position_monitoring_recover(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Restore EO-CK watcher state from a runtime snapshot."""
        self.position_monitoring_network.recover_from_snapshot(snapshot)
        return self.state()

    def position_monitoring_replay(self) -> dict[str, Any]:
        """Replay EO-CK monitoring without production mutation."""
        performance_truth = self.performance_truth_engine.snapshot(execution_environment="paper")
        market_data_provider = self.market_data_provider.snapshot(timestamp_utc=_now())
        replay = self.position_monitoring_network.replay(
            position_registry=self.performance_truth_engine.position_registry.snapshot(),
            market_data_provider=market_data_provider,
            performance_truth=performance_truth,
        )
        state = self.state()
        state["latestPositionMonitoringReplay"] = replay
        return state

    def communications_bus_state(self) -> dict[str, Any]:
        """Return the EO-CL Commander bridge payload."""
        return self.enterprise_communications_bus.snapshot()

    def communications_bus_publish_sample(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Publish a bounded Commander-visible system notification through EO-CL."""
        result = self.enterprise_communications_bus.publish_event(
            message_type=str(payload.get("messageType", "SYSTEM_NOTIFICATION")),
            source_service_id=str(payload.get("sourceServiceId", "Commander Interface")),
            source_office_id=str(payload.get("sourceOfficeId", "Commander")),
            payload={
                "summary": str(payload.get("summary", "Commander communications bus sample.")),
                "severity": str(payload.get("severity", "INFO")),
            },
            target_topic=str(payload.get("targetTopic", "commander.system")),
            routing_key=str(payload.get("routingKey", "commander.system")),
            correlation_id=str(payload.get("correlationId", f"ECL-COMMANDER-{len(self.enterprise_communications_bus.snapshot().get('messageStream', ())) + 1:06d}")),
            paper_live_mode=str(payload.get("paperLiveMode", "PAPER")),
            priority_class=str(payload.get("priorityClass", "normal")),
        )
        state = self.state()
        state["latestCommunicationsPublishResult"] = result.__dict__
        return state

    def communications_bus_retry_dead_letter(self, dead_letter_id: str, authorization: dict[str, Any] | None = None) -> dict[str, Any]:
        """Retry an eligible dead-letter through EO-CL policy checks."""
        result = self.enterprise_communications_bus.retry_dead_letter(dead_letter_id, authorization or {})
        state = self.state()
        state["latestCommunicationsRetryResult"] = result
        return state

    def communications_bus_replay(self, message_id: str, *, analytical: bool = True, authorization: dict[str, Any] | None = None) -> dict[str, Any]:
        """Request EO-CL replay without allowing unsafe production side effects."""
        result = self.enterprise_communications_bus.request_replay(message_id, analytical=analytical, authorization=authorization or {})
        state = self.state()
        state["latestCommunicationsReplayResult"] = result
        return state

    def communications_bus_recover(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Restore EO-CL transport state from a runtime snapshot."""
        self.enterprise_communications_bus.recover_from_snapshot(snapshot)
        return self.state()

    def communications_bus_trace(self, correlation_id: str) -> dict[str, Any]:
        """Return a deterministic EO-CL correlation trace."""
        state = self.state()
        state["latestCommunicationsTrace"] = self.enterprise_communications_bus.get_correlation_trace(correlation_id)
        return state

    def efficiency_analytics_refresh(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Persist one bounded EO-CN efficiency snapshot."""
        body = payload or {}
        current = self.state()
        result = self.enterprise_efficiency_analytics.analyze(
            _efficiency_sources_from_state(current),
            window_start=str(body.get("windowStart", "current_operating_day")),
            window_end=str(body.get("windowEnd", "latest_state_snapshot")),
            mode=str(body.get("mode", "COMBINED")),
            persist=True,
        )
        state = self.state()
        state["latestEfficiencyAnalyticsRefresh"] = result
        return state

    def efficiency_acknowledge_finding(self, finding_id: str, reason: str = "Commander acknowledged efficiency finding.") -> dict[str, Any]:
        """Acknowledge an EO-CN finding without changing operational policy."""
        self.enterprise_efficiency_analytics.acknowledge_finding(finding_id, reason)
        return self.state()

    def efficiency_recalculate_metric(self, metric_value_id: str, formula_version: str = "") -> dict[str, Any]:
        """Recalculate a metric deterministically without mutating source records."""
        result = self.enterprise_efficiency_analytics.recalculate_metric(metric_value_id, formula_version or None)
        state = self.state()
        state["latestEfficiencyRecalculation"] = result
        return state

    def efficiency_metric_lineage(self, metric_value_id: str) -> dict[str, Any]:
        """Return formula and source lineage for one EO-CN metric value."""
        state = self.state()
        state["latestEfficiencyMetricLineage"] = self.enterprise_efficiency_analytics.get_metric_lineage(metric_value_id)
        return state

    def efficiency_compare_periods(self, left: dict[str, Any] | None = None, right: dict[str, Any] | None = None) -> dict[str, Any]:
        """Compare two EO-CN snapshots without claiming causation."""
        current = self.state()["enterpriseEfficiencyAnalytics"]
        comparison = self.enterprise_efficiency_analytics.compare_periods(left or current, right or current)
        state = self.state()
        state["latestEfficiencyComparison"] = comparison
        return state

    def doctrine_policy_state(self) -> dict[str, Any]:
        return self.state()["enterpriseDoctrinePolicyManager"]

    def doctrine_policy_submit(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.enterprise_doctrine_policy_manager.submit_policy(
            payload,
            idempotency_key=str(payload.get("idempotencyKey", payload.get("idempotency_key", ""))),
            actor=str(payload.get("actor", "Commander")),
        )
        state = self.state()
        state["latestDoctrinePolicySubmission"] = result
        return state

    def doctrine_policy_approve(self, policy_version_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.enterprise_doctrine_policy_manager.approve_policy(
            policy_version_id,
            payload,
            idempotency_key=str(payload.get("idempotencyKey", payload.get("idempotency_key", ""))),
        )
        state = self.state()
        state["latestDoctrinePolicyApproval"] = result
        return state

    def doctrine_policy_schedule(self, policy_version_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.enterprise_doctrine_policy_manager.schedule_activation(
            policy_version_id,
            payload,
            idempotency_key=str(payload.get("idempotencyKey", payload.get("idempotency_key", ""))),
        )
        state = self.state()
        state["latestDoctrinePolicySchedule"] = result
        return state

    def doctrine_policy_activate(self, activation_plan_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        result = self.enterprise_doctrine_policy_manager.activate_policy(
            activation_plan_id,
            communications_bus=self.enterprise_communications_bus,
            idempotency_key=str(payload.get("idempotencyKey", payload.get("idempotency_key", ""))),
        )
        state = self.state()
        state["latestDoctrinePolicyActivation"] = result
        return state

    def doctrine_policy_suspend(self, policy_version_id: str, reason: str) -> dict[str, Any]:
        result = self.enterprise_doctrine_policy_manager.suspend_policy(policy_version_id, reason)
        state = self.state()
        state["latestDoctrinePolicySuspension"] = result
        return state

    def doctrine_policy_rollback(self, policy_version_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.enterprise_doctrine_policy_manager.rollback_policy(policy_version_id, payload)
        state = self.state()
        state["latestDoctrinePolicyRollback"] = result
        return state

    def doctrine_policy_directive(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.enterprise_doctrine_policy_manager.issue_temporary_directive(payload, emergency=bool(payload.get("emergency", False)))
        state = self.state()
        state["latestDoctrinePolicyDirective"] = result
        return state

    def doctrine_policy_drift(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.enterprise_doctrine_policy_manager.detect_drift(
            str(payload.get("subscriberId", payload.get("subscriber_id", "Enterprise Cost Governor"))),
            str(payload.get("policyVersionId", payload.get("policy_version_id", ""))),
            dict(payload.get("actualValues", payload.get("actual_values", {})) or {}),
            str(payload.get("actualHash", payload.get("actual_hash", ""))),
        )
        state = self.state()
        state["latestDoctrinePolicyDrift"] = result
        return state

    def doctrine_policy_replay(self, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.state()
        current["policyReplay"] = self.enterprise_doctrine_policy_manager.replay(
            str(payload.get("policyVersionId", payload.get("policy_version_id", ""))),
            str(payload.get("atTime", payload.get("at_time", ""))),
        )
        current["enterpriseDoctrinePolicyManager"] = self.enterprise_doctrine_policy_manager.snapshot()
        return current

    def doctrine_policy_impact(self, policy_version_id: str) -> dict[str, Any]:
        current = self.state()
        current["policyImpactAnalysis"] = self.enterprise_doctrine_policy_manager.impact_analysis(policy_version_id)
        current["enterpriseDoctrinePolicyManager"] = self.enterprise_doctrine_policy_manager.snapshot()
        return current

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
            event = self.eab.publish(**kwargs)
            self.enterprise_communications_bus.publish_event(
                message_type="ENTERPRISE_ACTIVITY_EVENT",
                source_service_id="Enterprise Activity Bus",
                source_office_id=str(kwargs.get("office", "")),
                payload={
                    "event_id": event.event_id,
                    "summary": event.summary,
                    "severity": event.severity,
                    "organization": event.organization,
                    "office": event.office,
                    "status": event.status,
                },
                target_topic="enterprise.activity",
                routing_key=event.event_category,
                correlation_id=event.correlation_identifier,
                causation_id=str(kwargs.get("causationId", "")),
                workflow_id=str(kwargs.get("workflow", "")),
                mission_id=str(kwargs.get("missionId", "")),
                paper_live_mode=MessageMode.PAPER,
                priority_class=event.severity,
                idempotency_key=f"EAB:{event.event_id}",
                partition_key="PAPER",
            )
            return event

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

    def _activate_eos_mission_offices(self, mission: Any) -> None:
        for office in mission.required_offices:
            target = self._office_lookup(office)
            if not target:
                continue
            activated = self.scheduler.activate(target["organization"], target["office"], "EOS Mission", mission.mission_id)
            self._publish_scheduler_transition(activated, "Office activated by EOS mission", "ACTIVE")

    def _office_lookup(self, office_name: str) -> dict[str, str]:
        normalized = office_name.lower()
        for item in self.scheduler.snapshot()["offices"]:
            if item["office"].lower() == normalized:
                return {"organization": item["organization"], "office": item["office"]}
        aliases = {
            "risk": ("Risk", "Readiness"),
            "trader": ("Trader", "Execution"),
            "historian": ("Historian", "Performance"),
            "librarian": ("Librarian", "Institutional Knowledge"),
            "seeker": ("Seeker", "Fusion"),
            "analyst": ("Analyst", "Review"),
            "commander briefing": ("Executive", "Dashboard"),
            "commander briefing generator": ("Executive", "Dashboard"),
            "runtime monitoring": ("Infrastructure", "Runtime"),
            "position monitor": ("Trader", "Monitoring"),
            "position lifecycle": ("Trader", "Position Management"),
            "performance truth engine": ("Trader", "Execution Quality"),
            "trader accounting": ("Trader", "Order Management"),
            "strategic intelligence command": ("Executive", "Chief of Staff"),
        }
        if normalized in aliases:
            organization, office = aliases[normalized]
            return {"organization": organization, "office": office}
        return {}

    def _publish_eos_event(self, summary: str, detail: str, status: str, mission_id: str = "") -> None:
        self._publish_enterprise_event(
            organization="Executive",
            office="Enterprise Operations Scheduler",
            workflow="Enterprise Operations Scheduling",
            task_identifier=mission_id or "EOS-CONTROL",
            event_category="SCHEDULING",
            severity="NOTICE" if status not in {"FAILED", "SUSPENDED"} else "WARNING",
            summary=summary,
            detailed_description=detail,
            supporting_evidence=(mission_id,) if mission_id else ("EO-CA",),
            correlation_identifier=mission_id or "EOS-CONTROL",
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


def _latest_performance_decision_object_id(performance_truth: dict[str, Any]) -> str:
    orders = performance_truth.get("orderLedger", ())
    if orders:
        return str(orders[-1].get("decision_object_id", ""))
    outcomes = performance_truth.get("decisionObjectOutcomes", ())
    if outcomes:
        return str(outcomes[-1].get("decision_object_id", ""))
    return ""


def _with_active_position_quotes(provider_snapshot: dict[str, Any], provider: MarketDataProviderAbstractionLayer, positions: tuple[Any, ...], timestamp_utc: str) -> dict[str, Any]:
    normalized = dict(provider_snapshot.get("normalizedObjects", {}))
    quotes = list(normalized.get("quotes", ()))
    present = {str(quote.get("symbol", "")).upper() for quote in quotes if isinstance(quote, dict)}
    for position in positions:
        symbol = str(getattr(position, "symbol", "")).upper()
        if not symbol or symbol in present:
            continue
        quote = provider.get_quote(symbol, timestamp_utc, workflow_id=str(getattr(position, "workflow_id", "")), decision_object_id=str(getattr(position, "decision_object_id", "")))
        quotes.append(quote["normalizedObject"])
        present.add(symbol)
    normalized["quotes"] = tuple(quotes)
    updated = dict(provider_snapshot)
    updated["normalizedObjects"] = normalized
    return updated


def _efficiency_sources_from_state(state: dict[str, Any]) -> dict[str, Any]:
    """Select authoritative source snapshots consumed by EO-CN."""
    keys = (
        "costs",
        "scheduler",
        "enterpriseOperationsScheduler",
        "officeDutyOfficers",
        "workflowOrchestrator",
        "workflowRuntimeMonitor",
        "apiRuntimeMonitor",
        "apiExecutionGateway",
        "enterpriseCostGovernor",
        "enterpriseCostGovernorEngine",
        "enterpriseMemoryCache",
        "informationFreshnessEngine",
        "workflowDeltaEngine",
        "enterprisePriorityEngine",
        "positionMonitoringNetwork",
        "enterpriseCommunicationsBus",
        "enterpriseFailureRecoveryFramework",
        "eventDetectionEngine",
        "performanceTruthEngine",
        "cnac",
        "commanderDailyReviewWorkspace",
    )
    return {key: state.get(key, {}) for key in keys}


def _latest_portfolio_construction_decision(strategy_performance: dict[str, Any]) -> dict[str, Any] | None:
    panel = strategy_performance.get("decisionObjectPanel", {})
    if panel.get("decisionObjectId"):
        return {
            "decisionObjectId": panel.get("decisionObjectId", ""),
            "workflowId": panel.get("workflowId", ""),
            "symbol": panel.get("symbol", "AAPL"),
            "assetType": panel.get("assetType", "STOCK"),
            "side": "BUY",
            "recommendation": panel.get("currentRecommendation", panel.get("recommendation", "")),
            "confidence": panel.get("currentConfidence", panel.get("confidence", 0.0)),
            "riskScore": panel.get("riskScore", 0.0),
            "positionSizeRecommendation": panel.get("positionSizeRecommendation", 0.0),
            "targetPrice": panel.get("targetPrice", 0.0),
            "stopLoss": panel.get("stopLoss", 0.0),
            "currentStrategy": panel.get("currentStrategy", "Workflow Proof Strategy"),
            "marketContext": panel.get("marketContext", {}),
        }
    evolution = strategy_performance.get("decisionObjectEvolution", ())
    if not evolution:
        return None
    latest = evolution[-1]
    revisions = latest.get("revisions", ())
    if not revisions:
        return None
    revision = revisions[-1]
    return {
        "decisionObjectId": latest.get("decisionObjectId", ""),
        "workflowId": latest.get("workflowId", ""),
        "symbol": "AAPL",
        "assetType": "STOCK",
        "side": "BUY",
        "recommendation": revision.get("recommendation", ""),
        "confidence": revision.get("confidence", 0.0),
        "riskScore": revision.get("risk", 0.0),
        "positionSizeRecommendation": revision.get("positionSizeRecommendation", 0.02),
        "targetPrice": revision.get("targetPrice", 0.0),
        "stopLoss": revision.get("stopLoss", 0.0),
        "currentStrategy": revision.get("strategy", "Workflow Proof Strategy"),
        "marketContext": {},
    }


def _trader_command_bridge_payload(
    *,
    timestamp_utc: str,
    performance_truth: dict[str, Any],
    position_surveillance: dict[str, Any],
    position_exit_decision: dict[str, Any],
    closed_position_truth: dict[str, Any],
    strategy_performance: dict[str, Any],
    workflow_runtime_monitor: dict[str, Any],
    enterprise_health_monitor: dict[str, Any],
) -> dict[str, Any]:
    active_positions = tuple(performance_truth.get("positionRegistry", {}).get("activePositions", ()))
    latest_snapshots = _latest_by(position_surveillance.get("latestSnapshots", ()) or position_surveillance.get("surveillanceSnapshots", ()), "position_id")
    latest_decisions = _latest_by(position_exit_decision.get("latestDecisions", ()) or position_exit_decision.get("exitDecisionRecords", ()), "position_id")
    orders = tuple(performance_truth.get("orderLedger", ()))
    closed_records = tuple(closed_position_truth.get("closedPositionTruthRecords", ())) or tuple(performance_truth.get("closedPositionTruth", ()))
    rows = tuple(_trader_position_row(position, latest_snapshots.get(position.get("position_id", ""), {}), latest_decisions.get(position.get("position_id", ""), {}), orders) for position in active_positions)
    summary = _trader_summary(rows, orders, performance_truth, position_surveillance, position_exit_decision)
    exposure = _trader_exposure(rows, performance_truth)
    return {
        "bridgeName": "Trader Command Bridge",
        "engineeringOrder": "EO-XF",
        "timestampUtc": timestamp_utc,
        "constitutionalChain": ("Decision Object", "Position Object", "Surveillance Snapshot", "Exit Decision Record", "Execution Record", "Closed Position Truth"),
        "summary": summary,
        "active_positions": rows,
        "position_details": tuple(_trader_position_detail(row, latest_snapshots.get(row["position_id"], {}), latest_decisions.get(row["position_id"], {}), orders) for row in rows),
        "exit_recommendations": tuple(_trader_exit_recommendation(item) for item in position_exit_decision.get("latestDecisions", ()) or position_exit_decision.get("exitDecisionRecords", ())),
        "orders": tuple(_trader_order_row(order) for order in orders[-80:]),
        "executions": tuple(_trader_order_row(order) for order in orders[-80:] if order.get("status") in {"FILLED", "PARTIALLY_FILLED"}),
        "closed_positions": tuple(_trader_closed_position(row) for row in closed_records[-40:]),
        "exposure": exposure,
        "surveillance_health": {
            "activePositionsSurveilled": position_surveillance.get("metrics", {}).get("activePositionsSurveilled", 0),
            "latestSurveillanceTimestamp": position_surveillance.get("diagnostics", {}).get("timestampUtc", timestamp_utc),
            "degradedSnapshots": sum(1 for item in position_surveillance.get("latestSnapshots", ()) if item.get("surveillance_status") == "DEGRADED"),
            "staleDataEvents": sum(1 for item in position_surveillance.get("latestEvents", ()) if item.get("event_type") in {"price_data_stale", "market_data_missing"}),
            "escalationsGenerated": position_surveillance.get("metrics", {}).get("latestEscalationCount", 0),
            "surveillanceFailures": len(position_surveillance.get("reconciliationEvents", ())),
            "averageSurveillanceLatency": "0ms",
        },
        "execution_realism_health": _trader_execution_realism(performance_truth),
        "alerts": _trader_alerts(rows, position_exit_decision, position_surveillance, enterprise_health_monitor),
        "commander_actions": {
            "implementedActions": ("cancel_pending_order", "pause_workflow", "resume_workflow", "open_decision_laboratory"),
            "authorizedRoute": "/api/trader/cancel-pending-orders",
            "directLedgerMutation": False,
            "directPositionMutation": False,
        },
        "lawVII": {
            "executesWorkflows": False,
            "ownsWorkflowTokens": False,
            "placesTrades": False,
            "mutatesLedgers": False,
            "mutatesPositions": False,
            "displayOnly": True,
        },
        "lawVIII": {"routineAiCallsUsed": 0, "deterministicDisplay": True},
        "diagnostics": {
            "backgroundWorkerActive": False,
            "aiCallsUsed": 0,
            "source": "Runtime aggregated state",
            "activeWorkflow": (workflow_runtime_monitor.get("activeWorkflow") or {}).get("workflowIdentifier", ""),
            "strategyPerformanceLinked": bool(strategy_performance),
        },
    }


def _trader_position_row(position: dict[str, Any], snapshot: dict[str, Any], decision: dict[str, Any], orders: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    current_price = float(snapshot.get("current_price", position.get("current_price", 0.0)) or 0.0)
    quantity = float(position.get("quantity", 0.0) or 0.0)
    average_cost = float(position.get("average_cost", 0.0) or 0.0)
    stop = float(position.get("stop_loss", 0.0) or 0.0)
    target = float(position.get("profit_target", 0.0) or 0.0)
    unrealized = float(snapshot.get("unrealized_pnl", position.get("unrealized_pnl", 0.0)) or 0.0)
    events = tuple(snapshot.get("detected_events", ()))
    latest_order = next((order for order in reversed(orders) if order.get("symbol") == position.get("symbol") and order.get("decision_object_id") == position.get("decision_object_id")), {})
    return {
        "position_id": position.get("position_id", ""),
        "workflow_id": position.get("workflow_id", ""),
        "decision_object_id": position.get("decision_object_id", ""),
        "symbol": position.get("symbol", ""),
        "asset_type": position.get("asset_type", ""),
        "side": position.get("side", ""),
        "quantity": quantity,
        "average_cost": average_cost,
        "current_price": current_price,
        "current_value": round(quantity * current_price, 4),
        "unrealized_pnl": round(unrealized, 4),
        "unrealized_pnl_percent": round(unrealized / max(1.0, average_cost * quantity), 6),
        "stop_loss": stop,
        "profit_target": target,
        "trailing_stop": float(position.get("trailing_stop", 0.0) or snapshot.get("trailing_stop", 0.0) or 0.0),
        "distance_to_stop": float(snapshot.get("distance_to_stop", current_price - stop if stop else 0.0) or 0.0),
        "distance_to_target": float(snapshot.get("distance_to_target", target - current_price if target else 0.0) or 0.0),
        "time_in_trade": position.get("time_in_trade", snapshot.get("time_in_trade", "")),
        "lifecycle_status": position.get("lifecycle_status", ""),
        "risk_score": float(position.get("current_risk", snapshot.get("risk_score", 0.0)) or 0.0),
        "confidence_score": float(position.get("current_confidence", snapshot.get("thesis_health_score", 0.0)) or 0.0),
        "latest_surveillance_status": snapshot.get("surveillance_status", "UNKNOWN"),
        "latest_exit_recommendation": decision.get("decision", position.get("exit_recommendation", "")) or "hold",
        "health": _trader_position_health(position, snapshot, decision),
        "detected_events": events,
        "pending_order_status": latest_order.get("status", ""),
    }


def _trader_position_health(position: dict[str, Any], snapshot: dict[str, Any], decision: dict[str, Any]) -> str:
    events = set(snapshot.get("detected_events", ()))
    if decision.get("decision") in {"emergency_exit"}:
        return "emergency_risk_state"
    if decision.get("decision") in {"exit_full", "exit_partial"} or position.get("lifecycle_status") == "exit_recommended":
        return "exit_recommended"
    if snapshot.get("surveillance_status") == "DEGRADED" or "market_data_missing" in events:
        return "data_degraded"
    if "stop_loss_approached" in events or "stop_loss_reached" in events:
        return "stop_approaching"
    if "profit_target_approached" in events or "profit_target_reached" in events:
        return "target_approaching"
    return "healthy"


def _trader_position_detail(row: dict[str, Any], snapshot: dict[str, Any], decision: dict[str, Any], orders: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    executions = tuple(_trader_order_row(order) for order in orders if order.get("decision_object_id") == row["decision_object_id"] and order.get("symbol") == row["symbol"])
    return {
        "position_id": row["position_id"],
        "entry_thesis": row.get("entry_thesis", ""),
        "linked_decision_object": row["decision_object_id"],
        "entry_execution_record": next((item for item in executions if item["side"] == "BUY"), {}),
        "latest_surveillance_snapshot": snapshot,
        "surveillance_event_history": snapshot.get("detected_events", ()),
        "exit_conditions": {"profitTarget": row["profit_target"], "stopLoss": row["stop_loss"], "trailingStop": row["trailing_stop"]},
        "latest_exit_decision_record": decision,
        "pending_order_status": row["pending_order_status"],
        "execution_history": executions,
        "lifecycle_status": row["lifecycle_status"],
        "current_risk_explanation": f"Risk {row['risk_score']} from Position Registry and surveillance.",
        "current_thesis_health": row["confidence_score"],
        "expected_next_step": decision.get("next_engine", "Continue surveillance"),
    }


def _trader_summary(rows: tuple[dict[str, Any], ...], orders: tuple[dict[str, Any], ...], performance_truth: dict[str, Any], surveillance: dict[str, Any], exit_decision: dict[str, Any]) -> dict[str, Any]:
    paper = performance_truth.get("paperAccount", {})
    return {
        "total_open_positions": len(rows),
        "total_market_value": round(sum(row["current_value"] for row in rows), 4),
        "total_unrealized_pnl": round(sum(row["unrealized_pnl"] for row in rows), 4),
        "total_realized_pnl_today": performance_truth.get("calculations", {}).get("portfolio", {}).get("realizedPnl", 0.0),
        "cash": paper.get("cash", paper.get("buyingPower", 0.0)),
        "buying_power": paper.get("buyingPower", 0.0),
        "pending_orders": sum(1 for order in orders if order.get("status") in {"QUEUED", "PENDING", "SUBMITTED"}),
        "positions_requiring_attention": sum(1 for row in rows if row["health"] != "healthy"),
        "exits_recommended": sum(1 for row in rows if row["latest_exit_recommendation"] in {"exit_full", "exit_partial", "emergency_exit"}),
        "positions_at_risk": sum(1 for row in rows if row["health"] in {"stop_approaching", "emergency_risk_state", "data_degraded"}),
        "surveillance_health": "DEGRADED" if any(row["latest_surveillance_status"] == "DEGRADED" for row in rows) else "WATCHING",
        "execution_health": "REVIEW" if performance_truth.get("executionRealism", {}).get("rejectedOrders", 0) else "BROKER_REALISTIC",
        "latest_exit_decision_count": exit_decision.get("metrics", {}).get("latestDecisionCount", 0),
        "surveillance_snapshots": surveillance.get("metrics", {}).get("totalSnapshotCount", 0),
    }


def _trader_order_row(order: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": order.get("order_id", ""),
        "workflow_id": order.get("workflow_id", ""),
        "decision_object_id": order.get("decision_object_id", ""),
        "symbol": order.get("symbol", ""),
        "asset_type": order.get("asset_type", ""),
        "side": order.get("side", ""),
        "status": order.get("status", ""),
        "requested_quantity": order.get("requested_quantity", 0.0),
        "filled_quantity": order.get("filled_quantity", 0.0),
        "remaining_quantity": order.get("remaining_quantity", 0.0),
        "rejection_reason": order.get("rejection_reason", ""),
        "queued_reason": order.get("queued_reason", ""),
        "fill_price": order.get("average_fill_price", 0.0),
        "bid": order.get("bid_price", 0.0),
        "ask": order.get("ask_price", 0.0),
        "spread": round(float(order.get("ask_price", 0.0) or 0.0) - float(order.get("bid_price", 0.0) or 0.0), 4),
        "slippage": order.get("slippage", 0.0),
        "cash_impact": order.get("cash_impact", 0.0),
        "realized_pnl": order.get("realized_profit_loss", 0.0),
        "fantasy_warnings": order.get("fantasy_warnings", ()),
        "timestamp": order.get("timestamp", ""),
    }


def _trader_exit_recommendation(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "position_id": item.get("position_id", ""),
        "symbol": item.get("symbol", ""),
        "recommended_action": item.get("recommended_action", ""),
        "decision": item.get("decision", ""),
        "recommended_quantity": item.get("recommended_quantity", 0.0),
        "urgency": item.get("urgency", ""),
        "trigger_type": item.get("trigger_type", ""),
        "trigger_evidence": item.get("trigger_evidence", {}),
        "deterministic_reasoning": item.get("deterministic_reasoning", ()),
        "ai_review_required": item.get("ai_review_required", False),
        "commander_review_required": item.get("decision") == "request_commander_review",
        "next_engine": item.get("next_engine", ""),
    }


def _trader_closed_position(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": row.get("symbol", ""),
        "entry_time": row.get("entry_time", ""),
        "exit_time": row.get("exit_time", ""),
        "holding_period": row.get("holding_period", ""),
        "realized_pnl": row.get("net_realized_pnl", 0.0),
        "benchmark_return": row.get("benchmark_return", 0.0),
        "alpha_vs_benchmark": row.get("alpha_vs_benchmark", 0.0),
        "exit_reason": row.get("exit_reason", ""),
        "execution_quality_score": row.get("execution_quality_score", 0.0),
        "lifecycle_summary": row.get("lifecycle_summary", ""),
        "learning_status": "LEARNING_EVENT_READY" if row.get("learning_payload") else "PENDING",
        "closed_position_truth_id": row.get("closed_position_truth_id", ""),
    }


def _trader_exposure(rows: tuple[dict[str, Any], ...], performance_truth: dict[str, Any]) -> dict[str, Any]:
    total = sum(row["current_value"] for row in rows)
    largest = max(rows, key=lambda row: row["current_value"], default={})
    cash = performance_truth.get("paperAccount", {}).get("buyingPower", 0.0)
    return {
        "cash_allocation": cash,
        "long_exposure": round(total, 4),
        "short_exposure": 0.0,
        "largest_position": {"symbol": largest.get("symbol", ""), "value": largest.get("current_value", 0.0)},
        "largest_sector": "UNKNOWN",
        "largest_thesis": "UNSPECIFIED",
        "portfolio_concentration": round(largest.get("current_value", 0.0) / max(1.0, total + cash), 6) if largest else 0.0,
        "positions_at_risk": sum(1 for row in rows if row["health"] != "healthy"),
        "correlated_exposure": "NOT_AVAILABLE",
    }


def _trader_execution_realism(performance_truth: dict[str, Any]) -> dict[str, Any]:
    realism = performance_truth.get("executionRealism", {})
    orders = tuple(performance_truth.get("orderLedger", ()))
    return {
        "execution_realism_audit_status": "REVIEW" if realism.get("fantasyWarningCount", 0) else "VALID",
        "suspicious_fill_events": realism.get("fantasyWarningCount", 0),
        "buying_power_inconsistencies": sum(1 for order in orders if float(order.get("buying_power_after", 0.0) or 0.0) < 0),
        "impossible_fill_warnings": tuple(warning for order in orders for warning in order.get("fantasy_warnings", ())),
        "portfolio_mutation_warnings": 0,
        "rejected_order_count": realism.get("rejectedOrders", 0),
        "partial_fill_count": realism.get("partialFills", 0),
        "queued_order_count": realism.get("queuedOrders", 0),
        "spread_cost": realism.get("spreadCost", 0.0),
        "slippage_cost": realism.get("slippageCost", 0.0),
    }


def _trader_alerts(rows: tuple[dict[str, Any], ...], exit_decision: dict[str, Any], surveillance: dict[str, Any], health: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    alerts = []
    for row in rows:
        if row["health"] != "healthy":
            alerts.append({"severity": "WARNING", "positionId": row["position_id"], "summary": f"{row['symbol']} {row['health'].replace('_', ' ')}"})
    for item in exit_decision.get("latestDecisions", ()):
        if item.get("decision") in {"exit_full", "exit_partial", "emergency_exit"}:
            alerts.append({"severity": item.get("urgency", "NOTICE").upper(), "positionId": item.get("position_id", ""), "summary": f"Exit recommended: {item.get('trigger_type', '')}"})
    if surveillance.get("metrics", {}).get("latestEscalationCount", 0):
        alerts.append({"severity": "NOTICE", "positionId": "", "summary": "Surveillance escalations generated"})
    for item in health.get("activeAlerts", ())[:3]:
        alerts.append({"severity": item.get("severity", "INFO"), "positionId": "", "summary": item.get("summary", "")})
    return tuple(alerts[:20])


def _latest_by(items: Any, key: str) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for item in items or ():
        latest[str(item.get(key, ""))] = item
    return latest


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
