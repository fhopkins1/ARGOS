from dataclasses import replace
from pathlib import Path
import json
import os
import re
import sys
import time
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import ApiExecutionRequest, BlackSwanSimulationConfig, BlackSwanSimulationEngine, BlueOceanIntelligenceOffice, CacheReuseDecision, CapitalAllocationConfig, CapitalAllocationEngine, CapitalRotationIntelligenceOffice, ChangeType, CommanderBriefingGenerator, CommanderStrategicDashboard, CorrelationIntelligenceConfig, CorrelationIntelligenceEngine, DataQualityClassification, DecisionUseClass, DependencyLink, DeltaMateriality, EnterpriseCommunicationsBus, EnterpriseDoctrinePolicyManager, EnterpriseEfficiencyAnalytics, EnterpriseMemoryCache, EnterprisePriorityClass, EnterprisePriorityEngine, FreshnessAction, FreshnessStatus, DeclineIntelligenceOffice, DisruptionIntelligenceOffice, EnterpriseCostGovernor, EnterpriseGrandStrategyEngine, EnterpriseMessageKind, EnterpriseMissionPlanner, EnterpriseOperationsScheduler, EventDetectionEngine, EventDomain, EventStatus, InformationFreshnessEngine, InvalidationReason, MessageMode, MessageSubscription, MissionPlanStatus, MissionTriggerType, MonitoringEventSeverity, OfficeDutyOfficerRegistry, OfficeImpactDecision, PolicyDomain, PositionMonitoringNetwork, RecommendationClassification, RevisionRequirement, WorkflowDeltaEngine, EnterpriseRealityCalibrationEngine, EnterpriseRiskFactorConfig, EnterpriseRiskFactorEngine, HistoricalReplayMarketProvider, MarketReplayEngine, MarketStructureIntelligenceOffice, MonteCarloPortfolioConfig, MonteCarloPortfolioEngine, PortfolioConstructionConfig, PortfolioConstructionEngine, PositionSizingConfig, PositionSizingEngine, RealityCalibrationConfig, ReplayClock, ReservationState, ShortOpportunityOffice, StrategicIntelligenceCommand, StrategicSynthesisOffice, StressTestingConfig, StressTestingEngine, create_runtime  # noqa: E402
from argos.control_panel.cognitive_contract import OFFICE_OUTPUT_SCHEMAS, PromptContractLibrary, build_prompt_contract_envelope  # noqa: E402


def _exit_snapshot(position, *, current_price: float, events: tuple[str, ...], status: str = "NOMINAL", trailing_stop: float = 0.0) -> dict:
    quantity = float(position.quantity)
    unrealized = round((current_price - position.average_cost) * quantity, 4)
    return {
        "snapshot_id": f"PSS-TEST-{position.position_id}-{str(current_price).replace('.', '-')}-{len(events)}-{status}",
        "position_id": position.position_id,
        "workflow_id": position.workflow_id,
        "decision_object_id": position.decision_object_id,
        "timestamp": "2026-07-09T15:00:00Z",
        "symbol": position.symbol,
        "asset_type": position.asset_type,
        "quantity": quantity,
        "average_cost": position.average_cost,
        "current_price": current_price,
        "current_value": round(current_price * quantity, 4),
        "unrealized_pnl": unrealized,
        "unrealized_pnl_percent": round(unrealized / max(1.0, position.average_cost * quantity), 6),
        "stop_loss": position.stop_loss,
        "profit_target": position.profit_target,
        "trailing_stop": trailing_stop,
        "distance_to_stop": round(current_price - position.stop_loss, 4) if position.stop_loss else 0.0,
        "distance_to_target": round(position.profit_target - current_price, 4) if position.profit_target else 0.0,
        "time_in_trade": position.time_in_trade,
        "market_session": "PAPER_OPEN",
        "spread": 0.02,
        "bid": round(current_price - 0.01, 4),
        "ask": round(current_price + 0.01, 4),
        "volume": 1000,
        "volatility": 0.01,
        "risk_score": position.current_risk,
        "thesis_health_score": position.current_confidence,
        "surveillance_status": status,
        "detected_events": events,
        "escalation_required": bool(events),
        "escalation_reason": ", ".join(events),
    }


def _closed_truth_fixture():
    from argos.control_panel.performance_truth_engine import PerformanceTruthEngine

    previous_session = os.environ.get("ARGOS_BROKER_SIM_MARKET_SESSION")
    os.environ["ARGOS_BROKER_SIM_MARKET_SESSION"] = "REGULAR"
    try:
        engine = PerformanceTruthEngine(paper_starting_cash=10000.0)
        buy = engine.record_manual_paper_order(symbol="AAPL", side="BUY", quantity=5, decision_object_id="DO-CPT", workflow_id="WF-CPT", token_id="TOK-CPT")
        position = engine.position_registry.position(f"POS-AAPL-{buy['decision_object_id']}")
        surveillance = {
            "surveillanceSnapshots": (
                _exit_snapshot(position, current_price=buy["average_fill_price"] + 2.0, events=("large_favorable_move",)),
                _exit_snapshot(position, current_price=buy["average_fill_price"] - 1.0, events=()),
                _exit_snapshot(position, current_price=buy["average_fill_price"] + 4.0, events=("profit_target_reached",)),
            ),
            "latestSnapshots": (),
        }
        sell = engine.record_manual_paper_order(symbol="AAPL", side="SELL", quantity=5, decision_object_id="DO-CPT", workflow_id="WF-CPT", token_id="TOK-CPT")
        closed = engine.position_registry.position(f"POS-AAPL-{buy['decision_object_id']}")
    finally:
        if previous_session is None:
            os.environ.pop("ARGOS_BROKER_SIM_MARKET_SESSION", None)
        else:
            os.environ["ARGOS_BROKER_SIM_MARKET_SESSION"] = previous_session
    exit_decision = {
        "exitDecisionRecords": (
            {
                "exit_decision_id": "EXD-CPT-001",
                "position_id": closed.position_id,
                "decision": "exit_full",
                "trigger_type": "profit_target_reached",
                "recommended_quantity": 5.0,
            },
        ),
        "latestDecisions": (),
    }
    benchmark = {
        "tradeLevelComparisons": (
            {
                "decisionObjectId": "DO-CPT",
                "benchmarkName": "SPY",
                "benchmarkReturn": 0.5,
                "argosReturn": 1.0,
                "excessReturn": 0.5,
            },
        )
    }
    return engine, buy, sell, surveillance, exit_decision, benchmark


class ARGOSControlPanelDashboardTests(unittest.TestCase):
    def _wait_for_state(self, runtime, predicate, *, timeout: float = 3.0, interval: float = 0.01):
        deadline = time.time() + timeout
        last_state = runtime.state()
        while time.time() < deadline:
            last_state = runtime.state()
            if predicate(last_state):
                return last_state
            time.sleep(interval)
        self.fail(f"condition was not met before timeout; last state keys: {tuple(last_state.keys())}")

    def _with_env(self, **values):
        previous = {key: os.environ.get(key) for key in values}
        for key, value in values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = str(value)
        return previous

    def _restore_env(self, previous):
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _portfolio_market_data(self, *, spread: float = 0.04, volume: float = 1000000.0):
        bid = round(100.0 - spread / 2, 4)
        ask = round(100.0 + spread / 2, 4)
        return {
            "normalizedObjects": {
                "quotes": (
                    {"symbol": "AAPL", "bid": bid, "ask": ask, "last": 100.0, "volume": volume},
                    {"symbol": "MSFT", "bid": 100.0, "ask": 100.04, "last": 100.02, "volume": 1000000.0},
                    {"symbol": "SPY", "bid": 100.0, "ask": 100.02, "last": 100.01, "volume": 1000000.0},
                )
            }
        }

    def _position(self, symbol: str, value: float, *, strategy: str = "Workflow Proof Strategy", asset_type: str = "STOCK"):
        return {
            "position_id": f"POS-{symbol}",
            "symbol": symbol,
            "asset_type": asset_type,
            "quantity": round(float(value) / 100.0, 4),
            "current_price": 100.0,
            "current_value": float(value),
            "currentStrategy": strategy,
        }

    def _portfolio_truth(self, *, cash: float, equity: float, positions: tuple[dict, ...] = (), orders: tuple[dict, ...] = ()):
        return {
            "paperAccount": {"cash": cash, "buyingPower": cash},
            "portfolioLedger": ({"cash": cash, "market_value": max(0.0, equity - cash), "total_equity": equity},),
            "positionRegistry": {"activePositions": positions},
            "positionLedger": positions,
            "orderLedger": orders,
            "brokerProfile": {"marginPermissions": False, "configuration": {"allowMargin": False}},
        }

    def test_or_002_manual_paper_order_is_provisional_broker_model(self) -> None:
        from argos.control_panel.performance_truth_engine import PerformanceTruthEngine

        previous = self._with_env(ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            engine = PerformanceTruthEngine(paper_starting_cash=10000.0)
            order = engine.record_manual_paper_order(symbol="AAPL", side="BUY", quantity=1, decision_object_id="DO-OR002", workflow_id="WF-OR002", token_id="TOK-OR002")
        finally:
            self._restore_env(previous)

        metadata = order["intended_order"]["truthMetadata"]
        self.assertEqual("PAPER", metadata["executionMode"])
        self.assertEqual("PAPER_PROVISIONAL_BROKER_MODEL", metadata["truthClassification"])
        self.assertEqual("PAPER_BROKER_PROVISIONAL_OR003", metadata["certificationStatus"])
        self.assertEqual("PAPER - PROVISIONAL BROKER MODEL", metadata["commanderTruthLabel"])

    def _capital_allocation_for_sizing(self, *, deployable: float = 20000.0, per_trade: float = 10000.0):
        return {
            "latestCapitalAllocationRecord": {"capital_allocation_id": "CALLOC-TEST", "deployable_capital": deployable},
            "positionSizingFeed": {
                "deployableCapital": deployable,
                "perTradeCapitalCeiling": per_trade,
                "maxCapitalPerStrategy": {"Workflow Proof Strategy": deployable},
                "maxCapitalPerAssetType": {"STOCK": deployable, "ETF": deployable},
                "maxCapitalPerSector": {"Technology": deployable, "Broad Market": deployable},
                "maxCapitalPerRiskBucket": {"low_risk": deployable, "medium_risk": deployable, "high_risk": deployable},
            },
        }

    def _portfolio_construction_for_sizing(self, *, action: str = "approve", notional: float = 10000.0, score: float = 90.0):
        return {
            "latestPortfolioConstructionRecord": {
                "portfolio_construction_id": "PCON-TEST",
                "recommended_action": action,
                "recommended_notional": notional,
                "construction_score": score,
            }
        }

    def _historical_replay_data(self):
        return {
            "dataSources": ("unit_test_history",),
            "bars": {
                "AAPL": (
                    {"timestamp": "2026-07-06T14:30:00Z", "close": 100.0, "volume": 1000000},
                    {"timestamp": "2026-07-07T14:30:00Z", "close": 102.0, "volume": 1000000},
                    {"timestamp": "2026-07-08T14:30:00Z", "close": 101.0, "volume": 1000000},
                ),
                "SPY": (
                    {"timestamp": "2026-07-06T14:30:00Z", "close": 400.0, "volume": 1000000},
                    {"timestamp": "2026-07-07T14:30:00Z", "close": 404.0, "volume": 1000000},
                    {"timestamp": "2026-07-08T14:30:00Z", "close": 402.0, "volume": 1000000},
                ),
                "QQQ": (
                    {"timestamp": "2026-07-06T14:30:00Z", "close": 300.0, "volume": 1000000},
                    {"timestamp": "2026-07-08T14:30:00Z", "close": 306.0, "volume": 1000000},
                ),
            },
        }

    def _executing_workflow_scope(self, runtime, stages=("Executive",), credit_budget=0.5):
        state = runtime.create_workflow("LAW VII Scoped Workflow", stages, 100, credit_budget, ("summary", "audit_identifier"))
        workflow = state["workflowOrchestrator"]["workflows"][-1]
        state = runtime.start_workflow_execution(workflow["workflow_id"])
        workflow = next(item for item in state["workflowOrchestrator"]["workflows"] if item["workflow_id"] == workflow["workflow_id"])
        return workflow["workflow_id"], workflow["token"]["audit_identifier"], workflow["token"]["current_owner"]

    def _gateway_request(self, workflow_id: str, token_id: str, office: str = "Analyst", cost: float = 0.001) -> ApiExecutionRequest:
        contract = self._prompt_contract(workflow_id, token_id, office, "AE-GATEWAY-TEST")
        return ApiExecutionRequest(
            workflow_id=workflow_id,
            workflow_token_id=token_id,
            requesting_office=office,
            workflow_stage=office,
            task_type="paper_trading_market_analysis",
            model="dry-run-model",
            prompt_template_id="PROMPT-TEST-GATEWAY",
            prompt_payload={"test": "gateway"},
            expected_output_schema=("summary", "evidence", "audit_identifier", "workflow_type", "workflow_stage", "initial_stage"),
            max_runtime_seconds=30,
            max_cost_usd=cost,
            max_input_tokens=128,
            max_output_tokens=128,
            audit_identifier="AE-GATEWAY-TEST",
            dry_run=True,
            prompt_contract_envelope=contract,
        )

    def _real_gateway_request(
        self,
        workflow_id: str,
        token_id: str,
        office: str = "Analyst",
        *,
        cost: float = 0.001,
        fallback: bool = True,
    ) -> ApiExecutionRequest:
        audit_identifier = "AE-REAL-GATEWAY-TEST"
        contract = self._prompt_contract(workflow_id, token_id, office, audit_identifier)
        return ApiExecutionRequest(
            workflow_id=workflow_id,
            workflow_token_id=token_id,
            requesting_office=office,
            workflow_stage=office,
            task_type="paper_trading_market_analysis",
            model=os.environ.get("ARGOS_REAL_API_MODEL", "gpt-4.1-mini"),
            prompt_template_id=contract["prompt_template_id"],
            prompt_payload={
                "current_decision_object": {"decisionObjectId": f"DO-{workflow_id}"},
                "seeker_revision": {"summary": "deterministic seeker signal"},
                "paper_market_context": {"environment": "paper"},
                "strategy_context": {"strategy": "test"},
                "risk_constraints": {"max_position_size": 0.05},
            },
            expected_output_schema=("summary", "evidence", "audit_identifier", "workflow_type", "workflow_stage", "initial_stage"),
            max_runtime_seconds=20,
            max_cost_usd=cost,
            max_input_tokens=2000,
            max_output_tokens=600,
            audit_identifier=audit_identifier,
            dry_run=False,
            execution_mode="real_api_pilot",
            provider=os.environ.get("ARGOS_REAL_API_PROVIDER", "openai"),
            decision_object_id=f"DO-{workflow_id}",
            allow_fallback_to_dry_run=fallback,
            prompt_contract_envelope=contract,
        )

    def _prompt_contract(self, workflow_id: str, token_id: str, office: str, audit_identifier: str) -> dict:
        decision_object_id = f"DO-{workflow_id}" if workflow_id else "DO-MISSING"
        return build_prompt_contract_envelope(
            library=PromptContractLibrary(),
            workflow_id=workflow_id,
            workflow_token_id=token_id,
            decision_object_id=decision_object_id,
            current_office=office,
            current_stage=office,
            current_revision=1,
            execution_environment="paper",
            strategy="test strategy",
            portfolio_context={"portfolio": "paper"},
            risk_constraints={"live_trading": False},
            commander_constraints={"no_live_trading": True},
            task=f"{office} test task",
            budget={"max_cost_usd": 0.001},
            audit_identifier=audit_identifier,
            decision_object={"decisionObjectId": decision_object_id},
            evidence_package={"test": "gateway"},
        )

    def _executing_paper_workflow_scope(self, runtime, stages=("Analyst",), credit_budget=0.01):
        workflow = runtime.workflow_orchestrator.create_validate_queue_assign(
            name="Real API Pilot Test Workflow",
            stages=stages,
            runtime_budget=100,
            credit_budget=credit_budget,
            expected_output_schema=("summary", "evidence", "audit_identifier", "workflow_type", "workflow_stage", "initial_stage"),
            workflow_type="paper_trading_session",
            initial_stage="market_preparation",
        )
        runtime.workflow_orchestrator.start_execution(workflow.workflow_id)
        workflow = runtime.workflow_orchestrator.workflow(workflow.workflow_id)
        return workflow.workflow_id, workflow.token.audit_identifier, workflow.token.current_owner

    def _valid_analyst_json(self) -> str:
        return json.dumps(
            {
                "recommendation": "BUY",
                "confidence": 0.73,
                "summary": "Real pilot Analyst JSON contract completed.",
                "evidence": ["seeker signal", "paper context"],
                "supporting_signals": ["momentum", "risk bounded"],
                "risk_flags": ["paper-only"],
                "expected_return": 0.041,
                "position_size_recommendation": 0.03,
                "target_price": 104.25,
                "stop_loss": 96.75,
                "confidence_reason": "Evidence was sufficient for a controlled paper recommendation.",
                "uncertainty_sources": ["paper simulation", "limited fixture context"],
                "required_additional_information": ["live market data unavailable by design"],
                "reasoning_audit": "Deterministic test provider returned schema-valid JSON.",
            }
        )

    def test_dashboard_state_contains_all_enterprise_groups_and_user_controls(self) -> None:
        runtime = create_runtime()

        state = runtime.state()

        self.assertEqual(len(state["groups"]), 8)
        self.assertEqual({group["name"] for group in state["groups"]}, {"Executive", "Seeker", "Analyst", "Risk", "Trader", "Historian", "Librarian", "Academy"})
        self.assertFalse(state["control"]["paper_trading_active"])
        self.assertTrue(state["control"]["real_world_trading_blocked"])
        self.assertIn("session_api_credits_usd", state["costs"])
        self.assertEqual(state["realWorldTradingSafety"], "BLOCKED_BY_CONFIGURATION")

    def test_start_paper_self_training_creates_tokenized_workflow_without_api_credit_burn(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="CLOSED")
        try:
            runtime = create_runtime()

            state = runtime.start_paper_self_training()
            active = state["workflowRuntimeMonitor"]["activeWorkflow"]
            workflow_id = active["workflowIdentifier"] if active else state["workflowOrchestrator"]["workflows"][-1]["workflow_id"]
            state = self._wait_for_state(
                runtime,
                lambda item: any(workflow["workflowIdentifier"] == workflow_id and workflow["status"] == "Archived" for workflow in item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            self.assertTrue(state["control"]["paper_trading_active"])
            self.assertEqual(state["environment"], "paper_trading")
            self.assertEqual(len(state["commands"]), 0)
            self.assertEqual(state["costs"]["session_api_credits_usd"], 0.001)
            self.assertEqual(1, state["workflowOrchestrator"]["metrics"]["workflowCount"])
            workflow = state["workflowOrchestrator"]["workflows"][0]
            self.assertEqual("Proof Workflow Session", workflow["name"])
            self.assertEqual("paper_trading_session", workflow["workflow_type"])
            self.assertEqual("market_preparation", workflow["initial_stage"])
            self.assertEqual(("Seeker", "Analyst", "Risk", "Trader", "Historian"), tuple(workflow["stages"]))
            self.assertEqual("Archived", workflow["token"]["workflow_status"])
            self.assertEqual("", workflow["token"]["current_owner"])
            self.assertEqual(5, workflow["token"]["transfer_count"])
            self.assertEqual(0, state["workflowOrchestrator"]["metrics"]["tokenExclusivityViolations"])
            self.assertEqual(0, state["workflowOrchestrator"]["metrics"]["nonDormantAfterTransferViolations"])
            self.assertEqual(5, len(state["workflowOrchestrator"]["auditHistory"]))
            self.assertEqual(("Seeker", "Analyst", "Risk", "Trader", "Historian"), tuple(item["previous_owner"] for item in state["workflowOrchestrator"]["auditHistory"]))
            self.assertEqual(1, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
            self.assertEqual(0.001, state["apiRuntimeMonitor"]["costThisSessionUsd"])
            self.assertEqual(0.001, state["apiRuntimeMonitor"]["officeCostTotalsUsd"]["Analyst"])
            self.assertTrue(all(value == 0.0 for office, value in state["apiRuntimeMonitor"]["officeCostTotalsUsd"].items() if office != "Analyst"))
            self.assertEqual(1, state["apiExecutionGateway"]["metrics"]["allowedCount"])
            self.assertEqual(1, state["workflowRuntimeMonitor"]["metrics"]["completedWorkflows"])
            self.assertEqual("Archived", state["workflowRuntimeMonitor"]["completedWorkflows"][0]["status"])
            self.assertEqual(1, len(state["performanceTruthEngine"]["orderLedger"]))
            self.assertEqual("QUEUED", state["performanceTruthEngine"]["orderLedger"][0]["status"])
            self.assertEqual("MARKET_CLOSED", state["performanceTruthEngine"]["orderLedger"][0]["queued_reason"])
            self.assertEqual(0, len(state["performanceTruthEngine"]["tradeLedger"]))
            self.assertEqual(0, len(state["performanceTruthEngine"]["positionLedger"]))
            self.assertEqual(1, state["performanceTruthEngine"]["integrity"]["proofModeTruthAttempts"])
            self.assertIn("PROOF_MODE_NOT_ACTIONABLE", state["performanceTruthEngine"]["rejectedTruthRecords"][0]["rejectionCodes"])
            latest_decision = workflow["output_history"][-1]["decision_object"]
            self.assertEqual("PROOF", latest_decision["executionMode"])
            self.assertEqual("PROOF_ONLY", latest_decision["truthClassification"])
            self.assertFalse(latest_decision["operationalProvenanceValidation"]["valid"])
        finally:
            self._restore_env(previous)

    def test_halt_paper_self_training_uses_trading_pause_and_remains_visible(self) -> None:
        runtime = create_runtime()
        runtime.start_paper_self_training()

        state = runtime.halt_paper_self_training()

        self.assertFalse(state["control"]["paper_trading_active"])
        self.assertEqual(state["control"]["latest_action_id"], "CPA-000002")
        self.assertTrue(any(item["action"] == "halt_paper_self_training" for item in state["commands"]))

    def test_treasury_and_live_trading_controls_are_visible_and_safe(self) -> None:
        runtime = create_runtime()

        funded = runtime.deposit_user_funds(1500.0)
        denied = runtime.request_real_world_trading()
        halted = runtime.halt_user_funds()

        self.assertEqual(funded["control"]["active_treasury_balance_usd"], 1500.0)
        self.assertFalse(denied["control"]["real_world_trading_active"])
        self.assertTrue(halted["control"]["user_funds_halted"])
        self.assertTrue(any(item["status"] == "DENIED" for item in denied["activity"]))

    def test_ui_files_expose_required_controls_and_metrics(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        self.assertIn("ARGOS CONTROL PANEL", html)
        self.assertIn("Start Paper Trading", html)
        self.assertIn("API Credit Burn", html)
        self.assertIn("Deposit User Funds", html)
        self.assertIn("Request Live Trading", html)
        self.assertIn("API Runtime Monitor", html)
        self.assertIn("Enterprise Workflow Orchestrator", html)
        self.assertIn("Workflow Runtime Monitor", html)
        self.assertIn("Prompt & Cognitive Contract", html)
        self.assertIn("prompt-contract-templates", html)
        self.assertIn("Controlled Cognitive Pilot", html)
        self.assertIn("cognitive-pilot-report", html)
        self.assertIn("arm-cost-chart", html)
        self.assertIn('width="1180"', html)
        self.assertIn("arm-cost-legend", html)
        self.assertIn("Open Live Feed", html)
        self.assertIn("Reset API Runtime Session", html)
        self.assertIn("Market data ingestion", html)
        self.assertIn("/api/paper/start", js)
        self.assertIn("/api/treasury/deposit", js)
        self.assertIn("/api/api-runtime-monitor/control", js)
        self.assertIn("/api/api-runtime-monitor/reset-session", js)
        self.assertIn("/api/api-runtime-monitor/reset-session", server)
        self.assertIn("/api/workflow-orchestrator/create", js)
        self.assertIn("renderWorkflowRuntimeMonitor", js)
        self.assertIn("drawApiRuntimeCostChart", js)
        self.assertIn("renderApiRuntimeCostLegend", js)
        self.assertIn("renderApiRuntimeLiveFeed", js)
        self.assertIn("renderPromptContract", js)
        self.assertIn("renderControlledCognitivePilot", js)

    def test_api_runtime_monitor_tracks_visible_ai_activation_and_controls(self) -> None:
        runtime = create_runtime()
        workflow_id, workflow_token_id, owner = self._executing_workflow_scope(runtime)

        initial = runtime.state()
        self.assertIn("apiRuntimeMonitor", initial)
        self.assertGreaterEqual(initial["apiRuntimeMonitor"]["metrics"]["sleepingCount"], 8)

        activated = runtime.request_credit_activation(
            task_identifier="TASK-COMMANDER-EXPLAIN",
            activating_source="Commander",
            receiving_office="Executive",
            purpose="Commander explanation",
            required_output="Structured explanation",
            maximum_runtime_minutes=5,
            maximum_credit_budget_usd=0.25,
            workflow="Commander Explanation Workflow",
            organization="Executive",
            evidence_package=("COMMANDER-REQUEST",),
            workflow_id=workflow_id,
            workflow_token_id=workflow_token_id,
            office=owner,
        )
        monitor = activated["apiRuntimeMonitor"]

        self.assertEqual(1, monitor["metrics"]["apiCallsLogged"])
        self.assertEqual(1, monitor["metrics"]["activeCount"])
        self.assertTrue(any(entity["office"] == "Executive" and entity["current_state"] == "Running" for entity in monitor["activeApiEntities"]))
        self.assertEqual("ARM-CALL-000001", monitor["recentApiCalls"][0]["call_id"])
        self.assertEqual(("Commander", "Executive", "Commander Interface"), tuple(monitor["activeActivationChains"][0]["chain"]))

        controlled = runtime.api_runtime_monitor_control("force_sleep", "Executive")
        self.assertTrue(any(entity["office"] == "Executive" and entity["current_state"] == "Sleeping" for entity in controlled["apiRuntimeMonitor"]["entities"]))
        self.assertTrue(any(item["action"] == "force_sleep" for item in controlled["apiRuntimeMonitor"]["controls"]))

    def test_api_runtime_monitor_exposes_live_office_cost_chart_series_for_authorized_usage(self) -> None:
        runtime = create_runtime()
        workflow_id, workflow_token_id, owner = self._executing_workflow_scope(runtime)

        state = runtime.request_credit_activation(
            task_identifier="TASK-COMMANDER-EXPLAIN",
            activating_source="Commander",
            receiving_office="Executive",
            purpose="Commander explanation",
            required_output="Structured explanation",
            maximum_runtime_minutes=5,
            maximum_credit_budget_usd=0.10,
            workflow="Commander Explanation Workflow",
            organization="Executive",
            evidence_package=("COMMANDER-REQUEST",),
            workflow_id=workflow_id,
            workflow_token_id=workflow_token_id,
            office=owner,
        )

        monitor = state["apiRuntimeMonitor"]
        totals = monitor["officeCostTotalsUsd"]

        self.assertIn("Commander", totals)
        self.assertIn("Risk Fusion Office", totals)
        self.assertGreater(totals["Executive"], 0.0)
        self.assertEqual(totals["Academy Fusion Office"], 0.0)
        self.assertGreaterEqual(len(monitor["officeCostSeries"]), 1)
        self.assertIn("timestampUtc", monitor["officeCostSeries"][-1])
        self.assertIn("totalsUsd", monitor["officeCostSeries"][-1])

    def test_new_runtime_starts_with_empty_zero_api_cost_series(self) -> None:
        runtime = create_runtime()

        state = runtime.state()
        monitor = state["apiRuntimeMonitor"]

        self.assertEqual(0, monitor["metrics"]["apiCallsLogged"])
        self.assertEqual(0.0, monitor["costThisSessionUsd"])
        self.assertEqual((), monitor["officeCostSeries"])
        self.assertTrue(all(value == 0.0 for value in monitor["officeCostTotalsUsd"].values()))

    def test_zero_api_calls_suppress_stale_office_cost_series(self) -> None:
        runtime = create_runtime()
        runtime.api_runtime_monitor.record_office_usage("Executive", "Commander", 0.25, "2026-07-06T00:00:00Z")

        state = runtime.state()
        monitor = state["apiRuntimeMonitor"]

        self.assertEqual(0, monitor["metrics"]["apiCallsLogged"])
        self.assertEqual(0.0, monitor["costThisSessionUsd"])
        self.assertEqual((), monitor["officeCostSeries"])
        self.assertTrue(all(value == 0.0 for value in monitor["officeCostTotalsUsd"].values()))

    def test_api_runtime_reset_session_clears_chart_data(self) -> None:
        runtime = create_runtime()
        workflow_id, workflow_token_id, owner = self._executing_workflow_scope(runtime)
        activated = runtime.request_credit_activation(
            task_identifier="TASK-OWNER",
            activating_source="Commander",
            receiving_office=owner,
            purpose="Commander explanation",
            required_output="Structured explanation",
            maximum_runtime_minutes=5,
            maximum_credit_budget_usd=0.10,
            workflow="Commander Explanation Workflow",
            organization=owner,
            evidence_package=("COMMANDER-REQUEST",),
            workflow_id=workflow_id,
            workflow_token_id=workflow_token_id,
            office=owner,
        )
        self.assertEqual(1, activated["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
        self.assertGreater(activated["apiRuntimeMonitor"]["costThisSessionUsd"], 0.0)

        state = runtime.reset_api_runtime_session()
        monitor = state["apiRuntimeMonitor"]

        self.assertEqual(0, monitor["metrics"]["apiCallsLogged"])
        self.assertEqual(0.0, monitor["costThisSessionUsd"])
        self.assertEqual((), monitor["officeCostSeries"])
        self.assertEqual((), monitor["activeApiEntities"])
        self.assertEqual((), monitor["blockedApiEntities"])
        self.assertEqual((), monitor["activeActivationChains"])
        self.assertEqual((), monitor["loopDetectionAlerts"])
        self.assertEqual((), monitor["budgetStops"])
        self.assertTrue(all(value == 0.0 for value in monitor["officeCostTotalsUsd"].values()))

    def test_api_runtime_reset_session_does_not_delete_audit_records(self) -> None:
        runtime = create_runtime()
        runtime.start_paper_self_training()
        before = len(runtime.audit.audit_log.events)

        runtime.reset_api_runtime_session()
        after = len(runtime.audit.audit_log.events)

        self.assertGreater(before, 0)
        self.assertGreaterEqual(after, before)

    def test_api_runtime_monitor_detects_repeated_activation_chain(self) -> None:
        runtime = create_runtime()
        workflow_id, workflow_token_id, owner = self._executing_workflow_scope(runtime, credit_budget=1.0)

        for task in ("TASK-COMMANDER-EXPLAIN-1", "TASK-COMMANDER-EXPLAIN-2"):
            state = runtime.request_credit_activation(
                task_identifier=task,
                activating_source="Commander",
                receiving_office="Executive",
                purpose="Commander explanation",
                required_output="Structured explanation",
                maximum_runtime_minutes=5,
                maximum_credit_budget_usd=0.10,
                workflow="Commander Explanation Workflow",
                organization="Executive",
                evidence_package=("COMMANDER-REQUEST",),
                workflow_id=workflow_id,
                workflow_token_id=workflow_token_id,
                office=owner,
            )

        self.assertTrue(state["apiRuntimeMonitor"]["loopDetectionAlerts"])

    def test_credit_governor_rejects_cross_office_chatter_and_market_data_ai_triggers(self) -> None:
        runtime = create_runtime()
        risk_workflow_id, risk_token_id, risk_owner = self._executing_workflow_scope(runtime, stages=("Risk",), credit_budget=1.0)
        analyst_workflow_id, analyst_token_id, analyst_owner = self._executing_workflow_scope(runtime, stages=("Analyst",), credit_budget=1.0)

        chatter = runtime.request_credit_activation(
            task_identifier="TASK-RISK-CHATTER",
            activating_source="Seeker",
            receiving_office="Risk",
            purpose="Conflict analysis",
            required_output="Risk challenge",
            maximum_runtime_minutes=5,
            maximum_credit_budget_usd=0.10,
            workflow="Cross Office Chatter Workflow",
            organization="Risk",
            evidence_package=("TRADE-CANDIDATE",),
            workflow_id=risk_workflow_id,
            workflow_token_id=risk_token_id,
            office=risk_owner,
        )
        market_data = runtime.request_credit_activation(
            task_identifier="TASK-TICK-QUOTE-001",
            activating_source="Enterprise Event",
            receiving_office="Analyst",
            purpose="Ambiguous reasoning",
            required_output="Reasoning response",
            maximum_runtime_minutes=5,
            maximum_credit_budget_usd=0.10,
            workflow="Market data quote workflow",
            organization="Analyst",
            evidence_package=("PRICE-UPDATE",),
            workflow_id=analyst_workflow_id,
            workflow_token_id=analyst_token_id,
            office=analyst_owner,
        )

        self.assertEqual("REJECTED", chatter["creditGovernor"]["activations"][0]["status"])
        self.assertTrue(any(item["category"] == "Cross-Office Chatter" for item in chatter["creditGovernor"]["detections"]))
        self.assertEqual("REJECTED", market_data["creditGovernor"]["activations"][0]["status"])
        self.assertTrue(any(item["category"] == "Market Data AI Trigger" for item in market_data["creditGovernor"]["detections"]))

    def test_credit_governor_detects_paper_trading_overactivation(self) -> None:
        runtime = create_runtime()
        runtime.start_paper_self_training()
        workflow_id, workflow_token_id, owner = self._executing_workflow_scope(runtime, stages=("Analyst",), credit_budget=1.0)

        state = runtime.request_credit_activation(
            task_identifier="TASK-PAPER-CANDLE-001",
            activating_source="Enterprise Event",
            receiving_office="Analyst",
            purpose="Ambiguous reasoning",
            required_output="Reasoning response",
            maximum_runtime_minutes=5,
            maximum_credit_budget_usd=0.10,
            workflow="Paper trading candle workflow",
            organization="Analyst",
            evidence_package=("CANDLE-UPDATE",),
            workflow_id=workflow_id,
            workflow_token_id=workflow_token_id,
            office=owner,
        )

        self.assertEqual("REJECTED", state["creditGovernor"]["activations"][0]["status"])
        self.assertTrue(any(item["category"] == "Paper-Trading Overactivation" for item in state["creditGovernor"]["detections"]))

    def test_state_polling_does_not_increase_api_totals(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="CLOSED")
        runtime = create_runtime()
        try:
            runtime.start_paper_self_training()
            self._wait_for_state(runtime, lambda item: item["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"] == 1, timeout=2.0)
            runtime.halt_paper_self_training()
            self._wait_for_state(runtime, lambda item: item["workflowOrchestrator"]["metrics"]["activeWorkflowCount"] == 0, timeout=2.0)

            before = runtime.state()
            for _ in range(5):
                after = runtime.state()

            self.assertEqual(before["costs"]["session_api_credits_usd"], after["costs"]["session_api_credits_usd"])
            self.assertEqual(before["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"], after["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
        finally:
            self._restore_env(previous)

    def test_paper_trading_start_does_not_charge_all_offices(self) -> None:
        previous = self._with_env(ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
        runtime = create_runtime()

        try:
            state = runtime.start_paper_self_training()
            state = self._wait_for_state(runtime, lambda item: item["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"] == 1, timeout=5.0)
            runtime.halt_paper_self_training()
            totals = state["apiRuntimeMonitor"]["officeCostTotalsUsd"]

            self.assertTrue(state["control"]["paper_trading_active"])
            self.assertEqual(0.001, totals["Analyst"])
            self.assertTrue(all(value == 0.0 for office, value in totals.items() if office != "Analyst"))
        finally:
            self._restore_env(previous)

    def test_api_usage_without_workflow_scope_is_rejected(self) -> None:
        runtime = create_runtime()

        state = runtime.request_credit_activation(
            task_identifier="TASK-UNSCOPED",
            activating_source="Commander",
            receiving_office="Executive",
            purpose="Commander explanation",
            required_output="Structured explanation",
            maximum_runtime_minutes=5,
            maximum_credit_budget_usd=0.10,
            workflow="Commander Explanation Workflow",
            organization="Executive",
            evidence_package=("COMMANDER-REQUEST",),
        )

        self.assertEqual("REJECTED", state["creditGovernor"]["activations"][0]["status"])
        self.assertEqual("LAW_VII_VIOLATION_UNSCOPED_API_USAGE", state["creditGovernor"]["activations"][0]["law_vii_validation"])
        self.assertEqual(0, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])

    def test_non_token_owner_office_cannot_record_api_usage(self) -> None:
        runtime = create_runtime()
        workflow_id, workflow_token_id, _owner = self._executing_workflow_scope(runtime, stages=("Executive", "Risk"), credit_budget=0.5)

        state = runtime.request_credit_activation(
            task_identifier="TASK-NON-OWNER",
            activating_source="Commander",
            receiving_office="Risk",
            purpose="Commander explanation",
            required_output="Structured explanation",
            maximum_runtime_minutes=5,
            maximum_credit_budget_usd=0.10,
            workflow="Commander Explanation Workflow",
            organization="Risk",
            evidence_package=("COMMANDER-REQUEST",),
            workflow_id=workflow_id,
            workflow_token_id=workflow_token_id,
            office="Risk",
        )

        self.assertEqual("REJECTED", state["creditGovernor"]["activations"][0]["status"])
        self.assertEqual("LAW_VII_VIOLATION_NON_OWNER_API_USAGE", state["creditGovernor"]["activations"][0]["law_vii_validation"])
        self.assertEqual(0, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])

    def test_only_current_token_owner_can_record_api_usage(self) -> None:
        runtime = create_runtime()
        workflow_id, workflow_token_id, owner = self._executing_workflow_scope(runtime, credit_budget=0.5)

        state = runtime.request_credit_activation(
            task_identifier="TASK-OWNER",
            activating_source="Commander",
            receiving_office=owner,
            purpose="Commander explanation",
            required_output="Structured explanation",
            maximum_runtime_minutes=5,
            maximum_credit_budget_usd=0.10,
            workflow="Commander Explanation Workflow",
            organization=owner,
            evidence_package=("COMMANDER-REQUEST",),
            workflow_id=workflow_id,
            workflow_token_id=workflow_token_id,
            office=owner,
        )

        self.assertEqual("APPROVED", state["creditGovernor"]["activations"][0]["status"])
        self.assertEqual("LAW_VII_API_USAGE_AUTHORIZED", state["creditGovernor"]["activations"][0]["law_vii_validation"])
        self.assertEqual(1, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])

    def test_api_execution_gateway_blocks_unscoped_unknown_and_non_owner_requests(self) -> None:
        runtime = create_runtime()
        workflow_id, workflow_token_id, _owner = self._executing_workflow_scope(runtime, stages=("Analyst", "Risk"), credit_budget=0.5)

        missing_workflow = runtime.api_execution_gateway.execute_model_request(self._gateway_request("", workflow_token_id))
        missing_token = runtime.api_execution_gateway.execute_model_request(self._gateway_request(workflow_id, ""))
        non_owner = runtime.api_execution_gateway.execute_model_request(self._gateway_request(workflow_id, workflow_token_id, office="Risk"))
        unknown_workflow = runtime.api_execution_gateway.execute_model_request(self._gateway_request("EWO-WF-UNKNOWN", workflow_token_id))
        unknown_token = runtime.api_execution_gateway.execute_model_request(self._gateway_request(workflow_id, "AE-EWO-UNKNOWN"))

        self.assertEqual("LAW_VII_VIOLATION_UNSCOPED_API_REQUEST", missing_workflow.violation_code)
        self.assertEqual("LAW_VII_VIOLATION_UNSCOPED_API_REQUEST", missing_token.violation_code)
        self.assertEqual("LAW_VII_VIOLATION_NON_OWNER_API_REQUEST", non_owner.violation_code)
        self.assertEqual("LAW_VII_VIOLATION_UNKNOWN_WORKFLOW", unknown_workflow.violation_code)
        self.assertEqual("LAW_VII_VIOLATION_UNKNOWN_TOKEN", unknown_token.violation_code)
        state = runtime.state()
        self.assertEqual(0, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
        self.assertEqual(5, state["apiExecutionGateway"]["metrics"]["blockedCount"])

    def test_api_execution_gateway_blocks_not_executing_and_over_budget_without_consuming_credits(self) -> None:
        runtime = create_runtime()
        assigned = runtime.create_workflow("Gateway Assigned Workflow", ("Analyst",), 100, 0.5, ("summary", "audit_identifier"))
        assigned_workflow = assigned["workflowOrchestrator"]["workflows"][-1]
        not_executing = runtime.api_execution_gateway.execute_model_request(
            self._gateway_request(assigned_workflow["workflow_id"], assigned_workflow["token"]["audit_identifier"])
        )

        workflow_id, token_id, _owner = self._executing_workflow_scope(runtime, stages=("Analyst",), credit_budget=0.0005)
        over_budget = runtime.api_execution_gateway.execute_model_request(self._gateway_request(workflow_id, token_id, cost=0.001))

        self.assertEqual("LAW_VII_VIOLATION_WORKFLOW_NOT_EXECUTING", not_executing.violation_code)
        self.assertEqual("LAW_VII_VIOLATION_BUDGET_EXCEEDED", over_budget.violation_code)
        state = runtime.state()
        self.assertEqual(0, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
        self.assertEqual(0.0, state["apiRuntimeMonitor"]["costThisSessionUsd"])
        self.assertEqual(2, state["apiExecutionGateway"]["metrics"]["blockedCount"])

    def test_api_execution_gateway_success_updates_audit_credit_governor_and_api_runtime(self) -> None:
        runtime = create_runtime()
        workflow_id, token_id, _owner = self._executing_workflow_scope(runtime, stages=("Analyst",), credit_budget=0.5)

        response = runtime.api_execution_gateway.execute_model_request(self._gateway_request(workflow_id, token_id))
        state = runtime.state()

        self.assertTrue(response.allowed)
        self.assertFalse(response.blocked)
        self.assertEqual("DRY_RUN_COMPLETED", response.execution_status)
        self.assertEqual("Analyst", response.requesting_office)
        self.assertEqual(0.001, response.actual_cost_usd)
        self.assertIn("api_execution_gateway", response.structured_output)
        self.assertEqual(1, state["apiExecutionGateway"]["metrics"]["allowedCount"])
        self.assertEqual(1, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
        self.assertEqual(0.001, state["apiRuntimeMonitor"]["officeCostTotalsUsd"]["Analyst"])
        self.assertTrue(all(value == 0.0 for office, value in state["apiRuntimeMonitor"]["officeCostTotalsUsd"].items() if office != "Analyst"))
        self.assertEqual("COMPLETED", state["creditGovernor"]["activations"][0]["status"])
        self.assertEqual("LAW_VII_API_USAGE_AUTHORIZED", state["creditGovernor"]["activations"][0]["law_vii_validation"])
        self.assertEqual(0.001, state["costs"]["workflow_token_authorized_api_usage_usd"])

    def test_enterprise_workflow_orchestrator_enforces_token_lifecycle_and_dormancy(self) -> None:
        runtime = create_runtime()

        created = runtime.create_workflow(
            "Commander Evidence Workflow",
            ("Executive", "Seeker", "Analyst"),
            100,
            0.5,
            ("summary", "evidence", "audit_identifier"),
        )
        workflow = created["workflowOrchestrator"]["workflows"][0]

        self.assertEqual("Assigned", workflow["token"]["workflow_status"])
        self.assertEqual("Executive", workflow["token"]["current_owner"])
        self.assertEqual(0, created["workflowOrchestrator"]["metrics"]["tokenExclusivityViolations"])

        executing = runtime.start_workflow_execution(workflow["workflow_id"])
        workflow = executing["workflowOrchestrator"]["workflows"][0]
        self.assertEqual("Executing", workflow["token"]["workflow_status"])
        self.assertEqual("Executing", workflow["office_states"]["Executive"])

        output = runtime.produce_workflow_output(
            workflow["workflow_id"],
            {"summary": "ok", "evidence": "EV-1", "audit_identifier": "AE-1"},
            10,
            0.05,
            100,
            3,
        )
        workflow = output["workflowOrchestrator"]["workflows"][0]
        self.assertEqual("Structured Output Produced", workflow["token"]["workflow_status"])
        self.assertEqual("VALID", workflow["validation_status"])

        transferred = runtime.transfer_workflow_token(workflow["workflow_id"])
        workflow = transferred["workflowOrchestrator"]["workflows"][0]
        self.assertEqual("Ownership Transferred", workflow["token"]["workflow_status"])
        self.assertEqual("Executive", workflow["token"]["previous_owner"])
        self.assertEqual("Seeker", workflow["token"]["current_owner"])
        self.assertEqual("Dormant", workflow["office_states"]["Executive"])
        self.assertEqual("Assigned", workflow["office_states"]["Seeker"])
        self.assertEqual(1, len(transferred["workflowOrchestrator"]["auditHistory"]))
        self.assertEqual(0, transferred["workflowOrchestrator"]["metrics"]["nonDormantAfterTransferViolations"])

        next_stage = runtime.advance_workflow_stage(workflow["workflow_id"])
        workflow = next_stage["workflowOrchestrator"]["workflows"][0]
        self.assertEqual("Assigned", workflow["token"]["workflow_status"])
        self.assertEqual("Seeker", workflow["token"]["current_owner"])

    def test_enterprise_workflow_orchestrator_blocks_budget_and_schema_violations(self) -> None:
        runtime = create_runtime()
        state = runtime.create_workflow("Budget Workflow", ("Executive",), 5, 0.01, ("summary", "audit_identifier"))
        workflow_id = state["workflowOrchestrator"]["workflows"][0]["workflow_id"]
        runtime.start_workflow_execution(workflow_id)

        with self.assertRaises(ValueError):
            runtime.produce_workflow_output(workflow_id, {"summary": "missing audit"}, 1, 0.001, 10, 1)

        with self.assertRaises(ValueError):
            runtime.produce_workflow_output(workflow_id, {"summary": "ok", "audit_identifier": "AE"}, 6, 0.001, 10, 1)

    def test_structured_output_is_required_before_workflow_transfer(self) -> None:
        runtime = create_runtime()
        state = runtime.create_workflow("Structured Gate Workflow", ("Seeker", "Analyst"), 20, 0.01, ("summary", "audit_identifier"))
        workflow_id = state["workflowOrchestrator"]["workflows"][0]["workflow_id"]
        runtime.start_workflow_execution(workflow_id)

        with self.assertRaises(ValueError):
            runtime.transfer_workflow_token(workflow_id)

    def test_workflow_runtime_monitor_observes_token_movement_and_timeline(self) -> None:
        runtime = create_runtime()

        state = runtime.create_workflow(
            "Monitor Workflow",
            ("Executive", "Seeker"),
            100,
            0.5,
            ("summary", "evidence", "audit_identifier"),
        )
        monitor = state["workflowRuntimeMonitor"]

        self.assertTrue(monitor["observationalOnly"])
        self.assertTrue(monitor["doesNotExecuteWorkflows"])
        self.assertTrue(monitor["doesNotTransferTokens"])
        self.assertEqual(1, monitor["metrics"]["activeWorkflows"])
        self.assertEqual("Executive", monitor["allWorkflows"][0]["currentOwner"])
        self.assertIn("Seeker", monitor["allWorkflows"][0]["waitingOffices"])
        self.assertTrue(any(event["event_type"] == "Workflow Created" for event in monitor["timeline"]))
        self.assertTrue(any(event["event_type"] == "Ownership Assigned" for event in monitor["timeline"]))

        state = runtime.start_workflow_execution(monitor["allWorkflows"][0]["workflowIdentifier"])
        monitor = state["workflowRuntimeMonitor"]
        self.assertEqual("Executing", monitor["allWorkflows"][0]["stageProgress"]["Executive"])
        self.assertEqual(0, monitor["metrics"]["commanderAlertCount"])

        state = runtime.produce_workflow_output(
            monitor["allWorkflows"][0]["workflowIdentifier"],
            {"summary": "ok", "evidence": "EV", "audit_identifier": "AE"},
            8,
            0.05,
            100,
            4,
        )
        state = runtime.transfer_workflow_token(monitor["allWorkflows"][0]["workflowIdentifier"])
        monitor = state["workflowRuntimeMonitor"]
        self.assertEqual("Seeker", monitor["allWorkflows"][0]["currentOwner"])
        self.assertEqual("Executive", monitor["allWorkflows"][0]["previousOwner"])
        self.assertTrue(any(event["event_type"] == "Ownership Transferred" for event in monitor["timeline"]))
        self.assertTrue(monitor["tokenIntegrity"]["exactlyOneOwner"])

    def test_workflow_runtime_monitor_displays_delayed_paper_workflow_without_api_usage(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="1.25", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
        try:
            runtime = create_runtime()
            state = runtime.start_paper_self_training()
            monitor = state["workflowRuntimeMonitor"]
            self.assertEqual(1, len(monitor["liveWorkflowExecution"]))
            active = monitor["liveWorkflowExecution"][0]
            workflow_id = active["workflowIdentifier"]

            self.assertEqual("Proof Workflow Session", active["workflowName"])
            self.assertEqual("Executing", active["status"])
            self.assertEqual("Seeker", active["currentOwner"])
            self.assertEqual(active["workflowIdentifier"], monitor["activeWorkflow"]["workflowIdentifier"])
            self.assertEqual("Seeker is executing market discovery.", monitor["commanderStatusLine"])
            self.assertEqual("VALID", monitor["tokenIntegrity"]["status"])
            self.assertEqual(0, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
            self.assertEqual(0.0, state["apiRuntimeMonitor"]["costThisSessionUsd"])
            self.assertEqual("VALID", active["lawViiStatus"])

            baton = monitor["workflowBaton"]
            self.assertEqual(workflow_id, baton["workflowIdentifier"])
            self.assertEqual(
                ["ACTIVE", "WAITING", "WAITING", "WAITING", "WAITING"],
                [stage["status"] for stage in baton["stages"]],
            )
            self.assertEqual("Seeker", baton["stages"][0]["stage_name"])
            self.assertEqual("Seeker", baton["stages"][0]["office"])
            self.assertTrue(baton["stages"][0]["started_at"])

            def assert_one_owner(current_state):
                workflow = next(item for item in current_state["workflowOrchestrator"]["workflows"] if item["workflow_id"] == workflow_id)
                owner = workflow["token"]["current_owner"]
                active_owners = tuple(office for office, status in workflow["office_states"].items() if status in {"Assigned", "Executing"})
                self.assertEqual((owner,), active_owners)
                self.assertEqual(0, current_state["workflowOrchestrator"]["metrics"]["tokenExclusivityViolations"])
                self.assertEqual(0, current_state["workflowOrchestrator"]["metrics"]["nonDormantAfterTransferViolations"])

            assert_one_owner(state)
            expected_prefix = (
                ("Seeker", ["ACTIVE", "WAITING", "WAITING", "WAITING", "WAITING"]),
                ("Analyst", ["COMPLETED", "ACTIVE", "WAITING", "WAITING", "WAITING"]),
                ("Risk", ["COMPLETED", "COMPLETED", "ACTIVE", "WAITING", "WAITING"]),
                ("Trader", ["COMPLETED", "COMPLETED", "COMPLETED", "ACTIVE", "WAITING"]),
                ("Historian", ["COMPLETED", "COMPLETED", "COMPLETED", "COMPLETED", "ACTIVE"]),
            )
            observed = {"Seeker"}
            for owner, stage_states in expected_prefix[1:]:
                state = self._wait_for_state(
                    runtime,
                    lambda item, expected=owner: any(
                        workflow["workflowIdentifier"] == workflow_id and workflow["currentOwner"] == expected and workflow["status"] == "Executing"
                        for workflow in item["workflowRuntimeMonitor"]["liveWorkflowExecution"]
                    ),
                    timeout=20.0,
                )
                observed.add(owner)
                assert_one_owner(state)
                active = state["workflowRuntimeMonitor"]["activeWorkflow"]
                self.assertEqual(owner, active["currentOwner"])
                self.assertEqual(expected_prefix.index((owner, stage_states)) + 1, active["stageNumber"])
                self.assertIn(owner, state["workflowRuntimeMonitor"]["commanderStatusLine"])
                baton = state["workflowRuntimeMonitor"]["workflowBaton"]
                self.assertEqual(stage_states, [stage["status"] for stage in baton["stages"]])
                self.assertEqual(1, sum(1 for stage in baton["stages"] if stage["status"] == "ACTIVE"))
                self.assertEqual(owner, next(stage["office"] for stage in baton["stages"] if stage["status"] == "ACTIVE"))
                if owner == "Analyst":
                    self.assertEqual("Seeker", active["previousOwner"])
                    self.assertEqual("Risk", active["nextOwner"])
                expected_calls = 1 if owner in {"Risk", "Trader", "Historian"} else 0
                self.assertEqual(expected_calls, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
                self.assertEqual(round(expected_calls * 0.001, 3), state["apiRuntimeMonitor"]["costThisSessionUsd"])

            self.assertEqual({"Seeker", "Analyst", "Risk", "Trader", "Historian"}, observed)
            state = self._wait_for_state(
                runtime,
                lambda item: any(workflow["workflowIdentifier"] == workflow_id and workflow["status"] == "Archived" for workflow in item["workflowRuntimeMonitor"]["allWorkflows"]),
                timeout=10.0,
            )
            monitor = state["workflowRuntimeMonitor"]
            retained = next(item for item in monitor["recentCompletedWorkflows"] if item["workflowIdentifier"] == workflow_id)
            self.assertEqual("Archived", retained["status"])
            self.assertEqual(100, retained["progress"])
            self.assertEqual(5, retained["structuredOutputsProduced"])
            archived_baton = next(item for item in monitor["workflowBatonView"] if item["workflowIdentifier"] == workflow_id)
            self.assertEqual(["COMPLETED", "COMPLETED", "COMPLETED", "COMPLETED", "COMPLETED"], [stage["status"] for stage in archived_baton["stages"]])
            integrity = next(item for item in monitor["workflowTokenIntegrityPanel"] if item["workflowIdentifier"] == workflow_id)
            self.assertEqual("VALID", integrity["lawViiStatus"])
            self.assertTrue(any(event["event_type"] == "Token Transferred" for event in monitor["workflowTimeline"]))
            self.assertTrue(any(event["event_type"] == "Stage Completed" for event in monitor["workflowTimeline"]))
            self.assertEqual("Workflow completed and archived.", retained["commanderStatusLine"])
            self.assertEqual(1, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
            self.assertEqual(0.001, state["apiRuntimeMonitor"]["costThisSessionUsd"])
            self.assertEqual(1, state["apiExecutionGateway"]["metrics"]["allowedCount"])
        finally:
            self._restore_env(previous)

    def test_workflow_runtime_monitor_retains_latest_ten_completed_workflows(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: item["workflowRuntimeMonitor"]["metrics"]["completedWorkflows"] >= 12,
                timeout=90.0,
            )
            runtime.halt_paper_self_training()
            monitor = state["workflowRuntimeMonitor"]
            retained = monitor["recentCompletedWorkflows"]
            self.assertEqual(10, len(retained))
            self.assertEqual("Archived", retained[-1]["status"])
            self.assertEqual(100, retained[-1]["progress"])
            self.assertEqual(5, retained[-1]["structured_outputs_produced"])
            self.assertEqual("COMPLETE", retained[-1]["execution_health"])
            self.assertTrue(retained[-1]["completed_at"])
            self.assertGreaterEqual(state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"], 12)
            self.assertEqual(round(state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"] * 0.001, 3), state["apiRuntimeMonitor"]["costThisSessionUsd"])
            self.assertGreaterEqual(state["apiExecutionGateway"]["metrics"]["allowedCount"], 12)
            self.assertEqual("VALID", monitor["tokenIntegrity"]["status"])
        finally:
            self._restore_env(previous)

    def test_paper_trading_loop_continues_until_halt_with_single_active_workflow(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0.02", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="false")
        try:
            runtime = create_runtime()
            state = runtime.start_paper_self_training()
            first_thread_id = runtime._paper_runner_thread.ident
            runtime.start_paper_self_training()
            self.assertEqual(first_thread_id, runtime._paper_runner_thread.ident)

            state = self._wait_for_state(
                runtime,
                lambda item: item["workflowOrchestrator"]["metrics"]["workflowCount"] >= 2,
                timeout=2.0,
            )
            self.assertTrue(state["control"]["paper_trading_active"])
            paper_workflows = [workflow for workflow in state["workflowOrchestrator"]["workflows"] if workflow["workflow_type"] == "paper_trading_session"]
            active_paper = [workflow for workflow in paper_workflows if workflow["token"]["workflow_status"] not in {"Completed", "Archived"}]
            self.assertLessEqual(len(active_paper), 1)
            self.assertEqual(0, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
            self.assertEqual("VALID", state["workflowRuntimeMonitor"]["tokenIntegrity"]["status"])

            halted = runtime.halt_paper_self_training()
            self.assertFalse(halted["control"]["paper_trading_active"])
            state = self._wait_for_state(
                runtime,
                lambda item: item["workflowOrchestrator"]["metrics"]["activeWorkflowCount"] == 0,
                timeout=2.0,
            )
            final_count = state["workflowOrchestrator"]["metrics"]["workflowCount"]
            time.sleep(0.12)
            after_wait = runtime.state()
            self.assertEqual(final_count, after_wait["workflowOrchestrator"]["metrics"]["workflowCount"])
            self.assertEqual(0, after_wait["workflowOrchestrator"]["metrics"]["activeWorkflowCount"])
            self.assertTrue(all(workflow["token"]["workflow_status"] == "Archived" for workflow in after_wait["workflowOrchestrator"]["workflows"]))
            self.assertEqual(0.0, after_wait["apiRuntimeMonitor"]["costThisSessionUsd"])
        finally:
            self._restore_env(previous)

    def test_placeholder_credit_proof_records_only_analyst_cost_once_per_workflow(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0.02", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
        try:
            runtime = create_runtime()
            state = runtime.start_paper_self_training()
            workflow_id = state["workflowRuntimeMonitor"]["activeWorkflow"]["workflowIdentifier"]
            runtime.halt_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: any(
                    workflow["workflowIdentifier"] == workflow_id and workflow["status"] == "Archived"
                    for workflow in item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]
                ) and len(item["performanceTruthEngine"]["orderLedger"]) == 0
                and item["performanceTruthEngine"]["integrity"]["proofModeTruthAttempts"] == 1,
                timeout=10.0,
            )
            self.assertEqual(1, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
            self.assertEqual(0.001, state["apiRuntimeMonitor"]["costThisSessionUsd"])
            office_totals = state["apiRuntimeMonitor"]["officeCostTotalsUsd"]
            self.assertEqual(0.001, office_totals["Analyst"])
            for office, amount in office_totals.items():
                if office != "Analyst":
                    self.assertEqual(0.0, amount, office)
            call = state["apiRuntimeMonitor"]["recentApiCalls"][0]
            self.assertEqual("Analyst", call["office"])
            self.assertEqual(workflow_id, call["workflow_id"])
            self.assertTrue(call["workflow_token_id"])
            self.assertEqual("workflow-token-authorized dry-run API usage", call["usage_classification"])
            self.assertEqual("dry_run", call["execution_mode"])
            self.assertEqual("VALID", state["workflowRuntimeMonitor"]["tokenIntegrity"]["status"])
            self.assertEqual(0, state["workflowOrchestrator"]["metrics"]["tokenExclusivityViolations"])
            self.assertEqual(0, state["workflowOrchestrator"]["metrics"]["nonDormantAfterTransferViolations"])
            self.assertEqual(0, len(state["performanceTruthEngine"]["tradeLedger"]))
            self.assertEqual(0, len(state["performanceTruthEngine"]["positionLedger"]))
            self.assertIn("PROOF_MODE_NOT_ACTIONABLE", state["performanceTruthEngine"]["rejectedTruthRecords"][0]["rejectionCodes"])
        finally:
            self._restore_env(previous)

    def test_real_api_pilot_disabled_by_default_keeps_analyst_on_dry_run(self) -> None:
        previous = self._with_env(ARGOS_ENABLE_REAL_API_PILOT=None, ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
        try:
            runtime = create_runtime()
            state = runtime.start_paper_self_training()
            workflow_id = state["workflowRuntimeMonitor"]["activeWorkflow"]["workflowIdentifier"] if state["workflowRuntimeMonitor"]["activeWorkflow"] else state["workflowOrchestrator"]["workflows"][-1]["workflow_id"]
            state = self._wait_for_state(
                runtime,
                lambda item: any(workflow["workflowIdentifier"] == workflow_id and workflow["status"] == "Archived" for workflow in item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            self.assertFalse(state["apiExecutionGateway"]["directProviderCallsEnabled"])
            self.assertEqual(1, state["apiExecutionGateway"]["metrics"]["dryRunCount"])
            self.assertEqual(0, state["apiExecutionGateway"]["metrics"]["realApiPilotCount"])
            call = state["apiRuntimeMonitor"]["recentApiCalls"][0]
            self.assertEqual("dry_run", call["execution_mode"])
            self.assertEqual("none", call["provider"])
            self.assertEqual("workflow-token-authorized dry-run API usage", call["usage_classification"])
        finally:
            self._restore_env(previous)

    def test_real_api_pilot_scope_law_vii_and_budget_guards(self) -> None:
        previous = self._with_env(ARGOS_ENABLE_REAL_API_PILOT="true", ARGOS_REAL_API_MODEL="gpt-4.1-mini", ARGOS_REAL_API_FALLBACK_TO_DRY_RUN="false")
        try:
            runtime = create_runtime()
            runtime.api_execution_gateway.set_provider_call_for_testing(lambda _request, _prompt: self._valid_analyst_json())

            seeker_workflow_id, seeker_token_id, _owner = self._executing_paper_workflow_scope(runtime, stages=("Seeker",))
            seeker = runtime.api_execution_gateway.execute_model_request(self._real_gateway_request(seeker_workflow_id, seeker_token_id, office="Seeker", fallback=False))
            self.assertEqual("REAL_API_PILOT_SCOPE_VIOLATION", seeker.violation_code)

            risk_workflow_id, risk_token_id, _owner = self._executing_paper_workflow_scope(runtime, stages=("Risk",))
            risk = runtime.api_execution_gateway.execute_model_request(self._real_gateway_request(risk_workflow_id, risk_token_id, office="Risk", fallback=False))
            self.assertEqual("REAL_API_PILOT_SCOPE_VIOLATION", risk.violation_code)

            trader_workflow_id, trader_token_id, _owner = self._executing_paper_workflow_scope(runtime, stages=("Trader",))
            trader = runtime.api_execution_gateway.execute_model_request(self._real_gateway_request(trader_workflow_id, trader_token_id, office="Trader", fallback=False))
            self.assertEqual("REAL_API_PILOT_SCOPE_VIOLATION", trader.violation_code)

            historian_workflow_id, historian_token_id, _owner = self._executing_paper_workflow_scope(runtime, stages=("Historian",))
            historian = runtime.api_execution_gateway.execute_model_request(self._real_gateway_request(historian_workflow_id, historian_token_id, office="Historian", fallback=False))
            self.assertEqual("REAL_API_PILOT_SCOPE_VIOLATION", historian.violation_code)

            workflow_id, token_id, _owner = self._executing_paper_workflow_scope(runtime, stages=("Risk", "Analyst"))
            non_owner = runtime.api_execution_gateway.execute_model_request(self._real_gateway_request(workflow_id, token_id, office="Analyst", fallback=False))
            self.assertEqual("LAW_VII_VIOLATION_NON_OWNER_API_REQUEST", non_owner.violation_code)

            analyst_workflow_id, analyst_token_id, _owner = self._executing_paper_workflow_scope(runtime, stages=("Analyst",))
            missing_workflow = runtime.api_execution_gateway.execute_model_request(self._real_gateway_request("", analyst_token_id, fallback=False))
            missing_token = runtime.api_execution_gateway.execute_model_request(self._real_gateway_request(analyst_workflow_id, "", fallback=False))
            budget = runtime.api_execution_gateway.execute_model_request(self._real_gateway_request(analyst_workflow_id, analyst_token_id, cost=0.002, fallback=False))
            self.assertEqual("LAW_VII_VIOLATION_UNSCOPED_API_REQUEST", missing_workflow.violation_code)
            self.assertEqual("LAW_VII_VIOLATION_UNSCOPED_API_REQUEST", missing_token.violation_code)
            self.assertEqual("REAL_API_PILOT_BUDGET_BLOCKED", budget.violation_code)

            assigned = runtime.workflow_orchestrator.create_validate_queue_assign(
                name="Assigned Real Pilot",
                stages=("Analyst",),
                runtime_budget=100,
                credit_budget=0.01,
                expected_output_schema=("summary", "evidence", "audit_identifier", "workflow_type", "workflow_stage", "initial_stage"),
                workflow_type="paper_trading_session",
                initial_stage="market_preparation",
            )
            not_executing = runtime.api_execution_gateway.execute_model_request(self._real_gateway_request(assigned.workflow_id, assigned.token.audit_identifier, fallback=False))
            self.assertEqual("LAW_VII_VIOLATION_WORKFLOW_NOT_EXECUTING", not_executing.violation_code)

            state = runtime.state()
            self.assertEqual(0, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
        finally:
            self._restore_env(previous)

    def test_real_api_pilot_success_updates_runtime_and_decision_source(self) -> None:
        previous = self._with_env(
            ARGOS_ENABLE_REAL_API_PILOT="true",
            ARGOS_REAL_API_MODEL="gpt-4.1-mini",
            ARGOS_REAL_API_FALLBACK_TO_DRY_RUN="false",
            ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0",
            ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5",
            ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true",
        )
        try:
            runtime = create_runtime()
            runtime.api_execution_gateway.set_provider_call_for_testing(lambda _request, _prompt: self._valid_analyst_json())
            state = runtime.start_paper_self_training()
            workflow_id = state["workflowRuntimeMonitor"]["activeWorkflow"]["workflowIdentifier"] if state["workflowRuntimeMonitor"]["activeWorkflow"] else state["workflowOrchestrator"]["workflows"][-1]["workflow_id"]
            state = self._wait_for_state(
                runtime,
                lambda item: any(workflow["workflowIdentifier"] == workflow_id and workflow["status"] == "Archived" for workflow in item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            self.assertTrue(state["apiExecutionGateway"]["directProviderCallsEnabled"])
            self.assertEqual(1, state["apiExecutionGateway"]["metrics"]["realApiPilotCount"])
            self.assertEqual(0, state["apiExecutionGateway"]["metrics"]["fallbackCount"])
            self.assertEqual(1, state["apiRuntimeMonitor"]["metrics"]["realApiCallsLogged"])
            self.assertEqual(0, state["apiRuntimeMonitor"]["metrics"]["dryRunApiCallsLogged"])
            self.assertEqual(0.001, state["apiRuntimeMonitor"]["officeCostTotalsUsd"]["Analyst"])
            cost = state["enterpriseCostGovernor"]
            self.assertEqual(1, len(cost["missionReservations"]))
            self.assertEqual(1, len(cost["usageRecords"]))
            self.assertEqual("consumed", cost["missionReservations"][0]["state"])
            self.assertEqual("openai", cost["usageRecords"][0]["provider"])
            self.assertTrue(all(value == 0.0 for office, value in state["apiRuntimeMonitor"]["officeCostTotalsUsd"].items() if office != "Analyst"))
            call = state["apiRuntimeMonitor"]["recentApiCalls"][0]
            self.assertEqual("real_api_pilot", call["execution_mode"])
            self.assertEqual("real API usage", call["usage_classification"])
            workflow = next(item for item in state["workflowOrchestrator"]["workflows"] if item["workflow_id"] == workflow_id)
            analyst_output = workflow["output_history"][1]
            decision = analyst_output["decision_object"]
            self.assertEqual("real_api_pilot", decision["revisionSource"])
            self.assertEqual("BUY", decision["recommendation"])
            self.assertEqual("real_api_pilot", decision["apiExecutionMode"])
            baton = next(item for item in state["workflowRuntimeMonitor"]["workflowBatonView"] if item["workflowIdentifier"] == workflow_id)
            analyst_stage = next(item for item in baton["stages"] if item["office"] == "Analyst")
            self.assertTrue(analyst_stage["realApiPilot"])
            self.assertEqual("VALID", state["workflowRuntimeMonitor"]["tokenIntegrity"]["status"])
        finally:
            self._restore_env(previous)

    def test_real_api_pilot_invalid_json_fallback_and_blocked_modes(self) -> None:
        previous = self._with_env(ARGOS_ENABLE_REAL_API_PILOT="true", ARGOS_REAL_API_MODEL="gpt-4.1-mini", ARGOS_REAL_API_FALLBACK_TO_DRY_RUN="true")
        try:
            runtime = create_runtime()
            runtime.api_execution_gateway.set_provider_call_for_testing(lambda _request, _prompt: "not-json")
            workflow_id, token_id, _owner = self._executing_paper_workflow_scope(runtime, stages=("Analyst",))
            fallback = runtime.api_execution_gateway.execute_model_request(self._real_gateway_request(workflow_id, token_id, fallback=True))
            self.assertTrue(fallback.allowed)
            self.assertTrue(fallback.fallback_used)
            self.assertEqual("MALFORMED_JSON", fallback.validation_status)
            self.assertEqual("FALLBACK_DRY_RUN_COMPLETED", fallback.execution_status)
        finally:
            self._restore_env(previous)

    def test_prompt_contract_framework_is_visible_and_templates_are_versioned(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        contract = state["promptContract"]

        self.assertEqual("OE-011F", contract["engineeringOrder"])
        self.assertEqual("OE-011F-1.0.0", contract["contractVersion"])
        self.assertEqual(0.2, contract["defaultTemperature"])
        self.assertTrue(contract["providerIndependent"])
        self.assertEqual({"Seeker", "Analyst", "Risk", "Trader", "Historian"}, {item["office"] for item in contract["templates"]})
        analyst = next(item for item in contract["templates"] if item["office"] == "Analyst")
        self.assertTrue(analyst["immutable"])
        self.assertEqual("1.0.0", analyst["prompt_version"])
        self.assertIn("confidence_reason", analyst["output_schema"])
        self.assertIn("workflow_id", contract["requiredEnvelopeFields"])
        self.assertIn("Decision Object validation", contract["validationPipeline"])

    def test_gateway_blocks_ai_execution_without_prompt_contract(self) -> None:
        runtime = create_runtime()
        workflow_id, token_id, _owner = self._executing_workflow_scope(runtime, stages=("Analyst",), credit_budget=0.5)
        request = self._gateway_request(workflow_id, token_id)
        request.prompt_contract_envelope.clear()

        response = runtime.api_execution_gateway.execute_model_request(request)

        self.assertTrue(response.blocked)
        self.assertEqual("PROMPT_CONTRACT_MISSING", response.violation_code)
        state = runtime.state()
        self.assertEqual(0, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])

    def test_gateway_blocks_wrong_office_schema_before_credit_accounting(self) -> None:
        runtime = create_runtime()
        workflow_id, token_id, _owner = self._executing_workflow_scope(runtime, stages=("Analyst",), credit_budget=0.5)
        request = self._gateway_request(workflow_id, token_id)
        request.prompt_contract_envelope["output_schema"] = OFFICE_OUTPUT_SCHEMAS["Seeker"]

        response = runtime.api_execution_gateway.execute_model_request(request)

        self.assertTrue(response.blocked)
        self.assertEqual("PROMPT_CONTRACT_SCHEMA_MISMATCH", response.violation_code)
        state = runtime.state()
        self.assertEqual(0, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])

    def test_prompt_versions_are_preserved_in_workflow_and_decision_laboratory_replay(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
        try:
            runtime = create_runtime()
            state = runtime.start_paper_self_training()
            workflow_id = state["workflowRuntimeMonitor"]["activeWorkflow"]["workflowIdentifier"] if state["workflowRuntimeMonitor"]["activeWorkflow"] else state["workflowOrchestrator"]["workflows"][-1]["workflow_id"]
            state = self._wait_for_state(
                runtime,
                lambda item: any(workflow["workflowIdentifier"] == workflow_id and workflow["status"] == "Archived" for workflow in item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            workflow = next(item for item in state["workflowOrchestrator"]["workflows"] if item["workflow_id"] == workflow_id)
            self.assertEqual(5, len(workflow["output_history"]))
            for output in workflow["output_history"]:
                self.assertIn("prompt_contract", output)
                self.assertTrue(output["prompt_contract"]["promptVersion"])
                self.assertTrue(output["prompt_contract"]["promptTemplateId"])
                self.assertTrue(output["prompt_contract"]["schemaVersion"])
                self.assertTrue(output["prompt_contract"]["replayable"])

            lab = state["decisionLaboratory"]
            replay = next(item for item in lab["workflowReplay"] if item["workflowId"] == workflow_id)
            self.assertEqual(5, len(replay["promptVersions"]))
            self.assertEqual(("Seeker", "Analyst", "Risk", "Trader", "Historian"), tuple(item["office"] for item in replay["promptVersions"]))
            comparison = next(item for item in lab["promptRevisionComparisons"] if item["workflowId"] == workflow_id)
            self.assertTrue(comparison["allPromptVersionsPreserved"])
            self.assertTrue(comparison["allSchemaVersionsPreserved"])
            self.assertEqual("READY_FOR_HISTORIAN_REVIEW", comparison["historianComparisonStatus"])
            analyst_revision = next(item for item in lab["decisionObjectReplay"] if item["workflowId"] == workflow_id)["revisions"][1]
            self.assertEqual("PROMPT-CONTRACT-ANALYST-1.0.0", analyst_revision["promptTemplateId"])
        finally:
            self._restore_env(previous)

        previous = self._with_env(ARGOS_ENABLE_REAL_API_PILOT="true", ARGOS_REAL_API_MODEL="gpt-4.1-mini", ARGOS_REAL_API_FALLBACK_TO_DRY_RUN="false")
        try:
            runtime = create_runtime()
            runtime.api_execution_gateway.set_provider_call_for_testing(lambda _request, _prompt: json.dumps({"recommendation": "BUY"}))
            workflow_id, token_id, _owner = self._executing_paper_workflow_scope(runtime, stages=("Analyst",))
            blocked = runtime.api_execution_gateway.execute_model_request(self._real_gateway_request(workflow_id, token_id, fallback=False))
            self.assertTrue(blocked.blocked)
            self.assertEqual("REAL_API_PILOT_SCHEMA_INVALID", blocked.violation_code)
            self.assertEqual("SCHEMA_INVALID", blocked.validation_status)
        finally:
            self._restore_env(previous)

    def test_controlled_cognitive_pilot_completes_bounded_real_analyst_workflows(self) -> None:
        previous = self._with_env(
            ARGOS_ENABLE_REAL_API_PILOT="true",
            ARGOS_ENABLE_CONTROLLED_COGNITIVE_PILOT="true",
            ARGOS_COGNITIVE_PILOT_MAX_WORKFLOWS="3",
            ARGOS_COGNITIVE_PILOT_MAX_TOTAL_COST_USD="0.05",
            ARGOS_COGNITIVE_PILOT_MAX_WORKFLOW_COST_USD="0.005",
            ARGOS_REAL_API_MODEL="gpt-4.1-mini",
            ARGOS_REAL_API_FALLBACK_TO_DRY_RUN="false",
            ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0",
            ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05",
            ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true",
            ARGOS_BROKER_SIM_MARKET_SESSION="CLOSED",
        )
        try:
            runtime = create_runtime()
            runtime.api_execution_gateway.set_provider_call_for_testing(lambda _request, _prompt: self._valid_analyst_json())
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: item["controlledCognitivePilot"]["status"] == "COMPLETE"
                and item["workflowOrchestrator"]["metrics"]["activeWorkflowCount"] == 0
                and len(item["performanceTruthEngine"]["orderLedger"]) == 3,
                timeout=3.0,
            )

            pilot = state["controlledCognitivePilot"]
            self.assertTrue(pilot["enabled"])
            self.assertTrue(pilot["success"])
            self.assertEqual("COMPLETE", pilot["status"])
            self.assertEqual(3, pilot["report"]["completed"])
            self.assertEqual(3, state["apiRuntimeMonitor"]["metrics"]["realApiCallsLogged"])
            self.assertEqual(0, state["apiRuntimeMonitor"]["metrics"]["dryRunApiCallsLogged"])
            self.assertEqual(3, state["apiExecutionGateway"]["metrics"]["realApiPilotCount"])
            self.assertLessEqual(pilot["report"]["budgetUsed"], 0.05)
            self.assertTrue(all(item["realApiCalls"] == 1 for item in pilot["realApiCallsByWorkflow"]))
            self.assertEqual(3, len(pilot["realApiCallsByWorkflow"]))
            self.assertEqual("VALID", state["workflowRuntimeMonitor"]["tokenIntegrity"]["status"])
            totals = state["apiRuntimeMonitor"]["officeCostTotalsUsd"]
            self.assertEqual(0.003, totals["Analyst"])
            self.assertTrue(all(value == 0.0 for office, value in totals.items() if office != "Analyst"))
            completed = [workflow for workflow in state["workflowOrchestrator"]["workflows"] if workflow["token"]["workflow_status"] == "Archived"]
            self.assertEqual(3, len(completed))
            for workflow in completed:
                analyst = workflow["output_history"][1]["decision_object"]
                self.assertEqual("real_api_pilot", analyst["revisionSource"])
                self.assertEqual("PROMPT-CONTRACT-ANALYST-1.0.0", analyst["promptContract"]["promptTemplateId"])
            self.assertEqual(3, len(state["performanceTruthEngine"]["orderLedger"]))
            self.assertGreaterEqual(state["decisionLaboratory"]["metrics"]["decisionReplayCount"], 3)
        finally:
            runtime.halt_paper_self_training()
            self._restore_env(previous)

    def test_live_strategy_performance_console_tracks_performance_and_decision_evolution(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.deposit_user_funds(10000.0)
            state = runtime.start_paper_self_training()
            workflow_id = state["workflowRuntimeMonitor"]["activeWorkflow"]["workflowIdentifier"] if state["workflowRuntimeMonitor"]["activeWorkflow"] else state["workflowOrchestrator"]["workflows"][-1]["workflow_id"]
            state = self._wait_for_state(
                runtime,
                lambda item: any(
                    workflow["workflowIdentifier"] == workflow_id and workflow["status"] == "Archived"
                    for workflow in item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]
                ) and len(item["performanceTruthEngine"]["orderLedger"]) == 1
                and item["strategyPerformanceConsole"]["trace"]["performanceSource"] == "PERFORMANCE_TRUTH_ENGINE"
                and item["strategyPerformanceConsole"]["decisionObjectPanel"]["currentRevision"] == 5,
                timeout=10.0,
            )
            runtime.halt_paper_self_training()

            console = state["strategyPerformanceConsole"]
            portfolio = console["livePortfolioPanel"]
            self.assertEqual("Live Strategy Performance Console", console["consoleName"])
            self.assertEqual("OE-011B", console["engineeringOrder"])
            self.assertIn("Is ARGOS making money?", console["answers"])
            self.assertGreater(portfolio["portfolioValue"], 0)
            self.assertIn("sharpeRatio", portfolio)
            self.assertIn("expectancy", portfolio)
            self.assertEqual({"SPY", "QQQ", "DIA", "IWM", "USER_SELECTED"}, {item["benchmark"] for item in console["marketBenchmarks"]})
            self.assertTrue(all("alpha" in item and "trackingDifference" in item for item in console["marketBenchmarks"]))
            self.assertGreaterEqual(len(console["currentPositions"]), 1)
            first_position = console["currentPositions"][0]
            self.assertIn("riskRating", first_position)
            self.assertIn("decisionObjectId", first_position)
            self.assertGreaterEqual(len(console["tradeStream"]), 0)
            self.assertEqual(1, len(state["performanceTruthEngine"]["orderLedger"]))
            self.assertTrue(console["decisionObjectPanel"]["decisionObjectId"].startswith("DO-"))
            self.assertEqual(5, console["decisionObjectPanel"]["currentRevision"])
            evolution = next(item for item in console["decisionObjectEvolution"] if item["workflowId"] == workflow_id)
            self.assertEqual(5, evolution["revisionCount"])
            self.assertEqual(("Seeker", "Analyst", "Risk", "Trader", "Historian"), tuple(revision["office"] for revision in evolution["revisions"]))
            self.assertTrue(all(revision["immutable"] for revision in evolution["revisions"]))
            workflow_contribution = next(item for item in console["workflowContribution"] if item["workflow"] == workflow_id)
            self.assertEqual(1, workflow_contribution["tradesGenerated"])
            self.assertEqual(5, len(console["officeContribution"]))
            analyst = next(item for item in console["officeContribution"] if item["office"] == "Analyst")
            self.assertEqual(1, analyst["structuredOutputsProduced"])
            self.assertGreaterEqual(len(console["strategyLeaderboard"]), 1)
            self.assertGreaterEqual(len(console["liveEquityCurve"]), 1)
            self.assertGreaterEqual(len(console["performanceAlerts"]), 1)
            scorecard = console["enterpriseScorecard"]
            self.assertIn("overallCommanderScore", scorecard)
            self.assertGreater(scorecard["overallCommanderScore"], 0)
            self.assertEqual("LAW_VII_ENFORCED", console["integration"]["workflowExecutionToken"])
            self.assertEqual(
                sum(len(item["revisions"]) for item in console["decisionObjectEvolution"]),
                console["trace"]["immutableRevisionCount"],
            )
        finally:
            runtime.halt_paper_self_training()
            self._restore_env(previous)

    def test_live_strategy_performance_console_ui_and_endpoint_are_exposed(self) -> None:
        runtime = create_runtime()
        state = runtime.strategy_performance_state()
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        self.assertIn("strategyPerformanceConsole", state)
        self.assertIn("Live Strategy Performance Console", html)
        self.assertIn("spc-equity-chart", html)
        self.assertIn("renderStrategyPerformanceConsole", js)
        self.assertIn("drawStrategyEquityCurve", js)
        self.assertIn("/api/strategy-performance/state", server)

    def test_performance_truth_engine_records_immutable_ledgers_and_drives_dashboard_metrics(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="CLOSED")
        try:
            runtime = create_runtime()
            state = runtime.start_paper_self_training()
            workflow_id = state["workflowRuntimeMonitor"]["activeWorkflow"]["workflowIdentifier"] if state["workflowRuntimeMonitor"]["activeWorkflow"] else state["workflowOrchestrator"]["workflows"][-1]["workflow_id"]
            state = self._wait_for_state(
                runtime,
                lambda item: any(
                    workflow["workflowIdentifier"] == workflow_id and workflow["status"] == "Archived"
                    for workflow in item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]
                ) and len(item["performanceTruthEngine"]["orderLedger"]) == 1
                and item["strategyPerformanceConsole"]["trace"]["performanceSource"] == "PERFORMANCE_TRUTH_ENGINE",
                timeout=10.0,
            )
            runtime.halt_paper_self_training()

            truth = state["performanceTruthEngine"]
            self.assertEqual("Performance Truth Engine", truth["engineName"])
            self.assertEqual("OE-011C", truth["engineeringOrder"])
            self.assertEqual("IMMUTABLE_LEDGER", truth["sourceOfTruth"])
            self.assertEqual(1, len(truth["orderLedger"]))
            self.assertEqual(0, len(truth["tradeLedger"]))
            self.assertEqual(0, len(truth["positionLedger"]))
            self.assertEqual(1, len(truth["portfolioLedger"]))
            self.assertEqual(1, len(truth["decisionObjectOutcomes"]))
            self.assertEqual(1, len(truth["workflowAttribution"]))
            self.assertEqual(5, len(truth["officeAttribution"]))
            self.assertEqual(5, len(truth["benchmarkHistory"]))
            order = truth["orderLedger"][0]
            self.assertEqual(workflow_id, order["workflow_id"])
            self.assertEqual("paper", order["execution_environment"])
            self.assertEqual("QUEUED", order["status"])
            self.assertEqual("MARKET_CLOSED", order["queued_reason"])
            self.assertEqual(0.0, order["filled_quantity"])
            self.assertTrue(order["hash"])
            self.assertEqual(0.0, truth["calculations"]["portfolio"]["portfolioValue"])
            self.assertEqual(1, truth["executionRealism"]["queuedOrders"])
            self.assertEqual(workflow_id, truth["workflowAttribution"][0]["workflow_id"])
            self.assertEqual(1, len({item["workflow_id"] for item in truth["workflowAttribution"]}))
            self.assertEqual(("Seeker", "Analyst", "Risk", "Trader", "Historian"), tuple(item["office"] for item in truth["officeAttribution"]))
            self.assertTrue(truth["integrity"]["immutable"])
            self.assertTrue(truth["integrity"]["appendOnly"])
            self.assertTrue(truth["integrity"]["uniqueWorkflowAttribution"])
            self.assertTrue(truth["integrity"]["paperLiveIsolated"])
            self.assertTrue(truth["integrity"]["hashesValid"])

            calculations = truth["calculations"]
            console = state["strategyPerformanceConsole"]
            self.assertEqual("PERFORMANCE_TRUTH_ENGINE", console["trace"]["performanceSource"])
            self.assertEqual(calculations["portfolio"]["portfolioValue"], console["livePortfolioPanel"]["portfolioValue"])
            self.assertEqual(calculations["portfolio"]["realizedPnl"], console["livePortfolioPanel"]["realizedPnl"])
            self.assertEqual(calculations["performance"]["profitFactor"], console["livePortfolioPanel"]["profitFactor"])
            self.assertEqual(tuple(calculations["benchmarks"]), tuple(console["marketBenchmarks"]))
            self.assertEqual(tuple(calculations["strategy"]), tuple(console["strategyLeaderboard"]))
            self.assertEqual(tuple(calculations["workflow"]), tuple(console["workflowContribution"]))
            self.assertEqual(tuple(calculations["office"]), tuple(console["officeContribution"]))
            self.assertEqual("PERFORMANCE_TRUTH_ENGINE", console["trace"]["performanceSource"])
            self.assertEqual(order["decision_object_id"], console["decisionObjectPanel"]["decisionObjectId"])
            self.assertEqual("LAW_VII_ENFORCED", console["integration"]["workflowExecutionToken"])
            self.assertEqual("PERFORMANCE_TRUTH_ENGINE", console["integration"]["oe011cPerformanceTruthEngine"])
        finally:
            self._restore_env(previous)

    def test_performance_truth_engine_isolates_paper_and_live_records_and_does_not_mutate_on_state_poll(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="CLOSED")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["performanceTruthEngine"]["orderLedger"]) == 1,
                timeout=5.0,
            )
            runtime.halt_paper_self_training()
            first_truth = state["performanceTruthEngine"]
            first_order_count = len(first_truth["orderLedger"])
            first_hashes = tuple(item["hash"] for item in first_truth["orderLedger"])

            for _ in range(5):
                state = runtime.performance_truth_state()

            truth = state["performanceTruthEngine"]
            self.assertEqual(first_order_count, len(truth["orderLedger"]))
            self.assertEqual(first_hashes, tuple(item["hash"] for item in truth["orderLedger"]))
            live_truth = runtime.performance_truth_engine.snapshot(execution_environment="live")
            self.assertEqual(0, len(live_truth["tradeLedger"]))
            self.assertEqual(0, len(live_truth["portfolioLedger"]))
            self.assertEqual("live", live_truth["executionEnvironment"])
        finally:
            runtime.halt_paper_self_training()
            self._restore_env(previous)

    def test_broker_realistic_paper_trading_rejects_open_market_orders_without_buying_power(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["performanceTruthEngine"]["orderLedger"]) == 1,
                timeout=5.0,
            )
            runtime.halt_paper_self_training()

            truth = state["performanceTruthEngine"]
            order = truth["orderLedger"][0]
            self.assertEqual("REGULAR", order["market_session"])
            self.assertEqual("REJECTED", order["status"])
            self.assertEqual("Buying Power", order["rejection_reason"])
            self.assertEqual(0.0, order["buying_power_before"])
            self.assertEqual(0.0, order["filled_quantity"])
            self.assertEqual(0, len(truth["positionLedger"]))
            self.assertEqual(0, len(truth["tradeLedger"]))
            self.assertEqual(1, truth["executionRealism"]["rejectedOrders"])
        finally:
            runtime.halt_paper_self_training()
            self._restore_env(previous)

    def test_broker_realistic_paper_trading_fills_only_with_deposited_cash_during_regular_session(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.deposit_user_funds(10000.0)
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["performanceTruthEngine"]["orderLedger"]) == 1,
                timeout=5.0,
            )
            runtime.halt_paper_self_training()

            truth = state["performanceTruthEngine"]
            order = truth["orderLedger"][0]
            self.assertEqual("FILLED", order["status"])
            self.assertGreater(order["filled_quantity"], 0)
            self.assertGreater(order["spread_cost"], 0)
            self.assertGreater(order["slippage"], 0)
            self.assertLess(order["buying_power_after"], order["buying_power_before"])
            self.assertEqual(1, len(truth["positionLedger"]))
            self.assertEqual(1, len(truth["tradeLedger"]))
            self.assertEqual(order["order_id"], truth["tradeLedger"][0]["entry_order_id"])
            self.assertEqual(order["filled_quantity"], truth["tradeLedger"][0]["quantity"])
            self.assertGreater(order["average_fill_price"], order["ask_price"])
            self.assertEqual(1, truth["executionRealism"]["filledOrders"])
            self.assertEqual(order["buying_power_after"], truth["paperAccount"]["buyingPower"])
            self.assertLessEqual(truth["portfolioLedger"][0]["total_return"], 0.0)
        finally:
            self._restore_env(previous)

    def test_broker_realistic_paper_trading_partial_fill_updates_only_filled_quantity(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR", ARGOS_BROKER_SIM_PARTIAL_FILL_RATIO="0.4")
        try:
            runtime = create_runtime()
            runtime.deposit_user_funds(10000.0)
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["performanceTruthEngine"]["orderLedger"]) == 1,
                timeout=10.0,
            )
            runtime.halt_paper_self_training()

            truth = state["performanceTruthEngine"]
            order = truth["orderLedger"][0]
            self.assertEqual("PARTIALLY_FILLED", order["status"])
            self.assertGreater(order["remaining_quantity"], 0)
            self.assertLess(order["filled_quantity"], order["requested_quantity"])
            self.assertEqual(order["filled_quantity"], truth["positionLedger"][0]["quantity"])
            self.assertEqual(1, len(truth["tradeLedger"]))
            self.assertEqual(1, truth["executionRealism"]["partialFills"])
        finally:
            self._restore_env(previous)

    def test_broker_realistic_paper_trading_sell_reduces_position_and_records_realized_pl(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.deposit_user_funds(10000.0)
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["performanceTruthEngine"]["orderLedger"]) == 1,
                timeout=10.0,
            )
            runtime.halt_paper_self_training()

            buy_order = state["performanceTruthEngine"]["orderLedger"][0]
            sell_order = runtime.performance_truth_engine.record_manual_paper_order(symbol=buy_order["symbol"], side="SELL", quantity=5)
            truth = runtime.performance_truth_engine.snapshot(execution_environment="paper")
            latest_position = truth["positionLedger"][0]
            sell_trade = truth["tradeLedger"][-1]

            self.assertEqual("SELL", sell_order["side"])
            self.assertEqual("FILLED", sell_order["status"])
            self.assertEqual(20.0, latest_position["quantity"])
            self.assertEqual(sell_order["order_id"], sell_trade["exit_order_id"])
            self.assertNotEqual(0.0, sell_trade["realized_profit_loss"])
            self.assertGreater(sell_order["buying_power_after"], sell_order["buying_power_before"])
        finally:
            self._restore_env(previous)

    def test_eo_xa_position_object_is_created_from_filled_buy_execution(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.deposit_user_funds(10000.0)
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["performanceTruthEngine"]["positionRegistry"]["activePositions"]) == 1,
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            registry = state["performanceTruthEngine"]["positionRegistry"]
            position = registry["activePositions"][0]
            order = state["performanceTruthEngine"]["orderLedger"][0]
            self.assertEqual("EO-XA", registry["engineeringOrder"])
            self.assertEqual(order["workflow_id"], position["workflow_id"])
            self.assertEqual(order["decision_object_id"], position["decision_object_id"])
            self.assertEqual(order["symbol"], position["symbol"])
            self.assertIn(position["lifecycle_status"], {"open", "monitoring", "exit_recommended"})
            self.assertGreater(position["quantity"], 0)
            self.assertTrue(position["monitoring_history"])
        finally:
            self._restore_env(previous)

    def test_eo_xa_position_registry_retrieves_and_updates_active_positions(self) -> None:
        from argos.control_panel.position_registry import PositionRegistry

        registry = PositionRegistry()
        order = {
            "order_id": "BRP-ORD-TEST",
            "workflow_id": "WF-EOXA",
            "decision_object_id": "DO-EOXA",
            "symbol": "AAPL",
            "asset_type": "STOCK",
            "side": "BUY",
            "status": "FILLED",
            "filled_quantity": 10.0,
            "average_fill_price": 100.0,
            "mid_price": 100.0,
            "timestamp": "2026-07-09T14:30:00Z",
        }
        decision = {"recommendation": "BUY", "stopLoss": 95.0, "targetPrice": 110.0, "riskScore": 0.31, "confidence": 0.72}

        position = registry.create_from_execution(order, decision)
        fetched = registry.position(position.position_id)
        by_workflow = registry.positions_by_workflow("WF-EOXA")
        by_decision = registry.positions_by_decision_object("DO-EOXA")
        updated = registry.update_market_price(position.position_id, 103.0, reason="deterministic mark")

        self.assertEqual(position.position_id, fetched.position_id)
        self.assertEqual(1, len(registry.active_positions()))
        self.assertEqual(position.position_id, by_workflow[0].position_id)
        self.assertEqual(position.position_id, by_decision[0].position_id)
        self.assertEqual(1030.0, updated.current_value)
        self.assertEqual(30.0, updated.unrealized_pnl)
        self.assertGreaterEqual(len(registry.snapshot()["positionHistory"]), 2)

    def test_eo_xa_position_registry_rejects_invalid_state_and_transitions(self) -> None:
        from argos.control_panel.position_registry import PositionLifecycleStatus, PositionObject, PositionRegistry

        registry = PositionRegistry()
        invalid = PositionObject(
            position_id="POS-BAD",
            workflow_id="WF-BAD",
            decision_object_id="DO-BAD",
            symbol="AAPL",
            asset_type="STOCK",
            side="LONG",
            lifecycle_status=PositionLifecycleStatus.OPEN.value,
            entry_thesis="test",
            entry_time="2026-07-09T14:30:00Z",
            entry_price=100.0,
            quantity=-1.0,
            average_cost=100.0,
            current_price=100.0,
            current_value=-100.0,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            stop_loss=95.0,
            profit_target=110.0,
            trailing_stop=0.0,
            time_in_trade="0m",
            current_risk=0.2,
            current_confidence=0.7,
            market_context={},
            monitoring_history=(),
            exit_conditions=(),
            exit_recommendation="",
            created_at="2026-07-09T14:30:00Z",
            updated_at="2026-07-09T14:30:00Z",
        )
        self.assertFalse(registry.validate(invalid).valid)

        good = registry.create_from_execution(
            {
                "order_id": "BRP-ORD-VALID",
                "workflow_id": "WF-GOOD",
                "decision_object_id": "DO-GOOD",
                "symbol": "MSFT",
                "asset_type": "STOCK",
                "side": "BUY",
                "status": "FILLED",
                "filled_quantity": 4.0,
                "average_fill_price": 50.0,
                "mid_price": 50.0,
                "timestamp": "2026-07-09T14:30:00Z",
            },
            {"recommendation": "BUY", "confidence": 0.7},
        )
        with self.assertRaises(ValueError):
            registry.archive_position(good.position_id)
        self.assertTrue(registry.snapshot()["auditEvents"])

    def test_eo_xa_position_registry_closes_position_with_zero_quantity(self) -> None:
        from argos.control_panel.position_registry import PositionRegistry

        registry = PositionRegistry()
        position = registry.create_from_execution(
            {
                "order_id": "BRP-ORD-CLOSE",
                "workflow_id": "WF-CLOSE",
                "decision_object_id": "DO-CLOSE",
                "symbol": "TLT",
                "asset_type": "ETF",
                "side": "BUY",
                "status": "FILLED",
                "filled_quantity": 3.0,
                "average_fill_price": 90.0,
                "mid_price": 90.0,
                "timestamp": "2026-07-09T14:30:00Z",
            },
            {"recommendation": "BUY"},
        )
        closed = registry.close_position(position.position_id, reason="unit test close")

        self.assertEqual("closed", closed.lifecycle_status)
        self.assertEqual(0.0, closed.quantity)
        self.assertEqual(0, len(registry.active_positions()))
        self.assertGreaterEqual(len(closed.monitoring_history), 2)

    def test_eo_xb_surveillance_engine_updates_active_position_from_market_data(self) -> None:
        from argos.control_panel.position_registry import PositionRegistry
        from argos.control_panel.position_surveillance_engine import PositionSurveillanceEngine

        registry = PositionRegistry()
        position = registry.create_from_execution(
            {
                "symbol": "SPY",
                "asset_type": "ETF",
                "side": "BUY",
                "filled_quantity": 10,
                "average_fill_price": 100.0,
                "mid_price": 100.0,
                "status": "FILLED",
                "workflow_id": "WF-EOXB",
                "decision_object_id": "DO-EOXB",
                "timestamp": "2026-07-09T14:00:00+00:00",
            },
            {"targetPrice": 110.0, "stopLoss": 95.0, "confidence": 0.7, "riskScore": 0.2},
        )
        provider = {
            "normalizedObjects": {
                "quotes": ({"symbol": "SPY", "bid": 104.99, "ask": 105.01, "last": 105.0, "volume": 1000, "volatility": 0.01},),
                "marketStatus": ({"status": "PAPER_OPEN"},),
            }
        }

        snapshot = PositionSurveillanceEngine().surveil(
            position_registry=registry,
            market_data_provider=provider,
            timestamp_utc="2026-07-09T14:10:00+00:00",
        )

        updated = registry.position(position.position_id)
        latest = snapshot["latestSnapshots"][0]
        self.assertEqual("EO-XB", snapshot["engineeringOrder"])
        self.assertEqual(105.0, updated.current_price)
        self.assertEqual(1050.0, updated.current_value)
        self.assertEqual(50.0, updated.unrealized_pnl)
        self.assertEqual("10m", updated.time_in_trade)
        self.assertEqual("monitoring", updated.lifecycle_status)
        self.assertEqual(position.position_id, latest["position_id"])
        self.assertEqual(105.0, latest["current_price"])
        self.assertEqual(5.0, latest["distance_to_target"])
        self.assertEqual(10.0, latest["distance_to_stop"])
        self.assertEqual("PositionSurveillanceEngine", registry.snapshot()["positionHistory"][-1]["source"])
        self.assertEqual(0, snapshot["diagnostics"]["aiCallsUsed"])

    def test_eo_xb_surveillance_degrades_without_market_data_and_does_not_mutate_position(self) -> None:
        from argos.control_panel.position_registry import PositionRegistry
        from argos.control_panel.position_surveillance_engine import PositionSurveillanceEngine

        registry = PositionRegistry()
        position = registry.create_from_execution(
            {
                "symbol": "QQQ",
                "asset_type": "ETF",
                "side": "BUY",
                "filled_quantity": 5,
                "average_fill_price": 200.0,
                "mid_price": 200.0,
                "status": "FILLED",
                "workflow_id": "WF-EOXB-MISSING",
                "decision_object_id": "DO-EOXB-MISSING",
            },
            {"targetPrice": 220.0, "stopLoss": 190.0},
        )
        history_count = len(registry.snapshot()["positionHistory"])

        snapshot = PositionSurveillanceEngine().surveil(
            position_registry=registry,
            market_data_provider={"normalizedObjects": {"quotes": (), "marketStatus": ({"status": "PAPER_OPEN"},)}},
            timestamp_utc="2026-07-09T14:10:00+00:00",
        )

        latest = snapshot["latestSnapshots"][0]
        unchanged = registry.position(position.position_id)
        self.assertEqual("DEGRADED", latest["surveillance_status"])
        self.assertEqual(("market_data_missing",), latest["detected_events"])
        self.assertTrue(latest["escalation_required"])
        self.assertEqual(history_count, len(registry.snapshot()["positionHistory"]))
        self.assertEqual(200.0, unchanged.current_price)

    def test_eo_xb_surveillance_detects_targets_stops_and_escalates_meaningful_events(self) -> None:
        from argos.control_panel.position_registry import PositionRegistry
        from argos.control_panel.position_surveillance_engine import PositionSurveillanceEngine

        registry = PositionRegistry()
        registry.create_from_execution(
            {
                "symbol": "SPY",
                "asset_type": "ETF",
                "side": "BUY",
                "filled_quantity": 10,
                "average_fill_price": 100.0,
                "mid_price": 100.0,
                "status": "FILLED",
                "workflow_id": "WF-EOXB-EVENTS",
                "decision_object_id": "DO-EOXB-EVENTS",
            },
            {"targetPrice": 105.0, "stopLoss": 96.0, "confidence": 0.7, "riskScore": 0.2},
        )
        provider = {
            "normalizedObjects": {
                "quotes": ({"symbol": "SPY", "bid": 105.49, "ask": 105.51, "last": 105.5, "volume": 1000, "volatility": 0.01},),
                "marketStatus": ({"status": "PAPER_OPEN"},),
            }
        }

        snapshot = PositionSurveillanceEngine().surveil(position_registry=registry, market_data_provider=provider, timestamp_utc="2026-07-09T14:10:00+00:00")

        latest = snapshot["latestSnapshots"][0]
        self.assertIn("profit_target_reached", latest["detected_events"])
        self.assertIn("unusual_unrealized_gain", latest["detected_events"])
        self.assertTrue(latest["escalation_required"])
        self.assertGreaterEqual(snapshot["metrics"]["latestEscalationCount"], 1)
        self.assertEqual("EO-XC Position Exit Evaluation Engine", snapshot["latestEscalations"][0]["recommended_next_engine"])

    def test_eo_xb_surveillance_snapshots_are_append_only(self) -> None:
        from argos.control_panel.position_registry import PositionRegistry
        from argos.control_panel.position_surveillance_engine import PositionSurveillanceEngine

        registry = PositionRegistry()
        registry.create_from_execution(
            {
                "symbol": "SPY",
                "asset_type": "ETF",
                "side": "BUY",
                "filled_quantity": 1,
                "average_fill_price": 100.0,
                "mid_price": 100.0,
                "status": "FILLED",
                "workflow_id": "WF-EOXB-APPEND",
                "decision_object_id": "DO-EOXB-APPEND",
            },
            {"targetPrice": 110.0, "stopLoss": 95.0},
        )
        engine = PositionSurveillanceEngine()
        first_provider = {"normalizedObjects": {"quotes": ({"symbol": "SPY", "bid": 100.99, "ask": 101.01, "last": 101.0},), "marketStatus": ({"status": "PAPER_OPEN"},)}}
        second_provider = {"normalizedObjects": {"quotes": ({"symbol": "SPY", "bid": 101.99, "ask": 102.01, "last": 102.0},), "marketStatus": ({"status": "PAPER_OPEN"},)}}

        first = engine.surveil(position_registry=registry, market_data_provider=first_provider, timestamp_utc="2026-07-09T14:10:00+00:00")
        first_snapshot = first["surveillanceSnapshots"][0]
        second = engine.surveil(position_registry=registry, market_data_provider=second_provider, timestamp_utc="2026-07-09T14:11:00+00:00")

        self.assertEqual(2, second["metrics"]["totalSnapshotCount"])
        self.assertEqual(first_snapshot, second["surveillanceSnapshots"][0])
        self.assertEqual(102.0, second["surveillanceSnapshots"][1]["current_price"])

    def test_eo_xb_runtime_exposes_position_surveillance_without_background_worker_or_ai(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.deposit_user_funds(10000.0)
            state = runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: item["workflowOrchestrator"]["metrics"]["workflowCount"] >= 1
                and item["performanceTruthEngine"]["integrity"]["proofModeTruthAttempts"] >= 1,
                timeout=10.0,
            )
            runtime.halt_paper_self_training()

            surveillance = state["positionSurveillanceEngine"]
            registry = state["performanceTruthEngine"]["positionRegistry"]
            self.assertEqual("EO-XB", surveillance["engineeringOrder"])
            self.assertFalse(surveillance["diagnostics"]["backgroundWorkerActive"])
            self.assertEqual(0, surveillance["lawVIII"]["routineAiCallsUsed"])
            self.assertTrue(surveillance["lawVII"]["mutatesPositionsThroughRegistryOnly"])
            self.assertTrue(surveillance["lawVII"]["readOnlyObservationModeAvailable"])
            self.assertFalse(surveillance["diagnostics"]["mutatedRegistryThisPass"])
            self.assertEqual(0, surveillance["metrics"]["totalSnapshotCount"])
            self.assertEqual(0, registry["metrics"]["historyRecordCount"])
            self.assertEqual(0, len(state["performanceTruthEngine"]["positionLedger"]))
        finally:
            runtime.halt_paper_self_training()
            self._restore_env(previous)

    def test_eo_xc_stop_loss_reached_produces_full_exit_and_registry_recommendation(self) -> None:
        from argos.control_panel.position_exit_decision_engine import ExitDecisionEngine
        from argos.control_panel.position_registry import PositionRegistry

        registry = PositionRegistry()
        position = registry.create_from_execution(
            {"symbol": "SPY", "asset_type": "ETF", "side": "BUY", "filled_quantity": 10, "average_fill_price": 100.0, "mid_price": 100.0, "status": "FILLED", "workflow_id": "WF-EOXC-STOP", "decision_object_id": "DO-EOXC-STOP"},
            {"targetPrice": 110.0, "stopLoss": 95.0, "confidence": 0.7, "riskScore": 0.2},
        )
        surveillance = {"latestSnapshots": (_exit_snapshot(position, current_price=94.5, events=("stop_loss_reached",)),), "latestEscalations": ()}

        state = ExitDecisionEngine().evaluate(position_registry=registry, position_surveillance=surveillance, timestamp_utc="2026-07-09T15:00:00Z")

        decision = state["latestDecisions"][0]
        updated = registry.position(position.position_id)
        self.assertEqual("EO-XC", state["engineeringOrder"])
        self.assertEqual("exit_full", decision["decision"])
        self.assertEqual("PREPARE_FULL_EXIT_ORDER", decision["recommended_action"])
        self.assertEqual(10.0, decision["recommended_quantity"])
        self.assertEqual("high", decision["urgency"])
        self.assertEqual("stop_loss_reached", decision["trigger_type"])
        self.assertEqual("exit_recommended", updated.lifecycle_status)
        self.assertEqual("ExitDecisionEngine", registry.snapshot()["positionHistory"][-1]["source"])

    def test_eo_xc_profit_target_can_produce_configured_partial_exit_quantity(self) -> None:
        from argos.control_panel.position_exit_decision_engine import ExitDecisionConfig, ExitDecisionEngine
        from argos.control_panel.position_registry import PositionRegistry

        registry = PositionRegistry()
        position = registry.create_from_execution(
            {"symbol": "SPY", "asset_type": "ETF", "side": "BUY", "filled_quantity": 20, "average_fill_price": 100.0, "mid_price": 100.0, "status": "FILLED", "workflow_id": "WF-EOXC-TARGET", "decision_object_id": "DO-EOXC-TARGET"},
            {"targetPrice": 105.0, "stopLoss": 95.0},
        )
        surveillance = {"latestSnapshots": (_exit_snapshot(position, current_price=106.0, events=("profit_target_reached",)),), "latestEscalations": ()}

        state = ExitDecisionEngine(ExitDecisionConfig(profit_target_behavior="exit_partial", partial_exit_percent=0.25)).evaluate(
            position_registry=registry,
            position_surveillance=surveillance,
            timestamp_utc="2026-07-09T15:00:00Z",
        )

        decision = state["latestDecisions"][0]
        self.assertEqual("exit_partial", decision["decision"])
        self.assertEqual(0.25, decision["recommended_percent"])
        self.assertEqual(5.0, decision["recommended_quantity"])
        self.assertEqual("STRAT-PROFIT-TARGET", decision["strategy_rule_id"])

    def test_eo_xc_trailing_stop_large_adverse_and_degraded_data_are_deterministic(self) -> None:
        from argos.control_panel.position_exit_decision_engine import ExitDecisionEngine
        from argos.control_panel.position_registry import PositionRegistry

        registry = PositionRegistry()
        trailing = registry.create_from_execution(
            {"symbol": "TLT", "asset_type": "ETF", "side": "BUY", "filled_quantity": 4, "average_fill_price": 100.0, "mid_price": 100.0, "status": "FILLED", "workflow_id": "WF-EOXC-TRAIL", "decision_object_id": "DO-EOXC-TRAIL"},
            {"targetPrice": 110.0, "stopLoss": 95.0},
        )
        large_loss = registry.create_from_execution(
            {"symbol": "GLD", "asset_type": "ETF", "side": "BUY", "filled_quantity": 4, "average_fill_price": 100.0, "mid_price": 100.0, "status": "FILLED", "workflow_id": "WF-EOXC-LOSS", "decision_object_id": "DO-EOXC-LOSS"},
            {"targetPrice": 110.0, "stopLoss": 90.0},
        )
        degraded = registry.create_from_execution(
            {"symbol": "MSFT", "asset_type": "STOCK", "side": "BUY", "filled_quantity": 4, "average_fill_price": 100.0, "mid_price": 100.0, "status": "FILLED", "workflow_id": "WF-EOXC-DEG", "decision_object_id": "DO-EOXC-DEG"},
            {"targetPrice": 110.0, "stopLoss": 90.0},
        )
        snapshots = (
            _exit_snapshot(trailing, current_price=96.0, events=("trailing_stop_reached",), trailing_stop=96.5),
            _exit_snapshot(large_loss, current_price=92.0, events=("large_adverse_move",)),
            _exit_snapshot(degraded, current_price=100.0, status="DEGRADED", events=("market_data_missing",)),
        )

        state = ExitDecisionEngine().evaluate(position_registry=registry, position_surveillance={"latestSnapshots": snapshots, "latestEscalations": ()}, timestamp_utc="2026-07-09T15:00:00Z")
        by_position = {item["position_id"]: item for item in state["latestDecisions"]}

        self.assertEqual("exit_full", by_position[trailing.position_id]["decision"])
        self.assertEqual("trailing_stop_reached", by_position[trailing.position_id]["trigger_type"])
        self.assertEqual("exit_full", by_position[large_loss.position_id]["decision"])
        self.assertEqual("large_adverse_move", by_position[large_loss.position_id]["trigger_type"])
        self.assertEqual("request_commander_review", by_position[degraded.position_id]["decision"])
        self.assertEqual("market_data_degraded", by_position[degraded.position_id]["trigger_type"])

    def test_eo_xc_hold_record_is_immutable_and_does_not_execute_orders_or_ai(self) -> None:
        from argos.control_panel.position_exit_decision_engine import ExitDecisionEngine
        from argos.control_panel.position_registry import PositionRegistry

        registry = PositionRegistry()
        position = registry.create_from_execution(
            {"symbol": "AAPL", "asset_type": "STOCK", "side": "BUY", "filled_quantity": 3, "average_fill_price": 100.0, "mid_price": 100.0, "status": "FILLED", "workflow_id": "WF-EOXC-HOLD", "decision_object_id": "DO-EOXC-HOLD"},
            {"targetPrice": 110.0, "stopLoss": 90.0},
        )
        engine = ExitDecisionEngine()
        surveillance = {"latestSnapshots": (_exit_snapshot(position, current_price=101.0, events=()),), "latestEscalations": ()}

        first = engine.evaluate(position_registry=registry, position_surveillance=surveillance, timestamp_utc="2026-07-09T15:00:00Z")
        first_record = first["exitDecisionRecords"][0]
        second = engine.evaluate(position_registry=registry, position_surveillance=surveillance, timestamp_utc="2026-07-09T15:01:00Z")

        self.assertEqual("hold", first["latestDecisions"][0]["decision"])
        self.assertEqual(first_record, second["exitDecisionRecords"][0])
        self.assertEqual(0, second["metrics"]["ordersExecuted"])
        self.assertEqual(0, second["diagnostics"]["aiCallsUsed"])
        self.assertEqual("monitoring" if registry.position(position.position_id).lifecycle_status == "monitoring" else "open", registry.position(position.position_id).lifecycle_status)

    def test_eo_xc_commander_override_and_emergency_risk_override_take_priority(self) -> None:
        from argos.control_panel.position_exit_decision_engine import ExitDecisionEngine
        from argos.control_panel.position_registry import PositionRegistry

        registry = PositionRegistry()
        commander = registry.create_from_execution(
            {"symbol": "SPY", "asset_type": "ETF", "side": "BUY", "filled_quantity": 8, "average_fill_price": 100.0, "mid_price": 100.0, "status": "FILLED", "workflow_id": "WF-EOXC-CMD", "decision_object_id": "DO-EOXC-CMD"},
            {"targetPrice": 110.0, "stopLoss": 90.0},
        )
        risk = registry.create_from_execution(
            {"symbol": "TLT", "asset_type": "ETF", "side": "BUY", "filled_quantity": 8, "average_fill_price": 100.0, "mid_price": 100.0, "status": "FILLED", "workflow_id": "WF-EOXC-RISK", "decision_object_id": "DO-EOXC-RISK"},
            {"targetPrice": 110.0, "stopLoss": 90.0},
        )
        snapshots = (_exit_snapshot(commander, current_price=100.0, events=()), _exit_snapshot(risk, current_price=100.0, events=()))

        commander_state = ExitDecisionEngine().evaluate(
            position_registry=registry,
            position_surveillance={"latestSnapshots": snapshots, "latestEscalations": ()},
            timestamp_utc="2026-07-09T15:00:00Z",
            commander_overrides=({"positionId": commander.position_id, "overrideId": "CMD-EXIT-1", "action": "exit_full"},),
        )
        risk_state = ExitDecisionEngine().evaluate(
            position_registry=registry,
            position_surveillance={"latestSnapshots": (_exit_snapshot(risk, current_price=100.0, events=()),), "latestEscalations": ()},
            timestamp_utc="2026-07-09T15:01:00Z",
            risk_context={"emergencyRiskOverride": True},
        )

        self.assertEqual("exit_full", commander_state["latestDecisions"][0]["decision"])
        self.assertEqual("CMD-EXIT-1", commander_state["latestDecisions"][0]["commander_override_id"])
        self.assertEqual("emergency_exit", risk_state["latestDecisions"][0]["decision"])
        self.assertEqual("RISK-EMERGENCY-OVERRIDE", risk_state["latestDecisions"][0]["risk_rule_id"])

    def test_eo_xc_strategy_invalidation_marks_ai_review_without_calling_ai(self) -> None:
        from argos.control_panel.position_exit_decision_engine import ExitDecisionEngine
        from argos.control_panel.position_registry import PositionRegistry

        registry = PositionRegistry()
        position = registry.create_from_execution(
            {"symbol": "QQQ", "asset_type": "ETF", "side": "BUY", "filled_quantity": 6, "average_fill_price": 100.0, "mid_price": 100.0, "status": "FILLED", "workflow_id": "WF-EOXC-AI", "decision_object_id": "DO-EOXC-AI"},
            {"targetPrice": 110.0, "stopLoss": 90.0, "marketContext": {"strategyInvalidation": True}},
        )

        state = ExitDecisionEngine().evaluate(
            position_registry=registry,
            position_surveillance={"latestSnapshots": (_exit_snapshot(position, current_price=100.0, events=()),), "latestEscalations": ()},
            timestamp_utc="2026-07-09T15:00:00Z",
        )

        decision = state["latestDecisions"][0]
        self.assertEqual("request_ai_review", decision["decision"])
        self.assertTrue(decision["ai_review_required"])
        self.assertIn("no AI call", decision["ai_review_reason"])
        self.assertEqual(0, state["lawVIII"]["routineAiCallsUsed"])

    def test_eo_xc_runtime_exposes_exit_decision_engine_without_broker_execution(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.deposit_user_funds(10000.0)
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["performanceTruthEngine"]["positionRegistry"]["activePositions"]) >= 1
                and item["positionExitDecisionEngine"]["metrics"]["latestDecisionCount"] >= 1,
                timeout=10.0,
            )
            runtime.halt_paper_self_training()

            exit_engine = state["positionExitDecisionEngine"]
            self.assertEqual("EO-XC", exit_engine["engineeringOrder"])
            self.assertFalse(exit_engine["diagnostics"]["backgroundWorkerActive"])
            self.assertEqual(0, exit_engine["metrics"]["ordersExecuted"])
            self.assertEqual(0, exit_engine["diagnostics"]["aiCallsUsed"])
            self.assertIn(exit_engine["latestDecisions"][0]["decision"], exit_engine["supportedDecisions"])
        finally:
            runtime.halt_paper_self_training()
            self._restore_env(previous)

    def test_eo_xe_closed_position_truth_is_created_for_fully_closed_position(self) -> None:
        from argos.control_panel.closed_position_truth import ClosedPositionTruthBuilder

        previous = self._with_env(ARGOS_BROKER_SIM_MARKET_SESSION="CLOSED")
        try:
            engine, buy, sell, surveillance, exit_decision, benchmark = _closed_truth_fixture()
            builder = ClosedPositionTruthBuilder()
            state = builder.build(
                position_registry=engine.position_registry.snapshot(),
                performance_truth=engine.snapshot(execution_environment="paper"),
                position_surveillance=surveillance,
                exit_decision_engine=exit_decision,
                enterprise_benchmark_engine=benchmark,
                trade_attribution_engine={},
                timestamp_utc="2026-07-09T16:00:00Z",
            )

            record = state["latestClosedPositionTruthRecords"][0]
            self.assertEqual("EO-XE", state["engineeringOrder"])
            self.assertEqual("POS-AAPL-DO-CPT", record["position_id"])
            self.assertEqual(buy["filled_quantity"], record["quantity_opened"])
            self.assertEqual(sell["filled_quantity"], record["quantity_closed"])
            self.assertEqual((buy["order_id"],), record["entry_execution_ids"])
            self.assertEqual((sell["order_id"],), record["exit_execution_ids"])
            self.assertEqual("EXD-CPT-001", record["exit_decision_id"])
            self.assertEqual("COMPLETE", record["benchmark_payload"]["status"])
            self.assertEqual("PREPARED", record["attribution_payload"]["status"])
            self.assertTrue(record["learning_payload"]["influenceFutureStrategyEvaluation"])
            self.assertTrue(record["hash"])
        finally:
            self._restore_env(previous)

    def test_eo_xe_builder_rejects_open_position_and_missing_exit_execution(self) -> None:
        from argos.control_panel.closed_position_truth import ClosedPositionTruthBuilder
        from argos.control_panel.performance_truth_engine import PerformanceTruthEngine

        previous = self._with_env(ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            engine = PerformanceTruthEngine(paper_starting_cash=10000.0)
            engine.record_manual_paper_order(symbol="AAPL", side="BUY", quantity=5, decision_object_id="DO-CPT-OPEN", workflow_id="WF-CPT-OPEN")
            builder = ClosedPositionTruthBuilder()
            open_state = builder.build(
                position_registry=engine.position_registry.snapshot(),
                performance_truth=engine.snapshot(execution_environment="paper"),
                position_surveillance={},
                exit_decision_engine={},
                timestamp_utc="2026-07-09T16:00:00Z",
            )
            position = engine.position_registry.position("POS-AAPL-DO-CPT-OPEN")
            engine.position_registry.close_position(position.position_id, reason="unit test forced close without sell")
            missing_exit_state = builder.build(
                position_registry=engine.position_registry.snapshot(),
                performance_truth=engine.snapshot(execution_environment="paper"),
                position_surveillance={},
                exit_decision_engine={},
                timestamp_utc="2026-07-09T16:01:00Z",
            )

            self.assertEqual(0, open_state["metrics"]["truthRecordCount"])
            self.assertTrue(any(item["eventType"] == "position_not_closed" for item in open_state["reconciliationEvents"]))
            self.assertEqual(0, missing_exit_state["metrics"]["truthRecordCount"])
            self.assertTrue(any(item["eventType"] == "missing_exit_execution" for item in missing_exit_state["reconciliationEvents"]))
        finally:
            self._restore_env(previous)

    def test_eo_xe_builder_is_idempotent_and_performance_truth_consumes_record(self) -> None:
        from argos.control_panel.closed_position_truth import ClosedPositionTruthBuilder

        previous = self._with_env(ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            engine, _buy, _sell, surveillance, exit_decision, benchmark = _closed_truth_fixture()
            builder = ClosedPositionTruthBuilder()
            first = builder.build(
                position_registry=engine.position_registry.snapshot(),
                performance_truth=engine.snapshot(execution_environment="paper"),
                position_surveillance=surveillance,
                exit_decision_engine=exit_decision,
                enterprise_benchmark_engine=benchmark,
                timestamp_utc="2026-07-09T16:00:00Z",
            )
            second = builder.build(
                position_registry=engine.position_registry.snapshot(),
                performance_truth=engine.snapshot(execution_environment="paper"),
                position_surveillance=surveillance,
                exit_decision_engine=exit_decision,
                enterprise_benchmark_engine=benchmark,
                timestamp_utc="2026-07-09T16:01:00Z",
            )
            engine.ingest_closed_position_truth(tuple(first["latestClosedPositionTruthRecords"]))
            engine.ingest_closed_position_truth(tuple(first["latestClosedPositionTruthRecords"]))
            truth = engine.snapshot(execution_environment="paper")

            self.assertEqual(1, first["metrics"]["truthRecordCount"])
            self.assertEqual(0, second["metrics"]["latestTruthRecordCount"])
            self.assertEqual(1, len(truth["closedPositionTruth"]))
            self.assertEqual(1, truth["closedLifecycleAnalytics"]["closedTruthRecordCount"])
        finally:
            self._restore_env(previous)

    def test_eo_xe_lifecycle_analytics_calculate_pnl_holding_period_and_surveillance_extremes(self) -> None:
        from argos.control_panel.closed_position_truth import ClosedPositionTruthBuilder

        previous = self._with_env(ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            engine, buy, sell, surveillance, exit_decision, benchmark = _closed_truth_fixture()
            state = ClosedPositionTruthBuilder().build(
                position_registry=engine.position_registry.snapshot(),
                performance_truth=engine.snapshot(execution_environment="paper"),
                position_surveillance=surveillance,
                exit_decision_engine=exit_decision,
                enterprise_benchmark_engine=benchmark,
                timestamp_utc="2026-07-09T16:00:00Z",
            )
            record = state["latestClosedPositionTruthRecords"][0]
            gross = round((sell["average_fill_price"] - buy["average_fill_price"]) * sell["filled_quantity"], 4)

            self.assertEqual(gross, record["gross_realized_pnl"])
            self.assertEqual(sell["realized_profit_loss"], record["net_realized_pnl"])
            self.assertTrue(record["holding_period"].endswith("m"))
            self.assertGreater(record["max_unrealized_gain"], 0)
            self.assertLess(record["max_unrealized_loss"], 0)
            self.assertLessEqual(record["max_drawdown_during_trade"], 0)
            self.assertGreater(record["execution_quality_score"], 0)
            self.assertEqual(2, record["surveillance_event_count"])
        finally:
            self._restore_env(previous)

    def test_eo_xe_missing_benchmark_creates_degraded_section_when_allowed(self) -> None:
        from argos.control_panel.closed_position_truth import ClosedPositionTruthBuilder

        previous = self._with_env(ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            engine, _buy, _sell, surveillance, exit_decision, _benchmark = _closed_truth_fixture()
            state = ClosedPositionTruthBuilder().build(
                position_registry=engine.position_registry.snapshot(),
                performance_truth=engine.snapshot(execution_environment="paper"),
                position_surveillance=surveillance,
                exit_decision_engine=exit_decision,
                enterprise_benchmark_engine={},
                timestamp_utc="2026-07-09T16:00:00Z",
            )
            record = state["latestClosedPositionTruthRecords"][0]
            self.assertEqual("DEGRADED", record["benchmark_payload"]["status"])
            self.assertIn("warning", record["benchmark_payload"])
        finally:
            self._restore_env(previous)

    def test_eo_xe_reconciliation_guards_quantity_and_pnl_mismatches(self) -> None:
        from argos.control_panel.closed_position_truth import ClosedPositionTruthBuilder

        previous = self._with_env(ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            engine, _buy, _sell, surveillance, exit_decision, benchmark = _closed_truth_fixture()
            truth = engine.snapshot(execution_environment="paper")
            orders = [dict(item) for item in truth["orderLedger"]]
            orders[-1]["filled_quantity"] = 4.0
            quantity_state = ClosedPositionTruthBuilder().build(
                position_registry=engine.position_registry.snapshot(),
                performance_truth=dict(truth, orderLedger=tuple(orders)),
                position_surveillance=surveillance,
                exit_decision_engine=exit_decision,
                enterprise_benchmark_engine=benchmark,
                timestamp_utc="2026-07-09T16:00:00Z",
            )
            orders = [dict(item) for item in truth["orderLedger"]]
            orders[-1]["realized_profit_loss"] = orders[-1]["realized_profit_loss"] + 99.0
            pnl_state = ClosedPositionTruthBuilder().build(
                position_registry=engine.position_registry.snapshot(),
                performance_truth=dict(truth, orderLedger=tuple(orders)),
                position_surveillance=surveillance,
                exit_decision_engine=exit_decision,
                enterprise_benchmark_engine=benchmark,
                timestamp_utc="2026-07-09T16:00:00Z",
            )

            self.assertTrue(any(item["eventType"] == "quantity_mismatch" for item in quantity_state["reconciliationEvents"]))
            self.assertTrue(any(item["eventType"] == "realized_pnl_mismatch" for item in pnl_state["reconciliationEvents"]))
            self.assertEqual(0, quantity_state["metrics"]["truthRecordCount"])
            self.assertEqual(0, pnl_state["metrics"]["truthRecordCount"])
        finally:
            self._restore_env(previous)

    def test_eo_xe_closed_positive_quantity_is_rejected_and_no_ai_is_used(self) -> None:
        from argos.control_panel.closed_position_truth import ClosedPositionTruthBuilder

        position = {
            "position_id": "POS-BAD-QTY",
            "workflow_id": "WF-BAD",
            "decision_object_id": "DO-BAD",
            "symbol": "AAPL",
            "asset_type": "STOCK",
            "side": "LONG",
            "quantity": 1.0,
            "lifecycle_status": "closed",
        }
        state = ClosedPositionTruthBuilder().build(
            position_registry={"allPositions": (position,)},
            performance_truth={"orderLedger": ()},
            position_surveillance={},
            exit_decision_engine={},
            timestamp_utc="2026-07-09T16:00:00Z",
        )

        self.assertTrue(any(item["eventType"] == "closed_position_has_quantity" for item in state["reconciliationEvents"]))
        self.assertEqual(0, state["diagnostics"]["aiCallsUsed"])
        self.assertFalse(state["diagnostics"]["backgroundWorkerActive"])

    def test_eo_xf_trader_bridge_payload_includes_summary_active_positions_and_distances(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.deposit_user_funds(10000.0)
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: item["traderCommandBridge"]["summary"]["total_open_positions"] >= 1
                and len(item["traderCommandBridge"]["active_positions"]) >= 1,
                timeout=10.0,
            )
            runtime.halt_paper_self_training()
            bridge = state["traderCommandBridge"]
            position = bridge["active_positions"][0]

            self.assertEqual("EO-XF", bridge["engineeringOrder"])
            self.assertIn("total_open_positions", bridge["summary"])
            self.assertIn("total_market_value", bridge["summary"])
            self.assertIn("profit_target", position)
            self.assertIn("stop_loss", position)
            self.assertIn("distance_to_target", position)
            self.assertIn("distance_to_stop", position)
            self.assertIn(position["health"], {"healthy", "target_approaching", "stop_approaching", "exit_recommended", "data_degraded", "emergency_risk_state"})
        finally:
            runtime.halt_paper_self_training()
            self._restore_env(previous)

    def test_eo_xf_trader_bridge_displays_exit_recommendations_orders_surveillance_and_realism(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.deposit_user_funds(10000.0)
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["traderCommandBridge"]["orders"]) >= 1
                and item["traderCommandBridge"]["surveillance_health"]["activePositionsSurveilled"] >= 1,
                timeout=5.0,
            )
            runtime.halt_paper_self_training()
            bridge = state["traderCommandBridge"]

            self.assertIn("exit_recommendations", bridge)
            self.assertIn("orders", bridge)
            self.assertIn("executions", bridge)
            self.assertIn("surveillance_health", bridge)
            self.assertIn("execution_realism_health", bridge)
            self.assertIn("rejected_order_count", bridge["execution_realism_health"])
            self.assertIn("partial_fill_count", bridge["execution_realism_health"])
            order = bridge["orders"][0]
            for key in ("status", "rejection_reason", "fill_price", "bid", "ask", "spread", "slippage", "cash_impact"):
                self.assertIn(key, order)
        finally:
            self._restore_env(previous)

    def test_eo_xf_trader_bridge_displays_closed_position_truth_and_exposure(self) -> None:
        previous = self._with_env(ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.performance_truth_engine.set_paper_account_cash(10000.0)
            buy = runtime.performance_truth_engine.record_manual_paper_order(symbol="AAPL", side="BUY", quantity=5, decision_object_id="DO-XF-CLOSED", workflow_id="WF-XF-CLOSED")
            runtime.performance_truth_engine.record_manual_paper_order(symbol="AAPL", side="SELL", quantity=5, decision_object_id=buy["decision_object_id"], workflow_id=buy["workflow_id"])
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["traderCommandBridge"]["closed_positions"]) >= 1,
                timeout=2.0,
            )
            bridge = state["traderCommandBridge"]
            closed = bridge["closed_positions"][0]

            self.assertIn("exposure", bridge)
            self.assertIn("cash_allocation", bridge["exposure"])
            self.assertIn("long_exposure", bridge["exposure"])
            self.assertIn("largest_position", bridge["exposure"])
            self.assertIn("realized_pnl", closed)
            self.assertIn("benchmark_return", closed)
            self.assertIn("alpha_vs_benchmark", closed)
            self.assertIn("execution_quality_score", closed)
            self.assertIn("learning_status", closed)
        finally:
            self._restore_env(previous)

    def test_eo_xf_position_detail_links_decision_snapshot_exit_decision_and_executions(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.deposit_user_funds(10000.0)
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["traderCommandBridge"]["position_details"]) >= 1,
                timeout=5.0,
            )
            runtime.halt_paper_self_training()
            detail = state["traderCommandBridge"]["position_details"][0]

            self.assertTrue(detail["linked_decision_object"])
            self.assertIn("entry_execution_record", detail)
            self.assertIn("latest_surveillance_snapshot", detail)
            self.assertIn("latest_exit_decision_record", detail)
            self.assertIn("execution_history", detail)
            self.assertIn("expected_next_step", detail)
        finally:
            self._restore_env(previous)

    def test_eo_xf_trader_bridge_is_display_only_and_ui_panels_exist(self) -> None:
        runtime = create_runtime()
        before = runtime.state()
        before_history = before["performanceTruthEngine"]["positionRegistry"]["metrics"]["historyRecordCount"]
        before_orders = len(before["performanceTruthEngine"]["orderLedger"])
        bridge = before["traderCommandBridge"]
        after = runtime.state()

        self.assertFalse(bridge["lawVII"]["mutatesLedgers"])
        self.assertFalse(bridge["lawVII"]["mutatesPositions"])
        self.assertEqual(0, bridge["lawVIII"]["routineAiCallsUsed"])
        self.assertEqual(before_history, after["performanceTruthEngine"]["positionRegistry"]["metrics"]["historyRecordCount"])
        self.assertEqual(before_orders, len(after["performanceTruthEngine"]["orderLedger"]))

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        self.assertIn("trader-active-positions", html)
        self.assertIn("trader-exit-recommendations", html)
        self.assertIn("trader-order-status", html)
        self.assertIn("trader-closed-truth", html)
        self.assertIn("traderCommandBridge", js)
        self.assertIn("/api/trader/cancel-pending-orders", js)

    def test_eo_y_reality_calibration_report_is_created_and_scores_are_normalized(self) -> None:
        engine = EnterpriseRealityCalibrationEngine()
        snapshot = engine.calibrate(
            timestamp_utc="2026-07-09T15:00:00Z",
            performance_truth={"orderLedger": (), "portfolioLedger": (), "positionLedger": (), "tradeLedger": (), "benchmarkHistory": (), "brokerProfile": {"marginPermissions": False}},
            market_data_provider={"normalizedObjects": {}},
            position_surveillance={"surveillanceSnapshots": ()},
            closed_position_truth={"closedPositionTruthRecords": ()},
            enterprise_benchmark_engine={},
            enterprise_learning_engine={},
            audit_event_count=4,
        )

        report = snapshot["latestCalibrationReport"]
        self.assertEqual("EO-Y", snapshot["engineeringOrder"])
        self.assertEqual("ERC-000001", report["calibration_report_id"])
        for key in (
            "market_data_fidelity_score",
            "execution_fidelity_score",
            "liquidity_fidelity_score",
            "valuation_fidelity_score",
            "benchmark_fidelity_score",
            "truth_reliability_score",
            "learning_reliability_score",
            "overall_reality_fidelity_score",
        ):
            self.assertGreaterEqual(report[key], 0.0)
            self.assertLessEqual(report[key], 100.0)
        self.assertLess(report["overall_reality_fidelity_score"], 100.0)
        self.assertTrue(snapshot["lawVII"]["calibrationPassTerminates"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])

    def test_eo_y_detects_execution_drift_and_degrades_learning_reliability(self) -> None:
        engine = EnterpriseRealityCalibrationEngine(RealityCalibrationConfig(degraded_learning_threshold=95.0, unsafe_learning_threshold=90.0, blocked_learning_threshold=20.0))
        bad_order = {
            "order_id": "ORD-BAD-001",
            "side": "BUY",
            "status": "FILLED",
            "bid_price": 99.0,
            "ask_price": 100.0,
            "average_fill_price": 104.0,
            "market_session": "CLOSED",
            "requested_quantity": 10,
            "available_volume": 100,
            "slippage": 0.5,
            "timestamp": "2026-07-09T15:00:00Z",
        }
        snapshot = engine.calibrate(
            timestamp_utc="2026-07-09T15:00:00Z",
            performance_truth={"orderLedger": (bad_order,), "portfolioLedger": (), "positionLedger": (), "tradeLedger": (), "benchmarkHistory": (), "brokerProfile": {"marginPermissions": False}},
            market_data_provider={"normalizedObjects": {"quotes": ()}},
            position_surveillance={"surveillanceSnapshots": ()},
            closed_position_truth={"closedPositionTruthRecords": ()},
            enterprise_benchmark_engine={},
            enterprise_learning_engine={},
        )

        drift_types = {item["drift_type"] for item in snapshot["latestCalibrationReport"]["detected_drift_events"]}
        self.assertIn("fill_outside_bid_ask_envelope", drift_types)
        self.assertIn("impossible_closed_market_fill", drift_types)
        self.assertIn(snapshot["learningReliabilityGate"]["state"], {"unsafe", "blocked"})
        self.assertTrue(snapshot["learningReliabilityGate"]["blockLearningPromotion"])

    def test_eo_y_detects_valuation_and_cash_drift(self) -> None:
        engine = EnterpriseRealityCalibrationEngine()
        valuation = {
            "audit_identifier": "PORT-BAD-001",
            "timestamp": "2026-07-09T15:00:00Z",
            "cash": -25.0,
            "market_value": 100.0,
            "total_equity": 1000.0,
        }
        snapshot = engine.calibrate(
            timestamp_utc="2026-07-09T15:00:00Z",
            performance_truth={"orderLedger": (), "portfolioLedger": (valuation,), "positionLedger": (), "tradeLedger": (), "benchmarkHistory": (), "brokerProfile": {"marginPermissions": False, "configuration": {"allowMargin": False}}},
            market_data_provider={"normalizedObjects": {"quotes": ()}},
            position_surveillance={"surveillanceSnapshots": ()},
            closed_position_truth={"closedPositionTruthRecords": ()},
            enterprise_benchmark_engine={},
            enterprise_learning_engine={},
        )

        drift_types = {item["drift_type"] for item in snapshot["latestCalibrationReport"]["detected_drift_events"]}
        self.assertIn("portfolio_value_without_accounting_support", drift_types)
        self.assertIn("negative_cash_without_margin", drift_types)
        self.assertGreaterEqual(snapshot["enterpriseHealthMetrics"]["valuationAnomalyCount"], 1)

    def test_eo_y_detects_truth_drift_for_missing_closed_position_evidence(self) -> None:
        engine = EnterpriseRealityCalibrationEngine()
        trade = {"trade_id": "TRD-NO-CPT", "timestamp": "2026-07-09T15:00:00Z"}
        closed_truth = {"closed_position_truth_id": "CPT-INCOMPLETE", "created_at": "2026-07-09T15:01:00Z", "surveillance_snapshot_ids": ()}
        snapshot = engine.calibrate(
            timestamp_utc="2026-07-09T15:02:00Z",
            performance_truth={"orderLedger": (), "portfolioLedger": (), "positionLedger": (), "tradeLedger": (trade,), "benchmarkHistory": (), "brokerProfile": {"marginPermissions": False}},
            market_data_provider={"normalizedObjects": {"quotes": ()}},
            position_surveillance={"surveillanceSnapshots": ()},
            closed_position_truth={"closedPositionTruthRecords": (closed_truth,)},
            enterprise_benchmark_engine={},
            enterprise_learning_engine={},
        )

        drift_types = {item["drift_type"] for item in snapshot["latestCalibrationReport"]["detected_drift_events"]}
        self.assertIn("closed_position_truth_without_exit_execution", drift_types)
        self.assertIn("closed_position_truth_without_surveillance_history", drift_types)
        self.assertGreaterEqual(snapshot["enterpriseHealthMetrics"]["degradedTruthCount"], 1)

    def test_eo_y_runtime_exposes_health_metrics_and_commander_summary(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        calibration = state["enterpriseRealityCalibrationEngine"]

        self.assertIn("latestCalibrationReport", calibration)
        self.assertIn("commanderSummary", calibration)
        self.assertIn("overallRealityFidelityScore", calibration["commanderSummary"])
        self.assertIn("realityCalibrationHealth", state["enterpriseHealthMonitor"])
        self.assertEqual(calibration["enterpriseHealthMetrics"], state["enterpriseHealthMonitor"]["realityCalibrationHealth"])
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("/api/reality-calibration/state", server)

    def test_eo_y_calibration_does_not_mutate_positions_ledgers_or_invoke_ai(self) -> None:
        previous = self._with_env(ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.performance_truth_engine.set_paper_account_cash(10000.0)
            runtime.performance_truth_engine.record_manual_paper_order(symbol="AAPL", side="BUY", quantity=5, decision_object_id="DO-EOY", workflow_id="WF-EOY")
            before = runtime.state()
            before_orders = tuple(item["hash"] for item in before["performanceTruthEngine"]["orderLedger"])
            before_history = before["performanceTruthEngine"]["positionRegistry"]["metrics"]["historyRecordCount"]
            after = runtime.state()

            self.assertEqual(before_orders, tuple(item["hash"] for item in after["performanceTruthEngine"]["orderLedger"]))
            self.assertEqual(before_history, after["performanceTruthEngine"]["positionRegistry"]["metrics"]["historyRecordCount"])
            self.assertFalse(after["enterpriseRealityCalibrationEngine"]["internalDiagnostics"]["mutatesPositions"])
            self.assertFalse(after["enterpriseRealityCalibrationEngine"]["internalDiagnostics"]["mutatesLedgers"])
            self.assertEqual(0, after["enterpriseRealityCalibrationEngine"]["lawVIII"]["routineAiInvocations"])
        finally:
            self._restore_env(previous)

    def test_eo_ae_capital_allocation_record_and_deployable_capital_are_created(self) -> None:
        engine = CapitalAllocationEngine()
        snapshot = engine.allocate(
            timestamp_utc="2026-07-09T15:00:00Z",
            performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0),
            strategy_package_manager={"activePackages": ({"strategyName": "Workflow Proof Strategy", "currentStatus": "Active", "packageHealth": "HEALTHY"},)},
            market_context_engine={"latestMarketContext": {"marketRegime": "risk_on", "confidence": 0.9}},
            enterprise_benchmark_engine={"tradeLevelComparisons": ()},
            trade_attribution_engine={"attributionRepository": ()},
            enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95, "learningReliabilityState": "reliable"}},
            enterprise_operational_guardrails={"readinessState": "Authorized"},
        )

        record = snapshot["latestCapitalAllocationRecord"]
        self.assertEqual("CALLOC-000001", record["capital_allocation_id"])
        self.assertEqual(10000.0, record["required_cash_reserve"])
        self.assertEqual(5000.0, record["deployable_capital"])
        self.assertLessEqual(record["deployable_capital"], record["buying_power"])
        self.assertIn("Portfolio Construction", snapshot["portfolioConstructionFeed"].get("allocationWarnings", ()) or ("Portfolio Construction",))
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])

    def test_eo_ae_pending_orders_buying_power_and_halt_constrain_deployable_capital(self) -> None:
        engine = CapitalAllocationEngine(CapitalAllocationConfig(max_allocation_increase_per_review=1.0))
        pending_truth = self._portfolio_truth(
            cash=50000.0,
            equity=100000.0,
            orders=({"order_id": "ORD-PENDING", "symbol": "AAPL", "status": "QUEUED", "estimated_notional": 12000.0},),
        )
        pending = engine.allocate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=pending_truth, strategy_package_manager={}, market_context_engine={}, enterprise_benchmark_engine={}, trade_attribution_engine={}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95, "learningReliabilityState": "reliable"}}, enterprise_operational_guardrails={"readinessState": "Authorized"})
        self.assertEqual(28000.0, pending["latestCapitalAllocationRecord"]["deployable_capital"])

        low_bp = self._portfolio_truth(cash=50000.0, equity=100000.0)
        low_bp["paperAccount"]["buyingPower"] = 7000.0
        capped = engine.allocate(timestamp_utc="2026-07-09T15:01:00Z", performance_truth=low_bp, strategy_package_manager={}, market_context_engine={}, enterprise_benchmark_engine={}, trade_attribution_engine={}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95, "learningReliabilityState": "reliable"}}, enterprise_operational_guardrails={"readinessState": "Authorized"})
        self.assertEqual(0.0, capped["latestCapitalAllocationRecord"]["deployable_capital"])

        halted = engine.allocate(timestamp_utc="2026-07-09T15:02:00Z", performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), strategy_package_manager={}, market_context_engine={}, enterprise_benchmark_engine={}, trade_attribution_engine={}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95, "learningReliabilityState": "reliable"}}, enterprise_operational_guardrails={"readinessState": "Emergency Halt"})
        self.assertEqual(0.0, halted["latestCapitalAllocationRecord"]["deployable_capital"])
        self.assertIn("emergency_or_reality_halt", halted["latestCapitalAllocationRecord"]["risk_constraints_applied"])

    def test_eo_ae_strategy_asset_sector_and_risk_bucket_budgets_are_exposed(self) -> None:
        engine = CapitalAllocationEngine(CapitalAllocationConfig(max_allocation_increase_per_review=1.0))
        truth = self._portfolio_truth(cash=100000.0, equity=100000.0, positions=(self._position("AAPL", 10000.0), self._position("XYZ", 5000.0),))
        snapshot = engine.allocate(
            timestamp_utc="2026-07-09T15:00:00Z",
            performance_truth=truth,
            strategy_package_manager={"activePackages": ({"strategyName": "Workflow Proof Strategy", "currentStatus": "Active", "packageHealth": "HEALTHY", "maximumDrawdown": 0.12},)},
            market_context_engine={"latestMarketContext": {"marketRegime": "uncertain", "confidence": 0.4}},
            enterprise_benchmark_engine={},
            trade_attribution_engine={},
            enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95, "learningReliabilityState": "reliable"}},
            enterprise_operational_guardrails={"readinessState": "Authorized"},
        )
        record = snapshot["latestCapitalAllocationRecord"]
        self.assertTrue(record["allocation_by_strategy"])
        self.assertTrue(record["allocation_by_asset_type"])
        self.assertTrue(record["allocation_by_sector"])
        self.assertTrue(record["allocation_by_risk_bucket"])
        self.assertTrue(record["allocation_by_market_regime"][0]["degraded"])
        self.assertIn("sector_metadata_missing", record["degraded_inputs"])
        self.assertLess(record["allocation_by_strategy"][0]["cap"], 30000.0)

    def test_eo_ae_reality_fidelity_and_sample_size_limit_allocation_growth(self) -> None:
        engine = CapitalAllocationEngine(CapitalAllocationConfig(max_allocation_increase_per_review=1.0))
        reliable = {"commanderSummary": {"overallRealityFidelityScore": 95, "learningReliabilityState": "reliable"}}
        low = {"commanderSummary": {"overallRealityFidelityScore": 70, "learningReliabilityState": "degraded"}}
        unsafe = {"commanderSummary": {"overallRealityFidelityScore": 45, "learningReliabilityState": "unsafe"}}
        kwargs = {"timestamp_utc": "2026-07-09T15:00:00Z", "performance_truth": self._portfolio_truth(cash=100000.0, equity=100000.0), "strategy_package_manager": {}, "market_context_engine": {}, "enterprise_benchmark_engine": {}, "trade_attribution_engine": {}, "enterprise_operational_guardrails": {"readinessState": "Authorized"}}

        baseline = engine.allocate(**kwargs, enterprise_reality_calibration=reliable)
        degraded = engine.allocate(**{**kwargs, "timestamp_utc": "2026-07-09T15:01:00Z"}, enterprise_reality_calibration=low)
        blocked = engine.allocate(**{**kwargs, "timestamp_utc": "2026-07-09T15:02:00Z"}, enterprise_reality_calibration=unsafe)

        self.assertEqual(90000.0, baseline["latestCapitalAllocationRecord"]["deployable_capital"])
        self.assertLess(degraded["latestCapitalAllocationRecord"]["deployable_capital"], baseline["latestCapitalAllocationRecord"]["deployable_capital"])
        self.assertEqual(0.0, blocked["latestCapitalAllocationRecord"]["deployable_capital"])
        self.assertIn("reality_fidelity_unsafe", blocked["latestCapitalAllocationRecord"]["degraded_inputs"])

    def test_eo_ae_commander_policy_integration_and_deterministic_score(self) -> None:
        policy = {"policyId": "CMD-CAP-001", "policyVersion": "2.0", "minimumCashReservePercent": 0.2, "maxSingleStrategyAllocation": 0.1}
        kwargs = {"timestamp_utc": "2026-07-09T15:00:00Z", "performance_truth": self._portfolio_truth(cash=100000.0, equity=100000.0), "strategy_package_manager": {}, "market_context_engine": {}, "enterprise_benchmark_engine": {}, "trade_attribution_engine": {}, "enterprise_reality_calibration": {"commanderSummary": {"overallRealityFidelityScore": 95, "learningReliabilityState": "reliable"}}, "enterprise_operational_guardrails": {"readinessState": "Authorized"}, "commander_policy": policy}
        first = CapitalAllocationEngine().allocate(**kwargs)
        second = CapitalAllocationEngine().allocate(**kwargs)

        self.assertEqual("2.0", first["latestCapitalAllocationRecord"]["allocation_policy_version"])
        self.assertEqual("CMD-CAP-001", first["latestCapitalAllocationRecord"]["commander_policy_reference"])
        self.assertEqual(20000.0, first["latestCapitalAllocationRecord"]["required_cash_reserve"])
        self.assertEqual(first["latestCapitalAllocationRecord"]["allocation_score"], second["latestCapitalAllocationRecord"]["allocation_score"])

    def test_eo_ae_runtime_and_portfolio_construction_position_sizing_feeds_are_available(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        allocation = state["capitalAllocationEngine"]

        self.assertIn("portfolioConstructionFeed", allocation)
        self.assertIn("positionSizingFeed", allocation)
        self.assertIn("capitalAllocationEngine", state)
        self.assertIn("portfolioConstructionEngine", state)
        self.assertIn("maxCapitalPerStrategy", allocation["portfolioConstructionFeed"])
        self.assertIn("perTradeCapitalCeiling", allocation["positionSizingFeed"])
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("/api/capital-allocation/state", server)

    def test_eo_ae_no_ai_no_mutation_and_terminates(self) -> None:
        engine = CapitalAllocationEngine()
        truth = self._portfolio_truth(cash=100000.0, equity=100000.0)
        before = json.dumps(truth, sort_keys=True)
        snapshot = engine.allocate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, strategy_package_manager={}, market_context_engine={}, enterprise_benchmark_engine={}, trade_attribution_engine={}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95, "learningReliabilityState": "reliable"}}, enterprise_operational_guardrails={"readinessState": "Authorized"})

        self.assertEqual(before, json.dumps(truth, sort_keys=True))
        self.assertFalse(snapshot["internalDiagnostics"]["mutatesLedgers"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertTrue(snapshot["lawVII"]["terminatesImmediately"])

    def test_eo_af_position_sizing_record_and_order_execution_feed_are_created(self) -> None:
        engine = PositionSizingEngine(PositionSizingConfig(maximum_order_notional=100000.0, fractional_shares_enabled=True))
        decision = {"decisionObjectId": "DO-PSIZE-1", "workflowId": "WF-PSIZE-1", "symbol": "AAPL", "assetType": "STOCK", "proposedQuantity": 50, "referencePrice": 100.0, "stopLoss": 95.0, "confidence": 0.9, "currentStrategy": "Workflow Proof Strategy"}
        snapshot = engine.size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(), portfolio_construction=self._portfolio_construction_for_sizing(), enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95}})

        record = snapshot["latestPositionSizingRecord"]
        self.assertEqual("PSIZE-000001", record["position_sizing_id"])
        self.assertEqual("DO-PSIZE-1", record["decision_object_id"])
        self.assertEqual("CALLOC-TEST", record["capital_allocation_id"])
        self.assertEqual("PCON-TEST", record["portfolio_construction_id"])
        self.assertEqual("AAPL", snapshot["orderExecutionFeed"]["symbol"])
        self.assertEqual(record["recommended_quantity"], snapshot["orderExecutionFeed"]["recommended_quantity"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])

    def test_eo_af_risk_based_sizing_uses_stop_loss_distance(self) -> None:
        engine = PositionSizingEngine(PositionSizingConfig(maximum_order_notional=100000.0, fractional_shares_enabled=True))
        decision = {"decisionObjectId": "DO-PSIZE-RISK", "workflowId": "WF-PSIZE", "symbol": "AAPL", "proposedQuantity": 500, "referencePrice": 100.0, "stopLoss": 95.0, "confidence": 1.0, "currentStrategy": "Workflow Proof Strategy"}
        snapshot = engine.size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(deployable=100000.0, per_trade=100000.0), portfolio_construction=self._portfolio_construction_for_sizing(notional=100000.0), enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 100}})
        record = snapshot["latestPositionSizingRecord"]

        self.assertEqual("risk_per_trade", record["limiting_factor"])
        self.assertLess(record["recommended_notional"], record["proposed_notional"])
        self.assertLessEqual(record["risk_per_trade"], 1000.0)

    def test_eo_af_missing_stop_loss_requests_review_or_rejects_by_config(self) -> None:
        decision = {"decisionObjectId": "DO-PSIZE-STOP", "workflowId": "WF-PSIZE", "symbol": "AAPL", "proposedQuantity": 10, "referencePrice": 100.0, "confidence": 0.9, "currentStrategy": "Workflow Proof Strategy"}
        review = PositionSizingEngine().size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(), portfolio_construction=self._portfolio_construction_for_sizing())
        rejected = PositionSizingEngine(PositionSizingConfig(missing_stop_policy="reject")).size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(), portfolio_construction=self._portfolio_construction_for_sizing())

        self.assertEqual("request_risk_review", review["latestPositionSizingRecord"]["recommended_action"])
        self.assertIn("stop_loss_missing_or_invalid", review["latestPositionSizingRecord"]["degraded_inputs"])
        self.assertEqual("reject_size", rejected["latestPositionSizingRecord"]["recommended_action"])

    def test_eo_af_buying_power_allocation_and_construction_caps_reduce_size(self) -> None:
        decision = {"decisionObjectId": "DO-PSIZE-CAPS", "workflowId": "WF-PSIZE", "symbol": "AAPL", "proposedQuantity": 100, "referencePrice": 100.0, "stopLoss": 90.0, "confidence": 1.0, "currentStrategy": "Workflow Proof Strategy"}
        config = PositionSizingConfig(maximum_order_notional=100000.0, fractional_shares_enabled=True)
        buying_power = PositionSizingEngine(config).size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=3000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(deployable=100000.0, per_trade=100000.0), portfolio_construction=self._portfolio_construction_for_sizing(notional=100000.0))
        allocation = PositionSizingEngine(config).size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(deployable=2500.0, per_trade=2500.0), portfolio_construction=self._portfolio_construction_for_sizing(notional=100000.0))
        construction = PositionSizingEngine(config).size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(deployable=100000.0, per_trade=100000.0), portfolio_construction=self._portfolio_construction_for_sizing(action="approve_reduced", notional=4000.0))

        self.assertEqual("buying_power", buying_power["latestPositionSizingRecord"]["limiting_factor"])
        self.assertLessEqual(buying_power["latestPositionSizingRecord"]["recommended_notional"], 3000.0)
        self.assertEqual("capital_allocation", allocation["latestPositionSizingRecord"]["limiting_factor"])
        self.assertLessEqual(allocation["latestPositionSizingRecord"]["recommended_notional"], 2500.0)
        self.assertEqual("portfolio_construction", construction["latestPositionSizingRecord"]["limiting_factor"])
        self.assertLessEqual(construction["latestPositionSizingRecord"]["recommended_notional"], 4000.0)

    def test_eo_af_portfolio_construction_rejection_blocks_without_override(self) -> None:
        decision = {"decisionObjectId": "DO-PSIZE-PCON", "workflowId": "WF-PSIZE", "symbol": "AAPL", "proposedQuantity": 20, "referencePrice": 100.0, "stopLoss": 90.0, "confidence": 0.9, "currentStrategy": "Workflow Proof Strategy"}
        blocked = PositionSizingEngine().size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(), portfolio_construction=self._portfolio_construction_for_sizing(action="reject", notional=0.0))
        override = PositionSizingEngine().size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=1000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(), portfolio_construction=self._portfolio_construction_for_sizing(action="reject", notional=0.0), commander_override={"overrideId": "CMD-PSIZE"})

        self.assertEqual("reject_size", blocked["latestPositionSizingRecord"]["recommended_action"])
        self.assertEqual(0.0, blocked["latestPositionSizingRecord"]["recommended_notional"])
        self.assertEqual("request_commander_review", override["latestPositionSizingRecord"]["recommended_action"])
        self.assertEqual("CMD-PSIZE", override["latestPositionSizingRecord"]["commander_override"]["overrideId"])
        self.assertLessEqual(override["latestPositionSizingRecord"]["recommended_notional"], 1000.0)

    def test_eo_af_liquidity_volatility_and_confidence_reduce_size(self) -> None:
        decision = {"decisionObjectId": "DO-PSIZE-ADJ", "workflowId": "WF-PSIZE", "symbol": "AAPL", "proposedQuantity": 100, "referencePrice": 100.0, "stopLoss": 90.0, "confidence": 0.3, "volatilityScore": 0.8, "currentStrategy": "Workflow Proof Strategy"}
        snapshot = PositionSizingEngine(PositionSizingConfig(maximum_order_notional=100000.0, fractional_shares_enabled=True, minimum_order_notional=0.0)).size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(spread=2.0, volume=200.0), capital_allocation=self._capital_allocation_for_sizing(deployable=100000.0, per_trade=100000.0), portfolio_construction=self._portfolio_construction_for_sizing(notional=100000.0, score=60.0), enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 70}})
        record = snapshot["latestPositionSizingRecord"]

        self.assertLess(record["max_size_by_liquidity"], record["proposed_notional"])
        self.assertLess(record["volatility_adjustment"], 1.0)
        self.assertLess(record["confidence_adjustment"], 0.65)
        self.assertIn(record["recommended_action"], {"request_commander_review", "reduce_size"})

    def test_eo_af_fractional_and_whole_share_modes_never_round_up(self) -> None:
        decision = {"decisionObjectId": "DO-PSIZE-FRAC", "workflowId": "WF-PSIZE", "symbol": "AAPL", "proposedQuantity": 1.55, "referencePrice": 100.0, "stopLoss": 90.0, "confidence": 1.0, "currentStrategy": "Workflow Proof Strategy"}
        fractional = PositionSizingEngine(PositionSizingConfig(fractional_shares_enabled=True, maximum_order_notional=100000.0)).size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(), portfolio_construction=self._portfolio_construction_for_sizing(notional=1000.0))
        whole = PositionSizingEngine(PositionSizingConfig(fractional_shares_enabled=False, maximum_order_notional=100000.0)).size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(), portfolio_construction=self._portfolio_construction_for_sizing(notional=1000.0))

        self.assertGreater(fractional["latestPositionSizingRecord"]["recommended_quantity"], whole["latestPositionSizingRecord"]["recommended_quantity"])
        self.assertEqual(1.0, whole["latestPositionSizingRecord"]["recommended_quantity"])
        self.assertLessEqual(fractional["latestPositionSizingRecord"]["recommended_notional"], fractional["latestPositionSizingRecord"]["proposed_notional"])

    def test_eo_af_max_order_notional_and_output_for_execution_are_enforced(self) -> None:
        decision = {"decisionObjectId": "DO-PSIZE-MAX", "workflowId": "WF-PSIZE", "symbol": "AAPL", "proposedQuantity": 100, "referencePrice": 100.0, "stopLoss": 90.0, "confidence": 1.0, "orderType": "limit", "timeInForce": "day", "currentStrategy": "Workflow Proof Strategy"}
        snapshot = PositionSizingEngine(PositionSizingConfig(maximum_order_notional=1500.0, fractional_shares_enabled=True)).size(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(deployable=100000.0, per_trade=100000.0), portfolio_construction=self._portfolio_construction_for_sizing(notional=100000.0))
        record = snapshot["latestPositionSizingRecord"]

        self.assertEqual("maximum_order_notional", record["limiting_factor"])
        self.assertLessEqual(record["recommended_notional"], 1500.0)
        self.assertEqual("LIMIT", snapshot["orderExecutionFeed"]["order_type"])
        self.assertEqual("DAY", snapshot["orderExecutionFeed"]["time_in_force"])
        self.assertEqual("PSIZE-000001", snapshot["orderExecutionFeed"]["sizing_record_reference"])

    def test_eo_af_runtime_api_no_ai_no_mutation_and_terminates(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        sizing = state["positionSizingEngine"]
        truth = self._portfolio_truth(cash=100000.0, equity=100000.0)
        before = json.dumps(truth, sort_keys=True)
        snapshot = PositionSizingEngine().size(timestamp_utc="2026-07-09T15:00:00Z", decision_object={"decisionObjectId": "DO-PSIZE-SAFE", "workflowId": "WF-PSIZE", "symbol": "AAPL", "proposedQuantity": 1, "referencePrice": 100.0, "stopLoss": 90.0}, performance_truth=truth, market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(), portfolio_construction=self._portfolio_construction_for_sizing())

        self.assertIn("positionSizingEngine", state)
        self.assertIn("latestPositionSizingRecord", sizing)
        self.assertEqual(before, json.dumps(truth, sort_keys=True))
        self.assertFalse(snapshot["internalDiagnostics"]["mutatesLedgers"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertTrue(snapshot["lawVII"]["terminatesImmediately"])
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("/api/position-sizing/state", server)

    def test_eo_ag_risk_factor_record_and_exposure_calculations_are_created(self) -> None:
        engine = EnterpriseRiskFactorEngine()
        truth = self._portfolio_truth(cash=70000.0, equity=100000.0, positions=(self._position("AAPL", 20000.0), self._position("MSFT", 10000.0)))
        snapshot = engine.evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data(), market_context_engine={"latestMarketContext": {"marketRegime": "risk_on", "confidence": 0.9}}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95, "learningReliabilityState": "reliable"}}, enterprise_benchmark_engine={"tradeLevelComparisons": ({"id": "B1"},)}, closed_position_truth={})

        record = snapshot["latestRiskFactorRecord"]
        self.assertEqual("RFAC-000001", record["risk_factor_record_id"])
        self.assertEqual(100000.0, record["portfolio_equity"])
        self.assertEqual(30000.0, record["total_market_value"])
        self.assertEqual(30000.0, record["long_exposure"])
        self.assertEqual(0.3, record["exposure_summary"]["top3PositionWeight"])
        self.assertIn("riskOfficeFeed", snapshot)
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])

    def test_eo_ag_concentration_sector_and_missing_metadata_affect_risk(self) -> None:
        engine = EnterpriseRiskFactorEngine()
        concentrated = engine.evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=self._portfolio_truth(cash=10000.0, equity=100000.0, positions=(self._position("AAPL", 70000.0), self._position("MSFT", 20000.0))), market_data_provider=self._portfolio_market_data(), market_context_engine={}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95}})
        missing = engine.evaluate(timestamp_utc="2026-07-09T15:01:00Z", performance_truth=self._portfolio_truth(cash=50000.0, equity=100000.0, positions=(self._position("XYZ", 50000.0),)), market_data_provider=self._portfolio_market_data(), market_context_engine={}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95}})

        record = concentrated["latestRiskFactorRecord"]
        self.assertGreater(record["concentration_risk_score"], 50)
        self.assertGreater(record["sector_risk_score"], 50)
        self.assertIn("reduce_sector_exposure", record["recommended_risk_actions"])
        self.assertIn("sector_metadata_missing", missing["latestRiskFactorRecord"]["degraded_inputs"])

    def test_eo_ag_liquidity_and_missing_liquidity_score_conservatively(self) -> None:
        engine = EnterpriseRiskFactorEngine()
        poor = engine.evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=self._portfolio_truth(cash=10000.0, equity=100000.0, positions=(self._position("AAPL", 50000.0),)), market_data_provider=self._portfolio_market_data(spread=3.0, volume=100.0), market_context_engine={}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95}})
        missing = engine.evaluate(timestamp_utc="2026-07-09T15:01:00Z", performance_truth=self._portfolio_truth(cash=10000.0, equity=100000.0, positions=(self._position("AAPL", 50000.0),)), market_data_provider={"normalizedObjects": {"quotes": ()}}, market_context_engine={}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95}})

        self.assertGreater(poor["latestRiskFactorRecord"]["liquidity_risk_score"], 60)
        self.assertGreaterEqual(missing["latestRiskFactorRecord"]["liquidity_risk_score"], 55)
        self.assertIn("liquidity_data_missing", missing["latestRiskFactorRecord"]["degraded_inputs"])

    def test_eo_ag_volatility_drawdown_reality_and_execution_risks_increase(self) -> None:
        engine = EnterpriseRiskFactorEngine()
        truth = self._portfolio_truth(cash=50000.0, equity=100000.0, positions=(self._position("AAPL", 50000.0),), orders=({"order_id": "ORD-1", "status": "REJECTED", "symbol": "AAPL"},))
        truth["portfolioLedger"] = ({"cash": 50000.0, "market_value": 50000.0, "total_equity": 100000.0}, {"cash": 45000.0, "market_value": 35000.0, "total_equity": 80000.0})
        truth["executionRealism"] = {"rejectedOrders": 1, "partialFills": 0, "fantasyTradeWarnings": ("impossible_fill",), "slippageCost": 3.0}
        market = self._portfolio_market_data()
        market["normalizedObjects"]["quotes"][0]["volatility"] = 0.8
        snapshot = engine.evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=market, market_context_engine={"latestMarketContext": {"marketRegime": "risk_off", "confidence": 0.5, "volatilityState": "high"}}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 45, "learningReliabilityState": "unsafe"}}, enterprise_benchmark_engine={}, closed_position_truth={})
        record = snapshot["latestRiskFactorRecord"]

        self.assertGreater(record["volatility_risk_score"], 60)
        self.assertGreater(record["drawdown_risk_score"], 60)
        self.assertGreater(record["reality_fidelity_risk_score"], 80)
        self.assertGreater(record["execution_risk_score"], 60)
        self.assertIn("require_reality_calibration", record["recommended_risk_actions"])

    def test_eo_ag_composite_risk_is_deterministic_and_critical_recommends_action(self) -> None:
        config = EnterpriseRiskFactorConfig(halt_trading_threshold=45.0)
        kwargs = {"timestamp_utc": "2026-07-09T15:00:00Z", "performance_truth": self._portfolio_truth(cash=0.0, equity=100000.0, positions=(self._position("AAPL", 90000.0),)), "market_data_provider": {"normalizedObjects": {"quotes": ()}}, "market_context_engine": {"latestMarketContext": {"marketRegime": "crisis", "confidence": 0.2}}, "enterprise_reality_calibration": {"commanderSummary": {"overallRealityFidelityScore": 30, "learningReliabilityState": "blocked"}}}
        first = EnterpriseRiskFactorEngine(config).evaluate(**kwargs)
        second = EnterpriseRiskFactorEngine(config).evaluate(**kwargs)

        self.assertEqual(first["latestRiskFactorRecord"]["composite_risk_score"], second["latestRiskFactorRecord"]["composite_risk_score"])
        self.assertTrue(first["riskOfficeFeed"]["haltRecommended"])
        self.assertIn("halt_trading", first["latestRiskFactorRecord"]["recommended_risk_actions"])

    def test_eo_ag_feeds_are_consumable_by_risk_and_portfolio_engines(self) -> None:
        risk = EnterpriseRiskFactorEngine(EnterpriseRiskFactorConfig(halt_trading_threshold=45.0)).evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=self._portfolio_truth(cash=0.0, equity=100000.0, positions=(self._position("AAPL", 90000.0),)), market_data_provider={"normalizedObjects": {"quotes": ()}}, market_context_engine={"latestMarketContext": {"marketRegime": "crisis", "confidence": 0.2}}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 30, "learningReliabilityState": "blocked"}})
        allocation = CapitalAllocationEngine(CapitalAllocationConfig(max_allocation_increase_per_review=1.0)).allocate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), strategy_package_manager={}, market_context_engine={}, enterprise_benchmark_engine={}, trade_attribution_engine={}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95, "learningReliabilityState": "reliable"}}, enterprise_operational_guardrails={"readinessState": "Authorized"}, enterprise_risk_factor=risk)
        construction = PortfolioConstructionEngine().evaluate(timestamp_utc="2026-07-09T15:00:00Z", decision_object={"decisionObjectId": "DO-RISK", "workflowId": "WF-RISK", "symbol": "AAPL", "positionSizeRecommendation": 0.02, "stopLoss": 95.0, "currentStrategy": "Workflow Proof Strategy"}, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), strategy_package_manager={}, capital_allocation=self._capital_allocation_for_sizing(), enterprise_risk_factor=risk)
        sizing = PositionSizingEngine().size(timestamp_utc="2026-07-09T15:00:00Z", decision_object={"decisionObjectId": "DO-RISK", "workflowId": "WF-RISK", "symbol": "AAPL", "proposedQuantity": 10, "referencePrice": 100.0, "stopLoss": 90.0}, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(), portfolio_construction=self._portfolio_construction_for_sizing(), enterprise_risk_factor=risk)

        self.assertEqual(0.0, allocation["latestCapitalAllocationRecord"]["deployable_capital"])
        self.assertEqual("reject", construction["latestPortfolioConstructionRecord"]["recommended_action"])
        self.assertEqual("reject_size", sizing["latestPositionSizingRecord"]["recommended_action"])
        self.assertTrue(risk["riskOfficeFeed"]["topRiskFactors"])

    def test_eo_ag_runtime_health_api_no_ai_no_mutation_and_terminates(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        risk = state["enterpriseRiskFactorEngine"]
        truth = self._portfolio_truth(cash=100000.0, equity=100000.0)
        before = json.dumps(truth, sort_keys=True)
        snapshot = EnterpriseRiskFactorEngine().evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data(), market_context_engine={}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95}})

        self.assertIn("enterpriseRiskFactorEngine", state)
        self.assertIn("riskFactorHealth", state["enterpriseHealthMonitor"])
        self.assertIn("latestCompositeRiskScore", risk["enterpriseHealthMetrics"])
        self.assertEqual(before, json.dumps(truth, sort_keys=True))
        self.assertFalse(snapshot["internalDiagnostics"]["mutatesLedgers"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertTrue(snapshot["lawVII"]["terminatesImmediately"])
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("/api/risk-factor/state", server)

    def test_eo_ah_correlation_record_and_pairwise_return_correlation_are_created(self) -> None:
        engine = CorrelationIntelligenceEngine()
        truth = self._portfolio_truth(cash=40000.0, equity=100000.0, positions=(self._position("AAPL", 30000.0), self._position("MSFT", 30000.0)))
        provider = {"normalizedObjects": {"returnHistory": ({"symbol": "AAPL", "returns": (0.01, 0.02, -0.01, 0.03, 0.01)}, {"symbol": "MSFT", "returns": (0.011, 0.021, -0.009, 0.029, 0.012)})}}
        snapshot = engine.evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=provider, enterprise_benchmark_engine={"tradeLevelComparisons": ({"id": "B1"},)})

        record = snapshot["latestCorrelationIntelligenceRecord"]
        self.assertEqual("CORR-000001", record["correlation_intelligence_id"])
        self.assertEqual("pearson_return_correlation", record["correlation_method"])
        self.assertGreater(record["correlation_matrix"]["AAPL"]["MSFT"], 0.95)
        self.assertEqual(1, len(record["high_correlation_pairs"]))
        self.assertIn("riskFactorFeed", snapshot)

    def test_eo_ah_insufficient_history_inverse_and_uncorrelated_pairs_are_classified(self) -> None:
        truth = self._portfolio_truth(cash=10000.0, equity=100000.0, positions=(self._position("AAPL", 30000.0), self._position("MSFT", 30000.0), self._position("GLD", 30000.0)))
        provider = {"normalizedObjects": {"returnHistory": ({"symbol": "AAPL", "returns": (0.01, 0.02, -0.01, 0.03, 0.01)}, {"symbol": "MSFT", "returns": (-0.01, -0.02, 0.01, -0.03, -0.01)}, {"symbol": "GLD", "returns": (0.0, 0.01, 0.0, -0.01, 0.0)})}}
        classified = CorrelationIntelligenceEngine().evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=provider)
        insufficient = CorrelationIntelligenceEngine().evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider={"normalizedObjects": {"returnHistory": ({"symbol": "AAPL", "returns": (0.01,)},)}})

        self.assertTrue(classified["latestCorrelationIntelligenceRecord"]["inverse_correlation_pairs"])
        self.assertTrue(classified["latestCorrelationIntelligenceRecord"]["uncorrelated_pairs"])
        self.assertEqual("metadata_proxy", insufficient["latestCorrelationIntelligenceRecord"]["correlation_method"])
        self.assertIn("return_history_insufficient", insufficient["latestCorrelationIntelligenceRecord"]["degraded_inputs"])

    def test_eo_ah_metadata_strategy_thesis_and_etf_overlap_groups_are_detected(self) -> None:
        aapl = {**self._position("AAPL", 20000.0), "sector": "Technology", "thesis_tags": ("AI",)}
        msft = {**self._position("MSFT", 20000.0), "sector": "Technology", "thesis_tags": ("AI",)}
        qqq = {**self._position("QQQ", 20000.0, asset_type="ETF"), "sector": "Technology", "thesis_tags": ("AI",)}
        truth = self._portfolio_truth(cash=40000.0, equity=100000.0, positions=(aapl, msft, qqq))
        provider = {"normalizedObjects": {"fundHoldings": ({"symbol": "QQQ", "holdings": ("AAPL", "MSFT")},)}}
        snapshot = CorrelationIntelligenceEngine().evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=provider)
        record = snapshot["latestCorrelationIntelligenceRecord"]

        self.assertTrue(record["sector_overlap_groups"])
        self.assertTrue(record["strategy_overlap_groups"])
        self.assertTrue(record["thesis_overlap_groups"])
        self.assertTrue(record["asset_type_overlap_groups"])
        self.assertTrue(record["etf_overlap_groups"])

    def test_eo_ah_etf_overlap_degrades_without_holdings_metadata(self) -> None:
        qqq = self._position("QQQ", 20000.0, asset_type="ETF")
        snapshot = CorrelationIntelligenceEngine().evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=self._portfolio_truth(cash=80000.0, equity=100000.0, positions=(qqq,)), market_data_provider={"normalizedObjects": {}})

        self.assertIn("etf_holdings_unavailable", snapshot["latestCorrelationIntelligenceRecord"]["degraded_inputs"])
        self.assertFalse(snapshot["latestCorrelationIntelligenceRecord"]["etf_overlap_groups"])

    def test_eo_ah_hidden_concentration_diversification_and_actions_are_deterministic(self) -> None:
        positions = (self._position("AAPL", 45000.0), self._position("MSFT", 45000.0))
        truth = self._portfolio_truth(cash=10000.0, equity=100000.0, positions=positions)
        provider = {"normalizedObjects": {"returnHistory": ({"symbol": "AAPL", "returns": (0.01, 0.02, -0.01, 0.03, 0.01)}, {"symbol": "MSFT", "returns": (0.011, 0.021, -0.009, 0.029, 0.012)})}}
        first = CorrelationIntelligenceEngine().evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=provider)
        second = CorrelationIntelligenceEngine().evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=provider)
        record = first["latestCorrelationIntelligenceRecord"]

        self.assertEqual(record["correlation_risk_score"], second["latestCorrelationIntelligenceRecord"]["correlation_risk_score"])
        self.assertGreater(record["hidden_concentration_score"], 50)
        self.assertLess(record["diversification_quality_score"], 70)
        self.assertIn("reduce_correlated_exposure", record["recommended_actions"])

    def test_eo_ah_feeds_are_consumable_by_risk_construction_allocation_and_sizing(self) -> None:
        positions = (self._position("AAPL", 45000.0), self._position("MSFT", 45000.0))
        truth = self._portfolio_truth(cash=10000.0, equity=100000.0, positions=positions)
        provider = {"normalizedObjects": {"returnHistory": ({"symbol": "AAPL", "returns": (0.01, 0.02, -0.01, 0.03, 0.01)}, {"symbol": "MSFT", "returns": (0.011, 0.021, -0.009, 0.029, 0.012)})}}
        correlation = CorrelationIntelligenceEngine(CorrelationIntelligenceConfig(correlation_risk_high_threshold=40.0)).evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=provider)
        risk = EnterpriseRiskFactorEngine().evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data(), market_context_engine={}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95}}, correlation_intelligence=correlation)
        allocation = CapitalAllocationEngine(CapitalAllocationConfig(max_allocation_increase_per_review=1.0)).allocate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), strategy_package_manager={}, market_context_engine={}, enterprise_benchmark_engine={}, trade_attribution_engine={}, enterprise_reality_calibration={"commanderSummary": {"overallRealityFidelityScore": 95, "learningReliabilityState": "reliable"}}, enterprise_operational_guardrails={"readinessState": "Authorized"}, correlation_intelligence=correlation)
        construction = PortfolioConstructionEngine().evaluate(timestamp_utc="2026-07-09T15:00:00Z", decision_object={"decisionObjectId": "DO-CORR", "workflowId": "WF-CORR", "symbol": "AAPL", "positionSizeRecommendation": 0.02, "stopLoss": 95.0, "currentStrategy": "Workflow Proof Strategy"}, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), strategy_package_manager={}, capital_allocation=self._capital_allocation_for_sizing(), correlation_intelligence=correlation)
        sizing = PositionSizingEngine(PositionSizingConfig(maximum_order_notional=100000.0, fractional_shares_enabled=True)).size(timestamp_utc="2026-07-09T15:00:00Z", decision_object={"decisionObjectId": "DO-CORR", "workflowId": "WF-CORR", "symbol": "AAPL", "proposedQuantity": 100, "referencePrice": 100.0, "stopLoss": 90.0}, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), capital_allocation=self._capital_allocation_for_sizing(deployable=100000.0, per_trade=100000.0), portfolio_construction=self._portfolio_construction_for_sizing(notional=100000.0), correlation_intelligence=correlation)

        self.assertEqual(risk["latestRiskFactorRecord"]["correlation_risk_score"], correlation["latestCorrelationIntelligenceRecord"]["correlation_risk_score"])
        self.assertIn("correlation_intelligence_reduction", allocation["latestCapitalAllocationRecord"]["risk_constraints_applied"])
        self.assertIn(construction["latestPortfolioConstructionRecord"]["recommended_action"], {"approve_reduced", "request_commander_review"})
        self.assertLess(sizing["latestPositionSizingRecord"]["recommended_notional"], sizing["latestPositionSizingRecord"]["proposed_notional"])

    def test_eo_ah_runtime_health_api_no_ai_no_mutation_and_terminates(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        truth = self._portfolio_truth(cash=100000.0, equity=100000.0)
        before = json.dumps(truth, sort_keys=True)
        snapshot = CorrelationIntelligenceEngine().evaluate(timestamp_utc="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider={"normalizedObjects": {}})

        self.assertIn("correlationIntelligenceEngine", state)
        self.assertIn("correlationIntelligenceHealth", state["enterpriseHealthMonitor"])
        self.assertEqual(before, json.dumps(truth, sort_keys=True))
        self.assertFalse(snapshot["internalDiagnostics"]["mutatesLedgers"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertTrue(snapshot["lawVII"]["terminatesImmediately"])
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("/api/correlation-intelligence/state", server)

    def test_eo_ba_replay_scenario_and_run_records_are_created(self) -> None:
        engine = MarketReplayEngine()
        scenario_snapshot = engine.create_scenario(scenario_name="AAPL replay", replay_start="2026-07-06T14:30:00Z", replay_end="2026-07-08T14:30:00Z", symbols=("AAPL",), historical_market_data=self._historical_replay_data(), initial_cash=10000.0)
        scenario = scenario_snapshot["latestReplayScenarioRecord"]
        run = engine.run_replay(scenario=scenario, historical_market_data=self._historical_replay_data())["latestReplayRunRecord"]

        self.assertEqual("MRE-SCEN-000001", scenario["replay_scenario_id"])
        self.assertEqual("MRE-RUN-000001", run["replay_run_id"])
        self.assertEqual("COMPLETED", run["status"])
        self.assertTrue(run["order_ids"])
        self.assertTrue(run["execution_ids"])
        self.assertEqual("replay", run["replay_performance_truth"]["execution_environment"])

    def test_eo_ba_replay_clock_advances_deterministically_without_wall_clock(self) -> None:
        clock = ReplayClock("2026-07-06T14:30:00Z", "2026-07-08T14:30:00Z", "1D")
        first = clock.timestamp()
        second = clock.advance()
        third = clock.advance()

        self.assertEqual("2026-07-06T14:30:00Z", first)
        self.assertEqual("2026-07-07T14:30:00Z", second)
        self.assertEqual("2026-07-08T14:30:00Z", third)
        self.assertTrue(clock.done())

    def test_eo_ba_point_in_time_provider_excludes_future_prices_and_marks_missing(self) -> None:
        provider = HistoricalReplayMarketProvider(self._historical_replay_data())
        quote = provider.latest_quote("AAPL", "2026-07-07T14:30:00Z")
        missing = provider.latest_quote("AAPL", "2026-07-05T14:30:00Z")

        self.assertEqual(102.0, quote["last"])
        self.assertNotEqual(101.0, quote["last"])
        self.assertEqual("MISSING", missing["status"])
        self.assertTrue(provider.lookahead_violations)

    def test_eo_ba_replay_buy_sell_positions_truth_and_benchmarks_are_isolated(self) -> None:
        runtime = create_runtime()
        before_positions = len(runtime.state()["performanceTruthEngine"]["positionRegistry"]["activePositions"])
        engine = MarketReplayEngine()
        scenario = engine.create_scenario(scenario_name="AAPL replay", replay_start="2026-07-06T14:30:00Z", replay_end="2026-07-08T14:30:00Z", symbols=("AAPL",), historical_market_data=self._historical_replay_data(), benchmark_symbols=("SPY",), initial_cash=10000.0)["latestReplayScenarioRecord"]
        run = engine.run_replay(scenario=scenario, historical_market_data=self._historical_replay_data())["latestReplayRunRecord"]
        after_positions = len(runtime.state()["performanceTruthEngine"]["positionRegistry"]["activePositions"])

        self.assertEqual(before_positions, after_positions)
        self.assertTrue(any(order["side"] == "BUY" for order in run["replay_orders"]))
        self.assertTrue(any(order["side"] == "SELL" for order in run["replay_orders"]))
        self.assertEqual("replay", run["replay_closed_position_truth"][0]["execution_environment"])
        self.assertEqual("COMPLETE", run["benchmark_results"][0]["status"])
        self.assertTrue(run["replay_performance_truth"]["isolatedFromPaper"])

    def test_eo_ba_same_scenario_reproducibility_hash_is_stable(self) -> None:
        data = self._historical_replay_data()
        first_engine = MarketReplayEngine()
        second_engine = MarketReplayEngine()
        scenario_one = first_engine.create_scenario(scenario_name="Replay", replay_start="2026-07-06T14:30:00Z", replay_end="2026-07-08T14:30:00Z", symbols=("AAPL",), historical_market_data=data, initial_cash=10000.0)["latestReplayScenarioRecord"]
        scenario_two = second_engine.create_scenario(scenario_name="Replay", replay_start="2026-07-06T14:30:00Z", replay_end="2026-07-08T14:30:00Z", symbols=("AAPL",), historical_market_data=data, initial_cash=10000.0)["latestReplayScenarioRecord"]
        first = first_engine.run_replay(scenario=scenario_one, historical_market_data=data)["latestReplayRunRecord"]
        second = second_engine.run_replay(scenario=scenario_two, historical_market_data=data)["latestReplayRunRecord"]

        self.assertEqual(first["reproducibility_hash"], second["reproducibility_hash"])
        self.assertEqual(first["replay_return"], second["replay_return"])

    def test_eo_ba_degraded_data_and_lookahead_violation_affect_learning_eligibility(self) -> None:
        engine = MarketReplayEngine()
        scenario = engine.create_scenario(scenario_name="Missing replay", replay_start="2026-07-05T14:30:00Z", replay_end="2026-07-06T14:30:00Z", symbols=("AAPL",), historical_market_data=self._historical_replay_data(), initial_cash=10000.0)["latestReplayScenarioRecord"]
        run = engine.run_replay(scenario=scenario, historical_market_data=self._historical_replay_data())["latestReplayRunRecord"]

        self.assertIn("lookahead_guard_violation", run["degraded_inputs"])
        self.assertEqual("blocked", run["learning_eligibility"])
        self.assertTrue(any(event["event_type"] == "lookahead_guard_violation" for event in run["replay_audit_trail"]))

    def test_eo_ba_runtime_api_no_ai_no_live_trading_and_terminates(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        engine = MarketReplayEngine()
        snapshot = engine.snapshot(timestamp_utc="2026-07-09T15:00:00Z")

        self.assertIn("marketReplayEngine", state)
        self.assertFalse(snapshot["internalDiagnostics"]["mutatesPaperLedgers"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesLiveTrades"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertTrue(snapshot["lawVII"]["terminatesImmediately"])
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("/api/market-replay/state", server)

    def test_eo_bc_stress_scenario_and_test_records_are_created(self) -> None:
        engine = StressTestingEngine()
        scenario = engine.create_scenario(
            scenario_name="Technology selloff",
            scenario_type="combined_stress",
            created_at="2026-07-09T15:00:00Z",
            market_shock_percent=-0.10,
            sector_shocks={"Technology": -0.05},
            symbol_shocks={"AAPL": -0.10},
        )["latestStressScenarioRecord"]
        record = engine.run_stress_test(
            scenario=scenario,
            timestamp_utc="2026-07-09T15:01:00Z",
            performance_truth=self._portfolio_truth(cash=90000.0, equity=100000.0, positions=({**self._position("AAPL", 10000.0), "average_cost": 100.0},)),
            market_data_provider=self._portfolio_market_data(),
        )["latestStressTestRecord"]

        self.assertEqual("STR-SCEN-000001", scenario["stress_scenario_id"])
        self.assertEqual("STR-TEST-000001", record["stress_test_id"])
        self.assertEqual("EO-BC", engine.snapshot(timestamp_utc="2026-07-09T15:02:00Z")["engineeringOrder"])
        self.assertEqual(1, record["positions_tested"])

    def test_eo_bc_stress_does_not_mutate_live_positions_cash_or_buying_power(self) -> None:
        engine = StressTestingEngine()
        position = {**self._position("AAPL", 10000.0), "average_cost": 100.0, "stop_loss": 95.0}
        truth = self._portfolio_truth(cash=90000.0, equity=100000.0, positions=(position,))
        before = json.dumps(truth, sort_keys=True)
        scenario = engine.create_scenario(scenario_name="Isolation", created_at="2026-07-09T15:00:00Z", market_shock_percent=-0.20)["latestStressScenarioRecord"]

        snapshot = engine.run_stress_test(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())

        self.assertEqual(before, json.dumps(truth, sort_keys=True))
        self.assertFalse(snapshot["internalDiagnostics"]["mutatesPositions"])
        self.assertFalse(snapshot["internalDiagnostics"]["mutatesPortfolioLedger"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])

    def test_eo_bc_market_sector_and_symbol_shocks_are_deterministic_and_scoped(self) -> None:
        engine = StressTestingEngine()
        positions = (
            {**self._position("AAPL", 10000.0), "average_cost": 100.0, "sector": "Technology"},
            {**self._position("SPY", 10000.0, asset_type="ETF"), "average_cost": 100.0, "sector": "Broad Market"},
        )
        truth = self._portfolio_truth(cash=80000.0, equity=100000.0, positions=positions)
        scenario = engine.create_scenario(
            scenario_name="Scoped shocks",
            scenario_type="combined_stress",
            created_at="2026-07-09T15:00:00Z",
            market_shock_percent=-0.10,
            sector_shocks={"Technology": -0.05},
            symbol_shocks={"AAPL": -0.10},
        )["latestStressScenarioRecord"]

        first = engine.run_stress_test(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())["latestStressTestRecord"]
        second = StressTestingEngine().run_stress_test(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())["latestStressTestRecord"]
        rows = {item["symbol"]: item for item in first["stressed_position_results"]}

        self.assertEqual(75.0, rows["AAPL"]["stressed_price"])
        self.assertEqual(90.009, rows["SPY"]["stressed_price"])
        self.assertEqual(first["composite_stress_score"], second["composite_stress_score"])

    def test_eo_bc_spread_liquidity_stop_and_cascade_risk_are_detected(self) -> None:
        engine = StressTestingEngine()
        positions = (
            {**self._position("AAPL", 10000.0), "average_cost": 100.0, "stop_loss": 95.0},
            {**self._position("MSFT", 10000.0), "average_cost": 100.0, "stop_loss": 96.0, "sector": "Technology"},
        )
        truth = self._portfolio_truth(cash=80000.0, equity=100000.0, positions=positions)
        scenario = engine.create_scenario(
            scenario_name="Cascade",
            created_at="2026-07-09T15:00:00Z",
            market_shock_percent=-0.08,
            spread_multiplier=6.0,
            liquidity_multiplier=0.01,
            slippage_multiplier=4.0,
        )["latestStressScenarioRecord"]

        record = engine.run_stress_test(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data(volume=1000.0))["latestStressTestRecord"]

        self.assertEqual(2, record["positions_at_stop"])
        self.assertTrue(record["stop_cascade_risk"]["cascadeRisk"])
        self.assertGreater(record["execution_stress_results"][0]["stressedSpread"], 0.04)
        self.assertGreater(record["liquidity_stress_results"][0]["liquiditySeverity"], 50)
        self.assertIn("increase_cash_reserve", record["recommended_actions"])

    def test_eo_bc_correlation_clusters_use_eo_ah_and_missing_correlation_degrades(self) -> None:
        engine = StressTestingEngine()
        positions = (
            {**self._position("AAPL", 10000.0), "average_cost": 100.0, "sector": "Technology"},
            {**self._position("MSFT", 10000.0), "average_cost": 100.0, "sector": "Technology"},
        )
        truth = self._portfolio_truth(cash=80000.0, equity=100000.0, positions=positions)
        scenario = engine.create_scenario(scenario_name="Correlation", created_at="2026-07-09T15:00:00Z", market_shock_percent=-0.10)["latestStressScenarioRecord"]
        eo_ah = {"riskFactorFeed": {"overlapGroups": ({"group_id": "CORR-TECH", "group_type": "same_sector", "members": ("AAPL", "MSFT")},)}}

        with_corr = engine.run_stress_test(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data(), correlation_intelligence=eo_ah)["latestStressTestRecord"]
        without_corr = StressTestingEngine().run_stress_test(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())["latestStressTestRecord"]

        self.assertEqual("EO-AH", with_corr["correlation_cluster_results"][0]["source"])
        self.assertIn("correlation_proxy_used", without_corr["degraded_inputs"])

    def test_eo_bc_risk_rule_violations_critical_actions_and_health_feed_are_recorded(self) -> None:
        engine = StressTestingEngine(StressTestingConfig(critical_stress_threshold=60.0, critical_drawdown_threshold=0.05, max_sector_exposure_percent=0.05))
        position = {**self._position("AAPL", 50000.0), "average_cost": 100.0, "stop_loss": 95.0, "sector": "Technology"}
        truth = self._portfolio_truth(cash=50000.0, equity=100000.0, positions=(position,))
        scenario = engine.create_scenario(scenario_name="Critical", created_at="2026-07-09T15:00:00Z", market_shock_percent=-0.20)["latestStressScenarioRecord"]

        snapshot = engine.run_stress_test(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())
        record = snapshot["latestStressTestRecord"]

        self.assertTrue(record["risk_rule_violations"])
        self.assertIn(record["stress_level"], {"high", "critical"})
        self.assertTrue({"request_risk_review", "request_commander_review", "halt_trading"} & set(record["recommended_actions"]))
        self.assertEqual(record["composite_stress_score"], snapshot["enterpriseHealthMetrics"]["latestCompositeStressScore"])
        self.assertTrue(snapshot["riskFactorFeed"]["stressTestingAvailable"])

    def test_eo_bc_runtime_api_configuration_no_ai_no_uncontrolled_loop(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        snapshot = state["stressTestingEngine"]
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        self.assertIn("stressTestingEngine", state)
        self.assertIn("stressTestingHealth", state["enterpriseHealthMonitor"])
        self.assertIn("/api/stress-testing/state", server)
        self.assertTrue(any(item["name"] == "Stress Testing Enabled" for item in state["enterpriseConfigurationRegistry"]["configurationRegistry"]))
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertTrue(snapshot["lawVII"]["terminatesImmediately"])
        self.assertFalse(snapshot["internalDiagnostics"]["createsExecutionRecords"])

    def test_eo_bd_black_swan_scenario_and_simulation_records_are_created(self) -> None:
        engine = BlackSwanSimulationEngine()
        scenario = engine.create_scenario(
            scenario_name="Overnight gap",
            scenario_type="overnight_gap",
            created_at="2026-07-09T15:00:00Z",
            market_gap_percent=-0.30,
        )["latestBlackSwanScenarioRecord"]
        record = engine.run_simulation(
            scenario=scenario,
            timestamp_utc="2026-07-09T15:01:00Z",
            performance_truth=self._portfolio_truth(cash=90000.0, equity=100000.0, positions=({**self._position("AAPL", 10000.0), "average_cost": 100.0},)),
            market_data_provider=self._portfolio_market_data(),
        )["latestBlackSwanSimulationRecord"]

        self.assertEqual("BSW-SCEN-000001", scenario["black_swan_scenario_id"])
        self.assertEqual("BSW-SIM-000001", record["black_swan_simulation_id"])
        self.assertEqual(1, record["positions_simulated"])
        self.assertEqual("EO-BD", engine.snapshot(timestamp_utc="2026-07-09T15:02:00Z")["engineeringOrder"])

    def test_eo_bd_simulation_does_not_mutate_live_positions_cash_or_buying_power(self) -> None:
        engine = BlackSwanSimulationEngine()
        position = {**self._position("AAPL", 10000.0), "average_cost": 100.0, "stop_loss": 95.0}
        truth = self._portfolio_truth(cash=90000.0, equity=100000.0, positions=(position,))
        before = json.dumps(truth, sort_keys=True)
        scenario = engine.create_scenario(scenario_name="Isolation", created_at="2026-07-09T15:00:00Z", market_gap_percent=-0.40)["latestBlackSwanScenarioRecord"]

        snapshot = engine.run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())

        self.assertEqual(before, json.dumps(truth, sort_keys=True))
        self.assertFalse(snapshot["internalDiagnostics"]["mutatesPositions"])
        self.assertFalse(snapshot["internalDiagnostics"]["mutatesPortfolioLedger"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])

    def test_eo_bd_overnight_gap_through_stop_and_stop_failure_are_detected(self) -> None:
        engine = BlackSwanSimulationEngine()
        position = {**self._position("AAPL", 10000.0), "average_cost": 100.0, "stop_loss": 95.0, "sector": "Technology"}
        scenario = engine.create_scenario(
            scenario_name="Gap through stop",
            scenario_type="overnight_gap",
            created_at="2026-07-09T15:00:00Z",
            market_gap_percent=-0.20,
            sector_gap_shocks={"Technology": -0.10},
        )["latestBlackSwanScenarioRecord"]

        record = engine.run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=self._portfolio_truth(cash=90000.0, equity=100000.0, positions=(position,)), market_data_provider=self._portfolio_market_data())["latestBlackSwanSimulationRecord"]
        row = record["shocked_position_results"][0]

        self.assertLess(row["shocked_price"], 95.0)
        self.assertTrue(row["gap_through_stop"])
        self.assertTrue(record["stop_failure_results"][0]["stopFailure"])
        self.assertGreater(record["stop_failure_results"][0]["stopFailureSeverity"], 30)

    def test_eo_bd_halted_symbol_unexitable_liquidity_collapse_and_spread_explosion(self) -> None:
        engine = BlackSwanSimulationEngine()
        position = {**self._position("AAPL", 10000.0), "average_cost": 100.0, "stop_loss": 95.0}
        scenario = engine.create_scenario(
            scenario_name="Halt and vanish",
            created_at="2026-07-09T15:00:00Z",
            market_gap_percent=-0.25,
            trading_halt_symbols=("AAPL",),
            liquidity_collapse_factor=0.0,
            spread_multiplier=30.0,
        )["latestBlackSwanScenarioRecord"]

        record = engine.run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=self._portfolio_truth(cash=90000.0, equity=100000.0, positions=(position,)), market_data_provider=self._portfolio_market_data(volume=1000.0))["latestBlackSwanSimulationRecord"]

        self.assertEqual(1, record["positions_halted"])
        self.assertEqual(1, record["positions_unexitable"])
        self.assertEqual(0.0, record["liquidity_failure_results"][0]["executableQuantity"])
        self.assertEqual("EXTREME", record["liquidity_failure_results"][0]["marketOrderDanger"])
        self.assertGreater(record["execution_failure_results"][0]["explodedSpread"], 1.0)

    def test_eo_bd_broker_restriction_and_data_blackout_are_represented(self) -> None:
        engine = BlackSwanSimulationEngine()
        position = {**self._position("AAPL", 10000.0), "average_cost": 100.0}
        scenario = engine.create_scenario(
            scenario_name="Restricted blackout",
            created_at="2026-07-09T15:00:00Z",
            broker_restriction_mode="sell_disabled",
            data_outage_symbols=("AAPL",),
        )["latestBlackSwanScenarioRecord"]

        record = engine.run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=self._portfolio_truth(cash=90000.0, equity=100000.0, positions=(position,)), market_data_provider=self._portfolio_market_data())["latestBlackSwanSimulationRecord"]

        self.assertTrue(record["broker_restriction_results"][0]["restricted"])
        self.assertEqual("BLACKOUT", record["data_failure_results"][0]["dataState"])
        self.assertIn("data_blackout:AAPL", record["degraded_inputs"])
        self.assertIn("require_data_quality_repair", record["recommended_actions"])

    def test_eo_bd_correlated_collapse_uses_eo_ah_and_missing_correlation_degrades(self) -> None:
        engine = BlackSwanSimulationEngine()
        positions = (
            {**self._position("AAPL", 10000.0), "average_cost": 100.0, "sector": "Technology"},
            {**self._position("MSFT", 10000.0), "average_cost": 100.0, "sector": "Technology"},
        )
        truth = self._portfolio_truth(cash=80000.0, equity=100000.0, positions=positions)
        scenario = engine.create_scenario(scenario_name="Correlated collapse", created_at="2026-07-09T15:00:00Z", market_gap_percent=-0.25, correlation_to_one_enabled=True)["latestBlackSwanScenarioRecord"]
        eo_ah = {"riskFactorFeed": {"overlapGroups": ({"group_id": "CORR-TECH", "group_type": "same_sector", "members": ("AAPL", "MSFT")},)}}

        with_corr = engine.run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data(), correlation_intelligence=eo_ah)["latestBlackSwanSimulationRecord"]
        without_corr = BlackSwanSimulationEngine().run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())["latestBlackSwanSimulationRecord"]

        self.assertEqual("EO-AH", with_corr["correlation_cluster_impairment"][0]["source"])
        self.assertIn("correlation_proxy_used", without_corr["degraded_inputs"])

    def test_eo_bd_survival_ruin_scores_and_critical_actions_are_deterministic(self) -> None:
        config = BlackSwanSimulationConfig(critical_black_swan_threshold=60.0, ruin_risk_critical_threshold=60.0)
        engine = BlackSwanSimulationEngine(config)
        position = {**self._position("AAPL", 50000.0), "average_cost": 100.0, "stop_loss": 95.0, "sector": "Technology"}
        truth = self._portfolio_truth(cash=50000.0, equity=100000.0, positions=(position,))
        scenario = engine.create_scenario(scenario_name="Critical discontinuity", created_at="2026-07-09T15:00:00Z", market_gap_percent=-0.60, liquidity_collapse_factor=0.0, broker_restriction_mode="sell_disabled")["latestBlackSwanScenarioRecord"]

        first = engine.run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())["latestBlackSwanSimulationRecord"]
        second = BlackSwanSimulationEngine(config).run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())["latestBlackSwanSimulationRecord"]

        self.assertEqual(first["survival_score"], second["survival_score"])
        self.assertEqual(first["ruin_risk_score"], second["ruin_risk_score"])
        self.assertIn(first["black_swan_level"], {"high", "critical"})
        self.assertTrue({"halt_trading", "request_commander_review", "request_risk_review"} & set(first["recommended_actions"]))

    def test_eo_bd_runtime_api_configuration_no_ai_no_uncontrolled_loop(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        snapshot = state["blackSwanSimulationEngine"]
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        self.assertIn("blackSwanSimulationEngine", state)
        self.assertIn("blackSwanSimulationHealth", state["enterpriseHealthMonitor"])
        self.assertIn("/api/black-swan/state", server)
        self.assertTrue(any(item["name"] == "Black Swan Simulation Enabled" for item in state["enterpriseConfigurationRegistry"]["configurationRegistry"]))
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertTrue(snapshot["lawVII"]["terminatesImmediately"])
        self.assertFalse(snapshot["internalDiagnostics"]["createsExecutionRecords"])

    def test_eo_be_monte_carlo_scenario_and_result_records_are_created(self) -> None:
        engine = MonteCarloPortfolioEngine(MonteCarloPortfolioConfig(default_simulation_count=20, default_time_horizon=5))
        truth = self._portfolio_truth(cash=90000.0, equity=100000.0, positions=({**self._position("AAPL", 10000.0), "average_cost": 100.0},))
        scenario = engine.create_scenario(scenario_name="Seeded distribution", created_at="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data(), random_seed=42)["latestMonteCarloScenarioRecord"]
        result = engine.run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())["latestMonteCarloResultRecord"]

        self.assertEqual("MCP-SCEN-000001", scenario["monte_carlo_scenario_id"])
        self.assertEqual("MCP-RESULT-000001", result["monte_carlo_result_id"])
        self.assertEqual(20, result["simulation_count_completed"])
        self.assertIn("terminal_value_percentiles", result)

    def test_eo_be_monte_carlo_does_not_mutate_live_state_and_is_reproducible_by_seed(self) -> None:
        truth = self._portfolio_truth(cash=90000.0, equity=100000.0, positions=({**self._position("AAPL", 10000.0), "average_cost": 100.0},))
        before = json.dumps(truth, sort_keys=True)
        kwargs = {"scenario_name": "Stable seed", "created_at": "2026-07-09T15:00:00Z", "performance_truth": truth, "market_data_provider": self._portfolio_market_data(), "simulation_count": 30, "time_horizon": 6, "random_seed": 77}
        scenario = MonteCarloPortfolioEngine().create_scenario(**kwargs)["latestMonteCarloScenarioRecord"]
        first = MonteCarloPortfolioEngine().run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())
        second = MonteCarloPortfolioEngine().run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())

        self.assertEqual(before, json.dumps(truth, sort_keys=True))
        self.assertEqual(first["latestMonteCarloResultRecord"]["reproducibility_hash"], second["latestMonteCarloResultRecord"]["reproducibility_hash"])
        self.assertEqual(first["latestMonteCarloResultRecord"]["terminal_value_percentiles"], second["latestMonteCarloResultRecord"]["terminal_value_percentiles"])
        self.assertFalse(first["internalDiagnostics"]["mutatesPositions"])

    def test_eo_be_different_seeds_change_distribution_and_bounds_are_enforced(self) -> None:
        config = MonteCarloPortfolioConfig(maximum_simulation_count=25, maximum_time_horizon=7)
        truth = self._portfolio_truth(cash=90000.0, equity=100000.0, positions=({**self._position("AAPL", 10000.0), "average_cost": 100.0},))
        first_engine = MonteCarloPortfolioEngine(config)
        second_engine = MonteCarloPortfolioEngine(config)
        first_scenario = first_engine.create_scenario(scenario_name="Seed one", created_at="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data(), simulation_count=100, time_horizon=30, random_seed=1)["latestMonteCarloScenarioRecord"]
        second_scenario = second_engine.create_scenario(scenario_name="Seed two", created_at="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data(), simulation_count=100, time_horizon=30, random_seed=2)["latestMonteCarloScenarioRecord"]

        first = first_engine.run_simulation(scenario=first_scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())["latestMonteCarloResultRecord"]
        second = second_engine.run_simulation(scenario=second_scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=self._portfolio_market_data())["latestMonteCarloResultRecord"]

        self.assertEqual(25, first_scenario["simulation_count"])
        self.assertEqual(7, first_scenario["time_horizon"])
        self.assertNotEqual(first["terminal_value_percentiles"], second["terminal_value_percentiles"])

    def test_eo_be_correlation_matrix_consumed_and_invalid_matrix_falls_back(self) -> None:
        truth = self._portfolio_truth(cash=80000.0, equity=100000.0, positions=(self._position("AAPL", 10000.0), self._position("MSFT", 10000.0)))
        provider = {"normalizedObjects": {"returnHistory": ({"symbol": "AAPL", "returns": (0.01, 0.02, -0.01, 0.03)}, {"symbol": "MSFT", "returns": (0.011, 0.021, -0.009, 0.029)})}}
        valid_corr = {"latestCorrelationIntelligenceRecord": {"correlation_matrix": {"AAPL": {"AAPL": 1.0, "MSFT": 0.8}, "MSFT": {"AAPL": 0.8, "MSFT": 1.0}}}}
        invalid_corr = {"latestCorrelationIntelligenceRecord": {"correlation_matrix": {"AAPL": {"AAPL": 1.0, "MSFT": 1.5}, "MSFT": {"AAPL": 1.5, "MSFT": 1.0}}}}

        valid = MonteCarloPortfolioEngine().create_scenario(scenario_name="Valid corr", created_at="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=provider, correlation_intelligence=valid_corr)["latestMonteCarloScenarioRecord"]
        fallback = MonteCarloPortfolioEngine().create_scenario(scenario_name="Bad corr", created_at="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=provider, correlation_intelligence=invalid_corr)["latestMonteCarloScenarioRecord"]

        self.assertEqual("EO-AH_correlation_matrix", valid["correlation_model"])
        self.assertEqual(0.8, valid["correlation_assumptions"]["matrix"]["AAPL"]["MSFT"])
        self.assertEqual("conservative_metadata_fallback", fallback["correlation_model"])
        self.assertIn("correlation_matrix_fallback", fallback["correlation_assumptions"]["degradedInputs"])

    def test_eo_be_missing_correlation_and_volatility_mark_degraded_and_lower_confidence(self) -> None:
        truth = self._portfolio_truth(cash=90000.0, equity=100000.0, positions=({**self._position("AAPL", 10000.0), "average_cost": 100.0},))
        scenario = MonteCarloPortfolioEngine().create_scenario(scenario_name="Fallback assumptions", created_at="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider={"normalizedObjects": {"quotes": ()}}, simulation_count=20, time_horizon=5, random_seed=4)["latestMonteCarloScenarioRecord"]
        result = MonteCarloPortfolioEngine().run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider={})["latestMonteCarloResultRecord"]

        self.assertIn("volatility_fallback:AAPL", scenario["correlation_assumptions"]["degradedInputs"])
        self.assertIn("correlation_matrix_fallback", scenario["correlation_assumptions"]["degradedInputs"])
        self.assertLess(result["model_confidence"], 82.0)
        self.assertIn("require_reality_calibration", result["recommended_actions"])

    def test_eo_be_percentiles_probabilities_var_shortfall_and_stop_cascade_are_calculated(self) -> None:
        config = MonteCarloPortfolioConfig(default_loss_threshold=-0.01, default_ruin_threshold=-0.05, default_target_return=0.01)
        truth = self._portfolio_truth(
            cash=80000.0,
            equity=100000.0,
            positions=(
                {**self._position("AAPL", 10000.0), "average_cost": 100.0, "stop_loss": 95.0},
                {**self._position("MSFT", 10000.0), "average_cost": 100.0, "stop_loss": 95.0},
            ),
        )
        provider = {"normalizedObjects": {"returnHistory": ({"symbol": "AAPL", "returns": (0.04, -0.06, 0.02, -0.03, 0.01)}, {"symbol": "MSFT", "returns": (0.035, -0.055, 0.018, -0.025, 0.012)})}}
        scenario = MonteCarloPortfolioEngine(config).create_scenario(scenario_name="Risk metrics", created_at="2026-07-09T15:00:00Z", performance_truth=truth, market_data_provider=provider, simulation_count=40, time_horizon=8, random_seed=9)["latestMonteCarloScenarioRecord"]
        result = MonteCarloPortfolioEngine(config).run_simulation(scenario=scenario, timestamp_utc="2026-07-09T15:01:00Z", performance_truth=truth, market_data_provider=provider)["latestMonteCarloResultRecord"]

        self.assertLessEqual(result["terminal_value_percentiles"]["p05"], result["terminal_value_percentiles"]["p95"])
        self.assertGreaterEqual(result["probability_of_loss"], 0.0)
        self.assertGreaterEqual(result["probability_of_target_achievement"], 0.0)
        self.assertGreaterEqual(result["probability_of_drawdown_threshold_breach"], 0.0)
        self.assertGreaterEqual(result["probability_of_ruin"], 0.0)
        self.assertLessEqual(result["value_at_risk"], result["return_percentiles"]["p50"])
        self.assertLessEqual(result["expected_shortfall"], result["value_at_risk"])
        self.assertIn("probability_of_stop_cascade", result)

    def test_eo_be_benchmark_strategy_feeds_and_runtime_health_are_exposed(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        snapshot = state["monteCarloPortfolioEngine"]
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        self.assertIn("monteCarloPortfolioEngine", state)
        self.assertIn("monteCarloPortfolioHealth", state["enterpriseHealthMonitor"])
        self.assertIn("/api/monte-carlo/state", server)
        self.assertTrue(any(item["name"] == "Monte Carlo Enabled" for item in state["enterpriseConfigurationRegistry"]["configurationRegistry"]))
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertTrue(snapshot["lawVII"]["terminatesImmediately"])
        self.assertFalse(snapshot["internalDiagnostics"]["createsExecutionRecords"])

    def test_eo_ac_portfolio_construction_record_is_created_and_trade_within_limits_approved(self) -> None:
        engine = PortfolioConstructionEngine()
        decision = {"decisionObjectId": "DO-PCON-1", "workflowId": "WF-PCON-1", "symbol": "AAPL", "assetType": "STOCK", "positionSizeRecommendation": 0.02, "riskScore": 0.25, "currentStrategy": "Workflow Proof Strategy"}
        snapshot = engine.evaluate(
            timestamp_utc="2026-07-09T15:00:00Z",
            decision_object=decision,
            performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0),
            market_data_provider=self._portfolio_market_data(),
            strategy_package_manager={"activePackages": ()},
        )

        record = snapshot["latestPortfolioConstructionRecord"]
        self.assertEqual("PCON-000001", record["portfolio_construction_id"])
        self.assertEqual("approve", record["recommended_action"])
        self.assertGreater(record["construction_score"], 75)
        self.assertTrue(snapshot["decisionWorkflowGate"]["executionMayProceed"])

    def test_eo_ac_concentration_sector_strategy_and_cash_rules_are_enforced(self) -> None:
        engine = PortfolioConstructionEngine()
        decision = {"decisionObjectId": "DO-PCON-2", "workflowId": "WF-PCON-2", "symbol": "AAPL", "assetType": "STOCK", "positionSizeRecommendation": 0.05, "riskScore": 0.25, "currentStrategy": "Workflow Proof Strategy"}
        truth = self._portfolio_truth(cash=100000.0, equity=100000.0, positions=(self._position("AAPL", 19000.0),))
        concentrated = engine.evaluate(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=truth, market_data_provider=self._portfolio_market_data(), strategy_package_manager={})
        self.assertEqual("approve_reduced", concentrated["latestPortfolioConstructionRecord"]["recommended_action"])
        self.assertLess(concentrated["latestPortfolioConstructionRecord"]["recommended_notional"], concentrated["latestPortfolioConstructionRecord"]["proposed_notional"])
        self.assertEqual("VIOLATION", concentrated["latestPortfolioConstructionRecord"]["concentration_impact"]["status"])

        sector_truth = self._portfolio_truth(cash=100000.0, equity=100000.0, positions=(self._position("MSFT", 34000.0),))
        sector = engine.evaluate(timestamp_utc="2026-07-09T15:01:00Z", decision_object={**decision, "decisionObjectId": "DO-PCON-3"}, performance_truth=sector_truth, market_data_provider=self._portfolio_market_data(), strategy_package_manager={})
        self.assertEqual("VIOLATION", sector["latestPortfolioConstructionRecord"]["sector_impact"]["status"])

        strategy_truth = self._portfolio_truth(cash=100000.0, equity=100000.0, positions=(self._position("SPY", 34000.0, strategy="Workflow Proof Strategy"),))
        strategy = engine.evaluate(timestamp_utc="2026-07-09T15:02:00Z", decision_object={**decision, "decisionObjectId": "DO-PCON-4"}, performance_truth=strategy_truth, market_data_provider=self._portfolio_market_data(), strategy_package_manager={})
        self.assertEqual("VIOLATION", strategy["latestPortfolioConstructionRecord"]["strategy_impact"]["status"])

        reserve = engine.evaluate(timestamp_utc="2026-07-09T15:03:00Z", decision_object={**decision, "decisionObjectId": "DO-PCON-5"}, performance_truth=self._portfolio_truth(cash=5500.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), strategy_package_manager={})
        self.assertEqual("defer", reserve["latestPortfolioConstructionRecord"]["recommended_action"])
        self.assertIn("minimum_cash_reserve_violation", reserve["latestPortfolioConstructionRecord"]["rejection_reason"])

    def test_eo_ac_duplicate_open_order_and_poor_liquidity_are_visible(self) -> None:
        engine = PortfolioConstructionEngine()
        decision = {"decisionObjectId": "DO-PCON-6", "workflowId": "WF-PCON-6", "symbol": "AAPL", "assetType": "STOCK", "positionSizeRecommendation": 0.02, "riskScore": 0.25, "currentStrategy": "Workflow Proof Strategy"}
        truth = self._portfolio_truth(cash=100000.0, equity=100000.0, orders=({"order_id": "ORD-AAPL-OPEN", "symbol": "AAPL", "status": "QUEUED"},))
        duplicate = engine.evaluate(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=truth, market_data_provider=self._portfolio_market_data(), strategy_package_manager={})
        self.assertTrue(duplicate["latestPortfolioConstructionRecord"]["correlation_impact"]["openOrderDuplicate"])

        poor = engine.evaluate(timestamp_utc="2026-07-09T15:01:00Z", decision_object={**decision, "decisionObjectId": "DO-PCON-7"}, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(spread=5.0, volume=10), strategy_package_manager={})
        self.assertEqual("POOR", poor["latestPortfolioConstructionRecord"]["liquidity_assessment"]["status"])
        self.assertLess(poor["latestPortfolioConstructionRecord"]["construction_score"], duplicate["latestPortfolioConstructionRecord"]["construction_score"])

    def test_eo_ac_missing_data_degrades_record_and_risk_halt_blocks_approval(self) -> None:
        engine = PortfolioConstructionEngine()
        decision = {"decisionObjectId": "DO-PCON-8", "workflowId": "WF-PCON-8", "symbol": "AAPL", "assetType": "STOCK", "positionSizeRecommendation": 0.02, "riskScore": 0.25, "currentStrategy": "Workflow Proof Strategy"}
        degraded = engine.evaluate(timestamp_utc="2026-07-09T15:00:00Z", decision_object=decision, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider={"normalizedObjects": {"quotes": ()}}, strategy_package_manager={})
        self.assertTrue(degraded["latestPortfolioConstructionRecord"]["degraded"])
        self.assertEqual("DEGRADED", degraded["latestPortfolioConstructionRecord"]["liquidity_assessment"]["dataQuality"])

        halted = engine.evaluate(timestamp_utc="2026-07-09T15:01:00Z", decision_object={**decision, "decisionObjectId": "DO-PCON-9"}, performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0), market_data_provider=self._portfolio_market_data(), strategy_package_manager={}, enterprise_operational_guardrails={"readinessState": "Emergency Halt"})
        self.assertEqual("reject", halted["latestPortfolioConstructionRecord"]["recommended_action"])
        self.assertFalse(halted["decisionWorkflowGate"]["executionMayProceed"])

    def test_eo_ac_score_is_deterministic_and_decision_object_is_not_mutated(self) -> None:
        decision = {"decisionObjectId": "DO-PCON-10", "workflowId": "WF-PCON-10", "symbol": "AAPL", "assetType": "STOCK", "positionSizeRecommendation": 0.02, "riskScore": 0.25, "currentStrategy": "Workflow Proof Strategy"}
        original = dict(decision)
        kwargs = {
            "timestamp_utc": "2026-07-09T15:00:00Z",
            "decision_object": decision,
            "performance_truth": self._portfolio_truth(cash=100000.0, equity=100000.0),
            "market_data_provider": self._portfolio_market_data(),
            "strategy_package_manager": {},
        }
        first = PortfolioConstructionEngine().evaluate(**kwargs)
        second = PortfolioConstructionEngine().evaluate(**kwargs)
        self.assertEqual(first["latestPortfolioConstructionRecord"]["construction_score"], second["latestPortfolioConstructionRecord"]["construction_score"])
        self.assertEqual(original, decision)
        self.assertFalse(first["internalDiagnostics"]["mutatesDecisionObjects"])
        self.assertEqual(0, first["lawVIII"]["routineAiInvocations"])

    def test_eo_ac_runtime_exposes_gate_and_commander_override_does_not_bypass_risk_halt(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        self.assertIn("portfolioConstructionEngine", state)
        self.assertIn("decisionWorkflowGate", state["portfolioConstructionEngine"])
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("/api/portfolio-construction/state", server)

        engine = PortfolioConstructionEngine()
        override = engine.evaluate(
            timestamp_utc="2026-07-09T15:00:00Z",
            decision_object={"decisionObjectId": "DO-PCON-11", "workflowId": "WF-PCON-11", "symbol": "AAPL", "assetType": "STOCK", "positionSizeRecommendation": 0.02, "riskScore": 0.25, "currentStrategy": "Workflow Proof Strategy"},
            performance_truth=self._portfolio_truth(cash=100000.0, equity=100000.0),
            market_data_provider=self._portfolio_market_data(),
            strategy_package_manager={},
            enterprise_operational_guardrails={"readinessState": "Emergency Halt"},
            commander_override={"overrideId": "CMD-OVR-PCON-001", "reason": "Commander review test"},
        )
        self.assertTrue(override["decisionWorkflowGate"]["commanderOverrideRecorded"])
        self.assertFalse(override["decisionWorkflowGate"]["executionMayProceed"])
        self.assertTrue(override["decisionWorkflowGate"]["brokerRulesStillRequired"])

    def test_decision_laboratory_replays_completed_workflow_and_preserves_truth(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="CLOSED")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["performanceTruthEngine"]["orderLedger"]) == 1,
                timeout=2.0,
            )
            runtime.halt_paper_self_training()
            workflow_id = state["performanceTruthEngine"]["orderLedger"][0]["workflow_id"]
            truth_hashes = tuple(item["hash"] for item in state["performanceTruthEngine"]["orderLedger"])

            state = runtime.start_decision_lab_replay(workflow_id)
            lab = state["decisionLaboratory"]
            self.assertEqual("Decision Laboratory", lab["laboratoryName"])
            self.assertEqual("OE-011D", lab["engineeringOrder"])
            self.assertTrue(lab["productionHistoryImmutable"])
            replay = next(item for item in lab["workflowReplay"] if item["workflowId"] == workflow_id)
            self.assertEqual(workflow_id, replay["workflowId"])
            self.assertTrue(replay["decisionObjectId"].startswith("DO-"))
            self.assertEqual(("Seeker", "Analyst", "Risk", "Trader", "Historian"), tuple(replay["officeSequence"]))
            decision = next(item for item in lab["decisionObjectReplay"] if item["workflowId"] == workflow_id)
            self.assertEqual((1, 2, 3, 4, 5), tuple(decision["revisionFlow"]))
            offices = next(item for item in lab["officeContributionReplay"] if item["workflowId"] == workflow_id)
            self.assertEqual(("Seeker", "Analyst", "Risk", "Trader", "Historian"), tuple(item["office"] for item in offices["offices"]))
            self.assertEqual(1, len(lab["replaySessions"]))

            replay_id = lab["replaySessions"][0]["replay_id"]
            state = runtime.control_decision_lab_replay(replay_id, "Step Forward")
            session = state["decisionLaboratory"]["replaySessions"][0]
            self.assertEqual(2, session["current_revision"])
            self.assertEqual("Analyst", session["current_stage"])

            after_hashes = tuple(item["hash"] for item in state["performanceTruthEngine"]["orderLedger"])
            self.assertEqual(truth_hashes, after_hashes)
            self.assertEqual(0, state["decisionLaboratory"]["metrics"]["productionMutationCount"])
            self.assertEqual("IMMUTABLE_LEDGER", state["decisionLaboratory"]["integration"]["tradeLedger"])
        finally:
            self._restore_env(previous)

    def test_decision_laboratory_experiments_compare_without_modifying_production_history(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true", ARGOS_BROKER_SIM_MARKET_SESSION="CLOSED")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["performanceTruthEngine"]["orderLedger"]) == 1,
                timeout=2.0,
            )
            runtime.halt_paper_self_training()
            workflow_id = state["performanceTruthEngine"]["orderLedger"][0]["workflow_id"]
            truth_counts = (
                len(state["performanceTruthEngine"]["orderLedger"]),
                len(state["performanceTruthEngine"]["portfolioLedger"]),
                len(state["performanceTruthEngine"]["decisionObjectOutcomes"]),
            )
            truth_hashes = tuple(item["hash"] for item in state["performanceTruthEngine"]["orderLedger"])

            state = runtime.create_decision_lab_experiment(
                workflow_id,
                {"confidence": 0.81, "stopLoss": 93.25, "positionSizeRecommendation": 0.04, "expectedReturn": 0.05},
            )
            lab = state["decisionLaboratory"]
            self.assertEqual(1, lab["metrics"]["experimentCount"])
            experiment = lab["experiments"][0]
            self.assertEqual(workflow_id, experiment["original_workflow_id"])
            self.assertTrue(experiment["experiment_decision_object"]["decisionObjectId"].endswith("-EXP-001"))
            self.assertEqual(0.81, experiment["experiment_decision_object"]["confidence"])
            self.assertEqual(1, len(lab["decisionComparisons"]))
            self.assertEqual(1, len(lab["performanceComparisons"]))
            self.assertEqual(1, len(lab["historianReports"]))
            self.assertFalse(lab["historianReports"][0]["productionStrategyModified"])
            self.assertTrue(any(node["nodeId"] == experiment["experiment_id"] for node in lab["decisionTree"]))
            self.assertTrue(all(item["immutable_production_preserved"] for item in lab["experimentAudit"]))

            updated_counts = (
                len(state["performanceTruthEngine"]["orderLedger"]),
                len(state["performanceTruthEngine"]["portfolioLedger"]),
                len(state["performanceTruthEngine"]["decisionObjectOutcomes"]),
            )
            self.assertEqual(truth_counts, updated_counts)
            self.assertEqual(truth_hashes, tuple(item["hash"] for item in state["performanceTruthEngine"]["orderLedger"]))

            searched = runtime.decision_laboratory_state("AAPL")
            self.assertTrue(searched["decisionLaboratory"]["searchResults"])
        finally:
            self._restore_env(previous)

    def test_decision_laboratory_ui_and_endpoints_are_exposed(self) -> None:
        runtime = create_runtime()
        state = runtime.decision_laboratory_state()
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        self.assertIn("decisionLaboratory", state)
        self.assertIn("Decision Laboratory", html)
        self.assertIn("dl-start-replay", html)
        self.assertIn("dl-create-experiment", html)
        self.assertIn("renderDecisionLaboratory", js)
        self.assertIn("createDecisionLabExperiment", js)
        self.assertIn("/api/decision-laboratory/state", server)
        self.assertIn("/api/decision-laboratory/experiment", server)

    def test_oe100_command_bridge_is_default_commander_surface(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        css = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "styles.css").read_text(encoding="utf-8")

        self.assertIn('id="command-bridge"', html)
        self.assertIn('id="engineering-mode" class="engineering-mode hidden"', html)
        self.assertIn("body:not(.engineering-open) .engineering-shell", css)
        self.assertIn(".engineering-mode.hidden { display: none; }", css)
        self.assertIn("function renderCommandBridge()", js)
        self.assertIn("bridgeWorkflow()", js)
        self.assertIn("bridgePortfolio()", js)
        self.assertIn("bridgeLatestDecision()", js)

        for element_id in (
            "capital-portfolio-value",
            "capital-today-return-usd",
            "capital-today-return-percent",
            "capital-total-return-percent",
            "capital-benchmark-return",
            "capital-alpha",
            "capital-cash",
            "capital-exposure",
            "capital-max-drawdown",
            "capital-trust-posture",
            "capital-equity-chart",
            "capital-empty-state",
            "credit-burn-heartbeat",
            "mission-scorecards",
            "bridge-baton",
            "bridge-decision",
            "bridge-office-hud",
        ):
            self.assertIn(f'id="{element_id}"', html)
            self.assertIn(f'("{element_id}")', js)

        self.assertIn("function drawCapitalEquityChart()", js)
        self.assertIn("function bridgeBenchmark()", js)
        self.assertIn("function bridgeCreditMetrics()", js)
        self.assertIn(".capital-main-grid", css)
        self.assertIn(".capital-heartbeat-strip", css)

    def test_oe100_bridge_buttons_are_wired_to_live_endpoints(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        expected = {
            "bridge-start-paper": "/api/paper/start",
            "bridge-halt": "/api/paper/halt",
            "bridge-pause": "/api/bridge/pause",
            "bridge-step": "/api/bridge/step",
        }
        for button_id, endpoint in expected.items():
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
            self.assertIn(endpoint, js)
            self.assertIn(endpoint, server)

        self.assertNotIn('id="bridge-engineering"', html)
        self.assertIn("/api/cnac/briefing", js)
        self.assertIn("requestCommanderBriefing", js)
        self.assertIn("morning_readiness", js)
        for button_id in ("bridge-replay", "bridge-lab", "bridge-commander-report", "system-health-report"):
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)

    def test_oe100_bridge_idle_state_is_clean_and_traceable(self) -> None:
        runtime = create_runtime()

        state = runtime.state()

        self.assertFalse(state["control"]["paper_trading_active"])
        self.assertIsNone(state["workflowRuntimeMonitor"]["activeWorkflow"])
        self.assertEqual("VALID", state["workflowRuntimeMonitor"]["tokenIntegrity"]["status"])
        self.assertEqual(0, state["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"])
        self.assertIn("strategyPerformanceConsole", state)
        self.assertIn("performanceTruthEngine", state)

    def test_oe100a_capital_first_bridge_uses_truth_and_cost_sources(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("Capital Performance", html)
        self.assertIn("Credit Expenditure", html)
        self.assertIn("Mission Scorecards", html)
        self.assertIn("Awaiting portfolio truth history.", html)
        self.assertIn("state.performanceTruthEngine", js)
        self.assertIn("state.apiRuntimeMonitor", js)
        self.assertIn("state.creditGovernor", js)
        self.assertIn("total_equity", js)
        self.assertIn("benchmark_return", js)
        self.assertIn("currentCostBurnRateUsdPerHour", js)
        self.assertIn("costPerWorkflow", js)
        self.assertIn("budgetRemaining", js)

    def test_oe100a_performance_truth_history_drives_capital_metrics(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["performanceTruthEngine"]["portfolioLedger"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            truth = state["performanceTruthEngine"]
            latest = truth["portfolioLedger"][-1]
            calculated = truth["calculations"]["portfolio"]
            self.assertEqual(latest["total_equity"], calculated["portfolioValue"])
            self.assertIn("SPY", {item["benchmark"] for item in truth["benchmarkHistory"]})
            self.assertIn("alpha", latest)
            self.assertIn("drawdown", latest)
            self.assertEqual("Performance Truth Engine", truth["engineName"])
        finally:
            self._restore_env(previous)

    def test_oe101_office_hud_buttons_navigate_to_subcommand_bridges(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("OFFICE_BRIDGE_VIEWS", js)
        self.assertIn("data-bridge-view", js)
        self.assertIn("navigateBridge(button.dataset.bridgeView)", js)
        self.assertIn('Executive: "executive_bridge"', js)
        self.assertIn('Seeker: "seeker_bridge"', js)
        self.assertIn('Risk: "risk_bridge"', js)
        self.assertIn('Trader: "trader_bridge"', js)
        self.assertIn('Historian: "historian_bridge"', js)
        self.assertIn('Librarian: "librarian_bridge"', js)
        self.assertIn('Academy: "academy_bridge"', js)
        for office in ("Analyst",):
            self.assertIn(f'{office}: "{office.lower()}_bridge_placeholder"', js)

        self.assertIn('id="executive-subcommand-bridge"', html)
        self.assertIn('id="seeker-subcommand-bridge"', html)
        self.assertIn('id="risk-subcommand-bridge"', html)
        self.assertIn('id="trader-subcommand-bridge"', html)
        self.assertIn('id="historian-subcommand-bridge"', html)
        self.assertIn('id="librarian-subcommand-bridge"', html)
        self.assertIn('id="academy-subcommand-bridge"', html)
        self.assertIn('id="subcommand-placeholder"', html)

    def test_oe101_executive_bridge_renders_operational_sections(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        css = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("Executive Subcommand Bridge", html)
        for element_id in (
            "exec-coordination",
            "exec-health-matrix",
            "exec-workflow-operations",
            "exec-directives",
            "exec-performance",
            "exec-alerts",
            "exec-office-nav",
        ):
            self.assertIn(f'id="{element_id}"', html)
            self.assertIn(f'("{element_id}")', js)
        self.assertIn("function renderExecutiveBridge()", js)
        self.assertIn("performanceTruthEngine", js)
        self.assertIn('source: "TRUTH ENGINE"', js)
        self.assertIn(".executive-grid", css)
        self.assertIn(".subcommand-bridge.hidden", css)

    def test_oe101_bridge_commands_are_real_or_explicitly_unavailable(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        expected = {
            "executive-return-command": "command_bridge",
            "placeholder-return-command": "command_bridge",
            "exec-start-paper": "/api/paper/start",
            "exec-halt": "/api/paper/halt",
            "exec-pause": "/api/bridge/pause",
            "exec-open-lab": "openBridgeLab",
            "exec-open-engineering": "toggleEngineeringMode",
        }
        for button_id, target in expected.items():
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
            self.assertIn(target, js)
        self.assertIn("/api/bridge/pause", server)
        self.assertIn("Resume unavailable until paused workflow resume endpoint exists.", html)
        self.assertNotIn('id="exec-resume"', html)

    def test_oe101_executive_bridge_uses_live_state_sources(self) -> None:
        runtime = create_runtime()

        state = runtime.state()

        self.assertIn("workflowRuntimeMonitor", state)
        self.assertIn("workflowOrchestrator", state)
        self.assertIn("apiRuntimeMonitor", state)
        self.assertIn("apiExecutionGateway", state)
        self.assertIn("performanceTruthEngine", state)
        self.assertIn("strategyPerformanceConsole", state)
        self.assertEqual("VALID", state["workflowRuntimeMonitor"]["tokenIntegrity"]["status"])

    def test_oe101_only_current_token_owner_can_render_active_in_office_matrix(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0.05", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: item["workflowRuntimeMonitor"]["activeWorkflow"] is not None,
                timeout=2.0,
            )
            active = state["workflowRuntimeMonitor"]["activeWorkflow"]
            runtime.halt_paper_self_training()

            self.assertIn(active["currentOwner"], {"Seeker", "Analyst", "Risk", "Trader", "Historian"})
            self.assertEqual("VALID", state["workflowRuntimeMonitor"]["tokenIntegrity"]["status"])
            self.assertEqual(1, len([office for office in ("Executive", "Seeker", "Analyst", "Risk", "Trader", "Historian", "Librarian", "Academy") if office == active["currentOwner"]]))
        finally:
            self._restore_env(previous)

    def test_oe101_recent_completed_workflows_and_directives_are_available(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            self.assertTrue(state["workflowRuntimeMonitor"]["recentCompletedWorkflows"])
            self.assertIn("decisionObjectPanel", state["strategyPerformanceConsole"])
            self.assertIn("tradeLedger", state["performanceTruthEngine"])
        finally:
            self._restore_env(previous)

    def test_oe102_seeker_bridge_renders_reconnaissance_sections(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        css = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("Seeker Subcommand Bridge", html)
        self.assertIn('Seeker: "seeker_bridge"', js)
        self.assertIn("function renderSeekerBridge()", js)
        self.assertIn("function seekerCandidates()", js)
        for element_id in (
            "seeker-mission-panel",
            "seeker-radar",
            "seeker-candidate-queue",
            "seeker-current-decision",
            "seeker-signal-sources",
            "seeker-discovery-metrics",
            "seeker-market-intelligence",
            "seeker-office-health",
            "seeker-promotions",
            "seeker-office-nav",
        ):
            self.assertIn(f'id="{element_id}"', html)
            self.assertIn(f'("{element_id}")', js)
        for element_id in (
            "seeker-signal-health",
            "seeker-current-objective",
            "seeker-radar-filter",
        ):
            self.assertIn(f'id="{element_id}"', html)
            self.assertIn(f'("{element_id}")', js)
        self.assertIn(".discovery-radar", css)
        self.assertIn(".radar-candidate", css)
        self.assertIn(".radar-filter", css)
        self.assertIn("function seekerMarketIntelligence(", js)
        self.assertIn("function seekerHealth(", js)
        self.assertIn("function filteredSeekerCandidates(", js)

    def test_oe102_seeker_bridge_matches_intelligence_mission_contract(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        for phrase in (
            "Discovery Radar",
            "Market Intelligence",
            "Discovery Metrics",
            "Recent Promotions",
            "Office Health",
            "Current Decision Object",
            "Return to Executive Bridge",
        ):
            self.assertIn(phrase, html)
        for phrase in (
            "Candidates Scanned",
            "Candidates Qualified",
            "Average Discovery Confidence",
            "Signal Sources Active",
            "Market Trend",
            "Sector Leadership",
            "Gateway Status",
            "Dormant/Active",
            "Awaiting workflow assignment. Signal sources healthy. Discovery systems standing by. No active candidates.",
        ):
            self.assertIn(phrase, js)
        self.assertIn("activeSeekerFilter", js)
        self.assertIn("renderSeekerBridge()", js)

    def test_oe102_seeker_commands_are_real_and_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        expected = {
            "seeker-pause": "/api/bridge/pause",
            "seeker-resume": "/api/bridge/resume",
            "seeker-replay": "startLatestBridgeReplay",
            "seeker-open-lab": "openBridgeLab",
            "seeker-open-executive": "executive_bridge",
            "seeker-open-engineering": "toggleEngineeringMode",
            "seeker-return-executive": "executive_bridge",
        }
        for button_id, target in expected.items():
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
            self.assertIn(target, js)
        self.assertIn("/api/bridge/resume", server)
        runtime = create_runtime()
        self.assertIn("Workflow resume requested", runtime.resume_after_pause()["activity"][0]["message"])

    def test_oe102_seeker_bridge_idle_state_is_intentional(self) -> None:
        runtime = create_runtime()

        state = runtime.state()

        self.assertFalse(state["control"]["paper_trading_active"])
        self.assertIsNone(state["workflowRuntimeMonitor"]["activeWorkflow"])
        self.assertEqual("VALID", state["workflowRuntimeMonitor"]["tokenIntegrity"]["status"])
        self.assertEqual(0, len(state["strategyPerformanceConsole"]["decisionObjectEvolution"]))
        self.assertEqual(0, len(state["performanceTruthEngine"]["tradeLedger"]))

    def test_oe102_seeker_radar_has_candidates_after_paper_workflow(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["strategyPerformanceConsole"]["decisionObjectPanel"]["decisionObjectId"])
                and bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            decision = state["strategyPerformanceConsole"]["decisionObjectPanel"]
            self.assertTrue(decision["decisionObjectId"].startswith("DO-"))
            self.assertGreaterEqual(decision["evidenceCount"], 1)
            self.assertTrue(state["strategyPerformanceConsole"]["decisionObjectEvolution"])
            self.assertTrue(state["workflowRuntimeMonitor"]["recentCompletedWorkflows"])
        finally:
            self._restore_env(previous)

    def test_oe102_seeker_navigation_no_long_engineering_default(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="seeker-subcommand-bridge" class="subcommand-bridge seeker-bridge hidden"', html)
        self.assertIn("navigateBridge(\"executive_bridge\")", js)
        self.assertIn("seekerSignalSources()", js)
        self.assertNotIn('id="seeker-debug"', html)

    def test_oe104_risk_bridge_renders_capital_protection_sections(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        css = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("Risk Office Subcommand Bridge", html)
        self.assertIn("Capital Protection Operations", html)
        self.assertIn('Risk: "risk_bridge"', js)
        self.assertIn("function renderRiskBridge()", js)
        self.assertIn("function riskHeatMap(", js)
        for element_id in (
            "risk-heat-map",
            "risk-current-decision",
            "risk-assessment",
            "risk-capital-exposure",
            "risk-rule-validation",
            "risk-historical-comparison",
            "risk-recent-decisions",
            "risk-office-health",
            "risk-office-nav",
        ):
            self.assertIn(f'id="{element_id}"', html)
            self.assertIn(f'("{element_id}")', js)
        self.assertIn(".risk-heat-map", css)
        self.assertIn(".risk-heat-cell.critical", css)
        self.assertIn(".risk-grid", css)

    def test_oe104_risk_bridge_matches_capital_defense_contract(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        for phrase in (
            "Risk Heat Map",
            "Current Decision Object",
            "Risk Assessment",
            "Capital Exposure",
            "Risk Rule Validation",
            "Historical Risk Comparison",
            "Recent Risk Decisions",
            "Office Health",
            "Return to Executive Bridge",
        ):
            self.assertIn(phrase, html)
        for phrase in (
            "Market Risk",
            "Sector Risk",
            "Volatility Risk",
            "Liquidity Risk",
            "Concentration Risk",
            "Correlation Risk",
            "Macro Risk",
            "Gap Risk",
            "Event Risk",
            "Execution Risk",
            "Tail Risk",
            "Confidence Risk",
            "Expected Downside",
            "Reward/Risk Ratio",
            "Capital At Risk",
            "Risk Recommendation",
            "Maximum Position Size",
            "Risk/Reward Minimum",
            "Awaiting Decision Object. Risk systems standing by. Enterprise capital protected.",
        ):
            self.assertIn(phrase, js)
        self.assertNotIn('id="risk-debug"', html)
        self.assertNotIn("Risk model internals", html)
        self.assertNotIn("Raw JSON", html)

    def test_oe104_risk_commands_are_real_and_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        expected = {
            "risk-pause": "/api/bridge/pause",
            "risk-resume": "/api/bridge/resume",
            "risk-replay": "startLatestBridgeReplay",
            "risk-open-lab": "openBridgeLab",
            "risk-open-executive": "executive_bridge",
            "risk-open-engineering": "toggleEngineeringMode",
            "risk-return-executive": "executive_bridge",
        }
        for button_id, target in expected.items():
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
            self.assertIn(target, js)
        self.assertIn("/api/bridge/pause", server)
        self.assertIn("/api/bridge/resume", server)
        self.assertNotIn('id="risk-approve"', html)
        self.assertNotIn('id="risk-reject"', html)

    def test_oe104_risk_bridge_updates_after_paper_workflow(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05", ARGOS_BROKER_SIM_MARKET_SESSION="REGULAR")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["strategyPerformanceConsole"]["decisionObjectPanel"]["decisionObjectId"])
                and bool(item["performanceTruthEngine"]["portfolioLedger"]),
                timeout=5.0,
            )
            runtime.halt_paper_self_training()

            decision = state["strategyPerformanceConsole"]["decisionObjectPanel"]
            truth = state["performanceTruthEngine"]
            self.assertTrue(decision["decisionObjectId"].startswith("DO-"))
            self.assertIn("riskScore", decision)
            self.assertTrue(truth["portfolioLedger"])
            self.assertIn("workflowRuntimeMonitor", state)
            self.assertIn("decisionLaboratory", state)
            self.assertIn("apiExecutionGateway", state)
        finally:
            self._restore_env(previous)

    def test_oe105_trader_bridge_renders_execution_sections(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        css = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("Trader Office Subcommand Bridge", html)
        self.assertIn("Execution Control Center", html)
        self.assertIn('Trader: "trader_bridge"', js)
        self.assertIn("function renderTraderBridge()", js)
        self.assertIn("function traderExecutionQueue(", js)
        for element_id in (
            "trader-execution-queue",
            "trader-order-lifecycle",
            "trader-current-decision",
            "trader-position-management",
            "trader-execution-metrics",
            "trader-completed-orders",
            "trader-office-health",
            "trader-office-nav",
        ):
            self.assertIn(f'id="{element_id}"', html)
            self.assertIn(f'("{element_id}")', js)
        self.assertIn(".order-lifecycle", css)
        self.assertIn(".lifecycle-stage.active", css)
        self.assertIn(".execution-queue", css)

    def test_oe105_trader_bridge_matches_execution_mission_contract(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        for phrase in (
            "Execution Queue",
            "Order Lifecycle",
            "Current Decision Object",
            "Position Management",
            "Execution Metrics",
            "Completed Orders",
            "Office Health",
            "Return to Executive Bridge",
        ):
            self.assertIn(phrase, html)
        for phrase in (
            "Decision Approved",
            "Order Created",
            "Order Submitted",
            "Acknowledged",
            "Partially Filled",
            "Filled",
            "Position Open",
            "Position Managed",
            "Position Closed",
            "Average Slippage",
            "Average Fill Time",
            "Execution Accuracy",
            "Orders Submitted",
            "Broker Health",
            "Awaiting approved Decision Object. Execution systems ready. No pending orders. Broker healthy.",
        ):
            self.assertIn(phrase, js)
        self.assertNotIn('id="trader-debug"', html)
        self.assertNotIn("Order JSON", html)
        self.assertNotIn("Execution traces", html)

    def test_oe105_trader_commands_are_real_and_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        expected = {
            "trader-pause": "/api/bridge/pause",
            "trader-resume": "/api/bridge/resume",
            "trader-cancel-pending": "/api/trader/cancel-pending-orders",
            "trader-replay": "startLatestBridgeReplay",
            "trader-open-lab": "openBridgeLab",
            "trader-open-executive": "executive_bridge",
            "trader-open-engineering": "toggleEngineeringMode",
            "trader-return-executive": "executive_bridge",
        }
        for button_id, target in expected.items():
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
            self.assertIn(target, js)
        self.assertIn("/api/trader/cancel-pending-orders", server)
        runtime = create_runtime()
        self.assertIn("Pending execution orders cancellation requested", runtime.cancel_pending_orders()["activity"][0]["message"])
        self.assertNotIn('id="trader-submit-order"', html)
        self.assertNotIn('id="trader-force-fill"', html)

    def test_oe105_trader_bridge_updates_after_paper_workflow(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05", ARGOS_BROKER_SIM_MARKET_SESSION="CLOSED")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["strategyPerformanceConsole"]["decisionObjectPanel"]["decisionObjectId"])
                and bool(item["performanceTruthEngine"]["orderLedger"]),
                timeout=5.0,
            )
            runtime.halt_paper_self_training()

            decision = state["strategyPerformanceConsole"]["decisionObjectPanel"]
            self.assertTrue(decision["decisionObjectId"].startswith("DO-"))
            self.assertTrue(state["performanceTruthEngine"]["orderLedger"])
            self.assertIn("currentPositions", state["strategyPerformanceConsole"])
            self.assertIn("tradeLedger", state["performanceTruthEngine"])
            self.assertIn("apiExecutionGateway", state)
        finally:
            self._restore_env(previous)

    def test_oe106_historian_bridge_renders_learning_sections(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        css = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("Historian Office Subcommand Bridge", html)
        self.assertIn("Enterprise Learning Center", html)
        self.assertIn('Historian: "historian_bridge"', js)
        self.assertIn("function renderHistorianBridge()", js)
        self.assertIn("function historianTimelineEntries(", js)
        for element_id in (
            "historian-learning-timeline",
            "historian-decision-evolution",
            "historian-performance-truth",
            "historian-lessons",
            "historian-prompt-evolution",
            "historian-strategy-evolution",
            "historian-recommendations",
            "historian-learning-metrics",
            "historian-office-health",
            "historian-office-nav",
        ):
            self.assertIn(f'id="{element_id}"', html)
            self.assertIn(f'("{element_id}")', js)
        self.assertIn(".learning-timeline", css)
        self.assertIn(".learning-timeline-stage.complete", css)
        self.assertIn(".historian-record", css)

    def test_oe106_historian_bridge_matches_learning_mission_contract(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        for phrase in (
            "Enterprise Learning Timeline",
            "Decision Object Evolution",
            "Performance Truth Analysis",
            "Lessons Learned",
            "Prompt Evolution",
            "Strategy Evolution",
            "Historian Recommendations",
            "Learning Metrics",
            "Office Health",
            "Return to Executive Bridge",
        ):
            self.assertIn(phrase, html)
        for phrase in (
            "Completed Workflow",
            "Performance Truth Recorded",
            "Decision Laboratory Replay",
            "Historian Analysis",
            "Lesson Learned",
            "Prompt Recommendation",
            "Strategy Recommendation",
            "Commander Review",
            "Prediction Accuracy",
            "Confidence Calibration",
            "Average Prediction Error",
            "Expected vs Actual Return",
            "Decision Quality Trend",
            "Momentum-only trades underperform.",
            "Risk reduction improved returns.",
            "Prompt Version 14 outperformed Version 12.",
            "Improve Analyst confidence calibration.",
            "Awaiting completed workflows. Enterprise memory healthy. No learning cycle currently running. Ready for analysis.",
        ):
            self.assertIn(phrase, js)
        self.assertNotIn('id="historian-debug"', html)
        self.assertNotIn("Prompt JSON", html)
        self.assertNotIn("Raw ledgers", html)
        self.assertNotIn("Hash validation", html)

    def test_oe106_historian_commands_are_real_and_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        expected = {
            "historian-replay-workflow": "startLatestBridgeReplay",
            "historian-open-lab": "openBridgeLab",
            "historian-generate-report": "/api/historian/generate-learning-report",
            "historian-compare-prompts": "/api/historian/compare-prompt-versions",
            "historian-compare-strategies": "/api/historian/compare-strategies",
            "historian-open-executive": "executive_bridge",
            "historian-open-engineering": "toggleEngineeringMode",
            "historian-return-executive": "executive_bridge",
        }
        for button_id, target in expected.items():
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
            self.assertIn(target, js)
        self.assertIn("/api/historian/generate-learning-report", server)
        self.assertIn("/api/historian/compare-prompt-versions", server)
        self.assertIn("/api/historian/compare-strategies", server)
        runtime = create_runtime()
        self.assertIn("Historian learning report generated", runtime.generate_learning_report()["activity"][0]["message"])
        self.assertIn("Prompt versions compared", runtime.compare_prompt_versions()["activity"][0]["message"])
        self.assertIn("Strategies compared", runtime.compare_strategies()["activity"][0]["message"])
        self.assertNotIn('id="historian-deploy-prompt"', html)
        self.assertNotIn('id="historian-auto-promote"', html)

    def test_oe106_historian_bridge_updates_after_paper_workflow(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"])
                and bool(item["strategyPerformanceConsole"]["decisionObjectEvolution"])
                and bool(item["performanceTruthEngine"]["portfolioLedger"]),
                timeout=5.0,
            )
            runtime.halt_paper_self_training()

            self.assertTrue(state["workflowRuntimeMonitor"]["recentCompletedWorkflows"])
            self.assertTrue(state["strategyPerformanceConsole"]["decisionObjectEvolution"])
            self.assertTrue(state["performanceTruthEngine"]["portfolioLedger"])
            self.assertIn("decisionLaboratory", state)
            self.assertIn("promptContract", state)
            self.assertIn("strategyPerformanceConsole", state)
        finally:
            self._restore_env(previous)

    def test_oe107_librarian_bridge_renders_knowledge_sections(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        css = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("Librarian Office Subcommand Bridge", html)
        self.assertIn("Enterprise Knowledge Center", html)
        self.assertIn('Librarian: "librarian_bridge"', js)
        self.assertIn("function renderLibrarianBridge()", js)
        self.assertIn("function librarianKnowledgeItems()", js)
        for element_id in (
            "librarian-search-input",
            "librarian-knowledge-graph",
            "librarian-enterprise-library",
            "librarian-reference-material",
            "librarian-decision-archive",
            "librarian-prompt-archive",
            "librarian-strategy-archive",
            "librarian-knowledge-metrics",
            "librarian-office-health",
            "librarian-office-nav",
        ):
            self.assertIn(f'id="{element_id}"', html)
            self.assertIn(f'("{element_id}")', js)
        self.assertIn(".knowledge-graph", css)
        self.assertIn(".knowledge-node.populated", css)
        self.assertIn(".library-shelf-grid", css)

    def test_oe107_librarian_bridge_matches_knowledge_retrieval_contract(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        for phrase in (
            "Knowledge Search",
            "Enterprise Knowledge Graph",
            "Enterprise Library",
            "Reference Material",
            "Decision Archive",
            "Prompt Archive",
            "Strategy Archive",
            "Knowledge Metrics",
            "Return to Executive Bridge",
        ):
            self.assertIn(phrase, html)
        for phrase in (
            "Ticker",
            "Workflow",
            "Decision Object",
            "Prompt",
            "Strategy",
            "Office",
            "Trade",
            "Lesson",
            "Market Regime",
            "Most referenced",
            "Most successful",
            "Most related",
            "Decision Objects",
            "Performance Truth Records",
            "Prompt Versions",
            "Historian Lessons",
            "Commander Doctrine",
            "Operations Engineering Orders",
            "Knowledge systems healthy. Awaiting search. Enterprise library available. Ready to answer questions.",
        ):
            self.assertIn(phrase, html + js)
        self.assertNotIn('id="librarian-debug"', html)
        self.assertNotIn("Vector index internals", html)
        self.assertNotIn("Embedding diagnostics", html)
        self.assertNotIn("Raw JSON", html)

    def test_oe107_librarian_search_and_commands_are_real_and_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        expected = {
            "librarian-search-button": "renderLibrarianBridge",
            "librarian-replay": "startLatestBridgeReplay",
            "librarian-open-lab": "openBridgeLab",
            "librarian-open-historian": "historian_bridge",
            "librarian-open-executive": "executive_bridge",
            "librarian-open-engineering": "toggleEngineeringMode",
            "librarian-return-executive": "executive_bridge",
        }
        for button_id, target in expected.items():
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
            self.assertIn(target, js)
        self.assertIn("activeLibrarianQuery", js)
        self.assertIn("librarianMatchesQuery", js)
        self.assertIn("data-librarian-query", js)
        self.assertNotIn('id="librarian-create-recommendation"', html)
        self.assertNotIn('id="librarian-modify-decision"', html)

    def test_oe107_librarian_bridge_updates_after_paper_workflow(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["strategyPerformanceConsole"]["decisionObjectEvolution"])
                and bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"])
                and bool(item["performanceTruthEngine"]["portfolioLedger"]),
                timeout=5.0,
            )
            runtime.halt_paper_self_training()

            self.assertTrue(state["strategyPerformanceConsole"]["decisionObjectEvolution"])
            self.assertTrue(state["workflowRuntimeMonitor"]["recentCompletedWorkflows"])
            self.assertTrue(state["performanceTruthEngine"]["portfolioLedger"])
            self.assertIn("promptContract", state)
            self.assertIn("decisionLaboratory", state)
            self.assertIn("strategyPerformanceConsole", state)
        finally:
            self._restore_env(previous)

    def test_oe108_academy_bridge_renders_development_sections(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        css = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("Academy Office Subcommand Bridge", html)
        self.assertIn("Enterprise Development Command", html)
        self.assertIn('Academy: "academy_bridge"', js)
        self.assertIn("function renderAcademyBridge()", js)
        self.assertIn("function academyStats()", js)
        for element_id in (
            "academy-capability-growth",
            "academy-heartbeat",
            "academy-learning-feed",
            "academy-education-pipeline",
            "academy-current-weaknesses",
            "academy-capability-radar",
            "academy-learning-velocity",
            "academy-capability-timeline",
            "academy-institutional-memory",
            "academy-enterprise-maturity",
            "academy-mission",
            "academy-office-nav",
        ):
            self.assertIn(f'id="{element_id}"', html)
            self.assertIn(f'("{element_id}")', js)
        self.assertIn(".academy-capability-panel", css)
        self.assertIn(".academy-capability-score", css)
        self.assertIn(".academy-radar", css)

    def test_oe108_academy_bridge_matches_institutional_growth_contract(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        for phrase in (
            "Enterprise Capability Growth",
            "Academy Heartbeat",
            "Learning Feed",
            "Enterprise Education Pipeline",
            "Current Weaknesses",
            "Enterprise Capability Radar",
            "Learning Velocity",
            "Capability Timeline",
            "Institutional Memory",
            "Enterprise Maturity",
            "Academy Mission",
            "Return to Executive Bridge",
        ):
            self.assertIn(phrase, html)
        for phrase in (
            "Decision Quality",
            "Prompt Quality",
            "Strategy Quality",
            "Confidence Calibration",
            "Knowledge Depth",
            "Enterprise Maturity",
            "Institutional Discipline",
            "Learning Velocity",
            "Performance Truth",
            "Historian",
            "Academy Review",
            "Decision Laboratory",
            "Commander Approval",
            "Enterprise Upgrade",
            "Transform enterprise experience into institutional capability.",
            "Every trading day should leave ARGOS more capable than it was yesterday.",
        ):
            self.assertIn(phrase, js)
        self.assertNotIn('id="academy-debug"', html)
        academy_bridge = html.split('id="academy-subcommand-bridge"', 1)[1].split('id="subcommand-placeholder"', 1)[0]
        self.assertNotIn("Capability Calculations", academy_bridge)
        self.assertNotIn("Recommendation Database", academy_bridge)
        self.assertNotIn("Internal Diagnostics", academy_bridge)

    def test_oe108_academy_navigation_is_real_and_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="academy-return-executive"', html)
        self.assertIn('id="academy-office-nav"', html)
        self.assertIn('("academy-return-executive").addEventListener', js)
        self.assertIn('("academy-office-nav").addEventListener', js)
        self.assertIn("engineering_mode", js)
        for office in ("Executive", "Seeker", "Risk", "Trader", "Historian", "Librarian", "Academy"):
            self.assertIn(f'{office}: "{office.lower()}_bridge', js)
        self.assertNotIn('id="academy-own-workflow"', html)
        self.assertNotIn('id="academy-execute-trade"', html)
        self.assertNotIn('id="academy-market-analysis"', html)

    def test_oe108_academy_bridge_updates_after_paper_workflow(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"])
                and bool(item["strategyPerformanceConsole"]["decisionObjectEvolution"])
                and bool(item["performanceTruthEngine"]["portfolioLedger"]),
                timeout=5.0,
            )
            runtime.halt_paper_self_training()

            self.assertTrue(state["workflowRuntimeMonitor"]["recentCompletedWorkflows"])
            self.assertTrue(state["strategyPerformanceConsole"]["decisionObjectEvolution"])
            self.assertTrue(state["performanceTruthEngine"]["portfolioLedger"])
            self.assertIn("decisionLaboratory", state)
            self.assertIn("promptContract", state)
            self.assertIn("strategyPerformanceConsole", state)
        finally:
            self._restore_env(previous)

    def test_eo_a_enterprise_learning_engine_state_is_advisory_only(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        learning = state["enterpriseLearningEngine"]

        self.assertEqual("Enterprise Learning Engine", learning["engineName"])
        self.assertEqual("EO-A", learning["engineeringOrder"])
        self.assertEqual("ADVISORY_ONLY", learning["constitutionalMode"])
        self.assertFalse(learning["lawVII"]["executesWorkflows"])
        self.assertEqual("NEVER", learning["lawVII"]["workflowTokenOwnership"])
        self.assertEqual("BLOCKED", learning["lawVII"]["brokerAccess"])
        self.assertEqual("BLOCKED", learning["lawVII"]["productionPromptMutation"])
        self.assertEqual("BLOCKED", learning["lawVII"]["productionStrategyMutation"])
        self.assertEqual(0.0, learning["internalDiagnostics"]["apiCreditsConsumed"])

    def test_eo_a_completed_workflow_produces_learning_observation(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["enterpriseLearningEngine"]["observations"]),
                timeout=10.0,
            )
            runtime.halt_paper_self_training()

            observation = state["enterpriseLearningEngine"]["observations"][0]
            for key in (
                "observationId",
                "creationTime",
                "workflowId",
                "decisionObjectId",
                "relatedStrategy",
                "relatedPrompt",
                "relatedMarketConditions",
                "observedOutcome",
                "expectedOutcome",
                "difference",
                "evidence",
                "confidence",
                "category",
                "suggestedImprovement",
                "recommendationPriority",
                "laboratoryStatus",
                "commanderStatus",
                "productionStatus",
            ):
                self.assertIn(key, observation)
            self.assertIn("Capability Growth", observation["category"])
            self.assertIn("Workflow Optimization", observation["category"])
            self.assertEqual("QUEUED_FOR_VALIDATION", observation["laboratoryStatus"])
            self.assertEqual("AWAITING_REVIEW", observation["commanderStatus"])
            self.assertEqual("BLOCKED_PENDING_COMMANDER_APPROVAL", observation["productionStatus"])
        finally:
            self._restore_env(previous)

    def test_eo_a_recommendations_are_evidence_scored_and_blocked_from_production(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["enterpriseLearningEngine"]["recommendations"]),
                timeout=10.0,
            )
            runtime.halt_paper_self_training()

            learning = state["enterpriseLearningEngine"]
            self.assertGreaterEqual(len(learning["recommendations"]), 1)
            self.assertGreaterEqual(learning["recommendationThresholds"]["minimumEvidenceCount"], 1)
            for recommendation in learning["recommendations"]:
                for key in (
                    "title",
                    "category",
                    "priority",
                    "expectedBenefit",
                    "evidenceStrength",
                    "confidence",
                    "relatedPrompt",
                    "relatedStrategy",
                    "relatedOffice",
                    "laboratoryStatus",
                    "commanderApprovalStatus",
                    "productionStatus",
                ):
                    self.assertIn(key, recommendation)
                self.assertIn(recommendation["evidenceStrength"], {"WEAK", "MODERATE", "STRONG"})
                self.assertEqual("QUEUED_FOR_VALIDATION", recommendation["laboratoryStatus"])
                self.assertEqual("AWAITING_COMMANDER_REVIEW", recommendation["commanderApprovalStatus"])
                self.assertEqual("BLOCKED_PENDING_COMMANDER_APPROVAL", recommendation["productionStatus"])
            self.assertEqual(len(learning["recommendations"]), len(learning["improvementBacklog"]))
            self.assertEqual(len(learning["recommendations"]), learning["metrics"]["laboratoryQueue"])
            self.assertEqual(len(learning["recommendations"]), learning["metrics"]["commanderReviews"])
            self.assertEqual(0, learning["metrics"]["rejectedImprovements"])
        finally:
            self._restore_env(previous)

    def test_eo_a_learning_dashboard_metrics_feed_academy_bridge(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        metrics = state["enterpriseLearningEngine"]["metrics"]
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        for key in (
            "observationsToday",
            "recommendationsToday",
            "recommendationsPending",
            "validatedImprovements",
            "rejectedImprovements",
            "laboratoryQueue",
            "commanderReviews",
            "averageConfidence",
            "learningVelocity",
            "capabilityGrowth",
            "knowledgeCoverage",
            "institutionalMaturity",
        ):
            self.assertIn(key, metrics)
        self.assertIn("enterpriseLearningEngine", js)
        self.assertIn("learningMetrics", js)
        self.assertIn("learningRecommendations", js)
        self.assertIn("academyLearningFeed", js)

    def test_eo_a_engineering_mode_exposes_learning_internals_only_there(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        academy_bridge = html.split('id="academy-subcommand-bridge"', 1)[1].split('id="subcommand-placeholder"', 1)[0]

        for phrase in (
            "Enterprise Learning Engine",
            "Observation Database",
            "Recommendation Database",
            "Recommendation Thresholds",
            "Knowledge Gap Detection",
            "Improvement Backlog",
            "Learning Rules",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "ele-observations",
            "ele-recommendations",
            "ele-backlog",
            "ele-gaps",
            "ele-metrics",
            "ele-thresholds",
            "ele-rules",
            "ele-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertIn("function renderEnterpriseLearningEngine()", js)
        self.assertNotIn("Observation Database", academy_bridge)
        self.assertNotIn("Recommendation Database", academy_bridge)
        self.assertNotIn("Internal Diagnostics", academy_bridge)

    def test_eo_b_historian_recommendation_engine_state_is_advisory_only(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        historian = state["historianRecommendationEngine"]

        self.assertEqual("Historian Recommendation Engine", historian["engineName"])
        self.assertEqual("EO-B", historian["engineeringOrder"])
        self.assertEqual("ADVISORY_ONLY", historian["constitutionalMode"])
        self.assertEqual("What does history consistently teach us?", historian["constitutionalQuestion"])
        self.assertFalse(historian["lawVII"]["executesWorkflows"])
        self.assertEqual("NEVER", historian["lawVII"]["workflowTokenOwnership"])
        self.assertEqual("BLOCKED", historian["lawVII"]["brokerAccess"])
        self.assertEqual("BLOCKED", historian["lawVII"]["productionPromptMutation"])
        self.assertEqual("BLOCKED", historian["lawVII"]["productionStrategyMutation"])
        self.assertFalse(historian["recommendationThresholds"]["isolatedEventRecommendationsAllowed"])
        self.assertEqual(0.0, historian["internalDiagnostics"]["apiCreditsConsumed"])

    def test_eo_b_isolated_workflow_creates_pattern_but_no_historian_recommendation(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            historian = state["historianRecommendationEngine"]
            self.assertTrue(historian["historicalPatternDatabase"])
            self.assertEqual(0, len(historian["recommendationDatabase"]))
            self.assertEqual(0, historian["recommendationStatistics"]["recommendationsGenerated"])
            self.assertTrue(historian["knowledgeGapReports"])
            self.assertEqual("MINIMUM_HISTORICAL_FREQUENCY", historian["internalDiagnostics"]["recommendationSpamGuard"])
        finally:
            self._restore_env(previous)

    def test_eo_b_accumulated_history_generates_constitutional_recommendations_and_lessons(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: item["workflowRuntimeMonitor"]["metrics"]["completedWorkflows"] >= 2
                and bool(item["historianRecommendationEngine"]["recommendationDatabase"]),
                timeout=4.0,
            )
            runtime.halt_paper_self_training()

            historian = state["historianRecommendationEngine"]
            self.assertGreaterEqual(historian["recommendationStatistics"]["historicalCoverage"], 2)
            self.assertGreaterEqual(len(historian["recommendationDatabase"]), 1)
            self.assertGreaterEqual(len(historian["institutionalLessonLibrary"]), 1)
            for recommendation in historian["recommendationDatabase"]:
                for key in (
                    "recommendationId",
                    "creationDate",
                    "authorOffice",
                    "category",
                    "summary",
                    "detailedExplanation",
                    "supportingEvidence",
                    "supportingWorkflows",
                    "supportingDecisionObjects",
                    "supportingTruthRecords",
                    "historicalFrequency",
                    "historicalSuccessRate",
                    "estimatedEnterpriseBenefit",
                    "confidenceScore",
                    "priority",
                    "laboratoryStatus",
                    "commanderStatus",
                    "productionStatus",
                    "relatedPromptVersions",
                    "relatedStrategyVersions",
                    "relatedExperiments",
                    "relatedRecommendations",
                ):
                    self.assertIn(key, recommendation)
                self.assertGreaterEqual(recommendation["historicalFrequency"], 2)
                self.assertEqual("Historian", recommendation["authorOffice"])
                self.assertEqual("QUEUED_FOR_VALIDATION", recommendation["laboratoryStatus"])
                self.assertEqual("AWAITING_COMMANDER_REVIEW", recommendation["commanderStatus"])
                self.assertEqual("BLOCKED_PENDING_COMMANDER_APPROVAL", recommendation["productionStatus"])
            self.assertEqual(len(historian["recommendationDatabase"]), historian["recommendationStatistics"]["laboratoryQueue"])
            self.assertEqual(len(historian["recommendationDatabase"]), historian["recommendationStatistics"]["commanderReviews"])
        finally:
            self._restore_env(previous)

    def test_eo_b_recommendations_enter_enterprise_learning_engine(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["historianRecommendationEngine"]["recommendationDatabase"]) >= 1
                and len(item["enterpriseLearningEngine"]["historianRecommendationInputs"]) >= 1,
                timeout=4.0,
            )
            runtime.halt_paper_self_training()

            historian_count = len(state["historianRecommendationEngine"]["recommendationDatabase"])
            learning = state["enterpriseLearningEngine"]
            self.assertEqual(historian_count, learning["inputs"]["historianRecommendations"])
            self.assertEqual(historian_count, len(learning["historianRecommendationInputs"]))
            self.assertTrue(any(item["relatedOffice"] == "Historian" for item in learning["recommendations"]))
            self.assertTrue(all(item["productionStatus"] == "BLOCKED_PENDING_COMMANDER_APPROVAL" for item in learning["recommendations"]))
        finally:
            self._restore_env(previous)

    def test_eo_b_historian_ui_and_engineering_mode_are_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        historian_bridge = html.split('id="historian-subcommand-bridge"', 1)[1].split('id="librarian-subcommand-bridge"', 1)[0]

        self.assertIn("historianRecommendationEngine", js)
        self.assertIn("function renderHistorianRecommendationEngine()", js)
        self.assertIn("institutionalLessonLibrary", js)
        self.assertIn("recommendationDatabase", js)
        for phrase in (
            "Historian Recommendation Engine",
            "Historical Pattern Database",
            "Recommendation Database",
            "Evidence Thresholds",
            "Pattern Detection Algorithms",
            "Recommendation Lifecycle",
            "Lesson Archive",
            "Knowledge Gap Reports",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "hre-metrics",
            "hre-thresholds",
            "hre-patterns",
            "hre-recommendations",
            "hre-lessons",
            "hre-gaps",
            "hre-algorithms",
            "hre-lifecycle",
            "hre-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Historical Pattern Database", historian_bridge)
        self.assertNotIn("Pattern Detection Algorithms", historian_bridge)
        self.assertNotIn("Internal Diagnostics", historian_bridge)

    def test_eo_c_prompt_evolution_engine_state_is_advisory_lifecycle_only(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        prompt_evolution = state["promptEvolutionEngine"]

        self.assertEqual("Prompt Evolution Engine", prompt_evolution["engineName"])
        self.assertEqual("EO-C", prompt_evolution["engineeringOrder"])
        self.assertEqual("ADVISORY_LIFECYCLE_ONLY", prompt_evolution["constitutionalMode"])
        self.assertEqual("How should ARGOS think more effectively tomorrow than it thinks today?", prompt_evolution["constitutionalQuestion"])
        self.assertFalse(prompt_evolution["lawVII"]["executesWorkflows"])
        self.assertEqual("NEVER", prompt_evolution["lawVII"]["workflowTokenOwnership"])
        self.assertEqual("BLOCKED", prompt_evolution["lawVII"]["autonomousProductionPromptMutation"])
        self.assertEqual("FORBIDDEN", prompt_evolution["lawVII"]["commanderOverride"])
        self.assertEqual(0.0, prompt_evolution["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, prompt_evolution["internalDiagnostics"]["productionPromptMutationCount"])

    def test_eo_c_prompt_repository_contains_immutable_constitutional_assets(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        prompt_evolution = state["promptEvolutionEngine"]
        repository = prompt_evolution["promptRepository"]
        contract_templates = state["promptContract"]["templates"]

        self.assertEqual(len(contract_templates), len(repository))
        self.assertEqual(len(contract_templates), prompt_evolution["performanceDashboard"]["productionPrompts"])
        self.assertEqual(0, prompt_evolution["performanceDashboard"]["productionMutationCount"])
        for asset in repository:
            for key in (
                "promptId",
                "promptName",
                "purpose",
                "associatedOffice",
                "creationDate",
                "author",
                "versionNumber",
                "status",
                "currentProductionVersion",
                "parentPrompt",
                "childPrompts",
                "experimentHistory",
                "promotionHistory",
                "retirementHistory",
                "supportingRecommendations",
                "supportingEvidence",
                "performanceMetrics",
                "confidence",
                "approvalHistory",
            ):
                self.assertIn(key, asset)
            self.assertEqual("Production", asset["status"])
            self.assertEqual(asset["versionNumber"], asset["currentProductionVersion"])
            self.assertIn(asset["status"], prompt_evolution["promptStates"])
        for history in prompt_evolution["promptVersionHistory"]:
            self.assertTrue(history["immutable"])
            self.assertTrue(history["olderVersionsPreserved"])

    def test_eo_c_prompt_improvement_candidates_are_lab_queued_not_production_mutations(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["promptEvolutionEngine"]["promptImprovementCandidates"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            prompt_evolution = state["promptEvolutionEngine"]
            self.assertGreaterEqual(len(prompt_evolution["promptImprovementCandidates"]), 1)
            self.assertEqual(len(prompt_evolution["promptImprovementCandidates"]), prompt_evolution["performanceDashboard"]["laboratoryQueue"])
            for candidate in prompt_evolution["promptImprovementCandidates"]:
                for key in (
                    "improvementId",
                    "relatedPrompt",
                    "currentVersion",
                    "candidateVersion",
                    "summary",
                    "detailedExplanation",
                    "supportingEvidence",
                    "expectedBenefit",
                    "confidence",
                    "relatedWorkflows",
                    "relatedDecisionObjects",
                    "relatedRecommendations",
                    "historicalJustification",
                    "laboratoryStatus",
                    "commanderStatus",
                    "productionStatus",
                ):
                    self.assertIn(key, candidate)
                self.assertNotEqual(candidate["currentVersion"], candidate["candidateVersion"])
                self.assertEqual("QUEUED_FOR_PROMPT_REPLAY", candidate["laboratoryStatus"])
                self.assertEqual("NOT_READY_PENDING_LAB_VALIDATION", candidate["commanderStatus"])
                self.assertEqual("BLOCKED_PENDING_COMMANDER_APPROVAL", candidate["productionStatus"])
            self.assertEqual(0, prompt_evolution["performanceDashboard"]["productionMutationCount"])
            self.assertTrue(prompt_evolution["laboratoryValidationQueue"])
            self.assertTrue(prompt_evolution["comparisonEngine"])
        finally:
            self._restore_env(previous)

    def test_eo_c_prompt_evolution_preserves_prompt_contract_production_versions(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            before = runtime.state()["promptContract"]["templates"]
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["promptEvolutionEngine"]["promptImprovementCandidates"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()
            after = state["promptContract"]["templates"]

            self.assertEqual(before, after)
            self.assertTrue(all(template["prompt_version"] == "1.0.0" for template in after))
            self.assertEqual(0, state["promptEvolutionEngine"]["performanceDashboard"]["productionMutationCount"])
            self.assertTrue(state["promptEvolutionEngine"]["internalDiagnostics"]["productionReferencesImmutablePromptVersion"])
            self.assertTrue(state["promptEvolutionEngine"]["internalDiagnostics"]["commanderApprovalRequired"])
        finally:
            self._restore_env(previous)

    def test_eo_c_prompt_evolution_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("promptEvolutionEngine", js)
        self.assertIn("function renderPromptEvolutionEngine()", js)
        for phrase in (
            "Prompt Evolution Engine",
            "Prompt Repository",
            "Version Graph & Prompt Lineage",
            "Metadata Editor",
            "Performance Dashboard",
            "Comparison Engine",
            "Laboratory Results & Replay Statistics",
            "Promotion, Retirement & Approval History",
            "Version Difference Viewer",
            "Prompt Dependency Graph",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "pee-metrics",
            "pee-diagnostics",
            "pee-repository",
            "pee-candidates",
            "pee-lineage",
            "pee-metadata",
            "pee-comparisons",
            "pee-lab",
            "pee-history",
            "pee-diff",
            "pee-dependency",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Prompt Repository", command_bridge)
        self.assertNotIn("Version Difference Viewer", command_bridge)
        self.assertNotIn("Metadata Editor", command_bridge)

    def test_eo_e_market_context_engine_state_is_awareness_only(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        market_context = state["marketContextIntegrationEngine"]

        self.assertEqual("Market Context Integration Engine", market_context["engineName"])
        self.assertEqual("EO-E", market_context["engineeringOrder"])
        self.assertEqual("AWARENESS_ONLY", market_context["constitutionalMode"])
        self.assertEqual("What is happening in the market right now that the Analyst should understand?", market_context["constitutionalQuestion"])
        self.assertFalse(market_context["lawVII"]["executesWorkflows"])
        self.assertEqual("NEVER", market_context["lawVII"]["workflowTokenOwnership"])
        self.assertFalse(market_context["lawVII"]["placesTrades"])
        self.assertFalse(market_context["lawVII"]["generatesRecommendations"])
        self.assertEqual("BLOCKED", market_context["lawVII"]["brokerAccess"])
        self.assertEqual("FORBIDDEN", market_context["lawVII"]["commanderOverride"])
        self.assertEqual(0.0, market_context["apiConsumption"]["costUsd"])
        self.assertEqual(0.0, market_context["internalDiagnostics"]["apiCreditsConsumed"])

    def test_eo_e_market_context_object_and_layers_are_normalized(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        market_context = state["marketContextIntegrationEngine"]
        context = market_context["latestMarketContext"]

        for key in (
            "snapshotId",
            "creationTime",
            "marketSession",
            "marketRegime",
            "overallTrend",
            "volatilityState",
            "liquidityState",
            "riskEnvironment",
            "confidence",
            "supportingEvidence",
            "dataFreshness",
            "relatedSymbols",
            "relatedSectors",
            "relatedIndices",
            "relatedMacroEvents",
            "relatedNews",
            "relatedPortfolioExposure",
        ):
            self.assertIn(key, context)
        self.assertTrue(context["snapshotId"].startswith("MCTX-"))
        self.assertEqual("VALID", context["dataFreshness"]["validationStatus"])
        layers = market_context["normalizedMarketLayers"]
        for layer in (
            "marketPrices",
            "technicalIndicators",
            "sectorLeadership",
            "fundamentalInformation",
            "macroeconomicEnvironment",
            "newsIntelligence",
            "optionsMarket",
            "portfolioContext",
            "marketRegimeClassification",
        ):
            self.assertIn(layer, layers)
        for layer in ("marketPrices", "technicalIndicators", "sectorLeadership", "fundamentalInformation", "optionsMarket", "portfolioContext"):
            self.assertIn("quality", layers[layer])
            self.assertEqual("VALID", layers[layer]["quality"]["validationStatus"])
            self.assertIn("source", layers[layer]["quality"])
        self.assertEqual("UNKNOWN", layers["marketPrices"]["currentPrice"])
        self.assertEqual("UNKNOWN", layers["fundamentalInformation"]["marketCapitalization"])
        self.assertEqual("UNKNOWN", layers["optionsMarket"]["openInterest"])

    def test_eo_e_decision_objects_receive_market_context_before_analyst_review(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            workflow_id = state["workflowRuntimeMonitor"]["recentCompletedWorkflows"][0]["workflowIdentifier"]
            workflow = next(item for item in state["workflowOrchestrator"]["workflows"] if item["workflow_id"] == workflow_id)
            analyst_output = next(item for item in workflow["output_history"] if item["workflow_stage"] == "Analyst")
            decision = analyst_output["decision_object"]
            context = decision["marketContext"]
            self.assertEqual(context["snapshotId"], decision["marketContextSnapshotId"])
            self.assertEqual(workflow_id, decision["workflowId"])
            self.assertIn("marketRegime", context)
            self.assertIn("relatedPortfolioExposure", context)
            self.assertIn("relatedNews", context)
            self.assertIn("relatedMacroEvents", context)
            self.assertEqual("VALID", context["dataFreshness"]["validationStatus"])
            self.assertTrue(decision["immutable"])
        finally:
            self._restore_env(previous)

    def test_eo_e_cache_and_api_consumption_are_cost_controlled(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: item["workflowRuntimeMonitor"]["metrics"]["completedWorkflows"] >= 2,
                timeout=4.0,
            )
            runtime.halt_paper_self_training()

            market_context = state["marketContextIntegrationEngine"]
            self.assertTrue(market_context["cacheStatistics"]["cacheEnabled"])
            self.assertGreaterEqual(market_context["cacheStatistics"]["duplicateRequestsAvoided"], 1)
            self.assertEqual(0.0, market_context["cacheStatistics"]["apiCreditsConsumed"])
            self.assertEqual(0, market_context["apiConsumption"]["externalApiCalls"])
            self.assertEqual(0, market_context["apiConsumption"]["brokerCalls"])
            self.assertEqual(0, market_context["apiConsumption"]["tradingApiCalls"])
            self.assertFalse(market_context["internalDiagnostics"]["fabricatesUnknownMarketInformation"])
            self.assertFalse(market_context["internalDiagnostics"]["rawFeedsExposedToDecisionObject"])
            self.assertTrue(market_context["marketSnapshotEngine"]["historicalReplayReady"])
        finally:
            self._restore_env(previous)

    def test_eo_e_market_context_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        seeker_bridge = html.split('id="seeker-subcommand-bridge"', 1)[1].split('id="risk-subcommand-bridge"', 1)[0]

        self.assertIn("marketContextIntegrationEngine", js)
        self.assertIn("function renderMarketContextIntegrationEngine()", js)
        self.assertIn("Context Snapshot", js)
        self.assertIn("Data Freshness", js)
        for phrase in (
            "Market Context Integration Engine",
            "Market Context Repository",
            "Market Snapshot Viewer",
            "Normalized Market Layers",
            "Market Regime Engine",
            "Sector Dashboard",
            "Portfolio Context Engine",
            "Cache Statistics",
            "API Consumption",
            "Data Freshness",
            "Source Health",
            "Normalization Rules",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "mcie-summary",
            "mcie-regime",
            "mcie-repository",
            "mcie-layers",
            "mcie-sector",
            "mcie-portfolio",
            "mcie-cache",
            "mcie-api",
            "mcie-freshness",
            "mcie-source-health",
            "mcie-normalization",
            "mcie-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Normalized Market Layers", seeker_bridge)
        self.assertNotIn("Source Health", seeker_bridge)
        self.assertNotIn("Internal Diagnostics", seeker_bridge)

    def test_eo_f_daily_learning_pipeline_state_is_orchestration_only(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        pipeline = state["dailyEnterpriseLearningPipeline"]

        self.assertEqual("Daily Enterprise Learning Pipeline", pipeline["pipelineName"])
        self.assertEqual("EO-F", pipeline["engineeringOrder"])
        self.assertEqual("LEARNING_ORCHESTRATION_ONLY", pipeline["constitutionalMode"])
        self.assertEqual("How does today's experience improve tomorrow's enterprise?", pipeline["constitutionalQuestion"])
        self.assertFalse(pipeline["lawVII"]["executesWorkflows"])
        self.assertEqual("NEVER", pipeline["lawVII"]["workflowTokenOwnership"])
        self.assertFalse(pipeline["lawVII"]["tradesSecurities"])
        self.assertEqual("BLOCKED", pipeline["lawVII"]["autonomousProductionDeployment"])
        self.assertEqual("FORBIDDEN", pipeline["lawVII"]["commanderOverride"])
        self.assertEqual(0.0, pipeline["pipelineDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, pipeline["pipelineDiagnostics"]["productionChangesDeployed"])

    def test_eo_f_daily_learning_record_is_produced_and_counts_workflows(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05", ARGOS_BROKER_SIM_MARKET_SESSION="CLOSED")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"])
                and bool(item["performanceTruthEngine"]["orderLedger"])
                and item["dailyEnterpriseLearningPipeline"]["activeDailyLearningRecord"]["workflowCount"] >= 1
                and item["dailyEnterpriseLearningPipeline"]["activeDailyLearningRecord"]["performanceTruthCount"] >= 1,
                timeout=5.0,
            )
            runtime.halt_paper_self_training()

            record = state["dailyEnterpriseLearningPipeline"]["activeDailyLearningRecord"]
            for key in (
                "learningSessionId",
                "tradingDate",
                "workflowCount",
                "decisionObjectCount",
                "performanceTruthCount",
                "historianObservations",
                "recommendationsGenerated",
                "recommendationsValidated",
                "laboratoryExperiments",
                "promptCandidates",
                "strategyCandidates",
                "commanderReviews",
                "approvedPromotions",
                "rejectedPromotions",
                "enterpriseCapabilityChange",
                "knowledgeGrowth",
                "confidenceGrowth",
                "creditConsumption",
                "runtimeStatistics",
                "lessonsLearned",
                "outstandingQuestions",
                "commanderSummary",
            ):
                self.assertIn(key, record)
            self.assertGreaterEqual(record["workflowCount"], 1)
            self.assertGreaterEqual(record["decisionObjectCount"], 1)
            self.assertGreaterEqual(record["performanceTruthCount"], 1)
            self.assertEqual(1, len(state["dailyEnterpriseLearningPipeline"]["dailyLearningRecords"]))
        finally:
            self._restore_env(previous)

    def test_eo_f_pipeline_queues_recommendations_validation_and_promotions_without_deploying(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="0.05")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["dailyEnterpriseLearningPipeline"]["recommendationQueue"]) >= 1
                and len(item["dailyEnterpriseLearningPipeline"]["validationQueue"]) >= 1
                and len(item["dailyEnterpriseLearningPipeline"]["promotionQueue"]) >= 1,
                timeout=4.0,
            )
            runtime.halt_paper_self_training()

            pipeline = state["dailyEnterpriseLearningPipeline"]
            self.assertTrue(pipeline["improvementBacklog"])
            self.assertTrue(pipeline["recommendationQueue"])
            self.assertTrue(pipeline["validationQueue"])
            self.assertTrue(pipeline["promotionQueue"])
            self.assertTrue(all(item["productionStatus"] == "BLOCKED_PENDING_COMMANDER_APPROVAL" for item in pipeline["promotionQueue"]))
            self.assertTrue(all(item["automaticDeployment"] is False for item in pipeline["promotionQueue"]))
            self.assertEqual(0, pipeline["activeDailyLearningRecord"]["approvedPromotions"])
            self.assertEqual(0, pipeline["pipelineDiagnostics"]["productionChangesDeployed"])
            self.assertTrue(pipeline["pipelineDiagnostics"]["commanderSovereigntyPreserved"])
        finally:
            self._restore_env(previous)

    def test_eo_f_capability_index_and_knowledge_metrics_feed_academy(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        pipeline = state["dailyEnterpriseLearningPipeline"]
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        capability = pipeline["enterpriseCapabilityIndex"]
        knowledge = pipeline["knowledgeGrowthMetrics"]
        for key in (
            "decisionQuality",
            "promptQuality",
            "strategyQuality",
            "knowledgeDepth",
            "riskDiscipline",
            "confidenceAccuracy",
            "learningVelocity",
            "marketUnderstanding",
            "executionConsistency",
            "institutionalMaturity",
        ):
            self.assertIn(key, capability["dimensions"])
        for key in (
            "decisionObjects",
            "truthRecords",
            "observations",
            "recommendations",
            "validatedLessons",
            "promptVersions",
            "strategyVersions",
            "laboratoryExperiments",
            "commanderApprovals",
            "institutionalDoctrine",
            "knowledgeCoverage",
        ):
            self.assertIn(key, knowledge)
        self.assertIn("dailyEnterpriseLearningPipeline", js)
        self.assertIn("capabilityIndex", js)
        self.assertIn("knowledgeMetrics", js)
        self.assertEqual("READY_FOR_ACADEMY_REVIEW", pipeline["academyHandoff"]["handoffStatus"])

    def test_eo_f_pipeline_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        academy_bridge = html.split('id="academy-subcommand-bridge"', 1)[1].split('id="subcommand-placeholder"', 1)[0]

        self.assertIn("function renderDailyEnterpriseLearningPipeline()", js)
        for phrase in (
            "Daily Enterprise Learning Pipeline",
            "Daily Learning Records",
            "Learning Timeline",
            "Improvement Backlog",
            "Recommendation Queue",
            "Validation Queue",
            "Promotion Queue",
            "Capability Index Calculations",
            "Knowledge Metrics",
            "Commander Briefings",
            "Academy Handoff",
            "Historical Reports",
            "Learning Orchestrator",
            "Pipeline Diagnostics",
            "Internal Statistics",
            "Performance Logs",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "dlp-records",
            "dlp-timeline",
            "dlp-backlog",
            "dlp-recommendations",
            "dlp-validation",
            "dlp-promotion",
            "dlp-capability",
            "dlp-knowledge",
            "dlp-briefing",
            "dlp-academy",
            "dlp-memory",
            "dlp-orchestrator",
            "dlp-diagnostics",
            "dlp-statistics",
            "dlp-logs",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Daily Learning Records", academy_bridge)
        self.assertNotIn("Pipeline Diagnostics", academy_bridge)
        self.assertNotIn("Performance Logs", academy_bridge)

    def test_eo_g_market_data_provider_layer_state_is_access_only(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        provider = state["marketDataProviderAbstractionLayer"]

        self.assertEqual("Market Data Provider Abstraction Layer", provider["layerName"])
        self.assertEqual("EO-G", provider["engineeringOrder"])
        self.assertEqual("ACCESS_ONLY", provider["constitutionalMode"])
        self.assertEqual("Can ARGOS change market data vendors without changing enterprise cognition?", provider["constitutionalQuestion"])
        self.assertFalse(provider["lawVII"]["executesWorkflows"])
        self.assertEqual("NEVER", provider["lawVII"]["workflowTokenOwnership"])
        self.assertFalse(provider["lawVII"]["placesTrades"])
        self.assertFalse(provider["lawVII"]["generatesInvestmentDecisions"])
        self.assertEqual("BLOCKED", provider["lawVII"]["brokerAccess"])
        self.assertEqual(0, provider["internalDiagnostics"]["externalNetworkCalls"])
        self.assertEqual(0.0, provider["internalDiagnostics"]["apiCreditsConsumed"])

    def test_eo_g_provider_registry_capabilities_and_normalized_objects_are_visible(self) -> None:
        runtime = create_runtime()
        provider = runtime.state()["marketDataProviderAbstractionLayer"]
        registry = provider["providerRegistry"]

        provider_ids = {item["providerId"] for item in registry}
        self.assertIn("external-paper", provider_ids)
        self.assertIn("external-live", provider_ids)
        self.assertIn("replay-market-data", provider_ids)
        self.assertIn("test-market-data", provider_ids)
        self.assertIn("development-simulation-market-data", provider_ids)
        self.assertNotIn("mock", provider_ids)
        self.assertNotIn("synthetic", provider_ids)
        self.assertTrue(any(item["providerType"] == "AUTHORITATIVE_EXTERNAL" for item in registry))
        self.assertFalse(provider["providerConfiguration"]["mockFallbackEnabled"])
        self.assertFalse(provider["providerConfiguration"]["syntheticFallbackEnabled"])
        for entry in registry:
            for key in (
                "providerId",
                "providerName",
                "providerType",
                "enabled",
                "environment",
                "supportedCapabilities",
                "defaultPriority",
                "fallbackPriority",
                "costModel",
                "rateLimitModel",
                "authenticationStatus",
                "healthStatus",
                "commanderApprovalStatus",
            ):
                self.assertIn(key, entry)
        self.assertEqual((), provider["normalizedObjects"]["quotes"])
        self.assertFalse(provider["providerConfiguration"]["authoritativeProviderConfigured"])
        self.assertEqual("UNCONFIGURED", provider["commanderVisibility"]["providerHealth"])

        from argos.control_panel.market_data_provider import MarketDataProviderAbstractionLayer

        requested_at = "2026-07-19T14:30:00Z"
        controlled = MarketDataProviderAbstractionLayer.with_controlled_authoritative_provider(
            observations={
                "SPY": {"bid": "529.00", "ask": "529.02", "last": "529.01", "volume": "1000", "source_timestamp_utc": requested_at},
                "MARKET": {"status": "REGULAR", "source_timestamp_utc": requested_at},
            }
        ).snapshot(timestamp_utc=requested_at)
        quote = controlled["normalizedObjects"]["quotes"][0]
        self.assertEqual("NormalizedQuote", quote["objectType"])
        attribution = quote["sourceAttribution"]
        for key in (
            "providerId",
            "providerType",
            "sourceAuthority",
            "proofDomain",
            "requestId",
            "correlationId",
            "dataTimestamp",
            "ingestionTimestamp",
            "freshness",
            "rawPayloadReference",
            "deterministicHash",
            "schemaVersion",
        ):
            self.assertIn(key, attribution)
        self.assertEqual("AUTHORITATIVE_EXTERNAL", attribution["providerType"])
        self.assertEqual("PAPER_AUTHORITATIVE", attribution["proofDomain"])
        self.assertEqual("FRESH", attribution["freshness"])
        self.assertEqual("VALID", quote["validation"]["validationStatus"])

    def test_eo_g_unsupported_capabilities_failover_cache_and_cost_are_audited(self) -> None:
        runtime = create_runtime()
        provider = runtime.state()["marketDataProviderAbstractionLayer"]

        unsupported = provider["normalizedObjects"]["unsupportedCapabilities"][0]
        self.assertEqual("UnsupportedCapabilityResponse", unsupported["objectType"])
        self.assertFalse(unsupported["supported"])
        self.assertEqual("UNSUPPORTED", unsupported["validation"]["validationStatus"])
        self.assertTrue(provider["failoverEvents"])
        self.assertTrue(provider["failoverEvents"][0]["audited"])
        self.assertTrue(provider["cacheStatistics"]["cacheEnabled"])
        self.assertGreaterEqual(provider["cacheStatistics"]["cacheHitRate"], 0)
        self.assertTrue(all(item["actualCostUsd"] == 0.0 for item in provider["costHistory"]))
        self.assertTrue(all(item["creditGovernorApproval"] == "NOT_REQUIRED_ZERO_COST" for item in provider["callHistory"]))
        self.assertTrue(provider["replayModeTools"]["preventsFutureLeakage"])
        self.assertFalse(provider["normalizationDiagnostics"]["vendorSpecificPayloadVisibleToCognition"])

    def test_eo_g_market_context_uses_provider_abstraction_without_vendor_payloads(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        provider = state["marketDataProviderAbstractionLayer"]
        market_context = state["marketContextIntegrationEngine"]

        self.assertEqual("mock", provider["commanderVisibility"]["currentPrimaryProvider"])
        self.assertEqual("synthetic", provider["commanderVisibility"]["activeFallbackProvider"])
        self.assertEqual("EO-G", market_context["internalDiagnostics"]["providerAbstractionLayer"])
        self.assertFalse(market_context["internalDiagnostics"]["vendorSpecificPayloadVisibleToCognition"])
        self.assertIn("providerAbstraction", market_context["sourceHealth"])
        self.assertEqual("Market Data Provider Abstraction Layer", market_context["sourceHealth"]["providerAbstraction"]["source"])

    def test_eo_g_provider_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("marketDataProviderAbstractionLayer", js)
        self.assertIn("function renderMarketDataProviderAbstractionLayer()", js)
        for phrase in (
            "Market Data Provider Abstraction Layer",
            "Provider Registry",
            "Provider Configuration",
            "Capability Matrix",
            "Provider Health Dashboard",
            "Call History",
            "Cost History",
            "Rate Limit Status",
            "Cache Statistics",
            "Raw Payload Viewer",
            "Normalization Diagnostics",
            "Failover Events",
            "Replay Mode Tools",
            "Mock Provider Controls",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "mdpa-summary",
            "mdpa-auth",
            "mdpa-registry",
            "mdpa-config",
            "mdpa-capabilities",
            "mdpa-health",
            "mdpa-rates",
            "mdpa-calls",
            "mdpa-costs",
            "mdpa-cache",
            "mdpa-raw",
            "mdpa-normalization",
            "mdpa-failover",
            "mdpa-replay",
            "mdpa-controls",
            "mdpa-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Provider Registry", command_bridge)
        self.assertNotIn("Raw Payload Viewer", command_bridge)
        self.assertNotIn("Mock Provider Controls", command_bridge)

    def test_eo_h_decision_object_schema_state_is_frozen_and_constitutional(self) -> None:
        runtime = create_runtime()
        schema = runtime.state()["decisionObjectSchema"]

        self.assertEqual("Decision Object Schema", schema["schemaName"])
        self.assertEqual("EO-H", schema["engineeringOrder"])
        self.assertEqual("KNOWLEDGE_PRESERVATION_ONLY", schema["constitutionalMode"])
        self.assertEqual("What exactly constitutes enterprise knowledge?", schema["constitutionalQuestion"])
        self.assertEqual("1.0.0", schema["schemaVersion"])
        self.assertTrue(schema["frozen"])
        self.assertIn("1.0.0", schema["immutableSchemaVersions"])
        for field in (
            "decisionObjectId",
            "schemaVersion",
            "workflowId",
            "workflowTokenId",
            "creationTimestamp",
            "decisionTimestamp",
            "office",
            "currentOwner",
            "lifecycleState",
            "decisionType",
            "confidence",
            "priority",
            "commanderVisibility",
            "immutable",
            "schemaValidationStatus",
            "marketContext",
            "marketContextSnapshotId",
            "promptContract",
            "schemaFingerprint",
        ):
            self.assertIn(field, schema["requiredFields"])
        self.assertTrue(schema["serializationStandard"]["stableOrdering"])
        self.assertTrue(schema["serializationStandard"]["hashStable"])
        self.assertFalse(schema["lawVII"]["executesWorkflows"])
        self.assertFalse(schema["lawVII"]["ownsWorkflowExecutionTokens"])
        self.assertFalse(schema["lawVII"]["generatesTrades"])
        self.assertFalse(schema["lawVII"]["overridesCommanderAuthority"])
        self.assertEqual(0, schema["internalDiagnostics"]["apiCallsMade"])

    def test_eo_h_paper_decision_objects_are_schema_frozen_and_valid(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"])
                and item["decisionObjectSchema"]["objectValidator"]["validDecisionObjects"] >= 5,
                timeout=10.0,
            )
            runtime.halt_paper_self_training()

            schema = state["decisionObjectSchema"]
            workflow_id = state["workflowRuntimeMonitor"]["recentCompletedWorkflows"][0]["workflowIdentifier"]
            workflow = next(item for item in state["workflowOrchestrator"]["workflows"] if item["workflow_id"] == workflow_id)
            self.assertEqual(5, len(workflow["output_history"]))
            for output in workflow["output_history"]:
                decision = output["decision_object"]
                self.assertEqual(schema["schemaVersion"], decision["schemaVersion"])
                self.assertTrue(decision["schemaFrozen"])
                self.assertTrue(decision["immutable"])
                self.assertEqual("VALID", decision["schemaValidationStatus"])
                self.assertEqual((), decision["schemaValidationErrors"])
                self.assertTrue(decision["schemaFingerprint"].startswith("DO-SCHEMA-EO-H-V1"))
                self.assertEqual(decision["marketContext"]["snapshotId"], decision["marketContextSnapshotId"])
                self.assertEqual(decision["supportingAuditIdentifier"], decision["workflowTokenId"])
                self.assertEqual("CURRENT_SCHEMA", decision["compatibilityStatus"])
                self.assertEqual("NOT_REQUIRED", decision["migrationStatus"])
                self.assertEqual("REPLAYABLE", decision["audit"]["replayVerificationStatus"])
            self.assertEqual(5, schema["objectValidator"]["validDecisionObjects"])
            self.assertEqual(0, schema["objectValidator"]["invalidDecisionObjects"])
            self.assertTrue(schema["repositoryBrowser"])
            self.assertTrue(schema["hashViewer"])
            self.assertTrue(schema["referenceGraph"])
        finally:
            self._restore_env(previous)

    def test_eo_h_schema_rejects_missing_required_fields(self) -> None:
        from argos.control_panel.decision_object_schema import DecisionObjectSchemaRegistry

        registry = DecisionObjectSchemaRegistry()
        invalid = registry.freeze({"decisionObjectId": "DO-BAD", "immutable": True})

        self.assertEqual("INVALID", invalid["schemaValidationStatus"])
        self.assertIn("workflowId", invalid["schemaValidationErrors"])
        self.assertIn("workflowTokenId", invalid["schemaValidationErrors"])
        self.assertIn("marketContext", invalid["schemaValidationErrors"])

    def test_eo_h_schema_metadata_survives_strategy_console_and_laboratory_replay(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["strategyPerformanceConsole"]["decisionObjectEvolution"])
                and bool(item["decisionLaboratory"]["decisionObjectReplay"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            evolution = state["strategyPerformanceConsole"]["decisionObjectEvolution"][-1]
            self.assertTrue(all(revision["schemaVersion"] == "1.0.0" for revision in evolution["revisions"]))
            self.assertTrue(all(revision["schemaValidationStatus"] == "VALID" for revision in evolution["revisions"]))
            self.assertTrue(all(revision["schemaFingerprint"].startswith("DO-SCHEMA-EO-H-V1") for revision in evolution["revisions"]))
            replay = state["decisionLaboratory"]["decisionObjectReplay"][-1]
            analyst_revision = replay["revisions"][1]
            self.assertEqual("1.0.0", analyst_revision["structuredOutput"]["decision_object"]["schemaVersion"])
            self.assertEqual("VALID", analyst_revision["structuredOutput"]["decision_object"]["schemaValidationStatus"])
            self.assertEqual("REPLAYABLE", analyst_revision["structuredOutput"]["decision_object"]["audit"]["replayVerificationStatus"])
        finally:
            self._restore_env(previous)

    def test_eo_h_schema_engineering_mode_is_wired_and_hidden_from_bridges(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("decisionObjectSchema", js)
        self.assertIn("function renderDecisionObjectSchema()", js)
        for phrase in (
            "Decision Object Schema Freeze",
            "Schema Registry",
            "Object Validator",
            "Required Fields",
            "Optional Fields & Enumerations",
            "Validation Rules",
            "Repository Browser",
            "Hash Viewer",
            "Reference Graph",
            "Compatibility Matrix",
            "Serialization Standard",
            "LAW VII Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "dos-summary",
            "dos-validation",
            "dos-fields",
            "dos-enums",
            "dos-rules",
            "dos-repository",
            "dos-hashes",
            "dos-lineage",
            "dos-compatibility",
            "dos-serialization",
            "dos-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Schema Registry", command_bridge)
        self.assertNotIn("Hash Viewer", command_bridge)
        self.assertNotIn("LAW VII Diagnostics", command_bridge)

    def test_eo_i_prompt_package_manager_state_governs_deployment_only(self) -> None:
        runtime = create_runtime()
        manager = runtime.state()["promptPackageManager"]

        self.assertEqual("Prompt Package Manager", manager["managerName"])
        self.assertEqual("EO-I", manager["engineeringOrder"])
        self.assertEqual("PROMPT_DEPLOYMENT_GOVERNANCE_ONLY", manager["constitutionalMode"])
        self.assertEqual(
            "Can enterprise cognition be installed, upgraded, reverted, and audited exactly like production software?",
            manager["constitutionalQuestion"],
        )
        self.assertIn("Office Prompt", manager["packageTypes"])
        self.assertIn("Active", manager["packageStates"])
        self.assertEqual("Package Candidate", manager["installationPipeline"][0])
        self.assertEqual("Audit Record", manager["installationPipeline"][-1])
        self.assertFalse(manager["lawVII"]["executesWorkflows"])
        self.assertFalse(manager["lawVII"]["ownsWorkflowTokens"])
        self.assertFalse(manager["lawVII"]["tradesSecurities"])
        self.assertFalse(manager["lawVII"]["autonomousPromptModification"])
        self.assertFalse(manager["lawVII"]["activationWithoutCommanderApproval"])
        self.assertEqual(0.0, manager["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, manager["internalDiagnostics"]["productionPromptMutationCount"])

    def test_eo_i_every_production_prompt_has_active_package_assignment(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        manager = state["promptPackageManager"]
        template_ids = {item["prompt_template_id"] for item in state["promptContract"]["templates"]}
        active_packages = manager["activePackages"]

        self.assertEqual(template_ids, {item["repositoryReference"] for item in active_packages})
        self.assertEqual({"Seeker", "Analyst", "Risk", "Trader", "Historian"}, {item["owningOffice"] for item in active_packages})
        for package in active_packages:
            for key in (
                "packageId",
                "packageName",
                "packageVersion",
                "packageType",
                "owningOffice",
                "purpose",
                "description",
                "author",
                "creationDate",
                "currentStatus",
                "promptVersion",
                "repositoryReference",
                "checksum",
                "hash",
                "compatibilityMatrix",
                "dependencyList",
                "deploymentStatus",
                "approvalStatus",
                "packageHealth",
                "promptHash",
                "dependencyHashes",
                "validationHash",
                "installationHash",
            ):
                self.assertIn(key, package)
            self.assertEqual("Active", package["currentStatus"])
            self.assertEqual("ACTIVE", package["deploymentStatus"])
            self.assertEqual("HEALTHY", package["packageHealth"])
            self.assertTrue(all(item["status"] == "SATISFIED" for item in package["dependencyList"]))
            self.assertTrue(all(item["status"] == "SATISFIED" for item in package["compatibilityMatrix"]))

        assignments = manager["officePackageAssignment"]
        self.assertEqual(5, len(assignments))
        self.assertTrue(all(item["consumptionMode"] == "PROMPT_PACKAGE_MANAGER" for item in assignments))
        self.assertEqual(5, len(manager["integrityVerification"]))
        self.assertTrue(all(item["verifiedBeforeActivation"] for item in manager["integrityVerification"]))
        self.assertTrue(manager["rollbackManager"]["rollbackSupported"])
        self.assertTrue(manager["rollbackManager"]["requiresCommanderApproval"])
        self.assertFalse(manager["rollbackManager"]["automaticRollback"])

    def test_eo_i_prompt_package_trace_flows_into_decision_objects(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            workflow_id = state["workflowRuntimeMonitor"]["recentCompletedWorkflows"][0]["workflowIdentifier"]
            workflow = next(item for item in state["workflowOrchestrator"]["workflows"] if item["workflow_id"] == workflow_id)
            for output in workflow["output_history"]:
                contract = output["decision_object"]["promptContract"]
                self.assertIn("promptPackageId", contract)
                self.assertIn("promptPackageVersion", contract)
                self.assertEqual("Active", contract["promptPackageStatus"])
                self.assertEqual("EO-I", contract["promptPackageManager"])
                self.assertEqual("PROMPT_PACKAGE_MANAGER", contract["consumptionMode"])
        finally:
            self._restore_env(previous)

    def test_eo_i_prompt_package_manager_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("promptPackageManager", js)
        self.assertIn("function renderPromptPackageManager()", js)
        for phrase in (
            "Prompt Package Manager",
            "Package Registry",
            "Installed Packages",
            "Active Packages",
            "Office Package Assignment",
            "Version Graph",
            "Dependency Graph",
            "Compatibility Matrix",
            "Installation History",
            "Activation History",
            "Rollback Manager",
            "Integrity Verification",
            "Health Dashboard",
            "Laboratory Results",
            "Deployment Timeline",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "ppm-summary",
            "ppm-diagnostics",
            "ppm-installed",
            "ppm-active",
            "ppm-offices",
            "ppm-versions",
            "ppm-dependencies",
            "ppm-compatibility",
            "ppm-install-history",
            "ppm-activation-history",
            "ppm-rollback",
            "ppm-integrity",
            "ppm-health",
            "ppm-lab",
            "ppm-timeline",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Package Registry", command_bridge)
        self.assertNotIn("Rollback Manager", command_bridge)
        self.assertNotIn("Integrity Verification", command_bridge)

    def test_eo_j_strategy_package_manager_state_governs_deployment_only(self) -> None:
        runtime = create_runtime()
        manager = runtime.state()["strategyPackageManager"]

        self.assertEqual("Strategy Package Manager", manager["managerName"])
        self.assertEqual("EO-J", manager["engineeringOrder"])
        self.assertEqual("STRATEGY_DEPLOYMENT_GOVERNANCE_ONLY", manager["constitutionalMode"])
        self.assertEqual(
            "Can enterprise investment doctrine be installed, upgraded, validated, reverted, and audited exactly like enterprise software?",
            manager["constitutionalQuestion"],
        )
        self.assertIn("Momentum Strategy", manager["packageTypes"])
        self.assertIn("Capital Preservation Strategy", manager["packageTypes"])
        self.assertIn("Active", manager["packageStates"])
        self.assertEqual("Strategy Candidate", manager["installationPipeline"][0])
        self.assertEqual("Audit Record", manager["installationPipeline"][-1])
        self.assertFalse(manager["lawVII"]["executesWorkflows"])
        self.assertFalse(manager["lawVII"]["ownsWorkflowTokens"])
        self.assertFalse(manager["lawVII"]["tradesSecurities"])
        self.assertFalse(manager["lawVII"]["activationWithoutCommanderApproval"])
        self.assertFalse(manager["lawVII"]["autonomousDoctrineModification"])
        self.assertEqual(0.0, manager["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, manager["internalDiagnostics"]["productionStrategyMutationCount"])

    def test_eo_j_every_production_strategy_has_managed_package(self) -> None:
        runtime = create_runtime()
        manager = runtime.state()["strategyPackageManager"]
        active = manager["activePackages"]

        self.assertTrue(active)
        self.assertTrue(any(item["strategyName"] == "Workflow Proof Strategy" for item in active))
        for package in manager["strategyPackageRegistry"]:
            for key in (
                "packageId",
                "packageName",
                "packageVersion",
                "strategyName",
                "strategyVersion",
                "strategyFamily",
                "purpose",
                "investmentThesis",
                "description",
                "author",
                "creationDate",
                "owningOffice",
                "currentStatus",
                "repositoryReference",
                "checksum",
                "compatibilityMatrix",
                "dependencyList",
                "validationStatus",
                "deploymentStatus",
                "approvalStatus",
                "packageHealth",
                "supportedMarketRegimes",
                "strategyHash",
                "dependencyHashes",
                "validationHash",
                "deploymentHash",
            ):
                self.assertIn(key, package)
            self.assertTrue(all(item["status"] == "SATISFIED" for item in package["dependencyList"]))
            self.assertTrue(all(item["status"] == "SATISFIED" for item in package["compatibilityMatrix"]))
        self.assertEqual("Analyst", manager["analystStrategyAssignment"]["office"])
        self.assertEqual("STRATEGY_PACKAGE_MANAGER", manager["analystStrategyAssignment"]["consumptionMode"])
        self.assertTrue(manager["analystStrategyAssignment"]["directSourceFileReferenceBlocked"])
        self.assertTrue(manager["rollbackManager"]["rollbackSupported"])
        self.assertTrue(manager["rollbackManager"]["requiresCommanderApproval"])
        self.assertFalse(manager["rollbackManager"]["automaticRollback"])
        self.assertTrue(all(item["verifiedBeforeActivation"] for item in manager["integrityDashboard"]))
        self.assertTrue(manager["marketRegimeAssignment"])

    def test_eo_j_strategy_package_trace_flows_into_decision_objects(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            workflow_id = state["workflowRuntimeMonitor"]["recentCompletedWorkflows"][0]["workflowIdentifier"]
            workflow = next(item for item in state["workflowOrchestrator"]["workflows"] if item["workflow_id"] == workflow_id)
            for output in workflow["output_history"]:
                decision = output["decision_object"]
                self.assertIn("strategyPackageId", decision)
                self.assertIn("strategyPackageVersion", decision)
                self.assertEqual("EO-J", decision["strategyPackageManager"])
                self.assertEqual("STRATEGY_PACKAGE_MANAGER", decision["strategyConsumptionMode"])
                self.assertTrue(decision["strategyPackageId"].startswith("SPM-"))
        finally:
            self._restore_env(previous)

    def test_eo_j_strategy_package_manager_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("strategyPackageManager", js)
        self.assertIn("function renderStrategyPackageManager()", js)
        for phrase in (
            "Strategy Package Manager",
            "Strategy Package Registry",
            "Installed Packages",
            "Active Packages",
            "Strategy Assignment",
            "Version Graph",
            "Dependency Graph",
            "Compatibility Matrix",
            "Installation History",
            "Activation History",
            "Rollback Manager",
            "Integrity Dashboard",
            "Health Dashboard",
            "Laboratory Results",
            "Replay Statistics",
            "Counterfactual Reports",
            "Market Regime Assignment",
            "Deployment Timeline",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "spm-summary",
            "spm-diagnostics",
            "spm-installed",
            "spm-active",
            "spm-assignments",
            "spm-versions",
            "spm-dependencies",
            "spm-compatibility",
            "spm-install-history",
            "spm-activation-history",
            "spm-rollback",
            "spm-integrity",
            "spm-health",
            "spm-lab",
            "spm-replay",
            "spm-counterfactual",
            "spm-regimes",
            "spm-timeline",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Strategy Package Registry", command_bridge)
        self.assertNotIn("Integrity Dashboard", command_bridge)
        self.assertNotIn("Market Regime Assignment", command_bridge)

    def test_eo_k_enterprise_configuration_registry_is_single_truth(self) -> None:
        runtime = create_runtime()
        registry = runtime.state()["enterpriseConfigurationRegistry"]

        self.assertEqual("Enterprise Configuration Registry", registry["registryName"])
        self.assertEqual("EO-K", registry["engineeringOrder"])
        self.assertEqual("CONFIGURATION_GOVERNANCE_ONLY", registry["constitutionalMode"])
        self.assertEqual("One Enterprise. One Configuration Truth.", registry["constitutionalMission"])
        self.assertEqual("The Enterprise Configuration Registry.", registry["constitutionalAnswer"])
        for category in (
            "Enterprise",
            "Workflow",
            "Office",
            "Prompt",
            "Strategy",
            "Market Context",
            "Risk",
            "Portfolio",
            "Execution",
            "Paper Trading",
            "Broker",
            "Learning",
            "Laboratory",
            "Historian",
            "Academy",
            "Runtime",
            "Monitoring",
            "API Gateway",
            "Credit Governor",
            "Security",
            "Diagnostics",
            "Commander Preferences",
        ):
            self.assertIn(category, registry["categories"])
        self.assertFalse(registry["lawVII"]["executesWorkflows"])
        self.assertFalse(registry["lawVII"]["ownsWorkflowTokens"])
        self.assertFalse(registry["lawVII"]["tradesSecurities"])
        self.assertFalse(registry["lawVII"]["autonomousProductionBehaviorModification"])
        self.assertEqual(0, registry["internalDiagnostics"]["invalidConfigurationCount"])
        self.assertFalse(registry["internalDiagnostics"]["hiddenConfigurationDetected"])

    def test_eo_k_configuration_entries_are_versioned_validated_and_auditable(self) -> None:
        runtime = create_runtime()
        registry = runtime.state()["enterpriseConfigurationRegistry"]
        entries = registry["configurationRegistry"]

        self.assertGreaterEqual(len(entries), 40)
        for entry in entries:
            for key in (
                "configurationId",
                "category",
                "name",
                "value",
                "dataType",
                "description",
                "defaultValue",
                "currentValue",
                "environment",
                "version",
                "createdBy",
                "createdDate",
                "modifiedDate",
                "commanderApproval",
                "validationStatus",
                "dependencies",
                "auditReference",
                "checksum",
            ):
                self.assertIn(key, entry)
            self.assertEqual("VALID", entry["validationStatus"])
            self.assertEqual("Production", entry["state"])
            self.assertEqual("APPROVED_BASELINE", entry["commanderApproval"])
        self.assertEqual(len(entries), registry["validationDashboard"]["validEntries"])
        self.assertEqual(0, registry["validationDashboard"]["circularDependenciesDetected"])
        self.assertEqual("NONE", registry["configurationHealth"]["configurationDrift"])
        self.assertTrue(registry["rollbackManager"]["rollbackSupported"])
        self.assertTrue(registry["rollbackManager"]["requiresCommanderApproval"])
        self.assertFalse(registry["rollbackManager"]["automaticRollback"])
        self.assertTrue(all(item["configurationSource"] == "Enterprise Configuration Registry" for item in registry["componentConsumption"]))
        self.assertTrue(all(item["hiddenConfigurationAllowed"] is False for item in registry["componentConsumption"]))

    def test_eo_k_decision_objects_reference_active_configuration(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            workflow_id = state["workflowRuntimeMonitor"]["recentCompletedWorkflows"][0]["workflowIdentifier"]
            workflow = next(item for item in state["workflowOrchestrator"]["workflows"] if item["workflow_id"] == workflow_id)
            registry = state["enterpriseConfigurationRegistry"]
            for output in workflow["output_history"]:
                decision = output["decision_object"]
                self.assertEqual("EO-K", decision["enterpriseConfigurationRegistry"])
                self.assertEqual(registry["enterpriseConfigurationVersion"], decision["enterpriseConfigurationVersion"])
                self.assertEqual(registry["currentEnvironment"], decision["enterpriseConfigurationEnvironment"])
                self.assertTrue(decision["enterpriseConfigurationId"].startswith("ECR-"))
        finally:
            self._restore_env(previous)

    def test_eo_k_configuration_registry_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("enterpriseConfigurationRegistry", js)
        self.assertIn("function renderEnterpriseConfigurationRegistry()", js)
        for phrase in (
            "Enterprise Configuration Registry",
            "Configuration Registry",
            "Configuration History",
            "Version Graph",
            "Dependency Graph",
            "Environment Manager",
            "Validation Dashboard",
            "Promotion Queue",
            "Rollback Manager",
            "Configuration Diff Viewer",
            "Configuration Search",
            "Configuration Health",
            "Audit History",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "ecr-summary",
            "ecr-diagnostics",
            "ecr-history",
            "ecr-versions",
            "ecr-dependencies",
            "ecr-environments",
            "ecr-validation",
            "ecr-promotion",
            "ecr-rollback",
            "ecr-diff",
            "ecr-search",
            "ecr-health",
            "ecr-audit",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Configuration Diff Viewer", command_bridge)
        self.assertNotIn("Configuration Search", command_bridge)
        self.assertNotIn("Environment Manager", command_bridge)

    def test_eo_l_enterprise_health_monitor_state_is_observation_only(self) -> None:
        health = create_runtime().state()["enterpriseHealthMonitor"]

        self.assertEqual("Enterprise Health Monitor", health["monitorName"])
        self.assertEqual("EO-L", health["engineeringOrder"])
        self.assertEqual("OBSERVATION_ONLY", health["constitutionalMode"])
        self.assertEqual(
            "Continuously assess the operational readiness, stability, reliability, and constitutional integrity of the enterprise.",
            health["constitutionalMission"],
        )
        self.assertEqual("Is ARGOS healthy enough to perform its mission?", health["constitutionalQuestion"])
        self.assertGreaterEqual(health["enterpriseHealthScore"], 95)
        self.assertIn(health["status"], health["healthStates"])
        self.assertIn(health["trend"], ("Stable", "Improving"))
        self.assertGreaterEqual(health["confidence"], 0.9)
        for boundary in (
            "executesWorkflows",
            "ownsWorkflowTokens",
            "tradesSecurities",
            "modifiesEnterpriseBehavior",
            "overridesCommanderAuthority",
            "suppressesConstitutionalViolations",
        ):
            self.assertFalse(health["lawVII"][boundary])
        self.assertEqual(0.0, health["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, health["internalDiagnostics"]["workflowTokensOwned"])
        self.assertEqual(0, health["internalDiagnostics"]["tradesPlaced"])

    def test_eo_l_component_dependency_and_constitutional_health_cover_enterprise(self) -> None:
        health = create_runtime().state()["enterpriseHealthMonitor"]
        components = {item["component"] for item in health["componentHealth"]}
        dependencies = {item["dependencyChain"] for item in health["dependencyGraph"]}

        for component in (
            "Commander",
            "Executive",
            "Seeker",
            "Analyst",
            "Risk",
            "Trader",
            "Historian",
            "Librarian",
            "Academy",
            "Workflow Engine",
            "Workflow Token System",
            "Decision Object System",
            "Performance Truth Engine",
            "Decision Laboratory",
            "Prompt Evolution",
            "Strategy Evolution",
            "Market Context Engine",
            "Provider Layer",
            "Configuration Registry",
            "Credit Governor",
            "API Gateway",
            "Runtime Monitor",
            "Audit System",
        ):
            self.assertIn(component, components)
        for dependency in (
            "Prompt Package Dependencies",
            "Strategy Dependencies",
            "Provider Dependencies",
            "Configuration Dependencies",
            "Workflow Dependencies",
        ):
            self.assertIn(dependency, dependencies)
        self.assertIn("tokenIntegrity", health["workflowHealth"])
        self.assertIn("schemaCompliance", health["decisionObjectHealth"])
        self.assertIn("providerHealth", health["apiHealth"])
        self.assertEqual("VALID", health["databaseHealth"]["integrity"])
        self.assertIn("recommendationsGenerated", health["enterpriseLearningHealth"])
        self.assertIn("packageCount", health["promptHealth"])
        self.assertIn("packageCount", health["strategyHealth"])
        self.assertIn("status", health["configurationHealth"])
        self.assertIn("remainingBudget", health["creditHealth"])
        self.assertEqual("Healthy", health["runtimeHealth"]["status"])
        self.assertEqual("VALID", health["constitutionalHealth"]["status"])
        dashboard = health["commanderHealthDashboard"]
        for key in (
            "enterpriseHealthScore",
            "healthyComponents",
            "warningComponents",
            "criticalComponents",
            "currentAlerts",
            "creditHealth",
            "providerHealth",
            "workflowHealth",
            "constitutionalHealth",
        ):
            self.assertIn(key, dashboard)
        self.assertFalse(dashboard["interventionRequired"])

    def test_eo_l_health_history_and_forecasts_update_after_paper_workflow(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            health = state["enterpriseHealthMonitor"]
            forecasts = {item["forecast"] for item in health["forecastModels"]}
            self.assertTrue(health["healthHistory"])
            self.assertTrue(health["healthTimeline"])
            for forecast in ("Credit Exhaustion", "API Saturation", "Workflow Backlog", "Provider Stability"):
                self.assertIn(forecast, forecasts)
            for alert in health["currentAlerts"]:
                for key in ("timestamp", "component", "description", "evidence", "severity", "recommendedAction", "resolutionStatus"):
                    self.assertIn(key, alert)
        finally:
            self._restore_env(previous)

    def test_eo_l_enterprise_health_monitor_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("enterpriseHealthMonitor", js)
        self.assertIn("function renderEnterpriseHealthMonitor()", js)
        for phrase in (
            "Enterprise Health Monitor",
            "Component Health",
            "Dependency Graph",
            "Alert History",
            "Health Calculations",
            "Telemetry Viewer",
            "Health Timeline",
            "Forecast Models",
            "Runtime Statistics",
            "Infrastructure Metrics",
            "Validation Failures",
            "Provider Diagnostics",
            "Database Diagnostics",
            "Internal Health Rules",
            "Health Configuration",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "ehm-summary",
            "ehm-components",
            "ehm-dependencies",
            "ehm-alerts",
            "ehm-calculations",
            "ehm-telemetry",
            "ehm-timeline",
            "ehm-forecasts",
            "ehm-runtime",
            "ehm-infrastructure",
            "ehm-validation",
            "ehm-provider",
            "ehm-database",
            "ehm-rules",
            "ehm-config",
            "ehm-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Telemetry Viewer", command_bridge)
        self.assertNotIn("Forecast Models", command_bridge)
        self.assertNotIn("Internal Health Rules", command_bridge)

    def test_eo_m_enterprise_failure_recovery_framework_is_constitutional(self) -> None:
        recovery = create_runtime().state()["enterpriseFailureRecoveryFramework"]

        self.assertEqual("Enterprise Failure Recovery Framework", recovery["frameworkName"])
        self.assertEqual("EO-M", recovery["engineeringOrder"])
        self.assertEqual("ENTERPRISE_CONTINUITY_ONLY", recovery["constitutionalMode"])
        self.assertEqual(
            "Preserve enterprise integrity during every failure and guarantee deterministic recovery.",
            recovery["constitutionalMission"],
        )
        self.assertIn("can it safely continue", recovery["constitutionalQuestion"])
        self.assertEqual("Yes. ARGOS recovers safely when recovery validation is green.", recovery["constitutionalAnswer"])
        self.assertEqual("SAFE", recovery["safeEnterpriseState"]["status"])
        for boundary in (
            "executesInvestmentDecisions",
            "ownsWorkflowTokens",
            "createsDuplicateWorkflowTokens",
            "assignsMultipleWorkflowOwners",
            "rewritesHistoricalDecisionObjects",
            "modifiesProductionDoctrine",
            "bypassesCommanderAuthority",
        ):
            self.assertFalse(recovery["lawVII"][boundary])
        self.assertEqual(0.0, recovery["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, recovery["internalDiagnostics"]["workflowTokensOwned"])
        self.assertEqual(0, recovery["internalDiagnostics"]["tradesPlaced"])

    def test_eo_m_recovery_artifacts_cover_failures_safe_state_and_validation(self) -> None:
        recovery = create_runtime().state()["enterpriseFailureRecoveryFramework"]

        for classification in (
            "Information",
            "Transient",
            "Recoverable",
            "Persistent",
            "Infrastructure",
            "Application",
            "Configuration",
            "Authentication",
            "Provider",
            "Database",
            "Runtime",
            "Workflow",
            "Constitutional",
            "Critical",
            "Emergency",
            "Unknown",
        ):
            self.assertIn(classification, recovery["failureClassifications"])
        strategies = {item["classification"]: item["strategy"] for item in recovery["recoveryStrategies"]}
        self.assertEqual("Retry", strategies["Transient"])
        self.assertEqual("Failover", strategies["Provider"])
        self.assertEqual("Quarantine", strategies["Constitutional"])
        for key in (
            "noOrphanedWorkflowTokens",
            "noDuplicateWorkflows",
            "noPartialDecisionObjects",
            "noPartialPromptPromotions",
            "noPartialStrategyPromotions",
            "noCorruptedPerformanceTruth",
            "noBrokenConstitutionalChains",
        ):
            self.assertTrue(recovery["safeEnterpriseState"][key])
        for key in (
            "lawVII",
            "workflowIntegrity",
            "decisionObjectIntegrity",
            "auditIntegrity",
            "configurationIntegrity",
            "dependencyIntegrity",
            "performanceTruthIntegrity",
            "commanderApprovalChain",
        ):
            self.assertEqual("VALID", recovery["recoveryValidation"][key])
        self.assertEqual("None", recovery["commanderRecoverySummary"]["requiredCommanderAction"])

    def test_eo_m_checkpoints_chaos_and_quarantine_are_visible_after_paper_workflow(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            recovery = state["enterpriseFailureRecoveryFramework"]
            checkpoints = {item["checkpoint"] for item in recovery["checkpointBrowser"]}
            chaos = {item["simulation"] for item in recovery["chaosTestingControls"]}
            boundaries = {item["operation"] for item in recovery["transactionBoundaries"]}
            self.assertIn("Workflow Start", checkpoints)
            self.assertIn("Workflow Complete", checkpoints)
            self.assertIn("Truth Recorded", checkpoints)
            self.assertIn("Provider Offline", chaos)
            self.assertIn("Workflow Crash", chaos)
            self.assertIn("Configuration Corruption", chaos)
            self.assertIn("Workflow Creation", boundaries)
            self.assertIn("Decision Object Creation", boundaries)
            self.assertIn("Performance Truth Recording", boundaries)
            self.assertFalse(recovery["quarantine"]["productionParticipationAllowed"])
            self.assertTrue(recovery["failoverSupport"]["recorded"])
        finally:
            self._restore_env(previous)

    def test_eo_m_failure_recovery_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("enterpriseFailureRecoveryFramework", js)
        self.assertIn("function renderEnterpriseFailureRecoveryFramework()", js)
        for phrase in (
            "Enterprise Failure Recovery Framework",
            "Failure History",
            "Recovery History",
            "Failure Timeline",
            "Recovery Dashboard",
            "Recovery Validation",
            "Checkpoint Browser",
            "Recovery Rules",
            "Recovery Statistics",
            "Recovery Forecasts",
            "Chaos Testing Controls",
            "Failure Classification",
            "Recovery Diagnostics",
            "Dependency Failures",
            "Infrastructure Diagnostics",
            "Transaction Boundaries",
            "Quarantine",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "efr-summary",
            "efr-failures",
            "efr-recoveries",
            "efr-timeline",
            "efr-dashboard",
            "efr-validation",
            "efr-checkpoints",
            "efr-rules",
            "efr-statistics",
            "efr-forecasts",
            "efr-chaos",
            "efr-classification",
            "efr-diagnostics",
            "efr-dependencies",
            "efr-infrastructure",
            "efr-boundaries",
            "efr-quarantine",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Chaos Testing Controls", command_bridge)
        self.assertNotIn("Recovery Diagnostics", command_bridge)
        self.assertNotIn("Transaction Boundaries", command_bridge)

    def test_eo_n_decision_object_quality_scoring_engine_is_read_only(self) -> None:
        quality = create_runtime().state()["decisionObjectQualityScoringEngine"]

        self.assertEqual("Decision Object Quality Scoring Engine", quality["engineName"])
        self.assertEqual("EO-N", quality["engineeringOrder"])
        self.assertEqual("KNOWLEDGE_ASSESSMENT_ONLY", quality["constitutionalMode"])
        self.assertEqual(
            "Measure the quality of enterprise knowledge before enterprise cognition acts upon it.",
            quality["constitutionalMission"],
        )
        self.assertEqual("How trustworthy is the knowledge available for this decision?", quality["constitutionalQuestion"])
        for grade in ("A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F", "Unknown"):
            self.assertIn(grade, quality["qualityGrades"])
        for boundary in (
            "executesWorkflows",
            "ownsWorkflowTokens",
            "tradesSecurities",
            "makesInvestmentDecisions",
            "modifiesPrompts",
            "modifiesStrategies",
            "overridesCommanderAuthority",
        ):
            self.assertFalse(quality["lawVII"][boundary])
        self.assertEqual(0.0, quality["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, quality["internalDiagnostics"]["workflowTokensOwned"])
        self.assertEqual(0, quality["internalDiagnostics"]["tradesPlaced"])

    def test_eo_n_quality_reports_attach_to_paper_decision_objects(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"])
                and bool(item["decisionObjectQualityScoringEngine"]["qualityReports"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            quality = state["decisionObjectQualityScoringEngine"]
            report = quality["qualityReports"][-1]
            decision = state["strategyPerformanceConsole"]["decisionObjectPanel"]
            workflow_id = state["workflowRuntimeMonitor"]["recentCompletedWorkflows"][0]["workflowIdentifier"]
            workflow = next(item for item in state["workflowOrchestrator"]["workflows"] if item["workflow_id"] == workflow_id)
            decision_object = workflow["output_history"][-1]["decision_object"]

            self.assertTrue(report["qualityId"].startswith("DOQ-"))
            self.assertEqual(decision["decisionObjectId"], report["decisionObjectId"])
            self.assertEqual(report["qualityId"], decision_object["qualityReport"]["qualityId"])
            self.assertEqual(report["overallScore"], decision_object["decisionObjectQuality"])
            self.assertEqual(report["grade"], decision_object["qualityGrade"])
            self.assertEqual(report["decisionReadiness"], decision_object["decisionReadiness"])
            self.assertTrue(report["immutable"])
            self.assertGreaterEqual(report["overallScore"], 90)
            self.assertIn(report["grade"], quality["qualityGrades"])
        finally:
            self._restore_env(previous)

    def test_eo_n_dimension_scores_thresholds_and_trends_are_available(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["decisionObjectQualityScoringEngine"]["qualityReports"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            quality = state["decisionObjectQualityScoringEngine"]
            dimensions = {item["dimension"] for item in quality["latestQualityReport"]["dimensionScores"]}
            for dimension in (
                "Completeness",
                "Evidence Quality",
                "Freshness",
                "Consistency",
                "Confidence Calibration",
                "Market Context",
                "Risk Awareness",
                "Portfolio Awareness",
                "Prompt Quality",
                "Strategy Alignment",
                "Data Integrity",
                "Schema Integrity",
                "Source Diversity",
                "Knowledge Coverage",
                "Decision Readiness",
            ):
                self.assertIn(dimension, dimensions)
            self.assertGreaterEqual(quality["thresholdConfiguration"]["minimumDecisionQuality"], 80)
            self.assertTrue(quality["thresholdConfiguration"]["commanderControlled"])
            self.assertIn("averageQualityScore", quality["trendAnalysis"])
            self.assertIn("knowledgeCoverageTrend", quality["academyBridgeFeed"])
            self.assertGreaterEqual(len(quality["scoringAlgorithms"]), 15)
            self.assertTrue(quality["qualityRecommendations"])
        finally:
            self._restore_env(previous)

    def test_eo_n_quality_scoring_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("decisionObjectQualityScoringEngine", js)
        self.assertIn("function renderDecisionObjectQualityScoringEngine()", js)
        for phrase in (
            "Decision Object Quality Scoring Engine",
            "Quality Reports",
            "Dimension Scores",
            "Quality History",
            "Trend Analysis",
            "Threshold Configuration",
            "Scoring Algorithms",
            "Completeness Analysis",
            "Consistency Analysis",
            "Freshness Metrics",
            "Evidence Metrics",
            "Calibration Metrics",
            "Quality Forecasts",
            "Quality Recommendations",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "doq-summary",
            "doq-reports",
            "doq-dimensions",
            "doq-history",
            "doq-trends",
            "doq-thresholds",
            "doq-algorithms",
            "doq-completeness",
            "doq-consistency",
            "doq-freshness",
            "doq-evidence",
            "doq-calibration",
            "doq-forecasts",
            "doq-recommendations",
            "doq-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Scoring Algorithms", command_bridge)
        self.assertNotIn("Threshold Configuration", command_bridge)
        self.assertNotIn("Quality Forecasts", command_bridge)

    def test_eo_o_commander_daily_review_workspace_is_operational_table(self) -> None:
        workspace = create_runtime().state()["commanderDailyReviewWorkspace"]

        self.assertEqual("Commander Daily Review Workspace", workspace["workspaceName"])
        self.assertEqual("EO-O", workspace["engineeringOrder"])
        self.assertEqual("COMMANDER_OPERATING_TABLE_ONLY", workspace["constitutionalMode"])
        self.assertEqual(
            "Provide the Commander with one complete operational workspace from which the enterprise can be understood, directed, improved, and approved.",
            workspace["constitutionalMission"],
        )
        self.assertEqual("If I had only ten minutes each day to operate ARGOS, what would I need to know?", workspace["constitutionalQuestion"])
        for section in ("Morning Readiness", "Enterprise Operations", "Commander Approval Queue", "Enterprise Learning", "End-of-Day Review"):
            self.assertIn(section, workspace["workspaceSections"])
        for boundary in (
            "executesWorkflows",
            "ownsWorkflowTokens",
            "makesInvestmentDecisions",
            "automaticallyApprovesPromotions",
            "modifiesDoctrineAutonomously",
            "overridesConstitutionalGovernance",
        ):
            self.assertFalse(workspace["lawVII"][boundary])
        self.assertEqual(0.0, workspace["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, workspace["internalDiagnostics"]["workflowTokensOwned"])
        self.assertEqual(0, workspace["internalDiagnostics"]["tradesPlaced"])

    def test_eo_o_workspace_aggregates_daily_reviews_and_approval_queue(self) -> None:
        runtime = create_runtime()
        workspace = runtime.state()["commanderDailyReviewWorkspace"]

        self.assertIn("enterpriseHealth", workspace["morningReadiness"])
        self.assertIn("activePromptPackage", workspace["morningReadiness"])
        self.assertIn("activeStrategyPackage", workspace["morningReadiness"])
        self.assertIn("decisionObjectQuality", workspace["enterpriseOperations"])
        self.assertTrue(workspace["commanderApprovalQueue"])
        approval = workspace["commanderApprovalQueue"][0]
        for key in ("summary", "evidence", "confidence", "expectedBenefit", "risk", "commanderActions"):
            self.assertIn(key, approval)
        for action in ("Approve", "Reject", "Request More Information", "Defer"):
            self.assertIn(action, approval["commanderActions"])
        self.assertIn("tradingSummary", workspace["endOfDayReview"])
        self.assertTrue(workspace["dailyReportsArchive"])
        self.assertTrue(workspace["priorityPanel"])
        self.assertTrue(workspace["commanderInsights"])
        self.assertIn("morning", workspace["reviewChecklist"])
        self.assertIn("evening", workspace["reviewChecklist"])

    def test_eo_o_commander_journal_records_immutable_artifacts(self) -> None:
        runtime = create_runtime()
        state = runtime.add_commander_journal_entry("Doctrine Notes", "Keep paper trading review disciplined.")
        workspace = state["commanderDailyReviewWorkspace"]
        entry = workspace["commanderJournal"][-1]

        self.assertEqual("Doctrine Notes", entry["category"])
        self.assertEqual("Keep paper trading review disciplined.", entry["entry"])
        self.assertTrue(entry["immutable"])
        self.assertTrue(entry["journalId"].startswith("CDRW-JOURNAL-"))
        self.assertTrue(entry["auditReference"].startswith("AE-CDRW-JOURNAL-"))
        self.assertEqual(1, workspace["internalDiagnostics"]["journalEntryCount"])
        self.assertTrue(any(event["summary"] == "Commander journal entry recorded" for event in state["eab"]["events"]))

    def test_eo_o_commander_workspace_ui_and_engineering_links_are_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]
        engineering = html.split('id="engineering-mode"', 1)[1]

        self.assertIn("commanderDailyReviewWorkspace", js)
        self.assertIn("function renderCommanderDailyReviewWorkspace()", js)
        self.assertIn("/api/commander/journal", js)
        self.assertIn("/api/commander/journal", server)
        for phrase in (
            "Commander Daily Review Workspace",
            "Morning Readiness",
            "Enterprise Operations",
            "Commander Approval Queue",
            "Enterprise Learning",
            "End-of-Day Review",
            "Priority Panel",
            "Commander Insights",
            "Commander Journal",
        ):
            self.assertIn(phrase, command_bridge)
        for element_id in (
            "cdw-morning",
            "cdw-operations",
            "cdw-approvals",
            "cdw-learning",
            "cdw-eod",
            "cdw-priorities",
            "cdw-insights",
            "cdw-journal-category",
            "cdw-journal-entry",
            "cdw-journal-save",
            "cdw-journal",
        ):
            self.assertIn(f'id="{element_id}"', command_bridge)
            self.assertIn(f'("{element_id}")', js)
        for phrase in ("Enterprise Scorecard", "Enterprise Timeline", "Review Checklist", "Daily Reports Archive", "Engineering Mode Links"):
            self.assertIn(phrase, engineering)
        for element_id in ("cdrw-scorecard", "cdrw-timeline", "cdrw-checklist", "cdrw-reports", "cdrw-engineering-links", "cdrw-diagnostics"):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)

    def test_eo_p_enterprise_benchmark_engine_is_measurement_only(self) -> None:
        benchmark = create_runtime().state()["enterpriseBenchmarkEngine"]

        self.assertEqual("Enterprise Benchmark Engine", benchmark["engineName"])
        self.assertEqual("EO-P", benchmark["engineeringOrder"])
        self.assertEqual("MEASUREMENT_ONLY", benchmark["constitutionalMode"])
        self.assertEqual(
            "Measure whether ARGOS creates value beyond what would have happened through simpler alternatives.",
            benchmark["constitutionalMission"],
        )
        self.assertEqual("Did ARGOS actually outperform a reasonable baseline?", benchmark["constitutionalQuestion"])
        for boundary in (
            "executesWorkflows",
            "ownsWorkflowTokens",
            "tradesSecurities",
            "makesInvestmentDecisions",
            "modifiesPrompts",
            "modifiesStrategies",
            "overridesCommanderAuthority",
            "generatesAutonomousDeployments",
        ):
            self.assertFalse(benchmark["lawVII"][boundary])
        self.assertEqual(0.0, benchmark["benchmarkDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, benchmark["benchmarkDiagnostics"]["workflowTokensOwned"])
        self.assertEqual(0, benchmark["benchmarkDiagnostics"]["tradesPlaced"])

    def test_eo_p_benchmark_registry_contains_default_baselines(self) -> None:
        benchmark = create_runtime().state()["enterpriseBenchmarkEngine"]
        names = {item["benchmarkName"] for item in benchmark["benchmarkRegistry"]}
        types = set(benchmark["benchmarkTypes"])

        for name in (
            "Cash",
            "Risk-Free Rate",
            "SPY Buy And Hold",
            "QQQ Buy And Hold",
            "DIA Buy And Hold",
            "IWM Buy And Hold",
            "Equal Weight S&P 500",
            "Relevant Sector ETF",
            "Relevant Industry ETF",
            "Previous Production Strategy",
            "Random Entry Baseline",
            "No-Trade Baseline",
        ):
            self.assertIn(name, names)
        for benchmark_type in (
            "Market Benchmark",
            "Sector Benchmark",
            "Strategy Benchmark",
            "Portfolio Benchmark",
            "Risk-Free Benchmark",
            "Randomized Benchmark",
            "Historical Strategy Benchmark",
            "No-Action Benchmark",
            "Synthetic Benchmark",
        ):
            self.assertIn(benchmark_type, types)
        self.assertTrue(benchmark["benchmarkConfiguration"]["riskAdjustmentRequired"])
        self.assertTrue(benchmark["benchmarkConfiguration"]["commanderMayAddOrRemoveBenchmarks"])

    def test_eo_p_benchmark_snapshots_are_created_for_paper_trades(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["enterpriseBenchmarkEngine"]["benchmarkSnapshots"]),
                timeout=10.0,
            )
            runtime.halt_paper_self_training()

            benchmark = state["enterpriseBenchmarkEngine"]
            snapshot = benchmark["benchmarkSnapshots"][0]
            for key in (
                "benchmarkSnapshotId",
                "decisionObjectId",
                "workflowId",
                "tradeId",
                "benchmarkId",
                "benchmarkReturn",
                "argosReturn",
                "excessReturn",
                "riskAdjustment",
                "holdingPeriod",
                "capitalExposure",
                "marketRegime",
                "timestamp",
                "dataSource",
                "confidence",
            ):
                self.assertIn(key, snapshot)
            self.assertTrue(any(item["benchmarkName"] == "No Trade" for item in benchmark["tradeLevelComparisons"]))
            self.assertTrue(any(item["benchmarkName"] == "Random Entry Baseline" for item in benchmark["tradeLevelComparisons"]))
            self.assertTrue(benchmark["opportunityCost"])
            self.assertIn("alpha", benchmark["riskAdjustedMetrics"])
            self.assertTrue(benchmark["randomBaselineControls"]["seeded"])
            self.assertTrue(benchmark["randomBaselineControls"]["replayable"])
            self.assertIn("actionJustified", benchmark["noTradeBaseline"])
        finally:
            runtime.halt_paper_self_training()
            self._restore_env(previous)

    def test_eo_p_benchmark_reports_feed_learning_and_commander_review(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["enterpriseBenchmarkEngine"]["benchmarkSnapshots"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            benchmark = state["enterpriseBenchmarkEngine"]
            periods = {item["period"] for item in benchmark["benchmarkReports"]}
            for period in ("Daily", "Weekly", "Monthly", "Strategy-Level", "Prompt-Level", "Portfolio-Level"):
                self.assertIn(period, periods)
            self.assertTrue(benchmark["historianFeed"]["benchmarkSnapshots"])
            self.assertTrue(benchmark["enterpriseLearningFeed"]["benchmarkEvidenceAvailable"])
            self.assertTrue(benchmark["strategyEvolutionFeed"]["promotionRequiresBenchmarkContext"])
            self.assertTrue(benchmark["promptEvolutionFeed"]["promptBenchmarkingAvailable"])
            self.assertIn("valueAddedStatement", benchmark["commanderReviewFeed"])
            self.assertIn("benchmarkValueAdded", state["commanderDailyReviewWorkspace"]["enterpriseScorecard"])
        finally:
            self._restore_env(previous)

    def test_eo_p_enterprise_benchmark_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("enterpriseBenchmarkEngine", js)
        self.assertIn("function renderEnterpriseBenchmarkEngine()", js)
        for phrase in (
            "Enterprise Benchmark Engine",
            "Benchmark Registry",
            "Benchmark Configuration",
            "Benchmark Performance",
            "Benchmark Reports",
            "Trade-Level Comparisons",
            "Strategy-Level Comparisons",
            "Portfolio-Level Comparisons",
            "Risk-Adjusted Metrics",
            "Random Baseline Controls",
            "No-Trade Baseline",
            "Market Regime Buckets",
            "Historical Benchmark Data",
            "Benchmark Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "ebe-summary",
            "ebe-registry",
            "ebe-configuration",
            "ebe-performance",
            "ebe-reports",
            "ebe-trades",
            "ebe-strategies",
            "ebe-portfolio",
            "ebe-risk",
            "ebe-random",
            "ebe-no-trade",
            "ebe-regimes",
            "ebe-history",
            "ebe-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Random Baseline Controls", command_bridge)
        self.assertNotIn("Historical Benchmark Data", command_bridge)

    def test_eo_q_decision_explainability_engine_is_explanation_only(self) -> None:
        explain = create_runtime().state()["decisionExplainabilityEngine"]

        self.assertEqual("Decision Explainability Engine", explain["engineName"])
        self.assertEqual("EO-Q", explain["engineeringOrder"])
        self.assertEqual("EXPLANATION_ONLY", explain["constitutionalMode"])
        self.assertEqual(
            "Every enterprise decision shall be understandable, explainable, reproducible, and auditable.",
            explain["constitutionalMission"],
        )
        self.assertEqual("Why did ARGOS make this decision?", explain["constitutionalQuestion"])
        for boundary in (
            "executesWorkflows",
            "ownsWorkflowTokens",
            "tradesSecurities",
            "makesInvestmentDecisions",
            "modifiesPrompts",
            "modifiesStrategies",
            "generatesAutonomousDecisions",
            "overridesCommanderAuthority",
        ):
            self.assertFalse(explain["lawVII"][boundary])
        self.assertEqual(0.0, explain["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, explain["internalDiagnostics"]["workflowTokensOwned"])
        self.assertEqual(0, explain["internalDiagnostics"]["tradesPlaced"])

    def test_eo_q_explainability_reports_attach_to_paper_decision_objects(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["decisionExplainabilityEngine"]["explainabilityRepository"])
                and bool(item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            explain = state["decisionExplainabilityEngine"]
            report = explain["explainabilityRepository"][-1]
            decision = state["strategyPerformanceConsole"]["decisionObjectPanel"]
            workflow_id = state["workflowRuntimeMonitor"]["recentCompletedWorkflows"][0]["workflowIdentifier"]
            workflow = next(item for item in state["workflowOrchestrator"]["workflows"] if item["workflow_id"] == workflow_id)
            decision_object = workflow["output_history"][-1]["decision_object"]

            self.assertTrue(report["explainabilityReportId"].startswith("EXP-"))
            self.assertEqual(decision["decisionObjectId"], report["decisionObjectId"])
            self.assertEqual(report["explainabilityReportId"], decision_object["explainabilityReport"]["explainabilityReportId"])
            self.assertEqual(report["explainabilityReportId"], decision_object["explainabilityReportId"])
            self.assertEqual(report["commanderReadabilityScore"], decision_object["commanderReadabilityScore"])
            self.assertTrue(report["immutable"])
            self.assertEqual("AUDIT_READY", report["auditStatus"])
            self.assertGreaterEqual(report["commanderReadabilityScore"], 90)
        finally:
            self._restore_env(previous)

    def test_eo_q_reasoning_evidence_alternatives_and_confidence_are_explicit(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["decisionExplainabilityEngine"]["latestExplainabilityReport"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            latest = state["decisionExplainabilityEngine"]["latestExplainabilityReport"]
            chain_stages = [item["stage"] for item in latest["reasoningChain"]]
            self.assertEqual(["Observed Facts", "Reasoning", "Decision", "Expected Outcome", "Confidence"], chain_stages)
            self.assertTrue(latest["evidenceSummary"])
            self.assertTrue(any(item["category"] == "Decision Quality Report" for item in latest["evidenceSummary"]))
            self.assertTrue(latest["evidenceWeighting"])
            self.assertTrue(any(item["action"] == "NO ACTION" for item in latest["alternativeActions"]))
            self.assertIn("overallExplanationConfidence", latest["confidenceExplanation"])
            self.assertIn("expectedReturn", latest["expectedOutcome"])
            self.assertIn("confidenceRisk", latest["riskSummary"])
        finally:
            self._restore_env(previous)

    def test_eo_q_explainability_feeds_replay_learning_and_evolution(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["decisionExplainabilityEngine"]["explanationHistory"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            explain = state["decisionExplainabilityEngine"]
            self.assertGreater(explain["historianFeed"]["explanationsAvailable"], 0)
            self.assertIn("explanationQualityTrend", explain["enterpriseLearningFeed"])
            self.assertTrue(explain["promptEvolutionFeed"]["readabilityMetricAvailable"])
            self.assertTrue(explain["strategyEvolutionFeed"]["reasoningStrengthMetricAvailable"])
            self.assertTrue(explain["decisionLaboratoryFeed"]["replayReproducible"])
            self.assertTrue(explain["historicalSearch"])
            self.assertTrue(explain["referenceGraph"])
        finally:
            self._restore_env(previous)

    def test_eo_q_decision_explainability_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("decisionExplainabilityEngine", js)
        self.assertIn("function renderDecisionExplainabilityEngine()", js)
        for phrase in (
            "Decision Explainability Engine",
            "Explainability Repository",
            "Reasoning Graph",
            "Evidence Graph",
            "Evidence Weighting",
            "Explanation Templates",
            "Explanation Quality",
            "Readability Scores",
            "Alternative Decisions",
            "Confidence Breakdown",
            "Historical Search",
            "Reference Graph",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "dee-summary",
            "dee-repository",
            "dee-reasoning",
            "dee-evidence",
            "dee-weighting",
            "dee-templates",
            "dee-quality",
            "dee-readability",
            "dee-alternatives",
            "dee-confidence",
            "dee-search",
            "dee-reference",
            "dee-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Reasoning Graph", command_bridge)
        self.assertNotIn("Evidence Weighting", command_bridge)

    def test_eo_r_trade_attribution_engine_is_attribution_only(self) -> None:
        attribution = create_runtime().state()["tradeAttributionEngine"]

        self.assertEqual("Trade Attribution Engine", attribution["engineName"])
        self.assertEqual("EO-R", attribution["engineeringOrder"])
        self.assertEqual("ATTRIBUTION_ONLY", attribution["constitutionalMode"])
        self.assertEqual(
            "Separate skill, process, market conditions, and randomness so enterprise learning is based upon causation rather than coincidence.",
            attribution["constitutionalMission"],
        )
        self.assertEqual("What factors actually produced this outcome?", attribution["constitutionalQuestion"])
        for boundary in (
            "executesWorkflows",
            "ownsWorkflowTokens",
            "tradesSecurities",
            "makesInvestmentDecisions",
            "modifiesPrompts",
            "modifiesStrategies",
            "overridesCommanderAuthority",
            "generatesAutonomousDecisions",
        ):
            self.assertFalse(attribution["lawVII"][boundary])
        self.assertEqual(0.0, attribution["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, attribution["internalDiagnostics"]["workflowTokensOwned"])
        self.assertEqual(0, attribution["internalDiagnostics"]["tradesPlaced"])

    def test_eo_r_completed_trade_receives_immutable_attribution_report(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_BROKER_SIM_MARKET_SESSION="CLOSED")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["tradeAttributionEngine"]["attributionRepository"]),
                timeout=10.0,
            )
            runtime.halt_paper_self_training()

            attribution = state["tradeAttributionEngine"]
            report = attribution["attributionRepository"][-1]
            order = state["performanceTruthEngine"]["orderLedger"][-1]

            self.assertTrue(report["attributionReportId"].startswith("TAE-ATTR-"))
            self.assertEqual(order["order_id"], report["tradeId"])
            self.assertEqual(order["workflow_id"], report["workflowId"])
            self.assertEqual(order["decision_object_id"], report["decisionObjectId"])
            self.assertEqual(order["hash"], report["performanceTruthId"])
            self.assertTrue(report["immutable"])
            self.assertIn("hash", report)
            self.assertIn("promptVersion", report)
            self.assertIn("strategyVersion", report)
            self.assertIn("overallAttributionConfidence", report)
            self.assertGreater(report["overallAttributionConfidence"], 0.5)
            self.assertTrue(report["primaryContributors"])
            self.assertTrue(report["secondaryContributors"])
            self.assertTrue(report["commanderSummary"])
        finally:
            runtime.halt_paper_self_training()
            self._restore_env(previous)

    def test_eo_r_attribution_dimensions_counterfactuals_and_unknowns_are_explicit(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["tradeAttributionEngine"]["latestAttributionReport"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            report = state["tradeAttributionEngine"]["latestAttributionReport"]
            dimensions = {item["dimension"]: item for item in report["dimensionScores"]}
            for dimension in (
                "Strategy",
                "Prompt",
                "Market Regime",
                "Sector Leadership",
                "Technical Signals",
                "Fundamental Signals",
                "News",
                "Macroeconomics",
                "Portfolio Construction",
                "Risk Management",
                "Execution Timing",
                "Position Sizing",
                "Randomness",
                "Unknown",
            ):
                self.assertIn(dimension, dimensions)
                self.assertIn("contributionScore", dimensions[dimension])
                self.assertIn("confidence", dimensions[dimension])
            self.assertTrue(report["counterfactuals"])
            self.assertTrue(any(item["scenario"] == "No Trade" for item in report["counterfactuals"]))
            self.assertTrue(any(item["scenario"] == "Passive Benchmark" for item in report["counterfactuals"]))
            self.assertTrue(report["uncertaintyAssessment"]["unknownExplicitlyPreserved"])
            self.assertTrue(report["outcomeSummary"]["skillSeparatedFromMarketBeta"])
            self.assertIn("enterpriseAlpha", report["benchmarkAttribution"])
        finally:
            self._restore_env(previous)

    def test_eo_r_attribution_feeds_learning_evolution_and_commander_review(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["tradeAttributionEngine"]["attributionHistory"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            attribution = state["tradeAttributionEngine"]
            self.assertTrue(attribution["historianFeed"]["causalPatternsAvailable"])
            self.assertTrue(attribution["enterpriseLearningFeed"]["attributionEvidenceAvailable"])
            self.assertTrue(attribution["enterpriseLearningFeed"]["learnFromCausationNotCoincidence"])
            self.assertTrue(attribution["promptEvolutionFeed"]["promptContributionTracked"])
            self.assertTrue(attribution["strategyEvolutionFeed"]["promotionUsesAttributionEvidence"])
            self.assertIn("attributionSummary", attribution["commanderReviewFeed"])
            self.assertTrue(attribution["decisionLaboratoryFeed"]["counterfactualValidationAvailable"])
            self.assertTrue(attribution["historicalSearch"])
            self.assertTrue(attribution["attributionTrends"])
            self.assertTrue(attribution["randomnessEstimation"]["unknownRemainsUnknown"])
        finally:
            self._restore_env(previous)

    def test_eo_r_trade_attribution_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("tradeAttributionEngine", js)
        self.assertIn("function renderTradeAttributionEngine()", js)
        for phrase in (
            "Trade Attribution Engine",
            "Attribution Repository",
            "Contribution Analysis",
            "Counterfactual Reports",
            "Strategy Attribution",
            "Prompt Attribution",
            "Market Attribution",
            "Risk Attribution",
            "Execution Attribution",
            "Portfolio Attribution",
            "Randomness Estimation",
            "Attribution Trends",
            "Confidence Analysis",
            "Historical Search",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "tae-summary",
            "tae-repository",
            "tae-contribution",
            "tae-counterfactuals",
            "tae-strategy",
            "tae-prompt",
            "tae-market",
            "tae-risk",
            "tae-execution",
            "tae-portfolio",
            "tae-randomness",
            "tae-trends",
            "tae-confidence",
            "tae-search",
            "tae-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Counterfactual Reports", command_bridge)
        self.assertNotIn("Randomness Estimation", command_bridge)

    def test_eo_s_enterprise_reproducibility_framework_is_reproducibility_only(self) -> None:
        reproducibility = create_runtime().state()["enterpriseReproducibilityFramework"]

        self.assertEqual("Enterprise Reproducibility Framework", reproducibility["frameworkName"])
        self.assertEqual("EO-S", reproducibility["engineeringOrder"])
        self.assertEqual("REPRODUCIBILITY_ONLY", reproducibility["constitutionalMode"])
        self.assertEqual("Every enterprise decision shall remain reproducible forever.", reproducibility["constitutionalMission"])
        self.assertEqual(
            "If this exact workflow were replayed years from now, would ARGOS reach the same decision using only the information that originally existed?",
            reproducibility["constitutionalQuestion"],
        )
        for boundary in (
            "executesWorkflows",
            "ownsWorkflowTokens",
            "tradesSecurities",
            "makesInvestmentDecisions",
            "modifiesHistoricalArtifacts",
            "modifiesPrompts",
            "modifiesStrategies",
            "overridesCommanderAuthority",
        ):
            self.assertFalse(reproducibility["lawVII"][boundary])
        self.assertEqual(0.0, reproducibility["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, reproducibility["internalDiagnostics"]["workflowTokensOwned"])
        self.assertEqual(0, reproducibility["internalDiagnostics"]["tradesPlaced"])

    def test_eo_s_completed_workflow_produces_immutable_enterprise_snapshot(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_BROKER_SIM_MARKET_SESSION="CLOSED")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["enterpriseReproducibilityFramework"]["enterpriseSnapshots"])
                and bool(item["enterpriseReproducibilityFramework"]["enterpriseSnapshots"][-1]["performanceTruthId"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            reproducibility = state["enterpriseReproducibilityFramework"]
            snapshot = reproducibility["enterpriseSnapshots"][-1]
            workflow_id = state["workflowRuntimeMonitor"]["recentCompletedWorkflows"][0]["workflowIdentifier"]

            self.assertTrue(snapshot["snapshotId"].startswith("ERF-SNAP-"))
            self.assertEqual(workflow_id, snapshot["workflowId"])
            self.assertTrue(snapshot["workflowTokenId"])
            self.assertTrue(snapshot["decisionObjectId"].startswith("DO-"))
            self.assertTrue(snapshot["performanceTruthId"])
            self.assertIn("promptPackageVersion", snapshot)
            self.assertIn("strategyPackageVersion", snapshot)
            self.assertIn("decisionObjectSchemaVersion", snapshot)
            self.assertIn("marketContextVersion", snapshot)
            self.assertIn("configurationVersion", snapshot)
            self.assertIn("providerVersion", snapshot)
            self.assertTrue(snapshot["immutable"])
            self.assertEqual(snapshot["checksum"], snapshot["hash"])
            self.assertEqual("Exact Match", snapshot["replayStatus"])
        finally:
            self._restore_env(previous)

    def test_eo_s_replay_certification_difference_analysis_and_provenance_are_explicit(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["enterpriseReproducibilityFramework"]["replayCertification"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            reproducibility = state["enterpriseReproducibilityFramework"]
            certification = reproducibility["replayCertification"][-1]
            difference = reproducibility["differenceAnalysis"][-1]
            snapshot = reproducibility["latestEnterpriseSnapshot"]

            for check in (
                "decisionMatch",
                "promptMatch",
                "strategyMatch",
                "configurationMatch",
                "decisionObjectMatch",
                "performanceTruthMatch",
                "marketContextMatch",
                "referenceIntegrity",
                "hashValidation",
            ):
                self.assertIn(check, certification["checks"])
            self.assertIn(certification["replayStatus"], ("Exact Match", "Functionally Equivalent", "Minor Difference", "Material Difference", "Replay Failed"))
            self.assertTrue(difference["allDifferencesExplained"])
            self.assertTrue(difference["differences"])
            self.assertTrue(snapshot["dataProvenance"])
            for provenance in snapshot["dataProvenance"]:
                for key in ("origin", "timestamp", "creator", "version", "validation", "hash", "repositoryReference"):
                    self.assertIn(key, provenance)
            self.assertTrue(snapshot["replayInputs"]["usesHistoricalMarketInformationOnly"])
            self.assertFalse(snapshot["replayInputs"]["usesCurrentApiProviders"])
        finally:
            self._restore_env(previous)

    def test_eo_s_captures_environment_prompt_strategy_configuration_provider_portfolio_and_model(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["enterpriseReproducibilityFramework"]["enterpriseSnapshots"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            reproducibility = state["enterpriseReproducibilityFramework"]
            self.assertTrue(reproducibility["environmentSnapshots"])
            self.assertTrue(reproducibility["promptSnapshots"])
            self.assertTrue(reproducibility["strategySnapshots"])
            self.assertTrue(reproducibility["configurationSnapshots"])
            self.assertTrue(reproducibility["providerSnapshots"])
            self.assertTrue(reproducibility["portfolioSnapshots"])
            self.assertTrue(reproducibility["modelSnapshots"])
            self.assertTrue(reproducibility["marketSnapshots"])
            self.assertTrue(reproducibility["determinismPolicy"]["historicalArtifactsOnly"])
            self.assertFalse(reproducibility["determinismPolicy"]["liveMarketDataAllowedInReplay"])
            self.assertTrue(reproducibility["providerSnapshots"][-1]["replayDoesNotDependOnCurrentProviders"])
            self.assertIn("systemPromptHash", reproducibility["modelSnapshots"][-1])
        finally:
            self._restore_env(previous)

    def test_eo_s_reproducibility_feeds_learning_replay_and_commander_review(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: bool(item["enterpriseReproducibilityFramework"]["snapshotArchive"]),
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            reproducibility = state["enterpriseReproducibilityFramework"]
            self.assertGreaterEqual(reproducibility["reproducibilityScore"]["overallScore"], 80)
            self.assertTrue(reproducibility["historianFeed"]["replayFailuresBecomeLessons"])
            self.assertTrue(reproducibility["enterpriseLearningFeed"]["weaknessDetectionAvailable"])
            self.assertTrue(reproducibility["promptEvolutionFeed"]["identicalHistoricalEnvironmentRequired"])
            self.assertTrue(reproducibility["strategyEvolutionFeed"]["identicalHistoricalEnvironmentRequired"])
            self.assertTrue(reproducibility["decisionLaboratoryFeed"]["historicalEnvironmentReconstructedBeforeExperiment"])
            self.assertIn("reproducibilitySummary", reproducibility["commanderReviewFeed"])
            self.assertTrue(reproducibility["historicalCoverage"]["coveragePercent"])
            self.assertTrue(reproducibility["provenanceGraph"])
        finally:
            self._restore_env(previous)

    def test_eo_s_enterprise_reproducibility_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("enterpriseReproducibilityFramework", js)
        self.assertIn("function renderEnterpriseReproducibilityFramework()", js)
        for phrase in (
            "Enterprise Reproducibility Framework",
            "Enterprise Snapshots",
            "Replay Browser",
            "Replay Certification",
            "Difference Analysis",
            "Environment Snapshots",
            "Prompt Snapshots",
            "Strategy Snapshots",
            "Configuration Snapshots",
            "Provider Snapshots",
            "Portfolio Snapshots",
            "Replay Statistics",
            "Historical Coverage",
            "Provenance Graph",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "erf-summary",
            "erf-snapshots",
            "erf-replay-browser",
            "erf-certification",
            "erf-differences",
            "erf-environment",
            "erf-prompts",
            "erf-strategies",
            "erf-configuration",
            "erf-providers",
            "erf-portfolio",
            "erf-replay-statistics",
            "erf-coverage",
            "erf-provenance",
            "erf-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Replay Certification", command_bridge)
        self.assertNotIn("Provenance Graph", command_bridge)

    def test_eo_t_enterprise_operational_guardrails_are_governance_only(self) -> None:
        guardrails = create_runtime().state()["enterpriseOperationalGuardrails"]

        self.assertEqual("Enterprise Operational Guardrails", guardrails["frameworkName"])
        self.assertEqual("EO-T", guardrails["engineeringOrder"])
        self.assertEqual("OPERATIONAL_GOVERNANCE_ONLY", guardrails["constitutionalMode"])
        self.assertEqual(
            "ARGOS shall never knowingly operate outside the conditions under which its decisions are scientifically valid.",
            guardrails["constitutionalMission"],
        )
        self.assertEqual("Should ARGOS continue operating?", guardrails["constitutionalQuestion"])
        for boundary in (
            "executesWorkflows",
            "ownsWorkflowTokens",
            "tradesSecurities",
            "placesTrades",
            "modifiesPrompts",
            "modifiesStrategies",
            "overridesConstitutionalGovernance",
            "overridesCommanderAuthority",
        ):
            self.assertFalse(guardrails["lawVII"][boundary])
        self.assertEqual(0.0, guardrails["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, guardrails["internalDiagnostics"]["workflowTokensOwned"])
        self.assertEqual(0, guardrails["internalDiagnostics"]["tradesPlaced"])

    def test_eo_t_readiness_registry_and_thresholds_authorize_nominal_operation(self) -> None:
        guardrails = create_runtime().state()["enterpriseOperationalGuardrails"]

        self.assertGreaterEqual(guardrails["enterpriseReadinessScore"], 90)
        self.assertEqual("Authorized", guardrails["readinessState"])
        self.assertTrue(guardrails["tradingAuthorization"]["paperTradingAuthorized"])
        self.assertTrue(guardrails["tradingAuthorization"]["workflowCreationAuthorized"])
        names = {item["guardrail"] for item in guardrails["guardrailRegistry"]}
        for name in (
            "Health Guardrails",
            "Decision Object Guardrails",
            "Market Data Guardrails",
            "Workflow Guardrails",
            "Prompt Guardrails",
            "Strategy Guardrails",
            "Configuration Guardrails",
            "Credit Guardrails",
            "Portfolio Guardrails",
            "Market Condition Guardrails",
            "Constitutional Guardrails",
            "Recovery Guardrails",
        ):
            self.assertIn(name, names)
        self.assertTrue(guardrails["thresholdConfiguration"]["commanderConfigurable"])
        self.assertEqual("Pause", guardrails["thresholdConfiguration"]["uncertaintyResponse"])

    def test_eo_t_workflow_start_records_pre_execution_authorization_and_audit(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5")
        try:
            runtime = create_runtime()
            state = runtime.start_paper_self_training()
            runtime.halt_paper_self_training()

            guardrails = state["enterpriseOperationalGuardrails"]
            authorization = guardrails["authorizationHistory"][-1]
            audit = guardrails["guardrailAuditHistory"][-1]
            self.assertTrue(authorization["authorizationId"].startswith("EOG-AUTH-"))
            self.assertEqual("Authorize Workflow", authorization["decision"])
            self.assertEqual("Continue", authorization["response"])
            self.assertEqual("Not Required", authorization["commanderNotification"])
            self.assertTrue(authorization["hash"])
            self.assertTrue(audit["auditId"].startswith("EOG-AUD-"))
            self.assertTrue(audit["immutable"])
            self.assertIn("Enterprise Operational Guardrails", str(state["eab"]))
        finally:
            self._restore_env(previous)

    def test_eo_t_safe_mode_emergency_halt_and_recovery_policies_preserve_artifacts(self) -> None:
        guardrails = create_runtime().state()["enterpriseOperationalGuardrails"]

        self.assertTrue(guardrails["safeMode"]["stopsNewWorkflows"])
        self.assertTrue(guardrails["safeMode"]["completesExistingWorkflowsSafely"])
        self.assertTrue(guardrails["safeMode"]["preservesEnterpriseState"])
        self.assertFalse(guardrails["safeMode"]["corruptsConstitutionalArtifacts"])
        self.assertTrue(guardrails["emergencyHaltPolicy"]["stopsWorkflowCreation"])
        self.assertTrue(guardrails["emergencyHaltPolicy"]["preservesWorkflowTokens"])
        self.assertTrue(guardrails["emergencyHaltPolicy"]["preservesDecisionObjects"])
        self.assertTrue(guardrails["emergencyHaltPolicy"]["preservesPerformanceTruth"])
        self.assertTrue(guardrails["recoveryAuthorization"]["guardrailsReevaluated"])
        self.assertTrue(guardrails["recoveryAuthorization"]["explicitRecoveryRequired"])
        self.assertIn("LAW VII", guardrails["commanderOverridePolicy"]["absoluteProtections"])

    def test_eo_t_operational_guardrails_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("enterpriseOperationalGuardrails", js)
        self.assertIn("function renderEnterpriseOperationalGuardrails()", js)
        for phrase in (
            "Enterprise Operational Guardrails",
            "Guardrail Registry",
            "Threshold Configuration",
            "Authorization History",
            "Emergency Halts",
            "Safe Mode Events",
            "Recovery Events",
            "Commander Overrides",
            "Health Thresholds",
            "Quality Thresholds",
            "Budget Thresholds",
            "Dependency Status",
            "Operational Timeline",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "eog-summary",
            "eog-registry",
            "eog-thresholds",
            "eog-authorization",
            "eog-emergency",
            "eog-safe-mode",
            "eog-recovery",
            "eog-overrides",
            "eog-health",
            "eog-quality",
            "eog-budget",
            "eog-dependencies",
            "eog-timeline",
            "eog-audit",
            "eog-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Guardrail Registry", command_bridge)
        self.assertNotIn("Emergency Halts", command_bridge)

    def test_eo_v_enterprise_experiment_scheduler_is_planning_only(self) -> None:
        scheduler = create_runtime().state()["enterpriseExperimentScheduler"]

        self.assertEqual("Enterprise Experiment Scheduler", scheduler["schedulerName"])
        self.assertEqual("EO-V", scheduler["engineeringOrder"])
        self.assertEqual("RESEARCH_PLANNING_ONLY", scheduler["constitutionalMode"])
        self.assertEqual(
            "Ensure every enterprise experiment maximizes institutional learning while respecting constitutional governance and enterprise resource limits.",
            scheduler["constitutionalMission"],
        )
        self.assertEqual("What experiment will most improve ARGOS today?", scheduler["constitutionalQuestion"])
        for boundary in (
            "executesWorkflows",
            "ownsWorkflowTokens",
            "tradesSecurities",
            "makesInvestmentDecisions",
            "promotesProductionChanges",
            "modifiesPrompts",
            "modifiesStrategies",
            "overridesCommanderAuthority",
        ):
            self.assertFalse(scheduler["lawVII"][boundary])
        self.assertEqual(0.0, scheduler["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, scheduler["internalDiagnostics"]["workflowTokensOwned"])
        self.assertEqual(0, scheduler["internalDiagnostics"]["tradesPlaced"])
        self.assertEqual(0, scheduler["internalDiagnostics"]["experimentsExecuted"])

    def test_eo_v_research_backlog_contains_immutable_experiment_objects_with_hypotheses(self) -> None:
        scheduler = create_runtime().state()["enterpriseExperimentScheduler"]
        backlog = scheduler["researchBacklog"]

        self.assertTrue(backlog)
        for experiment in backlog:
            for key in (
                "experimentId",
                "title",
                "description",
                "category",
                "researchQuestion",
                "hypothesis",
                "successCriteria",
                "expectedBenefit",
                "estimatedInformationGain",
                "estimatedCreditCost",
                "estimatedRuntime",
                "priority",
                "dependencies",
                "commanderStatus",
                "laboratoryStatus",
                "validationStatus",
                "finalOutcome",
                "knowledgeProduced",
                "hash",
            ):
                self.assertIn(key, experiment)
            self.assertTrue(experiment["immutable"])
            self.assertIn(experiment["state"], scheduler["experimentStates"])
            self.assertIn(experiment["category"], scheduler["experimentCategories"])

    def test_eo_v_priority_information_gain_resource_and_law_viii_are_explicit(self) -> None:
        scheduler = create_runtime().state()["enterpriseExperimentScheduler"]

        self.assertTrue(scheduler["priorityCalculations"])
        top = scheduler["priorityCalculations"][0]
        for key in (
            "priorityScore",
            "expectedEnterpriseBenefit",
            "estimatedInformationGain",
            "knowledgeGap",
            "riskReduction",
            "estimatedCreditCost",
            "researchAge",
            "commanderPriority",
            "knowledgePerCredit",
        ):
            self.assertIn(key, top)
        self.assertTrue(scheduler["informationGainEstimates"])
        self.assertTrue(scheduler["budgetAllocation"]["noExperimentExceedsAllocatedResources"])
        self.assertGreaterEqual(scheduler["laboratoryCapacity"]["availableExperimentSlots"], 0)
        self.assertTrue(scheduler["lawVIIIFrugality"]["reusesHistoricalData"])
        self.assertTrue(scheduler["lawVIIIFrugality"]["maximizesKnowledgePerCredit"])

    def test_eo_v_queue_calendar_dependencies_and_feeds_are_managed(self) -> None:
        scheduler = create_runtime().state()["enterpriseExperimentScheduler"]

        self.assertTrue(scheduler["experimentQueue"])
        self.assertTrue(scheduler["dependencyGraph"])
        self.assertIn("today", scheduler["schedulingCalendar"])
        self.assertIn("thisWeek", scheduler["schedulingCalendar"])
        self.assertTrue(scheduler["knowledgeYieldMetrics"]["rejectedHypothesesValuable"])
        self.assertTrue(scheduler["researchVelocity"]["diversityProtected"])
        self.assertTrue(scheduler["decisionLaboratoryFeed"]["approvedResearchPlansRequired"])
        self.assertTrue(scheduler["enterpriseLearningFeed"]["researchOpportunitiesConverted"] >= 0)
        self.assertTrue(scheduler["promptEvolutionFeed"]["candidatePromptsPrioritized"] >= 0)
        self.assertTrue(scheduler["strategyEvolutionFeed"]["candidateStrategiesSequenced"] >= 0)
        self.assertIn("enterpriseCuriosityIndex", scheduler["researchDashboard"])

    def test_eo_v_enterprise_experiment_scheduler_engineering_mode_is_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        engineering = html.split('id="engineering-mode"', 1)[1]
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("enterpriseExperimentScheduler", js)
        self.assertIn("function renderEnterpriseExperimentScheduler()", js)
        for phrase in (
            "Enterprise Experiment Scheduler",
            "Research Backlog",
            "Experiment Queue",
            "Priority Calculations",
            "Information Gain Estimates",
            "Dependency Graph",
            "Scheduling Calendar",
            "Laboratory Capacity",
            "Budget Allocation",
            "Knowledge Yield Metrics",
            "Research Velocity",
            "Commander Priorities",
            "Experiment History",
            "Internal Diagnostics",
        ):
            self.assertIn(phrase, engineering)
        for element_id in (
            "ees-summary",
            "ees-backlog",
            "ees-queue",
            "ees-priority",
            "ees-information",
            "ees-dependencies",
            "ees-calendar",
            "ees-capacity",
            "ees-budget",
            "ees-yield",
            "ees-velocity",
            "ees-commander",
            "ees-history",
            "ees-diagnostics",
        ):
            self.assertIn(f'id="{element_id}"', engineering)
            self.assertIn(f'("{element_id}")', js)
        self.assertNotIn("Priority Calculations", command_bridge)
        self.assertNotIn("Experiment Queue", command_bridge)

    def test_eo_bi_commander_strategic_dashboard_payload_is_created(self) -> None:
        dashboard = create_runtime().state()["commanderStrategicDashboard"]

        self.assertEqual("Commander Strategic Dashboard", dashboard["dashboardName"])
        self.assertEqual("EO-BI", dashboard["engineeringOrder"])
        self.assertEqual("STRATEGIC_OBSERVATION_ONLY", dashboard["constitutionalMode"])
        for section in (
            "command_state",
            "capital_state",
            "readiness",
            "reality_fidelity",
            "strategic_risk",
            "correlation",
            "active_portfolio",
            "performance",
            "attribution",
            "stress_and_survival",
            "capital_allocation",
            "learning_and_research",
            "intelligence_efficiency",
            "attention_queue",
            "strategic_recommendation",
            "data_freshness",
        ):
            self.assertIn(section, dashboard)

    def test_eo_bi_capital_state_uses_performance_truth_authority(self) -> None:
        runtime = create_runtime()
        runtime.deposit_user_funds(10000.0)
        state = runtime.state()
        dashboard_capital = state["commanderStrategicDashboard"]["capital_state"]["data"]
        truth_capital = state["performanceTruthEngine"]["calculations"]["portfolio"]

        self.assertEqual(truth_capital["portfolioValue"], dashboard_capital["portfolioEquity"])
        self.assertEqual(truth_capital["cash"], dashboard_capital["cash"])
        self.assertIn("capitalHeartbeat", dashboard_capital)
        self.assertFalse(state["commanderStrategicDashboard"]["internalDiagnostics"]["mutatesLedgers"])

    def test_eo_bi_reality_risk_correlation_and_survival_sources_are_consumed(self) -> None:
        state = create_runtime().state()
        dashboard = state["commanderStrategicDashboard"]

        self.assertEqual(
            state["enterpriseRealityCalibrationEngine"]["commanderSummary"]["overallRealityFidelityScore"],
            dashboard["reality_fidelity"]["data"]["overallRealityFidelityScore"],
        )
        self.assertEqual(
            state["enterpriseRiskFactorEngine"]["commanderSummary"]["compositeRiskScore"],
            dashboard["strategic_risk"]["data"]["compositeEnterpriseRiskScore"],
        )
        self.assertEqual(
            state["correlationIntelligenceEngine"]["commanderSummary"]["correlationRiskScore"],
            dashboard["correlation"]["data"]["correlationRiskScore"],
        )
        self.assertEqual(
            state["stressTestingEngine"]["commanderSummary"]["latestStressLevel"],
            dashboard["stress_and_survival"]["data"]["latestStressLevel"],
        )
        self.assertEqual(
            state["blackSwanSimulationEngine"]["commanderSummary"]["survivalScore"],
            dashboard["stress_and_survival"]["data"]["blackSwanSurvivalScore"],
        )
        self.assertEqual(
            state["monteCarloPortfolioEngine"]["commanderSummary"]["probabilityOfLoss"],
            dashboard["stress_and_survival"]["data"]["monteCarloProbabilityOfLoss"],
        )

    def test_eo_bi_active_portfolio_performance_learning_and_credit_are_separated(self) -> None:
        state = create_runtime().state()
        dashboard = state["commanderStrategicDashboard"]

        self.assertEqual(
            state["traderCommandBridge"]["summary"]["total_open_positions"],
            dashboard["active_portfolio"]["data"]["activePositions"],
        )
        self.assertIn("realizedPerformance", dashboard["performance"]["data"])
        self.assertIn("unrealizedPerformance", dashboard["performance"]["data"])
        self.assertEqual(
            state["closedPositionTruthBuilder"]["metrics"]["truthRecordCount"],
            dashboard["learning_and_research"]["data"]["completedTradeObservations"],
        )
        self.assertEqual(
            state["costs"].today_api_credits_usd if hasattr(state["costs"], "today_api_credits_usd") else state["costs"]["today_api_credits_usd"],
            dashboard["intelligence_efficiency"]["data"]["creditsUsedToday"],
        )

    def test_eo_bi_attention_queue_sorts_and_recommendation_is_deterministic(self) -> None:
        dashboard_service = CommanderStrategicDashboard()
        payload = dashboard_service.snapshot(
            timestamp_utc="2026-07-09T00:00:00Z",
            enterprise_risk_factor={
                "commanderSummary": {"compositeRiskScore": 91.0, "riskLevel": "critical", "recommendedRiskActions": ("halt",), "topRiskFactors": ()},
                "riskOfficeFeed": {"haltRecommended": True},
                "latestRiskFactorRecord": {"timestamp": "2026-07-09T00:00:00Z", "composite_risk_score": 91.0},
            },
            enterprise_reality_calibration={
                "commanderSummary": {"overallRealityFidelityScore": 52.0, "learningReliabilityState": "unsafe", "latestCalibrationTimestamp": "2026-07-09T00:00:00Z"},
                "latestCalibrationReport": {"timestamp": "2026-07-09T00:00:00Z", "execution_fidelity_score": 52.0, "valuation_fidelity_score": 52.0, "truth_reliability_score": 52.0},
            },
            trader_command_bridge={"summary": {"totalOpenPositions": 0}},
        )
        queue = payload["attention_queue"]

        self.assertEqual("CRITICAL", queue[0]["severity"])
        self.assertEqual("halt_trading", payload["strategic_recommendation"]["recommendation"])
        self.assertTrue(payload["strategic_recommendation"]["deterministic"])
        self.assertFalse(payload["strategic_recommendation"]["aiUsed"])

    def test_eo_bi_missing_sources_are_marked_without_false_zero_live_claims(self) -> None:
        payload = CommanderStrategicDashboard().snapshot(timestamp_utc="2026-07-09T00:00:00Z")

        self.assertTrue(payload["capital_state"]["stale"])
        self.assertTrue(payload["reality_fidelity"]["stale"])
        self.assertTrue(payload["strategic_risk"]["stale"])
        self.assertIn("unknown", payload["command_state"]["data"]["marketSession"])
        self.assertGreaterEqual(len(payload["attention_queue"]), 1)

    def test_eo_bi_dashboard_does_not_mutate_or_invoke_ai(self) -> None:
        dashboard = create_runtime().state()["commanderStrategicDashboard"]

        self.assertFalse(dashboard["internalDiagnostics"]["mutatesPositions"])
        self.assertFalse(dashboard["internalDiagnostics"]["mutatesLedgers"])
        self.assertFalse(dashboard["internalDiagnostics"]["mutatesTruthRecords"])
        self.assertFalse(dashboard["internalDiagnostics"]["placesTrades"])
        self.assertEqual(0.0, dashboard["internalDiagnostics"]["apiCreditsConsumed"])
        self.assertEqual(0, dashboard["lawVIII"]["routineAiInvocations"])
        self.assertFalse(dashboard["commander_actions"]["directPositionMutation"])
        self.assertFalse(dashboard["commander_actions"]["directLedgerMutation"])
        self.assertFalse(dashboard["commander_actions"]["directTruthMutation"])

    def test_eo_bi_ui_and_route_are_wired_with_engineering_separation(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        css = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "styles.css").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        command_bridge = html.split('id="command-bridge"', 1)[1].split('id="executive-subcommand-bridge"', 1)[0]

        self.assertIn("/api/commander/strategic-dashboard", server)
        self.assertIn("commanderStrategicDashboard", js)
        self.assertIn("function renderCommanderStrategicDashboard()", js)
        self.assertIn('id="commander-strategic-dashboard"', command_bridge)
        for element_id in (
            "csd-command-state",
            "csd-capital",
            "csd-heartbeat",
            "csd-readiness",
            "csd-reality",
            "csd-risk",
            "csd-portfolio",
            "csd-performance",
            "csd-stress",
            "csd-learning",
            "csd-attention",
            "csd-navigation",
        ):
            self.assertIn(f'id="{element_id}"', command_bridge)
            self.assertIn(f'("{element_id}")', js)
        self.assertIn(".commander-strategic-dashboard", css)
        self.assertNotIn("audit_reference", command_bridge)
        self.assertNotIn("provider versions", command_bridge.lower())

    def test_eo_bn_commander_briefing_record_is_created_with_schema(self) -> None:
        briefing = create_runtime().state()["commanderBriefingGenerator"]
        record = briefing["latestBriefingRecord"]

        self.assertEqual("Commander Briefing Generator", briefing["generatorName"])
        self.assertEqual("EO-BN", briefing["engineeringOrder"])
        self.assertEqual("morning_readiness", record["briefing_type"])
        for key in (
            "commander_briefing_id",
            "briefing_window_start",
            "briefing_window_end",
            "generated_at",
            "enterprise_mode",
            "overall_status",
            "executive_summary",
            "capital_summary",
            "portfolio_summary",
            "performance_summary",
            "benchmark_summary",
            "risk_summary",
            "position_summary",
            "execution_summary",
            "reality_fidelity_summary",
            "enterprise_health_summary",
            "stress_and_survival_summary",
            "learning_summary",
            "experiment_summary",
            "strategy_evolution_summary",
            "prompt_evolution_summary",
            "intelligence_efficiency_summary",
            "material_changes",
            "critical_alerts",
            "decisions_required",
            "recommended_actions",
            "recommended_action_rationales",
            "deferred_items",
            "data_freshness",
            "degraded_sources",
            "evidence_references",
            "narrative_mode",
            "audit_reference",
            "hash",
        ):
            self.assertIn(key, record)
        self.assertTrue(record["immutable"])
        self.assertEqual(len(record["recommended_actions"]), len(record["recommended_action_rationales"]))
        self.assertTrue(all(item["action"] in record["recommended_actions"] for item in record["recommended_action_rationales"]))
        self.assertTrue(all(item["reasoning"].endswith(".") for item in record["recommended_action_rationales"]))

    def test_eo_bn_briefing_types_templates_and_sections_are_supported(self) -> None:
        generator = create_runtime().commander_briefing_generator
        for briefing_type in (
            "morning_readiness",
            "intraday_update",
            "end_of_day",
            "critical_incident",
            "weekly_strategic",
            "learning_and_experiment",
            "portfolio_and_risk",
            "ad_hoc",
        ):
            snapshot = generator.generate(
                briefing_type=briefing_type,
                briefing_window_start="2026-07-09T00:00:00Z",
                briefing_window_end="2026-07-09T00:05:00Z",
                generated_at="2026-07-09T00:05:00Z",
                sources={},
            )
            self.assertEqual(briefing_type, snapshot["latestBriefingRecord"]["briefing_type"])
            self.assertIn(briefing_type, snapshot["briefingTemplates"])

    def test_eo_bn_end_of_day_and_weekly_briefings_distinguish_truth_evidence(self) -> None:
        runtime = create_runtime()
        runtime.deposit_user_funds(10000.0)
        state = runtime.generate_commander_briefing("end_of_day")
        record = state["commanderBriefing"]

        self.assertIn("realizedPerformance", record["performance_summary"])
        self.assertIn("unrealizedPerformance", record["performance_summary"])
        self.assertIn("benchmarkReturn", record["benchmark_summary"])
        weekly = runtime.generate_commander_briefing("weekly_strategic")["commanderBriefing"]
        self.assertIn("sampleSizeConfidence", weekly["benchmark_summary"])
        self.assertTrue(weekly["evidence_references"])

    def test_eo_bn_material_change_detection_and_prioritization_are_deterministic(self) -> None:
        generator = CommanderBriefingGenerator()
        sources = {
            "commanderStrategicDashboard": {
                "command_state": {"data": {"tradingMode": "PAPER"}},
                "strategic_risk": {"data": {"compositeEnterpriseRiskScore": 82, "riskLevel": "high"}},
                "reality_fidelity": {"data": {"overallRealityFidelityScore": 55}},
                "active_portfolio": {"data": {"positionsWithExitRecommendations": 1}},
                "attention_queue": (),
                "data_freshness": {},
            }
        }
        snapshot = generator.generate(
            briefing_type="critical_incident",
            briefing_window_start="A",
            briefing_window_end="B",
            generated_at="B",
            sources=sources,
        )
        record = snapshot["latestBriefingRecord"]

        self.assertTrue(record["material_changes"])
        self.assertEqual("require_reality_calibration", record["recommended_operating_posture"])
        self.assertEqual("CRITICAL", record["critical_alerts"][0]["severity"])
        self.assertEqual("Enterprise Reality Calibration Engine", record["critical_alerts"][0]["sourceEngine"])
        self.assertTrue(all(item["actionable"] for item in record["decisions_required"]))

    def test_eo_bn_material_change_detection_ignores_immaterial_fluctuations(self) -> None:
        snapshot = CommanderBriefingGenerator().generate(
            briefing_type="intraday_update",
            briefing_window_start="A",
            briefing_window_end="B",
            generated_at="B",
            sources={"commanderStrategicDashboard": {"strategic_risk": {"data": {"compositeEnterpriseRiskScore": 2}}, "reality_fidelity": {"data": {"overallRealityFidelityScore": 99}}, "active_portfolio": {"data": {"positionsWithExitRecommendations": 0}}, "attention_queue": (), "data_freshness": {}}},
        )

        self.assertEqual((), snapshot["latestBriefingRecord"]["material_changes"])
        self.assertEqual("continue_normal_operations", snapshot["latestBriefingRecord"]["recommended_operating_posture"])

    def test_eo_bn_freshness_missing_sources_and_evidence_traceability_are_explicit(self) -> None:
        snapshot = CommanderBriefingGenerator().generate(
            briefing_type="ad_hoc",
            briefing_window_start="A",
            briefing_window_end="B",
            generated_at="B",
            sources={},
        )
        record = snapshot["latestBriefingRecord"]

        self.assertIn("commanderStrategicDashboard", record["data_freshness"])
        self.assertTrue(record["data_freshness"]["commanderStrategicDashboard"]["unavailable"])
        self.assertIn("commanderStrategicDashboard", record["degraded_sources"])
        self.assertTrue(record["evidence_references"])
        self.assertNotEqual(0, len(record["evidence_references"]))

    def test_eo_bn_routine_generation_uses_no_ai_and_optional_narrative_is_guarded(self) -> None:
        generator = CommanderBriefingGenerator()
        snapshot = generator.generate(
            briefing_type="ad_hoc",
            briefing_window_start="A",
            briefing_window_end="B",
            generated_at="B",
            sources={},
            narrative_requested=True,
        )
        record = snapshot["latestBriefingRecord"]

        self.assertEqual("REJECTED_OPTIONAL_NARRATIVE_DISABLED", record["narrative_mode"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        rejected = generator.render_optional_narrative("", None, "invented")
        self.assertEqual("REJECTED", rejected["status"])
        self.assertEqual("structured_briefing_required", rejected["reason"])

    def test_eo_bn_dashboard_daily_review_and_notification_integrations_are_wired(self) -> None:
        runtime = create_runtime()
        state = runtime.generate_commander_briefing("critical_incident")

        self.assertIn("latest_briefing", state["commanderStrategicDashboard"])
        self.assertEqual("critical_incident", state["commanderStrategicDashboard"]["latest_briefing"]["latestBriefingType"])
        self.assertIn("latestCommanderBriefing", state["commanderDailyReviewWorkspace"])
        self.assertIn("commanderBriefingGenerator", state["commanderDailyReviewWorkspace"])
        self.assertIn("notificationFeed", state["commanderBriefingGenerator"])
        if state["commanderBriefing"]["critical_alerts"]:
            self.assertTrue(any(note["source_event_id"] or note["notification_id"] for note in state["cnac"]["notifications"]))

    def test_eo_bn_idempotency_export_and_no_mutation_boundaries(self) -> None:
        runtime = create_runtime()
        first = runtime.state()["commanderBriefingGenerator"]
        second = runtime.state()["commanderBriefingGenerator"]

        self.assertGreaterEqual(len(first["briefingRecords"]), 1)
        self.assertGreaterEqual(len(second["briefingRecords"]), len(first["briefingRecords"]))
        briefing_id = second["latestBriefingRecord"]["commander_briefing_id"]
        exported = runtime.commander_briefing_generator.export(briefing_id, "markdown")
        self.assertIn("# Morning Readiness", exported)
        diagnostics = second["internalDiagnostics"]
        self.assertFalse(diagnostics["mutatesPositions"])
        self.assertFalse(diagnostics["mutatesLedgers"])
        self.assertFalse(diagnostics["mutatesTruthRecords"])
        self.assertEqual(0.0, diagnostics["apiCreditsConsumed"])

    def test_eo_bn_ui_and_routes_are_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        self.assertIn("/api/commander/briefing", server)
        self.assertIn("commanderBriefingGenerator", js)
        self.assertIn('id="csd-briefing"', html)
        self.assertIn("latest_briefing", js)

    def test_eo_bx_grand_strategy_record_is_created_immutable_and_versioned(self) -> None:
        strategy = create_runtime().state()["enterpriseGrandStrategyEngine"]
        record = strategy["activeGrandStrategyRecord"]

        self.assertEqual("Enterprise Grand Strategy Engine", strategy["engineName"])
        self.assertEqual("EO-BX", strategy["engineeringOrder"])
        self.assertEqual("STRATEGIC_POLICY_ONLY_NO_TRADING", strategy["constitutionalMode"])
        self.assertTrue(record["grand_strategy_id"].startswith("GSR-"))
        self.assertTrue(record["strategy_version"].startswith("GS-"))
        self.assertTrue(record["immutable"])
        self.assertTrue(record["hash"])
        for key in (
            "commander_intent_reference",
            "constitutional_reference",
            "strategic_posture",
            "primary_objectives",
            "prohibited_actions",
            "capital_preservation_policy",
            "benchmark_objective",
            "risk_tolerance",
            "strategy_portfolio_policy",
            "research_priorities",
            "experiment_priorities",
            "capability_priorities",
            "operational_maturity_targets",
            "live_readiness_policy",
            "confidence",
            "evidence_references",
            "deterministic_reasoning",
            "audit_reference",
        ):
            self.assertIn(key, record)

    def test_eo_bx_idempotent_inputs_and_material_revision_versioning(self) -> None:
        engine = EnterpriseGrandStrategyEngine()
        stable = {"enterpriseRealityCalibrationEngine": {"commanderSummary": {"overallRealityFidelityScore": 95}}, "enterpriseRiskFactorEngine": {"commanderSummary": {"compositeRiskScore": 10}}}
        first = engine.generate(timestamp_utc="A", planning_horizon="monthly", sources=stable)
        second = engine.generate(timestamp_utc="B", planning_horizon="monthly", sources=stable)
        changed = engine.generate(timestamp_utc="C", planning_horizon="monthly", sources={"enterpriseRealityCalibrationEngine": {"commanderSummary": {"overallRealityFidelityScore": 45}}, "enterpriseRiskFactorEngine": {"commanderSummary": {"compositeRiskScore": 10}}})

        self.assertEqual(1, len(second["grandStrategyRecords"]))
        self.assertEqual(first["activeGrandStrategyRecord"]["strategy_version"], second["activeGrandStrategyRecord"]["strategy_version"])
        self.assertEqual(2, len(changed["grandStrategyRecords"]))
        self.assertEqual("GS-0002", changed["activeGrandStrategyRecord"]["strategy_version"])
        self.assertIn("strategic_posture", changed["activeGrandStrategyRecord"]["changed_policies"])

    def test_eo_bx_missing_intent_unsafe_fidelity_and_critical_risk_are_conservative(self) -> None:
        missing = EnterpriseGrandStrategyEngine().generate(timestamp_utc="A", sources={})["activeGrandStrategyRecord"]
        unsafe = EnterpriseGrandStrategyEngine().generate(timestamp_utc="A", sources={"enterpriseRealityCalibrationEngine": {"commanderSummary": {"overallRealityFidelityScore": 50}}})["activeGrandStrategyRecord"]
        critical = EnterpriseGrandStrategyEngine().generate(timestamp_utc="A", sources={"enterpriseRealityCalibrationEngine": {"commanderSummary": {"overallRealityFidelityScore": 95}}, "enterpriseRiskFactorEngine": {"commanderSummary": {"compositeRiskScore": 90}}})["activeGrandStrategyRecord"]

        self.assertEqual("COMMANDER-INTENT-MISSING-CONSERVATIVE", missing["commander_intent_reference"])
        self.assertEqual("preservation", missing["strategic_posture"])
        self.assertEqual("calibration_only", unsafe["strategic_posture"])
        self.assertEqual("defensive", critical["strategic_posture"])

    def test_eo_bx_short_term_returns_do_not_create_aggressive_posture(self) -> None:
        record = EnterpriseGrandStrategyEngine().generate(
            timestamp_utc="A",
            commander_intent={"intent_id": "CI-1", "live_trading_permission_state": "prohibited"},
            sources={
                "performanceTruthEngine": {"calculations": {"portfolio": {"alpha": 14.5}}},
                "closedPositionTruthBuilder": {"metrics": {"truthRecordCount": 2}},
                "enterpriseRealityCalibrationEngine": {"commanderSummary": {"overallRealityFidelityScore": 95}},
                "enterpriseRiskFactorEngine": {"commanderSummary": {"compositeRiskScore": 20}},
            },
        )["activeGrandStrategyRecord"]

        self.assertIn(record["strategic_posture"], {"cautious_growth", "preservation"})
        self.assertNotIn(record["strategic_posture"], {"opportunistic", "aggressive_research"})
        self.assertIn("recent gains do not justify aggression", " ".join(record["deterministic_reasoning"]))

    def test_eo_bx_policies_objectives_success_and_failure_conditions_are_generated(self) -> None:
        record = create_runtime().state()["enterpriseGrandStrategyEngine"]["activeGrandStrategyRecord"]

        self.assertGreaterEqual(len(record["primary_objectives"]), 3)
        for objective in record["primary_objectives"]:
            self.assertIn("targetMetric", objective)
            self.assertIn("targetValue", objective)
            self.assertIn("evidenceRequirement", objective)
        self.assertIn("requiredCashReservePercent", record["capital_preservation_policy"])
        self.assertIn("primaryBenchmark", record["benchmark_objective"])
        self.assertIn("acceptableCompositeRisk", record["risk_tolerance"])
        self.assertIn("promotionRequirements", record["strategy_portfolio_policy"])
        self.assertTrue(record["research_priorities"])
        self.assertTrue(record["experiment_priorities"])
        self.assertTrue(record["capability_priorities"])
        self.assertTrue(record["success_metrics"])
        self.assertTrue(record["failure_conditions"])
        self.assertTrue(all("strategicResponse" in item for item in record["failure_conditions"]))

    def test_eo_bx_maturity_live_readiness_and_market_policy_are_conservative(self) -> None:
        record = create_runtime().state()["enterpriseGrandStrategyEngine"]["activeGrandStrategyRecord"]
        maturity = record["operational_maturity_targets"]
        live = record["live_readiness_policy"]
        market = record["market_participation_policy"]

        self.assertIn(maturity["currentStage"], ("architectural", "broker_realistic", "lifecycle_complete", "scientifically_reproducible", "statistically_informative", "strategically_adaptive"))
        self.assertNotEqual("commander_authorized", live["state"])
        self.assertFalse(live["liveTradingEnabledByThisEngine"])
        self.assertFalse(live["checks"]["architectureAlone"])
        self.assertFalse(market["options"]["enabled"])
        self.assertFalse(market["crypto"]["enabled"])
        self.assertFalse(market["margin"]["enabled"])
        self.assertTrue(market["options"]["commanderAuthorizationRequired"])

    def test_eo_bx_ai_credit_policy_and_law_boundaries_are_explicit(self) -> None:
        strategy = create_runtime().state()["enterpriseGrandStrategyEngine"]
        record = strategy["activeGrandStrategyRecord"]

        self.assertIn("deterministic_scoring", record["AI_usage_policy"]["prohibitedUseCases"])
        self.assertLessEqual(record["credit_budget_policy"]["dailyCreditCeiling"], 25.0)
        self.assertEqual(0, strategy["lawVIII"]["routineAiInvocations"])
        self.assertFalse(strategy["internalDiagnostics"]["enablesLiveTrading"])
        self.assertFalse(strategy["internalDiagnostics"]["promotesStrategies"])
        self.assertFalse(strategy["internalDiagnostics"]["schedulesExperiments"])
        self.assertFalse(strategy["lawVII"]["amendsConstitution"])

    def test_eo_bx_conflict_resolution_precedence_records_conflicts(self) -> None:
        snapshot = EnterpriseGrandStrategyEngine().generate(
            timestamp_utc="A",
            commander_intent={"intent_id": "CI-LIVE", "live_trading_permission_state": "commander_authorized"},
            sources={"control": {"real_world_trading_active": False}, "enterpriseRealityCalibrationEngine": {"commanderSummary": {"overallRealityFidelityScore": 95}}},
        )
        record = snapshot["activeGrandStrategyRecord"]

        self.assertTrue(record["conflicts"])
        self.assertEqual("constitutional_law", record["conflicts"][0]["precedenceWinner"])
        self.assertEqual("constitutional_law", snapshot["conflictResolutionPrecedence"][0])

    def test_eo_bx_policy_feeds_are_available_to_existing_consumers(self) -> None:
        state = create_runtime().state()
        strategy = state["enterpriseGrandStrategyEngine"]

        for feed_name in (
            "capitalAllocationFeed",
            "portfolioConstructionFeed",
            "positionSizingFeed",
            "strategyEvolutionFeed",
            "promptEvolutionFeed",
            "experimentSchedulerFeed",
            "organizationalEvolutionFeed",
            "creditGovernorFeed",
        ):
            self.assertIn(feed_name, strategy)
        self.assertIn("grandStrategyFeed", state["capitalAllocationEngine"])
        self.assertIn("grandStrategyFeed", state["portfolioConstructionEngine"])
        self.assertIn("grandStrategyFeed", state["positionSizingEngine"])
        self.assertIn("grandStrategyFeed", state["strategyPackageManager"])
        self.assertIn("grandStrategyFeed", state["promptEvolutionEngine"])
        self.assertIn("grandStrategyFeed", state["enterpriseExperimentScheduler"])

    def test_eo_bx_dashboard_briefing_daily_review_and_routes_are_wired(self) -> None:
        state = create_runtime().state()
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        self.assertIn("grand_strategy", state["commanderStrategicDashboard"])
        self.assertIn("currentStrategicPosture", state["commanderStrategicDashboard"]["grand_strategy"])
        self.assertIn("grandStrategyPosture", state["commanderBriefingGenerator"]["latestBriefingRecord"]["strategy_evolution_summary"])
        self.assertIn("enterpriseGrandStrategy", state["commanderDailyReviewWorkspace"])
        self.assertIn("/api/grand-strategy/state", server)
        self.assertIn('id="csd-grand-strategy"', html)
        self.assertIn("enterpriseGrandStrategyEngine", js)

    def test_eo_bs_strategic_intelligence_command_exists_as_peer_advisory_org(self) -> None:
        command = StrategicIntelligenceCommand()
        snapshot = command.snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})

        self.assertEqual("Strategic Intelligence Command", snapshot["commandName"])
        self.assertEqual("EO-BS", snapshot["engineeringOrder"])
        self.assertTrue(snapshot["enterprisePeerOrganization"])
        self.assertTrue(snapshot["authorityBoundary"]["advisoryOnly"])
        self.assertFalse(snapshot["authorityBoundary"]["executesTrades"])
        self.assertFalse(snapshot["authorityBoundary"]["modifiesPortfolios"])
        self.assertEqual(0.0, snapshot["metrics"]["apiCost"])
        self.assertFalse(snapshot["lawVII"]["uncontrolledLoops"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])

    def test_eo_bs_standardized_reports_include_required_fields_and_horizons(self) -> None:
        state = create_runtime().state()
        sic = state["strategicIntelligenceCommand"]
        reports = sic["latestStrategicReports"]
        report_types = {report["report_type"] for report in reports}

        self.assertEqual(set(sic["supportedReportTypes"]), report_types)
        for report in reports:
            self.assertIn(report["time_horizon"], sic["timeHorizonFramework"])
            self.assertEqual("Strategic Intelligence Command", report["authoring_office"])
            self.assertTrue(report["supporting_evidence"])
            self.assertGreaterEqual(report["confidence_score"], 0)
            self.assertTrue(report["revision_history"])
            self.assertTrue(report["decision_traceability"])
            self.assertTrue(report["historian_archive_identifier"].startswith("HIST-SIC-"))

    def test_eo_bs_subordinate_office_interfaces_are_ready_for_future_orders(self) -> None:
        sic = create_runtime().state()["strategicIntelligenceCommand"]
        offices = {office["officeName"]: office for office in sic["subordinateOfficeInterfaces"]}

        expected = {
            "Blue Ocean Intelligence Office",
            "Disruption Intelligence Office",
            "Decline Intelligence Office",
            "Short Opportunity Office",
            "Market Structure Intelligence Office",
            "Capital Rotation Intelligence Office",
            "Strategic Synthesis Office",
        }
        self.assertEqual(expected, set(offices))
        for name, office in offices.items():
            expected_status = "OPERATIONAL" if name in {"Blue Ocean Intelligence Office", "Disruption Intelligence Office", "Decline Intelligence Office", "Short Opportunity Office", "Market Structure Intelligence Office", "Capital Rotation Intelligence Office", "Strategic Synthesis Office"} else "PLACEHOLDER_READY"
            self.assertEqual(expected_status, office["status"])
            self.assertFalse(office["mayTrade"])
            self.assertTrue(office["receivesDirectives"])

    def test_eo_bs_bridge_payload_exposes_required_commander_panels(self) -> None:
        bridge = create_runtime().state()["strategicIntelligenceCommand"]["strategicIntelligenceBridge"]

        for key in (
            "strategicThemes",
            "emergingIndustries",
            "decliningIndustries",
            "researchPriorities",
            "globalHeatMap",
            "timeHorizonDistribution",
            "strategicWatchList",
            "confidenceDistribution",
            "subordinateOfficeStatus",
            "historicalPerformance",
            "commanderDirectives",
        ):
            self.assertIn(key, bridge)
        self.assertTrue(bridge["strategicThemes"])
        self.assertTrue(bridge["emergingIndustries"])
        self.assertTrue(bridge["researchPriorities"])

    def test_eo_bs_runtime_dashboard_briefing_and_api_routes_are_wired(self) -> None:
        state = create_runtime().state()
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("strategicIntelligenceCommand", state)
        self.assertIn("strategic_intelligence", state["commanderStrategicDashboard"])
        self.assertIn("strategicIntelligenceCommand", state["commanderDailyReviewWorkspace"])
        briefing_evidence = state["commanderBriefingGenerator"]["latestBriefingRecord"]["evidence_references"]
        self.assertIn("strategicIntelligenceCommand", {item["recordId"] for item in briefing_evidence})
        self.assertIn("/api/strategic-intelligence/state", server)
        self.assertIn('id="strategic-intelligence-subcommand-bridge"', html)
        self.assertIn('"Strategic Intelligence": "strategic_intelligence_bridge"', js)
        self.assertIn("function renderStrategicIntelligenceBridge", js)

    def test_eo_bs_historian_librarian_workflow_and_audit_feeds_exist(self) -> None:
        sic = create_runtime().state()["strategicIntelligenceCommand"]

        self.assertEqual(len(sic["strategicReports"]), len(sic["historianFeed"]))
        self.assertEqual(len(sic["strategicReports"]), len(sic["librarianFeed"]))
        self.assertTrue(sic["enterpriseWorkflowIntegration"]["participatesInWorkflowTokenArchitecture"])
        self.assertFalse(sic["enterpriseWorkflowIntegration"]["lawVIIBypass"])
        self.assertTrue(sic["auditTrail"])
        self.assertTrue(sic["decisionQueue"])
        self.assertTrue(sic["executiveAssignmentFeed"])
        self.assertTrue(sic["inbox"])
        self.assertTrue(sic["outbox"])

    def test_eo_bs_snapshot_is_idempotent_for_unchanged_source_fingerprint(self) -> None:
        command = StrategicIntelligenceCommand()
        first = command.snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})
        second = command.snapshot(timestamp_utc="2026-07-09T15:01:00Z", sources={})

        self.assertEqual(len(first["strategicReports"]), len(second["strategicReports"]))
        self.assertEqual(
            [report["report_id"] for report in first["latestStrategicReports"]],
            [report["report_id"] for report in second["latestStrategicReports"]],
        )

    def test_eo_bt_blue_ocean_office_exists_under_sic_with_advisory_boundary(self) -> None:
        snapshot = BlueOceanIntelligenceOffice().snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})

        self.assertEqual("Blue Ocean Intelligence Office", snapshot["officeName"])
        self.assertEqual("Strategic Intelligence Command", snapshot["parentCommand"])
        self.assertEqual("PROHIBITED", snapshot["traderCommunication"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])
        self.assertFalse(snapshot["internalDiagnostics"]["communicatesDirectlyWithTrader"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertFalse(snapshot["lawVII"]["uncontrolledLoops"])

    def test_eo_bt_scores_all_candidates_and_generates_strategic_opportunity_dossiers(self) -> None:
        boio = create_runtime().state()["blueOceanIntelligenceOffice"]
        dossiers = boio["latestStrategicOpportunityDossiers"]

        self.assertGreaterEqual(len(boio["discoveryDomains"]), 24)
        self.assertTrue(boio["opportunityCandidates"])
        self.assertTrue(dossiers)
        for dossier in dossiers:
            score = dossier["blue_ocean_score"]
            self.assertGreaterEqual(score["overall_score"], 0)
            self.assertLessEqual(score["overall_score"], 100)
            for factor in boio["scoreFactors"]:
                self.assertIn(factor, score["factor_scores"])
            self.assertTrue(score["confidence_interval"])
            self.assertTrue(dossier["historian_id"].startswith("HIST-BOIO-DOS-"))
            self.assertTrue(dossier["librarian_index_id"].startswith("LIB-BOIO-DOS-"))
            self.assertTrue(dossier["research_gaps"])

    def test_eo_bt_bridge_exposes_required_blue_ocean_panels(self) -> None:
        bridge = create_runtime().state()["blueOceanIntelligenceOffice"]["blueOceanBridge"]

        for key in (
            "highestRankedOpportunities",
            "emergingIndustries",
            "emergingTechnologies",
            "blueOceanScoreDistribution",
            "innovationHeatMap",
            "commercializationTimeline",
            "analystCoverageDistribution",
            "institutionalOwnershipDistribution",
            "researchPipeline",
            "recentlyDiscoveredOpportunities",
            "opportunityWatchList",
            "historicalForecastAccuracy",
            "evidenceConfidence",
            "runtimeHealth",
            "apiUsage",
            "workflowStatus",
        ):
            self.assertIn(key, bridge)
        self.assertTrue(bridge["highestRankedOpportunities"])
        self.assertEqual("deterministic_no_paid_calls", bridge["apiUsage"]["mode"])

    def test_eo_bt_historian_librarian_and_research_directive_feeds_exist(self) -> None:
        boio = create_runtime().state()["blueOceanIntelligenceOffice"]

        self.assertEqual(len(boio["strategicOpportunityDossiers"]), len(boio["historianFeed"]))
        self.assertEqual(len(boio["strategicOpportunityDossiers"]), len(boio["librarianFeed"]))
        self.assertTrue(boio["researchDirectives"])
        self.assertTrue(all(item["advisoryOnly"] for item in boio["researchDirectives"]))
        self.assertEqual("Strategic Intelligence Command", boio["outbox"][0]["target"])
        self.assertTrue(boio["workflowParticipation"]["workflowTokenCompatible"])
        self.assertFalse(boio["workflowParticipation"]["lawVIIBypass"])

    def test_eo_bt_sic_runtime_api_and_ui_are_wired(self) -> None:
        state = create_runtime().state()
        sic_offices = {office["officeName"]: office for office in state["strategicIntelligenceCommand"]["subordinateOfficeInterfaces"]}
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("blueOceanIntelligenceOffice", state)
        self.assertEqual("OPERATIONAL", sic_offices["Blue Ocean Intelligence Office"]["status"])
        self.assertEqual("blue_ocean_bridge", sic_offices["Blue Ocean Intelligence Office"]["route"])
        self.assertTrue(state["strategicIntelligenceCommand"]["commanderStrategicDashboardFeed"]["blueOceanOpportunities"])
        self.assertIn("/api/blue-ocean/state", server)
        self.assertIn('id="blue-ocean-subcommand-bridge"', html)
        self.assertIn("function renderBlueOceanBridge", js)
        self.assertIn("blue_ocean_bridge", js)

    def test_eo_bt_snapshot_is_idempotent_for_unchanged_sources(self) -> None:
        office = BlueOceanIntelligenceOffice()
        first = office.snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})
        second = office.snapshot(timestamp_utc="2026-07-09T15:01:00Z", sources={})

        self.assertEqual(len(first["strategicOpportunityDossiers"]), len(second["strategicOpportunityDossiers"]))
        self.assertEqual(
            [item["dossier_id"] for item in first["latestStrategicOpportunityDossiers"]],
            [item["dossier_id"] for item in second["latestStrategicOpportunityDossiers"]],
        )

    def test_eo_bu_disruption_office_exists_under_sic_with_advisory_boundary(self) -> None:
        snapshot = DisruptionIntelligenceOffice().snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})

        self.assertEqual("Disruption Intelligence Office", snapshot["officeName"])
        self.assertEqual("Strategic Intelligence Command", snapshot["parentCommand"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])
        self.assertFalse(snapshot["internalDiagnostics"]["createsOrders"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertFalse(snapshot["lawVII"]["uncontrolledLoops"])

    def test_eo_bu_scores_candidates_and_generates_strategic_disruption_assessments(self) -> None:
        dio = create_runtime().state()["disruptionIntelligenceOffice"]
        assessments = dio["latestStrategicDisruptionAssessments"]

        self.assertGreaterEqual(len(dio["evaluationDomains"]), 25)
        self.assertTrue(dio["innovationCandidates"])
        self.assertTrue(assessments)
        for assessment in assessments:
            score = assessment["disruption_score"]
            self.assertGreaterEqual(score["overall_score"], 0)
            self.assertLessEqual(score["overall_score"], 100)
            for factor in dio["scoreFactors"]:
                self.assertIn(factor, score["component_scores"])
            self.assertIn(assessment["adoption_stage"], dio["adoptionStages"])
            self.assertTrue(assessment["industry_impact"])
            self.assertTrue(assessment["historian_archive_id"].startswith("HIST-DIO-ASM-"))
            self.assertTrue(assessment["librarian_index_id"].startswith("LIB-DIO-ASM-"))

    def test_eo_bu_bridge_exposes_required_disruption_panels(self) -> None:
        bridge = create_runtime().state()["disruptionIntelligenceOffice"]["disruptionBridge"]

        for key in (
            "highestDisruptionScores",
            "technologyReadiness",
            "commercializationTimeline",
            "industryRiskMap",
            "innovationHeatMap",
            "adoptionCurveDistribution",
            "emergingDisruptors",
            "incumbentVulnerability",
            "strategicWatchList",
            "historicalForecastAccuracy",
            "confidenceDistribution",
            "evidenceQuality",
            "runtimeHealth",
            "workflowStatus",
            "apiUsage",
        ):
            self.assertIn(key, bridge)
        self.assertTrue(bridge["highestDisruptionScores"])
        self.assertEqual("deterministic_no_paid_calls", bridge["apiUsage"]["mode"])

    def test_eo_bu_historian_librarian_and_research_directive_feeds_exist(self) -> None:
        dio = create_runtime().state()["disruptionIntelligenceOffice"]

        self.assertEqual(len(dio["strategicDisruptionAssessments"]), len(dio["historianFeed"]))
        self.assertEqual(len(dio["strategicDisruptionAssessments"]), len(dio["librarianFeed"]))
        self.assertTrue(dio["researchDirectives"])
        self.assertTrue(all(item["advisoryOnly"] for item in dio["researchDirectives"]))
        self.assertEqual("Strategic Intelligence Command", dio["outbox"][0]["target"])
        self.assertTrue(dio["workflowParticipation"]["workflowTokenCompatible"])
        self.assertFalse(dio["workflowParticipation"]["lawVIIBypass"])

    def test_eo_bu_sic_runtime_api_and_ui_are_wired(self) -> None:
        state = create_runtime().state()
        sic_offices = {office["officeName"]: office for office in state["strategicIntelligenceCommand"]["subordinateOfficeInterfaces"]}
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("disruptionIntelligenceOffice", state)
        self.assertEqual("OPERATIONAL", sic_offices["Disruption Intelligence Office"]["status"])
        self.assertEqual("disruption_bridge", sic_offices["Disruption Intelligence Office"]["route"])
        self.assertTrue(state["strategicIntelligenceCommand"]["commanderStrategicDashboardFeed"]["disruptionOpportunities"])
        self.assertIn("/api/disruption/state", server)
        self.assertIn('id="disruption-subcommand-bridge"', html)
        self.assertIn("function renderDisruptionBridge", js)
        self.assertIn("disruption_bridge", js)

    def test_eo_bu_snapshot_is_idempotent_for_unchanged_sources(self) -> None:
        office = DisruptionIntelligenceOffice()
        first = office.snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})
        second = office.snapshot(timestamp_utc="2026-07-09T15:01:00Z", sources={})

        self.assertEqual(len(first["strategicDisruptionAssessments"]), len(second["strategicDisruptionAssessments"]))
        self.assertEqual(
            [item["assessment_id"] for item in first["latestStrategicDisruptionAssessments"]],
            [item["assessment_id"] for item in second["latestStrategicDisruptionAssessments"]],
        )

    def test_eo_bv_decline_office_exists_under_sic_with_advisory_boundary(self) -> None:
        snapshot = DeclineIntelligenceOffice().snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})

        self.assertEqual("Decline Intelligence Office", snapshot["officeName"])
        self.assertEqual("Strategic Intelligence Command", snapshot["parentCommand"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])
        self.assertFalse(snapshot["internalDiagnostics"]["createsOrders"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertFalse(snapshot["lawVII"]["uncontrolledLoops"])

    def test_eo_bv_scores_candidates_and_generates_strategic_decline_assessments(self) -> None:
        dcl = create_runtime().state()["declineIntelligenceOffice"]
        assessments = dcl["latestStrategicDeclineAssessments"]

        self.assertGreaterEqual(len(dcl["evaluationDomains"]), 20)
        self.assertTrue(dcl["declineCandidates"])
        self.assertTrue(assessments)
        for assessment in assessments:
            score = assessment["decline_score"]
            self.assertGreaterEqual(score["overall_score"], 0)
            self.assertLessEqual(score["overall_score"], 100)
            for factor in dcl["scoreFactors"]:
                self.assertIn(factor, score["component_scores"])
            self.assertIn(assessment["decline_stage"], dcl["declineStages"])
            self.assertTrue(assessment["root_cause_analysis"])
            self.assertTrue(assessment["historian_archive_id"].startswith("HIST-DCLIO-ASM-"))
            self.assertTrue(assessment["librarian_index_id"].startswith("LIB-DCLIO-ASM-"))

    def test_eo_bv_bridge_exposes_required_decline_panels(self) -> None:
        bridge = create_runtime().state()["declineIntelligenceOffice"]["declineBridge"]

        for key in (
            "highestDeclineScores",
            "decliningIndustries",
            "decliningCompanies",
            "technologyObsolescence",
            "demandTrends",
            "competitiveThreats",
            "regulatoryRisk",
            "demergingIndustriesMap",
            "historicalForecastAccuracy",
            "recoveryCandidates",
            "confidenceDistribution",
            "evidenceQuality",
            "runtimeHealth",
            "workflowStatus",
            "apiUsage",
        ):
            self.assertIn(key, bridge)
        self.assertTrue(bridge["highestDeclineScores"])
        self.assertEqual("deterministic_no_paid_calls", bridge["apiUsage"]["mode"])

    def test_eo_bv_historian_librarian_and_research_directive_feeds_exist(self) -> None:
        dcl = create_runtime().state()["declineIntelligenceOffice"]

        self.assertEqual(len(dcl["strategicDeclineAssessments"]), len(dcl["historianFeed"]))
        self.assertEqual(len(dcl["strategicDeclineAssessments"]), len(dcl["librarianFeed"]))
        self.assertTrue(dcl["researchDirectives"])
        self.assertTrue(all(item["advisoryOnly"] for item in dcl["researchDirectives"]))
        self.assertEqual("Strategic Intelligence Command", dcl["outbox"][0]["target"])
        self.assertTrue(dcl["workflowParticipation"]["workflowTokenCompatible"])
        self.assertFalse(dcl["workflowParticipation"]["lawVIIBypass"])

    def test_eo_bv_sic_runtime_api_and_ui_are_wired(self) -> None:
        state = create_runtime().state()
        sic_offices = {office["officeName"]: office for office in state["strategicIntelligenceCommand"]["subordinateOfficeInterfaces"]}
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("declineIntelligenceOffice", state)
        self.assertEqual("OPERATIONAL", sic_offices["Decline Intelligence Office"]["status"])
        self.assertEqual("decline_bridge", sic_offices["Decline Intelligence Office"]["route"])
        self.assertTrue(state["strategicIntelligenceCommand"]["commanderStrategicDashboardFeed"]["declineWarnings"])
        self.assertIn("/api/decline/state", server)
        self.assertIn('id="decline-subcommand-bridge"', html)
        self.assertIn("function renderDeclineBridge", js)
        self.assertIn("decline_bridge", js)

    def test_eo_bv_snapshot_is_idempotent_for_unchanged_sources(self) -> None:
        office = DeclineIntelligenceOffice()
        first = office.snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})
        second = office.snapshot(timestamp_utc="2026-07-09T15:01:00Z", sources={})

        self.assertEqual(len(first["strategicDeclineAssessments"]), len(second["strategicDeclineAssessments"]))
        self.assertEqual(
            [item["assessment_id"] for item in first["latestStrategicDeclineAssessments"]],
            [item["assessment_id"] for item in second["latestStrategicDeclineAssessments"]],
        )

    def test_eo_bw_short_opportunity_office_exists_under_sic_with_advisory_boundary(self) -> None:
        snapshot = ShortOpportunityOffice().snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})

        self.assertEqual("Short Opportunity Office", snapshot["officeName"])
        self.assertEqual("Strategic Intelligence Command", snapshot["parentCommand"])
        self.assertEqual("NONE", snapshot["tradingAuthority"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])
        self.assertFalse(snapshot["internalDiagnostics"]["routesToTrader"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertFalse(snapshot["lawVII"]["uncontrolledLoops"])

    def test_eo_bw_scores_candidates_and_generates_strategic_short_assessments(self) -> None:
        soo = create_runtime().state()["shortOpportunityOffice"]
        assessments = soo["latestStrategicShortAssessments"]

        self.assertGreaterEqual(len(soo["evaluationDomains"]), 10)
        self.assertTrue(soo["shortCandidates"])
        self.assertTrue(assessments)
        for assessment in assessments:
            score = assessment["short_opportunity_score"]
            self.assertGreaterEqual(score["overall_score"], 0)
            self.assertLessEqual(score["overall_score"], 100)
            for factor in soo["scoreFactors"]:
                self.assertIn(factor, score["factor_scores"])
            self.assertTrue(assessment["supporting_evidence"])
            self.assertTrue(assessment["contradictory_evidence"])
            self.assertTrue(assessment["counterarguments"])
            self.assertTrue(assessment["invalidation_criteria"])
            self.assertTrue(assessment["bull_case"])
            self.assertTrue(assessment["bear_case"])
            self.assertTrue(assessment["unknowns"])
            self.assertTrue(assessment["evidence_gaps"])

    def test_eo_bw_bridge_exposes_required_short_opportunity_panels(self) -> None:
        bridge = create_runtime().state()["shortOpportunityOffice"]["shortOpportunityBridge"]

        for key in (
            "highestShortScores",
            "bearishWatchList",
            "highestDownsidePotential",
            "industryWeakness",
            "financialDistress",
            "valuationExtremes",
            "catalystCalendar",
            "confidenceDistribution",
            "counterargumentStatus",
            "evidenceQuality",
            "historicalForecastAccuracy",
            "runtimeHealth",
            "workflowStatus",
            "apiUsage",
        ):
            self.assertIn(key, bridge)
        self.assertTrue(bridge["highestShortScores"])
        self.assertEqual("deterministic_no_paid_calls", bridge["apiUsage"]["mode"])

    def test_eo_bw_historian_librarian_and_research_directive_feeds_exist(self) -> None:
        soo = create_runtime().state()["shortOpportunityOffice"]

        self.assertEqual(len(soo["strategicShortAssessments"]), len(soo["historianFeed"]))
        self.assertEqual(len(soo["strategicShortAssessments"]), len(soo["librarianFeed"]))
        self.assertTrue(soo["researchDirectives"])
        self.assertTrue(all(item["advisoryOnly"] for item in soo["researchDirectives"]))
        self.assertEqual("Strategic Intelligence Command", soo["outbox"][0]["target"])
        self.assertTrue(soo["workflowParticipation"]["workflowTokenCompatible"])
        self.assertFalse(soo["workflowParticipation"]["lawVIIBypass"])

    def test_eo_bw_sic_runtime_api_and_ui_are_wired(self) -> None:
        state = create_runtime().state()
        sic_offices = {office["officeName"]: office for office in state["strategicIntelligenceCommand"]["subordinateOfficeInterfaces"]}
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("shortOpportunityOffice", state)
        self.assertEqual("OPERATIONAL", sic_offices["Short Opportunity Office"]["status"])
        self.assertEqual("short_opportunity_bridge", sic_offices["Short Opportunity Office"]["route"])
        self.assertTrue(state["strategicIntelligenceCommand"]["commanderStrategicDashboardFeed"]["shortOpportunities"])
        self.assertIn("/api/short-opportunity/state", server)
        self.assertIn('id="short-opportunity-subcommand-bridge"', html)
        self.assertIn("function renderShortOpportunityBridge", js)
        self.assertIn("short_opportunity_bridge", js)

    def test_eo_bw_snapshot_is_idempotent_for_unchanged_sources(self) -> None:
        office = ShortOpportunityOffice()
        first = office.snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})
        second = office.snapshot(timestamp_utc="2026-07-09T15:01:00Z", sources={})

        self.assertEqual(len(first["strategicShortAssessments"]), len(second["strategicShortAssessments"]))
        self.assertEqual(
            [item["assessment_id"] for item in first["latestStrategicShortAssessments"]],
            [item["assessment_id"] for item in second["latestStrategicShortAssessments"]],
        )

    def test_eo_bx_market_structure_office_exists_under_sic_with_advisory_boundary(self) -> None:
        snapshot = MarketStructureIntelligenceOffice().snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})

        self.assertEqual("Market Structure Intelligence Office", snapshot["officeName"])
        self.assertEqual("Strategic Intelligence Command", snapshot["parentCommand"])
        self.assertEqual("NONE", snapshot["tradingAuthority"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])
        self.assertFalse(snapshot["internalDiagnostics"]["routesToTrader"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertFalse(snapshot["lawVII"]["uncontrolledLoops"])

    def test_eo_bx_scores_markets_and_generates_strategic_market_structure_assessments(self) -> None:
        msio = create_runtime().state()["marketStructureIntelligenceOffice"]
        assessments = msio["latestStrategicMarketStructureAssessments"]

        self.assertGreaterEqual(len(msio["evaluationDomains"]), 15)
        self.assertTrue(msio["evaluatedMarkets"])
        self.assertTrue(assessments)
        for assessment in assessments:
            score = assessment["market_structure_score"]
            self.assertGreaterEqual(score["overall_score"], 0)
            self.assertLessEqual(score["overall_score"], 100)
            for component in msio["scoreComponents"]:
                self.assertIn(component, score["component_scores"])
            self.assertIn(assessment["structural_classification"], msio["structuralClassifications"])
            self.assertTrue(assessment["liquidity_assessment"])
            self.assertTrue(assessment["volatility_assessment"])
            self.assertTrue(assessment["correlation_assessment"])
            self.assertTrue(assessment["breadth_assessment"])
            self.assertTrue(assessment["institutional_participation"])
            self.assertTrue(assessment["root_cause_analysis"])
            self.assertTrue(assessment["structural_risks"])
            self.assertTrue(assessment["structural_opportunities"])
            self.assertTrue(assessment["historian_archive_id"].startswith("HIST-MSIO-ASM-"))
            self.assertTrue(assessment["librarian_index_id"].startswith("LIB-MSIO-ASM-"))

    def test_eo_bx_bridge_exposes_required_market_structure_panels(self) -> None:
        bridge = create_runtime().state()["marketStructureIntelligenceOffice"]["marketStructureIntelligenceBridge"]

        for key in (
            "marketStructureScore",
            "liquidityHeatMap",
            "volatilityRegimes",
            "breadthIndicators",
            "correlationMatrix",
            "crossAssetRelationships",
            "structuralOpportunityMap",
            "systemicStressIndicators",
            "institutionalParticipation",
            "historicalRegimeTimeline",
            "confidenceDistribution",
            "evidenceQuality",
            "runtimeHealth",
            "workflowStatus",
            "apiUsage",
        ):
            self.assertIn(key, bridge)
        self.assertTrue(bridge["marketStructureScore"])
        self.assertEqual("deterministic_no_paid_calls", bridge["apiUsage"]["mode"])

    def test_eo_bx_historian_librarian_and_research_directive_feeds_exist(self) -> None:
        msio = create_runtime().state()["marketStructureIntelligenceOffice"]

        self.assertEqual(len(msio["strategicMarketStructureAssessments"]), len(msio["historianFeed"]))
        self.assertEqual(len(msio["strategicMarketStructureAssessments"]), len(msio["librarianFeed"]))
        self.assertTrue(msio["researchDirectives"])
        self.assertTrue(all(item["advisoryOnly"] for item in msio["researchDirectives"]))
        self.assertEqual("Strategic Intelligence Command", msio["outbox"][0]["target"])
        self.assertTrue(msio["workflowParticipation"]["workflowTokenCompatible"])
        self.assertFalse(msio["workflowParticipation"]["lawVIIBypass"])

    def test_eo_bx_sic_runtime_api_and_ui_are_wired(self) -> None:
        state = create_runtime().state()
        sic_offices = {office["officeName"]: office for office in state["strategicIntelligenceCommand"]["subordinateOfficeInterfaces"]}
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("marketStructureIntelligenceOffice", state)
        self.assertEqual("OPERATIONAL", sic_offices["Market Structure Intelligence Office"]["status"])
        self.assertEqual("market_structure_bridge", sic_offices["Market Structure Intelligence Office"]["route"])
        self.assertTrue(state["strategicIntelligenceCommand"]["commanderStrategicDashboardFeed"]["marketStructureOpportunities"])
        self.assertIn("marketStructureIntelligenceOffice", state["commanderDailyReviewWorkspace"])
        self.assertIn("/api/market-structure/state", server)
        self.assertIn('id="market-structure-subcommand-bridge"', html)
        self.assertIn("function renderMarketStructureBridge", js)
        self.assertIn("market_structure_bridge", js)

    def test_eo_bx_snapshot_is_idempotent_for_unchanged_sources(self) -> None:
        office = MarketStructureIntelligenceOffice()
        first = office.snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})
        second = office.snapshot(timestamp_utc="2026-07-09T15:01:00Z", sources={})

        self.assertEqual(len(first["strategicMarketStructureAssessments"]), len(second["strategicMarketStructureAssessments"]))
        self.assertEqual(
            [item["assessment_id"] for item in first["latestStrategicMarketStructureAssessments"]],
            [item["assessment_id"] for item in second["latestStrategicMarketStructureAssessments"]],
        )

    def test_eo_by_capital_rotation_office_exists_under_sic_with_advisory_boundary(self) -> None:
        snapshot = CapitalRotationIntelligenceOffice().snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})

        self.assertEqual("Capital Rotation Intelligence Office", snapshot["officeName"])
        self.assertEqual("Strategic Intelligence Command", snapshot["parentCommand"])
        self.assertEqual("NONE", snapshot["tradingAuthority"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])
        self.assertFalse(snapshot["internalDiagnostics"]["routesToTrader"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertFalse(snapshot["lawVII"]["uncontrolledLoops"])

    def test_eo_by_scores_segments_and_generates_strategic_capital_rotation_assessments(self) -> None:
        crio = create_runtime().state()["capitalRotationIntelligenceOffice"]
        assessments = crio["latestStrategicCapitalRotationAssessments"]

        self.assertGreaterEqual(len(crio["evaluationDomains"]), 20)
        self.assertTrue(crio["evaluatedSegments"])
        self.assertTrue(assessments)
        for assessment in assessments:
            score = assessment["capital_rotation_score"]
            self.assertGreaterEqual(score["overall_score"], 0)
            self.assertLessEqual(score["overall_score"], 100)
            for component in crio["scoreComponents"]:
                self.assertIn(component, score["component_scores"])
            self.assertIn(assessment["rotation_classification"], crio["rotationClassifications"])
            self.assertTrue(assessment["primary_capital_destinations"])
            self.assertTrue(assessment["primary_capital_sources"])
            self.assertTrue(assessment["sector_rotation"])
            self.assertTrue(assessment["industry_rotation"])
            self.assertTrue(assessment["asset_allocation_trends"])
            self.assertTrue(assessment["geographic_rotation"])
            self.assertTrue(assessment["institutional_participation"])
            self.assertTrue(assessment["rotation_persistence"])
            self.assertTrue(assessment["root_cause_analysis"])
            self.assertTrue(assessment["historian_archive_id"].startswith("HIST-CRIO-ASM-"))
            self.assertTrue(assessment["librarian_index_id"].startswith("LIB-CRIO-ASM-"))

    def test_eo_by_bridge_exposes_required_capital_rotation_panels(self) -> None:
        bridge = create_runtime().state()["capitalRotationIntelligenceOffice"]["capitalRotationIntelligenceBridge"]

        for key in (
            "capitalRotationScore",
            "sectorRotationMap",
            "industryRotationMap",
            "assetAllocationChanges",
            "geographicCapitalFlows",
            "institutionalParticipation",
            "etfFlowDashboard",
            "mutualFundPositioning",
            "optionsPositioning",
            "riskOnRiskOffIndicator",
            "historicalRotationTimeline",
            "confidenceDistribution",
            "evidenceQuality",
            "runtimeHealth",
            "workflowStatus",
            "apiUsage",
        ):
            self.assertIn(key, bridge)
        self.assertTrue(bridge["capitalRotationScore"])
        self.assertEqual("deterministic_no_paid_calls", bridge["apiUsage"]["mode"])

    def test_eo_by_historian_librarian_and_research_directive_feeds_exist(self) -> None:
        crio = create_runtime().state()["capitalRotationIntelligenceOffice"]

        self.assertEqual(len(crio["strategicCapitalRotationAssessments"]), len(crio["historianFeed"]))
        self.assertEqual(len(crio["strategicCapitalRotationAssessments"]), len(crio["librarianFeed"]))
        self.assertTrue(crio["researchDirectives"])
        self.assertTrue(all(item["advisoryOnly"] for item in crio["researchDirectives"]))
        self.assertEqual("Strategic Intelligence Command", crio["outbox"][0]["target"])
        self.assertTrue(crio["workflowParticipation"]["workflowTokenCompatible"])
        self.assertFalse(crio["workflowParticipation"]["lawVIIBypass"])

    def test_eo_by_sic_runtime_api_and_ui_are_wired(self) -> None:
        state = create_runtime().state()
        sic_offices = {office["officeName"]: office for office in state["strategicIntelligenceCommand"]["subordinateOfficeInterfaces"]}
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("capitalRotationIntelligenceOffice", state)
        self.assertEqual("OPERATIONAL", sic_offices["Capital Rotation Intelligence Office"]["status"])
        self.assertEqual("capital_rotation_bridge", sic_offices["Capital Rotation Intelligence Office"]["route"])
        self.assertTrue(state["strategicIntelligenceCommand"]["commanderStrategicDashboardFeed"]["capitalRotationDestinations"])
        self.assertIn("capitalRotationIntelligenceOffice", state["commanderDailyReviewWorkspace"])
        self.assertIn("/api/capital-rotation/state", server)
        self.assertIn('id="capital-rotation-subcommand-bridge"', html)
        self.assertIn("function renderCapitalRotationBridge", js)
        self.assertIn("capital_rotation_bridge", js)

    def test_eo_by_snapshot_is_idempotent_for_unchanged_sources(self) -> None:
        office = CapitalRotationIntelligenceOffice()
        first = office.snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})
        second = office.snapshot(timestamp_utc="2026-07-09T15:01:00Z", sources={})

        self.assertEqual(len(first["strategicCapitalRotationAssessments"]), len(second["strategicCapitalRotationAssessments"]))
        self.assertEqual(
            [item["assessment_id"] for item in first["latestStrategicCapitalRotationAssessments"]],
            [item["assessment_id"] for item in second["latestStrategicCapitalRotationAssessments"]],
        )

    def test_eo_bz_strategic_synthesis_office_exists_under_sic_with_advisory_boundary(self) -> None:
        snapshot = StrategicSynthesisOffice().snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})

        self.assertEqual("Strategic Synthesis Office", snapshot["officeName"])
        self.assertEqual("Strategic Intelligence Command", snapshot["parentCommand"])
        self.assertEqual("NONE", snapshot["tradingAuthority"])
        self.assertFalse(snapshot["internalDiagnostics"]["placesTrades"])
        self.assertFalse(snapshot["internalDiagnostics"]["routesToTrader"])
        self.assertEqual(0, snapshot["lawVIII"]["routineAiInvocations"])
        self.assertFalse(snapshot["lawVII"]["uncontrolledLoops"])

    def test_eo_bz_integrates_strategic_office_outputs_into_commander_assessment(self) -> None:
        sso = create_runtime().state()["strategicSynthesisOffice"]
        assessments = sso["latestCommanderStrategicAssessments"]

        self.assertTrue(assessments)
        self.assertGreaterEqual(len(sso["sourceOfficeEvidence"]), 6)
        for assessment in assessments:
            score = assessment["strategic_consensus_score"]
            self.assertGreaterEqual(score["overall_score"], 0)
            self.assertLessEqual(score["overall_score"], 100)
            for component in sso["consensusComponents"]:
                self.assertIn(component, score["component_scores"])
            self.assertIn(assessment["strategic_classification"], sso["strategicClassifications"])
            self.assertTrue(assessment["primary_strategic_themes"])
            self.assertTrue(assessment["areas_of_agreement"])
            self.assertIn("areas_of_disagreement", assessment)
            self.assertTrue(assessment["uncertainty_map"])
            self.assertTrue(assessment["commander_strategic_briefing"])
            self.assertTrue(assessment["historian_archive_id"].startswith("HIST-SSO-ASM-"))
            self.assertTrue(assessment["librarian_index_id"].startswith("LIB-SSO-ASM-"))

    def test_eo_bz_bridge_exposes_required_strategic_synthesis_panels(self) -> None:
        bridge = create_runtime().state()["strategicSynthesisOffice"]["strategicSynthesisBridge"]

        for key in (
            "strategicConsensusScore",
            "consensusMatrix",
            "officeAgreementMatrix",
            "evidenceHeatMap",
            "confidenceDistribution",
            "uncertaintyMap",
            "strategicThemes",
            "emergingRisks",
            "researchPriorities",
            "commanderBriefing",
            "historicalStrategicAssessments",
            "forecastAccuracy",
            "runtimeHealth",
            "workflowStatus",
            "apiUsage",
        ):
            self.assertIn(key, bridge)
        self.assertTrue(bridge["consensusMatrix"])
        self.assertEqual("deterministic_no_paid_calls", bridge["apiUsage"]["mode"])

    def test_eo_bz_historian_librarian_and_research_directive_feeds_exist(self) -> None:
        sso = create_runtime().state()["strategicSynthesisOffice"]

        self.assertEqual(len(sso["commanderStrategicAssessments"]), len(sso["historianFeed"]))
        self.assertEqual(len(sso["commanderStrategicAssessments"]), len(sso["librarianFeed"]))
        self.assertTrue(sso["researchDirectives"])
        self.assertTrue(all(item["advisoryOnly"] for item in sso["researchDirectives"]))
        self.assertEqual("Strategic Intelligence Command", sso["outbox"][0]["target"])
        self.assertTrue(sso["workflowParticipation"]["workflowTokenCompatible"])
        self.assertFalse(sso["workflowParticipation"]["lawVIIBypass"])

    def test_eo_bz_sic_runtime_api_and_ui_are_wired(self) -> None:
        state = create_runtime().state()
        sic_offices = {office["officeName"]: office for office in state["strategicIntelligenceCommand"]["subordinateOfficeInterfaces"]}
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertIn("strategicSynthesisOffice", state)
        self.assertEqual("OPERATIONAL", sic_offices["Strategic Synthesis Office"]["status"])
        self.assertEqual("strategic_synthesis_bridge", sic_offices["Strategic Synthesis Office"]["route"])
        self.assertTrue(state["strategicIntelligenceCommand"]["commanderStrategicDashboardFeed"]["strategicSynthesis"])
        self.assertIn("strategicSynthesisOffice", state["commanderDailyReviewWorkspace"])
        self.assertIn("/api/strategic-synthesis/state", server)
        self.assertIn('id="strategic-synthesis-subcommand-bridge"', html)
        self.assertIn("function renderStrategicSynthesisBridge", js)
        self.assertIn("strategic_synthesis_bridge", js)

    def test_eo_bz_snapshot_is_idempotent_for_unchanged_sources(self) -> None:
        office = StrategicSynthesisOffice()
        first = office.snapshot(timestamp_utc="2026-07-09T15:00:00Z", sources={})
        second = office.snapshot(timestamp_utc="2026-07-09T15:01:00Z", sources={})

        self.assertEqual(len(first["commanderStrategicAssessments"]), len(second["commanderStrategicAssessments"]))
        self.assertEqual(
            [item["assessment_id"] for item in first["latestCommanderStrategicAssessments"]],
            [item["assessment_id"] for item in second["latestCommanderStrategicAssessments"]],
        )

    def test_control_panel_does_not_display_dead_static_links(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")

        self.assertNotIn("<a ", html)
        self.assertNotIn("View Dashboard", js)
        self.assertIn('class="status-pill"', html)
        self.assertNotIn('<button class="nav-item', html)

        static_buttons = re.findall(r"<button([^>]*)>", html)
        button_ids = []
        for attrs in static_buttons:
            match = re.search(r'id="([^"]+)"', attrs)
            self.assertIsNotNone(match, f"Static button is missing a command id: {attrs}")
            button_ids.append(match.group(1))

        missing_handlers = [
            button_id
            for button_id in button_ids
            if f'$("${button_id}")' not in js and f'$("#{button_id}")' not in js and f'$("{button_id}").addEventListener' not in js
        ]
        self.assertEqual([], missing_handlers)

    def test_windows_launcher_files_open_control_panel(self) -> None:
        cmd = (REPOSITORY_ROOT / "Launch_ARGOS_Control_Panel.cmd").read_text(encoding="utf-8")
        ps1 = (REPOSITORY_ROOT / "Scripts" / "launch_argos_control_panel.ps1").read_text(encoding="utf-8")

        self.assertIn("launch_argos_control_panel.ps1", cmd)
        self.assertIn("http://$hostName`:$Port/", ps1)
        self.assertIn("$WindowWidth = 1600", ps1)
        self.assertIn("$WindowHeight = 1000", ps1)
        self.assertIn("--window-size=$Width,$Height", ps1)
        self.assertIn("Open-ArgosDashboard", ps1)
        self.assertIn("start_argos_control_panel.py", ps1)

    def test_eo_ca_enterprise_operations_scheduler_defaults_safe(self) -> None:
        scheduler = EnterpriseOperationsScheduler()
        snapshot = scheduler.snapshot()

        self.assertEqual("Enterprise Operations Scheduler", snapshot["schedulerName"])
        self.assertEqual("EO-CA", snapshot["engineeringOrder"])
        self.assertFalse(snapshot["enabled"])
        self.assertEqual("Observation Only", snapshot["currentOperatingMode"])
        self.assertEqual("DISABLED_SAFE", snapshot["status"])
        self.assertTrue(snapshot["lawVII"]["workflowExecutionTokenRequired"])
        self.assertFalse(snapshot["lawVII"]["uncontrolledLoopsCreated"])
        self.assertTrue(any(item["template_id"] == "pre_market_readiness" for item in snapshot["missionTemplates"]))
        self.assertTrue(any(item["template_id"] == "overnight_strategic_research" and not item["enabled_by_default"] for item in snapshot["missionTemplates"]))

    def test_eo_ca_mission_creation_dispatch_completion_and_activation_records(self) -> None:
        scheduler = EnterpriseOperationsScheduler()
        scheduler.set_enabled(True)
        scheduler.set_mode("Full Paper Trading")

        mission = scheduler.create_scheduled_mission("midday_position_review", now="2026-07-10T15:00:00Z")
        self.assertEqual("Queued", mission.status)
        dispatched = scheduler.dispatch_mission(mission.mission_id, workflow_id="WF-EOS", token_id="TOK-EOS")
        self.assertEqual("Running", dispatched.status)
        self.assertEqual("TOK-EOS", dispatched.execution_token_id)
        completed = scheduler.complete_mission(dispatched.mission_id, actual_api_cost=0.02, api_calls=1)
        self.assertEqual("Completed", completed.status)

        snapshot = scheduler.snapshot()
        self.assertEqual(1, snapshot["metrics"]["missionsCompleted"])
        self.assertTrue(snapshot["activationRequests"])
        self.assertTrue(all(item["mission_id"] == mission.mission_id for item in snapshot["activationRequests"]))

    def test_eo_ca_invalid_transition_duplicate_suppression_and_market_deferral(self) -> None:
        scheduler = EnterpriseOperationsScheduler()
        scheduler.set_enabled(True)
        scheduler.set_mode("Full Paper Trading")

        deferred = scheduler.create_scheduled_mission("post_open_discovery", now="2026-07-10T02:00:00Z")
        self.assertEqual("Awaiting Market Session", deferred.status)
        first = scheduler.create_scheduled_mission("pre_market_readiness", now="2026-07-10T09:00:00Z")
        second = scheduler.create_scheduled_mission("pre_market_readiness", now="2026-07-10T09:00:30Z")
        self.assertEqual(first.mission_id, second.mission_id)
        self.assertTrue(scheduler.snapshot()["suppressedWork"])
        with self.assertRaises(ValueError):
            scheduler.complete_mission(first.mission_id)

    def test_eo_ca_operating_modes_and_budget_protect_position_safety(self) -> None:
        scheduler = EnterpriseOperationsScheduler()
        scheduler.set_enabled(True)
        scheduler.set_mode("Position Management Only")

        discovery = scheduler.create_scheduled_mission("post_open_discovery", now="2026-07-10T14:05:00Z")
        blocked = scheduler.authorize_mission(discovery.mission_id)
        self.assertEqual("Suspended", blocked.status)

        safety = scheduler.create_scheduled_mission("midday_position_review", now="2026-07-10T12:30:00Z")
        authorized = scheduler.authorize_mission(safety.mission_id)
        self.assertEqual("Authorized", authorized.status)

        scheduler.set_budget(0.0, 0.01)
        constrained = scheduler.create_commander_directed_mission(mission_name="Emergency Risk Review", required_offices=("Risk",), maximum_api_cost=0.02)
        waiting = scheduler.authorize_mission(constrained.mission_id)
        self.assertEqual("Awaiting Resources", waiting.status)

    def test_eo_ca_restart_recovery_and_gateway_authorization_context(self) -> None:
        scheduler = EnterpriseOperationsScheduler()
        scheduler.set_enabled(True)
        scheduler.set_mode("Full Paper Trading")
        mission = scheduler.create_scheduled_mission("midday_position_review", now="2026-07-10T12:30:00Z")
        running = scheduler.dispatch_mission(mission.mission_id, workflow_id="WF-EOS", token_id="TOK-EOS")
        context = scheduler.gateway_authorization_context(running.mission_id, "Risk", "WF-EOS")

        self.assertTrue(context["authorized"])
        self.assertEqual(running.mission_id, context["mission_id"])
        recovered = EnterpriseOperationsScheduler()
        recovered.recover_from_snapshot(scheduler.snapshot())
        recovered_mission = recovered.snapshot()["missionRecords"][0]
        self.assertEqual("Suspended", recovered_mission["status"])
        self.assertTrue(recovered.snapshot()["recoveryRecords"])

    def test_eo_ca_runtime_routes_and_bridge_are_wired(self) -> None:
        runtime = create_runtime()
        state = runtime.eos_control("enable", {"reason": "unit test"})
        self.assertTrue(state["enterpriseOperationsScheduler"]["enabled"])
        state = runtime.eos_control("set_mode", {"mode": "Capital Preservation"})
        self.assertEqual("Capital Preservation", state["enterpriseOperationsScheduler"]["currentOperatingMode"])
        state = runtime.eos_control("run_mission_now", {"templateId": "midday_position_review"})
        self.assertTrue(state["enterpriseOperationsScheduler"]["missionRecords"])

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("Enterprise Operations Scheduler", html)
        for button_id in ("eos-enable", "eos-disable", "eos-set-mode", "eos-run-mission", "eos-cancel-mission"):
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
        self.assertIn("/api/eos/control", js)
        self.assertIn("/api/eos/control", server)

    def _odo_eos_snapshot(self, mode: str = "Full Paper Trading", budget: float = 25.0) -> tuple[EnterpriseOperationsScheduler, dict]:
        scheduler = EnterpriseOperationsScheduler()
        scheduler.set_enabled(True)
        scheduler.set_mode(mode)
        scheduler.set_budget(budget, 5.0)
        mission = scheduler.create_scheduled_mission("midday_position_review", now="2026-07-10T12:30:00Z")
        scheduler.dispatch_mission(mission.mission_id, workflow_id="WF-ODO", token_id="TOK-ODO")
        return scheduler, scheduler.snapshot()

    def _odo_request(self, target: str = "Risk", request_type: str = "risk_review", **overrides) -> dict:
        request = {
            "sourceOfficeId": "Commander",
            "targetOfficeId": target,
            "missionId": overrides.pop("mission_id", "EOS-MIS-000001"),
            "workflowId": "WF-ODO",
            "executionTokenId": overrides.pop("execution_token_id", "TOK-ODO"),
            "requestType": request_type,
            "taskDescription": overrides.pop("task_description", "Review duty officer tasking."),
            "priority": overrides.pop("priority", "High"),
            "criticality": overrides.pop("criticality", "Normal"),
            "eventReference": overrides.pop("event_reference", "EVT-ODO"),
            "estimatedValue": overrides.pop("estimated_value", 90),
            "estimatedCost": overrides.pop("estimated_cost", 0.01),
        }
        request.update(overrides)
        return request

    def test_eo_cb_duty_officer_registration_profiles_and_safe_defaults(self) -> None:
        registry = OfficeDutyOfficerRegistry()
        snapshot = registry.snapshot()

        self.assertEqual("Office Duty Officer", snapshot["frameworkName"])
        self.assertEqual("EO-CB", snapshot["engineeringOrder"])
        self.assertTrue(snapshot["enabled"])
        self.assertFalse(snapshot["lawVII"]["bypassesScheduler"])
        self.assertFalse(snapshot["lawVII"]["routineTriageUsesAi"])
        offices = {item["office_id"] for item in snapshot["enterpriseDutyRoster"]}
        for office in ("Executive", "Seeker", "Analyst", "Strategic Intelligence", "Risk", "Trader", "Historian", "Librarian", "Academy"):
            self.assertIn(office, offices)

    def test_eo_cb_invalid_authorization_duplicate_cache_and_routing(self) -> None:
        scheduler, eos = self._odo_eos_snapshot()
        registry = scheduler.duty_officers

        missing = registry.submit_request(self._odo_request(mission_id=""), eos)
        self.assertEqual("Reject", missing.disposition)
        self.assertEqual("Missing mission authorization", missing.reason_code)

        first = registry.submit_request(self._odo_request(target="Seeker", request_type="candidate_scan", task_description="Scan AAPL"), eos)
        duplicate = registry.submit_request(self._odo_request(target="Seeker", request_type="candidate_scan", task_description="Scan AAPL"), eos)
        self.assertIn(first.disposition, {"Emergency Wake Request", "Recommend Wake", "Queue", "Defer"})
        self.assertEqual("Duplicate Suppressed", duplicate.disposition)

        cached = registry.submit_request(self._odo_request(target="Librarian", request_type="knowledge_retrieval", task_description="Lookup doctrine"), eos)
        self.assertEqual("Answer From Cache", cached.disposition)
        self.assertTrue(cached.cache_reference)

        routed = registry.submit_request(self._odo_request(target="Lib", request_type="knowledge_retrieval", task_description="Wrong target"), eos)
        self.assertEqual("Route", routed.disposition)
        self.assertEqual("Librarian", routed.routing_destination)

    def test_eo_cb_modes_budget_cooldown_and_wake_recommendations(self) -> None:
        scheduler, eos = self._odo_eos_snapshot()
        registry = scheduler.duty_officers

        wake = registry.submit_request(self._odo_request(target="Risk", request_type="risk_review", criticality="Critical"), eos)
        self.assertIn(wake.disposition, {"Recommend Wake", "Emergency Wake Request"})
        self.assertTrue(wake.wake_recommendation)
        self.assertGreaterEqual(wake.wake_justification_score, 65)

        cooldown = registry.submit_request(self._odo_request(target="Risk", request_type="exposure_change", task_description="Second risk item", event_reference="EVT-ODO-2"), eos)
        self.assertEqual("Prohibited by Cooldown", cooldown.disposition)

        _, preservation = self._odo_eos_snapshot("Capital Preservation")
        academy = OfficeDutyOfficerRegistry().submit_request(self._odo_request(target="Academy", request_type="training_request", mission_id="EOS-MIS-000001"), preservation)
        self.assertEqual("Prohibited by Operating Mode", academy.disposition)

        budget_scheduler, budget_eos = self._odo_eos_snapshot(budget=0.0)
        budget = budget_scheduler.duty_officers.submit_request(self._odo_request(target="Risk", request_type="risk_review", event_reference="EVT-BUDGET"), budget_eos)
        self.assertEqual("Prohibited by Budget", budget.disposition)

    def test_eo_cb_queue_recovery_metrics_and_runtime_bridge(self) -> None:
        scheduler, eos = self._odo_eos_snapshot("Strategic Research Only")
        queued = scheduler.duty_officers.submit_request(
            self._odo_request(target="Academy", request_type="training_request", priority="Low", estimated_value=20, event_reference="EVT-QUEUE"),
            eos,
        )
        self.assertIn(queued.disposition, {"Queue", "Defer"})
        snapshot = scheduler.duty_officers.snapshot(eos)
        recovered = OfficeDutyOfficerRegistry()
        recovered.recover_from_snapshot(snapshot)
        self.assertTrue(recovered.snapshot()["recoveryRecords"])
        self.assertGreaterEqual(snapshot["metrics"]["fullOfficeActivationsAvoided"], 1)

        runtime = create_runtime()
        state = runtime.eos_control("enable", {"reason": "odo test"})
        state = runtime.eos_control("set_mode", {"mode": "Full Paper Trading"})
        state = runtime.eos_control("run_mission_now", {"templateId": "midday_position_review"})
        mission = state["enterpriseOperationsScheduler"]["missionRecords"][0]
        state = runtime.submit_duty_officer_request(
            self._odo_request(mission_id=mission["mission_id"], execution_token_id=mission["execution_token_id"])
        )
        self.assertIn("officeDutyOfficers", state)
        self.assertIn("latestDutyOfficerDecision", state)
        self.assertTrue(state["officeDutyOfficers"]["auditDetail"])

    def test_eo_cb_ui_api_gateway_and_routes_are_wired(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        gateway = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "api_execution_gateway.py").read_text(encoding="utf-8")

        self.assertIn("Office Duty Officers", html)
        for button_id in ("odo-submit",):
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
        self.assertIn("/api/odo/task", js)
        self.assertIn("/api/odo/task", server)
        self.assertIn("duty_officer_id", gateway)
        self.assertIn("parent_office_id", gateway)

    def test_eo_ck_position_monitoring_network_emits_events_only(self) -> None:
        network = PositionMonitoringNetwork()
        snapshot = network.scan(
            position_registry={
                "activePositions": (
                    {
                        "position_id": "POS-AAPL-CK",
                        "symbol": "AAPL",
                        "quantity": 10,
                        "average_cost": 100.0,
                        "current_value": 940.0,
                        "stop_loss": 95.0,
                        "profit_target": 110.0,
                        "trailing_stop": 96.0,
                        "current_risk": 0.82,
                        "time_in_trade": "370m",
                    },
                )
            },
            market_data_provider={"normalizedObjects": {"quotes": ({"symbol": "AAPL", "last": 94.0, "bid": 93.99, "ask": 94.01, "volatility": 0.05},)}},
            performance_truth={"orderLedger": ({"symbol": "AAPL", "status": "REJECTED", "order_id": "ORD-CK"},)},
            timestamp_utc="2026-07-10T14:30:00Z",
        )

        event_types = {item["event_type"] for item in snapshot["latestMonitoringEvents"]}
        self.assertIn("position_stop_loss_breached", event_types)
        self.assertIn("position_trailing_stop_breached", event_types)
        self.assertIn("position_risk_threshold_breached", event_types)
        self.assertGreaterEqual(snapshot["summary"]["triggeredWatchers"], 4)
        self.assertEqual(0, snapshot["lawCK"]["routineAiInvocations"])
        self.assertFalse(snapshot["lawCK"]["wakesOffices"])
        self.assertFalse(snapshot["lawCK"]["placesTrades"])
        self.assertFalse(snapshot["lawCK"]["mutatesPositions"])
        self.assertFalse(snapshot["lawCK"]["mutatesLedgers"])
        self.assertTrue(snapshot["lawCK"]["feedsEOCC"])
        self.assertTrue(any(item["severity"] == MonitoringEventSeverity.CRITICAL.value for item in snapshot["eventDetectionFeed"]))

    def test_eo_ck_degraded_missing_quote_and_recovery_replay(self) -> None:
        network = PositionMonitoringNetwork()
        snapshot = network.scan(
            position_registry={"activePositions": ({"position_id": "POS-MISSING-CK", "symbol": "MSFT", "quantity": 4, "average_cost": 200.0},)},
            market_data_provider={"normalizedObjects": {"quotes": ()}},
            performance_truth={},
            timestamp_utc="2026-07-10T14:31:00Z",
        )

        self.assertEqual("DEGRADED", snapshot["status"])
        self.assertEqual("position_market_data_missing", snapshot["latestMonitoringEvents"][0]["event_type"])
        recovered = PositionMonitoringNetwork()
        recovered.recover_from_snapshot(snapshot)
        recovered_snapshot = recovered.snapshot()
        self.assertEqual(snapshot["watcherRoster"][0]["watcher_id"], recovered_snapshot["watcherRoster"][0]["watcher_id"])
        replay = network.replay(
            position_registry={"activePositions": ({"position_id": "POS-MISSING-CK", "symbol": "MSFT", "quantity": 4, "average_cost": 200.0},)},
            market_data_provider={"normalizedObjects": {"quotes": ()}},
            performance_truth={},
        )
        self.assertTrue(replay["replayMode"])
        self.assertFalse(replay["productionMutation"])

    def test_eo_ck_feeds_event_detection_without_waking_offices(self) -> None:
        monitor = PositionMonitoringNetwork()
        monitor_snapshot = monitor.scan(
            position_registry={"activePositions": ({"position_id": "POS-EDE-CK", "symbol": "SPY", "quantity": 2, "average_cost": 500.0, "stop_loss": 490.0},)},
            market_data_provider={"normalizedObjects": {"quotes": ({"symbol": "SPY", "last": 489.0, "volatility": 0.01},)}},
            performance_truth={},
            timestamp_utc="2026-07-10T14:32:00Z",
        )
        engine = EventDetectionEngine()
        observed = engine.observe({"positionMonitoringNetwork": monitor_snapshot}, route=False)

        self.assertTrue(any(item["detector_id"] == "position_monitoring_network_detector" for item in observed["activeEvents"]))
        self.assertEqual("position_stop_loss_breached", observed["activeEvents"][-1]["event_type"])
        self.assertEqual(0, observed["lawCC"]["officeActivations"])
        self.assertEqual(0, observed["lawCC"]["workflowStarts"])
        self.assertEqual(0, observed["lawCC"]["brokerWrites"])

    def test_eo_ck_runtime_api_and_bridge_are_wired(self) -> None:
        runtime = create_runtime()
        state = runtime.position_monitoring_scan()
        self.assertIn("positionMonitoringNetwork", state)
        self.assertEqual("EO-CK", state["positionMonitoringNetwork"]["engineeringOrder"])
        self.assertTrue(state["positionMonitoringNetwork"]["lawCK"]["returnsImmediately"])

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("Position Monitoring Network", html)
        for button_id in ("pmn-scan", "pmn-replay"):
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
        self.assertIn("renderPositionMonitoringNetwork", js)
        self.assertIn("/api/position-monitoring/scan", js)
        self.assertIn("/api/position-monitoring/state", server)
        self.assertIn("/api/position-monitoring/scan", server)
        self.assertIn("/api/position-monitoring/replay", server)

    def test_eo_cl_bus_defaults_schema_subscribers_and_law_boundaries(self) -> None:
        bus = EnterpriseCommunicationsBus()
        snapshot = bus.snapshot()

        self.assertEqual("Enterprise Communications Bus", snapshot["busName"])
        self.assertEqual("EO-CL", snapshot["engineeringOrder"])
        self.assertGreaterEqual(len(snapshot["schemaRegistry"]), 10)
        self.assertGreaterEqual(snapshot["summary"]["activeSubscribers"], 5)
        self.assertFalse(snapshot["lawCL"]["authorizesMissions"])
        self.assertFalse(snapshot["lawCL"]["wakesOffices"])
        self.assertFalse(snapshot["lawCL"]["transfersWorkflowExecutionToken"])
        self.assertFalse(snapshot["lawCL"]["executesBusinessLogic"])
        self.assertFalse(snapshot["lawCL"]["placesTrades"])
        self.assertEqual(0, snapshot["lawCL"]["routineAiInvocations"])

    def test_eo_cl_position_observation_routes_to_eo_cc_without_mission_authority(self) -> None:
        bus = EnterpriseCommunicationsBus()
        result = bus.publish_observation(
            message_type="POSITION_MONITORING_OBSERVATION",
            source_service_id="Position Monitoring Network",
            payload={"event_type": "position_stop_loss_breached", "position_id": "POS-ECL", "severity": "critical"},
            target_service_id="Event Detection Engine",
            target_topic="position.monitoring",
            correlation_id="CORR-POS-ECL",
            position_id="POS-ECL",
            idempotency_key="OBS-POS-ECL",
            paper_live_mode=MessageMode.PAPER,
        )
        snapshot = bus.snapshot()

        self.assertTrue(result.accepted)
        self.assertEqual("CORR-POS-ECL", result.correlation_id)
        self.assertTrue(any(item["subscriber_service_id"] == "Event Detection Engine" for item in snapshot["outbox"]))
        self.assertEqual(0, snapshot["metrics"]["messagesRejected"])
        self.assertFalse(snapshot["lawCL"]["authorizesMissions"])
        self.assertFalse(snapshot["lawCL"]["wakesOffices"])
        trace = bus.get_correlation_trace("CORR-POS-ECL")
        self.assertEqual(1, trace["messageCount"])
        self.assertEqual("POSITION_MONITORING_OBSERVATION", trace["nodes"][0]["messageType"])

    def test_eo_cl_rejects_unauthorized_and_cross_mode_authority_messages(self) -> None:
        bus = EnterpriseCommunicationsBus()
        cost = bus.publish_command(
            message_type="COST_APPROVAL",
            source_service_id="Not EO-CE",
            target_service_id="API Execution Gateway",
            payload={"authorization_id": "AUTH-BAD", "amount_usd": 25.0},
            authorization_context_reference="AUTH-BAD",
            paper_live_mode=MessageMode.PAPER,
        )
        order = bus.publish_command(
            message_type="BROKER_ORDER_COMMAND",
            source_service_id="Unified Order Execution Engine",
            target_service_id="LIVE Broker Adapter",
            payload={"order_id": "ORD-CROSS", "side": "BUY", "symbol": "SPY"},
            authorization_context_reference="AUTH-ORDER",
            paper_live_mode=MessageMode.PAPER,
        )
        snapshot = bus.snapshot()

        self.assertFalse(cost.accepted)
        self.assertEqual("unauthorized_publisher", cost.reason_code)
        self.assertFalse(order.accepted)
        self.assertEqual("paper_live_mode_conflict", order.reason_code)
        self.assertGreaterEqual(snapshot["metrics"]["messagesQuarantined"], 2)
        self.assertGreaterEqual(snapshot["metrics"]["authorizationFailures"], 1)
        self.assertGreaterEqual(snapshot["metrics"]["paperLiveConflictAttempts"], 1)

    def test_eo_cl_workflow_handoff_requires_law_vii_metadata_and_does_not_transfer_token(self) -> None:
        bus = EnterpriseCommunicationsBus()
        rejected = bus.publish(
            bus.create_envelope(
                EnterpriseMessageKind.WORKFLOW_HANDOFF,
                "WORKFLOW_TOKEN_HANDOFF",
                "Workflow Runtime Monitor",
                {"workflow_id": "WF-ECL", "target_office_id": "Risk", "token_reference": "TOKEN-ECL"},
                workflow_id="WF-ECL",
                target_office_id="Risk",
                paper_live_mode=MessageMode.PAPER,
            )
        )
        accepted = bus.publish(
            bus.create_envelope(
                EnterpriseMessageKind.WORKFLOW_HANDOFF,
                "WORKFLOW_TOKEN_HANDOFF",
                "Workflow Runtime Monitor",
                {"workflow_id": "WF-ECL", "target_office_id": "Risk", "token_reference": "TOKEN-ECL"},
                workflow_id="WF-ECL",
                target_office_id="Risk",
                authorization_context_reference="LAW-VII-VALIDATION-REQUIRED",
                correlation_id="WF-ECL",
                idempotency_key="WF-ECL-HANDOFF",
                paper_live_mode=MessageMode.PAPER,
            )
        )
        snapshot = bus.snapshot()

        self.assertFalse(rejected.accepted)
        self.assertEqual("authorization_metadata_required", rejected.reason_code)
        self.assertTrue(accepted.accepted)
        self.assertTrue(any(item["subscriber_service_id"] == "Workflow Runtime Monitor" for item in snapshot["outbox"]))
        self.assertFalse(snapshot["lawCL"]["transfersWorkflowExecutionToken"])

    def test_eo_cl_dead_letter_retry_replay_and_recovery_are_deterministic(self) -> None:
        bus = EnterpriseCommunicationsBus()
        bus.register_subscriber(
            MessageSubscription(
                "ECL-SUB-FAIL",
                "Failure Test Subscriber",
                "Infrastructure",
                ("SYSTEM_NOTIFICATION",),
                ("1.0",),
                {"testBehavior": "terminal_fail"},
                (MessageMode.PAPER,),
                dead_letter_after_attempts=1,
            )
        )
        result = bus.publish_event(
            message_type="SYSTEM_NOTIFICATION",
            source_service_id="Commander Interface",
            payload={"summary": "Failure path"},
            correlation_id="CORR-DLQ-ECL",
            idempotency_key="DLQ-ECL",
            paper_live_mode=MessageMode.PAPER,
        )
        snapshot = bus.snapshot()
        dead = snapshot["deadLetters"][0]
        retry = bus.retry_dead_letter(dead["dead_letter_id"], {"commanderAuthorized": True})
        replay = bus.request_replay(result.message_id, analytical=True)
        recovered = EnterpriseCommunicationsBus()
        recovered.recover_from_snapshot(bus.snapshot())

        self.assertTrue(result.accepted)
        self.assertTrue(dead["replay_eligible"])
        self.assertTrue(retry["retried"])
        self.assertTrue(replay["accepted"])
        self.assertFalse(replay["productionMutation"])
        self.assertEqual(bus.snapshot()["summary"]["messagesPublished"], recovered.snapshot()["summary"]["messagesPublished"])

    def test_eo_cl_runtime_bridge_routes_and_ui_are_wired(self) -> None:
        runtime = create_runtime()
        state = runtime.position_monitoring_scan()

        self.assertIn("enterpriseCommunicationsBus", state)
        bus = state["enterpriseCommunicationsBus"]
        self.assertEqual("EO-CL", bus["engineeringOrder"])
        self.assertTrue(any(item["message_type"] == "POSITION_MONITORING_OBSERVATION" for item in bus["messageStream"]) or bus["summary"]["messagesPublished"] >= 1)
        self.assertFalse(bus["lawCL"]["authorizesMissions"])
        self.assertFalse(bus["lawCL"]["wakesOffices"])

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("Enterprise Communications Bus", html)
        for button_id in ("ecl-publish", "ecl-trace-latest", "ecl-replay", "ecl-retry"):
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
        self.assertIn("renderEnterpriseCommunicationsBus", js)
        self.assertIn("/api/communications-bus/state", server)
        self.assertIn("/api/communications-bus/publish", server)
        self.assertIn("/api/communications-bus/replay", server)
        self.assertIn("/api/communications-bus/retry", server)

    def _efficiency_sources(self) -> dict:
        return {
            "costs": {"today_api_credits_usd": 0.02, "budget_status": "NOMINAL"},
            "enterpriseOperationsScheduler": {
                "missionRecords": (
                    {"mission_id": "MIS-001", "mission_type": "position_review", "status": "COMPLETED", "queue_seconds": 30, "active_seconds": 90, "actual_cost": 0.01, "required_offices": ("Risk",)},
                    {"mission_id": "MIS-002", "mission_type": "commander_briefing", "status": "QUEUED", "queue_seconds": 60, "actual_cost": 0.0, "required_offices": ("Executive",)},
                )
            },
            "scheduler": {"offices": ({"office": "Risk", "activation_count": 1}, {"office": "Trader", "activation_count": 0})},
            "officeDutyOfficers": {"metrics": {"fullOfficeActivationsAvoided": 2}},
            "workflowOrchestrator": {"metrics": {"workflowCount": 4}, "workflows": ({"workflow_id": "WF-001", "execution_time_seconds": 120, "credits_used": 0.01, "status": "Completed", "office_states": {"Risk": "Dormant"}},)},
            "workflowRuntimeMonitor": {"metrics": {"completedWorkflows": 3, "executingOffices": 1, "dormantOffices": 3, "activeWorkflows": 1}},
            "apiRuntimeMonitor": {"metrics": {"apiCallsLogged": 1}, "costThisSessionUsd": 0.02},
            "apiExecutionGateway": {"metrics": {"allowedCount": 1, "blockedCount": 0}},
            "enterpriseCostGovernor": {"usageLedger": (), "summary": {"settledCost": 0.02}},
            "enterpriseMemoryCache": {"headerIndicators": {"cacheHits": 3, "cacheMisses": 1, "costAvoided": 0.03}, "metrics": {"exactReuse": 2, "partialReuse": 1}},
            "informationFreshnessEngine": {"summary": {"freshRecords": 4, "staleRecords": 1}},
            "workflowDeltaEngine": {"deltaPackages": ({"delta_package_id": "CH-PKG-1", "cost_reduction_evidence": {"fullReassessmentRequired": False}},)},
            "enterprisePriorityEngine": {"rankedQueue": ({"candidateId": "PRI-1", "disposition": "Run Now"},)},
            "positionMonitoringNetwork": {"summary": {"activePositionsMonitored": 2}, "watcherCoverage": {"positionsWithWatchers": 2}},
            "enterpriseCommunicationsBus": {"summary": {"deliverySuccessRate": 90.0, "messagesPublished": 10, "retryBacklog": 4, "deadLetterCount": 1, "paperLaneLatencyMs": 0, "liveLaneLatencyMs": 0}, "outbox": ({"delivery_state": "ACKNOWLEDGED"}, {"delivery_state": "RETRY_SCHEDULED"})},
            "enterpriseFailureRecoveryFramework": {"failureRecords": ({"failureId": "FAIL-1", "status": "OPEN"},)},
            "eventDetectionEngine": {"activeEvents": ()},
            "performanceTruthEngine": {"portfolioLedger": (), "orderLedger": ()},
            "cnac": {"notifications": ({"notification_id": "N1", "status": "Open"}, {"notification_id": "N2", "status": "Open"})},
            "commanderDailyReviewWorkspace": {"unresolvedItems": ("review-risk",)},
        }

    def test_eo_cn_metric_registry_snapshot_and_law_boundaries(self) -> None:
        analytics = EnterpriseEfficiencyAnalytics()
        snapshot = analytics.snapshot()

        self.assertEqual("Enterprise Efficiency Analytics", snapshot["analyticsName"])
        self.assertEqual("EO-CN", snapshot["engineeringOrder"])
        self.assertGreaterEqual(len(snapshot["metricRegistry"]), 12)
        self.assertFalse(snapshot["lawCN"]["authorizesMissions"])
        self.assertFalse(snapshot["lawCN"]["changesEnterprisePriority"])
        self.assertFalse(snapshot["lawCN"]["approvesCost"])
        self.assertFalse(snapshot["lawCN"]["wakesOffices"])
        self.assertFalse(snapshot["lawCN"]["transfersWorkflowExecutionToken"])
        self.assertTrue(snapshot["lawCN"]["lawVIIIntact"])

    def test_eo_cn_calculates_metrics_lineage_findings_and_scorecard(self) -> None:
        analytics = EnterpriseEfficiencyAnalytics()
        result = analytics.analyze(self._efficiency_sources(), window_start="2026-07-10T00:00:00Z", window_end="2026-07-10T23:59:59Z", persist=True)

        metrics = {item["metric_id"]: item for item in result["metricValues"]}
        self.assertEqual(2.0, metrics["ECN-MISSION-THROUGHPUT"]["value"])
        self.assertEqual(3.0, metrics["ECN-WORKFLOW-THROUGHPUT"]["value"])
        self.assertEqual(75.0, metrics["ECN-CACHE-REUSE"]["value"])
        self.assertEqual(100.0, metrics["ECN-DELTA-WORK"]["value"])
        self.assertEqual(100.0, metrics["ECN-MONITORING-COVERAGE"]["value"])
        self.assertEqual(90.0, metrics["ECN-MESSAGE-DELIVERY"]["value"])
        self.assertTrue(metrics["ECN-MESSAGE-DELIVERY"]["metric_hash"])
        self.assertTrue(result["metricLineage"])
        self.assertTrue(any(item["finding_type"] == "COMMUNICATION_RETRY_BURDEN" for item in result["findings"]))
        self.assertTrue(result["scorecard"])
        self.assertEqual("observed_metric_not_causal_claim", result["findings"][0]["causal_status"])

    def test_eo_cn_marks_missing_data_insufficient_not_zero(self) -> None:
        analytics = EnterpriseEfficiencyAnalytics()
        result = analytics.analyze({"enterpriseCommunicationsBus": {"summary": {"deliverySuccessRate": 100.0}}}, persist=False)
        metrics = {item["metric_id"]: item for item in result["metricValues"]}

        self.assertIsNone(metrics["ECN-CACHE-REUSE"]["value"])
        self.assertEqual(DataQualityClassification.INSUFFICIENT.value, metrics["ECN-CACHE-REUSE"]["data_completeness"])
        self.assertTrue(any(item["finding_type"] == "DATA_QUALITY_GAP" for item in result["findings"]))

    def test_eo_cn_recalculation_comparison_acknowledgement_and_lineage_are_advisory(self) -> None:
        analytics = EnterpriseEfficiencyAnalytics()
        result = analytics.analyze(self._efficiency_sources(), persist=True)
        metric_id = result["metricValues"][0]["metric_value_id"]
        finding_id = result["findings"][0]["finding_id"]

        lineage = analytics.get_metric_lineage(metric_id)
        recalculated = analytics.recalculate_metric(metric_id)
        acknowledged = analytics.acknowledge_finding(finding_id, "Reviewed in test.")
        comparison = analytics.compare_periods(result, result)

        self.assertTrue(lineage["found"])
        self.assertTrue(recalculated["accepted"])
        self.assertFalse(recalculated["productionMutation"])
        self.assertTrue(any(item["acknowledged"] for item in acknowledged["findings"]))
        self.assertEqual("comparison_only_no_causal_claim", comparison["comparisons"][0]["causalStatus"])
        self.assertFalse(comparison["lawCN"]["authorizesMissions"])

    def test_eo_cn_runtime_bridge_routes_and_ui_are_wired(self) -> None:
        runtime = create_runtime()
        state = runtime.efficiency_analytics_refresh({})

        self.assertIn("enterpriseEfficiencyAnalytics", state)
        analytics = state["enterpriseEfficiencyAnalytics"]
        self.assertEqual("EO-CN", analytics["engineeringOrder"])
        self.assertTrue(analytics["scorecard"])
        self.assertFalse(analytics["lawCN"]["wakesOffices"])
        self.assertFalse(analytics["lawCN"]["changesBudgets"])

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("Enterprise Efficiency Analytics", html)
        for button_id in ("ecn-refresh", "ecn-compare", "ecn-recalculate", "ecn-lineage-latest", "ecn-acknowledge"):
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
        self.assertIn("renderEnterpriseEfficiencyAnalytics", js)
        self.assertIn("/api/efficiency-analytics/state", server)
        self.assertIn("/api/efficiency-analytics/refresh", server)
        self.assertIn("/api/efficiency-analytics/recalculate", server)
        self.assertIn("/api/efficiency-analytics/lineage", server)

    def test_eo_co_bootstrap_doctrine_policy_matrix_and_law_boundaries(self) -> None:
        manager = EnterpriseDoctrinePolicyManager()
        snapshot = manager.snapshot()

        self.assertEqual("Enterprise Doctrine & Policy Manager", snapshot["managerName"])
        self.assertEqual("EO-CO", snapshot["engineeringOrder"])
        self.assertTrue(any(item["doctrine_id"] == "LAW-VII" for item in snapshot["doctrineLibrary"]))
        self.assertGreaterEqual(len(snapshot["policySchemaRegistry"]), 14)
        self.assertGreaterEqual(snapshot["policyMetrics"]["activePolicies"], 14)
        self.assertFalse(snapshot["lawCO"]["authorizesMissions"])
        self.assertFalse(snapshot["lawCO"]["wakesOffices"])
        self.assertFalse(snapshot["lawCO"]["transfersWorkflowExecutionToken"])
        self.assertFalse(snapshot["lawCO"]["approvesIndividualExpenditure"])
        self.assertFalse(snapshot["lawCO"]["issuesTrades"])
        self.assertFalse(snapshot["lawCO"]["rewritesLedgers"])
        self.assertTrue(snapshot["lawCO"]["lawVIIConstitutional"])

        domains = {item["policyDomain"] for item in snapshot["seriesCIntegrationMatrix"]}
        for domain in ("SCHEDULING", "PRIORITY", "POSITION_MONITORING", "COMMUNICATIONS", "EFFICIENCY_ANALYTICS"):
            self.assertIn(domain, domains)
        self.assertTrue(all(item["eoCoAuthority"] for item in snapshot["seriesCIntegrationMatrix"]))

    def test_eo_co_rejects_self_wake_law_vii_and_unsafe_policy(self) -> None:
        manager = EnterpriseDoctrinePolicyManager()
        result = manager.submit_policy(
            {
                "policyDomain": "OFFICE_WAKEFULNESS",
                "policyId": "CO-POL-OFFICE_WAKEFULNESS",
                "schemaId": "CO-SCHEMA-OFFICE_WAKEFULNESS",
                "configuration": {
                    "enabled": True,
                    "modeApplicability": "BOTH",
                    "acknowledgementRequired": True,
                    "selfWakeAllowed": True,
                    "workflowTokenParallelOwners": 2,
                    "paperLiveSharedState": False,
                    "brokerReconciliationRequired": True,
                    "aiExpenditureUnbounded": False,
                    "immutableLedgerRewriteAllowed": False,
                },
            },
            idempotency_key="eo-co-self-wake",
        )

        self.assertFalse(result["accepted"])
        errors = result["validation"]["errors"]
        self.assertIn("law_vii_conflict", errors)
        self.assertIn("office_self_wake_rejected", errors)
        self.assertIn("simultaneous_reasoning_office_ownership_rejected", errors)
        self.assertFalse(result["validation"]["lawVIIIntact"])

    def test_eo_co_validation_approval_activation_distribution_and_resolution(self) -> None:
        manager = EnterpriseDoctrinePolicyManager()
        submitted = manager.submit_policy(
            {
                "policyDomain": "PRIORITY",
                "policyId": "CO-POL-PRIORITY",
                "schemaId": "CO-SCHEMA-PRIORITY",
                "semanticVersion": "1.0.1",
                "configuration": {
                    "enabled": True,
                    "modeApplicability": "BOTH",
                    "acknowledgementRequired": True,
                    "priorityThreshold": 82,
                    "selfWakeAllowed": False,
                    "workflowTokenParallelOwners": 1,
                    "paperLiveSharedState": False,
                    "brokerReconciliationRequired": True,
                    "aiExpenditureUnbounded": False,
                    "immutableLedgerRewriteAllowed": False,
                },
            },
            idempotency_key="eo-co-priority-submit",
        )
        version_id = submitted["policyVersion"]["policy_version_id"]
        approved = manager.approve_policy(version_id, {"approver": "Commander", "authority": "Commander"}, idempotency_key="eo-co-priority-approve")
        scheduled = manager.schedule_activation(version_id, {"activationStrategy": "STAGED"}, idempotency_key="eo-co-priority-stage")
        plan_id = scheduled["activationPlan"]["activation_plan_id"]
        activated = manager.activate_policy(plan_id, idempotency_key="eo-co-priority-activate")
        resolved = manager.get_active_policy(PolicyDomain.PRIORITY)

        self.assertTrue(submitted["accepted"])
        self.assertTrue(approved["approved"])
        self.assertTrue(scheduled["scheduled"])
        self.assertTrue(activated["activated"])
        self.assertEqual(82, resolved.final_resolved_values["priorityThreshold"])
        self.assertIn(version_id, resolved.applicable_policy_versions)
        self.assertTrue(any(item["policy_version_id"] == version_id for item in activated["state"]["distributionRecords"]))

    def test_eo_co_directives_drift_rollback_and_replay_are_bounded(self) -> None:
        manager = EnterpriseDoctrinePolicyManager()
        cost_row = next(item for item in manager.snapshot()["activePolicyMatrix"] if item["policyDomain"] == "COST_GOVERNANCE")
        version_id = cost_row["policyVersionId"]

        directive = manager.issue_temporary_directive(
            {
                "policyDomain": "ENTERPRISE_MODE",
                "issuer": "Commander",
                "expiresAt": "2999-01-01T00:00:00Z",
                "requestedChange": {"newLiveOrdersEnabled": False},
            }
        )
        drift = manager.detect_drift("Enterprise Cost Governor", version_id, {"enabled": True, "budgetCeilingUsd": 999.0})
        replay = manager.replay(version_id)
        rollback = manager.rollback_policy(version_id, {"actor": "Commander"})

        self.assertTrue(directive["accepted"])
        self.assertTrue(drift["driftDetected"])
        self.assertEqual("UNAUTHORIZED_OVERRIDE", drift["driftRecord"]["drift_classification"])
        self.assertFalse(replay["productionMutation"])
        self.assertFalse(replay["wakesOffices"])
        self.assertFalse(rollback["rolledBack"])
        self.assertEqual("rollback_unsafe", rollback["reasonCode"])
        self.assertEqual("SECURITY_HOLD", manager.snapshot()["health"]["overallState"])

    def test_eo_co_runtime_routes_ui_and_eo_cl_policy_publication_are_wired(self) -> None:
        runtime = create_runtime()
        state = runtime.doctrine_policy_state()
        self.assertIn("enterpriseDoctrinePolicyManager", runtime.state())
        self.assertEqual("EO-CO", state["engineeringOrder"])
        self.assertTrue(state["activePolicyMatrix"])

        submitted = runtime.doctrine_policy_submit(
            {
                "policyDomain": "COMMUNICATIONS",
                "policyId": "CO-POL-COMMUNICATIONS",
                "schemaId": "CO-SCHEMA-COMMUNICATIONS",
                "configuration": {
                    "enabled": True,
                    "modeApplicability": "BOTH",
                    "acknowledgementRequired": True,
                    "retryLimit": 3,
                    "selfWakeAllowed": False,
                    "workflowTokenParallelOwners": 1,
                    "paperLiveSharedState": False,
                    "brokerReconciliationRequired": True,
                    "aiExpenditureUnbounded": False,
                    "immutableLedgerRewriteAllowed": False,
                },
            }
        )
        version_id = submitted["enterpriseDoctrinePolicyManager"]["policyVersions"][-1]["policy_version_id"]
        runtime.doctrine_policy_approve(version_id, {"approver": "Commander", "authority": "Commander"})
        scheduled = runtime.doctrine_policy_schedule(version_id, {"activationStrategy": "STAGED", "targetSubscribers": ["Enterprise Communications Bus"]})
        plan_id = scheduled["enterpriseDoctrinePolicyManager"]["activationPlans"][-1]["activation_plan_id"]
        activated = runtime.doctrine_policy_activate(plan_id)

        self.assertTrue(any(item["message_type"] == "POLICY_PUBLICATION" for item in activated["enterpriseCommunicationsBus"]["messageStream"]))
        self.assertFalse(activated["enterpriseDoctrinePolicyManager"]["lawCO"]["startsMissions"])
        self.assertFalse(activated["enterpriseDoctrinePolicyManager"]["lawCO"]["wakesOffices"])

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("Enterprise Doctrine &amp; Policy Manager", html)
        for button_id in ("eco-submit-safe", "eco-approve-latest", "eco-stage-latest", "eco-activate-latest", "eco-restrictive-directive", "eco-drift-sample", "eco-replay", "eco-impact"):
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
        self.assertIn("renderEnterpriseDoctrinePolicyManager", js)
        self.assertIn("/api/doctrine-policy/state", server)
        self.assertIn("/api/doctrine-policy/submit", server)
        self.assertIn("/api/doctrine-policy/activate", server)

    def test_eo_cc_event_detection_engine_defaults_safe_and_complete(self) -> None:
        engine = EventDetectionEngine()
        snapshot = engine.snapshot()

        self.assertEqual("Event Detection Engine", snapshot["engineName"])
        self.assertEqual("EO-CC", snapshot["engineeringOrder"])
        self.assertGreaterEqual(snapshot["activeDetectors"], 9)
        self.assertEqual(0, snapshot["lawCC"]["routineAiInvocations"])
        self.assertEqual(0, snapshot["lawCC"]["officeActivations"])
        self.assertEqual(0, snapshot["lawCC"]["workflowStarts"])
        self.assertEqual(0.0, snapshot["externalDataApiCost"])
        domains = {item["domain"] for item in snapshot["rules"]}
        for domain in ("market", "portfolio", "position", "order", "risk", "intelligence", "enterprise", "commander", "schedule"):
            self.assertIn(domain, domains)

    def test_eo_cc_market_event_validation_hash_and_duplicate_suppression(self) -> None:
        engine = EventDetectionEngine()
        engine.observe({"marketDataProviderAbstractionLayer": {"normalizedObjects": {"quotes": ({"symbol": "AAPL", "last": 100.0},)}}}, route=False)
        snapshot = engine.observe({"marketDataProviderAbstractionLayer": {"normalizedObjects": {"quotes": ({"symbol": "AAPL", "last": 103.0},)}}}, route=False)

        self.assertEqual(1, snapshot["validatedEventsToday"])
        event = snapshot["activeEvents"][0]
        self.assertEqual("market", event["domain"])
        self.assertEqual("price_movement", event["event_type"])
        self.assertEqual(3.0, event["delta_percent"])
        self.assertTrue(event["content_hash"])

        suppressed = engine.observe({"marketDataProviderAbstractionLayer": {"normalizedObjects": {"quotes": ({"symbol": "AAPL", "last": 106.0},)}}}, route=False)
        self.assertGreaterEqual(suppressed["suppressedEventsToday"], 1)
        self.assertIn(suppressed["suppressionAndDeduplication"][-1]["reason"], {"duplicate_event", "cooldown_active"})

    def test_eo_cc_noise_suppression_and_position_safety_priority(self) -> None:
        engine = EventDetectionEngine()
        transient = engine._candidate(
            "market_price_detector",
            EventDomain.MARKET,
            "price_movement",
            "MarketDataProvider",
            "MSFT",
            100,
            103,
            "percent_change",
            "market_price_movement",
            ticker="MSFT",
            metadata={"transient": True},
        )
        self.assertIsNone(engine._validate_candidate(transient))
        self.assertEqual("persistence_requirement_not_met", engine.snapshot()["suppressionAndDeduplication"][-1]["reason"])

        position_source = {
            "positionSurveillanceEngine": {
                "latestSnapshots": (
                    {
                        "position_id": "POS-EO-CC",
                        "symbol": "AAPL",
                        "average_cost": 100.0,
                        "current_price": 94.0,
                        "current_value": 940.0,
                        "detected_events": ("stop_loss_reached",),
                    },
                )
            }
        }
        snapshot = engine.observe(position_source, route=False)
        event = snapshot["activeEvents"][-1]
        self.assertEqual("position", event["domain"])
        self.assertEqual("critical", event["severity"])
        self.assertEqual("immediate", event["urgency"])
        self.assertEqual("major", event["materiality"])

    def test_eo_cc_routes_validated_events_through_odo_and_eos_only(self) -> None:
        scheduler = EnterpriseOperationsScheduler()
        scheduler.set_enabled(True)
        scheduler.set_mode("Full Paper Trading")
        engine = EventDetectionEngine()

        snapshot = engine.observe(
            {
                "positionSurveillanceEngine": {
                    "latestSnapshots": (
                        {
                            "position_id": "POS-ROUTE",
                            "symbol": "SPY",
                            "average_cost": 500.0,
                            "current_price": 475.0,
                            "current_value": 4750.0,
                            "detected_events": ("stop_loss_reached",),
                        },
                    )
                }
            },
            eos=scheduler,
            duty_officers=scheduler.duty_officers,
            route=True,
        )

        self.assertEqual("mission_proposed", snapshot["activeEvents"][0]["status"])
        self.assertTrue(snapshot["routingRecords"][0]["scheduler_mission_id"])
        self.assertTrue(scheduler.snapshot()["missionRecords"])
        self.assertGreaterEqual(len(scheduler.duty_officers.snapshot(scheduler.snapshot())["auditDetail"]), 1)
        self.assertEqual(0, snapshot["lawCC"]["officeActivations"])
        self.assertEqual(0, snapshot["lawCC"]["workflowStarts"])
        self.assertEqual(0, snapshot["lawCC"]["brokerWrites"])
        self.assertEqual(0, snapshot["lawCC"]["ledgerMutations"])

    def test_eo_cc_restart_replay_and_json_safe_snapshot(self) -> None:
        engine = EventDetectionEngine()
        source = {"marketDataProviderAbstractionLayer": {"normalizedObjects": {"quotes": ({"symbol": "QQQ", "last": 100.0},)}}}
        engine.observe(source, route=False)
        event_source = {"marketDataProviderAbstractionLayer": {"normalizedObjects": {"quotes": ({"symbol": "QQQ", "last": 103.5},)}}}
        snapshot = engine.observe(event_source, route=False)
        json.dumps(snapshot)

        recovered = EventDetectionEngine()
        recovered.recover_from_snapshot(snapshot)
        recovered_snapshot = recovered.snapshot()
        self.assertEqual(snapshot["activeEvents"][0]["event_id"], recovered_snapshot["activeEvents"][0]["event_id"])
        self.assertEqual(EventStatus.VALIDATED.value, recovered_snapshot["activeEvents"][0]["status"])

        replay = engine.replay((source, event_source))
        self.assertTrue(replay["replayMode"])
        self.assertFalse(replay["productionMutation"])
        self.assertEqual(1, replay["validatedEventsToday"])
        self.assertEqual(1, snapshot["validatedEventsToday"])

    def test_eo_cc_runtime_api_and_bridge_are_wired(self) -> None:
        runtime = create_runtime()
        state = runtime.event_detection_observe()
        self.assertIn("eventDetectionEngine", state)
        self.assertEqual("EO-CC", state["eventDetectionEngine"]["engineeringOrder"])

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("Event Detection Bridge", html)
        for button_id in ("ede-observe", "ede-replay"):
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
        self.assertIn("renderEventDetectionEngine", js)
        self.assertIn("/api/event-detection/observe", js)
        self.assertIn("/api/event-detection/observe", server)
        self.assertIn("/api/event-detection/replay", server)
        self.assertIn("/api/event-detection/resolve", server)

    def test_eo_cd_mission_planner_defaults_templates_and_law_boundaries(self) -> None:
        planner = EnterpriseMissionPlanner()
        snapshot = planner.snapshot()

        self.assertEqual("Enterprise Mission Planner", snapshot["plannerName"])
        self.assertEqual("EO-CD", snapshot["engineeringOrder"])
        self.assertTrue(snapshot["enabled"])
        self.assertGreaterEqual(len(snapshot["missionTemplates"]), 8)
        self.assertTrue(any(item["mission_type"] == "position_safety_review" for item in snapshot["missionTemplates"]))
        self.assertTrue(any(item["office_id"] == "Risk" for item in snapshot["officeCapabilityRegistry"]))
        self.assertEqual(0, snapshot["lawCD"]["officeActivations"])
        self.assertEqual(0, snapshot["lawCD"]["workflowStarts"])
        self.assertEqual(0, snapshot["lawCD"]["routineAiInvocations"])
        self.assertEqual(0, snapshot["lawCD"]["brokerOrdersSubmitted"])
        self.assertEqual(0, snapshot["lawCD"]["ledgerMutations"])
        self.assertEqual(0, snapshot["lawCD"]["selfAuthorizedPlans"])

    def test_eo_cd_validated_position_event_creates_minimum_workforce_plan(self) -> None:
        planner = EnterpriseMissionPlanner()
        event = {
            "event_id": "EDE-EVT-POS-001",
            "event_type": "stop_loss_reached",
            "title": "Position Stop Loss Reached",
            "subject_id": "POS-AAPL-001",
            "position_id": "POS-AAPL-001",
            "ticker": "AAPL",
            "severity": "critical",
            "urgency": "immediate",
            "materiality": "major",
            "recommended_mission_type": "position_safety_review",
            "recommended_offices": ("Risk", "Trader"),
            "metadata": {"changed_fields": ("current_price", "distance_to_stop")},
        }

        snapshot = planner.plan_from_event(event)
        plan = snapshot["draftMissionPlans"][0]
        offices = {item["office_id"] for item in plan["office_assignments"]}
        self.assertEqual("ready_for_submission", plan["status"])
        self.assertEqual("position_safety_review", plan["mission_type"])
        self.assertIn("Risk", offices)
        self.assertIn("Position Lifecycle", offices)
        self.assertNotIn("Seeker", offices)
        self.assertTrue(plan["delta_decision"]["delta_mission"])
        self.assertTrue(plan["dependencies"])
        self.assertTrue(plan["input_requirements"])
        self.assertTrue(plan["output_contracts"])
        self.assertGreater(plan["resource_envelope"]["runtime_ceiling_seconds"], 0)
        self.assertTrue(all(result["valid"] for result in plan["validation_results"]))

    def test_eo_cd_cache_resolution_prevents_new_mission(self) -> None:
        planner = EnterpriseMissionPlanner()
        snapshot = planner.plan_commander_request(
            {
                "directiveId": "CMD-CACHE",
                "objective": "Retrieve current report for AAPL",
                "subjectId": "AAPL",
                "missionType": "information_refresh",
                "metadata": {"cache_current": True, "cache_reference": "CACHE-AAPL-001"},
            }
        )

        self.assertEqual(1, snapshot["metrics"]["noActionDecisions"])
        self.assertEqual("not_required", snapshot["allMissionPlans"][0]["status"])
        self.assertEqual("USE_CACHED_OR_LOCAL_RESULT", snapshot["allMissionPlans"][0]["necessity_decision"])
        self.assertEqual([], list(snapshot["draftMissionPlans"]))

    def test_eo_cd_duplicate_merge_supersession_and_restart_recovery(self) -> None:
        planner = EnterpriseMissionPlanner()
        event = {
            "event_id": "EDE-EVT-BRK-001",
            "event_type": "order_rejected",
            "subject_id": "ORD-55",
            "order_id": "ORD-55",
            "severity": "high",
            "recommended_mission_type": "broker_reconciliation",
        }
        second = dict(event, event_id="EDE-EVT-BRK-002")
        planner.plan_from_event(event)
        merged = planner.plan_from_event(second)
        self.assertEqual(1, merged["metrics"]["plansMerged"])
        self.assertEqual(2, len(merged["draftMissionPlans"][0]["source_trigger_ids"]))

        routine = {
            "event_id": "EDE-EVT-POS-ROUTINE",
            "event_type": "stop_loss_approached",
            "subject_id": "POS-SPY-1",
            "position_id": "POS-SPY-1",
            "severity": "moderate",
            "recommended_mission_type": "position_safety_review",
        }
        critical = dict(routine, event_id="EDE-EVT-POS-CRITICAL", severity="critical")
        planner.plan_from_event(routine)
        before = planner.snapshot()["draftMissionPlans"][-1]["mission_plan_id"]
        planner.plan_from_event(critical)
        after_snapshot = planner.snapshot()
        self.assertTrue(any(item["old_plan_id"] == before for item in after_snapshot["supersessionRecords"]))

        recovered = EnterpriseMissionPlanner()
        recovered.recover_from_snapshot(after_snapshot)
        self.assertEqual(len(after_snapshot["allMissionPlans"]), len(recovered.snapshot()["allMissionPlans"]))

    def test_eo_cd_scheduler_submission_does_not_authorize_or_dispatch(self) -> None:
        planner = EnterpriseMissionPlanner()
        scheduler = EnterpriseOperationsScheduler()
        scheduler.set_enabled(True)
        scheduler.set_mode("Full Paper Trading")
        planner.plan_from_event(
            {
                "event_id": "EDE-EVT-POS-SUBMIT",
                "event_type": "stop_loss_reached",
                "subject_id": "POS-SUBMIT",
                "position_id": "POS-SUBMIT",
                "severity": "critical",
                "recommended_mission_type": "position_safety_review",
            }
        )
        plan_id = planner.snapshot()["draftMissionPlans"][0]["mission_plan_id"]
        submitted = planner.submit_plan(plan_id, eos=scheduler)
        scheduler_snapshot = scheduler.snapshot()

        self.assertEqual(MissionPlanStatus.SUBMITTED, submitted.status)
        self.assertTrue(submitted.scheduler_disposition["scheduler_mission_id"])
        mission = scheduler_snapshot["missionRecords"][0]
        self.assertIn(mission["status"], {"Queued", "Planned"})
        self.assertEqual(0, scheduler_snapshot["activeMissionCount"])
        self.assertEqual(0, len(scheduler_snapshot["activationRequests"]))
        self.assertFalse(submitted.scheduler_disposition["authorization_performed"])
        self.assertEqual(0, planner.snapshot()["lawCD"]["officeActivations"])

    def test_eo_cd_runtime_api_bridge_and_replay_are_wired(self) -> None:
        runtime = create_runtime()
        state = runtime.mission_planner_commander_request({"directiveId": "CMD-BRIEF", "objective": "Generate Commander report", "missionType": "commander_briefing"})
        self.assertIn("enterpriseMissionPlanner", state)
        self.assertEqual("EO-CD", state["enterpriseMissionPlanner"]["engineeringOrder"])
        self.assertTrue(state["enterpriseMissionPlanner"]["draftMissionPlans"])

        replay = runtime.mission_planner_replay((
            {
                "trigger_id": "EMP-TRG-REPLAY",
                "trigger_type": MissionTriggerType.COMMANDER_DIRECTIVE.value,
                "source_event_id": "",
                "source_event_group_id": "",
                "source_schedule_id": "",
                "source_directive_id": "CMD-REPLAY",
                "source_duty_officer_id": "",
                "title": "Replay",
                "summary": "Replay a cost review.",
                "subject_type": "directive",
                "subject_id": "cost",
                "ticker": "",
                "position_id": "",
                "order_id": "",
                "workflow_id": "",
                "severity": "moderate",
                "urgency": "prompt",
                "materiality": "material",
                "confidence": 1.0,
                "requested_mission_type": "cost_review",
                "recommended_offices": (),
                "earliest_start_at": "",
                "deadline_at": "",
                "expires_at": "",
                "provenance": {},
                "metadata": {},
                "received_at": "",
            },
        ))
        self.assertTrue(replay["enterpriseMissionPlanningReplay"]["replayMode"])
        self.assertFalse(replay["enterpriseMissionPlanningReplay"]["productionMutation"])

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("Enterprise Mission Planner", html)
        for button_id in ("emp-create-request", "emp-replay"):
            self.assertIn(f'id="{button_id}"', html)
            self.assertIn(f'("{button_id}").addEventListener', js)
        self.assertIn("renderEnterpriseMissionPlanner", js)
        self.assertIn("/api/mission-planner/commander-request", js)
        self.assertIn("/api/mission-planner/plan-event", server)
        self.assertIn("/api/mission-planner/submit", server)
        self.assertIn("/api/mission-planner/replay", server)

    def test_eo_ce_cost_governor_defaults_policy_reserves_and_law_boundaries(self) -> None:
        governor = EnterpriseCostGovernor()
        snapshot = governor.snapshot()

        self.assertEqual("Enterprise Cost Governor", snapshot["governorName"])
        self.assertEqual("EO-CE", snapshot["engineeringOrder"])
        self.assertEqual("HEALTHY", snapshot["status"])
        self.assertGreaterEqual(len(snapshot["budgetAccounts"]), 10)
        self.assertTrue(snapshot["protectedReserves"])
        self.assertTrue(snapshot["gatewayIntegration"]["mandatory"])
        self.assertTrue(snapshot["lawCE"]["unattributedSpendBlocked"])
        self.assertFalse(snapshot["lawCE"]["costAuthorityCreatesMissions"])
        self.assertFalse(snapshot["lawCE"]["officeWakeAuthority"])
        self.assertFalse(snapshot["lawCE"]["directProviderBypassAllowed"])

    def test_eo_ce_plan_reservation_gateway_usage_settlement_and_duplicate_protection(self) -> None:
        runtime = create_runtime()
        state = runtime.mission_planner_commander_request({"directiveId": "CMD-COST", "objective": "Generate Commander report", "missionType": "commander_briefing"})
        plan_id = state["enterpriseMissionPlanner"]["draftMissionPlans"][0]["mission_plan_id"]
        state = runtime.cost_governor_reserve_for_plan(plan_id)
        reservation = state["enterpriseCostGovernor"]["missionReservations"][0]
        self.assertIn(reservation["state"], {"approved", "reduced"})
        self.assertEqual("commander_briefing", state["enterpriseMissionPlanner"]["draftMissionPlans"][0]["mission_type"])

        workflow_id, token_id, owner = self._executing_workflow_scope(runtime, stages=("Analyst",), credit_budget=0.5)
        request = replace(self._gateway_request(workflow_id, token_id, owner, cost=0.001), cost_reservation_id=reservation["reservation_id"])
        response = runtime.api_execution_gateway.execute_model_request(request)
        self.assertTrue(response.allowed)
        state = runtime.state()
        cost = state["enterpriseCostGovernor"]
        self.assertEqual(1, len(cost["usageRecords"]))
        self.assertEqual(1, cost["metrics"]["activeReservations"])

        duplicate = runtime.enterprise_cost_governor.record_gateway_usage(request, response, cost["authorizationStream"][-1])
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(1, len(runtime.enterprise_cost_governor.snapshot()["usageRecords"]))

        settled = runtime.cost_governor_settle_reservation(reservation["reservation_id"])
        settled_reservation = settled["enterpriseCostGovernor"]["missionReservations"][0]
        self.assertEqual("settled", settled_reservation["state"])
        self.assertGreaterEqual(len(settled["enterpriseCostGovernor"]["costLedger"]), 1)

    def test_eo_ce_unreserved_gateway_call_and_prohibited_model_are_blocked(self) -> None:
        runtime = create_runtime()
        workflow_id, token_id, owner = self._executing_workflow_scope(runtime, stages=("Analyst",), credit_budget=0.5)

        unreserved = runtime.enterprise_cost_governor.authorize_gateway_request(self._gateway_request(workflow_id, token_id, owner, cost=0.001))
        self.assertFalse(unreserved["allowed"])
        self.assertEqual("COST_GOVERNOR_UNRESERVED_CALL", unreserved["code"])

        real_pilot = runtime.enterprise_cost_governor.authorize_gateway_request(self._real_gateway_request(workflow_id, token_id, owner, cost=0.001))
        self.assertTrue(real_pilot["allowed"])
        self.assertTrue(real_pilot["reservationId"].startswith("ECG-RES-"))

        state = runtime.mission_planner_commander_request({"directiveId": "CMD-MODEL", "objective": "Generate Commander report", "missionType": "commander_briefing"})
        plan_id = state["enterpriseMissionPlanner"]["draftMissionPlans"][0]["mission_plan_id"]
        state = runtime.cost_governor_reserve_for_plan(plan_id)
        reservation_id = state["enterpriseCostGovernor"]["missionReservations"][0]["reservation_id"]
        prohibited = replace(self._gateway_request(workflow_id, token_id, owner, cost=0.001), cost_reservation_id=reservation_id, provider="openai", model="gpt-5-thinking-unbounded")
        response = runtime.enterprise_cost_governor.authorize_gateway_request(prohibited)
        self.assertFalse(response["allowed"])
        self.assertEqual("COST_GOVERNOR_MODEL_BLOCKED", response["code"])

    def test_eo_ce_discretionary_exhaustion_preserves_safety_reserve_and_recovery(self) -> None:
        governor = EnterpriseCostGovernor()
        governor.create_policy_version({"dailyLimit": 0.01, "reason": "unit test constrained budget"})
        tactical = {
            "reservation_request_id": "ECG-REQ-DISC",
            "mission_plan_id": "EMP-PLAN-DISC",
            "mission_plan_version": 1,
            "mission_id": "",
            "workflow_id": "",
            "mission_type": "opportunity_scan",
            "priority_class": "tactical_evaluation",
            "budget_category": "opportunity_discovery",
            "requesting_office_id": "Seeker",
            "requested_by": "EnterpriseMissionPlanner",
            "estimated_minimum_cost": 10,
            "estimated_expected_cost": 10,
            "estimated_maximum_cost": 10,
            "requested_reservation_amount": 10,
            "requested_api_calls": 1,
            "requested_paid_data_calls": 0,
            "requested_input_tokens": 100,
            "requested_output_tokens": 100,
            "requested_models": ("gpt-4.1-mini",),
            "requested_providers": ("openai",),
            "requested_data_sources": (),
            "estimated_runtime_seconds": 60,
            "deadline_at": "",
            "safety_critical": False,
            "open_position_related": False,
            "active_order_related": False,
            "estimate_basis": {},
            "estimate_confidence": 0.8,
            "submitted_at": "",
        }
        rejected = governor.request_reservation(tactical)
        self.assertIn(rejected.state, {ReservationState.REJECTED, ReservationState.DEFERRED})

        safety = dict(tactical, reservation_request_id="ECG-REQ-SAFE", mission_plan_id="EMP-PLAN-SAFE", mission_type="position_safety_review", priority_class="position_safety", budget_category="position_safety", requesting_office_id="Risk", requested_reservation_amount=0.01, estimated_expected_cost=0.01, estimated_maximum_cost=0.01, safety_critical=True, open_position_related=True)
        approved = governor.request_reservation(safety)
        self.assertIn(approved.state, {ReservationState.APPROVED, ReservationState.REDUCED})
        self.assertIn(approved.decision.value, {"approve", "safety_reserve_only"})

    def test_eo_ce_restart_recovery_policy_version_and_ui_routes_are_wired(self) -> None:
        runtime = create_runtime()
        state = runtime.cost_governor_policy({"dailyLimit": 10, "reason": "unit test policy"})
        self.assertGreaterEqual(len(state["enterpriseCostGovernor"]["policyVersions"]), 2)
        snapshot = state["enterpriseCostGovernor"]
        recovered = EnterpriseCostGovernor()
        recovered.recover_from_snapshot(snapshot)
        self.assertEqual(len(snapshot["budgetAccounts"]), len(recovered.snapshot()["budgetAccounts"]))

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("Enterprise Cost Governance Bridge", html)
        self.assertIn('id="ecg-reserve"', html)
        self.assertIn('("ecg-reserve").addEventListener', js)
        self.assertIn("renderEnterpriseCostGovernor", js)
        self.assertIn("/api/cost-governor/reserve", js)
        self.assertIn("/api/cost-governor/reserve", server)
        self.assertIn("/api/cost-governor/release", server)
        self.assertIn("/api/cost-governor/settle", server)
        self.assertIn("/api/cost-governor/policy", server)

    def test_eo_cf_freshness_engine_defaults_bridge_and_law_boundaries(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        engine = state["informationFreshnessEngine"]

        self.assertEqual("Information Freshness Engine", engine["engineName"])
        self.assertEqual("EO-CF", engine["engineeringOrder"])
        self.assertGreaterEqual(engine["headerIndicators"]["registeredInformationRecords"], 3)
        self.assertTrue(engine["freshnessPolicies"])
        self.assertFalse(engine["lawCF"]["retrievalAuthority"])
        self.assertFalse(engine["lawCF"]["officeWakeAuthority"])
        self.assertFalse(engine["lawCF"]["missionCreationAuthority"])
        self.assertFalse(engine["lawCF"]["expenditureAuthorizationAuthority"])
        self.assertEqual(0, engine["lawCF"]["routineAiInvocations"])

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("Information Freshness Bridge", html)
        self.assertIn('id="ifr-evaluate"', html)
        self.assertIn("renderInformationFreshnessEngine", js)
        self.assertIn("/api/information-freshness/evaluate", js)
        self.assertIn("/api/information-freshness/register", server)
        self.assertIn("/api/information-freshness/invalidate", server)

    def test_eo_cf_contextual_market_freshness_same_quote_differs_by_use(self) -> None:
        engine = InformationFreshnessEngine()
        engine.register_record(
            {
                "information_record_id": "IFR-QUOTE-SPY",
                "domain": "market",
                "information_type": "last_trade",
                "subject_type": "ticker",
                "subject_id": "SPY",
                "ticker": "SPY",
                "source_system": "Primary Market Data",
                "source_record_id": "QUOTE-SPY-001",
                "source_authority_class": "market_data_primary",
                "observed_at": "2026-07-10T13:00:00Z",
                "validated_at": "2026-07-10T13:00:00Z",
                "content_hash": "QUOTEHASH",
                "confidence": 0.995,
                "validation_state": "VALID",
                "field_manifest": ("last", "bid", "ask"),
                "section_manifest": ("quote",),
            }
        )

        tactical = engine.evaluate_record("IFR-QUOTE-SPY", {"decisionUseClass": "tactical_analysis", "marketState": "open", "evaluationRequestedAt": "2026-07-10T13:00:30Z"})
        live = engine.evaluate_record("IFR-QUOTE-SPY", {"decisionUseClass": "live_order_action", "marketState": "open", "activeOrder": True, "safetyCritical": True, "evaluationRequestedAt": "2026-07-10T13:00:30Z"})

        self.assertEqual(FreshnessStatus.FRESH, tactical.status)
        self.assertEqual(FreshnessAction.REUSE_EXACT, tactical.recommended_action)
        self.assertEqual(FreshnessStatus.STALE, live.status)
        self.assertEqual(FreshnessAction.ACQUIRE_NEW_SOURCE, live.recommended_action)
        self.assertFalse(live.usable_for_requested_scope)

    def test_eo_cf_partial_invalidation_dependency_and_supersession_are_preserved(self) -> None:
        engine = InformationFreshnessEngine()
        engine.register_record(
            {
                "information_record_id": "IFR-GUIDANCE-OLD",
                "domain": "fundamental",
                "information_type": "earnings_guidance",
                "subject_type": "ticker",
                "subject_id": "AAPL",
                "ticker": "AAPL",
                "source_system": "Company IR",
                "source_record_id": "GUIDE-Q1",
                "source_authority_class": "company_primary",
                "observed_at": "2026-07-10T12:00:00Z",
                "validated_at": "2026-07-10T12:00:00Z",
                "content_hash": "GUIDE1",
                "confidence": 0.95,
                "validation_state": "VALID",
                "field_manifest": ("revenue", "eps"),
                "section_manifest": ("financial_performance", "valuation"),
            }
        )
        engine.register_record(
            {
                "information_record_id": "IFR-ANALYST-AAPL",
                "domain": "analytical_product",
                "information_type": "analyst_report",
                "subject_type": "ticker",
                "subject_id": "AAPL",
                "ticker": "AAPL",
                "source_system": "Analyst Office",
                "source_record_id": "AAPL-REPORT",
                "source_authority_class": "validated_internal",
                "observed_at": "2026-07-10T12:05:00Z",
                "validated_at": "2026-07-10T12:05:00Z",
                "content_hash": "REPORT1",
                "confidence": 0.91,
                "validation_state": "VALID",
                "field_manifest": ("company", "valuation", "risk", "thesis"),
                "section_manifest": ("company", "valuation", "risk", "trade_thesis"),
            }
        )
        engine.add_dependency({"dependentRecordId": "IFR-ANALYST-AAPL", "dependencyRecordId": "IFR-GUIDANCE-OLD", "dependencyType": "earnings_guidance", "affectedFields": ("valuation", "risk"), "affectedSections": ("valuation", "risk"), "invalidationBehavior": "partial"})
        engine.invalidate_record("IFR-GUIDANCE-OLD", InvalidationReason.EVENT_TRIGGERED, affected_sections=("valuation",), explanation="New earnings release.", source_event_id="EDE-EARNINGS")

        analyst = engine.evaluate_record("IFR-ANALYST-AAPL", {"decisionUseClass": "strategic_analysis", "evaluationRequestedAt": "2026-07-10T12:06:00Z"})
        self.assertEqual(FreshnessStatus.PARTIALLY_STALE, analyst.status)
        self.assertIn("valuation", analyst.stale_sections)
        self.assertIn("company", analyst.fresh_sections)

        engine.register_record(
            {
                "information_record_id": "IFR-GUIDANCE-NEW",
                "domain": "fundamental",
                "information_type": "earnings_guidance",
                "subject_type": "ticker",
                "subject_id": "AAPL",
                "ticker": "AAPL",
                "source_system": "Company IR",
                "source_record_id": "GUIDE-Q2",
                "source_authority_class": "company_primary",
                "observed_at": "2026-07-10T12:10:00Z",
                "validated_at": "2026-07-10T12:10:00Z",
                "content_hash": "GUIDE2",
                "confidence": 0.96,
                "validation_state": "VALID",
                "supersedesRecordId": "IFR-GUIDANCE-OLD",
            }
        )
        old = engine.evaluate_record("IFR-GUIDANCE-OLD", {"decisionUseClass": "tactical_analysis"})
        self.assertEqual(FreshnessStatus.SUPERSEDED, old.status)
        self.assertEqual("IFR-GUIDANCE-NEW", old.superseding_record_id)

    def test_eo_cf_contradiction_blocks_broker_reconciliation_and_recovery_preserves_state(self) -> None:
        engine = InformationFreshnessEngine()
        for record_id, source, authority, quantity in (
            ("IFR-BROKER-POS", "Broker", "broker_confirmed", "100"),
            ("IFR-LEDGER-POS", "Performance Truth Engine", "enterprise_truth", "90"),
        ):
            engine.register_record(
                {
                    "information_record_id": record_id,
                    "domain": "position",
                    "information_type": "position_quantity",
                    "subject_type": "position",
                    "subject_id": "POS-AAPL",
                    "position_id": "POS-AAPL",
                    "source_system": source,
                    "source_record_id": f"{source}-{quantity}",
                    "source_authority_class": authority,
                    "observed_at": "2026-07-10T12:00:00Z",
                    "validated_at": "2026-07-10T12:00:00Z",
                    "content_hash": f"HASH-{quantity}",
                    "confidence": 0.99,
                    "validation_state": "VALID",
                    "field_manifest": ("quantity",),
                    "section_manifest": ("position_state",),
                }
            )
        engine.register_contradiction({"recordAId": "IFR-BROKER-POS", "recordBId": "IFR-LEDGER-POS", "affectedFields": ("quantity",), "affectedSections": ("position_state",), "preferredRecordId": "IFR-BROKER-POS", "preferenceReason": "Broker confirmed has higher authority."})

        decision = engine.evaluate_record("IFR-BROKER-POS", {"decisionUseClass": "broker_reconciliation", "safetyCritical": True})
        self.assertEqual(FreshnessStatus.CONTRADICTED, decision.status)
        self.assertEqual(FreshnessAction.RESOLVE_CONTRADICTION, decision.recommended_action)
        self.assertFalse(decision.usable_for_requested_scope)

        recovered = InformationFreshnessEngine()
        recovered.recover_from_snapshot(engine.snapshot())
        self.assertEqual(engine.snapshot()["headerIndicators"]["contradictedRecords"], recovered.snapshot()["headerIndicators"]["contradictedRecords"])

    def test_eo_cf_runtime_integrates_with_odo_mission_planner_and_cost_justification(self) -> None:
        runtime = create_runtime()
        runtime.information_freshness_register(
            {
                "information_record_id": "IFR-CACHED-COMPANY",
                "domain": "fundamental",
                "information_type": "business_description",
                "subject_type": "ticker",
                "subject_id": "MSFT",
                "ticker": "MSFT",
                "source_system": "Company Filing",
                "source_record_id": "MSFT-10K-BUSINESS",
                "source_authority_class": "company_primary",
                "observed_at": "2026-06-10T12:00:00Z",
                "validated_at": "2026-06-10T12:00:00Z",
                "content_hash": "MSFT-BUSINESS",
                "confidence": 0.96,
                "validation_state": "VALID",
                "field_manifest": ("business_description",),
                "section_manifest": ("company",),
            }
        )

        planned = runtime.mission_planner_commander_request({"directiveId": "CMD-FRESH", "objective": "Refresh MSFT business description", "missionType": "information_refresh", "subjectId": "MSFT", "informationRecordIds": ("IFR-CACHED-COMPANY",), "decisionUseClass": "strategic_analysis"})
        self.assertEqual(1, planned["enterpriseMissionPlanner"]["metrics"]["noActionDecisions"])
        self.assertEqual("USE_CACHED_OR_LOCAL_RESULT", planned["enterpriseMissionPlanner"]["allMissionPlans"][0]["necessity_decision"])

        duty = runtime.submit_duty_officer_request({"sourceOfficeId": "Commander", "targetOfficeId": "Analyst", "requestType": "analysis", "taskDescription": "Review cached company description", "informationRecordIds": ("IFR-CACHED-COMPANY",)})
        self.assertEqual("fresh", duty["latestDutyOfficerDecision"]["relevant_freshness_state"]["overallStatus"])

        justification = runtime.information_freshness_engine.eo_ce_refresh_justification("IFR-CACHED-COMPANY", {"decisionUseClass": "strategic_analysis", "estimatedCostUsd": 0.01})
        self.assertFalse(justification["paidRetrievalJustified"])

    def test_eo_cg_memory_cache_admission_retrieval_and_law_boundaries(self) -> None:
        from argos.foundation.contracts import utc_timestamp

        freshness = InformationFreshnessEngine()
        cache = EnterpriseMemoryCache(freshness)
        admission = cache.admit_product(
            {
                "cacheRecordId": "EMC-AAPL-REPORT",
                "productReference": "analyst://AAPL/report",
                "productType": "office_report",
                "productSubtype": "analyst_report",
                "environment": "paper",
                "producingOfficeId": "Analyst",
                "producingServiceId": "AnalystOffice",
                "subjectType": "ticker",
                "subjectId": "AAPL",
                "ticker": "AAPL",
                "title": "AAPL Analyst Report",
                "summary": "Validated analyst report for AAPL.",
                "payloadReference": "analyst://AAPL/report",
                "payloadFormat": "json_reference",
                "payloadSizeBytes": 512,
                "schemaName": "AnalystReport",
                "schemaVersion": "1.0",
                "confidence": 0.93,
                "validationState": "VALID",
                "sourceAuthorityClass": "validated_internal",
                "fieldManifest": ("summary", "valuation", "risk"),
                "sectionManifest": ("overview", "valuation", "risk"),
                "decisionUseClasses": ("strategic_analysis",),
                "contentHash": "AAPL-REPORT-HASH",
                "createdAt": utc_timestamp(),
            }
        )
        self.assertTrue(admission["decision"]["admitted"])

        result = cache.query({"subjectId": "AAPL", "subjectType": "ticker", "requestedProductTypes": ("office_report",), "requestedFields": ("summary", "risk"), "requestedSections": ("overview", "risk"), "decisionUseClass": "strategic_analysis", "environment": "paper"})
        self.assertEqual(("EMC-AAPL-REPORT",), result.exact_reuse_record_ids)
        self.assertEqual(CacheReuseDecision.REUSE_EXACT, result.reuse_evaluations[0].decision)
        snapshot = cache.snapshot()
        self.assertEqual("Enterprise Memory Cache", snapshot["cacheName"])
        self.assertFalse(snapshot["lawCG"]["existenceEqualsReusability"])
        self.assertEqual("EO-CF", snapshot["lawCG"]["freshnessAuthority"])
        self.assertFalse(snapshot["lawCG"]["missionCreationAuthority"])
        self.assertEqual(0, snapshot["lawCG"]["routineAiInvocations"])

    def test_eo_cg_rejects_unfresh_invalidated_and_cross_environment_reuse(self) -> None:
        freshness = InformationFreshnessEngine()
        cache = EnterpriseMemoryCache(freshness)
        cache.admit_product(
            {
                "cacheRecordId": "EMC-SIM-REPORT",
                "productReference": "sim://report",
                "productType": "office_report",
                "productSubtype": "analyst_report",
                "environment": "simulation",
                "producingOfficeId": "Analyst",
                "subjectType": "ticker",
                "subjectId": "MSFT",
                "schemaName": "AnalystReport",
                "schemaVersion": "1.0",
                "payloadReference": "sim://report",
                "payloadSizeBytes": 300,
                "confidence": 0.91,
                "validationState": "VALID",
                "sourceAuthorityClass": "validated_internal",
                "fieldManifest": ("summary",),
                "sectionManifest": ("overview",),
                "contentHash": "SIM-HASH",
                "createdAt": "2026-07-10T12:00:00Z",
            }
        )
        production = cache.query({"subjectId": "MSFT", "requestedProductTypes": ("office_report",), "decisionUseClass": "strategic_analysis", "environment": "live", "requestedFields": ("summary",), "requestedSections": ("overview",)})
        self.assertEqual((), production.selected_cache_record_ids)
        self.assertEqual(CacheReuseDecision.REJECT_REUSE, production.reuse_evaluations[0].decision)

        cache.invalidate("EMC-SIM-REPORT", reason="Unit test invalidation.", full=True)
        historical = cache.query({"subjectId": "MSFT", "requestedProductTypes": ("office_report",), "decisionUseClass": "historical_review", "environment": "simulation", "allowHistorical": True})
        self.assertNotIn("EMC-SIM-REPORT", historical.exact_reuse_record_ids)
        self.assertTrue(historical.rejected_record_ids)

    def test_eo_cg_duplicate_supersession_and_recovery_preserve_lineage(self) -> None:
        freshness = InformationFreshnessEngine()
        cache = EnterpriseMemoryCache(freshness)
        base = {
            "cacheRecordId": "EMC-RISK-V1",
            "productReference": "risk://POS-1/v1",
            "productType": "position_product",
            "productSubtype": "risk_assessment",
            "environment": "paper",
            "producingOfficeId": "Risk",
            "subjectType": "position",
            "subjectId": "POS-1",
            "positionId": "POS-1",
            "schemaName": "RiskAssessment",
            "schemaVersion": "1.0",
            "payloadReference": "risk://POS-1/v1",
            "payloadSizeBytes": 400,
            "confidence": 0.95,
            "validationState": "VALID",
            "sourceAuthorityClass": "validated_internal",
            "fieldManifest": ("risk", "stop"),
            "sectionManifest": ("risk",),
            "contentHash": "RISK-HASH-V1",
            "createdAt": "2026-07-10T12:00:00Z",
        }
        cache.admit_product(base)
        duplicate = cache.admit_product(dict(base, cacheRecordId="EMC-RISK-DUP"))
        self.assertFalse(duplicate["decision"]["admitted"])
        self.assertEqual("EMC-RISK-V1", duplicate["decision"]["duplicate_record_id"])

        superseded = cache.supersede("EMC-RISK-V1", dict(base, cacheRecordId="EMC-RISK-V2", productReference="risk://POS-1/v2", contentHash="RISK-HASH-V2"))
        self.assertTrue(superseded["decision"]["admitted"])
        snapshot = cache.snapshot()
        prior = next(item for item in snapshot["memoryInventory"] if item["cache_record_id"] == "EMC-RISK-V1")
        self.assertEqual("superseded", prior["status"])

        recovered = EnterpriseMemoryCache(freshness)
        recovered.recover_from_snapshot(snapshot)
        self.assertEqual(len(snapshot["memoryInventory"]), len(recovered.snapshot()["memoryInventory"]))

    def test_eo_cg_governance_exceptions_retention_and_repository_manifest(self) -> None:
        freshness = InformationFreshnessEngine()
        cache = EnterpriseMemoryCache(freshness)
        admitted = cache.admit_product(
            {
                "cacheRecordId": "EMC-GOV-REPORT",
                "productReference": "governance://report",
                "productType": "office_report",
                "productSubtype": "analyst_report",
                "environment": "paper",
                "producingOfficeId": "Analyst",
                "producingServiceId": "AnalystOffice",
                "subjectType": "ticker",
                "subjectId": "NVDA",
                "schemaName": "AnalystReport",
                "schemaVersion": "1.0",
                "payloadReference": "governance://report",
                "payloadSizeBytes": 250,
                "confidence": 0.92,
                "validationState": "VALID",
                "sourceAuthorityClass": "validated_internal",
                "fieldManifest": ("summary",),
                "sectionManifest": ("overview",),
                "contentHash": "GOV-HASH",
            }
        )
        self.assertTrue(admitted["decision"]["admitted"])
        self.assertEqual("EMC-GOV-REPORT", cache.get_cache_record("EMC-GOV-REPORT")["cache_record_id"])
        self.assertEqual(1, len(cache.list_records_by_subject("ticker", "NVDA")))
        self.assertIn("get_cache_record", cache.repository_method_manifest())

        contradiction = cache.register_contradiction(
            "EMC-GOV-REPORT",
            {"contradictingRecordId": "EMC-GOV-COUNTER", "affectedFields": ("summary",), "reason": "New authoritative evidence conflicts."},
        )
        self.assertEqual("contradicted", contradiction.new_status.value)
        rejected = cache.query({"subjectId": "NVDA", "requestedProductTypes": ("office_report",), "decisionUseClass": "strategic_analysis", "environment": "paper", "requestedFields": ("summary",)})
        self.assertEqual((), rejected.selected_cache_record_ids)
        self.assertEqual(CacheReuseDecision.REJECT_REUSE, rejected.reuse_evaluations[0].decision)

        cache.quarantine_record("EMC-GOV-REPORT", "Cache poisoning suspicion.")
        archive = cache.archive_record("EMC-GOV-REPORT", "Retention policy archive.")
        snapshot = cache.snapshot()
        self.assertEqual("EMC-ARC-000001", archive["archiveId"])
        self.assertTrue(snapshot["contradictionRecords"])
        self.assertTrue(snapshot["archivalRecords"])
        self.assertIn("repositoryMethods", snapshot)
        self.assertFalse(snapshot["retentionPolicy"]["automatic_delete_enabled"])
        self.assertEqual("runtime_snapshot", snapshot["persistence"]["mode"])

    def test_eo_cg_quarantines_unverified_authority_and_incomplete_validated_products(self) -> None:
        freshness = InformationFreshnessEngine()
        cache = EnterpriseMemoryCache(freshness)
        poisoned = cache.admit_product(
            {
                "cacheRecordId": "EMC-POISON",
                "productReference": "unsafe://broker",
                "productType": "evidence_package",
                "productSubtype": "broker_confirmation",
                "environment": "paper",
                "producingOfficeId": "Analyst",
                "subjectType": "order",
                "subjectId": "ORD-1",
                "schemaName": "BrokerConfirmation",
                "schemaVersion": "1.0",
                "payloadReference": "unsafe://broker",
                "payloadSizeBytes": 123,
                "confidence": 0.99,
                "validationState": "VALID",
                "sourceAuthorityClass": "broker_confirmed",
                "contentHash": "POISON-HASH",
            }
        )
        self.assertFalse(poisoned["decision"]["admitted"])
        self.assertTrue(poisoned["decision"]["quarantine_required"])
        self.assertIn("authority_claim_unverified", poisoned["decision"]["reason_codes"])
        self.assertEqual(1, len(cache.list_quarantined_records()))
        self.assertEqual("quarantined", poisoned["record"]["status"])

        candidate = cache.admit_product(
            {
                "cacheRecordId": "EMC-CANDIDATE",
                "productReference": "candidate://report",
                "productType": "office_report",
                "productSubtype": "analyst_report",
                "environment": "paper",
                "producingOfficeId": "Analyst",
                "subjectType": "ticker",
                "subjectId": "TSLA",
                "payloadReference": "candidate://report",
                "confidence": 0.95,
                "validationState": "VALID",
                "contentHash": "CANDIDATE-HASH",
            }
        )
        self.assertTrue(candidate["decision"]["admitted"])
        self.assertEqual("candidate", candidate["decision"]["assigned_tier"])
        self.assertEqual("pending_admission", candidate["record"]["status"])

    def test_eo_cg_runtime_bridge_routes_and_ui_are_wired(self) -> None:
        runtime = create_runtime()
        state = runtime.state()
        cache = state["enterpriseMemoryCache"]
        self.assertGreaterEqual(cache["headerIndicators"]["cacheRecords"], 2)

        state = runtime.enterprise_memory_admit(
            {
                "cacheRecordId": "EMC-CACHED-REPORT",
                "productReference": "report://cached",
                "productType": "office_report",
                "productSubtype": "analyst_report",
                "environment": "development",
                "producingOfficeId": "Analyst",
                "subjectType": "ticker",
                "subjectId": "SPY",
                "schemaName": "AnalystReport",
                "schemaVersion": "1.0",
                "payloadReference": "report://cached",
                "payloadSizeBytes": 250,
                "confidence": 0.9,
                "validationState": "VALID",
                "sourceAuthorityClass": "validated_internal",
                "fieldManifest": ("summary",),
                "sectionManifest": ("overview",),
                "contentHash": "SPY-CACHED",
            }
        )
        self.assertTrue(state["latestMemoryAdmission"]["decision"]["admitted"])
        state = runtime.enterprise_memory_query({"subjectId": "SPY", "requestedProductTypes": ("office_report",), "decisionUseClass": "strategic_analysis", "environment": "development"})
        self.assertIn("EMC-CACHED-REPORT", state["latestMemoryRetrieval"]["selected_cache_record_ids"])

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("Enterprise Memory Bridge", html)
        self.assertIn('id="emc-query"', html)
        self.assertIn("renderEnterpriseMemoryCache", js)
        self.assertIn("/api/enterprise-memory/query", js)
        self.assertIn("/api/enterprise-memory/admit", server)
        self.assertIn("/api/enterprise-memory/contradiction", server)
        self.assertIn("/api/enterprise-memory/quarantine", server)
        self.assertIn("/api/enterprise-memory/archive", server)
        self.assertIn("emc-contradictions", html)
        self.assertIn("emc-retention", html)

    def _eo_ch_engine_with_baseline(self) -> tuple[WorkflowDeltaEngine, dict]:
        freshness = InformationFreshnessEngine()
        cache = EnterpriseMemoryCache(freshness)
        cache.admit_product(
            {
                "cacheRecordId": "EMC-DELTA-ANALYST",
                "productReference": "analyst://DELTA/v1",
                "productType": "office_report",
                "productSubtype": "analyst_report",
                "environment": "paper",
                "producingOfficeId": "Analyst",
                "subjectType": "ticker",
                "subjectId": "DELTA",
                "schemaName": "AnalystReport",
                "schemaVersion": "1.0",
                "payloadReference": "analyst://DELTA/v1",
                "payloadSizeBytes": 256,
                "confidence": 0.93,
                "validationState": "VALID",
                "sourceAuthorityClass": "validated_internal",
                "fieldManifest": ("inputs.market.price", "outputs.analyst.valuation", "outputs.risk.score", "assumptions.thesis.core_assumption"),
                "sectionManifest": ("inputs", "outputs", "assumptions", "risk", "valuation"),
                "decisionUseClasses": ("strategic_analysis",),
                "contentHash": "DELTA-ANALYST-HASH",
                "createdAt": "2026-07-10T12:00:00Z",
            }
        )
        engine = WorkflowDeltaEngine(freshness, cache)
        baseline_payload = {
            "baselineId": "CH-BL-DELTA",
            "missionId": "MISSION-DELTA",
            "missionPlanId": "EMP-PLAN-DELTA",
            "workflowId": "WF-DELTA",
            "subjectType": "ticker",
            "subjectId": "DELTA",
            "ticker": "DELTA",
            "environment": "paper",
            "cacheRecordIds": ("EMC-DELTA-ANALYST",),
            "informationRecordIds": ("IFR-CACHE-EMC-DELTA-ANALYST",),
            "evidenceRecordIds": ("EVD-BASE",),
            "productRecordIds": ("PROD-ANALYST-V1",),
            "inputManifest": {"market": {"price": 100.0, "spread": 0.02}, "company": {"guidance": "stable"}},
            "outputManifest": {"analyst": {"valuation": 100.0, "thesis": "hold"}, "risk": {"score": 0.4}},
            "assumptionManifest": {"thesis": {"core_assumption": "business unchanged"}},
            "policyManifest": {"risk": {"version": "1.0", "max_exposure": 0.1}},
            "dependencyManifest": {"valuation": ("inputs.market.price", "inputs.company.guidance"), "risk": ("policy.risk.version", "inputs.market.price")},
            "workflowManifest": {"nodes": ("Librarian", "Analyst", "Risk")},
            "schemaVersions": {"analyst_report": "1.0"},
            "validationState": "VALID",
        }
        engine.create_baseline(baseline_payload)
        return engine, baseline_payload

    def test_eo_ch_baseline_delta_precision_and_reuse(self) -> None:
        engine, _baseline = self._eo_ch_engine_with_baseline()
        result = engine.analyze(
            {
                "deltaRequestId": "CH-REQ-PRICE",
                "requestType": "manual_comparison",
                "baselineId": "CH-BL-DELTA",
                "subjectType": "ticker",
                "subjectId": "DELTA",
                "missionType": "earnings_reassessment",
                "decisionUseClass": "strategic_analysis",
                "environment": "paper",
                "currentInformationRecordIds": ("IFR-CACHE-EMC-DELTA-ANALYST",),
                "currentCacheRecordIds": ("EMC-DELTA-ANALYST",),
                "currentEvidenceRecordIds": ("EVD-BASE", "EVD-GUIDANCE"),
                "requestedProducts": ("office_report",),
                "requestedFields": ("inputs.market.price", "outputs.analyst.valuation", "outputs.risk.score"),
                "requestedSections": ("valuation", "risk"),
                "currentState": {
                    "inputManifest": {"market": {"price": 102.5, "spread": 0.02}, "company": {"guidance": "raised"}},
                    "outputManifest": {"analyst": {"valuation": 104.0, "thesis": "hold"}, "risk": {"score": 0.48}},
                    "assumptionManifest": {"thesis": {"core_assumption": "business unchanged"}},
                    "policyManifest": {"risk": {"version": "1.0", "max_exposure": 0.1}},
                    "dependencyManifest": {"valuation": ("inputs.market.price", "inputs.company.guidance"), "risk": ("policy.risk.version", "inputs.market.price")},
                    "workflowManifest": {"nodes": ("Librarian", "Analyst", "Risk")},
                },
            }
        )
        package = result["package"]
        self.assertFalse(package["full_reassessment_required"])
        self.assertIn("inputs.market.price", package["minimum_revision_scope"])
        self.assertIn("EMC-DELTA-ANALYST", package["reusable_cache_record_ids"])
        self.assertTrue(any(item["change_type"] == ChangeType.UNCHANGED.value for item in package["field_changes"]))
        self.assertTrue(any(item["revision_requirement"] in {RevisionRequirement.PARTIAL_REVISION.value, RevisionRequirement.REUSE_WITH_VALIDATION.value} for item in package["product_impacts"]))
        self.assertEqual("EO-CD Enterprise Mission Planner", package["mission_planner_feed"]["targetEngine"])

    def test_eo_ch_office_impact_cost_reduction_and_law_boundaries(self) -> None:
        engine, _baseline = self._eo_ch_engine_with_baseline()
        result = engine.analyze(
            {
                "deltaRequestId": "CH-REQ-POSITION",
                "requestType": "position_review",
                "baselineId": "CH-BL-DELTA",
                "subjectType": "ticker",
                "subjectId": "DELTA",
                "positionId": "POS-DELTA",
                "missionType": "position_review",
                "decisionUseClass": "tactical_analysis",
                "environment": "paper",
                "currentInformationRecordIds": ("IFR-CACHE-EMC-DELTA-ANALYST",),
                "currentCacheRecordIds": ("EMC-DELTA-ANALYST",),
                "currentEvidenceRecordIds": ("EVD-BASE",),
                "requestedProducts": ("office_report",),
                "currentState": {
                    "inputManifest": {"market": {"price": 100.0, "spread": 0.02}, "position": {"quantity": 125}},
                    "outputManifest": {"analyst": {"valuation": 100.0, "thesis": "hold"}, "risk": {"score": 0.55}},
                    "assumptionManifest": {"thesis": {"core_assumption": "business unchanged"}},
                    "policyManifest": {"risk": {"version": "1.0", "max_exposure": 0.1}},
                    "dependencyManifest": {"risk": ("inputs.position.quantity", "policy.risk.version")},
                    "workflowManifest": {"nodes": ("Risk", "Performance Truth")},
                },
            }
        )
        package = result["package"]
        offices = {item["office_id"]: item for item in package["office_impacts"]}
        self.assertIn(offices["Risk"]["impact_decision"], {OfficeImpactDecision.PARTIAL_REACTIVATION.value, OfficeImpactDecision.VALIDATION_ONLY.value})
        self.assertEqual(OfficeImpactDecision.NOT_REQUIRED.value, offices["Seeker"]["impact_decision"])
        self.assertGreaterEqual(package["cost_reduction_evidence"]["officesAvoided"], 1)
        self.assertFalse(package["law_ch"]["wakesOffices"])
        self.assertFalse(package["law_ch"]["createsMissions"])
        self.assertFalse(package["law_ch"]["authorizesExpenditure"])
        self.assertEqual(0, package["law_ch"]["paidApiCalls"])
        self.assertEqual(0, package["law_ch"]["aiInvocations"])

    def test_eo_ch_blocks_untrusted_baseline_and_environment_mismatch(self) -> None:
        freshness = InformationFreshnessEngine()
        cache = EnterpriseMemoryCache(freshness)
        engine = WorkflowDeltaEngine(freshness, cache)
        engine.create_baseline({"baselineId": "CH-BL-BAD", "subjectId": "BAD", "environment": "paper", "validationState": "UNVERIFIED"})
        denied = engine.analyze({"deltaRequestId": "CH-REQ-BAD", "baselineId": "CH-BL-BAD", "subjectId": "BAD", "environment": "paper"})
        self.assertEqual({}, denied["package"])
        self.assertEqual("baseline_untrusted", engine.snapshot()["deadLetters"][-1]["reasonCode"])

        engine.create_baseline({"baselineId": "CH-BL-LIVE", "subjectId": "LIVE", "environment": "live", "validationState": "VALID"})
        mismatch = engine.analyze({"deltaRequestId": "CH-REQ-MISMATCH", "baselineId": "CH-BL-LIVE", "subjectId": "LIVE", "environment": "paper"})
        self.assertEqual({}, mismatch["package"])
        self.assertEqual("environment_mismatch", engine.snapshot()["deadLetters"][-1]["reasonCode"])

    def test_eo_ch_blocks_corrupt_baseline_hash_and_subject_mismatch(self) -> None:
        freshness = InformationFreshnessEngine()
        cache = EnterpriseMemoryCache(freshness)
        engine = WorkflowDeltaEngine(freshness, cache)
        engine.create_baseline({"baselineId": "CH-BL-CORRUPT", "subjectId": "CORRUPT", "environment": "paper", "validationState": "VALID", "contentHash": "WRONG"})
        corrupt = engine.analyze({"deltaRequestId": "CH-REQ-CORRUPT", "baselineId": "CH-BL-CORRUPT", "subjectId": "CORRUPT", "environment": "paper"})
        self.assertEqual({}, corrupt["package"])
        self.assertEqual("baseline_hash_failure", engine.snapshot()["deadLetters"][-1]["reasonCode"])
        self.assertTrue(engine.snapshot()["alerts"])

        engine.create_baseline({"baselineId": "CH-BL-SUBJECT", "subjectId": "AAPL", "environment": "paper", "validationState": "VALID"})
        mismatch = engine.analyze({"deltaRequestId": "CH-REQ-SUBJECT", "baselineId": "CH-BL-SUBJECT", "subjectId": "MSFT", "environment": "paper"})
        self.assertEqual({}, mismatch["package"])
        self.assertEqual("subject_mismatch", engine.snapshot()["deadLetters"][-1]["reasonCode"])

    def test_eo_ch_restart_recovery_is_idempotent(self) -> None:
        engine, _baseline = self._eo_ch_engine_with_baseline()
        engine.analyze({"deltaRequestId": "CH-REQ-RESTART", "baselineId": "CH-BL-DELTA", "subjectId": "DELTA", "environment": "paper", "currentState": {"inputManifest": {"market": {"price": 101.0}}}})
        snapshot = engine.snapshot()
        recovered = WorkflowDeltaEngine(InformationFreshnessEngine(), EnterpriseMemoryCache(InformationFreshnessEngine()))
        recovered.recover_from_snapshot(snapshot)
        self.assertEqual(snapshot["summary"]["packages"], recovered.snapshot()["summary"]["packages"])
        duplicate = recovered.analyze({"deltaRequestId": "CH-REQ-RESTART", "baselineId": "CH-BL-DELTA", "subjectId": "DELTA", "environment": "paper"})
        self.assertTrue(duplicate["duplicate"])

    def test_eo_ch_export_replay_and_manual_review_are_safe_controls(self) -> None:
        engine, _baseline = self._eo_ch_engine_with_baseline()
        result = engine.analyze({"deltaRequestId": "CH-REQ-CONTROLS", "baselineId": "CH-BL-DELTA", "subjectId": "DELTA", "environment": "paper", "currentState": {"inputManifest": {"market": {"price": 101.0}}}})
        package_id = result["package"]["delta_package_id"]
        exported = engine.export_package(package_id, "markdown")
        self.assertIn("# Workflow Delta Package", exported)
        replay = engine.replay(package_id)
        self.assertTrue(replay["replayMode"])
        self.assertFalse(replay["productionMutation"])
        review = engine.request_manual_review(package_id, "request_validation_review", "Unit test review.")
        self.assertTrue(review["accepted"])
        self.assertFalse(review["authorizesOfficeActivation"])
        self.assertFalse(review["authorizesMission"])

    def test_eo_ch_runtime_bridge_routes_and_ui_are_wired(self) -> None:
        runtime = create_runtime()
        state = runtime.workflow_delta_create_baseline(
            {
                "baselineId": "CH-BL-RUNTIME",
                "subjectType": "ticker",
                "subjectId": "SPY",
                "environment": "development",
                "inputManifest": {"market": {"price": 100}},
                "outputManifest": {"analyst": {"valuation": 100}},
                "validationState": "VALID",
            }
        )
        self.assertEqual("CH-BL-RUNTIME", state["latestDeltaBaseline"]["baseline_id"])
        state = runtime.workflow_delta_analyze(
            {
                "deltaRequestId": "CH-REQ-RUNTIME",
                "baselineId": "CH-BL-RUNTIME",
                "subjectType": "ticker",
                "subjectId": "SPY",
                "environment": "development",
                "requestedProducts": ("office_report",),
                "currentState": {"inputManifest": {"market": {"price": 103}}, "outputManifest": {"analyst": {"valuation": 104}}},
            }
        )
        self.assertIn("workflowDeltaEngine", state)
        self.assertEqual("CH-PKG-000001", state["latestWorkflowDelta"]["package"]["delta_package_id"])
        state = runtime.workflow_delta_export("CH-PKG-000001", "markdown")
        self.assertIn("# Workflow Delta Package", state["latestWorkflowDeltaExport"]["content"])
        state = runtime.workflow_delta_replay("CH-PKG-000001")
        self.assertTrue(state["latestWorkflowDeltaReplay"]["replayMode"])
        state = runtime.workflow_delta_review("CH-PKG-000001", {"action": "request_validation_review", "reason": "Unit test"})
        self.assertTrue(state["latestWorkflowDeltaReview"]["accepted"])

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("Workflow Delta Bridge", html)
        self.assertIn('id="wch-analyze"', html)
        self.assertIn("renderWorkflowDeltaEngine", js)
        self.assertIn("/api/workflow-delta/analyze", js)
        self.assertIn("/api/workflow-delta/state", server)
        self.assertIn("/api/workflow-delta/export", server)
        self.assertIn("/api/workflow-delta/replay", js)
        self.assertIn('id="wch-review"', html)

    def _eo_cj_sources(self) -> dict:
        now = "2026-07-09T15:00:00Z"

        def plan(plan_id: str, mission_type: str, priority_class: str, subject: str, *, cost: float = 0.01, runtime: int = 120, deps: tuple[str, ...] = ()) -> dict:
            return {
                "mission_plan_id": plan_id,
                "plan_version": 1,
                "status": "ready_for_submission",
                "mission_type": mission_type,
                "priority_class": priority_class,
                "created_at": now,
                "objective": {"subject_type": "ticker", "subject_id": subject, "deadline_at": ""},
                "resource_envelope": {"runtime_ceiling_seconds": runtime, "estimated_cost_usd": cost, "api_call_ceiling": 1},
                "office_assignments": ({"office_id": "Risk"}, {"office_id": "Trader"}),
                "dependencies": tuple({"upstream_node_id": dep, "downstream_node_id": plan_id, "required": True} for dep in deps),
                "delta_decision": {},
            }

        return {
            "enterpriseMissionPlanner": {
                "allMissionPlans": (
                    plan("EMP-PLAN-SAFETY", "position_safety_review", "position_safety", "AAPL"),
                    plan("EMP-PLAN-STRATEGIC", "strategic_research", "strategic_intelligence", "BLUE", cost=1.25, runtime=1800),
                    plan("EMP-PLAN-BROKER-DEP", "information_refresh", "tactical_evaluation", "AAPL", deps=("broker_quantity_truth",)),
                ),
                "mergeRecords": (),
            },
            "enterpriseOperationsScheduler": {
                "currentOperatingMode": "Full Paper Trading",
                "missionRecords": (),
            },
            "eventDetectionEngine": {
                "activeEvents": (
                    {
                        "event_id": "EDE-EVT-STOP",
                        "domain": "position",
                        "event_type": "stop_loss_proximity",
                        "severity": "critical",
                        "urgency": "immediate",
                        "materiality": "major",
                        "recommended_mission_type": "position_safety_review",
                        "recommended_offices": ("Risk", "Trader"),
                        "subject_type": "position",
                        "subject_id": "POS-AAPL",
                        "ticker": "AAPL",
                        "position_id": "POS-AAPL",
                        "validated_at": now,
                        "financial_exposure": 5000,
                        "estimated_downside": 400,
                    },
                ),
            },
            "enterpriseCostGovernor": {
                "budgetAllocation": {"available": 25.0},
                "metrics": {"safetyReserveRemaining": 2.0},
            },
            "informationFreshnessEngine": {"staleAndAtRiskInformation": ()},
            "enterpriseMemoryCache": {"latestRetrieval": {}},
            "workflowRuntimeMonitor": {"tokenIntegrity": {"status": "VALID"}},
            "offices": (),
        }

    def test_eo_cj_priority_engine_defaults_doctrine_and_law_boundaries(self) -> None:
        engine = EnterprisePriorityEngine()
        snapshot = engine.evaluate(self._eo_cj_sources())
        self.assertEqual("EO-CJ", snapshot["engineeringOrder"])
        self.assertEqual(EnterprisePriorityClass.EMERGENCY_RECOVERY.value, snapshot["activePolicy"]["class_order"][0])
        self.assertTrue(snapshot["summary"]["rankedCount"] >= 3)
        self.assertFalse(snapshot["lawCJ"]["priorityIsAuthorization"])
        self.assertFalse(snapshot["lawCJ"]["officeWakeAuthority"])
        self.assertFalse(snapshot["lawCJ"]["budgetReserveAuthority"])
        self.assertEqual(0, snapshot["lawCJ"]["routineAiInvocations"])
        self.assertFalse(snapshot["schedulerFeed"]["authorityTransferred"])

    def test_eo_cj_safety_precedence_blocks_discretionary_score_override(self) -> None:
        engine = EnterprisePriorityEngine()
        snapshot = engine.evaluate(self._eo_cj_sources())
        queue = snapshot["rankedMissionQueue"]
        safety_rank = min(item["rank"] for item in queue if item["priorityClass"] == EnterprisePriorityClass.POSITION_SAFETY.value)
        strategic_rank = min(item["rank"] for item in queue if item["priorityClass"] == EnterprisePriorityClass.STRATEGIC_INTELLIGENCE.value)
        self.assertLess(safety_rank, strategic_rank)
        self.assertFalse(snapshot["safetyPrecedence"]["discretionaryAboveSafety"])
        self.assertFalse(snapshot["safetyPrecedence"]["numericScoreCanOverrideSafety"])

    def test_eo_cj_dependency_inheritance_and_resource_reduction_are_visible(self) -> None:
        sources = self._eo_cj_sources()
        sources["enterpriseCostGovernor"]["budgetAllocation"]["available"] = 0.1
        engine = EnterprisePriorityEngine()
        snapshot = engine.evaluate(sources)
        inherited = tuple(item for item in snapshot["priorityDecisions"] if item["mission_plan_id"] == "EMP-PLAN-BROKER-DEP")
        self.assertTrue(inherited)
        self.assertEqual(EnterprisePriorityClass.BROKER_LEDGER_INTEGRITY.value, inherited[0]["effective_priority_class"])
        self.assertTrue(inherited[0]["inheritance_applied"])
        strategic = next(item for item in snapshot["priorityDecisions"] if item["mission_plan_id"] == "EMP-PLAN-STRATEGIC")
        self.assertIn(strategic["disposition"], {"defer", "blocked", "queue_normal"})
        self.assertTrue(any(item["reductionRecommendation"] for item in snapshot["resourceConstraints"]))

    def test_eo_cj_preemption_aging_restart_and_replay_are_deterministic(self) -> None:
        engine = EnterprisePriorityEngine()
        snapshot = engine.evaluate(self._eo_cj_sources())
        self.assertTrue(snapshot["preemptionAssessments"])
        self.assertTrue(snapshot["starvationAndAging"])
        recovered = EnterprisePriorityEngine()
        recovered.recover_from_snapshot(snapshot)
        restored = recovered.snapshot()
        self.assertEqual(snapshot["summary"]["rankedCount"], restored["summary"]["rankedCount"])
        self.assertEqual(snapshot["rankedMissionQueue"][0]["candidateId"], restored["rankedMissionQueue"][0]["candidateId"])
        replay = engine.replay(self._eo_cj_sources())
        self.assertTrue(replay["replayMode"])
        self.assertFalse(replay["productionMutation"])

    def test_eo_cj_runtime_bridge_routes_and_ui_are_wired(self) -> None:
        runtime = create_runtime()
        runtime.mission_planner_commander_request(
            {
                "directiveId": "CMD-PRIORITY",
                "objective": "Review live position safety",
                "missionType": "position_safety_review",
                "subjectId": "POS-AAPL",
                "positionId": "POS-AAPL",
                "severity": "critical",
                "urgency": "immediate",
            }
        )
        state = runtime.enterprise_priority_evaluate()
        self.assertIn("enterprisePriorityEngine", state)
        self.assertGreaterEqual(state["enterprisePriorityEngine"]["summary"]["rankedCount"], 1)
        self.assertFalse(state["enterprisePriorityEngine"]["lawCJ"]["missionCreationAuthority"])
        state = runtime.enterprise_priority_replay()
        self.assertTrue(state["latestEnterprisePriorityReplay"]["replayMode"])

        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")
        self.assertIn("Enterprise Priority Bridge", html)
        self.assertIn('id="epj-evaluate"', html)
        self.assertIn("renderEnterprisePriorityEngine", js)
        self.assertIn("/api/enterprise-priority/evaluate", js)
        self.assertIn("/api/enterprise-priority/state", server)
        self.assertIn("/api/enterprise-priority/replay", server)


if __name__ == "__main__":
    unittest.main()
