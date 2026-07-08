"""Prompt repository, passports, versioning, and snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp
from argos.foundation.identity import IdentifierKind, validate_identifier


SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
PROMPT_ID_PATTERN = re.compile(r"^PROMPT-[0-9]{3,}$")


class PromptRepositoryError(ValueError):
    """Raised when prompt repository rules are violated."""


@dataclass(frozen=True)
class PromptPassport:
    """Complete prompt metadata passport."""

    prompt_id: str
    title: str
    owner_group_id: str
    author_staff_id: str
    purpose: str
    allowed_environments: tuple[str, ...]
    input_contract_types: tuple[str, ...]
    output_contract_types: tuple[str, ...]
    dependencies: tuple[str, ...]
    safety_notes: str

    def __post_init__(self) -> None:
        _require_prompt_id(self.prompt_id)
        _require_identifier_kind(self.owner_group_id, IdentifierKind.DEPARTMENT)
        _require_identifier_kind(self.author_staff_id, IdentifierKind.STAFF)
        object.__setattr__(self, "allowed_environments", tuple(self.allowed_environments))
        object.__setattr__(self, "input_contract_types", tuple(self.input_contract_types))
        object.__setattr__(self, "output_contract_types", tuple(self.output_contract_types))
        object.__setattr__(self, "dependencies", tuple(self.dependencies))
        if not self.title.strip():
            raise PromptRepositoryError("prompt passport title must not be empty")
        if not self.purpose.strip():
            raise PromptRepositoryError("prompt passport purpose must not be empty")
        if not self.allowed_environments:
            raise PromptRepositoryError("prompt passport requires at least one allowed environment")

    def to_dict(self) -> dict[str, Any]:
        """Serialize passport metadata."""
        return {
            "allowed_environments": list(self.allowed_environments),
            "author_staff_id": self.author_staff_id,
            "dependencies": list(self.dependencies),
            "input_contract_types": list(self.input_contract_types),
            "output_contract_types": list(self.output_contract_types),
            "owner_group_id": self.owner_group_id,
            "prompt_id": self.prompt_id,
            "purpose": self.purpose,
            "safety_notes": self.safety_notes,
            "title": self.title,
        }


@dataclass(frozen=True)
class PromptRecord:
    """Immutable versioned prompt revision."""

    passport: PromptPassport
    version: str
    body: str
    created_timestamp_utc: str
    revision_hash: str

    @classmethod
    def create(cls, passport: PromptPassport, version: str, body: str) -> "PromptRecord":
        """Create a validated prompt revision."""
        _require_semver(version)
        if not body.strip():
            raise PromptRepositoryError("prompt body must not be empty")
        timestamp = utc_timestamp()
        digest = _hash_payload(
            {
                "body": body,
                "created_timestamp_utc": timestamp,
                "passport": passport.to_dict(),
                "version": version,
            }
        )
        return cls(passport, version, body, timestamp, digest)

    def to_dict(self) -> dict[str, Any]:
        """Serialize prompt revision."""
        return {
            "body": self.body,
            "created_timestamp_utc": self.created_timestamp_utc,
            "passport": self.passport.to_dict(),
            "revision_hash": self.revision_hash,
            "version": self.version,
        }


class PromptRepository:
    """Append-only prompt registry and repository."""

    def __init__(self) -> None:
        self._records: dict[str, list[PromptRecord]] = {}

    def register(self, passport: PromptPassport, version: str, body: str) -> PromptRecord:
        """Register a new prompt revision without overwriting history."""
        record = PromptRecord.create(passport, version, body)
        history = self._records.setdefault(passport.prompt_id, [])
        if any(existing.version == version for existing in history):
            raise PromptRepositoryError(f"prompt revision already exists: {passport.prompt_id} {version}")
        history.append(record)
        history.sort(key=lambda item: _semver_key(item.version))
        return record

    def latest(self, prompt_id: str) -> PromptRecord | None:
        """Return latest prompt revision."""
        history = self.history(prompt_id)
        return history[-1] if history else None

    def history(self, prompt_id: str) -> tuple[PromptRecord, ...]:
        """Return full prompt revision history."""
        return tuple(self._records.get(prompt_id, ()))

    def search(self, text: str) -> tuple[PromptRecord, ...]:
        """Search prompt passports and prompt bodies."""
        needle = text.lower()
        return tuple(
            record
            for history in self._records.values()
            for record in history
            if needle in record.body.lower()
            or needle in record.passport.title.lower()
            or needle in record.passport.purpose.lower()
        )


@dataclass(frozen=True)
class PromptSnapshot:
    """Case File-linked prompt snapshot."""

    prompt_snapshot_id: str
    case_file_id: str
    trade_cycle_id: str
    prompt_id: str
    prompt_version: str
    revision_hash: str
    snapshot_hash: str
    created_timestamp_utc: str
    metadata: Mapping[str, Any]


class PromptSnapshotService:
    """Create deterministic prompt snapshots linked to Case Files."""

    def __init__(self, repository: PromptRepository) -> None:
        self.repository = repository
        self._snapshots: dict[str, PromptSnapshot] = {}

    def snapshot(
        self,
        prompt_id: str,
        case_file_id: str,
        trade_cycle_id: str,
        version: str | None = None,
    ) -> PromptSnapshot:
        """Snapshot a prompt revision for a Case File."""
        _require_identifier_kind(case_file_id, IdentifierKind.CASE_FILE)
        _require_identifier_kind(trade_cycle_id, IdentifierKind.TRADE_CYCLE)
        record = _select_prompt_record(self.repository, prompt_id, version)
        timestamp = utc_timestamp()
        snapshot_id = f"PS-{len(self._snapshots) + 1:06d}"
        metadata = {
            "passport": record.passport.to_dict(),
            "prompt_body_hash": hashlib.sha256(record.body.encode("utf-8")).hexdigest(),
        }
        snapshot_hash = _hash_payload(
            {
                "case_file_id": case_file_id,
                "metadata": metadata,
                "prompt_id": prompt_id,
                "prompt_snapshot_id": snapshot_id,
                "prompt_version": record.version,
                "revision_hash": record.revision_hash,
                "timestamp": timestamp,
                "trade_cycle_id": trade_cycle_id,
            }
        )
        snapshot = PromptSnapshot(
            prompt_snapshot_id=snapshot_id,
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            prompt_id=prompt_id,
            prompt_version=record.version,
            revision_hash=record.revision_hash,
            snapshot_hash=snapshot_hash,
            created_timestamp_utc=timestamp,
            metadata=MappingProxyType(metadata),
        )
        self._snapshots[snapshot_id] = snapshot
        return snapshot

    def search_by_case_file_id(self, case_file_id: str) -> tuple[PromptSnapshot, ...]:
        """Return snapshots linked to a Case File."""
        return tuple(snapshot for snapshot in self._snapshots.values() if snapshot.case_file_id == case_file_id)


def _select_prompt_record(
    repository: PromptRepository,
    prompt_id: str,
    version: str | None,
) -> PromptRecord:
    if version is None:
        record = repository.latest(prompt_id)
    else:
        record = next((item for item in repository.history(prompt_id) if item.version == version), None)
    if record is None:
        raise PromptRepositoryError(f"prompt revision not found: {prompt_id} {version or 'latest'}")
    return record


def _require_prompt_id(prompt_id: str) -> None:
    if not PROMPT_ID_PATTERN.fullmatch(prompt_id):
        raise PromptRepositoryError("prompt_id must match PROMPT-NNN")


def _require_identifier_kind(identifier: str, expected_kind: IdentifierKind) -> None:
    result = validate_identifier(identifier)
    if not result.is_valid or result.kind != expected_kind:
        raise PromptRepositoryError(f"invalid {expected_kind.value} identifier: {identifier}")


def _require_semver(version: str) -> None:
    if not SEMVER_PATTERN.fullmatch(version):
        raise PromptRepositoryError("prompt version must use Major.Minor.Revision semantic versioning")


def _semver_key(version: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in version.split("."))  # type: ignore[return-value]


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

