"""Executive decision queue and registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from argos.foundation.contracts import utc_timestamp


class DecisionStatus(str, Enum):
    """Executive decision status."""

    QUEUED = "queued"
    REGISTERED = "registered"
    CDR_GENERATED = "cdr_generated"


@dataclass(frozen=True)
class DecisionRecord:
    """Immutable Executive decision record."""

    decision_id: str
    case_file_id: str
    trade_cycle_id: str
    requested_by_staff_id: str
    decision_type: str
    rationale: str
    risk_recommendation_document_id: str
    approved: bool
    created_timestamp_utc: str
    status: DecisionStatus = DecisionStatus.QUEUED

    def with_status(self, status: DecisionStatus) -> "DecisionRecord":
        """Return a new immutable decision record with updated status."""
        return DecisionRecord(
            decision_id=self.decision_id,
            case_file_id=self.case_file_id,
            trade_cycle_id=self.trade_cycle_id,
            requested_by_staff_id=self.requested_by_staff_id,
            decision_type=self.decision_type,
            rationale=self.rationale,
            risk_recommendation_document_id=self.risk_recommendation_document_id,
            approved=self.approved,
            created_timestamp_utc=self.created_timestamp_utc,
            status=status,
        )


class DecisionQueue:
    """Deterministic FIFO decision queue."""

    def __init__(self) -> None:
        self._records: list[DecisionRecord] = []

    def enqueue(self, record: DecisionRecord) -> None:
        """Queue a decision request."""
        self._records.append(record)

    def dequeue(self) -> DecisionRecord:
        """Return the next queued decision."""
        if not self._records:
            raise IndexError("decision queue is empty")
        return self._records.pop(0)

    def __len__(self) -> int:
        return len(self._records)


class DecisionRegistry:
    """Append-only decision registry."""

    def __init__(self) -> None:
        self._records: dict[str, DecisionRecord] = {}

    def register(self, record: DecisionRecord) -> DecisionRecord:
        """Register a decision once."""
        if record.decision_id in self._records:
            raise ValueError(f"decision already registered: {record.decision_id}")
        registered = record.with_status(DecisionStatus.REGISTERED)
        self._records[registered.decision_id] = registered
        return registered

    def mark_cdr_generated(self, decision_id: str) -> DecisionRecord:
        """Mark a registered decision as having a CDR."""
        if decision_id not in self._records:
            raise ValueError(f"unknown decision: {decision_id}")
        updated = self._records[decision_id].with_status(DecisionStatus.CDR_GENERATED)
        self._records[decision_id] = updated
        return updated

    def get(self, decision_id: str) -> DecisionRecord | None:
        """Return a decision by ID."""
        return self._records.get(decision_id)

    def all(self) -> tuple[DecisionRecord, ...]:
        """Return registered decisions."""
        return tuple(self._records.values())


def create_decision_record(
    sequence: int,
    case_file_id: str,
    trade_cycle_id: str,
    requested_by_staff_id: str,
    decision_type: str,
    rationale: str,
    risk_recommendation_document_id: str,
    approved: bool,
) -> DecisionRecord:
    """Create a deterministic decision record."""
    if not risk_recommendation_document_id:
        raise ValueError("risk_recommendation_document_id is required")
    return DecisionRecord(
        decision_id=f"CDR-DECISION-{sequence:03d}",
        case_file_id=case_file_id,
        trade_cycle_id=trade_cycle_id,
        requested_by_staff_id=requested_by_staff_id,
        decision_type=decision_type,
        rationale=rationale,
        risk_recommendation_document_id=risk_recommendation_document_id,
        approved=approved,
        created_timestamp_utc=utc_timestamp(),
    )

