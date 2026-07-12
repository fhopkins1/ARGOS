"""Enterprise Workflow Orchestrator for ARGOS OE-010."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from typing import Any

from argos.foundation.contracts import utc_timestamp


class WorkflowStatus(str, Enum):
    """Deterministic workflow lifecycle states."""

    CREATED = "Created"
    VALIDATED = "Validated"
    QUEUED = "Queued"
    ASSIGNED = "Assigned"
    EXECUTING = "Executing"
    STRUCTURED_OUTPUT_PRODUCED = "Structured Output Produced"
    OWNERSHIP_TRANSFERRED = "Ownership Transferred"
    NEXT_STAGE = "Next Stage"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


LIFECYCLE = tuple(status.value for status in WorkflowStatus)


@dataclass(frozen=True)
class WorkflowExecutionToken:
    """Exclusive workflow execution authority."""

    workflow_id: str
    current_owner: str
    previous_owner: str
    next_owner: str
    workflow_stage: str
    runtime_budget: int
    credit_budget: float
    expected_output_schema: tuple[str, ...]
    audit_identifier: str
    creation_timestamp: str
    transfer_count: int
    workflow_status: str


@dataclass(frozen=True)
class WorkflowRecord:
    """Workflow owned work package."""

    workflow_id: str
    name: str
    workflow_type: str
    initial_stage: str
    stages: tuple[str, ...]
    current_stage_index: int
    queue_position: int
    retry_count: int
    runtime_used: int
    credits_used: float
    token_usage: int
    execution_time_seconds: int
    latest_output: dict[str, Any]
    output_history: tuple[dict[str, Any], ...]
    validation_status: str
    completion_state: str
    office_states: dict[str, str]
    token: WorkflowExecutionToken


@dataclass(frozen=True)
class OwnershipTransferAudit:
    """Immutable ownership-transfer audit record."""

    audit_id: str
    timestamp: str
    workflow_id: str
    previous_owner: str
    current_owner: str
    next_owner: str
    runtime: int
    credits: float
    validation_status: str
    completion_state: str
    transfer_reason: str


class EnterpriseWorkflowOrchestrator:
    """Deterministic workflow execution engine."""

    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowRecord] = {}
        self._queue: list[str] = []
        self._audit_history: list[OwnershipTransferAudit] = []

    def create_workflow(
        self,
        *,
        name: str,
        stages: tuple[str, ...],
        runtime_budget: int,
        credit_budget: float,
        expected_output_schema: tuple[str, ...],
        workflow_type: str = "generic",
        initial_stage: str = "",
    ) -> WorkflowRecord:
        """Create a workflow and its one execution token."""
        if not stages:
            raise ValueError("workflow requires at least one stage")
        workflow_id = f"EWO-WF-{len(self._workflows) + 1:06d}"
        timestamp = utc_timestamp()
        token = WorkflowExecutionToken(
            workflow_id=workflow_id,
            current_owner="",
            previous_owner="",
            next_owner=stages[0],
            workflow_stage=stages[0],
            runtime_budget=max(1, int(runtime_budget)),
            credit_budget=round(max(0.0, float(credit_budget)), 4),
            expected_output_schema=tuple(expected_output_schema),
            audit_identifier=f"AE-EWO-{len(self._audit_history) + 1:06d}",
            creation_timestamp=timestamp,
            transfer_count=0,
            workflow_status=WorkflowStatus.CREATED.value,
        )
        record = WorkflowRecord(
            workflow_id=workflow_id,
            name=name,
            workflow_type=workflow_type,
            initial_stage=initial_stage,
            stages=tuple(stages),
            current_stage_index=0,
            queue_position=0,
            retry_count=0,
            runtime_used=0,
            credits_used=0.0,
            token_usage=0,
            execution_time_seconds=0,
            latest_output={},
            output_history=(),
            validation_status="PENDING",
            completion_state="OPEN",
            office_states={stage: "Dormant" for stage in stages},
            token=token,
        )
        self._workflows[workflow_id] = record
        return record

    def validate_workflow(self, workflow_id: str) -> WorkflowRecord:
        """Validate workflow definition without skipping lifecycle."""
        workflow = self._workflow(workflow_id)
        self._require_status(workflow, WorkflowStatus.CREATED)
        if not workflow.token.expected_output_schema:
            raise ValueError("workflow requires an expected output schema")
        return self._update(workflow, token=replace(workflow.token, workflow_status=WorkflowStatus.VALIDATED.value), validation_status="VALIDATED")

    def queue_workflow(self, workflow_id: str) -> WorkflowRecord:
        """Queue a validated workflow."""
        workflow = self._workflow(workflow_id)
        self._require_status(workflow, WorkflowStatus.VALIDATED)
        if workflow_id not in self._queue:
            self._queue.append(workflow_id)
        return self._update(workflow, token=replace(workflow.token, workflow_status=WorkflowStatus.QUEUED.value), queue_position=self._queue.index(workflow_id) + 1)

    def assign_next(self) -> WorkflowRecord:
        """Assign the next queued workflow token to its next owner."""
        if not self._queue:
            raise ValueError("workflow queue is empty")
        workflow_id = self._queue.pop(0)
        workflow = self._workflow(workflow_id)
        self._require_status(workflow, WorkflowStatus.QUEUED)
        owner = workflow.token.next_owner
        token = replace(workflow.token, current_owner=owner, next_owner="", workflow_status=WorkflowStatus.ASSIGNED.value)
        office_states = {key: ("Assigned" if key == owner else "Dormant") for key in workflow.office_states}
        return self._update(workflow, token=token, queue_position=0, office_states=office_states)

    def start_execution(self, workflow_id: str) -> WorkflowRecord:
        """Move assigned owner into executing state only when budgets exist."""
        workflow = self._workflow(workflow_id)
        self._require_status(workflow, WorkflowStatus.ASSIGNED)
        if workflow.token.runtime_budget <= workflow.runtime_used:
            raise ValueError("runtime budget exceeded")
        if workflow.token.credit_budget <= workflow.credits_used:
            raise ValueError("credit budget exceeded")
        owner = workflow.token.current_owner
        office_states = {key: ("Executing" if key == owner else "Dormant") for key in workflow.office_states}
        return self._update(workflow, token=replace(workflow.token, workflow_status=WorkflowStatus.EXECUTING.value), office_states=office_states)

    def produce_structured_output(
        self,
        workflow_id: str,
        output: dict[str, Any],
        *,
        runtime: int,
        credits: float,
        token_usage: int,
        execution_time_seconds: int,
    ) -> WorkflowRecord:
        """Validate structured output, enforce budgets, and mark output produced."""
        workflow = self._workflow(workflow_id)
        self._require_status(workflow, WorkflowStatus.EXECUTING)
        runtime_used = workflow.runtime_used + max(0, int(runtime))
        credits_used = round(workflow.credits_used + max(0.0, float(credits)), 4)
        token_total = workflow.token_usage + max(0, int(token_usage))
        execution_total = workflow.execution_time_seconds + max(0, int(execution_time_seconds))
        if runtime_used > workflow.token.runtime_budget:
            raise ValueError("runtime limit exceeded")
        if credits_used > workflow.token.credit_budget:
            raise ValueError("credit limit exceeded")
        missing = tuple(field for field in workflow.token.expected_output_schema if field not in output)
        validation_status = "VALID" if not missing else f"INVALID_MISSING_{','.join(missing)}"
        if missing:
            raise ValueError(validation_status)
        return self._update(
            workflow,
            token=replace(workflow.token, workflow_status=WorkflowStatus.STRUCTURED_OUTPUT_PRODUCED.value),
            latest_output=dict(output),
            output_history=(*workflow.output_history, dict(output)),
            validation_status=validation_status,
            runtime_used=runtime_used,
            credits_used=credits_used,
            token_usage=token_total,
            execution_time_seconds=execution_total,
        )

    def transfer_ownership(self, workflow_id: str, reason: str = "Structured output validated") -> WorkflowRecord:
        """Transfer exclusive token ownership after validated structured output."""
        workflow = self._workflow(workflow_id)
        self._require_status(workflow, WorkflowStatus.STRUCTURED_OUTPUT_PRODUCED)
        previous_owner = workflow.token.current_owner
        next_index = workflow.current_stage_index + 1
        next_owner = workflow.stages[next_index] if next_index < len(workflow.stages) else ""
        transfer_status = WorkflowStatus.COMPLETED.value if not next_owner else WorkflowStatus.OWNERSHIP_TRANSFERRED.value
        token = replace(
            workflow.token,
            previous_owner=previous_owner,
            current_owner=next_owner,
            next_owner="",
            workflow_stage=next_owner or workflow.token.workflow_stage,
            transfer_count=workflow.token.transfer_count + 1,
            workflow_status=transfer_status,
        )
        office_states = {key: ("Assigned" if key == next_owner else "Dormant") for key in workflow.office_states}
        audit = OwnershipTransferAudit(
            audit_id=f"EWO-AUD-{len(self._audit_history) + 1:06d}",
            timestamp=utc_timestamp(),
            workflow_id=workflow.workflow_id,
            previous_owner=previous_owner,
            current_owner=next_owner,
            next_owner=workflow.stages[next_index + 1] if next_index + 1 < len(workflow.stages) else "",
            runtime=workflow.runtime_used,
            credits=workflow.credits_used,
            validation_status=workflow.validation_status,
            completion_state="COMPLETED" if not next_owner else "TRANSFERRED",
            transfer_reason=reason,
        )
        self._audit_history.append(audit)
        completion_state = "COMPLETED" if not next_owner else "IN_PROGRESS"
        return self._update(
            workflow,
            token=token,
            current_stage_index=next_index if next_owner else workflow.current_stage_index,
            completion_state=completion_state,
            office_states=office_states,
        )

    def advance_next_stage(self, workflow_id: str) -> WorkflowRecord:
        """Move transferred token into the next-stage lifecycle gate."""
        workflow = self._workflow(workflow_id)
        self._require_status(workflow, WorkflowStatus.OWNERSHIP_TRANSFERRED)
        return self._update(workflow, token=replace(workflow.token, workflow_status=WorkflowStatus.NEXT_STAGE.value))

    def assign_transferred_stage(self, workflow_id: str) -> WorkflowRecord:
        """Assign a token already held by the next stage after Next Stage gate."""
        workflow = self._workflow(workflow_id)
        self._require_status(workflow, WorkflowStatus.NEXT_STAGE)
        owner = workflow.token.current_owner
        office_states = {key: ("Assigned" if key == owner else "Dormant") for key in workflow.office_states}
        return self._update(workflow, token=replace(workflow.token, workflow_status=WorkflowStatus.ASSIGNED.value), office_states=office_states)

    def archive_workflow(self, workflow_id: str) -> WorkflowRecord:
        """Archive a completed workflow."""
        workflow = self._workflow(workflow_id)
        self._require_status(workflow, WorkflowStatus.COMPLETED)
        office_states = {key: "Dormant" for key in workflow.office_states}
        return self._update(
            workflow,
            token=replace(workflow.token, current_owner="", next_owner="", workflow_status=WorkflowStatus.ARCHIVED.value),
            completion_state="ARCHIVED",
            office_states=office_states,
        )

    def create_validate_queue_assign(
        self,
        *,
        name: str,
        stages: tuple[str, ...],
        runtime_budget: int,
        credit_budget: float,
        expected_output_schema: tuple[str, ...],
        workflow_type: str = "generic",
        initial_stage: str = "",
    ) -> WorkflowRecord:
        """Convenience path used by the control panel."""
        workflow = self.create_workflow(
            name=name,
            stages=stages,
            runtime_budget=runtime_budget,
            credit_budget=credit_budget,
            expected_output_schema=expected_output_schema,
            workflow_type=workflow_type,
            initial_stage=initial_stage,
        )
        self.validate_workflow(workflow.workflow_id)
        self.queue_workflow(workflow.workflow_id)
        return self.assign_next()

    def snapshot(self) -> dict[str, Any]:
        """Return orchestrator state."""
        workflow_records = tuple(self._workflows.values())
        audit_records = tuple(self._audit_history)
        workflows = tuple(asdict(item) for item in workflow_records)
        active = tuple(item for item in workflows if item["token"]["workflow_status"] not in {WorkflowStatus.ARCHIVED.value, WorkflowStatus.COMPLETED.value})
        return {
            "law": "Enterprise Law VII",
            "workflowCentricExecution": True,
            "dormantByDefault": True,
            "lifecycle": LIFECYCLE,
            "queue": tuple(self._queue),
            "workflows": workflows,
            "activeWorkflows": active,
            "auditHistory": tuple(asdict(item) for item in audit_records),
            "metrics": {
                "workflowCount": len(workflow_records),
                "activeWorkflowCount": len(active),
                "queuedWorkflowCount": len(self._queue),
                "transferCount": len(audit_records),
                "tokenExclusivityViolations": self._token_exclusivity_violations(),
                "nonDormantAfterTransferViolations": self._non_dormant_after_transfer_violations(),
            },
        }

    def recover_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Recover workflows and Workflow Execution Tokens from authoritative persistence."""
        workflows: dict[str, WorkflowRecord] = {}
        queue = list(snapshot.get("queue", ()) or ())
        audits = tuple(OwnershipTransferAudit(**item) for item in snapshot.get("auditHistory", ()) or ())
        for item in snapshot.get("workflows", ()) or ():
            token_payload = dict(item.get("token", {}))
            token = WorkflowExecutionToken(
                workflow_id=str(token_payload.get("workflow_id", "")),
                current_owner=str(token_payload.get("current_owner", "")),
                previous_owner=str(token_payload.get("previous_owner", "")),
                next_owner=str(token_payload.get("next_owner", "")),
                workflow_stage=str(token_payload.get("workflow_stage", "")),
                runtime_budget=int(token_payload.get("runtime_budget", 0) or 0),
                credit_budget=float(token_payload.get("credit_budget", 0.0) or 0.0),
                expected_output_schema=tuple(token_payload.get("expected_output_schema", ()) or ()),
                audit_identifier=str(token_payload.get("audit_identifier", "")),
                creation_timestamp=str(token_payload.get("creation_timestamp", "")),
                transfer_count=int(token_payload.get("transfer_count", 0) or 0),
                workflow_status=str(token_payload.get("workflow_status", "")),
            )
            if token.workflow_id != item.get("workflow_id"):
                raise ValueError("workflow token references a different workflow")
            record = WorkflowRecord(
                workflow_id=str(item.get("workflow_id", "")),
                name=str(item.get("name", "")),
                workflow_type=str(item.get("workflow_type", "")),
                initial_stage=str(item.get("initial_stage", "")),
                stages=tuple(item.get("stages", ()) or ()),
                current_stage_index=int(item.get("current_stage_index", 0) or 0),
                queue_position=int(item.get("queue_position", 0) or 0),
                retry_count=int(item.get("retry_count", 0) or 0),
                runtime_used=int(item.get("runtime_used", 0) or 0),
                credits_used=float(item.get("credits_used", 0.0) or 0.0),
                token_usage=int(item.get("token_usage", 0) or 0),
                execution_time_seconds=int(item.get("execution_time_seconds", 0) or 0),
                latest_output=dict(item.get("latest_output", {}) or {}),
                output_history=tuple(item.get("output_history", ()) or ()),
                validation_status=str(item.get("validation_status", "")),
                completion_state=str(item.get("completion_state", "")),
                office_states=dict(item.get("office_states", {}) or {}),
                token=token,
            )
            if record.workflow_id in workflows:
                raise ValueError(f"duplicate recovered workflow: {record.workflow_id}")
            workflows[record.workflow_id] = record
        active_token_owners = [(record.workflow_id, record.token.current_owner) for record in workflows.values() if record.token.current_owner and record.token.workflow_status not in {WorkflowStatus.COMPLETED.value, WorkflowStatus.ARCHIVED.value}]
        if len(active_token_owners) != len({workflow_id for workflow_id, _ in active_token_owners}):
            raise ValueError("duplicate workflow token ownership detected during recovery")
        missing_queue = [workflow_id for workflow_id in queue if workflow_id not in workflows]
        if missing_queue:
            raise ValueError("workflow queue references unknown workflow")
        self._workflows = workflows
        self._queue = queue
        self._audit_history = list(audits)

    def workflow(self, workflow_id: str) -> WorkflowRecord:
        """Return one workflow record without exposing mutable storage."""
        return self._workflow(workflow_id)

    def validate_api_usage(self, workflow_id: str, workflow_token_id: str, office: str, credit_amount: float) -> tuple[bool, str, str]:
        """Validate that one office may record token-scoped API usage."""
        if not workflow_id or not workflow_token_id or not office:
            return False, "LAW_VII_VIOLATION_UNSCOPED_API_USAGE", "API usage requires workflow_id, workflow_token_id, and office."
        workflow = self._workflows.get(workflow_id)
        if workflow is None or workflow.token.audit_identifier != workflow_token_id:
            return False, "LAW_VII_VIOLATION_UNSCOPED_API_USAGE", "API usage referenced an unknown workflow or token."
        if workflow.token.workflow_status != WorkflowStatus.EXECUTING.value:
            return False, "LAW_VII_VIOLATION_WORKFLOW_NOT_EXECUTING", f"Workflow {workflow_id} is {workflow.token.workflow_status}, not Executing."
        if workflow.token.current_owner != office:
            return False, "LAW_VII_VIOLATION_NON_OWNER_API_USAGE", f"{office} is not the current Workflow Execution Token owner."
        if workflow.credits_used + max(0.0, float(credit_amount)) > workflow.token.credit_budget:
            return False, "LAW_VII_VIOLATION_BUDGET_EXCEEDED", f"Workflow {workflow_id} credit budget would be exceeded."
        return True, "LAW_VII_API_USAGE_AUTHORIZED", "Workflow token owner may record API usage."

    def _workflow(self, workflow_id: str) -> WorkflowRecord:
        if workflow_id not in self._workflows:
            raise ValueError(f"unknown workflow: {workflow_id}")
        return self._workflows[workflow_id]

    def _update(self, workflow: WorkflowRecord, **changes: Any) -> WorkflowRecord:
        updated = replace(workflow, **changes)
        self._workflows[workflow.workflow_id] = updated
        return updated

    def _require_status(self, workflow: WorkflowRecord, status: WorkflowStatus) -> None:
        if workflow.token.workflow_status != status.value:
            raise ValueError(f"workflow {workflow.workflow_id} must be {status.value}; currently {workflow.token.workflow_status}")

    def _token_exclusivity_violations(self) -> int:
        violations = 0
        for workflow in tuple(self._workflows.values()):
            active_owners = [owner for owner, state in workflow.office_states.items() if state in {"Assigned", "Executing"}]
            if len(active_owners) > 1:
                violations += 1
        return violations

    def _non_dormant_after_transfer_violations(self) -> int:
        violations = 0
        workflows = dict(self._workflows)
        for audit in tuple(self._audit_history):
            workflow = workflows[audit.workflow_id]
            if workflow.office_states.get(audit.previous_owner) != "Dormant":
                violations += 1
        return violations
