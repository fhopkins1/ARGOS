"""Specification repositories for ARGOS engineering artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


SPEC_ID_PATTERN = re.compile(r"^(SP|IF|DB|API|TS)-[0-9]{3,}$")
SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class SpecificationType(str, Enum):
    """Specification families required by EO-008."""

    STAFF = "SP"
    INTERFACE = "IF"
    DATABASE = "DB"
    API = "API"
    TEST = "TS"


@dataclass(frozen=True)
class SpecificationRecord:
    """Immutable specification revision."""

    specification_id: str
    specification_type: SpecificationType
    title: str
    version: str
    body: str
    dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.specification_type, SpecificationType):
            object.__setattr__(self, "specification_type", SpecificationType(self.specification_type))
        if not SPEC_ID_PATTERN.fullmatch(self.specification_id):
            raise ValueError("specification_id must match SP/IF/DB/API/TS-NNN")
        if not self.specification_id.startswith(f"{self.specification_type.value}-"):
            raise ValueError("specification_id prefix must match specification_type")
        if not SEMVER_PATTERN.fullmatch(self.version):
            raise ValueError("specification version must use Major.Minor.Revision semantic versioning")
        if not self.title.strip() or not self.body.strip():
            raise ValueError("specification title and body must not be empty")
        object.__setattr__(self, "dependencies", tuple(self.dependencies))


class SpecificationRepository:
    """Append-only repository for specification revisions."""

    def __init__(self, specification_type: SpecificationType) -> None:
        self.specification_type = specification_type
        self._records: dict[str, list[SpecificationRecord]] = {}

    def register(self, record: SpecificationRecord) -> SpecificationRecord:
        """Register a specification revision."""
        if record.specification_type != self.specification_type:
            raise ValueError("record specification type does not match repository")
        history = self._records.setdefault(record.specification_id, [])
        if any(existing.version == record.version for existing in history):
            raise ValueError(f"specification revision already exists: {record.specification_id}")
        history.append(record)
        history.sort(key=lambda item: tuple(int(part) for part in item.version.split(".")))
        return record

    def latest(self, specification_id: str) -> SpecificationRecord | None:
        """Return latest revision."""
        history = self.history(specification_id)
        return history[-1] if history else None

    def history(self, specification_id: str) -> tuple[SpecificationRecord, ...]:
        """Return specification revision history."""
        return tuple(self._records.get(specification_id, ()))

    def search(self, text: str) -> tuple[SpecificationRecord, ...]:
        """Search specification titles and bodies."""
        needle = text.lower()
        return tuple(
            record
            for history in self._records.values()
            for record in history
            if needle in record.title.lower() or needle in record.body.lower()
        )

