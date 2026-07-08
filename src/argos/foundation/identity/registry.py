"""Deterministic Department ID registry for ARGOS enterprise groups."""

from __future__ import annotations

from dataclasses import dataclass

from .identifiers import generate_department_id


@dataclass(frozen=True)
class DepartmentRecord:
    """Department registry entry."""

    identifier: str
    name: str
    package: str


DEPARTMENT_ID_REGISTRY: tuple[DepartmentRecord, ...] = (
    DepartmentRecord(generate_department_id(1), "Foundation", "argos.foundation"),
    DepartmentRecord(generate_department_id(2), "Executive Group", "argos.executive"),
    DepartmentRecord(generate_department_id(3), "Seeker Group", "argos.seeker"),
    DepartmentRecord(generate_department_id(4), "Analyst Group", "argos.analyst"),
    DepartmentRecord(generate_department_id(5), "Risk Office", "argos.risk"),
    DepartmentRecord(generate_department_id(6), "Trader Group", "argos.trader"),
    DepartmentRecord(generate_department_id(7), "Historian Group", "argos.historian"),
    DepartmentRecord(generate_department_id(8), "Librarian Group", "argos.librarian"),
    DepartmentRecord(generate_department_id(9), "Academy", "argos.academy"),
)


def get_department_record(identifier: str) -> DepartmentRecord | None:
    """Return a department record by deterministic Department ID."""
    for record in DEPARTMENT_ID_REGISTRY:
        if record.identifier == identifier:
            return record
    return None

