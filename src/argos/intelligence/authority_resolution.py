"""MO-TR-001 authority-domain and source-precedence doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp
from argos.intelligence.source_registry import ApprovedSourceRecord, SourceAuthorityClass, canonical_source_registry


MO_TR_001_VERSION = "MO-TR-001/1.0.0"


class AuthorityRole(str, Enum):
    PRIMARY_AUTHORITY = "PRIMARY_AUTHORITY"
    ACCOUNT_SPECIFIC_AUTHORITY = "ACCOUNT_SPECIFIC_AUTHORITY"
    PRIMARY_RECORD_AUTHORITY = "PRIMARY_RECORD_AUTHORITY"
    CORROBORATING_AUTHORITY = "CORROBORATING_AUTHORITY"
    DERIVATIVE_AUTHORITY = "DERIVATIVE_AUTHORITY"
    PROVISIONAL_SOURCE = "PROVISIONAL_SOURCE"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    PROHIBITED_OVERRIDE = "PROHIBITED_OVERRIDE"
    NO_AUTHORITY = "NO_AUTHORITY"
    UNKNOWN_AUTHORITY_ROLE = "UNKNOWN_AUTHORITY_ROLE"


class AuthorityStatus(str, Enum):
    AUTHORITATIVE = "AUTHORITATIVE"
    AUTHORITATIVE_WITH_SCOPE_LIMIT = "AUTHORITATIVE_WITH_SCOPE_LIMIT"
    CORROBORATING = "CORROBORATING"
    PROVISIONALLY_ADMISSIBLE = "PROVISIONALLY_ADMISSIBLE"
    DISCOVERY_ADMISSIBLE = "DISCOVERY_ADMISSIBLE"
    INELIGIBLE = "INELIGIBLE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"
    CONFLICTED_PRIMARY_AUTHORITY = "CONFLICTED_PRIMARY_AUTHORITY"
    PRIMARY_AUTHORITY_UNAVAILABLE = "PRIMARY_AUTHORITY_UNAVAILABLE"
    POLICY_NOT_FOUND = "POLICY_NOT_FOUND"
    SOURCE_NOT_CLASSIFIED = "SOURCE_NOT_CLASSIFIED"
    UNKNOWN = "UNKNOWN"


class PrecedenceOutcome(str, Enum):
    PRIMARY_PREVAILS = "PRIMARY_PREVAILS"
    ACCOUNT_AUTHORITY_PREVAILS = "ACCOUNT_AUTHORITY_PREVAILS"
    OFFICIAL_RECORD_PREVAILS = "OFFICIAL_RECORD_PREVAILS"
    AMENDED_RECORD_PREVAILS = "AMENDED_RECORD_PREVAILS"
    CORRECTED_RECORD_PREVAILS = "CORRECTED_RECORD_PREVAILS"
    LATEST_EFFECTIVE_OFFICIAL_VERSION_PREVAILS = "LATEST_EFFECTIVE_OFFICIAL_VERSION_PREVAILS"
    PROVISIONAL_USE_AUTHORIZED = "PROVISIONAL_USE_AUTHORIZED"
    CORROBORATION_REQUIRED = "CORROBORATION_REQUIRED"
    PRIMARY_INCOMPLETE = "PRIMARY_INCOMPLETE"
    PRIMARY_UNAVAILABLE = "PRIMARY_UNAVAILABLE"
    CONFLICTING_PRIMARY_AUTHORITIES = "CONFLICTING_PRIMARY_AUTHORITIES"
    NO_ELIGIBLE_AUTHORITY = "NO_ELIGIBLE_AUTHORITY"
    NONCOMPARABLE_OBSERVATIONS = "NONCOMPARABLE_OBSERVATIONS"
    ESCALATION_REQUIRED = "ESCALATION_REQUIRED"
    TRADE_BLOCK_REQUIRED = "TRADE_BLOCK_REQUIRED"
    UNKNOWN = "UNKNOWN"


class AuthorityFailureOutcome(str, Enum):
    FAIL_CLOSED = "FAIL_CLOSED"
    PRESERVE_AND_ESCALATE = "PRESERVE_AND_ESCALATE"
    RECOLLECT_PRIMARY = "RECOLLECT_PRIMARY"
    QUERY_SECONDARY_CONFIRMATION = "QUERY_SECONDARY_CONFIRMATION"
    ALLOW_EXPLICIT_PROVISIONAL_STATE = "ALLOW_EXPLICIT_PROVISIONAL_STATE"
    BLOCK_AFFECTED_INSTRUMENT = "BLOCK_AFFECTED_INSTRUMENT"
    BLOCK_NEW_ORDERS = "BLOCK_NEW_ORDERS"
    BLOCK_POSITION_INCREASES = "BLOCK_POSITION_INCREASES"
    BLOCK_ALL_TRADING = "BLOCK_ALL_TRADING"
    REQUIRE_HUMAN_REVIEW = "REQUIRE_HUMAN_REVIEW"
    MARK_UNKNOWN = "MARK_UNKNOWN"
    MARK_CONFLICTED = "MARK_CONFLICTED"


class GoverningTimestampType(str, Enum):
    MARKET_TIME = "market_time"
    PUBLICATION_TIME = "publication_time"
    FILING_TIME = "filing_time"
    EFFECTIVE_TIME = "effective_time"
    EXECUTION_TIME = "execution_time"
    RETRIEVAL_TIME = "retrieval_time"


@dataclass(frozen=True)
class AuthorityDomainPolicy:
    domain_id: str
    description: str
    fact_subject: str
    primary_authority_classes: tuple[AuthorityRole, ...]
    authority_boundary: tuple[str, ...]
    secondary_confirmation_classes: tuple[AuthorityRole, ...]
    provisional_source_classes: tuple[AuthorityRole, ...]
    discovery_only_classes: tuple[AuthorityRole, ...]
    prohibited_override_classes: tuple[AuthorityRole, ...]
    governing_timestamp_type: GoverningTimestampType
    revision_policy: str
    primary_unavailable_policy: AuthorityFailureOutcome
    conflict_policy: AuthorityFailureOutcome
    escalation_destination: str
    unresolved_state_consequence: str
    trade_blocking_behavior: AuthorityFailureOutcome
    account_or_instrument_scoping_rule: str
    source_independence_requirements: tuple[str, ...]
    required_evidence_fields: tuple[str, ...]
    policy_version: str
    effective_date: str
    retirement_date: str = ""
    superseding_policy_version: str = ""


@dataclass(frozen=True)
class SourceClassification:
    source_id: str
    source_organization: str
    source_product_or_surface: str
    source_class: AuthorityRole
    ownership_entity: str
    originating_data_provider: str
    jurisdiction: tuple[str, ...]
    covered_venues: tuple[str, ...]
    covered_instruments: tuple[str, ...]
    covered_accounts: tuple[str, ...]
    covered_fact_domains: tuple[str, ...]
    authentication_status: str
    licensing_status: str
    real_time_or_delayed_status: str
    source_timestamp_capabilities: tuple[GoverningTimestampType, ...]
    revision_capabilities: tuple[str, ...]
    provenance_capabilities: tuple[str, ...]
    source_health_state: str
    authority_eligible: bool
    discovery_eligible: bool
    provisional_eligible: bool
    corroboration_eligible: bool
    prohibited_domain_list: tuple[str, ...]
    effective_configuration_version: str


@dataclass(frozen=True)
class AuthorityObservation:
    observation_id: str
    fact_domain: str
    source_id: str
    instrument_id: str
    issuer_id: str
    account_id: str
    market_venue: str
    jurisdiction: str
    observation_timestamp: str
    publication_timestamp: str
    effective_timestamp: str
    retrieval_timestamp: str
    revision_status: str
    complete: bool
    current: bool
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class AuthorityDetermination:
    determination_id: str
    fact_domain: str
    policy_version: str
    authority_role: AuthorityRole
    authority_status: AuthorityStatus
    source_eligibility_result: str
    scope_match_result: str
    timestamp_governance_result: str
    revision_status: str
    precedence_rank: int
    permitted_uses: tuple[str, ...]
    prohibited_uses: tuple[str, ...]
    provisional_expiration: str
    escalation_requirement: str
    unresolved_state_consequence: str
    trade_consequence: AuthorityFailureOutcome
    reason_code: str
    evidence_references: tuple[str, ...]
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


@dataclass(frozen=True)
class PrecedenceDecision:
    precedence_id: str
    fact_domain: str
    outcome: PrecedenceOutcome
    selected_observation_id: str
    all_observation_ids: tuple[str, ...]
    escalation_destination: str
    trade_consequence: AuthorityFailureOutcome
    evidence_references: tuple[str, ...]
    created_at: str
    decision_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_digest", _stable_digest(self))


class AuthorityDomainRegistry:
    def __init__(self, policies: Mapping[str, AuthorityDomainPolicy] | None = None) -> None:
        self._policies = MappingProxyType(dict(policies or default_authority_domain_policies()))

    def policy(self, domain_id: str) -> AuthorityDomainPolicy | None:
        return self._policies.get(domain_id)


class SourceClassificationRegistry:
    def __init__(self, classifications: Mapping[str, SourceClassification] | None = None) -> None:
        self._classifications = MappingProxyType(dict(classifications or default_source_classifications()))

    def classification(self, source_id: str) -> SourceClassification | None:
        return self._classifications.get(source_id)


class AuthorityResolutionEngine:
    def __init__(self, domains: AuthorityDomainRegistry | None = None, sources: SourceClassificationRegistry | None = None) -> None:
        self.domains = domains or AuthorityDomainRegistry()
        self.sources = sources or SourceClassificationRegistry()

    def resolve(self, observation: AuthorityObservation, originating_office: str, workflow_id: str) -> AuthorityDetermination:
        policy = self.domains.policy(observation.fact_domain)
        source = self.sources.classification(observation.source_id)
        if policy is None:
            return _determination(observation, "UNKNOWN", AuthorityRole.UNKNOWN_AUTHORITY_ROLE, AuthorityStatus.POLICY_NOT_FOUND, 99, "policy_not_found", (), AuthorityFailureOutcome.FAIL_CLOSED)
        if source is None:
            return _determination(observation, policy.policy_version, AuthorityRole.UNKNOWN_AUTHORITY_ROLE, AuthorityStatus.SOURCE_NOT_CLASSIFIED, 99, "source_not_classified", (), policy.trade_blocking_behavior)
        role = _role_for(policy, source)
        scope = _scope_match(policy, source, observation)
        if role is AuthorityRole.NO_AUTHORITY:
            return _determination(observation, policy.policy_version, role, AuthorityStatus.INELIGIBLE, 99, "source_not_authorized_for_domain", (), policy.trade_blocking_behavior)
        if not scope:
            return _determination(observation, policy.policy_version, role, AuthorityStatus.OUT_OF_SCOPE, 99, "scope_mismatch", (), policy.trade_blocking_behavior)
        if not observation.current:
            return _determination(observation, policy.policy_version, role, AuthorityStatus.EXPIRED, _rank(role), "observation_not_current", (), policy.trade_blocking_behavior)
        status = {
            AuthorityRole.PRIMARY_AUTHORITY: AuthorityStatus.AUTHORITATIVE,
            AuthorityRole.ACCOUNT_SPECIFIC_AUTHORITY: AuthorityStatus.AUTHORITATIVE_WITH_SCOPE_LIMIT,
            AuthorityRole.PRIMARY_RECORD_AUTHORITY: AuthorityStatus.AUTHORITATIVE_WITH_SCOPE_LIMIT,
            AuthorityRole.CORROBORATING_AUTHORITY: AuthorityStatus.CORROBORATING,
            AuthorityRole.PROVISIONAL_SOURCE: AuthorityStatus.PROVISIONALLY_ADMISSIBLE,
            AuthorityRole.DISCOVERY_ONLY: AuthorityStatus.DISCOVERY_ADMISSIBLE,
            AuthorityRole.PROHIBITED_OVERRIDE: AuthorityStatus.INELIGIBLE,
        }.get(role, AuthorityStatus.UNKNOWN)
        return _determination(observation, policy.policy_version, role, status, _rank(role), "eligible_authority_scope", ("institutional_evidence",), policy.trade_blocking_behavior)


class PrecedenceEvaluator:
    def __init__(self, resolver: AuthorityResolutionEngine | None = None) -> None:
        self.resolver = resolver or AuthorityResolutionEngine()

    def evaluate(self, observations: tuple[AuthorityObservation, ...], workflow_id: str, originating_office: str) -> PrecedenceDecision:
        if not observations:
            return _precedence("UNKNOWN", (), PrecedenceOutcome.NO_ELIGIBLE_AUTHORITY, "", "Commander", AuthorityFailureOutcome.FAIL_CLOSED, ())
        domains = {obs.fact_domain for obs in observations}
        if len(domains) != 1:
            return _precedence("MULTI_DOMAIN", observations, PrecedenceOutcome.NONCOMPARABLE_OBSERVATIONS, "", "Analyst", AuthorityFailureOutcome.PRESERVE_AND_ESCALATE, ())
        determinations = [self.resolver.resolve(obs, originating_office, workflow_id) for obs in observations]
        eligible = [det for det in determinations if det.authority_status in {AuthorityStatus.AUTHORITATIVE, AuthorityStatus.AUTHORITATIVE_WITH_SCOPE_LIMIT, AuthorityStatus.CORROBORATING, AuthorityStatus.PROVISIONALLY_ADMISSIBLE}]
        policy = self.resolver.domains.policy(observations[0].fact_domain)
        destination = policy.escalation_destination if policy else "Commander"
        if not eligible:
            return _precedence(observations[0].fact_domain, observations, PrecedenceOutcome.NO_ELIGIBLE_AUTHORITY, "", destination, AuthorityFailureOutcome.FAIL_CLOSED, _evidence(determinations))
        primary = [det for det in eligible if det.authority_role in {AuthorityRole.PRIMARY_AUTHORITY, AuthorityRole.ACCOUNT_SPECIFIC_AUTHORITY, AuthorityRole.PRIMARY_RECORD_AUTHORITY}]
        if len(primary) > 1:
            return _precedence(observations[0].fact_domain, observations, PrecedenceOutcome.CONFLICTING_PRIMARY_AUTHORITIES, "", destination, AuthorityFailureOutcome.MARK_CONFLICTED, _evidence(determinations))
        if len(primary) == 1:
            selected = next(obs.observation_id for obs in observations if obs.evidence_references == primary[0].evidence_references)
            outcome = PrecedenceOutcome.ACCOUNT_AUTHORITY_PREVAILS if primary[0].authority_role is AuthorityRole.ACCOUNT_SPECIFIC_AUTHORITY else PrecedenceOutcome.OFFICIAL_RECORD_PREVAILS if primary[0].authority_role is AuthorityRole.PRIMARY_RECORD_AUTHORITY else PrecedenceOutcome.PRIMARY_PREVAILS
            return _precedence(observations[0].fact_domain, observations, outcome, selected, "", AuthorityFailureOutcome.MARK_UNKNOWN, _evidence(determinations))
        provisional = [det for det in eligible if det.authority_role is AuthorityRole.PROVISIONAL_SOURCE]
        if provisional:
            selected = next(obs.observation_id for obs in observations if obs.evidence_references == provisional[0].evidence_references)
            return _precedence(observations[0].fact_domain, observations, PrecedenceOutcome.PROVISIONAL_USE_AUTHORIZED, selected, destination, AuthorityFailureOutcome.ALLOW_EXPLICIT_PROVISIONAL_STATE, _evidence(determinations))
        return _precedence(observations[0].fact_domain, observations, PrecedenceOutcome.CORROBORATION_REQUIRED, "", destination, AuthorityFailureOutcome.QUERY_SECONDARY_CONFIRMATION, _evidence(determinations))


class AuthorityEvidenceLedger:
    def __init__(self) -> None:
        self._records: dict[str, AuthorityDetermination] = {}

    def append(self, determination: AuthorityDetermination) -> None:
        if determination.determination_id in self._records:
            raise ValueError("authority determinations are append-only")
        self._records[determination.determination_id] = determination

    def all_records(self) -> tuple[AuthorityDetermination, ...]:
        return tuple(self._records[key] for key in sorted(self._records))


def default_authority_domain_policies() -> Mapping[str, AuthorityDomainPolicy]:
    return MappingProxyType({
        "current_market_price": _policy("current_market_price", "Current Market Price", (AuthorityRole.PRIMARY_AUTHORITY,), GoverningTimestampType.MARKET_TIME, "Risk", AuthorityFailureOutcome.BLOCK_NEW_ORDERS),
        "official_opening_price": _policy("official_opening_price", "Official Opening Price", (AuthorityRole.PRIMARY_RECORD_AUTHORITY,), GoverningTimestampType.MARKET_TIME, "Intelligence", AuthorityFailureOutcome.FAIL_CLOSED),
        "official_closing_price": _policy("official_closing_price", "Official Closing Price", (AuthorityRole.PRIMARY_RECORD_AUTHORITY,), GoverningTimestampType.MARKET_TIME, "Intelligence", AuthorityFailureOutcome.FAIL_CLOSED),
        "sec_filing": _policy("sec_filing", "SEC Filing", (AuthorityRole.PRIMARY_RECORD_AUTHORITY,), GoverningTimestampType.FILING_TIME, "Analyst", AuthorityFailureOutcome.MARK_UNKNOWN),
        "issuer_publication": _policy("issuer_publication", "Issuer Publication", (AuthorityRole.PRIMARY_RECORD_AUTHORITY,), GoverningTimestampType.PUBLICATION_TIME, "Analyst", AuthorityFailureOutcome.MARK_UNKNOWN),
        "broker_account_state": _policy("broker_account_state", "Broker Account State", (AuthorityRole.ACCOUNT_SPECIFIC_AUTHORITY,), GoverningTimestampType.RETRIEVAL_TIME, "Risk", AuthorityFailureOutcome.BLOCK_NEW_ORDERS),
    })


def default_source_classifications() -> Mapping[str, SourceClassification]:
    registry = canonical_source_registry()
    return MappingProxyType({source.source_id: _classification_from_source(source) for source in registry.snapshot.sources})


def _policy(domain_id: str, description: str, primary: tuple[AuthorityRole, ...], timestamp: GoverningTimestampType, escalation: str, trade: AuthorityFailureOutcome) -> AuthorityDomainPolicy:
    return AuthorityDomainPolicy(domain_id, description, domain_id, primary, ("entity", "instrument", "account", "jurisdiction", "venue", "timestamp"), (AuthorityRole.CORROBORATING_AUTHORITY,), (AuthorityRole.PROVISIONAL_SOURCE,), (AuthorityRole.DISCOVERY_ONLY,), (AuthorityRole.PROHIBITED_OVERRIDE, AuthorityRole.DERIVATIVE_AUTHORITY), timestamp, "append_only_corrections_and_revisions", AuthorityFailureOutcome.RECOLLECT_PRIMARY, AuthorityFailureOutcome.PRESERVE_AND_ESCALATE, escalation, "mark_unknown_until_resolved", trade, "matching identifiers and scope required", ("MO-TR-002 independence required before corroboration",), ("source_id", "timestamp", "raw_evidence_reference"), MO_TR_001_VERSION, "2026-07-20T00:00:00Z")


def _classification_from_source(source: ApprovedSourceRecord) -> SourceClassification:
    role = {
        SourceAuthorityClass.PRIMARY_AUTHORITY: AuthorityRole.PRIMARY_RECORD_AUTHORITY if "regulatory_filing" in source.source_family or "issuer_publication" in source.source_family else AuthorityRole.PRIMARY_AUTHORITY,
        SourceAuthorityClass.LICENSED_MARKET_AUTHORITY: AuthorityRole.PRIMARY_AUTHORITY,
        SourceAuthorityClass.CORROBORATING_AUTHORITY: AuthorityRole.CORROBORATING_AUTHORITY,
        SourceAuthorityClass.DISCOVERY_ONLY: AuthorityRole.DISCOVERY_ONLY,
        SourceAuthorityClass.EARLY_WARNING_ONLY: AuthorityRole.DISCOVERY_ONLY,
        SourceAuthorityClass.ADVERSARIAL_EVIDENCE: AuthorityRole.CORROBORATING_AUTHORITY,
        SourceAuthorityClass.FALLBACK_ONLY: AuthorityRole.PROVISIONAL_SOURCE,
        SourceAuthorityClass.PROHIBITED: AuthorityRole.PROHIBITED_OVERRIDE,
    }[source.authority_class]
    if source.source_id == "SRC-BROKER-OF-RECORD":
        role = AuthorityRole.ACCOUNT_SPECIFIC_AUTHORITY
    return SourceClassification(source.source_id, source.owning_institution, source.canonical_name, role, source.owning_institution, source.owning_institution, source.jurisdiction, ("US",), source.asset_classes, ("paper",), source.fact_types, source.credential_requirement.value, source.licensing_class.value, source.freshness_expectation_class.value, (GoverningTimestampType.RETRIEVAL_TIME, GoverningTimestampType.PUBLICATION_TIME), ("append_only",), ("raw_evidence_reference", "digest"), source.source_status.value, role not in {AuthorityRole.PROHIBITED_OVERRIDE, AuthorityRole.DISCOVERY_ONLY}, role is AuthorityRole.DISCOVERY_ONLY, role is AuthorityRole.PROVISIONAL_SOURCE, role is AuthorityRole.CORROBORATING_AUTHORITY, source.prohibited_conclusions, source.registry_version)


def _role_for(policy: AuthorityDomainPolicy, source: SourceClassification) -> AuthorityRole:
    if policy.domain_id in source.prohibited_domain_list:
        return AuthorityRole.PROHIBITED_OVERRIDE
    if policy.domain_id == "current_market_price" and source.source_id == "SRC-LICENSED-SIP-MARKET-DATA":
        return AuthorityRole.PRIMARY_AUTHORITY
    if policy.domain_id in {"official_opening_price", "official_closing_price"} and source.source_id == "SRC-LICENSED-SIP-MARKET-DATA":
        return AuthorityRole.PRIMARY_RECORD_AUTHORITY
    if policy.domain_id == "sec_filing" and source.source_id == "SRC-US-SEC-EDGAR":
        return AuthorityRole.PRIMARY_RECORD_AUTHORITY
    if policy.domain_id == "issuer_publication" and source.source_id == "SRC-ISSUER-IR":
        return AuthorityRole.PRIMARY_RECORD_AUTHORITY
    if policy.domain_id == "broker_account_state" and source.source_id == "SRC-BROKER-OF-RECORD":
        return AuthorityRole.ACCOUNT_SPECIFIC_AUTHORITY
    if source.corroboration_eligible:
        return AuthorityRole.CORROBORATING_AUTHORITY
    if source.provisional_eligible:
        return AuthorityRole.PROVISIONAL_SOURCE
    if source.discovery_eligible:
        return AuthorityRole.DISCOVERY_ONLY
    return AuthorityRole.NO_AUTHORITY


def _scope_match(policy: AuthorityDomainPolicy, source: SourceClassification, observation: AuthorityObservation) -> bool:
    if observation.jurisdiction and source.jurisdiction and observation.jurisdiction not in source.jurisdiction and "GLOBAL" not in source.jurisdiction:
        return False
    if policy.domain_id == "broker_account_state" and not observation.account_id:
        return False
    if policy.domain_id != "broker_account_state" and not (observation.instrument_id or observation.issuer_id):
        return False
    return True


def _rank(role: AuthorityRole) -> int:
    return {
        AuthorityRole.PRIMARY_AUTHORITY: 1,
        AuthorityRole.ACCOUNT_SPECIFIC_AUTHORITY: 1,
        AuthorityRole.PRIMARY_RECORD_AUTHORITY: 1,
        AuthorityRole.CORROBORATING_AUTHORITY: 2,
        AuthorityRole.PROVISIONAL_SOURCE: 3,
        AuthorityRole.DISCOVERY_ONLY: 4,
    }.get(role, 99)


def _determination(observation: AuthorityObservation, policy_version: str, role: AuthorityRole, status: AuthorityStatus, rank: int, reason: str, permitted: tuple[str, ...], trade: AuthorityFailureOutcome) -> AuthorityDetermination:
    return AuthorityDetermination(_stable_id("AUTHDET", observation.observation_id, policy_version, role.value, status.value), observation.fact_domain, policy_version, role, status, "eligible" if status not in {AuthorityStatus.INELIGIBLE, AuthorityStatus.SOURCE_NOT_CLASSIFIED, AuthorityStatus.POLICY_NOT_FOUND} else "failed", "MATCH" if status is not AuthorityStatus.OUT_OF_SCOPE else "MISMATCH", "governing_timestamp_preserved", observation.revision_status, rank, permitted, ("universal_trust", "authority_outside_domain"), "", "NONE" if status in {AuthorityStatus.AUTHORITATIVE, AuthorityStatus.AUTHORITATIVE_WITH_SCOPE_LIMIT} else "ESCALATE", "block_or_mark_unknown", trade, reason, observation.evidence_references)


def _precedence(domain: str, observations: tuple[AuthorityObservation, ...], outcome: PrecedenceOutcome, selected: str, destination: str, trade: AuthorityFailureOutcome, evidence: tuple[str, ...]) -> PrecedenceDecision:
    return PrecedenceDecision(_stable_id("PRECEDENCE", domain, tuple(obs.observation_id for obs in observations), outcome.value), domain, outcome, selected, tuple(obs.observation_id for obs in observations), destination, trade, evidence, utc_timestamp())


def _evidence(determinations: list[AuthorityDetermination]) -> tuple[str, ...]:
    return tuple(det.determination_id for det in determinations)


def _stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{_stable_digest(parts)[:24].upper()}"


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return dict(value)
    if is_dataclass(value):
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name not in {"record_digest", "decision_digest"}}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
