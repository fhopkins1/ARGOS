"""Executive Briefing Packet object."""

from __future__ import annotations

from dataclasses import dataclass

from argos.foundation.identity import IdentifierKind, validate_identifier


@dataclass(frozen=True)
class ExecutiveBriefingPacket:
    """Deterministic input packet for Commander decisions."""

    ebp_id: str
    case_file_id: str
    trade_cycle_id: str
    produced_by_staff_id: str
    produced_by_group_id: str
    risk_recommendation_document_id: str
    evidence_reference_ids: tuple[str, ...]
    summary: str
    recommended_action: str
    requested_resize_factor: float | None = None
    document_signature_hash: str | None = None
    configuration_snapshot_hash: str | None = None
    prompt_snapshot_id: str | None = None
    model_snapshot_id: str | None = None

    def __post_init__(self) -> None:
        if not self.ebp_id.startswith("EBP-"):
            raise ValueError("ebp_id must start with EBP-")
        _require_identifier_kind(self.case_file_id, IdentifierKind.CASE_FILE)
        _require_identifier_kind(self.trade_cycle_id, IdentifierKind.TRADE_CYCLE)
        _require_identifier_kind(self.produced_by_staff_id, IdentifierKind.STAFF)
        _require_identifier_kind(self.produced_by_group_id, IdentifierKind.DEPARTMENT)
        _require_document_id(self.risk_recommendation_document_id)
        object.__setattr__(self, "evidence_reference_ids", tuple(self.evidence_reference_ids))
        if not self.evidence_reference_ids:
            raise ValueError("EBP requires at least one evidence reference")
        for evidence_id in self.evidence_reference_ids:
            _require_document_id(evidence_id)
        if not self.summary.strip():
            raise ValueError("EBP summary must not be empty")
        if not self.recommended_action.strip():
            raise ValueError("EBP recommended_action must not be empty")
        if self.requested_resize_factor is not None and self.requested_resize_factor <= 0:
            raise ValueError("requested_resize_factor must be positive")

    def source_reference_ids(self) -> tuple[str, ...]:
        """Return all source references required by a CDR."""
        return (self.risk_recommendation_document_id, *self.evidence_reference_ids)


def _require_identifier_kind(identifier: str, expected_kind: IdentifierKind) -> None:
    result = validate_identifier(identifier)
    if not result.is_valid or result.kind != expected_kind:
        raise ValueError(f"invalid {expected_kind.value} identifier: {identifier}")


def _require_document_id(identifier: str) -> None:
    result = validate_identifier(identifier)
    if not result.is_valid or result.kind != IdentifierKind.DOCUMENT:
        raise ValueError(f"invalid DOC identifier: {identifier}")
