"""Executive Workflow service and packet validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from argos.foundation.audit import AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType

from .briefing import ExecutiveBriefingPacket
from .engine import CommanderDecision, CommanderDecisionEngine, CommanderDecisionOutcome
from .mailboxes import EXECUTIVE_GROUP_ID


CHIEF_OF_STAFF_ID = "STF-003"


class PacketStatus(str, Enum):
    """Executive packet validation status."""

    VALIDATED = "validated"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ExecutiveReportReference:
    """Report metadata used by Executive verification."""

    document_id: str
    report_type: str
    created_clock_tick: int
    claim_key: str | None = None
    claim_value: str | None = None


@dataclass(frozen=True)
class PacketValidationResult:
    """Packet validation result."""

    status: PacketStatus
    errors: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Return whether validation passed."""
        return self.status == PacketStatus.VALIDATED


@dataclass(frozen=True)
class ExecutiveRoutingLogEntry:
    """Deterministic Executive routing log entry."""

    sequence: int
    clock_tick: int
    action: str
    ebp_id: str
    status: str
    detail: str


class ExecutiveClock:
    """Monotonic deterministic Executive clock."""

    def __init__(self) -> None:
        self._tick = 0

    def tick(self) -> int:
        """Advance and return the next clock tick."""
        self._tick += 1
        return self._tick

    @property
    def current_tick(self) -> int:
        """Return current clock tick."""
        return self._tick


class ExecutivePacketValidator:
    """Validate EBPs before Commander routing."""

    def __init__(self, max_report_age_ticks: int = 5) -> None:
        self.max_report_age_ticks = max_report_age_ticks

    def validate(
        self,
        ebp: ExecutiveBriefingPacket,
        reports: dict[str, ExecutiveReportReference],
        current_tick: int,
    ) -> PacketValidationResult:
        """Validate evidence, risk, contradictions, staleness, and Chief of Staff routing."""
        errors: list[str] = []
        if ebp.produced_by_staff_id != CHIEF_OF_STAFF_ID:
            errors.append("EBP must be produced by Chief of Staff")
        if ebp.produced_by_group_id != EXECUTIVE_GROUP_ID:
            errors.append("EBP must be produced by Executive Group")

        risk_report = reports.get(ebp.risk_recommendation_document_id)
        if risk_report is None:
            errors.append("missing risk recommendation report")
        elif risk_report.report_type != "risk":
            errors.append("risk recommendation document is not a risk report")
        elif _is_stale(risk_report, current_tick, self.max_report_age_ticks):
            errors.append("risk recommendation report is stale")

        claim_values: dict[str, str] = {}
        for evidence_id in ebp.evidence_reference_ids:
            report = reports.get(evidence_id)
            if report is None:
                errors.append(f"missing evidence report: {evidence_id}")
                continue
            if _is_stale(report, current_tick, self.max_report_age_ticks):
                errors.append(f"stale evidence report: {evidence_id}")
            if report.claim_key is not None and report.claim_value is not None:
                existing = claim_values.get(report.claim_key)
                if existing is not None and existing != report.claim_value:
                    errors.append(f"contradictory reports for claim: {report.claim_key}")
                claim_values[report.claim_key] = report.claim_value

        return PacketValidationResult(
            status=PacketStatus.REJECTED if errors else PacketStatus.VALIDATED,
            errors=tuple(errors),
        )


class ExecutiveSummaryGenerator:
    """Generate deterministic Executive summaries."""

    def generate(self, ebp: ExecutiveBriefingPacket, validation: PacketValidationResult) -> str:
        """Generate a summary for routing and audit logs."""
        return (
            f"EBP {ebp.ebp_id} for {ebp.case_file_id} is {validation.status.value}. "
            f"Recommended action: {ebp.recommended_action}. "
            f"Evidence count: {len(ebp.evidence_reference_ids)}."
        )


