"""MO-SP-006 Risk adversarial search doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_SP_006_VERSION = "MO-SP-006/1.0.0"


class RiskSearchError(ValueError):
    """Raised when adversarial search policy is incomplete or invalid."""


class ExposureTier(str, Enum):
    DE_MINIMIS = "de_minimis_exposure"
    STANDARD = "standard_exposure"
    ELEVATED = "elevated_exposure"
    CONCENTRATED = "concentrated_exposure"
    CONSTITUTIONALLY_PROHIBITED = "constitutionally_prohibited_exposure"


class HoldingPeriodClass(str, Enum):
    INTRADAY = "intraday"
    OVERNIGHT = "overnight"
    SHORT_SWING = "short_swing"
    INTERMEDIATE = "intermediate"
    LONG_HORIZON = "long_horizon"
    EXPIRATION_BOUND_DERIVATIVE = "expiration_bound_derivative"


class RiskSearchStatus(str, Enum):
    REQUIRED = "REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    ESCALATED = "ESCALATED"
    BLOCKED = "BLOCKED"
    UNSUPPORTED_ASSET_CLASS = "UNSUPPORTED_ASSET_CLASS"


class RiskSearchOutcome(str, Enum):
    RISK_ACCEPTABLE = "RISK_ACCEPTABLE"
    ADVERSE_EVIDENCE_FOUND = "ADVERSE_EVIDENCE_FOUND"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    CONFLICTED = "CONFLICTED"
    STALE = "STALE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"
    TRADE_BLOCK = "TRADE_BLOCK"


UNIVERSAL_RISK_DOMAINS = (
    "current_tradability_and_trading_status",
    "current_liquidity",
    "current_bid_ask_spread",
    "current_volatility_and_gap_state",
    "scheduled_material_event",
    "unscheduled_material_adverse_event",
    "regulatory_and_legal_adverse_event",
    "data_quality_and_source_health",
    "portfolio_concentration",
    "portfolio_correlation_and_contagion",
    "broker_restriction_and_account_eligibility",
    "thesis_fragility",
    "material_contrary_evidence",
    "source_conflict_assessment",
    "evidence_freshness_validation",
)


@dataclass(frozen=True)
class RiskSearchPolicy:
    policy_id: str
    policy_version: str
    risk_domain: str
    title: str
    purpose: str
    applicable_asset_classes: tuple[str, ...]
    applicable_instrument_classes: tuple[str, ...]
    applicable_position_directions: tuple[str, ...]
    minimum_position_size_tier: ExposureTier
    maximum_position_size_tier: ExposureTier | None
    holding_period_applicability: tuple[HoldingPeriodClass, ...]
    leverage_applicability: tuple[str, ...]
    derivatives_applicability: str
    portfolio_exposure_applicability: tuple[ExposureTier, ...]
    triggering_conditions: tuple[str, ...]
    mandatory_source_classes: tuple[str, ...]
    mandatory_source_identifiers: tuple[str, ...]
    mandatory_source_sequence: tuple[str, ...]
    conditional_sources: tuple[str, ...]
    fallback_only_sources: tuple[str, ...]
    prohibited_sources: tuple[str, ...]
    required_entity_identifiers: tuple[str, ...]
    required_instrument_identifiers: tuple[str, ...]
    query_template_ids: tuple[str, ...]
    required_time_windows: tuple[str, ...]
    maximum_lookback: str
    result_depth_limit: int
    page_or_record_limit: int
    source_freshness_limit_seconds: int
    cache_eligibility: str
    maximum_cache_age_seconds: int
    permitted_retry_count: int
    timeout_limit_seconds: int
    search_cost_class: str
    search_cost_ceiling: int
    evidence_requirements: tuple[str, ...]
    search_completion_rule: str
    insufficiency_rule: str
    conflict_rule: str
    stale_data_rule: str
    outage_rule: str
    block_rule: str
    size_reduction_rule: str
    analyst_return_rule: str
    human_escalation_rule: str
    required_audit_event_types: tuple[str, ...]
    policy_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_digest", _stable_digest(self))


@dataclass(frozen=True)
class ProposedTradeRiskContext:
    workflow_id: str
    workflow_execution_token_id: str
    decision_object_id: str
    proposed_order_id: str
    issuer_identifier: str
    ticker: str
    security_identifier: str
    exchange: str
    asset_class: str
    instrument_type: str
    position_direction: str
    proposed_quantity: float
    proposed_notional_exposure: float
    proposed_portfolio_percent: float
    expected_holding_period: HoldingPeriodClass
    leverage: float
    margin_usage: bool
    options_characteristics: Mapping[str, str] = field(default_factory=dict)
    short_sale_status: bool = False
    borrow_requirement: bool = False
    portfolio_sector_exposure: float = 0.0
    issuer_exposure: float = 0.0
    correlated_exposure: float = 0.0
    currency_exposure: str = "USD"
    commodity_exposure: str = "NONE"
    country_exposure: str = "US"
    thesis_claims: tuple[str, ...] = ()
    analyst_disposition: str = "UNKNOWN"
    evidence_package_version: str = "UNKNOWN"
    market_session_state: str = "UNKNOWN"
    broker_account_state: str = "UNKNOWN"


@dataclass(frozen=True)
class RiskSearchPlanItem:
    policy_id: str
    risk_domain: str
    status: RiskSearchStatus
    applicability_reason: str
    source_sequence: tuple[str, ...]
    query_parameters: Mapping[str, str]
    freshness_requirement_seconds: int
    depth_limit: int
    cost_limit: int
    stop_rule: str
    block_rule: str
    escalation_rule: str


@dataclass(frozen=True)
class RiskAdversarialSearchPlan:
    workflow_id: str
    decision_object_id: str
    proposed_order_id: str
    exposure_tier: ExposureTier
    holding_period_class: HoldingPeriodClass
    mandatory_searches: tuple[RiskSearchPlanItem, ...]
    conditional_searches_activated: tuple[RiskSearchPlanItem, ...]
    searches_not_applicable: tuple[RiskSearchPlanItem, ...]
    plan_version: str
    created_at: str
    plan_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_digest", _stable_digest(self))


@dataclass(frozen=True)
class RiskAdversarialSearchResult:
    plan_digest: str
    completed_domains: tuple[str, ...]
    incomplete_domains: tuple[str, ...]
    escalated_domains: tuple[str, ...]
    blocked_domains: tuple[str, ...]
    terminal_outcome: RiskSearchOutcome
    audit_events: tuple[Mapping[str, str], ...]


class RiskAdversarialPolicyRegistry:
    """Versioned immutable-at-runtime risk search policy registry."""

    def __init__(self, policies: tuple[RiskSearchPolicy, ...] | None = None) -> None:
        self._policies = tuple(policies or default_risk_search_policies())
        self._validate()

    def policies(self) -> tuple[RiskSearchPolicy, ...]:
        return self._policies

    def _validate(self) -> None:
        ids = [policy.policy_id for policy in self._policies]
        if len(ids) != len(set(ids)):
            raise RiskSearchError("duplicate risk search policy")
        for policy in self._policies:
            required = (
                policy.policy_id,
                policy.policy_version,
                policy.risk_domain,
                policy.title,
                policy.purpose,
                policy.search_completion_rule,
                policy.block_rule,
                policy.human_escalation_rule,
            )
            if any(not item for item in required):
                raise RiskSearchError(f"incomplete risk policy: {policy.policy_id}")
            if not policy.mandatory_source_sequence:
                raise RiskSearchError(f"missing source sequence: {policy.policy_id}")


class RiskSearchApplicabilityEngine:
    """Derives an immutable adversarial-search plan before execution."""

    def __init__(self, registry: RiskAdversarialPolicyRegistry | None = None) -> None:
        self.registry = registry or RiskAdversarialPolicyRegistry()

    def plan(self, context: ProposedTradeRiskContext) -> RiskAdversarialSearchPlan:
        if not context.workflow_execution_token_id:
            raise RiskSearchError("workflow execution token required")
        tier = exposure_tier(context)
        mandatory: list[RiskSearchPlanItem] = []
        conditional: list[RiskSearchPlanItem] = []
        not_applicable: list[RiskSearchPlanItem] = []
        for policy in self.registry.policies():
            item = _item(policy, context, tier)
            if context.asset_class not in policy.applicable_asset_classes:
                not_applicable.append(_replace_status(item, RiskSearchStatus.UNSUPPORTED_ASSET_CLASS, "asset class outside policy"))
            elif policy.risk_domain in UNIVERSAL_RISK_DOMAINS:
                mandatory.append(item)
            elif _applies(policy, context, tier):
                conditional.append(item)
            else:
                not_applicable.append(_replace_status(item, RiskSearchStatus.NOT_APPLICABLE, "deterministic applicability conditions false"))
        return RiskAdversarialSearchPlan(
            context.workflow_id,
            context.decision_object_id,
            context.proposed_order_id,
            tier,
            context.expected_holding_period,
            tuple(mandatory),
            tuple(conditional),
            tuple(not_applicable),
            MO_SP_006_VERSION,
            utc_timestamp(),
        )


class RiskAdversarialSearchExecutor:
    """Consumes precomputed observations; absence of evidence never proves absence of risk."""

    def execute(self, plan: RiskAdversarialSearchPlan, observations: Mapping[str, RiskSearchOutcome]) -> RiskAdversarialSearchResult:
        completed: list[str] = []
        incomplete: list[str] = []
        escalated: list[str] = []
        blocked: list[str] = []
        audit: list[Mapping[str, str]] = []
        for item in plan.mandatory_searches + plan.conditional_searches_activated:
            outcome = observations.get(item.risk_domain, RiskSearchOutcome.EVIDENCE_INCOMPLETE)
            audit.append(MappingProxyType({"risk_domain": item.risk_domain, "policy_id": item.policy_id, "outcome": outcome.value, "plan_digest": plan.plan_digest}))
            if outcome is RiskSearchOutcome.RISK_ACCEPTABLE:
                completed.append(item.risk_domain)
            elif outcome in {RiskSearchOutcome.ESCALATE_TO_HUMAN, RiskSearchOutcome.CONFLICTED}:
                escalated.append(item.risk_domain)
            elif outcome is RiskSearchOutcome.TRADE_BLOCK:
                blocked.append(item.risk_domain)
            else:
                incomplete.append(item.risk_domain)
        terminal = RiskSearchOutcome.RISK_ACCEPTABLE
        if blocked:
            terminal = RiskSearchOutcome.TRADE_BLOCK
        elif escalated:
            terminal = RiskSearchOutcome.ESCALATE_TO_HUMAN
        elif incomplete:
            terminal = RiskSearchOutcome.EVIDENCE_INCOMPLETE
        return RiskAdversarialSearchResult(plan.plan_digest, tuple(completed), tuple(incomplete), tuple(escalated), tuple(blocked), terminal, tuple(audit))


def exposure_tier(context: ProposedTradeRiskContext) -> ExposureTier:
    metric = max(context.proposed_portfolio_percent, context.issuer_exposure, context.portfolio_sector_exposure, context.correlated_exposure)
    if context.leverage > 3.0 or metric > 0.30:
        return ExposureTier.CONSTITUTIONALLY_PROHIBITED
    if metric > 0.20:
        return ExposureTier.CONCENTRATED
    if metric > 0.10:
        return ExposureTier.ELEVATED
    if metric < 0.01:
        return ExposureTier.DE_MINIMIS
    return ExposureTier.STANDARD


def default_risk_search_policies() -> tuple[RiskSearchPolicy, ...]:
    policies = [_policy(domain, universal=True) for domain in UNIVERSAL_RISK_DOMAINS]
    policies.extend(
        [
            _policy("earnings_risk", holding=(HoldingPeriodClass.OVERNIGHT, HoldingPeriodClass.SHORT_SWING, HoldingPeriodClass.INTERMEDIATE, HoldingPeriodClass.LONG_HORIZON)),
            _policy("corporate_action_risk", holding=(HoldingPeriodClass.OVERNIGHT, HoldingPeriodClass.SHORT_SWING, HoldingPeriodClass.INTERMEDIATE, HoldingPeriodClass.LONG_HORIZON, HoldingPeriodClass.EXPIRATION_BOUND_DERIVATIVE)),
            _policy("financing_and_debt_maturity_risk", min_tier=ExposureTier.ELEVATED, holding=(HoldingPeriodClass.INTERMEDIATE, HoldingPeriodClass.LONG_HORIZON)),
            _policy("bankruptcy_and_solvency_risk", min_tier=ExposureTier.ELEVATED, holding=(HoldingPeriodClass.INTERMEDIATE, HoldingPeriodClass.LONG_HORIZON)),
            _policy("short_interest_and_borrow_risk", directions=("short",), sources=("SRC-BROKER-OF-RECORD", "SRC-US-SEC-EDGAR")),
            _policy("options_assignment_and_exercise_risk", instruments=("option",), holding=(HoldingPeriodClass.EXPIRATION_BOUND_DERIVATIVE,), sources=("SRC-BROKER-OF-RECORD", "SRC-LICENSED-SIP-MARKET-DATA")),
            _policy("macro_sensitivity", min_tier=ExposureTier.ELEVATED, sources=("SRC-US-BLS", "SRC-US-FRED-DISTRIBUTION")),
            _policy("geopolitical_exposure", min_tier=ExposureTier.ELEVATED),
            _policy("currency_exposure", min_tier=ExposureTier.ELEVATED),
            _policy("commodity_sensitivity", min_tier=ExposureTier.ELEVATED),
            _policy("execution_critical_adverse_conditions", sources=("SRC-BROKER-OF-RECORD", "SRC-LICENSED-SIP-MARKET-DATA")),
        ]
    )
    return tuple(policies)


def _policy(
    domain: str,
    *,
    universal: bool = False,
    min_tier: ExposureTier = ExposureTier.DE_MINIMIS,
    directions: tuple[str, ...] = ("long", "short"),
    instruments: tuple[str, ...] = ("equity", "option"),
    holding: tuple[HoldingPeriodClass, ...] = tuple(HoldingPeriodClass),
    sources: tuple[str, ...] = ("SRC-LICENSED-SIP-MARKET-DATA", "SRC-US-SEC-EDGAR", "SRC-US-SEC-ENFORCEMENT"),
) -> RiskSearchPolicy:
    return RiskSearchPolicy(
        f"RASP-{domain.upper()}",
        "1.0.0",
        domain,
        domain.replace("_", " ").title(),
        "Search for contrary evidence and material failure modes before capital exposure.",
        ("equity", "option"),
        instruments,
        directions,
        min_tier,
        None,
        holding,
        ("cash", "margin", "leveraged"),
        "required_for_options" if "option" in instruments else "not_applicable",
        tuple(ExposureTier),
        ("universal" if universal else "conditional", domain),
        ("market", "filing", "broker", "regulatory"),
        sources,
        sources,
        (),
        (),
        ("SRC-SEARCH-ENGINE-DISCOVERY", "SRC-SOCIAL-EARLY-WARNING", "SRC-PROHIBITED-MODEL-MEMORY"),
        ("issuer_identifier",),
        ("security_identifier", "ticker"),
        (f"QRY-{domain.upper()}",),
        ("entry_window", "holding_period", "exit_window"),
        "30d",
        10,
        10,
        60,
        "cache_allowed_if_current",
        60,
        1,
        30,
        "bounded_public_or_entitled",
        10,
        ("raw_evidence_reference", "source_timestamp", "retrieval_timestamp", "adverse_evidence_state"),
        "complete only when mandatory adverse evidence checks are terminal",
        "incomplete blocks or escalates; absence of results is not proof",
        "conflict escalates to human risk authority",
        "stale data cannot satisfy trade eligibility",
        "source outage produces source unavailable state",
        "trade blocks on prohibited tier, unresolved broker restriction, or critical adverse evidence",
        "larger position may be reduced only by explicit Risk policy result",
        "return to Analyst when thesis verification uncertainty is material",
        "human escalation when capital exposure depends on unresolved uncertainty",
        ("plan_created", "source_authorized", "search_executed", "terminal_state_recorded"),
    )


def _applies(policy: RiskSearchPolicy, context: ProposedTradeRiskContext, tier: ExposureTier) -> bool:
    if context.instrument_type not in policy.applicable_instrument_classes:
        return False
    if context.position_direction not in policy.applicable_position_directions:
        return False
    if context.expected_holding_period not in policy.holding_period_applicability:
        return False
    if list(ExposureTier).index(tier) < list(ExposureTier).index(policy.minimum_position_size_tier):
        return False
    return True


def _item(policy: RiskSearchPolicy, context: ProposedTradeRiskContext, tier: ExposureTier) -> RiskSearchPlanItem:
    status = RiskSearchStatus.BLOCKED if tier is ExposureTier.CONSTITUTIONALLY_PROHIBITED else RiskSearchStatus.REQUIRED
    reason = f"asset={context.asset_class}; instrument={context.instrument_type}; tier={tier.value}; holding={context.expected_holding_period.value}"
    return RiskSearchPlanItem(
        policy.policy_id,
        policy.risk_domain,
        status,
        reason,
        policy.mandatory_source_sequence,
        MappingProxyType({"ticker": context.ticker, "security_identifier": context.security_identifier, "decision_object_id": context.decision_object_id}),
        policy.source_freshness_limit_seconds,
        policy.result_depth_limit,
        policy.search_cost_ceiling,
        policy.search_completion_rule,
        policy.block_rule,
        policy.human_escalation_rule,
    )


def _replace_status(item: RiskSearchPlanItem, status: RiskSearchStatus, reason: str) -> RiskSearchPlanItem:
    return RiskSearchPlanItem(item.policy_id, item.risk_domain, status, reason, item.source_sequence, item.query_parameters, item.freshness_requirement_seconds, item.depth_limit, item.cost_limit, item.stop_rule, item.block_rule, item.escalation_rule)


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return dict(value)
    if is_dataclass(value):
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name not in {"policy_digest", "plan_digest"}}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
