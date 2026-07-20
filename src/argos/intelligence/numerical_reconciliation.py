"""MO-TR-005 numerical tolerance and market-data reconciliation doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_005_VERSION = "MO-TR-005/1.0.0"


class NumericalDomain(str, Enum):
    LAST_TRADE = "LAST_TRADE"
    BID = "BID"
    ASK = "ASK"
    MIDPOINT = "MIDPOINT"
    OFFICIAL_OPEN = "OFFICIAL_OPEN"
    OFFICIAL_CLOSE = "OFFICIAL_CLOSE"
    INTRADAY_HIGH = "INTRADAY_HIGH"
    INTRADAY_LOW = "INTRADAY_LOW"
    VOLUME = "VOLUME"
    HISTORICAL_BAR = "HISTORICAL_BAR"
    NAV = "NAV"
    YIELD = "YIELD"
    INTEREST_RATE = "INTEREST_RATE"
    OPTION_PREMIUM = "OPTION_PREMIUM"
    IMPLIED_VOLATILITY = "IMPLIED_VOLATILITY"
    OPTION_GREEK = "OPTION_GREEK"
    FX_RATE = "FX_RATE"
    CRYPTO_PRICE = "CRYPTO_PRICE"
    PORTFOLIO_VALUATION = "PORTFOLIO_VALUATION"
    CASH_BALANCE = "CASH_BALANCE"
    BUYING_POWER = "BUYING_POWER"
    POSITION_QUANTITY = "POSITION_QUANTITY"
    BROKER_EXECUTION_VALUE = "BROKER_EXECUTION_VALUE"
    OTHER_NUMERICAL_FACT = "OTHER_NUMERICAL_FACT"


class NumericalObservationType(str, Enum):
    EXECUTABLE_PRICE = "EXECUTABLE_PRICE"
    INDICATIVE_PRICE = "INDICATIVE_PRICE"
    LAST_TRADE = "LAST_TRADE"
    BID = "BID"
    ASK = "ASK"
    MIDPOINT = "MIDPOINT"
    OFFICIAL_CONSOLIDATED_PRICE = "OFFICIAL_CONSOLIDATED_PRICE"
    PRIMARY_MARKET_PRICE = "PRIMARY_MARKET_PRICE"
    VENUE_SPECIFIC_PRICE = "VENUE_SPECIFIC_PRICE"
    BROKER_DISPLAYED_PRICE = "BROKER_DISPLAYED_PRICE"
    DELAYED_PRICE = "DELAYED_PRICE"
    OPENING_AUCTION_PRICE = "OPENING_AUCTION_PRICE"
    CLOSING_AUCTION_PRICE = "CLOSING_AUCTION_PRICE"
    OFFICIAL_OPEN = "OFFICIAL_OPEN"
    OFFICIAL_CLOSE = "OFFICIAL_CLOSE"
    INTRADAY_HIGH = "INTRADAY_HIGH"
    INTRADAY_LOW = "INTRADAY_LOW"
    MODEL_DERIVED_FAIR_VALUE = "MODEL_DERIVED_FAIR_VALUE"
    NET_ASSET_VALUE = "NET_ASSET_VALUE"
    INDICATIVE_NET_ASSET_VALUE = "INDICATIVE_NET_ASSET_VALUE"
    SETTLEMENT_PRICE = "SETTLEMENT_PRICE"
    MARK_PRICE = "MARK_PRICE"
    INDEX_VALUE = "INDEX_VALUE"


class ToleranceCombinationRule(str, Enum):
    ABSOLUTE_ONLY = "ABSOLUTE_ONLY"
    RELATIVE_ONLY = "RELATIVE_ONLY"
    ABSOLUTE_OR_RELATIVE = "ABSOLUTE_OR_RELATIVE"
    ABSOLUTE_AND_RELATIVE = "ABSOLUTE_AND_RELATIVE"
    TICK_ONLY = "TICK_ONLY"
    TICK_OR_ABSOLUTE = "TICK_OR_ABSOLUTE"
    TICK_AND_TIME = "TICK_AND_TIME"
    EXACT_MATCH = "EXACT_MATCH"
    DOMAIN_SPECIFIC = "DOMAIN_SPECIFIC"


class NumericalReconciliationOutcome(str, Enum):
    ACCEPTED = "ACCEPTED"
    WARNING = "WARNING"
    REFRESH_REQUIRED = "REFRESH_REQUIRED"
    ALTERNATE_SOURCE_REQUIRED = "ALTERNATE_SOURCE_REQUIRED"
    QUARANTINE_SOURCE = "QUARANTINE_SOURCE"
    ESCALATE_ANALYST = "ESCALATE_ANALYST"
    ESCALATE_RISK = "ESCALATE_RISK"
    EXECUTION_DEFERRED = "EXECUTION_DEFERRED"
    TRADE_PROHIBITED = "TRADE_PROHIBITED"
    NONCOMPARABLE = "NONCOMPARABLE"
    UNKNOWN = "UNKNOWN"


class DataQualityStatus(str, Enum):
    VALID = "VALID"
    TIME_MISALIGNED = "TIME_MISALIGNED"
    STALE_SOURCE = "STALE_SOURCE"
    DELAYED_SOURCE = "DELAYED_SOURCE"
    WRONG_VENUE = "WRONG_VENUE"
    WRONG_INSTRUMENT = "WRONG_INSTRUMENT"
    WRONG_CURRENCY = "WRONG_CURRENCY"
    WRONG_UNIT = "WRONG_UNIT"
    BAD_DECIMAL_PLACEMENT = "BAD_DECIMAL_PLACEMENT"
    INVALID_SIGN = "INVALID_SIGN"
    IMPOSSIBLE_NEGATIVE_VALUE = "IMPOSSIBLE_NEGATIVE_VALUE"
    ZERO_VALUE_CORRUPTION = "ZERO_VALUE_CORRUPTION"
    SOURCE_PRECISION_LOSS = "SOURCE_PRECISION_LOSS"
    UNKNOWN_ANOMALY = "UNKNOWN_ANOMALY"


@dataclass(frozen=True)
class NumericalDomainPolicy:
    domain: NumericalDomain
    fact_definition: str
    permitted_observation_types: tuple[NumericalObservationType, ...]
    authority_requirements: tuple[str, ...]
    unit: str
    currency_required: bool
    price_adjustment_basis: str
    venue_treatment: str
    market_session_treatment: str
    governing_timestamp: str
    time_alignment_window_seconds: int
    maximum_freshness_age_seconds: int
    delayed_data_treatment: str
    absolute_tolerance: Decimal
    relative_tolerance: Decimal
    tolerance_combination_rule: ToleranceCombinationRule
    tick_size: Decimal
    tick_size_treatment: str
    rounding_treatment: str
    aggregation_treatment: str
    outlier_rule: str
    materiality_threshold: Decimal
    required_evidence_fields: tuple[str, ...]
    policy_version: str = MO_TR_005_VERSION
    effective_date: str = "2026-07-20T00:00:00Z"
    retirement_date: str = ""
    superseding_policy_version: str = ""


@dataclass(frozen=True)
class NumericalObservation:
    observation_id: str
    workflow_id: str
    domain: NumericalDomain
    observation_type: NumericalObservationType
    instrument_id: str
    source_id: str
    raw_value: str
    raw_unit: str
    raw_currency: str
    raw_precision: str
    event_time: str
    market_time: str
    retrieval_time: str
    venue: str
    market_session: str
    adjustment_basis: str
    tick_size: str
    rounding_mode: str
    delayed: bool
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class NormalizedNumericalObservation:
    observation_id: str
    raw_value: str
    raw_unit: str
    raw_currency: str
    raw_precision: str
    normalized_value: Decimal | None
    normalized_unit: str
    normalized_currency: str
    conversion_rule: str
    conversion_inputs: Mapping[str, str]
    conversion_version: str
    rounding_rule: str
    normalization_timestamp: str
    normalization_status: DataQualityStatus
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class NumericalReconciliationRecord:
    reconciliation_id: str
    workflow_id: str
    fact_domain: NumericalDomain
    observation_ids: tuple[str, ...]
    observation_hashes: tuple[str, ...]
    signed_difference: Decimal | None
    absolute_difference: Decimal | None
    relative_difference: Decimal | None
    percentage_difference: Decimal | None
    basis_point_difference: Decimal | None
    tick_difference: Decimal | None
    time_difference_seconds: int | None
    freshness_difference_seconds: int | None
    materiality_amount: Decimal | None
    materiality_ratio: Decimal | None
    data_quality_status: DataQualityStatus
    outcome: NumericalReconciliationOutcome
    rule_identifier: str
    doctrine_version: str
    required_action: str
    evidence_references: tuple[str, ...]
    created_at: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class NumericalDomainPolicyRegistry:
    def __init__(self, policies: Mapping[NumericalDomain, NumericalDomainPolicy] | None = None) -> None:
        self._policies = MappingProxyType(dict(policies or default_numerical_domain_policies()))

    def policy(self, domain: NumericalDomain) -> NumericalDomainPolicy:
        return self._policies[domain]


class NumericalNormalizationEngine:
    def normalize(self, observation: NumericalObservation, policy: NumericalDomainPolicy) -> NormalizedNumericalObservation:
        try:
            value = Decimal(observation.raw_value)
        except (InvalidOperation, TypeError):
            return _normalized(observation, None, policy.unit, observation.raw_currency, "parse_decimal", DataQualityStatus.BAD_DECIMAL_PLACEMENT)
        if value < 0 and observation.domain in {NumericalDomain.BID, NumericalDomain.ASK, NumericalDomain.LAST_TRADE, NumericalDomain.VOLUME, NumericalDomain.CASH_BALANCE, NumericalDomain.POSITION_QUANTITY}:
            return _normalized(observation, value, policy.unit, observation.raw_currency, "identity", DataQualityStatus.IMPOSSIBLE_NEGATIVE_VALUE)
        if observation.raw_unit != policy.unit:
            return _normalized(observation, value, policy.unit, observation.raw_currency, "rejected_unknown_unit", DataQualityStatus.WRONG_UNIT)
        if policy.currency_required and not observation.raw_currency:
            return _normalized(observation, value, policy.unit, "", "rejected_missing_currency", DataQualityStatus.WRONG_CURRENCY)
        rounded = value
        if policy.rounding_treatment == "ROUND_TO_TICK" and policy.tick_size > 0:
            rounded = (value / policy.tick_size).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * policy.tick_size
        return _normalized(observation, rounded, policy.unit, observation.raw_currency, "identity", DataQualityStatus.VALID)


class NumericalReconciliationLedger:
    def __init__(self) -> None:
        self._records: dict[str, NumericalReconciliationRecord] = {}

    def append(self, record: NumericalReconciliationRecord) -> None:
        if record.reconciliation_id in self._records:
            raise ValueError("numerical reconciliations are append-only")
        self._records[record.reconciliation_id] = record

    def all_records(self) -> tuple[NumericalReconciliationRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))


class NumericalReconciliationEngine:
    def __init__(self, registry: NumericalDomainPolicyRegistry | None = None, normalizer: NumericalNormalizationEngine | None = None, ledger: NumericalReconciliationLedger | None = None) -> None:
        self.registry = registry or NumericalDomainPolicyRegistry()
        self.normalizer = normalizer or NumericalNormalizationEngine()
        self.ledger = ledger or NumericalReconciliationLedger()

    def reconcile(self, left: NumericalObservation, right: NumericalObservation) -> NumericalReconciliationRecord:
        if left.domain is not right.domain:
            return self._record(left, right, None, None, None, None, None, None, None, None, DataQualityStatus.UNKNOWN_ANOMALY, NumericalReconciliationOutcome.NONCOMPARABLE, "different_numerical_domains", "route_to_analyst")
        policy = self.registry.policy(left.domain)
        if left.observation_type not in policy.permitted_observation_types or right.observation_type not in policy.permitted_observation_types or left.observation_type is not right.observation_type:
            return self._record(left, right, None, None, None, None, None, None, None, None, DataQualityStatus.UNKNOWN_ANOMALY, NumericalReconciliationOutcome.NONCOMPARABLE, "different_price_meanings", "preserve_and_recollect_authorized_observation")
        if left.instrument_id != right.instrument_id:
            return self._record(left, right, None, None, None, None, None, None, None, None, DataQualityStatus.WRONG_INSTRUMENT, NumericalReconciliationOutcome.TRADE_PROHIBITED, "instrument_mismatch", "block_affected_instrument")
        if policy.venue_treatment == "VENUE_MUST_MATCH" and left.venue != right.venue:
            return self._record(left, right, None, None, None, None, None, None, None, None, DataQualityStatus.WRONG_VENUE, NumericalReconciliationOutcome.NONCOMPARABLE, "venue_mismatch", "recollect_same_venue")
        if policy.market_session_treatment == "SESSION_MUST_MATCH" and left.market_session != right.market_session:
            return self._record(left, right, None, None, None, None, None, None, None, None, DataQualityStatus.TIME_MISALIGNED, NumericalReconciliationOutcome.NONCOMPARABLE, "session_mismatch", "recollect_same_session")
        left_norm = self.normalizer.normalize(left, policy)
        right_norm = self.normalizer.normalize(right, policy)
        if left_norm.normalization_status is not DataQualityStatus.VALID or right_norm.normalization_status is not DataQualityStatus.VALID:
            status = left_norm.normalization_status if left_norm.normalization_status is not DataQualityStatus.VALID else right_norm.normalization_status
            return self._record(left, right, None, None, None, None, None, None, None, None, status, NumericalReconciliationOutcome.TRADE_PROHIBITED, "normalization_failed", "quarantine_and_recollect")
        if policy.currency_required and left_norm.normalized_currency != right_norm.normalized_currency:
            return self._record(left, right, None, None, None, None, None, None, None, None, DataQualityStatus.WRONG_CURRENCY, NumericalReconciliationOutcome.TRADE_PROHIBITED, "currency_mismatch", "block_until_currency_resolved")
        time_diff = abs(_epochish(left.market_time) - _epochish(right.market_time))
        if time_diff > policy.time_alignment_window_seconds:
            return self._record(left, right, None, None, None, None, None, None, time_diff, None, DataQualityStatus.TIME_MISALIGNED, NumericalReconciliationOutcome.REFRESH_REQUIRED, "time_window_exceeded", "refresh_same_market_time")
        freshness = max(abs(_epochish(left.retrieval_time) - _epochish(left.market_time)), abs(_epochish(right.retrieval_time) - _epochish(right.market_time)))
        if freshness > policy.maximum_freshness_age_seconds:
            return self._record(left, right, None, None, None, None, None, None, time_diff, freshness, DataQualityStatus.STALE_SOURCE, NumericalReconciliationOutcome.EXECUTION_DEFERRED, "freshness_window_exceeded", "refresh_before_execution")
        if left.delayed or right.delayed:
            return self._record(left, right, None, None, None, None, None, None, time_diff, freshness, DataQualityStatus.DELAYED_SOURCE, NumericalReconciliationOutcome.EXECUTION_DEFERRED, "delayed_data_not_executable", "defer_execution")

        signed = left_norm.normalized_value - right_norm.normalized_value  # type: ignore[operator]
        absolute = abs(signed)
        base = abs(right_norm.normalized_value) if right_norm.normalized_value else Decimal("0")  # type: ignore[arg-type]
        relative = absolute / base if base else Decimal("0") if absolute == 0 else Decimal("Infinity")
        ticks = absolute / policy.tick_size if policy.tick_size > 0 else None
        accepted = _within_tolerance(policy, absolute, relative, ticks)
        outcome = NumericalReconciliationOutcome.ACCEPTED if accepted else NumericalReconciliationOutcome.ESCALATE_RISK
        action = "accept_without_averaging" if accepted else "preserve_conflict_and_block_promotion"
        materiality_ratio = absolute / policy.materiality_threshold if policy.materiality_threshold > 0 else None
        return self._record(left, right, signed, absolute, relative, relative * Decimal("100"), relative * Decimal("10000"), ticks, time_diff, freshness, DataQualityStatus.VALID, outcome, policy.tolerance_combination_rule.value, action, absolute, materiality_ratio)

    def _record(
        self,
        left: NumericalObservation,
        right: NumericalObservation,
        signed: Decimal | None,
        absolute: Decimal | None,
        relative: Decimal | None,
        percentage: Decimal | None,
        bps: Decimal | None,
        ticks: Decimal | None,
        time_diff: int | None,
        freshness: int | None,
        quality: DataQualityStatus,
        outcome: NumericalReconciliationOutcome,
        rule: str,
        action: str,
        materiality_amount: Decimal | None = None,
        materiality_ratio: Decimal | None = None,
    ) -> NumericalReconciliationRecord:
        record = NumericalReconciliationRecord(
            _stable_id("NUMREC", left.observation_id, right.observation_id, rule, outcome.value),
            left.workflow_id or right.workflow_id,
            left.domain,
            (left.observation_id, right.observation_id),
            (_stable_digest(left), _stable_digest(right)),
            signed,
            absolute,
            relative,
            percentage,
            bps,
            ticks,
            time_diff,
            freshness,
            materiality_amount,
            materiality_ratio,
            quality,
            outcome,
            rule,
            MO_TR_005_VERSION,
            action,
            tuple(left.evidence_references + right.evidence_references),
            utc_timestamp(),
        )
        self.ledger.append(record)
        return record


def default_numerical_domain_policies() -> Mapping[NumericalDomain, NumericalDomainPolicy]:
    policies = {
        NumericalDomain.BID: _policy(NumericalDomain.BID, NumericalObservationType.BID, Decimal("0.01"), Decimal("0.0001"), ToleranceCombinationRule.TICK_OR_ABSOLUTE, Decimal("0.01"), 2, 15),
        NumericalDomain.ASK: _policy(NumericalDomain.ASK, NumericalObservationType.ASK, Decimal("0.01"), Decimal("0.0001"), ToleranceCombinationRule.TICK_OR_ABSOLUTE, Decimal("0.01"), 2, 15),
        NumericalDomain.LAST_TRADE: _policy(NumericalDomain.LAST_TRADE, NumericalObservationType.LAST_TRADE, Decimal("0.01"), Decimal("0.0001"), ToleranceCombinationRule.TICK_AND_TIME, Decimal("0.01"), 2, 15),
        NumericalDomain.OFFICIAL_CLOSE: _policy(NumericalDomain.OFFICIAL_CLOSE, NumericalObservationType.OFFICIAL_CLOSE, Decimal("0.0001"), Decimal("0.000001"), ToleranceCombinationRule.ABSOLUTE_AND_RELATIVE, Decimal("0.01"), 60, 86400),
        NumericalDomain.OFFICIAL_OPEN: _policy(NumericalDomain.OFFICIAL_OPEN, NumericalObservationType.OFFICIAL_OPEN, Decimal("0.0001"), Decimal("0.000001"), ToleranceCombinationRule.ABSOLUTE_AND_RELATIVE, Decimal("0.01"), 60, 86400),
        NumericalDomain.VOLUME: _policy(NumericalDomain.VOLUME, NumericalObservationType.INDEX_VALUE, Decimal("0"), Decimal("0"), ToleranceCombinationRule.EXACT_MATCH, Decimal("1"), 60, 86400, unit="SHARES", currency_required=False),
        NumericalDomain.CASH_BALANCE: _policy(NumericalDomain.CASH_BALANCE, NumericalObservationType.BROKER_DISPLAYED_PRICE, Decimal("0.01"), Decimal("0"), ToleranceCombinationRule.ABSOLUTE_ONLY, Decimal("0.01"), 60, 300),
        NumericalDomain.BUYING_POWER: _policy(NumericalDomain.BUYING_POWER, NumericalObservationType.BROKER_DISPLAYED_PRICE, Decimal("0.01"), Decimal("0"), ToleranceCombinationRule.ABSOLUTE_ONLY, Decimal("0.01"), 60, 300),
        NumericalDomain.POSITION_QUANTITY: _policy(NumericalDomain.POSITION_QUANTITY, NumericalObservationType.INDEX_VALUE, Decimal("0"), Decimal("0"), ToleranceCombinationRule.EXACT_MATCH, Decimal("1"), 60, 300, unit="SHARES", currency_required=False),
        NumericalDomain.BROKER_EXECUTION_VALUE: _policy(NumericalDomain.BROKER_EXECUTION_VALUE, NumericalObservationType.EXECUTABLE_PRICE, Decimal("0.01"), Decimal("0"), ToleranceCombinationRule.TICK_OR_ABSOLUTE, Decimal("0.01"), 5, 60),
    }
    for domain in NumericalDomain:
        policies.setdefault(domain, _policy(domain, NumericalObservationType.INDEX_VALUE, Decimal("0.0001"), Decimal("0.0001"), ToleranceCombinationRule.ABSOLUTE_AND_RELATIVE, Decimal("0.0001"), 60, 3600))
    return MappingProxyType(policies)


def _policy(domain: NumericalDomain, obs_type: NumericalObservationType, absolute: Decimal, relative: Decimal, rule: ToleranceCombinationRule, tick: Decimal, alignment: int, freshness: int, *, unit: str = "USD", currency_required: bool = True) -> NumericalDomainPolicy:
    return NumericalDomainPolicy(domain, domain.value.lower(), (obs_type,), ("approved_authority_registry", "source_timestamp", "raw_evidence"), unit, currency_required, "EXPLICIT_ONLY", "VENUE_MUST_MATCH", "SESSION_MUST_MATCH", "market_time", alignment, freshness, "DEFER_EXECUTION", absolute, relative, rule, tick, "DOMAIN_POLICY", "ROUND_TO_TICK", "NO_IMPLICIT_AGGREGATION", "PRESERVE_OUTLIERS", absolute, ("source_id", "raw_value", "market_time", "retrieval_time", "evidence_references"))


def _normalized(observation: NumericalObservation, value: Decimal | None, unit: str, currency: str, rule: str, status: DataQualityStatus) -> NormalizedNumericalObservation:
    return NormalizedNumericalObservation(observation.observation_id, observation.raw_value, observation.raw_unit, observation.raw_currency, observation.raw_precision, value, unit, currency, rule, {"raw_unit": observation.raw_unit, "raw_currency": observation.raw_currency}, MO_TR_005_VERSION, observation.rounding_mode, utc_timestamp(), status, observation.evidence_references)


def _within_tolerance(policy: NumericalDomainPolicy, absolute: Decimal, relative: Decimal, ticks: Decimal | None) -> bool:
    abs_ok = absolute <= policy.absolute_tolerance
    rel_ok = relative <= policy.relative_tolerance
    tick_ok = ticks is not None and ticks <= 1
    return {
        ToleranceCombinationRule.ABSOLUTE_ONLY: abs_ok,
        ToleranceCombinationRule.RELATIVE_ONLY: rel_ok,
        ToleranceCombinationRule.ABSOLUTE_OR_RELATIVE: abs_ok or rel_ok,
        ToleranceCombinationRule.ABSOLUTE_AND_RELATIVE: abs_ok and rel_ok,
        ToleranceCombinationRule.TICK_ONLY: tick_ok,
        ToleranceCombinationRule.TICK_OR_ABSOLUTE: tick_ok or abs_ok,
        ToleranceCombinationRule.TICK_AND_TIME: tick_ok,
        ToleranceCombinationRule.EXACT_MATCH: absolute == 0,
        ToleranceCombinationRule.DOMAIN_SPECIFIC: abs_ok and rel_ok,
    }[policy.tolerance_combination_rule]


def _epochish(value: str) -> int:
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits[:14]) if digits else 0


def _stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{_stable_digest(parts)[:24].upper()}"


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return dict(value)
    if is_dataclass(value):
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name != "record_digest"}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
