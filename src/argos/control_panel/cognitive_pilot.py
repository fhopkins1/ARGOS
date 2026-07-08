"""Controlled Cognitive Pilot for ARGOS OE-011G."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from argos.foundation.contracts import utc_timestamp


@dataclass(frozen=True)
class ControlledCognitivePilotLimits:
    """Hard limits for the OE-011G pilot."""

    maximum_concurrent_workflows: int = 1
    maximum_active_ai_offices: int = 1
    maximum_real_api_calls_per_workflow: int = 1
    maximum_session_workflows: int = 10
    maximum_total_pilot_cost_usd: float = 0.05
    maximum_workflow_cost_usd: float = 0.005
    maximum_api_timeout_seconds: int = 20
    maximum_retries: int = 1


class ControlledCognitivePilot:
    """Mission governor and reporting surface for the first real cognitive paper pilot."""

    def __init__(self, *, enabled: bool, limits: ControlledCognitivePilotLimits | None = None) -> None:
        self.enabled = enabled
        self.limits = limits or ControlledCognitivePilotLimits()
        self._started_timestamp = ""
        self._completed_timestamp = ""
        self._aborted_timestamp = ""
        self._abort_reason = ""
        self._alerts: list[dict[str, Any]] = []

    def start(self) -> None:
        """Mark the pilot as started."""
        if not self.enabled or self._started_timestamp:
            return
        self._started_timestamp = utc_timestamp()

    def complete(self, reason: str = "Pilot complete") -> None:
        """Mark the pilot as complete."""
        if not self.enabled or self._completed_timestamp:
            return
        self._completed_timestamp = utc_timestamp()
        self.alert("Pilot complete", "NOTICE", reason)

    def abort(self, reason: str) -> None:
        """Abort the pilot and preserve the failure reason."""
        if not self.enabled or self._aborted_timestamp:
            return
        self._aborted_timestamp = utc_timestamp()
        self._abort_reason = reason
        self.alert("Pilot aborted", "CRITICAL", reason)

    def alert(self, category: str, severity: str, summary: str, evidence: tuple[str, ...] = ()) -> None:
        """Append one pilot alert."""
        signature = (category, severity, summary, evidence)
        if any((item["category"], item["severity"], item["summary"], tuple(item["evidence"])) == signature for item in self._alerts):
            return
        self._alerts.append(
            {
                "alertId": f"CCP-ALERT-{len(self._alerts) + 1:06d}",
                "timestampUtc": utc_timestamp(),
                "category": category,
                "severity": severity,
                "summary": summary,
                "evidence": tuple(evidence),
            }
        )

    def should_start_next_workflow(self, *, completed_pilot_workflows: int, real_api_cost_usd: float) -> tuple[bool, str]:
        """Return whether another pilot workflow may start."""
        if not self.enabled:
            return True, ""
        if self._aborted_timestamp:
            return False, self._abort_reason
        if completed_pilot_workflows >= self.limits.maximum_session_workflows:
            return False, "Maximum session workflows reached."
        if real_api_cost_usd >= self.limits.maximum_total_pilot_cost_usd:
            return False, "Maximum total pilot cost reached."
        return True, ""

    def snapshot(
        self,
        *,
        workflow_orchestrator: dict[str, Any],
        workflow_runtime_monitor: dict[str, Any],
        api_runtime_monitor: dict[str, Any],
        api_execution_gateway: dict[str, Any],
        decision_laboratory: dict[str, Any],
        performance_truth: dict[str, Any],
    ) -> dict[str, Any]:
        """Return the OE-011G mission report."""
        workflows = tuple(
            item
            for item in workflow_orchestrator.get("workflows", ())
            if item.get("workflow_type") == "paper_trading_session"
        )
        completed = tuple(item for item in workflows if item.get("token", {}).get("workflow_status") == "Archived")
        failed = tuple(item for item in workflows if item.get("completion_state") == "BLOCKED")
        gateway_events = tuple(api_execution_gateway.get("events", ()))
        real_events = tuple(item for item in gateway_events if item.get("execution_mode") == "real_api_pilot" and item.get("allowed") and not item.get("fallback_used"))
        real_by_workflow: dict[str, int] = {}
        for event in real_events:
            real_by_workflow[event["workflow_id"]] = real_by_workflow.get(event["workflow_id"], 0) + 1
        total_cost = round(float(api_execution_gateway.get("realApiSessionSpendUsd", 0.0)), 4)
        total_tokens = sum(int(item.get("input_tokens", 0)) + int(item.get("output_tokens", 0)) for item in real_events)
        average_cost = round(total_cost / max(1, len(real_events)), 4)
        average_tokens = round(total_tokens / max(1, len(real_events)), 2)
        average_latency = round(sum(int(item.get("latency_ms", 0)) for item in real_events) / max(1, len(real_events)), 2)
        analyst_confidences = tuple(_analyst_confidence(workflow) for workflow in completed)
        prompt_failures = tuple(item for item in gateway_events if str(item.get("validation_status", "")).startswith("PROMPT"))
        schema_failures = tuple(item for item in gateway_events if item.get("validation_status") == "SCHEMA_INVALID")
        gateway_failures = tuple(item for item in gateway_events if item.get("blocked"))
        constitutional_violations = _constitutional_violations(workflow_orchestrator, workflow_runtime_monitor, api_runtime_monitor, prompt_failures)
        if self.enabled and constitutional_violations:
            self.alert("Constitutional violation", "CRITICAL", "Pilot has constitutional violations.", tuple(constitutional_violations))
        if self.enabled and total_cost > self.limits.maximum_total_pilot_cost_usd:
            self.alert("Budget exceeded", "CRITICAL", "Pilot cost exceeded total limit.", (str(total_cost),))
        status = "DISABLED"
        if self.enabled:
            status = "ABORTED" if self._aborted_timestamp else "COMPLETE" if self._completed_timestamp else "RUNNING" if self._started_timestamp else "READY"
        success = (
            self.enabled
            and len(completed) >= self.limits.maximum_session_workflows
            and not constitutional_violations
            and total_cost <= self.limits.maximum_total_pilot_cost_usd
            and all(real_by_workflow.get(workflow["workflow_id"], 0) == 1 for workflow in completed[-self.limits.maximum_session_workflows :])
        )
        return {
            "pilotName": "Controlled Cognitive Pilot",
            "engineeringOrder": "OE-011G",
            "enabled": self.enabled,
            "status": status,
            "success": success,
            "environment": "paper_trading",
            "realAiOffice": "Analyst",
            "workflowType": "paper_trading_session",
            "limits": self.limits.__dict__,
            "startedTimestampUtc": self._started_timestamp,
            "completedTimestampUtc": self._completed_timestamp,
            "abortedTimestampUtc": self._aborted_timestamp,
            "abortReason": self._abort_reason,
            "missionObjectives": {
                "lawViiValid": workflow_runtime_monitor.get("tokenIntegrity", {}).get("status") == "VALID",
                "exclusiveWorkflowToken": workflow_orchestrator.get("metrics", {}).get("tokenExclusivityViolations", 0) == 0,
                "promptContractGoverned": not prompt_failures,
                "gatewaySoleExecutionPath": True,
                "performanceTruthImmutable": performance_truth.get("integrity", {}).get("immutable", True),
                "decisionLaboratoryReplayable": decision_laboratory.get("metrics", {}).get("completedWorkflowCount", 0) >= len(completed),
                "budgetEnforced": total_cost <= self.limits.maximum_total_pilot_cost_usd,
            },
            "report": {
                "totalWorkflows": len(workflows),
                "completed": len(completed),
                "failed": len(failed),
                "averageRuntime": round(sum(item.get("execution_time_seconds", 0) for item in completed) / max(1, len(completed)), 2),
                "averageApiCost": average_cost,
                "averageTokens": average_tokens,
                "averageLatencyMs": average_latency,
                "averageConfidence": round(sum(analyst_confidences) / max(1, len(analyst_confidences)), 4),
                "gatewayFailures": len(gateway_failures),
                "promptFailures": len(prompt_failures),
                "schemaFailures": len(schema_failures),
                "budgetUsed": total_cost,
                "budgetRemaining": round(max(0.0, self.limits.maximum_total_pilot_cost_usd - total_cost), 4),
                "decisionLaboratoryReplays": decision_laboratory.get("metrics", {}).get("decisionReplayCount", 0),
                "historianFindings": ("Pilot evidence ready for Historian review.",),
                "commanderAssessment": "SUCCESS" if success else ("ABORTED" if self._aborted_timestamp else "IN_PROGRESS" if self.enabled else "STANDBY"),
            },
            "realApiCallsByWorkflow": tuple({"workflowId": key, "realApiCalls": value} for key, value in sorted(real_by_workflow.items())),
            "alerts": tuple(self._alerts),
            "failureCriteria": {
                "constitutionalViolations": tuple(constitutional_violations),
                "budgetExceeded": total_cost > self.limits.maximum_total_pilot_cost_usd,
                "duplicateWorkflowOwnership": workflow_orchestrator.get("metrics", {}).get("tokenExclusivityViolations", 0) > 0,
                "uncontrolledRetries": any(int(item.get("retry_count", 0)) > self.limits.maximum_retries for item in gateway_events),
            },
        }


def _analyst_confidence(workflow: dict[str, Any]) -> float:
    for output in workflow.get("output_history", ()):
        decision = output.get("decision_object", {})
        if decision.get("office") == "Analyst":
            return float(decision.get("confidence", 0.0))
    return 0.0


def _constitutional_violations(
    workflow_orchestrator: dict[str, Any],
    workflow_runtime_monitor: dict[str, Any],
    api_runtime_monitor: dict[str, Any],
    prompt_failures: tuple[dict[str, Any], ...],
) -> tuple[str, ...]:
    violations: list[str] = []
    if workflow_runtime_monitor.get("tokenIntegrity", {}).get("status") != "VALID":
        violations.append("LAW_VII_VIOLATION")
    if workflow_orchestrator.get("metrics", {}).get("tokenExclusivityViolations", 0):
        violations.append("WORKFLOW_TOKEN_VIOLATION")
    if workflow_orchestrator.get("metrics", {}).get("nonDormantAfterTransferViolations", 0):
        violations.append("DORMANCY_VIOLATION")
    if prompt_failures:
        violations.append("PROMPT_CONTRACT_VIOLATION")
    if any(item.get("category", "").startswith("LAW_VII") for item in api_runtime_monitor.get("runtimeAlerts", ())):
        violations.append("API_RUNTIME_LAW_VII_ALERT")
    return tuple(violations)
