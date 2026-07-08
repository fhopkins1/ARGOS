"""Workflow Runtime Monitor for ARGOS OE-011."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


ACTIVE_STATUSES = {
    "Assigned",
    "Executing",
    "Structured Output Produced",
    "Ownership Transferred",
    "Next Stage",
}

COMPLETED_STATUSES = {"Completed", "Archived"}


@dataclass(frozen=True)
class WorkflowTimelineEvent:
    """Chronological workflow history item observed by the monitor."""

    event_id: str
    workflow_id: str
    event_type: str
    timestamp_utc: str
    status: str
    stage: str
    owner: str
    audit_identifier: str
    transfer_count: int
    token_id: str
    message: str


@dataclass(frozen=True)
class WorkflowMonitorAlert:
    """Commander alert emitted by the observational monitor."""

    alert_id: str
    workflow_id: str
    severity: str
    category: str
    summary: str
    timestamp_utc: str
    evidence: tuple[str, ...]


class WorkflowRuntimeMonitor:
    """Observational workflow execution visibility layer."""

    def __init__(self) -> None:
        self._timeline: list[WorkflowTimelineEvent] = []
        self._alerts: list[WorkflowMonitorAlert] = []
        self._last_seen_signature: dict[str, tuple[Any, ...]] = {}
        self._alert_signatures: set[tuple[str, str, tuple[str, ...]]] = set()

    def snapshot(self, *, orchestrator: dict[str, Any], timestamp_utc: str) -> dict[str, Any]:
        """Observe workflow state and return Commander visibility."""
        workflows = tuple(orchestrator.get("workflows", ()))
        audit_history = tuple(orchestrator.get("auditHistory", ()))
        self._observe_workflows(workflows, audit_history, timestamp_utc)
        alerts = self._verify_integrity(orchestrator, workflows, timestamp_utc)
        active = tuple(_workflow_view(workflow, self._timeline) for workflow in workflows if workflow["token"]["workflow_status"] in ACTIVE_STATUSES)
        queued = tuple(_workflow_view(workflow, self._timeline) for workflow in workflows if workflow["token"]["workflow_status"] == "Queued")
        completed = tuple(_workflow_view(workflow, self._timeline) for workflow in workflows if workflow["token"]["workflow_status"] in COMPLETED_STATUSES)
        all_workflows = tuple(_workflow_view(workflow, self._timeline) for workflow in workflows)
        active_workflow = active[0] if active else None
        selected_baton = _baton_view(_workflow_by_id(workflows, active_workflow["workflowIdentifier"]), self._timeline) if active_workflow else (_baton_view(workflows[-1], self._timeline) if workflows else None)
        timeline = tuple(_timeline_event_view(event) for event in self._timeline[-80:])
        token_integrity = _global_token_integrity(orchestrator, workflows)
        commander_status_line = active_workflow["commanderStatusLine"] if active_workflow else ("Workflow completed and archived." if completed else "No active workflow.")
        commander_status_detail = active_workflow["commanderStatusDetail"] if active_workflow else ("Recent completed workflows remain visible in OE-011." if completed else "Workflow Runtime Monitor is standing by.")
        return {
            "observationalOnly": True,
            "doesNotExecuteWorkflows": True,
            "doesNotTransferTokens": True,
            "commanderStatusLine": commander_status_line,
            "commanderStatusDetail": commander_status_detail,
            "activeWorkflow": active_workflow,
            "activeWorkflows": active,
            "queuedWorkflows": queued,
            "completedWorkflows": completed,
            "allWorkflows": all_workflows,
            "liveWorkflowExecution": tuple(item for item in all_workflows if item["status"] in ACTIVE_STATUSES),
            "workflowBaton": selected_baton,
            "workflowBatonView": tuple(_baton_view(workflow, self._timeline) for workflow in workflows),
            "workflowTimeline": timeline,
            "workflowTimelineView": timeline,
            "recentCompletedWorkflows": tuple(completed[-10:]),
            "workflowTokenIntegrityPanel": tuple(_token_integrity_panel(workflow, orchestrator) for workflow in workflows),
            "timeline": tuple(asdict(event) for event in self._timeline[-80:]),
            "commanderAlerts": tuple(asdict(alert) for alert in alerts[-40:]),
            "enterpriseHealth": _enterprise_health(orchestrator, workflows),
            "tokenIntegrity": {
                "status": token_integrity["status"],
                "violation_code": token_integrity["violation_code"],
                "violation_reason": token_integrity["violation_reason"],
                "workflow_id": token_integrity["workflow_id"],
                "token_id": token_integrity["token_id"],
                "offending_office": token_integrity["offending_office"],
                "expected_owner": token_integrity["expected_owner"],
                "exactlyOneOwner": orchestrator.get("metrics", {}).get("tokenExclusivityViolations", 0) == 0,
                "validOwnershipChain": not any(alert.category == "Invalid Ownership Transfer" for alert in alerts),
                "validTransferSequence": not any(alert.category == "Enterprise Law Violation" for alert in alerts),
                "runtimeBudgetAvailability": not any(alert.category == "Runtime Exceeded" for alert in alerts),
                "creditBudgetAvailability": not any(alert.category == "Budget Exceeded" for alert in alerts),
                "auditContinuity": not any(alert.category == "Audit Inconsistency" for alert in alerts),
                "workflowConsistency": not any(alert.severity == "CRITICAL" for alert in alerts),
            },
            "metrics": {
                "activeWorkflows": len(active),
                "queuedWorkflows": len(queued),
                "completedWorkflows": len(completed),
                "commanderAlertCount": len(alerts),
                "timelineEventCount": len(self._timeline),
            },
        }

    def _observe_workflows(self, workflows: tuple[dict[str, Any], ...], audit_history: tuple[dict[str, Any], ...], timestamp_utc: str) -> None:
        audits_by_workflow: dict[str, list[dict[str, Any]]] = {}
        for audit in audit_history:
            audits_by_workflow.setdefault(audit["workflow_id"], []).append(audit)
        for workflow in workflows:
            workflow_id = workflow["workflow_id"]
            token = workflow["token"]
            signature = (
                token["workflow_status"],
                token["current_owner"],
                token["previous_owner"],
                token["next_owner"],
                token["transfer_count"],
                workflow["current_stage_index"],
                len(workflow.get("output_history", ())),
            )
            if self._last_seen_signature.get(workflow_id) != signature:
                self._synthesize_timeline(workflow, tuple(audits_by_workflow.get(workflow_id, ())), timestamp_utc)
            self._last_seen_signature[workflow_id] = signature

    def _synthesize_timeline(self, workflow: dict[str, Any], audits: tuple[dict[str, Any], ...], timestamp_utc: str) -> None:
        token = workflow["token"]
        stages = tuple(workflow["stages"])
        outputs = tuple(workflow.get("output_history", ()))
        status = token["workflow_status"]
        created_at = token["creation_timestamp"]
        self._append_event(workflow, "Workflow Created", created_at, stage=stages[0], owner="")
        self._append_event(workflow, "Workflow Validated", created_at, stage=stages[0], owner="")
        self._append_event(workflow, "Workflow Queued", created_at, stage=stages[0], owner="")
        if status in ACTIVE_STATUSES or status in COMPLETED_STATUSES or outputs:
            self._append_event(workflow, "Token Assigned", created_at, stage=stages[0], owner=stages[0])
            self._append_event(workflow, "Ownership Assigned", created_at, stage=stages[0], owner=stages[0])
            self._append_event(workflow, "Stage Started", created_at, stage=stages[0], owner=stages[0])
            self._append_event(workflow, "Execution Started", created_at, stage=stages[0], owner=stages[0])
        for index, output in enumerate(outputs):
            if index >= len(stages):
                break
            stage = stages[index]
            audit = audits[index] if index < len(audits) else {}
            event_time = audit.get("timestamp", timestamp_utc)
            structured_output_id = output.get("structured_output_id", f"{workflow['workflow_id']}-OUT-{index + 1:03d}")
            self._append_event(workflow, "Structured Output Produced", event_time, stage=stage, owner=stage, message=f"{stage} completed structured output {structured_output_id}.", transfer_count=index + 1)
            self._append_event(workflow, "Stage Completed", event_time, stage=stage, owner=stage, message=f"{stage} completed workflow stage.", transfer_count=index + 1)
            next_stage = stages[index + 1] if index + 1 < len(stages) else ""
            if next_stage:
                self._append_event(workflow, "Token Transferred", event_time, stage=next_stage, owner=next_stage, message=f"Workflow token transferred from {stage} to {next_stage}.", transfer_count=index + 1)
                self._append_event(workflow, "Ownership Transferred", event_time, stage=next_stage, owner=next_stage, message=f"Workflow token transferred from {stage} to {next_stage}.", transfer_count=index + 1)
                self._append_event(workflow, "Token Assigned", event_time, stage=next_stage, owner=next_stage, message=f"Workflow token assigned to {next_stage}.", transfer_count=index + 1)
                self._append_event(workflow, "Stage Started", event_time, stage=next_stage, owner=next_stage, message=_stage_started_message(next_stage), transfer_count=index + 1)
                self._append_event(workflow, "Execution Started", event_time, stage=next_stage, owner=next_stage, message=_stage_started_message(next_stage), transfer_count=index + 1)
        if status in COMPLETED_STATUSES:
            final_stage = stages[-1]
            final_time = audits[-1]["timestamp"] if audits else timestamp_utc
            self._append_event(workflow, "Workflow Completed", final_time, stage=final_stage, owner="")
        if status == "Archived":
            final_stage = stages[-1]
            self._append_event(workflow, "Workflow Archived", timestamp_utc, stage=final_stage, owner="")

    def _append_event(
        self,
        workflow: dict[str, Any],
        event_type: str,
        timestamp_utc: str,
        *,
        stage: str | None = None,
        owner: str | None = None,
        message: str = "",
        transfer_count: int | None = None,
    ) -> None:
        token = workflow["token"]
        event_stage = stage if stage is not None else token["workflow_stage"]
        event_owner = owner if owner is not None else token["current_owner"]
        event_transfer_count = token["transfer_count"] if transfer_count is None else transfer_count
        signature = (
            workflow["workflow_id"],
            event_type,
            event_stage,
            event_owner,
            event_transfer_count,
        )
        if any((event.workflow_id, event.event_type, event.stage, event.owner, event.transfer_count) == signature for event in self._timeline):
            return
        self._timeline.append(
            WorkflowTimelineEvent(
                event_id=f"WRM-TL-{len(self._timeline) + 1:06d}",
                workflow_id=workflow["workflow_id"],
                event_type=event_type,
                timestamp_utc=timestamp_utc,
                status=token["workflow_status"],
                stage=event_stage,
                owner=event_owner,
                audit_identifier=token["audit_identifier"],
                transfer_count=event_transfer_count,
                token_id=token["audit_identifier"],
                message=message or _event_message(event_type, workflow, event_stage, event_owner),
            )
        )

    def _verify_integrity(self, orchestrator: dict[str, Any], workflows: tuple[dict[str, Any], ...], timestamp_utc: str) -> tuple[WorkflowMonitorAlert, ...]:
        for workflow in workflows:
            token = workflow["token"]
            active_owners = tuple(owner for owner, state in workflow["office_states"].items() if state in {"Assigned", "Executing"})
            if len(active_owners) != (1 if token["workflow_status"] in ACTIVE_STATUSES else 0):
                self._append_alert(workflow, "CRITICAL", "Ownership Conflict", "Workflow does not display exactly one active owner.", timestamp_utc, active_owners)
            if len(active_owners) > 1:
                self._append_alert(workflow, "CRITICAL", "Duplicate Ownership", "Multiple offices appear active for one Workflow Execution Token.", timestamp_utc, active_owners)
            if workflow["runtime_used"] > token["runtime_budget"]:
                self._append_alert(workflow, "WARNING", "Runtime Exceeded", "Workflow runtime budget has been exceeded.", timestamp_utc, (str(workflow["runtime_used"]), str(token["runtime_budget"])))
            if workflow["credits_used"] > token["credit_budget"]:
                self._append_alert(workflow, "WARNING", "Budget Exceeded", "Workflow credit budget has been exceeded.", timestamp_utc, (str(workflow["credits_used"]), str(token["credit_budget"])))
            if token["workflow_status"] == "Executing" and not workflow["latest_output"] and workflow["execution_time_seconds"] > token["runtime_budget"]:
                self._append_alert(workflow, "WARNING", "Missing Structured Output", "Workflow exceeded expected runtime without structured output.", timestamp_utc, (workflow["workflow_id"],))
        if orchestrator.get("metrics", {}).get("tokenExclusivityViolations", 0):
            self._append_global_alert("CRITICAL", "Enterprise Law Violation", "Enterprise Law VII violation reported by OE-010.", timestamp_utc, ("tokenExclusivityViolations",))
        if orchestrator.get("metrics", {}).get("nonDormantAfterTransferViolations", 0):
            self._append_global_alert("CRITICAL", "Invalid Ownership Transfer", "Previous owner did not return to Dormant after token transfer.", timestamp_utc, ("nonDormantAfterTransferViolations",))
        audit_ids = [item["audit_id"] for item in orchestrator.get("auditHistory", ())]
        if len(audit_ids) != len(set(audit_ids)):
            self._append_global_alert("WARNING", "Audit Inconsistency", "Duplicate workflow transfer audit identifier detected.", timestamp_utc, tuple(audit_ids))
        return tuple(self._alerts)

    def _append_alert(self, workflow: dict[str, Any], severity: str, category: str, summary: str, timestamp_utc: str, evidence: tuple[str, ...]) -> None:
        self._append_alert_record(workflow["workflow_id"], severity, category, summary, timestamp_utc, evidence)

    def _append_global_alert(self, severity: str, category: str, summary: str, timestamp_utc: str, evidence: tuple[str, ...]) -> None:
        self._append_alert_record("ENTERPRISE", severity, category, summary, timestamp_utc, evidence)

    def _append_alert_record(self, workflow_id: str, severity: str, category: str, summary: str, timestamp_utc: str, evidence: tuple[str, ...]) -> None:
        signature = (workflow_id, category, tuple(evidence))
        if signature in self._alert_signatures:
            return
        self._alert_signatures.add(signature)
        self._alerts.append(
            WorkflowMonitorAlert(
                alert_id=f"WRM-ALERT-{len(self._alerts) + 1:06d}",
                workflow_id=workflow_id,
                severity=severity,
                category=category,
                summary=summary,
                timestamp_utc=timestamp_utc,
                evidence=tuple(evidence),
            )
        )


def _workflow_view(workflow: dict[str, Any], timeline: list[WorkflowTimelineEvent]) -> dict[str, Any]:
    token = workflow["token"]
    stage_progress = _stage_progress(workflow)
    structured_outputs = len(workflow.get("output_history", ()))
    gateway_outputs = tuple(output for output in workflow.get("output_history", ()) if output.get("api_execution_gateway"))
    elapsed = int(workflow.get("execution_time_seconds", 0))
    average_stage_duration = round(elapsed / max(1, token["transfer_count"] + structured_outputs), 2)
    law_status, law_reason = _law_vii_status(workflow, {})
    stage_number = min(len(workflow["stages"]), int(workflow["current_stage_index"]) + 1)
    display_next_owner = token["next_owner"] or _display_next_owner(workflow)
    completed_at = _event_timestamp(timeline, workflow["workflow_id"], "Workflow Archived") or _event_timestamp(timeline, workflow["workflow_id"], "Workflow Completed")
    commander_status_line, commander_status_detail = _commander_status(workflow)
    return {
        "workflow_id": workflow["workflow_id"],
        "name": workflow["name"],
        "type": workflow.get("workflow_type", "generic"),
        "workflowName": workflow["name"],
        "workflowIdentifier": workflow["workflow_id"],
        "workflowType": workflow.get("workflow_type", "generic"),
        "initialStage": workflow.get("initial_stage", ""),
        "status": token["workflow_status"],
        "priority": _priority(workflow),
        "progress": _progress(stage_progress),
        "workflowStage": token["workflow_stage"],
        "stageNumber": stage_number,
        "stageCount": len(workflow["stages"]),
        "stageLabel": f"Stage {stage_number} of {len(workflow['stages'])}",
        "currentOwner": token["current_owner"],
        "previousOwner": token["previous_owner"],
        "nextOwner": display_next_owner,
        "final_owner": token["previous_owner"] if token["workflow_status"] in COMPLETED_STATUSES else token["current_owner"],
        "elapsedRuntime": elapsed,
        "runtime_seconds": elapsed,
        "estimatedRemainingRuntime": max(0, token["runtime_budget"] - workflow["runtime_used"]),
        "runtimeBudget": token["runtime_budget"],
        "runtimeConsumed": workflow["runtime_used"],
        "creditsConsumed": workflow["credits_used"],
        "credits_consumed": workflow["credits_used"],
        "creditsRemaining": round(max(0.0, token["credit_budget"] - workflow["credits_used"]), 4),
        "transferCount": token["transfer_count"],
        "transfer_count": token["transfer_count"],
        "structuredOutputsProduced": structured_outputs,
        "structured_outputs_produced": structured_outputs,
        "gatewayExecutionCount": len(gateway_outputs),
        "waitingOffices": tuple(stage for stage, status in stage_progress.items() if status == "Waiting"),
        "tokenId": token["audit_identifier"],
        "auditIdentifier": token["audit_identifier"],
        "lawViiStatus": law_status,
        "lawViiViolationReason": law_reason,
        "executionHealth": _execution_health(workflow),
        "execution_health": _execution_health(workflow),
        "completed_at": completed_at,
        "commanderStatusLine": commander_status_line,
        "commanderStatusDetail": commander_status_detail,
        "stageProgress": stage_progress,
        "averageStageDuration": average_stage_duration,
        "totalExecutionDuration": elapsed,
        "timelineEvents": tuple(asdict(event) for event in timeline if event.workflow_id == workflow["workflow_id"]),
    }


def _stage_progress(workflow: dict[str, Any]) -> dict[str, str]:
    status = workflow["token"]["workflow_status"]
    current_index = workflow["current_stage_index"]
    progress: dict[str, str] = {}
    for index, stage in enumerate(workflow["stages"]):
        if index < current_index:
            progress[stage] = "Completed"
        elif index == current_index and status == "Executing":
            progress[stage] = "Executing"
        elif index == current_index and status in {"Structured Output Produced", "Ownership Transferred", "Completed", "Archived"}:
            progress[stage] = "Completed"
        elif index == current_index:
            progress[stage] = "Waiting"
        else:
            progress[stage] = "Waiting"
    return progress


def _progress(stage_progress: dict[str, str]) -> int:
    if not stage_progress:
        return 0
    completed = sum(1 for value in stage_progress.values() if value == "Completed")
    return round((completed / len(stage_progress)) * 100)


def _execution_health(workflow: dict[str, Any]) -> str:
    token = workflow["token"]
    if workflow["runtime_used"] > token["runtime_budget"] or workflow["credits_used"] > token["credit_budget"]:
        return "ATTENTION"
    if workflow["token"]["workflow_status"] in COMPLETED_STATUSES:
        return "COMPLETE"
    return "NOMINAL"


def _baton_view(workflow: dict[str, Any], timeline: list[WorkflowTimelineEvent]) -> dict[str, Any]:
    token = workflow["token"]
    stage_progress = _stage_progress(workflow)
    outputs = tuple(workflow.get("output_history", ()))
    stages = []
    workflow_events = tuple(event for event in timeline if event.workflow_id == workflow["workflow_id"])
    for index, stage in enumerate(workflow["stages"]):
        status = stage_progress.get(stage, "Waiting")
        baton_status = "ACTIVE" if status == "Executing" else status.upper()
        started_at = _event_timestamp(workflow_events, workflow["workflow_id"], "Stage Started", stage=stage)
        completed_at = _event_timestamp(workflow_events, workflow["workflow_id"], "Stage Completed", stage=stage)
        structured_output_id = ""
        if index < len(outputs):
            structured_output_id = outputs[index].get("structured_output_id", f"{workflow['workflow_id']}-OUT-{index + 1:03d}")
        gateway_metadata = outputs[index].get("api_execution_gateway", {}) if index < len(outputs) else {}
        stages.append(
            {
                "stage_name": stage,
                "stage": stage,
                "office": stage,
                "status": baton_status,
                "state": baton_status,
                "started_at": started_at,
                "completed_at": completed_at,
                "structured_output_id": structured_output_id,
                "duration_seconds": _duration_seconds(started_at, completed_at),
                "gateway_used": bool(gateway_metadata),
                "gateway_model": gateway_metadata.get("model", ""),
                "gateway_execution_mode": gateway_metadata.get("execution_mode", ""),
                "gateway_provider": gateway_metadata.get("provider", ""),
                "gateway_validation_status": gateway_metadata.get("validation_status", ""),
                "gateway_fallback_used": bool(gateway_metadata.get("fallback_used", False)),
                "realApiPilot": gateway_metadata.get("execution_mode") == "real_api_pilot" and not gateway_metadata.get("fallback_used", False),
                "isCurrentOwner": stage == token["current_owner"] and token["workflow_status"] in ACTIVE_STATUSES,
                "tokenOwner": token["current_owner"],
            }
        )
    return {
        "workflowName": workflow["name"],
        "workflowIdentifier": workflow["workflow_id"],
        "status": token["workflow_status"],
        "tokenId": token["audit_identifier"],
        "currentOwner": token["current_owner"],
        "previousOwner": token["previous_owner"],
        "nextOwner": token["next_owner"] or _display_next_owner(workflow),
        "transferCount": token["transfer_count"],
        "stages": tuple(stages),
    }


def _token_integrity_panel(workflow: dict[str, Any], orchestrator: dict[str, Any]) -> dict[str, Any]:
    token = workflow["token"]
    law_status, law_reason = _law_vii_status(workflow, orchestrator)
    active_owners = tuple(owner for owner, state in workflow["office_states"].items() if state in {"Assigned", "Executing"})
    return {
        "workflowName": workflow["name"],
        "workflowIdentifier": workflow["workflow_id"],
        "workflow_id": workflow["workflow_id"],
        "tokenId": token["audit_identifier"],
        "token_id": token["audit_identifier"],
        "currentOwner": token["current_owner"],
        "previousOwner": token["previous_owner"],
        "nextOwner": token["next_owner"] or _display_next_owner(workflow),
        "transferCount": token["transfer_count"],
        "currentStage": token["workflow_stage"],
        "validationStatus": workflow["validation_status"],
        "completionState": workflow["completion_state"],
        "lawViiStatus": law_status,
        "lawViiViolationReason": law_reason,
        "status": law_status,
        "violation_code": "" if law_status == "VALID" else "LAW_VII_OWNER_MISMATCH",
        "violation_reason": law_reason,
        "offending_office": ",".join(active_owners),
        "expected_owner": token["current_owner"],
    }


def _law_vii_status(workflow: dict[str, Any], orchestrator: dict[str, Any]) -> tuple[str, str]:
    token = workflow["token"]
    active_owners = tuple(owner for owner, state in workflow["office_states"].items() if state in {"Assigned", "Executing"})
    expected_owners = 1 if token["workflow_status"] in ACTIVE_STATUSES else 0
    if len(active_owners) != expected_owners:
        return "VIOLATION", f"Expected {expected_owners} active owner(s); observed {len(active_owners)}."
    if len(active_owners) == 1 and active_owners[0] != token["current_owner"]:
        return "VIOLATION", "Displayed active owner does not match Workflow Execution Token owner."
    metrics = orchestrator.get("metrics", {})
    if metrics.get("tokenExclusivityViolations", 0):
        return "VIOLATION", "OE-010 reported token exclusivity violations."
    if metrics.get("nonDormantAfterTransferViolations", 0):
        return "VIOLATION", "OE-010 reported non-dormant previous owner after transfer."
    return "VALID", ""


def _global_token_integrity(orchestrator: dict[str, Any], workflows: tuple[dict[str, Any], ...]) -> dict[str, str]:
    metrics = orchestrator.get("metrics", {})
    if metrics.get("tokenExclusivityViolations", 0):
        for workflow in workflows:
            active_owners = tuple(owner for owner, state in workflow["office_states"].items() if state in {"Assigned", "Executing"})
            if len(active_owners) > 1:
                return {
                    "status": "VIOLATION",
                    "violation_code": "LAW_VII_MULTIPLE_ACTIVE_OWNERS",
                    "violation_reason": "More than one office is active for one Workflow Execution Token.",
                    "workflow_id": workflow["workflow_id"],
                    "token_id": workflow["token"]["audit_identifier"],
                    "offending_office": ",".join(active_owners),
                    "expected_owner": workflow["token"]["current_owner"],
                }
    for workflow in workflows:
        law_status, law_reason = _law_vii_status(workflow, orchestrator)
        if law_status == "VIOLATION":
            active_owners = tuple(owner for owner, state in workflow["office_states"].items() if state in {"Assigned", "Executing"})
            return {
                "status": "VIOLATION",
                "violation_code": "LAW_VII_OWNER_MISMATCH",
                "violation_reason": law_reason,
                "workflow_id": workflow["workflow_id"],
                "token_id": workflow["token"]["audit_identifier"],
                "offending_office": ",".join(active_owners),
                "expected_owner": workflow["token"]["current_owner"],
            }
    return {
        "status": "VALID",
        "violation_code": "",
        "violation_reason": "",
        "workflow_id": "",
        "token_id": "",
        "offending_office": "",
        "expected_owner": "",
    }


def _timeline_event_view(event: WorkflowTimelineEvent) -> dict[str, Any]:
    return {
        "timestamp": event.timestamp_utc,
        "timestamp_utc": event.timestamp_utc,
        "workflow_id": event.workflow_id,
        "token_id": event.token_id,
        "stage": event.stage,
        "owner": event.owner,
        "event_type": event.event_type,
        "message": event.message,
        "audit_identifier": event.audit_identifier,
        "transfer_count": event.transfer_count,
        "status": event.status,
    }


def _workflow_by_id(workflows: tuple[dict[str, Any], ...], workflow_id: str) -> dict[str, Any]:
    for workflow in workflows:
        if workflow["workflow_id"] == workflow_id:
            return workflow
    return workflows[-1]


def _display_next_owner(workflow: dict[str, Any]) -> str:
    token = workflow["token"]
    if token["workflow_status"] in COMPLETED_STATUSES:
        return ""
    next_index = int(workflow["current_stage_index"]) + 1
    stages = tuple(workflow["stages"])
    return stages[next_index] if next_index < len(stages) else ""


def _event_timestamp(
    timeline: list[WorkflowTimelineEvent] | tuple[WorkflowTimelineEvent, ...],
    workflow_id: str,
    event_type: str,
    *,
    stage: str | None = None,
) -> str:
    for event in reversed(timeline):
        if event.workflow_id != workflow_id or event.event_type != event_type:
            continue
        if stage is not None and event.stage != stage:
            continue
        return event.timestamp_utc
    return ""


def _duration_seconds(started_at: str, completed_at: str) -> int:
    if not started_at or not completed_at:
        return 0
    try:
        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        complete = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    except ValueError:
        return 0
    return max(0, round((complete - start).total_seconds()))


def _event_message(event_type: str, workflow: dict[str, Any], stage: str, owner: str) -> str:
    if event_type == "Workflow Created":
        return f"{workflow['name']} created."
    if event_type == "Workflow Validated":
        return "Workflow validated."
    if event_type == "Workflow Queued":
        return "Workflow queued."
    if event_type in {"Token Assigned", "Ownership Assigned"}:
        return f"Workflow token assigned to {owner or stage}."
    if event_type in {"Stage Started", "Execution Started"}:
        return _stage_started_message(owner or stage)
    if event_type == "Structured Output Produced":
        return f"{owner or stage} completed structured output."
    if event_type == "Stage Completed":
        return f"{owner or stage} completed workflow stage."
    if event_type in {"Token Transferred", "Ownership Transferred"}:
        return f"Workflow token transferred to {owner or stage}."
    if event_type == "Workflow Completed":
        return "Workflow completed."
    if event_type == "Workflow Archived":
        return "Workflow completed and archived."
    return event_type


def _stage_started_message(stage: str) -> str:
    actions = {
        "Seeker": "Seeker is executing market discovery.",
        "Analyst": "Analyst is executing market analysis.",
        "Risk": "Risk is executing risk review.",
        "Trader": "Trader is executing trade workflow preparation.",
        "Historian": "Historian is executing historical recording.",
    }
    return actions.get(stage, f"{stage} is executing workflow stage.")


def _commander_status(workflow: dict[str, Any]) -> tuple[str, str]:
    token = workflow["token"]
    status = token["workflow_status"]
    current_owner = token["current_owner"]
    previous_owner = token["previous_owner"]
    next_owner = token["next_owner"]
    if status == "Queued":
        return "Workflow queued.", "The workflow is waiting for Workflow Execution Token assignment."
    if status == "Assigned":
        return f"Workflow token assigned to {current_owner}.", f"{current_owner} holds exclusive execution authority."
    if status == "Executing":
        detail = f"Stage {workflow['current_stage_index'] + 1} of {len(workflow['stages'])} is active."
        if previous_owner:
            detail = f"Workflow token transferred from {previous_owner} to {current_owner}. {detail}"
        return _stage_started_message(current_owner), detail
    if status == "Structured Output Produced":
        return f"{current_owner} completed structured output.", "Structured output has been emitted and validated."
    if status == "Ownership Transferred":
        return f"Workflow token transferred from {previous_owner} to {current_owner}.", f"Next owner is {current_owner or next_owner}."
    if status == "Completed":
        return "Workflow completed.", "All stages completed and final structured output was validated."
    if status == "Archived":
        return "Workflow completed and archived.", "The workflow remains visible in recent completed workflow retention."
    return status, "Workflow state is visible in OE-011."


def _priority(workflow: dict[str, Any]) -> str:
    ratio = workflow["credits_used"] / workflow["token"]["credit_budget"] if workflow["token"]["credit_budget"] else 1.0
    if ratio >= 0.9:
        return "Critical"
    if ratio >= 0.65:
        return "Warning"
    return "Normal"


def _enterprise_health(orchestrator: dict[str, Any], workflows: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    active = [workflow for workflow in workflows if workflow["token"]["workflow_status"] in ACTIVE_STATUSES]
    queued = [workflow for workflow in workflows if workflow["token"]["workflow_status"] == "Queued"]
    completed = [workflow for workflow in workflows if workflow["token"]["workflow_status"] in COMPLETED_STATUSES]
    total_runtime = sum(workflow["execution_time_seconds"] for workflow in workflows)
    total_credits = sum(workflow["credits_used"] for workflow in workflows)
    stage_counts = sum(len(workflow["stages"]) for workflow in workflows)
    executing = sum(1 for workflow in workflows for state in workflow["office_states"].values() if state == "Executing")
    dormant = sum(1 for workflow in workflows for state in workflow["office_states"].values() if state == "Dormant")
    return {
        "activeWorkflows": len(active),
        "queuedWorkflows": len(queued),
        "completedWorkflows": len(completed),
        "dormantOffices": dormant,
        "executingOffices": executing,
        "averageWorkflowRuntime": round(total_runtime / max(1, len(workflows)), 2),
        "averageCreditConsumption": round(total_credits / max(1, len(workflows)), 4),
        "averageStageDuration": round(total_runtime / max(1, stage_counts), 2),
        "workflowThroughput": len(completed),
        "enterpriseUtilization": round((executing / max(1, executing + dormant)) * 100, 2),
        "sourceMetrics": orchestrator.get("metrics", {}),
    }


def _initial_events_for_status(status: str) -> tuple[str, ...]:
    order = {
        "Validated": ("Workflow Validated",),
        "Queued": ("Workflow Validated", "Workflow Queued"),
        "Assigned": ("Workflow Validated", "Workflow Queued", "Ownership Assigned"),
        "Executing": ("Workflow Validated", "Workflow Queued", "Ownership Assigned", "Execution Started"),
        "Completed": ("Workflow Validated", "Workflow Queued", "Ownership Assigned", "Execution Started", "Structured Output Produced", "Workflow Completed"),
        "Archived": ("Workflow Validated", "Workflow Queued", "Ownership Assigned", "Execution Started", "Structured Output Produced", "Workflow Completed", "Workflow Archived"),
    }
    return order.get(status, ())


def _event_type_for_status(status: str) -> str:
    mapping = {
        "Created": "Workflow Created",
        "Validated": "Workflow Validated",
        "Queued": "Workflow Queued",
        "Assigned": "Ownership Assigned",
        "Executing": "Execution Started",
        "Structured Output Produced": "Structured Output Produced",
        "Ownership Transferred": "Ownership Transferred",
        "Next Stage": "Next Stage",
        "Completed": "Workflow Completed",
        "Archived": "Workflow Archived",
    }
    return mapping.get(status, status)
