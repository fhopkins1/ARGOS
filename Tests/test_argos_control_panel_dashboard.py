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

from argos.control_panel import ApiExecutionRequest, create_runtime  # noqa: E402
from argos.control_panel.cognitive_contract import OFFICE_OUTPUT_SCHEMAS, PromptContractLibrary, build_prompt_contract_envelope  # noqa: E402


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
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
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
            self.assertEqual("Paper Trading Session", workflow["name"])
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
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
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
            state = self._wait_for_state(runtime, lambda item: item["apiRuntimeMonitor"]["metrics"]["apiCallsLogged"] == 1, timeout=2.0)
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
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0.08", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
        try:
            runtime = create_runtime()
            state = runtime.start_paper_self_training()
            monitor = state["workflowRuntimeMonitor"]
            self.assertEqual(1, len(monitor["liveWorkflowExecution"]))
            active = monitor["liveWorkflowExecution"][0]
            workflow_id = active["workflowIdentifier"]

            self.assertEqual("Paper Trading Session", active["workflowName"])
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
                    timeout=2.0,
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
                timeout=2.0,
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
                timeout=5.0,
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
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0.02", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
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
                ),
                timeout=2.0,
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
        )
        try:
            runtime = create_runtime()
            runtime.api_execution_gateway.set_provider_call_for_testing(lambda _request, _prompt: self._valid_analyst_json())
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: item["controlledCognitivePilot"]["status"] == "COMPLETE" and item["workflowOrchestrator"]["metrics"]["activeWorkflowCount"] == 0,
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
            self.assertEqual(3, len(state["performanceTruthEngine"]["tradeLedger"]))
            self.assertGreaterEqual(state["decisionLaboratory"]["metrics"]["decisionReplayCount"], 3)
        finally:
            runtime.halt_paper_self_training()
            self._restore_env(previous)

    def test_live_strategy_performance_console_tracks_performance_and_decision_evolution(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
        try:
            runtime = create_runtime()
            state = runtime.start_paper_self_training()
            workflow_id = state["workflowRuntimeMonitor"]["activeWorkflow"]["workflowIdentifier"] if state["workflowRuntimeMonitor"]["activeWorkflow"] else state["workflowOrchestrator"]["workflows"][-1]["workflow_id"]
            state = self._wait_for_state(
                runtime,
                lambda item: any(
                    workflow["workflowIdentifier"] == workflow_id and workflow["status"] == "Archived"
                    for workflow in item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]
                ),
                timeout=2.0,
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
            self.assertGreaterEqual(len(console["tradeStream"]), 1)
            self.assertEqual(workflow_id, console["tradeStream"][-1]["responsibleWorkflow"])
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
            self.assertEqual(5, console["trace"]["immutableRevisionCount"])
        finally:
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
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
        try:
            runtime = create_runtime()
            state = runtime.start_paper_self_training()
            workflow_id = state["workflowRuntimeMonitor"]["activeWorkflow"]["workflowIdentifier"] if state["workflowRuntimeMonitor"]["activeWorkflow"] else state["workflowOrchestrator"]["workflows"][-1]["workflow_id"]
            state = self._wait_for_state(
                runtime,
                lambda item: any(
                    workflow["workflowIdentifier"] == workflow_id and workflow["status"] == "Archived"
                    for workflow in item["workflowRuntimeMonitor"]["recentCompletedWorkflows"]
                ) and len(item["performanceTruthEngine"]["tradeLedger"]) == 1,
                timeout=2.0,
            )
            runtime.halt_paper_self_training()

            truth = state["performanceTruthEngine"]
            self.assertEqual("Performance Truth Engine", truth["engineName"])
            self.assertEqual("OE-011C", truth["engineeringOrder"])
            self.assertEqual("IMMUTABLE_LEDGER", truth["sourceOfTruth"])
            self.assertEqual(1, len(truth["tradeLedger"]))
            self.assertEqual(1, len(truth["positionLedger"]))
            self.assertEqual(1, len(truth["portfolioLedger"]))
            self.assertEqual(1, len(truth["decisionObjectOutcomes"]))
            self.assertEqual(1, len(truth["workflowAttribution"]))
            self.assertEqual(5, len(truth["officeAttribution"]))
            self.assertEqual(5, len(truth["benchmarkHistory"]))
            trade = truth["tradeLedger"][0]
            self.assertEqual(workflow_id, trade["workflow_id"])
            self.assertEqual("paper", trade["execution_environment"])
            self.assertTrue(trade["hash"])
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
            self.assertEqual(trade["realized_profit_loss"], console["tradeStream"][0]["profitLoss"])
            self.assertEqual(trade["decision_object_id"], console["decisionObjectPanel"]["decisionObjectId"])
            self.assertEqual("LAW_VII_ENFORCED", console["integration"]["workflowExecutionToken"])
            self.assertEqual("PERFORMANCE_TRUTH_ENGINE", console["integration"]["oe011cPerformanceTruthEngine"])
        finally:
            self._restore_env(previous)

    def test_performance_truth_engine_isolates_paper_and_live_records_and_does_not_mutate_on_state_poll(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["performanceTruthEngine"]["tradeLedger"]) == 1,
                timeout=2.0,
            )
            runtime.halt_paper_self_training()
            first_truth = state["performanceTruthEngine"]
            first_trade_count = len(first_truth["tradeLedger"])
            first_hashes = tuple(item["hash"] for item in first_truth["tradeLedger"])

            for _ in range(5):
                state = runtime.performance_truth_state()

            truth = state["performanceTruthEngine"]
            self.assertEqual(first_trade_count, len(truth["tradeLedger"]))
            self.assertEqual(first_hashes, tuple(item["hash"] for item in truth["tradeLedger"]))
            live_truth = runtime.performance_truth_engine.snapshot(execution_environment="live")
            self.assertEqual(0, len(live_truth["tradeLedger"]))
            self.assertEqual(0, len(live_truth["portfolioLedger"]))
            self.assertEqual("live", live_truth["executionEnvironment"])
        finally:
            self._restore_env(previous)

    def test_decision_laboratory_replays_completed_workflow_and_preserves_truth(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["performanceTruthEngine"]["tradeLedger"]) == 1,
                timeout=2.0,
            )
            runtime.halt_paper_self_training()
            workflow_id = state["performanceTruthEngine"]["tradeLedger"][0]["workflow_id"]
            truth_hashes = tuple(item["hash"] for item in state["performanceTruthEngine"]["tradeLedger"])

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

            after_hashes = tuple(item["hash"] for item in state["performanceTruthEngine"]["tradeLedger"])
            self.assertEqual(truth_hashes, after_hashes)
            self.assertEqual(0, state["decisionLaboratory"]["metrics"]["productionMutationCount"])
            self.assertEqual("IMMUTABLE_LEDGER", state["decisionLaboratory"]["integration"]["tradeLedger"])
        finally:
            self._restore_env(previous)

    def test_decision_laboratory_experiments_compare_without_modifying_production_history(self) -> None:
        previous = self._with_env(ARGOS_WORKFLOW_DEMO_STAGE_DELAY_SECONDS="0", ARGOS_PAPER_WORKFLOW_CYCLE_INTERVAL_SECONDS="5", ARGOS_ENABLE_PLACEHOLDER_CREDIT_PROOF="true")
        try:
            runtime = create_runtime()
            runtime.start_paper_self_training()
            state = self._wait_for_state(
                runtime,
                lambda item: len(item["performanceTruthEngine"]["tradeLedger"]) == 1,
                timeout=2.0,
            )
            runtime.halt_paper_self_training()
            workflow_id = state["performanceTruthEngine"]["tradeLedger"][0]["workflow_id"]
            truth_counts = (
                len(state["performanceTruthEngine"]["tradeLedger"]),
                len(state["performanceTruthEngine"]["portfolioLedger"]),
                len(state["performanceTruthEngine"]["decisionObjectOutcomes"]),
            )
            truth_hashes = tuple(item["hash"] for item in state["performanceTruthEngine"]["tradeLedger"])

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
                len(state["performanceTruthEngine"]["tradeLedger"]),
                len(state["performanceTruthEngine"]["portfolioLedger"]),
                len(state["performanceTruthEngine"]["decisionObjectOutcomes"]),
            )
            self.assertEqual(truth_counts, updated_counts)
            self.assertEqual(truth_hashes, tuple(item["hash"] for item in state["performanceTruthEngine"]["tradeLedger"]))

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

        for button_id in ("bridge-replay", "bridge-lab", "bridge-engineering"):
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
        for office in ("Analyst", "Risk", "Trader", "Historian", "Librarian", "Academy"):
            self.assertIn(f'{office}: "{office.lower()}_bridge_placeholder"', js)

        self.assertIn('id="executive-subcommand-bridge"', html)
        self.assertIn('id="seeker-subcommand-bridge"', html)
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


if __name__ == "__main__":
    unittest.main()
