"""Enterprise Command Center model for the local ARGOS dashboard."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.contracts import OperationalContract, ValidationStatus, utc_timestamp
from argos.foundation.identity import generate_case_file_id, generate_document_id, generate_trade_cycle_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType


ORGANIZATION_OFFICES: dict[str, tuple[str, ...]] = {
    "Executive": ("Commander", "Chief of Staff", "Dashboard", "Human Override", "Control Panel"),
    "Seeker": ("Technical", "Fundamental", "Macro", "News", "Options", "Crypto", "Events", "Alternative Data", "Fusion"),
    "Analyst": ("Statistical", "Technical", "Fundamental", "Macro", "Derivatives", "Behavioral", "Risk Interaction", "Review", "Fusion"),
    "Risk": ("Position", "Portfolio", "Liquidity", "Volatility", "Tail", "Bubble", "Recovery", "Fusion", "Readiness"),
    "Trader": ("Execution", "Order Management", "Broker Integration", "Execution Quality", "Position Management", "Monitoring", "Fusion", "Readiness"),
    "Historian": ("Performance", "Hypothesis", "Model Calibration", "Prompt Evaluation", "Decision", "Evidence", "Fusion", "Readiness"),
    "Librarian": ("Institutional Knowledge", "Doctrine", "Specifications", "Knowledge Graph", "Learning Integration", "Fusion", "Readiness"),
    "Academy": ("Framework", "Instruction", "Curriculum", "Assessment", "Case Study", "Finance Tutor", "Fusion", "Readiness"),
    "Infrastructure": ("Runtime", "Persistence", "Audit", "Configuration", "Local Dashboard", "Launcher"),
}


@dataclass(frozen=True)
class EnterpriseTask:
    """Drill-down task visible through the ECC."""

    task_id: str
    name: str
    status: str
    priority: str
    supporting_evidence_ids: tuple[str, ...]
    historical_record_ids: tuple[str, ...]
    audit_log_ids: tuple[str, ...]


@dataclass(frozen=True)
class EnterpriseWorkflow:
    """Deterministic workflow state for an organization."""

    workflow_id: str
    name: str
    status: str
    queue_length: int
    tasks: tuple[EnterpriseTask, ...]


@dataclass
class EnterpriseOrganization:
    """Live operational state for one ARGOS organization."""

    name: str
    current_status: str
    current_task: str
    current_workflow: str
    operating_mode: str
    active_alerts: list[str]
    resource_usage: dict[str, int]
    recent_activity: list[str]
    workflows: tuple[EnterpriseWorkflow, ...]


@dataclass(frozen=True)
class CommanderActionRecord:
    """Immutable visible record for an ECC Commander action."""

    action_id: str
    action: str
    target: str
    status: str
    timestamp_utc: str
    detail: str
    audit_id: str
    document_id: str


class EnterpriseCommandCenter:
    """Aggregate and control live operational state for ARGOS organizations."""

    def __init__(self, audit_service: AuditService, persistence_repository: InMemoryPersistenceRepository) -> None:
        self.audit_service = audit_service
        self.persistence_repository = persistence_repository
        self._organizations = _baseline_organizations()
        self._actions: list[CommanderActionRecord] = []
        self._activity: list[dict[str, str]] = []

    def snapshot(
        self,
        *,
        control: dict[str, Any],
        resources: dict[str, int],
        activity: tuple[dict[str, str], ...],
        commands: tuple[dict[str, str], ...],
        costs: dict[str, Any],
    ) -> dict[str, Any]:
        """Return the complete ECC state used by the user control panel."""
        self._synchronize_dynamic_state(control, resources, commands, costs)
        organizations = tuple(asdict(org) for org in self._organizations.values())
        activity_stream = tuple(self._activity[-8:] + list(activity[:12]))
        alerts = _enterprise_alerts(self._organizations)
        return {
            "enterpriseHealth": "NOMINAL" if not alerts else "ATTENTION",
            "tradingStatus": "PAPER ACTIVE" if control["paper_trading_active"] else "STANDBY",
            "paperPortfolioStatus": "ACTIVE" if control["paper_trading_active"] else "INACTIVE",
            "livePortfolioStatus": "BLOCKED" if control["real_world_trading_blocked"] else "ARMED",
            "learningActivity": "SELF-TRAINING" if control["paper_trading_active"] else "READY",
            "knowledgeGrowth": "CONTINUOUS",
            "organizations": organizations,
            "activityStream": activity_stream,
            "commanderActions": tuple(asdict(action) for action in reversed(self._actions[-20:])),
            "alerts": alerts,
            "monitoring": _monitoring_snapshot(self._organizations, resources, alerts),
            "drilldown": _drilldown_tree(self._organizations),
        }

    def perform_action(self, action: str, target: str, detail: str = "") -> CommanderActionRecord:
        """Execute an audited Commander action against the ECC model."""
        if target not in self._organizations:
            raise ValueError(f"unknown ECC organization target: {target}")
        if action not in {
            "pause_organization",
            "resume_organization",
            "change_operating_mode",
            "configure_schedule",
            "review_evidence",
            "inspect_workflows",
            "view_historical_activity",
            "export_reports",
        }:
            raise ValueError(f"unsupported ECC Commander action: {action}")

        organization = self._organizations[target]
        status = "COMPLETED"
        readable = action.replace("_", " ").title()
        if action == "pause_organization":
            organization.current_status = "PAUSED"
            organization.operating_mode = "PAUSED"
            organization.active_alerts.append("Commander pause active")
        elif action == "resume_organization":
            organization.current_status = "NOMINAL"
            organization.operating_mode = "ACTIVE"
            organization.active_alerts = [alert for alert in organization.active_alerts if alert != "Commander pause active"]
        elif action == "change_operating_mode":
            organization.operating_mode = detail.strip().upper() or "ACTIVE"
        elif action == "configure_schedule":
            organization.recent_activity.append(f"Schedule configured: {detail or 'standard cadence'}")
        elif action == "review_evidence":
            organization.current_task = "Commander evidence review"
        elif action == "inspect_workflows":
            organization.current_task = "Commander workflow inspection"
        elif action == "view_historical_activity":
            organization.current_task = "Historical activity review"
        elif action == "export_reports":
            organization.current_task = "Commander report export"

        contract = _action_contract(len(self._actions) + 1, action, target, detail, status)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        event = self.audit_service.record_staff_decision(
            contract,
            "STF-001",
            "DEP-002",
            action.upper(),
            f"ECC Commander action for {target}: {detail or readable}",
        )
        record = CommanderActionRecord(
            action_id=f"ECC-{len(self._actions) + 1:06d}",
            action=action,
            target=target,
            status=status,
            timestamp_utc=contract.created_timestamp_utc,
            detail=detail or readable,
            audit_id=event.event_id,
            document_id=contract.contract_id,
        )
        self._actions.append(record)
        self._activity.append(
            {
                "time": contract.created_timestamp_utc,
                "group": "ECC",
                "message": f"{readable} issued for {target}",
                "reference": record.action_id,
                "status": status,
            }
        )
        return record

    def export_report(self) -> dict[str, Any]:
        """Return a deterministic command-center report payload."""
        generated_at = utc_timestamp()
        return {
            "reportId": f"ECC-REPORT-{len(self._actions) + 1:06d}",
            "generatedAtUtc": generated_at,
            "organizations": tuple(self._organizations.keys()),
            "pausedOrganizations": tuple(org.name for org in self._organizations.values() if org.current_status == "PAUSED"),
            "commanderActionCount": len(self._actions),
            "auditEventCount": len(self.audit_service.audit_log.events),
        }

    def _synchronize_dynamic_state(
        self,
        control: dict[str, Any],
        resources: dict[str, int],
        commands: tuple[dict[str, str], ...],
        costs: dict[str, Any],
    ) -> None:
        trader = self._organizations["Trader"]
        trader.current_status = "ACTIVE" if control["paper_trading_active"] else "NOMINAL"
        trader.current_task = "Paper self-training execution" if control["paper_trading_active"] else "Execution standby"
        trader.current_workflow = "Paper Trading Workflow" if control["paper_trading_active"] else "Execution Readiness"
        trader.operating_mode = "PAPER_TRADING" if control["paper_trading_active"] else trader.operating_mode
        trader.resource_usage["api_credit_burn"] = min(100, int(float(costs["total_operating_burn_usd"])))

        infrastructure = self._organizations["Infrastructure"]
        infrastructure.resource_usage = dict(resources)
        infrastructure.current_task = "Serving ARGOS Control Panel"
        if commands:
            latest = commands[0]
            target = latest.get("target", "Enterprise")
            if target in self._organizations:
                self._organizations[target].recent_activity.append(f"Command {latest.get('action', 'unknown')} acknowledged")


def _baseline_organizations() -> dict[str, EnterpriseOrganization]:
    return {
        name: EnterpriseOrganization(
            name=name,
            current_status="NOMINAL",
            current_task=_current_task(name),
            current_workflow=_current_workflow(name),
            operating_mode="ACTIVE",
            active_alerts=[],
            resource_usage={"cpu": 12 + index * 3, "memory": 24 + index * 2, "queue": index % 4},
            recent_activity=[f"{name} readiness heartbeat confirmed"],
            workflows=_workflows(name, index),
        )
        for index, name in enumerate(ORGANIZATION_OFFICES, start=1)
    }


def _workflows(name: str, organization_index: int) -> tuple[EnterpriseWorkflow, ...]:
    offices = ORGANIZATION_OFFICES[name]
    workflows: list[EnterpriseWorkflow] = []
    for workflow_index, office in enumerate(offices[:3], start=1):
        tasks = tuple(
            EnterpriseTask(
                task_id=f"TASK-{organization_index:02d}{workflow_index:02d}{task_index:02d}",
                name=f"{office} {label}",
                status="ACTIVE" if task_index == 1 else "QUEUED",
                priority="HIGH" if workflow_index == 1 else "NORMAL",
                supporting_evidence_ids=(f"EVD-{organization_index:02d}{workflow_index:02d}{task_index:02d}",),
                historical_record_ids=(f"HIS-{organization_index:02d}{workflow_index:02d}{task_index:02d}",),
                audit_log_ids=(f"AE-REF-{organization_index:02d}{workflow_index:02d}{task_index:02d}",),
            )
            for task_index, label in enumerate(("monitoring", "validation"), start=1)
        )
        workflows.append(
            EnterpriseWorkflow(
                workflow_id=f"WF-{organization_index:02d}{workflow_index:02d}",
                name=f"{office} Workflow",
                status="ACTIVE",
                queue_length=workflow_index + organization_index % 3,
                tasks=tasks,
            )
        )
    return tuple(workflows)


def _current_task(name: str) -> str:
    tasks = {
        "Executive": "Decision queue supervision",
        "Seeker": "Opportunity intelligence monitoring",
        "Analyst": "Reasoning chain validation",
        "Risk": "Organizational risk assessment",
        "Trader": "Execution standby",
        "Historian": "Performance evidence evaluation",
        "Librarian": "Knowledge repository governance",
        "Academy": "Personalized learning orchestration",
        "Infrastructure": "Control panel runtime",
    }
    return tasks[name]


def _current_workflow(name: str) -> str:
    return {
        "Executive": "Executive Briefing Workflow",
        "Seeker": "Multi-Office Intelligence Workflow",
        "Analyst": "Analytical Fusion Workflow",
        "Risk": "Risk Fusion Workflow",
        "Trader": "Execution Readiness",
        "Historian": "Historical Learning Workflow",
        "Librarian": "Doctrine Governance Workflow",
        "Academy": "Adaptive Education Workflow",
        "Infrastructure": "Local Runtime Workflow",
    }[name]


def _drilldown_tree(organizations: dict[str, EnterpriseOrganization]) -> dict[str, Any]:
    return {
        org.name: {
            "organization": org.name,
            "offices": tuple(
                {
                    "office": office,
                    "workflows": tuple(asdict(workflow) for workflow in org.workflows if workflow.name.startswith(office)),
                }
                for office in ORGANIZATION_OFFICES[org.name]
            ),
            "auditReferences": tuple(audit_id for workflow in org.workflows for task in workflow.tasks for audit_id in task.audit_log_ids),
        }
        for org in organizations.values()
    }


def _enterprise_alerts(organizations: dict[str, EnterpriseOrganization]) -> tuple[dict[str, str], ...]:
    alerts: list[dict[str, str]] = []
    for organization in organizations.values():
        for alert in organization.active_alerts:
            alerts.append({"severity": "WARNING", "organization": organization.name, "message": alert})
        if any(workflow.queue_length >= 6 for workflow in organization.workflows):
            alerts.append({"severity": "NOTICE", "organization": organization.name, "message": "Queue congestion watch"})
    return tuple(alerts)


def _monitoring_snapshot(
    organizations: dict[str, EnterpriseOrganization],
    resources: dict[str, int],
    alerts: tuple[dict[str, str], ...],
) -> dict[str, Any]:
    total_queue = sum(workflow.queue_length for org in organizations.values() for workflow in org.workflows)
    paused = sum(1 for org in organizations.values() if org.current_status == "PAUSED")
    return {
        "workflowDeadlocks": 0,
        "unresponsiveOrganizations": paused,
        "queueCongestion": total_queue,
        "infrastructureFailures": 0 if max(resources.values()) < 90 else 1,
        "operationalDrift": 0,
        "communicationFailures": 0,
        "activeAlerts": len(alerts),
    }


def _action_contract(sequence: int, action: str, target: str, detail: str, status: str) -> OperationalContract:
    timestamp = utc_timestamp()
    payload = {
        "action": action,
        "target": target,
        "detail": detail,
        "status": status,
        "permanent_audit_required": True,
    }
    return OperationalContract(
        contract_id=generate_document_id(9800 + sequence),
        contract_type="ECC_COMMANDER_ACTION",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=generate_case_file_id(9800 + sequence),
        trade_cycle_id=generate_trade_cycle_id(9800 + sequence),
        parent_contract_ids=(),
        produced_by_staff_id="STF-001",
        produced_by_group_id="DEP-002",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=timestamp,
        updated_timestamp_utc=timestamp,
        validation_status=ValidationStatus.VALID,
        validation_errors=(),
        human_summary=f"ECC Commander action {action} for {target}.",
        machine_payload=payload,
        signature_hash=sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest(),
        source_reference_ids=(),
    )
