"""Local HTTP server for the ARGOS Control Panel."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .runtime import create_runtime


UI_ROOT = Path(__file__).resolve().parents[3] / "ui" / "argos_control_panel"


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run the local ARGOS Control Panel server."""
    runtime = create_runtime()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/api/state":
                self._json(runtime.state())
                return
            if parsed.path == "/api/eab/events":
                filters = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
                self._json(runtime.eab_events(filters))
                return
            if parsed.path == "/api/cnac/notifications":
                filters = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
                self._json(runtime.cnac_notifications(filters))
                return
            if parsed.path == "/api/ioe/explorer":
                filters = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
                self._json(runtime.ioe_explorer(filters))
                return
            if parsed.path == "/api/command/history":
                filters = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
                self._json(runtime.command_console_history(filters))
                return
            if parsed.path == "/api/infrastructure/state":
                self._json(runtime.infrastructure_state())
                return
            if parsed.path == "/api/lppc/state":
                self._json(runtime.lppc_state())
                return
            if parsed.path == "/api/strategy-performance/state":
                self._json(runtime.strategy_performance_state())
                return
            if parsed.path == "/api/performance-truth/state":
                self._json(runtime.performance_truth_state())
                return
            if parsed.path == "/api/trader/bridge":
                self._json(runtime.state()["traderCommandBridge"])
                return
            if parsed.path == "/api/commander/strategic-dashboard":
                self._json(runtime.state()["commanderStrategicDashboard"])
                return
            if parsed.path == "/api/commander/briefing":
                self._json(runtime.state()["commanderBriefingGenerator"])
                return
            if parsed.path == "/api/information-freshness/state":
                self._json(runtime.state()["informationFreshnessEngine"])
                return
            if parsed.path == "/api/enterprise-memory/state":
                self._json(runtime.state()["enterpriseMemoryCache"])
                return
            if parsed.path == "/api/workflow-delta/state":
                self._json(runtime.state()["workflowDeltaEngine"])
                return
            if parsed.path == "/api/enterprise-priority/state":
                self._json(runtime.state()["enterprisePriorityEngine"])
                return
            if parsed.path == "/api/position-monitoring/state":
                self._json(runtime.state()["positionMonitoringNetwork"])
                return
            if parsed.path == "/api/communications-bus/state":
                self._json(runtime.communications_bus_state())
                return
            if parsed.path == "/api/efficiency-analytics/state":
                self._json(runtime.state()["enterpriseEfficiencyAnalytics"])
                return
            if parsed.path == "/api/doctrine-policy/state":
                self._json(runtime.doctrine_policy_state())
                return
            if parsed.path == "/api/grand-strategy/state":
                self._json(runtime.state()["enterpriseGrandStrategyEngine"])
                return
            if parsed.path == "/api/strategic-intelligence/state":
                self._json(runtime.state()["strategicIntelligenceCommand"])
                return
            if parsed.path == "/api/blue-ocean/state":
                self._json(runtime.state()["blueOceanIntelligenceOffice"])
                return
            if parsed.path == "/api/disruption/state":
                self._json(runtime.state()["disruptionIntelligenceOffice"])
                return
            if parsed.path == "/api/decline/state":
                self._json(runtime.state()["declineIntelligenceOffice"])
                return
            if parsed.path == "/api/short-opportunity/state":
                self._json(runtime.state()["shortOpportunityOffice"])
                return
            if parsed.path == "/api/market-structure/state":
                self._json(runtime.state()["marketStructureIntelligenceOffice"])
                return
            if parsed.path == "/api/capital-rotation/state":
                self._json(runtime.state()["capitalRotationIntelligenceOffice"])
                return
            if parsed.path == "/api/strategic-synthesis/state":
                self._json(runtime.state()["strategicSynthesisOffice"])
                return
            if parsed.path == "/api/reality-calibration/state":
                self._json(runtime.state()["enterpriseRealityCalibrationEngine"])
                return
            if parsed.path == "/api/correlation-intelligence/state":
                self._json(runtime.state()["correlationIntelligenceEngine"])
                return
            if parsed.path == "/api/market-replay/state":
                self._json(runtime.state()["marketReplayEngine"])
                return
            if parsed.path == "/api/stress-testing/state":
                self._json(runtime.state()["stressTestingEngine"])
                return
            if parsed.path == "/api/black-swan/state":
                self._json(runtime.state()["blackSwanSimulationEngine"])
                return
            if parsed.path == "/api/monte-carlo/state":
                self._json(runtime.state()["monteCarloPortfolioEngine"])
                return
            if parsed.path == "/api/risk-factor/state":
                self._json(runtime.state()["enterpriseRiskFactorEngine"])
                return
            if parsed.path == "/api/capital-allocation/state":
                self._json(runtime.state()["capitalAllocationEngine"])
                return
            if parsed.path == "/api/portfolio-construction/state":
                self._json(runtime.state()["portfolioConstructionEngine"])
                return
            if parsed.path == "/api/position-sizing/state":
                self._json(runtime.state()["positionSizingEngine"])
                return
            if parsed.path == "/api/decision-laboratory/state":
                filters = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
                self._json(runtime.decision_laboratory_state(str(filters.get("q", ""))))
                return
            if parsed.path == "/api/credit-governor/state":
                self._json(runtime.credit_governor_state())
                return
            if parsed.path == "/api/api-runtime-monitor/state":
                self._json(runtime.api_runtime_monitor_state())
                return
            if parsed.path == "/api/workflow-orchestrator/state":
                self._json(runtime.workflow_orchestrator_state())
                return
            if parsed.path == "/api/workflow-runtime-monitor/state":
                self._json(runtime.workflow_runtime_monitor_state())
                return
            path = "index.html" if parsed.path in {"", "/"} else parsed.path.lstrip("/")
            self._static(path)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            body = self._body()
            routes = {
                "/api/paper/start": runtime.start_paper_self_training,
                "/api/paper/halt": runtime.halt_paper_self_training,
                "/api/bridge/pause": runtime.pause_after_current_stage,
                "/api/bridge/step": runtime.step_paused_workflow,
                "/api/bridge/resume": runtime.resume_after_pause,
                "/api/trader/cancel-pending-orders": runtime.cancel_pending_orders,
                "/api/historian/generate-learning-report": runtime.generate_learning_report,
                "/api/historian/compare-prompt-versions": runtime.compare_prompt_versions,
                "/api/historian/compare-strategies": runtime.compare_strategies,
                "/api/treasury/halt": runtime.halt_user_funds,
                "/api/live/request": runtime.request_real_world_trading,
                "/api/live/halt": runtime.halt_real_world_trading,
            }
            if parsed.path in routes:
                self._json(routes[parsed.path]())
                return
            if parsed.path == "/api/treasury/deposit":
                self._json(runtime.deposit_user_funds(float(body.get("amountUsd", 0))))
                return
            if parsed.path == "/api/budget":
                self._json(runtime.set_api_budget(float(body.get("budgetUsd", 0))))
                return
            if parsed.path == "/api/ecc/action":
                self._json(
                    runtime.commander_action(
                        str(body.get("action", "")),
                        str(body.get("target", "")),
                        str(body.get("detail", "")),
                    )
                )
                return
            if parsed.path == "/api/ecc/export":
                self._json(runtime.export_ecc_report())
                return
            if parsed.path == "/api/scheduler/configure":
                self._json(
                    runtime.configure_office_schedule(
                        str(body.get("organization", "")),
                        str(body.get("office", "")),
                        str(body.get("operatingMode", "Event Driven")),
                        float(body.get("resourceBudgetUsd", 5.0)),
                        int(body.get("runtimeLimitMinutes", 60)),
                        str(body.get("timeZone", "America/Cancun")),
                        str(body.get("businessHours", "09:30-16:00")),
                    )
                )
                return
            if parsed.path == "/api/scheduler/activate":
                self._json(runtime.activate_office(str(body.get("organization", "")), str(body.get("office", "")), str(body.get("trigger", "Commander"))))
                return
            if parsed.path == "/api/scheduler/suspend":
                self._json(runtime.suspend_office(str(body.get("organization", "")), str(body.get("office", "")), str(body.get("trigger", "Commander"))))
                return
            if parsed.path == "/api/eos/control":
                self._json(runtime.eos_control(str(body.get("action", "")), body))
                return
            if parsed.path == "/api/odo/task":
                self._json(runtime.submit_duty_officer_request(body))
                return
            if parsed.path == "/api/event-detection/observe":
                self._json(runtime.event_detection_observe())
                return
            if parsed.path == "/api/event-detection/replay":
                self._json(runtime.event_detection_replay(tuple(body.get("observations", ()) or ())))
                return
            if parsed.path == "/api/event-detection/resolve":
                self._json(
                    runtime.resolve_event_detection_event(
                        str(body.get("eventId", "")),
                        str(body.get("reason", "Commander resolved event.")),
                    )
                )
                return
            if parsed.path == "/api/mission-planner/plan-event":
                self._json(runtime.mission_planner_plan_event(dict(body.get("event", body)), submit_to_scheduler=bool(body.get("submitToScheduler", False))))
                return
            if parsed.path == "/api/mission-planner/commander-request":
                self._json(runtime.mission_planner_commander_request(body, submit_to_scheduler=bool(body.get("submitToScheduler", False))))
                return
            if parsed.path == "/api/mission-planner/submit":
                self._json(runtime.mission_planner_submit_plan(str(body.get("missionPlanId", ""))))
                return
            if parsed.path == "/api/mission-planner/replay":
                self._json(runtime.mission_planner_replay(tuple(body.get("triggers", ()) or ())))
                return
            if parsed.path == "/api/cost-governor/reserve":
                self._json(runtime.cost_governor_reserve_for_plan(str(body.get("missionPlanId", ""))))
                return
            if parsed.path == "/api/cost-governor/release":
                self._json(runtime.cost_governor_release_reservation(str(body.get("reservationId", ""))))
                return
            if parsed.path == "/api/cost-governor/settle":
                self._json(runtime.cost_governor_settle_reservation(str(body.get("reservationId", ""))))
                return
            if parsed.path == "/api/cost-governor/policy":
                self._json(runtime.cost_governor_policy(body))
                return
            if parsed.path == "/api/information-freshness/register":
                self._json(runtime.information_freshness_register(body))
                return
            if parsed.path == "/api/information-freshness/evaluate":
                self._json(runtime.information_freshness_evaluate(str(body.get("recordId", body.get("record_id", ""))), dict(body.get("context", {}))))
                return
            if parsed.path == "/api/information-freshness/invalidate":
                self._json(runtime.information_freshness_invalidate(str(body.get("recordId", body.get("record_id", ""))), str(body.get("reason", "manual_invalidation")), body))
                return
            if parsed.path == "/api/information-freshness/supersede":
                self._json(runtime.information_freshness_supersede(str(body.get("priorRecordId", body.get("prior_record_id", ""))), dict(body.get("newRecord", body.get("new_record", {})))))
                return
            if parsed.path == "/api/information-freshness/contradiction":
                self._json(runtime.information_freshness_contradiction(body))
                return
            if parsed.path == "/api/information-freshness/policy":
                self._json(runtime.information_freshness_policy(body))
                return
            if parsed.path == "/api/enterprise-memory/admit":
                self._json(runtime.enterprise_memory_admit(body))
                return
            if parsed.path == "/api/enterprise-memory/query":
                self._json(runtime.enterprise_memory_query(body))
                return
            if parsed.path == "/api/enterprise-memory/invalidate":
                self._json(runtime.enterprise_memory_invalidate(str(body.get("recordId", body.get("cacheRecordId", body.get("cache_record_id", "")))), body))
                return
            if parsed.path == "/api/enterprise-memory/supersede":
                self._json(runtime.enterprise_memory_supersede(str(body.get("priorRecordId", body.get("prior_record_id", ""))), dict(body.get("newRecord", body.get("new_record", {})))))
                return
            if parsed.path == "/api/enterprise-memory/contradiction":
                self._json(runtime.enterprise_memory_contradiction(str(body.get("recordId", body.get("cacheRecordId", body.get("cache_record_id", "")))), body))
                return
            if parsed.path == "/api/enterprise-memory/quarantine":
                self._json(runtime.enterprise_memory_quarantine(str(body.get("recordId", body.get("cacheRecordId", body.get("cache_record_id", "")))), body))
                return
            if parsed.path == "/api/enterprise-memory/archive":
                self._json(runtime.enterprise_memory_archive(str(body.get("recordId", body.get("cacheRecordId", body.get("cache_record_id", "")))), body))
                return
            if parsed.path == "/api/workflow-delta/baseline":
                self._json(runtime.workflow_delta_create_baseline(body))
                return
            if parsed.path == "/api/workflow-delta/analyze":
                self._json(runtime.workflow_delta_analyze(body))
                return
            if parsed.path == "/api/workflow-delta/recover":
                self._json(runtime.workflow_delta_recover(dict(body.get("snapshot", body))))
                return
            if parsed.path == "/api/workflow-delta/export":
                self._json(runtime.workflow_delta_export(str(body.get("packageId", body.get("package_id", ""))), str(body.get("format", "json"))))
                return
            if parsed.path == "/api/workflow-delta/replay":
                self._json(runtime.workflow_delta_replay(str(body.get("packageId", body.get("package_id", "")))))
                return
            if parsed.path == "/api/workflow-delta/review":
                self._json(runtime.workflow_delta_review(str(body.get("packageId", body.get("package_id", ""))), body))
                return
            if parsed.path == "/api/enterprise-priority/evaluate":
                self._json(runtime.enterprise_priority_evaluate(body))
                return
            if parsed.path == "/api/enterprise-priority/recover":
                self._json(runtime.enterprise_priority_recover(dict(body.get("snapshot", body))))
                return
            if parsed.path == "/api/enterprise-priority/replay":
                self._json(runtime.enterprise_priority_replay(body))
                return
            if parsed.path == "/api/enterprise-priority/modifier":
                self._json(runtime.enterprise_priority_modifier(str(body.get("candidateId", body.get("candidate_id", ""))), body))
                return
            if parsed.path == "/api/position-monitoring/scan":
                self._json(runtime.position_monitoring_scan())
                return
            if parsed.path == "/api/position-monitoring/recover":
                self._json(runtime.position_monitoring_recover(dict(body.get("snapshot", body))))
                return
            if parsed.path == "/api/position-monitoring/replay":
                self._json(runtime.position_monitoring_replay())
                return
            if parsed.path == "/api/communications-bus/publish":
                self._json(runtime.communications_bus_publish_sample(body))
                return
            if parsed.path == "/api/communications-bus/retry":
                self._json(runtime.communications_bus_retry_dead_letter(str(body.get("deadLetterId", body.get("dead_letter_id", ""))), dict(body.get("authorization", {}))))
                return
            if parsed.path == "/api/communications-bus/replay":
                self._json(runtime.communications_bus_replay(str(body.get("messageId", body.get("message_id", ""))), analytical=bool(body.get("analytical", True)), authorization=dict(body.get("authorization", {}))))
                return
            if parsed.path == "/api/communications-bus/recover":
                self._json(runtime.communications_bus_recover(dict(body.get("snapshot", body))))
                return
            if parsed.path == "/api/communications-bus/trace":
                self._json(runtime.communications_bus_trace(str(body.get("correlationId", body.get("correlation_id", "")))))
                return
            if parsed.path == "/api/efficiency-analytics/refresh":
                self._json(runtime.efficiency_analytics_refresh(body))
                return
            if parsed.path == "/api/efficiency-analytics/acknowledge":
                self._json(runtime.efficiency_acknowledge_finding(str(body.get("findingId", body.get("finding_id", ""))), str(body.get("reason", "Commander acknowledged efficiency finding."))))
                return
            if parsed.path == "/api/efficiency-analytics/recalculate":
                self._json(runtime.efficiency_recalculate_metric(str(body.get("metricValueId", body.get("metric_value_id", ""))), str(body.get("formulaVersion", body.get("formula_version", "")))))
                return
            if parsed.path == "/api/efficiency-analytics/lineage":
                self._json(runtime.efficiency_metric_lineage(str(body.get("metricValueId", body.get("metric_value_id", "")))))
                return
            if parsed.path == "/api/efficiency-analytics/compare":
                self._json(runtime.efficiency_compare_periods(dict(body.get("left", {})), dict(body.get("right", {}))))
                return
            if parsed.path == "/api/doctrine-policy/submit":
                self._json(runtime.doctrine_policy_submit(body))
                return
            if parsed.path == "/api/doctrine-policy/approve":
                self._json(runtime.doctrine_policy_approve(str(body.get("policyVersionId", body.get("policy_version_id", ""))), body))
                return
            if parsed.path == "/api/doctrine-policy/schedule":
                self._json(runtime.doctrine_policy_schedule(str(body.get("policyVersionId", body.get("policy_version_id", ""))), body))
                return
            if parsed.path == "/api/doctrine-policy/activate":
                self._json(runtime.doctrine_policy_activate(str(body.get("activationPlanId", body.get("activation_plan_id", ""))), body))
                return
            if parsed.path == "/api/doctrine-policy/suspend":
                self._json(runtime.doctrine_policy_suspend(str(body.get("policyVersionId", body.get("policy_version_id", ""))), str(body.get("reason", "Commander requested policy suspension."))))
                return
            if parsed.path == "/api/doctrine-policy/rollback":
                self._json(runtime.doctrine_policy_rollback(str(body.get("policyVersionId", body.get("policy_version_id", ""))), body))
                return
            if parsed.path == "/api/doctrine-policy/directive":
                self._json(runtime.doctrine_policy_directive(body))
                return
            if parsed.path == "/api/doctrine-policy/drift":
                self._json(runtime.doctrine_policy_drift(body))
                return
            if parsed.path == "/api/doctrine-policy/replay":
                self._json(runtime.doctrine_policy_replay(body))
                return
            if parsed.path == "/api/doctrine-policy/impact":
                self._json(runtime.doctrine_policy_impact(str(body.get("policyVersionId", body.get("policy_version_id", "")))))
                return
            if parsed.path == "/api/cnac/acknowledge":
                self._json(runtime.acknowledge_notification(str(body.get("notificationId", ""))))
                return
            if parsed.path == "/api/cnac/escalate":
                self._json(runtime.escalate_notifications())
                return
            if parsed.path == "/api/cnac/briefing":
                self._json(runtime.generate_commander_briefing(str(body.get("briefingType", "Daily Enterprise Report"))))
                return
            if parsed.path == "/api/ioe/action":
                self._json(runtime.ioe_action(str(body.get("action", "")), str(body.get("nodeId", ""))))
                return
            if parsed.path == "/api/command/execute":
                self._json(
                    runtime.command_console_execute(
                        str(body.get("commandName", "")),
                        str(body.get("category", "")),
                        str(body.get("target", "")),
                        str(body.get("detail", "")),
                        float(body.get("amountUsd", 0)),
                    )
                )
                return
            if parsed.path == "/api/command/macro":
                self._json(runtime.command_console_macro(str(body.get("macroName", ""))))
                return
            if parsed.path == "/api/commander/journal":
                self._json(runtime.add_commander_journal_entry(str(body.get("category", "")), str(body.get("entry", ""))))
                return
            if parsed.path == "/api/infrastructure/configure":
                organization_limit = body.get("organizationLimitUsd")
                self._json(
                    runtime.configure_infrastructure(
                        float(body.get("dailyBudgetUsd", 25)),
                        float(body.get("monthlyBudgetUsd", 250)),
                        int(body.get("runtimeLimitMinutes", 60)),
                        str(body.get("resourceMode", "Balanced")),
                        str(body.get("organization", "")),
                        None if organization_limit in {None, ""} else float(organization_limit),
                    )
                )
                return
            if parsed.path == "/api/infrastructure/optimization":
                self._json(runtime.record_infrastructure_optimization(str(body.get("action", ""))))
                return
            if parsed.path == "/api/credit-governor/configure":
                self._json(
                    runtime.configure_credit_governor(
                        float(body.get("dailyBudgetUsd", 25)),
                        float(body.get("weeklyBudgetUsd", 100)),
                        float(body.get("monthlyBudgetUsd", 250)),
                        str(body.get("office", "")),
                        None if body.get("officeBudgetUsd") in {None, ""} else float(body.get("officeBudgetUsd", 0)),
                        str(body.get("workflow", "")),
                        None if body.get("workflowBudgetUsd") in {None, ""} else float(body.get("workflowBudgetUsd", 0)),
                        str(body.get("taskIdentifier", "")),
                        None if body.get("taskBudgetUsd") in {None, ""} else float(body.get("taskBudgetUsd", 0)),
                    )
                )
                return
            if parsed.path == "/api/credit-governor/activate":
                self._json(
                    runtime.request_credit_activation(
                        str(body.get("taskIdentifier", "")),
                        str(body.get("activatingSource", "")),
                        str(body.get("receivingOffice", "")),
                        str(body.get("purpose", "")),
                        str(body.get("requiredOutput", "")),
                        int(body.get("maximumRuntimeMinutes", 5)),
                        float(body.get("maximumCreditBudgetUsd", 0)),
                        str(body.get("workflow", "")),
                        str(body.get("organization", "")),
                        tuple(body.get("evidencePackage", ()) or ()),
                        str(body.get("returnRoute", "Commander Interface")),
                        str(body.get("workflowId", "")),
                        str(body.get("workflowTokenId", "")),
                        str(body.get("office", body.get("receivingOffice", ""))),
                    )
                )
                return
            if parsed.path == "/api/credit-governor/complete":
                self._json(runtime.complete_credit_activation(str(body.get("activationId", ""))))
                return
            if parsed.path == "/api/api-runtime-monitor/control":
                self._json(
                    runtime.api_runtime_monitor_control(
                        str(body.get("action", "")),
                        str(body.get("target", "")),
                        str(body.get("value", "")),
                    )
                )
                return
            if parsed.path == "/api/api-runtime-monitor/reset-session":
                self._json(runtime.reset_api_runtime_session())
                return
            if parsed.path == "/api/workflow-orchestrator/create":
                self._json(
                    runtime.create_workflow(
                        str(body.get("name", "Commander Workflow")),
                        tuple(body.get("stages", ()) or ()),
                        int(body.get("runtimeBudget", 60)),
                        float(body.get("creditBudget", 1.0)),
                        tuple(body.get("expectedOutputSchema", ()) or ()),
                    )
                )
                return
            if parsed.path == "/api/workflow-orchestrator/execute":
                self._json(runtime.start_workflow_execution(str(body.get("workflowId", ""))))
                return
            if parsed.path == "/api/workflow-orchestrator/output":
                self._json(
                    runtime.produce_workflow_output(
                        str(body.get("workflowId", "")),
                        dict(body.get("output", {}) or {}),
                        int(body.get("runtime", 1)),
                        float(body.get("credits", 0.01)),
                        int(body.get("tokenUsage", 1)),
                        int(body.get("executionTimeSeconds", 1)),
                    )
                )
                return
            if parsed.path == "/api/workflow-orchestrator/transfer":
                self._json(runtime.transfer_workflow_token(str(body.get("workflowId", "")), str(body.get("reason", "Structured output validated"))))
                return
            if parsed.path == "/api/workflow-orchestrator/next-stage":
                self._json(runtime.advance_workflow_stage(str(body.get("workflowId", ""))))
                return
            if parsed.path == "/api/workflow-orchestrator/archive":
                self._json(runtime.archive_workflow(str(body.get("workflowId", ""))))
                return
            if parsed.path == "/api/decision-laboratory/experiment":
                self._json(
                    runtime.create_decision_lab_experiment(
                        str(body.get("workflowId", "")),
                        dict(body.get("parameterChanges", {}) or {}),
                        str(body.get("parentExperimentId", "")),
                    )
                )
                return
            if parsed.path == "/api/decision-laboratory/replay/start":
                self._json(runtime.start_decision_lab_replay(str(body.get("workflowId", ""))))
                return
            if parsed.path == "/api/decision-laboratory/replay/control":
                self._json(
                    runtime.control_decision_lab_replay(
                        str(body.get("replayId", "")),
                        str(body.get("action", "")),
                        str(body.get("value", "")),
                    )
                )
                return
            self.send_error(404, "Unknown endpoint")

        def log_message(self, format: str, *args: object) -> None:
            return

        def _body(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            if self.headers.get("Content-Type", "").startswith("application/json"):
                return json.loads(raw)
            return {key: values[-1] for key, values in parse_qs(raw).items()}

        def _json(self, payload: object) -> None:
            encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _static(self, relative_path: str) -> None:
            target = (UI_ROOT / relative_path).resolve()
            if not str(target).startswith(str(UI_ROOT.resolve())) or not target.is_file():
                self.send_error(404, "Not found")
                return
            content_type = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
            }.get(target.suffix, "application/octet-stream")
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"ARGOS Control Panel running at http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ARGOS Control Panel")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