class ExecutiveWorkflowService:
    """Deterministic Executive workflow gate before Commander decisions."""

    def __init__(
        self,
        commander_engine: CommanderDecisionEngine,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        validator: ExecutivePacketValidator | None = None,
        clock: ExecutiveClock | None = None,
        summary_generator: ExecutiveSummaryGenerator | None = None,
    ) -> None:
        self.commander_engine = commander_engine
        self.configuration_service = configuration_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self.validator = validator or ExecutivePacketValidator()
        self.clock = clock or ExecutiveClock()
        self.summary_generator = summary_generator or ExecutiveSummaryGenerator()
        self.routing_log: list[ExecutiveRoutingLogEntry] = []

    def route_packet_to_commander(
        self,
        ebp: ExecutiveBriefingPacket,
        reports: dict[str, ExecutiveReportReference],
        decision: CommanderDecision,
        rationale: str,
        document_sequence: int,
        intended_consumer_group_id: str,
        resize_factor: float | None = None,
        received_via_courier: bool = True,
    ) -> CommanderDecisionOutcome:
        """Validate an EBP and route it to Commander if complete."""
        self.configuration_service.validate_startup()
        tick = self.clock.tick()
        if not received_via_courier:
            self._log(tick, "reject_packet", ebp.ebp_id, "rejected", "packet bypassed courier")
            raise ValueError("Executive packets must arrive through Courier Framework")

        validation = self.validator.validate(ebp, reports, tick)
        summary = self.summary_generator.generate(ebp, validation)
        self._persist_packet_event(ebp, validation, summary)
        if not validation.passed:
            self._log(tick, "reject_packet", ebp.ebp_id, "rejected", "; ".join(validation.errors))
            raise ValueError("; ".join(validation.errors))

        self._log(tick, "route_to_commander", ebp.ebp_id, "validated", summary)
        outcome = self.commander_engine.decide(
            ebp,
            decision,
            rationale,
            document_sequence,
            intended_consumer_group_id,
            resize_factor=resize_factor,
        )
        self._log(tick, "cdr_generated", ebp.ebp_id, "routed", outcome.cdr_contract_id)
        return outcome

    def route_cdr_to_outbox(
        self,
        cdr_contract_id: str,
        target_inbox: IncomingMailbox,
    ):
        """Route a generated CDR from Executive Outbox through Courier."""
        cdr = self.commander_engine.commander_office.persistence_repository.latest(
            ObjectType.OPERATIONAL_DOCUMENT,
            cdr_contract_id,
        )
        if cdr is None:
            raise ValueError(f"unknown CDR: {cdr_contract_id}")
        contract = self.commander_engine.commander_office.cdr_generator.generate(
            self.commander_engine.commander_office.decision_registry.all()[-1],
            int(cdr_contract_id.split("-")[1]),
            target_inbox.owner_group_id,
        )
        return self.commander_engine.commander_office.route_cdr(contract, target_inbox)

    def _persist_packet_event(
        self,
        ebp: ExecutiveBriefingPacket,
        validation: PacketValidationResult,
        summary: str,
    ) -> None:
        self.persistence_repository.persist(
            ObjectType.OPERATIONAL_DOCUMENT,
            ebp.ebp_id.replace("EBP", "DOC"),
            {
                "contract_id": ebp.ebp_id.replace("EBP", "DOC"),
                "case_file_id": ebp.case_file_id,
                "trade_cycle_id": ebp.trade_cycle_id,
                "ebp_id": ebp.ebp_id,
                "validation_status": validation.status.value,
                "validation_errors": list(validation.errors),
                "summary": summary,
            },
        )

    def _log(self, tick: int, action: str, ebp_id: str, status: str, detail: str) -> None:
        self.routing_log.append(
            ExecutiveRoutingLogEntry(
                sequence=len(self.routing_log) + 1,
                clock_tick=tick,
                action=action,
                ebp_id=ebp_id,
                status=status,
                detail=detail,
            )
        )


def _is_stale(report: ExecutiveReportReference, current_tick: int, max_age: int) -> bool:
    return current_tick - report.created_clock_tick > max_age

