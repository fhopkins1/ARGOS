"""Executable Trader constitutional governance records and fail-closed checks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence


TRADER_GOVERNANCE_VERSION = "TRADER-GOV-001-012/1.0.0"


class TraderGovernanceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class TraderOperatingMode(str, Enum):
    DISABLED = "Disabled"
    READ_ONLY = "Read-Only"
    DRY_RUN = "Dry Run"
    SIMULATION = "Simulation"
    PAPER = "Paper"
    LIVE = "Live"
    EMERGENCY_LIQUIDATION = "Emergency Liquidation"
    LOCKDOWN = "Lockdown"


class CertificationVerdict(str, Enum):
    UNCONDITIONAL_PASS = "UNCONDITIONAL PASS"
    FAIL = "FAIL"


class TorrVerdict(str, Enum):
    INTERNALLY_READY = "Internally Ready"
    INTERNALLY_READY_WITH_OBSERVATIONS = "Internally Ready with Observations"
    INTERNALLY_NOT_READY = "Internally Not Ready"


SUPPORTED_INSTRUMENTS = frozenset({"cash_equity", "spot_crypto", "paper_trade"})
SUPPORTED_ORDER_TYPES = frozenset({"market", "limit"})
SUPPORTED_ACCOUNT_TYPES = frozenset({"paper_brokerage", "cash_brokerage"})
EXCLUDED_FINANCIAL_SCOPE = frozenset({"margin", "collateral", "securities_lending", "leveraged_position", "derivative_collateral", "assignment_obligation"})


FINANCIAL_RESOURCE_OWNERS: Mapping[str, str] = {
    "Cash": "Financial Truth Office",
    "Available Cash": "Financial Truth Office",
    "Reserved Cash": "Financial Truth Office",
    "Unsettled Cash": "Settlement Authority",
    "Buying Power": "Financial Truth Office",
    "Fees": "Settlement Authority",
    "Commissions": "Settlement Authority",
    "Settlement Obligations": "Settlement Authority",
    "Collateral": "Collateral Authority",
    "Margin Requirements": "Margin Authority",
    "Account Balance": "Financial Truth Office",
    "Account Equity": "Financial Truth Office",
    "Net Liquidation Value": "Financial Truth Office",
    "Currency Balances": "Financial Truth Office",
    "Multi-currency Conversion Obligations": "Settlement Authority",
    "Broker Account Financial State": "Broker Truth Authority",
}


TRADER_OBJECT_REGISTRY: Mapping[str, Mapping[str, str]] = {
    "Trader Execution Mandate": {"owner": "Trader Office", "authority": "TRADER-GOV-001", "lifecycle": "TRADER-RM-001-005"},
    "Execution Plan": {"owner": "Trade Execution Office", "authority": "TRADER-GOV-001", "lifecycle": "TRADER-RM-001-005"},
    "Canonical Order": {"owner": "Order Management Office", "authority": "TRADER-RM-001-005", "lifecycle": "TRADER-RM-001-005"},
    "Broker Order": {"owner": "Broker Integration Office", "authority": "TRADER-RM-001-005", "lifecycle": "TRADER-RM-001-005"},
    "Broker Event": {"owner": "Broker Integration Office", "authority": "TRADER-RM-001-005", "lifecycle": "TRADER-RM-001-005"},
    "Canonical Fill Record": {"owner": "Order Management Office", "authority": "TRADER-RM-001-005", "lifecycle": "TRADER-RM-001-005"},
    "Canonical Position": {"owner": "Position Management Office", "authority": "TRADER-RM-001-005", "lifecycle": "TRADER-RM-001-005"},
    "Reconciliation Object": {"owner": "Trader Office", "authority": "TRADER-GOV-008", "lifecycle": "TRADER-RM-001-005"},
    "Trader Execution Case File": {"owner": "Trader Office", "authority": "TRADER-GOV-011", "lifecycle": "TRADER-RM-001-005"},
}


LIFECYCLE_STATES: Mapping[str, tuple[str, ...]] = {
    "Trader Execution Mandate": ("created", "validated", "planned", "consumed", "cancelled", "failed"),
    "Execution Plan": ("created", "validated", "orders_generated", "completed", "failed"),
    "Canonical Order": ("created", "validated", "submitted", "partially_filled", "filled", "cancelled", "rejected", "failed"),
    "Broker Order": ("submitted", "acknowledged", "accepted", "rejected", "cancelled", "terminal"),
    "Broker Event": ("received", "validated", "normalized", "reconciled", "quarantined"),
    "Canonical Fill Record": ("observed", "validated", "position_applied", "quality_reviewed"),
    "Canonical Position": ("opened", "adjusted", "partially_closed", "closed", "reconciled"),
    "Reconciliation Object": ("opened", "investigating", "corrected", "quarantined", "closed"),
    "Trader Execution Case File": ("assembled", "validated", "delivered", "custody_acknowledged", "terminal_failure"),
}


@dataclass(frozen=True)
class GovernanceDecision:
    status: TraderGovernanceStatus
    findings: tuple[str, ...]


@dataclass(frozen=True)
class AuthorityInputs:
    executive_intent: bool
    authorization: bool
    risk_certification: bool
    operating_mode_authority: bool
    account_authority: bool = True
    instrument_authority: bool = True
    broker_authority: bool = True
    conflicting_authority: bool = False


@dataclass(frozen=True)
class ExecutionScope:
    instrument_class: str
    order_type: str
    account_type: str
    financial_resource_owners: Mapping[str, str]
    buying_power_verified: bool
    settlement_owner_known: bool
    financial_discrepancy_material: bool = False
    margin_or_collateral_required: bool = False


@dataclass(frozen=True)
class TemporalContext:
    authoritative_time_present: bool
    timezone_verified: bool
    clock_drift_seconds: int
    permitted_drift_seconds: int
    authority_effective: bool
    authority_expired: bool
    evidence_fresh: bool
    market_state_known: bool
    market_open: bool


@dataclass(frozen=True)
class HistorianCompletionContext:
    case_file_assembled: bool
    case_file_validated: bool
    durable_delivery_completed: bool
    custody_acknowledged: bool


def validate_execution_authority(inputs: AuthorityInputs) -> GovernanceDecision:
    findings = []
    for field in ("executive_intent", "authorization", "risk_certification", "operating_mode_authority", "account_authority", "instrument_authority", "broker_authority"):
        if not getattr(inputs, field):
            findings.append(f"missing required authority: {field}")
    if inputs.conflicting_authority:
        findings.append("materially conflicting controlling authority")
    return _decision(findings)


def resolve_operating_mode(active_modes: Sequence[TraderOperatingMode]) -> GovernanceDecision:
    findings = []
    if len(active_modes) != 1:
        findings.append("exactly one active Trader operating mode is required")
    return _decision(findings)


def validate_execution_scope(scope: ExecutionScope) -> GovernanceDecision:
    findings = []
    if scope.instrument_class not in SUPPORTED_INSTRUMENTS:
        findings.append(f"unsupported instrument class: {scope.instrument_class}")
    if scope.order_type not in SUPPORTED_ORDER_TYPES:
        findings.append(f"unsupported order type: {scope.order_type}")
    if scope.account_type not in SUPPORTED_ACCOUNT_TYPES:
        findings.append(f"unsupported account type: {scope.account_type}")
    if scope.margin_or_collateral_required:
        findings.append("margin and collateral are excluded from initial certification scope")
    if not scope.buying_power_verified:
        findings.append("buying power cannot be verified")
    if not scope.settlement_owner_known:
        findings.append("settlement responsibility is ambiguous")
    if scope.financial_discrepancy_material:
        findings.append("material financial truth discrepancy remains unresolved")
    missing = sorted(resource for resource in FINANCIAL_RESOURCE_OWNERS if resource not in scope.financial_resource_owners)
    if missing:
        findings.append("financial resource ownership incomplete: " + ", ".join(missing))
    duplicate_owner_errors = [resource for resource, owner in scope.financial_resource_owners.items() if not owner]
    if duplicate_owner_errors:
        findings.append("financial resources must have exactly one explicit owner")
    return _decision(findings)


def validate_financial_resource_ownership(owners: Mapping[str, str]) -> GovernanceDecision:
    missing = sorted(resource for resource in FINANCIAL_RESOURCE_OWNERS if resource not in owners or not owners[resource])
    trader_owned = sorted(resource for resource, owner in owners.items() if owner == "Trader Office")
    findings = []
    if missing:
        findings.append("missing explicit constitutional owner: " + ", ".join(missing))
    if trader_owned:
        findings.append("Trader may not own financial account truth resources: " + ", ".join(trader_owned))
    return _decision(findings)


verify_financial_resource_ownership = validate_financial_resource_ownership


def validate_temporal_context(context: TemporalContext) -> GovernanceDecision:
    findings = []
    if not context.authoritative_time_present:
        findings.append("authoritative time cannot be established")
    if not context.timezone_verified:
        findings.append("timestamp timezone is missing or ambiguous")
    if context.clock_drift_seconds > context.permitted_drift_seconds:
        findings.append("clock drift exceeds permitted tolerance")
    if not context.authority_effective or context.authority_expired:
        findings.append("authority is not effective or has expired")
    if not context.evidence_fresh:
        findings.append("required Trader evidence is stale")
    if not context.market_state_known or not context.market_open:
        findings.append("market state is unknown or closed for execution")
    return _decision(findings)


def validate_historian_completion(context: HistorianCompletionContext) -> GovernanceDecision:
    findings = []
    if not context.case_file_assembled:
        findings.append("Trader Execution Case File is not assembled")
    if not context.case_file_validated:
        findings.append("Trader Execution Case File is not validated")
    if not context.durable_delivery_completed:
        findings.append("durable evidence delivery is incomplete")
    if not context.custody_acknowledged:
        findings.append("Historian or designated custodian has not acknowledged custody")
    return _decision(findings)


def validate_torr_verdict(verdict: str) -> GovernanceDecision:
    findings = []
    if verdict not in {item.value for item in TorrVerdict}:
        findings.append(f"unsupported TORR readiness verdict: {verdict}")
    if verdict in {CertificationVerdict.UNCONDITIONAL_PASS.value, "Conditional Pass", "Operational Pass"}:
        findings.append("TORR verdict cannot constitute independent certification")
    return _decision(findings)


def validate_certification_verdict(verdict: str, unresolved_findings: int = 0) -> GovernanceDecision:
    findings = []
    if verdict not in {item.value for item in CertificationVerdict}:
        findings.append(f"prohibited certification verdict: {verdict}")
    if verdict == CertificationVerdict.UNCONDITIONAL_PASS.value and unresolved_findings:
        findings.append("unconditional pass prohibited with unresolved findings")
    return _decision(findings)


def validate_object_registry() -> GovernanceDecision:
    findings = []
    for name, record in TRADER_OBJECT_REGISTRY.items():
        if not record.get("owner") or not record.get("authority") or not record.get("lifecycle"):
            findings.append(f"incomplete object registry entry: {name}")
        if name not in LIFECYCLE_STATES or not LIFECYCLE_STATES[name]:
            findings.append(f"missing lifecycle state model: {name}")
    return _decision(findings)


def _decision(findings: Sequence[str]) -> GovernanceDecision:
    normalized = tuple(findings)
    return GovernanceDecision(TraderGovernanceStatus.FAIL if normalized else TraderGovernanceStatus.PASS, normalized)
