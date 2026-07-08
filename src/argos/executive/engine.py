"""Commander Decision Engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from argos.foundation.prompts import PromptRepository, PromptSnapshotService

from .briefing import ExecutiveBriefingPacket
from .commander import CommanderOffice


class CommanderDecision(str, Enum):
    """Supported Commander decision paths."""

    APPROVE = "approve"
    REJECT = "reject"
    RESIZE = "resize"
    DEFER = "defer"
    REQUEST_MORE_ANALYSIS = "request_more_analysis"


@dataclass(frozen=True)
class CommanderDecisionOutcome:
    """Result of one Commander decision workflow."""

    decision: CommanderDecision
    decision_id: str
    cdr_contract_id: str
    prompt_snapshot_id: str


class CommanderDecisionEngine:
    """Consumes only EBPs and produces one CDR per decision."""

    def __init__(
        self,
        commander_office: CommanderOffice,
        prompt_repository: PromptRepository,
        commander_prompt_id: str,
    ) -> None:
        self.commander_office = commander_office
        self.prompt_repository = prompt_repository
        self.commander_prompt_id = commander_prompt_id
        self.prompt_snapshot_service = PromptSnapshotService(prompt_repository)

    def decide(
        self,
        ebp: ExecutiveBriefingPacket,
        decision: CommanderDecision,
        rationale: str,
        document_sequence: int,
        intended_consumer_group_id: str,
        resize_factor: float | None = None,
    ) -> CommanderDecisionOutcome:
        """Execute deterministic Commander decision workflow from one EBP."""
        if not isinstance(ebp, ExecutiveBriefingPacket):
            raise TypeError("Commander decisions must consume an ExecutiveBriefingPacket")
        if not rationale.strip():
            raise ValueError("Commander decision rationale is required")
        if decision == CommanderDecision.RESIZE:
            factor = resize_factor if resize_factor is not None else ebp.requested_resize_factor
            if factor is None or factor <= 0:
                raise ValueError("resize decision requires a positive resize factor")
        else:
            factor = None

        snapshot = self.prompt_snapshot_service.snapshot(
            self.commander_prompt_id,
            ebp.case_file_id,
            ebp.trade_cycle_id,
        )
        full_rationale = _rationale_with_evidence(rationale, ebp, snapshot.prompt_snapshot_id, factor)
        queued = self.commander_office.submit_decision_request(
            case_file_id=ebp.case_file_id,
            trade_cycle_id=ebp.trade_cycle_id,
            requested_by_staff_id=ebp.produced_by_staff_id,
            decision_type=decision.value,
            rationale=full_rationale,
            risk_recommendation_document_id=ebp.risk_recommendation_document_id,
            approved=decision == CommanderDecision.APPROVE,
        )
        registered = self.commander_office.register_next_decision()
        cdr = self.commander_office.generate_cdr(
            registered.decision_id,
            document_sequence,
            intended_consumer_group_id,
        )
        return CommanderDecisionOutcome(
            decision=decision,
            decision_id=registered.decision_id,
            cdr_contract_id=cdr.contract_id,
            prompt_snapshot_id=snapshot.prompt_snapshot_id,
        )


def _rationale_with_evidence(
    rationale: str,
    ebp: ExecutiveBriefingPacket,
    prompt_snapshot_id: str,
    resize_factor: float | None,
) -> str:
    evidence = ", ".join(ebp.evidence_reference_ids)
    resize_text = f" Resize factor: {resize_factor}." if resize_factor is not None else ""
    return (
        f"{rationale} EBP: {ebp.ebp_id}. Evidence: {evidence}. "
        f"Risk recommendation: {ebp.risk_recommendation_document_id}. "
        f"Prompt snapshot: {prompt_snapshot_id}.{resize_text}"
    )

