"""Foundation-owned deterministic identity framework."""

from .identifiers import (
    IdentifierKind,
    IdentifierValidationResult,
    generate_case_file_id,
    generate_department_id,
    generate_document_id,
    generate_identifier,
    generate_staff_id,
    generate_trade_cycle_id,
    parse_identifier,
    validate_identifier,
)
from .registry import DEPARTMENT_ID_REGISTRY, DepartmentRecord, get_department_record

__all__ = [
    "DEPARTMENT_ID_REGISTRY",
    "DepartmentRecord",
    "IdentifierKind",
    "IdentifierValidationResult",
    "generate_case_file_id",
    "generate_department_id",
    "generate_document_id",
    "generate_identifier",
    "generate_staff_id",
    "generate_trade_cycle_id",
    "get_department_record",
    "parse_identifier",
    "validate_identifier",
]

