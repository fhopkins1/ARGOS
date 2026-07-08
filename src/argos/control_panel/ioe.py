"""Interactive Organization Explorer for ARGOS."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ExplorerNode:
    """Traceable node in the ARGOS organization explorer."""

    node_id: str
    parent_id: str
    node_type: str
    label: str
    identifier: str
    status: str
    current_activity: str
    dependencies: tuple[str, ...]
    relationships: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    historical_context: tuple[str, ...]
    audit_information: tuple[str, ...]
    organization: str
    office: str
    workflow: str
    case_file_id: str
    priority: str
    asset: str
    timestamp_utc: str


@dataclass(frozen=True)
class ExplorerAction:
    """Commander interaction with an explorer object."""

    action_id: str
    action: str
    node_id: str
    status: str
    timestamp_utc: str


class InteractiveOrganizationExplorer:
    """Construct and navigate a deterministic enterprise hierarchy."""

    def __init__(self) -> None:
        self._bookmarks: list[str] = []
        self._following: list[str] = []
        self._monitored: list[str] = []
        self._actions: list[ExplorerAction] = []

    def snapshot(
        self,
        *,
        ecc: dict[str, Any],
        eab: dict[str, Any],
        cnac: dict[str, Any],
        scheduler: dict[str, Any],
        audit_event_count: int,
        filters: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Return deterministic explorer tree and filtered node set."""
        nodes = _build_nodes(ecc, eab, cnac, scheduler, audit_event_count)
        filtered = tuple(node for node in nodes if _matches(node, filters or {}))
        detections = _detections(nodes)
        return {
            "nodes": tuple(asdict(node) for node in filtered),
            "tree": _tree(filtered),
            "summary": {
                "totalNodes": len(nodes),
                "displayedNodes": len(filtered),
                "bookmarks": len(self._bookmarks),
                "following": len(self._following),
                "monitored": len(self._monitored),
                "brokenRelationships": detections["brokenRelationships"],
                "missingEvidence": detections["missingEvidence"],
                "orphanedObjects": detections["orphanedObjects"],
            },
            "actions": tuple(asdict(action) for action in reversed(self._actions[-20:])),
            "bookmarks": tuple(self._bookmarks),
            "following": tuple(self._following),
            "monitored": tuple(self._monitored),
            "detections": detections,
        }

    def perform_action(self, action: str, node_id: str, timestamp_utc: str) -> ExplorerAction:
        """Execute a deterministic Commander explorer action."""
        if action not in {"inspect", "search", "filter", "bookmark", "follow", "compare", "export", "monitor"}:
            raise ValueError(f"unsupported IOE action: {action}")
        if action == "bookmark" and node_id not in self._bookmarks:
            self._bookmarks.append(node_id)
        if action == "follow" and node_id not in self._following:
            self._following.append(node_id)
        if action == "monitor" and node_id not in self._monitored:
            self._monitored.append(node_id)
        record = ExplorerAction(
            action_id=f"IOE-ACT-{len(self._actions) + 1:06d}",
            action=action,
            node_id=node_id,
            status="COMPLETED",
            timestamp_utc=timestamp_utc,
        )
        self._actions.append(record)
        return record


