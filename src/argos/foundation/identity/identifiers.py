"""Deterministic ARGOS identifier generation and validation.

Foundation owns identifier formats. Operational departments consume this module
instead of inventing local naming conventions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


MIN_SEQUENCE_WIDTH = 3


class IdentifierKind(str, Enum):
    """Identifier kinds currently defined for EO-002."""

    DEPARTMENT = "DEP"
    STAFF = "STF"
    TRADE_CYCLE = "TC"
    CASE_FILE = "CF"
    DOCUMENT = "DOC"


_IDENTIFIER_PATTERN = re.compile(r"^(?P<prefix>[A-Z]{2,4})-(?P<sequence>[0-9]{3,})$")


@dataclass(frozen=True)
class IdentifierValidationResult:
    """Structured result for deterministic identifier validation."""

    is_valid: bool
    identifier: str
    kind: IdentifierKind | None
    reason: str | None = None


def generate_identifier(kind: IdentifierKind, sequence: int) -> str:
    """Generate a deterministic ARGOS identifier from kind and sequence."""
    if not isinstance(kind, IdentifierKind):
        raise TypeError("kind must be an IdentifierKind")
    if not isinstance(sequence, int):
        raise TypeError("sequence must be an integer")
    if sequence < 1:
        raise ValueError("sequence must be greater than or equal to 1")

    return f"{kind.value}-{sequence:0{MIN_SEQUENCE_WIDTH}d}"


def generate_department_id(sequence: int) -> str:
    """Generate a Department ID."""
    return generate_identifier(IdentifierKind.DEPARTMENT, sequence)


def generate_staff_id(sequence: int) -> str:
    """Generate a Staff ID."""
    return generate_identifier(IdentifierKind.STAFF, sequence)


def generate_trade_cycle_id(sequence: int) -> str:
    """Generate a Trade Cycle ID."""
    return generate_identifier(IdentifierKind.TRADE_CYCLE, sequence)


def generate_case_file_id(sequence: int) -> str:
    """Generate a Case File ID."""
    return generate_identifier(IdentifierKind.CASE_FILE, sequence)


def generate_document_id(sequence: int) -> str:
    """Generate an Operational Document ID."""
    return generate_identifier(IdentifierKind.DOCUMENT, sequence)


def parse_identifier(identifier: str) -> tuple[IdentifierKind, int]:
    """Parse a valid identifier into kind and numeric sequence."""
    validation = validate_identifier(identifier)
    if not validation.is_valid or validation.kind is None:
        raise ValueError(validation.reason or "invalid identifier")

    match = _IDENTIFIER_PATTERN.fullmatch(identifier)
    if match is None:
        raise ValueError("invalid identifier")
    return validation.kind, int(match.group("sequence"))


def validate_identifier(identifier: str) -> IdentifierValidationResult:
    """Validate an ARGOS identifier against EO-002/PB-006 rules."""
    if not isinstance(identifier, str):
        return IdentifierValidationResult(
            is_valid=False,
            identifier=str(identifier),
            kind=None,
            reason="identifier must be a string",
        )

    match = _IDENTIFIER_PATTERN.fullmatch(identifier)
    if match is None:
        return IdentifierValidationResult(
            is_valid=False,
            identifier=identifier,
            kind=None,
            reason="identifier must match PREFIX-NNN with uppercase prefix and numeric sequence",
        )

    prefix = match.group("prefix")
    sequence = match.group("sequence")
    kind = _kind_for_prefix(prefix)
    if kind is None:
        return IdentifierValidationResult(
            is_valid=False,
            identifier=identifier,
            kind=None,
            reason=f"unknown identifier prefix: {prefix}",
        )

    if int(sequence) < 1:
        return IdentifierValidationResult(
            is_valid=False,
            identifier=identifier,
            kind=kind,
            reason="sequence must be greater than or equal to 1",
        )

    return IdentifierValidationResult(
        is_valid=True,
        identifier=identifier,
        kind=kind,
        reason=None,
    )


def _kind_for_prefix(prefix: str) -> IdentifierKind | None:
    for kind in IdentifierKind:
        if kind.value == prefix:
            return kind
    return None

