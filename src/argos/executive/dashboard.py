"""Executive Dashboard read-only projections."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from argos.foundation.audit import AuditEventType, AuditService
from argos.foundation.contracts import BaseContract
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType

from .chief_of_staff import ChiefOfStaffService
from .commander import CommanderOffice


@dataclass(frozen=True)
class DashboardValue:
    """Traceable dashboard display value."""

    name: str
    value: Any
    source: str


@dataclass(frozen=True)
class CommandTableRow:
    """Rendered Command Table row."""

    decision_id: str
    decision_type: str
    status: str
    cdr_contract_id: str | None
    source: str


@dataclass(frozen=True)
class ExecutiveMetrics:
    """Executive metrics projection."""

    queue_depth: int
    decision_throughput: int
    utilization: float
    source: str


@dataclass(frozen=True)
class OrganizationalHealth:
    """Executive organizational health projection."""

    status: str
    reasons: tuple[str, ...]
    source: str


@dataclass(frozen=True)
class ExecutiveDashboardSnapshot:
    """Dashboard snapshot produced by refresh."""

    refresh_sequence: int
    executive_clock: DashboardValue
    pending_packets: tuple[DashboardValue, ...]
    rejected_packets: tuple[DashboardValue, ...]
    recent_decisions: tuple[DashboardValue, ...]
    executive_queue: tuple[DashboardValue, ...]
    commander_queue: tuple[DashboardValue, ...]
    chief_of_staff_queue: tuple[DashboardValue, ...]
    command_table: tuple[CommandTableRow, ...]
    metrics: ExecutiveMetrics
    health: OrganizationalHealth


class ExecutiveDashboard:
    """Read-only Executive Dashboard connected to existing services."""

    def __init__(
        self,
        commander_office: CommanderOffice,
        chief_of_staff_service: ChiefOfStaffService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
    ) -> None:
        self.commander_office = commander_office
        self.chief_of_staff_service = chief_of_staff_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self._refresh_sequence = 0
        self._last_snapshot: ExecutiveDashboardSnapshot | None = None

    def refresh(self) -> ExecutiveDashboardSnapshot:
        """Refresh dashboard projections from existing deterministic records."""
        self._refresh_sequence += 1
        snapshot = ExecutiveDashboardSnapshot(
            refresh_sequence=self._refresh_sequence,
            executive_clock=DashboardValue(
                "executive_clock",
                self.chief_of_staff_service.clock.current_tick,
                "chief_of_staff.clock.current_tick",
            ),
            pending_packets=self._packet_values("validated"),
            rejected_packets=self._packet_values("rejected"),
            recent_decisions=self._recent_decisions(),
            executive_queue=self._queue_values("executive"),
            commander_queue=self._queue_values("commander"),
            chief_of_staff_queue=self._queue_values("chief_of_staff"),
            command_table=self.render_command_table(),
            metrics=self._metrics(),
            health=self._health(),
        )
        self._last_snapshot = snapshot
        self._audit_interaction("dashboard_refresh", f"refresh={self._refresh_sequence}")
        return snapshot

    def auto_refresh(self, cycles: int = 1) -> ExecutiveDashboardSnapshot:
        """Run deterministic automatic refresh cycles."""
        if cycles < 1:
            raise ValueError("cycles must be at least 1")
        snapshot = None
        for _ in range(cycles):
            snapshot = self.refresh()
        return snapshot

    def render_command_table(
        self,
        status_filter: str | None = None,
        sort_by: str = "decision_id",
    ) -> tuple[CommandTableRow, ...]:
        """Render Command Table from Decision Registry."""
        rows = []
        cdr_records = self.persistence_repository.all_records()
        cdr_by_decision = {
            record.payload.get("machine_payload", {}).get("decision_id"): record.object_id
            for record in cdr_records
            if record.object_type == ObjectType.OPERATIONAL_DOCUMENT
            and record.payload.get("contract_type") == "CDR"
        }
        for decision in self.commander_office.decision_registry.all():
            if status_filter is not None and decision.status.value != status_filter:
                continue
            rows.append(
                CommandTableRow(
                    decision_id=decision.decision_id,
                    decision_type=decision.decision_type,
                    status=decision.status.value,
                    cdr_contract_id=cdr_by_decision.get(decision.decision_id),
                    source=f"decision_registry:{decision.decision_id}",
                )
            )
        rows.sort(key=lambda row: getattr(row, sort_by))
        self._audit_interaction("dashboard_command_table", f"filter={status_filter};sort={sort_by}")
        return tuple(rows)

    def filter_recent_decisions(self, decision_type: str) -> tuple[DashboardValue, ...]:
        """Filter recent decisions by decision type."""
        values = tuple(
            value
            for value in self._recent_decisions()
            if isinstance(value.value, dict) and value.value.get("decision_type") == decision_type
        )
        self._audit_interaction("dashboard_filter", f"decision_type={decision_type}")
        return values

    def sort_recent_decisions(self, descending: bool = False) -> tuple[DashboardValue, ...]:
        """Sort recent decisions deterministically by decision ID."""
        values = tuple(
            sorted(
                self._recent_decisions(),
                key=lambda value: value.value["decision_id"],
                reverse=descending,
            )
        )
        self._audit_interaction("dashboard_sort", f"recent_decisions_desc={descending}")
        return values

    def _packet_values(self, validation_status: str) -> tuple[DashboardValue, ...]:
        values = []
        for record in self.persistence_repository.all_records():
            if record.payload.get("ebp_id") and record.payload.get("validation_status") == validation_status:
                values.append(
                    DashboardValue(
                        name=str(record.payload["ebp_id"]),
                        value=record.payload,
                        source=f"persistence:{record.object_type.value}:{record.object_id}:v{record.version}",
                    )
                )
        return tuple(values)

    def _recent_decisions(self) -> tuple[DashboardValue, ...]:
        return tuple(
            DashboardValue(
                name=decision.decision_id,
                value={
                    "decision_id": decision.decision_id,
                    "decision_type": decision.decision_type,
                    "status": decision.status.value,
                },
                source=f"decision_registry:{decision.decision_id}",
            )
            for decision in self.commander_office.decision_registry.all()
        )

    def _queue_values(self, queue_name: str) -> tuple[DashboardValue, ...]:
        if queue_name == "commander":
            depth = len(self.commander_office.decision_queue)
            source = "commander_office.decision_queue"
        elif queue_name == "chief_of_staff":
            depth = sum(1 for entry in self.chief_of_staff_service.routing_log if entry["action"] == "approved_to_commander")
            source = "chief_of_staff.routing_log"
        else:
            depth = len(self.commander_office.decision_registry.all())
            source = "commander_office.decision_registry"
        return (DashboardValue(queue_name, depth, source),)

    def _metrics(self) -> ExecutiveMetrics:
        queue_depth = len(self.commander_office.decision_queue)
        decision_throughput = len(self.commander_office.decision_registry.all())
        total_routes = max(1, len(self.chief_of_staff_service.routing_log))
        utilization = decision_throughput / total_routes
        return ExecutiveMetrics(
            queue_depth=queue_depth,
            decision_throughput=decision_throughput,
            utilization=utilization,
            source="decision_registry+routing_log",
        )

    def _health(self) -> OrganizationalHealth:
        reasons = []
        if any(entry["action"] == "rejected_returned" for entry in self.chief_of_staff_service.routing_log):
            reasons.append("rejections_present")
        if len(self.commander_office.decision_queue) > 0:
            reasons.append("commander_queue_not_empty")
        status = "healthy" if not reasons else "attention"
        return OrganizationalHealth(status, tuple(reasons), "chief_of_staff.routing_log+decision_queue")

    def _audit_interaction(self, action: str, detail: str) -> None:
        contract = _dashboard_audit_contract(action, detail, self._refresh_sequence)
        self.audit_service.record_document_creation(contract)


def _dashboard_audit_contract(action: str, detail: str, sequence: int) -> BaseContract:
    from argos.foundation.contracts import OperationalContract, utc_timestamp

    created = utc_timestamp()
    payload = {"action": action, "detail": detail}
    return OperationalContract(
        contract_id=generate_document_id(900 + sequence),
        contract_type="DASHBOARD_AUDIT",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id="STF-002",
        produced_by_group_id="DEP-002",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=f"Executive dashboard interaction: {action}.",
        machine_payload=payload,
        signature_hash="e" * 64,
        source_reference_ids=(),
    )

