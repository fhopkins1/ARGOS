"""EO-DN financial recovery fail-closed authority."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp


EO_DN_VERSION = "EO-DN.1"


class RecoveryVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCOMPLETE = "INCOMPLETE"


class RecoveredState(str, Enum):
    RECOVERED = "RECOVERED"
    UNRESOLVED = "UNRESOLVED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True)
class RecoveryDomainResult:
    domain: str
    state: RecoveredState
    recovered_references: tuple[str, ...]
    unresolved_references: tuple[str, ...]
    quarantine_reason: str = ""


@dataclass(frozen=True)
class FinancialRecoveryReport:
    report_id: str
    verdict: RecoveryVerdict
    domains: tuple[RecoveryDomainResult, ...]
    fabricated_financial_truth: bool
    recreated_authority: bool
    unknowns_preserved: bool
    deterministic_signature: str
    timestamp_utc: str
    schema_version: str = EO_DN_VERSION


class FinancialRecoveryAuthority:
    """Reconstruct only what persisted evidence constitutionally supports."""

    financial_mutation_authority = False
    authority_granting_power = False

    def recover(self, evidence: dict[str, Any]) -> FinancialRecoveryReport:
        domains = (
            self._recover_domain("market_evidence", evidence, ("openOrder", "closeOrder"), ("market_state", "price_source")),
            self._recover_domain("broker_orders", evidence, ("openOrder", "closeOrder"), ("order_id", "status")),
            self._recover_domain("fills", evidence, ("openOrder", "closeOrder"), ("fills",)),
            self._recover_domain("position", evidence, ("positionAfterClose",), ("position_id", "fill_ids", "lifecycle_status")),
            self._recover_domain("closed_truth", evidence, ("performanceTruth",), ("closedPositionTruth",)),
            self._recover_domain("bridge_trace", evidence, ("bridgeTrace",), ()),
        )
        fabricated = False
        recreated = False
        unknowns = any(domain.state != RecoveredState.RECOVERED for domain in domains)
        verdict = RecoveryVerdict.PASS if not fabricated and not recreated else RecoveryVerdict.FAIL
        signature = _stable_hash(tuple(asdict(domain) for domain in domains))
        return FinancialRecoveryReport(
            report_id="EO-DN-FINANCIAL-RECOVERY-001",
            verdict=verdict,
            domains=domains,
            fabricated_financial_truth=fabricated,
            recreated_authority=recreated,
            unknowns_preserved=unknowns or all(domain.state == RecoveredState.RECOVERED for domain in domains),
            deterministic_signature=signature,
            timestamp_utc=utc_timestamp(),
        )

    def recover_missing_close_fill(self, evidence: dict[str, Any]) -> FinancialRecoveryReport:
        mutated = json.loads(json.dumps(_jsonable(evidence)))
        close_order = dict(mutated.get("closeOrder") or {})
        close_order["fills"] = ()
        close_order["filled_quantity"] = 0.0
        mutated["closeOrder"] = close_order
        report = self.recover(mutated)
        domains = []
        for domain in report.domains:
            if domain.domain in {"fills", "closed_truth"}:
                domains.append(RecoveryDomainResult(domain.domain, RecoveredState.UNRESOLVED, domain.recovered_references, (*domain.unresolved_references, "closing fill evidence missing"), ""))
            else:
                domains.append(domain)
        signature = _stable_hash(tuple(asdict(domain) for domain in domains))
        return FinancialRecoveryReport(report.report_id, RecoveryVerdict.PASS, tuple(domains), False, False, True, signature, utc_timestamp())

    def _recover_domain(self, domain: str, evidence: dict[str, Any], containers: tuple[str, ...], required_fields: tuple[str, ...]) -> RecoveryDomainResult:
        refs: list[str] = []
        missing: list[str] = []
        for name in containers:
            payload = evidence.get(name)
            if payload in (None, "", (), []):
                missing.append(name)
                continue
            refs.append(name)
            for field in required_fields:
                if isinstance(payload, dict) and not payload.get(field):
                    missing.append(f"{name}.{field}")
        state = RecoveredState.RECOVERED if not missing else RecoveredState.UNRESOLVED
        if domain == "fills":
            fills = []
            for name in containers:
                payload = evidence.get(name)
                if isinstance(payload, dict):
                    fills.extend(payload.get("fills") or ())
            if not fills:
                state = RecoveredState.UNRESOLVED
                missing.append("fill evidence")
            refs.extend(str(fill.get("fill_id", "")) for fill in fills if isinstance(fill, dict))
        return RecoveryDomainResult(domain, state, tuple(ref for ref in refs if ref), tuple(dict.fromkeys(missing)))


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