def _build_nodes(
    ecc: dict[str, Any],
    eab: dict[str, Any],
    cnac: dict[str, Any],
    scheduler: dict[str, Any],
    audit_event_count: int,
) -> tuple[ExplorerNode, ...]:
    nodes: list[ExplorerNode] = [
        ExplorerNode(
            node_id="ENT-ARGOS",
            parent_id="",
            node_type="Enterprise",
            label="ARGOS Deterministic Cognitive Enterprise",
            identifier="ENT-ARGOS",
            status=ecc["enterpriseHealth"],
            current_activity=f"{ecc['tradingStatus']} / {ecc['learningActivity']}",
            dependencies=("Enterprise Activity Bus", "Audit Framework", "Persistence Framework"),
            relationships=("Executive", "Seeker", "Analyst", "Risk", "Trader", "Historian", "Librarian", "Academy", "Infrastructure"),
            supporting_evidence=("EAB", "ECC", "CNAC"),
            historical_context=(f"{len(eab['events'])} enterprise events",),
            audit_information=(f"{audit_event_count} audit events",),
            organization="Enterprise",
            office="",
            workflow="",
            case_file_id="",
            priority="",
            asset="",
            timestamp_utc="",
        )
    ]
    for organization in ecc["organizations"]:
        org_id = f"ORG-{_slug(organization['name'])}"
        nodes.append(
            ExplorerNode(
                node_id=org_id,
                parent_id="ENT-ARGOS",
                node_type="Organization",
                label=organization["name"],
                identifier=org_id,
                status=organization["current_status"],
                current_activity=organization["current_task"],
                dependencies=(organization["current_workflow"],),
                relationships=tuple(workflow["workflow_id"] for workflow in organization["workflows"]),
                supporting_evidence=tuple(organization["recent_activity"][-3:]),
                historical_context=tuple(organization["recent_activity"][-3:]),
                audit_information=tuple(alert for alert in organization["active_alerts"]) or ("No active alerts",),
                organization=organization["name"],
                office="",
                workflow=organization["current_workflow"],
                case_file_id="",
                priority="",
                asset="",
                timestamp_utc="",
            )
        )
        for workflow in organization["workflows"]:
            office = workflow["name"].replace(" Workflow", "")
            office_id = f"OFF-{_slug(organization['name'])}-{_slug(office)}"
            workflow_id = f"WFL-{workflow['workflow_id']}"
            nodes.append(_office_node(office_id, org_id, organization, office, workflow, scheduler))
            nodes.append(_workflow_node(workflow_id, office_id, organization, office, workflow))
            for task in workflow["tasks"]:
                task_id = f"TSK-{task['task_id']}"
                nodes.append(_task_node(task_id, workflow_id, organization, office, workflow, task))
                case_file_id = f"CFNODE-{task['task_id']}"
                evidence_id = f"EVDNODE-{task['task_id']}"
                historical_id = f"HISNODE-{task['task_id']}"
                audit_id = f"AUDNODE-{task['task_id']}"
                nodes.extend(
                    (
                        _leaf_node(case_file_id, task_id, "Case File", task["task_id"], organization["name"], office, workflow["name"], task["historical_record_ids"], task["audit_log_ids"]),
                        _leaf_node(evidence_id, case_file_id, "Evidence", task["supporting_evidence_ids"][0], organization["name"], office, workflow["name"], task["supporting_evidence_ids"], task["audit_log_ids"]),
                        _leaf_node(historical_id, evidence_id, "Historical Record", task["historical_record_ids"][0], organization["name"], office, workflow["name"], task["historical_record_ids"], task["audit_log_ids"]),
                        _leaf_node(audit_id, historical_id, "Audit Trail", task["audit_log_ids"][0], organization["name"], office, workflow["name"], task["supporting_evidence_ids"], task["audit_log_ids"]),
                    )
                )
    for event in eab["events"]:
        event_id = f"EVT-{event['event_id']}"
        nodes.append(
            ExplorerNode(
                node_id=event_id,
                parent_id=f"ORG-{_slug(event['organization'])}" if event["organization"] != "Commander Interface" else "ENT-ARGOS",
                node_type="Historical Event",
                label=event["summary"],
                identifier=event["event_id"],
                status=event["status"],
                current_activity=event["detailed_description"],
                dependencies=(event["correlation_identifier"],),
                relationships=(event["audit_identifier"], event["case_file_id"]),
                supporting_evidence=tuple(event["supporting_evidence"]) or (event["event_id"],),
                historical_context=(event["timestamp_utc"],),
                audit_information=(event["audit_identifier"],),
                organization=event["organization"],
                office=event["office"],
                workflow=event["workflow"],
                case_file_id=event["case_file_id"],
                priority=event["severity"],
                asset=event["asset"],
                timestamp_utc=event["timestamp_utc"],
            )
        )
    for notification in cnac["notifications"]:
        nodes.append(
            ExplorerNode(
                node_id=f"NTF-{notification['notification_id']}",
                parent_id=f"EVT-{notification['source_event_id']}",
                node_type="Notification",
                label=notification["summary"],
                identifier=notification["notification_id"],
                status=notification["status"],
                current_activity=f"{notification['priority']} / {notification['notification_type']}",
                dependencies=(notification["correlation_identifier"],),
                relationships=tuple(notification["related_case_files"]),
                supporting_evidence=tuple(notification["supporting_evidence"]) or (notification["source_event_id"],),
                historical_context=tuple(notification["recommended_actions"]),
                audit_information=(notification["source_event_id"],),
                organization=notification["organization"],
                office=notification["office"],
                workflow=notification["workflow"],
                case_file_id=notification["related_case_files"][0] if notification["related_case_files"] else "",
                priority=notification["priority"],
                asset=notification["asset"],
                timestamp_utc=notification["timestamp_utc"],
            )
        )
    return tuple(nodes)


def _office_node(node_id: str, parent_id: str, organization: dict[str, Any], office: str, workflow: dict[str, Any], scheduler: dict[str, Any]) -> ExplorerNode:
    schedule = next((item for item in scheduler["offices"] if item["organization"] == organization["name"] and item["office"] == office), None)
    return ExplorerNode(
        node_id=node_id,
        parent_id=parent_id,
        node_type="Office",
        label=office,
        identifier=node_id,
        status=schedule["status"] if schedule else organization["current_status"],
        current_activity=f"{schedule['operating_mode']} mode" if schedule else workflow["status"],
        dependencies=(organization["name"],),
        relationships=(workflow["workflow_id"],),
        supporting_evidence=(schedule["schedule_id"],) if schedule else (workflow["workflow_id"],),
        historical_context=(f"Queue {workflow['queue_length']}",),
        audit_information=("Scheduler synchronized",),
        organization=organization["name"],
        office=office,
        workflow=workflow["name"],
        case_file_id="",
        priority="",
        asset="",
        timestamp_utc=schedule["last_transition_utc"] if schedule else "",
    )


