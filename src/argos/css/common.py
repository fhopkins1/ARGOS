"""Common CSS transport envelope without subsystem decision authority."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any


CSS_COMMON_CONTRACT_VERSION = "CSS-COMMON.1"


class CSSExecutionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    NOT_EXECUTED = "NOT_EXECUTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"


class CSSVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INDETERMINATE = "INDETERMINATE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class CSSCapability:
    subsystem_id: str
    implementation_version: str
    contract_version: str
    evidence_schema_version: str
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class CSSResultEnvelope:
    schema_version: str
    subsystem_id: str
    subsystem_version: str
    contract_version: str
    candidate_identity: dict[str, Any]
    execution_status: CSSExecutionStatus
    verdict: CSSVerdict
    failure_codes: tuple[str, ...]
    evidence: dict[str, Any]
    authoritative: bool = True
    deterministic: bool = True

    def to_dict(self) -> dict[str, Any]:
        body = jsonable(asdict(self))
        return {**body, "result_digest": stable_hash(body)}


def result_envelope(
    capability: CSSCapability,
    candidate_identity: dict[str, Any],
    failure_codes: tuple[str, ...],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    status = CSSExecutionStatus.COMPLETED
    verdict = CSSVerdict.FAIL if failure_codes else CSSVerdict.PASS
    return CSSResultEnvelope(
        CSS_COMMON_CONTRACT_VERSION,
        capability.subsystem_id,
        capability.implementation_version,
        capability.contract_version,
        candidate_identity,
        status,
        verdict,
        tuple(dict.fromkeys(failure_codes)),
        evidence,
    ).to_dict()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def jsonable(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    return value

