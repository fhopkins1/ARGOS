"""MO-TR-008 macroeconomic, government, and statistical revision doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from decimal import Decimal
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_008_VERSION = "MO-TR-008/1.0.0"


class MacroDomain(str, Enum):
    INFLATION = "INFLATION"
    EMPLOYMENT = "EMPLOYMENT"
    UNEMPLOYMENT = "UNEMPLOYMENT"
    WAGES = "WAGES"
    GROSS_DOMESTIC_PRODUCT = "GROSS_DOMESTIC_PRODUCT"
    RETAIL_SALES = "RETAIL_SALES"
    INDUSTRIAL_PRODUCTION = "INDUSTRIAL_PRODUCTION"
    INTEREST_RATES = "INTEREST_RATES"
    CENTRAL_BANK_DECISIONS = "CENTRAL_BANK_DECISIONS"
    TREASURY_YIELDS = "TREASURY_YIELDS"
    TREASURY_ISSUANCE = "TREASURY_ISSUANCE"
    FISCAL_DATA = "FISCAL_DATA"
    HOUSING = "HOUSING"
    CONSUMER_CONFIDENCE = "CONSUMER_CONFIDENCE"
    BUSINESS_SURVEYS = "BUSINESS_SURVEYS"
    INVENTORIES = "INVENTORIES"
    COMMODITY_STATISTICS = "COMMODITY_STATISTICS"
    TRADE_BALANCE = "TRADE_BALANCE"
    CURRENT_ACCOUNT = "CURRENT_ACCOUNT"
    MONEY_SUPPLY = "MONEY_SUPPLY"
    CREDIT_CONDITIONS = "CREDIT_CONDITIONS"
    PRODUCTIVITY = "PRODUCTIVITY"
    LABOR_COSTS = "LABOR_COSTS"
    PERSONAL_INCOME = "PERSONAL_INCOME"
    PERSONAL_CONSUMPTION = "PERSONAL_CONSUMPTION"
    MANUFACTURING_ACTIVITY = "MANUFACTURING_ACTIVITY"
    SERVICES_ACTIVITY = "SERVICES_ACTIVITY"
    CONSTRUCTION_SPENDING = "CONSTRUCTION_SPENDING"
    UNKNOWN_MACRO_DOMAIN = "UNKNOWN_MACRO_DOMAIN"


class MacroAuthorityClass(str, Enum):
    OFFICIAL_STATISTICAL_AGENCY = "OFFICIAL_STATISTICAL_AGENCY"
    OFFICIAL_RELEASE_CALENDAR = "OFFICIAL_RELEASE_CALENDAR"
    CENTRAL_BANK = "CENTRAL_BANK"
    TREASURY_OR_DEBT_AUTHORITY = "TREASURY_OR_DEBT_AUTHORITY"
    PRIVATE_ECONOMIC_DATA = "PRIVATE_ECONOMIC_DATA"
    NEWS = "NEWS"
    MARKET_COMMENTARY = "MARKET_COMMENTARY"
    UNKNOWN_AUTHORITY = "UNKNOWN_AUTHORITY"


class MacroReleaseStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    DELAYED = "DELAYED"
    RESCHEDULED = "RESCHEDULED"
    PUBLISHED = "PUBLISHED"
    PARTIALLY_PUBLISHED = "PARTIALLY_PUBLISHED"
    CORRECTED = "CORRECTED"
    REVISED = "REVISED"
    BENCHMARK_REVISED = "BENCHMARK_REVISED"
    CANCELLED = "CANCELLED"
    WITHDRAWN = "WITHDRAWN"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN_RELEASE_STATUS = "UNKNOWN_RELEASE_STATUS"


class MacroVersionState(str, Enum):
    ADVANCE = "ADVANCE"
    FLASH = "FLASH"
    PRELIMINARY = "PRELIMINARY"
    FIRST_ESTIMATE = "FIRST_ESTIMATE"
    SECOND_ESTIMATE = "SECOND_ESTIMATE"
    THIRD_ESTIMATE = "THIRD_ESTIMATE"
    INITIAL = "INITIAL"
    REVISED = "REVISED"
    FINAL = "FINAL"
    BENCHMARK_REVISED = "BENCHMARK_REVISED"
    ANNUAL_REVISED = "ANNUAL_REVISED"
    SEASONALLY_REVISED = "SEASONALLY_REVISED"
    CORRECTED = "CORRECTED"
    RESTATED = "RESTATED"
    WITHDRAWN = "WITHDRAWN"
    UNKNOWN_VERSION = "UNKNOWN_VERSION"


class ExpectationCategory(str, Enum):
    ACTUAL_VALUE = "ACTUAL_VALUE"
    PRIOR_REPORTED_VALUE = "PRIOR_REPORTED_VALUE"
    REVISED_PRIOR_VALUE = "REVISED_PRIOR_VALUE"
    CONSENSUS_ESTIMATE = "CONSENSUS_ESTIMATE"
    ESTIMATE_RANGE_LOW = "ESTIMATE_RANGE_LOW"
    ESTIMATE_RANGE_HIGH = "ESTIMATE_RANGE_HIGH"
    MARKET_IMPLIED_EXPECTATION = "MARKET_IMPLIED_EXPECTATION"
    PRIVATE_FORECAST = "PRIVATE_FORECAST"
    ARGOS_MODEL_FORECAST = "ARGOS_MODEL_FORECAST"
    OFFICIAL_FORECAST = "OFFICIAL_FORECAST"
    UNKNOWN_EXPECTATION_TYPE = "UNKNOWN_EXPECTATION_TYPE"


class MacroReconciliationState(str, Enum):
    CURRENT_OFFICIAL_VALUE = "CURRENT_OFFICIAL_VALUE"
    HISTORICAL_VINTAGE = "HISTORICAL_VINTAGE"
    REVISION_SUPERSEDES_CURRENT_ONLY = "REVISION_SUPERSEDES_CURRENT_ONLY"
    FORECAST_SEPARATE = "FORECAST_SEPARATE"
    DIFFERENT_SERIES = "DIFFERENT_SERIES"
    CONFLICTED_OFFICIAL_RELEASE = "CONFLICTED_OFFICIAL_RELEASE"
    UNKNOWN = "UNKNOWN"
    ESCALATE_ANALYST = "ESCALATE_ANALYST"
    TRADE_RESTRICTED = "TRADE_RESTRICTED"


@dataclass(frozen=True)
class EconomicSeriesIdentity:
    series_id: str
    official_series_code: str
    series_name: str
    publishing_institution: str
    jurisdiction: str
    geographic_scope: str
    economic_domain: MacroDomain
    subject_population: str
    frequency: str
    unit: str
    scale: str
    currency: str
    price_basis: str
    seasonal_adjustment_basis: str
    annualization_basis: str
    index_base: str
    reference_period_type: str
    release_schedule_id: str
    authority_class: MacroAuthorityClass
    source_registry_id: str
    active_status: str
    effective_from: str
    effective_to: str
    rule_version: str = MO_TR_008_VERSION


@dataclass(frozen=True)
class EconomicReleaseIdentity:
    release_id: str
    release_family: str
    publishing_institution: str
    scheduled_publication_time: str
    actual_publication_time: str
    retrieval_time: str
    system_recorded_time: str
    release_status: MacroReleaseStatus
    release_vintage: str
    reference_period: str
    covered_series_ids: tuple[str, ...]
    official_document_ids: tuple[str, ...]
    source_urls_or_references: tuple[str, ...]
    superseded_release_id: str
    revision_relationships: tuple[str, ...]
    rule_version: str = MO_TR_008_VERSION


@dataclass(frozen=True)
class MacroObservation:
    observation_id: str
    series: EconomicSeriesIdentity
    release: EconomicReleaseIdentity
    reference_period: str
    reference_period_start: str
    reference_period_end: str
    publication_time: str
    retrieval_time: str
    system_recorded_time: str
    release_vintage: str
    value: str | None
    unit: str
    scale: str
    currency: str
    seasonal_adjustment_status: str
    annualization_status: str
    price_basis: str
    version_status: MacroVersionState
    source_authority: MacroAuthorityClass
    source_document_id: str
    expectation_category: ExpectationCategory
    prior_reported_value: str | None
    revised_prior_value: str | None
    consensus_estimate: str | None
    estimate_low: str | None
    estimate_high: str | None
    market_implied_expectation: str | None
    normalization_status: str
    comparability_status: str
    conflict_status: str
    evidence_references: tuple[str, ...]
    rule_version: str = MO_TR_008_VERSION


@dataclass(frozen=True)
class MacroRevisionRelationship:
    revision_id: str
    earlier_observation_id: str
    later_observation_id: str
    revision_type: str
    revision_scope: str
    publication_time: str
    reference_period: str
    original_value: str | None
    revised_value: str | None
    absolute_change: Decimal | None
    relative_change: Decimal | None
    source_declared_reason: str
    materiality_status: str
    affected_artifacts: tuple[str, ...]
    rule_version: str = MO_TR_008_VERSION


@dataclass(frozen=True)
class MacroReconciliationRecord:
    reconciliation_id: str
    selector_id: str
    state: MacroReconciliationState
    selected_observation_id: str
    excluded_observation_ids: tuple[str, ...]
    series_id: str
    reference_period: str
    vintage_cutoff: str
    rule_identifier: str
    doctrine_version: str
    reason: str
    evidence_references: tuple[str, ...]
    created_at: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class MacroTruthArchive:
    def __init__(self) -> None:
        self._observations: dict[str, MacroObservation] = {}
        self._revisions: list[MacroRevisionRelationship] = []
        self._records: dict[str, MacroReconciliationRecord] = {}

    def append_observation(self, observation: MacroObservation) -> None:
        if observation.observation_id in self._observations:
            raise ValueError("macro observations are append-only")
        self._observations[observation.observation_id] = observation

    def append_revision_relationship(self, relationship: MacroRevisionRelationship) -> None:
        self._revisions.append(relationship)

    def resolve_current_official(self, series_id: str, reference_period: str) -> MacroReconciliationRecord:
        candidates = self._official_candidates(series_id, reference_period, "")
        selected = _select_latest_official(candidates)
        state = MacroReconciliationState.CURRENT_OFFICIAL_VALUE if selected else MacroReconciliationState.UNKNOWN
        reason = "latest_official_vintage_selected_without_erasing_prior_vintages" if selected else "no_official_observation"
        return self._record("current", state, selected, candidates, series_id, reference_period, "", reason)

    def resolve_as_known_at(self, series_id: str, reference_period: str, knowledge_cutoff: str) -> MacroReconciliationRecord:
        candidates = self._official_candidates(series_id, reference_period, knowledge_cutoff)
        selected = _select_latest_official(candidates)
        state = MacroReconciliationState.HISTORICAL_VINTAGE if selected else MacroReconciliationState.UNKNOWN
        reason = "post_cutoff_revisions_excluded" if selected else "no_official_observation_known_at_cutoff"
        return self._record("as_known_at", state, selected, candidates, series_id, reference_period, knowledge_cutoff, reason)

    def classify_expectation(self, observation: MacroObservation) -> MacroReconciliationRecord:
        state = MacroReconciliationState.CURRENT_OFFICIAL_VALUE if observation.expectation_category is ExpectationCategory.ACTUAL_VALUE and _is_official(observation) else MacroReconciliationState.FORECAST_SEPARATE
        reason = "actual_official_value" if state is MacroReconciliationState.CURRENT_OFFICIAL_VALUE else "forecast_estimate_or_commentary_cannot_replace_actual_release"
        return self._record("expectation", state, observation if state is MacroReconciliationState.CURRENT_OFFICIAL_VALUE else None, (observation,), observation.series.series_id, observation.reference_period, observation.publication_time, reason)

    def _official_candidates(self, series_id: str, reference_period: str, cutoff: str) -> tuple[MacroObservation, ...]:
        candidates = [
            obs
            for obs in self._observations.values()
            if obs.series.series_id == series_id
            and obs.reference_period == reference_period
            and obs.expectation_category is ExpectationCategory.ACTUAL_VALUE
            and _is_official(obs)
            and obs.value is not None
            and obs.version_status is not MacroVersionState.WITHDRAWN
            and (not cutoff or obs.publication_time <= cutoff)
        ]
        return tuple(candidates)

    def _record(self, selector: str, state: MacroReconciliationState, selected: MacroObservation | None, candidates: tuple[MacroObservation, ...], series_id: str, reference_period: str, cutoff: str, reason: str) -> MacroReconciliationRecord:
        record = MacroReconciliationRecord(
            _stable_id("MACROREC", selector, series_id, reference_period, cutoff, selected.observation_id if selected else "", state.value),
            _stable_id("MACROSEL", selector, series_id, reference_period, cutoff),
            state,
            selected.observation_id if selected else "",
            tuple(obs.observation_id for obs in candidates if selected is None or obs.observation_id != selected.observation_id),
            series_id,
            reference_period,
            cutoff,
            selector,
            MO_TR_008_VERSION,
            reason,
            tuple(ref for obs in candidates for ref in obs.evidence_references),
            utc_timestamp(),
        )
        self._records[record.reconciliation_id] = record
        return record

    def all_records(self) -> tuple[MacroReconciliationRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))


def make_macro_revision_relationship(earlier: MacroObservation, later: MacroObservation, revision_type: str, reason: str = "") -> MacroRevisionRelationship:
    original = Decimal(earlier.value) if earlier.value is not None else None
    revised = Decimal(later.value) if later.value is not None else None
    absolute = abs(revised - original) if revised is not None and original is not None else None
    relative = absolute / abs(original) if absolute is not None and original not in {None, Decimal("0")} else None
    return MacroRevisionRelationship(_stable_id("MACROREV", earlier.observation_id, later.observation_id, revision_type), earlier.observation_id, later.observation_id, revision_type, "declared_series_reference_period", later.publication_time, later.reference_period, earlier.value, later.value, absolute, relative, reason, "MATERIALITY_REQUIRES_POLICY", (), MO_TR_008_VERSION)


def _select_latest_official(candidates: tuple[MacroObservation, ...]) -> MacroObservation | None:
    if not candidates:
        return None
    priority = {
        MacroVersionState.CORRECTED: 1,
        MacroVersionState.BENCHMARK_REVISED: 2,
        MacroVersionState.ANNUAL_REVISED: 3,
        MacroVersionState.SEASONALLY_REVISED: 4,
        MacroVersionState.REVISED: 5,
        MacroVersionState.FINAL: 6,
        MacroVersionState.THIRD_ESTIMATE: 7,
        MacroVersionState.SECOND_ESTIMATE: 8,
        MacroVersionState.FIRST_ESTIMATE: 9,
        MacroVersionState.INITIAL: 10,
        MacroVersionState.PRELIMINARY: 11,
        MacroVersionState.ADVANCE: 12,
        MacroVersionState.UNKNOWN_VERSION: 99,
    }
    return sorted(candidates, key=lambda obs: (obs.publication_time, -priority.get(obs.version_status, 50), obs.observation_id))[-1]


def _is_official(observation: MacroObservation) -> bool:
    return observation.source_authority in {MacroAuthorityClass.OFFICIAL_STATISTICAL_AGENCY, MacroAuthorityClass.CENTRAL_BANK, MacroAuthorityClass.TREASURY_OR_DEBT_AUTHORITY}


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
