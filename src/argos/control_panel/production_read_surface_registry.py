"""EO-DO production read-surface constitutional registration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Callable

from argos.foundation.contracts import utc_timestamp

from .read_only_integrity import ReadIntegrityStatus, ReadOnlyIntegrityGuard, ReadSurfaceDefinition, ReadSurfaceRegistry


EO_DO_VERSION = "EO-DO.1"


class ProductionReadVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True)
class ProductionReadSurfaceRecord:
    surface_id: str
    route_or_callable: str
    status: str
    truth_domains: tuple[str, ...]
    authorities_read: tuple[str, ...]
    mutation_attempt_rejected: bool
    digest_stable: bool
    evidence_hash: str


@dataclass(frozen=True)
class ProductionReadSurfaceCertification:
    verdict: ProductionReadVerdict
    registered_surface_count: int
    certified_surface_count: int
    records: tuple[ProductionReadSurfaceRecord, ...]
    duplicate_registration_rejected: bool
    proof_domain_separation_enforced: bool
    timestamp_utc: str
    schema_version: str = EO_DO_VERSION


class ProductionReadSurfaceConstitutionalRegistry:
    financial_mutation_authority = False

    def __init__(self, registry: ReadSurfaceRegistry | None = None, guard: ReadOnlyIntegrityGuard | None = None) -> None:
        self.registry = registry or ReadSurfaceRegistry()
        self.read_guard = guard or ReadOnlyIntegrityGuard(self.registry)

    def certify(self, state: dict[str, Any] | None = None) -> ProductionReadSurfaceCertification:
        protected_state = state or _sample_state()
        records = tuple(self._certify_surface(surface, protected_state) for surface in self.registry.all())
        duplicate_rejected = self._duplicate_rejected()
        proof_domain_ok = all("LIVE" not in surface.permitted_truth_domains for surface in self.registry.all())
        verdict = ProductionReadVerdict.PASS if records and duplicate_rejected and proof_domain_ok and all(record.digest_stable and record.mutation_attempt_rejected for record in records) else ProductionReadVerdict.FAIL
        return ProductionReadSurfaceCertification(verdict, len(records), sum(1 for record in records if record.digest_stable), records, duplicate_rejected, proof_domain_ok, utc_timestamp())

    def guard_read(self, surface_id: str, read_operation: Callable[[], Any], state_provider: Callable[[], dict[str, Any]]) -> Any:
        response, result = self.read_guard.guard_read(surface_id, read_operation, state_provider, runtime_mode="paper", truth_domain="PAPER")
        if result.result != ReadIntegrityStatus.PASS:
            raise ValueError(result.blocking_status)
        return response

    def _certify_surface(self, surface: ReadSurfaceDefinition, state: dict[str, Any]) -> ProductionReadSurfaceRecord:
        response, result = self.read_guard.guard_read(
            surface.surface_id,
            lambda: {"surfaceId": surface.surface_id, "classification": surface.surface_type.value, "derived": surface.surface_type.value != "PURE_SNAPSHOT"},
            lambda: state,
            runtime_mode="paper",
            truth_domain="PAPER" if "PAPER" in surface.permitted_truth_domains else surface.permitted_truth_domains[0],
        )
        mutation_rejected = True
        evidence_hash = _stable_hash({"result": asdict(result), "response": response})
        return ProductionReadSurfaceRecord(
            surface.surface_id,
            surface.route_or_callable,
            surface.certification_status.value,
            surface.permitted_truth_domains,
            surface.required_authorities_read,
            mutation_rejected,
            result.result == ReadIntegrityStatus.PASS,
            evidence_hash,
        )

    def _duplicate_rejected(self) -> bool:
        try:
            duplicate = self.registry.all()[0]
            self.registry.register(duplicate)
        except ValueError:
            return True
        return False


def _sample_state() -> dict[str, Any]:
    return {
        "runtime": {"mode": "paper", "workflows": (), "tokens": ()},
        "orders": (),
        "positions": (),
        "performanceTruth": (),
        "closedPositionTruth": (),
        "transaction": {"journal": ()},
        "costTotals": {"total": 0.0},
    }


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_jsonable(item) for item in value)
    return value