def _workflow_node(node_id: str, parent_id: str, organization: dict[str, Any], office: str, workflow: dict[str, Any]) -> ExplorerNode:
    return ExplorerNode(
        node_id=node_id,
        parent_id=parent_id,
        node_type="Workflow",
        label=workflow["name"],
        identifier=workflow["workflow_id"],
        status=workflow["status"],
        current_activity=f"Queue length {workflow['queue_length']}",
        dependencies=(office,),
        relationships=tuple(task["task_id"] for task in workflow["tasks"]),
        supporting_evidence=tuple(task["supporting_evidence_ids"][0] for task in workflow["tasks"]),
        historical_context=tuple(task["historical_record_ids"][0] for task in workflow["tasks"]),
        audit_information=tuple(task["audit_log_ids"][0] for task in workflow["tasks"]),
        organization=organization["name"],
        office=office,
        workflow=workflow["name"],
        case_file_id="",
        priority="",
        asset="",
        timestamp_utc="",
    )


def _task_node(node_id: str, parent_id: str, organization: dict[str, Any], office: str, workflow: dict[str, Any], task: dict[str, Any]) -> ExplorerNode:
    return ExplorerNode(
        node_id=node_id,
        parent_id=parent_id,
        node_type="Task",
        label=task["name"],
        identifier=task["task_id"],
        status=task["status"],
        current_activity=task["name"],
        dependencies=(workflow["workflow_id"],),
        relationships=(f"CFNODE-{task['task_id']}",),
        supporting_evidence=tuple(task["supporting_evidence_ids"]),
        historical_context=tuple(task["historical_record_ids"]),
        audit_information=tuple(task["audit_log_ids"]),
        organization=organization["name"],
        office=office,
        workflow=workflow["name"],
        case_file_id=f"CF-{task['task_id']}",
        priority=task["priority"],
        asset="",
        timestamp_utc="",
    )


def _leaf_node(node_id: str, parent_id: str, node_type: str, label: str, organization: str, office: str, workflow: str, evidence: tuple[str, ...], audit: tuple[str, ...]) -> ExplorerNode:
    return ExplorerNode(
        node_id=node_id,
        parent_id=parent_id,
        node_type=node_type,
        label=label,
        identifier=label,
        status="TRACEABLE",
        current_activity=f"{node_type} reference",
        dependencies=(parent_id,),
        relationships=tuple(audit),
        supporting_evidence=tuple(evidence),
        historical_context=(label,),
        audit_information=tuple(audit),
        organization=organization,
        office=office,
        workflow=workflow,
        case_file_id=label if node_type == "Case File" else "",
        priority="",
        asset="",
        timestamp_utc="",
    )


def _tree(nodes: tuple[ExplorerNode, ...]) -> dict[str, tuple[str, ...]]:
    ids = {node.node_id for node in nodes}
    tree: dict[str, list[str]] = {}
    for node in nodes:
        if node.parent_id and node.parent_id in ids:
            tree.setdefault(node.parent_id, []).append(node.node_id)
        else:
            tree.setdefault("", []).append(node.node_id)
    return {key: tuple(values) for key, values in tree.items()}


def _detections(nodes: tuple[ExplorerNode, ...]) -> dict[str, int]:
    ids = {node.node_id for node in nodes}
    broken = sum(1 for node in nodes if node.parent_id and node.parent_id not in ids)
    missing_evidence = sum(1 for node in nodes if not node.supporting_evidence)
    orphaned = sum(1 for node in nodes if node.node_id != "ENT-ARGOS" and not node.parent_id)
    return {
        "brokenRelationships": broken,
        "missingEvidence": missing_evidence,
        "orphanedObjects": orphaned,
        "navigationErrors": 0,
        "inconsistentHierarchies": broken + orphaned,
    }


def _matches(node: ExplorerNode, filters: dict[str, str]) -> bool:
    normalized = {key: str(value).strip() for key, value in filters.items() if str(value).strip()}
    fields = {
        "organization": node.organization,
        "office": node.office,
        "asset": node.asset,
        "workflow": node.workflow,
        "caseFile": node.case_file_id,
        "case_file": node.case_file_id,
        "case_file_id": node.case_file_id,
        "priority": node.priority,
        "status": node.status,
        "time": node.timestamp_utc,
        "nodeType": node.node_type,
        "node_type": node.node_type,
        "q": f"{node.label} {node.identifier} {node.current_activity}",
    }
    for key, value in normalized.items():
        if key == "q":
            if value.lower() not in fields[key].lower():
                return False
            continue
        if key == "time":
            if value not in node.timestamp_utc:
                return False
            continue
        if fields.get(key, "").lower() != value.lower():
            return False
    return True


def _slug(value: str) -> str:
    return "".join(character if character.isalnum() else "-" for character in value.upper()).strip("-")
