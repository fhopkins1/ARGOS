"""Canonical ARGOS data contracts.

Contracts are deterministic data structures. They validate shared metadata,
serialize to JSON, and remain free of business or trading logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
import json
import re
from typing import Any, ClassVar, Self

from argos.foundation.identity import validate_identifier


SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
CONTRACT_TYPE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
SHA256_HEX_PATTERN = re.compile(r"^[a-f0-9]{64}$")


class ValidationStatus(str, Enum):
    """Permitted validation states for canonical contracts."""

    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"


class ContractValidationError(ValueError):
    """Raised when a contract violates canonical metadata rules."""


def utc_timestamp(moment: datetime | None = None) -> str:
    """Return a UTC ISO-8601 timestamp string."""
    if moment is None:
        moment = datetime.now(UTC)
    if moment.tzinfo is None:
        raise ValueError("timestamp source datetime must be timezone-aware")
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class BaseContract:
    """Universal metadata envelope inherited by structured ARGOS records."""

    contract_id: str
    contract_type: str
    contract_version: str
    schema_version: str
    case_file_id: str
    trade_cycle_id: str
    parent_contract_ids: tuple[str, ...]
    produced_by_staff_id: str
    produced_by_group_id: str
    intended_consumer_group_id: str
    created_timestamp_utc: str
    updated_timestamp_utc: str
    validation_status: ValidationStatus
    validation_errors: tuple[str, ...]
    human_summary: str
    machine_payload: dict[str, Any]
    signature_hash: str
    source_reference_ids: tuple[str, ...]

    contract_family: ClassVar[str] = "base"
    required_fields: ClassVar[tuple[str, ...]] = (
        "contract_id",
        "contract_type",
        "contract_version",
        "schema_version",
        "case_file_id",
        "trade_cycle_id",
        "parent_contract_ids",
        "produced_by_staff_id",
        "produced_by_group_id",
        "intended_consumer_group_id",
        "created_timestamp_utc",
        "updated_timestamp_utc",
        "validation_status",
        "validation_errors",
        "human_summary",
        "machine_payload",
        "signature_hash",
        "source_reference_ids",
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "parent_contract_ids", tuple(self.parent_contract_ids))
        object.__setattr__(self, "source_reference_ids", tuple(self.source_reference_ids))
        object.__setattr__(self, "validation_errors", tuple(self.validation_errors))
        if not isinstance(self.validation_status, ValidationStatus):
            object.__setattr__(self, "validation_status", ValidationStatus(self.validation_status))

        errors = self.validate()
        if errors:
            raise ContractValidationError("; ".join(errors))

    def validate(self) -> list[str]:
        """Return canonical metadata validation errors."""
        errors: list[str] = []
        errors.extend(_validate_identifier("contract_id", self.contract_id))
        errors.extend(_validate_identifier("case_file_id", self.case_file_id))
        errors.extend(_validate_identifier("trade_cycle_id", self.trade_cycle_id))
        errors.extend(_validate_identifier("produced_by_staff_id", self.produced_by_staff_id))
        errors.extend(_validate_identifier("produced_by_group_id", self.produced_by_group_id))
        errors.extend(_validate_identifier("intended_consumer_group_id", self.intended_consumer_group_id))

        if not CONTRACT_TYPE_PATTERN.fullmatch(self.contract_type):
            errors.append("contract_type must be uppercase with optional digits and underscores")
        if not SEMVER_PATTERN.fullmatch(self.contract_version):
            errors.append("contract_version must use Major.Minor.Revision semantic versioning")
        if not SEMVER_PATTERN.fullmatch(self.schema_version):
            errors.append("schema_version must use Major.Minor.Revision semantic versioning")

        errors.extend(_validate_timestamp("created_timestamp_utc", self.created_timestamp_utc))
        errors.extend(_validate_timestamp("updated_timestamp_utc", self.updated_timestamp_utc))
        if not errors and self.updated_timestamp_utc < self.created_timestamp_utc:
            errors.append("updated_timestamp_utc must not be earlier than created_timestamp_utc")

        if not isinstance(self.machine_payload, dict):
            errors.append("machine_payload must be a JSON object")
        if not self.human_summary.strip():
            errors.append("human_summary must not be empty")
        if not SHA256_HEX_PATTERN.fullmatch(self.signature_hash):
            errors.append("signature_hash must be a 64-character lowercase SHA-256 hex digest")

        errors.extend(_validate_identifier_collection("parent_contract_ids", self.parent_contract_ids))
        if self.contract_id in self.parent_contract_ids:
            errors.append("parent_contract_ids must not include contract_id")
        errors.extend(_validate_identifier_collection("source_reference_ids", self.source_reference_ids))

        if self.validation_status == ValidationStatus.VALID and self.validation_errors:
            errors.append("validation_errors must be empty when validation_status is valid")
        if self.validation_status == ValidationStatus.INVALID and not self.validation_errors:
            errors.append("validation_errors must not be empty when validation_status is invalid")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize the contract to a JSON-compatible dictionary."""
        data = asdict(self)
        data["validation_status"] = self.validation_status.value
        data["parent_contract_ids"] = list(self.parent_contract_ids)
        data["validation_errors"] = list(self.validation_errors)
        data["source_reference_ids"] = list(self.source_reference_ids)
        data["contract_family"] = self.contract_family
        return data

    def to_json(self) -> str:
        """Serialize the contract to deterministic JSON."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize a contract from a dictionary and validate it."""
        missing = [field_name for field_name in cls.required_fields if field_name not in data]
        if missing:
            raise ContractValidationError(f"missing required fields: {', '.join(missing)}")

        normalized = {field_name: data[field_name] for field_name in cls.required_fields}
        return cls(**normalized)

    @classmethod
    def from_json(cls, payload: str) -> Self:
        """Deserialize a contract from JSON and validate it."""
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ContractValidationError("contract JSON must decode to an object")
        return cls.from_dict(data)


@dataclass(frozen=True)
class OperationalContract(BaseContract):
    """Base class for future department-facing operational reports."""

    contract_family: ClassVar[str] = "operational"


@dataclass(frozen=True)
class InfrastructureContract(BaseContract):
    """Base class for internal Foundation infrastructure records."""

    contract_family: ClassVar[str] = "infrastructure"


def _validate_identifier(field_name: str, identifier: str) -> list[str]:
    result = validate_identifier(identifier)
    if result.is_valid:
        return []
    return [f"{field_name}: {result.reason}"]


def _validate_identifier_collection(field_name: str, identifiers: tuple[str, ...]) -> list[str]:
    if not isinstance(identifiers, tuple):
        return [f"{field_name} must be a sequence"]
    errors: list[str] = []
    if len(identifiers) != len(set(identifiers)):
        errors.append(f"{field_name} must not contain duplicates")
    for identifier in identifiers:
        errors.extend(_validate_identifier(field_name, identifier))
    return errors


def _validate_timestamp(field_name: str, timestamp: str) -> list[str]:
    if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
        return [f"{field_name} must be an ISO-8601 UTC timestamp ending in Z"]
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return [f"{field_name} must be a valid ISO-8601 UTC timestamp"]
    return []

